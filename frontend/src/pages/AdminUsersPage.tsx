/**
 * User Management Administration Page
 * Allows admins to create, edit, lock/unlock, and manage users.
 */
import React, { useCallback, useEffect, useState } from 'react';
import {
  Box, Button, Chip, IconButton, Stack, Tooltip,
} from '@mui/material';
import { DataGrid, GridColDef } from '@mui/x-data-grid';
import { PersonAdd, Lock, LockOpen, Refresh } from '@mui/icons-material';
import { useSnackbar } from 'notistack';
import PageHeader from '../components/common/PageHeader';
import apiClient from '../services/api';

const AdminUsersPage: React.FC = () => {
  const { enqueueSnackbar } = useSnackbar();
  const [users, setUsers] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [total, setTotal] = useState(0);

  const loadUsers = useCallback(async () => {
    setLoading(true);
    try {
      const res = await apiClient.get('/users');
      setUsers(res.data.items || []);
      setTotal(res.data.total || 0);
    } catch { enqueueSnackbar('Failed to load users', { variant: 'error' }); }
    finally { setLoading(false); }
  }, [enqueueSnackbar]);

  useEffect(() => { loadUsers(); }, [loadUsers]);

  const columns: GridColDef[] = [
    { field: 'username', headerName: 'Username', flex: 1 },
    { field: 'full_name', headerName: 'Full Name', flex: 1 },
    { field: 'email', headerName: 'Email', flex: 1.2 },
    { field: 'role', headerName: 'Role', width: 120,
      renderCell: (p) => <Chip label={p.value || 'None'} size="small" variant="outlined" />,
    },
    { field: 'is_active', headerName: 'Active', width: 80, type: 'boolean' },
    { field: 'is_locked', headerName: 'Locked', width: 80, type: 'boolean' },
    { field: 'auth_provider', headerName: 'Auth', width: 90 },
    { field: 'last_login_at', headerName: 'Last Login', width: 160,
      valueFormatter: (p) => p.value ? new Date(p.value).toLocaleString() : 'Never',
    },
    { field: 'actions', headerName: '', width: 80, sortable: false,
      renderCell: (p) => (
        <Tooltip title={p.row.is_locked ? 'Unlock' : 'Lock'}>
          <IconButton size="small" onClick={async () => {
            if (p.row.is_locked) {
              await apiClient.post(`/users/${p.row.id}/unlock`);
              enqueueSnackbar('User unlocked', { variant: 'success' });
            }
            loadUsers();
          }}>
            {p.row.is_locked ? <LockOpen fontSize="small" /> : <Lock fontSize="small" />}
          </IconButton>
        </Tooltip>
      ),
    },
  ];

  return (
    <Box>
      <PageHeader
        title="User Management"
        subtitle={`${total} users`}
        breadcrumbs={[{ label: 'Administration' }, { label: 'Users' }]}
        actions={
          <Stack direction="row" spacing={1}>
            <Tooltip title="Refresh"><IconButton onClick={loadUsers}><Refresh /></IconButton></Tooltip>
            <Button variant="contained" startIcon={<PersonAdd />} size="small">Create User</Button>
          </Stack>
        }
      />
      <DataGrid
        rows={users}
        columns={columns}
        loading={loading}
        autoHeight
        pageSizeOptions={[10, 25, 50]}
        disableRowSelectionOnClick
      />
    </Box>
  );
};

export default AdminUsersPage;
