import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { MemoryRouter, Route, Routes } from 'react-router-dom';
import { vi, describe, it, expect, beforeEach } from 'vitest';
import PeersPage from './PeersPage';
import * as api from '../api';

// Mock the API module
vi.mock('../api', () => ({
  getPeers: vi.fn(),
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

describe('PeersPage', () => {
  const mockPeerData = {
    success: true,
    main_ticker: {
      ticker: 'AAPL',
      company_name: 'Apple Inc',
      total_score_percentile_rank: 90,
      financial_total_percentile: 85,
      adjusted_pe_ratio: 25.5,
      short_float: '1.2%',
    },
    peers: [
      {
        ticker: 'MSFT',
        company_name: 'Microsoft Corp',
        total_score_percentile_rank: 88,
        financial_total_percentile: 82,
        adjusted_pe_ratio: 30.1,
        short_float: '0.8%',
      },
      {
        ticker: 'GOOGL',
        company_name: 'Alphabet Inc',
        total_score_percentile_rank: 85,
        financial_total_percentile: 80,
        adjusted_pe_ratio: 22.3,
        short_float: '1.0%',
      },
    ],
    analysis_timestamp: '2023-10-27T10:00:00Z',
  };

  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('renders loading state initially', async () => {
    vi.mocked(api.getPeers).mockReturnValue(new Promise(() => {})); // Never resolves
    
    render(
      <MemoryRouter>
        <PeersPage />
      </MemoryRouter>
    );

    expect(screen.getByText(/Loading peer data/i)).toBeInTheDocument();
  });

  it('renders peer data correctly', async () => {
    vi.mocked(api.getPeers).mockResolvedValue(mockPeerData);

    render(
      <MemoryRouter>
        <PeersPage />
      </MemoryRouter>
    );

    await waitFor(() => {
      expect(screen.getByText('Apple Inc')).toBeInTheDocument();
      expect(screen.getByText('Microsoft Corp')).toBeInTheDocument();
      expect(screen.getByText('Alphabet Inc')).toBeInTheDocument();
    });

    expect(screen.getByText('AAPL')).toBeInTheDocument();
    expect(screen.getByText('MSFT')).toBeInTheDocument();
    expect(screen.getByText('GOOGL')).toBeInTheDocument();
  });

  it('handles error state', async () => {
    vi.mocked(api.getPeers).mockResolvedValue({
      success: false,
      message: 'Failed to fetch peers',
    });

    render(
      <MemoryRouter>
        <PeersPage />
      </MemoryRouter>
    );

    await waitFor(() => {
      expect(screen.getByText('Failed to fetch peers')).toBeInTheDocument();
    });
  });

  it('allows sorting by ticker', async () => {
    vi.mocked(api.getPeers).mockResolvedValue(mockPeerData);

    render(
      <MemoryRouter>
        <PeersPage />
      </MemoryRouter>
    );

    await waitFor(() => {
      expect(screen.getByText('AAPL')).toBeInTheDocument();
    });

    const tickerHeader = screen.getByText(/Ticker/i);
    fireEvent.click(tickerHeader); // Sort asc

    const rows = screen.getAllByRole('row');
    // First row is header, second should be AAPL
    expect(rows[1]).toHaveTextContent('AAPL');

    fireEvent.click(tickerHeader); // Sort desc
    // Now last row should be AAPL or first row should be MSFT
    const updatedRows = screen.getAllByRole('row');
    expect(updatedRows[1]).toHaveTextContent('MSFT');
  });

  it('handles polling for peer finding', async () => {
    // Set a very short polling interval for the test
    (window as any).__POLL_INTERVAL__ = 100;

    // 1. Initial response says finding_peers: true
    vi.mocked(api.getPeers)
      .mockResolvedValueOnce({
        success: true,
        finding_peers: true,
        main_ticker: mockPeerData.main_ticker,
        peers: [],
      })
      // 2. Second response (poll) returns peers
      .mockResolvedValueOnce(mockPeerData);

    render(
      <MemoryRouter>
        <PeersPage />
      </MemoryRouter>
    );

    await waitFor(() => {
      expect(screen.getByText(/Finding peers using AI analysis/i)).toBeInTheDocument();
    });

    // Wait for poll
    await waitFor(() => {
      expect(screen.getByText('Microsoft Corp')).toBeInTheDocument();
    }, { timeout: 10000 });

    delete (window as any).__POLL_INTERVAL__;
  });

  it('handles sorting by other columns', async () => {
    vi.mocked(api.getPeers).mockResolvedValue(mockPeerData);

    render(
      <MemoryRouter>
        <PeersPage />
      </MemoryRouter>
    );

    await waitFor(() => {
      expect(screen.getByText('AAPL')).toBeInTheDocument();
    });

    // Sort by Quality Score
    const scoreHeader = screen.getByText(/Quality Score/i);
    fireEvent.click(scoreHeader); // Sort asc
    
    let rows = screen.getAllByRole('row');
    // GOOGL (85), MSFT (88), AAPL (90)
    expect(rows[1]).toHaveTextContent('GOOGL');

    fireEvent.click(scoreHeader); // Sort desc
    rows = screen.getAllByRole('row');
    // AAPL (90), MSFT (88), GOOGL (85)
    expect(rows[1]).toHaveTextContent('AAPL');
  });

  it('navigates back when back button is clicked', async () => {
    vi.mocked(api.getPeers).mockResolvedValue(mockPeerData);

    render(
      <MemoryRouter>
        <PeersPage />
      </MemoryRouter>
    );

    await waitFor(() => {
      expect(screen.getByText('Back')).toBeInTheDocument();
    });

    fireEvent.click(screen.getByText('Back'));
    expect(mockNavigate).toHaveBeenCalledWith(-1);
  });

  it('handles null values and complex sorting', async () => {
    const dataWithNulls = {
      success: true,
      main_ticker: { ticker: 'AAPL', adjusted_pe_ratio: null, short_float: '1.2%' },
      peers: [
        { ticker: 'MSFT', adjusted_pe_ratio: 25, short_float: '0.5%' },
        { ticker: 'GOOGL', adjusted_pe_ratio: 20, short_float: null }
      ]
    };
    vi.mocked(api.getPeers).mockResolvedValue(dataWithNulls);

    render(
      <MemoryRouter>
        <PeersPage />
      </MemoryRouter>
    );

    await waitFor(() => {
      expect(screen.getByText('AAPL')).toBeInTheDocument();
    });

    // Sort by Adjusted PE (asc) - nulls should go to bottom (Infinity)
    const peHeader = screen.getByText(/Adjusted PE/i);
    fireEvent.click(peHeader); 
    
    let rows = screen.getAllByRole('row');
    expect(rows[1]).toHaveTextContent('GOOGL'); // 20
    expect(rows[2]).toHaveTextContent('MSFT');  // 25
    expect(rows[3]).toHaveTextContent('AAPL');  // null

    // Sort by Short Float (asc)
    const shortHeader = screen.getByText(/Short Float/i);
    fireEvent.click(shortHeader);
    
    rows = screen.getAllByRole('row');
    expect(rows[1]).toHaveTextContent('GOOGL'); // null (0)
    expect(rows[2]).toHaveTextContent('MSFT');  // 0.5%
    expect(rows[3]).toHaveTextContent('AAPL');  // 1.2%
  });

  it('handles empty peers list', async () => {
    vi.mocked(api.getPeers).mockResolvedValue({
      success: true,
      main_ticker: { ticker: 'AAPL' },
      peers: []
    });

    render(
      <MemoryRouter>
        <PeersPage />
      </MemoryRouter>
    );

    await waitFor(() => {
      expect(screen.getByText('AAPL')).toBeInTheDocument();
    });
    
    // Should still show main ticker in table
    const rows = screen.getAllByRole('row');
    expect(rows.length).toBe(2); // Header + 1 row
  });

  it('handles network error in polling', async () => {
    (window as any).__POLL_INTERVAL__ = 50;
    vi.mocked(api.getPeers)
      .mockResolvedValueOnce({ success: true, finding_peers: true, main_ticker: { ticker: 'AAPL' }, peers: [] })
      .mockRejectedValueOnce(new Error('Network error during poll'));

    render(
      <MemoryRouter>
        <PeersPage />
      </MemoryRouter>
    );

    await waitFor(() => {
      expect(screen.getByText(/Finding peers/i)).toBeInTheDocument();
    });

    // Wait for a bit to let poll happen
    await new Promise(r => setTimeout(r, 200));
    
    // Should still be loading/showing finding peers message
    expect(screen.getByText(/Finding peers/i)).toBeInTheDocument();
    
    delete (window as any).__POLL_INTERVAL__;
  });
});
