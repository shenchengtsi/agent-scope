import React from 'react';
import CollapsibleSection from './CollapsibleSection';

function SubAgentDetail({ subagentInfo, onViewChildTrace }) {
  if (!subagentInfo) return null;

  const { agent_name, agent_id, input_query, child_trace_id, timeout, result_preview } = subagentInfo;

  // Prepare copy text
  const copyText = JSON.stringify({
    agent_name,
    agent_id,
    input_query,
    timeout,
    result_preview,
  }, null, 2);

  return (
    <div style={styles.container}>
      {/* Agent Header */}
      <div style={styles.header}>
        <div style={styles.agentBadge}>
          <span style={styles.agentIcon}>🤖</span>
          <div style={styles.agentInfo}>
            <span style={styles.agentName}>{agent_name}</span>
            {agent_id && (
              <code style={styles.agentId}>{agent_id}</code>
            )}
          </div>
        </div>
        
        {timeout > 0 && (
          <span style={styles.timeoutBadge}>
            ⏱️ {timeout}s timeout
          </span>
        )}
      </div>

      {/* Input Query */}
      {input_query && (
        <CollapsibleSection 
          title="Input Query" 
          copyText={input_query}
          defaultExpanded={true}
        >
          <div style={styles.queryBox}>
            <p style={styles.queryText}>{input_query}</p>
          </div>
        </CollapsibleSection>
      )}

      {/* Result Preview */}
      {result_preview && (
        <CollapsibleSection 
          title="Result Preview" 
          copyText={result_preview}
        >
          <div style={styles.resultBox}>
            <p style={styles.resultText}>{result_preview}</p>
          </div>
        </CollapsibleSection>
      )}

      {/* Child Trace Link */}
      {child_trace_id && (
        <div style={styles.traceSection}>
          <span style={styles.traceLabel}>Child Trace:</span>
          <div style={styles.traceLink}>
            <code style={styles.traceId}>{child_trace_id}</code>
            {onViewChildTrace && (
              <button 
                style={styles.viewButton}
                onClick={() => onViewChildTrace(child_trace_id)}
              >
                View Trace →
              </button>
            )}
          </div>
        </div>
      )}
    </div>
  );
}

const styles = {
  container: {
    padding: '8px 0',
  },
  header: {
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: '16px',
    padding: '12px',
    backgroundColor: '#141414',
    borderRadius: '8px',
  },
  agentBadge: {
    display: 'flex',
    alignItems: 'center',
    gap: '12px',
  },
  agentIcon: {
    fontSize: '24px',
  },
  agentInfo: {
    display: 'flex',
    flexDirection: 'column',
    gap: '2px',
  },
  agentName: {
    fontSize: '14px',
    fontWeight: 600,
    color: '#e0e0e0',
  },
  agentId: {
    fontSize: '11px',
    color: '#6b7280',
    fontFamily: 'monospace',
  },
  timeoutBadge: {
    fontSize: '11px',
    padding: '4px 10px',
    backgroundColor: 'rgba(245, 158, 11, 0.2)',
    color: '#f59e0b',
    borderRadius: '4px',
  },
  queryBox: {
    backgroundColor: '#141414',
    borderRadius: '8px',
    padding: '16px',
    borderLeft: '3px solid #3b82f6',
  },
  queryText: {
    margin: 0,
    fontSize: '13px',
    color: '#e0e0e0',
    lineHeight: 1.6,
    whiteSpace: 'pre-wrap',
    wordBreak: 'break-word',
  },
  resultBox: {
    backgroundColor: '#141414',
    borderRadius: '8px',
    padding: '16px',
    borderLeft: '3px solid #10b981',
  },
  resultText: {
    margin: 0,
    fontSize: '13px',
    color: '#e0e0e0',
    lineHeight: 1.6,
    whiteSpace: 'pre-wrap',
    wordBreak: 'break-word',
  },
  traceSection: {
    marginTop: '16px',
    padding: '12px',
    backgroundColor: '#141414',
    borderRadius: '8px',
  },
  traceLabel: {
    fontSize: '11px',
    color: '#6b7280',
    marginBottom: '8px',
    display: 'block',
  },
  traceLink: {
    display: 'flex',
    alignItems: 'center',
    gap: '12px',
  },
  traceId: {
    fontSize: '12px',
    color: '#9ca3af',
    fontFamily: 'monospace',
    backgroundColor: '#0d0d0d',
    padding: '6px 10px',
    borderRadius: '4px',
    flex: 1,
  },
  viewButton: {
    padding: '6px 12px',
    backgroundColor: '#3b82f6',
    color: '#fff',
    border: 'none',
    borderRadius: '4px',
    fontSize: '12px',
    fontWeight: 500,
    cursor: 'pointer',
    transition: 'background-color 0.2s ease',
    ':hover': {
      backgroundColor: '#2563eb',
    },
  },
};

export default SubAgentDetail;
