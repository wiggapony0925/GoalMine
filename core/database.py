import os
import logging
from typing import Dict, Optional, List
from supabase import create_client

logger = logging.getLogger("GoalMine")

class Database:
    """
    Persistence Hub. Strictly uses Supabase Cloud Database.
    """
    def __init__(self):
        self.supabase_url = os.getenv("SUPABASE_URL")
        self.supabase_key = os.getenv("SUPABASE_KEY")
        
        if not self.supabase_url or not self.supabase_key:
            logger.error("❌ CRITICAL: SUPABASE_URL and SUPABASE_KEY must be set in .env")
            raise ValueError("Missing Supabase configuration. Local JSON fallback disabled.")

        try:
            self.client = create_client(self.supabase_url, self.supabase_key)
            logger.info("📡 Cloud Database Initialized (Supabase Mode)")
        except Exception as e:
            logger.error(f"❌ Supabase Connection Failed: {e}")
            raise e

    def save_memory(self, user_phone: str, data: Dict):
        """Saves user session data (God View) to Supabase."""
        try:
            # Match info for tracking multiple games
            fixture = data.get("match", "Unknown Match")
            
            # Upserts to the 'sessions' table. 
            self.client.table('sessions').upsert({
                "phone": str(user_phone),
                "fixture": fixture,
                "god_view": data
            }).execute()
            logger.info(f"💾 [Supabase] God View Persisted: {fixture} for {user_phone}")
        except Exception as e:
            logger.error(f"Supabase Save Error for {user_phone}: {e}")

    def load_memory(self, user_phone: str) -> Optional[Dict]:
        """Loads the MOST RECENT user session data."""
        try:
            # Use 'created_at' which is guaranteed to exist in Supabase default schema
            res = self.client.table('sessions').select("god_view").eq("phone", str(user_phone)).order("created_at", desc=True).limit(1).execute()
            if res.data:
                return res.data[0].get("god_view")
        except Exception as e:
            logger.error(f"Supabase Load Error for {user_phone}: {e}")
        return None

    def load_all_matchday_memory(self, user_phone: str) -> List[Dict]:
        """Loads all matches analyzed for this user today."""
        try:
            res = self.client.table('sessions').select("god_view").eq("phone", str(user_phone)).execute()
            return [row.get("god_view") for row in res.data]
        except Exception as e:
            logger.error(f"Supabase Bulk Load Error: {e}")
            return []
