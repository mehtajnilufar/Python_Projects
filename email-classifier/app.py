# app.py
from fastapi import FastAPI, File, UploadFile, HTTPException
from pydantic import BaseModel
import joblib
import uvicorn
import pandas as pd
from typing import List, Optional
import os
from tempfile import NamedTemporaryFile

MODEL_PATH = os.getenv('MODEL_PATH', 'email_classifier.joblib')

app = FastAPI(title="Email Classifier API")

class PredictRequest(BaseModel):
    texts: List[str]

class PredictResponse(BaseModel):
    labels: List[str]
    confidences: Optional[List[float]] = None

# load model at startup
model = None
def load_model(path=MODEL_PATH):
    global model
    if os.path.exists(path):
        model = joblib.load(path)
    else:
        model = None

@app.on_event("startup")
def startup_event():
    load_model()

@app.get("/health")
def health():
    return {"status": "ok", "model_loaded": model is not None}

@app.post("/predict", response_model=PredictResponse)
def predict(req: PredictRequest):
    if model is None:
        raise HTTPException(status_code=503, detail="Model not available. Train or upload model first.")
    texts = req.texts
    preds = model.predict(texts)
    # confidence: if estimator supports predict_proba
    confidences = None
    if hasattr(model, "predict_proba"):
        probs = model.predict_proba(texts)
        confidences = [float(max(p)) for p in probs]
    elif hasattr(model.named_steps['clf'], 'decision_function'):
        try:
            scores = model.decision_function(texts)
            # convert to pseudo-confidence
            import numpy as np
            if scores.ndim == 1:
                confidences = [float(abs(s)) for s in scores]
            else:
                confidences = [float(max(s)) for s in scores]
        except Exception:
            confidences = None
    return {"labels": preds.tolist(), "confidences": confidences}

@app.post("/upload-model")
async def upload_model(file: UploadFile = File(...)):
    # accept a joblib file and replace current model
    suffix = os.path.splitext(file.filename)[1]
    if suffix not in ('.joblib', '.pkl'):
        raise HTTPException(status_code=400, detail="Upload .joblib or .pkl file")
    tmp = NamedTemporaryFile(delete=False, suffix=suffix)
    content = await file.read()
    tmp.write(content)
    tmp.flush()
    tmp.close()
    # replace model file
    target = MODEL_PATH
    os.replace(tmp.name, target)
    load_model(target)
    return {"status":"uploaded", "model_path": target}

@app.post("/train-from-csv")
async def train_from_csv(file: UploadFile = File(...), model_type: Optional[str] = 'nb'):
    # accepts CSV with text,label, trains and saves model
    tmp = NamedTemporaryFile(delete=False, suffix=".csv")
    content = await file.read()
    tmp.write(content)
    tmp.flush()
    tmp.close()
    import subprocess
    cmd = ["python", "train_model.py", "--data", tmp.name, "--out", MODEL_PATH, "--model", model_type]
    # run training (blocking)
    proc = subprocess.run(cmd, capture_output=True, text=True)
    if proc.returncode != 0:
        raise HTTPException(status_code=500, detail=f"Training failed: {proc.stderr}")
    load_model(MODEL_PATH)
    return {"status":"trained", "stdout": proc.stdout}

if __name__ == "__main__":
    uvicorn.run("app:app", host="0.0.0.0", port=8000, reload=True)
