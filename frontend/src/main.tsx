/**
 * Application entry point.
 * Renders the root App component with providers.
 *
 * Mock API is enabled automatically for GitHub Pages demo.
 * In production with a real backend, remove the setupMockApi() call.
 */
import React from 'react';
import ReactDOM from 'react-dom/client';
import { HashRouter } from 'react-router-dom';

import App from './App';
import { AuthProvider } from './contexts/AuthContext';
import { ThemeProvider } from './themes/ThemeProvider';
import { setupMockApi } from './mocks/mockApi';
import apiClient from './services/api';

// Enable mock API (no backend required for demo)
setupMockApi(apiClient);

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <HashRouter>
      <ThemeProvider>
        <AuthProvider>
          <App />
        </AuthProvider>
      </ThemeProvider>
    </HashRouter>
  </React.StrictMode>
);
