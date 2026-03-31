import React, { useState } from 'react';
import { useWebSocket } from '../hooks/useWebSocket';
import TraceListWithFilters from '../components/TraceListWithFilters';
import TraceTimeline from '../components/TraceTimeline';
import WorkflowVisualizer from '../components/WorkflowVisualizer';
import StepDetail from '../components/StepDetail';
import MetricsCards from '../components/MetricsCards';
import TraceCompare from '../components/TraceCompare';

function Dashboard() {
  const { traces, isConnected, clearAllTraces } = useWebSocket();
  const [selectedTrace, setSelectedTrace] = useState(null);
  const [selectedStep, setSelectedStep] = useState(null);
  const [viewMode, setViewMode] = useState('workflow'); // 'timeline' or 'workflow'
  const [compareMode, setCompareMode] = useState(false);
  const [tracesToCompare, setTracesToCompare] = useState([]);
  const [showComparison, setShowComparison] = useState(false);

  const handleSelectTrace = (trace) => {
    if (compareMode) {
      // Toggle selection for comparison
      setTracesToCompare(prev => {
        const exists = prev.find(t => t.id === trace.id);
        if (exists) {
          return prev.filter(t => t.id !== trace.id);
        }
        if (prev.length >= 2) {
          return [prev[1], trace]; // Keep only the last one and add new
        }
        return [...prev, trace];
      });
    } else {
      setSelectedTrace(trace);
      setSelectedStep(null);
    }
  };

  const handleSelectStep = (step) => {
    setSelectedStep(step);
  };

  const handleViewChildTrace = (childTraceId) => {
    const childTrace = traces.find(t => t.id === childTraceId);
    if (childTrace) {
      setSelectedTrace(childTrace);
      setSelectedStep(null);
    }
  };

  const toggleCompareMode = () => {
    setCompareMode(!compareMode);
    if (compareMode) {
      // Exit compare mode
      setTracesToCompare([]);
      setShowComparison(false);
    } else {
      // Enter compare mode - clear current selection
      setSelectedTrace(null);
      setSelectedStep(null);
    }
  };

  const executeComparison = () => {
    if (tracesToCompare.length === 2) {
      setShowComparison(true);
    }
  };

  return (
    <div style={styles.container}>
      {/* Metrics Cards */}
      <MetricsCards traces={traces} />
      
      {/* Compare Mode Bar */}
      {compareMode && (
        <div style={styles.compareBar}>
          <span style={styles.compareText}>
            Select 2 traces to compare ({tracesToCompare.length}/2 selected)
          </span>
          <div style={styles.compareActions}>
            {tracesToCompare.map(t => (
              <span key={t.id} style={styles.compareTag}>{t.id.slice(0, 8)}</span>
            ))}
            <button 
              style={{
                ...styles.compareButton,
                opacity: tracesToCompare.length === 2 ? 1 : 0.5,
                cursor: tracesToCompare.length === 2 ? 'pointer' : 'not-allowed',
              }}
              onClick={executeComparison}
              disabled={tracesToCompare.length !== 2}
            >
              Compare
            </button>
            <button style={styles.cancelButton} onClick={toggleCompareMode}>
              Cancel
            </button>
          </div>
        </div>
      )}

      <div style={styles.main}>
        {/* Left panel - Trace List */}
        <div style={styles.leftPanel}>
          <div style={styles.listHeader}>
            <span style={styles.listTitle}>Traces</span>
            {!compareMode && (
              <button style={styles.compareToggle} onClick={toggleCompareMode}>
                🔍 Compare
              </button>
            )}
          </div>
          <TraceListWithFilters 
            traces={traces}
            selectedTrace={compareMode ? null : selectedTrace}
            onSelectTrace={handleSelectTrace}
            compareMode={compareMode}
            tracesToCompare={tracesToCompare}
          />
        </div>

        {/* Center panel - Timeline/Workflow */}
        <div style={styles.centerPanel}>
          {selectedTrace ? (
            <>
              <div style={styles.traceHeader}>
                <div style={styles.traceHeaderLeft}>
                  <h2 style={styles.traceTitle}>{selectedTrace.name}</h2>
                  <div style={styles.traceMeta}>
                    <span style={styles.traceId}>ID: {selectedTrace.id}</span>
                    <span 
                      style={{
                        ...styles.traceStatus,
                        color: selectedTrace.status === 'success' ? '#10b981' : 
                               selectedTrace.status === 'error' ? '#ef4444' : '#3b82f6',
                      }}
                    >
                      {selectedTrace.status}
                    </span>
                    {selectedTrace.parent_trace_id && (
                      <span style={styles.parentBadge}>
                        Parent: {selectedTrace.parent_trace_id.slice(0, 8)}...
                      </span>
                    )}
                  </div>
                </div>
                <div style={styles.viewToggle}>
                  <button
                    style={{
                      ...styles.toggleButton,
                      ...(viewMode === 'timeline' ? styles.toggleButtonActive : {}),
                    }}
                    onClick={() => setViewMode('timeline')}
                  >
                    📋 Timeline
                  </button>
                  <button
                    style={{
                      ...styles.toggleButton,
                      ...(viewMode === 'workflow' ? styles.toggleButtonActive : {}),
                    }}
                    onClick={() => setViewMode('workflow')}
                  >
                    🔄 Workflow
                  </button>
                </div>
              </div>
              
              {/* Trace Stats Bar */}
              <div style={styles.traceStats}>
                <span style={styles.statItem}>📝 {selectedTrace.total_tokens?.toLocaleString() || 0} tokens</span>
                <span style={styles.statItem}>⏱️ {(selectedTrace.total_latency_ms / 1000)?.toFixed(2) || 0}s</span>
                <span style={styles.statItem}>🤖 {selectedTrace.llm_call_count || 0} LLM calls</span>
                <span style={styles.statItem}>🔧 {selectedTrace.tool_call_count || 0} tool calls</span>
                {selectedTrace.cost_estimate > 0 && (
                  <span style={styles.statItem}>💰 ${selectedTrace.cost_estimate.toFixed(4)}</span>
                )}
                {selectedTrace.context_window_usage > 0 && (
                  <span style={styles.statItem}>
                    📊 {(selectedTrace.context_window_usage * 100).toFixed(1)}% context
                  </span>
                )}
              </div>
              
              <div style={styles.timelineContainer}>
                {viewMode === 'timeline' ? (
                  <TraceTimeline 
                    steps={selectedTrace.steps}
                    onStepClick={handleSelectStep}
                    selectedStep={selectedStep}
                    traceStats={{
                      totalTokensIn: selectedTrace.steps?.reduce((sum, s) => sum + (s.tokens_input || 0), 0),
                      totalTokensOut: selectedTrace.steps?.reduce((sum, s) => sum + (s.tokens_output || 0), 0),
                      totalLatency: selectedTrace.total_latency_ms || selectedTrace.steps?.reduce((sum, s) => sum + (s.latency_ms || 0), 0),
                    }}
                  />
                ) : (
                  <WorkflowVisualizer
                    steps={selectedTrace.steps}
                    onStepClick={handleSelectStep}
                    selectedStep={selectedStep}
                    traceStats={{
                      totalTokensIn: selectedTrace.steps?.reduce((sum, s) => sum + (s.tokens_input || 0), 0),
                      totalTokensOut: selectedTrace.steps?.reduce((sum, s) => sum + (s.tokens_output || 0), 0),
                      totalLatency: selectedTrace.total_latency_ms || selectedTrace.steps?.reduce((sum, s) => sum + (s.latency_ms || 0), 0),
                    }}
                  />
                )}
              </div>
            </>
          ) : (
            <div style={styles.emptyState}>
              <div style={styles.emptyIcon}>📊</div>
              <h3 style={styles.emptyTitle}>Select a trace to view details</h3>
              <p style={styles.emptyText}>
                Click on a trace from the left panel to see the execution flow
              </p>
            </div>
          )}
        </div>

        {/* Right panel - Step Detail */}
        <div style={styles.rightPanel}>
          <StepDetail 
            step={selectedStep} 
            onViewChildTrace={handleViewChildTrace}
          />
        </div>
      </div>

      {/* Trace Comparison Modal */}
      {showComparison && tracesToCompare.length === 2 && (
        <TraceCompare
          trace1={tracesToCompare[0]}
          trace2={tracesToCompare[1]}
          onClose={() => {
            setShowComparison(false);
            setTracesToCompare([]);
            setCompareMode(false);
          }}
        />
      )}
    </div>
  );
}

const styles = {
  container: {
    height: '100vh',
    display: 'flex',
    flexDirection: 'column',
    backgroundColor: '#0a0a0a',
  },
  compareBar: {
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'center',
    padding: '10px 20px',
    backgroundColor: '#1a1a2e',
    borderBottom: '1px solid #333',
  },
  compareText: {
    fontSize: '13px',
    color: '#e0e0e0',
  },
  compareActions: {
    display: 'flex',
    alignItems: 'center',
    gap: '10px',
  },
  compareTag: {
    fontSize: '11px',
    padding: '4px 8px',
    backgroundColor: 'rgba(59, 130, 246, 0.2)',
    color: '#3b82f6',
    borderRadius: '4px',
    fontFamily: 'monospace',
  },
  compareButton: {
    padding: '6px 14px',
    backgroundColor: '#3b82f6',
    color: '#fff',
    border: 'none',
    borderRadius: '4px',
    fontSize: '12px',
    fontWeight: 500,
    cursor: 'pointer',
  },
  cancelButton: {
    padding: '6px 14px',
    backgroundColor: 'transparent',
    color: '#6b7280',
    border: '1px solid #333',
    borderRadius: '4px',
    fontSize: '12px',
    cursor: 'pointer',
  },
  main: {
    flex: 1,
    display: 'flex',
    overflow: 'hidden',
  },
  leftPanel: {
    width: '320px',
    borderRight: '1px solid #222',
    backgroundColor: '#0d0d0d',
    overflow: 'hidden',
    display: 'flex',
    flexDirection: 'column',
  },
  listHeader: {
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'center',
    padding: '12px 16px',
    borderBottom: '1px solid #222',
  },
  listTitle: {
    fontSize: '14px',
    fontWeight: 600,
    color: '#e0e0e0',
  },
  compareToggle: {
    padding: '4px 10px',
    backgroundColor: 'rgba(99, 102, 241, 0.2)',
    color: '#6366f1',
    border: 'none',
    borderRadius: '4px',
    fontSize: '11px',
    cursor: 'pointer',
    fontWeight: 500,
  },
  centerPanel: {
    flex: 1,
    display: 'flex',
    flexDirection: 'column',
    overflow: 'hidden',
    backgroundColor: '#0a0a0a',
  },
  traceHeader: {
    padding: '16px 20px',
    borderBottom: '1px solid #222',
    backgroundColor: '#0d0d0d',
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'center',
  },
  traceHeaderLeft: {
    flex: 1,
  },
  viewToggle: {
    display: 'flex',
    gap: '8px',
  },
  toggleButton: {
    padding: '8px 16px',
    borderRadius: '6px',
    border: '1px solid #333',
    backgroundColor: '#1a1a1a',
    color: '#9ca3af',
    fontSize: '13px',
    cursor: 'pointer',
    transition: 'all 0.2s ease',
  },
  toggleButtonActive: {
    backgroundColor: '#3b82f6',
    color: '#fff',
    borderColor: '#3b82f6',
  },
  traceTitle: {
    fontSize: '16px',
    fontWeight: 600,
    color: '#e0e0e0',
    margin: 0,
    marginBottom: '8px',
  },
  traceMeta: {
    display: 'flex',
    alignItems: 'center',
    gap: '12px',
  },
  traceId: {
    fontSize: '11px',
    color: '#4b5563',
    fontFamily: 'monospace',
  },
  traceStatus: {
    fontSize: '11px',
    padding: '2px 8px',
    borderRadius: '4px',
    backgroundColor: 'rgba(255,255,255,0.05)',
    fontWeight: 600,
    textTransform: 'uppercase',
  },
  parentBadge: {
    fontSize: '10px',
    padding: '2px 8px',
    backgroundColor: 'rgba(139, 92, 246, 0.2)',
    color: '#8b5cf6',
    borderRadius: '4px',
    fontFamily: 'monospace',
  },
  traceStats: {
    display: 'flex',
    gap: '16px',
    padding: '10px 20px',
    backgroundColor: '#0d0d0d',
    borderBottom: '1px solid #222',
    fontSize: '12px',
    color: '#9ca3af',
  },
  statItem: {
    display: 'flex',
    alignItems: 'center',
    gap: '4px',
  },
  timelineContainer: {
    flex: 1,
    overflow: 'hidden',
  },
  rightPanel: {
    width: '420px',
    borderLeft: '1px solid #222',
    backgroundColor: '#0d0d0d',
    overflow: 'hidden',
    display: 'flex',
    flexDirection: 'column',
  },
  emptyState: {
    flex: 1,
    display: 'flex',
    flexDirection: 'column',
    alignItems: 'center',
    justifyContent: 'center',
    color: '#6b7280',
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
  },
};

export default Dashboard;
