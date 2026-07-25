/**
 * Core type definitions for the application.
 * Mirrors backend Pydantic schemas for type safety.
 */

// ─── Server Types ──────────────────────────────────────────────

export interface Server {
  id: string;
  hostname: string;
  ip_address: string;
  port: number | null;
  description: string | null;
  environment: string;
  location: string | null;
  os_family: string | null;
  os_version: string | null;
  credential_profile_id: string;
  is_active: boolean;
  last_collection_at: string | null;
  last_collection_status: string | null;
  tags: string | null;
  created_at: string;
  updated_at: string;
}

export interface ServerCreate {
  hostname: string;
  ip_address: string;
  port?: number;
  description?: string;
  environment: string;
  location?: string;
  credential_profile_id: string;
  tags?: string;
}

// ─── Collection Types ──────────────────────────────────────────

export interface Collection {
  id: string;
  server_id: string;
  status: 'pending' | 'in_progress' | 'success' | 'failed';
  started_at: string | null;
  completed_at: string | null;
  duration_seconds: number | null;
  error_message: string | null;
  retry_count: number;
  triggered_by: string;
  created_at: string;
}

// ─── Change Types ──────────────────────────────────────────────

export interface ChangeRecord {
  id: string;
  server_id: string;
  category: string;
  change_type: 'added' | 'removed' | 'modified';
  field_name: string;
  old_value: string | null;
  new_value: string | null;
  severity: 'info' | 'warning' | 'critical';
  detected_at: string;
  acknowledged: boolean;
  acknowledged_by: string | null;
}

// ─── Credential Profile Types ──────────────────────────────────

export interface CredentialProfile {
  id: string;
  name: string;
  description: string | null;
  ssh_username: string;
  ssh_port: number;
  connection_timeout: number;
  command_timeout: number;
  max_retries: number;
  retry_delay_seconds: number;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

// ─── Auth Types ────────────────────────────────────────────────

export interface User {
  id: string;
  username: string;
  email: string;
  full_name: string;
  role: string | null;
  last_login_at: string | null;
}

export interface LoginCredentials {
  username: string;
  password: string;
}

export interface TokenResponse {
  access_token: string;
  refresh_token: string;
  token_type: string;
  expires_in: number;
}

// ─── Dashboard Types ───────────────────────────────────────────

export interface DashboardStats {
  total_servers: number;
  active_servers: number;
  servers_online: number;
  servers_failed: number;
  total_collections_today: number;
  total_changes_today: number;
  critical_changes: number;
  pending_notifications: number;
}

// ─── Pagination Types ──────────────────────────────────────────

export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  page: number;
  page_size: number;
  total_pages: number;
  has_next: boolean;
  has_previous: boolean;
}

// ─── Notification Types ────────────────────────────────────────

export interface Notification {
  id: string;
  title: string;
  message: string;
  severity: 'info' | 'warning' | 'error' | 'critical';
  category: string;
  is_read: boolean;
  created_at: string;
}

// ─── Scheduler Types ───────────────────────────────────────────

export interface SchedulerStatus {
  state: 'running' | 'paused' | 'stopped';
  jobs: SchedulerJob[];
  last_collection_time: string | null;
  last_retry_time: string | null;
  max_concurrent: number;
}

export interface SchedulerJob {
  id: string;
  name: string;
  next_run_time: string;
  trigger: string;
}
