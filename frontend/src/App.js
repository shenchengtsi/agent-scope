import React, { useState } from 'react';
import Dashboard from './pages/Dashboard';
import Analytics from './pages/Analytics';

function App() {
  const [currentPage, setCurrentPage] = useState('dashboard');

  return (
    <div className="App" style={styles.app}>
      {/* Navigation */}
      <nav style={styles.nav}>
        <div style={styles.navBrand}>
          <span style={styles.navLogo}>🔭</span>
          <span style={styles.navTitle}>AgentScope</span>
        </div>
        <div style={styles.navLinks}>
          <button
            style={{
              ...styles.navButton,
              ...(currentPage === 'dashboard' ? styles.navButtonActive : {}),
            }}
            onClick={() => setCurrentPage('dashboard')}
          >
            📊 Dashboard
          </button>
          <button
            style={{
              ...styles.navButton,
              ...(currentPage === 'analytics' ? styles.navButtonActive : {}),
            }}
            onClick={() => setCurrentPage('analytics')}
          >
            📈 Analytics
          </button>
        </div>
      </nav>

      {/* Page Content */}
      <main style={styles.main}>
        {currentPage === 'dashboard' ? <Dashboard /> : <Analytics />}
      </main>
    </div>
  );
}

const styles = {
  app: {
    minHeight: '100vh',
    backgroundColor: '#0a0a0a',
  },
  nav: {
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'space-between',
    padding: '12px 24px',
    backgroundColor: '#141414',
    borderBottom: '1px solid #222',
  },
  navBrand: {
    display: 'flex',
    alignItems: 'center',
    gap: '10px',
  },
  navLogo: {
    fontSize: '24px',
  },
  navTitle: {
    fontSize: '18px',
    fontWeight: 600,
    color: '#fff',
  },
  navLinks: {
    display: 'flex',
    gap: '8px',
  },
  navButton: {
    padding: '8px 16px',
    borderRadius: '6px',
    border: 'none',
    backgroundColor: 'transparent',
    color: '#9ca3af',
    fontSize: '14px',
    fontWeight: 500,
    cursor: 'pointer',
    transition: 'all 0.2s ease',
  },
  navButtonActive: {
    backgroundColor: '#1f1f1f',
    color: '#fff',
  },
  main: {
    minHeight: 'calc(100vh - 60px)',
  },
};

export default App;
