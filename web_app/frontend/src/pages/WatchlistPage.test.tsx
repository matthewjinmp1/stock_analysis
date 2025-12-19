import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import WatchlistPage from './WatchlistPage';
import { ThemeProvider } from '../components/ThemeContext';
import { BrowserRouter } from 'react-router-dom';
import * as api from '../api';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import React from 'react';

// Mock the API
vi.mock('../api', () => ({
  getWatchlist: vi.fn(),
  getSearchSuggestions: vi.fn(),
  addToWatchlist: vi.fn(),
  removeFromWatchlist: vi.fn(),
  calculateMissingAdjustedPE: vi.fn(),
}));

// Mock useNavigate
const mockNavigate = vi.fn();
vi.mock('react-router-dom', async () => {
  const actual = await vi.importActual('react-router-dom');
  return {
    ...actual,
    useNavigate: () => mockNavigate,
  };
});

const renderWatchlistPage = () => {
  return render(
    <ThemeProvider>
      <BrowserRouter>
        <WatchlistPage />
      </BrowserRouter>
    </ThemeProvider>
  );
};

describe('WatchlistPage', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('renders loading state initially', () => {
    (api.getWatchlist as any).mockReturnValue(new Promise(() => {}));
    renderWatchlistPage();
    expect(screen.getByText(/loading watchlist/i)).toBeInTheDocument();
  });

  it('renders watchlist items', async () => {
    const watchlist = [
      {
        ticker: 'AAPL',
        company_name: 'Apple Inc',
        total_score_percentile_rank: 90,
        financial_total_percentile: 85,
        adjusted_pe_ratio: 25.5,
        two_year_annualized_growth: 10,
        short_float: '1.5%',
        adjusted_pe_loading: false,
        growth_loading: false,
        short_interest_loading: false,
        financial_loading: false
      }
    ];
    (api.getWatchlist as any).mockResolvedValue({ success: true, watchlist });

    renderWatchlistPage();

    await waitFor(() => {
      expect(screen.getByText('AAPL')).toBeInTheDocument();
      expect(screen.getByText('Apple Inc')).toBeInTheDocument();
      expect(screen.getByText('90%')).toBeInTheDocument();
    });
  });

  it('handles empty watchlist', async () => {
    (api.getWatchlist as any).mockResolvedValue({ success: true, watchlist: [] });

    renderWatchlistPage();

    await waitFor(() => {
      expect(screen.getByText(/your watchlist is empty/i)).toBeInTheDocument();
    });
  });

  it('allows adding a ticker', async () => {
    (api.getWatchlist as any).mockResolvedValue({ success: true, watchlist: [] });
    (api.addToWatchlist as any).mockResolvedValue({ success: true });

    renderWatchlistPage();

    const input = screen.getByPlaceholderText(/enter ticker symbol/i);
    fireEvent.change(input, { target: { value: 'MSFT' } });
    fireEvent.keyDown(input, { key: 'Enter', code: 'Enter' });

    await waitFor(() => {
      expect(api.addToWatchlist).toHaveBeenCalledWith('MSFT');
    });
  });

  it('allows removing a ticker', async () => {
    const watchlist = [{ ticker: 'AAPL', company_name: 'Apple' }];
    (api.getWatchlist as any).mockResolvedValue({ success: true, watchlist });
    (api.removeFromWatchlist as any).mockResolvedValue({ success: true });

    renderWatchlistPage();

    await waitFor(() => {
      const removeButton = screen.getByText(/remove/i);
      fireEvent.click(removeButton);
    });

    await waitFor(() => {
      expect(api.removeFromWatchlist).toHaveBeenCalledWith('AAPL');
    });
  });

  it('toggles visibility of columns', async () => {
    const watchlist = [{ 
      ticker: 'AAPL', 
      company_name: 'Apple',
      total_score_percentile_rank: 90,
      financial_total_percentile: 85,
      adjusted_pe_ratio: 25.5,
      two_year_annualized_growth: 10,
      two_year_forward_pe: 20,
      short_float: '1.5%'
    }];
    (api.getWatchlist as any).mockResolvedValue({ success: true, watchlist });

    renderWatchlistPage();

    await waitFor(() => {
      expect(screen.getByText('90%')).toBeInTheDocument();
    });

    const totalScoreToggle = screen.getByText('Quality Score', { selector: 'button' });
    fireEvent.click(totalScoreToggle);

    expect(screen.queryByText('90%')).not.toBeInTheDocument();

    fireEvent.click(totalScoreToggle);
    expect(screen.getByText('90%')).toBeInTheDocument();
  });

  it('sorts watchlist items by ticker', async () => {
    const watchlist = [
      { ticker: 'MSFT', company_name: 'Microsoft' },
      { ticker: 'AAPL', company_name: 'Apple' }
    ];
    (api.getWatchlist as any).mockResolvedValue({ success: true, watchlist });

    renderWatchlistPage();

    await waitFor(() => {
      const cells = screen.getAllByRole('link').filter(l => l.getAttribute('href')?.includes('?q='));
      expect(cells[0]).toHaveTextContent('MSFT');
      expect(cells[1]).toHaveTextContent('AAPL');
    });

    const tickerHeader = screen.getByRole('columnheader', { name: /Ticker/i });
    fireEvent.click(tickerHeader); // Sort ASC

    await waitFor(() => {
      const cells = screen.getAllByRole('link').filter(l => l.getAttribute('href')?.includes('?q='));
      expect(cells[0]).toHaveTextContent('AAPL');
      expect(cells[1]).toHaveTextContent('MSFT');
    });

    fireEvent.click(tickerHeader); // Sort DESC
    await waitFor(() => {
      const cells = screen.getAllByRole('link').filter(l => l.getAttribute('href')?.includes('?q='));
      expect(cells[0]).toHaveTextContent('MSFT');
      expect(cells[1]).toHaveTextContent('AAPL');
    });
  });

  it('shows and selects search suggestions', async () => {
    (api.getWatchlist as any).mockResolvedValue({ success: true, watchlist: [] });
    const suggestions = [
      { ticker: 'AAPL', company_name: 'Apple Inc', match_type: 'ticker' }
    ];
    (api.getSearchSuggestions as any).mockResolvedValue({ success: true, suggestions });
    (api.addToWatchlist as any).mockResolvedValue({ success: true });

    renderWatchlistPage();

    const input = screen.getByPlaceholderText(/enter ticker symbol/i);
    fireEvent.change(input, { target: { value: 'AA' } });

    await waitFor(() => {
      expect(screen.getByText('Apple Inc')).toBeInTheDocument();
    });

    const suggestion = screen.getByText('Apple Inc');
    fireEvent.click(suggestion);

    await waitFor(() => {
      expect(api.addToWatchlist).toHaveBeenCalledWith('AAPL');
    });
  });

  it('handles keyboard navigation in suggestions', async () => {
    (api.getWatchlist as any).mockResolvedValue({ success: true, watchlist: [] });
    const suggestions = [
      { ticker: 'AAPL', company_name: 'Apple Inc', match_type: 'ticker' },
      { ticker: 'AMZN', company_name: 'Amazon.com', match_type: 'ticker' }
    ];
    (api.getSearchSuggestions as any).mockResolvedValue({ success: true, suggestions });
    (api.addToWatchlist as any).mockResolvedValue({ success: true });

    renderWatchlistPage();

    const input = screen.getByPlaceholderText(/enter ticker symbol/i);
    fireEvent.change(input, { target: { value: 'A' } });

    await waitFor(() => {
      expect(screen.getByText('Apple Inc')).toBeInTheDocument();
    });

    fireEvent.keyDown(input, { key: 'ArrowDown' });
    fireEvent.keyDown(input, { key: 'ArrowDown' });
    fireEvent.keyDown(input, { key: 'Enter' });

    await waitFor(() => {
      expect(api.addToWatchlist).toHaveBeenCalledWith('AMZN');
    });
  });

  it('handles API error when loading watchlist', async () => {
    (api.getWatchlist as any).mockResolvedValue({ success: false, message: 'API Error' });

    renderWatchlistPage();

    await waitFor(() => {
      expect(screen.getByText('API Error')).toBeInTheDocument();
    });
  });

  it('handles network error when loading watchlist', async () => {
    (api.getWatchlist as any).mockRejectedValue(new Error('Network Error'));

    renderWatchlistPage();

    await waitFor(() => {
      expect(screen.getByText(/error loading watchlist/i)).toBeInTheDocument();
    });
  });

  it('shows loading states for individual items', async () => {
    const watchlist = [
      { 
        ticker: 'AAPL', 
        company_name: 'Apple',
        financial_loading: true,
        adjusted_pe_loading: true,
        growth_loading: true,
        short_interest_loading: true
      }
    ];
    (api.getWatchlist as any).mockResolvedValue({ success: true, watchlist });

    renderWatchlistPage();

    await waitFor(() => {
      const loadingStates = screen.getAllByText('Loading...');
      expect(loadingStates.length).toBeGreaterThan(0);
    });
  });
});
