import React from 'react';

const statusColors = {
  pending: '#9ca3af',
  running: '#3b82f6',
  success: '#10b981',
  error: '#ef4444',
};

function TraceList({ traces, selectedTrace, onSelectTrace, compareMode, tracesToCompare }) {
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
      <div style={styles.list}>
        {traces.map((trace) => {
          const isSelected = selectedTrace?.id === trace.id;
          const isInCompare = tracesToCompare?.find(t => t.id === trace.id);
          const statusColor = statusColors[trace.status] || statusColors.pending;
          
          return (
            <div
              key={trace.id}
              style={{
                ...styles.trace,
                borderLeftColor: isInCompare ? '#6366f1' : statusColor,
                backgroundColor: isInCompare 
                  ? 'rgba(99, 102, 241, 0.15)' 
                  : isSelected 
                    ? 'rgba(59, 130, 246, 0.1)' 
                    : '#141414',
                border: isInCompare ? '1px solid #6366f1' : '1px solid transparent',
              }}
              onClick={() => onSelectTrace(trace)}
            >
              {/* Compare Indicator */}
              {compareMode && (
                <div style={styles.compareIndicator}>
                  <div style={{
                    ...styles.compareCheckbox,
                    backgroundColor: isInCompare ? '#6366f1' : 'transparent',
                    borderColor: isInCompare ? '#6366f1' : '#4b5563',
                  }}>
                    {isInCompare && <span style={styles.checkmark}>✓</span>}
                  </div>
                  {isInCompare && (
                    <span style={styles.compareOrder}>
                      #{tracesToCompare.findIndex(t => t.id === trace.id) + 1}
                    </span>
                  )}
                </div>
              )}
              
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
              
              {/* Additional Stats */}
              {(trace.llm_call_count > 0 || trace.tool_call_count > 0) && (
                <div style={styles.extraStats}>
                  {trace.llm_call_count > 0 && (
                    <span style={styles.extraStat}>🤖 {trace.llm_call_count}</span>
                  )}
                  {trace.tool_call_count > 0 && (
                    <span style={styles.extraStat}>🔧 {trace.tool_call_count}</span>
                  )}
                  {trace.cost_estimate > 0 && (
                    <span style={styles.extraStat}>💰 ${trace.cost_estimate.toFixed(3)}</span>
                  )}
                </div>
              )}
              
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
  
  try {
    // Ensure timestamp has Z suffix for UTC
    const utcTimestamp = typeof isoString === 'string' && isoString.endsWith('Z') 
      ? isoString 
      : isoString + 'Z';
    
    // Parse as UTC and convert to local time
    const date = new Date(utcTimestamp);
    
    // Check if valid date
    if (isNaN(date.getTime())) {
      return String(isoString);
    }
    
    const now = new Date();
    const diff = now - date;
    
    // Relative time for recent timestamps
    if (diff < 60000) return 'just now';
    if (diff < 3600000) return `${Math.floor(diff / 60000)}m ago`;
    if (diff < 86400000) return `${Math.floor(diff / 3600000)}h ago`;
    
    // Local date/time for older timestamps
    return date.toLocaleString('zh-CN', {
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
      hour12: false,
    });
  } catch (e) {
    return String(isoString);
  }
}

const styles = {
  container: {
    height: '100%',
    display: 'flex',
    flexDirection: 'column',
    overflow: 'hidden',
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
  compareIndicator: {
    display: 'flex',
    alignItems: 'center',
    gap: '8px',
    marginBottom: '8px',
  },
  compareCheckbox: {
    width: '18px',
    height: '18px',
    borderRadius: '4px',
    border: '2px solid',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
  },
  checkmark: {
    color: '#fff',
    fontSize: '12px',
    fontWeight: 'bold',
  },
  compareOrder: {
    fontSize: '11px',
    color: '#6366f1',
    fontWeight: 600,
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
  extraStats: {
    display: 'flex',
    gap: '10px',
    marginBottom: '8px',
  },
  extraStat: {
    fontSize: '10px',
    padding: '2px 6px',
    backgroundColor: 'rgba(255,255,255,0.05)',
    borderRadius: '4px',
    color: '#9ca3af',
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
