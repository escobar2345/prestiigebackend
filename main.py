import os

from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.sessions import SessionMiddleware
import uvicorn

from database import engine, Base
from auth import router as auth_router
from admin import router as admin_router

# Create all tables on startup
Base.metadata.create_all(bind=engine)

app = FastAPI(title="Ecommerce App with Admin Protection")

allowed_origins = [
    origin.strip()
    for origin in os.getenv(
        "ALLOWED_ORIGINS",
        "http://localhost:3000,http://localhost:3001,http://127.0.0.1:3000,http://127.0.0.1:3001",
    ).split(",")
    if origin.strip()
]

print(f"[OK] ALLOWED ORIGINS: {allowed_origins}")

# ─── Middleware (Order Matters - CORS should be first) ─────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
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
