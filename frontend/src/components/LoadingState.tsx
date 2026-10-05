import React from 'react';
import { Loader2, Activity } from 'lucide-react';

export const LoadingState: React.FC = () => {
  return (
    <div className="flex flex-col items-center justify-center min-h-[50vh] px-4">
      <div className="relative flex items-center justify-center mb-6">
        <div className="absolute h-16 w-16 rounded-full border border-emerald-500/20 animate-ping" />
        <div className="h-12 w-12 rounded-xl border border-emerald-500/40 bg-emerald-950/40 flex items-center justify-center text-emerald-400">
          <Activity className="h-6 w-6 animate-pulse" />
        </div>
      </div>

      <div className="text-center space-y-2 max-w-md">
        <div className="flex items-center justify-center gap-2 text-sm font-mono uppercase tracking-wider text-emerald-400">
          <Loader2 className="h-4 w-4 animate-spin text-emerald-400" />
          <span>Ingesting Telemetry Data</span>
        </div>
        <h2 className="font-display text-xl font-bold uppercase tracking-tight text-white">
          Fetching Scheduling Analysis
        </h2>
        <p className="text-xs font-mono text-slate-400 leading-relaxed">
          Connecting to FastAPI backend (<code className="text-slate-300">GET /api/demo</code>) on port 8008 to retrieve Bitbrains VM telemetry, GRU inference, and Electricity Maps carbon intensity.
        </p>
      </div>

      {/* Skeleton Cards Preview */}
      <div className="w-full max-w-4xl mt-10 grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 opacity-50">
        {[1, 2, 3, 4].map((i) => (
          <div key={i} className="h-28 rounded-xl border border-slate-800 bg-slate-900/60 p-4 animate-pulse">
            <div className="h-3 w-20 bg-slate-800 rounded mb-4" />
            <div className="h-7 w-28 bg-slate-750 rounded mb-2" />
            <div className="h-2.5 w-16 bg-slate-800 rounded" />
          </div>
        ))}
      </div>
    </div>
  );
};
