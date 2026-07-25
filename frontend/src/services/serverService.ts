/**
 * Server API service.
 * Handles all server-related API calls.
 */
import apiClient from './api';
import { Server, ServerCreate, PaginatedResponse } from '../types';

interface ServerListParams {
  page?: number;
  page_size?: number;
  search?: string;
  environment?: string;
  os_family?: string;
  is_active?: boolean;
  sort_by?: string;
  sort_order?: 'asc' | 'desc';
}

export const serverService = {
  async list(params: ServerListParams = {}): Promise<PaginatedResponse<Server>> {
    const response = await apiClient.get('/servers', { params });
    return response.data;
  },

  async getById(id: string): Promise<Server> {
    const response = await apiClient.get(`/servers/${id}`);
    return response.data;
  },

  async create(data: ServerCreate): Promise<Server> {
    const response = await apiClient.post('/servers', data);
    return response.data;
  },

  async update(id: string, data: Partial<ServerCreate>): Promise<Server> {
    const response = await apiClient.put(`/servers/${id}`, data);
    return response.data;
  },

  async delete(id: string): Promise<void> {
    await apiClient.delete(`/servers/${id}`);
  },

  async triggerCollection(id: string): Promise<void> {
    await apiClient.post(`/collections/trigger/${id}`);
  },
};
