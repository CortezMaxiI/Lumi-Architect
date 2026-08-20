import React, { useState } from 'react';
import ManifestViewer from './ManifestViewer';
import ForgeButton from './ForgeButton';
import { Terminal, Code, Cpu } from 'lucide-react';
import './index.css';

function App() {
  const [prompt, setPrompt] = useState('');
  const [manifest, setManifest] = useState(null);
  const [isPlanning, setIsPlanning] = useState(false);
  const [isForging, setIsForging] = useState(false);
  const [forgeOutput, setForgeOutput] = useState('');

  const handlePlan = async () => {
    if (!prompt.trim()) return;
    
    setIsPlanning(true);
    setManifest(null);
    setForgeOutput('');
    
    try {
      const response = await fetch('http://127.0.0.1:8000/api/forge/plan', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ prompt, demo_mode: true }),
      });
      const data = await response.json();
      if (data.success) {
        setManifest(data.manifest);
      }
    } catch (error) {
      console.error("Error connecting to API:", error);
    } finally {
      setIsPlanning(false);
    }
  };

  const handleForge = async () => {
    if (!manifest) return;
    
    setIsForging(true);
    try {
      const response = await fetch('http://127.0.0.1:8000/api/forge/execute', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ manifest }),
      });
      const data = await response.json();
      if (data.success) {
        setForgeOutput("Forge Execution Successful!\n" + data.output);
      } else {
        setForgeOutput("Forge Execution Failed.\n" + data.error);
      }
    } catch (error) {
      setForgeOutput("Connection error: " + error.message);
    } finally {
      setIsForging(false);
    }
  };

  return (
    <div className="app-container">
      <div className="header">
        <h1>Lumi Architect</h1>
        <p>AI-Powered Infrastructure Forge</p>
      </div>
      
      <div className="main-content">
        <div className="left-panel glass-panel">
          <div style={{ display: 'flex', alignItems: 'center', gap: '10px', marginBottom: '1rem' }}>
            <Terminal size={24} color="var(--accent-cyan)" />
            <h2 style={{ margin: 0, fontSize: '1.5rem' }}>Neural Interface</h2>
          </div>
          
          <p style={{ color: 'var(--text-secondary)' }}>
            Describe the development environment you want to forge.
          </p>
          
          <div className="chat-container">
            <textarea 
              className="chat-input"
              rows="5"
              placeholder="e.g. Entorno MERN stack con Node.js, React y MongoDB..."
              value={prompt}
              onChange={(e) => setPrompt(e.target.value)}
            ></textarea>
            
            <button 
              className="btn-forge" 
              onClick={handlePlan}
              disabled={isPlanning || !prompt.trim()}
              style={{ borderColor: 'var(--accent-cyan)', color: 'var(--accent-cyan)' }}
            >
              {isPlanning ? 'Analyzing...' : 'Generate Plan'}
            </button>
          </div>
          
          {forgeOutput && (
            <div style={{ marginTop: '2rem', padding: '1rem', background: 'rgba(0,0,0,0.5)', borderRadius: '8px', overflowY: 'auto' }}>
              <h3 style={{ margin: '0 0 10px 0', color: 'var(--accent-green)' }}>Forge Output</h3>
              <pre style={{ margin: 0, whiteSpace: 'pre-wrap', fontSize: '0.9rem' }}>{forgeOutput}</pre>
            </div>
          )}
        </div>
        
        <div className="right-panel glass-panel">
           <div style={{ display: 'flex', alignItems: 'center', gap: '10px', marginBottom: '1rem' }}>
            <Cpu size={24} color="var(--accent-magenta)" />
            <h2 style={{ margin: 0, fontSize: '1.5rem' }}>Dependency Tree</h2>
          </div>
          
          {manifest ? (
            <>
              <ManifestViewer manifest={manifest} />
              <div style={{ marginTop: 'auto', paddingTop: '2rem' }}>
                <ForgeButton onClick={handleForge} isForging={isForging} />
              </div>
            </>
          ) : (
            <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', height: '100%', opacity: 0.3 }}>
              <Code size={64} />
              <p>No manifest generated yet. Enter a prompt.</p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

export default App;
