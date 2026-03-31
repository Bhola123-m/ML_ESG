"""
FastAPI Server for ESG Platform
Loads dataset automatically from Streamlit output
"""

from fastapi import FastAPI
import pandas as pd
import os
from api.esg_api import api as esg_api

app = FastAPI(title="ESG Risk Intelligence API")

DATA_PATH = "data/final_df.csv"

# 🚀 Load dataset when server starts
@app.on_event("startup")
def load_dataset():
    if os.path.exists(DATA_PATH):
        df = pd.read_csv(DATA_PATH)
        esg_api.set_data(df)   # Load into API memory
        print("✅ ESG dataset loaded into API")
    else:
        print("❌ ERROR: Run Streamlit Step-4 first to generate dataset")

# Home endpoint
@app.get("/")
def root():
    return {"message":"ESG API is running "}

# --- ESG ENDPOINTS ---

@app.get("/api/v1/risk/all")
def risk_all():
    return esg_api.get_risk_all()

@app.get("/api/v1/risk/sector")
def risk_sector():
    return esg_api.get_risk_sector()

@app.get("/api/v1/model/compare")
def model_compare():
    return esg_api.get_model_compare()

@app.get("/api/v1/risk/top")
def risk_top(n:int=50):
    return esg_api.get_risk_top(n)
