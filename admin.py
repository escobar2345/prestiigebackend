from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy.orm import Session
from functools import wraps

from database import get_db
from models import User, UserRole

router = APIRouter()


# ════════════════════════════════════════════════════════════════
#  CORE GUARD FUNCTION — This is the protection engine
#  Call this at the top of ANY route you want to protect.
# ════════════════════════════════════════════════════════════════
def require_super_admin(request: Request, db: Session):
    """
    Checks if the current session user is a super_admin.
    Returns the User object if authorized.
    Raises a RedirectResponse if not logged in or not super_admin.
    
    Usage inside any route:
        user = require_super_admin(request, db)
    """
    user_id = request.session.get("user_id")

    # Step 1: Not logged in at all → redirect to login
    if not user_id:
        raise _redirect("/auth/login-page?error=Please+login+to+continue")

    # Step 2: Find the user in the database
    user = db.query(User).filter(User.id == user_id).first()

    # Step 3: User not found (deleted?) → clear session and redirect
    if not user:
        request.session.clear()
        raise _redirect("/auth/login-page?error=Session+invalid.+Please+login+again.")

    # Step 4: User exists but is NOT a super_admin → block access
    if not user.is_super_admin():
        raise _redirect("/?error=Access+Denied.+Admins+only.")

    # Step 5: All checks passed → return the user
    return user


def _redirect(url: str):
    """Helper: raises a redirect as an exception so it breaks out of any route."""
    from fastapi import HTTPException
    # We use a trick: return a RedirectResponse wrapped in an exception-like raise
    # FastAPI will catch this response object
    response = RedirectResponse(url=url, status_code=302)
    # We raise HTTPException but store redirect in headers approach won't work cleanly
    # Instead we just return the RedirectResponse directly (see usage below)
    return response  # Caller does: raise or return


# ════════════════════════════════════════════════════════════════
#  ADMIN ROUTES — All protected by require_super_admin()
# ════════════════════════════════════════════════════════════════

@router.get("/dashboard", response_class=HTMLResponse)
def admin_dashboard(request: Request, db: Session = Depends(get_db)):
    """
    Main admin dashboard — ONLY super_admin can access this.
    Regular users are redirected away automatically.
    """
    # ★ THIS ONE LINE PROTECTS THE ENTIRE ROUTE ★
    auth_result = require_super_admin(request, db)
    if isinstance(auth_result, RedirectResponse):
        return auth_result  # Block access — redirect non-admins
    user = auth_result

    return f"""
    <html>
      <head>
        <title>Admin Dashboard</title>
        <style>
          body {{ font-family: sans-serif; padding: 40px; background: #f4f4f4; }}
          .card {{ background: white; padding: 24px; border-radius: 8px; margin: 16px 0; box-shadow: 0 2px 8px rgba(0,0,0,0.1); }}
          .badge {{ background: #e74c3c; color: white; padding: 4px 10px; border-radius: 4px; font-size: 12px; }}
          .nav {{ background: #222; color: white; padding: 16px 40px; margin: -40px -40px 40px; display: flex; justify-content: space-between; }}
          a {{ color: #3498db; }}
          .btn {{ padding: 10px 20px; background: #e74c3c; color: white; border: none; border-radius: 4px; cursor: pointer; text-decoration: none; }}
        </style>
      </head>
      <body>
        <div class="nav">
          <span>🛒 EcommerceApp — <strong>Admin Panel</strong></span>
          <span>👤 {user.username} <span class="badge">SUPER ADMIN</span> | <a href="/auth/logout" style="color:#aaa;">Logout</a></span>
        </div>

        <h2>📊 Admin Dashboard</h2>

        <div class="card">
          <h3>✅ Access Granted</h3>
          <p>Welcome, <strong>{user.username}</strong>! You have full admin access.</p>
        </div>

        <div class="card">
          <h3>🔧 Admin Sections</h3>
          <p>
            <a href="/admin/users">👥 Manage Users</a> &nbsp;|&nbsp;
            <a href="/admin/products">📦 Manage Products</a> &nbsp;|&nbsp;
            <a href="/admin/orders">🧾 View Orders</a>
          </p>
        </div>

        <div class="card">
          <h3>🔐 Security Info</h3>
          <p>This page is protected. Regular users who try to visit this URL are automatically redirected away.</p>
        </div>
      </body>
    </html>
    """


@router.get("/users", response_class=HTMLResponse)
def admin_users(request: Request, db: Session = Depends(get_db)):
    """Manage users — protected route."""
    auth_result = require_super_admin(request, db)
    if isinstance(auth_result, RedirectResponse):
        return auth_result
    user = auth_result

    # Fetch all users from the database
    all_users = db.query(User).all()
    rows = ""
    for u in all_users:
        role_badge = "🔴 super_admin" if u.is_super_admin() else "🟢 user"
        rows += f"<tr><td>{u.id}</td><td>{u.username}</td><td>{u.email}</td><td>{role_badge}</td></tr>"

    return f"""
    <html>
      <head><title>Manage Users</title>
        <style>
          body {{ font-family: sans-serif; padding: 40px; }}
          table {{ width: 100%; border-collapse: collapse; }}
          th, td {{ border: 1px solid #ddd; padding: 10px; text-align: left; }}
          th {{ background: #222; color: white; }}
          tr:nth-child(even) {{ background: #f9f9f9; }}
        </style>
      </head>
      <body>
        <a href="/admin/dashboard">← Back to Dashboard</a>
        <h2>👥 All Users</h2>
        <table>
          <tr><th>ID</th><th>Username</th><th>Email</th><th>Role</th></tr>
          {rows}
        </table>
      </body>
    </html>
    """


@router.get("/products", response_class=HTMLResponse)
def admin_products(request: Request, db: Session = Depends(get_db)):
    """Manage products — protected route."""
    auth_result = require_super_admin(request, db)
    if isinstance(auth_result, RedirectResponse):
        return auth_result

    return """
    <html><body style="font-family:sans-serif; padding:40px;">
      <a href="/admin/dashboard">← Back to Dashboard</a>
      <h2>📦 Manage Products</h2>
      <p>Product management interface goes here.</p>
    </body></html>
    """