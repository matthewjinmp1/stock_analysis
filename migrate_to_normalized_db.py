#!/usr/bin/env python3
"""
Migration script to consolidate multiple databases into a single normalized database.
"""
import sqlite3
import os
import shutil
from datetime import datetime
import sys

# Project paths
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
WEB_APP_DIR = os.path.join(PROJECT_ROOT, 'web_app')
DATA_DIR = os.path.join(WEB_APP_DIR, 'data')
NEW_DB_PATH = os.path.join(DATA_DIR, 'consolidated.db')
SCHEMA_FILE = os.path.join(PROJECT_ROOT, 'normalized_schema.sql')

def create_backup():
    """Create backups of existing databases."""
    backup_dir = os.path.join(DATA_DIR, 'backup_' + datetime.now().strftime('%Y%m%d_%H%M%S'))
    os.makedirs(backup_dir, exist_ok=True)

    old_dbs = [
        'ui_cache.db', 'ai_scores.db', 'financial_scores.db',
        'adjusted_pe.db', 'watchlist.db', 'peers.db', 'tickers.db'
    ]

    for db_name in old_dbs:
        db_path = os.path.join(DATA_DIR, db_name)
        if os.path.exists(db_path):
            shutil.copy2(db_path, os.path.join(backup_dir, db_name))
            print(f"Backed up {db_name}")

    return backup_dir

def create_normalized_database():
    """Create the new normalized database from schema."""
    if not os.path.exists(SCHEMA_FILE):
        raise FileNotFoundError(f"Schema file not found: {SCHEMA_FILE}")

    # Remove existing consolidated db if it exists
    if os.path.exists(NEW_DB_PATH):
        os.remove(NEW_DB_PATH)

    # Create new database
    conn = sqlite3.connect(NEW_DB_PATH)
    cursor = conn.cursor()

    # Read and execute schema
    with open(SCHEMA_FILE, 'r') as f:
        schema_sql = f.read()

    cursor.executescript(schema_sql)
    conn.commit()
    conn.close()

    print(f"Created normalized database at {NEW_DB_PATH}")
    return NEW_DB_PATH

def migrate_tickers_data():
    """Migrate tickers data to companies and ticker_aliases tables."""
    tickers_db = os.path.join(DATA_DIR, 'tickers.db')
    if not os.path.exists(tickers_db):
        print("Tickers database not found, skipping...")
        return

    conn = sqlite3.connect(NEW_DB_PATH)
    cursor = conn.cursor()

    # Connect to source database
    source_conn = sqlite3.connect(tickers_db)
    source_cursor = source_conn.cursor()

    # Get all tickers
    source_cursor.execute("SELECT ticker, company_name, source FROM tickers")
    tickers_data = source_cursor.fetchall()

    migrated = 0
    for ticker, company_name, source in tickers_data:
        if not ticker or not company_name:
            continue

        # Insert into companies table
        cursor.execute("""
            INSERT INTO companies (ticker, company_name, exchange)
            VALUES (?, ?, ?)
        """, (ticker.upper(), company_name, source))

        company_id = cursor.lastrowid

        # Insert into ticker_aliases as primary
        cursor.execute("""
            INSERT INTO ticker_aliases (company_id, ticker, is_primary)
            VALUES (?, ?, ?)
        """, (company_id, ticker.upper(), True))

        migrated += 1

    conn.commit()
    source_conn.close()
    conn.close()

    print(f"Migrated {migrated} tickers to companies and ticker_aliases")

def migrate_ai_scores_data():
    """Migrate AI scores data."""
    ai_scores_db = os.path.join(DATA_DIR, 'ai_scores.db')
    if not os.path.exists(ai_scores_db):
        print("AI scores database not found, skipping...")
        return

    conn = sqlite3.connect(NEW_DB_PATH)
    cursor = conn.cursor()

    # Connect to source database
    source_conn = sqlite3.connect(ai_scores_db)
    source_cursor = source_conn.cursor()

    # Get all scores
    source_cursor.execute("SELECT * FROM scores")
    columns = [desc[0] for desc in source_cursor.description]
    scores_data = source_cursor.fetchall()

    migrated = 0
    for row in scores_data:
        score_dict = dict(zip(columns, row))
        ticker = score_dict.pop('ticker', None)

        if not ticker:
            continue

        # Get company_id
        cursor.execute("SELECT id FROM companies WHERE ticker = ?", (ticker.upper(),))
        company_result = cursor.fetchone()

        if not company_result:
            print(f"Warning: Company not found for ticker {ticker}, skipping AI scores")
            continue

        company_id = company_result[0]

        # Prepare AI scores insert
        score_columns = [col for col in score_dict.keys() if col != 'ticker']
        placeholders = ', '.join(['?' for _ in score_columns])
        values = [score_dict[col] for col in score_columns]

        insert_sql = f"""
            INSERT INTO ai_scores (company_id, {', '.join(score_columns)})
            VALUES (?, {placeholders})
        """

        try:
            cursor.execute(insert_sql, [company_id] + values)
            migrated += 1
        except Exception as e:
            print(f"Error migrating AI scores for {ticker}: {e}")

    conn.commit()
    source_conn.close()
    conn.close()

    print(f"Migrated {migrated} AI scores")

def migrate_financial_scores_data():
    """Migrate financial scores data."""
    financial_scores_db = os.path.join(DATA_DIR, 'financial_scores.db')
    if not os.path.exists(financial_scores_db):
        print("Financial scores database not found, skipping...")
        return

    conn = sqlite3.connect(NEW_DB_PATH)
    cursor = conn.cursor()

    # Connect to source database
    source_conn = sqlite3.connect(financial_scores_db)
    source_cursor = source_conn.cursor()

    # Get all financial scores
    source_cursor.execute("SELECT * FROM financial_scores")
    columns = [desc[0] for desc in source_cursor.description]
    financial_data = source_cursor.fetchall()

    migrated = 0
    for row in financial_data:
        data_dict = dict(zip(columns, row))
        ticker = data_dict.pop('ticker', None)
        company_name = data_dict.pop('company_name', None)  # Remove from insert

        if not ticker:
            continue

        # Get company_id
        cursor.execute("SELECT id FROM companies WHERE ticker = ?", (ticker.upper(),))
        company_result = cursor.fetchone()

        if not company_result:
            print(f"Warning: Company not found for ticker {ticker}, skipping financial scores")
            continue

        company_id = company_result[0]

        # Prepare financial scores insert
        score_columns = [col for col in data_dict.keys()]
        placeholders = ', '.join(['?' for _ in score_columns])
        values = [data_dict[col] for col in score_columns]

        insert_sql = f"""
            INSERT INTO financial_scores (company_id, {', '.join(score_columns)})
            VALUES (?, {placeholders})
        """

        try:
            cursor.execute(insert_sql, [company_id] + values)
            migrated += 1
        except Exception as e:
            print(f"Error migrating financial scores for {ticker}: {e}")
            # If it's the exchange column issue, try without exchange
            if 'exchange' in str(e):
                try:
                    # Remove exchange from data_dict if it exists
                    data_dict_no_exchange = {k: v for k, v in data_dict.items() if k != 'exchange'}
                    score_columns_no_exchange = [col for col in data_dict_no_exchange.keys()]
                    placeholders_no_exchange = ', '.join(['?' for _ in score_columns_no_exchange])
                    values_no_exchange = [data_dict_no_exchange[col] for col in score_columns_no_exchange]

                    insert_sql_no_exchange = f"""
                        INSERT INTO financial_scores (company_id, {', '.join(score_columns_no_exchange)})
                        VALUES (?, {placeholders_no_exchange})
                    """
                    cursor.execute(insert_sql_no_exchange, [company_id] + values_no_exchange)
                    migrated += 1
                    print(f"Successfully migrated {ticker} without exchange column")
                except Exception as e2:
                    print(f"Still failed for {ticker}: {e2}")
            else:
                print(f"Error migrating financial scores for {ticker}: {e}")

    conn.commit()
    source_conn.close()
    conn.close()

    print(f"Migrated {migrated} financial scores")

def migrate_adjusted_pe_data():
    """Migrate adjusted PE data."""
    adjusted_pe_db = os.path.join(DATA_DIR, 'adjusted_pe.db')
    if not os.path.exists(adjusted_pe_db):
        print("Adjusted PE database not found, skipping...")
        return

    conn = sqlite3.connect(NEW_DB_PATH)
    cursor = conn.cursor()

    # Connect to source database
    source_conn = sqlite3.connect(adjusted_pe_db)
    source_cursor = source_conn.cursor()

    # Get all adjusted PE data
    source_cursor.execute("SELECT * FROM adjusted_pe")
    columns = [desc[0] for desc in source_cursor.description]
    pe_data = source_cursor.fetchall()

    migrated = 0
    for row in pe_data:
        data_dict = dict(zip(columns, row))
        ticker = data_dict.pop('ticker', None)

        if not ticker:
            continue

        # Get company_id
        cursor.execute("SELECT id FROM companies WHERE ticker = ?", (ticker.upper(),))
        company_result = cursor.fetchone()

        if not company_result:
            print(f"Warning: Company not found for ticker {ticker}, skipping adjusted PE")
            continue

        company_id = company_result[0]

        # Prepare adjusted PE insert
        pe_columns = [col for col in data_dict.keys()]
        placeholders = ', '.join(['?' for _ in pe_columns])
        values = [data_dict[col] for col in pe_columns]

        insert_sql = f"""
            INSERT INTO adjusted_pe_calculations (company_id, {', '.join(pe_columns)})
            VALUES (?, {placeholders})
        """

        try:
            cursor.execute(insert_sql, [company_id] + values)
            migrated += 1
        except Exception as e:
            print(f"Error migrating adjusted PE for {ticker}: {e}")

    conn.commit()
    source_conn.close()
    conn.close()

    print(f"Migrated {migrated} adjusted PE calculations")

def migrate_watchlist_data():
    """Migrate watchlist data."""
    watchlist_db = os.path.join(DATA_DIR, 'watchlist.db')
    if not os.path.exists(watchlist_db):
        print("Watchlist database not found, skipping...")
        return

    conn = sqlite3.connect(NEW_DB_PATH)
    cursor = conn.cursor()

    # Connect to source database
    source_conn = sqlite3.connect(watchlist_db)
    source_cursor = source_conn.cursor()

    # Get all watchlist entries
    source_cursor.execute("SELECT ticker, added_at FROM watchlist")
    watchlist_data = source_cursor.fetchall()

    migrated = 0
    for ticker, added_at in watchlist_data:
        # Get company_id
        cursor.execute("SELECT id FROM companies WHERE ticker = ?", (ticker.upper(),))
        company_result = cursor.fetchone()

        if not company_result:
            print(f"Warning: Company not found for watchlist ticker {ticker}, skipping")
            continue

        company_id = company_result[0]

        # Insert into watchlist
        cursor.execute("""
            INSERT INTO watchlist (company_id, added_at)
            VALUES (?, ?)
        """, (company_id, added_at))

        migrated += 1

    conn.commit()
    source_conn.close()
    conn.close()

    print(f"Migrated {migrated} watchlist entries")

def migrate_ui_cache_additional_data():
    """Migrate additional data from ui_cache that isn't in other tables."""
    ui_cache_db = os.path.join(DATA_DIR, 'ui_cache.db')
    if not os.path.exists(ui_cache_db):
        print("UI cache database not found, skipping...")
        return

    conn = sqlite3.connect(NEW_DB_PATH)
    cursor = conn.cursor()

    # Connect to source database
    source_conn = sqlite3.connect(ui_cache_db)
    source_cursor = source_conn.cursor()

    # Get UI cache data
    source_cursor.execute("SELECT * FROM ui_cache")
    columns = [desc[0] for desc in source_cursor.description]
    ui_cache_data = source_cursor.fetchall()

    growth_migrated = 0
    short_interest_migrated = 0

    for row in ui_cache_data:
        data_dict = dict(zip(columns, row))
        ticker = data_dict.get('ticker')

        if not ticker:
            continue

        # Get company_id
        cursor.execute("SELECT id FROM companies WHERE ticker = ?", (ticker.upper(),))
        company_result = cursor.fetchone()

        if not company_result:
            continue

        company_id = company_result[0]

        # Migrate growth estimates
        current_year_growth = data_dict.get('current_year_growth')
        next_year_growth = data_dict.get('next_year_growth')

        if current_year_growth is not None or next_year_growth is not None:
            cursor.execute("""
                INSERT OR REPLACE INTO growth_estimates (company_id, current_year_growth, next_year_growth)
                VALUES (?, ?, ?)
            """, (company_id, current_year_growth, next_year_growth))
            growth_migrated += 1

        # Migrate short interest
        short_float = data_dict.get('short_float')
        short_interest_scraped_at = data_dict.get('short_interest_scraped_at')

        if short_float is not None:
            cursor.execute("""
                INSERT OR REPLACE INTO short_interest (company_id, short_float, scraped_at)
                VALUES (?, ?, ?)
            """, (company_id, short_float, short_interest_scraped_at))
            short_interest_migrated += 1

    conn.commit()
    source_conn.close()
    conn.close()

    print(f"Migrated {growth_migrated} growth estimates")
    print(f"Migrated {short_interest_migrated} short interest records")

def validate_migration():
    """Validate that migration was successful."""
    conn = sqlite3.connect(NEW_DB_PATH)
    cursor = conn.cursor()

    # Check table counts
    tables = ['companies', 'ai_scores', 'financial_scores', 'adjusted_pe_calculations',
              'growth_estimates', 'short_interest', 'watchlist', 'ticker_aliases']

    print("\nMigration validation:")
    for table in tables:
        cursor.execute(f"SELECT COUNT(*) FROM {table}")
        count = cursor.fetchone()[0]
        print(f"  {table}: {count} records")

    conn.close()

def main():
    """Main migration function."""
    print("Starting database consolidation migration...")

    # Create backup
    print("Creating backups...")
    backup_dir = create_backup()
    print(f"Backups created in: {backup_dir}")

    try:
        # Create normalized database
        print("\nCreating normalized database...")
        create_normalized_database()

        # Migrate data in order
        print("\nMigrating tickers data...")
        migrate_tickers_data()

        print("\nMigrating AI scores...")
        migrate_ai_scores_data()

        print("\nMigrating financial scores...")
        migrate_financial_scores_data()

        print("\nMigrating adjusted PE data...")
        migrate_adjusted_pe_data()

        print("\nMigrating watchlist...")
        migrate_watchlist_data()

        print("\nMigrating additional UI cache data...")
        migrate_ui_cache_additional_data()

        # Validate
        validate_migration()

        print(f"\nMigration completed successfully!")
        print(f"New consolidated database: {NEW_DB_PATH}")
        print(f"Backups available in: {backup_dir}")

    except Exception as e:
        print(f"Migration failed: {e}")
        import traceback
        traceback.print_exc()
        return False

    return True

if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)