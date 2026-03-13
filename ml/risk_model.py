"""
ML Risk Model — Placeholder Interface
======================================
The ML team can replace the `predict` method with a real trained model
(e.g., scikit-learn, XGBoost, or a PyTorch model) without changing the
calling interface in analytics/risk_engine.py.

Current implementation: delegates back to the formula-based engine.
"""
from __future__ import annotations
from dataclasses import dataclass


@dataclass
class UserEventFeatures:
    """Feature vector for the risk model."""
    clicks: int = 0
    credential_attempts: int = 0
    downloads: int = 0
    reported: int = 0
    campaigns_tested: int = 0


class RiskModel:
    """
    Drop-in interface for a trained risk model.
    To swap in a real model:
        1. Load your model artifact in __init__.
        2. Override `predict` to call model.predict([features]).
    """

    def __init__(self):
        # Placeholder: no model loaded
        self._model = None

    def predict(self, features: UserEventFeatures) -> float:
        """
        Returns a risk score in the range [0, 100].
        Currently uses the formula-based heuristic.
        """
        raw = (
            (features.clicks * 20)
            + (features.credential_attempts * 40)
            + (features.downloads * 30)
            - (features.reported * 15)
        )
        return float(max(0.0, min(100.0, raw)))

    def is_loaded(self) -> bool:
        return self._model is not None


# Singleton instance
risk_model = RiskModel()
