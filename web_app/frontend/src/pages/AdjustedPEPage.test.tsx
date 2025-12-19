import { render, screen, waitFor, fireEvent } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { vi, describe, it, expect, beforeEach } from 'vitest';
import AdjustedPEPage from './AdjustedPEPage';
import * as api from '../api';

// Mock the API module
vi.mock('../api', () => ({
  getAdjustedPE: vi.fn(),
}));

// Mock the react-router-dom hooks
const mockNavigate = vi.fn();
vi.mock('react-router-dom', async () => {
  const actual = await vi.importActual('react-router-dom');
  return {
    ...actual,
    useNavigate: () => mockNavigate,
    useParams: () => ({ ticker: 'AAPL' }),
  };
});

describe('AdjustedPEPage', () => {
  const mockAdjustedPEData = {
    success: true,
    ticker: 'AAPL',
    adjusted_pe_ratio: 25.5,
    breakdown: {
      ttm_operating_income: 120000000000,
      ttm_da: 11000000000,
      ttm_capex: 10000000000,
      adjustment: 1000000000,
      adjusted_operating_income: 121000000000,
      median_tax_rate: 0.15,
      adjusted_oi_after_tax: 102850000000,
      quickfs_ev: 3000000000000,
      quickfs_market_cap: 2950000000000,
      ev_difference: 50000000000,
      share_count: 15500000000,
      current_price: 190.5,
      updated_market_cap: 2952750000000,
      updated_ev: 3002750000000,
    },
  };

  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('renders loading state initially', () => {
    vi.mocked(api.getAdjustedPE).mockReturnValue(new Promise(() => {}));
    render(
      <MemoryRouter>
        <AdjustedPEPage />
      </MemoryRouter>
    );
    expect(screen.getByText(/Loading adjusted PE data/i)).toBeInTheDocument();
  });

  it('renders adjusted PE data correctly', async () => {
    vi.mocked(api.getAdjustedPE).mockResolvedValue(mockAdjustedPEData);
    render(
      <MemoryRouter>
        <AdjustedPEPage />
      </MemoryRouter>
    );

    await waitFor(() => {
      expect(screen.getByText('25.50')).toBeInTheDocument();
      expect(screen.getByText('$120.00B')).toBeInTheDocument(); // TTM Operating Income
      expect(screen.getByText('15.00%')).toBeInTheDocument(); // Median Tax Rate
    });
  });

  it('handles error state', async () => {
    vi.mocked(api.getAdjustedPE).mockResolvedValue({
      success: false,
      message: 'Adjusted PE data not available',
    });

    render(
      <MemoryRouter>
        <AdjustedPEPage />
      </MemoryRouter>
    );

    await waitFor(() => {
      expect(screen.getByText('Adjusted PE data not available')).toBeInTheDocument();
    });
  });

  it('navigates back when back button is clicked', async () => {
    vi.mocked(api.getAdjustedPE).mockResolvedValue(mockAdjustedPEData);
    render(
      <MemoryRouter>
        <AdjustedPEPage />
      </MemoryRouter>
    );

    await waitFor(() => {
      expect(screen.getByText('Back')).toBeInTheDocument();
    });

    fireEvent.click(screen.getByText('Back'));
    expect(mockNavigate).toHaveBeenCalledWith(-1);
  });
});
