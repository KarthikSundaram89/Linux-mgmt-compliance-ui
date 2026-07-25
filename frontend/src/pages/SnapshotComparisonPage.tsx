/**
 * Snapshot Comparison Page
 * Allows side-by-side comparison of two snapshots with color-coded diffs.
 */
import React, { useState } from 'react';
import { useParams, useSearchParams } from 'react-router-dom';
import { Box, Card, CardContent, Grid, Typography, Chip, Table, TableBody, TableCell, TableHead, TableRow } from '@mui/material';
import PageHeader from '../components/common/PageHeader';

const SnapshotComparisonPage: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const [searchParams] = useSearchParams();
  const snapA = searchParams.get('a');
  const snapB = searchParams.get('b');

  // Sample diff data for demonstration
  const diffs = [
    { category: 'packages', type: 'installed', field: 'nginx', old: null, new: '1.24.0', color: '#4caf50' },
    { category: 'packages', type: 'upgraded', field: 'openssl', old: '3.0.7', new: '3.0.8', color: '#ff9800' },
    { category: 'packages', type: 'removed', field: 'telnet', old: '0.17-85', new: null, color: '#f44336' },
    { category: 'users', type: 'added', field: 'deploy-bot', old: null, new: 'UID=1005', color: '#4caf50' },
    { category: 'services', type: 'stopped', field: 'httpd.service', old: 'running', new: 'dead', color: '#f44336' },
    { category: 'kernel', type: 'modified', field: 'kernel_release', old: '4.18.0-477', new: '4.18.0-513', color: '#ff9800' },
  ];

  return (
    <Box>
      <PageHeader
        title="Snapshot Comparison"
        subtitle={`Comparing snapshots for server ${id}`}
        breadcrumbs={[{ label: 'Servers', href: '/servers' }, { label: id || '' , href: `/servers/${id}` }, { label: 'Compare' }]}
      />

      <Grid container spacing={2} mb={3}>
        <Grid item xs={6}>
          <Card variant="outlined">
            <CardContent>
              <Typography variant="subtitle2" color="text.secondary">Snapshot A (Previous)</Typography>
              <Typography variant="body1">{snapA || '2026-07-24 02:15:30'}</Typography>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={6}>
          <Card variant="outlined">
            <CardContent>
              <Typography variant="subtitle2" color="text.secondary">Snapshot B (Current)</Typography>
              <Typography variant="body1">{snapB || '2026-07-25 02:15:30'}</Typography>
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      <Card>
        <CardContent>
          <Typography variant="h6" gutterBottom>
            Differences ({diffs.length} changes)
          </Typography>
          <Table size="small">
            <TableHead>
              <TableRow>
                <TableCell>Category</TableCell>
                <TableCell>Change</TableCell>
                <TableCell>Field</TableCell>
                <TableCell>Previous Value</TableCell>
                <TableCell>Current Value</TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {diffs.map((d, i) => (
                <TableRow key={i} sx={{ bgcolor: `${d.color}10` }}>
                  <TableCell><Chip label={d.category} size="small" variant="outlined" /></TableCell>
                  <TableCell>
                    <Chip
                      label={d.type}
                      size="small"
                      sx={{ bgcolor: d.color, color: '#fff', fontWeight: 500 }}
                    />
                  </TableCell>
                  <TableCell><Typography variant="body2" fontWeight={500}>{d.field}</Typography></TableCell>
                  <TableCell>
                    <Typography variant="body2" sx={{ color: d.old ? '#f44336' : 'text.secondary', textDecoration: d.old ? 'line-through' : 'none' }}>
                      {d.old || '—'}
                    </Typography>
                  </TableCell>
                  <TableCell>
                    <Typography variant="body2" sx={{ color: d.new ? '#4caf50' : 'text.secondary' }}>
                      {d.new || '—'}
                    </Typography>
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </CardContent>
      </Card>
    </Box>
  );
};

export default SnapshotComparisonPage;
