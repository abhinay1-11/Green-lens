import axios from 'axios';

const API_BASE = import.meta.env.VITE_API_BASE_URL || '/api';

const api = axios.create({
  baseURL: API_BASE,
  headers: {
    'Content-Type': 'application/json',
  },
});

export const getHealth = async () => {
  const response = await api.get('/health');
  return response.data;
};

export const getProviderStatus = async () => {
  const response = await api.get('/providers/status');
  return response.data;
};

export const predictSpecies = async (formData) => {
  const response = await api.post('/identification/predict', formData, {
    headers: {
      'Content-Type': 'multipart/form-data',
    },
  });
  return response.data;
};

export const createObservation = async (observationData) => {
  const response = await api.post('/observations', observationData);
  return response.data;
};

export const getObservations = async (params = {}) => {
  const response = await api.get('/observations', { params });
  return response.data;
};

export const getObservationById = async (id) => {
  const response = await api.get(`/observations/${id}`);
  return response.data;
};

export const updateObservation = async (id, data) => {
  const response = await api.patch(`/observations/${id}`, data);
  return response.data;
};

export const deleteObservation = async (id) => {
  const response = await api.delete(`/observations/${id}`);
  return response.data;
};

export const searchSpecies = async (query = '', category = '', options = {}) => {
  const response = await api.get('/species/search', {
    params: { q: query, category },
    signal: options.signal
  });
  return response.data;
};

export const getSpeciesProfile = async (scientificName, commonName = '', category = '') => {
  const response = await api.get('/species/profile', {
    params: { scientific_name: scientificName, common_name: commonName, category }
  });
  return response.data;
};

export const getSpeciesDetail = async (id) => {
  const response = await api.get(`/species/${id}`);
  return response.data;
};

export const getDashboardAnalytics = async () => {
  const response = await api.get('/analytics/dashboard');
  return response.data;
};

export const getTrendAnalytics = async (period = '30d') => {
  const response = await api.get('/analytics/trends', { params: { period } });
  return response.data;
};

export const getMapObservations = async (filters = {}) => {
  const response = await api.get('/analytics/map', { params: filters });
  return response.data;
};

// Collections API
export const getCollections = async () => {
  const response = await api.get('/collections');
  return response.data;
};

export const createCollection = async (collectionData) => {
  const response = await api.post('/collections', collectionData);
  return response.data;
};

export const getCollectionDetail = async (id) => {
  const response = await api.get(`/collections/${id}`);
  return response.data;
};

export const updateCollection = async (id, collectionData) => {
  const response = await api.put(`/collections/${id}`, collectionData);
  return response.data;
};

export const deleteCollection = async (id) => {
  const response = await api.delete(`/collections/${id}`);
  return response.data;
};

export const addCollectionItem = async (collectionId, itemData) => {
  const response = await api.post(`/collections/${collectionId}/items`, itemData);
  return response.data;
};

export const removeCollectionItem = async (collectionId, itemId) => {
  const response = await api.delete(`/collections/${collectionId}/items/${itemId}`);
  return response.data;
};

export const getCollectionExportPdfUrl = (id) => `${API_BASE}/collections/${id}/export/pdf`;
export const getCollectionExportCsvUrl = (id) => `${API_BASE}/collections/${id}/export/csv`;

export const getExportCsvUrl = () => `${API_BASE}/reports/observations.csv`;
export const getExportPdfUrl = () => `${API_BASE}/reports/observations.pdf`;

export default api;
