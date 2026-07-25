/**
 * Reports Page
 * Generate and download inventory reports in CSV, Excel, PDF.
 */
import React, { useState } from 'react';
import {
  Box, Button, Card, CardContent, FormControl, Grid, InputLabel,
  MenuItem, Select, Typography, Chip, Stack, LinearProgress,
} from '@mui/material';
import { Description, GetApp, Schedule } from '@mui/icons-material';
import { useSnackbar } from 'notistack';
import PageHeader from '../components/common/PageHeader';
import apiClient from '../services/api';

const REPORT_TYPES = [
  { value: 'inventory', label: 'Server Inventory Report', desc: 'Complete server list with OS, kernel, and status' },
  { value: 'users', label: 'User Account Report', desc: 'All non-system users across servers' },
  { value: 'packages', label: 'Package Inventory Report', desc: 'Installed packages by server' },
  { value: 'filesystem', label: 'Filesystem Report', desc: 'Disk usage and mount information' },
  { value: 'services', label: 'Service Status Report', desc: 'Systemd service states and failed services' },
  { value: 'compliance', label: 'Compliance Report', desc: 'Password policy and SSH config compliance' },
  { value: 'changes', label: 'Change Report', desc: 'Recent detected changes across all servers' },
  { value: 'chrony', label: 'Time Sync Report', desc: 'Chrony/NTP synchronization status' },
  { value: 'collection', label: 'Collection Report', desc: 'Collection history with success/failure metrics' },
];

const ReportsPage: React.FC = () => {
  const { enqueueSnackbar } = useSnackbar();
  const [reportType, setReportType] = useState('inventory');
  const [format, setFormat] = useState('csv');
  const [generating, setGenerating] = useState(false);

  const handleGenerate = async () => {
    setGenerating(true);
    try {
      await apiClient.post(`/reports/generate?report_type=${reportType}&format=${format}`);
      enqueueSnackbar('Report generation started. Check back shortly.', { variant: 'success' });
    } catch {
      enqueueSnackbar('Failed to start report generation', { variant: 'error' });
    } finally {
      setGenerating(false);
    }
  };

  return (
    <Box>
      <PageHeader title="Reports" subtitle="Generate and download inventory reports" />

      <Grid container spacing={3}>
        <Grid item xs={12} md={8}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>Generate New Report</Typography>
              <Grid container spacing={2} alignItems="center">
                <Grid item xs={12} sm={5}>
                  <FormControl fullWidth size="small">
                    <InputLabel>Report Type</InputLabel>
                    <Select value={reportType} label="Report Type" onChange={(e) => setReportType(e.target.value)}>
                      {REPORT_TYPES.map((t) => (
                        <MenuItem key={t.value} value={t.value}>{t.label}</MenuItem>
                      ))}
                    </Select>
                  </FormControl>
                </Grid>
                <Grid item xs={12} sm={3}>
                  <FormControl fullWidth size="small">
                    <InputLabel>Format</InputLabel>
                    <Select value={format} label="Format" onChange={(e) => setFormat(e.target.value)}>
                      <MenuItem value="csv">CSV</MenuItem>
                      <MenuItem value="excel">Excel</MenuItem>
                      <MenuItem value="pdf">PDF</MenuItem>
                    </Select>
                  </FormControl>
                </Grid>
                <Grid item xs={12} sm={4}>
                  <Button variant="contained" fullWidth startIcon={<Description />} onClick={handleGenerate} disabled={generating}>
                    {generating ? 'Generating...' : 'Generate Report'}
                  </Button>
                </Grid>
              </Grid>
              {generating && <LinearProgress sx={{ mt: 2 }} />}
              <Typography variant="body2" color="text.secondary" mt={2}>
                {REPORT_TYPES.find((t) => t.value === reportType)?.desc}
              </Typography>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} md={4}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>Recent Reports</Typography>
              <Stack spacing={1}>
                {[
                  { name: 'inventory_2026-07-25.csv', time: '2h ago', size: '245 KB' },
                  { name: 'compliance_2026-07-24.pdf', time: '1d ago', size: '1.2 MB' },
                  { name: 'changes_2026-07-23.xlsx', time: '2d ago', size: '380 KB' },
                ].map((r, i) => (
                  <Box key={i} display="flex" alignItems="center" justifyContent="space-between" py={0.5}>
                    <Box>
                      <Typography variant="body2">{r.name}</Typography>
                      <Typography variant="caption" color="text.secondary">{r.time} • {r.size}</Typography>
                    </Box>
                    <Button size="small" startIcon={<GetApp />}>Download</Button>
                  </Box>
                ))}
              </Stack>
            </CardContent>
          </Card>
        </Grid>
      </Grid>
    </Box>
  );
};

export default ReportsPage;
