# NGROK_CORS_FIX_INSTRUCTIONS.md

## Why you see:
CORS preflight error: "No 'Access-Control-Allow-Origin' header".

## What must be true
FastAPI CORS allowlist uses `ALLOWED_ORIGINS` from `python-backend/.env`.
Your browser Origin during dev is `http://localhost:3001` (from your console).

## Fix
1) Edit: `python-backend/.env`

Set (exact values):

ALLOWED_ORIGINS=http://localhost:3001,https://virtual-femininely-jinny.ngrok-free.dev
SESSION_SECRET=CHANGE_THIS_TO_A_LONG_RANDOM_SECRET_KEY_123!

(Keep any existing variables; just ensure ALLOWED_ORIGINS includes localhost:3001.)

2) Restart backend
- Stop FastAPI
- Start FastAPI again (so it reloads `.env`)

3) Restart ngrok
- Stop tunnel
- Start tunnel again (or ensure the same tunnel is still forwarding to port 8000)

4) Restart Next.js
- `npm run dev`

## Verification
Open your browser console again and retry login.

Also verify preflight headers:
In DevTools → Network → click the failed request → check Headers for:
- `Access-Control-Allow-Origin: http://localhost:3001`

If it still fails with the same message, your backend process is NOT reloading the `.env` (restart didn’t happen) or ngrok isn’t pointing to the correct backend port.

