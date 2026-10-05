import React from 'react';
import { DemoAnalysisResponse } from '../types';
import { Cpu, TrendingUp, Zap, Timer } from 'lucide-react';

interface TopMetricCardsProps {
  data: DemoAnalysisResponse;
}

export const TopMetricCards: React.FC<TopMetricCardsProps> = ({ data }) => {
  // Latest CPU value from cpu_history
  const latestCpu =
    data.cpu_history && data.cpu_history.length > 0
      ? data.cpu_history[data.cpu_history.length - 1]
      : 0;

  // Previous CPU value for context
  const prevCpu =
    data.cpu_history && data.cpu_history.length > 1
      ? data.cpu_history[data.cpu_history.length - 2]
      : latestCpu;

  const cpuDelta = latestCpu - prevCpu;

  return (
    <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
      {/* CARD 1: CURRENT CPU */}
      <div className="relative rounded-xl border border-slate-800 bg-slate-900/80 p-5 shadow-sm transition-all hover:border-slate-700/80">
        <div className="flex items-center justify-between text-slate-400">
          <span className="text-xs font-mono uppercase tracking-wider text-slate-400">
            Current CPU
          </span>
          <Cpu className="h-4 w-4 text-emerald-400" />
        </div>
        <div className="mt-3 flex items-baseline">
          <span className="font-mono-numbers text-3xl sm:text-4xl font-bold tracking-tight text-white">
            {latestCpu.toFixed(2)}
          </span>
          <span className="ml-1.5 font-mono text-sm uppercase text-slate-400">%</span>
        </div>
        <div className="mt-3 flex items-center justify-between text-xs font-mono text-slate-400">
          <span>Lookback: {data.lookback} steps</span>
          <span className={cpuDelta >= 0 ? 'text-amber-400' : 'text-emerald-400'}>
            {cpuDelta >= 0 ? `+${cpuDelta.toFixed(2)}%` : `${cpuDelta.toFixed(2)}%`}
          </span>
        </div>
      </div>

      {/* CARD 2: GRU PREDICTION */}
      <div className="relative rounded-xl border border-slate-800 bg-slate-900/80 p-5 shadow-sm transition-all hover:border-slate-700/80">
        <div className="flex items-center justify-between text-slate-400">
          <span className="text-xs font-mono uppercase tracking-wider text-slate-400">
            GRU Prediction
          </span>
          <TrendingUp className="h-4 w-4 text-teal-400" />
        </div>
        <div className="mt-3 flex items-baseline">
          <span className="font-mono-numbers text-3xl sm:text-4xl font-bold tracking-tight text-teal-300">
            {data.predicted_cpu_percent.toFixed(2)}
          </span>
          <span className="ml-1.5 font-mono text-sm uppercase text-slate-400">%</span>
        </div>
        <div className="mt-3 flex items-center justify-between text-xs font-mono text-slate-400">
          <span className="text-teal-400 font-medium">Next {data.horizon_minutes} minutes</span>
          <span className="text-slate-500">Horizon τ={data.horizon_minutes}m</span>
        </div>
      </div>

      {/* CARD 3: CARBON INTENSITY */}
      <div className="relative rounded-xl border border-slate-800 bg-slate-900/80 p-5 shadow-sm transition-all hover:border-slate-700/80">
        <div className="flex items-center justify-between text-slate-400">
          <span className="text-xs font-mono uppercase tracking-wider text-slate-400">
            Carbon Intensity
          </span>
          <Zap className="h-4 w-4 text-emerald-400" />
        </div>
        <div className="mt-3 flex items-baseline">
          <span className="font-mono-numbers text-3xl sm:text-4xl font-bold tracking-tight text-white">
            {data.current_carbon_intensity}
          </span>
          <span className="ml-2 font-mono text-xs text-slate-400">
            {data.carbon_unit || 'gCO₂eq/kWh'}
          </span>
        </div>
        <div className="mt-3 flex items-center justify-between text-xs font-mono text-slate-400 truncate">
          <span>Grid Region: {data.zone}</span>
          <span className="text-slate-500 truncate" title={data.current_carbon_timestamp}>
            {data.current_carbon_timestamp ? new Date(data.current_carbon_timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }) : 'Live'}
          </span>
        </div>
      </div>

      {/* CARD 4: DEADLINE */}
      <div className="relative rounded-xl border border-slate-800 bg-slate-900/80 p-5 shadow-sm transition-all hover:border-slate-700/80">
        <div className="flex items-center justify-between text-slate-400">
          <span className="text-xs font-mono uppercase tracking-wider text-slate-400">
            Deadline
          </span>
          <Timer className="h-4 w-4 text-cyan-400" />
        </div>
        <div className="mt-3 flex items-baseline">
          <span className="font-mono-numbers text-3xl sm:text-4xl font-bold tracking-tight text-white">
            {data.deadline_minutes}
          </span>
          <span className="ml-1.5 font-mono text-sm uppercase text-slate-400">min</span>
        </div>
        <div className="mt-3 flex items-center justify-between text-xs font-mono text-slate-400">
          <span>Duration: <strong className="text-slate-200 font-semibold">{data.workload_duration_minutes} min</strong></span>
          <span className={data.deadline_feasible ? 'text-emerald-400' : 'text-amber-400'}>
            {data.deadline_feasible ? 'Feasible' : '15 min execution / 30 min deadline'}
          </span>
        </div>
      </div>
    </div>
  );
};
