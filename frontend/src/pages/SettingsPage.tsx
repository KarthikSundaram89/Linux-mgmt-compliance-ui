/**
 * Application settings page (admin only).
 */
import React from 'react';
import { Box, Typography } from '@mui/material';

const SettingsPage: React.FC = () => (
  <Box>
    <Typography variant="h4" gutterBottom>Settings</Typography>
    <Typography variant="body2" color="text.secondary">
      Configure collection schedules, credential profiles,
      notification preferences, and retention policies.
    </Typography>
  </Box>
);

export default SettingsPage;
