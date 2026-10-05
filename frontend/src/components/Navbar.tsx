import React from 'react';
import { RefreshCw, Activity, Server, AlertCircle } from 'lucide-react';

interface NavbarProps {
  isLoading: boolean;
  onRefresh: () => void;
  isBackendConnected: boolean;
  lastUpdated: string | null;
}

export const Navbar: React.FC<NavbarProps> = ({
  isLoading,
  onRefresh,
  isBackendConnected,
  lastUpdated,
}) => {
  return (
    <header className="sticky top-0 z-50 w-full border-b border-slate-800/80 bg-slate-950/90 backdrop-blur-md">
      <div className="mx-auto flex h-16 max-w-7xl items-center justify-between px-4 sm:px-6 lg:px-8">
        {/* Zone 1: Single text element wordmark */}
        <div className="flex items-center gap-3">
          <div className="flex h-9 w-9 items-center justify-center rounded-lg border border-emerald-500/30 bg-emerald-950/40 text-emerald-400">
            <Activity className="h-5 w-5" />
          </div>
          <span className="font-display text-base sm:text-lg font-bold tracking-tight text-white uppercase">
            Carbon-Aware Workload Scheduling
          </span>
        </div>

        {/* Zone 2: Navigation Links */}
        <nav className="hidden lg:flex items-center gap-6 text-xs uppercase tracking-wider font-mono text-slate-400">
          <a href="#overview" className="hover:text-emerald-400 transition-colors">
            Overview
          </a>
          <a href="#forecast" className="hover:text-emerald-400 transition-colors">
            CPU Forecast
          </a>
          <a href="#carbon" className="hover:text-emerald-400 transition-colors">
            Carbon Profile
          </a>
          <a href="#impact" className="hover:text-emerald-400 transition-colors">
            CO₂ Impact
          </a>
          <a href="#specs" className="hover:text-emerald-400 transition-colors">
            Specifications
          </a>
        </nav>

        {/* Zone 3: Primary Actions */}
        <div className="flex items-center gap-3">
          <div className="hidden sm:flex items-center gap-2 text-xs font-mono text-slate-400 border-r border-slate-800 pr-3">
            <span
              className={`h-2 w-2 rounded-full ${
                isBackendConnected
                  ? 'bg-emerald-500 shadow-[0_0_8px_rgba(16,185,129,0.8)]'
                  : 'bg-rose-500 shadow-[0_0_8px_rgba(244,63,93,0.8)]'
              }`}
            />
            <span className="hidden md:inline">
              {isBackendConnected ? 'FastAPI 8008' : 'Disconnected'}
            </span>
          </div>

          <button
            onClick={onRefresh}
            disabled={isLoading}
            className="flex items-center gap-2 rounded-lg border border-emerald-500/40 bg-emerald-500/10 px-3.5 py-2 text-xs font-mono font-medium text-emerald-300 transition-all hover:bg-emerald-500/20 hover:border-emerald-400 active:scale-95 disabled:opacity-50 disabled:cursor-not-allowed whitespace-nowrap shadow-sm shadow-emerald-950"
            title="Fetch analysis from backend"
          >
            <RefreshCw className={`h-3.5 w-3.5 ${isLoading ? 'animate-spin text-emerald-400' : ''}`} />
            <span>REFRESH ANALYSIS</span>
          </button>
        </div>
      </div>
    </header>
  );
};
