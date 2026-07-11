import os

from fastapi import APIRouter, Depends, Request, Form, HTTPException, status
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from sqlalchemy.orm import Session
import bcrypt as bcrypt_lib

from database import get_db
from models import User, UserRole

router = APIRouter()


class AdminLoginPayload(BaseModel):
    email: str
    password: str


ADMIN_ACCESS_COOKIE = "prestiige_admin_access"


def _set_admin_cookie(response, is_admin: bool):
    if is_admin:
        response.set_cookie(
            key=ADMIN_ACCESS_COOKIE,
            value="true",
            httponly=True,
            secure=os.getenv("COOKIE_SECURE", "false").lower() == "true",
            samesite="lax",
            max_age=60 * 60 * 8,
            path="/",
        )
    else:
        response.delete_cookie(ADMIN_ACCESS_COOKIE, path="/")


def serialize_user(user: User) -> dict:
    return {
        "id": user.id,
        "username": user.username,
        "email": user.email,
        "role": user.role.value,
        "is_admin": user.is_super_admin(),
    }


# ─── Login Page (GET) ──────────────────────────────────────────
@router.get("/login-page", response_class=HTMLResponse)
def login_page(request: Request):
    error = request.query_params.get("error", "")
    error_html = f'<p style="color:red;">{error}</p>' if error else ""
    return f"""
    <html>
      <body style="font-family: sans-serif; padding: 40px; max-width: 400px;">
        <h2>🔐 Login</h2>
        {error_html}
        <form method="POST" action="/auth/login">
          <label>Username</label><br>
          <input name="username" type="text" required style="width:100%; padding:8px; margin:8px 0;"><br>
          <label>Password</label><br>
          <input name="password" type="password" required style="width:100%; padding:8px; margin:8px 0;"><br><br>
          <button type="submit" style="padding:10px 20px; background:#222; color:#fff; border:none; cursor:pointer;">
            Login
          </button>
        </form>
        <br><a href="/auth/register-page">Don't have an account? Register</a>
      </body>
    </html>
    """


# ─── Login (POST) ──────────────────────────────────────────────
@router.post("/login")
def login(
    request: Request,
    username: str = Form(...),
    password: str = Form(...),
    db: Session = Depends(get_db)
):
    # 1. Find user by username
    user = db.query(User).filter(User.username == username).first()

    # 2. Verify user exists and password is correct
    if not user or not bcrypt_lib.checkpw(password.encode('utf-8'), user.password.encode('utf-8')):
        response = RedirectResponse(
            url="/auth/login-page?error=Invalid+username+or+password",
            status_code=302
        )
        _set_admin_cookie(response, False)
        return response

    # 3. Save user info into the session
    request.session["user_id"]   = user.id
    request.session["username"]  = user.username
    request.session["role"]      = user.role.value  # "user" or "super_admin"

    # 4. Redirect based on role
    if user.is_super_admin():
        response = RedirectResponse(url="/admin/dashboard", status_code=302)
        _set_admin_cookie(response, True)
        return response
    else:
        response = RedirectResponse(url="/", status_code=302)
        _set_admin_cookie(response, False)
        return response


# ─── Logout ────────────────────────────────────────────────────
@router.get("/logout")
def logout(request: Request):
    request.session.clear()  # Wipe the session completely
    response = RedirectResponse(url="/auth/login-page", status_code=302)
    _set_admin_cookie(response, False)
    return response


@router.api_route("/api/login", methods=["POST", "OPTIONS"], include_in_schema=False)
def api_login(
    payload: AdminLoginPayload,
    request: Request,
    db: Session = Depends(get_db)
):
    # Optional: FastAPI will automatically respond to OPTIONS via CORSMiddleware.

    user = db.query(User).filter(User.email == payload.email).first()

    if not user or not bcrypt_lib.checkpw(payload.password.encode('utf-8'), user.password.encode('utf-8')):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password.",
        )

    if not user.is_super_admin():
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="This account does not have admin access.",
        )

    request.session["user_id"] = user.id
    request.session["username"] = user.username
    request.session["role"] = user.role.value

    response = JSONResponse({"user": serialize_user(user)})
    _set_admin_cookie(response, True)
    return response


@router.get("/api/me")
def api_me(request: Request, db: Session = Depends(get_db)):
    user_id = request.session.get("user_id")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated.",
        )

    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        request.session.clear()
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Session is invalid.",
        )

    if not user.is_super_admin():
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="This account does not have admin access.",
        )

    return {"user": serialize_user(user)}


@router.post("/api/logout")
def api_logout(request: Request):
    request.session.clear()
    response = JSONResponse({"success": True})
    _set_admin_cookie(response, False)
    return response


# ─── Register Page (GET) ───────────────────────────────────────
@router.get("/register-page", response_class=HTMLResponse)
def register_page(request: Request):
    error = request.query_params.get("error", "")
    error_html = f'<p style="color:red;">{error}</p>' if error else ""
    return f"""
    <html>
      <body style="font-family: sans-serif; padding: 40px; max-width: 400px;">
        <h2>📝 Register</h2>
        {error_html}
        <form method="POST" action="/auth/register">
          <label>Username</label><br>
          <input name="username" type="text" required style="width:100%; padding:8px; margin:8px 0;"><br>
          <label>Email</label><br>
          <input name="email" type="email" required style="width:100%; padding:8px; margin:8px 0;"><br>
          <label>Password</label><br>
          <input name="password" type="password" required style="width:100%; padding:8px; margin:8px 0;"><br><br>
          <button type="submit" style="padding:10px 20px; background:#222; color:#fff; border:none; cursor:pointer;">
            Register
          </button>
        </form>
        <br><a href="/auth/login-page">Already have an account? Login</a>
      </body>
    </html>
    """


# ─── Register (POST) ───────────────────────────────────────────
@router.post("/register")
def register(
    request: Request,
    username: str = Form(...),
    email: str    = Form(...),
    password: str = Form(...),
    db: Session   = Depends(get_db)
):
    # Check if username or email already exists
    existing = db.query(User).filter(
        (User.username == username) | (User.email == email)
    ).first()

    if existing:
        return RedirectResponse(
            url="/auth/register-page?error=Username+or+email+already+exists",
            status_code=302
        )

    # Hash the password before storing
    hashed_password = bcrypt.hash(password)

    # New users are always "user" role by default (never super_admin)
    new_user = User(
        username=username,
        email=email,
        password=hashed_password,
        role=UserRole.user  # Default role — safe!
    )

    db.add(new_user)
    db.commit()

    return RedirectResponse(
        url="/auth/login-page?error=Registration+successful!+Please+login.",
        status_code=302
    )
