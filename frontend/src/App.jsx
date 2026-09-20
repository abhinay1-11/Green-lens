import React, { useEffect } from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import Layout from './components/layout/Layout';

import Dashboard from './pages/Dashboard';
import Observe from './pages/Observe';
import MapPage from './pages/MapPage';
import SpeciesExplorer from './pages/SpeciesExplorer';
import SpeciesDetail from './pages/SpeciesDetail';
import ObservationDetail from './pages/ObservationDetail';
import Trends from './pages/Trends';
import Reports from './pages/Reports';
import Settings from './pages/Settings';
import { initTheme } from './utils/theme';
import { getHealth, getProviderStatus } from './services/api';

export default function App() {
  useEffect(() => {
    const cleanup = initTheme();

    // Establish immediate backend connectivity on frontend application startup
    const initBackendConnection = async () => {
      try {
        await getHealth();
        await getProviderStatus();
        console.log('[GreenLens] Startup backend health & AI provider readiness check completed.');
      } catch (err) {
        console.warn('[GreenLens] Startup backend connectivity note:', err);
      }
    };

    initBackendConnection();
    return cleanup;
  }, []);

  return (
    <Router>
      <Layout>
        <Routes>
          <Route path="/" element={<Dashboard />} />
          <Route path="/observe" element={<Observe />} />
          <Route path="/map" element={<MapPage />} />
          <Route path="/species" element={<SpeciesExplorer />} />
          <Route path="/species/:id" element={<SpeciesDetail />} />
          <Route path="/observations/:id" element={<ObservationDetail />} />
          <Route path="/trends" element={<Trends />} />
          <Route path="/reports" element={<Reports />} />
          <Route path="/settings" element={<Settings />} />
        </Routes>
      </Layout>
    </Router>
  );
}
