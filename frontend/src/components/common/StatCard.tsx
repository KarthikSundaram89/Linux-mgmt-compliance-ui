/**
 * Reusable statistic card for dashboards.
 * Shows a metric with icon, trend indicator, and optional subtitle.
 */
import React from 'react';
import { Card, CardContent, Box, Typography, Chip } from '@mui/material';
import { TrendingUp, TrendingDown } from '@mui/icons-material';

interface StatCardProps {
  title: string;
  value: number | string;
  icon: React.ReactNode;
  color?: string;
  subtitle?: string;
  trend?: { value: number; label: string };
  onClick?: () => void;
}

const StatCard: React.FC<StatCardProps> = ({
  title, value, icon, color = '#1976d2', subtitle, trend, onClick,
}) => (
  <Card
    sx={{ cursor: onClick ? 'pointer' : 'default', '&:hover': onClick ? { boxShadow: 4 } : {} }}
    onClick={onClick}
  >
    <CardContent sx={{ display: 'flex', alignItems: 'center', gap: 2, py: 2 }}>
      <Box sx={{ color, fontSize: 40, display: 'flex' }}>{icon}</Box>
      <Box sx={{ flexGrow: 1 }}>
        <Typography variant="h4" fontWeight={600}>{value}</Typography>
        <Typography variant="body2" color="text.secondary">{title}</Typography>
        {subtitle && (
          <Typography variant="caption" color="text.secondary">{subtitle}</Typography>
        )}
      </Box>
      {trend && (
        <Chip
          size="small"
          icon={trend.value >= 0 ? <TrendingUp /> : <TrendingDown />}
          label={trend.label}
          color={trend.value >= 0 ? 'success' : 'error'}
          variant="outlined"
        />
      )}
    </CardContent>
  </Card>
);

export default StatCard;
