import React, { useState } from 'react';
import ManifestViewer from './ManifestViewer';
import ForgeButton from './ForgeButton';
import LiveTerminal from './LiveTerminal';
import { Terminal, Code, Cpu } from 'lucide-react';
import './index.css';

function App() {
  const [prompt, setPrompt] = useState('');
  const [manifest, setManifest] = useState(null);
  const [isPlanning, setIsPlanning] = useState(false);
  const [isForging, setIsForging] = useState(false);
  const [terminalLogs, setTerminalLogs] = useState([]);
  const [forgeStage, setForgeStage] = useState('IDLE');

  const handlePlan = async () => {
    if (!prompt.trim()) return;
    
    setIsPlanning(true);
    setManifest(null);
    setTerminalLogs([]);
    setForgeStage('IDLE');
    
    try {
      const response = await fetch('http://127.0.0.1:8000/api/forge/plan', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ prompt, demo_mode: true }),
      });
      const data = await response.json();
      if (data.success) {
        setManifest(data.manifest);
        setTerminalLogs([
          `[OK] Generated manifest for "${data.manifest?.target_environment?.name || 'environment'}"`,
          `[INFO] Inferred languages: ${(data.manifest?.target_environment?.inferred_languages || []).join(', ')}`,
          `[INFO] Inferred packages: ${(data.manifest?.packages || []).map(p => p.display_name).join(', ')}`,
          `[INFO] Ready to forge. Click 'INITIATE FORGE' to begin execution.`
        ]);
      }
    } catch (error) {
      console.error("Error connecting to API:", error);
      setTerminalLogs([`[FAIL] Failed to communicate with Brain API: ${error.message}`]);
    } finally {
      setIsPlanning(false);
    }
  };

  const handleForge = () => {
    if (!manifest || isForging) return;
    
    setIsForging(true);
    setForgeStage('CONNECTING');
    setTerminalLogs((prev) => [
      ...prev,
      '',
      '======================================================================',
      '  INITIATING LIVE WEBSOCKET FORGE PIPELINE',
      '======================================================================',
      '[INFO] Connecting to ws://127.0.0.1:8000/ws/forge...'
    ]);

    const wsUrl = 'ws://127.0.0.1:8000/ws/forge';
    const socket = new WebSocket(wsUrl);

    socket.onopen = () => {
      setForgeStage('FORGING');
      setTerminalLogs((prev) => [...prev, '[OK] WebSocket connected. Transmitting manifest payload...']);
      socket.send(JSON.stringify({ manifest, dry_run: false }));
    };

    socket.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        if (data.type === 'log') {
          setTerminalLogs((prev) => [...prev, data.line]);
        } else if (data.type === 'status') {
          setForgeStage(data.stage);
          if (data.message) {
            setTerminalLogs((prev) => [...prev, `[INFO] ${data.message}`]);
          }
        } else if (data.type === 'complete') {
          setForgeStage(data.stage || (data.success ? 'COMPLETED' : 'FAILED'));
          setIsForging(false);
          const finishMsg = data.success
            ? '[OK] Forge execution and post-install health verification completed!'
            : '[FAIL] Forge completed with errors. See output logs above.';
          setTerminalLogs((prev) => [...prev, finishMsg]);
        } else if (data.type === 'error') {
          setForgeStage('FAILED');
          setIsForging(false);
          setTerminalLogs((prev) => [...prev, `[FAIL] Error: ${data.message}`]);
        }
      } catch (err) {
        setTerminalLogs((prev) => [...prev, event.data]);
      }
    };

    socket.onerror = (err) => {
      setForgeStage('FAILED');
      setIsForging(false);
      setTerminalLogs((prev) => [...prev, '[FAIL] Connection error with WebSocket server.']);
    };

    socket.onclose = () => {
      setIsForging(false);
    };
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
          
          <LiveTerminal 
            logs={terminalLogs} 
            stage={forgeStage} 
            isRunning={isForging} 
          />
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
