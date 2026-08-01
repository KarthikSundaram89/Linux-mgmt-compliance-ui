/**
 * Mock dashboard statistics for UI visualization.
 */

export const mockDashboardStats = {
  total_servers: 412,
  active_servers: 398,
  servers_online: 396,
  servers_failed: 8,
  total_collections_today: 404,
  total_changes_today: 47,
  critical_changes: 3,
  pending_notifications: 12,
  pending_retry: 8,
  never_collected: 6,
};

export const mockOsDistribution = {
  labels: ["RHEL", "Amazon Linux", "Ubuntu", "Rocky", "Debian", "Oracle", "Kali", "CentOS"],
  data: [142, 98, 72, 38, 28, 18, 8, 8],
  colors: ["#cc0000", "#ff9900", "#e95420", "#10b981", "#a855f7", "#ef4444", "#557c94", "#932279"],
};

export const mockKernelDistribution = [
  { version: "5.14.0-362.24.1.el9", count: 98 },
  { version: "4.18.0-513.24.1.el8", count: 85 },
  { version: "6.1.0-21-cloud-amd64", count: 62 },
  { version: "5.15.0-91-generic", count: 52 },
  { version: "6.5.0-35-generic", count: 48 },
  { version: "5.10.205-195.807.amzn2", count: 38 },
  { version: "4.18.0-477.27.1.el8_8", count: 29 },
];

export const mockCollectionTrend = {
  labels: ["Mon 7/19", "Tue 7/20", "Wed 7/21", "Thu 7/22", "Fri 7/23", "Sat 7/24", "Sun 7/25"],
  successful: [392, 398, 395, 401, 399, 404, 396],
  failed: [20, 14, 17, 11, 13, 8, 16],
};

export const mockChangesByCategory = {
  labels: ["Packages", "Services", "Users", "Cron", "Filesystem", "SSH Config", "Kernel", "Chrony", "Sudo", "Password Policy"],
  data: [186, 42, 18, 15, 12, 8, 6, 5, 3, 2],
};

export const mockRecentChanges = [
  { id: "ch-001", server: "web-prod-01", hostname: "web-prod-01.us-east-1.internal", category: "packages", change_type: "upgraded", field: "openssl", old_value: "3.0.7-20.el8", new_value: "3.0.8-1.el8", severity: "info", detected_at: "2026-07-25T02:16:00Z" },
  { id: "ch-002", server: "db-prod-03", hostname: "db-prod-03.us-east-1.internal", category: "services", change_type: "failed", field: "mysqld.service", old_value: "running", new_value: "failed", severity: "critical", detected_at: "2026-07-25T02:18:00Z" },
  { id: "ch-003", server: "api-staging-02", hostname: "api-staging-02.us-east-1.internal", category: "users", change_type: "added", field: "deploy-bot", old_value: null, new_value: "UID=1005", severity: "warning", detected_at: "2026-07-25T02:20:00Z" },
  { id: "ch-004", server: "web-prod-05", hostname: "web-prod-05.us-east-1.internal", category: "operating_system", change_type: "kernel_changed", field: "kernel_release", old_value: "4.18.0-477.el8", new_value: "4.18.0-513.24.1.el8", severity: "warning", detected_at: "2026-07-25T02:14:00Z" },
  { id: "ch-005", server: "cache-prod-01", hostname: "cache-prod-01.us-east-1.internal", category: "filesystem", change_type: "mount_removed", field: "/shared/data", old_value: "nfs-server:/export/data", new_value: null, severity: "critical", detected_at: "2026-07-25T02:13:30Z" },
  { id: "ch-006", server: "jenkins-ci-01", hostname: "jenkins-ci-01.us-east-1.internal", category: "packages", change_type: "installed", field: "docker-ce", old_value: null, new_value: "24.0.7-1.el8", severity: "info", detected_at: "2026-07-25T02:19:10Z" },
  { id: "ch-007", server: "vault-prod-01", hostname: "vault-prod-01.us-east-1.internal", category: "ssh_config", change_type: "config_changed", field: "MaxAuthTries", old_value: "6", new_value: "3", severity: "info", detected_at: "2026-07-25T02:13:50Z" },
  { id: "ch-008", server: "bastion-prod-01", hostname: "bastion-prod-01.us-east-1.internal", category: "sudo", change_type: "granted", field: "ops-team", old_value: null, new_value: "sudo access granted", severity: "warning", detected_at: "2026-07-25T02:11:30Z" },
  { id: "ch-009", server: "nfs-prod-01", hostname: "nfs-prod-01.us-east-1.internal", category: "chrony", change_type: "sync_lost", field: "time_sync", old_value: "synchronized", new_value: "NOT synchronized", severity: "critical", detected_at: "2026-07-25T02:20:10Z" },
  { id: "ch-010", server: "elk-prod-01", hostname: "elk-prod-01.us-east-1.internal", category: "packages", change_type: "upgraded", field: "elasticsearch", old_value: "8.11.3", new_value: "8.12.0", severity: "info", detected_at: "2026-07-25T02:18:40Z" },
];

export const mockRecentFailures = [
  { server: "legacy-app-01", reason: "SSH Connection Timeout (30s exceeded)", time: "2 hours ago", retry_count: 3 },
  { server: "monitor-prod-01", reason: "Authentication Failed: invalid key", time: "3 hours ago", retry_count: 2 },
  { server: "batch-prod-02", reason: "Host Key Mismatch (security violation)", time: "5 hours ago", retry_count: 1 },
  { server: "dmz-proxy-01", reason: "Connection Refused (port 22 unreachable)", time: "8 hours ago", retry_count: 3 },
  { server: "dev-sandbox-03", reason: "Command Timeout: rpm -qa (60s exceeded)", time: "12 hours ago", retry_count: 1 },
  { server: "test-load-01", reason: "Server intentionally offline (maintenance)", time: "1 day ago", retry_count: 5 },
  { server: "legacy-win-bridge", reason: "Not a Linux server (detection failed)", time: "2 days ago", retry_count: 1 },
  { server: "decommissioned-04", reason: "No route to host", time: "3 days ago", retry_count: 3 },
];

export const mockTopChangingServers = [
  { hostname: "jenkins-ci-01", changes_7d: 42, category: "packages" },
  { hostname: "web-prod-01", changes_7d: 28, category: "packages" },
  { hostname: "app-dev-01", changes_7d: 24, category: "services" },
  { hostname: "elk-prod-01", changes_7d: 18, category: "packages" },
  { hostname: "api-staging-01", changes_7d: 15, category: "users" },
];
