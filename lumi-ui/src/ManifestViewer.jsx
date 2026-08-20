import React from 'react';
import { Package, ShieldAlert, Cpu } from 'lucide-react';

export default function ManifestViewer({ manifest }) {
  if (!manifest) return null;

  const packages = manifest.packages || [];
  const sortedPackages = [...packages].sort((a, b) => a.priority_level - b.priority_level);

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem', height: '100%' }}>
      <div style={{ background: 'rgba(0,0,0,0.3)', padding: '1rem', borderRadius: '8px', borderLeft: '3px solid var(--accent-magenta)' }}>
        <h3 style={{ margin: '0 0 5px 0', color: 'var(--text-primary)' }}>{manifest.target_environment?.name || "Environment"}</h3>
        <p style={{ margin: 0, fontSize: '0.9rem', color: 'var(--text-secondary)' }}>
          {manifest.ai_reasoning}
        </p>
      </div>
      
      <ul className="manifest-tree" style={{ flex: 1, overflowY: 'auto' }}>
        {sortedPackages.map((pkg, idx) => (
          <li key={idx} className="manifest-item">
            <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
              {pkg.category === 'runtime' ? <Cpu size={18} color="var(--accent-magenta)" /> : <Package size={18} color="var(--accent-cyan)" />}
              <div>
                <div className="item-name">{pkg.display_name}</div>
                <div className="item-category">Manager: {pkg.package_manager}</div>
              </div>
            </div>
            
            <div style={{ display: 'flex', gap: '8px', alignItems: 'center' }}>
               <span className="badge badge-tool">v{pkg.version_requirement}</span>
               {pkg.is_critical && (
                 <span className="badge badge-critical" title="Critical Dependency">
                   <ShieldAlert size={14} style={{ display: 'inline', verticalAlign: 'middle', marginRight: '2px' }} />
                   CRITICAL
                 </span>
               )}
            </div>
          </li>
        ))}
      </ul>
    </div>
  );
}
