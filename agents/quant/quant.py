"""
Elite Quant Engine - Dixon-Coles Model
Professional-grade probability calculations for soccer betting.
"""
import numpy as np
from scipy.stats import poisson
from core.config import settings

def dixon_coles_matrix(lambda_a, lambda_b, rho=-0.13):
    """
    Computes the Dixon-Coles Adjusted Probability Matrix.
    
    Why this is 'Perfect Math':
    Standard Poisson underestimates low-scoring draws (0-0, 1-1). 
    Dixon-Coles applies a correction factor (rho) to these specific scores
    to align with real-world match dynamics.
    
    Args:
        lambda_a: Expected goals for Team A (Home)
        lambda_b: Expected goals for Team B (Away)
        rho: Correlation coefficient (Default -0.13 is standard for top leagues)
    
    Returns:
        dict: Probabilities for home win, draw, away win, and full matrix
    """
    MAX_GOALS = 10
    
    # 1. Generate Base Poisson Vectors (Exact PMF using Scipy)
    # This avoids manual factorial division errors and handles floating point stability
    goals = np.arange(MAX_GOALS)
    pmf_a = poisson.pmf(goals, lambda_a)
    pmf_b = poisson.pmf(goals, lambda_b)
    
    # 2. Create the Independent Matrix (Outer Product)
    # matrix[i, j] = P(Home=i) * P(Away=j)
    matrix = np.outer(pmf_a, pmf_b)
    
    # 3. Apply the Dixon-Coles Correction Factor
    # This corrects the probabilities for 0-0, 0-1, 1-0, and 1-1 scores.
    # Correction formula derived from Dixon & Coles (1997).
    
    # Boundary check: Ensure lambdas are non-zero to prevent division by zero
    l_a = max(lambda_a, 1e-9)
    l_b = max(lambda_b, 1e-9)
    
    # P(0, 0) adjustment
    matrix[0, 0] *= (1.0 - (l_a * l_b * rho))
    
    # P(0, 1) adjustment
    matrix[0, 1] *= (1.0 + (l_a * rho))
    
    # P(1, 0) adjustment
    matrix[1, 0] *= (1.0 + (l_b * rho))
    
    # P(1, 1) adjustment
    matrix[1, 1] *= (1.0 - rho)
    
    # 4. Re-Normalize Matrix
    # Dixon-Coles adjustments can slightly perturb the total sum from 1.0.
    # We re-normalize to ensure Strict Probability Conservation.
    matrix = matrix / np.sum(matrix)
    
    # 5. Sum outcomes
    prob_home = np.sum(np.tril(matrix, -1)) # Lower triangle
    prob_draw = np.sum(np.diag(matrix))     # Diagonal
    prob_away = np.sum(np.triu(matrix, 1))  # Upper triangle
    
    return {
        'a_win': prob_home,
        'draw': prob_draw,
        'b_win': prob_away,
        'matrix': matrix # Returned for specific scoreline debugging
    }


def run_quant_engine(adjusted_xg_a, adjusted_xg_b, best_odds, user_budget=100, team_a_name="Home", team_b_name="Away"):
    """
    Executes the strategy using Perfected Probability inputs.
    
    Args:
        adjusted_xg_a: Expected goals for Team A (adjusted by agents)
        adjusted_xg_b: Expected goals for Team B (adjusted by agents)
        best_odds: Dictionary of best odds from MarketAgent
        user_budget: Total bankroll for Kelly calculations
        team_a_name: Name of Team A (home team)
        team_b_name: Name of Team B (away team)
    
    Returns:
        dict: Probabilities and recommended value bets
    """
    # 1. Get Exact Dixon-Coles Probabilities
    probs = dixon_coles_matrix(adjusted_xg_a, adjusted_xg_b)
    
    value_bets = []
    MIN_EDGE = settings.get('GLOBAL_APP_CONFIG.strategy.min_edge_threshold', 0.04) 
    
    # Kelly Fraction - adjust based on settings or budget fallback
    KELLY_FRACTION = settings.get('GLOBAL_APP_CONFIG.strategy.kelly_multiplier', 0.35)
    
    # Dynamic minimum stake (1% of budget, min $1)
    MIN_STAKE = max(1.0, user_budget * 0.01)
    
    # Map Market Agent keys to probabilities
    # Market Agent returns: {'home': {...}, 'away': {...}, 'draw': {...}}
    mapping = [
        ('home', probs['a_win'], f'{team_a_name} Win'),
        ('draw', probs['draw'], 'Draw'),
        ('away', probs['b_win'], f'{team_b_name} Win')
    ]
    
    for outcome_key, true_prob, display_name in mapping:
        current_odds_data = best_odds.get(outcome_key)
        
        if current_odds_data:
            # Handle potential nested dictionary or direct value
            if isinstance(current_odds_data, dict):
                decimal_odds = float(current_odds_data.get('odds', 0) or current_odds_data.get('price', 0))
                platform = current_odds_data.get('platform', 'Market Consensus') or current_odds_data.get('book', 'Unknown')
            else:
                decimal_odds = 0
                platform = 'Unknown'
            
            if decimal_odds > 1.01:
                # 2. Calculate Expected Value (EV) / Edge
                # Edge = (Probability * Odds) - 1
                edge = (true_prob * decimal_odds) - 1
                
                # SANITY CHECK: Cap unrealistic edges
                # In efficient markets, edges >25% are extremely rare
                # Large "edges" usually indicate model error, not market inefficiency
                MAX_REALISTIC_EDGE = 0.25  # 25% max
                if edge > MAX_REALISTIC_EDGE:
                    # This is likely model noise, not real value
                    # Still include but cap the edge for risk management
                    edge = MAX_REALISTIC_EDGE
                    recommendation = "⚠️ SPECULATIVE"  # Flag as high-risk
                else:
                    recommendation = "💎 VALUE LOCK" if edge > 0.12 else "✅ PLAY"
                
                if edge > MIN_EDGE:
                    # 3. Professional Kelly Criterion (b*p - q) / b
                    # b = net odds (decimal - 1)
                    # p = true probability
                    # q = loss probability (1 - p)
                    
                    b = decimal_odds - 1.0
                    p = true_prob
                    q = 1.0 - p
                    
                    kelly_percentage = (b * p - q) / b
                    
                    # Apply Fractional Kelly for risk management
                    # (Full Kelly is mathematically optimal for growth but ruins bankrolls due to volatility)
                    safe_stake_pct = max(0, kelly_percentage) * KELLY_FRACTION
                    
                    # Additional cap for speculative bets
                    if edge == MAX_REALISTIC_EDGE:
                        safe_stake_pct = min(safe_stake_pct, 0.02)  # Max 2% on speculative
                    
                    stake_amount = round(user_budget * safe_stake_pct, 2)
                    
                    # Sanity Check: Never bet more than Max % of bankroll on one soccer match
                    MAX_EXPOSURE = user_budget * (settings.get('GLOBAL_APP_CONFIG.strategy.max_stake_pct', 5.0) / 100.0)
                    stake_amount = min(stake_amount, MAX_EXPOSURE)
                    
                    if stake_amount >= MIN_STAKE: # Dynamic minimum bet threshold
                        value_bets.append({
                            'market': display_name,
                            'selection': outcome_key,
                            'platform': platform,
                            'odds': decimal_odds,
                            'true_probability': round(true_prob * 100, 1),
                            'implied_probability': round((1/decimal_odds)*100, 1),
                            'edge_percent': round(edge * 100, 2),
                            'stake': stake_amount,
                            'recommendation': recommendation
                        })
    
    # Sort by mathematical edge
    top_plays = sorted(value_bets, key=lambda x: x['edge_percent'], reverse=True)
    
    return {
        'probabilities': {
            'team_a_win': round(probs['a_win'] * 100, 1),
            'draw': round(probs['draw'] * 100, 1),
            'team_b_win': round(probs['b_win'] * 100, 1),
        },
        'top_plays': top_plays
    }
