import React, { useState, useEffect } from 'react';
import { useParams, useNavigate, Link } from 'react-router-dom';
import { ArrowLeft, Loader2, AlertCircle } from 'lucide-react';
import * as api from '../api';

interface PeerCompany {
  ticker: string | null;
  company_name: string | null;
  total_score_percentile_rank: number | null;
  financial_total_percentile: number | null;
  adjusted_pe_ratio: number | null;
  short_float: string | null;
}

interface PeerDataResponse {
  main_ticker: PeerCompany;
  peers: PeerCompany[];
}

const PeersPage: React.FC = () => {
  const { ticker } = useParams<{ ticker: string }>();
  const navigate = useNavigate();
  const [data, setData] = useState<PeerDataResponse | null>(null);
  const [sortedCompanies, setSortedCompanies] = useState<PeerCompany[]>([]);
  const [loading, setLoading] = useState(true);
  const [loadingMessage, setLoadingMessage] = useState('Loading peer data from database...');
  const [error, setError] = useState<string | null>(null);
  const [sortColumn, setSortColumn] = useState<string | null>(null);
  const [sortDirection, setSortDirection] = useState<'asc' | 'desc'>('asc');

  useEffect(() => {
    if (!ticker) return;

    const aiTimeout = setTimeout(() => {
      setLoadingMessage(`Generating AI peer recommendations for ${ticker}... (No existing peers found. AI is analyzing the market to find the best matches. This typically takes 20-30 seconds.)`);
    }, 2000);

    const fetchPeers = async () => {
      try {
        const response = await api.getPeers(ticker);
        clearTimeout(aiTimeout);
        if (response.success) {
          setData(response);
          setSortedCompanies([response.main_ticker, ...(response.peers || [])]);
        } else {
          setError(response.message || 'Error loading peer data');
        }
      } catch (err: any) {
        clearTimeout(aiTimeout);
        setError(err.response?.data?.message || 'Error loading peer data');
      } finally {
        setLoading(false);
      }
    };

    fetchPeers();
  }, [ticker]);

  const handleSort = (column: string) => {
    if (!data) return;

    const isAsc = sortColumn === column && sortDirection === 'asc';
    const direction = isAsc ? 'desc' : 'asc';
    setSortDirection(direction);
    setSortColumn(column);

    const allCompanies = [data.main_ticker, ...data.peers];
    
    const getSortValue = (obj: PeerCompany, col: string) => {
      switch (col) {
        case 'ticker': return obj.ticker || '';
        case 'company_name': return obj.company_name || '';
        case 'total_score_percentile_rank': return obj.total_score_percentile_rank;
        case 'financial_total_percentile': return obj.financial_total_percentile;
        case 'adjusted_pe_ratio': return obj.adjusted_pe_ratio;
        case 'short_float':
          if (obj.short_float && typeof obj.short_float === 'string') {
            const match = obj.short_float.match(/(\d+(?:\.\d+)?)/);
            return match ? parseFloat(match[1]) : 0;
          }
          return 0;
        default: return (obj as any)[col];
      }
    };

    const sorted = allCompanies.sort((a, b) => {
      let aVal = getSortValue(a, column);
      let bVal = getSortValue(b, column);

      if (aVal === null || aVal === undefined) aVal = direction === 'asc' ? Infinity : -Infinity;
      if (bVal === null || bVal === undefined) bVal = direction === 'asc' ? Infinity : -Infinity;

      if (aVal < bVal) return direction === 'asc' ? -1 : 1;
      if (aVal > bVal) return direction === 'asc' ? 1 : -1;
      return 0;
    });

    setSortedCompanies(sorted);
  };

  const getSortIcon = (column: string) => {
    if (sortColumn !== column) return '⇅';
    return sortDirection === 'asc' ? '↑' : '↓';
  };

  return (
    <div className="flex flex-col">
      {/* Header */}
      <div className="p-10 text-center border-b border-border-color bg-header-bg">
        <h1 className="text-[2.5em] font-bold mb-2.5 text-text-secondary [text-shadow:0_0_8px_var(--glow-primary)]">
          Peer Comparison
        </h1>
        <p className="opacity-85 text-[1.1em] text-text-primary">
          Comparing {ticker} with its peers
        </p>
        <button 
          onClick={() => navigate(-1)} 
          className="mt-5 flex items-center gap-2 px-5 py-2.5 bg-button-bg text-text-secondary border border-border-color transition-all hover:bg-opacity-80 hover:text-accent-primary hover:border-accent-primary hover:-translate-x-1 mx-auto"
        >
          <ArrowLeft className="w-4 h-4" /> Back
        </button>
      </div>

      <div className="p-[20px_40px_40px] bg-bg-secondary min-h-[400px]">
        {loading ? (
          <div className="text-center p-10 text-text-muted">
            <Loader2 className="w-10 h-10 animate-spin mx-auto mb-5 text-accent-primary" />
            <p>{loadingMessage}</p>
          </div>
        ) : error ? (
          <div className="bg-bg-tertiary p-10 border border-border-color text-center text-accent-danger">
            <AlertCircle className="w-10 h-10 mx-auto mb-4" />
            <p>{error}</p>
          </div>
        ) : sortedCompanies.length === 0 ? (
          <div className="text-center p-[80px_20px] text-text-muted bg-bg-tertiary border border-border-color shadow-[0_0_15px_var(--shadow-color)]">
            <p>No peers found for {ticker}</p>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full border-collapse mt-5 bg-bg-primary overflow-hidden shadow-[0_0_15px_var(--shadow-color)]">
              <thead>
                <tr className="bg-table-header-bg">
                  <th className="p-[15px] text-left font-semibold border-b-2 border-border-color cursor-pointer select-none transition-all hover:bg-table-hover-bg text-text-secondary" onClick={() => handleSort('ticker')}>
                    Ticker {getSortIcon('ticker')}
                  </th>
                  <th className="p-[15px] text-left font-semibold border-b-2 border-border-color cursor-pointer select-none transition-all hover:bg-table-hover-bg text-text-secondary" onClick={() => handleSort('company_name')}>
                    Company Name {getSortIcon('company_name')}
                  </th>
                  <th className="p-[15px] text-left font-semibold border-b-2 border-border-color cursor-pointer select-none transition-all hover:bg-table-hover-bg text-text-secondary" onClick={() => handleSort('total_score_percentile_rank')}>
                    Total Score {getSortIcon('total_score_percentile_rank')}
                  </th>
                  <th className="p-[15px] text-left font-semibold border-b-2 border-border-color cursor-pointer select-none transition-all hover:bg-table-hover-bg text-text-secondary" onClick={() => handleSort('financial_total_percentile')}>
                    Financial Score {getSortIcon('financial_total_percentile')}
                  </th>
                  <th className="p-[15px] text-left font-semibold border-b-2 border-border-color cursor-pointer select-none transition-all hover:bg-table-hover-bg text-text-secondary" onClick={() => handleSort('adjusted_pe_ratio')}>
                    Adjusted PE {getSortIcon('adjusted_pe_ratio')}
                  </th>
                  <th className="p-[15px] text-left font-semibold border-b-2 border-border-color cursor-pointer select-none transition-all hover:bg-table-hover-bg text-text-secondary" onClick={() => handleSort('short_float')}>
                    Short Float {getSortIcon('short_float')}
                  </th>
                </tr>
              </thead>
              <tbody>
                {sortedCompanies.map((company, index) => {
                  const isMainTicker = company.ticker === ticker;
                  const linkTicker = company.ticker || company.company_name;
                  
                  return (
                    <tr key={(company.ticker || '') + index} className={`hover:bg-table-hover-bg transition-all ${isMainTicker ? 'bg-bg-secondary font-semibold border-y-2 border-accent-secondary' : ''}`}>
                      <td className="p-[15px] border-b border-border-color">
                        {company.ticker ? (
                          <Link to={`/?q=${company.ticker}`} className="text-accent-secondary hover:text-accent-primary hover:underline transition-all">
                            {company.ticker}
                          </Link>
                        ) : 'N/A'}
                      </td>
                      <td className="p-[15px] border-b border-border-color text-text-secondary">
                        {company.company_name || 'N/A'}
                      </td>
                      <td className="p-[15px] border-b border-border-color">
                        {company.total_score_percentile_rank !== null ? (
                          <Link to={`/metrics/${linkTicker}`} className="text-accent-secondary hover:text-accent-primary hover:underline transition-all">
                            {company.total_score_percentile_rank}%
                          </Link>
                        ) : 'N/A'}
                      </td>
                      <td className="p-[15px] border-b border-border-color">
                        {company.financial_total_percentile !== null ? (
                          <Link to={`/financial/${linkTicker}`} className="text-accent-secondary hover:text-accent-primary hover:underline transition-all">
                            {Math.round(company.financial_total_percentile)}%
                          </Link>
                        ) : 'N/A'}
                      </td>
                      <td className="p-[15px] border-b border-border-color">
                        {company.adjusted_pe_ratio !== null ? (
                          <Link to={`/adjusted-pe/${linkTicker}`} className="text-accent-secondary hover:text-accent-primary hover:underline transition-all">
                            {company.adjusted_pe_ratio.toFixed(2)}
                          </Link>
                        ) : 'N/A'}
                      </td>
                      <td className="p-[15px] border-b border-border-color text-text-secondary">
                        {company.short_float || 'N/A'}
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
};

export default PeersPage;
