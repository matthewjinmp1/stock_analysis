import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { ArrowLeft, Loader2, AlertCircle, Cpu, Clock, DollarSign } from 'lucide-react';
import * as api from '../api';

const FindPeersPage: React.FC = () => {
  const navigate = useNavigate();
  const [ticker, setTicker] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<any>(null);

  const handleFindPeers = async () => {
    const searchTicker = ticker.trim().toUpperCase();
    if (!searchTicker) {
      setError('Please enter a ticker symbol');
      return;
    }

    setLoading(true);
    setError(null);
    setResult(null);

    try {
      const data = await api.findPeersAI(searchTicker);
      if (data.success) {
        setResult(data);
      } else {
        setError(data.message || 'Error finding peers');
      }
    } catch (err: any) {
      setError(err.response?.data?.message || 'Error finding peers. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="flex flex-col w-full min-h-screen">
      <div className="p-10 text-center border-b border-border-color bg-header-bg">
        <h1 className="text-4xl md:text-5xl font-black mb-4 text-text-secondary [text-shadow:0_0_8px_var(--glow-primary)]">
          🤖 AI Peer Finder
        </h1>
        <p className="opacity-85 text-xl text-text-primary font-medium">
          Find comparable companies using artificial intelligence
        </p>
        <div className="mt-6 flex justify-center">
          <button 
            onClick={() => navigate(-1)} 
            className="flex items-center gap-3 px-8 py-3 bg-button-bg text-text-secondary border border-border-color font-black text-lg transition-all hover:bg-accent-primary hover:text-bg-primary hover:border-accent-primary active:scale-95 shadow-lg"
          >
            <ArrowLeft className="w-5 h-5" /> Back to Search
          </button>
        </div>
      </div>

      <div className="p-10 bg-bg-secondary flex-1 flex flex-col items-center">
        <div className="w-full max-w-2xl p-10 bg-bg-tertiary border border-border-color shadow-2xl text-center mb-10">
          <div className="mb-8 text-center">
            <label htmlFor="tickerInput" className="block text-text-muted mb-4 font-black uppercase tracking-widest opacity-70">Enter Ticker Symbol:</label>
            <input 
              type="text" 
              id="tickerInput" 
              value={ticker}
              onChange={(e) => setTicker(e.target.value)}
              onKeyDown={(e) => e.key === 'Enter' && handleFindPeers()}
              placeholder="e.g., AAPL, MSFT, GOOGL" 
              className="w-full p-5 bg-input-bg border border-border-color text-text-secondary text-center text-2xl outline-none focus:border-accent-secondary focus:ring-4 focus:ring-accent-secondary/10 shadow-sm uppercase font-black"
            />
          </div>
          <button 
            onClick={handleFindPeers}
            disabled={loading}
            className="w-full py-5 bg-accent-primary text-bg-primary font-black text-xl transition-all hover:opacity-90 active:scale-95 disabled:opacity-50 disabled:cursor-not-allowed shadow-lg"
          >
            {loading ? 'ANALYZING MARKET...' : 'FIND COMPARABLE PEERS'}
          </button>
        </div>

        {loading && (
          <div className="text-center p-20 text-text-muted w-full max-w-2xl bg-bg-tertiary border border-border-color shadow-2xl">
            <Loader2 className="w-12 h-12 animate-spin mx-auto mb-6 text-accent-primary" />
            <p className="text-2xl font-black text-text-secondary mb-4 uppercase tracking-widest">Finding peers for {ticker.toUpperCase()}...</p>
            <p className="text-lg font-medium opacity-70">
              AI is analyzing the market to find the 10 most comparable companies.
              This typically takes 20-30 seconds.
            </p>
          </div>
        )}

        {error && (
          <div className="w-full max-w-2xl bg-accent-danger/10 text-accent-danger p-8 border border-accent-danger/30 text-center mt-10 shadow-2xl">
            <AlertCircle className="w-12 h-12 mx-auto mb-4" />
            <p className="font-black text-xl">{error}</p>
          </div>
        )}

        {result && (
          <div className="w-full max-w-4xl animate-[fadeIn_0.5s_ease-out]">
            <div className="bg-bg-tertiary p-10 border border-border-color shadow-2xl mb-10">
              <div className="text-center mb-10 pb-6 border-b border-border-color">
                <h2 className="text-4xl font-black text-accent-secondary mb-2">{result.ticker}</h2>
                <p className="text-xl font-medium text-text-muted italic">{result.company_name || 'Company name not found'}</p>
              </div>
              
              <div className="grid gap-4">
                {result.peers.map((peer: any, index: number) => (
                  <div key={index} className="bg-bg-primary p-6 border border-border-color transition-all hover:bg-table-hover-bg hover:border-accent-primary flex items-center gap-6 group">
                    <div className="text-text-muted font-black text-2xl w-12 opacity-50 group-hover:text-accent-secondary transition-colors">#{index + 1}</div>
                    <div className="text-text-secondary font-black text-2xl">
                      {typeof peer === 'string' ? peer : `${peer.name} (${peer.ticker})`}
                    </div>
                  </div>
                ))}
              </div>
            </div>

            {(result.elapsed_time || result.token_usage || result.estimated_cost) && (
              <div className="bg-bg-secondary p-8 border border-border-color shadow-xl mb-20">
                <h3 className="text-text-muted font-black text-sm uppercase tracking-[0.2em] mb-6 flex items-center gap-3">
                  <Cpu className="w-5 h-5" /> Query Statistics
                </h3>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                  {result.elapsed_time && (
                    <div className="bg-bg-primary p-4 border border-border-color/50 flex items-center gap-4">
                      <Clock className="w-5 h-5 text-accent-secondary" />
                      <span className="text-text-secondary font-bold">Time: {result.elapsed_time.toFixed(2)}s</span>
                    </div>
                  )}
                  {result.estimated_cost !== undefined && (
                    <div className="bg-bg-primary p-4 border border-border-color/50 flex items-center gap-4">
                      <DollarSign className="w-5 h-5 text-accent-success" />
                      <span className="text-text-secondary font-bold">Cost: {(result.estimated_cost * 100).toFixed(4)}¢</span>
                    </div>
                  )}
                </div>
              </div>
            )}
          </div>
        )}
      </div>
      <style>{`
        @keyframes fadeIn {
          from { opacity: 0; }
          to { opacity: 1; }
        }
      `}</style>
    </div>
  );
};

export default FindPeersPage;
