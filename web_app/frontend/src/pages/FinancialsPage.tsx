import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { ArrowLeft, Loader2, AlertCircle } from 'lucide-react';
import * as api from '../api';

interface FinancialMetric {
  key: string;
  name: string;
  description: string;
  value: number;
  rank: number | null;
  percentile: number | null;
  sort_descending: boolean;
}

interface FinancialsResponse {
  ticker: string;
  company_name: string | null;
  metrics: FinancialMetric[];
  total_percentile: number | null;
  total_rank: number | null;
}

const FinancialsPage: React.FC = () => {
  const { ticker } = useParams<{ ticker: string }>();
  const navigate = useNavigate();
  const [data, setData] = useState<FinancialsResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!ticker) return;
    const fetchFinancials = async () => {
      try {
        const response = await api.getFinancials(ticker);
        if (response.success) {
          setData(response);
        } else {
          setError(response.message || 'Error loading financial metrics');
        }
      } catch (err: any) {
        setError(err.response?.data?.message || 'Error loading financial metrics');
      } finally {
        setLoading(false);
      }
    };
    fetchFinancials();
  }, [ticker]);

  const getPercentileBadgeClass = (percentile: number | null) => {
    if (percentile === null) return 'bg-bg-secondary text-text-muted border-border-color';
    if (percentile >= 70) return 'bg-bg-secondary text-accent-success border-accent-success';
    if (percentile >= 30) return 'bg-bg-secondary text-accent-warning border-accent-warning';
    return 'bg-bg-secondary text-accent-danger border-accent-danger';
  };

  return (
    <div className="flex flex-col w-full pb-10">
      <div className="p-6">
        <button 
          onClick={() => navigate(-1)} 
          className="flex items-center gap-2 px-5 py-2.5 bg-button-bg text-text-secondary border border-border-color font-bold transition-all hover:bg-opacity-80 hover:text-accent-primary hover:border-accent-primary hover:-translate-x-1 shadow-sm"
        >
          <ArrowLeft className="w-4 h-4" /> Back
        </button>
      </div>

      {loading ? (
        <div className="text-center p-20 text-text-muted min-h-[400px]">
          <Loader2 className="w-12 h-12 animate-spin mx-auto mb-6 text-accent-primary" />
          <p className="font-bold text-lg">Loading financial metrics...</p>
        </div>
      ) : error ? (
        <div className="p-12 mx-6 bg-accent-danger/5 border border-accent-danger/20 text-center text-accent-danger mb-10 shadow-lg">
          <AlertCircle className="w-12 h-12 mx-auto mb-4" />
          <h2 className="text-2xl font-black mb-2">Error</h2>
          <p className="font-medium">{error}</p>
        </div>
      ) : data ? (
        <>
          <div className="p-10 text-center border-b border-border-color bg-bg-tertiary/30 mb-8">
            <h1 className="text-4xl md:text-5xl font-black mb-4 text-text-secondary [text-shadow:0_0_8px_var(--glow-primary)]">
              {data.company_name || data.ticker}
            </h1>
            <div className="text-2xl text-accent-secondary font-black bg-button-bg px-6 py-2 inline-block border border-border-color shadow-sm">
              {data.ticker}
            </div>
            
            {data.total_percentile !== null && (
              <div className="flex flex-wrap gap-6 mt-8 justify-center">
                <div className="bg-bg-primary p-6 border border-border-color shadow-xl min-w-[180px] text-left">
                  <div className="text-xs font-black text-text-muted uppercase tracking-widest mb-2 opacity-70">Financial Score</div>
                  <div className="text-4xl font-black text-text-secondary">{data.total_percentile.toFixed(1)}th percentile</div>
                </div>
                {data.total_rank !== null && (
                  <div className="bg-bg-primary p-6 border border-border-color shadow-xl min-w-[180px] text-left">
                    <div className="text-xs font-black text-text-muted uppercase tracking-widest mb-2 opacity-70">Rank</div>
                    <div className="text-4xl font-black text-text-secondary">{data.total_rank}</div>
                  </div>
                )}
              </div>
            )}
          </div>

          <div className="mx-6 bg-bg-primary border border-border-color shadow-2xl overflow-x-auto">
            <table className="w-full border-collapse">
              <thead className="bg-table-header-bg text-text-secondary">
                <tr>
                  <th className="p-6 text-left font-black uppercase text-xs tracking-widest border-b border-border-color">Metric</th>
                  <th className="p-6 text-right font-black uppercase text-xs tracking-widest border-b border-border-color">Value</th>
                  <th className="p-6 text-center font-black uppercase text-xs tracking-widest border-b border-border-color">Rank</th>
                  <th className="p-6 text-center font-black uppercase text-xs tracking-widest border-b border-border-color">Percentile</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-border-color/50">
                {data.metrics.map((metric) => (
                  <tr key={metric.key} className="hover:bg-table-hover-bg transition-all group">
                    <td className="p-6">
                      <div className="font-bold text-lg text-text-secondary">{metric.name}</div>
                      <div className="text-sm text-text-muted mt-1 italic">{metric.description}</div>
                    </td>
                    <td className="p-6 text-right font-black text-text-secondary text-lg">
                      {metric.value !== null ? (
                        Math.abs(metric.value) >= 1 || metric.value === 0 
                          ? metric.value.toFixed(2) 
                          : metric.value.toFixed(4)
                      ) : 'N/A'}
                    </td>
                    <td className="p-6 text-center text-text-muted font-bold">
                      {metric.rank ?? 'N/A'}
                    </td>
                    <td className="p-6 text-center">
                      <span className={`inline-block px-4 py-1.5 font-black text-base border shadow-sm ${getPercentileBadgeClass(metric.percentile)}`}>
                        {metric.percentile !== null ? `${metric.percentile.toFixed(1)}th` : 'N/A'}
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </>
      ) : null}
    </div>
  );
};

export default FinancialsPage;
