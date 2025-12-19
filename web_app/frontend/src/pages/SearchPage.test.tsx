import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import SearchPage from './SearchPage';
import { ThemeProvider } from '../components/ThemeContext';
import { BrowserRouter } from 'react-router-dom';
import * as api from '../api';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import React from 'react';

// Mock the API
vi.mock('../api', () => ({
  getSearchSuggestions: vi.fn(),
  searchTicker: vi.fn(),
  addToWatchlist: vi.fn(),
  removeFromWatchlist: vi.fn(),
}));

const renderSearchPage = () => {
  return render(
    <ThemeProvider>
      <BrowserRouter>
        <SearchPage />
      </BrowserRouter>
    </ThemeProvider>
  );
};

describe('SearchPage', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('renders search input', () => {
    renderSearchPage();
    expect(screen.getByPlaceholderText(/search tickers/i)).toBeInTheDocument();
  });

  it('shows suggestions when typing', async () => {
    const suggestions = [
      { ticker: 'AAPL', company_name: 'Apple Inc', match_type: 'ticker' }
    ];
    (api.getSearchSuggestions as any).mockResolvedValue({ success: true, suggestions });

    renderSearchPage();
    const input = screen.getByPlaceholderText(/search tickers/i);
    
    fireEvent.change(input, { target: { value: 'AA' } });

    await waitFor(() => {
      expect(screen.getByText(/Apple Inc/)).toBeInTheDocument();
    });
  });

  it('performs search and displays result', async () => {
    const mockData = {
      success: true,
      ticker: 'AAPL',
      data: {
        company_name: 'Apple Inc',
        short_float: '1.5%',
        total_score_percentile_rank: 90,
        financial_total_percentile: 85,
        adjusted_pe_ratio: 25.5,
        current_year_growth: 10,
        next_year_growth: 12
      },
      in_watchlist: false
    };
    (api.searchTicker as any).mockResolvedValue(mockData);

    renderSearchPage();
    const input = screen.getByPlaceholderText(/search tickers/i);
    
    fireEvent.change(input, { target: { value: 'AAPL' } });
    fireEvent.keyDown(input, { key: 'Enter', code: 'Enter' });

    await waitFor(() => {
      // Use queryAllByText or be more specific to avoid multiple matches
      const results = screen.getAllByText('Apple Inc (AAPL)');
      expect(results.length).toBeGreaterThan(0);
      expect(screen.getByText('90%')).toBeInTheDocument();
      expect(screen.getByText('25.50')).toBeInTheDocument();
    });
  });

  it('handles search errors', async () => {
    (api.searchTicker as any).mockResolvedValue({ 
      success: false, 
      message: 'Ticker not found' 
    });

    renderSearchPage();
    const input = screen.getByPlaceholderText(/search tickers/i);
    
    fireEvent.change(input, { target: { value: 'INVALID' } });
    fireEvent.keyDown(input, { key: 'Enter', code: 'Enter' });

    await waitFor(() => {
      expect(screen.getByText(/Ticker not found/)).toBeInTheDocument();
    });
  });

  it('toggles watchlist status from search result', async () => {
    const mockData = {
      success: true,
      ticker: 'AAPL',
      data: { 
        company_name: 'Apple Inc', 
        total_score_percentile_rank: 90,
        financial_total_percentile: 85,
        adjusted_pe_ratio: 25.5,
        current_year_growth: 10,
        next_year_growth: 12,
        short_float: '1.5%'
      },
      in_watchlist: false
    };
    (api.searchTicker as any).mockResolvedValue(mockData);
    (api.addToWatchlist as any).mockResolvedValue({ success: true });

    renderSearchPage();
    const input = screen.getByPlaceholderText(/search tickers/i);
    fireEvent.change(input, { target: { value: 'AAPL' } });
    fireEvent.keyDown(input, { key: 'Enter' });

    await waitFor(() => {
      expect(screen.getByText('Add')).toBeInTheDocument();
    });

    const addButton = screen.getByText('Add');
    fireEvent.click(addButton);

    await waitFor(() => {
      expect(api.addToWatchlist).toHaveBeenCalledWith('AAPL');
    });
  });

  it('navigates search suggestions with keyboard', async () => {
    const suggestions = [
      { ticker: 'AAPL', company_name: 'Apple Inc', match_type: 'ticker' },
      { ticker: 'AMZN', company_name: 'Amazon.com', match_type: 'ticker' }
    ];
    (api.getSearchSuggestions as any).mockResolvedValue({ success: true, suggestions });
    (api.searchTicker as any).mockResolvedValue({ 
      success: true, 
      ticker: 'AMZN', 
      data: { 
        company_name: 'Amazon',
        total_score_percentile_rank: 90,
        financial_total_percentile: 85,
        adjusted_pe_ratio: 25.5,
        current_year_growth: 10,
        next_year_growth: 12,
        short_float: '1.5%'
      } 
    });

    renderSearchPage();
    const input = screen.getByPlaceholderText(/search tickers/i);
    fireEvent.change(input, { target: { value: 'A' } });

    await waitFor(() => {
      expect(screen.getByText(/Apple Inc/)).toBeInTheDocument();
    });

    fireEvent.keyDown(input, { key: 'ArrowDown' });
    fireEvent.keyDown(input, { key: 'ArrowDown' });
    fireEvent.keyDown(input, { key: 'Enter' });

    await waitFor(() => {
      expect(api.searchTicker).toHaveBeenCalledWith('AMZN');
    });
  });

  it('handles escape key to close suggestions', async () => {
    const suggestions = [{ ticker: 'AAPL', company_name: 'Apple Inc' }];
    (api.getSearchSuggestions as any).mockResolvedValue({ success: true, suggestions });

    renderSearchPage();
    const input = screen.getByPlaceholderText(/search tickers/i);
    fireEvent.change(input, { target: { value: 'A' } });

    await waitFor(() => {
      expect(screen.getByText(/Apple Inc/)).toBeInTheDocument();
    });

    fireEvent.keyDown(input, { key: 'Escape' });
    expect(screen.queryByText(/Apple Inc/)).not.toBeInTheDocument();
  });
});
