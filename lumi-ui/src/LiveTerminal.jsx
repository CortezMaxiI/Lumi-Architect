import React, { useEffect, useRef, useState } from "react";
import { Terminal, Copy, Check, ArrowDown, Trash2 } from "lucide-react";

export default function LiveTerminal({ logs = [], stage = "IDLE", isRunning = false }) {
  const terminalEndRef = useRef(null);
  const [autoScroll, setAutoScroll] = useState(true);
  const [copied, setCopied] = useState(false);

  useEffect(() => {
    if (autoScroll && terminalEndRef.current) {
      terminalEndRef.current.scrollIntoView({ behavior: "smooth" });
    }
  }, [logs, autoScroll]);

  const handleCopy = () => {
    const text = logs.join("\n");
    navigator.clipboard.writeText(text);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const getStageBadge = () => {
    switch (stage) {
      case "FORGING":
        return { label: "FORGING", className: "badge-running" };
      case "VERIFYING":
        return { label: "HEALTH CHECK", className: "badge-verifying" };
      case "COMPLETED":
        return { label: "COMPLETED", className: "badge-success" };
      case "FAILED":
        return { label: "FAILED", className: "badge-failed" };
      case "WARNING":
        return { label: "NEEDS ATTENTION", className: "badge-warning" };
      default:
        return { label: "READY", className: "badge-idle" };
    }
  };

  const badge = getStageBadge();

  const formatLine = (line, idx) => {
    let colorClass = "term-default";
    if (line.includes("[OK]")) colorClass = "term-ok";
    else if (line.includes("[FAIL]")) colorClass = "term-fail";
    else if (line.includes("[WARN]")) colorClass = "term-warn";
    else if (line.includes("[SKIP]")) colorClass = "term-skip";
    else if (line.includes("[INFO]")) colorClass = "term-info";
    else if (line.startsWith("==") || line.includes("FORGE")) colorClass = "term-header";

    return (
      <div key={idx} className={`term-line ${colorClass}`}>
        <span className="term-num">{idx + 1}</span>
        <span className="term-text">{line}</span>
      </div>
    );
  };

  return (
    <div className="terminal-container">
      <div className="terminal-header">
        <div className="terminal-title">
          <Terminal size={18} className={isRunning ? "animate-pulse" : ""} color="var(--accent-cyan)" />
          <span>Execution Console</span>
          <span className={`status-pill ${badge.className}`}>{badge.label}</span>
        </div>

        <div className="terminal-actions">
          <button
            className={`btn-icon ${autoScroll ? "active" : ""}`}
            title="Toggle Auto-Scroll"
            onClick={() => setAutoScroll(!autoScroll)}
          >
            <ArrowDown size={14} />
          </button>
          <button className="btn-icon" title="Copy Logs" onClick={handleCopy}>
            {copied ? <Check size={14} color="var(--accent-green)" /> : <Copy size={14} />}
          </button>
        </div>
      </div>

      <div className="terminal-body">
        {logs.length === 0 ? (
          <div className="terminal-empty">
            <span>Awaiting forge execution command...</span>
          </div>
        ) : (
          logs.map((line, idx) => formatLine(line, idx))
        )}
        <div ref={terminalEndRef} />
      </div>
    </div>
  );
}
