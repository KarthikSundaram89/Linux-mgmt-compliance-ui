/**
 * Mock notifications and scheduler status.
 */

export const mockNotifications = [
  { id: "n-001", title: "Collection failed: legacy-app-01", message: "SSH Connection Timeout after 30 seconds. Server may be offline or firewall is blocking port 22.", severity: "error", category: "collection", is_read: false, created_at: "2026-07-25T02:16:00Z" },
  { id: "n-002", title: "Critical change: db-prod-03", message: "Service mysqld.service entered failed state. Immediate investigation recommended.", severity: "critical", category: "change", is_read: false, created_at: "2026-07-25T02:18:00Z" },
  { id: "n-003", title: "Time sync lost: nfs-prod-01", message: "Chrony reports NOT synchronized. NTP sources unreachable. Time drift may affect log correlation.", severity: "critical", category: "change", is_read: false, created_at: "2026-07-25T02:20:10Z" },
  { id: "n-004", title: "New user detected: api-staging-02", message: "User 'deploy-bot' (UID 1005) was added. Verify this is an authorized change.", severity: "warning", category: "change", is_read: false, created_at: "2026-07-25T02:20:00Z" },
  { id: "n-005", title: "Sudo granted: bastion-prod-01", message: "Group 'ops-team' received sudo access. Review sudoers.d configuration.", severity: "warning", category: "change", is_read: true, created_at: "2026-07-25T02:11:30Z" },
  { id: "n-006", title: "Kernel updated: web-prod-05", message: "Kernel changed from 4.18.0-477 to 4.18.0-513.24.1. Reboot may be required.", severity: "info", category: "change", is_read: true, created_at: "2026-07-25T02:14:00Z" },
  { id: "n-007", title: "Daily collection complete", message: "Collected 404/412 servers successfully. 8 failures queued for retry.", severity: "info", category: "system", is_read: true, created_at: "2026-07-25T02:30:00Z" },
  { id: "n-008", title: "Host key mismatch: batch-prod-02", message: "SSH host key does not match known_hosts. Possible security incident or server rebuild.", severity: "error", category: "collection", is_read: false, created_at: "2026-07-24T19:00:00Z" },
  { id: "n-009", title: "Snapshot cleanup completed", message: "Removed 142 snapshots older than 365 days. Freed 8.2 GB disk space.", severity: "info", category: "system", is_read: true, created_at: "2026-07-25T01:00:00Z" },
  { id: "n-010", title: "Report generated: weekly compliance", message: "Weekly compliance report (PDF) is ready for download.", severity: "info", category: "system", is_read: true, created_at: "2026-07-24T06:00:00Z" },
];

export const mockSchedulerStatus = {
  state: "running",
  jobs: [
    { id: "daily_collection", name: "Daily Server Collection", next_run_time: "2026-07-26T02:00:00Z", trigger: "cron[hour=2, minute=0]" },
    { id: "retry_failed_collections", name: "Retry Failed Collections", next_run_time: "2026-07-25T03:00:00Z", trigger: "interval[1:00:00]" },
  ],
  last_collection_time: "2026-07-25T02:00:00Z",
  last_retry_time: "2026-07-25T03:00:00Z",
  max_concurrent: 20,
};

export const mockAuditLogs = [
  { id: "a-001", timestamp: "2026-07-25T09:15:00Z", user_id: "u-002", username: "jdoe", action: "login", resource_type: null, resource_id: null, status: "success", ip_address: "10.0.0.50" },
  { id: "a-002", timestamp: "2026-07-25T09:16:30Z", user_id: "u-002", username: "jdoe", action: "trigger_collection", resource_type: "server", resource_id: "s-001", status: "success", ip_address: "10.0.0.50" },
  { id: "a-003", timestamp: "2026-07-25T08:30:00Z", user_id: "u-001", username: "admin", action: "login", resource_type: null, resource_id: null, status: "success", ip_address: "10.0.0.100" },
  { id: "a-004", timestamp: "2026-07-25T08:35:00Z", user_id: "u-001", username: "admin", action: "update_setting", resource_type: "setting", resource_id: "scheduler_max_concurrent", status: "success", ip_address: "10.0.0.100" },
  { id: "a-005", timestamp: "2026-07-25T07:00:00Z", user_id: null, username: "system", action: "scheduler_collection_start", resource_type: "scheduler", resource_id: null, status: "success", ip_address: null },
  { id: "a-006", timestamp: "2026-07-25T07:18:00Z", user_id: null, username: "system", action: "scheduler_collection_complete", resource_type: "scheduler", resource_id: null, status: "success", ip_address: null },
  { id: "a-007", timestamp: "2026-07-24T22:00:00Z", user_id: "u-006", username: "former-emp", action: "login", resource_type: null, resource_id: null, status: "failure", ip_address: "192.168.1.50" },
  { id: "a-008", timestamp: "2026-07-24T16:00:00Z", user_id: "u-003", username: "asmith", action: "generate_report", resource_type: "report", resource_id: "compliance_2026-07-24", status: "success", ip_address: "10.0.0.51" },
  { id: "a-009", timestamp: "2026-07-24T14:00:00Z", user_id: "u-001", username: "admin", action: "create_user", resource_type: "user", resource_id: "u-005", status: "success", ip_address: "10.0.0.100" },
  { id: "a-010", timestamp: "2026-07-24T10:00:00Z", user_id: "u-001", username: "admin", action: "unlock_user", resource_type: "user", resource_id: "u-006", status: "success", ip_address: "10.0.0.100" },
];
