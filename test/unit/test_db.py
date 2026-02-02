import os
from dotenv import load_dotenv
from core.initializer.database import Database

def test_connection():
    load_dotenv()
    print("🚀 Testing Supabase Connection...")
    try:
        db = Database()
        test_data = {"test": "success", "message": "Supabase Logic Verified"}
        db.save_memory("test_user_123", test_data)
        
        loaded = db.load_memory("test_user_123")
        if loaded and loaded.get("test") == "success":
            print("✅ CONNECTION SUCCESS: Data saved and retrieved from Supabase!")
        else:
            print("❌ FAILURE: Data retrieved does not match or is empty.")
    except Exception as e:
        print(f"❌ ERROR: {e}")

if __name__ == "__main__":
    test_connection()
