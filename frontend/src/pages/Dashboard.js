import React, { useState } from 'react';
import { useWebSocket } from '../hooks/useWebSocket';
import Header from '../components/Header';
import TraceList from '../components/TraceList';
import TraceTimeline from '../components/TraceTimeline';
import StepDetail from '../components/StepDetail';

function Dashboard() {
  const { traces, isConnected, clearAllTraces } = useWebSocket();
  const [selectedTrace, setSelectedTrace] = useState(null);
  const [selectedStep, setSelectedStep] = useState(null);

  const handleSelectTrace = (trace) => {
    setSelectedTrace(trace);
    setSelectedStep(null);
  };

  const handleSelectStep = (step) => {
    setSelectedStep(step);
  };

  return (
    <div style={styles.container}>
      <Header 
        isConnected={isConnected} 
        tracesCount={traces.length}
        onClearAll={clearAllTraces}
      />
      
      <div style={styles.main}>
        {/* Left panel - Trace List */}
        <div style={styles.leftPanel}>
          <TraceList 
            traces={traces}
            selectedTrace={selectedTrace}
            onSelectTrace={handleSelectTrace}
          />
        </div>

        {/* Center panel - Timeline */}
        <div style={styles.centerPanel}>
          {selectedTrace ? (
            <>
              <div style={styles.traceHeader}>
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
                </div>
              </div>
              <div style={styles.timelineContainer}>
                <TraceTimeline 
                  steps={selectedTrace.steps}
                  onStepClick={handleSelectStep}
                  selectedStep={selectedStep}
                />
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
          <StepDetail step={selectedStep} />
        </div>
      </div>
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
  timelineContainer: {
    flex: 1,
    overflow: 'hidden',
  },
  rightPanel: {
    width: '380px',
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