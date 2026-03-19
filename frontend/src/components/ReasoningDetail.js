import React from 'react';
import CollapsibleSection from './CollapsibleSection';

const reasoningTypeConfig = {
  chain_of_thought: { icon: '💭', color: '#8b5cf6', label: 'Chain of Thought' },
  plan: { icon: '📋', color: '#3b82f6', label: 'Plan' },
  reflection: { icon: '🔄', color: '#f59e0b', label: 'Reflection' },
};

function ReasoningDetail({ reasoningInfo }) {
  if (!reasoningInfo) return null;

  const { reasoning_content, reasoning_type, plan_steps, confidence } = reasoningInfo;
  const config = reasoningTypeConfig[reasoning_type] || { icon: '💭', color: '#6b7280', label: 'Thinking' };

  // Prepare copy text
  const copyText = JSON.stringify({
    reasoning_type,
    reasoning_content,
    plan_steps,
    confidence,
  }, null, 2);

  return (
    <div style={styles.container}>
      {/* Type Badge */}
      <div style={styles.header}>
        <div style={{ ...styles.typeBadge, color: config.color, backgroundColor: `${config.color}15` }}>
          <span style={styles.typeIcon}>{config.icon}</span>
          <span style={styles.typeLabel}>{config.label}</span>
        </div>
        
        {confidence > 0 && (
          <div style={styles.confidence}>
            <span style={styles.confidenceLabel}>Confidence:</span>
            <span style={{ ...styles.confidenceValue, color: confidence > 0.8 ? '#10b981' : confidence > 0.5 ? '#f59e0b' : '#ef4444' }}>
              {(confidence * 100).toFixed(0)}%
            </span>
          </div>
        )}
      </div>

      {/* Reasoning Content */}
      {reasoning_content && (
        <CollapsibleSection 
          title="Reasoning Content" 
          copyText={reasoning_content}
          defaultExpanded={true}
        >
          <div style={styles.contentBox}>
            <p style={styles.contentText}>{reasoning_content}</p>
          </div>
        </CollapsibleSection>
      )}

      {/* Plan Steps */}
      {plan_steps && plan_steps.length > 0 && (
        <CollapsibleSection 
          title="Plan Steps" 
          badge={`${plan_steps.length} steps`}
          copyText={plan_steps.join('\n')}
        >
          <div style={styles.stepsList}>
            {plan_steps.map((step, index) => (
              <div key={index} style={styles.stepItem}>
                <span style={styles.stepNumber}>{index + 1}</span>
                <span style={styles.stepText}>{step}</span>
              </div>
            ))}
          </div>
        </CollapsibleSection>
      )}
    </div>
  );
}

const styles = {
  container: {
    padding: '8px 0',
  },
  header: {
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: '16px',
  },
  typeBadge: {
    display: 'flex',
    alignItems: 'center',
    gap: '8px',
    padding: '6px 12px',
    borderRadius: '6px',
    fontSize: '13px',
    fontWeight: 600,
  },
  typeIcon: {
    fontSize: '16px',
  },
  typeLabel: {
    textTransform: 'capitalize',
  },
  confidence: {
    display: 'flex',
    alignItems: 'center',
    gap: '6px',
  },
  confidenceLabel: {
    fontSize: '12px',
    color: '#6b7280',
  },
  confidenceValue: {
    fontSize: '13px',
    fontWeight: 600,
  },
  contentBox: {
    backgroundColor: '#141414',
    borderRadius: '8px',
    padding: '16px',
    borderLeft: '3px solid #6366f1',
  },
  contentText: {
    margin: 0,
    fontSize: '14px',
    color: '#e0e0e0',
    lineHeight: 1.7,
    whiteSpace: 'pre-wrap',
    wordBreak: 'break-word',
  },
  stepsList: {
    display: 'flex',
    flexDirection: 'column',
    gap: '10px',
  },
  stepItem: {
    display: 'flex',
    alignItems: 'flex-start',
    gap: '12px',
    padding: '12px',
    backgroundColor: '#141414',
    borderRadius: '8px',
  },
  stepNumber: {
    width: '24px',
    height: '24px',
    borderRadius: '50%',
    backgroundColor: '#3b82f6',
    color: '#fff',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    fontSize: '12px',
    fontWeight: 600,
    flexShrink: 0,
  },
  stepText: {
    fontSize: '13px',
    color: '#e0e0e0',
    lineHeight: 1.5,
    flex: 1,
    paddingTop: '2px',
  },
};

export default ReasoningDetail;
