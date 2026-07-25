/**
 * Server Inventory Page
 * =====================
 * Enterprise data grid with column selection, bulk actions,
 * CSV import/export, and advanced filtering.
 */
import React, { useCallback, useEffect, useMemo, useState } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import {
  Box, Button, Chip, IconButton, Menu, MenuItem, TextField, Tooltip,
  Checkbox, Toolbar, Typography, Divider, Stack,
} from '@mui/material';
import { DataGrid, GridColDef, GridRowSelectionModel, GridToolbar } from '@mui/x-data-grid';
import {
  Add, CloudDownload, CloudUpload, Delete, PlayArrow, Replay,
  MoreVert, FilterList, Refresh, Settings,
} from '@mui/icons-material';
import { useSnackbar } from 'notistack';
import PageHeader from '../components/common/PageHeader';
import FilterPanel, { FilterOption } from '../components/common/FilterPanel';
import ConfirmDialog from '../components/common/ConfirmDialog';
import LoadingState from '../components/common/LoadingState';
import { serverService } from '../services/serverService';
import { Server, PaginatedResponse } from '../types';
import apiClient from '../services/api';

const STATUS_COLORS: Record<string, 'success' | 'error' | 'warning' | 'default'> = {
  success: 'success',
  failed: 'error',
  in_progress: 'warning',
  pending: 'default',
};

const FILTER_OPTIONS: FilterOption[] = [
  {
    key: 'environment', label: 'Environment', type: 'select',
    options: [
      { value: 'production', label: 'Production' },
      { value: 'staging', label: 'Staging' },
      { value: 'development', label: 'Development' },
      { value: 'testing', label: 'Testing' },
    ],
  },
  {
    key: 'os_family', label: 'OS Family', type: 'select',
    options: [
      { value: 'rhel', label: 'RHEL' },
      { value: 'amazon_linux', label: 'Amazon Linux' },
      { value: 'ubuntu', label: 'Ubuntu' },
      { value: 'debian', label: 'Debian' },
      { value: 'rocky', label: 'Rocky' },
      { value: 'oracle', label: 'Oracle Linux' },
      { value: 'kali', label: 'Kali' },
    ],
  },
  {
    key: 'last_collection_status', label: 'Status', type: 'select',
    options: [
      { value: 'success', label: 'Success' },
      { value: 'failed', label: 'Failed' },
      { value: 'pending', label: 'Pending' },
    ],
  },
];

const ServersPage: React.FC = () => {
  const navigate = useNavigate();
  const { enqueueSnackbar } = useSnackbar();
  const [searchParams] = useSearchParams();
  const [data, setData] = useState<PaginatedResponse<Server>>({
    items: [], total: 0, page: 1, page_size: 25, total_pages: 0, has_next: false, has_previous: false,
  });
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState('');
  const [page, setPage] = useState(0);
  const [pageSize, setPageSize] = useState(25);
  const [selection, setSelection] = useState<GridRowSelectionModel>([]);
  const [filters, setFilters] = useState<Record<string, string | undefined>>({});
  const [bulkAnchor, setBulkAnchor] = useState<null | HTMLElement>(null);
  const [confirmOpen, setConfirmOpen] = useState(false);
  const [confirmAction, setConfirmAction] = useState<string>('');

  const columns: GridColDef[] = useMemo(() => [
    { field: 'hostname', headerName: 'Hostname', flex: 1.5, minWidth: 200 },
    { field: 'ip_address', headerName: 'IP Address', width: 135 },
    { field: 'os_family', headerName: 'Distribution', width: 130 },
    { field: 'os_version', headerName: 'Version', width: 90 },
    { field: 'environment', headerName: 'Environment', width: 120,
      renderCell: (p) => <Chip label={p.value} size="small" variant="outlined" />,
    },
    { field: 'last_collection_status', headerName: 'Status', width: 100,
      renderCell: (p) => {
        const status = (p.value as string) || 'pending';
        return <Chip label={status} size="small" color={STATUS_COLORS[status] || 'default'} />;
      },
    },
    { field: 'last_collection_at', headerName: 'Last Collected', width: 170,
      valueFormatter: (params) => params.value ? new Date(params.value).toLocaleString() : 'Never',
    },
    { field: 'is_active', headerName: 'Active', width: 80, type: 'boolean' },
  ], []);

  const loadServers = useCallback(async () => {
    setLoading(true);
    try {
      const result = await serverService.list({
        page: page + 1,
        page_size: pageSize,
        search: search || undefined,
        environment: filters.environment,
        os_family: filters.os_family,
      });
      setData(result);
    } catch (err) {
      enqueueSnackbar('Failed to load servers', { variant: 'error' });
    } finally {
      setLoading(false);
    }
  }, [page, pageSize, search, filters, enqueueSnackbar]);

  useEffect(() => { loadServers(); }, [loadServers]);

  const activeFilterCount = Object.values(filters).filter(Boolean).length;

  const handleBulkAction = async (action: string) => {
    setBulkAnchor(null);
    const ids = selection as string[];
    if (!ids.length) return;

    try {
      switch (action) {
        case 'collect':
          await apiClient.post('/bulk/collect', { server_ids: ids });
          enqueueSnackbar(`Collection triggered for ${ids.length} servers`, { variant: 'success' });
          break;
        case 'retry':
          await apiClient.post('/bulk/retry', { server_ids: ids });
          enqueueSnackbar(`Retry triggered for ${ids.length} servers`, { variant: 'success' });
          break;
        case 'enable':
          await apiClient.post('/bulk/enable-collection', { server_ids: ids });
          enqueueSnackbar(`Enabled ${ids.length} servers`, { variant: 'success' });
          break;
        case 'disable':
          await apiClient.post('/bulk/disable-collection', { server_ids: ids });
          enqueueSnackbar(`Disabled ${ids.length} servers`, { variant: 'info' });
          break;
        case 'delete':
          setConfirmAction('delete');
          setConfirmOpen(true);
          return;
      }
      loadServers();
    } catch { enqueueSnackbar('Bulk action failed', { variant: 'error' }); }
  };

  const confirmDelete = async () => {
    setConfirmOpen(false);
    const ids = selection as string[];
    try {
      await apiClient.post('/bulk/delete', { server_ids: ids });
      enqueueSnackbar(`Deleted ${ids.length} servers`, { variant: 'success' });
      setSelection([]);
      loadServers();
    } catch { enqueueSnackbar('Delete failed', { variant: 'error' }); }
  };

  return (
    <Box>
      <PageHeader
        title="Server Inventory"
        subtitle={`${data.total} servers managed`}
        actions={
          <Stack direction="row" spacing={1}>
            <Button variant="outlined" startIcon={<CloudUpload />} size="small">Import CSV</Button>
            <Button variant="outlined" startIcon={<CloudDownload />} size="small">Export</Button>
            <Button variant="contained" startIcon={<Add />} size="small">Add Server</Button>
          </Stack>
        }
      />

      {/* Filter Panel */}
      <FilterPanel
        filters={FILTER_OPTIONS}
        values={filters}
        onChange={(key, val) => setFilters((prev) => ({ ...prev, [key]: val as string }))}
        onClear={() => setFilters({})}
        activeCount={activeFilterCount}
      />

      {/* Search + Bulk Actions */}
      <Box display="flex" gap={1} mb={2} alignItems="center">
        <TextField
          placeholder="Search servers..."
          size="small"
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          sx={{ width: 350 }}
        />
        <Tooltip title="Refresh"><IconButton onClick={loadServers}><Refresh /></IconButton></Tooltip>

        {selection.length > 0 && (
          <>
            <Divider orientation="vertical" flexItem />
            <Typography variant="body2" color="primary" fontWeight={500}>
              {selection.length} selected
            </Typography>
            <Button size="small" startIcon={<PlayArrow />} onClick={() => handleBulkAction('collect')}>
              Collect
            </Button>
            <Button size="small" startIcon={<Replay />} onClick={() => handleBulkAction('retry')}>
              Retry
            </Button>
            <IconButton size="small" onClick={(e) => setBulkAnchor(e.currentTarget)}>
              <MoreVert />
            </IconButton>
            <Menu anchorEl={bulkAnchor} open={Boolean(bulkAnchor)} onClose={() => setBulkAnchor(null)}>
              <MenuItem onClick={() => handleBulkAction('enable')}>Enable Collection</MenuItem>
              <MenuItem onClick={() => handleBulkAction('disable')}>Disable Collection</MenuItem>
              <MenuItem onClick={() => handleBulkAction('export')}>Export Selected</MenuItem>
              <Divider />
              <MenuItem onClick={() => handleBulkAction('delete')} sx={{ color: 'error.main' }}>
                Delete Selected
              </MenuItem>
            </Menu>
          </>
        )}
      </Box>

      {/* Data Grid */}
      <DataGrid
        rows={data.items}
        columns={columns}
        rowCount={data.total}
        loading={loading}
        pageSizeOptions={[10, 25, 50, 100]}
        paginationModel={{ page, pageSize }}
        onPaginationModelChange={(m) => { setPage(m.page); setPageSize(m.pageSize); }}
        paginationMode="server"
        checkboxSelection
        disableRowSelectionOnClick
        rowSelectionModel={selection}
        onRowSelectionModelChange={setSelection}
        onRowClick={(params) => navigate(`/servers/${params.id}`)}
        autoHeight
        sx={{ '& .MuiDataGrid-row:hover': { cursor: 'pointer' } }}
      />

      {/* Confirm Dialog */}
      <ConfirmDialog
        open={confirmOpen}
        title="Delete Servers"
        message={`Are you sure you want to delete ${selection.length} server(s)? This action cannot be undone.`}
        confirmLabel="Delete"
        severity="error"
        onConfirm={confirmDelete}
        onCancel={() => setConfirmOpen(false)}
      />
    </Box>
  );
};

export default ServersPage;
