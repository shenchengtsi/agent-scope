import React from 'react';

const statusColors = {
  pending: '#9ca3af',
  running: '#3b82f6',
  success: '#10b981',
  error: '#ef4444',
};

function TraceList({ traces, selectedTrace, onSelectTrace }) {
  if (traces.length === 0) {
    return (
      <div style={styles.empty}>
        <div style={styles.emptyIcon}>🔍</div>
        <h3 style={styles.emptyTitle}>No traces yet</h3>
        <p style={styles.emptyText}>
          Run an agent with @trace decorator to see traces here
        </p>
      </div>
    );
  }

  return (
    <div style={styles.container}>
      <div style={styles.header}>
        <span style={styles.count}>{traces.length} traces</span>
      </div>
      
      <div style={styles.list}>
        {traces.map((trace) => {
          const isSelected = selectedTrace?.id === trace.id;
          const statusColor = statusColors[trace.status] || statusColors.pending;
          
          return (
            <div
              key={trace.id}
              style={{
                ...styles.trace,
                borderLeftColor: statusColor,
                backgroundColor: isSelected ? 'rgba(59, 130, 246, 0.1)' : '#141414',
              }}
              onClick={() => onSelectTrace(trace)}
            >
              <div style={styles.traceHeader}>
                <span style={styles.name}>{trace.name}</span>
                <span
                  style={{
                    ...styles.status,
                    color: statusColor,
                    backgroundColor: `${statusColor}15`,
                  }}
                >
                  {trace.status}
                </span>
              </div>
              
              <p style={styles.query}>
                {trace.input_query?.substring(0, 60)}
                {trace.input_query?.length > 60 ? '...' : ''}
              </p>
              
              <div style={styles.meta}>
                <span style={styles.metaItem}>
                  🕒 {formatTime(trace.start_time)}
                </span>
                {trace.total_tokens > 0 && (
                  <span style={styles.metaItem}>
                    📊 {trace.total_tokens.toLocaleString()} tokens
                  </span>
                )}
                {trace.total_latency_ms > 0 && (
                  <span style={styles.metaItem}>
                    ⚡ {trace.total_latency_ms.toFixed(0)}ms
                  </span>
                )}
              </div>
              
              {trace.tags?.length > 0 && (
                <div style={styles.tags}>
                  {trace.tags.map((tag) => (
                    <span key={tag} style={styles.tag}>{tag}</span>
                  ))}
                </div>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
}

function formatTime(isoString) {
  if (!isoString) return '';
  const date = new Date(isoString);
  const now = new Date();
  const diff = now - date;
  
  if (diff < 60000) return 'just now';
  if (diff < 3600000) return `${Math.floor(diff / 60000)}m ago`;
  if (diff < 86400000) return `${Math.floor(diff / 3600000)}h ago`;
  
  return date.toLocaleDateString();
}

const styles = {
  container: {
    height: '100%',
    display: 'flex',
    flexDirection: 'column',
  },
  header: {
    padding: '12px 16px',
    borderBottom: '1px solid #222',
  },
  count: {
    fontSize: '12px',
    color: '#6b7280',
    fontWeight: 500,
  },
  list: {
    flex: 1,
    overflowY: 'auto',
    padding: '8px',
  },
  trace: {
    padding: '12px',
    marginBottom: '8px',
    borderRadius: '8px',
    borderLeft: '3px solid',
    cursor: 'pointer',
    transition: 'all 0.2s ease',
  },
  traceHeader: {
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: '6px',
  },
  name: {
    fontSize: '13px',
    fontWeight: 600,
    color: '#e0e0e0',
  },
  status: {
    fontSize: '10px',
    padding: '2px 6px',
    borderRadius: '4px',
    textTransform: 'uppercase',
    fontWeight: 600,
  },
  query: {
    fontSize: '12px',
    color: '#9ca3af',
    marginBottom: '8px',
    lineHeight: 1.4,
    fontFamily: 'monospace',
  },
  meta: {
    display: 'flex',
    gap: '12px',
    marginBottom: '8px',
  },
  metaItem: {
    fontSize: '11px',
    color: '#6b7280',
  },
  tags: {
    display: 'flex',
    gap: '6px',
    flexWrap: 'wrap',
  },
  tag: {
    fontSize: '10px',
    padding: '2px 6px',
    backgroundColor: 'rgba(59, 130, 246, 0.15)',
    color: '#3b82f6',
    borderRadius: '4px',
  },
  empty: {
    padding: '40px 20px',
    textAlign: 'center',
  },
  emptyIcon: {
    fontSize: '48px',
    marginBottom: '16px',
  },
  emptyTitle: {
    fontSize: '16px',
    fontWeight: 600,
    color: '#e0e0e0',
    marginBottom: '8px',
  },
  emptyText: {
    fontSize: '13px',
    color: '#6b7280',
    lineHeight: 1.5,
  },
};

export default TraceList;