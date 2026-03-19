import React from 'react';
import CollapsibleSection from './CollapsibleSection';

const statusConfig = {
  loaded: { color: '#10b981', icon: '✓', label: 'Loaded' },
  failed: { color: '#ef4444', icon: '✗', label: 'Failed' },
  loading: { color: '#3b82f6', icon: '⟳', label: 'Loading' },
  success: { color: '#10b981', icon: '✓', label: 'Success' },
  error: { color: '#ef4444', icon: '✗', label: 'Error' },
};

function SkillDetail({ skills }) {
  console.log('SkillDetail received:', skills);
  
  // Handle various formats
  let skillList = [];
  
  if (Array.isArray(skills)) {
    skillList = skills;
  } else if (typeof skills === 'object' && skills !== null) {
    // Handle object format like {skill_name: {status, error}}
    skillList = Object.entries(skills).map(([name, data]) => {
      if (typeof data === 'object' && data !== null) {
        return { name, ...data };
      }
      return { name, status: data };
    });
  } else if (typeof skills === 'string') {
    // Single skill as string
    skillList = [{ name: skills, status: 'loaded' }];
  }
  
  // Filter out empty/null skills and ensure each has a name
  skillList = skillList.filter(s => {
    if (!s) return false;
    if (typeof s === 'string') return s.length > 0;
    return s.name || s.id || s.skill_name || s.skill_id;
  });
  
  console.log('Processed skillList:', skillList);
  
  if (skillList.length === 0) {
    return (
      <div style={styles.container}>
        <CollapsibleSection title="Skills" badge="0 skills">
          <p style={styles.emptyText}>No skill information available</p>
        </CollapsibleSection>
      </div>
    );
  }

  const loadedCount = skillList.filter(s => {
    const status = (s.status || s.state || '').toLowerCase();
    return status === 'loaded' || status === 'success';
  }).length;
  
  const failedCount = skillList.filter(s => {
    const status = (s.status || s.state || '').toLowerCase();
    return status === 'failed' || status === 'error';
  }).length;
  
  const loadingCount = skillList.filter(s => {
    const status = (s.status || s.state || '').toLowerCase();
    return status === 'loading';
  }).length;

  const summary = `${loadedCount} loaded${failedCount > 0 ? `, ${failedCount} failed` : ''}${loadingCount > 0 ? `, ${loadingCount} loading` : ''}`;

  // Prepare copy text
  const copyText = JSON.stringify(skillList, null, 2);

  return (
    <div style={styles.container}>
      <CollapsibleSection 
        title="Skills" 
        badge={summary}
        copyText={copyText}
        defaultExpanded={true}
      >
        <div style={styles.skillsList}>
          {skillList.map((skill, index) => (
            <SkillItem key={index} skill={skill} index={index} />
          ))}
        </div>
      </CollapsibleSection>
    </div>
  );
}

function SkillItem({ skill, index }) {
  // Handle string skills
  if (typeof skill === 'string') {
    return (
      <div style={styles.skillItem}>
        <div style={styles.skillHeader}>
          <div style={styles.skillLeft}>
            <span style={{ ...styles.statusIcon, color: '#10b981' }}>✓</span>
            <code style={styles.skillName}>{skill}</code>
          </div>
          <span style={{ ...styles.statusBadge, color: '#10b981', backgroundColor: '#10b98115' }}>
            Loaded
          </span>
        </div>
      </div>
    );
  }
  
  // Extract skill properties with fallbacks
  const skillName = skill.name 
    || skill.skill_name 
    || skill.skillName
    || skill.id 
    || skill.skill_id 
    || skill.skillId
    || skill.key
    || skill.module
    || `Skill ${index + 1}`;
  
  const rawStatus = (skill.status || skill.state || skill.load_status || 'unknown').toLowerCase();
  const skillStatus = rawStatus === 'success' ? 'loaded' : rawStatus === 'error' ? 'failed' : rawStatus;
  
  const skillDesc = skill.description || skill.desc || skill.summary || skill.doc || '';
  const skillError = skill.error || skill.err || skill.failure || skill.error_message || skill.exception || null;
  const loadTime = skill.load_time_ms || skill.loadTimeMs || skill.time_ms || skill.duration || skill.load_time || 0;
  
  const config = statusConfig[skillStatus] || statusConfig.loading;

  return (
    <div style={styles.skillItem}>
      <div style={styles.skillHeader}>
        <div style={styles.skillLeft}>
          <span style={{ ...styles.statusIcon, color: config.color }}>
            {config.icon}
          </span>
          <code style={styles.skillName}>{skillName}</code>
        </div>
        <span style={{ ...styles.statusBadge, color: config.color, backgroundColor: `${config.color}15` }}>
          {config.label}
        </span>
      </div>
      
      {skillDesc && (
        <p style={styles.description}>{skillDesc}</p>
      )}
      
      <div style={styles.skillMeta}>
        {loadTime > 0 && (
          <span style={styles.metaItem}>⏱️ {Number(loadTime).toFixed(1)}ms</span>
        )}
        {skillError && (
          <span style={styles.errorText}>⚠️ {skillError}</span>
        )}
      </div>
    </div>
  );
}

const styles = {
  container: {
    padding: '8px 0',
  },
  emptyText: {
    fontSize: '13px',
    color: '#6b7280',
    fontStyle: 'italic',
    padding: '12px',
    textAlign: 'center',
  },
  skillsList: {
    display: 'flex',
    flexDirection: 'column',
    gap: '10px',
  },
  skillItem: {
    backgroundColor: '#141414',
    borderRadius: '8px',
    padding: '12px',
    borderLeft: '3px solid #333',
  },
  skillHeader: {
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: '8px',
  },
  skillLeft: {
    display: 'flex',
    alignItems: 'center',
    gap: '8px',
  },
  statusIcon: {
    fontSize: '14px',
    fontWeight: 'bold',
  },
  skillName: {
    fontSize: '14px',
    fontWeight: 600,
    color: '#e0e0e0',
    fontFamily: 'monospace',
  },
  statusBadge: {
    fontSize: '10px',
    padding: '2px 8px',
    borderRadius: '4px',
    fontWeight: 600,
    textTransform: 'uppercase',
  },
  description: {
    fontSize: '12px',
    color: '#9ca3af',
    margin: '0 0 8px 0',
    lineHeight: 1.4,
  },
  skillMeta: {
    display: 'flex',
    gap: '12px',
    flexWrap: 'wrap',
  },
  metaItem: {
    fontSize: '11px',
    color: '#6b7280',
  },
  errorText: {
    fontSize: '11px',
    color: '#ef4444',
  },
};

export default SkillDetail;
