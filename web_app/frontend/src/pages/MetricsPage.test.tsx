import { render, screen, waitFor, fireEvent } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { vi, describe, it, expect, beforeEach } from 'vitest';
import MetricsPage from './MetricsPage';
import * as api from '../api';

// Mock the API module
vi.mock('../api', () => ({
  getMetrics: vi.fn(),
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

describe('MetricsPage', () => {
  const mockMetricsData = {
    success: true,
    ticker: 'AAPL',
    company_name: 'Apple Inc',
    total_score_percentage: 85.5,
    total_score_percentile_rank: 92,
    max_score: 100,
    metrics: [
      {
        key: 'gross_margin',
        name: 'Gross Margin',
        raw_score: 8.0,
        adjusted_score: 8.0,
        weight: 1.5,
        contribution: 12.0,
        is_reverse: false,
        percentage: 14.0,
      },
      {
        key: 'net_debt_to_ebitda',
        name: 'Net Debt to EBITDA',
        raw_score: 2.0,
        adjusted_score: 8.0,
        weight: 1.0,
        contribution: 8.0,
        is_reverse: true,
        percentage: 9.3,
      },
    ],
  };

  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('renders loading state initially', () => {
    vi.mocked(api.getMetrics).mockReturnValue(new Promise(() => {}));
    render(
      <MemoryRouter>
        <MetricsPage />
      </MemoryRouter>
    );
    expect(screen.getByText(/Loading metrics/i)).toBeInTheDocument();
  });

  it('renders metrics data correctly', async () => {
    vi.mocked(api.getMetrics).mockResolvedValue(mockMetricsData);
    render(
      <MemoryRouter>
        <MetricsPage />
      </MemoryRouter>
    );

    await waitFor(() => {
      expect(screen.getByText('Apple Inc')).toBeInTheDocument();
      expect(screen.getByText('85.5%')).toBeInTheDocument();
      expect(screen.getByText('92th')).toBeInTheDocument();
    });

    expect(screen.getByText('Gross Margin')).toBeInTheDocument();
    expect(screen.getByText('Net Debt to EBITDA')).toBeInTheDocument();
    expect(screen.getByText('Reverse Metric')).toBeInTheDocument();
  });

  it('handles error state', async () => {
    vi.mocked(api.getMetrics).mockResolvedValue({
      success: false,
      message: 'Failed to fetch metrics',
    });

    render(
      <MemoryRouter>
        <MetricsPage />
      </MemoryRouter>
    );

    await waitFor(() => {
      expect(screen.getByText('Failed to fetch metrics')).toBeInTheDocument();
    });
  });

  it('navigates back when back button is clicked', async () => {
    vi.mocked(api.getMetrics).mockResolvedValue(mockMetricsData);
    render(
      <MemoryRouter>
        <MetricsPage />
      </MemoryRouter>
    );

    await waitFor(() => {
      expect(screen.getByText('Back')).toBeInTheDocument();
    });

    fireEvent.click(screen.getByText('Back'));
    expect(mockNavigate).toHaveBeenCalledWith(-1);
  });
});
