/**
 * Change History Page
 * Displays all detected changes with filtering by category, severity, server.
 */
import React, { useCallback, useEffect, useState } from 'react';
import {
  Box, Chip, TextField, Tooltip, IconButton,
} from '@mui/material';
import { DataGrid, GridColDef } from '@mui/x-data-grid';
import { Refresh, CheckCircle } from '@mui/icons-material';
import { useSnackbar } from 'notistack';
import PageHeader from '../components/common/PageHeader';
import FilterPanel, { FilterOption } from '../components/common/FilterPanel';
import apiClient from '../services/api';

const SEVERITY_COLOR: Record<string, 'error' | 'warning' | 'default' | 'info'> = {
  critical: 'error',
  warning: 'warning',
  info: 'info',
};

const CHANGE_FILTERS: FilterOption[] = [
  {
    key: 'severity', label: 'Severity', type: 'select',
    options: [
      { value: 'critical', label: 'Critical' },
      { value: 'warning', label: 'Warning' },
      { value: 'info', label: 'Info' },
    ],
  },
  {
    key: 'category', label: 'Category', type: 'select',
    options: [
      { value: 'packages', label: 'Packages' },
      { value: 'services', label: 'Services' },
      { value: 'users', label: 'Users' },
      { value: 'filesystem', label: 'Filesystem' },
      { value: 'operating_system', label: 'OS/Kernel' },
      { value: 'sudo', label: 'Sudo' },
      { value: 'ssh_config', label: 'SSH Config' },
      { value: 'chrony', label: 'Chrony' },
      { value: 'cron', label: 'Cron' },
      { value: 'password_policy', label: 'Password Policy' },
    ],
  },
];

const ChangesPage: React.FC = () => {
  const { enqueueSnackbar } = useSnackbar();
  const [changes, setChanges] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(0);
  const [pageSize, setPageSize] = useState(25);
  const [filters, setFilters] = useState<Record<string, string | undefined>>({});

  const loadChanges = useCallback(async () => {
    setLoading(true);
    try {
      const params: any = { page: page + 1, page_size: pageSize };
      if (filters.severity) params.severity = filters.severity;
      if (filters.category) params.category = filters.category;
      const res = await apiClient.get('/changes', { params });
      setChanges(res.data.items || []);
      setTotal(res.data.total || 0);
    } catch { enqueueSnackbar('Failed to load changes', { variant: 'error' }); }
    finally { setLoading(false); }
  }, [page, pageSize, filters, enqueueSnackbar]);

  useEffect(() => { loadChanges(); }, [loadChanges]);

  const columns: GridColDef[] = [
    { field: 'detected_at', headerName: 'Detected', width: 170,
      valueFormatter: (p) => p.value ? new Date(p.value).toLocaleString() : '',
    },
    { field: 'server_id', headerName: 'Server', width: 130 },
    { field: 'category', headerName: 'Category', width: 130,
      renderCell: (p) => <Chip label={p.value} size="small" variant="outlined" />,
    },
    { field: 'severity', headerName: 'Severity', width: 100,
      renderCell: (p) => <Chip label={p.value} size="small" color={SEVERITY_COLOR[p.value] || 'default'} />,
    },
    { field: 'change_type', headerName: 'Change', width: 110 },
    { field: 'field_name', headerName: 'Field', flex: 1 },
    { field: 'old_value', headerName: 'Old Value', width: 150,
      renderCell: (p) => <Box sx={{ color: 'error.main', textDecoration: p.value ? 'line-through' : 'none' }}>{p.value || '—'}</Box>,
    },
    { field: 'new_value', headerName: 'New Value', width: 150,
      renderCell: (p) => <Box sx={{ color: 'success.main' }}>{p.value || '—'}</Box>,
    },
    { field: 'acknowledged', headerName: 'Ack', width: 60, type: 'boolean',
      renderCell: (p) => p.value ? <CheckCircle fontSize="small" color="success" /> : null,
    },
  ];

  return (
    <Box>
      <PageHeader
        title="Change History"
        subtitle={`${total} changes detected`}
        actions={<Tooltip title="Refresh"><IconButton onClick={loadChanges}><Refresh /></IconButton></Tooltip>}
      />
      <FilterPanel
        filters={CHANGE_FILTERS}
        values={filters}
        onChange={(k, v) => setFilters((p) => ({ ...p, [k]: v as string }))}
        onClear={() => setFilters({})}
        activeCount={Object.values(filters).filter(Boolean).length}
      />
      <DataGrid
        rows={changes}
        columns={columns}
        rowCount={total}
        loading={loading}
        pageSizeOptions={[10, 25, 50, 100]}
        paginationModel={{ page, pageSize }}
        onPaginationModelChange={(m) => { setPage(m.page); setPageSize(m.pageSize); }}
        paginationMode="server"
        autoHeight
        disableRowSelectionOnClick
      />
    </Box>
  );
};

export default ChangesPage;
