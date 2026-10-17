# TimeCapsule React Native + FastAPI starter

This project is a runnable foundation for the TimeCapsule travel-memory app.

## Stack

- Expo + React Native + TypeScript
- FastAPI + SQLAlchemy
- SQLite by default for demos; PostgreSQL can be enabled with `DATABASE_URL`
- Firebase authentication is intentionally left as an integration point

## Run the API

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn main:app --reload --port 8000
```

The API is available at `http://127.0.0.1:8000` and its interactive docs are at `/docs`.

## Run the Expo app

```bash
cd mobile
npm install
npx expo start
```

Use Expo Go for the UI demo. Camera, microphone, HealthKit, and Apple Sign In require an Expo development build and native configuration.

For a physical phone, set `API_BASE_URL` in `mobile/.env` to the computer's LAN address, for example `http://192.168.1.25:8000`.

## Demo account

The account screen creates a local demo account through the API. Verification accepts `123456` until Firebase/email/SMS verification is configured.

## Production integration points

- Replace demo verification with Firebase Auth email/phone verification.
- Verify Firebase ID tokens in FastAPI and use the Firebase UID as the user identity.
- Add Firebase Storage or S3-compatible media uploads; SQL should store media metadata and URLs, not large video blobs.
- Change `DATABASE_URL` to PostgreSQL for shared multi-user data.
- Add Expo development-build modules for camera recording and HealthKit step data.
