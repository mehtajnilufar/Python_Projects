from flask import Flask, request, jsonify
import numpy as np
import pickle

app = Flask(__name__)

# Load ML model
try:
    model = pickle.load(open("model.pkl", "rb"))
    print("✅ Model loaded successfully")
except:
    print("❌ ERROR: model.pkl not found. Run model_train.py first!")

@app.route("/", methods=["GET"])
def home():
    return jsonify({"message": "Fraud Detection API is running ✅"})

@app.route("/predict", methods=["POST"])
def predict():
    try:
        data = request.json["features"]     # expecting a list of numbers
        data = np.array(data).reshape(1, -1)
        prediction = model.predict(data)[0]

        if prediction == 1:
            return jsonify({"fraud": True, "message": "⚠️ Fraudulent Transaction"})
        else:
            return jsonify({"fraud": False, "message": "✅ Genuine Transaction"})

    except Exception as e:
        return jsonify({"error": str(e), "message": "Invalid input format"})

if __name__ == "__main__":
    print("✅ Starting Flask API...")
    app.run(debug=True)
