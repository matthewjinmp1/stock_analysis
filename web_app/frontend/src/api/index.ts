import axios from 'axios';

const API_BASE_URL = '/api';

const api = axios.create({
  baseURL: API_BASE_URL,
});

export const searchTicker = async (query: string) => {
  const response = await api.get(`/search/${encodeURIComponent(query)}`);
  return response.data;
};

export const getSearchSuggestions = async (query: string) => {
  const response = await api.get(`/search_suggestions/${encodeURIComponent(query)}`);
  return response.data;
};

export const getWatchlist = async () => {
  const response = await api.get('/watchlist');
  return response.data;
};

export const addToWatchlist = async (ticker: string) => {
  const response = await api.post(`/watchlist/add/${ticker}`);
  return response.data;
};

export const removeFromWatchlist = async (ticker: string) => {
  const response = await api.post(`/watchlist/remove/${ticker}`);
  return response.data;
};

export const getPeers = async (ticker: string) => {
  const response = await api.get(`/peers/${ticker}`);
  return response.data;
};

export const findPeersAI = async (ticker: string) => {
  const response = await api.get(`/find_peers/${ticker}`);
  return response.data;
};

export const getAdjustedPE = async (ticker: string) => {
  const response = await api.get(`/adjusted_pe/${ticker}`);
  return response.data;
};

export const getAIScores = async () => {
  const response = await api.get('/ai_scores');
  return response.data;
};

export const getList = async () => {
  const response = await api.get('/list');
  return response.data;
};

export const getMetrics = async (ticker: string) => {
  const response = await api.get(`/metrics/${ticker}`);
  return response.data;
};

export const getFinancials = async (ticker: string) => {
  const response = await api.get(`/financial/${ticker}`);
  return response.data;
};

export const calculateMissingAdjustedPE = async () => {
  const response = await api.post('/calculate_missing_adjusted_pe');
  return response.data;
};

export default api;
