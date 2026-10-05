import React from 'react';
import { Layers, Brain, Radio, Gauge } from 'lucide-react';

export const HowItWorks: React.FC = () => {
  const steps = [
    {
      number: '01',
      title: 'Workload Ingestion',
      description: 'Historical workload data from Bitbrains VM 846 is used.',
      detail: '24 lookback steps of CPU utilization captures trace dynamics.',
      icon: Layers,
    },
    {
      number: '02',
      title: 'Workload Prediction',
      description: 'The trained GRU predicts near-term CPU usage.',
      detail: 'Recurrent architecture estimates execution power consumption over horizon τ.',
      icon: Brain,
    },
    {
      number: '03',
      title: 'Carbon Intensity Feed',
      description: 'Electricity Maps provides carbon intensity.',
      detail: 'Live grid marginal emissions data mapped across regional balancing authorities.',
      icon: Radio,
    },
    {
      number: '04',
      title: 'Adaptive Scheduling',
      description: 'The scheduling logic selects a feasible lower-carbon execution option.',
      detail: 'Evaluates immediate vs. delayed options while strictly enforcing completion deadlines.',
      icon: Gauge,
    },
  ];

  return (
    <section aria-label="Methodology Explanation" className="rounded-xl border border-slate-800 bg-slate-900/60 p-5 sm:p-6">
      <div className="pb-4 border-b border-slate-800">
        <h2 className="font-display text-base sm:text-lg font-bold uppercase tracking-tight text-white">
          System Architecture & Scheduling Workflow
        </h2>
        <p className="mt-1 text-xs text-slate-400 font-mono">
          End-to-end telemetry pipeline from trace ingestion to carbon-optimal execution
        </p>
      </div>

      <div className="mt-6 grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        {steps.map((step, idx) => {
          const Icon = step.icon;
          return (
            <div
              key={idx}
              className="relative rounded-lg border border-slate-800/80 bg-slate-950/70 p-4 transition-all hover:border-emerald-500/30 flex flex-col justify-between"
            >
              <div>
                <div className="flex items-center justify-between mb-3">
                  <span className="font-display text-xs font-bold text-emerald-400/90 font-mono">
                    {step.number}
                  </span>
                  <div className="h-7 w-7 rounded-md border border-slate-800 bg-slate-900 flex items-center justify-center text-slate-300">
                    <Icon className="h-3.5 w-3.5 text-teal-400" />
                  </div>
                </div>

                <h3 className="font-display text-sm font-semibold text-slate-100 uppercase tracking-tight">
                  {step.title}
                </h3>

                <p className="mt-2 text-xs text-slate-300 leading-relaxed">
                  {step.description}
                </p>
              </div>

              <div className="mt-3 text-xs font-mono text-slate-400 border-t border-slate-850 pt-2.5">
                {step.detail}
              </div>
            </div>
          );
        })}
      </div>
    </section>
  );
};
