/**
 * System Status Page
 * Shows application health, resource usage, and operational metrics.
 */
import React, { useEffect, useState } from 'react';
import { Box, Card, CardContent, Grid, LinearProgress, Typography, Chip, Stack } from '@mui/material';
import PageHeader from '../components/common/PageHeader';
import LoadingState from '../components/common/LoadingState';
import apiClient from '../services/api';

const SystemStatusPage: React.FC = () => {
  const [status, setStatus] = useState<any>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    apiClient.get('/system/status')
      .then((r) => setStatus(r.data))
      .catch(() => {})
      .finally(() => setLoading(false));
  }, []);

  return (
    <Box>
      <PageHeader title="System Status" subtitle="Application health and resource usage" />
      <LoadingState loading={loading} error={null} empty={!status && !loading}>
        {status && (
          <Grid container spacing={3}>
            <Grid item xs={12} md={4}>
              <Card>
                <CardContent>
                  <Typography variant="h6" gutterBottom>Application</Typography>
                  <InfoLine label="Name" value={status.application?.name} />
                  <InfoLine label="Version" value={status.application?.version} />
                  <InfoLine label="Environment" value={status.application?.environment} />
                  <InfoLine label="Python" value={status.application?.python_version} />
                </CardContent>
              </Card>
            </Grid>
            <Grid item xs={12} md={4}>
              <Card>
                <CardContent>
                  <Typography variant="h6" gutterBottom>Database</Typography>
                  <InfoLine label="Status" value={<Chip label="Connected" size="small" color="success" />} />
                  <InfoLine label="URL" value={status.database?.url} />
                </CardContent>
              </Card>
            </Grid>
            <Grid item xs={12} md={4}>
              <Card>
                <CardContent>
                  <Typography variant="h6" gutterBottom>Scheduler</Typography>
                  <InfoLine label="Enabled" value={status.scheduler?.enabled ? 'Yes' : 'No'} />
                  <InfoLine label="Concurrent" value={String(status.scheduler?.max_concurrent)} />
                  <InfoLine label="Collection Hour" value={`${status.scheduler?.collection_hour}:00 UTC`} />
                  <InfoLine label="Retry Interval" value={`${status.scheduler?.retry_interval_minutes} min`} />
                </CardContent>
              </Card>
            </Grid>
            <Grid item xs={12}>
              <Card>
                <CardContent>
                  <Typography variant="h6" gutterBottom>Storage</Typography>
                  <Box mb={2}>
                    <Stack direction="row" justifyContent="space-between" mb={0.5}>
                      <Typography variant="body2">Disk Usage</Typography>
                      <Typography variant="body2">{status.storage?.disk_usage_percent}%</Typography>
                    </Stack>
                    <LinearProgress variant="determinate" value={status.storage?.disk_usage_percent || 0} color={status.storage?.disk_usage_percent > 80 ? 'error' : 'primary'} />
                  </Box>
                  <Grid container spacing={2}>
                    <Grid item xs={4}><InfoLine label="Snapshots" value={`${status.storage?.snapshots_size_mb} MB`} /></Grid>
                    <Grid item xs={4}><InfoLine label="Logs" value={`${status.storage?.logs_size_mb} MB`} /></Grid>
                    <Grid item xs={4}><InfoLine label="Reports" value={`${status.storage?.reports_size_mb} MB`} /></Grid>
                  </Grid>
                </CardContent>
              </Card>
            </Grid>
          </Grid>
        )}
      </LoadingState>
    </Box>
  );
};

const InfoLine: React.FC<{ label: string; value: any }> = ({ label, value }) => (
  <Box display="flex" justifyContent="space-between" py={0.5}>
    <Typography variant="body2" color="text.secondary">{label}</Typography>
    <Typography variant="body2">{value || '—'}</Typography>
  </Box>
);

export default SystemStatusPage;
