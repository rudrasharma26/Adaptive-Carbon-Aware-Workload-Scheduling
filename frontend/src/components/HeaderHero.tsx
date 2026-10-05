import React from 'react';
import { DemoAnalysisResponse } from '../types';
import { Cpu, Globe, Clock, Layers } from 'lucide-react';

interface HeaderHeroProps {
  data: DemoAnalysisResponse;
}

export const HeaderHero: React.FC<HeaderHeroProps> = ({ data }) => {
  return (
    <div id="overview" className="border-b border-slate-850 pb-8 pt-4">
      <div className="flex flex-col lg:flex-row lg:items-end lg:justify-between gap-6">
        <div className="space-y-3">
          <div className="flex items-center gap-2 text-xs font-mono uppercase tracking-wider text-emerald-400">
            <span>Dynamic Optimization</span>
            <span aria-hidden="true" className="text-slate-600">·</span>
            <span>Bitbrains Workload Telemetry</span>
            <span aria-hidden="true" className="text-slate-600">·</span>
            <span>Electricity Maps Integration</span>
          </div>

          <h1 className="font-display text-3xl sm:text-4xl md:text-5xl font-bold tracking-tight text-white uppercase leading-none">
            Adaptive Carbon-Aware
            <span className="block text-transparent bg-clip-text bg-gradient-to-r from-emerald-400 via-teal-300 to-cyan-400">
              Workload Scheduling
            </span>
          </h1>

          <p className="max-w-3xl text-sm sm:text-base text-slate-300 font-normal leading-relaxed">
            Deadline-aware workload execution using workload prediction and grid carbon intensity.
          </p>
        </div>

        {/* Quiet Meta Ribbon */}
        <div className="flex flex-wrap items-center gap-x-5 gap-y-2 text-xs font-mono text-slate-400 border border-slate-800 bg-slate-900/60 rounded-lg p-3 lg:self-start">
          <div className="flex items-center gap-1.5">
            <Layers className="h-3.5 w-3.5 text-emerald-400" />
            <span className="text-slate-500">WORKLOAD:</span>
            <span className="font-semibold text-slate-200">{data.workload_name}</span>
          </div>
          <span aria-hidden="true" className="text-slate-700">|</span>
          <div className="flex items-center gap-1.5">
            <Globe className="h-3.5 w-3.5 text-teal-400" />
            <span className="text-slate-500">ZONE:</span>
            <span className="font-semibold text-slate-200">{data.zone}</span>
          </div>
          <span aria-hidden="true" className="text-slate-700">|</span>
          <div className="flex items-center gap-1.5">
            <Clock className="h-3.5 w-3.5 text-cyan-400" />
            <span className="text-slate-500">HORIZON:</span>
            <span className="font-semibold text-slate-200">{data.horizon_minutes}m</span>
          </div>
        </div>
      </div>
    </div>
  );
};
