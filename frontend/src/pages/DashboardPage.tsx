/**
 * Executive Dashboard
 * ===================
 * Displays KPI cards, charts for OS distribution, collection trends,
 * recent changes, and operational health metrics.
 */
import React, { useEffect, useState } from 'react';
import { Box, Grid, Card, CardContent, Typography, Divider, List, ListItem, ListItemText, Chip, IconButton, Tooltip } from '@mui/material';
import { Dns, CheckCircle, Error as ErrorIcon, ChangeCircle, Schedule, Replay, Warning, CloudOff, Refresh } from '@mui/icons-material';
import { Chart as ChartJS, ArcElement, CategoryScale, LinearScale, BarElement, LineElement, PointElement, Tooltip as ChartTooltip, Legend, Filler } from 'chart.js';
import { Doughnut, Bar, Line } from 'react-chartjs-2';
import { useNavigate } from 'react-router-dom';
import StatCard from '../components/common/StatCard';
import LoadingState from '../components/common/LoadingState';
import PageHeader from '../components/common/PageHeader';
import { dashboardService } from '../services/dashboardService';
import { DashboardStats } from '../types';

// Register Chart.js components
ChartJS.register(ArcElement, CategoryScale, LinearScale, BarElement, LineElement, PointElement, ChartTooltip, Legend, Filler);

const DashboardPage: React.FC = () => {
  const navigate = useNavigate();
  const [stats, setStats] = useState<DashboardStats | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const loadData = async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await dashboardService.getStats();
      setStats(data);
    } catch (err: any) {
      setError(err.message || 'Failed to load dashboard');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { loadData(); }, []);

  // Chart data - OS Distribution (Doughnut)
  const osDistributionData = {
    labels: ['RHEL', 'Amazon Linux', 'Ubuntu', 'Rocky', 'Debian', 'Oracle', 'Other'],
    datasets: [{
      data: [95, 78, 52, 35, 22, 15, 8],
      backgroundColor: ['#d32f2f', '#ff9800', '#e95420', '#10b981', '#a855f7', '#ef4444', '#6b7280'],
      borderWidth: 2,
      borderColor: 'transparent',
    }],
  };

  // Chart data - Collection Success Rate (Line)
  const collectionTrendData = {
    labels: ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'],
    datasets: [
      {
        label: 'Successful',
        data: [285, 290, 288, 295, 292, 298, 300],
        borderColor: '#2e7d32',
        backgroundColor: 'rgba(46, 125, 50, 0.1)',
        fill: true,
        tension: 0.4,
      },
      {
        label: 'Failed',
        data: [15, 10, 12, 5, 8, 2, 0],
        borderColor: '#d32f2f',
        backgroundColor: 'rgba(211, 47, 47, 0.1)',
        fill: true,
        tension: 0.4,
      },
    ],
  };

  // Chart data - Recent Changes by Category (Bar)
  const changesByCategoryData = {
    labels: ['Packages', 'Services', 'Users', 'Filesystem', 'Kernel', 'SSH Config', 'Cron'],
    datasets: [{
      label: 'Changes (7 days)',
      data: [142, 38, 12, 8, 5, 3, 15],
      backgroundColor: '#1976d2',
      borderRadius: 4,
    }],
  };

  // Chart data - Kernel Distribution (Bar horizontal)
  const kernelDistData = {
    labels: ['4.18.0-513', '5.14.0-362', '5.15.0-91', '6.1.0-18', '6.5.0-35', '4.18.0-477'],
    datasets: [{
      label: 'Server Count',
      data: [85, 72, 48, 42, 35, 23],
      backgroundColor: '#7c3aed',
      borderRadius: 4,
    }],
  };

  const chartOptions = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: { legend: { position: 'bottom' as const } },
  };

  const barOptions = {
    ...chartOptions,
    scales: { y: { beginAtZero: true } },
  };

  return (
    <Box>
      <PageHeader
        title="Dashboard"
        subtitle="Enterprise Linux Inventory & Compliance Overview"
        actions={
          <Tooltip title="Refresh">
            <IconButton onClick={loadData}><Refresh /></IconButton>
          </Tooltip>
        }
      />

      <LoadingState loading={loading} error={error} onRetry={loadData} empty={false}>
        {/* KPI Stat Cards */}
        <Grid container spacing={2} sx={{ mb: 3 }}>
          <Grid item xs={12} sm={6} md={3} lg={2.4}>
            <StatCard title="Total Servers" value={stats?.total_servers ?? 305} icon={<Dns fontSize="inherit" />} color="#1976d2" onClick={() => navigate('/servers')} />
          </Grid>
          <Grid item xs={12} sm={6} md={3} lg={2.4}>
            <StatCard title="Healthy" value={stats?.active_servers ?? 292} icon={<CheckCircle fontSize="inherit" />} color="#2e7d32" />
          </Grid>
          <Grid item xs={12} sm={6} md={3} lg={2.4}>
            <StatCard title="Failed" value={stats?.servers_failed ?? 8} icon={<ErrorIcon fontSize="inherit" />} color="#d32f2f" onClick={() => navigate('/servers?status=failed')} />
          </Grid>
          <Grid item xs={12} sm={6} md={3} lg={2.4}>
            <StatCard title="Changes Today" value={stats?.total_changes_today ?? 23} icon={<ChangeCircle fontSize="inherit" />} color="#ed6c02" onClick={() => navigate('/changes')} />
          </Grid>
          <Grid item xs={12} sm={6} md={3} lg={2.4}>
            <StatCard title="Pending Retry" value={5} icon={<Replay fontSize="inherit" />} color="#7c3aed" />
          </Grid>
        </Grid>

        {/* Charts Row 1 */}
        <Grid container spacing={3} sx={{ mb: 3 }}>
          <Grid item xs={12} md={4}>
            <Card>
              <CardContent>
                <Typography variant="h6" gutterBottom>OS Distribution</Typography>
                <Box sx={{ height: 260 }}>
                  <Doughnut data={osDistributionData} options={{ ...chartOptions, cutout: '60%' }} />
                </Box>
              </CardContent>
            </Card>
          </Grid>
          <Grid item xs={12} md={8}>
            <Card>
              <CardContent>
                <Typography variant="h6" gutterBottom>Collection Trend (7 Days)</Typography>
                <Box sx={{ height: 260 }}>
                  <Line data={collectionTrendData} options={barOptions} />
                </Box>
              </CardContent>
            </Card>
          </Grid>
        </Grid>

        {/* Charts Row 2 */}
        <Grid container spacing={3} sx={{ mb: 3 }}>
          <Grid item xs={12} md={6}>
            <Card>
              <CardContent>
                <Typography variant="h6" gutterBottom>Changes by Category (7 Days)</Typography>
                <Box sx={{ height: 260 }}>
                  <Bar data={changesByCategoryData} options={barOptions} />
                </Box>
              </CardContent>
            </Card>
          </Grid>
          <Grid item xs={12} md={6}>
            <Card>
              <CardContent>
                <Typography variant="h6" gutterBottom>Kernel Version Distribution</Typography>
                <Box sx={{ height: 260 }}>
                  <Bar data={kernelDistData} options={{ ...barOptions, indexAxis: 'y' as const }} />
                </Box>
              </CardContent>
            </Card>
          </Grid>
        </Grid>

        {/* Recent Activity */}
        <Grid container spacing={3}>
          <Grid item xs={12} md={6}>
            <Card>
              <CardContent>
                <Typography variant="h6" gutterBottom>Recent Changes</Typography>
                <Divider sx={{ mb: 1 }} />
                <List dense>
                  {[
                    { server: 'web-prod-01', change: 'Package upgraded: openssl 3.0.7 → 3.0.8', severity: 'info' },
                    { server: 'db-prod-03', change: 'Service failed: mysqld.service', severity: 'critical' },
                    { server: 'app-staging-02', change: 'User added: deploy-bot', severity: 'warning' },
                    { server: 'web-prod-05', change: 'Kernel changed: 4.18.0-513 → 5.14.0-362', severity: 'warning' },
                    { server: 'cache-prod-01', change: 'NFS mount removed: /shared/data', severity: 'critical' },
                  ].map((item, i) => (
                    <ListItem key={i} sx={{ px: 0 }}>
                      <ListItemText primary={item.change} secondary={item.server} primaryTypographyProps={{ variant: 'body2' }} />
                      <Chip label={item.severity} size="small" color={item.severity === 'critical' ? 'error' : item.severity === 'warning' ? 'warning' : 'default'} />
                    </ListItem>
                  ))}
                </List>
              </CardContent>
            </Card>
          </Grid>
          <Grid item xs={12} md={6}>
            <Card>
              <CardContent>
                <Typography variant="h6" gutterBottom>Recent Failures</Typography>
                <Divider sx={{ mb: 1 }} />
                <List dense>
                  {[
                    { server: 'legacy-app-01', reason: 'SSH Connection Timeout', time: '2 hours ago' },
                    { server: 'bastion-dmz-02', reason: 'Authentication Failed', time: '3 hours ago' },
                    { server: 'monitor-prod-01', reason: 'Command Timeout (uptime)', time: '5 hours ago' },
                    { server: 'build-ci-03', reason: 'Host Key Mismatch', time: '8 hours ago' },
                  ].map((item, i) => (
                    <ListItem key={i} sx={{ px: 0 }}>
                      <ListItemText primary={item.server} secondary={`${item.reason} • ${item.time}`} primaryTypographyProps={{ variant: 'body2', fontWeight: 500 }} />
                      <Chip label="Failed" size="small" color="error" variant="outlined" />
                    </ListItem>
                  ))}
                </List>
              </CardContent>
            </Card>
          </Grid>
        </Grid>
      </LoadingState>
    </Box>
  );
};

export default DashboardPage;
