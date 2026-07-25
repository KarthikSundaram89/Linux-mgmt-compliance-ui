/**
 * Servers list page with search, filter, and data grid.
 */
import React, { useCallback, useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Box, Button, Chip, TextField, Typography } from '@mui/material';
import { DataGrid, GridColDef } from '@mui/x-data-grid';
import { Add as AddIcon } from '@mui/icons-material';
import { serverService } from '../services/serverService';
import { Server, PaginatedResponse } from '../types';

const columns: GridColDef[] = [
  { field: 'hostname', headerName: 'Hostname', flex: 1, minWidth: 200 },
  { field: 'ip_address', headerName: 'IP Address', width: 140 },
  { field: 'environment', headerName: 'Environment', width: 120 },
  { field: 'os_family', headerName: 'OS Family', width: 130 },
  {
    field: 'last_collection_status',
    headerName: 'Status',
    width: 110,
    renderCell: (params) => {
      const status = params.value as string;
      const color = status === 'success' ? 'success' : status === 'failed' ? 'error' : 'default';
      return <Chip label={status || 'pending'} size="small" color={color} />;
    },
  },
  { field: 'last_collection_at', headerName: 'Last Collected', width: 180 },
];

const ServersPage: React.FC = () => {
  const navigate = useNavigate();
  const [data, setData] = useState<PaginatedResponse<Server>>({ items: [], total: 0, page: 1, page_size: 25, total_pages: 0, has_next: false, has_previous: false });
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState('');
  const [page, setPage] = useState(0);
  const [pageSize, setPageSize] = useState(25);

  const loadServers = useCallback(async () => {
    setLoading(true);
    try {
      const result = await serverService.list({ page: page + 1, page_size: pageSize, search: search || undefined });
      setData(result);
    } catch (err) {
      console.error('Failed to load servers', err);
    } finally {
      setLoading(false);
    }
  }, [page, pageSize, search]);

  useEffect(() => { loadServers(); }, [loadServers]);

  return (
    <Box>
      <Box display="flex" justifyContent="space-between" alignItems="center" mb={2}>
        <Typography variant="h4">Servers</Typography>
        <Button variant="contained" startIcon={<AddIcon />}>Add Server</Button>
      </Box>
      <TextField fullWidth placeholder="Search servers..." value={search} onChange={(e) => setSearch(e.target.value)} sx={{ mb: 2 }} />
      <DataGrid
        rows={data.items}
        columns={columns}
        rowCount={data.total}
        loading={loading}
        pageSizeOptions={[10, 25, 50]}
        paginationModel={{ page, pageSize }}
        onPaginationModelChange={(model) => { setPage(model.page); setPageSize(model.pageSize); }}
        paginationMode="server"
        onRowClick={(params) => navigate(`/servers/${params.id}`)}
        autoHeight
        disableRowSelectionOnClick
      />
    </Box>
  );
};

export default ServersPage;
