import os
from datetime import datetime, timezone
from typing import Dict, Optional, List, Any
from supabase import create_client
from core.log import get_logger

logger = get_logger("Database")


class Database:
    """
    Persistence Hub. Manages User State, Bet History, and Analytics.
    Stores interactive message states for session persistence.
    """

    def __init__(self):
        self.supabase_url = os.getenv("SUPABASE_URL")
        self.supabase_key = os.getenv("SUPABASE_KEY")

        if not self.supabase_url or not self.supabase_key:
            logger.critical(
                "❌ SUPABASE_URL or SUPABASE_KEY missing. Database offline."
            )
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
            data = {
                "phone": str(user_phone),
                "updated_at": datetime.utcnow().isoformat(),
            }
            data.update(updates)

            self.client.table("users").upsert(data).execute()
            logger.info(f"👤 Profile updated for {user_phone}")
        except Exception as e:
            logger.error(f"Failed to update profile for {user_phone}: {e}")


    def save_button_state(self, user_phone: str, interactive_obj: Dict):
        """
        Saves the last sent interactive message inside the 'sessions' table.
        """
        try:
            existing = self.load_memory(user_phone) or {}
            existing["interactive_state"] = interactive_obj

            self.save_memory(user_phone, existing)
            logger.info(f"💾 Interactive state persisted for {user_phone}")
        except Exception as e:
            logger.error(f"Failed to save button state for {user_phone}: {e}")

    def load_button_state(self, user_phone: str) -> Optional[Dict]:
        """Loads the last interactive message from the 'sessions' blob."""
        try:
            data = self.load_memory(user_phone)
            if data and "interactive_state" in data:
                return data["interactive_state"]
        except Exception as e:
            logger.warning(f"No button state found for {user_phone}: {e}")
        return None


    def log_bet_prediction(self, user_phone: str, match_id: str, prediction: Dict):
        """
        CRITICAL: Logs every prediction the bot makes.
        Allows you to calculate 'True ROI' later.

        Table: predictions
        Schema: user_phone, match_id, predicted_outcome, odds, confidence,
                stake, model_version, created_at
        """
        try:
            TABLE_PREDICTIONS = "predictions"
            self.client.table(TABLE_PREDICTIONS).insert(
                {
                    "user_phone": str(user_phone),
                    "match_id": match_id,
                    "predicted_outcome": prediction.get("selection"),
                    "odds": prediction.get("odds"),
                    "confidence": prediction.get("confidence_grade")
                    or prediction.get("confidence"),
                    "stake": prediction.get("stake", 0),
                    "model_version": "v2.1_dixon_coles",
                    "created_at": datetime.utcnow().isoformat(),
                }
            ).execute()
            logger.info(
                f"📝 Bet Logged: {prediction.get('selection')} @ {prediction.get('odds')} (Conviction: {prediction.get('confidence_pct') or 'N/A'}%)"
            )
        except Exception as e:
            logger.error(f"Failed to log bet: {e}")

    def get_session_info(self, user_phone: str) -> Dict[str, Any]:
        """
        Returns { 'data': god_view_dict, 'age_minutes': float }
        Used for context-aware greetings.
        """
        try:
            res = (
                self.client.table("sessions")
                .select("god_view, created_at")
                .eq("phone", str(user_phone))
                .order("created_at", desc=True)
                .limit(1)
                .execute()
            )
            if not res.data:
                return {"data": None, "age_minutes": 9999}

            record = res.data[0]
            god_view = record.get("god_view")
            created_at_str = record.get("created_at")

            if not created_at_str:
                return {"data": god_view, "age_minutes": 9999}

            created_at_dt = datetime.fromisoformat(
                created_at_str.replace("Z", "+00:00")
            )
            now = (
                datetime.now(timezone.utc)
                if created_at_dt.tzinfo
                else datetime.utcnow()
            )
            age_minutes = (now - created_at_dt).total_seconds() / 60.0

            return {"data": god_view, "age_minutes": age_minutes}
        except Exception as e:
            logger.error(f"Error getting session info: {e}")
            return {"data": None, "age_minutes": 9999}

    def save_memory(self, user_phone: str, data: Dict):
        """
        Saves user session data to Supabase.
        MERGE LOGIC: Fetches existing data first to avoid overwriting 'messages' or 'interactive_state'.
        """
        try:
            # 1. Load existing data for this user
            res = (
                self.client.table("sessions")
                .select("god_view")
                .eq("phone", str(user_phone))
                .limit(1)
                .execute()
            )

            merged_data = data
            if res.data:
                existing_god_view = res.data[0].get("god_view", {})
                # Perform a shallow merge - 'data' takes precedence but we keep 'messages' and 'interactive_state'
                # if they aren't in the new payload.
                merged_data = existing_god_view.copy()
                merged_data.update(data)

            # 2. Upsert the merged blob
            self.client.table("sessions").upsert(
                {
                    "phone": str(user_phone),
                    "god_view": merged_data,
                    "created_at": datetime.now(timezone.utc).isoformat(),
                }
            ).execute()
            logger.info(f"💾 God View Persisted (Merged) for {user_phone}")
        except Exception as e:
            logger.error(f"Supabase Merge Save Error for {user_phone}: {e}")

    def load_memory(self, user_phone: str) -> Optional[Dict]:
        """
        Legacy method for backward compatibility.
        Loads the MOST RECENT user session data.

        [TTL CHECK] Enforces data freshness policy.
        """
        try:
            # Modified to select created_at
            res = (
                self.client.table("sessions")
                .select("god_view, created_at")
                .eq("phone", str(user_phone))
                .order("created_at", desc=True)
                .limit(1)
                .execute()
            )

            if res.data:
                record = res.data[0]
                god_view = record.get("god_view")
                created_at_str = record.get("created_at")  # ISO format from Supabase

                # TTL Check
                from core.config import settings

                ttl_hours = settings.get(
                    "GLOBAL_APP_CONFIG.retention.god_view_ttl_hours", 4
                )  # Default 4h life

                if created_at_str:
                    # Handle both Z-terminated and offset-aware ISO strings
                    created_at_dt = datetime.fromisoformat(
                        created_at_str.replace("Z", "+00:00")
                    )
                    # Ensure now() is timezone aware (UTC) to match Supabase
                    now = (
                        datetime.now(timezone.utc)
                        if created_at_dt.tzinfo
                        else datetime.utcnow()
                    )

                    age_hours = (now - created_at_dt).total_seconds() / 3600.0

                    if age_hours > ttl_hours:
                        logger.info(
                            f"💀 Memory Expired for {user_phone} (Age: {round(age_hours, 1)}h > Limit: {ttl_hours}h). Starting fresh."
                        )
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
            self.client.table("sessions").delete().eq(
                "phone", str(user_phone)
            ).execute()
            logger.info(f"🧹 Memory cleared for {user_phone}")
        except Exception as e:
            logger.error(f"Memory clear error for {user_phone}: {e}")

    def delete_all_user_data(self, user_phone: str):
        """
        PERMANENT WIPE: Deletes all user records across all tables for compliance.
        """
        user_phone_str = str(user_phone)
        try:
            # Wipe from all known tables
            self.client.table("sessions").delete().eq("phone", user_phone_str).execute()
            self.client.table("users").delete().eq("phone", user_phone_str).execute()
            self.client.table("predictions").delete().eq(
                "user_phone", user_phone_str
            ).execute()

            logger.warning(
                f"🚨 [COMPLIANCE] All data permanently deleted for {user_phone_str}"
            )
            return True
        except Exception as e:
            logger.error(
                f"Failed to perform full data deletion for {user_phone_str}: {e}"
            )
            return False

    def load_all_matchday_memory(self, user_phone: str) -> List[Dict]:
        """Loads all matches analyzed for this user today."""
        try:
            res = (
                self.client.table("sessions")
                .select("god_view")
                .eq("phone", str(user_phone))
                .execute()
            )
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
            res = (
                self.client.table("predictions")
                .select("*")
                .eq("user_phone", str(user_phone))
                .execute()
            )

            total_staked = sum(p.get("stake", 0) for p in res.data)

            # This is a placeholder - you'd need to join with match results
            # For now, return the data structure
            return {
                "total_staked": total_staked,
                "total_bets": len(res.data),
                "roi_percent": 0.0,  # Calculate when results are available
            }
        except Exception as e:
            logger.error(f"ROI calculation failed: {e}")
            return {"total_staked": 0, "total_bets": 0, "roi_percent": 0.0}

    def save_global_odds(self, match_id: str, odds_data: Dict):
        """Saves current odds for a match to detect movements later."""
        try:
            self.client.table("market_data").upsert(
                {
                    "match_id": match_id,
                    "odds_json": odds_data,
                    "updated_at": datetime.utcnow().isoformat(),
                }
            ).execute()
        except Exception as e:
            logger.error(f"Failed to save global odds: {e}")

    def load_global_odds(self, match_id: str) -> Optional[Dict]:
        """Loads previous odds for a match."""
        try:
            res = (
                self.client.table("market_data")
                .select("odds_json")
                .eq("match_id", match_id)
                .execute()
            )
            if res.data:
                return res.data[0].get("odds_json")
        except Exception:
            logger.warning(f"No previous odds found for {match_id}")
        return None

    def get_all_active_users(self) -> List[str]:
        """Returns list of all phone numbers that have interacted with the bot."""
        try:
            # Priority 1: The 'users' table
            res = self.client.table("users").select("phone").execute()
            return [row["phone"] for row in res.data]
        except Exception as e:
            # Robust check for PGRST205 (Table not found)
            error_str = str(e)
            is_table_missing = "PGRST205" in error_str or "schema cache" in error_str

            if is_table_missing:
                # Fallback: Look in the 'sessions' table since it exists as seen in screenshot
                try:
                    logger.warning(
                        "⚠️ 'users' table missing, falling back to 'sessions' for user list."
                    )
                    res = self.client.table("sessions").select("phone").execute()
                    # Return unique set of phones
                    phones = list(set([row["phone"] for row in res.data]))
                    return phones
                except Exception:
                    logger.error(f"Failed to fetch users from sessions too: {e}")
            else:
                logger.error(f"Failed to fetch active users: {e}")
            return []

    def save_live_schedule(self, schedule_data: List[Dict]):
        """Persists the merged/live schedule to the database."""
        try:
            # We store the entire list as a blob in a 'system_storage' or similar table
            # Or dedicated 'fixtures' table. For simplicity, we'll try a system_config table.
            data = {
                "key": "live_schedule",
                "value": schedule_data,
                "updated_at": datetime.now(timezone.utc).isoformat(),
            }
            self.client.table("system_storage").upsert(data).execute()
            logger.info("💾 Live schedule saved to database.")
        except Exception as e:
            logger.error(f"Failed to save live schedule: {e}")

    def load_live_schedule(self) -> List[Dict]:
        """Loads the last known live schedule from the database."""
        try:
            res = (
                self.client.table("system_storage")
                .select("value")
                .eq("key", "live_schedule")
                .execute()
            )
            if res.data:
                return res.data[0].get("value", [])
        except Exception as e:
            logger.warning(f"Could not load live schedule from DB: {e}")
        return []
