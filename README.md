# MediSlot — Smart Healthcare Appointment & Prediction Platform

A full-stack appointment booking system with an AI-powered disease-risk
check, built as **MERN** (MongoDB, Express, React, Node) plus a small
**Python (Flask)** microservice for the prediction engine.

```
smart-healthcare/
├── backend/           Node.js + Express REST API (MongoDB via Mongoose)
├── python-service/    Flask AI microservice (rule-based risk scoring)
└── frontend/          React single-page app
```

## How the pieces talk to each other

```
React (3000)  ──HTTP──▶  Node/Express API (5000)  ──HTTP──▶  Flask AI service (8000)
                              │
                              ▼
                          MongoDB
```

The React app never calls the Python service directly — it always goes
through the Node API (`/api/predict/risk`), which forwards the request.
This keeps one auth layer, one CORS config, and lets you swap the Python
engine for a real ML model later without touching the frontend.

## 1. Backend (Node/Express)

```bash
cd backend
cp .env.example .env      # edit MONGO_URI / JWT_SECRET if needed
npm install
npm run dev                # or: npm start
```
Runs on **http://localhost:5000**. Requires a running MongoDB instance
(local `mongod` or a MongoDB Atlas URI in `.env`).

## 2. AI prediction service (Python/Flask)

```bash
cd python-service
python -m venv venv && source venv/bin/activate   # optional but recommended
pip install -r requirements.txt
python app.py
```
Runs on **http://localhost:8000**. This is a **rule-based** scorer (age,
BMI, blood pressure, blood sugar, symptoms, smoking) — no dataset or
training step needed. The scoring function in `app.py` is isolated
(`score_age`, `score_bmi`, etc.) so it's a drop-in spot to later plug in a
trained scikit-learn/TensorFlow model behind the same `/predict` contract.

## 3. Frontend (React)

```bash
cd frontend
cp .env.example .env       # points to the backend API
npm install
npm start
```
Runs on **http://localhost:3000**.

## Core features implemented

- **Auth**: JWT-based register/login for two roles, `patient` and `doctor`.
- **Doctor directory**: search by specialization, see fee & experience.
- **Scheduling**: doctors publish open slots per date; patients book an
  open slot; the slot is locked so it can't be double-booked.
- **Appointments**: patients see their bookings and can cancel; doctors
  can confirm/complete appointments from the same table.
- **AI risk check**: patients fill in vitals + symptoms, the Flask service
  returns a 0–100 risk score, a low/moderate/high label, a score
  breakdown, and plain-language recommendations.

## Suggested next steps

- Add a doctor-facing "publish slots" UI (the API route `PUT
  /api/doctors/:id/slots` already exists, it just isn't wired to a page
  yet).
- Swap the Flask rule-based scorer for a trained model (e.g. logistic
  regression on a public diabetes/heart-disease dataset) — the API
  contract (`POST /predict` → `{riskScore, riskLevel, breakdown,
  recommendations}`) won't need to change.
- Add MongoDB indexes on `Appointment.date` and `Doctor.specialization`
  once real data volume shows up.
- Add PHP later if you specifically need it for a separate reporting
  module or CMS piece — it wasn't included here since MERN + Python
  already covers the full booking + AI flow end to end.
