import React, { useState, useEffect, useRef } from 'react';
import { Link, useSearchParams } from 'react-router-dom';
import { AlertCircle, Loader2 } from 'lucide-react';
import * as api from '../api';

interface SearchSuggestion {
  ticker: string;
  company_name: string;
  match_type: string;
}

interface StockData {
  ticker: string;
  company_name: string;
  short_float: string | null;
  total_score_percentile_rank: number | null;
  financial_total_percentile: number | null;
  adjusted_pe_ratio: number | null;
  current_year_growth: number | null;
  next_year_growth: number | null;
}

const HomePage: React.FC = () => {
  const [searchParams, setSearchParams] = useSearchParams();
  const [query, setQuery] = useState(searchParams.get('q') || '');
  const [suggestions, setSuggestions] = useState<SearchSuggestion[]>([]);
  const [showDropdown, setShowDropdown] = useState(false);
  const [selectedIndex, setSelectedIndex] = useState(-1);
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<{ ticker: string; data: StockData; in_watchlist: boolean } | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [stats, setStats] = useState<string>('');
  
  const dropdownRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    // Initial search if q param is present
    const q = searchParams.get('q');
    if (q) {
      performSearch(q);
    }

    // Load stats
    api.getList().then(data => {
      if (data.success) {
        setStats(`Database contains ${data.count} tickers with cached short interest data`);
      }
    }).catch(err => console.error('Error loading stats:', err));

    // Handle clicks outside dropdown
    const handleClickOutside = (event: MouseEvent) => {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target as Node) && 
          inputRef.current && !inputRef.current.contains(event.target as Node)) {
        setShowDropdown(false);
      }
    };

    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  const handleInputChange = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const val = e.target.value;
    setQuery(val);
    setSelectedIndex(-1);

    if (val.trim().length < 1) {
      setSuggestions([]);
      setShowDropdown(false);
      return;
    }

    try {
      const data = await api.getSearchSuggestions(val);
      if (data.success && data.suggestions.length > 0) {
        setSuggestions(data.suggestions);
        setShowDropdown(true);
      } else {
        setShowDropdown(false);
      }
    } catch (err) {
      console.error('Error fetching suggestions:', err);
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (!showDropdown) {
      if (e.key === 'Enter') handleSearch();
      return;
    }

    switch (e.key) {
      case 'ArrowDown':
        e.preventDefault();
        setSelectedIndex(prev => Math.min(prev + 1, suggestions.length - 1));
        break;
      case 'ArrowUp':
        e.preventDefault();
        setSelectedIndex(prev => Math.max(prev - 1, -1));
        break;
      case 'Enter':
        e.preventDefault();
        if (selectedIndex >= 0) {
          selectSuggestion(suggestions[selectedIndex]);
        } else {
          handleSearch();
        }
        break;
      case 'Escape':
        setShowDropdown(false);
        break;
    }
  };

  const selectSuggestion = (suggestion: SearchSuggestion) => {
    setQuery(suggestion.ticker);
    setShowDropdown(false);
    performSearch(suggestion.ticker);
  };

  const handleSearch = () => {
    if (!query.trim()) {
      setError('Please enter a ticker symbol');
      return;
    }
    performSearch(query);
  };

  const performSearch = async (searchQuery: string) => {
    setShowDropdown(false);
    setLoading(true);
    setError(null);
    setResult(null);
    setSearchParams({ q: searchQuery });

    try {
      const data = await api.searchTicker(searchQuery);
      if (data.success) {
        setResult({
          ticker: data.ticker,
          data: data.data,
          in_watchlist: data.in_watchlist
        });
      } else {
        setError(data.message || `No data found for "${searchQuery}"`);
      }
    } catch (err: any) {
      setError(err.response?.data?.message || 'Error fetching data. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  const toggleWatchlist = async () => {
    if (!result) return;
    
    try {
      if (result.in_watchlist) {
        await api.removeFromWatchlist(result.ticker);
      } else {
        await api.addToWatchlist(result.ticker);
      }
      // Refresh result to update watchlist status
      performSearch(result.ticker);
    } catch (err) {
      alert('Error updating watchlist');
    }
  };

  return (
    <div className="flex flex-col">
      {/* Header */}
      <div className="p-10 text-center border-b border-border-color bg-header-bg rounded-t-[15px]">
        <h1 className="text-[2.5em] font-bold mb-2.5 text-text-secondary [text-shadow:0_0_8px_var(--glow-primary)]">
          📊 Stock Analysis
        </h1>
        <p className="opacity-85 text-[1.1em] text-text-primary [text-shadow:0_0_3px_var(--glow-primary)]">
          Analyze stocks with AI scores, financial metrics, and short interest data
        </p>
        <div className="mt-4 flex justify-center flex-wrap gap-2">
          <Link to="/watchlist" className="px-4 py-2 text-[0.9em] font-medium text-text-secondary border border-border-color rounded-lg transition-all hover:bg-button-bg hover:text-accent-primary hover:border-accent-primary hover:shadow-[0_0_12px_var(--glow-primary)]">
            View Watchlist
          </Link>
          <Link to="/ai-scores" className="px-4 py-2 text-[0.9em] font-medium text-text-secondary border border-border-color rounded-lg transition-all hover:bg-button-bg hover:text-accent-primary hover:border-accent-primary hover:shadow-[0_0_12px_var(--glow-primary)]">
            AI Analysis Scores
          </Link>
          <Link to="/find-peers" className="px-4 py-2 text-[0.9em] font-medium text-text-secondary border border-border-color rounded-lg transition-all hover:bg-button-bg hover:text-accent-primary hover:border-accent-primary hover:shadow-[0_0_12px_var(--glow-primary)]">
            🤖 Find Peers
          </Link>
        </div>
      </div>

      {/* Search Section */}
      <div className="p-10 bg-bg-secondary flex flex-col items-center">
        <div className="flex gap-2.5 mb-5 w-full justify-center items-center">
          <div className="relative w-full max-width-[500px]">
            <input
              ref={inputRef}
              type="text"
              value={query}
              onChange={handleInputChange}
              onKeyDown={handleKeyDown}
              placeholder="Search tickers or company names (e.g., apple, AAPL)"
              className="w-full p-[15px_20px] text-[1.1em] bg-input-bg text-text-secondary border border-border-color rounded-[10px] outline-none transition-all focus:border-accent-secondary focus:shadow-[0_0_15px_var(--glow-secondary)] font-sans"
              autoComplete="off"
            />
            
            {showDropdown && (
              <div 
                ref={dropdownRef}
                className="absolute top-full left-0 right-0 bg-bg-primary border border-border-color rounded-b-[10px] shadow-[0_8px_25px_var(--shadow-color)] max-h-[300px] overflow-y-auto z-[2000]"
              >
                {suggestions.map((suggestion, index) => (
                  <div
                    key={suggestion.ticker}
                    onClick={() => selectSuggestion(suggestion)}
                    className={`p-[12px_20px] border-b border-border-color last:border-b-0 cursor-pointer transition-all flex justify-between items-center text-text-secondary hover:bg-table-hover-bg hover:border-l-[3px] hover:border-accent-secondary ${
                      index === selectedIndex ? 'bg-table-hover-bg border-l-[3px] border-accent-secondary' : ''
                    }`}
                  >
                    <div className="font-semibold text-accent-secondary">{suggestion.ticker}</div>
                    <div className="text-[0.9em] flex-1 ml-3">{suggestion.company_name}</div>
                  </div>
                ))}
              </div>
            )}
          </div>
          <button 
            onClick={handleSearch}
            className="p-[15px_30px] text-[1.1em] bg-button-bg text-text-secondary border border-border-color rounded-[10px] cursor-pointer font-semibold transition-all hover:-translate-y-0.5 hover:bg-accent-primary hover:text-bg-primary hover:shadow-[0_5px_15px_var(--glow-primary)]"
          >
            Search
          </button>
        </div>

        {/* Loading State */}
        {loading && (
          <div className="text-center p-10 text-text-muted">
            <Loader2 className="w-10 h-10 animate-spin mx-auto mb-5 text-accent-primary" />
            <p>Loading {query.toUpperCase()}...</p>
          </div>
        )}

        {/* Error State */}
        {error && (
          <div className="w-full bg-button-bg text-accent-danger p-5 rounded-[10px] border-l-4 border-accent-danger mt-5">
            <div className="flex items-center gap-2">
              <AlertCircle className="w-5 h-5" />
              <strong>Error:</strong> {error}
            </div>
          </div>
        )}

        {/* Result Card */}
        {result && (
          <div className="w-full max-w-4xl bg-card-bg rounded-[15px] p-[30px] mb-5 border border-border-color border-l-4 border-accent-secondary shadow-[0_0_15px_var(--shadow-color),inset_0_0_15px_var(--shadow-inset)] animate-[slideIn_0.3s_ease-out]">
            <div className="flex justify-between items-center mb-5">
              <div className="text-[1.8em] font-bold text-text-secondary">
                {result.data.company_name || result.ticker}
              </div>
              <div className="flex items-center gap-2.5">
                <div className="text-[1.2em] text-accent-secondary font-semibold bg-button-bg p-[5px_15px] rounded-lg border border-border-color">
                  {result.ticker}
                </div>
                <Link 
                  to={`/peers/${result.ticker}`} 
                  className="p-[8px_16px] text-[0.9em] rounded-lg cursor-pointer font-semibold transition-all border border-border-color bg-button-bg text-text-secondary hover:bg-accent-secondary hover:text-bg-primary"
                >
                  Peers
                </Link>
                <button 
                  onClick={toggleWatchlist}
                  className={`p-[8px_16px] text-[0.9em] rounded-lg cursor-pointer font-semibold transition-all border border-border-color bg-button-bg text-text-secondary ${
                    result.in_watchlist 
                      ? 'hover:bg-accent-danger hover:text-bg-primary hover:border-accent-danger' 
                      : 'hover:bg-accent-success hover:text-bg-primary hover:border-accent-success'
                  }`}
                >
                  {result.in_watchlist ? 'Remove from Watchlist' : 'Add to Watchlist'}
                </button>
              </div>
            </div>

            <div className="grid grid-cols-[repeat(auto-fit,minmax(200px,1fr))] gap-[15px] mt-5">
              {result.data.total_score_percentile_rank !== null && (
                <div className="bg-bg-primary p-[15px] rounded-[10px] border border-border-color shadow-[0_0_8px_var(--shadow-color)]">
                  <div className="text-[0.9em] text-text-muted mb-1.25">Total Score</div>
                  <div className="text-[1.2em] font-semibold text-text-secondary">
                    <Link to={`/metrics/${result.ticker}`} className="text-accent-secondary hover:underline">
                      {result.data.total_score_percentile_rank}%
                    </Link>
                  </div>
                </div>
              )}
              
              {result.data.financial_total_percentile !== null && (
                <div className="bg-bg-primary p-[15px] rounded-[10px] border border-border-color shadow-[0_0_8px_var(--shadow-color)]">
                  <div className="text-[0.9em] text-text-muted mb-1.25">Financial Score</div>
                  <div className="text-[1.2em] font-semibold text-text-secondary">
                    <Link to={`/financial/${result.ticker}`} className="text-accent-secondary hover:underline">
                      {Math.round(result.data.financial_total_percentile!)}%
                    </Link>
                  </div>
                </div>
              )}

              {result.data.adjusted_pe_ratio !== null && (
                <div className="bg-bg-primary p-[15px] rounded-[10px] border border-border-color shadow-[0_0_8px_var(--shadow-color)]">
                  <div className="text-[0.9em] text-text-muted mb-1.25">Adjusted PE Ratio</div>
                  <div className="text-[1.2em] font-semibold text-text-secondary">
                    <Link to={`/adjusted-pe/${result.ticker}`} className="text-accent-secondary hover:underline">
                      {result.data.adjusted_pe_ratio.toFixed(2)}
                    </Link>
                  </div>
                </div>
              )}

              {result.data.current_year_growth !== null && (
                <div className="bg-bg-primary p-[15px] rounded-[10px] border border-border-color shadow-[0_0_8px_var(--shadow-color)]">
                  <div className="text-[0.9em] text-text-muted mb-1.25">Current Year Growth</div>
                  <div className="text-[1.2em] font-semibold text-text-secondary">
                    {result.data.current_year_growth.toFixed(1)}%
                  </div>
                </div>
              )}

              {result.data.next_year_growth !== null && (
                <div className="bg-bg-primary p-[15px] rounded-[10px] border border-border-color shadow-[0_0_8_var(--shadow-color)]">
                  <div className="text-[0.9em] text-text-muted mb-1.25">Next Year Growth</div>
                  <div className="text-[1.2em] font-semibold text-text-secondary">
                    {result.data.next_year_growth.toFixed(1)}%
                  </div>
                </div>
              )}

              <div className="bg-bg-primary p-[15px] rounded-[10px] border border-border-color shadow-[0_0_8px_var(--shadow-color)]">
                <div className="text-[0.9em] text-text-muted mb-1.25">Short Float (Short Interest)</div>
                <div className="text-[1.2em] font-semibold text-text-secondary">
                  {result.data.short_float || 'No data available'}
                </div>
              </div>
            </div>
          </div>
        )}
      </div>

      {/* Stats Footer */}
      <div className="p-5 text-center bg-bg-secondary text-text-muted text-[0.9em] border-t border-border-color rounded-b-[15px]">
        {stats}
      </div>

      <style>{`
        @keyframes slideIn {
          from { opacity: 0; transform: translateY(20px); }
          to { opacity: 1; transform: translateY(0); }
        }
      `}</style>
    </div>
  );
};

export default HomePage;
