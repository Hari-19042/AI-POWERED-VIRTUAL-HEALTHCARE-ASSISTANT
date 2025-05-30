from flask import Flask, render_template, request, jsonify
from flask_cors import CORS  # ✅ Import CORS to fix cross-origin issues
import speech_recognition as sr
import pandas as pd
import re

app = Flask(__name__)
CORS(app)  # ✅ Enable CORS for all routes

# ✅ Load dataset
csv_path = "D:\\trail\\csv_output\\med.csv"
try:
    df = pd.read_csv(csv_path, delimiter="\t")
except Exception:
    df = pd.read_csv(csv_path, delimiter=",")
    if df.shape[1] == 1:
        df = pd.read_csv(csv_path, delimiter="|")

# ✅ Clean column names
df.columns = df.columns.str.strip().str.lower()
required_columns = ["condition", "symptoms", "duration", "severity", "risk_factors", "suggested_action"]
missing_columns = set(required_columns) - set(df.columns)
if missing_columns:
    raise ValueError(f"❌ Missing required columns: {missing_columns}. Available columns: {df.columns}")

df["symptoms"] = df["symptoms"].astype(str).str.lower()

def extract_duration(text):
    """Extracts numeric duration from input text."""
    match = re.search(r"\d+", text)
    return int(match.group()) if match else None

def is_duration_valid(user_duration, duration_range):
    """Checks if user duration falls within the given range."""
    try:
        user_duration = int(user_duration)
        match = re.match(r"(\d+)-(\d+)", duration_range)
        if match:
            lower, upper = map(int, match.groups())
            return lower <= user_duration <= upper
        return user_duration == int(duration_range)
    except ValueError:
        return False

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/start', methods=['GET'])
def start_chat():
    return jsonify({"response": "Hello, I'm Dr. Mira. How can I assist you today?"})

@app.route('/consult', methods=['POST'])
def process_symptom():
    symptom = request.json.get('symptom', '').strip().lower()
    if not symptom:
        return jsonify({"response": "Please provide a symptom."})
    
    matched_conditions = df[df["symptoms"].str.contains(symptom, na=False, regex=True)]
    if matched_conditions.empty:
        return jsonify({"response": "I couldn't find any condition related to that symptom."})
    
    return jsonify({"response": f"I found {len(matched_conditions)} conditions related to {symptom}. For how many days have you had this symptom?"})

@app.route('/duration', methods=['POST'])
def process_duration():
    duration_text = request.json.get('duration', '').strip()
    duration_number = extract_duration(duration_text)
    
    if not duration_number:
        return jsonify({"response": "I didn't hear a valid duration. Please try again."})
    
    matched_conditions = df[df["duration"].apply(lambda x: is_duration_valid(duration_number, str(x)))]
    
    if matched_conditions.empty:
        return jsonify({"response": "No conditions match that duration range. Please consult a doctor."})
    
    return jsonify({"response": f"{len(matched_conditions)} conditions match your symptom and duration. Is it mild, moderate, or severe?"})

@app.route('/severity', methods=['POST'])
def process_severity():
    severity = request.json.get('severity', '').strip().lower()
    if not severity:
        return jsonify({"response": "Please specify mild, moderate, or severe."})
    
    matched_conditions = df[df["severity"].str.contains(severity, na=False, regex=True)]
    
    if matched_conditions.empty:
        return jsonify({"response": "No conditions match that severity level. Please consult a doctor."})
    
    return jsonify({"response": f"{len(matched_conditions)} conditions match your symptom, duration, and severity. Do you have any risk factors?"})

@app.route('/risk', methods=['POST'])
def process_risk():
    user_risk_factor = request.json.get('risk_factor', '').strip().lower()
    
    matched_conditions = df[df["risk_factors"].str.contains(user_risk_factor, na=False, regex=True)]
    
    if matched_conditions.empty:
        return jsonify({"response": "I couldn't find a perfect match. However, please consult a doctor."})
    
    condition_name = matched_conditions.iloc[0]["condition"]
    suggested_action = matched_conditions.iloc[0]["suggested_action"]
    
    return jsonify({"response": f"It looks like you might have {condition_name}. {suggested_action}"})

if __name__ == "__main__":
    app.run(debug=True, host="127.0.0.1", port=5000)
