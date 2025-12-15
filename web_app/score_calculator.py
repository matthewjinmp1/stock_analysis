#!/usr/bin/env python3
"""
Score calculation module for web app.
Contains weights and score definitions from AI_stock_scorer.
"""

# Score weightings - from AI_stock_scorer/src/scoring/scorer.py
SCORE_WEIGHTS = {
    'moat_score': 10,
    'barriers_score': 10,
    'disruption_risk': 10,
    'switching_cost': 10,
    'brand_strength': 10, 
    'competition_intensity': 10,
    'network_effect': 10,
    'product_differentiation': 10,
    'innovativeness_score': 10,
    'growth_opportunity': 10,
    'riskiness_score': 10,
    'pricing_power': 10,
    'ambition_score': 10,
    'bargaining_power_of_customers': 10,
    'bargaining_power_of_suppliers': 10,
    'product_quality_score': 10,
    'culture_employee_satisfaction_score': 10,
    'trailblazer_score': 10,
    'management_quality_score': 10,
    'ai_knowledge_score': 10, 
    'size_well_known_score': 19.31,
    'ethical_healthy_environmental_score': 10,
    'long_term_orientation_score': 10,
}

# Score definitions with is_reverse flag - from AI_stock_scorer/src/scoring/scorer.py
SCORE_DEFINITIONS = {
    'moat_score': {'is_reverse': False},
    'barriers_score': {'is_reverse': False},
    'disruption_risk': {'is_reverse': True},
    'switching_cost': {'is_reverse': False},
    'brand_strength': {'is_reverse': False},
    'competition_intensity': {'is_reverse': True},
    'network_effect': {'is_reverse': False},
    'product_differentiation': {'is_reverse': False},
    'innovativeness_score': {'is_reverse': False},
    'growth_opportunity': {'is_reverse': False},
    'riskiness_score': {'is_reverse': True},
    'pricing_power': {'is_reverse': False},
    'ambition_score': {'is_reverse': False},
    'bargaining_power_of_customers': {'is_reverse': True},
    'bargaining_power_of_suppliers': {'is_reverse': True},
    'product_quality_score': {'is_reverse': False},
    'culture_employee_satisfaction_score': {'is_reverse': False},
    'trailblazer_score': {'is_reverse': False},
    'management_quality_score': {'is_reverse': False},
    'ai_knowledge_score': {'is_reverse': False},
    'size_well_known_score': {'is_reverse': True},
    'ethical_healthy_environmental_score': {'is_reverse': False},
    'long_term_orientation_score': {'is_reverse': False},
}


def calculate_total_score(scores_dict):
    """Calculate total score from a dictionary of scores.
    
    Args:
        scores_dict: Dictionary with score keys and their string values
        
    Returns:
        tuple: (total_score, max_score, percentage) where:
            - total_score: The total weighted score (float)
            - max_score: Maximum possible score (float)
            - percentage: Total score as percentage (float)
    """
    total = 0.0
    for score_key in SCORE_DEFINITIONS:
        score_def = SCORE_DEFINITIONS[score_key]
        weight = SCORE_WEIGHTS.get(score_key, 1.0)  # Default to 1.0 if weight not found
        try:
            score_value = float(scores_dict.get(score_key, 0) or 0)
            # For reverse scores, invert to get "goodness" value
            if score_def['is_reverse']:
                total += (10 - score_value) * weight
            else:
                total += score_value * weight
        except (ValueError, TypeError):
            pass
    
    # Calculate max possible score with weights
    max_score = sum(SCORE_WEIGHTS.get(key, 1.0) for key in SCORE_DEFINITIONS) * 10
    percentage = (total / max_score) * 100 if max_score > 0 else 0.0
    
    return total, max_score, percentage
