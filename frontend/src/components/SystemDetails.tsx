import React from 'react';
import { DemoAnalysisResponse } from '../types';
import { Database, CheckCircle, XCircle } from 'lucide-react';

interface SystemDetailsProps {
  data: DemoAnalysisResponse;
}

export const SystemDetails: React.FC<SystemDetailsProps> = ({ data }) => {
  const details = [
    {
      label: 'Workload',
      value: data.workload_name,
      description: 'Bitbrains FastStorage trace container VM',
    },
    {
      label: 'Zone',
      value: data.zone,
      description: 'Electricity Maps country/grid bidding zone',
    },
    {
      label: 'Forecast horizon',
      value: `${data.horizon_minutes} minutes`,
      description: 'Forward-looking GRU window τ',
    },
    {
      label: 'Workload duration',
      value: `${data.workload_duration_minutes} minutes`,
      description: 'Expected execution runtime duration',
    },
    {
      label: 'Deadline',
      value: `${data.deadline_minutes} minutes`,
      description: 'Maximum allowable completion threshold',
    },
    {
      label: 'Current carbon intensity',
      value: `${data.current_carbon_intensity} ${data.carbon_unit || 'gCO₂eq/kWh'}`,
      description: 'Real-time grid marginal carbon factor',
    },
    {
      label: 'Predicted CPU',
      value: `${data.predicted_cpu_percent.toFixed(4)}%`,
      description: 'Recurrent model inferred utilization',
    },
    {
      label: 'Decision',
      value: data.decision,
      description: 'Scheduler optimal execution policy',
    },
    {
      label: 'Delay',
      value: `${data.delay_minutes} minutes`,
      description: 'Scheduled execution offset from arrival',
    },
  ];

  return (
    <div id="specs" className="rounded-xl border border-slate-800 bg-slate-900/80 p-5 sm:p-6">
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between pb-4 border-b border-slate-800 gap-3">
        <div className="flex items-center gap-2">
          <Database className="h-4 w-4 text-emerald-400" />
          <h2 className="font-display text-base sm:text-lg font-bold uppercase tracking-tight text-white">
            System & Parameter Specifications
          </h2>
        </div>

        {/* DEADLINE STATUS HIGHLIGHT */}
        <div className="flex items-center gap-2 text-xs font-mono">
          <span className="text-slate-400">DEADLINE STATUS:</span>
          {data.deadline_feasible ? (
            <span className="flex items-center gap-1.5 font-bold text-emerald-400">
              <CheckCircle className="h-3.5 w-3.5" />
              <span>FEASIBLE (true)</span>
            </span>
          ) : (
            <span className="flex items-center gap-1.5 font-bold text-rose-400">
              <XCircle className="h-3.5 w-3.5" />
              <span>DELAY NOT FEASIBLE (false)</span>
            </span>
          )}
        </div>
      </div>

      <div className="mt-5 grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
        {details.map((item, idx) => (
          <div
            key={idx}
            className="rounded-lg border border-slate-800/80 bg-slate-950/60 p-3.5 flex flex-col justify-between"
          >
            <div>
              <div className="text-xs font-mono uppercase tracking-wider text-slate-400">
                {item.label}
              </div>
              <div className="mt-1 font-mono-numbers text-base font-semibold text-slate-100">
                {item.value}
              </div>
            </div>
            <div className="mt-2 text-xs font-mono text-slate-400">
              {item.description}
            </div>
          </div>
        ))}

        {/* Explicit Deadline Status Detail Card */}
        <div className="rounded-lg border border-slate-800/80 bg-slate-950/60 p-3.5 flex flex-col justify-between">
          <div>
            <div className="text-xs font-mono uppercase tracking-wider text-slate-400">
              Deadline Status
            </div>
            <div className="mt-1 flex items-center gap-1.5 font-mono text-base font-semibold">
              {data.deadline_feasible ? (
                <span className="text-emerald-400">true (Constraint Satisfied)</span>
              ) : (
                <span className="text-rose-400">false (Deadline satisfied — immediate execution required)</span>
              )}
            </div>
          </div>
          <div className="mt-2 text-xs font-mono text-slate-400">
            Workload completion {data.delay_minutes + data.workload_duration_minutes}m ≤ {data.deadline_minutes}m
          </div>
        </div>
      </div>
    </div>
  );
};
