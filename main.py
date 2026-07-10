import os

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.sessions import SessionMiddleware
import uvicorn

from database import engine, Base, SessionLocal
from auth import router as auth_router
from admin import router as admin_router
from models import User, UserRole
import bcrypt as bcrypt_lib

# Create all tables on startup
Base.metadata.create_all(bind=engine)


def seed_super_admin():
    username = os.getenv("ADMIN_USERNAME")
    email = os.getenv("ADMIN_EMAIL")
    password = os.getenv("ADMIN_PASSWORD")

    if not username or not email or not password:
        print("[INFO] Super admin seed skipped. ADMIN_USERNAME, ADMIN_EMAIL, or ADMIN_PASSWORD missing.")
        return

    db = SessionLocal()
    try:
        existing = db.query(User).filter(User.email == email).first()

        if existing:
            print(f"[INFO] Super admin already exists: {email}")
            return

        hashed = bcrypt_lib.hashpw(password.encode("utf-8"), bcrypt_lib.gensalt()).decode("utf-8")

        admin = User(
            username=username,
            email=email,
            password=hashed,
            role=UserRole.super_admin,
        )

        db.add(admin)
        db.commit()
        print(f"[OK] Super admin created: {email}")
    finally:
        db.close()


seed_super_admin()

app = FastAPI(title="Ecommerce App with Admin Protection")

allowed_origins = [
    origin.strip()
    for origin in os.getenv(
        "ALLOWED_ORIGINS",
        "http://localhost:3000,http://localhost:3001,http://127.0.0.1:3000,http://127.0.0.1:3001",
    ).split(",")
    if origin.strip()
]
allowed_origin_regex = os.getenv(
    "ALLOWED_ORIGIN_REGEX",
    r"https://ascend-[a-z0-9-]+\.vercel\.app",
)

print(f"[OK] ALLOWED ORIGINS: {allowed_origins}")
print(f"[OK] ALLOWED ORIGIN REGEX: {allowed_origin_regex}")

# ─── Middleware (Order Matters - CORS should be first) ─────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_origin_regex=allowed_origin_regex,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS", "PATCH"],
    allow_headers=["*"],
    max_age=3600,
)

app.add_middleware(
    SessionMiddleware,
    secret_key=os.getenv("SESSION_SECRET", "CHANGE_THIS_TO_A_LONG_RANDOM_SECRET_KEY_123!"),
)

# NOTE: If you see CORS errors like:
# "Response to preflight request doesn't pass access control check: No 'Access-Control-Allow-Origin' header"
# then your frontend origin is not included in ALLOWED_ORIGINS.
# Add your Next.js origin (e.g. http://localhost:3001) to python-backend/.env as ALLOWED_ORIGINS.


@app.middleware("http")
async def protect_admin_routes(request: Request, call_next):
    path = request.url.path
    if not path.startswith("/admin"):
        return await call_next(request)

    db = SessionLocal()
    try:
        user_id = request.session.get("user_id")
        if not user_id:
            return RedirectResponse(url="/auth/login-page?error=Please+login+to+continue", status_code=302)

        user = db.query(User).filter(User.id == user_id).first()
        if not user or not user.is_super_admin():
            return RedirectResponse(url="/?error=Access+Denied.+Admins+only.", status_code=302)

        return await call_next(request)
    finally:
        db.close()


# ─── Routers ───────────────────────────────────────────────────
app.include_router(auth_router, prefix="/auth", tags=["Authentication"])
app.include_router(admin_router, prefix="/admin", tags=["Admin"])


# ─── Public Home Page ──────────────────────────────────────────
@app.get("/", response_class=HTMLResponse)
def home():
    return """
    <html>
      <body style="font-family: sans-serif; padding: 40px;">
        <h1>🛒 Ecommerce Store</h1>
        <p>Welcome! This is the public page.</p>
        <a href="/auth/login-page">🔐 Login</a> |
        <a href="/admin/dashboard">🛠 Admin Panel</a>
      </body>
    </html>
    """


if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
