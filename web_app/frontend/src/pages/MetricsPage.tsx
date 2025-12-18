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
    if (is_reverse) {
      if (raw_score >= 7) return 'bg-bg-secondary text-accent-danger border-accent-danger';
      if (raw_score >= 4) return 'bg-bg-secondary text-accent-warning border-accent-warning';
      return 'bg-bg-secondary text-accent-success border-accent-success';
    } else {
      if (raw_score >= 7) return 'bg-bg-secondary text-accent-success border-accent-success';
      if (raw_score >= 4) return 'bg-bg-secondary text-accent-warning border-accent-warning';
      return 'bg-bg-secondary text-accent-danger border-accent-danger';
    }
  };

  return (
    <div className="flex flex-col">
      <div className="p-6">
        <button 
          onClick={() => navigate(-1)} 
          className="flex items-center gap-2 px-4 py-2 bg-button-bg text-text-secondary border border-border-color rounded-lg transition-all hover:bg-opacity-80 hover:text-accent-primary hover:border-accent-primary hover:-translate-x-1"
        >
          <ArrowLeft className="w-4 h-4" /> Back
        </button>
      </div>

      {loading ? (
        <div className="text-center p-20 text-text-muted min-h-[400px]">
          <Loader2 className="w-10 h-10 animate-spin mx-auto mb-5 text-accent-primary" />
          <p>Loading metrics...</p>
        </div>
      ) : error ? (
        <div className="p-10 mx-6 bg-bg-tertiary rounded-[15px] border border-accent-danger text-center text-accent-danger mb-10">
          <AlertCircle className="w-10 h-10 mx-auto mb-4" />
          <h2 className="text-xl font-bold mb-2">Error</h2>
          <p>{error}</p>
        </div>
      ) : data ? (
        <>
          <div className="p-10 text-center">
            <h1 className="text-[2.5em] font-bold mb-2.5 text-text-secondary [text-shadow:0_0_8px_var(--glow-primary)]">
              {data.company_name || data.ticker}
            </h1>
            <div className="text-[1.2em] text-accent-secondary mb-5 bg-button-bg p-[5px_15px] rounded-lg inline-block border border-border-color">
              {data.ticker}
            </div>
            
            {data.total_score_percentage !== null && (
              <div className="flex gap-5 mt-5 justify-center">
                <div className="bg-bg-primary p-[15px] rounded-lg border border-border-color shadow-[0_0_8px_var(--shadow-color)] min-w-[150px]">
                  <div className="text-[0.9em] text-text-muted mb-1.25">Total Score</div>
                  <div className="text-[1.5em] font-bold text-text-secondary">{data.total_score_percentage.toFixed(1)}%</div>
                </div>
                {data.total_score_percentile_rank !== null && (
                  <div className="bg-bg-primary p-[15px] rounded-lg border border-border-color shadow-[0_0_8px_var(--shadow-color)] min-w-[150px]">
                    <div className="text-[0.9em] text-text-muted mb-1.25">Percentile Rank</div>
                    <div className="text-[1.5em] font-bold text-text-secondary">{data.total_score_percentile_rank}th</div>
                  </div>
                )}
              </div>
            )}
          </div>

          <div className="m-[0_20px_20px] bg-bg-primary rounded-[15px] overflow-hidden border border-border-color shadow-[0_0_15px_var(--shadow-color)] overflow-x-auto">
            <table className="w-full border-collapse">
              <thead className="bg-table-header-bg text-text-secondary">
                <tr>
                  <th className="p-[15px] text-left font-semibold border-b border-border-color">Metric</th>
                  <th className="p-[15px] text-center font-semibold border-b border-border-color">Raw Score</th>
                  <th className="p-[15px] text-center font-semibold border-b border-border-color">Adjusted Score</th>
                  <th className="p-[15px] text-center font-semibold border-b border-border-color">Weight</th>
                  <th className="p-[15px] text-right font-semibold border-b border-border-color">Contribution</th>
                  <th className="p-[15px] text-right font-semibold border-b border-border-color">% of Total</th>
                </tr>
              </thead>
              <tbody>
                {data.metrics.map((metric) => (
                  <tr key={metric.key} className="hover:bg-table-hover-bg transition-all">
                    <td className="p-[12px_15px] border-b border-border-color text-text-secondary">
                      <div className="font-medium">
                        {metric.name}
                        {metric.is_reverse && (
                          <span className="ml-2 bg-button-bg text-accent-secondary p-[2px_8px] rounded-md text-[0.75em] border border-border-color">Reverse</span>
                        )}
                      </div>
                    </td>
                    <td className="p-[12px_15px] border-b border-border-color text-center">
                      <span className={`inline-block p-[4px_12px] rounded-full font-semibold text-[0.9em] border ${getScoreColorClass(metric.raw_score, metric.is_reverse)}`}>
                        {metric.raw_score.toFixed(1)}/10
                      </span>
                    </td>
                    <td className="p-[12px_15px] border-b border-border-color text-center">
                      <span className={`inline-block p-[4px_12px] rounded-full font-semibold text-[0.9em] border ${getScoreColorClass(metric.raw_score, metric.is_reverse)}`}>
                        {metric.adjusted_score.toFixed(1)}/10
                      </span>
                    </td>
                    <td className="p-[12px_15px] border-b border-border-color text-center text-text-muted">
                      {metric.weight.toFixed(2)}
                    </td>
                    <td className="p-[12px_15px] border-b border-border-color text-right font-semibold text-text-secondary">
                      {metric.contribution.toFixed(2)}
                    </td>
                    <td className="p-[12px_15px] border-b border-border-color text-right text-text-muted text-[0.9em]">
                      {metric.percentage.toFixed(2)}%
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

export default MetricsPage;
