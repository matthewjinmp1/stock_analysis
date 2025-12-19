import { render, screen } from '@testing-library/react';
import { vi, describe, it, expect } from 'vitest';
import App from './App';

// Mock all the pages to avoid complex rendering in App test
vi.mock('./pages/SearchPage', () => ({ default: () => <div>Search Page</div> }));
vi.mock('./pages/WatchlistPage', () => ({ default: () => <div>Watchlist Page</div> }));
vi.mock('./pages/AIScoresPage', () => ({ default: () => <div>AI Scores Page</div> }));
vi.mock('./pages/PeersPage', () => ({ default: () => <div>Peers Page</div> }));
vi.mock('./pages/MetricsPage', () => ({ default: () => <div>Metrics Page</div> }));
vi.mock('./pages/FinancialsPage', () => ({ default: () => <div>Financials Page</div> }));
vi.mock('./pages/AdjustedPEPage', () => ({ default: () => <div>Adjusted PE Page</div> }));
vi.mock('./pages/FindPeersPage', () => ({ default: () => <div>Find Peers Page</div> }));

describe('App', () => {
  it('renders search page by default', () => {
    render(<App />);
    expect(screen.getByText('Search Page')).toBeInTheDocument();
  });
});
