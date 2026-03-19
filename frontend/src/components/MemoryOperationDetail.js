import React from 'react';
import CollapsibleSection from './CollapsibleSection';

const operationConfig = {
  read: { icon: '📖', color: '#3b82f6', label: 'Read' },
  write: { icon: '✏️', color: '#10b981', label: 'Write' },
  delete: { icon: '🗑️', color: '#ef4444', label: 'Delete' },
  search: { icon: '🔍', color: '#8b5cf6', label: 'Search' },
  consolidate: { icon: '📦', color: '#f59e0b', label: 'Consolidate' },
};

function MemoryOperationDetail({ memoryInfo }) {
  if (!memoryInfo) return null;

  const { operation, key, namespace, data_preview, tokens_affected, operation_details } = memoryInfo;
  const config = operationConfig[operation] || { icon: '📦', color: '#6b7280', label: operation };

  // Prepare copy text
  const copyText = JSON.stringify({
    operation,
    key,
    namespace,
    data_preview,
    tokens_affected,
    operation_details,
  }, null, 2);

  return (
    <div style={styles.container}>
      {/* Operation Header */}
      <div style={styles.header}>
        <div style={styles.operationBadge}>
          <span style={styles.operationIcon}>{config.icon}</span>
          <span style={{ ...styles.operationLabel, color: config.color }}>
            {config.label}
          </span>
        </div>
        
        {tokens_affected > 0 && (
          <span style={styles.tokensBadge}>
            {tokens_affected.toLocaleString()} tokens
          </span>
        )}
      </div>

      {/* Key & Namespace */}
      <div style={styles.metaSection}>
        {key && (
          <div style={styles.metaItem}>
            <span style={styles.metaLabel}>Key:</span>
            <code style={styles.metaValue}>{key}</code>
          </div>
        )}
        {namespace && namespace !== 'default' && (
          <div style={styles.metaItem}>
            <span style={styles.metaLabel}>Namespace:</span>
            <code style={styles.metaValue}>{namespace}</code>
          </div>
        )}
      </div>

      {/* Data Preview */}
      {data_preview && (
        <CollapsibleSection 
          title="Data Preview" 
          copyText={data_preview}
          defaultExpanded={false}
        >
          <pre style={styles.dataPreview}>{data_preview}</pre>
        </CollapsibleSection>
      )}

      {/* Operation Details */}
      {operation_details && Object.keys(operation_details).length > 0 && (
        <CollapsibleSection 
          title="Operation Details" 
          copyText={JSON.stringify(operation_details, null, 2)}
        >
          <div style={styles.detailsGrid}>
            {Object.entries(operation_details).map(([key, value]) => (
              <div key={key} style={styles.detailItem}>
                <span style={styles.detailKey}>{key}:</span>
                <span style={styles.detailValue}>
                  {typeof value === 'number' 
                    ? value.toLocaleString() 
                    : String(value)}
                </span>
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
    padding: '12px',
    backgroundColor: '#141414',
    borderRadius: '8px',
  },
  operationBadge: {
    display: 'flex',
    alignItems: 'center',
    gap: '8px',
  },
  operationIcon: {
    fontSize: '18px',
  },
  operationLabel: {
    fontSize: '14px',
    fontWeight: 600,
    textTransform: 'uppercase',
  },
  tokensBadge: {
    fontSize: '12px',
    padding: '4px 10px',
    backgroundColor: 'rgba(59, 130, 246, 0.2)',
    color: '#3b82f6',
    borderRadius: '4px',
    fontWeight: 500,
  },
  metaSection: {
    display: 'flex',
    flexDirection: 'column',
    gap: '8px',
    marginBottom: '16px',
  },
  metaItem: {
    display: 'flex',
    alignItems: 'center',
    gap: '10px',
  },
  metaLabel: {
    fontSize: '12px',
    color: '#6b7280',
    minWidth: '80px',
  },
  metaValue: {
    fontSize: '13px',
    color: '#e0e0e0',
    fontFamily: 'monospace',
    backgroundColor: '#141414',
    padding: '4px 8px',
    borderRadius: '4px',
  },
  dataPreview: {
    margin: 0,
    fontSize: '12px',
    color: '#e0e0e0',
    lineHeight: 1.5,
    fontFamily: 'monospace',
    whiteSpace: 'pre-wrap',
    wordBreak: 'break-word',
    maxHeight: '300px',
    overflow: 'auto',
  },
  detailsGrid: {
    display: 'grid',
    gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))',
    gap: '10px',
  },
  detailItem: {
    display: 'flex',
    flexDirection: 'column',
    gap: '4px',
    padding: '8px',
    backgroundColor: '#141414',
    borderRadius: '6px',
  },
  detailKey: {
    fontSize: '11px',
    color: '#6b7280',
    textTransform: 'capitalize',
  },
  detailValue: {
    fontSize: '13px',
    color: '#e0e0e0',
    fontFamily: 'monospace',
  },
};

export default MemoryOperationDetail;
