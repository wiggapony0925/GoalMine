"""
GoalMine Terminal Test - Test the full analysis pipeline
"""
import asyncio
import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from agents.quant.quant import run_quant_engine, dixon_coles_matrix

def test_quant_engine():
    """Test the Quant Engine with realistic data"""
    print("\n" + "="*60)
    print("🧪 TESTING QUANT ENGINE")
    print("="*60)
    
    # Realistic xG from the logs
    home_xg = 1.55  # Mexico
    away_xg = 1.15  # South Africa
    
    print(f"\n📊 Input:")
    print(f"   Home xG (Mexico): {home_xg}")
    print(f"   Away xG (South Africa): {away_xg}")
    
    # Test Dixon-Coles probabilities
    probs = dixon_coles_matrix(home_xg, away_xg)
    print(f"\n🎯 Dixon-Coles Probabilities:")
    print(f"   Mexico Win: {probs['a_win']*100:.1f}%")
    print(f"   Draw: {probs['draw']*100:.1f}%")
    print(f"   South Africa Win: {probs['b_win']*100:.1f}%")
    
    # Real odds from the logs
    best_odds = {
        'home': {'price': 1.54, 'book': 'FanDuel'},
        'draw': {'price': 4.2, 'book': 'Bovada'},
        'away': {'price': 6.5, 'book': 'FanDuel'}
    }
    
    print(f"\n💰 Market Odds:")
    print(f"   Mexico Win: {best_odds['home']['price']} ({best_odds['home']['book']})")
    print(f"   Draw: {best_odds['draw']['price']} ({best_odds['draw']['book']})")
    print(f"   South Africa Win: {best_odds['away']['price']} ({best_odds['away']['book']})")
    
    # Calculate implied probabilities
    print(f"\n📈 Implied Probabilities (from odds):")
    print(f"   Mexico Win: {(1/1.54)*100:.1f}%")
    print(f"   Draw: {(1/4.2)*100:.1f}%")
    print(f"   South Africa Win: {(1/6.5)*100:.1f}%")
    
    # Run Quant Engine
    user_budget = 50
    result = run_quant_engine(home_xg, away_xg, best_odds, user_budget, "Mexico", "South Africa")
    
    print(f"\n🤖 Quant Engine Result (Budget: ${user_budget}):")
    print(f"\n   Probabilities:")
    print(f"   - Mexico Win: {result['probabilities']['team_a_win']}%")
    print(f"   - Draw: {result['probabilities']['draw']}%")
    print(f"   - South Africa Win: {result['probabilities']['team_b_win']}%")
    
    print(f"\n   💎 Value Plays Identified:")
    if result['top_plays']:
        for i, play in enumerate(result['top_plays'], 1):
            print(f"\n   {i}. {play['market']} @ {play['odds']} ({play['platform']})")
            print(f"      Edge: {play['edge_percent']}%")
            print(f"      True Prob: {play['true_probability']}% vs Implied: {play['implied_probability']}%")
            print(f"      Stake: ${play['stake']}")
            print(f"      Recommendation: {play['recommendation']}")
    else:
        print("   ⚠️ No value plays found (edges < 4%)")
    
    # Manual edge calculation check
    print(f"\n🔍 EDGE VERIFICATION:")
    for outcome, key in [("Mexico Win", "home"), ("Draw", "draw"), ("South Africa Win", "away")]:
        true_prob = probs['a_win' if key == 'home' else ('draw' if key == 'draw' else 'b_win')]
        odds = best_odds[key]['price']
        implied_prob = 1 / odds
        edge = (true_prob * odds) - 1
        
        print(f"\n   {outcome}:")
        print(f"      Model Probability: {true_prob*100:.1f}%")
        print(f"      Implied Probability: {implied_prob*100:.1f}%")
        print(f"      Raw Edge: {edge*100:.2f}%")
        print(f"      Edge Status: {'✅ VALUE' if edge > 0.04 else '❌ NO VALUE'}")

def test_with_different_budgets():
    """Test stake sizing with different budgets"""
    print("\n" + "="*60)
    print("🧪 TESTING STAKE SIZING")
    print("="*60)
    
    home_xg = 1.55
    away_xg = 1.15
    best_odds = {
        'home': {'price': 1.54, 'book': 'FanDuel'},
        'draw': {'price': 4.2, 'book': 'Bovada'},
        'away': {'price': 6.5, 'book': 'FanDuel'}
    }
    
    for budget in [50, 100, 500, 1000]:
        result = run_quant_engine(home_xg, away_xg, best_odds, budget, "Mexico", "South Africa")
        print(f"\n💵 Budget: ${budget}")
        if result['top_plays']:
            total_stake = sum(p['stake'] for p in result['top_plays'])
            print(f"   Total Stake: ${total_stake:.2f} ({total_stake/budget*100:.1f}% of bankroll)")
            for play in result['top_plays']:
                print(f"   - {play['market']}: ${play['stake']} @ {play['odds']}")
        else:
            print("   No value plays")

def test_edge_cases():
    """Test edge cases"""
    print("\n" + "="*60)
    print("🧪 TESTING EDGE CASES")
    print("="*60)
    
    # Case 1: Very close xG (should be close to draw)
    print("\n📊 Case 1: Close xG (1.2 vs 1.1)")
    probs = dixon_coles_matrix(1.2, 1.1)
    print(f"   Home: {probs['a_win']*100:.1f}% | Draw: {probs['draw']*100:.1f}% | Away: {probs['b_win']*100:.1f}%")
    
    # Case 2: Dominant team
    print("\n📊 Case 2: Dominant Team (2.5 vs 0.8)")
    probs = dixon_coles_matrix(2.5, 0.8)
    print(f"   Home: {probs['a_win']*100:.1f}% | Draw: {probs['draw']*100:.1f}% | Away: {probs['b_win']*100:.1f}%")
    
    # Case 3: Underdog
    print("\n📊 Case 3: Underdog Home (0.8 vs 1.8)")
    probs = dixon_coles_matrix(0.8, 1.8)
    print(f"   Home: {probs['a_win']*100:.1f}% | Draw: {probs['draw']*100:.1f}% | Away: {probs['b_win']*100:.1f}%")

if __name__ == "__main__":
    print("\n" + "🏆"*20)
    print("   GOALMINE QUANT ENGINE TEST")
    print("🏆"*20)
    
    test_quant_engine()
    test_with_different_budgets()
    test_edge_cases()
    
    print("\n" + "="*60)
    print("✅ ALL TESTS COMPLETE")
    print("="*60 + "\n")
