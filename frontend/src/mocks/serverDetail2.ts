/**
 * Additional mock data for server detail page tabs.
 */

export const mockPackages = [
  { name: "bash", version: "5.1.8", release: "9.el8", architecture: "x86_64", vendor: "Red Hat, Inc.", install_date: "2026-01-15" },
  { name: "openssl", version: "3.0.8", release: "1.el8", architecture: "x86_64", vendor: "Red Hat, Inc.", install_date: "2026-07-20" },
  { name: "kernel", version: "4.18.0", release: "513.24.1.el8_9", architecture: "x86_64", vendor: "Red Hat, Inc.", install_date: "2026-07-01" },
  { name: "nodejs", version: "20.11.1", release: "1.module+el8", architecture: "x86_64", vendor: "Red Hat, Inc.", install_date: "2026-04-10" },
  { name: "nginx", version: "1.24.0", release: "3.el8", architecture: "x86_64", vendor: "Red Hat, Inc.", install_date: "2026-03-05" },
  { name: "git", version: "2.43.0", release: "1.el8", architecture: "x86_64", vendor: "Red Hat, Inc.", install_date: "2026-02-20" },
  { name: "python3", version: "3.12.2", release: "1.el8", architecture: "x86_64", vendor: "Red Hat, Inc.", install_date: "2026-05-01" },
  { name: "curl", version: "8.6.0", release: "1.el8", architecture: "x86_64", vendor: "Red Hat, Inc.", install_date: "2026-06-15" },
  { name: "vim-enhanced", version: "9.0.2081", release: "1.el8", architecture: "x86_64", vendor: "Red Hat, Inc.", install_date: "2026-01-15" },
  { name: "docker-ce", version: "24.0.7", release: "1.el8", architecture: "x86_64", vendor: "Docker Inc.", install_date: "2026-04-20" },
];

export const mockServices = [
  { name: "sshd.service", description: "OpenSSH server daemon", active_state: "active", sub_state: "running", enabled: "enabled", is_failed: false },
  { name: "nginx.service", description: "The nginx HTTP and reverse proxy server", active_state: "active", sub_state: "running", enabled: "enabled", is_failed: false },
  { name: "chronyd.service", description: "NTP client/server", active_state: "active", sub_state: "running", enabled: "enabled", is_failed: false },
  { name: "docker.service", description: "Docker Application Container Engine", active_state: "active", sub_state: "running", enabled: "enabled", is_failed: false },
  { name: "node-app.service", description: "Node.js Production Application", active_state: "active", sub_state: "running", enabled: "enabled", is_failed: false },
  { name: "firewalld.service", description: "firewalld - dynamic firewall daemon", active_state: "active", sub_state: "running", enabled: "enabled", is_failed: false },
  { name: "rsyslog.service", description: "System Logging Service", active_state: "active", sub_state: "running", enabled: "enabled", is_failed: false },
  { name: "crond.service", description: "Command Scheduler", active_state: "active", sub_state: "running", enabled: "enabled", is_failed: false },
  { name: "postfix.service", description: "Postfix Mail Transport Agent", active_state: "inactive", sub_state: "dead", enabled: "disabled", is_failed: false },
  { name: "kdump.service", description: "Kernel crash dump mechanism", active_state: "failed", sub_state: "failed", enabled: "enabled", is_failed: true },
];

export const mockFilesystems = [
  { mount_point: "/", filesystem_type: "xfs", device: "/dev/nvme0n1p1", capacity_kb: 104857600, used_kb: 31457280, free_kb: 73400320, usage_percent: 30, mount_options: "rw,relatime", read_only: false, is_network: false },
  { mount_point: "/var", filesystem_type: "xfs", device: "/dev/nvme1n1", capacity_kb: 52428800, used_kb: 15728640, free_kb: 36700160, usage_percent: 30, mount_options: "rw,nodev,nosuid", read_only: false, is_network: false },
  { mount_point: "/home", filesystem_type: "xfs", device: "/dev/nvme2n1", capacity_kb: 20971520, used_kb: 2097152, free_kb: 18874368, usage_percent: 10, mount_options: "rw,nodev,nosuid", read_only: false, is_network: false },
  { mount_point: "/tmp", filesystem_type: "tmpfs", device: "tmpfs", capacity_kb: 2097152, used_kb: 10240, free_kb: 2086912, usage_percent: 1, mount_options: "rw,nosuid,nodev,noexec", read_only: false, is_network: false },
  { mount_point: "/shared/logs", filesystem_type: "nfs4", device: "nfs-prod-01:/export/logs", capacity_kb: 524288000, used_kb: 209715200, free_kb: 314572800, usage_percent: 40, mount_options: "rw,hard,intr", read_only: false, is_network: true, remote_server: "nfs-prod-01" },
  { mount_point: "/backup", filesystem_type: "nfs4", device: "nfs-prod-01:/export/backup", capacity_kb: 1048576000, used_kb: 629145600, free_kb: 419430400, usage_percent: 60, mount_options: "rw,soft", read_only: false, is_network: true, remote_server: "nfs-prod-01" },
];

export const mockChrony = {
  installed: true,
  service_running: true,
  service_enabled: true,
  synchronized: true,
  tracking: {
    reference_id: "A9FEA9FE (169.254.169.254)",
    stratum: "4",
    system_time: "0.000000123 seconds fast of NTP time",
    last_offset: "+0.000000234 seconds",
    rms_offset: "0.000000456 seconds",
    frequency: "-0.123 ppm slow",
    leap_status: "Normal",
  },
  sources: [
    { mode: "*", name: "169.254.169.123", stratum: "3", poll: "6", reach: "377" },
    { mode: "+", name: "time.aws.com", stratum: "3", poll: "6", reach: "377" },
  ],
};

export const mockSSHConfig = {
  version: "OpenSSH_8.7p1, OpenSSL 3.0.8 7 Feb 2023",
  service_running: true,
  service_enabled: true,
  config: {
    permitrootlogin: "prohibit-password",
    passwordauthentication: "no",
    pubkeyauthentication: "yes",
    maxauthtries: "3",
    clientaliveinterval: "300",
    clientalivecountmax: "3",
    x11forwarding: "no",
    permitemptypasswords: "no",
    logingracetime: "60",
  },
  security_issues: [],
};

export const mockCollectionHistory = [
  { id: "col-001", started_at: "2026-07-25T02:14:00Z", completed_at: "2026-07-25T02:15:30Z", duration_seconds: 90, status: "success", retry_count: 0, triggered_by: "scheduler", collectors_run: 12, collectors_failed: 0 },
  { id: "col-002", started_at: "2026-07-24T02:14:00Z", completed_at: "2026-07-24T02:15:20Z", duration_seconds: 80, status: "success", retry_count: 0, triggered_by: "scheduler", collectors_run: 12, collectors_failed: 0 },
  { id: "col-003", started_at: "2026-07-23T02:14:00Z", completed_at: "2026-07-23T02:15:45Z", duration_seconds: 105, status: "success", retry_count: 0, triggered_by: "scheduler", collectors_run: 12, collectors_failed: 1 },
  { id: "col-004", started_at: "2026-07-22T02:14:00Z", completed_at: "2026-07-22T02:15:10Z", duration_seconds: 70, status: "success", retry_count: 0, triggered_by: "scheduler", collectors_run: 12, collectors_failed: 0 },
  { id: "col-005", started_at: "2026-07-21T14:00:00Z", completed_at: "2026-07-21T14:01:25Z", duration_seconds: 85, status: "success", retry_count: 0, triggered_by: "manual", collectors_run: 12, collectors_failed: 0 },
];
