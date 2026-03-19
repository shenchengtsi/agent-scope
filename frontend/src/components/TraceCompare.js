import React from 'react';

function TraceCompare({ trace1, trace2, onClose }) {
  if (!trace1 || !trace2) return null;

  // Calculate differences
  const latency1 = trace1.total_latency_ms || 0;
  const latency2 = trace2.total_latency_ms || 0;
  const latencyDiff = latency2 - latency1;
  const latencyDiffPercent = latency1 > 0 ? (latencyDiff / latency1) * 100 : 0;

  const tokens1 = trace1.total_tokens || 0;
  const tokens2 = trace2.total_tokens || 0;
  const tokensDiff = tokens2 - tokens1;
  const tokensDiffPercent = tokens1 > 0 ? (tokensDiff / tokens1) * 100 : 0;

  const steps1 = trace1.steps?.length || 0;
  const steps2 = trace2.steps?.length || 0;
  const stepsDiff = steps2 - steps1;

  const cost1 = trace1.cost_estimate || 0;
  const cost2 = trace2.cost_estimate || 0;
  const costDiff = cost2 - cost1;

  const llmCalls1 = trace1.llm_call_count || 0;
  const llmCalls2 = trace2.llm_call_count || 0;
  const llmCallsDiff = llmCalls2 - llmCalls1;

  const toolCalls1 = trace1.tool_call_count || 0;
  const toolCalls2 = trace2.tool_call_count || 0;
  const toolCallsDiff = toolCalls2 - toolCalls1;

  const DiffBadge = ({ value, unit = '' }) => {
    const isPositive = value > 0;
    const isNegative = value < 0;
    const isZero = value === 0;

    if (isZero) {
      return <span style={styles.diffBadgeZero}>0{unit}</span>;
    }

    return (
      <span style={{
        ...styles.diffBadge,
        color: isPositive ? '#ef4444' : '#10b981',
        backgroundColor: isPositive ? 'rgba(239, 68, 68, 0.1)' : 'rgba(16, 185, 129, 0.1)',
      }}>
        {isPositive ? '+' : ''}{value.toFixed(2)}{unit}
        {unit === '%' ? '' : ` (${isPositive ? '+' : ''}${((value / (isPositive ? (unit === 'ms' ? latency1 : tokens1) : Math.abs(value))) * 100).toFixed(1)}%)`}
      </span>
    );
  };

  return (
    <div style={styles.overlay}>
      <div style={styles.container}>
        {/* Header */}
        <div style={styles.header}>
          <h2 style={styles.title}>🔍 Trace Comparison</h2>
          <button style={styles.closeButton} onClick={onClose}>✕</button>
        </div>

        {/* Trace Headers */}
        <div style={styles.traceHeaders}>
          <div style={styles.traceHeader}>
            <span style={styles.traceLabel}>Trace A</span>
            <code style={styles.traceId}>{trace1.id}</code>
            <span style={{
              ...styles.statusBadge,
              color: trace1.status === 'success' ? '#10b981' : trace1.status === 'error' ? '#ef4444' : '#9ca3af',
              backgroundColor: trace1.status === 'success' ? 'rgba(16, 185, 129, 0.1)' : trace1.status === 'error' ? 'rgba(239, 68, 68, 0.1)' : 'rgba(156, 163, 175, 0.1)',
            }}>
              {trace1.status}
            </span>
          </div>
          <div style={styles.vsBadge}>VS</div>
          <div style={styles.traceHeader}>
            <span style={styles.traceLabel}>Trace B</span>
            <code style={styles.traceId}>{trace2.id}</code>
            <span style={{
              ...styles.statusBadge,
              color: trace2.status === 'success' ? '#10b981' : trace2.status === 'error' ? '#ef4444' : '#9ca3af',
              backgroundColor: trace2.status === 'success' ? 'rgba(16, 185, 129, 0.1)' : trace2.status === 'error' ? 'rgba(239, 68, 68, 0.1)' : 'rgba(156, 163, 175, 0.1)',
            }}>
              {trace2.status}
            </span>
          </div>
        </div>

        {/* Comparison Grid */}
        <div style={styles.comparisonGrid}>
          <ComparisonRow
            label="Latency"
            value1={`${latency1.toFixed(0)}ms`}
            value2={`${latency2.toFixed(0)}ms`}
            diff={<DiffBadge value={latencyDiff} />}
          />
          <ComparisonRow
            label="Tokens"
            value1={tokens1.toLocaleString()}
            value2={tokens2.toLocaleString()}
            diff={<DiffBadge value={tokensDiff} />}
          />
          <ComparisonRow
            label="Steps"
            value1={steps1}
            value2={steps2}
            diff={<DiffBadge value={stepsDiff} />}
          />
          <ComparisonRow
            label="Est. Cost"
            value1={`$${cost1.toFixed(4)}`}
            value2={`$${cost2.toFixed(4)}`}
            diff={<DiffBadge value={costDiff} />}
          />
          <ComparisonRow
            label="LLM Calls"
            value1={llmCalls1}
            value2={llmCalls2}
            diff={<DiffBadge value={llmCallsDiff} />}
          />
          <ComparisonRow
            label="Tool Calls"
            value1={toolCalls1}
            value2={toolCalls2}
            diff={<DiffBadge value={toolCallsDiff} />}
          />
        </div>

        {/* Steps Comparison */}
        <div style={styles.stepsSection}>
          <h3 style={styles.sectionTitle}>Steps Breakdown</h3>
          <StepsComparison trace1={trace1} trace2={trace2} />
        </div>
      </div>
    </div>
  );
}

function ComparisonRow({ label, value1, value2, diff }) {
  return (
    <div style={styles.row}>
      <div style={styles.rowLabel}>{label}</div>
      <div style={styles.rowValues}>
        <div style={styles.rowValue}>{value1}</div>
        <div style={styles.rowDiff}>{diff}</div>
        <div style={styles.rowValue}>{value2}</div>
      </div>
    </div>
  );
}

function StepsComparison({ trace1, trace2 }) {
  const steps1 = trace1.steps || [];
  const steps2 = trace2.steps || [];
  const maxSteps = Math.max(steps1.length, steps2.length);

  if (maxSteps === 0) {
    return <p style={styles.emptyText}>No steps to compare</p>;
  }

  const getStepTypeColor = (type) => {
    const colors = {
      input: '#3b82f6',
      llm_call: '#8b5cf6',
      tool_call: '#f59e0b',
      tool_result: '#10b981',
      output: '#10b981',
      error: '#ef4444',
      thinking: '#6b7280',
      skill_loading: '#06b6d4',
      prompt_build: '#6366f1',
      tool_selection: '#f59e0b',
      memory_operation: '#ec4899',
      subagent_call: '#8b5cf6',
      reasoning: '#6366f1',
    };
    return colors[type] || '#6b7280';
  };

  return (
    <div style={styles.stepsList}>
      {Array.from({ length: maxSteps }).map((_, index) => {
        const step1 = steps1[index];
        const step2 = steps2[index];
        const isDifferent = step1?.type !== step2?.type || 
                          step1?.status !== step2?.status;

        return (
          <div 
            key={index} 
            style={{
              ...styles.stepRow,
              backgroundColor: isDifferent ? 'rgba(245, 158, 11, 0.1)' : 'transparent',
            }}
          >
            <span style={styles.stepIndex}>{index + 1}</span>
            <div style={styles.stepSide}>
              {step1 ? (
                <>
                  <span style={{
                    ...styles.stepType,
                    color: getStepTypeColor(step1.type),
                    backgroundColor: `${getStepTypeColor(step1.type)}15`,
                  }}>
                    {step1.type}
                  </span>
                  <span style={{
                    ...styles.stepStatus,
                    color: step1.status === 'success' ? '#10b981' : step1.status === 'error' ? '#ef4444' : '#9ca3af',
                  }}>
                    {step1.status}
                  </span>
                </>
              ) : (
                <span style={styles.noStep}>-</span>
              )}
            </div>
            <div style={styles.stepSide}>
              {step2 ? (
                <>
                  <span style={{
                    ...styles.stepType,
                    color: getStepTypeColor(step2.type),
                    backgroundColor: `${getStepTypeColor(step2.type)}15`,
                  }}>
                    {step2.type}
                  </span>
                  <span style={{
                    ...styles.stepStatus,
                    color: step2.status === 'success' ? '#10b981' : step2.status === 'error' ? '#ef4444' : '#9ca3af',
                  }}>
                    {step2.status}
                  </span>
                </>
              ) : (
                <span style={styles.noStep}>-</span>
              )}
            </div>
          </div>
        );
      })}
    </div>
  );
}

const styles = {
  overlay: {
    position: 'fixed',
    top: 0,
    left: 0,
    right: 0,
    bottom: 0,
    backgroundColor: 'rgba(0, 0, 0, 0.8)',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    zIndex: 1000,
    padding: '20px',
  },
  container: {
    backgroundColor: '#0d0d0d',
    borderRadius: '12px',
    width: '100%',
    maxWidth: '900px',
    maxHeight: '90vh',
    overflow: 'auto',
    border: '1px solid #333',
  },
  header: {
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'center',
    padding: '20px',
    borderBottom: '1px solid #222',
  },
  title: {
    margin: 0,
    fontSize: '18px',
    fontWeight: 600,
    color: '#e0e0e0',
  },
  closeButton: {
    background: 'none',
    border: 'none',
    color: '#6b7280',
    fontSize: '20px',
    cursor: 'pointer',
    padding: '4px',
    ':hover': {
      color: '#e0e0e0',
    },
  },
  traceHeaders: {
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'space-between',
    padding: '16px 20px',
    backgroundColor: '#141414',
    gap: '20px',
  },
  traceHeader: {
    flex: 1,
    display: 'flex',
    flexDirection: 'column',
    gap: '6px',
  },
  traceLabel: {
    fontSize: '11px',
    color: '#6b7280',
    textTransform: 'uppercase',
  },
  traceId: {
    fontSize: '13px',
    color: '#9ca3af',
    fontFamily: 'monospace',
  },
  statusBadge: {
    fontSize: '10px',
    padding: '2px 8px',
    borderRadius: '4px',
    fontWeight: 600,
    alignSelf: 'flex-start',
  },
  vsBadge: {
    fontSize: '12px',
    fontWeight: 700,
    color: '#6366f1',
    backgroundColor: 'rgba(99, 102, 241, 0.1)',
    padding: '6px 12px',
    borderRadius: '20px',
  },
  comparisonGrid: {
    padding: '20px',
  },
  row: {
    display: 'flex',
    alignItems: 'center',
    padding: '12px 0',
    borderBottom: '1px solid #222',
    ':last-child': {
      borderBottom: 'none',
    },
  },
  rowLabel: {
    width: '100px',
    fontSize: '12px',
    color: '#6b7280',
    fontWeight: 500,
  },
  rowValues: {
    flex: 1,
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'space-between',
    gap: '20px',
  },
  rowValue: {
    flex: 1,
    fontSize: '14px',
    color: '#e0e0e0',
    fontFamily: 'monospace',
    textAlign: 'center',
  },
  rowDiff: {
    minWidth: '120px',
    textAlign: 'center',
  },
  diffBadge: {
    fontSize: '11px',
    padding: '4px 10px',
    borderRadius: '4px',
    fontWeight: 500,
  },
  diffBadgeZero: {
    fontSize: '11px',
    padding: '4px 10px',
    borderRadius: '4px',
    fontWeight: 500,
    color: '#6b7280',
    backgroundColor: 'rgba(107, 114, 128, 0.1)',
  },
  stepsSection: {
    padding: '20px',
    borderTop: '1px solid #222',
  },
  sectionTitle: {
    fontSize: '14px',
    fontWeight: 600,
    color: '#e0e0e0',
    margin: '0 0 16px 0',
  },
  emptyText: {
    fontSize: '13px',
    color: '#6b7280',
    textAlign: 'center',
  },
  stepsList: {
    display: 'flex',
    flexDirection: 'column',
    gap: '4px',
  },
  stepRow: {
    display: 'flex',
    alignItems: 'center',
    padding: '8px 12px',
    borderRadius: '6px',
    gap: '12px',
  },
  stepIndex: {
    width: '24px',
    fontSize: '11px',
    color: '#6b7280',
    textAlign: 'center',
  },
  stepSide: {
    flex: 1,
    display: 'flex',
    alignItems: 'center',
    gap: '8px',
  },
  stepType: {
    fontSize: '10px',
    padding: '2px 6px',
    borderRadius: '4px',
    fontWeight: 600,
    textTransform: 'uppercase',
  },
  stepStatus: {
    fontSize: '10px',
    fontWeight: 500,
  },
  noStep: {
    fontSize: '12px',
    color: '#4b5563',
  },
};

export default TraceCompare;
