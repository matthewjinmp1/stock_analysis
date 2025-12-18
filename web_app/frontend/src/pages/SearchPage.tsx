import React, { useState, useEffect, useRef } from 'react';
import { Link, useSearchParams } from 'react-router-dom';
import { AlertCircle, Loader2 } from 'lucide-react';
import { useTheme } from '../components/ThemeContext';
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

const SearchPage: React.FC = () => {
  const { theme } = useTheme();
  const [searchParams, setSearchParams] = useSearchParams();
  const [query, setQuery] = useState(searchParams.get('q') || '');
  const [suggestions, setSuggestions] = useState<SearchSuggestion[]>([]);
  const [showDropdown, setShowDropdown] = useState(false);
  const [selectedIndex, setSelectedIndex] = useState(-1);
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<{ ticker: string; data: StockData; in_watchlist: boolean } | null>(null);
  const [error, setError] = useState<string | null>(null);
  
  const dropdownRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  // Sync state with URL params
  useEffect(() => {
    const q = searchParams.get('q');
    if (q) {
      setQuery(q);
      performSearch(q);
    }
  }, [searchParams]);

  useEffect(() => {
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
        setSuggestions([]);
        setShowDropdown(false);
      }
    } catch (err) {
      console.error('Error fetching suggestions:', err);
      setShowDropdown(false);
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
    const trimmedQuery = query.trim();
    if (!trimmedQuery) {
      setError('Please enter a ticker symbol');
      return;
    }
    performSearch(trimmedQuery);
  };

  const performSearch = async (searchQuery: string) => {
    setShowDropdown(false);
    setLoading(true);
    setError(null);
    setResult(null);
    
    // Only update search params if they are different to avoid infinite loops
    if (searchParams.get('q') !== searchQuery) {
      setSearchParams({ q: searchQuery });
    }

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
      // Re-fetch to get updated state
      const data = await api.searchTicker(result.ticker);
      if (data.success) {
        setResult({
          ticker: data.ticker,
          data: data.data,
          in_watchlist: data.in_watchlist
        });
      }
    } catch (err) {
      alert('Error updating watchlist');
    }
  };

  return (
    <div className="flex flex-col w-full min-h-screen pb-20">
      {/* Header */}
      <div className="p-8 text-center border-b border-border-color bg-header-bg">
        <h1 className="text-4xl md:text-5xl font-black mb-4 text-text-secondary [text-shadow:0_0_8px_var(--glow-primary)]">
          📊 Stock Analysis
        </h1>
        <p className="opacity-80 text-lg text-text-primary mb-6 font-medium">
          Analyze stocks with AI scores, financial metrics, and short interest data
        </p>
        <div className="flex flex-col sm:flex-row justify-center items-center gap-10 md:gap-32 mt-12 w-full max-w-4xl mx-auto">
          <Link to="/watchlist" className="flex-1 min-w-[280px] px-12 py-5 bg-button-bg text-text-secondary border border-border-color transition-all hover:bg-accent-primary hover:text-bg-primary hover:border-accent-primary shadow-xl text-xl font-black text-center whitespace-nowrap">
            View Watchlist
          </Link>
          <Link to="/ai-scores" className="flex-1 min-w-[280px] px-12 py-5 bg-button-bg text-text-secondary border border-border-color transition-all hover:bg-accent-primary hover:text-bg-primary hover:border-accent-primary shadow-xl text-xl font-black text-center whitespace-nowrap">
            AI Analysis Scores
          </Link>
        </div>
      </div>

      {/* Search Section */}
      <div className="p-12 bg-bg-secondary flex flex-col items-center border-b border-border-color relative z-[1000]">
        <div className="flex gap-4 w-full max-w-[700px]">
          <div className="relative flex-1 z-[1100]">
            <input
              ref={inputRef}
              type="text"
              value={query}
              onChange={handleInputChange}
              onKeyDown={handleKeyDown}
              placeholder="Search tickers or company names..."
              className="w-full p-5 text-xl bg-input-bg text-text-secondary border border-border-color outline-none transition-all focus:border-accent-secondary focus:ring-4 focus:ring-accent-secondary/10 shadow-sm"
              autoComplete="off"
            />
            
            {showDropdown && suggestions.length > 0 && (
              <div 
                ref={dropdownRef}
                className="absolute top-full left-0 right-0 mt-2 border-2 border-border-color shadow-[0_30px_60px_rgba(0,0,0,0.8)] max-h-[400px] overflow-y-auto z-[2000] !opacity-100"
                style={{ backgroundColor: theme === 'light' ? '#ffffff' : '#0a0a0a' }}
              >
                {suggestions.map((suggestion, index) => (
                  <div
                    key={suggestion.ticker}
                    onClick={() => selectSuggestion(suggestion)}
                    className={`p-5 border-b border-border-color last:border-b-0 cursor-pointer transition-all flex justify-between items-center text-text-secondary hover:bg-table-hover-bg ${
                      index === selectedIndex ? 'bg-table-hover-bg border-l-8 border-accent-secondary' : ''
                    }`}
                    style={{ backgroundColor: theme === 'light' ? '#ffffff' : '#0a0a0a' }}
                  >
                    <div className="font-bold text-xl text-accent-secondary flex-shrink-0 min-w-[80px]">
                      {suggestion.ticker}
                    </div>
                    <div className="text-base opacity-80 flex-1 ml-10 text-right truncate font-medium">
                      {suggestion.company_name}
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
          <button 
            onClick={handleSearch}
            disabled={loading}
            className="px-10 bg-accent-primary text-bg-primary font-black text-lg transition-all hover:opacity-90 active:scale-95 disabled:opacity-50 whitespace-nowrap shadow-lg"
          >
            {loading ? '...' : 'Search'}
          </button>
        </div>

        {/* Loading State */}
        {loading && (
          <div className="text-center p-12 text-text-muted">
            <Loader2 className="w-12 h-12 animate-spin mx-auto mb-6 text-accent-primary" />
            <p className="font-bold text-lg">Loading {query.toUpperCase()}...</p>
          </div>
        )}

        {/* Error State */}
        {error && (
          <div className="w-full max-w-[700px] bg-accent-danger/10 text-accent-danger p-6 border border-accent-danger/20 mt-8 flex items-center gap-4 animate-[slideIn_0.3s_ease-out]">
            <AlertCircle className="w-6 h-6 flex-shrink-0" />
            <p className="font-bold"><strong>Error:</strong> {error}</p>
          </div>
        )}

        {/* Result Card */}
        {result && (
          <div className="w-full max-w-[1000px] bg-card-bg p-10 mt-10 border border-border-color shadow-2xl animate-[slideIn_0.3s_ease-out] relative z-[1]">
            <div className="flex justify-between items-center mb-10 flex-wrap gap-8 text-left">
              <div className="flex flex-wrap items-baseline gap-4 flex-1 min-w-[200px]">
                <h2 className="text-4xl font-black text-text-secondary">
                  {result.data.company_name || result.ticker}
                </h2>
                <div className="text-2xl text-accent-secondary font-black bg-button-bg px-4 py-1 border border-border-color shadow-sm">
                  {result.ticker}
                </div>
              </div>
              
              <div className="flex items-center gap-3">
                <Link 
                  to={`/peers/${result.ticker}`} 
                  className="px-6 py-3 font-black transition-all border border-border-color bg-button-bg text-text-secondary hover:bg-accent-secondary hover:text-bg-primary text-base shadow-sm"
                >
                  Peers
                </Link>
                <button 
                  onClick={toggleWatchlist}
                  className={`px-6 py-3 font-black transition-all border border-border-color text-base shadow-sm ${
                    result.in_watchlist 
                      ? 'bg-accent-danger/10 text-accent-danger hover:bg-accent-danger hover:text-bg-primary border-accent-danger/30' 
                      : 'bg-accent-success/10 text-accent-success hover:bg-accent-success hover:text-bg-primary border-accent-success/30'
                  }`}
                >
                  {result.in_watchlist ? 'Remove' : 'Add'}
                </button>
              </div>
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6">
              {result.data.total_score_percentile_rank !== null && (
                <div className="bg-bg-primary/50 p-6 border border-border-color hover:border-accent-secondary transition-all group text-left shadow-sm">
                  <div className="text-xs font-black text-text-muted uppercase tracking-[0.2em] mb-3 opacity-70">Total Score</div>
                  <div className="text-4xl font-black text-text-secondary">
                    <Link to={`/metrics/${result.ticker}`} className="text-accent-secondary group-hover:text-accent-primary transition-colors">
                      {result.data.total_score_percentile_rank}%
                    </Link>
                  </div>
                </div>
              )}
              
              {result.data.financial_total_percentile !== null && (
                <div className="bg-bg-primary/50 p-6 border border-border-color hover:border-accent-secondary transition-all group text-left shadow-sm">
                  <div className="text-xs font-black text-text-muted uppercase tracking-[0.2em] mb-3 opacity-70">Financial Score</div>
                  <div className="text-4xl font-black text-text-secondary">
                    <Link to={`/financial/${result.ticker}`} className="text-accent-secondary group-hover:text-accent-primary transition-colors">
                      {Math.round(result.data.financial_total_percentile!)}%
                    </Link>
                  </div>
                </div>
              )}

              {result.data.adjusted_pe_ratio !== null && (
                <div className="bg-bg-primary/50 p-6 border border-border-color hover:border-accent-secondary transition-all group text-left shadow-sm">
                  <div className="text-xs font-black text-text-muted uppercase tracking-[0.2em] mb-3 opacity-70">Adjusted PE</div>
                  <div className="text-4xl font-black text-text-secondary">
                    <Link to={`/adjusted-pe/${result.ticker}`} className="text-accent-secondary group-hover:text-accent-primary transition-colors">
                      {result.data.adjusted_pe_ratio.toFixed(2)}
                    </Link>
                  </div>
                </div>
              )}

              {result.data.current_year_growth !== null && (
                <div className="bg-bg-primary/50 p-6 border border-border-color transition-all text-left shadow-sm">
                  <div className="text-xs font-black text-text-muted uppercase tracking-[0.2em] mb-3 opacity-70">Growth (Current)</div>
                  <div className="text-4xl font-black text-text-secondary">
                    {result.data.current_year_growth.toFixed(1)}%
                  </div>
                </div>
              )}

              {result.data.next_year_growth !== null && (
                <div className="bg-bg-primary/50 p-6 border border-border-color transition-all text-left shadow-sm">
                  <div className="text-xs font-black text-text-muted uppercase tracking-[0.2em] mb-3 opacity-70">Growth (Next)</div>
                  <div className="text-4xl font-black text-text-secondary">
                    {result.data.next_year_growth.toFixed(1)}%
                  </div>
                </div>
              )}

              <div className="bg-bg-primary/50 p-6 border border-border-color transition-all text-left shadow-sm">
                <div className="text-xs font-black text-text-muted uppercase tracking-[0.2em] mb-3 opacity-70">Short Float</div>
                <div className="text-3xl font-black text-text-secondary truncate">
                  {result.data.short_float || 'N/A'}
                </div>
              </div>
            </div>
          </div>
        )}
      </div>

      <style>{`
        @keyframes slideIn {
          from { opacity: 0; transform: translateY(10px); }
          to { opacity: 1; transform: translateY(0); }
        }
      `}</style>
    </div>
  );
};

export default SearchPage;
