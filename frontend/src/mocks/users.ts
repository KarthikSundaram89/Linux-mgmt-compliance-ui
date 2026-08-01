/**
 * Mock user and role data for admin pages.
 */

export const mockAppUsers = [
  { id: "u-001", username: "admin", email: "admin@company.com", full_name: "System Administrator", role: "admin", is_active: true, is_locked: false, auth_provider: "local", last_login_at: "2026-07-25T08:30:00Z", created_at: "2025-01-01T00:00:00Z" },
  { id: "u-002", username: "jdoe", email: "jdoe@company.com", full_name: "John Doe", role: "operator", is_active: true, is_locked: false, auth_provider: "local", last_login_at: "2026-07-25T09:15:00Z", created_at: "2025-03-15T10:00:00Z" },
  { id: "u-003", username: "asmith", email: "asmith@company.com", full_name: "Alice Smith", role: "operator", is_active: true, is_locked: false, auth_provider: "local", last_login_at: "2026-07-24T16:00:00Z", created_at: "2025-03-15T10:00:00Z" },
  { id: "u-004", username: "bwilson", email: "bwilson@company.com", full_name: "Bob Wilson", role: "readonly", is_active: true, is_locked: false, auth_provider: "local", last_login_at: "2026-07-23T11:00:00Z", created_at: "2025-06-01T09:00:00Z" },
  { id: "u-005", username: "security-audit", email: "audit@company.com", full_name: "Security Auditor", role: "readonly", is_active: true, is_locked: false, auth_provider: "local", last_login_at: "2026-07-20T14:00:00Z", created_at: "2025-09-01T08:00:00Z" },
  { id: "u-006", username: "former-emp", email: "former@company.com", full_name: "Former Employee", role: "operator", is_active: false, is_locked: true, auth_provider: "local", last_login_at: "2026-05-01T10:00:00Z", created_at: "2025-01-15T10:00:00Z" },
];

export const mockRoles = [
  { id: "r-001", name: "admin", description: "Full system access. Can manage users, servers, credentials, and all settings.", user_count: 1 },
  { id: "r-002", name: "operator", description: "Can view inventory, trigger collections, export reports. Cannot manage users or secrets.", user_count: 3 },
  { id: "r-003", name: "readonly", description: "View-only access to dashboards, inventory, and reports. Cannot modify anything.", user_count: 2 },
];

export const mockCredentialProfiles = [
  { id: "cp-prod", name: "Production Linux", description: "SSH access to all production Linux servers", ssh_username: "ec2-user", ssh_port: 22, connection_timeout: 30, command_timeout: 60, max_retries: 3, is_active: true, server_count: 285 },
  { id: "cp-staging", name: "Staging Linux", description: "SSH access to staging environment", ssh_username: "ec2-user", ssh_port: 22, connection_timeout: 30, command_timeout: 60, max_retries: 3, is_active: true, server_count: 65 },
  { id: "cp-dev", name: "Development Linux", description: "SSH access to development servers", ssh_username: "ubuntu", ssh_port: 22, connection_timeout: 15, command_timeout: 30, max_retries: 2, is_active: true, server_count: 42 },
  { id: "cp-dmz", name: "DMZ Servers", description: "SSH access to DMZ/perimeter servers", ssh_username: "admin", ssh_port: 2222, connection_timeout: 45, command_timeout: 90, max_retries: 5, is_active: true, server_count: 20 },
];
