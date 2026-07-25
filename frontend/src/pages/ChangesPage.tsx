/**
 * Change detection history page.
 */
import React from 'react';
import { Box, Typography } from '@mui/material';

const ChangesPage: React.FC = () => (
  <Box>
    <Typography variant="h4" gutterBottom>Change History</Typography>
    <Typography variant="body2" color="text.secondary">
      View detected changes across all servers. Filter by category,
      severity, and acknowledgement status.
    </Typography>
  </Box>
);

export default ChangesPage;
