import React, { useState, useEffect } from 'react';
import Navbar from './Navbar';
import Sidebar from './Sidebar';
import { getProviderStatus } from '../../services/api';

export default function Layout({ children }) {
  const [providerStatus, setProviderStatus] = useState(null);

  useEffect(() => {
    getProviderStatus()
      .then((data) => setProviderStatus(data))
      .catch(() => setProviderStatus(null));
  }, []);

  return (
    <div style={{ minHeight: '100vh', display: 'flex', flexDirection: 'column' }}>
      <Navbar providerStatus={providerStatus} />
      <div style={{ display: 'flex', flex: 1 }}>
        <Sidebar />
        <main style={{ flex: 1, padding: '24px', maxWidth: '1400px', margin: '0 auto', width: '100%' }}>
          {children}
        </main>
      </div>
    </div>
  );
}
