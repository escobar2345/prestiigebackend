from fastapi import APIRouter, Depends, Request, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime

from database import get_db
from models import User, UserRole

router = APIRouter()


# ════════════════════════════════════════════════════════════════
#  RESPONSE MODELS — For frontend consumption
# ════════════════════════════════════════════════════════════════
class UserDTO(BaseModel):
    id: int
    username: str
    email: str
    role: str
    created_at: Optional[str] = None

    class Config:
        from_attributes = True


class AdminKPIResponse(BaseModel):
    """Dashboard KPI metrics"""
    total_partners: str
    active_partners: str
    pending_payouts: str
    total_revenue: str
    total_bookings: int
    pending_activations: int


class AdminStatsResponse(BaseModel):
    """Overall admin statistics"""
    total_users: int
    total_partners: int
    total_referrals: int
    total_payouts: str
    pending_payouts: str
    system_status: str


# ════════════════════════════════════════════════════════════════
#  CORE GUARD FUNCTION — This is the protection engine
#  Call this at the top of ANY route you want to protect.
# ════════════════════════════════════════════════════════════════
def require_super_admin(request: Request, db: Session):
    """
    Checks if the current session user is a super_admin.
    Returns the User object if authorized.
    Raises HTTPException if not logged in or not super_admin.
    
    Usage inside any route:
        user = require_super_admin(request, db)
    """
    user_id = request.session.get("user_id")

    # Step 1: Not logged in at all → error
    if not user_id:
        raise HTTPException(status_code=401, detail="Not authenticated")

    # Step 2: Find the user in the database
    user = db.query(User).filter(User.id == user_id).first()

    # Step 3: User not found (deleted?) → clear session and error
    if not user:
        request.session.clear()
        raise HTTPException(status_code=401, detail="Session invalid")

    # Step 4: User exists but is NOT a super_admin → block access
    if not user.is_super_admin():
        raise HTTPException(status_code=403, detail="Access denied. Admin role required.")

    # Step 5: All checks passed → return the user
    return user


# ════════════════════════════════════════════════════════════════
#  ADMIN API ROUTES — All protected by require_super_admin()
# ════════════════════════════════════════════════════════════════

@router.get("/api/kpis")
def get_admin_kpis(request: Request, db: Session = Depends(get_db)):
    """Get main dashboard KPIs"""
    user = require_super_admin(request, db)
    
    # Count total users/partners
    total_users = db.query(User).count()
    active_users = db.query(User).filter(User.role == UserRole.user).count()
    
    return {
        "total_partners": "1,248",
        "active_partners": "892",
        "pending_payouts": "₦ 1,240,500",
        "total_revenue": "₦ 18.7M",
        "total_bookings": 12500,
        "pending_activations": 856,
        "total_users": total_users,
        "active_users": active_users
    }


@router.get("/api/stats")
def get_admin_stats(request: Request, db: Session = Depends(get_db)):
    """Get overall system statistics"""
    user = require_super_admin(request, db)
    
    total_users = db.query(User).count()
    total_partners = db.query(User).filter(User.role == UserRole.user).count()
    
    return {
        "total_users": total_users,
        "total_partners": total_partners,
        "total_referrals": 156,
        "total_payouts": "₦ 5,240,500",
        "pending_payouts": "₦ 1,240,500",
        "system_status": "Operational"
    }


@router.get("/api/users")
def get_all_users(
    request: Request,
    db: Session = Depends(get_db),
    skip: int = 0,
    limit: int = 100
):
    """Get all users with pagination"""
    user = require_super_admin(request, db)
    
    users = db.query(User).offset(skip).limit(limit).all()
    return [
        {
            "id": u.id,
            "username": u.username,
            "email": u.email,
            "role": u.role.value,
            "created_at": u.created_at.isoformat() if u.created_at else None
        }
        for u in users
    ]


@router.get("/api/partners")
def get_all_partners(request: Request, db: Session = Depends(get_db)):
    """Get all partners/non-admin users"""
    user = require_super_admin(request, db)
    
    partners = db.query(User).filter(User.role == UserRole.user).all()
    return [
        {
            "id": p.id,
            "name": p.username,
            "email": p.email,
            "joinedDate": p.created_at.strftime("%b %d, %Y") if p.created_at else "N/A",
            "referrals": 0,  # This would come from a referrals table
            "amount": "₦20,000",
            "status": "Active"
        }
        for p in partners
    ]


@router.get("/api/revenue-trend")
def get_revenue_trend(request: Request, db: Session = Depends(get_db)):
    """Get revenue data for charts"""
    user = require_super_admin(request, db)
    
    return {
        "series": [4.2, 5.1, 4.6, 6.3, 7.8, 6.9, 8.4, 9.1, 7.5, 8.9, 9.6, 11.2],
        "months": ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"],
        "legend": "Revenue (₦M)"
    }


@router.get("/api/referrals-trend")
def get_referrals_trend(request: Request, db: Session = Depends(get_db)):
    """Get referrals data for charts"""
    user = require_super_admin(request, db)
    
    return {
        "series": [22, 31, 28, 45, 38, 52, 48, 61],
        "weeks": ["W1", "W2", "W3", "W4", "W5", "W6", "W7", "W8"],
        "legend": "Referrals"
    }


@router.get("/api/payouts")
def get_pending_payouts(request: Request, db: Session = Depends(get_db)):
    """Get pending payouts list"""
    user = require_super_admin(request, db)
    
    # Mock data - replace with actual DB queries
    return [
        {
            "partner": "Ibrahim Lawal",
            "email": "ibrahim@email.com",
            "amount": "₦20,000",
            "method": "Bank Transfer",
            "requestDate": "May 20, 2024",
            "status": "Pending"
        }
    ]


@router.get("/api/notifications-sent")
def get_notifications_history(request: Request, db: Session = Depends(get_db)):
    """Get notification history"""
    user = require_super_admin(request, db)
    
    return [
        {
            "title": "New Bonus",
            "audience": "All Partners",
            "sentDate": "May 20, 2024"
        },
        {
            "title": "System Maintenance",
            "audience": "All Partners",
            "sentDate": "May 20, 2024"
        }
    ]


@router.post("/api/send-notification")
def send_notification(
    request: Request,
    db: Session = Depends(get_db),
    title: str = None,
    message: str = None,
    audience: str = "all"
):
    """Send notification to partners"""
    user = require_super_admin(request, db)
    
    # TODO: Implement actual notification sending logic
    return {
        "success": True,
        "message": f"Notification sent to {audience}",
        "timestamp": datetime.now().isoformat()
    }


@router.put("/api/user/{user_id}/status")
def update_user_status(
    request: Request,
    user_id: int,
    db: Session = Depends(get_db),
    status: str = None
):
    """Update user/partner status (Active/Inactive/Suspended)"""
    admin = require_super_admin(request, db)
    
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # TODO: Add status field to User model if needed
    return {
        "success": True,
        "user_id": user_id,
        "status": status,
        "message": f"User status updated to {status}"
    }


@router.post("/api/process-payout")
def process_payout(
    request: Request,
    db: Session = Depends(get_db),
    partner_id: int = None,
    amount: str = None
):
    """Process payout for a partner"""
    admin = require_super_admin(request, db)
    
    # TODO: Implement payout processing logic
    return {
        "success": True,
        "partner_id": partner_id,
        "amount": amount,
        "status": "Processed",
        "timestamp": datetime.now().isoformat()
    }


@router.get("/api/services-breakdown")
def get_services_breakdown(request: Request, db: Session = Depends(get_db)):
    """Get breakdown of services"""
    user = require_super_admin(request, db)
    
    return {
        "services": [
            {"label": "Home Cleaning", "value": 42, "color": "#2563EB"},
            {"label": "Office Cleaning", "value": 26, "color": "#60A5FA"},
            {"label": "Laundry", "value": 18, "color": "#FBBF24"},
            {"label": "Other", "value": 14, "color": "#64748B"}
        ],
        "total": 100
    }


@router.get("/api/recent-activity")
def get_recent_activity(request: Request, db: Session = Depends(get_db)):
    """Get recent system activity"""
    user = require_super_admin(request, db)
    
    recent_users = db.query(User).order_by(User.created_at.desc()).limit(8).all()
    
    return [
        {
            "partner": u.username,
            "email": u.email,
            "joined": u.created_at.strftime("%b %d %Y") if u.created_at else "N/A",
            "referrals": 0,
            "earned": "₦ 0",
            "status": "Active"
        }
        for u in recent_users
    ]


@router.get("/dashboard", response_class=HTMLResponse)
def admin_dashboard_html(request: Request, db: Session = Depends(get_db)):
    """
    Main admin dashboard — ONLY super_admin can access this.
    Regular users are redirected away automatically.
    Returns HTML page that loads data from JSON API endpoints.
    """
    try:
        auth_result = require_super_admin(request, db)
        user = auth_result
    except HTTPException:
        return RedirectResponse(url="/?error=Access+Denied", status_code=302)

    # Return a minimal HTML page that redirects to the Next.js admin page
    # or serves a basic dashboard
    return """
    <html>
      <head>
        <title>Admin Dashboard</title>
        <style>
          body { font-family: sans-serif; padding: 40px; background: #f4f4f4; }
          .card { background: white; padding: 24px; border-radius: 8px; margin: 16px 0; box-shadow: 0 2px 8px rgba(0,0,0,0.1); }
          .badge { background: #e74c3c; color: white; padding: 4px 10px; border-radius: 4px; font-size: 12px; }
          .nav { background: #222; color: white; padding: 16px 40px; margin: -40px -40px 40px; display: flex; justify-content: space-between; }
          a { color: #3498db; text-decoration: none; }
          a:hover { text-decoration: underline; }
          .btn { padding: 10px 20px; background: #e74c3c; color: white; border: none; border-radius: 4px; cursor: pointer; text-decoration: none; }
        </style>
      </head>
      <body>
        <div class="nav">
          <span>🛒 Prestiige — <strong>Admin Panel</strong></span>
          <span>👤 """ + user.username + """ <span class="badge">SUPER ADMIN</span> | <a href="/auth/logout" style="color:#aaa;">Logout</a></span>
        </div>

        <h2>📊 Admin Dashboard</h2>

        <div class="card">
          <h3>✅ Access Granted</h3>
          <p>Welcome, <strong>""" + user.username + """</strong>! You have full admin access.</p>
        </div>

        <div class="card">
          <h3>🔧 API Endpoints Available</h3>
          <ul>
            <li><a href="/admin/api/kpis">📊 Get KPIs</a></li>
            <li><a href="/admin/api/stats">📈 Get Stats</a></li>
            <li><a href="/admin/api/users">👥 Get Users</a></li>
            <li><a href="/admin/api/partners">🤝 Get Partners</a></li>
            <li><a href="/admin/api/revenue-trend">💰 Revenue Trend</a></li>
            <li><a href="/admin/api/referrals-trend">📞 Referrals Trend</a></li>
            <li><a href="/admin/api/payouts">💸 Pending Payouts</a></li>
            <li><a href="/admin/api/notifications-sent">📬 Notifications</a></li>
            <li><a href="/admin/api/recent-activity">⏱️ Recent Activity</a></li>
          </ul>
        </div>

        <div class="card">
          <h3>🔐 Security Info</h3>
          <p>All API endpoints are protected and require super_admin role.</p>
        </div>
      </body>
    </html>
    """