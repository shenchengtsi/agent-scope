import React, { useState, useEffect } from 'react';
import {
  LineChart, Line, BarChart, Bar, PieChart, Pie, Cell,
  XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer,
  AreaChart, Area
} from 'recharts';
import CostReport from '../components/CostReport';

const COLORS = ['#10b981', '#3b82f6', '#f59e0b', '#ef4444', '#8b5cf6', '#ec4899'];

function Analytics() {
  const [timeRange, setTimeRange] = useState(24);
  const [interval, setInterval] = useState('hour');
  const [historicalData, setHistoricalData] = useState([]);
  const [stats, setStats] = useState(null);
  const [traces, setTraces] = useState([]);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState('trends'); // 'trends' | 'cost'

  useEffect(() => {
    fetchData();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [timeRange, interval]);

  const fetchData = async () => {
    setLoading(true);
    try {
      const [histRes, statsRes, tracesRes] = await Promise.all([
        fetch(`/api/metrics/historical?hours=${timeRange}&interval=${interval}`),
        fetch('/api/stats'),
        fetch(`/api/traces?limit=10000&start_time=${new Date(Date.now() - timeRange * 3600000).toISOString()}`)
      ]);

      const histData = await histRes.json();
      const statsData = await statsRes.json();
      const tracesData = await tracesRes.json();

      setHistoricalData(histData.data || []);
      setStats(statsData);
      setTraces(tracesData.traces || tracesData || []);
    } catch (error) {
      console.error('Failed to fetch analytics data:', error);
    } finally {
      setLoading(false);
    }
  };

  // Calculate summary metrics
  const summary = historicalData.reduce(
    (acc, item) => ({
      totalTraces: acc.totalTraces + item.total_traces,
      totalTokens: acc.totalTokens + item.total_tokens,
      avgLatency: acc.avgLatency + item.avg_latency_ms,
      count: acc.count + 1,
    }),
    { totalTraces: 0, totalTokens: 0, avgLatency: 0, count: 0 }
  );

  const avgLatency = summary.count > 0 ? summary.avgLatency / summary.count : 0;

  // Status distribution for pie chart
  const statusData = stats?.by_status
    ? Object.entries(stats.by_status).map(([status, count]) => ({
        name: status,
        value: count,
      }))
    : [];

  // Format time label based on interval
  const formatTimeLabel = (timestamp) => {
    if (interval === 'hour') {
      return timestamp.split(' ')[1]; // Return HH:MM
    }
    return timestamp;
  };

  // Tab styles
  const getTabStyle = (tab) => ({
    ...styles.tab,
    ...(activeTab === tab ? styles.tabActive : {}),
  });

  return (
    <div style={styles.container}>
      <div style={styles.header}>
        <div>
          <h1 style={styles.title}>📈 Analytics Dashboard</h1>
          {/* Tabs */}
          <div style={styles.tabs}>
            <button
              style={getTabStyle('trends')}
              onClick={() => setActiveTab('trends')}
            >
              📊 Trends
            </button>
            <button
              style={getTabStyle('cost')}
              onClick={() => setActiveTab('cost')}
            >
              💰 Cost Report
            </button>
          </div>
        </div>
        
        {activeTab === 'trends' && (
          <div style={styles.controls}>
            <select
              style={styles.select}
              value={timeRange}
              onChange={(e) => setTimeRange(Number(e.target.value))}
            >
              <option value={6}>Last 6 hours</option>
              <option value={12}>Last 12 hours</option>
              <option value={24}>Last 24 hours</option>
              <option value={48}>Last 48 hours</option>
              <option value={72}>Last 3 days</option>
              <option value={168}>Last 7 days</option>
            </select>
            <select
              style={styles.select}
              value={interval}
              onChange={(e) => setInterval(e.target.value)}
            >
              <option value="hour">By Hour</option>
              <option value="day">By Day</option>
            </select>
            <button style={styles.refreshBtn} onClick={fetchData}>
              🔄 Refresh
            </button>
          </div>
        )}
      </div>

      {loading && activeTab === 'trends' ? (
        <div style={styles.loading}>Loading analytics...</div>
      ) : activeTab === 'trends' ? (
        <>
          {/* Summary Cards */}
          <div style={styles.summaryGrid}>
            <SummaryCard
              title="Total Traces"
              value={summary.totalTraces.toLocaleString()}
              icon="📊"
              color="#3b82f6"
            />
            <SummaryCard
              title="Total Tokens"
              value={summary.totalTokens >= 1000000
                ? `${(summary.totalTokens / 1000000).toFixed(1)}M`
                : summary.totalTokens >= 1000
                ? `${(summary.totalTokens / 1000).toFixed(1)}K`
                : summary.totalTokens.toLocaleString()}
              icon="📝"
              color="#8b5cf6"
            />
            <SummaryCard
              title="Avg Latency"
              value={`${avgLatency.toFixed(0)}ms`}
              icon="⏱️"
              color="#10b981"
            />
            <SummaryCard
              title="Est. Cost"
              value={`$${historicalData.reduce((sum, d) => sum + (d.total_cost || 0), 0).toFixed(3)}`}
              icon="💰"
              color="#ec4899"
            />
          </div>

          {/* Charts Grid */}
          <div style={styles.chartsGrid}>
            {/* Traces Over Time */}
            <div style={styles.chartCard}>
              <h3 style={styles.chartTitle}>📊 Traces Over Time</h3>
              <ResponsiveContainer width="100%" height={250}>
                <AreaChart data={historicalData}>
                  <defs>
                    <linearGradient id="colorTraces" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="5%" stopColor="#3b82f6" stopOpacity={0.3}/>
                      <stop offset="95%" stopColor="#3b82f6" stopOpacity={0}/>
                    </linearGradient>
                  </defs>
                  <CartesianGrid strokeDasharray="3 3" stroke="#333" />
                  <XAxis 
                    dataKey="timestamp" 
                    tickFormatter={formatTimeLabel}
                    stroke="#666"
                    fontSize={12}
                  />
                  <YAxis stroke="#666" fontSize={12} />
                  <Tooltip 
                    contentStyle={{ backgroundColor: '#1a1a1a', border: '1px solid #333' }}
                    labelStyle={{ color: '#fff' }}
                  />
                  <Area
                    type="monotone"
                    dataKey="total_traces"
                    stroke="#3b82f6"
                    fillOpacity={1}
                    fill="url(#colorTraces)"
                    name="Traces"
                  />
                </AreaChart>
              </ResponsiveContainer>
            </div>

            {/* Success/Error Rate */}
            <div style={styles.chartCard}>
              <h3 style={styles.chartTitle}>✅ Success & Error Rate</h3>
              <ResponsiveContainer width="100%" height={250}>
                <LineChart data={historicalData}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#333" />
                  <XAxis 
                    dataKey="timestamp" 
                    tickFormatter={formatTimeLabel}
                    stroke="#666"
                    fontSize={12}
                  />
                  <YAxis 
                    stroke="#666" 
                    fontSize={12}
                    tickFormatter={(val) => `${(val * 100).toFixed(0)}%`}
                  />
                  <Tooltip 
                    contentStyle={{ backgroundColor: '#1a1a1a', border: '1px solid #333' }}
                    labelStyle={{ color: '#fff' }}
                    formatter={(val) => `${(val * 100).toFixed(1)}%`}
                  />
                  <Legend />
                  <Line
                    type="monotone"
                    dataKey="success_rate"
                    stroke="#10b981"
                    strokeWidth={2}
                    dot={false}
                    name="Success Rate"
                  />
                  <Line
                    type="monotone"
                    dataKey="error_rate"
                    stroke="#ef4444"
                    strokeWidth={2}
                    dot={false}
                    name="Error Rate"
                  />
                </LineChart>
              </ResponsiveContainer>
            </div>

            {/* Latency Trend */}
            <div style={styles.chartCard}>
              <h3 style={styles.chartTitle}>⏱️ Latency Trend</h3>
              <ResponsiveContainer width="100%" height={250}>
                <AreaChart data={historicalData}>
                  <defs>
                    <linearGradient id="colorLatency" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="5%" stopColor="#f59e0b" stopOpacity={0.3}/>
                      <stop offset="95%" stopColor="#f59e0b" stopOpacity={0}/>
                    </linearGradient>
                  </defs>
                  <CartesianGrid strokeDasharray="3 3" stroke="#333" />
                  <XAxis 
                    dataKey="timestamp" 
                    tickFormatter={formatTimeLabel}
                    stroke="#666"
                    fontSize={12}
                  />
                  <YAxis 
                    stroke="#666" 
                    fontSize={12}
                    tickFormatter={(val) => `${val}ms`}
                  />
                  <Tooltip 
                    contentStyle={{ backgroundColor: '#1a1a1a', border: '1px solid #333' }}
                    labelStyle={{ color: '#fff' }}
                    formatter={(val) => `${val.toFixed(0)}ms`}
                  />
                  <Area
                    type="monotone"
                    dataKey="avg_latency_ms"
                    stroke="#f59e0b"
                    fillOpacity={1}
                    fill="url(#colorLatency)"
                    name="Avg Latency"
                  />
                </AreaChart>
              </ResponsiveContainer>
            </div>

            {/* Token Usage */}
            <div style={styles.chartCard}>
              <h3 style={styles.chartTitle}>📝 Token Usage</h3>
              <ResponsiveContainer width="100%" height={250}>
                <BarChart data={historicalData}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#333" />
                  <XAxis 
                    dataKey="timestamp" 
                    tickFormatter={formatTimeLabel}
                    stroke="#666"
                    fontSize={12}
                  />
                  <YAxis 
                    stroke="#666" 
                    fontSize={12}
                    tickFormatter={(val) => val >= 1000 ? `${(val/1000).toFixed(0)}k` : val}
                  />
                  <Tooltip 
                    contentStyle={{ backgroundColor: '#1a1a1a', border: '1px solid #333' }}
                    labelStyle={{ color: '#fff' }}
                    formatter={(val) => val.toLocaleString()}
                  />
                  <Bar
                    dataKey="total_tokens"
                    fill="#8b5cf6"
                    name="Tokens"
                    radius={[4, 4, 0, 0]}
                  />
                </BarChart>
              </ResponsiveContainer>
            </div>

            {/* Cost Trend */}
            <div style={styles.chartCard}>
              <h3 style={styles.chartTitle}>💰 Cost Trend</h3>
              <ResponsiveContainer width="100%" height={250}>
                <AreaChart data={historicalData}>
                  <defs>
                    <linearGradient id="colorCost" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="5%" stopColor="#ec4899" stopOpacity={0.3}/>
                      <stop offset="95%" stopColor="#ec4899" stopOpacity={0}/>
                    </linearGradient>
                  </defs>
                  <CartesianGrid strokeDasharray="3 3" stroke="#333" />
                  <XAxis 
                    dataKey="timestamp" 
                    tickFormatter={formatTimeLabel}
                    stroke="#666"
                    fontSize={12}
                  />
                  <YAxis 
                    stroke="#666" 
                    fontSize={12}
                    tickFormatter={(val) => `$${val.toFixed(3)}`}
                  />
                  <Tooltip 
                    contentStyle={{ backgroundColor: '#1a1a1a', border: '1px solid #333' }}
                    labelStyle={{ color: '#fff' }}
                    formatter={(val) => `$${val.toFixed(4)}`}
                  />
                  <Area
                    type="monotone"
                    dataKey="total_cost"
                    stroke="#ec4899"
                    fillOpacity={1}
                    fill="url(#colorCost)"
                    name="Cost (USD)"
                  />
                </AreaChart>
              </ResponsiveContainer>
            </div>

            {/* Status Distribution */}
            {statusData.length > 0 && (
              <div style={styles.chartCard}>
                <h3 style={styles.chartTitle}>📊 Status Distribution</h3>
                <ResponsiveContainer width="100%" height={250}>
                  <PieChart>
                    <Pie
                      data={statusData}
                      cx="50%"
                      cy="50%"
                      innerRadius={60}
                      outerRadius={80}
                      paddingAngle={5}
                      dataKey="value"
                    >
                      {statusData.map((entry, index) => (
                        <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                      ))}
                    </Pie>
                    <Tooltip 
                      contentStyle={{ backgroundColor: '#1a1a1a', border: '1px solid #333' }}
                      labelStyle={{ color: '#fff' }}
                    />
                    <Legend />
                  </PieChart>
                </ResponsiveContainer>
              </div>
            )}
          </div>
        </>
      ) : (
        <CostReport traces={traces} />
      )}
    </div>
  );
}

function SummaryCard({ title, value, icon, color }) {
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
        <span style={styles.summaryLabel}>{title}</span>
        <span style={{ ...styles.summaryValue, color }}>{value}</span>
      </div>
    </div>
  );
}

const styles = {
  container: {
    padding: '20px',
    backgroundColor: '#0a0a0a',
    minHeight: '100vh',
    color: '#fff',
  },
  header: {
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'flex-start',
    marginBottom: '24px',
    flexWrap: 'wrap',
    gap: '16px',
  },
  title: {
    margin: '0 0 12px 0',
    fontSize: '24px',
    fontWeight: 600,
  },
  tabs: {
    display: 'flex',
    gap: '8px',
  },
  tab: {
    padding: '8px 16px',
    borderRadius: '6px',
    border: 'none',
    backgroundColor: '#1a1a1a',
    color: '#9ca3af',
    fontSize: '14px',
    fontWeight: 500,
    cursor: 'pointer',
    transition: 'all 0.2s ease',
  },
  tabActive: {
    backgroundColor: '#3b82f6',
    color: '#fff',
  },
  controls: {
    display: 'flex',
    gap: '12px',
    alignItems: 'center',
  },
  select: {
    padding: '8px 12px',
    borderRadius: '6px',
    border: '1px solid #333',
    backgroundColor: '#1a1a1a',
    color: '#fff',
    fontSize: '14px',
    cursor: 'pointer',
  },
  refreshBtn: {
    padding: '8px 16px',
    borderRadius: '6px',
    border: '1px solid #333',
    backgroundColor: '#1a1a1a',
    color: '#fff',
    fontSize: '14px',
    cursor: 'pointer',
    transition: 'all 0.2s',
  },
  summaryGrid: {
    display: 'grid',
    gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))',
    gap: '16px',
    marginBottom: '24px',
  },
  summaryCard: {
    display: 'flex',
    alignItems: 'center',
    gap: '16px',
    padding: '20px',
    backgroundColor: '#141414',
    borderRadius: '12px',
    border: '1px solid',
    transition: 'transform 0.2s ease, box-shadow 0.2s ease',
  },
  summaryIcon: {
    width: '48px',
    height: '48px',
    borderRadius: '10px',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    fontSize: '24px',
  },
  summaryContent: {
    display: 'flex',
    flexDirection: 'column',
    gap: '2px',
  },
  summaryLabel: {
    fontSize: '12px',
    color: '#9ca3af',
    textTransform: 'uppercase',
    letterSpacing: '0.5px',
  },
  summaryValue: {
    fontSize: '20px',
    fontWeight: 700,
  },
  chartsGrid: {
    display: 'grid',
    gridTemplateColumns: 'repeat(auto-fit, minmax(450px, 1fr))',
    gap: '20px',
  },
  chartCard: {
    backgroundColor: '#141414',
    borderRadius: '12px',
    padding: '20px',
    border: '1px solid #222',
  },
  chartTitle: {
    margin: '0 0 16px 0',
    fontSize: '14px',
    fontWeight: 600,
    color: '#e5e7eb',
  },
  loading: {
    textAlign: 'center',
    padding: '60px',
    color: '#6b7280',
    fontSize: '16px',
  },
};

export default Analytics;
