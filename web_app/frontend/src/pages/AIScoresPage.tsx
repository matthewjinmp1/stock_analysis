import React, { useState, useEffect } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { ArrowLeft, Search, Loader2, AlertCircle } from 'lucide-react';
import * as api from '../api';

const METRIC_LABELS: Record<string, string> = {
  'moat_score': 'Economic Moat',
  'barriers_score': 'Barriers to Entry',
  'disruption_risk': 'Disruption Risk',
  'switching_cost': 'Switching Cost',
  'brand_strength': 'Brand Strength',
  'competition_intensity': 'Competition Intensity',
  'network_effect': 'Network Effect',
  'product_differentiation': 'Product Differentiation',
  'innovativeness_score': 'Innovativeness',
  'growth_opportunity': 'Growth Opportunity',
  'riskiness_score': 'Business Risk',
  'pricing_power': 'Pricing Power',
  'ambition_score': 'Ambition',
  'bargaining_power_of_customers': 'Customer Power',
  'bargaining_power_of_suppliers': 'Supplier Power',
  'product_quality_score': 'Product Quality',
  'culture_employee_satisfaction_score': 'Employee Culture',
  'trailblazer_score': 'Market Leadership',
  'management_quality_score': 'Management Quality',
  'size_well_known_score': 'Company Size',
  'ethical_healthy_environmental_score': 'Ethical/ESG',
  'long_term_orientation_score': 'Long Term Focus'
};

const AIScoresPage: React.FC = () => {
  const navigate = useNavigate();
  const [scores, setScores] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [searchTerm, setSearchTerm] = useState('');
  const [visibleMetrics, setVisibleMetrics] = useState<string[]>([]);
  const [sortConfig, setSortConfig] = useState<{ column: string, direction: 'asc' | 'desc' }>({
    column: 'total_score_percentile_rank',
    direction: 'desc'
  });

  useEffect(() => {
    const fetchScores = async () => {
      try {
        const data = await api.getAIScores();
        if (data.success) {
          setScores(data.scores || []);
        } else {
          setError(data.message || 'Error loading scores');
        }
      } catch (err) {
        setError('Error loading scores. Please try again.');
      } finally {
        setLoading(false);
      }
    };
    fetchScores();
  }, []);

  const toggleMetric = (key: string) => {
    setVisibleMetrics(prev => 
      prev.includes(key) ? prev.filter(m => m !== key) : [...prev, key]
    );
  };

  const handleSort = (column: string) => {
    setSortConfig(prev => ({
      column,
      direction: prev.column === column && prev.direction === 'desc' ? 'asc' : 'desc'
    }));
  };

  const sortedAndFilteredScores = scores
    .filter(score => 
      score.ticker.toUpperCase().includes(searchTerm.toUpperCase()) || 
      (score.company_name && score.company_name.toUpperCase().includes(searchTerm.toUpperCase()))
    )
    .sort((a, b) => {
      let valA = a[sortConfig.column];
      let valB = b[sortConfig.column];

      if (valA === null || valA === undefined) valA = '';
      if (valB === null || valB === undefined) valB = '';

      const isNumA = typeof valA === 'number' || (!isNaN(parseFloat(valA)) && isFinite(valA));
      const isNumB = typeof valB === 'number' || (!isNaN(parseFloat(valB)) && isFinite(valB));

      if (isNumA && isNumB) {
        return sortConfig.direction === 'asc' ? valA - valB : valB - valA;
      }
      
      const strA = String(valA).toLowerCase();
      const strB = String(valB).toLowerCase();
      return sortConfig.direction === 'asc' 
        ? strA.localeCompare(strB) 
        : strB.localeCompare(strA);
    });

  const getSortIcon = (column: string) => {
    if (sortConfig.column !== column) return '⇅';
    return sortConfig.direction === 'asc' ? '↑' : '↓';
  };

  return (
    <div className="flex flex-col">
      {/* Header */}
      <div className="p-10 text-center border-b border-border-color bg-header-bg rounded-t-[15px]">
        <h1 className="text-[2.5em] font-bold mb-2.5 text-text-secondary [text-shadow:0_0_8px_var(--glow-primary)]">
          📊 AI Analysis Scores
        </h1>
        <div className="mt-4 flex justify-center">
          <button 
            onClick={() => navigate(-1)} 
            className="flex items-center gap-2 px-5 py-2.5 bg-button-bg text-text-secondary border border-border-color rounded-lg transition-all hover:bg-opacity-80 hover:text-accent-primary hover:border-accent-primary hover:-translate-x-1"
          >
            <ArrowLeft className="w-4 h-4" /> Back to Main Page
          </button>
        </div>
      </div>

      <div className="p-10 bg-bg-secondary">
        {/* Controls Section */}
        <div className="bg-bg-secondary rounded-[15px] p-5 mb-5 border border-border-color shadow-[0_0_15px_var(--shadow-color)]">
          <div className="mb-5 text-center">
            <div className="relative max-w-md mx-auto">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-text-muted" />
              <input 
                type="text" 
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                placeholder="Search by ticker or company name..." 
                className="w-full pl-10 pr-5 py-3 bg-input-bg border border-border-color rounded-lg color-text-secondary outline-none focus:border-accent-secondary focus:shadow-[0_0_15px_var(--glow-secondary)]"
              />
            </div>
          </div>
          
          <p className="text-[0.9em] text-text-secondary mb-1.25 font-semibold">Select Metrics to Show:</p>
          <div className="flex flex-wrap gap-2.5 mt-[15px] pt-[15px] border-t border-border-color">
            {Object.keys(METRIC_LABELS).map(key => (
              <button
                key={key}
                onClick={() => toggleMetric(key)}
                className={`flex items-center gap-1.25 px-3 py-1.25 rounded-full text-[0.85em] cursor-pointer transition-all border border-border-color ${
                  visibleMetrics.includes(key) 
                    ? 'bg-accent-primary border-accent-primary text-bg-primary' 
                    : 'bg-bg-primary text-text-secondary hover:bg-button-bg hover:border-accent-primary'
                }`}
              >
                {METRIC_LABELS[key]}
              </button>
            ))}
          </div>
        </div>

        {/* Scores Section */}
        <div className="bg-bg-secondary rounded-[15px] p-5 border border-border-color shadow-[0_0_15px_var(--shadow-color)] overflow-x-auto min-h-[400px]">
          {loading ? (
            <div className="text-center p-10 text-text-muted">
              <Loader2 className="w-10 h-10 animate-spin mx-auto mb-5 text-accent-primary" />
              <p>Loading scores from AI database...</p>
            </div>
          ) : error ? (
            <div className="p-10 text-center text-accent-danger">
              <AlertCircle className="w-10 h-10 mx-auto mb-4" />
              <p>{error}</p>
            </div>
          ) : (
            <table className="w-full border-collapse text-text-primary">
              <thead>
                <tr className="bg-table-header-bg">
                  <th className="p-[12px_15px] text-left border-b border-border-color uppercase text-[0.85em] tracking-wider font-semibold cursor-pointer sticky top-0 z-10 hover:bg-table-hover-bg text-text-secondary" onClick={() => handleSort('ticker')}>
                    Ticker {getSortIcon('ticker')}
                  </th>
                  <th className="p-[12px_15px] text-left border-b border-border-color uppercase text-[0.85em] tracking-wider font-semibold cursor-pointer sticky top-0 z-10 hover:bg-table-hover-bg text-text-secondary" onClick={() => handleSort('company_name')}>
                    Company {getSortIcon('company_name')}
                  </th>
                  <th className="p-[12px_15px] text-center border-b border-border-color uppercase text-[0.85em] tracking-wider font-semibold cursor-pointer sticky top-0 z-10 hover:bg-table-hover-bg text-text-secondary" onClick={() => handleSort('total_score_percentile_rank')}>
                    Percentile {getSortIcon('total_score_percentile_rank')}
                  </th>
                  {visibleMetrics.map(m => (
                    <th key={m} className="p-[12px_15px] text-center border-b border-border-color uppercase text-[0.85em] tracking-wider font-semibold cursor-pointer sticky top-0 z-10 hover:bg-table-hover-bg text-text-secondary" onClick={() => handleSort(m)}>
                      {METRIC_LABELS[m]} {getSortIcon(m)}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {sortedAndFilteredScores.map((score, idx) => (
                  <tr key={score.ticker + idx} className="hover:bg-table-hover-bg transition-all">
                    <td className="p-[12px_15px] border-b border-border-color">
                      <Link to={`/?q=${score.ticker}`} className="font-bold text-accent-secondary hover:underline hover:text-accent-primary transition-all">
                        {score.ticker}
                      </Link>
                    </td>
                    <td className="p-[12px_15px] border-b border-border-color text-text-secondary text-[0.9em] max-w-[250px] overflow-hidden text-ellipsis whitespace-nowrap" title={score.company_name}>
                      {score.company_name || 'N/A'}
                    </td>
                    <td className="p-[12px_15px] border-b border-border-color text-center font-semibold text-text-secondary">
                      {score.total_score_percentile_rank ?? 'N/A'}
                    </td>
                    {visibleMetrics.map(m => (
                      <td key={m} className="p-[12px_15px] border-b border-border-color text-center text-text-primary">
                        {score[m] ?? 'N/A'}
                      </td>
                    ))}
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </div>
      </div>
    </div>
  );
};

export default AIScoresPage;
