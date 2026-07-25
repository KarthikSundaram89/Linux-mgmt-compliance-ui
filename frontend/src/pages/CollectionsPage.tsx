/**
 * Collections history page.
 */
import React from 'react';
import { Box, Typography } from '@mui/material';

const CollectionsPage: React.FC = () => (
  <Box>
    <Typography variant="h4" gutterBottom>Collection History</Typography>
    <Typography variant="body2" color="text.secondary">
      View collection runs, statuses, durations, and error logs.
      Filter by server, status, or date range.
    </Typography>
  </Box>
);

export default CollectionsPage;
