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
    <div className="flex flex-col w-full min-h-screen pb-20">
      {/* Header */}
      <div className="p-8 md:p-12 text-center border-b border-border-color bg-header-bg">
        <h1 className="text-4xl md:text-5xl font-black mb-6 text-text-secondary [text-shadow:0_0_8px_var(--glow-primary)]">
          📊 AI Analysis Scores
        </h1>
        <div className="flex justify-center mt-6">
          <button 
            onClick={() => navigate(-1)} 
            className="flex items-center gap-3 px-8 py-3 bg-button-bg text-text-secondary border border-border-color font-black text-lg transition-all hover:bg-accent-primary hover:text-bg-primary hover:border-accent-primary shadow-lg active:scale-95"
          >
            <ArrowLeft className="w-5 h-5" /> Back to Search
          </button>
        </div>
      </div>

      <div className="p-4 md:p-12 bg-bg-secondary flex-1 flex flex-col items-center">
        {/* Search Bar Section */}
        <div className="w-full max-w-[1000px] bg-bg-secondary p-8 md:p-10 mb-6 border border-border-color shadow-2xl">
          <div className="relative w-full max-w-2xl mx-auto group">
            <div className="absolute left-6 top-1/2 -translate-y-1/2 flex items-center justify-center z-20 pointer-events-none">
              <Search className="w-6 h-6 text-text-muted group-focus-within:text-accent-secondary transition-colors" />
            </div>
            <input 
              type="text" 
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              placeholder="Search by ticker or company name..." 
              className="w-full pr-8 py-5 bg-input-bg border border-border-color text-text-secondary text-xl outline-none transition-all focus:border-accent-secondary focus:ring-4 focus:ring-accent-secondary/10 shadow-sm relative z-10 font-medium"
              style={{ paddingLeft: '4.5rem' }}
            />
          </div>
        </div>

        {/* Metric Selection Section */}
        <div className="w-full max-w-[1000px] bg-bg-secondary p-8 md:p-10 mb-10 border border-border-color shadow-2xl">
          <p className="text-sm text-text-muted mb-6 font-black uppercase tracking-widest opacity-70 text-center md:text-left">Select Metrics to Show:</p>
          <div className="flex flex-wrap justify-center md:justify-start gap-3">
            {Object.keys(METRIC_LABELS).map(key => (
              <button
                key={key}
                onClick={() => toggleMetric(key)}
                className={`flex items-center gap-2 px-5 py-2.5 font-black cursor-pointer transition-all border shadow-sm ${
                  visibleMetrics.includes(key) 
                    ? 'bg-accent-primary border-accent-primary text-bg-primary scale-105' 
                    : 'bg-bg-primary text-text-secondary border-border-color hover:border-accent-primary hover:text-accent-primary'
                }`}
              >
                {METRIC_LABELS[key]}
              </button>
            ))}
          </div>
        </div>

        {/* Scores Section */}
        <div className="w-full max-w-[1400px] bg-bg-secondary p-4 border border-border-color shadow-2xl overflow-hidden min-h-[500px]">
          {loading ? (
            <div className="text-center p-20 text-text-muted">
              <Loader2 className="w-12 h-12 animate-spin mx-auto mb-6 text-accent-primary" />
              <p className="font-bold text-lg">Loading scores from AI database...</p>
            </div>
          ) : error ? (
            <div className="p-12 text-center text-accent-danger">
              <AlertCircle className="w-12 h-12 mx-auto mb-4" />
              <p className="font-bold text-lg">{error}</p>
            </div>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full border-collapse text-text-primary">
                <thead>
                  <tr className="bg-table-header-bg">
                    <th className="p-5 text-left border-b border-border-color uppercase text-[10px] tracking-[0.2em] font-black cursor-pointer sticky top-0 z-10 hover:bg-table-hover-bg text-text-secondary transition-colors" onClick={() => handleSort('ticker')}>
                      Ticker {getSortIcon('ticker')}
                    </th>
                    <th className="p-5 text-left border-b border-border-color uppercase text-[10px] tracking-[0.2em] font-black cursor-pointer sticky top-0 z-10 hover:bg-table-hover-bg text-text-secondary transition-colors" onClick={() => handleSort('company_name')}>
                      Company {getSortIcon('company_name')}
                    </th>
                    <th className="p-5 text-center border-b border-border-color uppercase text-[10px] tracking-[0.2em] font-black cursor-pointer sticky top-0 z-10 hover:bg-table-hover-bg text-text-secondary transition-colors" onClick={() => handleSort('total_score_percentile_rank')}>
                      Percentile {getSortIcon('total_score_percentile_rank')}
                    </th>
                    {visibleMetrics.map(m => (
                      <th key={m} className="p-5 text-center border-b border-border-color uppercase text-[10px] tracking-[0.2em] font-black cursor-pointer sticky top-0 z-10 hover:bg-table-hover-bg text-text-secondary transition-colors whitespace-nowrap" onClick={() => handleSort(m)}>
                        {METRIC_LABELS[m]} {getSortIcon(m)}
                      </th>
                    ))}
                  </tr>
                </thead>
                <tbody className="divide-y divide-border-color/30">
                  {sortedAndFilteredScores.map((score, idx) => (
                    <tr key={score.ticker + idx} className="hover:bg-table-hover-bg/50 transition-all group">
                      <td className="p-5 border-b border-border-color">
                        <Link to={`/?q=${score.ticker}`} className="font-black text-accent-secondary hover:text-accent-primary transition-all text-lg">
                          {score.ticker}
                        </Link>
                      </td>
                      <td className="p-5 border-b border-border-color text-text-secondary font-bold text-sm max-w-[250px] overflow-hidden text-ellipsis whitespace-nowrap" title={score.company_name}>
                        {score.company_name || 'N/A'}
                      </td>
                      <td className="p-5 border-b border-border-color text-center">
                        <span className="font-black text-text-secondary text-xl">
                          {score.total_score_percentile_rank ?? 'N/A'}
                        </span>
                      </td>
                      {visibleMetrics.map(m => (
                        <td key={m} className="p-5 border-b border-border-color text-center">
                          <span className="text-text-primary font-bold">
                            {score[m] ?? 'N/A'}
                          </span>
                        </td>
                      ))}
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

export default AIScoresPage;
