/**
 * Mock server detail data — full snapshot for web-prod-01.
 */

export const mockServerDetail = {
  id: "s-001",
  hostname: "web-prod-01.us-east-1.internal",
  ip_address: "10.0.1.10",
  port: 22,
  environment: "production",
  os_family: "rhel",
  os_version: "8.9",
  last_collection_at: "2026-07-25T02:15:30Z",
  last_collection_status: "success",
  is_active: true,
  tags: "web,frontend,nodejs",
};

export const mockOsData = {
  hostname: "web-prod-01",
  fqdn: "web-prod-01.us-east-1.internal",
  distribution: "rhel",
  distribution_version: "8.9",
  pretty_name: "Red Hat Enterprise Linux 8.9 (Ootpa)",
  kernel_release: "4.18.0-513.24.1.el8_9.x86_64",
  kernel_version: "4.18.0",
  architecture: "x86-64",
  machine_type: "x86_64",
  virtualization_type: "kvm",
  virtualization_vendor: "Amazon EC2",
  timezone: "America/New_York",
  current_time: "2026-07-25T02:15:30-0400",
  last_boot_time: "2026-07-01 03:15:22",
  uptime_seconds: 2073930,
  boot_id: "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
  reboot_pending: false,
};

export const mockUsers = [
  { username: "root", uid: 0, gid: 0, primary_group: "root", secondary_groups: [], home_directory: "/root", login_shell: "/bin/bash", account_status: "active", account_locked: false, password_expired: false, password_last_changed: "19650", last_login: "2026-07-24 14:30:00", ssh_authorized_keys_present: true },
  { username: "jdoe", uid: 1001, gid: 1001, primary_group: "jdoe", secondary_groups: ["wheel", "docker", "users"], home_directory: "/home/jdoe", login_shell: "/bin/bash", account_status: "active", account_locked: false, password_expired: false, password_last_changed: "19700", last_login: "2026-07-25 09:15:00", ssh_authorized_keys_present: true },
  { username: "asmith", uid: 1002, gid: 1002, primary_group: "asmith", secondary_groups: ["users", "developers"], home_directory: "/home/asmith", login_shell: "/bin/bash", account_status: "active", account_locked: false, password_expired: false, password_last_changed: "19690", last_login: "2026-07-24 16:00:00", ssh_authorized_keys_present: true },
  { username: "deploy", uid: 1003, gid: 1003, primary_group: "deploy", secondary_groups: ["docker"], home_directory: "/home/deploy", login_shell: "/bin/bash", account_status: "active", account_locked: false, password_expired: false, password_last_changed: "19600", last_login: "Never", ssh_authorized_keys_present: true },
  { username: "monitoring", uid: 1004, gid: 1004, primary_group: "monitoring", secondary_groups: [], home_directory: "/home/monitoring", login_shell: "/sbin/nologin", account_status: "active", account_locked: false, password_expired: false, password_last_changed: "19500", last_login: "Never", ssh_authorized_keys_present: false },
];
