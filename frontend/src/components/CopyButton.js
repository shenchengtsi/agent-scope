import React, { useState } from 'react';

function CopyButton({ text, label = "Copy" }) {
  const [copied, setCopied] = useState(false);

  const handleCopy = async () => {
    try {
      await navigator.clipboard.writeText(text);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    } catch (err) {
      console.error('Failed to copy:', err);
    }
  };

  return (
    <button
      onClick={handleCopy}
      style={{
        ...styles.button,
        backgroundColor: copied ? '#10b981' : '#3b82f6',
      }}
      title={copied ? "Copied!" : label}
    >
      {copied ? '✓ Copied' : label}
    </button>
  );
}

const styles = {
  button: {
    padding: '6px 12px',
    borderRadius: '4px',
    border: 'none',
    color: '#fff',
    fontSize: '12px',
    fontWeight: 500,
    cursor: 'pointer',
    transition: 'all 0.2s ease',
  },
};

export default CopyButton;
