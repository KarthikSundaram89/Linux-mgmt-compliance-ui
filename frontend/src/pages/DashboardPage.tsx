/**
 * Dashboard page with summary statistics and charts.
 */
import React, { useEffect, useState } from 'react';
import { Box, Card, CardContent, Grid, Typography, CircularProgress } from '@mui/material';
import { Dns, CheckCircle, Error as ErrorIcon, ChangeCircle } from '@mui/icons-material';
import { dashboardService } from '../services/dashboardService';
import { DashboardStats } from '../types';

const StatCard: React.FC<{ title: string; value: number; icon: React.ReactNode; color: string }> = ({
  title, value, icon, color,
}) => (
  <Card>
    <CardContent sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
      <Box sx={{ color, fontSize: 40 }}>{icon}</Box>
      <Box>
        <Typography variant="h4">{value}</Typography>
        <Typography variant="body2" color="text.secondary">{title}</Typography>
      </Box>
    </CardContent>
  </Card>
);

const DashboardPage: React.FC = () => {
  const [stats, setStats] = useState<DashboardStats | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    dashboardService.getStats()
      .then(setStats)
      .catch(console.error)
      .finally(() => setLoading(false));
  }, []);

  if (loading) return <Box display="flex" justifyContent="center" p={4}><CircularProgress /></Box>;

  return (
    <Box>
      <Typography variant="h4" gutterBottom>Dashboard</Typography>
      <Grid container spacing={3}>
        <Grid item xs={12} sm={6} md={3}>
          <StatCard title="Total Servers" value={stats?.total_servers ?? 0} icon={<Dns fontSize="inherit" />} color="#1976d2" />
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <StatCard title="Active Servers" value={stats?.active_servers ?? 0} icon={<CheckCircle fontSize="inherit" />} color="#2e7d32" />
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <StatCard title="Failed Collections" value={stats?.servers_failed ?? 0} icon={<ErrorIcon fontSize="inherit" />} color="#d32f2f" />
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <StatCard title="Changes Today" value={stats?.total_changes_today ?? 0} icon={<ChangeCircle fontSize="inherit" />} color="#ed6c02" />
        </Grid>
      </Grid>
    </Box>
  );
};

export default DashboardPage;
