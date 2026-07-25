/**
 * Audit logs page (admin/auditor only).
 */
import React from 'react';
import { Box, Typography } from '@mui/material';

const AuditLogsPage: React.FC = () => (
  <Box>
    <Typography variant="h4" gutterBottom>Audit Logs</Typography>
    <Typography variant="body2" color="text.secondary">
      View all system actions including logins, data changes,
      and administrative operations. Filter by user, action, or date.
    </Typography>
  </Box>
);

export default AuditLogsPage;
