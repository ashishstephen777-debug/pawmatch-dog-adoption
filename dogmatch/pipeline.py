from __future__ import annotations

import json
import math
import os
import random
import time
from dataclasses import dataclass
from typing import Any, Dict, Iterable, List, Optional, Tuple

import joblib
import numpy as np
import pandas as pd
from sklearn.base import BaseEstimator
from sklearn.compose import ColumnTransformer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import roc_auc_score
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler

# -----------------------------
# Feature engineering utilities
# -----------------------------


def _sigmoid(x: float) -> float:
    # Numerically stable sigmoid
    if x >= 0:
        z = math.exp(-x)
        return 1 / (1 + z)
    z = math.exp(x)
    return z / (1 + z)


def _categorical_age_bucket(age_years: float) -> str:
    if age_years < 1.0:
        return "puppy"
    if age_years < 8.0:
        return "adult"
    return "senior"


def _preferred_age_target(preferred_age: str) -> float:
    # Used for age proximity
    return {
        "puppy": 0.5,
        "young_adult": 4.0,
        "adult": 6.0,
        "senior": 11.0,
    }.get(preferred_age, 6.0)


def _energy_target(activity_level: str) -> int:
    # low=1, medium=2, high=3
    return {"low": 1, "medium": 2, "high": 3}.get(activity_level, 2)


def _energy_value(energy_level: str) -> int:
    return {"low": 1, "medium": 2, "high": 3}.get(energy_level, 2)


def _temperament_match_score(preferred: str, dog: str) -> float:
    if preferred == dog:
        return 1.0
    # Soft matching rules for common real-world pairings
    if preferred == "friendly" and dog in {"friendly", "shy"}:
        return 0.85
    if preferred == "calm" and dog in {"shy", "friendly", "calm"}:
        return 0.8
    if preferred in {"energetic", "playful"} and dog in {"energetic", "playful"}:
        return 0.95
    if dog == "aggressive":
        return 0.05
    # Default partial credit
    return 0.35


def _hypoallergenic_compat(allergies_level: str, hypoallergenic: bool) -> float:
    if allergies_level == "none":
        return 1.0
    if allergies_level == "mild":
        return 0.7 if hypoallergenic else 0.35
    if allergies_level == "severe":
        return 1.0 if hypoallergenic else 0.1
    return 0.6 if hypoallergenic else 0.3


def _energy_compat(activity_level: str, work_hours_away: float, dog_energy: str) -> float:
    # Two-step heuristic:
    # 1) hard schedule constraints
    # 2) softer activity alignment
    target = _energy_target(activity_level)
    dval = _energy_value(dog_energy)

    if work_hours_away >= 7:
        schedule_ok = {"low": 0.95, "medium": 0.6, "high": 0.25}.get(dog_energy, 0.5)
    elif work_hours_away >= 4:
        schedule_ok = {"low": 0.85, "medium": 0.7, "high": 0.4}.get(dog_energy, 0.6)
    else:
        schedule_ok = {"low": 0.75, "medium": 0.9, "high": 1.0}.get(dog_energy, 0.85)

    align = 1.0 - abs(target - dval) / 2.0  # 0..1
    return float(max(0.0, min(1.0, 0.6 * schedule_ok + 0.4 * align)))


def _training_compat(pet_experience: str, training_level: str, special_needs: int) -> float:
    exp = {"none": 0, "some": 1, "expert": 2}.get(pet_experience, 1)
    tl = {"low": 0, "medium": 1, "high": 2}.get(training_level, 1)

    # Base based on match between experience and training complexity
    base = 1.0 - abs(exp - tl) / 2.2
    base = float(max(0.0, min(1.0, base)))

    if special_needs == 1:
        # Special needs increase risk if experience is not expert
        if pet_experience == "expert":
            return float(max(0.2, min(1.0, base * 0.95)))
        return float(max(0.05, min(0.85, base * 0.65)))

    return float(max(0.0, min(1.0, base)))


def _kids_compat(kids_in_household: int, kid_compatibility: str) -> float:
    if kids_in_household == 0:
        return 1.0
    return {"high": 1.0, "medium": 0.6, "low": 0.15}.get(kid_compatibility, 0.5)


def _other_pets_compat(other_pets_in_household: int, other_pets_compatibility: str) -> float:
    if other_pets_in_household == 0:
        return 1.0
    return {"high": 1.0, "medium": 0.65, "low": 0.2}.get(other_pets_compatibility, 0.55)


def _budget_estimate(dog_size: str, special_needs: int, training_level: str) -> float:
    # Toy estimate (monthly). In production, replace with empirically derived shelter + vet costs.
    size_base = {"small": 120.0, "medium": 170.0, "large": 220.0}.get(dog_size, 170.0)
    needs_penalty = 100.0 * float(special_needs)
    training_adj = {"low": 0.0, "medium": 25.0, "high": 50.0}.get(training_level, 25.0)
    return size_base + needs_penalty + training_adj


def _budget_compat(budget_monthly: float, dog_cost_estimate: float) -> float:
    if dog_cost_estimate <= 0:
        return 0.5
    ratio = budget_monthly / dog_cost_estimate
    if ratio >= 1.0:
        return 1.0
    if ratio >= 0.85:
        return 0.8
    if ratio >= 0.65:
        return 0.55
    if ratio >= 0.45:
        return 0.25
    return 0.1


def _age_proximity(preferred_age: str, dog_age_years: float) -> float:
    target = _preferred_age_target(preferred_age)
    # Exponential drop-off with distance in years
    dist = abs(dog_age_years - target)
    return float(max(0.0, min(1.0, math.exp(-dist / 3.0))))


def _make_interaction_features(user: Dict[str, Any], dog: Dict[str, Any]) -> Dict[str, Any]:
    # Canonicalize expected user and dog fields; default to safe values.
    housing_type = user.get("housing_type", "apartment")
    yard_size_bucket = user.get("yard_size_bucket", "none")
    activity_level = user.get("activity_level", "medium")
    work_hours_away = float(user.get("work_hours_away", 4))
    pet_experience = user.get("pet_experience", "some")
    allergies_level = user.get("allergies", "none")
    budget_monthly = float(user.get("budget_monthly", 250))
    kids_in_household = int(user.get("kids_in_household", 0))
    other_pets_in_household = int(user.get("other_pets_in_household", 0))
    preferred = user.get("preferred_traits", {}) or {}
    preferred_size = preferred.get("size", "medium")
    preferred_age = preferred.get("age", "adult")
    preferred_temperament = preferred.get("temperament", "friendly")

    # Dog fields
    breed = dog.get("breed", "mixed")
    dog_age_years = float(dog.get("age_years", 3))
    dog_age_bucket = _categorical_age_bucket(dog_age_years)
    dog_size = dog.get("size", "medium")
    energy_level = dog.get("energy_level", "medium")
    temperament = dog.get("temperament", "friendly")
    training_level = dog.get("training_level", "medium")
    special_needs = int(bool(dog.get("special_needs", 0)))
    hypoallergenic = bool(dog.get("hypoallergenic", False))
    kid_compatibility = dog.get("kid_compatibility", "medium")
    other_pets_compatibility = dog.get("other_pets_compatibility", "medium")

    # Optional "fairness group" (not used for training by default)
    fairness_group = user.get("fairness_group")

    # Interaction/compatibility features (interpretable)
    size_match = 1 if dog_size == preferred_size else 0
    age_proximity = _age_proximity(preferred_age, dog_age_years)
    temperament_match = _temperament_match_score(preferred_temperament, temperament)
    energy_compat = _energy_compat(activity_level, work_hours_away, energy_level)
    allergies_compat = _hypoallergenic_compat(allergies_level, hypoallergenic)
    training_compat = _training_compat(pet_experience, training_level, special_needs)
    kids_compat = _kids_compat(kids_in_household, kid_compatibility)
    other_pets_compat = _other_pets_compat(other_pets_in_household, other_pets_compatibility)

    dog_cost_estimate = _budget_estimate(dog_size, special_needs, training_level)
    budget_compat = _budget_compat(budget_monthly, dog_cost_estimate)

    allergies_severe_flag = 1 if allergies_level == "severe" else 0

    # Behavioral risk signals: these help the return-risk model.
    unrealistic_preferences_flag = 0
    if pet_experience == "none" and energy_level == "high" and activity_level == "high":
        unrealistic_preferences_flag = 1
    if pet_experience == "none" and training_level == "high":
        unrealistic_preferences_flag = 1
    if allergies_level in {"mild", "severe"} and not hypoallergenic:
        unrealistic_preferences_flag = max(unrealistic_preferences_flag, 1)

    schedule_mismatch_flag = 0
    if work_hours_away >= 7 and energy_level == "high":
        schedule_mismatch_flag = 1

    # Yard housing constraints
    yard_ok = 1
    if housing_type == "apartment" and yard_size_bucket in {"medium", "large"}:
        yard_ok = 0

    # For ML we keep this as a feature instead of enforcing hard vetoes.
    # Rule-based matching will still use hard constraints.
    yard_ok_flag = yard_ok

    return {
        # User attributes (categorical)
        "housing_type": housing_type,
        "yard_size_bucket": yard_size_bucket,
        "activity_level": activity_level,
        "pet_experience": pet_experience,
        "allergies_level": allergies_level,
        "preferred_size": preferred_size,
        "preferred_age": preferred_age,
        "preferred_temperament": preferred_temperament,
        # User attributes (numeric/binary)
        "work_hours_away": work_hours_away,
        "budget_monthly": budget_monthly,
        "kids_in_household": kids_in_household,
        "other_pets_in_household": other_pets_in_household,
        "allergies_severe_flag": allergies_severe_flag,
        "unrealistic_preferences_flag": unrealistic_preferences_flag,
        "schedule_mismatch_flag": schedule_mismatch_flag,
        "yard_ok_flag": yard_ok_flag,
        # Dog attributes (categorical)
        "breed": breed,
        "dog_size": dog_size,
        "dog_age_bucket": dog_age_bucket,
        "energy_level": energy_level,
        "temperament": temperament,
        "training_level": training_level,
        "kid_compatibility": kid_compatibility,
        "other_pets_compatibility": other_pets_compatibility,
        # Dog attributes (numeric/binary)
        "dog_age_years": dog_age_years,
        "special_needs": special_needs,
        "hypoallergenic": int(hypoallergenic),
        # Derived interaction features (interpretable numeric)
        "size_match": size_match,
        "age_proximity": age_proximity,
        "temperament_match": temperament_match,
        "energy_compat": energy_compat,
        "allergies_compat": allergies_compat,
        "training_compat": training_compat,
        "kids_compat": kids_compat,
        "other_pets_compat": other_pets_compat,
        "dog_cost_estimate": dog_cost_estimate,
        "budget_compat": budget_compat,
        # For fairness audits (do not include by default in training)
        "fairness_group": fairness_group,
    }


# -----------------------------
# Synthetic data generation
# -----------------------------


@dataclass
class SyntheticSchema:
    user_fields: List[str]
    dog_fields: List[str]
    pair_feature_columns: List[str]
    match_label_col: str
    risk_label_col: str
    sensitive_group_col: str


def generate_synthetic_catalogs(
    rng: random.Random, n_users: int, n_dogs: int
) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    # Dog catalog
    dog_breeds = [
        "Labrador Retriever",
        "German Shepherd",
        "Beagle",
        "Poodle",
        "Bulldog",
        "Corgi",
        "Husky",
        "Shih Tzu",
        "Mixed",
        "Greyhound",
        "Golden Retriever",
        "Boxer",
    ]
    dog_temperaments = ["friendly", "shy", "energetic", "calm", "aggressive"]
    dog_energy_levels = ["low", "medium", "high"]
    dog_training_levels = ["low", "medium", "high"]
    kid_compat_levels = ["high", "medium", "low"]
    other_pets_levels = ["high", "medium", "low"]

    # A toy hypoallergenic list (replace with verified breed-level data)
    hypoallergenic_breeds = {"Poodle", "Shih Tzu"}

    dogs: List[Dict[str, Any]] = []
    for i in range(n_dogs):
        breed = rng.choice(dog_breeds)
        dog_size = rng.choice(["small", "medium", "large"])
        age_years = float(max(0.1, rng.gauss(3.5, 2.3)))
        energy_level = rng.choice(dog_energy_levels)
        temperament = rng.choice(dog_temperaments)
        training_level = rng.choice(dog_training_levels)
        special_needs = 1 if rng.random() < 0.18 else 0

        # Compatibility heuristics
        kid_compatibility = "high" if temperament in {"friendly", "calm"} else rng.choice(kid_compat_levels)
        other_pets_compatibility = "high" if temperament in {"friendly", "calm"} else rng.choice(other_pets_levels)
        hypoallergenic = breed in hypoallergenic_breeds

        dogs.append(
            {
                "breed": breed,
                "age_years": round(age_years, 2),
                "size": dog_size,
                "energy_level": energy_level,
                "temperament": temperament,
                "training_level": training_level,
                "special_needs": special_needs,
                "hypoallergenic": hypoallergenic,
                "kid_compatibility": kid_compatibility,
                "other_pets_compatibility": other_pets_compatibility,
                # Optional shelter notes - kept unused in model for simplicity.
                "shelter_notes": rng.choice(
                    [
                        "Good with people.",
                        "May be shy at first.",
                        "Needs consistent routine.",
                        "Learning basic commands.",
                        "Active and playful.",
                        "Has medical considerations.",
                    ]
                ),
            }
        )

    # Adopter catalog
    housing_type = ["apartment", "house"]
    yard_size_bucket_vals = ["none", "small", "medium", "large"]
    activity_levels = ["low", "medium", "high"]
    pet_experience_vals = ["none", "some", "expert"]
    allergies_levels = ["none", "mild", "severe"]
    preferred_sizes = ["small", "medium", "large"]
    preferred_ages = ["puppy", "young_adult", "adult", "senior"]
    preferred_temperaments = ["friendly", "shy", "calm", "energetic", "aggressive"]

    income_brackets = ["low", "mid", "high"]  # used only for fairness audits
    adopters: List[Dict[str, Any]] = []
    for i in range(n_users):
        house_or_apt = rng.choice(housing_type)
        if house_or_apt == "apartment":
            yard_bucket = rng.choice(["none", "small"])
        else:
            yard_bucket = rng.choice(yard_size_bucket_vals)

        adopters.append(
            {
                "housing_type": house_or_apt,
                "yard_size_bucket": yard_bucket,
                "activity_level": rng.choice(activity_levels),
                "work_hours_away": int(max(0, min(10, rng.gauss(5.0, 2.8)))),
                "pet_experience": rng.choice(pet_experience_vals),
                "allergies": rng.choice(allergies_levels),
                "budget_monthly": int(max(60, min(500, rng.gauss(240, 90)))),
                "kids_in_household": 1 if rng.random() < 0.22 else 0,
                "other_pets_in_household": 1 if rng.random() < 0.28 else 0,
                "preferred_traits": {
                    "size": rng.choice(preferred_sizes),
                    "age": rng.choice(preferred_ages),
                    "temperament": rng.choice(preferred_temperaments),
                },
                "fairness_group": rng.choice(income_brackets),
            }
        )

    return adopters, dogs


def build_synthetic_pair_dataset(
    n_users: int = 2000,
    n_dogs: int = 300,
    pairs_per_user: int = 20,
    seed: int = 7,
) -> Tuple[pd.DataFrame, SyntheticSchema]:
    rng = random.Random(seed)
    users, dogs = generate_synthetic_catalogs(rng, n_users=n_users, n_dogs=n_dogs)

    rows: List[Dict[str, Any]] = []
    # Generate a smaller number of pairs to keep training fast.
    for user in users:
        candidates = rng.sample(dogs, k=min(pairs_per_user, len(dogs)))
        for dog in candidates:
            feats = _make_interaction_features(user, dog)

            # Latent adoption success probability (used to derive labels)
            # Higher compatibility -> lower return risk.
            # Add mild noise so models aren't perfect.
            logit = (
                2.2 * feats["energy_compat"]
                + 1.6 * feats["size_match"]
                + 1.1 * feats["age_proximity"]
                + 1.1 * feats["temperament_match"]
                + 1.0 * feats["kids_compat"]
                + 0.8 * feats["other_pets_compat"]
                + 1.0 * feats["allergies_compat"]
                + 1.0 * feats["training_compat"]
                + 0.9 * feats["budget_compat"]
                + 0.5 * feats["yard_ok_flag"]
                - 1.2 * feats["special_needs"] * (1.0 if user.get("pet_experience") != "expert" else 0.0)
                - 1.4 * feats["schedule_mismatch_flag"]
                - 1.2 * feats["unrealistic_preferences_flag"]
            )
            logit += rng.gauss(0, 0.8)
            p_success = _sigmoid(logit)
            returned_prob = float(max(0.01, min(0.99, 1.0 - p_success)))
            returned = 1 if rng.random() < returned_prob else 0

            feats["risk_returned"] = returned
            feats["compatible"] = 1 - returned
            rows.append(feats)

    df = pd.DataFrame(rows)

    # Identify columns for preprocessing
    pair_feature_columns = [
        c
        for c in df.columns
        if c
        not in {
            "compatible",
            "risk_returned",
        }
    ]

    schema = SyntheticSchema(
        user_fields=[
            "housing_type",
            "yard_size_bucket",
            "activity_level",
            "work_hours_away",
            "pet_experience",
            "allergies",
            "budget_monthly",
            "kids_in_household",
            "other_pets_in_household",
            "preferred_traits",
        ],
        dog_fields=[
            "breed",
            "age_years",
            "size",
            "energy_level",
            "temperament",
            "training_level",
            "special_needs",
            "hypoallergenic",
            "kid_compatibility",
            "other_pets_compatibility",
        ],
        pair_feature_columns=pair_feature_columns,
        match_label_col="compatible",
        risk_label_col="risk_returned",
        sensitive_group_col="fairness_group",
    )

    return df, schema


# -----------------------------
# Preprocessing + training
# -----------------------------


DEFAULT_CATEGORICAL_COLS = [
    "housing_type",
    "yard_size_bucket",
    "activity_level",
    "pet_experience",
    "allergies_level",
    "preferred_size",
    "preferred_age",
    "preferred_temperament",
    "breed",
    "dog_size",
    "dog_age_bucket",
    "energy_level",
    "temperament",
    "training_level",
    "kid_compatibility",
    "other_pets_compatibility",
]

DEFAULT_NUMERIC_COLS = [
    "work_hours_away",
    "budget_monthly",
    "kids_in_household",
    "other_pets_in_household",
    "allergies_severe_flag",
    "unrealistic_preferences_flag",
    "schedule_mismatch_flag",
    "yard_ok_flag",
    "dog_age_years",
    "special_needs",
    "hypoallergenic",
    "size_match",
    "age_proximity",
    "temperament_match",
    "energy_compat",
    "allergies_compat",
    "training_compat",
    "kids_compat",
    "other_pets_compat",
    "dog_cost_estimate",
    "budget_compat",
]


def build_preprocessor(
    categorical_cols: List[str] = DEFAULT_CATEGORICAL_COLS,
    numeric_cols: List[str] = DEFAULT_NUMERIC_COLS,
):
    preprocessor = ColumnTransformer(
        transformers=[
            (
                "cat",
                OneHotEncoder(handle_unknown="ignore", sparse_output=False),
                categorical_cols,
            ),
            ("num", StandardScaler(), numeric_cols),
        ],
        remainder="drop",
    )
    return preprocessor


def train_matching_model(
    df: pd.DataFrame, categorical_cols: List[str], numeric_cols: List[str], seed: int = 7
) -> Tuple[Pipeline, Dict[str, Any]]:
    # Label: compatible=1 means high chance of staying (not returned)
    X = df[categorical_cols + numeric_cols + ["fairness_group"]].copy()
    y = df["compatible"].astype(int).values

    preprocessor = build_preprocessor(categorical_cols, numeric_cols)
    model = LogisticRegression(
        max_iter=600,
        class_weight="balanced",
        solver="lbfgs",
    )
    pipe = Pipeline(steps=[("preprocess", preprocessor), ("model", model)])

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=seed, stratify=y
    )
    pipe.fit(X_train, y_train)
    proba = pipe.predict_proba(X_test)[:, 1]
    auc = roc_auc_score(y_test, proba)

    # Fairness audit: group-level prediction stats (fairness_group is dropped from features).
    fairness_audit = {}
    if "fairness_group" in X.columns:
        group_test = X_test["fairness_group"].astype(str).fillna("unknown")
        for g in sorted(group_test.unique()):
            mask = group_test == g
            fairness_audit[g] = {
                "avg_pred_compatible": float(np.mean(proba[mask])) if mask.any() else None,
                "observed_compatible_rate": float(np.mean(y_test[mask])) if mask.any() else None,
                "count": int(np.sum(mask)),
            }

    metrics = {"auc": float(auc), "fairness_audit": fairness_audit}
    return pipe, metrics


def train_risk_model(
    df: pd.DataFrame, categorical_cols: List[str], numeric_cols: List[str], seed: int = 7
) -> Tuple[Pipeline, Dict[str, Any]]:
    # Label: risk_returned=1 indicates likely return (higher risk)
    X = df[categorical_cols + numeric_cols + ["fairness_group"]].copy()
    y = df["risk_returned"].astype(int).values

    preprocessor = build_preprocessor(categorical_cols, numeric_cols)
    model = LogisticRegression(
        max_iter=600,
        class_weight="balanced",
        solver="lbfgs",
    )
    pipe = Pipeline(steps=[("preprocess", preprocessor), ("model", model)])

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=seed, stratify=y
    )
    pipe.fit(X_train, y_train)
    proba = pipe.predict_proba(X_test)[:, 1]
    auc = roc_auc_score(y_test, proba)

    # Fairness audit: group-level prediction stats (fairness_group is dropped from features).
    fairness_audit = {}
    if "fairness_group" in X.columns:
        group_test = X_test["fairness_group"].astype(str).fillna("unknown")
        low_risk_threshold = 0.34
        for g in sorted(group_test.unique()):
            mask = group_test == g
            fairness_audit[g] = {
                "avg_pred_return_risk": float(np.mean(proba[mask])) if mask.any() else None,
                "observed_return_rate": float(np.mean(y_test[mask])) if mask.any() else None,
                "low_risk_selection_rate": float(np.mean(proba[mask] < low_risk_threshold)) if mask.any() else None,
                "count": int(np.sum(mask)),
            }

    metrics = {"auc": float(auc), "fairness_audit": fairness_audit}
    return pipe, metrics


def _extract_feature_contributions(
    pipe: Pipeline, preprocessed_feature_names: List[str], x_row: pd.DataFrame
) -> List[Tuple[str, float]]:
    """
    For a logistic regression model:
        logit = intercept + sum_i (coef_i * x_i)
    We return top contributions by absolute logit effect.
    """
    preprocess = pipe.named_steps["preprocess"]
    model: BaseEstimator = pipe.named_steps["model"]

    X_trans = preprocess.transform(x_row)
    # Ensure 2D
    if hasattr(X_trans, "toarray"):
        X_trans = X_trans.toarray()
    x_vec = np.asarray(X_trans).reshape(-1)
    coefs = getattr(model, "coef_")
    intercept = float(getattr(model, "intercept_")[0])
    coefs = np.asarray(coefs).reshape(-1)
    # x_i * coef_i
    contrib = x_vec * coefs

    pairs = list(zip(preprocessed_feature_names, contrib))
    # Sort by absolute effect
    pairs.sort(key=lambda t: abs(t[1]), reverse=True)
    return pairs[:12]


def explain_matching_reasons(
    pipe: Pipeline,
    user: Dict[str, Any],
    dog: Dict[str, Any],
    fallback_reasons: List[str],
    top_k: int = 3,
) -> Dict[str, Any]:
    # Rule reasons: always useful and interpretable
    rule_reasons = fallback_reasons[:]

    # ML reasons: coefficient contributions (logit space)
    try:
        feat = _make_interaction_features(user, dog)
        df_row = pd.DataFrame([feat])
        preprocessor = pipe.named_steps["preprocess"]
        model = pipe.named_steps["model"]

        # Get consistent feature names from preprocessor
        feature_names = preprocessor.get_feature_names_out()

        contrib_pairs = _extract_feature_contributions(pipe, list(feature_names), df_row)

        # Convert to more readable tokens
        ml_reasons: List[str] = []
        for name, val in contrib_pairs[: top_k * 2]:
            # Filter mostly noisy tiny effects
            if abs(val) < 0.03:
                continue
            direction = "increases" if val >= 0 else "decreases"
            ml_reasons.append(f"Model {direction} compatibility via `{name}` (logit {val:+.2f})")

        # If model isn't informative, avoid empty list
        if not ml_reasons:
            ml_reasons = ["Model found no strong single-feature drivers; rules dominate."]

        return {"rules": rule_reasons, "model": ml_reasons[:top_k]}
    except Exception as e:
        return {"rules": rule_reasons, "model": [f"ML explanation unavailable: {type(e).__name__}"]}


def explain_risk_reasons(
    pipe: Pipeline,
    user: Dict[str, Any],
    dog: Dict[str, Any],
    fallback_reasons: List[str],
    top_k: int = 5,
) -> Dict[str, Any]:
    rule_reasons = fallback_reasons[:]
    try:
        feat = _make_interaction_features(user, dog)
        df_row = pd.DataFrame([feat])
        preprocessor = pipe.named_steps["preprocess"]
        feature_names = preprocessor.get_feature_names_out()

        contrib_pairs = _extract_feature_contributions(pipe, list(feature_names), df_row)
        ml_reasons: List[str] = []
        for name, val in contrib_pairs[: top_k * 2]:
            if abs(val) < 0.03:
                continue
            direction = "increases" if val >= 0 else "decreases"
            ml_reasons.append(f"Model {direction} return-risk via `{name}` (logit {val:+.2f})")
        if not ml_reasons:
            ml_reasons = ["Model explanation unavailable (low signal)."]

        return {"rules": rule_reasons, "model": ml_reasons[:top_k]}
    except Exception as e:
        return {"rules": rule_reasons, "model": [f"ML explanation unavailable: {type(e).__name__}"]}


# -----------------------------
# Rule-based fallback scoring
# -----------------------------


def rule_based_compatibility_score(user: Dict[str, Any], dog: Dict[str, Any]) -> Tuple[float, List[str]]:
    feat = _make_interaction_features(user, dog)

    reasons: List[str] = []

    # Hard vetoes that reduce return risk
    if int(user.get("kids_in_household", 0)) == 1 and dog.get("kid_compatibility", "medium") == "low":
        reasons.append("Veto: dog compatibility with kids is low, raising early-return risk.")
        return 0.02, reasons
    if int(user.get("other_pets_in_household", 0)) == 1 and dog.get("other_pets_compatibility", "medium") == "low":
        reasons.append("Veto: low compatibility with other pets increases conflict/return risk.")
        return 0.02, reasons
    if user.get("allergies", "none") == "severe" and not bool(dog.get("hypoallergenic", False)):
        reasons.append("Veto: severe allergies without hypoallergenic dog increases health-driven returns.")
        return 0.03, reasons
    if float(user.get("work_hours_away", 0)) >= 7 and dog.get("energy_level", "medium") == "high":
        reasons.append("Veto: high energy dog with long work absences increases stress/return risk.")
        return 0.05, reasons

    # Soft scoring: weighted sum of interpretable features
    w = {
        "energy_compat": 0.22,
        "training_compat": 0.16,
        "temperament_match": 0.16,
        "allergies_compat": 0.12,
        "budget_compat": 0.12,
        "age_proximity": 0.10,
        "kids_compat": 0.08,
        "other_pets_compat": 0.06,
        "yard_ok_flag": 0.06,
        "size_match": 0.10,
    }
    # Normalize weights in case sum != 1
    total_w = sum(w.values())
    w = {k: v / total_w for k, v in w.items()}

    raw = 0.0
    for key, weight in w.items():
        raw += float(feat[key]) * weight

    # Gentle penalty for special needs when experience is not expert
    if int(feat["special_needs"]) == 1 and user.get("pet_experience") != "expert":
        raw *= 0.75
        reasons.append("Special needs + non-expert experience lowers adoption stability.")
    if feat["unrealistic_preferences_flag"] == 1:
        raw *= 0.85
        reasons.append("Unrealistic preference pattern increases mismatch and return risk.")

    # Build reasons for the score
    if feat["energy_compat"] >= 0.85:
        reasons.append("Energy and activity are aligned with your schedule.")
    else:
        reasons.append("Energy/schedule alignment is only moderate; expect more management.");

    if feat["allergies_compat"] >= 0.8:
        reasons.append("Allergy risk appears low for this dog (hypoallergenic fit).")
    else:
        reasons.append("Allergy fit is weaker; ensure medical suitability checks.")

    if feat["kids_compat"] < 0.5 and int(user.get("kids_in_household", 0)) == 1:
        reasons.append("Kids compatibility is a concern for this home setup.")

    if feat["budget_compat"] >= 0.85:
        reasons.append("Your monthly budget matches expected dog care costs.")
    else:
        reasons.append("Budget match is partial; financial friction can cause returns.")

    # Clamp to 0..1
    score = float(max(0.0, min(1.0, raw)))
    return score, reasons


def rule_based_return_risk_score(user: Dict[str, Any], dog: Dict[str, Any]) -> Tuple[float, List[str]]:
    compat_score, reasons = rule_based_compatibility_score(user, dog)
    # Convert compatibility to risk (inverse) with nonlinearity
    # If compat is high -> low return risk.
    risk = float(max(0.0, min(1.0, (1.0 - compat_score) ** 1.25)))
    # Add a couple risk-oriented clarifications
    if risk >= 0.66:
        reasons.append("Overall: higher mismatch indicators suggest higher probability of return.")
    elif risk >= 0.33:
        reasons.append("Overall: moderate mismatch indicators; mitigation steps recommended.")
    else:
        reasons.append("Overall: strong fit indicators; lower return-risk expected.")
    return risk, reasons


# -----------------------------
# Artifacts loading/saving
# -----------------------------


ARTIFACT_DIR_DEFAULT = os.path.join(os.path.dirname(os.path.dirname(__file__)), "artifacts")
MATCHING_ARTIFACT_PATH_DEFAULT = os.path.join(ARTIFACT_DIR_DEFAULT, "matching_pipeline.joblib")
RISK_ARTIFACT_PATH_DEFAULT = os.path.join(ARTIFACT_DIR_DEFAULT, "risk_pipeline.joblib")


def save_artifacts(
    matching_pipe: Pipeline,
    risk_pipe: Pipeline,
    metadata: Dict[str, Any],
    matching_path: str = MATCHING_ARTIFACT_PATH_DEFAULT,
    risk_path: str = RISK_ARTIFACT_PATH_DEFAULT,
) -> None:
    os.makedirs(os.path.dirname(matching_path), exist_ok=True)
    joblib.dump({"pipeline": matching_pipe, "metadata": metadata}, matching_path)
    joblib.dump({"pipeline": risk_pipe, "metadata": metadata}, risk_path)


def load_artifacts(
    matching_path: str = MATCHING_ARTIFACT_PATH_DEFAULT,
    risk_path: str = RISK_ARTIFACT_PATH_DEFAULT,
) -> Dict[str, Any]:
    matching_obj = None
    risk_obj = None
    if os.path.exists(matching_path):
        matching_obj = joblib.load(matching_path)
    if os.path.exists(risk_path):
        risk_obj = joblib.load(risk_path)

    return {
        "matching": matching_obj,
        "risk": risk_obj,
    }


# -----------------------------
# Prediction pipeline
# -----------------------------


def _prepare_feature_df(user: Dict[str, Any], dog: Dict[str, Any]) -> pd.DataFrame:
    feat = _make_interaction_features(user, dog)
    return pd.DataFrame([feat])


def predict_compatibility_matches(
    user: Dict[str, Any],
    candidate_dogs: List[Dict[str, Any]],
    artifacts: Dict[str, Any],
    top_k: int = 5,
) -> Dict[str, Any]:
    matching_obj = artifacts.get("matching")
    matching_pipe = matching_obj["pipeline"] if matching_obj else None

    matches: List[Dict[str, Any]] = []
    fallback_used = matching_pipe is None

    for dog in candidate_dogs:
        # Always compute fallback reasons; they are useful even with ML.
        fallback_score, fallback_reasons = rule_based_compatibility_score(user, dog)

        if matching_pipe is None:
            score = fallback_score
            why = {"rules": fallback_reasons, "model": []}
        else:
            df_row = _prepare_feature_df(user, dog)
            # Model predicts P(compatible=1) which we map directly to compatibility score.
            proba = float(matching_pipe.predict_proba(df_row)[:, 1][0])
            score = proba
            why = explain_matching_reasons(
                matching_pipe, user=user, dog=dog, fallback_reasons=fallback_reasons
            )

        matches.append(
            {
                "dog": dog,
                "compatibility_score": float(score),
                "why": why,
                "fallback_compatibility_score": float(fallback_score),
            }
        )

    matches.sort(key=lambda m: m["compatibility_score"], reverse=True)
    return {
        "matches": matches[:top_k],
        "fallback_used": bool(fallback_used),
        "top_k": top_k,
        "timestamp": int(time.time()),
    }


def predict_return_risk(
    user: Dict[str, Any],
    dog: Dict[str, Any],
    artifacts: Dict[str, Any],
) -> Dict[str, Any]:
    risk_obj = artifacts.get("risk")
    risk_pipe = risk_obj["pipeline"] if risk_obj else None

    fallback_risk, fallback_reasons = rule_based_return_risk_score(user, dog)
    if risk_pipe is None:
        risk_score = fallback_risk
        why = {"rules": fallback_reasons, "model": []}
    else:
        df_row = _prepare_feature_df(user, dog)
        risk_score = float(risk_pipe.predict_proba(df_row)[:, 1][0])
        why = explain_risk_reasons(
            risk_pipe, user=user, dog=dog, fallback_reasons=fallback_reasons
        )

    # Labels based on risk score
    if risk_score < 0.34:
        risk_label = "Low Risk"
    elif risk_score < 0.66:
        risk_label = "Medium Risk"
    else:
        risk_label = "High Risk"

    return {
        "risk_score": float(risk_score),
        "risk_label": risk_label,
        "fallback_risk_score": float(fallback_risk),
        "why": why,
        "fallback_used": bool(risk_pipe is None),
        "timestamp": int(time.time()),
    }


# -----------------------------
# Feedback loop helpers
# -----------------------------


FEEDBACK_CSV_PATH_DEFAULT = os.path.join(ARTIFACT_DIR_DEFAULT, "feedback_log.csv")


def append_feedback(
    user: Dict[str, Any],
    dog: Dict[str, Any],
    returned: int,
    feedback_csv_path: str = FEEDBACK_CSV_PATH_DEFAULT,
) -> None:
    os.makedirs(os.path.dirname(feedback_csv_path), exist_ok=True)
    row = _make_interaction_features(user, dog)
    row["risk_returned"] = int(returned)
    row["compatible"] = 1 - int(returned)
    row["feedback_timestamp"] = int(time.time())

    df_row = pd.DataFrame([row])
    if os.path.exists(feedback_csv_path):
        df_row.to_csv(feedback_csv_path, mode="a", header=False, index=False)
    else:
        df_row.to_csv(feedback_csv_path, mode="w", header=True, index=False)


def load_feedback_df(feedback_csv_path: str = FEEDBACK_CSV_PATH_DEFAULT) -> pd.DataFrame:
    if not os.path.exists(feedback_csv_path):
        return pd.DataFrame()
    return pd.read_csv(feedback_csv_path)


# -----------------------------
# Training entrypoint used by train script
# -----------------------------


def train_and_save_models(
    out_dir: str = ARTIFACT_DIR_DEFAULT,
    n_users: int = 2000,
    n_dogs: int = 300,
    pairs_per_user: int = 20,
    seed: int = 7,
    include_feedback: bool = True,
) -> Dict[str, Any]:
    from sklearn.utils import shuffle

    os.makedirs(out_dir, exist_ok=True)

    df_pairs, schema = build_synthetic_pair_dataset(
        n_users=n_users,
        n_dogs=n_dogs,
        pairs_per_user=pairs_per_user,
        seed=seed,
    )

    if include_feedback:
        fb_df = load_feedback_df()
        if not fb_df.empty:
            # Keep only columns we can use
            df_pairs = pd.concat([df_pairs, fb_df], ignore_index=True)

    # Drop fairness_group for training inputs unless you explicitly add it to feature lists.
    # Our default preprocess ignores it via remainder="drop".
    df_pairs = shuffle(df_pairs, random_state=seed)

    matching_pipe, matching_metrics = train_matching_model(
        df_pairs, categorical_cols=DEFAULT_CATEGORICAL_COLS, numeric_cols=DEFAULT_NUMERIC_COLS, seed=seed
    )
    risk_pipe, risk_metrics = train_risk_model(
        df_pairs, categorical_cols=DEFAULT_CATEGORICAL_COLS, numeric_cols=DEFAULT_NUMERIC_COLS, seed=seed
    )

    # Basic artifact metadata
    metadata = {
        "seed": seed,
        "schema": schema.__dict__,
        "feature_columns": {
            "categorical": DEFAULT_CATEGORICAL_COLS,
            "numeric": DEFAULT_NUMERIC_COLS,
        },
        "metrics": {"matching": matching_metrics, "risk": risk_metrics},
        "trained_at": int(time.time()),
    }

    save_artifacts(
        matching_pipe=matching_pipe,
        risk_pipe=risk_pipe,
        metadata=metadata,
        matching_path=os.path.join(out_dir, "matching_pipeline.joblib"),
        risk_path=os.path.join(out_dir, "risk_pipeline.joblib"),
    )

    return metadata


__all__ = [
    "build_preprocessor",
    "build_synthetic_pair_dataset",
    "train_and_save_models",
    "load_artifacts",
    "predict_compatibility_matches",
    "predict_return_risk",
    "append_feedback",
    "load_feedback_df",
    "SyntheticSchema",
]

