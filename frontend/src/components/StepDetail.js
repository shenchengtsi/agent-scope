import React from 'react';
import CollapsibleSection from './CollapsibleSection';
import PromptDetail from './PromptDetail';
import SkillDetail from './SkillDetail';
import ToolSelectionDetail from './ToolSelectionDetail';
import MemoryOperationDetail from './MemoryOperationDetail';
import ReasoningDetail from './ReasoningDetail';
import SubAgentDetail from './SubAgentDetail';
import CopyButton from './CopyButton';

const typeColors = {
  input: '#3b82f6',
  llm_call: '#8b5cf6',
  tool_call: '#f59e0b',
  tool_result: '#10b981',
  output: '#10b981',
  error: '#ef4444',
  thinking: '#6b7280',
  // Enhanced types
  skill_loading: '#06b6d4',
  prompt_build: '#6366f1',
  tool_selection: '#f59e0b',
  memory_operation: '#ec4899',
  subagent_call: '#8b5cf6',
  reasoning: '#6366f1',
};

const typeLabels = {
  input: 'Input',
  llm_call: 'LLM Call',
  tool_call: 'Tool Call',
  tool_result: 'Tool Result',
  output: 'Output',
  error: 'Error',
  thinking: 'Thinking',
  // Enhanced types
  skill_loading: 'Skills Loading',
  prompt_build: 'Prompt Build',
  tool_selection: 'Tool Selection',
  memory_operation: 'Memory Operation',
  subagent_call: 'Sub-Agent Call',
  reasoning: 'Reasoning',
};

// Helper component to display step status with error detection
function StepStatus({ step }) {
  // Determine actual status - check for errors in tool_call or metadata
  let displayStatus = step.status;
  let hasError = step.status === 'error';
  
  // Check tool_call for errors
  if (step.tool_call?.error) {
    hasError = true;
    displayStatus = 'error';
  }
  
  // Check metadata for errors
  if (step.metadata?.error || step.metadata?.status === 'error') {
    hasError = true;
    displayStatus = 'error';
  }
  
  // Check content for error indicators (for LLM calls)
  if (step.type === 'llm_call' && step.content) {
    const contentLower = step.content.toLowerCase();
    if (contentLower.includes('error:') || contentLower.includes('exception:')) {
      hasError = true;
      displayStatus = 'error';
    }
  }
  
  const statusColor = displayStatus === 'success' 
    ? '#10b981' 
    : displayStatus === 'error' 
      ? '#ef4444' 
      : '#9ca3af';
  
  return (
    <span style={styles.status}>
      Status: <span style={{ color: statusColor, fontWeight: 600 }}>
        {displayStatus}
      </span>
      {hasError && step.tool_call?.error && (
        <span style={styles.errorIndicator}>(tool error)</span>
      )}
    </span>
  );
}

// Helper component to display local time
function LocalTime({ timestamp }) {
  const [localTime, setLocalTime] = React.useState('');
  
  React.useEffect(() => {
    if (!timestamp) return;
    
    try {
      // The timestamp from backend is in UTC (ends with Z)
      // Create date object - Date constructor automatically handles UTC with Z suffix
      let date;
      if (typeof timestamp === 'string') {
        // Ensure it has Z suffix for UTC
        const utcTimestamp = timestamp.endsWith('Z') ? timestamp : timestamp + 'Z';
        date = new Date(utcTimestamp);
      } else {
        date = new Date(timestamp);
      }
      
      // Check if valid date
      if (isNaN(date.getTime())) {
        setLocalTime(String(timestamp));
        return;
      }
      
      // Format to local time string
      const formatted = date.toLocaleString('zh-CN', {
        year: 'numeric',
        month: '2-digit',
        day: '2-digit',
        hour: '2-digit',
        minute: '2-digit',
        second: '2-digit',
        hour12: false,
      });
      
      setLocalTime(formatted);
    } catch (e) {
      console.error('Error formatting timestamp:', e);
      setLocalTime(String(timestamp));
    }
  }, [timestamp]);
  
  return (
    <span style={styles.timestamp}>
      {localTime || timestamp}
    </span>
  );
}

function StepDetail({ step, onViewChildTrace }) {
  if (!step) {
    return (
      <div style={styles.empty}>
        <p>Select a step to view details</p>
      </div>
    );
  }

  const color = typeColors[step.type] || '#6b7280';
  const label = typeLabels[step.type] || step.type;

  // Render enhanced detail section based on step type
  const renderEnhancedDetails = () => {
    switch (step.type) {
      case 'prompt_build':
        return step.prompt_info && <PromptDetail promptInfo={step.prompt_info} />;
      case 'skill_loading':
        return step.skill_info && <SkillDetail skills={step.skill_info} />;
      case 'tool_selection':
        return step.tool_selection && <ToolSelectionDetail toolSelection={step.tool_selection} />;
      case 'memory_operation':
        return step.memory_info && <MemoryOperationDetail memoryInfo={step.memory_info} />;
      case 'reasoning':
        return step.reasoning_info && <ReasoningDetail reasoningInfo={step.reasoning_info} />;
      case 'subagent_call':
        return step.subagent_info && (
          <SubAgentDetail 
            subagentInfo={step.subagent_info} 
            onViewChildTrace={onViewChildTrace}
          />
        );
      default:
        return null;
    }
  };

  return (
    <div style={styles.container}>
      {/* Header */}
      <div style={styles.header}>
        <div>
          <h3 style={styles.title}>Step Details</h3>
          <div style={styles.headerMeta}>
            <span
              style={{
                ...styles.type,
                color: color,
                backgroundColor: `${color}15`,
              }}
            >
              {label}
            </span>
            {step.metadata?.call_sequence && (
              <span style={styles.sequenceBadge}>
                Call #{step.metadata.call_sequence}
              </span>
            )}
            <code style={styles.stepId}>{step.id}</code>
          </div>
        </div>
        <CopyButton text={JSON.stringify(step, null, 2)} label="Copy JSON" />
      </div>

      {/* Content Section */}
      <CollapsibleSection 
        title="Content" 
        copyText={typeof step.content === 'string' ? step.content : JSON.stringify(step.content, null, 2)}
        defaultExpanded={true}
      >
        <pre style={styles.code}>
          {typeof step.content === 'string' 
            ? step.content 
            : JSON.stringify(step.content, null, 2)}
        </pre>
      </CollapsibleSection>

      {/* Enhanced Type-Specific Details */}
      {renderEnhancedDetails()}

      {/* Tool Call Details (for tool_call type) */}
      {step.tool_call && (
        <CollapsibleSection title="Tool Call Details" defaultExpanded={true}>
          <div style={styles.toolSection}>
            <div style={styles.toolRow}>
              <span style={styles.toolLabel}>Name:</span>
              <span style={styles.toolValue}>{step.tool_call.name}</span>
            </div>
            <div style={styles.toolRow}>
              <span style={styles.toolLabel}>ID:</span>
              <code style={styles.toolCode}>{step.tool_call.id}</code>
            </div>
            <div style={styles.toolRow}>
              <span style={styles.toolLabel}>Latency:</span>
              <span style={styles.toolValue}>{step.tool_call.latency_ms?.toFixed(2)}ms</span>
            </div>
            {step.tool_call.error && (
              <div style={styles.toolRow}>
                <span style={styles.toolLabel}>Error:</span>
                <span style={styles.errorText}>{step.tool_call.error}</span>
              </div>
            )}
          </div>
          
          <h5 style={styles.subTitle}>Arguments</h5>
          <pre style={styles.code}>
            {JSON.stringify(step.tool_call.arguments, null, 2)}
          </pre>
          
          {step.tool_call.result !== undefined && (
            <>
              <h5 style={styles.subTitle}>Result</h5>
              <pre style={styles.code}>
                {typeof step.tool_call.result === 'object'
                  ? JSON.stringify(step.tool_call.result, null, 2)
                  : String(step.tool_call.result)}
              </pre>
            </>
          )}
        </CollapsibleSection>
      )}

      {/* Metadata */}
      {step.metadata && Object.keys(step.metadata).length > 0 && (
        <CollapsibleSection 
          title="Metadata" 
          copyText={JSON.stringify(step.metadata, null, 2)}
        >
          <pre style={styles.code}>
            {JSON.stringify(step.metadata, null, 2)}
          </pre>
        </CollapsibleSection>
      )}

      {/* Stats */}
      <div style={styles.stats}>
        <div style={styles.stat}>
          <span style={styles.statLabel}>Tokens In</span>
          <span style={styles.statValue}>{step.tokens_input?.toLocaleString() || 0}</span>
        </div>
        <div style={styles.stat}>
          <span style={styles.statLabel}>Tokens Out</span>
          <span style={styles.statValue}>{step.tokens_output?.toLocaleString() || 0}</span>
        </div>
        <div style={styles.stat}>
          <span style={styles.statLabel}>Latency</span>
          <span style={styles.statValue}>{step.latency_ms?.toFixed(2) || 0}ms</span>
        </div>
      </div>

      {/* Footer */}
      <div style={styles.footer}>
        <StepStatus step={step} />
        <LocalTime timestamp={step.timestamp} />
      </div>
    </div>
  );
}

const styles = {
  container: {
    padding: '20px',
    height: '100%',
    overflowY: 'auto',
  },
  empty: {
    padding: '40px',
    textAlign: 'center',
    color: '#6b7280',
  },
  header: {
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'flex-start',
    marginBottom: '20px',
    paddingBottom: '16px',
    borderBottom: '1px solid #222',
  },
  title: {
    fontSize: '18px',
    fontWeight: 600,
    color: '#e0e0e0',
    margin: '0 0 8px 0',
  },
  headerMeta: {
    display: 'flex',
    alignItems: 'center',
    gap: '10px',
  },
  type: {
    fontSize: '12px',
    padding: '4px 12px',
    borderRadius: '6px',
    textTransform: 'uppercase',
    fontWeight: 600,
  },
  stepId: {
    fontSize: '11px',
    color: '#4b5563',
    fontFamily: 'monospace',
  },
  sequenceBadge: {
    fontSize: '11px',
    padding: '2px 8px',
    borderRadius: '4px',
    backgroundColor: '#3b82f620',
    color: '#3b82f6',
    fontWeight: 600,
    fontFamily: 'monospace',
  },
  code: {
    backgroundColor: '#0d0d0d',
    padding: '12px',
    borderRadius: '8px',
    fontSize: '12px',
    fontFamily: 'monospace',
    color: '#e0e0e0',
    overflowX: 'auto',
    lineHeight: 1.5,
    whiteSpace: 'pre-wrap',
    wordBreak: 'break-word',
    margin: 0,
  },
  toolSection: {
    backgroundColor: '#141414',
    padding: '12px',
    borderRadius: '8px',
    marginBottom: '12px',
  },
  toolRow: {
    display: 'flex',
    marginBottom: '8px',
  },
  toolLabel: {
    width: '80px',
    fontSize: '12px',
    color: '#6b7280',
    fontWeight: 500,
  },
  toolValue: {
    fontSize: '12px',
    color: '#e0e0e0',
  },
  toolCode: {
    fontSize: '11px',
    color: '#9ca3af',
    fontFamily: 'monospace',
  },
  errorText: {
    fontSize: '12px',
    color: '#ef4444',
  },
  subTitle: {
    fontSize: '12px',
    fontWeight: 600,
    color: '#6b7280',
    marginTop: '12px',
    marginBottom: '8px',
  },
  stats: {
    display: 'flex',
    gap: '16px',
    marginTop: '24px',
    padding: '16px',
    backgroundColor: '#141414',
    borderRadius: '8px',
  },
  stat: {
    display: 'flex',
    flexDirection: 'column',
    gap: '4px',
  },
  statLabel: {
    fontSize: '11px',
    color: '#6b7280',
    textTransform: 'uppercase',
  },
  statValue: {
    fontSize: '18px',
    fontWeight: 600,
    color: '#e0e0e0',
  },
  footer: {
    marginTop: '24px',
    paddingTop: '16px',
    borderTop: '1px solid #222',
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'center',
  },
  status: {
    fontSize: '12px',
    color: '#9ca3af',
  },
  timestamp: {
    fontSize: '11px',
    color: '#9ca3af',
  },
  errorIndicator: {
    fontSize: '10px',
    color: '#ef4444',
    marginLeft: '6px',
    fontWeight: 500,
  },
};

export default StepDetail;
