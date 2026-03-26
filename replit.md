# PawMatch — Dog Adoption Matching App

## Overview
A full-stack dog adoption matching app. A modern web frontend (served by FastAPI) lets users describe their lifestyle, then calls a machine learning API that ranks shelter dogs by compatibility and provides adoption risk assessments.

## Architecture
- **Language:** Python 3.12
- **Framework:** FastAPI + Uvicorn (dev) / Gunicorn + UvicornWorker (prod)
- **Frontend:** Vanilla HTML/CSS/JS served as static files from FastAPI
- **ML:** scikit-learn (Logistic Regression), pandas, numpy, joblib
- **Port:** 5000 (webview workflow)

## Project Structure
- `dogmatch/` — Core Python package
  - `api.py` — FastAPI app, static file mount, REST endpoints
  - `pipeline.py` — Feature engineering, synthetic data generation, model training, prediction
- `static/` — Frontend assets
  - `index.html` — Single-page app shell with navigation
  - `style.css` — Modern design system (amber/teal palette, cards, responsive)
  - `app.js` — Dog catalog (18 dogs), matching form logic, risk check, results rendering
- `train_models.py` — CLI to generate synthetic data and train models (saves to `artifacts/`)
- `run_server.py` — Dev server entry point (uvicorn, port 5000, reload=True)
- `requirements.txt` — Python dependencies
- `examples/` — Sample JSON request bodies

## Frontend Pages
- **Home** — Hero section, feature cards, dog preview grid
- **Match Dogs** — Lifestyle form → POST `/match_dogs` → Top 5 match cards with scores
- **Adoption Risk** — Profile form + dog picker → POST `/predict_risk` → Risk gauge + explanation

## API Endpoints
- `GET /` — Serves the PawMatch frontend (index.html)
- `GET /health` — Health check
- `POST /match_dogs` — Match user against dog catalog
- `POST /predict_risk` — Predict return risk for user + dog pair
- `POST /feedback` — Append adoption outcome feedback

## Setup
1. `pip install -r requirements.txt`
2. `python train_models.py` (generates `artifacts/` directory)
3. `python run_server.py`

## Workflow
- **Start application** — `python run_server.py` on port 5000 (webview)

## Deployment
- Target: autoscale
- Build: `pip install -r requirements.txt && python train_models.py`
- Run: `gunicorn --bind=0.0.0.0:5000 --workers=2 dogmatch.api:app -k uvicorn.workers.UvicornWorker`
