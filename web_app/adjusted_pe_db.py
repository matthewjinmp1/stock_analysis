#!/usr/bin/env python3
"""
Adjusted PE storage.
Stores TTM components and computed adjusted PE per ticker.
"""

import os
import sqlite3
from typing import Optional, Dict, Any

# Database path
ADJUSTED_PE_DB = os.path.join(os.path.dirname(__file__), "data", "adjusted_pe.db")


def init_adjusted_pe_db() -> None:
    """Initialize adjusted_pe table."""
    os.makedirs(os.path.dirname(ADJUSTED_PE_DB), exist_ok=True)
    conn = sqlite3.connect(ADJUSTED_PE_DB)
    cur = conn.cursor()
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS adjusted_pe (
            ticker TEXT PRIMARY KEY,
            adjusted_pe_ratio REAL,
            ttm_operating_income REAL,
            ttm_da REAL,
            ttm_capex REAL,
            adjustment REAL,
            adjusted_operating_income REAL,
            median_tax_rate REAL,
            adjusted_oi_after_tax REAL,
            quickfs_ev REAL,
            quickfs_market_cap REAL,
            updated_ev REAL,
            share_count REAL,
            current_price REAL,
            ev_difference REAL,
            updated_market_cap REAL,
            last_updated TEXT
        )
        """
    )
    # Add missing columns if table already existed
    cur.execute("PRAGMA table_info(adjusted_pe)")
    existing_cols = {row[1] for row in cur.fetchall()}
    for col in ["ev_difference", "updated_market_cap"]:
        if col not in existing_cols:
            cur.execute(f"ALTER TABLE adjusted_pe ADD COLUMN {col} REAL")
    cur.execute(
        "CREATE INDEX IF NOT EXISTS idx_adjusted_pe_ticker ON adjusted_pe(ticker)"
    )
    conn.commit()
    conn.close()


def upsert_adjusted_pe(
    ticker: str, data: Dict[str, Any], ratio: Optional[float], timestamp: str
) -> None:
    """Insert or update adjusted PE breakdown."""
    init_adjusted_pe_db()
    conn = sqlite3.connect(ADJUSTED_PE_DB)
    cur = conn.cursor()
    cur.execute(
        """
        INSERT INTO adjusted_pe (
            ticker, adjusted_pe_ratio, ttm_operating_income, ttm_da, ttm_capex,
            adjustment, adjusted_operating_income, median_tax_rate,
            adjusted_oi_after_tax, quickfs_ev, quickfs_market_cap, updated_ev,
            share_count, current_price, ev_difference, updated_market_cap, last_updated
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(ticker) DO UPDATE SET
            adjusted_pe_ratio=excluded.adjusted_pe_ratio,
            ttm_operating_income=excluded.ttm_operating_income,
            ttm_da=excluded.ttm_da,
            ttm_capex=excluded.ttm_capex,
            adjustment=excluded.adjustment,
            adjusted_operating_income=excluded.adjusted_operating_income,
            median_tax_rate=excluded.median_tax_rate,
            adjusted_oi_after_tax=excluded.adjusted_oi_after_tax,
            quickfs_ev=excluded.quickfs_ev,
            quickfs_market_cap=excluded.quickfs_market_cap,
            updated_ev=excluded.updated_ev,
            share_count=excluded.share_count,
            current_price=excluded.current_price,
            ev_difference=excluded.ev_difference,
            updated_market_cap=excluded.updated_market_cap,
            last_updated=excluded.last_updated
        """,
        (
            ticker,
            ratio,
            data.get("ttm_operating_income"),
            data.get("ttm_da"),
            data.get("ttm_capex"),
            data.get("adjustment"),
            data.get("adjusted_operating_income"),
            data.get("median_tax_rate"),
            data.get("adjusted_oi_after_tax"),
            data.get("quickfs_ev"),
            data.get("quickfs_market_cap"),
            data.get("updated_ev"),
            data.get("share_count"),
            data.get("current_price"),
            data.get("ev_difference"),
            data.get("updated_market_cap"),
            timestamp,
        ),
    )
    conn.commit()
    conn.close()


def get_adjusted_pe(ticker: str) -> Optional[Dict[str, Any]]:
    """Fetch stored adjusted PE breakdown for ticker."""
    init_adjusted_pe_db()
    conn = sqlite3.connect(ADJUSTED_PE_DB)
    cur = conn.cursor()
    cur.execute(
        """
        SELECT
            adjusted_pe_ratio, ttm_operating_income, ttm_da, ttm_capex,
            adjustment, adjusted_operating_income, median_tax_rate,
            adjusted_oi_after_tax, quickfs_ev, quickfs_market_cap, updated_ev,
            share_count, current_price, ev_difference, updated_market_cap, last_updated
        FROM adjusted_pe
        WHERE ticker = ?
        """,
        (ticker,),
    )
    row = cur.fetchone()
    conn.close()
    if not row:
        return None
    keys = [
        "adjusted_pe_ratio",
        "ttm_operating_income",
        "ttm_da",
        "ttm_capex",
        "adjustment",
        "adjusted_operating_income",
        "median_tax_rate",
        "adjusted_oi_after_tax",
        "quickfs_ev",
        "quickfs_market_cap",
        "updated_ev",
        "share_count",
        "current_price",
        "ev_difference",
        "updated_market_cap",
        "last_updated",
    ]
    return dict(zip(keys, row))
