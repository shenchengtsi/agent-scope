import React from 'react';

function Header({ isConnected, onClearAll, tracesCount }) {
  return (
    <header style={styles.header}>
      <div style={styles.left}>
        <div style={styles.logo}>
          <span style={styles.icon}>🎯</span>
          <h1 style={styles.title}>AgentScope</h1>
        </div>
        <span style={styles.subtitle}>Agent Debugging & Observability</span>
      </div>

      <div style={styles.center}>
        <div style={styles.stats}>
          <div style={styles.stat}>
            <span style={styles.statValue}>{tracesCount}</span>
            <span style={styles.statLabel}>Traces</span>
          </div>
        </div>
      </div>

      <div style={styles.right}>
        <div style={styles.connection}>
          <span
            style={{
              ...styles.statusDot,
              backgroundColor: isConnected ? '#10b981' : '#ef4444',
              boxShadow: isConnected ? '0 0 8px #10b981' : '0 0 8px #ef4444',
            }}
          />
          <span style={styles.statusText}>
            {isConnected ? 'Connected' : 'Disconnected'}
          </span>
        </div>
        
        {tracesCount > 0 && (
          <button style={styles.clearButton} onClick={onClearAll}>
            🗑️ Clear All
          </button>
        )}
      </div>
    </header>
  );
}

const styles = {
  header: {
    height: '64px',
    backgroundColor: '#0d0d0d',
    borderBottom: '1px solid #222',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'space-between',
    padding: '0 24px',
  },
  left: {
    display: 'flex',
    alignItems: 'center',
    gap: '12px',
  },
  logo: {
    display: 'flex',
    alignItems: 'center',
    gap: '10px',
  },
  icon: {
    fontSize: '24px',
  },
  title: {
    fontSize: '20px',
    fontWeight: 700,
    color: '#e0e0e0',
    margin: 0,
    background: 'linear-gradient(90deg, #3b82f6, #8b5cf6)',
    WebkitBackgroundClip: 'text',
    WebkitTextFillColor: 'transparent',
  },
  subtitle: {
    fontSize: '12px',
    color: '#6b7280',
  },
  center: {
    display: 'flex',
    alignItems: 'center',
  },
  stats: {
    display: 'flex',
    gap: '24px',
  },
  stat: {
    display: 'flex',
    alignItems: 'center',
    gap: '6px',
    padding: '6px 12px',
    backgroundColor: '#141414',
    borderRadius: '6px',
  },
  statValue: {
    fontSize: '16px',
    fontWeight: 600,
    color: '#3b82f6',
  },
  statLabel: {
    fontSize: '12px',
    color: '#6b7280',
  },
  right: {
    display: 'flex',
    alignItems: 'center',
    gap: '16px',
  },
  connection: {
    display: 'flex',
    alignItems: 'center',
    gap: '8px',
    padding: '6px 12px',
    backgroundColor: '#141414',
    borderRadius: '6px',
  },
  statusDot: {
    width: '8px',
    height: '8px',
    borderRadius: '50%',
  },
  statusText: {
    fontSize: '12px',
    color: '#9ca3af',
  },
  clearButton: {
    padding: '8px 16px',
    backgroundColor: '#1f1f1f',
    color: '#ef4444',
    border: '1px solid #333',
    borderRadius: '6px',
    fontSize: '12px',
    cursor: 'pointer',
    transition: 'all 0.2s',
  },
};

export default Header;