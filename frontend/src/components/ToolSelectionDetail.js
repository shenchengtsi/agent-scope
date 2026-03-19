import React from 'react';
import CollapsibleSection from './CollapsibleSection';

function ToolSelectionDetail({ toolSelection }) {
  if (!toolSelection) return null;

  const { selected_tool, available_tools, selection_reason, confidence, tool_call_id } = toolSelection;

  // Prepare copy text
  const copyText = JSON.stringify({
    selected_tool,
    available_tools,
    selection_reason,
    confidence,
    tool_call_id,
  }, null, 2);

  return (
    <div style={styles.container}>
      {/* Selected Tool */}
      <div style={styles.selectedSection}>
        <span style={styles.selectedLabel}>Selected Tool</span>
        <div style={styles.selectedTool}>
          <span style={styles.toolIcon}>🔧</span>
          <code style={styles.toolName}>{selected_tool}</code>
        </div>
        {confidence > 0 && (
          <div style={styles.confidence}>
            <span style={styles.confidenceLabel}>Confidence:</span>
            <div style={styles.confidenceBar}>
              <div 
                style={{ 
                  ...styles.confidenceFill, 
                  width: `${confidence * 100}%`,
                  backgroundColor: confidence > 0.8 ? '#10b981' : confidence > 0.5 ? '#f59e0b' : '#ef4444',
                }} 
              />
            </div>
            <span style={styles.confidenceValue}>{(confidence * 100).toFixed(0)}%</span>
          </div>
        )}
      </div>

      {/* Selection Reason */}
      {selection_reason && (
        <CollapsibleSection title="Selection Reason" defaultExpanded={true}>
          <div style={styles.reasonContent}>
            <p style={styles.reasonText}>{selection_reason}</p>
          </div>
        </CollapsibleSection>
      )}

      {/* Available Tools */}
      {available_tools && available_tools.length > 0 && (
        <CollapsibleSection 
          title="Available Tools" 
          badge={`${available_tools.length} tools`}
          copyText={copyText}
        >
          <div style={styles.toolsList}>
            {available_tools.map((tool, index) => (
              <ToolItem 
                key={index} 
                tool={tool} 
                isSelected={tool.name === selected_tool || tool.function?.name === selected_tool}
              />
            ))}
          </div>
        </CollapsibleSection>
      )}

      {/* Tool Call ID */}
      {tool_call_id && (
        <div style={styles.toolCallIdSection}>
          <span style={styles.toolCallIdLabel}>Tool Call ID:</span>
          <code style={styles.toolCallId}>{tool_call_id}</code>
        </div>
      )}
    </div>
  );
}

function ToolItem({ tool, isSelected }) {
  const toolName = tool.name || tool.function?.name || 'unknown';
  const toolDesc = tool.description || tool.function?.description || '';

  return (
    <div style={{
      ...styles.toolItem,
      borderColor: isSelected ? '#10b981' : '#333',
      backgroundColor: isSelected ? 'rgba(16, 185, 129, 0.1)' : '#141414',
    }}>
      <div style={styles.toolHeader}>
        <code style={styles.toolItemName}>{toolName}</code>
        {isSelected && (
          <span style={styles.selectedBadge}>Selected</span>
        )}
      </div>
      {toolDesc && (
        <p style={styles.toolDescription}>{toolDesc}</p>
      )}
    </div>
  );
}

const styles = {
  container: {
    padding: '8px 0',
  },
  selectedSection: {
    backgroundColor: '#141414',
    borderRadius: '8px',
    padding: '16px',
    marginBottom: '16px',
  },
  selectedLabel: {
    fontSize: '11px',
    color: '#6b7280',
    textTransform: 'uppercase',
    letterSpacing: '0.5px',
    marginBottom: '8px',
    display: 'block',
  },
  selectedTool: {
    display: 'flex',
    alignItems: 'center',
    gap: '10px',
    marginBottom: '12px',
  },
  toolIcon: {
    fontSize: '20px',
  },
  toolName: {
    fontSize: '16px',
    color: '#e0e0e0',
    backgroundColor: '#0d0d0d',
    padding: '6px 12px',
    borderRadius: '6px',
  },
  confidence: {
    display: 'flex',
    alignItems: 'center',
    gap: '10px',
    marginTop: '12px',
  },
  confidenceLabel: {
    fontSize: '12px',
    color: '#9ca3af',
  },
  confidenceBar: {
    flex: 1,
    height: '6px',
    backgroundColor: '#333',
    borderRadius: '3px',
    overflow: 'hidden',
  },
  confidenceFill: {
    height: '100%',
    borderRadius: '3px',
    transition: 'width 0.3s ease',
  },
  confidenceValue: {
    fontSize: '12px',
    color: '#e0e0e0',
    minWidth: '40px',
    textAlign: 'right',
  },
  reasonContent: {
    backgroundColor: '#141414',
    borderRadius: '8px',
    padding: '12px',
  },
  reasonText: {
    margin: 0,
    fontSize: '13px',
    color: '#e0e0e0',
    lineHeight: 1.6,
    fontStyle: 'italic',
  },
  toolsList: {
    display: 'flex',
    flexDirection: 'column',
    gap: '8px',
  },
  toolItem: {
    borderRadius: '8px',
    padding: '12px',
    border: '1px solid',
    borderLeft: '3px solid',
  },
  toolHeader: {
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: '6px',
  },
  toolItemName: {
    fontSize: '13px',
    color: '#e0e0e0',
  },
  selectedBadge: {
    fontSize: '10px',
    padding: '2px 8px',
    backgroundColor: 'rgba(16, 185, 129, 0.2)',
    color: '#10b981',
    borderRadius: '4px',
    fontWeight: 600,
  },
  toolDescription: {
    margin: 0,
    fontSize: '12px',
    color: '#9ca3af',
    lineHeight: 1.4,
  },
  toolCallIdSection: {
    marginTop: '12px',
    padding: '10px',
    backgroundColor: '#141414',
    borderRadius: '6px',
    display: 'flex',
    alignItems: 'center',
    gap: '10px',
  },
  toolCallIdLabel: {
    fontSize: '11px',
    color: '#6b7280',
  },
  toolCallId: {
    fontSize: '12px',
    color: '#9ca3af',
    fontFamily: 'monospace',
  },
};

export default ToolSelectionDetail;
