import React, { useState } from 'react';
import { AlertCircle, RefreshCw, Terminal, Settings, ExternalLink } from 'lucide-react';
import { BACKEND_URL, getActiveBackendUrl, setActiveBackendUrl } from '../config';

interface ErrorStateProps {
  onRefresh: () => void;
  isLoading: boolean;
  errorMessage?: string;
}

export const ErrorState: React.FC<ErrorStateProps> = ({
  onRefresh,
  isLoading,
  errorMessage,
}) => {
  const [showConfig, setShowConfig] = useState(false);
  const [customUrl, setCustomUrl] = useState(getActiveBackendUrl());
  const [savedNote, setSavedNote] = useState(false);

  const handleSaveUrl = (e: React.FormEvent) => {
    e.preventDefault();
    setActiveBackendUrl(customUrl);
    setSavedNote(true);
    setTimeout(() => setSavedNote(false), 2000);
    onRefresh();
  };

  const handleResetUrl = () => {
    setCustomUrl(BACKEND_URL);
    setActiveBackendUrl(BACKEND_URL);
    onRefresh();
  };

  return (
    <div className="flex flex-col items-center justify-center min-h-[60vh] px-4 py-12">
      <div className="w-full max-w-2xl rounded-2xl border border-rose-500/30 bg-slate-900/90 p-6 sm:p-8 shadow-2xl shadow-rose-950/20 text-center">
        {/* Warning Icon */}
        <div className="mx-auto flex h-14 w-14 items-center justify-center rounded-2xl border border-rose-500/40 bg-rose-950/40 text-rose-400 mb-5">
          <AlertCircle className="h-8 w-8" />
        </div>

        {/* EXACT REQUIRED MESSAGE */}
        <h2 className="font-display text-xl sm:text-2xl font-bold uppercase tracking-tight text-white">
          Backend unavailable — make sure FastAPI is running on port 8008.
        </h2>

        <p className="mt-3 text-xs sm:text-sm font-mono text-slate-300 max-w-xl mx-auto leading-relaxed">
          Could not establish connection to <code className="text-emerald-300 bg-slate-950 px-2 py-0.5 rounded border border-slate-800">{getActiveBackendUrl()}/api/demo</code>.
          Real backend data is strictly required. No synthetic or placeholder data will be displayed.
        </p>

        {errorMessage && (
          <div className="mt-4 rounded-lg border border-slate-800 bg-slate-950 p-3 text-left font-mono text-xs text-rose-300/90 max-w-lg mx-auto overflow-x-auto">
            <span className="text-slate-500">Error diagnostic: </span>
            {errorMessage}
          </div>
        )}

        {/* Primary Action Button */}
        <div className="mt-6 flex flex-wrap items-center justify-center gap-3">
          <button
            onClick={onRefresh}
            disabled={isLoading}
            className="flex items-center gap-2 rounded-lg border border-emerald-500 bg-emerald-600 px-5 py-2.5 text-xs font-mono font-bold text-white shadow-lg shadow-emerald-950 hover:bg-emerald-500 active:scale-95 disabled:opacity-50 transition-all cursor-pointer"
          >
            <RefreshCw className={`h-4 w-4 ${isLoading ? 'animate-spin' : ''}`} />
            <span>REFRESH ANALYSIS</span>
          </button>

          <button
            onClick={() => setShowConfig(!showConfig)}
            className="flex items-center gap-1.5 rounded-lg border border-slate-700 bg-slate-800 px-4 py-2.5 text-xs font-mono font-medium text-slate-300 hover:bg-slate-750 transition-all cursor-pointer"
          >
            <Settings className="h-3.5 w-3.5" />
            <span>{showConfig ? 'Hide Backend Settings' : 'Configure Endpoint'}</span>
          </button>
        </div>

        {/* Quick Instructions Terminal */}
        <div className="mt-8 rounded-xl border border-slate-800 bg-slate-950 p-4 text-left">
          <div className="flex items-center gap-2 text-xs font-mono text-slate-400 mb-2">
            <Terminal className="h-3.5 w-3.5 text-emerald-400" />
            <span className="uppercase font-semibold text-slate-300">How to launch your FastAPI backend:</span>
          </div>
          <div className="space-y-1 font-mono text-xs text-emerald-400 bg-black/60 p-3 rounded-lg border border-slate-850 overflow-x-auto">
            <p className="text-slate-400"># Start FastAPI backend on port 8008</p>
            <p>uvicorn main:app --host 0.0.0.0 --port 8008 --reload</p>
            <p className="text-slate-400 pt-1"># Ensure endpoint responds:</p>
            <p>curl http://127.0.0.1:8008/api/demo</p>
          </div>
        </div>

        {/* Optional Custom URL Override Accordion */}
        {showConfig && (
          <form onSubmit={handleSaveUrl} className="mt-6 rounded-xl border border-slate-800 bg-slate-950/80 p-4 text-left">
            <div className="text-xs font-mono uppercase text-slate-300 mb-2 font-semibold">
              Backend Endpoint URL
            </div>
            <p className="text-xs font-mono text-slate-400 mb-3">
              Default is <code className="text-emerald-400">{BACKEND_URL}</code>. If running in a container or reverse tunnel, you can point to another reachable host.
            </p>
            <div className="flex flex-col sm:flex-row gap-2">
              <input
                type="text"
                value={customUrl}
                onChange={(e) => setCustomUrl(e.target.value)}
                placeholder="http://127.0.0.1:8008"
                className="flex-1 rounded-lg border border-slate-700 bg-slate-900 px-3 py-2 text-xs font-mono text-white focus:border-emerald-500 focus:outline-none"
              />
              <button
                type="submit"
                className="rounded-lg bg-emerald-600 px-4 py-2 text-xs font-mono font-medium text-white hover:bg-emerald-500 transition-colors whitespace-nowrap cursor-pointer"
              >
                Save & Retry
              </button>
              <button
                type="button"
                onClick={handleResetUrl}
                className="rounded-lg border border-slate-700 bg-slate-800 px-3 py-2 text-xs font-mono text-slate-300 hover:bg-slate-700 transition-colors whitespace-nowrap cursor-pointer"
              >
                Reset Default
              </button>
            </div>
            {savedNote && (
              <div className="mt-2 text-xs font-mono text-emerald-400">
                Endpoint configuration updated!
              </div>
            )}
          </form>
        )}
      </div>
    </div>
  );
};
