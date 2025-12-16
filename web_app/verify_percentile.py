#!/usr/bin/env python3
"""Quick verification script for percentile ranks."""

import sqlite3
import os

SCORES_DB = os.path.join(os.path.dirname(__file__), 'data', 'ai_scores.db')

conn = sqlite3.connect(SCORES_DB)
cursor = conn.cursor()

# Check columns
cursor.execute('PRAGMA table_info(scores)')
cols = cursor.fetchall()
print('Relevant database columns:')
for col in cols:
    if 'percentile' in col[1] or 'percentage' in col[1] or col[1] == 'ticker':
        print(f'  {col[1]:<30} {col[2]:<10}')

# Count companies with percentile rank
cursor.execute('SELECT COUNT(*) FROM scores WHERE total_score_percentile_rank IS NOT NULL')
count = cursor.fetchone()[0]
print(f'\nCompanies with percentile rank: {count}')

# Get percentile statistics
cursor.execute('SELECT MIN(total_score_percentile_rank), MAX(total_score_percentile_rank), AVG(total_score_percentile_rank) FROM scores WHERE total_score_percentile_rank IS NOT NULL')
min_p, max_p, avg_p = cursor.fetchone()
print(f'Percentile range: {min_p} - {max_p}, Average: {avg_p:.1f}')

# Show sample of companies at different percentile levels
print('\nSample companies at different percentile levels:')
cursor.execute('SELECT ticker, total_score_percentage, total_score_percentile_rank FROM scores WHERE total_score_percentile_rank IS NOT NULL ORDER BY total_score_percentile_rank DESC LIMIT 5')
print('Top 5:')
for row in cursor.fetchall():
    print(f'  {row[0]:<6} | Score: {row[1]:>6.2f}% | Percentile: {row[2]:>3}')

cursor.execute('SELECT ticker, total_score_percentage, total_score_percentile_rank FROM scores WHERE total_score_percentile_rank IS NOT NULL ORDER BY total_score_percentile_rank ASC LIMIT 5')
print('\nBottom 5:')
for row in cursor.fetchall():
    print(f'  {row[0]:<6} | Score: {row[1]:>6.2f}% | Percentile: {row[2]:>3}')

conn.close()

