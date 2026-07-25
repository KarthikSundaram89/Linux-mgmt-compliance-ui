/**
 * Reusable filter panel with chips display and clear button.
 */
import React from 'react';
import {
  Box, Chip, FormControl, InputLabel, MenuItem, Select, Button, Stack,
} from '@mui/material';
import { FilterList, Clear } from '@mui/icons-material';

export interface FilterOption {
  key: string;
  label: string;
  type: 'select' | 'boolean';
  options?: { value: string; label: string }[];
}

interface FilterPanelProps {
  filters: FilterOption[];
  values: Record<string, string | boolean | undefined>;
  onChange: (key: string, value: string | boolean | undefined) => void;
  onClear: () => void;
  activeCount: number;
}

const FilterPanel: React.FC<FilterPanelProps> = ({
  filters, values, onChange, onClear, activeCount,
}) => (
  <Box sx={{ mb: 2 }}>
    <Stack direction="row" spacing={2} alignItems="center" flexWrap="wrap" useFlexGap>
      <Chip icon={<FilterList />} label={`Filters (${activeCount})`} variant="outlined" />
      {filters.map((f) => (
        <FormControl key={f.key} size="small" sx={{ minWidth: 140 }}>
          <InputLabel>{f.label}</InputLabel>
          <Select
            value={(values[f.key] as string) || ''}
            label={f.label}
            onChange={(e) => onChange(f.key, e.target.value || undefined)}
          >
            <MenuItem value="">All</MenuItem>
            {f.options?.map((opt) => (
              <MenuItem key={opt.value} value={opt.value}>{opt.label}</MenuItem>
            ))}
          </Select>
        </FormControl>
      ))}
      {activeCount > 0 && (
        <Button startIcon={<Clear />} size="small" onClick={onClear}>Clear All</Button>
      )}
    </Stack>
  </Box>
);

export default FilterPanel;
