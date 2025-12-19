import { describe, it, expect, vi, beforeEach } from 'vitest';
import api, {
  searchTicker,
  getSearchSuggestions,
  getWatchlist,
  addToWatchlist,
  removeFromWatchlist,
  getPeers,
  findPeersAI,
  getAdjustedPE,
  getAIScores,
  getList,
  getMetrics,
  getFinancials,
  calculateMissingAdjustedPE
} from './index';

vi.mock('axios', async () => {
  const actual = await vi.importActual('axios');
  return {
    default: {
      create: vi.fn(() => ({
        get: vi.fn(),
        post: vi.fn(),
        defaults: { baseURL: '' },
        interceptors: {
          request: { use: vi.fn(), eject: vi.fn() },
          response: { use: vi.fn(), eject: vi.fn() }
        }
      }))
    }
  };
});

describe('API Functions', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('searchTicker should call correct endpoint', async () => {
    const mockData = { success: true };
    (api.get as any).mockResolvedValue({ data: mockData });
    const result = await searchTicker('AAPL');
    expect(api.get).toHaveBeenCalledWith('/search/AAPL');
    expect(result).toEqual(mockData);
  });

  it('getSearchSuggestions should call correct endpoint', async () => {
    const mockData = { success: true, suggestions: [] };
    (api.get as any).mockResolvedValue({ data: mockData });
    const result = await getSearchSuggestions('AA');
    expect(api.get).toHaveBeenCalledWith('/search_suggestions/AA');
    expect(result).toEqual(mockData);
  });

  it('getWatchlist should call correct endpoint', async () => {
    const mockData = { success: true, watchlist: [] };
    (api.get as any).mockResolvedValue({ data: mockData });
    const result = await getWatchlist();
    expect(api.get).toHaveBeenCalledWith('/watchlist');
    expect(result).toEqual(mockData);
  });

  it('addToWatchlist should call correct endpoint', async () => {
    const mockData = { success: true };
    (api.post as any).mockResolvedValue({ data: mockData });
    const result = await addToWatchlist('AAPL');
    expect(api.post).toHaveBeenCalledWith('/watchlist/add/AAPL');
    expect(result).toEqual(mockData);
  });

  it('removeFromWatchlist should call correct endpoint', async () => {
    const mockData = { success: true };
    (api.post as any).mockResolvedValue({ data: mockData });
    const result = await removeFromWatchlist('AAPL');
    expect(api.post).toHaveBeenCalledWith('/watchlist/remove/AAPL');
    expect(result).toEqual(mockData);
  });

  it('getPeers should call correct endpoint', async () => {
    const mockData = { success: true };
    (api.get as any).mockResolvedValue({ data: mockData });
    const result = await getPeers('AAPL');
    expect(api.get).toHaveBeenCalledWith('/peers/AAPL');
    expect(result).toEqual(mockData);
  });

  it('findPeersAI should call correct endpoint', async () => {
    const mockData = { success: true };
    (api.get as any).mockResolvedValue({ data: mockData });
    const result = await findPeersAI('AAPL');
    expect(api.get).toHaveBeenCalledWith('/find_peers/AAPL');
    expect(result).toEqual(mockData);
  });

  it('getAdjustedPE should call correct endpoint', async () => {
    const mockData = { success: true };
    (api.get as any).mockResolvedValue({ data: mockData });
    const result = await getAdjustedPE('AAPL');
    expect(api.get).toHaveBeenCalledWith('/adjusted_pe/AAPL');
    expect(result).toEqual(mockData);
  });

  it('getAIScores should call correct endpoint', async () => {
    const mockData = { success: true };
    (api.get as any).mockResolvedValue({ data: mockData });
    const result = await getAIScores();
    expect(api.get).toHaveBeenCalledWith('/ai_scores');
    expect(result).toEqual(mockData);
  });

  it('getList should call correct endpoint', async () => {
    const mockData = { success: true };
    (api.get as any).mockResolvedValue({ data: mockData });
    const result = await getList();
    expect(api.get).toHaveBeenCalledWith('/list');
    expect(result).toEqual(mockData);
  });

  it('getMetrics should call correct endpoint', async () => {
    const mockData = { success: true };
    (api.get as any).mockResolvedValue({ data: mockData });
    const result = await getMetrics('AAPL');
    expect(api.get).toHaveBeenCalledWith('/metrics/AAPL');
    expect(result).toEqual(mockData);
  });

  it('getFinancials should call correct endpoint', async () => {
    const mockData = { success: true };
    (api.get as any).mockResolvedValue({ data: mockData });
    const result = await getFinancials('AAPL');
    expect(api.get).toHaveBeenCalledWith('/financial/AAPL');
    expect(result).toEqual(mockData);
  });

  it('calculateMissingAdjustedPE should call correct endpoint', async () => {
    const mockData = { success: true };
    (api.post as any).mockResolvedValue({ data: mockData });
    const result = await calculateMissingAdjustedPE();
    expect(api.post).toHaveBeenCalledWith('/calculate_missing_adjusted_pe');
    expect(result).toEqual(mockData);
  });
});
