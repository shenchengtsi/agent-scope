import React from 'react';
import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer,
  RadarChart, PolarGrid, PolarAngleAxis, PolarRadiusAxis, Radar
} from 'recharts';

function TraceCompare({ trace1, trace2, onClose }) {
  if (!trace1 || !trace2) return null;

  // Calculate metrics
  const latency1 = trace1.total_latency_ms || 0;
  const latency2 = trace2.total_latency_ms || 0;
  const latencyDiff = latency2 - latency1;

  const tokens1 = trace1.total_tokens || 0;
  const tokens2 = trace2.total_tokens || 0;
  const tokensDiff = tokens2 - tokens1;

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

  // Calculate tokens per dollar efficiency
  const efficiency1 = cost1 > 0 ? tokens1 / cost1 : 0;
  const efficiency2 = cost2 > 0 ? tokens2 / cost2 : 0;

  // Radar chart data (normalized)
  const maxLatency = Math.max(latency1, latency2, 1);
  const maxTokens = Math.max(tokens1, tokens2, 1);
  const maxSteps = Math.max(steps1, steps2, 1);
  const maxCost = Math.max(cost1, cost2, 0.001);

  const radarData = [
    { metric: 'Latency', A: (latency1 / maxLatency) * 100, B: (latency2 / maxLatency) * 100, fullMark: 100 },
    { metric: 'Tokens', A: (tokens1 / maxTokens) * 100, B: (tokens2 / maxTokens) * 100, fullMark: 100 },
    { metric: 'Steps', A: (steps1 / maxSteps) * 100, B: (steps2 / maxSteps) * 100, fullMark: 100 },
    { metric: 'Cost', A: (cost1 / maxCost) * 100, B: (cost2 / maxCost) * 100, fullMark: 100 },
  ];

  // Bar chart data
  const comparisonData = [
    { name: 'Latency (ms)', trace1: latency1, trace2: latency2 },
    { name: 'Tokens', trace1: tokens1, trace2: tokens2 },
    { name: 'Steps', trace1: steps1, trace2: steps2 },
    { name: 'LLM Calls', trace1: llmCalls1, trace2: llmCalls2 },
    { name: 'Tool Calls', trace1: toolCalls1, trace2: toolCalls2 },
  ];

  const DiffBadge = ({ value, unit = '', inverse = false }) => {
    const isPositive = value > 0;
    const isZero = value === 0;

    if (isZero) {
      return <span style={styles.diffBadgeZero}>0{unit}</span>;
    }

    // For latency/cost, lower is better (green when negative)
    // For tokens/steps, context matters
    const isGood = inverse ? isPositive : !isPositive;

    return (
      <span style={{
        ...styles.diffBadge,
        color: isGood ? '#10b981' : '#ef4444',
        backgroundColor: isGood ? 'rgba(16, 185, 129, 0.1)' : 'rgba(239, 68, 68, 0.1)',
      }}>
        {isPositive ? '+' : ''}{value.toFixed(2)}{unit}
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
            <div style={styles.traceMeta}>
              <span style={{
                ...styles.statusBadge,
                color: trace1.status === 'success' ? '#10b981' : trace1.status === 'error' ? '#ef4444' : '#9ca3af',
                backgroundColor: trace1.status === 'success' ? 'rgba(16, 185, 129, 0.1)' : trace1.status === 'error' ? 'rgba(239, 68, 68, 0.1)' : 'rgba(156, 163, 175, 0.1)',
              }}>
                {trace1.status}
              </span>
              <span style={styles.timestamp}>{formatTime(trace1.start_time)}</span>
            </div>
          </div>
          <div style={styles.vsBadge}>VS</div>
          <div style={styles.traceHeader}>
            <span style={styles.traceLabel}>Trace B</span>
            <code style={styles.traceId}>{trace2.id}</code>
            <div style={styles.traceMeta}>
              <span style={{
                ...styles.statusBadge,
                color: trace2.status === 'success' ? '#10b981' : trace2.status === 'error' ? '#ef4444' : '#9ca3af',
                backgroundColor: trace2.status === 'success' ? 'rgba(16, 185, 129, 0.1)' : trace2.status === 'error' ? 'rgba(239, 68, 68, 0.1)' : 'rgba(156, 163, 175, 0.1)',
              }}>
                {trace2.status}
              </span>
              <span style={styles.timestamp}>{formatTime(trace2.start_time)}</span>
            </div>
          </div>
        </div>

        {/* Charts Section */}
        <div style={styles.chartsSection}>
          {/* Radar Chart - Overall Profile */}
          <div style={styles.chartCard}>
            <h3 style={styles.chartTitle}>📊 Performance Profile</h3>
            <ResponsiveContainer width="100%" height={250}>
              <RadarChart cx="50%" cy="50%" outerRadius="70%" data={radarData}>
                <PolarGrid stroke="#333" />
                <PolarAngleAxis dataKey="metric" tick={{ fill: '#9ca3af', fontSize: 11 }} />
                <PolarRadiusAxis angle={90} domain={[0, 100]} tick={false} axisLine={false} />
                <Radar
                  name={trace1.id.slice(0, 8)}
                  dataKey="A"
                  stroke="#3b82f6"
                  strokeWidth={2}
                  fill="#3b82f6"
                  fillOpacity={0.2}
                />
                <Radar
                  name={trace2.id.slice(0, 8)}
                  dataKey="B"
                  stroke="#10b981"
                  strokeWidth={2}
                  fill="#10b981"
                  fillOpacity={0.2}
                />
                <Legend />
                <Tooltip 
                  contentStyle={{ backgroundColor: '#1a1a1a', border: '1px solid #333' }}
                  labelStyle={{ color: '#fff' }}
                />
              </RadarChart>
            </ResponsiveContainer>
          </div>

          {/* Bar Chart - Side by Side */}
          <div style={styles.chartCard}>
            <h3 style={styles.chartTitle}>📈 Metric Comparison</h3>
            <ResponsiveContainer width="100%" height={250}>
              <BarChart data={comparisonData} layout="vertical">
                <CartesianGrid strokeDasharray="3 3" stroke="#333" />
                <XAxis type="number" stroke="#666" fontSize={11} />
                <YAxis dataKey="name" type="category" stroke="#9ca3af" fontSize={11} width={80} />
                <Tooltip 
                  contentStyle={{ backgroundColor: '#1a1a1a', border: '1px solid #333' }}
                  labelStyle={{ color: '#fff' }}
                  formatter={(value) => value.toLocaleString()}
                />
                <Legend />
                <Bar dataKey="trace1" name={`A: ${trace1.id.slice(0, 8)}`} fill="#3b82f6" radius={[0, 4, 4, 0]} />
                <Bar dataKey="trace2" name={`B: ${trace2.id.slice(0, 8)}`} fill="#10b981" radius={[0, 4, 4, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Comparison Grid */}
        <div style={styles.comparisonSection}>
          <h3 style={styles.sectionTitle}>📋 Detailed Metrics</h3>
          <div style={styles.comparisonGrid}>
            <ComparisonRow
              label="Latency"
              value1={`${latency1.toFixed(0)}ms`}
              value2={`${latency2.toFixed(0)}ms`}
              diff={<DiffBadge value={latencyDiff} unit="ms" inverse />}
              hint="Lower is better"
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
              diff={<DiffBadge value={costDiff} inverse />}
              hint="Lower is better"
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
            <ComparisonRow
              label="Efficiency"
              value1={`${efficiency1.toFixed(0)} tok/$`}
              value2={`${efficiency2.toFixed(0)} tok/$`}
              diff={<DiffBadge value={efficiency2 - efficiency1} />}
              hint="Tokens per dollar"
            />
          </div>
        </div>

        {/* Steps Comparison */}
        <div style={styles.stepsSection}>
          <h3 style={styles.sectionTitle}>🔄 Steps Breakdown</h3>
          <StepsComparison trace1={trace1} trace2={trace2} />
        </div>
      </div>
    </div>
  );
}

function formatTime(timestamp) {
  if (!timestamp) return '-';
  const date = new Date(timestamp);
  return date.toLocaleString('zh-CN', { 
    month: 'short', 
    day: 'numeric', 
    hour: '2-digit', 
    minute: '2-digit' 
  });
}

function ComparisonRow({ label, value1, value2, diff, hint }) {
  return (
    <div style={styles.row}>
      <div style={styles.rowLabel}>
        {label}
        {hint && <span style={styles.rowHint}>{hint}</span>}
      </div>
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

  // Calculate step type distribution
  const typeCount1 = {};
  const typeCount2 = {};
  steps1.forEach(s => { typeCount1[s.type] = (typeCount1[s.type] || 0) + 1; });
  steps2.forEach(s => { typeCount2[s.type] = (typeCount2[s.type] || 0) + 1; });

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
    <div>
      {/* Step Type Distribution */}
      <div style={styles.typeDistribution}>
        <div style={styles.typeColumn}>
          <h4 style={styles.typeColumnTitle}>Trace A</h4>
          {Object.entries(typeCount1).map(([type, count]) => (
            <div key={type} style={styles.typeItem}>
              <span style={{
                ...styles.typeBadge,
                color: getStepTypeColor(type),
                backgroundColor: `${getStepTypeColor(type)}15`,
              }}>
                {type}
              </span>
              <span style={styles.typeCount}>×{count}</span>
            </div>
          ))}
        </div>
        <div style={styles.typeColumn}>
          <h4 style={styles.typeColumnTitle}>Trace B</h4>
          {Object.entries(typeCount2).map(([type, count]) => (
            <div key={type} style={styles.typeItem}>
              <span style={{
                ...styles.typeBadge,
                color: getStepTypeColor(type),
                backgroundColor: `${getStepTypeColor(type)}15`,
              }}>
                {type}
              </span>
              <span style={styles.typeCount}>×{count}</span>
            </div>
          ))}
        </div>
      </div>

      {/* Step by Step Comparison */}
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
                    {step1.latency_ms > 0 && (
                      <span style={styles.stepLatency}>{step1.latency_ms}ms</span>
                    )}
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
                    {step2.latency_ms > 0 && (
                      <span style={styles.stepLatency}>{step2.latency_ms}ms</span>
                    )}
                  </>
                ) : (
                  <span style={styles.noStep}>-</span>
                )}
              </div>
            </div>
          );
        })}
      </div>
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
    backgroundColor: 'rgba(0, 0, 0, 0.85)',
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
    maxWidth: '1000px',
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
  traceMeta: {
    display: 'flex',
    alignItems: 'center',
    gap: '10px',
  },
  timestamp: {
    fontSize: '11px',
    color: '#6b7280',
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
  chartsSection: {
    display: 'grid',
    gridTemplateColumns: '1fr 1fr',
    gap: '20px',
    padding: '20px',
    borderBottom: '1px solid #222',
  },
  chartCard: {
    backgroundColor: '#141414',
    borderRadius: '8px',
    padding: '16px',
    border: '1px solid #222',
  },
  chartTitle: {
    margin: '0 0 12px 0',
    fontSize: '14px',
    fontWeight: 600,
    color: '#e0e0e0',
  },
  comparisonSection: {
    padding: '20px',
    borderBottom: '1px solid #222',
  },
  sectionTitle: {
    fontSize: '14px',
    fontWeight: 600,
    color: '#e0e0e0',
    margin: '0 0 16px 0',
  },
  comparisonGrid: {
    display: 'flex',
    flexDirection: 'column',
    gap: '8px',
  },
  row: {
    display: 'flex',
    alignItems: 'center',
    padding: '10px 0',
    borderBottom: '1px solid #222',
  },
  rowLabel: {
    width: '120px',
    display: 'flex',
    flexDirection: 'column',
    gap: '2px',
  },
  rowHint: {
    fontSize: '10px',
    color: '#6b7280',
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
    minWidth: '100px',
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
  },
  emptyText: {
    fontSize: '13px',
    color: '#6b7280',
    textAlign: 'center',
  },
  typeDistribution: {
    display: 'grid',
    gridTemplateColumns: '1fr 1fr',
    gap: '20px',
    marginBottom: '16px',
    padding: '12px',
    backgroundColor: '#141414',
    borderRadius: '8px',
  },
  typeColumn: {
    display: 'flex',
    flexDirection: 'column',
    gap: '6px',
  },
  typeColumnTitle: {
    fontSize: '11px',
    color: '#6b7280',
    margin: '0 0 4px 0',
    textTransform: 'uppercase',
  },
  typeItem: {
    display: 'flex',
    alignItems: 'center',
    gap: '8px',
  },
  typeBadge: {
    fontSize: '10px',
    padding: '2px 6px',
    borderRadius: '4px',
    fontWeight: 600,
    textTransform: 'uppercase',
  },
  typeCount: {
    fontSize: '11px',
    color: '#9ca3af',
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
  stepLatency: {
    fontSize: '10px',
    color: '#6b7280',
    fontFamily: 'monospace',
  },
  noStep: {
    fontSize: '12px',
    color: '#4b5563',
  },
};

export default TraceCompare;
