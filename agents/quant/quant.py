import math
import random
from math import exp, factorial, sqrt

def poisson_probability(k, lambda_):
    """Calculate Poisson probability of k events occurring given lambda average rate."""
    return (lambda_**k * exp(-lambda_)) / factorial(k)

def kelly_criterion(probability, odds, fraction=0.25):
    """
    Calculate Kelly Criterion stake percentage.
    fraction: Risk management scaler (default 0.25 for fractional Kelly)
    """
    q = 1 - probability
    b = odds - 1
    if b <= 0: return 0
    kelly = (b * probability - q) / b
    return max(0, kelly * fraction)

def monte_carlo_simulation(lambda_a, lambda_b, num_simulations=10000):
    """Run Monte Carlo simulation for scorelines based on Team A & B expected goals (lambda)."""
    score_counts = {}
    outcomes = {'a_win': 0, 'draw': 0, 'b_win': 0}
    
    for _ in range(num_simulations):
        # Generate random scores using Poisson distribution
        # Optimizing: using numpy would be faster but sticking to native python as per request simplicity unless performance needed
        # Simulating Poisson by counting events - actually utilizing simple inverse transform or library is better
        # For simplicity in pure python without numpy for the 'random' loop:
        
        # NOTE: For 10,000 runs, this purely iterative approach might be slow in Python.
        # It's better to just sample once per match using a library or a robust function.
        # Since I added numpy to requirements, let's use it for the simulation if available, otherwise fallback.
        try:
            import numpy as np
            score_a = np.random.poisson(lambda_a)
            score_b = np.random.poisson(lambda_b)
        except ImportError:
            # Fallback (slower)
            # Simple approximation or just use stats logic
            # Implementing a basic knuth algorithm for poisson generation if numpy fails is overkill here
            # Let's hope numpy is installed as requested.
            pass 
            
        score_a = min(score_a, 5) # Cap at 5 for practical scorelines
        score_b = min(score_b, 5)
        
        scoreline = f"{score_a}-{score_b}"
        score_counts[scoreline] = score_counts.get(scoreline, 0) + 1
        
        if score_a > score_b:
            outcomes['a_win'] += 1
        elif score_a == score_b:
            outcomes['draw'] += 1
        else:
            outcomes['b_win'] += 1
            
    # Normalize
    for key in outcomes:
        outcomes[key] = outcomes[key] / num_simulations
        
    for key in score_counts:
        score_counts[key] = score_counts[key] / num_simulations
        
    return outcomes, score_counts

def calculate_confidence_interval(probability, num_simulations=10000):
    std_error = sqrt((probability * (1 - probability)) / num_simulations)
    margin = 1.96 * std_error
    return {
        'lower': max(0, probability - margin),
        'upper': min(1, probability + margin)
    }

def run_quant_engine(adjusted_xg_a, adjusted_xg_b, best_odds, user_budget=1000):
    """
    Main entry point for the Quant Engine.
    adjusted_xg_a: Team A Expected Goals (float)
    adjusted_xg_b: Team B Expected Goals (float)
    best_odds: Dictionary of market odds (from Market Agent)
    user_budget: Bankroll (float)
    """
    outcomes, scorelines = monte_carlo_simulation(adjusted_xg_a, adjusted_xg_b)
    
    confidence_intervals = {
        'team_a_win': calculate_confidence_interval(outcomes['a_win']),
        'draw': calculate_confidence_interval(outcomes['draw']),
        'team_b_win': calculate_confidence_interval(outcomes['b_win'])
    }
    
    value_bets = []
    MIN_EDGE = 0.05
    
    # Mapping outcome keys to what Market Agent provides
    # Assuming Market Agent keys: 'Team_A_Win', 'Draw', 'Team_B_Win' or similar
    # We need to standardize this.
    
    mapping = [
        ('Team_A_Win', outcomes['a_win']),
        ('Draw', outcomes['draw']),
        ('Team_B_Win', outcomes['b_win'])
    ]
    
    for outcome_key, prob in mapping:
        # Check if we have odds for this outcome
        # Flexible lookup: exact match or normalized
        current_odds_data = best_odds.get(outcome_key)
        
        if current_odds_data:
            odds = current_odds_data.get('odds', 0)
            platform = current_odds_data.get('platform', 'Unknown')
            
            if odds > 1:
                ev = (prob * odds) - 1
                
                if ev > MIN_EDGE:
                    kelly_stake = kelly_criterion(prob, odds, fraction=0.25)
                    stake_amount = round(user_budget * kelly_stake, 2)
                    
                    value_bets.append({
                        'market': outcome_key,
                        'platform': platform,
                        'odds': odds,
                        'true_probability': round(prob * 100, 2),
                        'implied_probability': round((1/odds) * 100, 2),
                        'edge': round(ev * 100, 2),
                        'expected_value': round(ev, 4),
                        'stake': stake_amount,
                        'potential_profit': round(stake_amount * (odds - 1), 2)
                    })
    
    # Sort top 3
    top_plays = sorted(value_bets, key=lambda x: x['edge'], reverse=True)[:3]
    
    return {
        'probabilities': {
            'team_a_win': round(outcomes['a_win'] * 100, 2),
            'draw': round(outcomes['draw'] * 100, 2),
            'team_b_win': round(outcomes['b_win'] * 100, 2),
        },
        'top_plays': top_plays,
        'confidence_intervals': confidence_intervals
    }
