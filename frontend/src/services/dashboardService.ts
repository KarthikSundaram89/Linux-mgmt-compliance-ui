/**
 * Dashboard API service.
 * Fetches summary statistics for the dashboard view.
 */
import apiClient from './api';
import { DashboardStats, SchedulerStatus } from '../types';

export const dashboardService = {
  async getStats(): Promise<DashboardStats> {
    const response = await apiClient.get('/dashboard/stats');
    return response.data;
  },

  async getSchedulerStatus(): Promise<SchedulerStatus> {
    const response = await apiClient.get('/scheduler/status');
    return response.data;
  },

  async pauseScheduler(): Promise<void> {
    await apiClient.post('/scheduler/pause');
  },

  async resumeScheduler(): Promise<void> {
    await apiClient.post('/scheduler/resume');
  },

  async triggerFullCollection(): Promise<void> {
    await apiClient.post('/collections/trigger-all');
  },
};
