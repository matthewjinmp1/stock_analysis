-- Normalized database schema for stock analysis application
-- Consolidates all existing databases into a single, properly normalized structure

-- Enable foreign key constraints
PRAGMA foreign_keys = ON;

-- Companies table - central entity
CREATE TABLE companies (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    ticker TEXT UNIQUE NOT NULL,
    company_name TEXT NOT NULL,
    exchange TEXT,
    sector TEXT,
    industry TEXT,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT DEFAULT CURRENT_TIMESTAMP
);

-- Ticker aliases table (for companies with multiple tickers)
CREATE TABLE ticker_aliases (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    company_id INTEGER NOT NULL,
    ticker TEXT NOT NULL,
    is_primary BOOLEAN DEFAULT FALSE,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (company_id) REFERENCES companies(id) ON DELETE CASCADE,
    UNIQUE(ticker)
);

-- AI Scores table - qualitative scores from AI analysis
CREATE TABLE ai_scores (
    company_id INTEGER PRIMARY KEY,
    ai_knowledge_score REAL,
    ambition_score REAL,
    bargaining_power_of_customers REAL,
    bargaining_power_of_suppliers REAL,
    barriers_score REAL,
    brand_strength REAL,
    competition_intensity REAL,
    culture_employee_satisfaction_score REAL,
    disruption_risk REAL,
    ethical_healthy_environmental_score REAL,
    growth_opportunity REAL,
    innovativeness_score REAL,
    long_term_orientation_score REAL,
    management_quality_score REAL,
    moat_score REAL,
    model TEXT,
    network_effect REAL,
    pricing_power REAL,
    product_differentiation REAL,
    product_quality_score REAL,
    riskiness_score REAL,
    size_well_known_score REAL,
    switching_cost REAL,
    trailblazer_score REAL,
    total_score_percentage REAL,
    total_score_percentile_rank INTEGER,
    last_updated TEXT DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (company_id) REFERENCES companies(id) ON DELETE CASCADE
);

-- Financial Scores table - quantitative metrics
CREATE TABLE financial_scores (
    company_id INTEGER PRIMARY KEY,
    exchange TEXT,
    period TEXT,
    market_cap REAL,
    total_percentile REAL,
    total_rank INTEGER,
    ebit_ppe REAL,
    ebit_ppe_rank INTEGER,
    ebit_ppe_percentile REAL,
    gross_margin REAL,
    gross_margin_rank INTEGER,
    gross_margin_percentile REAL,
    operating_margin REAL,
    operating_margin_rank INTEGER,
    operating_margin_percentile REAL,
    revenue_growth REAL,
    revenue_growth_rank INTEGER,
    revenue_growth_percentile REAL,
    growth_consistency REAL,
    growth_consistency_rank INTEGER,
    growth_consistency_percentile REAL,
    operating_margin_growth REAL,
    operating_margin_growth_rank INTEGER,
    operating_margin_growth_percentile REAL,
    operating_margin_consistency REAL,
    operating_margin_consistency_rank INTEGER,
    operating_margin_consistency_percentile REAL,
    net_debt_to_ttm_operating_income REAL,
    net_debt_to_ttm_operating_income_rank INTEGER,
    net_debt_to_ttm_operating_income_percentile REAL,
    adjusted_pe_ratio REAL,
    adjusted_pe_ratio_rank INTEGER,
    adjusted_pe_ratio_percentile REAL,
    last_updated TEXT DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (company_id) REFERENCES companies(id) ON DELETE CASCADE
);

-- Adjusted PE calculations
CREATE TABLE adjusted_pe_calculations (
    company_id INTEGER PRIMARY KEY,
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
    last_updated TEXT DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (company_id) REFERENCES companies(id) ON DELETE CASCADE
);

-- Growth estimates
CREATE TABLE growth_estimates (
    company_id INTEGER PRIMARY KEY,
    current_year_growth REAL,
    next_year_growth REAL,
    last_updated TEXT DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (company_id) REFERENCES companies(id) ON DELETE CASCADE
);

-- Short interest data
CREATE TABLE short_interest (
    company_id INTEGER PRIMARY KEY,
    short_float REAL,
    scraped_at TEXT,
    last_updated TEXT DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (company_id) REFERENCES companies(id) ON DELETE CASCADE
);

-- Watchlist (junction table for users and companies)
-- Note: This assumes a future user system. For now, we'll use a simple watchlist.
CREATE TABLE watchlist (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    company_id INTEGER NOT NULL,
    added_at TEXT DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (company_id) REFERENCES companies(id) ON DELETE CASCADE,
    UNIQUE(company_id)
);

-- Peer relationships (many-to-many)
CREATE TABLE peer_relationships (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    company_id INTEGER NOT NULL,
    peer_company_id INTEGER NOT NULL,
    rank INTEGER,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (company_id) REFERENCES companies(id) ON DELETE CASCADE,
    FOREIGN KEY (peer_company_id) REFERENCES companies(id) ON DELETE CASCADE,
    UNIQUE(company_id, peer_company_id)
);

-- Indexes for performance
CREATE INDEX idx_companies_ticker ON companies(ticker);
CREATE INDEX idx_ticker_aliases_ticker ON ticker_aliases(ticker);
CREATE INDEX idx_watchlist_company_id ON watchlist(company_id);
CREATE INDEX idx_peer_relationships_company_id ON peer_relationships(company_id);
CREATE INDEX idx_peer_relationships_peer_company_id ON peer_relationships(peer_company_id);

-- Views for backward compatibility
CREATE VIEW ui_cache AS
SELECT
    c.ticker,
    c.company_name,
    ais.last_updated,
    ais.ai_knowledge_score,
    ais.ambition_score,
    ais.bargaining_power_of_customers,
    ais.bargaining_power_of_suppliers,
    ais.barriers_score,
    ais.brand_strength,
    ais.competition_intensity,
    ais.culture_employee_satisfaction_score,
    ais.disruption_risk,
    ais.ethical_healthy_environmental_score,
    ais.growth_opportunity,
    ais.innovativeness_score,
    ais.long_term_orientation_score,
    ais.management_quality_score,
    ais.moat_score,
    ais.model,
    ais.network_effect,
    ais.pricing_power,
    ais.product_differentiation,
    ais.product_quality_score,
    ais.riskiness_score,
    ais.size_well_known_score,
    ais.switching_cost,
    ais.trailblazer_score,
    ais.total_score_percentage,
    ais.total_score_percentile_rank,
    si.short_float,
    si.scraped_at as short_interest_scraped_at,
    ap.adjusted_pe_ratio,
    ge.current_year_growth,
    ge.next_year_growth
FROM companies c
LEFT JOIN ai_scores ais ON c.id = ais.company_id
LEFT JOIN short_interest si ON c.id = si.company_id
LEFT JOIN adjusted_pe_calculations ap ON c.id = ap.company_id
LEFT JOIN growth_estimates ge ON c.id = ge.company_id;

CREATE VIEW scores AS
SELECT
    c.ticker,
    ais.ai_knowledge_score,
    ais.ambition_score,
    ais.bargaining_power_of_customers,
    ais.bargaining_power_of_suppliers,
    ais.barriers_score,
    ais.brand_strength,
    ais.competition_intensity,
    ais.culture_employee_satisfaction_score,
    ais.disruption_risk,
    ais.ethical_healthy_environmental_score,
    ais.growth_opportunity,
    ais.innovativeness_score,
    ais.long_term_orientation_score,
    ais.management_quality_score,
    ais.moat_score,
    ais.model,
    ais.network_effect,
    ais.pricing_power,
    ais.product_differentiation,
    ais.product_quality_score,
    ais.riskiness_score,
    ais.size_well_known_score,
    ais.switching_cost,
    ais.trailblazer_score,
    ais.total_score_percentage,
    ais.total_score_percentile_rank
FROM companies c
LEFT JOIN ai_scores ais ON c.id = ais.company_id;