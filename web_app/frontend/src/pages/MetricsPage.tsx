import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { ArrowLeft, Loader2, AlertCircle } from 'lucide-react';
import * as api from '../api';

interface MetricDetail {
  key: string;
  name: string;
  raw_score: number;
  adjusted_score: number;
  weight: number;
  contribution: number;
  is_reverse: boolean;
  percentage: number;
}

interface MetricsResponse {
  ticker: string;
  company_name: string | null;
  metrics: MetricDetail[];
  total_score_percentage: number | null;
  total_score_percentile_rank: number | null;
  max_score: number;
}

const MetricsPage: React.FC = () => {
  const { ticker } = useParams<{ ticker: string }>();
  const navigate = useNavigate();
  const [data, setData] = useState<MetricsResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!ticker) return;
    const fetchMetrics = async () => {
      try {
        const response = await api.getMetrics(ticker);
        if (response.success) {
          setData(response);
        } else {
          setError(response.message || 'Error loading metrics');
        }
      } catch (err: any) {
        setError(err.response?.data?.message || 'Error loading metrics');
      } finally {
        setLoading(false);
      }
    };
    fetchMetrics();
  }, [ticker]);

  const getScoreColorClass = (raw_score: number, is_reverse: boolean) => {
    const score = is_reverse ? 10 - raw_score : raw_score;
    if (score >= 7.5) return 'bg-accent-success/10 text-accent-success border-accent-success/30';
    if (score >= 5) return 'bg-accent-warning/10 text-accent-warning border-accent-warning/30';
    return 'bg-accent-danger/10 text-accent-danger border-accent-danger/30';
  };

  return (
    <div className="flex flex-col w-full pb-10">
      <div className="p-6">
        <button 
          onClick={() => navigate(-1)} 
          className="flex items-center gap-2 px-5 py-2.5 bg-button-bg text-text-secondary border border-border-color rounded-xl font-bold transition-all hover:bg-opacity-80 hover:text-accent-primary hover:border-accent-primary hover:-translate-x-1 shadow-sm"
        >
          <ArrowLeft className="w-4 h-4" /> Back
        </button>
      </div>

      {loading ? (
        <div className="text-center p-20 text-text-muted min-h-[400px]">
          <Loader2 className="w-12 h-12 animate-spin mx-auto mb-6 text-accent-primary" />
          <p className="font-bold text-lg">Loading metrics...</p>
        </div>
      ) : error ? (
        <div className="p-12 mx-6 bg-accent-danger/5 rounded-2xl border border-accent-danger/20 text-center text-accent-danger mb-10 shadow-lg">
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
            <div className="text-2xl text-accent-secondary font-black bg-button-bg px-6 py-2 rounded-xl inline-block border border-border-color shadow-sm">
              {data.ticker}
            </div>
            
            {data.total_score_percentage !== null && (
              <div className="flex flex-wrap gap-6 mt-8 justify-center">
                <div className="bg-bg-primary p-6 rounded-2xl border border-border-color shadow-xl min-w-[180px] text-left">
                  <div className="text-xs font-black text-text-muted uppercase tracking-widest mb-2 opacity-70">Total Score</div>
                  <div className="text-4xl font-black text-text-secondary">{data.total_score_percentage.toFixed(1)}%</div>
                </div>
                {data.total_score_percentile_rank !== null && (
                  <div className="bg-bg-primary p-6 rounded-2xl border border-border-color shadow-xl min-w-[180px] text-left">
                    <div className="text-xs font-black text-text-muted uppercase tracking-widest mb-2 opacity-70">Percentile Rank</div>
                    <div className="text-4xl font-black text-text-secondary">{data.total_score_percentile_rank}th</div>
                  </div>
                )}
              </div>
            )}
          </div>

          <div className="mx-6 bg-bg-primary rounded-3xl overflow-hidden border border-border-color shadow-2xl">
            <div className="overflow-x-auto">
              <table className="w-full border-collapse">
                <thead className="bg-table-header-bg text-text-secondary">
                  <tr>
                    <th className="p-6 text-left font-black uppercase text-xs tracking-widest border-b border-border-color">Metric</th>
                    <th className="p-6 text-center font-black uppercase text-xs tracking-widest border-b border-border-color whitespace-nowrap">Raw Score</th>
                    <th className="p-6 text-center font-black uppercase text-xs tracking-widest border-b border-border-color whitespace-nowrap">Adjusted Score</th>
                    <th className="p-6 text-center font-black uppercase text-xs tracking-widest border-b border-border-color">Weight</th>
                    <th className="p-6 text-right font-black uppercase text-xs tracking-widest border-b border-border-color">Contribution</th>
                    <th className="p-6 text-right font-black uppercase text-xs tracking-widest border-b border-border-color whitespace-nowrap">% of Total</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-border-color/50">
                  {data.metrics.map((metric) => (
                    <tr key={metric.key} className="hover:bg-table-hover-bg transition-all group">
                      <td className="p-6 text-text-secondary">
                        <div className="flex items-center gap-3">
                          <span className="font-bold text-lg">{metric.name}</span>
                          {metric.is_reverse && (
                            <span className="bg-accent-warning/10 text-accent-warning px-3 py-1 rounded-full text-[10px] font-black uppercase tracking-widest border border-accent-warning/20 whitespace-nowrap">
                              Reverse Metric
                            </span>
                          )}
                        </div>
                      </td>
                      <td className="p-6 text-center">
                        <span className={`inline-block px-4 py-1.5 rounded-xl font-black text-base border shadow-sm ${getScoreColorClass(metric.raw_score, false)}`}>
                          {metric.raw_score.toFixed(1)}/10
                        </span>
                      </td>
                      <td className="p-6 text-center">
                        <span className={`inline-block px-4 py-1.5 rounded-xl font-black text-base border shadow-sm ${getScoreColorClass(metric.raw_score, metric.is_reverse)}`}>
                          {metric.adjusted_score.toFixed(1)}/10
                        </span>
                      </td>
                      <td className="p-6 text-center text-text-muted font-bold">
                        {metric.weight.toFixed(2)}
                      </td>
                      <td className="p-6 text-right font-black text-text-secondary text-lg">
                        {metric.contribution.toFixed(2)}
                      </td>
                      <td className="p-6 text-right text-text-muted font-bold">
                        {metric.percentage.toFixed(2)}%
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </>
      ) : null}
    </div>
  );
};

export default MetricsPage;
