import sys
import os
import asyncio
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from dotenv import load_dotenv
load_dotenv()

# Mocking query_llm to avoid API calls and just see the data
import core.llm

async def mock_query(system, user, **kwargs):
    print("\n" + "="*50)
    print("🤖 SYSTEM PROMPT IDENTIFIED AS:", system.split('\n')[1]) # Just show identifier
    print("="*50)
    print("\n🔍 RAW DATA FEED (EVIDENCE):")
    # The 'evidence' is part of the user prompt in the agent
    print(user)
    print("\n" + "="*50)
    return "Analysis: Success | Score: 5"

core.llm.query_llm = mock_query

from agents.narrative.api.google_news import fetch_headlines
from agents.narrative.narrative import NarrativeAgent

async def test_data_view():
    agent = NarrativeAgent()
    team = "Manchester United" # Good for testing drama
    print(f"🚀 Running Dual-Scan Deep Intelligence for '{team}'...")
    
    # 1. Injury Scan
    injuries = fetch_headlines(team, query_type="injury", region="GB")
    # 2. Narrative/Drama Scan
    drama = fetch_headlines(team, query_type="narrative", region="GB")
    # 3. Reddit Scan
    reddit_data = await agent.reddit.scan_team_sentiment(team)
    
    all_articles = injuries + drama
    
    from agents.narrative.api.web_scraper import extract_article_text
    deep_content = extract_article_text(all_articles[0].get('link')) if all_articles else None
    
    print("\n" + "="*50)
    print("💎 DUAL-SCAN INTELLIGENCE FEED")
    print("="*50)
    
    print(f"🏥 INJURY UPDATES: {len(injuries)} found")
    for a in injuries[:2]:
        print(f"  - {a['title']}")
        
    print(f"\n🎭 NARRATIVE/DRAMA: {len(drama)} found")
    for a in drama[:2]:
        print(f"  - {a['title']}")
    
    if all_articles:
        print(f"\n🧠 DEEP CONTENT (TOP ARTICLE): {str(deep_content)[:300]}...")
    
    print("\n" + "-"*50)
    
    if reddit_data.get('headlines'):
        for h in reddit_data['headlines'][:2]:
            print(f"💬 REDDIT: {h['title']}")
            if h.get('comments'):
                print(f"🗣️ TOP COMMENTS: {' // '.join(h['comments'])}")
    
    print("="*50)

if __name__ == "__main__":
    asyncio.run(test_data_view())
