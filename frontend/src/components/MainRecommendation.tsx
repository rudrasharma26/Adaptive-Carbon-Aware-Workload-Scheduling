import React from 'react';
import { DemoAnalysisResponse } from '../types';
import { PlayCircle, Clock, CheckCircle2, AlertTriangle, Leaf, Percent, ShieldCheck, Flame } from 'lucide-react';

interface MainRecommendationProps {
  data: DemoAnalysisResponse;
}

export const MainRecommendation: React.FC<MainRecommendationProps> = ({ data }) => {
  const isRunNow = data.decision === 'RUN_NOW';
  const isDelay = data.decision === 'DELAY';

  const decisionLabel = isRunNow
    ? 'RUN NOW'
    : isDelay
    ? `DELAY ${data.delay_minutes} MIN`
    : data.decision;

  const isPositiveSavings = data.co2_saved_grams > 0;

  return (
    <section aria-label="Main Scheduling Recommendation" className="relative overflow-hidden rounded-2xl border border-emerald-500/40 bg-gradient-to-b from-slate-900 via-slate-900 to-slate-950 p-6 sm:p-8 shadow-xl shadow-emerald-950/20">
      {/* Decorative hairline calibration frame */}
      <div className="absolute top-0 left-0 right-0 h-1 bg-gradient-to-r from-emerald-500 via-teal-400 to-cyan-500" />
      
      <div className="flex flex-col lg:flex-row lg:items-center lg:justify-between gap-8">
        {/* Left Column: Primary Decision Display */}
        <div className="space-y-4 max-w-2xl">
          <div className="flex items-center gap-2 text-xs font-mono tracking-widest uppercase text-emerald-400">
            <span className="inline-block h-2 w-2 rounded-full bg-emerald-400 animate-pulse" />
            <span>Optimal Scheduling Decision</span>
          </div>

          <div className="flex items-center gap-4">
            <div className="flex h-14 w-14 sm:h-16 sm:w-16 shrink-0 items-center justify-center rounded-xl border border-emerald-500/30 bg-emerald-950/60 text-emerald-400 shadow-inner">
              {isRunNow ? (
                <PlayCircle className="h-8 w-8 sm:h-9 sm:w-9 text-emerald-400" />
              ) : (
                <Clock className="h-8 w-8 sm:h-9 sm:w-9 text-teal-400" />
              )}
            </div>

            <div>
              <div className="font-display text-4xl sm:text-5xl md:text-6xl font-extrabold tracking-tight text-white uppercase drop-shadow-sm">
                {decisionLabel}
              </div>
              <p className="mt-1 text-xs sm:text-sm font-mono text-slate-400">
                {isRunNow
                  ? 'Immediate execution minimizes carbon penalty or honors deadline limits.'
                  : `Defer workload execution by ${data.delay_minutes} minutes for cleaner grid conditions.`}
              </p>
            </div>
          </div>

          {/* Human-readable Reason */}
          <div className="rounded-xl border border-slate-800 bg-slate-950/60 p-4">
            <div className="text-xs font-mono uppercase tracking-wider text-slate-400 mb-1">
              Scheduler Rationale
            </div>
            <p className="text-sm sm:text-base text-slate-200 leading-relaxed font-normal">
              {data.reason}
            </p>
          </div>
        </div>

        {/* Right Column: Key Decision Metrics & Deadline Feasibility */}
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 lg:w-96 shrink-0">
          {/* Deadline Feasibility Box */}
          <div className="rounded-xl border border-slate-800 bg-slate-950/80 p-4 flex flex-col justify-between">
            <div className="flex items-center justify-between text-slate-400 mb-2">
              <span className="text-xs font-mono uppercase tracking-wider text-slate-400">
                Deadline Status
              </span>
              {data.deadline_feasible ? (
                <CheckCircle2 className="h-4 w-4 text-emerald-400" />
              ) : (
                <AlertTriangle className="h-4 w-4 text-amber-400" />
              )}
            </div>
            <div className="font-display text-lg font-bold text-slate-100">
              {data.deadline_feasible ? 'FEASIBLE' : 'DEADLINE CONSTRAINED'}
            </div>
            <p className="mt-1 text-xs font-mono text-slate-400">
              {data.deadline_feasible
                ? `Workload fits within ${data.deadline_minutes}m deadline`
                : 'No feasible delay slot is available within the deadline. Immediate execution is recommended.'}
            </p>
          </div>

          {/* CO2 Savings Metric */}
          <div className="rounded-xl border border-slate-800 bg-slate-950/80 p-4 flex flex-col justify-between">
            <div className="flex items-center justify-between text-slate-400 mb-2">
              <span className="text-xs font-mono uppercase tracking-wider text-slate-400">
                CO₂ Saved
              </span>
              <Leaf className="h-4 w-4 text-emerald-400" />
            </div>
            <div className="flex items-baseline">
              <span className="font-mono-numbers text-2xl font-bold text-emerald-400">
                {data.co2_saved_grams >= 0
                  ? data.co2_saved_grams.toFixed(4)
                  : Math.abs(data.co2_saved_grams).toFixed(4)}
              </span>
              <span className="ml-1 text-xs font-mono text-slate-400">gCO₂</span>
            </div>
            <p className="mt-1 text-xs font-mono text-slate-400">
              {isPositiveSavings
                ? 'Avoided emissions by optimal timing'
                : 'Zero or baseline emission delta'}
            </p>
          </div>

          {/* Savings Percentage */}
          <div className="rounded-xl border border-slate-800 bg-slate-950/80 p-4 flex flex-col justify-between sm:col-span-2">
            <div className="flex items-center justify-between text-slate-400 mb-2">
              <span className="text-xs font-mono uppercase tracking-wider text-slate-400">
                Emissions Reduction
              </span>
              <Percent className="h-4 w-4 text-teal-400" />
            </div>
            <div className="flex items-baseline justify-between">
              <div className="flex items-baseline">
                <span className="font-mono-numbers text-3xl font-bold text-teal-300">
                  {data.savings_percent.toFixed(2)}
                </span>
                <span className="ml-1 font-mono text-sm text-slate-400">%</span>
              </div>
              <div className="text-right text-xs font-mono text-slate-400">
                <span>Delay: <strong>{data.delay_minutes} min</strong></span>
                <span className="block text-slate-500">Duration: {data.workload_duration_minutes} min</span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
};
