/**
 * Server detail page with inventory info and collection history.
 */
import React from 'react';
import { useParams } from 'react-router-dom';
import { Box, Typography, Card, CardContent } from '@mui/material';

const ServerDetailPage: React.FC = () => {
  const { id } = useParams<{ id: string }>();

  return (
    <Box>
      <Typography variant="h4" gutterBottom>Server Details</Typography>
      <Card>
        <CardContent>
          <Typography variant="body1">Server ID: {id}</Typography>
          <Typography variant="body2" color="text.secondary" sx={{ mt: 2 }}>
            Full server details, inventory data, collection history, and change history
            will be rendered here. This page integrates with snapshot storage to display
            current and historical inventory data.
          </Typography>
        </CardContent>
      </Card>
    </Box>
  );
};

export default ServerDetailPage;
