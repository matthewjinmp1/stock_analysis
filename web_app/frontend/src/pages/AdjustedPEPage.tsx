import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { ArrowLeft, Loader2, AlertCircle } from 'lucide-react';
import * as api from '../api';

const fmt = (value: any, decimals = 2) => {
  if (value === null || value === undefined) return 'N/A';
  const num = Number(value);
  if (Number.isNaN(num)) return 'N/A';
  return num.toFixed(decimals);
};

const fmtPercent = (value: any, decimals = 2) => {
  if (value === null || value === undefined) return 'N/A';
  return (Number(value) * 100).toFixed(decimals) + '%';
};

const fmtSuffix = (value: any, decimals = 2) => {
  if (value === null || value === undefined) return 'N/A';
  const num = Number(value);
  if (Number.isNaN(num)) return 'N/A';
  const abs = Math.abs(num);
  let suffix = '';
  let scaled = num;
  if (abs >= 1_000_000_000) {
    scaled = num / 1_000_000_000;
    suffix = 'B';
  } else if (abs >= 1_000_000) {
    scaled = num / 1_000_000;
    suffix = 'M';
  } else if (abs >= 1_000) {
    scaled = num / 1_000;
    suffix = 'K';
  }
  return scaled.toFixed(decimals) + suffix;
};

const fmtMoney = (value: any, decimals = 2) => {
  if (value === null || value === undefined) return 'N/A';
  const res = fmtSuffix(value, decimals);
  return res === 'N/A' ? 'N/A' : '$' + res;
};

const AdjustedPEPage: React.FC = () => {
  const { ticker } = useParams<{ ticker: string }>();
  const navigate = useNavigate();
  const [data, setData] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!ticker) return;
    const fetchAdjustedPE = async () => {
      try {
        const response = await api.getAdjustedPE(ticker);
        if (response.success) {
          setData(response);
        } else {
          setError(response.message || 'Adjusted PE data not available');
        }
      } catch (err: any) {
        setError(err.response?.data?.message || 'Error loading adjusted PE data');
      } finally {
        setLoading(false);
      }
    };
    fetchAdjustedPE();
  }, [ticker]);

  const b = data?.breakdown || {};
  const fields = [
    { label: 'TTM Operating Income', value: fmtMoney(b.ttm_operating_income) },
    { label: 'TTM Depreciation & Amortization (DA)', value: fmtMoney(b.ttm_da) },
    { label: 'TTM Capex', value: fmtMoney(b.ttm_capex) },
    { label: 'Adjustment (if DA exceeds Capex)', value: fmtMoney(b.adjustment) },
    { label: 'Adjusted Operating Income', value: fmtMoney(b.adjusted_operating_income) },
    { label: 'Median Tax Rate (5yr)', value: fmtPercent(b.median_tax_rate, 2) },
    { label: 'Adjusted Earnings', value: fmtMoney(b.adjusted_oi_after_tax) },
    { label: 'QuickFS EV (latest)', value: fmtMoney(b.quickfs_ev) },
    { label: 'QuickFS Market Cap (latest)', value: fmtMoney(b.quickfs_market_cap) },
    { label: 'EV Difference (EV - Market Cap)', value: fmtMoney(b.ev_difference) },
    { label: 'Share Count (latest QuickFS)', value: fmtSuffix(b.share_count, 2) },
    { label: 'Current Price (yfinance)', value: b.current_price !== undefined && b.current_price !== null ? '$' + fmt(b.current_price) : 'N/A' },
    { label: 'Updated Market Cap', value: fmtMoney(b.updated_market_cap) },
    { label: 'Updated EV (with current price)', value: fmtMoney(b.updated_ev) },
  ];

  return (
    <div className="flex flex-col w-full min-h-screen">
      <div className="p-10 text-center border-b border-border-color bg-header-bg">
        <h1 className="text-4xl md:text-5xl font-black mb-4 text-text-secondary [text-shadow:0_0_8px_var(--glow-primary)]">
          Adjusted PE Breakdown
        </h1>
        <p className="opacity-85 text-xl text-accent-secondary mb-5 bg-button-bg px-6 py-2 inline-block border border-border-color font-black">
          {ticker}
        </p>
        <button 
          onClick={() => navigate(-1)} 
          className="mt-5 flex items-center gap-2 px-8 py-3 bg-button-bg text-text-secondary border border-border-color font-black text-lg transition-all hover:bg-opacity-80 hover:text-accent-primary hover:border-accent-primary hover:-translate-x-1 mx-auto shadow-lg active:scale-95"
        >
          <ArrowLeft className="w-5 h-5" /> Back
        </button>
      </div>

      <div className="p-10 bg-bg-secondary flex-1 flex flex-col items-center">
        {loading ? (
          <div className="text-center p-20 text-text-muted">
            <Loader2 className="w-12 h-12 animate-spin mx-auto mb-6 text-accent-primary" />
            <p className="font-bold text-lg">Loading adjusted PE data...</p>
          </div>
        ) : error ? (
          <div className="bg-bg-tertiary p-12 border border-accent-danger text-center text-accent-danger shadow-2xl max-w-2xl">
            <AlertCircle className="w-12 h-12 mx-auto mb-4" />
            <p className="font-black text-xl">{error}</p>
          </div>
        ) : (
          <div className="flex flex-col gap-8 w-full max-w-[1000px]">
            <div className="bg-card-bg p-10 border border-border-color shadow-2xl">
              <h2 className="text-2xl font-black text-text-secondary mb-6 uppercase tracking-widest opacity-70">Adjusted PE Ratio</h2>
              <div className="text-6xl font-black text-accent-secondary mb-4">
                {data.adjusted_pe_ratio !== null && data.adjusted_pe_ratio !== undefined ? fmt(data.adjusted_pe_ratio) : 'N/A'}
              </div>
              <div className="text-sm text-text-muted font-medium italic">Click any ticker to recalculate from QuickFS/yfinance if data is missing.</div>
            </div>

            <div className="bg-card-bg p-10 border border-border-color shadow-2xl overflow-hidden">
              <h2 className="text-2xl font-black text-text-secondary mb-6 uppercase tracking-widest opacity-70">TTM Components</h2>
              <div className="overflow-x-auto">
                <table className="w-full border-collapse">
                  <thead>
                    <tr className="bg-table-header-bg">
                      <th className="p-5 text-left border-b border-border-color font-black text-text-secondary uppercase text-xs tracking-[0.2em]">Item</th>
                      <th className="p-5 text-left border-b border-border-color font-black text-text-secondary uppercase text-xs tracking-[0.2em]">Value</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-border-color/30">
                    {fields.map((f, i) => (
                      <tr key={i} className="hover:bg-table-hover-bg transition-all group">
                        <td className="p-5 font-bold text-text-secondary text-lg">{f.label}</td>
                        <td className="p-5 font-black text-accent-secondary text-lg">{f.value}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default AdjustedPEPage;
