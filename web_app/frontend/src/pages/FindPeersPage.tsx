import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { ArrowLeft, Loader2, AlertCircle, Cpu, Clock, DollarSign, ListOrdered } from 'lucide-react';
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
    <div className="flex flex-col">
      <div className="p-6 pb-0">
        <button 
          onClick={() => navigate(-1)} 
          className="flex items-center gap-2 px-4 py-2 bg-button-bg text-text-secondary border border-border-color rounded-lg transition-all hover:bg-opacity-80 hover:text-accent-primary hover:border-accent-primary hover:-translate-x-1"
        >
          <ArrowLeft className="w-4 h-4" /> Back
        </button>
      </div>

      <div className="p-10 text-center">
        <h1 className="text-[2.5em] font-bold mb-2.5 text-text-secondary [text-shadow:0_0_8px_var(--glow-primary)]">
          🤖 AI Peer Finder
        </h1>
        <p className="opacity-85 text-[1.1em] text-text-primary">
          Find comparable companies using artificial intelligence
        </p>
      </div>

      <div className="p-10 pt-0 bg-bg-secondary flex flex-col items-center">
        <div className="w-full max-w-lg p-[30px] bg-bg-secondary rounded-[15px] border border-border-color shadow-[0_0_15px_var(--shadow-color)] text-center mb-5">
          <div className="mb-5">
            <label htmlFor="tickerInput" className="block text-text-secondary mb-2 font-medium">Enter Ticker Symbol:</label>
            <input 
              type="text" 
              id="tickerInput" 
              value={ticker}
              onChange={(e) => setTicker(e.target.value)}
              onKeyDown={(e) => e.key === 'Enter' && handleFindPeers()}
              placeholder="e.g., AAPL, MSFT, GOOGL" 
              className="w-full p-3 bg-input-bg border border-border-color rounded-lg text-text-secondary text-center text-[1em] outline-none focus:border-accent-secondary focus:shadow-[0_0_8px_var(--glow-primary)] uppercase"
            />
          </div>
          <button 
            onClick={handleFindPeers}
            disabled={loading}
            className="w-full py-3 bg-button-bg text-text-primary border border-border-color rounded-lg font-semibold transition-all hover:bg-accent-primary hover:text-bg-primary hover:border-accent-primary disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {loading ? 'Searching...' : 'Find Peers'}
          </button>
        </div>

        {loading && (
          <div className="text-center p-10 text-text-muted w-full max-w-lg">
            <Loader2 className="w-10 h-10 animate-spin mx-auto mb-5 text-accent-primary" />
            <p className="text-lg">Finding peers for {ticker.toUpperCase()} using AI...</p>
            <p className="text-sm mt-2 opacity-70">
              AI is analyzing the market to find the 10 most comparable companies.
              This typically takes 20-30 seconds.
            </p>
          </div>
        )}

        {error && (
          <div className="w-full max-w-lg bg-button-bg text-accent-danger p-5 rounded-[12px] border border-accent-danger text-center mt-5">
            <AlertCircle className="w-8 h-8 mx-auto mb-2" />
            <p>{error}</p>
          </div>
        )}

        {result && (
          <div className="w-full max-w-3xl animate-[fadeIn_0.5s_ease-out]">
            <div className="bg-bg-secondary rounded-[15px] p-[30px] border border-border-color shadow-[0_0_15px_var(--shadow-color)] mb-5">
              <div className="text-center mb-[30px] pb-5 border-b border-border-color">
                <h2 className="text-2xl font-bold text-text-secondary mb-1">{result.ticker}</h2>
                <p className="text-text-muted">{result.company_name || 'Company name not found'}</p>
              </div>
              
              <div className="grid gap-[15px]">
                {result.peers.map((peer: any, index: number) => (
                  <div key={index} className="bg-bg-primary p-[15px] rounded-lg border border-border-color transition-all hover:bg-table-hover-bg hover:border-accent-primary flex items-center gap-4">
                    <div className="text-text-muted font-bold text-lg w-8">#{index + 1}</div>
                    <div className="text-text-secondary font-medium text-lg">
                      {typeof peer === 'string' ? peer : `${peer.name} (${peer.ticker})`}
                    </div>
                  </div>
                ))}
              </div>
            </div>

            {(result.elapsed_time || result.token_usage || result.estimated_cost) && (
              <div className="bg-card-bg rounded-lg p-[15px] border border-border-color">
                <h3 className="text-text-secondary font-semibold mb-2.5 flex items-center gap-2">
                  <Cpu className="w-4 h-4" /> Query Statistics
                </h3>
                <div className="space-y-1 text-sm">
                  {result.elapsed_time && (
                    <p className="text-text-muted flex items-center gap-2">
                      <Clock className="w-3.5 h-3.5" /> Time taken: {result.elapsed_time.toFixed(2)} seconds
                    </p>
                  )}
                  {result.estimated_cost !== undefined && (
                    <p className="text-text-muted flex items-center gap-2">
                      <DollarSign className="w-3.5 h-3.5" /> Estimated cost: {(result.estimated_cost * 100).toFixed(4)} cents
                    </p>
                  )}
                  {result.token_usage && (
                    <div className="text-text-muted text-[0.9em] flex items-start gap-2 mt-2">
                      <ListOrdered className="w-3.5 h-3.5 mt-0.5" /> 
                      <span>Token usage: {JSON.stringify(result.token_usage)}</span>
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
