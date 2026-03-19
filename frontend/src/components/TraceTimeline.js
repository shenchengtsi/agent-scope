import React from 'react';

const stepTypeConfig = {
  input: { icon: '📥', color: '#3b82f6', label: 'Input' },
  llm_call: { icon: '🤖', color: '#8b5cf6', label: 'LLM' },
  tool_call: { icon: '🔧', color: '#f59e0b', label: 'Tool' },
  tool_result: { icon: '📤', color: '#10b981', label: 'Result' },
  output: { icon: '✅', color: '#10b981', label: 'Output' },
  error: { icon: '❌', color: '#ef4444', label: 'Error' },
  thinking: { icon: '💭', color: '#6b7280', label: 'Thinking' },
};

const statusConfig = {
  pending: { color: '#9ca3af', bg: 'rgba(156, 163, 175, 0.1)' },
  running: { color: '#3b82f6', bg: 'rgba(59, 130, 246, 0.1)' },
  success: { color: '#10b981', bg: 'rgba(16, 185, 129, 0.1)' },
  error: { color: '#ef4444', bg: 'rgba(239, 68, 68, 0.1)' },
};

function TraceTimeline({ steps, onStepClick, selectedStep, traceStats }) {
  if (!steps || steps.length === 0) {
    return (
      <div style={styles.empty}>
        <p>No execution steps yet</p>
      </div>
    );
  }

  return (
    <div style={styles.container}>
      <div style={styles.timeline}>
        {steps.map((step, index) => {
          const config = stepTypeConfig[step.type] || stepTypeConfig.thinking;
          const status = statusConfig[step.status] || statusConfig.pending;
          const isSelected = selectedStep?.id === step.id;

          return (
            <div
              key={step.id}
              style={{
                ...styles.step,
                borderColor: isSelected ? config.color : 'transparent',
                backgroundColor: isSelected ? `${config.color}15` : '#1a1a1a',
              }}
              onClick={() => onStepClick(step)}
            >
              {/* Timeline line */}
              {index < steps.length - 1 && (
                <div style={styles.connector} />
              )}

              {/* Step indicator */}
              <div
                style={{
                  ...styles.indicator,
                  backgroundColor: config.color,
                  boxShadow: `0 0 12px ${config.color}50`,
                }}
              >
                <span style={styles.icon}>{config.icon}</span>
              </div>

              {/* Step content */}
              <div style={styles.content}>
                <div style={styles.header}>
                  <span style={styles.type}>{config.label}</span>
                  <span
                    style={{
                      ...styles.status,
                      color: status.color,
                      backgroundColor: status.bg,
                    }}
                  >
                    {step.status}
                  </span>
                </div>

                <p style={styles.description}>
                  {step.content?.substring(0, 120)}
                  {step.content?.length > 120 ? '...' : ''}
                </p>

                <div style={styles.meta}>
                  {/* For output step, show trace totals */}
                  {step.type === 'output' && traceStats && (
                    <>
                      <span style={{ ...styles.badge, color: '#3b82f6' }}>
                        📥 {traceStats.totalTokensIn?.toLocaleString() || 0} in
                      </span>
                      <span style={{ ...styles.badge, color: '#10b981' }}>
                        📤 {traceStats.totalTokensOut?.toLocaleString() || 0} out
                      </span>
                      <span style={{ ...styles.badge, color: '#f59e0b' }}>
                        ⏱️ {(traceStats.totalLatency / 1000)?.toFixed(2) || 0}s
                      </span>
                    </>
                  )}
                  
                  {/* Regular step metrics */}
                  {step.type !== 'output' && step.tokens_input > 0 && (
                    <span style={styles.badge}>
                      📊 {(step.tokens_input + step.tokens_output).toLocaleString()} tokens
                    </span>
                  )}
                  {step.type !== 'output' && step.latency_ms > 0 && (
                    <span style={styles.badge}>
                      ⏱️ {step.latency_ms.toFixed(0)}ms
                    </span>
                  )}
                  {step.tool_call && (
                    <span style={{ ...styles.badge, color: '#f59e0b' }}>
                      🔧 {step.tool_call.name}
                    </span>
                  )}
                </div>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}

const styles = {
  container: {
    padding: '16px',
    overflowY: 'auto',
    height: '100%',
  },
  timeline: {
    position: 'relative',
    paddingLeft: '24px',
  },
  step: {
    position: 'relative',
    padding: '16px',
    marginBottom: '12px',
    borderRadius: '12px',
    border: '2px solid transparent',
    cursor: 'pointer',
    transition: 'all 0.2s ease',
  },
  connector: {
    position: 'absolute',
    left: '27px',
    top: '48px',
    width: '2px',
    height: 'calc(100% + 12px)',
    background: 'linear-gradient(to bottom, #333, #333)',
    zIndex: 0,
  },
  indicator: {
    position: 'absolute',
    left: '-12px',
    top: '16px',
    width: '32px',
    height: '32px',
    borderRadius: '50%',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    zIndex: 1,
  },
  icon: {
    fontSize: '14px',
  },
  content: {
    marginLeft: '16px',
  },
  header: {
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: '8px',
  },
  type: {
    fontSize: '14px',
    fontWeight: 600,
    color: '#e0e0e0',
  },
  status: {
    fontSize: '11px',
    padding: '4px 8px',
    borderRadius: '4px',
    textTransform: 'uppercase',
    fontWeight: 600,
  },
  description: {
    fontSize: '13px',
    color: '#9ca3af',
    lineHeight: 1.5,
    marginBottom: '8px',
    fontFamily: 'monospace',
  },
  meta: {
    display: 'flex',
    gap: '8px',
    flexWrap: 'wrap',
  },
  badge: {
    fontSize: '11px',
    padding: '4px 8px',
    backgroundColor: 'rgba(255,255,255,0.05)',
    borderRadius: '4px',
    color: '#9ca3af',
  },
  empty: {
    padding: '40px',
    textAlign: 'center',
    color: '#6b7280',
  },
};

export default TraceTimeline;