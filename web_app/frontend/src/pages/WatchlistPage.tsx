import React, { useState, useEffect } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { ArrowLeft, Trash2, Loader2, AlertCircle } from 'lucide-react';
import * as api from '../api';

interface WatchlistItem {
  ticker: string;
  company_name: string | null;
  short_float: string | null;
  total_score_percentile_rank: number | null;
  financial_total_percentile: number | null;
  adjusted_pe_ratio: number | null;
}

const WatchlistPage: React.FC = () => {
  const navigate = useNavigate();
  const [watchlist, setWatchlist] = useState<WatchlistItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [newTicker, setNewTicker] = useState('');
  const [addMessage, setAddMessage] = useState<{ type: 'success' | 'error', text: string } | null>(null);
  const [sortColumn, setSortColumn] = useState<keyof WatchlistItem | null>(null);
  const [sortDirection, setSortDirection] = useState<'asc' | 'desc'>('asc');

  const fetchWatchlist = async () => {
    try {
      const data = await api.getWatchlist();
      if (data.success) {
        setWatchlist(data.watchlist || []);
      } else {
        setError(data.message || 'Error loading watchlist');
      }
    } catch (err) {
      setError('Error loading watchlist. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchWatchlist();
  }, []);

  const handleAddTicker = async () => {
    const ticker = newTicker.trim().toUpperCase();
    if (!ticker) {
      setAddMessage({ type: 'error', text: 'Please enter a ticker symbol' });
      return;
    }

    setAddMessage(null);
    try {
      const data = await api.addToWatchlist(ticker);
      if (data.success) {
        setAddMessage({ type: 'success', text: `${ticker} added to watchlist` });
        setNewTicker('');
        fetchWatchlist();
      } else {
        setAddMessage({ type: 'error', text: data.message || 'Error adding ticker' });
      }
    } catch (err: any) {
      setAddMessage({ type: 'error', text: err.response?.data?.message || 'Error adding ticker' });
    }
  };

  const handleRemoveTicker = async (ticker: string) => {
    try {
      const data = await api.removeFromWatchlist(ticker);
      if (data.success) {
        fetchWatchlist();
      } else {
        alert(data.message || 'Error removing ticker');
      }
    } catch (err) {
      alert('Error removing ticker');
    }
  };

  const handleSort = (column: keyof WatchlistItem) => {
    const isAsc = sortColumn === column && sortDirection === 'asc';
    setSortDirection(isAsc ? 'desc' : 'asc');
    setSortColumn(column);

    const sortedData = [...watchlist].sort((a, b) => {
      let aVal: any = a[column];
      let bVal: any = b[column];

      if (aVal === null) aVal = column === 'adjusted_pe_ratio' ? Infinity : -1;
      if (bVal === null) bVal = column === 'adjusted_pe_ratio' ? Infinity : -1;

      if (typeof aVal === 'string') {
        const numA = parseFloat(aVal.replace(/[^\d.-]/g, ''));
        const numB = parseFloat(bVal.replace(/[^\d.-]/g, ''));
        if (!isNaN(numA) && !isNaN(numB)) {
          return isAsc ? numB - numA : numA - numB;
        }
        return isAsc ? bVal.localeCompare(aVal) : aVal.localeCompare(bVal);
      }
      return isAsc ? bVal - aVal : aVal - bVal;
    });
    setWatchlist(sortedData);
  };

  const getSortIcon = (column: keyof WatchlistItem) => {
    if (sortColumn !== column) return '⇅';
    return sortDirection === 'asc' ? '↑' : '↓';
  };

  return (
    <div className="flex flex-col">
      {/* Header */}
      <div className="p-10 text-center border-b border-border-color bg-header-bg rounded-t-[15px]">
        <h1 className="text-[2.5em] font-bold mb-2.5 text-text-secondary [text-shadow:0_0_8px_var(--glow-primary)]">
          📋 Watchlist
        </h1>
        <p className="opacity-85 text-[1.1em] text-text-primary [text-shadow:0_0_3px_var(--glow-primary)]">
          Your saved tickers with basic stats
        </p>
        <div className="mt-4 flex justify-center gap-2.5">
          <button 
            onClick={() => navigate(-1)} 
            className="flex items-center gap-2 px-5 py-2.5 bg-button-bg text-text-secondary border border-border-color rounded-lg transition-all hover:bg-opacity-80 hover:text-accent-primary hover:border-accent-primary hover:-translate-x-1"
          >
            <ArrowLeft className="w-4 h-4" /> Back
          </button>
          <Link 
            to="/ai-scores" 
            className="flex items-center gap-2 px-5 py-2.5 bg-button-bg text-text-secondary border border-border-color rounded-lg transition-all hover:bg-opacity-80 hover:text-accent-primary hover:border-accent-primary"
          >
            AI Analysis Scores
          </Link>
        </div>
      </div>

      <div className="p-10 bg-bg-secondary">
        {/* Add Ticker Section */}
        <div className="mb-[30px] p-[25px] bg-bg-tertiary rounded-[15px] border border-border-color shadow-[0_0_15px_var(--shadow-color)]">
          <div className="text-[1.15em] font-bold text-text-secondary mb-[15px] tracking-[0.3px] text-center">
            Add Ticker to Watchlist
          </div>
          <div className="flex gap-2.5 justify-center">
            <input 
              type="text" 
              value={newTicker}
              onChange={(e) => setNewTicker(e.target.value)}
              onKeyDown={(e) => e.key === 'Enter' && handleAddTicker()}
              placeholder="Enter ticker symbol (e.g., AAPL)"
              className="flex-1 max-w-[500px] p-[15px_20px] text-[1.05em] border border-border-color rounded-[10px] outline-none transition-all bg-input-bg text-text-secondary focus:border-accent-secondary focus:shadow-[0_0_15px_var(--glow-secondary)]"
            />
            <button 
              onClick={handleAddTicker}
              className="p-[15px_30px] text-[1.05em] bg-button-bg text-text-secondary border border-border-color rounded-[10px] cursor-pointer font-semibold transition-all hover:-translate-y-0.5 hover:bg-accent-primary hover:text-bg-primary hover:border-accent-primary hover:shadow-[0_0_12px_var(--glow-primary)]"
            >
              Add
            </button>
          </div>
          {addMessage && (
            <div className={`mt-2.5 p-2.5 rounded-lg border text-center ${
              addMessage.type === 'success' 
                ? 'bg-bg-secondary text-accent-success border-accent-success' 
                : 'bg-bg-secondary text-accent-danger border-accent-danger'
            }`}>
              {addMessage.text}
            </div>
          )}
        </div>

        {/* Watchlist Content */}
        <div id="watchlist-content">
          {loading ? (
            <div className="text-center p-10 text-text-muted">
              <Loader2 className="w-10 h-10 animate-spin mx-auto mb-5 text-accent-primary" />
              <p>Loading watchlist...</p>
            </div>
          ) : error ? (
            <div className="bg-bg-tertiary p-10 rounded-[15px] border border-border-color text-center text-accent-danger">
              <AlertCircle className="w-10 h-10 mx-auto mb-4" />
              <p>{error}</p>
            </div>
          ) : watchlist.length === 0 ? (
            <div className="text-center p-[80px_20px] text-text-muted bg-bg-tertiary rounded-[15px] border border-border-color shadow-[0_0_15px_var(--shadow-color)]">
              <p className="text-[1.5em] font-semibold text-text-secondary mb-[15px]">Your watchlist is empty</p>
              <p className="text-[1em] opacity-70">Search for a ticker and add it to your watchlist to see it here.</p>
            </div>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full border-separate border-spacing-0 mt-5 bg-bg-primary rounded-[15px] overflow-hidden border border-border-color shadow-[0_0_15px_var(--shadow-color)]">
                <thead>
                  <tr className="bg-table-header-bg">
                    <th className="p-[18px_15px] text-left font-semibold text-[0.95em] border-b border-border-color cursor-pointer hover:bg-table-hover-bg transition-all text-text-secondary" onClick={() => handleSort('ticker')}>
                      Ticker {getSortIcon('ticker')}
                    </th>
                    <th className="p-[18px_15px] text-left font-semibold text-[0.95em] border-b border-border-color cursor-pointer hover:bg-table-hover-bg transition-all text-text-secondary" onClick={() => handleSort('company_name')}>
                      Company Name {getSortIcon('company_name')}
                    </th>
                    <th className="p-[18px_15px] text-left font-semibold text-[0.95em] border-b border-border-color cursor-pointer hover:bg-table-hover-bg transition-all text-text-secondary" onClick={() => handleSort('total_score_percentile_rank')}>
                      Total Score {getSortIcon('total_score_percentile_rank')}
                    </th>
                    <th className="p-[18px_15px] text-left font-semibold text-[0.95em] border-b border-border-color cursor-pointer hover:bg-table-hover-bg transition-all text-text-secondary" onClick={() => handleSort('financial_total_percentile')}>
                      Financial Score {getSortIcon('financial_total_percentile')}
                    </th>
                    <th className="p-[18px_15px] text-left font-semibold text-[0.95em] border-b border-border-color cursor-pointer hover:bg-table-hover-bg transition-all text-text-secondary" onClick={() => handleSort('adjusted_pe_ratio')}>
                      Adjusted PE {getSortIcon('adjusted_pe_ratio')}
                    </th>
                    <th className="p-[18px_15px] text-left font-semibold text-[0.95em] border-b border-border-color cursor-pointer hover:bg-table-hover-bg transition-all text-text-secondary" onClick={() => handleSort('short_float')}>
                      Short Float {getSortIcon('short_float')}
                    </th>
                    <th className="p-[18px_15px] text-left font-semibold text-[0.95em] border-b border-border-color text-text-secondary">Actions</th>
                  </tr>
                </thead>
                <tbody>
                  {watchlist.map((item) => (
                    <tr key={item.ticker} className="hover:bg-table-hover-bg transition-all">
                      <td className="p-[18px_15px] border-b border-border-color">
                        <Link to={`/?q=${item.ticker}`} className="text-accent-secondary font-bold p-[4px_8px] rounded-md hover:bg-button-bg hover:text-accent-primary hover:translate-x-0.5 transition-all inline-block">
                          {item.ticker}
                        </Link>
                      </td>
                      <td className="p-[18px_15px] border-b border-border-color text-text-secondary">
                        {item.company_name || item.ticker}
                      </td>
                      <td className="p-[18px_15px] border-b border-border-color">
                        {item.total_score_percentile_rank !== null ? (
                          <Link to={`/metrics/${item.ticker}`} className="text-accent-secondary font-semibold hover:underline">
                            {item.total_score_percentile_rank}%
                          </Link>
                        ) : 'N/A'}
                      </td>
                      <td className="p-[18px_15px] border-b border-border-color">
                        {item.financial_total_percentile !== null ? (
                          <Link to={`/financial/${item.ticker}`} className="text-accent-secondary font-semibold hover:underline">
                            {Math.round(item.financial_total_percentile)}%
                          </Link>
                        ) : 'N/A'}
                      </td>
                      <td className="p-[18px_15px] border-b border-border-color">
                        {item.adjusted_pe_ratio !== null ? (
                          <Link to={`/adjusted-pe/${item.ticker}`} className="text-accent-secondary font-semibold hover:underline">
                            {item.adjusted_pe_ratio.toFixed(2)}
                          </Link>
                        ) : 'N/A'}
                      </td>
                      <td className="p-[18px_15px] border-b border-border-color text-text-secondary">
                        {item.short_float || 'N/A'}
                      </td>
                      <td className="p-[18px_15px] border-b border-border-color">
                        <button 
                          onClick={() => handleRemoveTicker(item.ticker)}
                          className="p-[8px_16px] text-[0.9em] bg-button-bg text-accent-danger border border-border-color rounded-lg font-semibold transition-all hover:bg-accent-danger hover:text-bg-primary hover:border-accent-danger hover:-translate-y-0.5"
                        >
                          <Trash2 className="w-4 h-4 inline mr-1" /> Remove
                        </button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default WatchlistPage;
