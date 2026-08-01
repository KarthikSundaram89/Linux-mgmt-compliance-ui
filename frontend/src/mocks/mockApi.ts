/**
 * Mock API Interceptor
 * ====================
 * Intercepts API calls and returns mock data for UI visualization.
 *
 * Enable by setting VITE_USE_MOCKS=true in frontend/.env
 * or by importing setupMockApi() in main.tsx.
 *
 * This allows the entire frontend to run without a backend,
 * making it easy to demo, screenshot, and develop UI components.
 */

import {
  mockDashboardStats, mockOsDistribution,
  mockCollectionTrend, mockChangesByCategory,
  mockRecentChanges, mockRecentFailures,
  mockTopChangingServers,
} from './dashboard';
import { mockServers } from './servers';
import {
  mockServerDetail, mockOsData, mockUsers as mockServerUsers,
} from './serverDetail';
import {
  mockPackages, mockServices, mockFilesystems,
  mockChrony, mockSSHConfig, mockCollectionHistory,
} from './serverDetail2';
import { mockAppUsers, mockRoles, mockCredentialProfiles } from './users';
import { mockNotifications, mockSchedulerStatus, mockAuditLogs } from './notifications';

/**
 * Simulates API response delay (realistic feel).
 */
const delay = (ms: number = 300) => new Promise(r => setTimeout(r, ms));

/**
 * Paginate an array of items.
 */
function paginate<T>(items: T[], page: number, pageSize: number) {
  const total = items.length;
  const totalPages = Math.ceil(total / pageSize);
  const start = (page - 1) * pageSize;
  const pageItems = items.slice(start, start + pageSize);

  return {
    items: pageItems,
    total,
    page,
    page_size: pageSize,
    total_pages: totalPages,
    has_next: page < totalPages,
    has_previous: page > 1,
  };
}

/**
 * Mock API handler map.
 * Each key is a regex pattern matching the API path.
 */
const mockHandlers: Record<string, (params?: any) => any> = {
  // Dashboard
  '/dashboard/stats': () => mockDashboardStats,

  // Servers
  '/servers$': (params: any) => {
    const page = parseInt(params?.page || '1');
    const pageSize = parseInt(params?.page_size || '25');
    let filtered = [...mockServers];
    if (params?.search) {
      const q = params.search.toLowerCase();
      filtered = filtered.filter(s =>
        s.hostname.toLowerCase().includes(q) ||
        s.ip_address.includes(q) ||
        (s.tags || '').toLowerCase().includes(q)
      );
    }
    if (params?.environment) {
      filtered = filtered.filter(s => s.environment === params.environment);
    }
    if (params?.os_family) {
      filtered = filtered.filter(s => s.os_family === params.os_family);
    }
    return paginate(filtered, page, pageSize);
  },

  // Server detail
  '/servers/[^/]+$': () => mockServerDetail,

  // Snapshots
  '/snapshots/[^/]+/latest': () => ({
    snapshot_id: "snap-001",
    collected_at: "2026-07-25T02:15:30Z",
    data: {
      operating_system: { data: mockOsData },
      users: { data: { users: mockServerUsers, total_count: mockServerUsers.length } },
      packages: { data: { packages: mockPackages, total_count: 856 } },
      services: { data: { services: mockServices, total_count: 142, failed_count: 1 } },
      filesystem: { data: { mounts: mockFilesystems, total_count: 6 } },
      chrony: { data: mockChrony },
      ssh_config: { data: mockSSHConfig },
    },
  }),

  // Collections
  '/collections$': (params: any) => paginate(mockCollectionHistory, parseInt(params?.page || '1'), 25),

  // Changes
  '/changes$': (params: any) => {
    let filtered = [...mockRecentChanges];
    if (params?.severity) filtered = filtered.filter(c => c.severity === params.severity);
    if (params?.category) filtered = filtered.filter(c => c.category === params.category);
    return paginate(filtered, parseInt(params?.page || '1'), 25);
  },

  // Scheduler
  '/scheduler/status': () => mockSchedulerStatus,

  // Users
  '/users$': () => paginate(mockAppUsers, 1, 25),

  // Notifications
  '/notifications$': () => paginate(mockNotifications, 1, 25),

  // Audit Logs
  '/audit-logs$': () => paginate(mockAuditLogs, 1, 50),

  // Search
  '/search$': (params: any) => {
    const q = (params?.q || '').toLowerCase();
    const results = mockServers
      .filter(s => s.hostname.toLowerCase().includes(q) || s.ip_address.includes(q))
      .slice(0, 10)
      .map(s => ({
        id: s.id,
        type: "server",
        title: s.hostname,
        subtitle: `${s.os_family} - ${s.ip_address}`,
        match_field: "hostname",
        link: `/servers/${s.id}`,
      }));
    return { query: q, total_results: results.length, results };
  },

  // System status
  '/system/status': () => ({
    application: { name: "Linux Inventory Manager", version: "1.0.0", environment: "production", python_version: "3.12.4" },
    database: { url: "sqlite:///storage/inventory.db", status: "connected" },
    scheduler: { enabled: true, max_concurrent: 20, collection_hour: 2, retry_interval_minutes: 60 },
    storage: { disk_total_gb: 100, disk_used_gb: 28.5, disk_free_gb: 71.5, disk_usage_percent: 28.5, snapshots_size_mb: 245, logs_size_mb: 82, reports_size_mb: 15 },
  }),

  // Health
  '/health$': () => ({ status: "healthy", service: "linux-inventory-manager", version: "1.0.0" }),

  // Credential profiles
  '/credential-profiles$': () => paginate(mockCredentialProfiles, 1, 25),

  // Reports (empty - generate returns 202)
  '/reports$': () => paginate([], 1, 25),
};

/**
 * Find a matching mock handler for a given path.
 */
function findHandler(path: string): ((params?: any) => any) | null {
  for (const [pattern, handler] of Object.entries(mockHandlers)) {
    if (new RegExp(pattern).test(path)) {
      return handler;
    }
  }
  return null;
}

/**
 * Setup mock API interceptor on the axios instance.
 * Call this in main.tsx when VITE_USE_MOCKS=true.
 */
export function setupMockApi(apiClient: any): void {
  apiClient.interceptors.request.use(async (config: any) => {
    const path = config.url || '';
    const handler = findHandler(path);

    if (handler) {
      await delay(200 + Math.random() * 300); // Realistic delay
      const params = config.params || {};
      const data = handler(params);

      // Return mock response by throwing a "fulfilled" adapter response
      return Promise.reject({
        __MOCK__: true,
        config,
        response: {
          status: 200,
          data,
          headers: {},
          config,
        },
      });
    }

    return config;
  });

  // Catch mock responses and resolve them
  apiClient.interceptors.response.use(
    (response: any) => response,
    (error: any) => {
      if (error?.__MOCK__) {
        return Promise.resolve(error.response);
      }
      return Promise.reject(error);
    }
  );

  console.log('%c[MOCK API] Mock data enabled - no backend required', 'color: #4caf50; font-weight: bold');
}
