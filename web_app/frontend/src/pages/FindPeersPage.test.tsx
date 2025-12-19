import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { vi, describe, it, expect, beforeEach } from 'vitest';
import FindPeersPage from './FindPeersPage';
import * as api from '../api';

// Mock the API module
vi.mock('../api', () => ({
  findPeersAI: vi.fn(),
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

describe('FindPeersPage', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('renders correctly', () => {
    render(
      <MemoryRouter>
        <FindPeersPage />
      </MemoryRouter>
    );

    expect(screen.getByText(/AI Peer Finder/i)).toBeInTheDocument();
    expect(screen.getByPlaceholderText(/e.g., AAPL/i)).toBeInTheDocument();
    expect(screen.getByText(/FIND COMPARABLE PEERS/i)).toBeInTheDocument();
  });

  it('handles input and finding peers', async () => {
    const mockResult = {
      success: true,
      ticker: 'AAPL',
      company_name: 'Apple Inc',
      peers: [
        { name: 'Microsoft', ticker: 'MSFT' },
        { name: 'Google', ticker: 'GOOGL' },
      ],
      elapsed_time: 1.5,
      estimated_cost: 0.001,
    };

    vi.mocked(api.findPeersAI).mockResolvedValue(mockResult);

    render(
      <MemoryRouter>
        <FindPeersPage />
      </MemoryRouter>
    );

    const input = screen.getByPlaceholderText(/e.g., AAPL/i);
    fireEvent.change(input, { target: { value: 'AAPL' } });
    
    const button = screen.getByText(/FIND COMPARABLE PEERS/i);
    fireEvent.click(button);

    expect(screen.getByText(/ANALYZING MARKET/i)).toBeInTheDocument();

    await waitFor(() => {
      expect(screen.getByText('Apple Inc')).toBeInTheDocument();
      expect(screen.getByText('Microsoft (MSFT)')).toBeInTheDocument();
      expect(screen.getByText('Google (GOOGL)')).toBeInTheDocument();
    });

    expect(api.findPeersAI).toHaveBeenCalledWith('AAPL');
  });

  it('handles error from API', async () => {
    vi.mocked(api.findPeersAI).mockResolvedValue({
      success: false,
      message: 'Failed to find peers',
    });

    render(
      <MemoryRouter>
        <FindPeersPage />
      </MemoryRouter>
    );

    const input = screen.getByPlaceholderText(/e.g., AAPL/i);
    fireEvent.change(input, { target: { value: 'XYZ' } });
    
    fireEvent.click(screen.getByText(/FIND COMPARABLE PEERS/i));

    await waitFor(() => {
      expect(screen.getByText('Failed to find peers')).toBeInTheDocument();
    });
  });

  it('shows error if ticker is empty', async () => {
    render(
      <MemoryRouter>
        <FindPeersPage />
      </MemoryRouter>
    );

    fireEvent.click(screen.getByText(/FIND COMPARABLE PEERS/i));

    expect(screen.getByText(/Please enter a ticker symbol/i)).toBeInTheDocument();
    expect(api.findPeersAI).not.toHaveBeenCalled();
  });

  it('navigates back when back button is clicked', () => {
    render(
      <MemoryRouter>
        <FindPeersPage />
      </MemoryRouter>
    );

    fireEvent.click(screen.getByText(/Back to Search/i));
    expect(mockNavigate).toHaveBeenCalledWith(-1);
  });
});
