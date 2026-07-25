/**
 * Global search bar with autocomplete suggestions.
 * Searches across servers, users, packages, services.
 */
import React, { useCallback, useEffect, useState } from 'react';
import {
  Autocomplete, InputAdornment, TextField, Box, Typography, Chip,
} from '@mui/material';
import { Search as SearchIcon } from '@mui/icons-material';
import { useNavigate } from 'react-router-dom';
import { debounce } from '../../utils/debounce';
import apiClient from '../../services/api';

interface SearchResult {
  id: string;
  type: string;
  title: string;
  subtitle: string;
  match_field: string;
  link: string;
}

const SearchBar: React.FC = () => {
  const navigate = useNavigate();
  const [query, setQuery] = useState('');
  const [results, setResults] = useState<SearchResult[]>([]);
  const [loading, setLoading] = useState(false);

  const search = useCallback(
    debounce(async (q: string) => {
      if (q.length < 2) { setResults([]); return; }
      setLoading(true);
      try {
        const res = await apiClient.get('/search', { params: { q } });
        setResults(res.data.results || []);
      } catch { setResults([]); }
      finally { setLoading(false); }
    }, 300),
    []
  );

  useEffect(() => { search(query); }, [query, search]);

  return (
    <Autocomplete
      freeSolo
      options={results}
      getOptionLabel={(opt) => typeof opt === 'string' ? opt : opt.title}
      loading={loading}
      inputValue={query}
      onInputChange={(_, v) => setQuery(v)}
      onChange={(_, value) => {
        if (value && typeof value !== 'string') navigate(value.link);
      }}
      renderOption={(props, option) => (
        <Box component="li" {...props} key={option.id}>
          <Box>
            <Typography variant="body2" fontWeight={500}>{option.title}</Typography>
            <Typography variant="caption" color="text.secondary">{option.subtitle}</Typography>
          </Box>
          <Chip label={option.type} size="small" sx={{ ml: 'auto' }} />
        </Box>
      )}
      renderInput={(params) => (
        <TextField
          {...params}
          placeholder="Search servers, users, packages..."
          size="small"
          sx={{ width: 400, bgcolor: 'action.hover', borderRadius: 1 }}
          InputProps={{
            ...params.InputProps,
            startAdornment: (
              <InputAdornment position="start"><SearchIcon fontSize="small" /></InputAdornment>
            ),
          }}
        />
      )}
    />
  );
};

export default SearchBar;
