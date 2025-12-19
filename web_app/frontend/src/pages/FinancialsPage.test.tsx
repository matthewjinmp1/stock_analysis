import { render, screen, waitFor, fireEvent } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { vi, describe, it, expect, beforeEach } from 'vitest';
import FinancialsPage from './FinancialsPage';
import * as api from '../api';

// Mock the API module
vi.mock('../api', () => ({
  getFinancials: vi.fn(),
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

describe('FinancialsPage', () => {
  const mockFinancialsData = {
    success: true,
    ticker: 'AAPL',
    company_name: 'Apple Inc',
    total_percentile: 88.5,
    total_rank: 45,
    metrics: [
      {
        key: 'revenue_growth',
        name: 'Revenue Growth',
        description: 'Year over year revenue growth',
        value: 12.5,
        rank: 100,
        percentile: 75.0,
        sort_descending: true,
      },
      {
        key: 'gross_margin',
        name: 'Gross Margin',
        description: 'Gross profit as percentage of revenue',
        value: 42.1,
        rank: 50,
        percentile: 90.0,
        sort_descending: true,
      },
    ],
  };

  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('renders loading state initially', () => {
    vi.mocked(api.getFinancials).mockReturnValue(new Promise(() => {}));
    render(
      <MemoryRouter>
        <FinancialsPage />
      </MemoryRouter>
    );
    expect(screen.getByText(/Loading financial metrics/i)).toBeInTheDocument();
  });

  it('renders financials data correctly', async () => {
    vi.mocked(api.getFinancials).mockResolvedValue(mockFinancialsData);
    render(
      <MemoryRouter>
        <FinancialsPage />
      </MemoryRouter>
    );

    await waitFor(() => {
      expect(screen.getByText('Apple Inc')).toBeInTheDocument();
      expect(screen.getByText(/88.5th percentile/i)).toBeInTheDocument();
      expect(screen.getByText('45')).toBeInTheDocument();
    });

    expect(screen.getByText('Revenue Growth')).toBeInTheDocument();
    expect(screen.getByText('12.50')).toBeInTheDocument();
    expect(screen.getByText('75.0th')).toBeInTheDocument();
  });

  it('handles error state', async () => {
    vi.mocked(api.getFinancials).mockResolvedValue({
      success: false,
      message: 'Failed to fetch financial metrics',
    });

    render(
      <MemoryRouter>
        <FinancialsPage />
      </MemoryRouter>
    );

    await waitFor(() => {
      expect(screen.getByText('Failed to fetch financial metrics')).toBeInTheDocument();
    });
  });

  it('navigates back when back button is clicked', async () => {
    vi.mocked(api.getFinancials).mockResolvedValue(mockFinancialsData);
    render(
      <MemoryRouter>
        <FinancialsPage />
      </MemoryRouter>
    );

    await waitFor(() => {
      expect(screen.getByText('Back')).toBeInTheDocument();
    });

    fireEvent.click(screen.getByText('Back'));
    expect(mockNavigate).toHaveBeenCalledWith(-1);
  });
});
