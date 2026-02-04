from core.log import get_logger
from .morning_brief import MorningBriefService
from .kickoff_alerts import KickoffAlertService
from .market_monitor import MarketMonitor

logger = get_logger("AutoMsg")

__all__ = ["MorningBriefService", "KickoffAlertService", "MarketMonitor"]
