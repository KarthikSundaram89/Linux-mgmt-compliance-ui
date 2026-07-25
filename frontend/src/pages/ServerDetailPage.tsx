/**
 * Server Detail Page
 * ==================
 * Tabbed view with all 12 collector sections, collection history,
 * detected changes, snapshots, and audit trail.
 */
import React, { useEffect, useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import {
  Box, Tabs, Tab, Card, CardContent, Typography, Chip, Grid,
  Table, TableBody, TableCell, TableContainer, TableHead, TableRow,
  Paper, Button, Stack, IconButton, Tooltip, Divider,
} from '@mui/material';
import {
  Computer, People, VpnKey, Storage, Settings as SettingsIcon,
  Schedule, NetworkCheck, Security, Timer, History, ChangeCircle,
  CameraAlt, PlayArrow, Refresh, ArrowBack,
} from '@mui/icons-material';
import PageHeader from '../components/common/PageHeader';
import LoadingState from '../components/common/LoadingState';
import { serverService } from '../services/serverService';
import { Server } from '../types';

interface TabPanelProps { children?: React.ReactNode; index: number; value: number; }
const TabPanel: React.FC<TabPanelProps> = ({ children, value, index }) => (
  <Box role="tabpanel" hidden={value !== index} sx={{ pt: 2 }}>
    {value === index && children}
  </Box>
);

// Info row helper
const InfoRow: React.FC<{ label: string; value: string | React.ReactNode }> = ({ label, value }) => (
  <Box display="flex" py={0.5}>
    <Typography variant="body2" color="text.secondary" sx={{ minWidth: 200 }}>{label}</Typography>
    <Typography variant="body2">{value || '—'}</Typography>
  </Box>
);

const ServerDetailPage: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const [server, setServer] = useState<Server | null>(null);
  const [loading, setLoading] = useState(true);
  const [tab, setTab] = useState(0);

  useEffect(() => {
    if (!id) return;
    setLoading(true);
    serverService.getById(id).then(setServer).catch(() => {}).finally(() => setLoading(false));
  }, [id]);

  return (
    <Box>
      <PageHeader
        title={server?.hostname || 'Server Details'}
        subtitle={server ? `${server.ip_address} • ${server.environment} • ${server.os_family || 'Unknown OS'}` : ''}
        breadcrumbs={[
          { label: 'Servers', href: '/servers' },
          { label: server?.hostname || '...' },
        ]}
        actions={
          <Stack direction="row" spacing={1}>
            <Button variant="outlined" startIcon={<PlayArrow />} size="small">Collect Now</Button>
            <Button variant="outlined" startIcon={<Refresh />} size="small">Retry</Button>
          </Stack>
        }
      />

      <LoadingState loading={loading} error={null} empty={!server && !loading} emptyMessage="Server not found">
        {server && (
          <>
            {/* Status bar */}
            <Box display="flex" gap={2} mb={2} alignItems="center">
              <Chip
                label={server.last_collection_status || 'pending'}
                color={server.last_collection_status === 'success' ? 'success' : server.last_collection_status === 'failed' ? 'error' : 'default'}
              />
              <Typography variant="body2" color="text.secondary">
                Last collected: {server.last_collection_at ? new Date(server.last_collection_at).toLocaleString() : 'Never'}
              </Typography>
              <Chip label={server.is_active ? 'Active' : 'Disabled'} variant="outlined" size="small" color={server.is_active ? 'success' : 'default'} />
            </Box>

            {/* Tabs */}
            <Box sx={{ borderBottom: 1, borderColor: 'divider' }}>
              <Tabs value={tab} onChange={(_, v) => setTab(v)} variant="scrollable" scrollButtons="auto">
                <Tab icon={<Computer />} label="Overview" iconPosition="start" />
                <Tab icon={<People />} label="Users" iconPosition="start" />
                <Tab icon={<VpnKey />} label="Sudo" iconPosition="start" />
                <Tab icon={<Storage />} label="Packages" iconPosition="start" />
                <Tab icon={<SettingsIcon />} label="Services" iconPosition="start" />
                <Tab icon={<Storage />} label="Filesystem" iconPosition="start" />
                <Tab icon={<Schedule />} label="Chrony" iconPosition="start" />
                <Tab icon={<NetworkCheck />} label="Network" iconPosition="start" />
                <Tab icon={<Security />} label="SSH Config" iconPosition="start" />
                <Tab icon={<Timer />} label="Cron" iconPosition="start" />
                <Tab icon={<Security />} label="Password Policy" iconPosition="start" />
                <Tab icon={<History />} label="Collections" iconPosition="start" />
                <Tab icon={<ChangeCircle />} label="Changes" iconPosition="start" />
                <Tab icon={<CameraAlt />} label="Snapshots" iconPosition="start" />
              </Tabs>
            </Box>

            {/* Overview Tab */}
            <TabPanel value={tab} index={0}>
              <Grid container spacing={3}>
                <Grid item xs={12} md={6}>
                  <Card>
                    <CardContent>
                      <Typography variant="h6" gutterBottom>System Information</Typography>
                      <InfoRow label="Hostname" value={server.hostname} />
                      <InfoRow label="IP Address" value={server.ip_address} />
                      <InfoRow label="OS Family" value={server.os_family || '—'} />
                      <InfoRow label="OS Version" value={server.os_version || '—'} />
                      <InfoRow label="Environment" value={server.environment} />
                      <InfoRow label="Location" value={server.location || '—'} />
                      <InfoRow label="Tags" value={server.tags || '—'} />
                    </CardContent>
                  </Card>
                </Grid>
                <Grid item xs={12} md={6}>
                  <Card>
                    <CardContent>
                      <Typography variant="h6" gutterBottom>Collection Status</Typography>
                      <InfoRow label="Status" value={<Chip label={server.last_collection_status || 'pending'} size="small" color={server.last_collection_status === 'success' ? 'success' : 'error'} />} />
                      <InfoRow label="Last Collection" value={server.last_collection_at ? new Date(server.last_collection_at).toLocaleString() : 'Never'} />
                      <InfoRow label="Collection Active" value={server.is_active ? 'Yes' : 'No'} />
                      <InfoRow label="SSH Port" value={String(server.port || 22)} />
                      <InfoRow label="Created" value={new Date(server.created_at).toLocaleString()} />
                    </CardContent>
                  </Card>
                </Grid>
              </Grid>
            </TabPanel>

            {/* Users Tab */}
            <TabPanel value={tab} index={1}>
              <Card><CardContent>
                <Typography variant="h6" gutterBottom>User Accounts</Typography>
                <Typography variant="body2" color="text.secondary">
                  User inventory data from the most recent collection. Shows non-system users with password aging, group membership, and SSH key status.
                </Typography>
                <TableContainer component={Paper} sx={{ mt: 2 }}>
                  <Table size="small">
                    <TableHead>
                      <TableRow>
                        <TableCell>Username</TableCell>
                        <TableCell>UID</TableCell>
                        <TableCell>Primary Group</TableCell>
                        <TableCell>Shell</TableCell>
                        <TableCell>Status</TableCell>
                        <TableCell>SSH Keys</TableCell>
                      </TableRow>
                    </TableHead>
                    <TableBody>
                      <TableRow><TableCell colSpan={6} align="center"><Typography variant="body2" color="text.secondary">Load snapshot data to view users</Typography></TableCell></TableRow>
                    </TableBody>
                  </Table>
                </TableContainer>
              </CardContent></Card>
            </TabPanel>

            {/* Sudo Tab */}
            <TabPanel value={tab} index={2}>
              <Card><CardContent>
                <Typography variant="h6" gutterBottom>Sudo Configuration</Typography>
                <Typography variant="body2" color="text.secondary">Privileged users, sudoers rules, NOPASSWD entries, and potential conflicts.</Typography>
              </CardContent></Card>
            </TabPanel>

            {/* Packages Tab */}
            <TabPanel value={tab} index={3}>
              <Card><CardContent>
                <Typography variant="h6" gutterBottom>Installed Packages</Typography>
                <Typography variant="body2" color="text.secondary">Complete package inventory with version tracking and change history.</Typography>
              </CardContent></Card>
            </TabPanel>

            {/* Services Tab */}
            <TabPanel value={tab} index={4}>
              <Card><CardContent>
                <Typography variant="h6" gutterBottom>Systemd Services</Typography>
                <Typography variant="body2" color="text.secondary">All systemd services with running/enabled status. Failed services are highlighted.</Typography>
              </CardContent></Card>
            </TabPanel>

            {/* Filesystem Tab */}
            <TabPanel value={tab} index={5}>
              <Card><CardContent>
                <Typography variant="h6" gutterBottom>Filesystem Inventory</Typography>
                <Typography variant="body2" color="text.secondary">Mounted filesystems with capacity, usage, NFS/SMB mounts, and mount options.</Typography>
              </CardContent></Card>
            </TabPanel>

            {/* Chrony Tab */}
            <TabPanel value={tab} index={6}>
              <Card><CardContent>
                <Typography variant="h6" gutterBottom>Time Synchronization (Chrony)</Typography>
                <Typography variant="body2" color="text.secondary">NTP synchronization status, time sources, offset, and stratum information.</Typography>
              </CardContent></Card>
            </TabPanel>

            {/* Network Tab */}
            <TabPanel value={tab} index={7}>
              <Card><CardContent>
                <Typography variant="h6" gutterBottom>Network Identity</Typography>
                <Typography variant="body2" color="text.secondary">DNS servers, interfaces, IP addresses, default gateway, and routing.</Typography>
              </CardContent></Card>
            </TabPanel>

            {/* SSH Config Tab */}
            <TabPanel value={tab} index={8}>
              <Card><CardContent>
                <Typography variant="h6" gutterBottom>SSH Configuration</Typography>
                <Typography variant="body2" color="text.secondary">SSH daemon security settings and configuration audit results.</Typography>
              </CardContent></Card>
            </TabPanel>

            {/* Cron Tab */}
            <TabPanel value={tab} index={9}>
              <Card><CardContent>
                <Typography variant="h6" gutterBottom>Scheduled Tasks</Typography>
                <Typography variant="body2" color="text.secondary">System cron jobs, user crontabs, and systemd timers.</Typography>
              </CardContent></Card>
            </TabPanel>

            {/* Password Policy Tab */}
            <TabPanel value={tab} index={10}>
              <Card><CardContent>
                <Typography variant="h6" gutterBottom>Password Policy</Typography>
                <Typography variant="body2" color="text.secondary">Global password policies, PAM configuration, lockout settings, and compliance issues.</Typography>
              </CardContent></Card>
            </TabPanel>

            {/* Collections Tab */}
            <TabPanel value={tab} index={11}>
              <Card><CardContent>
                <Typography variant="h6" gutterBottom>Collection History</Typography>
                <Typography variant="body2" color="text.secondary">All collection runs with timing, status, and collector details.</Typography>
              </CardContent></Card>
            </TabPanel>

            {/* Changes Tab */}
            <TabPanel value={tab} index={12}>
              <Card><CardContent>
                <Typography variant="h6" gutterBottom>Detected Changes</Typography>
                <Typography variant="body2" color="text.secondary">All changes detected between consecutive snapshots.</Typography>
              </CardContent></Card>
            </TabPanel>

            {/* Snapshots Tab */}
            <TabPanel value={tab} index={13}>
              <Card><CardContent>
                <Typography variant="h6" gutterBottom>Inventory Snapshots</Typography>
                <Typography variant="body2" color="text.secondary">Historical snapshots with download, comparison, and raw JSON viewing capabilities.</Typography>
              </CardContent></Card>
            </TabPanel>
          </>
        )}
      </LoadingState>
    </Box>
  );
};

export default ServerDetailPage;
