import React from 'react';

const stepTypeConfig = {
  input: { 
    icon: '📥', 
    color: '#3b82f6', 
    label: 'User Input',
    description: 'User message received'
  },
  context_build: { 
    icon: '📚', 
    color: '#6366f1', 
    label: 'Context Building',
    description: 'Loading history, skills, and memory'
  },
  llm_call: { 
    icon: '🤖', 
    color: '#8b5cf6', 
    label: 'LLM Processing',
    description: 'AI model processing'
  },
  tool_call: { 
    icon: '🔧', 
    color: '#f59e0b', 
    label: 'Tool Execution',
    description: 'Executing tools'
  },
  tool_result: { 
    icon: '📤', 
    color: '#10b981', 
    label: 'Tool Result',
    description: 'Tool execution result'
  },
  memory_update: { 
    icon: '🧠', 
    color: '#ec4899', 
    label: 'Memory Update',
    description: 'Updating conversation memory'
  },
  output: { 
    icon: '✅', 
    color: '#10b981', 
    label: 'Response Output',
    description: 'Final response sent'
  },
  error: { 
    icon: '❌', 
    color: '#ef4444', 
    label: 'Error',
    description: 'An error occurred'
  },
  thinking: { 
    icon: '💭', 
    color: '#6b7280', 
    label: 'Processing',
    description: 'Internal processing'
  },
};

const statusConfig = {
  pending: { color: '#9ca3af', bg: 'rgba(156, 163, 175, 0.1)', icon: '⏳' },
  running: { color: '#3b82f6', bg: 'rgba(59, 130, 246, 0.1)', icon: '🔄' },
  success: { color: '#10b981', bg: 'rgba(16, 185, 129, 0.1)', icon: '✓' },
  error: { color: '#ef4444', bg: 'rgba(239, 68, 68, 0.1)', icon: '✗' },
};

function WorkflowVisualizer({ steps, onStepClick, selectedStep }) {
  if (!steps || steps.length === 0) {
    return (
      <div style={styles.empty}>
        <div style={styles.emptyIcon}>🔍</div>
        <p style={styles.emptyText}>No execution data yet</p>
        <p style={styles.emptySubtext}>Send a message to see the workflow</p>
      </div>
    );
  }

  // Group steps by type for better visualization
  const groupedSteps = groupSteps(steps);

  return (
    <div style={styles.container}>
      <div style={styles.workflow}>
        {groupedSteps.map((group, groupIndex) => (
          <div key={groupIndex} style={styles.group}>
            {group.map((step, stepIndex) => {
              const config = stepTypeConfig[step.type] || stepTypeConfig.thinking;
              const status = statusConfig[step.status] || statusConfig.pending;
              const isSelected = selectedStep?.id === step.id;
              const isLast = groupIndex === groupedSteps.length - 1 && stepIndex === group.length - 1;

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
                  {/* Connection line */}
                  {!isLast && <div style={styles.connector} />}

                  {/* Step number badge */}
                  <div style={styles.stepNumber}>
                    {groupIndex * 10 + stepIndex + 1}
                  </div>

                  {/* Step icon */}
                  <div
                    style={{
                      ...styles.iconContainer,
                      backgroundColor: config.color,
                      boxShadow: `0 0 20px ${config.color}40`,
                    }}
                  >
                    <span style={styles.icon}>{config.icon}</span>
                  </div>

                  {/* Step content */}
                  <div style={styles.content}>
                    <div style={styles.header}>
                      <div style={styles.titleRow}>
                        <span style={styles.type}>{config.label}</span>
                        <span
                          style={{
                            ...styles.status,
                            color: status.color,
                            backgroundColor: status.bg,
                          }}
                        >
                          {status.icon} {step.status}
                        </span>
                      </div>
                      <span style={styles.description}>{config.description}</span>
                    </div>

                    {/* Step details preview */}
                    <div style={styles.details}>
                      {step.content && (
                        <p style={styles.contentPreview}>
                          {step.content.substring(0, 150)}
                          {step.content.length > 150 ? '...' : ''}
                        </p>
                      )}

                      {/* Metrics */}
                      <div style={styles.metrics}>
                        {step.tokens_input > 0 && (
                          <span style={styles.metric}>
                            <span style={styles.metricIcon}>📊</span>
                            {(step.tokens_input + step.tokens_output).toLocaleString()} tokens
                          </span>
                        )}
                        {step.latency_ms > 0 && (
                          <span style={styles.metric}>
                            <span style={styles.metricIcon}>⏱️</span>
                            {step.latency_ms.toFixed(1)}ms
                          </span>
                        )}
                        {step.tool_call && (
                          <span style={{ ...styles.metric, color: '#f59e0b' }}>
                            <span style={styles.metricIcon}>🔧</span>
                            {step.tool_call.name}
                          </span>
                        )}
                      </div>
                    </div>
                  </div>

                  {/* Arrow indicator */}
                  {!isLast && (
                    <div style={styles.arrow}>↓</div>
                  )}
                </div>
              );
            })}
          </div>
        ))}
      </div>
    </div>
  );
}

// Group related steps together
function groupSteps(steps) {
  const groups = [];
  let currentGroup = [];
  
  steps.forEach((step, index) => {
    currentGroup.push({ ...step, index });
    
    // Start a new group after output or error, or if we have multiple LLM/tool calls
    if (step.type === 'output' || step.type === 'error') {
      groups.push([...currentGroup]);
      currentGroup = [];
    } else if (step.type === 'tool_result' && index < steps.length - 1 && steps[index + 1].type === 'llm_call') {
      groups.push([...currentGroup]);
      currentGroup = [];
    }
  });
  
  if (currentGroup.length > 0) {
    groups.push(currentGroup);
  }
  
  return groups;
}

const styles = {
  container: {
    padding: '20px',
    overflowY: 'auto',
    height: '100%',
  },
  workflow: {
    display: 'flex',
    flexDirection: 'column',
    gap: '16px',
  },
  group: {
    display: 'flex',
    flexDirection: 'column',
    gap: '12px',
  },
  step: {
    position: 'relative',
    padding: '16px 20px',
    borderRadius: '12px',
    border: '2px solid transparent',
    cursor: 'pointer',
    transition: 'all 0.2s ease',
    display: 'flex',
    alignItems: 'flex-start',
    gap: '16px',
    ':hover': {
      backgroundColor: '#222',
    },
  },
  connector: {
    position: 'absolute',
    left: '39px',
    top: '56px',
    width: '2px',
    height: 'calc(100% + 16px)',
    background: 'linear-gradient(to bottom, #333 50%, transparent)',
    zIndex: 0,
  },
  stepNumber: {
    position: 'absolute',
    left: '-8px',
    top: '-8px',
    width: '20px',
    height: '20px',
    borderRadius: '50%',
    backgroundColor: '#333',
    color: '#999',
    fontSize: '10px',
    fontWeight: 'bold',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    zIndex: 2,
  },
  iconContainer: {
    width: '40px',
    height: '40px',
    borderRadius: '50%',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    flexShrink: 0,
    zIndex: 1,
  },
  icon: {
    fontSize: '18px',
  },
  content: {
    flex: 1,
    minWidth: 0,
  },
  header: {
    marginBottom: '8px',
  },
  titleRow: {
    display: 'flex',
    alignItems: 'center',
    gap: '12px',
    marginBottom: '4px',
  },
  type: {
    fontSize: '14px',
    fontWeight: 600,
    color: '#e0e0e0',
  },
  status: {
    fontSize: '11px',
    padding: '4px 10px',
    borderRadius: '4px',
    fontWeight: 600,
    textTransform: 'uppercase',
  },
  description: {
    fontSize: '12px',
    color: '#6b7280',
  },
  details: {
    marginTop: '8px',
  },
  contentPreview: {
    fontSize: '13px',
    color: '#9ca3af',
    lineHeight: 1.5,
    marginBottom: '8px',
    fontFamily: 'monospace',
    backgroundColor: '#0d0d0d',
    padding: '10px',
    borderRadius: '6px',
    border: '1px solid #222',
  },
  metrics: {
    display: 'flex',
    gap: '12px',
    flexWrap: 'wrap',
  },
  metric: {
    fontSize: '12px',
    padding: '4px 10px',
    backgroundColor: 'rgba(255,255,255,0.05)',
    borderRadius: '4px',
    color: '#9ca3af',
    display: 'flex',
    alignItems: 'center',
    gap: '4px',
  },
  metricIcon: {
    fontSize: '11px',
  },
  arrow: {
    position: 'absolute',
    left: '39px',
    bottom: '-20px',
    color: '#444',
    fontSize: '14px',
    zIndex: 1,
  },
  empty: {
    height: '100%',
    display: 'flex',
    flexDirection: 'column',
    alignItems: 'center',
    justifyContent: 'center',
    color: '#6b7280',
    padding: '40px',
  },
  emptyIcon: {
    fontSize: '48px',
    marginBottom: '16px',
    opacity: 0.5,
  },
  emptyText: {
    fontSize: '16px',
    fontWeight: 600,
    color: '#9ca3af',
    marginBottom: '8px',
  },
  emptySubtext: {
    fontSize: '13px',
    color: '#6b7280',
  },
};

export default WorkflowVisualizer;