import React, { useEffect, useState } from 'react';

function MetricsCards({ traces }) {
  const [metrics, setMetrics] = useState({
    totalTraces: 0,
    successRate: 0,
    avgLatency: 0,
    totalTokens: 0,
    totalCost: 0,
    llmCalls: 0,
    toolCalls: 0,
  });

  useEffect(() => {
    if (!traces || traces.length === 0) {
      setMetrics({
        totalTraces: 0,
        successRate: 0,
        avgLatency: 0,
        totalTokens: 0,
        totalCost: 0,
        llmCalls: 0,
        toolCalls: 0,
      });
      return;
    }

    const total = traces.length;
    const successful = traces.filter(t => t.status === 'success').length;
    const latencies = traces.map(t => t.total_latency_ms || 0).filter(l => l > 0);
    const tokens = traces.map(t => t.total_tokens || 0);
    const costs = traces.map(t => t.cost_estimate || 0);
    const llmCalls = traces.reduce((sum, t) => sum + (t.llm_call_count || 0), 0);
    const toolCalls = traces.reduce((sum, t) => sum + (t.tool_call_count || 0), 0);

    setMetrics({
      totalTraces: total,
      successRate: (successful / total) * 100,
      avgLatency: latencies.length > 0 ? latencies.reduce((a, b) => a + b, 0) / latencies.length : 0,
      totalTokens: tokens.reduce((a, b) => a + b, 0),
      totalCost: costs.reduce((a, b) => a + b, 0),
      llmCalls,
      toolCalls,
    });
  }, [traces]);

  const cards = [
    {
      label: 'Total Traces',
      value: metrics.totalTraces.toLocaleString(),
      icon: '📊',
      color: '#3b82f6',
    },
    {
      label: 'Success Rate',
      value: `${metrics.successRate.toFixed(1)}%`,
      icon: '✓',
      color: metrics.successRate >= 90 ? '#10b981' : metrics.successRate >= 70 ? '#f59e0b' : '#ef4444',
    },
    {
      label: 'Avg Latency',
      value: `${metrics.avgLatency.toFixed(0)}ms`,
      icon: '⏱️',
      color: metrics.avgLatency < 1000 ? '#10b981' : metrics.avgLatency < 3000 ? '#f59e0b' : '#ef4444',
    },
    {
      label: 'Total Tokens',
      value: metrics.totalTokens >= 1000000 
        ? `${(metrics.totalTokens / 1000000).toFixed(1)}M` 
        : metrics.totalTokens >= 1000 
          ? `${(metrics.totalTokens / 1000).toFixed(1)}K` 
          : metrics.totalTokens.toLocaleString(),
      icon: '📝',
      color: '#8b5cf6',
    },
    {
      label: 'Est. Cost',
      value: `$${metrics.totalCost.toFixed(3)}`,
      icon: '💰',
      color: '#ec4899',
    },
    {
      label: 'LLM Calls',
      value: metrics.llmCalls.toLocaleString(),
      icon: '🤖',
      color: '#6366f1',
    },
  ];

  return (
    <div style={styles.container}>
      {cards.map((card, index) => (
        <div 
          key={index} 
          style={{
            ...styles.card,
            borderColor: `${card.color}30`,
          }}
        >
          <div style={{ ...styles.iconContainer, backgroundColor: `${card.color}15` }}>
            <span style={{ ...styles.icon, color: card.color }}>{card.icon}</span>
          </div>
          <div style={styles.cardContent}>
            <span style={styles.cardLabel}>{card.label}</span>
            <span style={{ ...styles.cardValue, color: card.color }}>{card.value}</span>
          </div>
        </div>
      ))}
    </div>
  );
}

const styles = {
  container: {
    display: 'grid',
    gridTemplateColumns: 'repeat(auto-fit, minmax(140px, 1fr))',
    gap: '12px',
    padding: '16px',
    backgroundColor: '#0d0d0d',
    borderBottom: '1px solid #222',
  },
  card: {
    display: 'flex',
    alignItems: 'center',
    gap: '12px',
    padding: '12px',
    backgroundColor: '#141414',
    borderRadius: '8px',
    border: '1px solid',
    transition: 'transform 0.2s ease, box-shadow 0.2s ease',
    ':hover': {
      transform: 'translateY(-2px)',
      boxShadow: '0 4px 12px rgba(0,0,0,0.3)',
    },
  },
  iconContainer: {
    width: '40px',
    height: '40px',
    borderRadius: '8px',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
  },
  icon: {
    fontSize: '18px',
  },
  cardContent: {
    display: 'flex',
    flexDirection: 'column',
    gap: '2px',
  },
  cardLabel: {
    fontSize: '11px',
    color: '#6b7280',
    textTransform: 'uppercase',
    letterSpacing: '0.5px',
  },
  cardValue: {
    fontSize: '18px',
    fontWeight: 700,
  },
};

export default MetricsCards;
