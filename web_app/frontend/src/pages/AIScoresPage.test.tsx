import { render, screen, waitFor, fireEvent } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { vi, describe, it, expect, beforeEach } from 'vitest';
import AIScoresPage from './AIScoresPage';
import * as api from '../api';

// Mock the API module
vi.mock('../api', () => ({
  getAIScores: vi.fn(),
}));

// Mock the react-router-dom hooks
const mockNavigate = vi.fn();
vi.mock('react-router-dom', async () => {
  const actual = await vi.importActual('react-router-dom');
  return {
    ...actual,
    useNavigate: () => mockNavigate,
  };
});

describe('AIScoresPage', () => {
  const mockScoresData = {
    success: true,
    scores: [
      {
        ticker: 'AAPL',
        company_name: 'Apple Inc',
        total_score_percentile_rank: 95,
        moat_score: 9.0,
      },
      {
        ticker: 'MSFT',
        company_name: 'Microsoft Corp',
        total_score_percentile_rank: 92,
        moat_score: 8.5,
      },
    ],
  };

  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('renders correctly', async () => {
    vi.mocked(api.getAIScores).mockResolvedValue(mockScoresData);
    render(
      <MemoryRouter>
        <AIScoresPage />
      </MemoryRouter>
    );

    expect(screen.getByText(/AI Analysis Scores/i)).toBeInTheDocument();
    
    await waitFor(() => {
      expect(screen.getByText('AAPL')).toBeInTheDocument();
      expect(screen.getByText('MSFT')).toBeInTheDocument();
    });
  });

  it('handles search filtering', async () => {
    vi.mocked(api.getAIScores).mockResolvedValue(mockScoresData);
    render(
      <MemoryRouter>
        <AIScoresPage />
      </MemoryRouter>
    );

    await waitFor(() => {
      expect(screen.getByText('AAPL')).toBeInTheDocument();
    });

    const searchInput = screen.getByPlaceholderText(/Search by ticker/i);
    fireEvent.change(searchInput, { target: { value: 'MSFT' } });

    expect(screen.queryByText('AAPL')).not.toBeInTheDocument();
    expect(screen.getByText('MSFT')).toBeInTheDocument();
  });

  it('toggles metric visibility', async () => {
    vi.mocked(api.getAIScores).mockResolvedValue(mockScoresData);
    render(
      <MemoryRouter>
        <AIScoresPage />
      </MemoryRouter>
    );

    await waitFor(() => {
      expect(screen.getByText('AAPL')).toBeInTheDocument();
    });

    const moatButton = screen.getByRole('button', { name: 'Economic Moat' });
    fireEvent.click(moatButton);

    // Check if header for Economic Moat appeared in table
    // It will have the sort icon as well, so we use regex
    expect(screen.getByRole('columnheader', { name: /Economic Moat/i })).toBeInTheDocument();
    expect(screen.getByText('9')).toBeInTheDocument();
  });

  it('handles error state', async () => {
    vi.mocked(api.getAIScores).mockResolvedValue({
      success: false,
      message: 'Failed to load scores',
    });

    render(
      <MemoryRouter>
        <AIScoresPage />
      </MemoryRouter>
    );

    await waitFor(() => {
      expect(screen.getByText('Failed to load scores')).toBeInTheDocument();
    });
  });

  it('navigates back when back button is clicked', async () => {
    vi.mocked(api.getAIScores).mockResolvedValue(mockScoresData);
    render(
      <MemoryRouter>
        <AIScoresPage />
      </MemoryRouter>
    );

    await waitFor(() => {
      expect(screen.getByText(/Back to Search/i)).toBeInTheDocument();
    });

    fireEvent.click(screen.getByText(/Back to Search/i));
    expect(mockNavigate).toHaveBeenCalledWith(-1);
  });

  it('handles sorting by various columns including strings and numbers', async () => {
    const scores = [
      { ticker: 'Z', company_name: 'Zebra', total_score_percentile_rank: 50 },
      { ticker: 'A', company_name: 'Apple', total_score_percentile_rank: 90 },
      { ticker: 'M', company_name: null, total_score_percentile_rank: 70 }
    ];
    vi.mocked(api.getAIScores).mockResolvedValue({ success: true, scores });

    render(
      <MemoryRouter>
        <AIScoresPage />
      </MemoryRouter>
    );

    await waitFor(() => {
      expect(screen.getByText('Z')).toBeInTheDocument();
    });

    // Sort by Ticker (asc)
    const tickerHeader = screen.getByRole('columnheader', { name: /Ticker/i });
    fireEvent.click(tickerHeader); // Already desc by default in code? No, default is desc for Percentile.
    fireEvent.click(tickerHeader); // Click once for desc, twice for asc?
    
    // Default is Percentile DESC. 
    // Let's click Ticker. First click will set to DESC. Second click to ASC.
    fireEvent.click(tickerHeader); // DESC
    let rows = screen.getAllByRole('row');
    expect(rows[1]).toHaveTextContent('Z');

    fireEvent.click(tickerHeader); // ASC
    rows = screen.getAllByRole('row');
    expect(rows[1]).toHaveTextContent('A');

    // Sort by Company Name (asc) - handle null
    const companyHeader = screen.getByRole('columnheader', { name: /Company/i });
    fireEvent.click(companyHeader); // DESC
    fireEvent.click(companyHeader); // ASC
    
    rows = screen.getAllByRole('row');
    // Null/Empty string should be at the beginning for ASC
    expect(rows[1]).toHaveTextContent('M'); 
  });

  it('handles network errors', async () => {
    vi.mocked(api.getAIScores).mockRejectedValue(new Error('Network error'));

    render(
      <MemoryRouter>
        <AIScoresPage />
      </MemoryRouter>
    );

    await waitFor(() => {
      expect(screen.getByText(/Error loading scores/i)).toBeInTheDocument();
    });
  });
});
