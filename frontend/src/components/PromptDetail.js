import React from 'react';
import CollapsibleSection from './CollapsibleSection';

const roleColors = {
  system: '#8b5cf6',      // Purple
  user: '#3b82f6',        // Blue
  assistant: '#10b981',   // Green
  tool: '#f59e0b',        // Orange
};

function PromptDetail({ promptInfo }) {
  console.log('PromptDetail received:', promptInfo);
  
  if (!promptInfo) return null;

  // Handle different data formats
  let messages = promptInfo.messages || [];
  
  // Handle case where promptInfo itself is an array of messages
  if (Array.isArray(promptInfo)) {
    messages = promptInfo;
  }
  
  // Handle case where messages is inside a 'messages' property
  if (promptInfo.messages && Array.isArray(promptInfo.messages)) {
    messages = promptInfo.messages;
  }
  
  const systemPrompt = promptInfo.system_prompt || promptInfo.systemPrompt || '';
  const model = promptInfo.model || promptInfo.model_name || promptInfo.modelName || '';
  const temperature = promptInfo.temperature ?? promptInfo.temp ?? 0;
  const maxTokens = promptInfo.max_tokens || promptInfo.maxTokens || 0;
  const topP = promptInfo.top_p || promptInfo.topP || 0;
  const contextWindow = promptInfo.context_window || promptInfo.contextWindow || 0;

  // Prepare copy text
  const copyText = JSON.stringify({
    messages,
    system_prompt: systemPrompt,
    model,
    temperature,
    max_tokens: maxTokens,
    top_p: topP,
    context_window: contextWindow,
  }, null, 2);

  // Calculate message structure
  const structure = {};
  messages.forEach((msg, idx) => {
    const role = (msg.role || msg.type || 'unknown').toLowerCase();
    if (!structure[role]) {
      structure[role] = { count: 0, indices: [] };
    }
    structure[role].count++;
    structure[role].indices.push(idx);
  });

  return (
    <div style={styles.container}>
      {/* Model Configuration */}
      {(model || temperature || maxTokens) && (
        <div style={styles.configSection}>
          <h5 style={styles.configTitle}>Model Configuration</h5>
          <div style={styles.configGrid}>
            {model && (
              <div style={styles.configItem}>
                <span style={styles.configLabel}>Model</span>
                <span style={styles.configValue}>{model}</span>
              </div>
            )}
            {temperature !== undefined && temperature !== 0 && (
              <div style={styles.configItem}>
                <span style={styles.configLabel}>Temperature</span>
                <span style={styles.configValue}>{temperature}</span>
              </div>
            )}
            {maxTokens > 0 && (
              <div style={styles.configItem}>
                <span style={styles.configLabel}>Max Tokens</span>
                <span style={styles.configValue}>{maxTokens.toLocaleString()}</span>
              </div>
            )}
            {topP !== undefined && topP !== 0 && (
              <div style={styles.configItem}>
                <span style={styles.configLabel}>Top P</span>
                <span style={styles.configValue}>{topP}</span>
              </div>
            )}
            {contextWindow > 0 && (
              <div style={styles.configItem}>
                <span style={styles.configLabel}>Context Window</span>
                <span style={styles.configValue}>{contextWindow.toLocaleString()}</span>
              </div>
            )}
          </div>
        </div>
      )}

      {/* Messages Structure Overview */}
      {Object.keys(structure).length > 0 && (
        <div style={styles.structureSection}>
          <h5 style={styles.structureTitle}>Message Structure ({messages.length} total)</h5>
          <div style={styles.structureGrid}>
            {Object.entries(structure).map(([role, info]) => {
              const color = roleColors[role] || '#6b7280';
              return (
                <div key={role} style={{ ...styles.structureItem, borderColor: color }}>
                  <span style={{ ...styles.structureRole, color }}>{role}</span>
                  <span style={styles.structureCount}>{info.count}</span>
                  <span style={styles.structureIndices}>({info.indices.map(i => `#${i+1}`).join(', ')})</span>
                </div>
              );
            })}
          </div>
        </div>
      )}

      {/* Messages */}
      <CollapsibleSection 
        title="Messages" 
        badge={`${messages.length} messages`}
        copyText={copyText}
        defaultExpanded={true}
      >
        <div style={styles.messagesContainer}>
          {messages.length === 0 ? (
            <p style={styles.emptyText}>No messages</p>
          ) : (
            messages.map((msg, index) => (
              <MessageItem key={index} message={msg} index={index} />
            ))
          )}
        </div>
      </CollapsibleSection>

      {/* System Prompt (if separate from messages) */}
      {systemPrompt && (
        <CollapsibleSection title="System Prompt" copyText={systemPrompt}>
          <pre style={styles.systemPrompt}>{systemPrompt}</pre>
        </CollapsibleSection>
      )}
    </div>
  );
}

function MessageItem({ message, index }) {
  // Handle different message formats
  const role = (message.role || message.type || 'unknown').toLowerCase();
  const content = message.content || message.text || message.message || '';
  const color = roleColors[role] || '#6b7280';
  const hasToolCalls = message.tool_calls && message.tool_calls.length > 0;
  const name = message.name || message.tool_name || '';
  const toolCallId = message.tool_call_id || message.toolId || '';

  return (
    <div style={{ ...styles.messageItem, borderLeftColor: color }}>
      <div style={styles.messageHeader}>
        <span style={{ ...styles.roleBadge, backgroundColor: `${color}20`, color }}>
          {role}
        </span>
        <span style={styles.messageIndex}>#{index + 1}</span>
        {name && (
          <span style={styles.nameTag}>name: {name}</span>
        )}
        {toolCallId && (
          <span style={styles.toolCallId}>tool_call_id: {toolCallId}</span>
        )}
      </div>
      
      <div style={styles.messageContent}>
        {content ? (
          <pre style={styles.contentText}>{content}</pre>
        ) : hasToolCalls ? (
          <span style={styles.emptyContent}>(no text content)</span>
        ) : (
          <span style={styles.emptyContent}>(no content)</span>
        )}
      </div>

      {hasToolCalls && (
        <div style={styles.toolCallsSection}>
          <span style={styles.toolCallsLabel}>Tool Calls:</span>
          {message.tool_calls.map((tc, i) => (
            <div key={i} style={styles.toolCall}>
              <code style={styles.toolCallCode}>
                {tc.function?.name || tc.name}({tc.function?.arguments || tc.arguments || '{}'})
              </code>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

const styles = {
  container: {
    padding: '8px 0',
  },
  configSection: {
    marginBottom: '16px',
    padding: '12px',
    backgroundColor: '#141414',
    borderRadius: '8px',
  },
  configTitle: {
    fontSize: '12px',
    fontWeight: 600,
    color: '#9ca3af',
    margin: '0 0 12px 0',
    textTransform: 'uppercase',
  },
  configGrid: {
    display: 'grid',
    gridTemplateColumns: 'repeat(auto-fit, minmax(150px, 1fr))',
    gap: '12px',
  },
  configItem: {
    display: 'flex',
    flexDirection: 'column',
    gap: '4px',
  },
  configLabel: {
    fontSize: '11px',
    color: '#6b7280',
  },
  configValue: {
    fontSize: '13px',
    color: '#e0e0e0',
    fontFamily: 'monospace',
  },
  structureSection: {
    marginBottom: '16px',
    padding: '12px',
    backgroundColor: '#141414',
    borderRadius: '8px',
  },
  structureTitle: {
    fontSize: '12px',
    fontWeight: 600,
    color: '#9ca3af',
    margin: '0 0 12px 0',
    textTransform: 'uppercase',
  },
  structureGrid: {
    display: 'flex',
    gap: '10px',
    flexWrap: 'wrap',
  },
  structureItem: {
    display: 'flex',
    alignItems: 'center',
    gap: '8px',
    padding: '6px 12px',
    backgroundColor: '#0d0d0d',
    borderRadius: '6px',
    border: '1px solid',
    borderLeft: '3px solid',
  },
  structureRole: {
    fontSize: '12px',
    fontWeight: 600,
    textTransform: 'uppercase',
  },
  structureCount: {
    fontSize: '14px',
    fontWeight: 700,
    color: '#e0e0e0',
  },
  structureIndices: {
    fontSize: '10px',
    color: '#6b7280',
    fontFamily: 'monospace',
  },
  messagesContainer: {
    display: 'flex',
    flexDirection: 'column',
    gap: '12px',
  },
  emptyText: {
    fontSize: '13px',
    color: '#6b7280',
    fontStyle: 'italic',
    textAlign: 'center',
    padding: '20px',
  },
  messageItem: {
    backgroundColor: '#141414',
    borderRadius: '8px',
    padding: '12px',
    borderLeft: '3px solid',
  },
  messageHeader: {
    display: 'flex',
    alignItems: 'center',
    gap: '8px',
    marginBottom: '8px',
  },
  roleBadge: {
    fontSize: '11px',
    fontWeight: 600,
    padding: '2px 8px',
    borderRadius: '4px',
    textTransform: 'uppercase',
  },
  messageIndex: {
    fontSize: '10px',
    color: '#6b7280',
    fontFamily: 'monospace',
  },
  nameTag: {
    fontSize: '11px',
    color: '#9ca3af',
    fontFamily: 'monospace',
  },
  toolCallId: {
    fontSize: '10px',
    color: '#6b7280',
    fontFamily: 'monospace',
  },
  messageContent: {
    marginTop: '8px',
  },
  contentText: {
    margin: 0,
    fontSize: '13px',
    color: '#e0e0e0',
    lineHeight: 1.5,
    fontFamily: 'monospace',
    whiteSpace: 'pre-wrap',
    wordBreak: 'break-word',
  },
  emptyContent: {
    fontSize: '12px',
    color: '#6b7280',
    fontStyle: 'italic',
  },
  toolCallsSection: {
    marginTop: '12px',
    padding: '8px',
    backgroundColor: '#0d0d0d',
    borderRadius: '6px',
  },
  toolCallsLabel: {
    fontSize: '11px',
    color: '#9ca3af',
    marginBottom: '8px',
    display: 'block',
  },
  toolCall: {
    marginBottom: '4px',
  },
  toolCallCode: {
    fontSize: '12px',
    color: '#f59e0b',
    fontFamily: 'monospace',
  },
  systemPrompt: {
    margin: 0,
    fontSize: '13px',
    color: '#e0e0e0',
    lineHeight: 1.6,
    fontFamily: 'monospace',
    whiteSpace: 'pre-wrap',
    wordBreak: 'break-word',
  },
};

export default PromptDetail;
