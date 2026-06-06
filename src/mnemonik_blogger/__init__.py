"""Mnemonik multi-platform blogger agent."""

from __future__ import annotations

__version__ = "0.1.0"

from .agent import CampaignResult, run_campaign
from .config import Platform, Settings, load_settings

__all__ = ["CampaignResult", "run_campaign", "Platform", "Settings", "load_settings", "__version__"]
