"""
Smart Healthcare - AI Prediction Microservice
------------------------------------------------
A lightweight rule-based "risk score" engine that estimates a patient's
general health risk from basic vitals and reported symptoms.

This is intentionally rule-based (not a trained ML model) so it can run
with zero external dependencies or datasets. It's built so the scoring
function can later be swapped for a trained scikit-learn/TensorFlow model
without changing the Flask API contract.

Run:
    pip install -r requirements.txt
    python app.py
Service listens on http://localhost:8000
"""

from flask import Flask, request, jsonify
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

# Symptoms that meaningfully raise concern when self-reported.
HIGH_WEIGHT_SYMPTOMS = {
    "chest pain": 25,
    "shortness of breath": 20,
    "severe headache": 15,
    "fainting": 20,
    "blurred vision": 10,
    "numbness": 15,
}
LOW_WEIGHT_SYMPTOMS = {
    "fatigue": 5,
    "fever": 5,
    "cough": 3,
    "nausea": 4,
    "dizziness": 8,
    "joint pain": 4,
}
ALL_SYMPTOM_WEIGHTS = {**HIGH_WEIGHT_SYMPTOMS, **LOW_WEIGHT_SYMPTOMS}


def score_age(age):
    if age is None:
        return 0
    if age >= 65:
        return 20
    if age >= 45:
        return 12
    if age >= 30:
        return 5
    return 0


def score_bmi(bmi):
    if bmi is None:
        return 0
    if bmi >= 35:
        return 18
    if bmi >= 30:
        return 12
    if bmi >= 25:
        return 6
    if bmi < 18.5:
        return 6  # underweight also carries some risk
    return 0


def score_blood_pressure(bp):
    """bp expected as a dict {systolic, diastolic} or a '120/80' string."""
    if not bp:
        return 0
    try:
        if isinstance(bp, str):
            systolic, diastolic = [int(x) for x in bp.split("/")]
        else:
            systolic = int(bp.get("systolic", 0))
            diastolic = int(bp.get("diastolic", 0))
    except (ValueError, AttributeError, TypeError):
        return 0

    if systolic >= 160 or diastolic >= 100:
        return 25
    if systolic >= 140 or diastolic >= 90:
        return 15
    if systolic >= 130 or diastolic >= 85:
        return 8
    return 0


def score_blood_sugar(mg_dl):
    if mg_dl is None:
        return 0
    if mg_dl >= 200:
        return 20
    if mg_dl >= 140:
        return 12
    if mg_dl >= 100:
        return 5
    return 0


def score_symptoms(symptoms):
    if not symptoms:
        return 0
    total = 0
    for raw in symptoms:
        key = str(raw).strip().lower()
        total += ALL_SYMPTOM_WEIGHTS.get(key, 2)  # small default weight for unlisted symptoms
    return total


def score_smoker(smoker):
    return 10 if smoker else 0


def classify(score):
    if score >= 60:
        return "high"
    if score >= 30:
        return "moderate"
    return "low"


def build_recommendations(level, symptoms):
    symptoms = [s.lower() for s in (symptoms or [])]
    tips = []

    if level == "high":
        tips.append("Book an appointment with a doctor as soon as possible.")
        if "chest pain" in symptoms or "shortness of breath" in symptoms:
            tips.append("If symptoms are severe or sudden, seek emergency care immediately.")
    elif level == "moderate":
        tips.append("Consider scheduling a check-up within the next 1-2 weeks.")
        tips.append("Monitor your symptoms and note any changes.")
    else:
        tips.append("No urgent action needed. Keep up routine check-ups.")

    tips.append("This is an automated estimate, not a medical diagnosis.")
    return tips


@app.route("/predict", methods=["POST"])
def predict():
    data = request.get_json(silent=True) or {}

    age = data.get("age")
    bmi = data.get("bmi")
    blood_pressure = data.get("bloodPressure")
    blood_sugar = data.get("bloodSugar")
    symptoms = data.get("symptoms", [])
    smoker = data.get("smoker", False)

    breakdown = {
        "age": score_age(age),
        "bmi": score_bmi(bmi),
        "bloodPressure": score_blood_pressure(blood_pressure),
        "bloodSugar": score_blood_sugar(blood_sugar),
        "symptoms": score_symptoms(symptoms),
        "smoker": score_smoker(smoker),
    }

    raw_score = sum(breakdown.values())
    risk_score = min(raw_score, 100)  # cap at 100
    risk_level = classify(risk_score)
    recommendations = build_recommendations(risk_level, symptoms)

    return jsonify(
        {
            "riskScore": risk_score,
            "riskLevel": risk_level,
            "breakdown": breakdown,
            "recommendations": recommendations,
        }
    )


@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "ok", "service": "python-prediction-service"})


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000, debug=True)
