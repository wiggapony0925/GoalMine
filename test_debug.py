"""
Debug stake calculation
"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from agents.quant.quant import dixon_coles_matrix

print("\n🔍 DEBUGGING STAKE CALCULATION\n")

# Data from test
home_xg = 1.55
away_xg = 1.15
best_odds = {
    "home": {"price": 1.54, "book": "FanDuel"},
    "draw": {"price": 4.2, "book": "Bovada"},
    "away": {"price": 6.5, "book": "FanDuel"},
}
user_budget = 50

probs = dixon_coles_matrix(home_xg, away_xg)

print("📊 For Draw:")
true_prob = probs["draw"]
odds = 4.2
edge = (true_prob * odds) - 1

print(f"   True Probability: {true_prob * 100:.2f}%")
print(f"   Odds: {odds}")
print(f"   Edge: {edge * 100:.2f}%")

# Kelly calculation
b = odds - 1.0  # net odds
p = true_prob
q = 1.0 - p
kelly = (b * p - q) / b
print("\n   Kelly Calculation:")
print(f"   b (net odds) = {b}")
print(f"   p (true prob) = {p:.4f}")
print(f"   q (loss prob) = {q:.4f}")
print(f"   Full Kelly % = {kelly * 100:.2f}%")

# Fractional Kelly
KELLY_FRACTION = 0.20
safe_kelly = max(0, kelly) * KELLY_FRACTION
print(f"   1/5 Kelly % = {safe_kelly * 100:.2f}%")

# Stake
stake = user_budget * safe_kelly
print(f"\n   Budget: ${user_budget}")
print(f"   Stake: ${stake:.2f}")

# Cap check
MAX_EXPOSURE = user_budget * 0.05
print(f"   Max Exposure (5%): ${MAX_EXPOSURE}")
stake = min(stake, MAX_EXPOSURE)
print(f"   Final Stake: ${stake:.2f}")

print("\n📊 For South Africa Win:")
true_prob = probs["b_win"]
odds = 6.5
edge = (true_prob * odds) - 1

# After capping at 25%
if edge > 0.25:
    edge = 0.25
    print("   ⚠️ Edge capped from 73% to 25%")

print(f"   True Probability: {true_prob * 100:.2f}%")
print(f"   Odds: {odds}")
print(f"   Edge (capped): {edge * 100:.2f}%")

# Kelly calculation
b = odds - 1.0
p = true_prob
q = 1.0 - p
kelly = (b * p - q) / b
print("\n   Kelly Calculation:")
print(f"   Full Kelly % = {kelly * 100:.2f}%")

# Fractional Kelly with speculative cap
safe_kelly = max(0, kelly) * KELLY_FRACTION
print(f"   1/5 Kelly % = {safe_kelly * 100:.2f}%")

# Speculative cap
safe_kelly = min(safe_kelly, 0.02)  # 2% max for speculative
print(f"   Speculative cap (2%): {safe_kelly * 100:.2f}%")

stake = user_budget * safe_kelly
print(f"\n   Budget: ${user_budget}")
print(f"   Stake: ${stake:.2f}")
print(f"   Stake > $2 threshold? {stake > 2.0}")
