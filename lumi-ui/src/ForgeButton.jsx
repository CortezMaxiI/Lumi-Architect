import React from 'react';
import { Zap } from 'lucide-react';

export default function ForgeButton({ onClick, isForging }) {
  return (
    <button 
      className="btn-forge" 
      onClick={onClick} 
      disabled={isForging}
      style={{ 
        width: '100%', 
        display: 'flex', 
        justifyContent: 'center', 
        alignItems: 'center', 
        gap: '10px' 
      }}
    >
      <Zap size={24} className={isForging ? "animate-pulse" : ""} />
      {isForging ? "FORGING ENVIRONMENT..." : "INITIATE FORGE"}
    </button>
  );
}
