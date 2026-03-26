# AVDS Dog Matching + Adoption Risk

This repo contains a small, runnable starter implementation of:
- `DOG-OWNER MATCHING MODEL`: ranks top dog matches with interpretable “why” reasons
- `ADOPTION RISK / RETURN PREDICTION MODEL`: predicts likelihood of return-risk (0-1)

Models are trained on a synthetic dataset generator (since real shelter data is not provided).

## Quick start

1. Install dependencies:
   - `pip install -r requirements.txt`

2. Train models:
   - `python train_models.py`

3. Run API:
   - `python run_server.py`

4. Test endpoints:
   - `POST http://localhost:8000/match_dogs`
   - `POST http://localhost:8000/predict_risk`

Sample requests are in `examples/`.

## Notes

- If artifacts do not exist, the API falls back to a rules-only scoring model.
- A feedback endpoint (`POST /feedback`) logs outcomes to support a feedback loop.

