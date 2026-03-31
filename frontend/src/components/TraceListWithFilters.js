import React, { useState, useMemo } from 'react';

const statusColors = {
  pending: '#9ca3af',
  running: '#3b82f6',
  success: '#10b981',
  error: '#ef4444',
};

function TraceListWithFilters({ traces, selectedTrace, onSelectTrace, compareMode, tracesToCompare }) {
  // 过滤状态
  const [statusFilter, setStatusFilter] = useState('all');
  const [tagFilter, setTagFilter] = useState('');
  const [searchQuery, setSearchQuery] = useState('');
  const [timeRange, setTimeRange] = useState('all');
  const [showFilters, setShowFilters] = useState(false);

  // 获取所有唯一的标签
  const allTags = useMemo(() => {
    const tags = new Set();
    traces.forEach(trace => {
      trace.tags?.forEach(tag => tags.add(tag));
    });
    return Array.from(tags).sort();
  }, [traces]);

  // 过滤逻辑
  const filteredTraces = useMemo(() => {
    return traces.filter(trace => {
      // 状态过滤
      if (statusFilter !== 'all' && trace.status !== statusFilter) {
        return false;
      }

      // 标签过滤
      if (tagFilter && !trace.tags?.includes(tagFilter)) {
        return false;
      }

      // 搜索过滤
      if (searchQuery) {
        const query = searchQuery.toLowerCase();
        const nameMatch = trace.name?.toLowerCase().includes(query);
        const inputMatch = trace.input_query?.toLowerCase().includes(query);
        const idMatch = trace.id?.toLowerCase().includes(query);
        if (!nameMatch && !inputMatch && !idMatch) {
          return false;
        }
      }

      // 时间范围过滤
      if (timeRange !== 'all' && trace.start_time) {
        const traceTime = new Date(trace.start_time).getTime();
        const now = Date.now();
        const ranges = {
          '1h': 60 * 60 * 1000,
          '24h': 24 * 60 * 60 * 1000,
          '7d': 7 * 24 * 60 * 60 * 1000,
        };
        if (ranges[timeRange] && now - traceTime > ranges[timeRange]) {
          return false;
        }
      }

      return true;
    });
  }, [traces, statusFilter, tagFilter, searchQuery, timeRange]);

  // 统计信息
  const stats = useMemo(() => ({
    total: filteredTraces.length,
    byStatus: {
      success: filteredTraces.filter(t => t.status === 'success').length,
      error: filteredTraces.filter(t => t.status === 'error').length,
      pending: filteredTraces.filter(t => t.status === 'pending').length,
      running: filteredTraces.filter(t => t.status === 'running').length,
    }
  }), [filteredTraces]);

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
      {/* 搜索栏 */}
      <div style={styles.searchBar}>
        <input
          type="text"
          placeholder="Search traces..."
          value={searchQuery}
          onChange={(e) => setSearchQuery(e.target.value)}
          style={styles.searchInput}
        />
        <button
          onClick={() => setShowFilters(!showFilters)}
          style={{
            ...styles.filterToggle,
            backgroundColor: showFilters ? '#3b82f6' : '#1f2937',
          }}
        >
          🔍 Filters {showFilters ? '▲' : '▼'}
        </button>
      </div>

      {/* 过滤面板 */}
      {showFilters && (
        <div style={styles.filterPanel}>
          {/* 状态过滤 */}
          <div style={styles.filterGroup}>
            <label style={styles.filterLabel}>Status</label>
            <div style={styles.filterOptions}>
              {['all', 'success', 'error', 'pending', 'running'].map(status => (
                <button
                  key={status}
                  onClick={() => setStatusFilter(status)}
                  style={{
                    ...styles.filterButton,
                    backgroundColor: statusFilter === status ? '#3b82f6' : '#1f2937',
                    color: statusFilter === status ? '#fff' : '#9ca3af',
                  }}
                >
                  {status === 'all' ? 'All' : status}
                  {status !== 'all' && (
                    <span style={styles.filterCount}>
                      {traces.filter(t => t.status === status).length}
                    </span>
                  )}
                </button>
              ))}
            </div>
          </div>

          {/* 标签过滤 */}
          {allTags.length > 0 && (
            <div style={styles.filterGroup}>
              <label style={styles.filterLabel}>Tags</label>
              <div style={styles.filterOptions}>
                <button
                  onClick={() => setTagFilter('')}
                  style={{
                    ...styles.filterButton,
                    backgroundColor: tagFilter === '' ? '#3b82f6' : '#1f2937',
                    color: tagFilter === '' ? '#fff' : '#9ca3af',
                  }}
                >
                  All
                </button>
                {allTags.map(tag => (
                  <button
                    key={tag}
                    onClick={() => setTagFilter(tag)}
                    style={{
                      ...styles.filterButton,
                      backgroundColor: tagFilter === tag ? '#3b82f6' : '#1f2937',
                      color: tagFilter === tag ? '#fff' : '#9ca3af',
                    }}
                  >
                    {tag}
                  </button>
                ))}
              </div>
            </div>
          )}

          {/* 时间范围过滤 */}
          <div style={styles.filterGroup}>
            <label style={styles.filterLabel}>Time Range</label>
            <div style={styles.filterOptions}>
              {[
                { value: 'all', label: 'All Time' },
                { value: '1h', label: 'Last Hour' },
                { value: '24h', label: 'Last 24h' },
                { value: '7d', label: 'Last 7 Days' },
              ].map(({ value, label }) => (
                <button
                  key={value}
                  onClick={() => setTimeRange(value)}
                  style={{
                    ...styles.filterButton,
                    backgroundColor: timeRange === value ? '#3b82f6' : '#1f2937',
                    color: timeRange === value ? '#fff' : '#9ca3af',
                  }}
                >
                  {label}
                </button>
              ))}
            </div>
          </div>

          {/* 清除过滤 */}
          <button
            onClick={() => {
              setStatusFilter('all');
              setTagFilter('');
              setSearchQuery('');
              setTimeRange('all');
            }}
            style={styles.clearButton}
          >
            Clear All Filters
          </button>
        </div>
      )}

      {/* 统计信息 */}
      <div style={styles.statsBar}>
        <span style={styles.statsText}>
          Showing {filteredTraces.length} of {traces.length} traces
        </span>
        <div style={styles.statsBadges}>
          {stats.byStatus.success > 0 && (
            <span style={{ ...styles.statsBadge, backgroundColor: '#10b98120', color: '#10b981' }}>
              ✓ {stats.byStatus.success}
            </span>
          )}
          {stats.byStatus.error > 0 && (
            <span style={{ ...styles.statsBadge, backgroundColor: '#ef444420', color: '#ef4444' }}>
              ✗ {stats.byStatus.error}
            </span>
          )}
          {stats.byStatus.pending > 0 && (
            <span style={{ ...styles.statsBadge, backgroundColor: '#9ca3af20', color: '#9ca3af' }}>
              ○ {stats.byStatus.pending}
            </span>
          )}
        </div>
      </div>

      {/* Trace 列表 */}
      <div style={styles.list}>
        {filteredTraces.map((trace) => {
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
                    <span
                      key={tag}
                      style={{
                        ...styles.tag,
                        backgroundColor: tagFilter === tag ? '#3b82f6' : 'rgba(59, 130, 246, 0.15)',
                        color: tagFilter === tag ? '#fff' : '#3b82f6',
                      }}
                      onClick={(e) => {
                        e.stopPropagation();
                        setTagFilter(tagFilter === tag ? '' : tag);
                      }}
                    >
                      {tag}
                    </span>
                  ))}
                </div>
              )}
            </div>
          );
        })}

        {filteredTraces.length === 0 && (
          <div style={styles.noResults}>
            <p>No traces match the current filters</p>
            <button
              onClick={() => {
                setStatusFilter('all');
                setTagFilter('');
                setSearchQuery('');
                setTimeRange('all');
              }}
              style={styles.clearButton}
            >
              Clear Filters
            </button>
          </div>
        )}
      </div>
    </div>
  );
}

function formatTime(isoString) {
  if (!isoString) return '';

  try {
    const utcTimestamp = typeof isoString === 'string' && isoString.endsWith('Z')
      ? isoString
      : isoString + 'Z';

    const date = new Date(utcTimestamp);

    if (isNaN(date.getTime())) {
      return String(isoString);
    }

    const now = new Date();
    const diff = now - date;

    if (diff < 60000) return 'just now';
    if (diff < 3600000) return `${Math.floor(diff / 60000)}m ago`;
    if (diff < 86400000) return `${Math.floor(diff / 3600000)}h ago`;

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
  searchBar: {
    display: 'flex',
    gap: '8px',
    padding: '12px',
    borderBottom: '1px solid #2a2a2a',
  },
  searchInput: {
    flex: 1,
    padding: '8px 12px',
    backgroundColor: '#1f2937',
    border: '1px solid #374151',
    borderRadius: '6px',
    color: '#e0e0e0',
    fontSize: '13px',
    outline: 'none',
  },
  filterToggle: {
    padding: '8px 12px',
    border: 'none',
    borderRadius: '6px',
    cursor: 'pointer',
    fontSize: '12px',
    color: '#e0e0e0',
    transition: 'all 0.2s',
  },
  filterPanel: {
    padding: '12px',
    backgroundColor: '#1a1a1a',
    borderBottom: '1px solid #2a2a2a',
    display: 'flex',
    flexDirection: 'column',
    gap: '12px',
  },
  filterGroup: {
    display: 'flex',
    flexDirection: 'column',
    gap: '6px',
  },
  filterLabel: {
    fontSize: '11px',
    color: '#6b7280',
    textTransform: 'uppercase',
    fontWeight: 600,
  },
  filterOptions: {
    display: 'flex',
    flexWrap: 'wrap',
    gap: '6px',
  },
  filterButton: {
    padding: '4px 10px',
    border: 'none',
    borderRadius: '4px',
    cursor: 'pointer',
    fontSize: '11px',
    transition: 'all 0.2s',
    display: 'flex',
    alignItems: 'center',
    gap: '4px',
  },
  filterCount: {
    fontSize: '10px',
    opacity: 0.7,
  },
  clearButton: {
    padding: '6px 12px',
    backgroundColor: '#374151',
    border: 'none',
    borderRadius: '4px',
    color: '#9ca3af',
    fontSize: '11px',
    cursor: 'pointer',
    alignSelf: 'flex-start',
  },
  statsBar: {
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'center',
    padding: '8px 12px',
    backgroundColor: '#1a1a1a',
    borderBottom: '1px solid #2a2a2a',
  },
  statsText: {
    fontSize: '11px',
    color: '#6b7280',
  },
  statsBadges: {
    display: 'flex',
    gap: '6px',
  },
  statsBadge: {
    fontSize: '10px',
    padding: '2px 6px',
    borderRadius: '4px',
    fontWeight: 600,
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
    borderRadius: '4px',
    cursor: 'pointer',
    transition: 'all 0.2s',
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
  noResults: {
    padding: '40px 20px',
    textAlign: 'center',
    color: '#6b7280',
  },
};

export default TraceListWithFilters;
