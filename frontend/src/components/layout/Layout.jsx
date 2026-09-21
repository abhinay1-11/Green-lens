import React, { useState, useEffect } from 'react';
import Navbar from './Navbar';
import Sidebar from './Sidebar';
import { getProviderStatus } from '../../services/api';

export default function Layout({ children }) {
  const [providerStatus, setProviderStatus] = useState(null);
  const [isMobileOpen, setIsMobileOpen] = useState(false);

  useEffect(() => {
    getProviderStatus()
      .then((data) => setProviderStatus(data))
      .catch(() => setProviderStatus(null));
  }, []);

  const toggleMobileMenu = () => setIsMobileOpen((prev) => !prev);
  const closeMobileMenu = () => setIsMobileOpen(false);

  return (
    <div style={{ minHeight: '100vh', display: 'flex', flexDirection: 'column', width: '100%', overflowX: 'hidden' }}>
      <Navbar
        providerStatus={providerStatus}
        onToggleMobileMenu={toggleMobileMenu}
        isMobileOpen={isMobileOpen}
      />
      <div style={{ display: 'flex', flex: 1, position: 'relative' }}>
        <Sidebar
          isMobileOpen={isMobileOpen}
          onCloseMobileMenu={closeMobileMenu}
        />
        <main className="main-content" style={{ flex: 1, padding: '24px', maxWidth: '1400px', margin: '0 auto', width: '100%' }}>
          {children}
        </main>
      </div>
    </div>
  );
}

