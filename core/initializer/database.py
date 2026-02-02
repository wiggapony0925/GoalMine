import os
import json
from datetime import datetime
from typing import Dict, Optional, List, Any
from supabase import create_client
from core.log import get_logger

logger = get_logger("Database")

class Database:
    """
    Persistence Hub. Manages User State, Bet History, and Analytics.
    Separates chat memory from betting history for ROI tracking.
    """
    def __init__(self):
        self.supabase_url = os.getenv("SUPABASE_URL")
        self.supabase_key = os.getenv("SUPABASE_KEY")
        
        if not self.supabase_url or not self.supabase_key:
            logger.critical("❌ SUPABASE_URL or SUPABASE_KEY missing. Database offline.")
            raise ValueError("Supabase Credentials Missing")

        try:
            self.client = create_client(self.supabase_url, self.supabase_key)
            logger.info("📡 Supabase Connected.")
        except Exception as e:
            logger.critical(f"❌ Supabase Connection Failed: {e}")
            raise e

    def update_user_profile(self, user_phone: str, updates: Dict[str, Any]):
        """
        Saves user preferences (e.g., 'Risk Tolerance', 'Favorite Team').
        This is separated from chat logs so it doesn't get overwritten.
        
        Table: users
        Schema: phone (PK), risk_tolerance, favorite_team, budget, updated_at
        """
        try:
            data = {"phone": str(user_phone), "updated_at": datetime.utcnow().isoformat()}
            data.update(updates)
            
            self.client.table('users').upsert(data).execute()
            logger.info(f"👤 Profile updated for {user_phone}")
        except Exception as e:
            logger.error(f"Failed to update profile for {user_phone}: {e}")

    def save_chat_context(self, user_phone: str, context: List[Dict]):
        """
        Saves the active conversation history (Vector Store lite).
        
        Table: active_sessions
        Schema: phone (PK), messages (JSONB), last_active
        """
        try:
            self.client.table('active_sessions').upsert({
                "phone": str(user_phone),
                "messages": context,
                "last_active": datetime.utcnow().isoformat()
            }).execute()
            logger.info(f"💬 Chat context saved for {user_phone}")
        except Exception as e:
            logger.error(f"Memory Save Error: {e}")

    def load_chat_context(self, user_phone: str) -> List[Dict]:
        """Loads the last conversation for context window."""
        try:
            res = self.client.table('active_sessions').select("messages").eq("phone", str(user_phone)).execute()
            if res.data:
                return res.data[0].get("messages", [])
        except Exception as e:
            logger.warning(f"No chat context found for {user_phone}: {e}")
        return []

    def log_bet_prediction(self, user_phone: str, match_id: str, prediction: Dict):
        """
        CRITICAL: Logs every prediction the bot makes.
        Allows you to calculate 'True ROI' later.
        
        Table: predictions
        Schema: user_phone, match_id, predicted_outcome, odds, confidence, 
                stake, model_version, created_at
        """
        try:
            self.client.table('predictions').insert({
                "user_phone": str(user_phone),
                "match_id": match_id,
                "predicted_outcome": prediction.get('selection'),
                "odds": prediction.get('odds'),
                "confidence": prediction.get('confidence'),
                "stake": prediction.get('stake', 0),
                "model_version": "v2.1_dixon_coles",
                "created_at": datetime.utcnow().isoformat()
            }).execute()
            logger.info(f"📝 Bet Logged: {prediction.get('selection')} @ {prediction.get('odds')}")
        except Exception as e:
            logger.error(f"Failed to log bet: {e}")

    def save_memory(self, user_phone: str, data: Dict):
        """
        Legacy method for backward compatibility.
        Saves user session data (God View) to Supabase.
        
        Table: sessions
        Schema: phone, god_view (JSONB), created_at
        """
        try:
            self.client.table('sessions').upsert({
                "phone": str(user_phone),
                "god_view": data
            }).execute()
            logger.info(f"💾 [Supabase] God View Persisted for {user_phone}")
        except Exception as e:
            logger.error(f"Supabase Save Error for {user_phone}: {e}")

    def load_memory(self, user_phone: str) -> Optional[Dict]:
        """
        Legacy method for backward compatibility.
        Loads the MOST RECENT user session data.
        
        [TTL CHECK] Enforces data freshness policy.
        """
        try:
            # Modified to select created_at
            res = self.client.table('sessions').select("god_view, created_at").eq("phone", str(user_phone)).order("created_at", desc=True).limit(1).execute()
            
            if res.data:
                record = res.data[0]
                god_view = record.get("god_view")
                created_at_str = record.get("created_at") # ISO format from Supabase
                
                # TTL Check
                from core.config import settings
                ttl_hours = settings.get('retention.god_view_ttl_hours', 4) # Default 4h life
                
                if created_at_str:
                    # Handle both Z-terminated and offset-aware ISO strings
                    created_at_dt = datetime.fromisoformat(created_at_str.replace('Z', '+00:00'))
                    # Ensure now() is timezone aware (UTC) to match Supabase
                    now = datetime.now(datetime.timezone.utc) if created_at_dt.tzinfo else datetime.utcnow()
                    
                    age_hours = (now - created_at_dt).total_seconds() / 3600.0
                    
                    if age_hours > ttl_hours:
                        logger.info(f"💀 Memory Expired for {user_phone} (Age: {round(age_hours, 1)}h > Limit: {ttl_hours}h). Starting fresh.")
                        return None
                
                return god_view
        except Exception as e:
            logger.error(f"Supabase Load Error for {user_phone}: {e}")
        return None

    def clear_memory(self, user_phone: str):
        """
        Deletes session memory for a user.
        """
        try:
            self.client.table('sessions').delete().eq("phone", str(user_phone)).execute()
            logger.info(f"🧹 Memory cleared for {user_phone}")
        except Exception as e:
            logger.error(f"Memory clear error for {user_phone}: {e}")

    def load_all_matchday_memory(self, user_phone: str) -> List[Dict]:
        """Loads all matches analyzed for this user today."""
        try:
            res = self.client.table('sessions').select("god_view").eq("phone", str(user_phone)).execute()
            return [row.get("god_view") for row in res.data]
        except Exception as e:
            logger.error(f"Supabase Bulk Load Error: {e}")
            return []

    def get_user_roi(self, user_phone: str) -> Dict[str, float]:
        """
        Calculates user's ROI from logged predictions.
        Returns: {'total_staked': 100, 'total_return': 120, 'roi_percent': 20.0}
        """
        try:
            res = self.client.table('predictions').select("*").eq("user_phone", str(user_phone)).execute()
            
            total_staked = sum(p.get('stake', 0) for p in res.data)
            total_return = 0  # Would need actual results to calculate
            
            # This is a placeholder - you'd need to join with match results
            # For now, return the data structure
            return {
                'total_staked': total_staked,
                'total_bets': len(res.data),
                'roi_percent': 0.0  # Calculate when results are available
            }
        except Exception as e:
            logger.error(f"ROI calculation failed: {e}")
            return {'total_staked': 0, 'total_bets': 0, 'roi_percent': 0.0}
