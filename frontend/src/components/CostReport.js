import React, { useState, useEffect, useMemo } from 'react';
import {
  PieChart, Pie, Cell, ResponsiveContainer, Tooltip, Legend,
  BarChart, Bar, XAxis, YAxis, CartesianGrid
} from 'recharts';

const COLORS = ['#3b82f6', '#10b981', '#f59e0b', '#ef4444', '#8b5cf6', '#ec4899', '#06b6d4', '#6366f1'];

function CostReport({ traces }) {
  const [timeRange, setTimeRange] = useState('24h');

  // Ensure traces is an array
  const tracesArray = useMemo(() => {
    if (!traces) return [];
    if (Array.isArray(traces)) return traces;
    if (traces.traces && Array.isArray(traces.traces)) return traces.traces;
    return [];
  }, [traces]);

  // Filter traces based on time range
  const filteredTraces = useMemo(() => {
    const now = new Date();
    const ranges = {
      '1h': 60 * 60 * 1000,
      '6h': 6 * 60 * 60 * 1000,
      '24h': 24 * 60 * 60 * 1000,
      '7d': 7 * 24 * 60 * 60 * 1000,
      '30d': 30 * 24 * 60 * 60 * 1000,
      'all': Infinity,
    };
    const cutoff = now.getTime() - (ranges[timeRange] || ranges['24h']);
    
    return tracesArray.filter(t => {
      const traceTime = new Date(t.start_time).getTime();
      return traceTime >= cutoff;
    });
  }, [tracesArray, timeRange]);

  // Calculate cost metrics
  const metrics = useMemo(() => {
    const totalCost = filteredTraces.reduce((sum, t) => sum + (t.cost_estimate || 0), 0);
    const totalTokens = filteredTraces.reduce((sum, t) => sum + (t.total_tokens || 0), 0);
    const avgCostPerTrace = filteredTraces.length > 0 ? totalCost / filteredTraces.length : 0;
    const efficiency = totalCost > 0 ? totalTokens / totalCost : 0;

    // Find most expensive trace
    const mostExpensive = filteredTraces.reduce((max, t) => 
      (t.cost_estimate || 0) > (max?.cost_estimate || 0) ? t : max
    , null);

    // Projected monthly cost (based on daily average)
    const daysInRange = timeRange === 'all' ? 30 : 
      { '1h': 1/24, '6h': 0.25, '24h': 1, '7d': 7, '30d': 30 }[timeRange];
    const dailyAvg = daysInRange > 0 ? totalCost / daysInRange : 0;
    const projectedMonthly = dailyAvg * 30;

    return {
      totalCost,
      totalTokens,
      avgCostPerTrace,
      efficiency,
      mostExpensive,
      projectedMonthly,
      traceCount: filteredTraces.length,
    };
  }, [filteredTraces, timeRange]);

  // Cost by trace name
  const costByName = useMemo(() => {
    const grouped = {};
    filteredTraces.forEach(t => {
      const name = t.name || 'Unknown';
      if (!grouped[name]) {
        grouped[name] = { name, cost: 0, count: 0, tokens: 0 };
      }
      grouped[name].cost += t.cost_estimate || 0;
      grouped[name].count += 1;
      grouped[name].tokens += t.total_tokens || 0;
    });
    return Object.values(grouped)
      .sort((a, b) => b.cost - a.cost)
      .slice(0, 10); // Top 10
  }, [filteredTraces]);

  // Cost by tags
  const costByTags = useMemo(() => {
    const grouped = {};
    filteredTraces.forEach(t => {
      (t.tags || []).forEach(tag => {
        if (!grouped[tag]) {
          grouped[tag] = { tag, cost: 0, count: 0 };
        }
        grouped[tag].cost += t.cost_estimate || 0;
        grouped[tag].count += 1;
      });
    });
    return Object.values(grouped)
      .sort((a, b) => b.cost - a.cost)
      .slice(0, 8);
  }, [filteredTraces]);

  // Cost trend by hour/day
  const costTrend = useMemo(() => {
    const grouped = {};
    filteredTraces.forEach(t => {
      const date = new Date(t.start_time);
      let key;
      if (timeRange === '1h' || timeRange === '6h') {
        key = date.toISOString().slice(0, 13) + ':00'; // Hour
      } else if (timeRange === '24h') {
        key = date.toISOString().slice(0, 13) + ':00';
      } else {
        key = date.toISOString().slice(0, 10); // Day
      }
      
      if (!grouped[key]) {
        grouped[key] = { time: key, cost: 0, count: 0 };
      }
      grouped[key].cost += t.cost_estimate || 0;
      grouped[key].count += 1;
    });
    return Object.values(grouped).sort((a, b) => a.time.localeCompare(b.time));
  }, [filteredTraces, timeRange]);

  // Cost efficiency tiers
  const efficiencyTiers = useMemo(() => {
    const tiers = [
      { name: 'High (>50k tok/$)', min: 50000, count: 0, cost: 0 },
      { name: 'Good (10-50k)', min: 10000, max: 50000, count: 0, cost: 0 },
      { name: 'Avg (1-10k)', min: 1000, max: 10000, count: 0, cost: 0 },
      { name: 'Low (<1k)', max: 1000, count: 0, cost: 0 },
    ];

    filteredTraces.forEach(t => {
      const efficiency = t.cost_estimate > 0 ? t.total_tokens / t.cost_estimate : 0;
      const tier = tiers.find(t => 
        (t.min === undefined || efficiency >= t.min) && 
        (t.max === undefined || efficiency < t.max)
      );
      if (tier) {
        tier.count += 1;
        tier.cost += t.cost_estimate || 0;
      }
    });

    return tiers.filter(t => t.count > 0);
  }, [filteredTraces]);

  return (
    <div style={styles.container}>
      {/* Header */}
      <div style={styles.header}>
        <h2 style={styles.title}>💰 Cost Report</h2>
        <select 
          style={styles.select}
          value={timeRange}
          onChange={(e) => setTimeRange(e.target.value)}
        >
          <option value="1h">Last 1 hour</option>
          <option value="6h">Last 6 hours</option>
          <option value="24h">Last 24 hours</option>
          <option value="7d">Last 7 days</option>
          <option value="30d">Last 30 days</option>
          <option value="all">All time</option>
        </select>
      </div>

      {/* Summary Cards */}
      <div style={styles.summaryGrid}>
        <SummaryCard
          title="Total Cost"
          value={`$${metrics.totalCost.toFixed(4)}`}
          subtitle={`${metrics.traceCount} traces`}
          icon="💵"
          color="#ec4899"
        />
        <SummaryCard
          title="Avg per Trace"
          value={`$${metrics.avgCostPerTrace.toFixed(4)}`}
          subtitle="Average cost"
          icon="📊"
          color="#3b82f6"
        />
        <SummaryCard
          title="Efficiency"
          value={`${metrics.efficiency.toFixed(0)}`}
          subtitle="tokens / $"
          icon="⚡"
          color="#10b981"
        />
        <SummaryCard
          title="Projected Monthly"
          value={`$${metrics.projectedMonthly.toFixed(2)}`}
          subtitle="Based on current rate"
          icon="📅"
          color="#f59e0b"
        />
      </div>

      {/* Charts Row 1 */}
      <div style={styles.chartsRow}>
        {/* Cost Trend */}
        <div style={styles.chartCard}>
          <h3 style={styles.chartTitle}>📈 Cost Trend</h3>
          <ResponsiveContainer width="100%" height={200}>
            <BarChart data={costTrend}>
              <CartesianGrid strokeDasharray="3 3" stroke="#222" />
              <XAxis 
                dataKey="time" 
                stroke="#444" 
                fontSize={10}
                tickFormatter={(val) => val.slice(-5)}
              />
              <YAxis 
                stroke="#444" 
                fontSize={10}
                tickFormatter={(val) => `$${val.toFixed(3)}`}
              />
              <Tooltip 
                contentStyle={{ backgroundColor: '#1a1a1a', border: '1px solid #333' }}
                formatter={(val) => `$${val.toFixed(4)}`}
              />
              <Bar dataKey="cost" fill="#ec4899" radius={[4, 4, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </div>

        {/* Cost by Trace Name */}
        <div style={styles.chartCard}>
          <h3 style={styles.chartTitle}>🏷️ Cost by Trace Name (Top 10)</h3>
          <ResponsiveContainer width="100%" height={200}>
            <PieChart>
              <Pie
                data={costByName}
                cx="50%"
                cy="50%"
                innerRadius={40}
                outerRadius={70}
                paddingAngle={2}
                dataKey="cost"
                nameKey="name"
              >
                {costByName.map((entry, index) => (
                  <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                ))}
              </Pie>
              <Tooltip 
                contentStyle={{ backgroundColor: '#1a1a1a', border: '1px solid #333' }}
                formatter={(val, name, props) => [`$${val.toFixed(4)}`, props.payload.name]}
              />
              <Legend fontSize={10} />
            </PieChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* Charts Row 2 */}
      <div style={styles.chartsRow}>
        {/* Cost by Tags */}
        <div style={styles.chartCard}>
          <h3 style={styles.chartTitle}>🏷️ Cost by Tags</h3>
          <div style={styles.tagList}>
            {costByTags.length > 0 ? (
              costByTags.map((tag, index) => (
                <div key={tag.tag} style={styles.tagItem}>
                  <div style={styles.tagInfo}>
                    <span style={styles.tagName}>{tag.tag}</span>
                    <span style={styles.tagCount}>{tag.count} traces</span>
                  </div>
                  <div style={styles.tagBar}>
                    <div 
                      style={{
                        ...styles.tagBarFill,
                        width: `${(tag.cost / (costByTags[0]?.cost || 1)) * 100}%`,
                        backgroundColor: COLORS[index % COLORS.length],
                      }}
                    />
                  </div>
                  <span style={styles.tagCost}>${tag.cost.toFixed(4)}</span>
                </div>
              ))
            ) : (
              <p style={styles.emptyText}>No tags found</p>
            )}
          </div>
        </div>

        {/* Efficiency Tiers */}
        <div style={styles.chartCard}>
          <h3 style={styles.chartTitle}>⚡ Efficiency Distribution</h3>
          <ResponsiveContainer width="100%" height={200}>
            <PieChart>
              <Pie
                data={efficiencyTiers}
                cx="50%"
                cy="50%"
                innerRadius={40}
                outerRadius={70}
                paddingAngle={2}
                dataKey="count"
                nameKey="name"
              >
                {efficiencyTiers.map((entry, index) => (
                  <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                ))}
              </Pie>
              <Tooltip 
                contentStyle={{ backgroundColor: '#1a1a1a', border: '1px solid #333' }}
                formatter={(val, name) => [`${val} traces`, name]}
              />
              <Legend fontSize={10} />
            </PieChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* Cost Details Table */}
      <div style={styles.tableCard}>
        <h3 style={styles.chartTitle}>📋 Cost Details by Trace</h3>
        <div style={styles.tableContainer}>
          <table style={styles.table}>
            <thead>
              <tr>
                <th style={styles.th}>Name</th>
                <th style={styles.th}>Traces</th>
                <th style={styles.th}>Total Cost</th>
                <th style={styles.th}>Avg Cost</th>
                <th style={styles.th}>Total Tokens</th>
                <th style={styles.th}>Efficiency</th>
              </tr>
            </thead>
            <tbody>
              {costByName.map((item) => (
                <tr key={item.name} style={styles.tr}>
                  <td style={styles.td}>{item.name}</td>
                  <td style={styles.td}>{item.count}</td>
                  <td style={{ ...styles.td, color: '#ec4899', fontWeight: 600 }}>
                    ${item.cost.toFixed(4)}
                  </td>
                  <td style={styles.td}>${(item.cost / item.count).toFixed(4)}</td>
                  <td style={styles.td}>{item.tokens.toLocaleString()}</td>
                  <td style={styles.td}>
                    {item.cost > 0 ? (item.tokens / item.cost).toFixed(0) : '∞'} tok/$
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}

function SummaryCard({ title, value, subtitle, icon, color }) {
  return (
    <div style={{
      ...styles.summaryCard,
      borderColor: `${color}30`,
    }}>
      <div style={{
        ...styles.summaryIcon,
        backgroundColor: `${color}15`,
        color: color,
      }}>
        {icon}
      </div>
      <div style={styles.summaryContent}>
        <div style={styles.summaryTitle}>{title}</div>
        <div style={{ ...styles.summaryValue, color }}>{value}</div>
        <div style={styles.summarySubtitle}>{subtitle}</div>
      </div>
    </div>
  );
}

const styles = {
  container: {
    padding: '20px',
    backgroundColor: '#0a0a0a',
    color: '#fff',
  },
  header: {
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: '20px',
  },
  title: {
    margin: 0,
    fontSize: '20px',
    fontWeight: 600,
  },
  select: {
    padding: '8px 12px',
    borderRadius: '6px',
    border: '1px solid #333',
    backgroundColor: '#1a1a1a',
    color: '#fff',
    fontSize: '14px',
  },
  summaryGrid: {
    display: 'grid',
    gridTemplateColumns: 'repeat(auto-fit, minmax(180px, 1fr))',
    gap: '16px',
    marginBottom: '24px',
  },
  summaryCard: {
    display: 'flex',
    alignItems: 'center',
    gap: '16px',
    padding: '16px',
    backgroundColor: '#141414',
    borderRadius: '10px',
    border: '1px solid',
  },
  summaryIcon: {
    width: '44px',
    height: '44px',
    borderRadius: '10px',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    fontSize: '22px',
  },
  summaryContent: {
    display: 'flex',
    flexDirection: 'column',
    gap: '2px',
  },
  summaryTitle: {
    fontSize: '11px',
    color: '#9ca3af',
    textTransform: 'uppercase',
  },
  summaryValue: {
    fontSize: '20px',
    fontWeight: 700,
  },
  summarySubtitle: {
    fontSize: '11px',
    color: '#6b7280',
  },
  chartsRow: {
    display: 'grid',
    gridTemplateColumns: 'repeat(auto-fit, minmax(400px, 1fr))',
    gap: '20px',
    marginBottom: '20px',
  },
  chartCard: {
    backgroundColor: '#141414',
    borderRadius: '10px',
    padding: '16px',
    border: '1px solid #222',
  },
  chartTitle: {
    margin: '0 0 12px 0',
    fontSize: '14px',
    fontWeight: 600,
    color: '#e5e7eb',
  },
  tagList: {
    display: 'flex',
    flexDirection: 'column',
    gap: '10px',
  },
  tagItem: {
    display: 'flex',
    alignItems: 'center',
    gap: '12px',
  },
  tagInfo: {
    width: '100px',
    display: 'flex',
    flexDirection: 'column',
  },
  tagName: {
    fontSize: '12px',
    fontWeight: 500,
    color: '#e5e7eb',
  },
  tagCount: {
    fontSize: '10px',
    color: '#6b7280',
  },
  tagBar: {
    flex: 1,
    height: '6px',
    backgroundColor: '#222',
    borderRadius: '3px',
    overflow: 'hidden',
  },
  tagBarFill: {
    height: '100%',
    borderRadius: '3px',
    transition: 'width 0.3s ease',
  },
  tagCost: {
    width: '70px',
    textAlign: 'right',
    fontSize: '12px',
    fontFamily: 'monospace',
    color: '#ec4899',
  },
  emptyText: {
    fontSize: '12px',
    color: '#6b7280',
    textAlign: 'center',
    padding: '20px',
  },
  tableCard: {
    backgroundColor: '#141414',
    borderRadius: '10px',
    padding: '16px',
    border: '1px solid #222',
  },
  tableContainer: {
    overflowX: 'auto',
  },
  table: {
    width: '100%',
    borderCollapse: 'collapse',
    fontSize: '13px',
  },
  th: {
    textAlign: 'left',
    padding: '10px 12px',
    borderBottom: '1px solid #333',
    color: '#9ca3af',
    fontWeight: 500,
    fontSize: '11px',
    textTransform: 'uppercase',
  },
  tr: {
    borderBottom: '1px solid #222',
  },
  td: {
    padding: '10px 12px',
    color: '#e5e7eb',
  },
};

export default CostReport;
