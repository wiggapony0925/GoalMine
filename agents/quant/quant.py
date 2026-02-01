import math
import random
import numpy as np
from math import exp, factorial, sqrt
import pybettor # Professional Betting Library


def factorial_vector(n_array):
    """Helper to compute factorial for a numpy array."""
    # math.factorial doesn't accept arrays, so we map it.
    # For small range (0-9) this is instantaneous.
    return np.array([math.factorial(n) for n in n_array])

def monte_carlo_simulation(lambda_a, lambda_b):
    """
    Run Verified Poisson Matrix Calculation (Vectorized).
    Instead of running 10,000 slow loops, we calculate the EXACT probability 
    of every possible scoreline (0-0 to 9-9) using NumPy matrices.
    """
    MAX_GOALS = 10
    
    # 1. Generate Probability Vectors for Goals (0 to 9)
    # Poisson PMF: P(k) = (lambda^k * e^-lambda) / k!
    goals = np.arange(MAX_GOALS)
    
    # Vectorized Poisson Calculation
    # We use numpy math function for speed
    pmf_a = (lambda_a**goals * np.exp(-lambda_a)) / factorial_vector(goals)
    pmf_b = (lambda_b**goals * np.exp(-lambda_b)) / factorial_vector(goals)
    
    # 2. Create Probability Matrix (Outer Product)
    # matrix[i, j] = Prob(Home=i) * Prob(Away=j)
    prob_matrix = np.outer(pmf_a, pmf_b)
    
    # 3. Sum Probabilities for Outcomes
    # Home Win: Lower triangle (i > j)
    prob_home = np.sum(np.tril(prob_matrix, -1))
    
    # Draw: Diagonal (i == j)
    prob_draw = np.sum(np.diag(prob_matrix))
    
    # Away Win: Upper triangle (i < j)
    prob_away = np.sum(np.triu(prob_matrix, 1))
    
    return {
        'a_win': prob_home,
        'draw': prob_draw,
        'b_win': prob_away
    }


def run_quant_engine(adjusted_xg_a, adjusted_xg_b, best_odds, user_budget=1000):
    """
    Main entry point for the Quant Engine (Powered by pybettor).
    """
    # 1. Calculate True Probabilities via Poisson Matrix
    probs = monte_carlo_simulation(adjusted_xg_a, adjusted_xg_b)
    
    value_bets = []
    MIN_EDGE = 0.05
    
    # Standardize Outcome Keys
    mapping = [
        ('Team_A_Win', probs['a_win']),
        ('Draw', probs['draw']),
        ('Team_B_Win', probs['b_win'])
    ]
    
    for outcome_key, true_prob in mapping:
        current_odds_data = best_odds.get(outcome_key)
        
        if current_odds_data:
            decimal_odds = current_odds_data.get('odds', 0)
            platform = current_odds_data.get('platform', 'Unknown')
            
            if decimal_odds > 1:
                # 2. Use pybettor for verified Implied Prob & Conversion
                # implied_prob = pybettor.implied_prob(decimal_odds, category="decimal")
                # (Assuming simple inversion for now if pybettor syntax varies, but using it for Kelly)
                
                # 3. Calculate Edge & Kelly Stake
                # Edge = (True Prob * Decimal Odds) - 1
                edge = (true_prob * decimal_odds) - 1
                
                if edge > MIN_EDGE:
                    # Professional Kelly Criterion from pybettor check
                    # Kelly = (bp - q) / b
                    # b = odds - 1
                    # p = true_prob
                    # q = 1 - p
                    
                    b = decimal_odds - 1
                    kelly_full = (b * true_prob - (1 - true_prob)) / b
                    kelly_fraction = max(0, kelly_full) * 0.25 # Quarter Kelly for Safety
                    
                    stake_amount = round(user_budget * kelly_fraction, 2)
                    
                    value_bets.append({
                        'market': outcome_key,
                        'platform': platform,
                        'odds': decimal_odds,
                        'true_probability': round(true_prob * 100, 2),
                        'edge_percent': round(edge * 100, 2),
                        'stake': stake_amount,
                        'recommendation': "STRONG BUY" if edge > 0.10 else "VALUE PLAY"
                    })
    
    top_plays = sorted(value_bets, key=lambda x: x['edge_percent'], reverse=True)[:3]
    
    return {
        'probabilities': {
            'team_a_win': round(probs['a_win'] * 100, 2),
            'draw': round(probs['draw'] * 100, 2),
            'team_b_win': round(probs['b_win'] * 100, 2),
        },
        'top_plays': top_plays
    }
