/**
 * Consistent page header with title, subtitle, and action buttons.
 */
import React from 'react';
import { Box, Typography, Breadcrumbs, Link } from '@mui/material';
import { NavigateNext } from '@mui/icons-material';

interface Crumb {
  label: string;
  href?: string;
}

interface PageHeaderProps {
  title: string;
  subtitle?: string;
  breadcrumbs?: Crumb[];
  actions?: React.ReactNode;
}

const PageHeader: React.FC<PageHeaderProps> = ({ title, subtitle, breadcrumbs, actions }) => (
  <Box sx={{ mb: 3 }}>
    {breadcrumbs && (
      <Breadcrumbs separator={<NavigateNext fontSize="small" />} sx={{ mb: 1 }}>
        {breadcrumbs.map((crumb, i) => (
          crumb.href ? (
            <Link key={i} href={crumb.href} underline="hover" color="inherit">{crumb.label}</Link>
          ) : (
            <Typography key={i} color="text.primary">{crumb.label}</Typography>
          )
        ))}
      </Breadcrumbs>
    )}
    <Box display="flex" justifyContent="space-between" alignItems="center">
      <Box>
        <Typography variant="h4" fontWeight={600}>{title}</Typography>
        {subtitle && <Typography variant="body2" color="text.secondary" mt={0.5}>{subtitle}</Typography>}
      </Box>
      {actions && <Box>{actions}</Box>}
    </Box>
  </Box>
);

export default PageHeader;
