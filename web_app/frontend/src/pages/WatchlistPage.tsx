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
    <div className="flex flex-col w-full min-h-screen pb-20">
      {/* Header */}
      <div className="p-10 text-center border-b border-border-color bg-header-bg">
        <h1 className="text-4xl md:text-5xl font-black mb-4 text-text-secondary [text-shadow:0_0_8px_var(--glow-primary)]">
          📋 Watchlist
        </h1>
        <p className="opacity-85 text-xl text-text-primary [text-shadow:0_0_3px_var(--glow-primary)] font-medium">
          Your saved tickers with basic stats
        </p>
        <div className="mt-6 flex justify-center gap-6">
          <button 
            onClick={() => navigate(-1)} 
            className="flex items-center gap-3 px-8 py-3 bg-button-bg text-text-secondary border border-border-color font-black text-lg transition-all hover:bg-accent-primary hover:text-bg-primary hover:border-accent-primary active:scale-95 shadow-lg"
          >
            <ArrowLeft className="w-5 h-5" /> Back
          </button>
          <Link 
            to="/ai-scores" 
            className="flex items-center gap-3 px-8 py-3 bg-button-bg text-text-secondary border border-border-color font-black text-lg transition-all hover:bg-accent-primary hover:text-bg-primary hover:border-accent-primary shadow-lg"
          >
            AI Analysis Scores
          </Link>
        </div>
      </div>

      <div className="p-10 bg-bg-secondary flex-1 flex flex-col items-center">
        {/* Add Ticker Section */}
        <div className="mb-10 p-10 bg-bg-tertiary border border-border-color shadow-2xl w-full max-w-[1000px]">
          <div className="text-2xl font-black text-text-secondary mb-8 uppercase tracking-widest text-center opacity-70">
            Add Ticker to Watchlist
          </div>
          <div className="flex gap-4 justify-center max-w-2xl mx-auto">
            <input 
              type="text" 
              value={newTicker}
              onChange={(e) => setNewTicker(e.target.value)}
              onKeyDown={(e) => e.key === 'Enter' && handleAddTicker()}
              placeholder="Enter ticker symbol (e.g., AAPL)"
              className="flex-1 p-5 text-xl border border-border-color outline-none transition-all bg-input-bg text-text-secondary focus:border-accent-secondary focus:ring-4 focus:ring-accent-secondary/10 shadow-sm font-medium"
            />
            <button 
              onClick={handleAddTicker}
              className="px-10 bg-accent-primary text-bg-primary font-black text-xl transition-all hover:opacity-90 active:scale-95 shadow-lg"
            >
              Add
            </button>
          </div>
          {addMessage && (
            <div className={`mt-6 p-4 border text-center font-bold text-lg ${
              addMessage.type === 'success' 
                ? 'bg-accent-success/10 text-accent-success border-accent-success/30' 
                : 'bg-accent-danger/10 text-accent-danger border-accent-danger/30'
            }`}>
              {addMessage.text}
            </div>
          )}
        </div>

        {/* Watchlist Content */}
        <div id="watchlist-content" className="w-full max-w-[1400px]">
          {loading ? (
            <div className="text-center p-20 text-text-muted">
              <Loader2 className="w-12 h-12 animate-spin mx-auto mb-6 text-accent-primary" />
              <p className="font-bold text-lg">Loading watchlist...</p>
            </div>
          ) : error ? (
            <div className="bg-bg-tertiary p-12 border border-border-color text-center text-accent-danger shadow-2xl">
              <AlertCircle className="w-12 h-12 mx-auto mb-4" />
              <p className="font-black text-xl">{error}</p>
            </div>
          ) : watchlist.length === 0 ? (
            <div className="text-center p-20 text-text-muted bg-bg-tertiary border border-border-color shadow-2xl">
              <p className="text-3xl font-black text-text-secondary mb-4 uppercase tracking-widest opacity-70">Your watchlist is empty</p>
              <p className="text-lg font-medium opacity-70">Search for a ticker and add it to your watchlist to see it here.</p>
            </div>
          ) : (
            <div className="overflow-x-auto bg-bg-primary border border-border-color shadow-2xl">
              <table className="w-full border-collapse">
                <thead>
                  <tr className="bg-table-header-bg">
                    <th className="p-5 text-left font-black uppercase text-xs tracking-[0.2em] border-b border-border-color cursor-pointer hover:bg-table-hover-bg transition-all text-text-secondary" onClick={() => handleSort('ticker')}>
                      Ticker {getSortIcon('ticker')}
                    </th>
                    <th className="p-5 text-left font-black uppercase text-xs tracking-[0.2em] border-b border-border-color cursor-pointer hover:bg-table-hover-bg transition-all text-text-secondary" onClick={() => handleSort('company_name')}>
                      Company {getSortIcon('company_name')}
                    </th>
                    <th className="p-5 text-center font-black uppercase text-xs tracking-[0.2em] border-b border-border-color cursor-pointer hover:bg-table-hover-bg transition-all text-text-secondary" onClick={() => handleSort('total_score_percentile_rank')}>
                      Total Score {getSortIcon('total_score_percentile_rank')}
                    </th>
                    <th className="p-5 text-center font-black uppercase text-xs tracking-[0.2em] border-b border-border-color cursor-pointer hover:bg-table-hover-bg transition-all text-text-secondary" onClick={() => handleSort('financial_total_percentile')}>
                      Financial {getSortIcon('financial_total_percentile')}
                    </th>
                    <th className="p-5 text-center font-black uppercase text-xs tracking-[0.2em] border-b border-border-color cursor-pointer hover:bg-table-hover-bg transition-all text-text-secondary" onClick={() => handleSort('adjusted_pe_ratio')}>
                      Adj PE {getSortIcon('adjusted_pe_ratio')}
                    </th>
                    <th className="p-5 text-center font-black uppercase text-xs tracking-[0.2em] border-b border-border-color cursor-pointer hover:bg-table-hover-bg transition-all text-text-secondary" onClick={() => handleSort('short_float')}>
                      Short Float {getSortIcon('short_float')}
                    </th>
                    <th className="p-5 text-center font-black uppercase text-xs tracking-[0.2em] border-b border-border-color text-text-secondary">Actions</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-border-color/30">
                  {watchlist.map((item) => (
                    <tr key={item.ticker} className="hover:bg-table-hover-bg/50 transition-all group">
                      <td className="p-5">
                        <Link to={`/?q=${item.ticker}`} className="text-accent-secondary font-black text-xl hover:text-accent-primary transition-all inline-block">
                          {item.ticker}
                        </Link>
                      </td>
                      <td className="p-5 text-text-secondary font-bold truncate max-w-[200px]">
                        {item.company_name || item.ticker}
                      </td>
                      <td className="p-5 text-center">
                        {item.total_score_percentile_rank !== null ? (
                          <Link to={`/metrics/${item.ticker}`} className="text-accent-secondary font-black text-lg hover:underline decoration-2 underline-offset-4">
                            {item.total_score_percentile_rank}%
                          </Link>
                        ) : 'N/A'}
                      </td>
                      <td className="p-5 text-center">
                        {item.financial_total_percentile !== null ? (
                          <Link to={`/financial/${item.ticker}`} className="text-accent-secondary font-black text-lg hover:underline decoration-2 underline-offset-4">
                            {Math.round(item.financial_total_percentile)}%
                          </Link>
                        ) : 'N/A'}
                      </td>
                      <td className="p-5 text-center">
                        {item.adjusted_pe_ratio !== null ? (
                          <Link to={`/adjusted-pe/${item.ticker}`} className="text-accent-secondary font-black text-lg hover:underline decoration-2 underline-offset-4">
                            {item.adjusted_pe_ratio.toFixed(2)}
                          </Link>
                        ) : 'N/A'}
                      </td>
                      <td className="p-5 text-center text-text-primary font-bold">
                        {item.short_float || 'N/A'}
                      </td>
                      <td className="p-5 text-center">
                        <button 
                          onClick={() => handleRemoveTicker(item.ticker)}
                          className="px-4 py-2 bg-accent-danger/10 text-accent-danger border border-accent-danger/30 font-black text-xs uppercase tracking-widest transition-all hover:bg-accent-danger hover:text-bg-primary active:scale-95"
                        >
                          <Trash2 className="w-4 h-4 inline-block mr-2" /> Remove
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
