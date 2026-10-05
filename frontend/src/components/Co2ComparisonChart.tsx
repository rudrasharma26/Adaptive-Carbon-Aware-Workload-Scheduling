import React from 'react';
import {
  ResponsiveContainer,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Cell,
} from 'recharts';
import { DemoAnalysisResponse } from '../types';
import { BarChart3, Leaf, Zap, ShieldCheck } from 'lucide-react';

interface Co2ComparisonChartProps {
  data: DemoAnalysisResponse;
}

export const Co2ComparisonChart: React.FC<Co2ComparisonChartProps> = ({ data }) => {
  const runNowCo2 = data.run_now?.estimated_co2_grams ?? 0;
  const delayedCo2 = data.delayed?.estimated_co2_grams ?? 0;
  const runNowEnergy = data.run_now?.estimated_energy_kwh ?? 0;
  const delayedEnergy = data.delayed?.estimated_energy_kwh ?? 0;

  const barData = [
    {
      name: 'RUN NOW',
      co2: Number(runNowCo2.toFixed(4)),
      energy: Number(runNowEnergy.toFixed(6)),
      intensity: data.run_now?.carbon_intensity ?? data.current_carbon_intensity,
      color: '#0284c7', // Sky / blue for immediate execution
    },
    {
      name: 'DELAY',
      co2: Number(delayedCo2.toFixed(4)),
      energy: Number(delayedEnergy.toFixed(6)),
      intensity: data.delayed?.carbon_intensity ?? data.current_carbon_intensity,
      color: '#10b981', // Emerald for optimized delayed execution
    },
  ];

  const maxCo2 = Math.max(runNowCo2, delayedCo2, 0.001);

  return (
    <div id="impact" className="rounded-xl border border-slate-800 bg-slate-900/80 p-5 sm:p-6">
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between pb-4 border-b border-slate-800 gap-3">
        <div>
          <div className="flex items-center gap-2">
            <BarChart3 className="h-4 w-4 text-emerald-400" />
            <h2 className="font-display text-base sm:text-lg font-bold uppercase tracking-tight text-white">
              CO₂ Emissions Comparison
            </h2>
          </div>
          <p className="mt-1 text-xs text-slate-400 font-mono">
            Estimated carbon footprint: immediate execution vs. adaptive delayed schedule
          </p>
        </div>

        <div className="flex items-center gap-3 text-xs font-mono text-slate-400">
          <span className="flex items-center gap-1.5">
            <span className="h-2.5 w-2.5 rounded-sm bg-sky-600 inline-block" />
            <span>RUN NOW</span>
          </span>
          <span className="flex items-center gap-1.5">
            <span className="h-2.5 w-2.5 rounded-sm bg-emerald-500 inline-block" />
            <span>DELAY</span>
          </span>
        </div>
      </div>

      {/* Bar Chart */}
      <div className="mt-6 h-64 sm:h-72 w-full">
        <ResponsiveContainer width="100%" height="100%">
          <BarChart data={barData} margin={{ top: 20, right: 30, left: 0, bottom: 5 }} barSize={56}>
            <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" vertical={false} />
            <XAxis
              dataKey="name"
              stroke="#64748b"
              tick={{ fill: '#f1f5f9', fontSize: 12, fontWeight: 600, fontFamily: 'Plus Jakarta Sans' }}
              tickLine={{ stroke: '#334155' }}
            />
            <YAxis
              stroke="#64748b"
              tick={{ fill: '#94a3b8', fontSize: 11, fontFamily: 'JetBrains Mono' }}
              tickLine={{ stroke: '#334155' }}
              unit=" g"
              domain={[0, Math.ceil(maxCo2 * 1.25 * 100) / 100]}
            />
            <Tooltip
              content={({ active, payload }) => {
                if (active && payload && payload.length) {
                  const item = payload[0].payload;
                  return (
                    <div className="rounded-lg border border-slate-700 bg-slate-950 p-3 shadow-xl font-mono text-xs text-slate-200">
                      <div className="text-slate-300 font-bold border-b border-slate-800 pb-1 mb-2">
                        {item.name}
                      </div>
                      <div className="flex justify-between gap-4 py-0.5">
                        <span className="text-slate-400">Estimated CO₂:</span>
                        <span className="font-bold text-white tabular-nums">
                          {item.co2} gCO₂
                        </span>
                      </div>
                      <div className="flex justify-between gap-4 py-0.5">
                        <span className="text-slate-400">Energy (kWh):</span>
                        <span className="font-bold text-slate-300 tabular-nums">
                          {item.energy} kWh
                        </span>
                      </div>
                      <div className="flex justify-between gap-4 py-0.5">
                        <span className="text-slate-400">Grid Carbon:</span>
                        <span className="font-bold text-emerald-400 tabular-nums">
                          {item.intensity} gCO₂eq/kWh
                        </span>
                      </div>
                    </div>
                  );
                }
                return null;
              }}
            />
            <Bar dataKey="co2" radius={[4, 4, 0, 0]} isAnimationActive={false}>
              {barData.map((entry, index) => (
                <Cell key={`cell-${index}`} fill={entry.color} />
              ))}
            </Bar>
          </BarChart>
        </ResponsiveContainer>
      </div>

      {/* Below the chart displays: CO2 SAVED and SAVINGS */}
      <div className="mt-6 grid grid-cols-1 sm:grid-cols-2 gap-4 border-t border-slate-800 pt-5">
        <div className="rounded-lg border border-slate-800 bg-slate-950/70 p-4">
          <div className="flex items-center justify-between text-xs font-mono uppercase tracking-wider text-slate-400">
            <span>CO₂ Saved</span>
            <Leaf className="h-4 w-4 text-emerald-400" />
          </div>
          <div className="mt-2 flex items-baseline">
            <span className="font-mono-numbers text-2xl sm:text-3xl font-bold text-emerald-400">
              {data.co2_saved_grams.toFixed(4)}
            </span>
            <span className="ml-2 font-mono text-xs text-slate-400">gCO₂</span>
          </div>
          <div className="mt-2 text-xs font-mono text-slate-400">
            Run Now ({runNowCo2.toFixed(4)}g) vs. Delay ({delayedCo2.toFixed(4)}g)
          </div>
        </div>

        <div className="rounded-lg border border-slate-800 bg-slate-950/70 p-4">
          <div className="flex items-center justify-between text-xs font-mono uppercase tracking-wider text-slate-400">
            <span>Savings</span>
            <Zap className="h-4 w-4 text-teal-400" />
          </div>
          <div className="mt-2 flex items-baseline">
            <span className="font-mono-numbers text-2xl sm:text-3xl font-bold text-teal-300">
              {data.savings_percent.toFixed(2)}
            </span>
            <span className="ml-1.5 font-mono text-sm text-slate-400">%</span>
          </div>
          <div className="mt-2 text-xs font-mono text-slate-400">
            Reduction percentage relative to immediate execution baseline
          </div>
        </div>
      </div>
    </div>
  );
};
