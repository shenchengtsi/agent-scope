import React, { useState } from 'react';
import CopyButton from './CopyButton';

function CollapsibleSection({ 
  title, 
  children, 
  defaultExpanded = false,
  copyText = null,
  badge = null,
}) {
  const [isExpanded, setIsExpanded] = useState(defaultExpanded);

  return (
    <div style={styles.container}>
      <div 
        style={styles.header}
        onClick={() => setIsExpanded(!isExpanded)}
      >
        <div style={styles.headerLeft}>
          <span style={{
            ...styles.arrow,
            transform: isExpanded ? 'rotate(90deg)' : 'rotate(0deg)',
          }}>
            ▶
          </span>
          <span style={styles.title}>{title}</span>
          {badge && (
            <span style={styles.badge}>{badge}</span>
          )}
        </div>
        <div style={styles.headerRight}>
          {copyText && isExpanded && (
            <CopyButton text={copyText} />
          )}
        </div>
      </div>
      
      {isExpanded && (
        <div style={styles.content}>
          {children}
        </div>
      )}
    </div>
  );
}

const styles = {
  container: {
    border: '1px solid #222',
    borderRadius: '8px',
    marginBottom: '12px',
    backgroundColor: '#0d0d0d',
  },
  header: {
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'center',
    padding: '12px 16px',
    cursor: 'pointer',
    backgroundColor: '#141414',
    borderRadius: '8px',
    transition: 'background-color 0.2s ease',
    ':hover': {
      backgroundColor: '#1a1a1a',
    },
  },
  headerLeft: {
    display: 'flex',
    alignItems: 'center',
    gap: '10px',
    flex: 1,
  },
  headerRight: {
    display: 'flex',
    alignItems: 'center',
  },
  arrow: {
    fontSize: '10px',
    color: '#6b7280',
    transition: 'transform 0.2s ease',
  },
  title: {
    fontSize: '13px',
    fontWeight: 600,
    color: '#e0e0e0',
  },
  badge: {
    fontSize: '11px',
    padding: '2px 8px',
    backgroundColor: 'rgba(59, 130, 246, 0.2)',
    color: '#3b82f6',
    borderRadius: '4px',
    fontWeight: 500,
  },
  content: {
    padding: '16px',
    borderTop: '1px solid #222',
  },
};

export default CollapsibleSection;
