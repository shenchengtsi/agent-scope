import React from 'react';

function StepDetail({ step }) {
  if (!step) {
    return (
      <div style={styles.empty}>
        <p>Select a step to view details</p>
      </div>
    );
  }

  const typeColors = {
    input: '#3b82f6',
    llm_call: '#8b5cf6',
    tool_call: '#f59e0b',
    tool_result: '#10b981',
    output: '#10b981',
    error: '#ef4444',
    thinking: '#6b7280',
  };

  return (
    <div style={styles.container}>
      <div style={styles.header}>
        <h3 style={styles.title}>Step Details</h3>
        <span
          style={{
            ...styles.type,
            color: typeColors[step.type] || '#6b7280',
            backgroundColor: `${typeColors[step.type] || '#6b7280'}15`,
          }}
        >
          {step.type}
        </span>
      </div>

      <div style={styles.section}>
        <h4 style={styles.sectionTitle}>Content</h4>
        <pre style={styles.code}>{step.content}</pre>
      </div>

      {step.metadata && Object.keys(step.metadata).length > 0 && (
        <div style={styles.section}>
          <h4 style={styles.sectionTitle}>Metadata</h4>
          <pre style={styles.code}>
            {JSON.stringify(step.metadata, null, 2)}
          </pre>
        </div>
      )}

      {step.tool_call && (
        <div style={styles.section}>
          <h4 style={styles.sectionTitle}>Tool Call</h4>
          <div style={styles.toolSection}>
            <div style={styles.toolRow}>
              <span style={styles.toolLabel}>Name:</span>
              <span style={styles.toolValue}>{step.tool_call.name}</span>
            </div>
            <div style={styles.toolRow}>
              <span style={styles.toolLabel}>ID:</span>
              <code style={styles.toolCode}>{step.tool_call.id}</code>
            </div>
            <div style={styles.toolRow}>
              <span style={styles.toolLabel}>Latency:</span>
              <span style={styles.toolValue}>{step.tool_call.latency_ms.toFixed(2)}ms</span>
            </div>
            {step.tool_call.error && (
              <div style={styles.toolRow}>
                <span style={styles.toolLabel}>Error:</span>
                <span style={styles.errorText}>{step.tool_call.error}</span>
              </div>
            )}
          </div>
          
          <h5 style={styles.subTitle}>Arguments</h5>
          <pre style={styles.code}>
            {JSON.stringify(step.tool_call.arguments, null, 2)}
          </pre>
          
          {step.tool_call.result !== undefined && (
            <>
              <h5 style={styles.subTitle}>Result</h5>
              <pre style={styles.code}>
                {typeof step.tool_call.result === 'object'
                  ? JSON.stringify(step.tool_call.result, null, 2)
                  : String(step.tool_call.result)}
              </pre>
            </>
          )}
        </div>
      )}

      <div style={styles.stats}>
        <div style={styles.stat}>
          <span style={styles.statLabel}>Tokens In</span>
          <span style={styles.statValue}>{step.tokens_input?.toLocaleString() || 0}</span>
        </div>
        <div style={styles.stat}>
          <span style={styles.statLabel}>Tokens Out</span>
          <span style={styles.statValue}>{step.tokens_output?.toLocaleString() || 0}</span>
        </div>
        <div style={styles.stat}>
          <span style={styles.statLabel}>Latency</span>
          <span style={styles.statValue}>{step.latency_ms?.toFixed(2) || 0}ms</span>
        </div>
      </div>

      <div style={styles.footer}>
        <span style={styles.id}>ID: {step.id}</span>
        <span style={styles.timestamp}>
          {new Date(step.timestamp).toLocaleString()}
        </span>
      </div>
    </div>
  );
}

const styles = {
  container: {
    padding: '20px',
    height: '100%',
    overflowY: 'auto',
  },
  header: {
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: '20px',
    paddingBottom: '16px',
    borderBottom: '1px solid #222',
  },
  title: {
    fontSize: '18px',
    fontWeight: 600,
    color: '#e0e0e0',
  },
  type: {
    fontSize: '12px',
    padding: '4px 12px',
    borderRadius: '6px',
    textTransform: 'uppercase',
    fontWeight: 600,
  },
  section: {
    marginBottom: '20px',
  },
  sectionTitle: {
    fontSize: '13px',
    fontWeight: 600,
    color: '#9ca3af',
    marginBottom: '10px',
    textTransform: 'uppercase',
    letterSpacing: '0.5px',
  },
  subTitle: {
    fontSize: '12px',
    fontWeight: 600,
    color: '#6b7280',
    marginTop: '12px',
    marginBottom: '8px',
  },
  code: {
    backgroundColor: '#0d0d0d',
    padding: '12px',
    borderRadius: '8px',
    fontSize: '12px',
    fontFamily: 'monospace',
    color: '#e0e0e0',
    overflowX: 'auto',
    lineHeight: 1.5,
    whiteSpace: 'pre-wrap',
    wordBreak: 'break-word',
  },
  toolSection: {
    backgroundColor: '#141414',
    padding: '12px',
    borderRadius: '8px',
    marginBottom: '12px',
  },
  toolRow: {
    display: 'flex',
    marginBottom: '8px',
  },
  toolLabel: {
    width: '80px',
    fontSize: '12px',
    color: '#6b7280',
    fontWeight: 500,
  },
  toolValue: {
    fontSize: '12px',
    color: '#e0e0e0',
  },
  toolCode: {
    fontSize: '11px',
    color: '#9ca3af',
    fontFamily: 'monospace',
  },
  errorText: {
    fontSize: '12px',
    color: '#ef4444',
  },
  stats: {
    display: 'flex',
    gap: '16px',
    marginTop: '24px',
    padding: '16px',
    backgroundColor: '#141414',
    borderRadius: '8px',
  },
  stat: {
    display: 'flex',
    flexDirection: 'column',
    gap: '4px',
  },
  statLabel: {
    fontSize: '11px',
    color: '#6b7280',
    textTransform: 'uppercase',
  },
  statValue: {
    fontSize: '18px',
    fontWeight: 600,
    color: '#e0e0e0',
  },
  footer: {
    marginTop: '24px',
    paddingTop: '16px',
    borderTop: '1px solid #222',
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'center',
  },
  id: {
    fontSize: '11px',
    color: '#4b5563',
    fontFamily: 'monospace',
  },
  timestamp: {
    fontSize: '11px',
    color: '#4b5563',
  },
  empty: {
    padding: '40px',
    textAlign: 'center',
    color: '#6b7280',
  },
};

export default StepDetail;