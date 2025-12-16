#!/usr/bin/env python3
"""
Add percentile rank column to ai_scores.db and calculate percentile ranks
for all companies based on their total_score_percentage.
"""

import sqlite3
import os

# Paths
SCORES_DB = os.path.join(os.path.dirname(__file__), 'data', 'ai_scores.db')

def calculate_percentile_rank(score, all_scores):
    """Calculate percentile rank of a score among all scores.
    
    Args:
        score: The score to calculate percentile for (float)
        all_scores: List of all scores to compare against (list of floats)
        
    Returns:
        int: Percentile rank (0-100), or None if no scores to compare
    """
    if not all_scores or len(all_scores) == 0:
        return None
    
    # Count how many scores are less than or equal to this score
    scores_less_or_equal = sum(1 for s in all_scores if s <= score)
    
    # Percentile rank = (number of scores <= this score) / total scores * 100
    percentile = int((scores_less_or_equal / len(all_scores)) * 100)
    return percentile

def add_percentile_rank_column():
    """Add total_score_percentile_rank column to database and calculate values."""
    if not os.path.exists(SCORES_DB):
        print(f"Error: {SCORES_DB} not found")
        return False
    
    print(f"Connecting to {SCORES_DB}...")
    conn = sqlite3.connect(SCORES_DB)
    cursor = conn.cursor()
    
    # Check if column already exists
    cursor.execute('PRAGMA table_info(scores)')
    columns = [row[1] for row in cursor.fetchall()]
    
    if 'total_score_percentile_rank' in columns:
        print("Column 'total_score_percentile_rank' already exists. Updating values...")
    else:
        print("Adding 'total_score_percentile_rank' column...")
        cursor.execute('ALTER TABLE scores ADD COLUMN total_score_percentile_rank INTEGER')
    
    # Get all total_score_percentage values
    print("Fetching all total_score_percentage values...")
    cursor.execute('SELECT ticker, total_score_percentage FROM scores WHERE total_score_percentage IS NOT NULL')
    rows = cursor.fetchall()
    
    if len(rows) == 0:
        print("No scores found in database")
        conn.close()
        return False
    
    # Extract scores for percentile calculation
    all_scores = [row[1] for row in rows if row[1] is not None]
    
    if len(all_scores) == 0:
        print("No valid scores found for percentile calculation")
        conn.close()
        return False
    
    print(f"Calculating percentile ranks for {len(rows)} companies...")
    
    # Calculate and update percentile rank for each company
    updated = 0
    for ticker, score in rows:
        if score is not None:
            percentile_rank = calculate_percentile_rank(score, all_scores)
            cursor.execute(
                'UPDATE scores SET total_score_percentile_rank = ? WHERE ticker = ?',
                (percentile_rank, ticker)
            )
            updated += 1
    
    # Commit changes
    conn.commit()
    conn.close()
    
    print(f"Successfully updated percentile ranks for {updated} companies")
    return True

if __name__ == "__main__":
    success = add_percentile_rank_column()
    if success:
        print("Percentile rank calculation complete!")
    else:
        print("Percentile rank calculation failed!")
        exit(1)

