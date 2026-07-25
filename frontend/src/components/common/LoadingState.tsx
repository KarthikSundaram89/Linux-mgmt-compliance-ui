/**
 * Reusable loading/empty/error state display.
 */
import React from 'react';
import { Box, CircularProgress, Typography, Button } from '@mui/material';
import { ErrorOutline, InboxOutlined } from '@mui/icons-material';

interface LoadingStateProps {
  loading?: boolean;
  error?: string | null;
  empty?: boolean;
  emptyMessage?: string;
  onRetry?: () => void;
  children: React.ReactNode;
}

const LoadingState: React.FC<LoadingStateProps> = ({
  loading, error, empty, emptyMessage = 'No data found', onRetry, children,
}) => {
  if (loading) {
    return (
      <Box display="flex" justifyContent="center" alignItems="center" p={6}>
        <CircularProgress />
      </Box>
    );
  }

  if (error) {
    return (
      <Box display="flex" flexDirection="column" alignItems="center" p={6}>
        <ErrorOutline color="error" sx={{ fontSize: 48, mb: 1 }} />
        <Typography color="error" gutterBottom>{error}</Typography>
        {onRetry && <Button onClick={onRetry} variant="outlined">Retry</Button>}
      </Box>
    );
  }

  if (empty) {
    return (
      <Box display="flex" flexDirection="column" alignItems="center" p={6}>
        <InboxOutlined sx={{ fontSize: 48, color: 'text.secondary', mb: 1 }} />
        <Typography color="text.secondary">{emptyMessage}</Typography>
      </Box>
    );
  }

  return <>{children}</>;
};

export default LoadingState;
