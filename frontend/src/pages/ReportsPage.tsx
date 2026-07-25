/**
 * Reports generation and download page.
 */
import React from 'react';
import { Box, Typography } from '@mui/material';

const ReportsPage: React.FC = () => (
  <Box>
    <Typography variant="h4" gutterBottom>Reports</Typography>
    <Typography variant="body2" color="text.secondary">
      Generate and download inventory, compliance, and change reports
      in CSV, Excel, or PDF format.
    </Typography>
  </Box>
);

export default ReportsPage;
