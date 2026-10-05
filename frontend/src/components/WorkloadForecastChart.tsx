import React from 'react';
import {
  ResponsiveContainer,
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  Dot,
} from 'recharts';
import { DemoAnalysisResponse } from '../types';
import { Activity } from 'lucide-react';

interface WorkloadForecastChartProps {
  data: DemoAnalysisResponse;
}

export const WorkloadForecastChart: React.FC<WorkloadForecastChartProps> = ({ data }) => {
  const cpuHistory = data.cpu_history || [];
  const lookback = data.lookback || cpuHistory.length;
  const predictedValue = data.predicted_cpu_percent;
  const horizonMinutes = data.horizon_minutes || 5;

  // Build chart dataset
  // 24 historical points + 1 predicted point
  const chartData = cpuHistory.map((val, idx) => {
    const stepsFromNow = idx - (cpuHistory.length - 1);
    const label = stepsFromNow === 0 ? 'Now (t)' : `t${stepsFromNow}`;
    return {
      index: idx,
      label,
      actualCpu: Number(val.toFixed(4)),
      predictedCpu: idx === cpuHistory.length - 1 ? Number(val.toFixed(4)) : null,
      isPrediction: false,
    };
  });

  // Append the predicted point
  if (chartData.length > 0) {
    chartData.push({
      index: chartData.length,
      label: `+${horizonMinutes}m Forecast`,
      actualCpu: null as any,
      predictedCpu: Number(predictedValue.toFixed(4)),
      isPrediction: true,
    });
  }

  // Calculate min and max for sensible Y-axis bounds
  const allValues = [
    ...cpuHistory,
    predictedValue,
  ].filter((v) => typeof v === 'number' && !isNaN(v));
  
  const minVal = allValues.length ? Math.floor(Math.min(...allValues) * 0.85) : 0;
  const maxVal = allValues.length ? Math.ceil(Math.max(...allValues) * 1.15) : 100;

  // Custom marker for the predicted point
  const renderCustomDot = (props: any) => {
    const { cx, cy, payload } = props;
    if (payload.isPrediction) {
      return (
        <g key={`predicted-dot-${payload.index}`}>
          {/* Pulsing outer aura ring */}
          <circle cx={cx} cy={cy} r={9} fill="rgba(45, 212, 191, 0.25)" className="animate-ping" />
          <circle cx={cx} cy={cy} r={7} fill="#14b8a6" stroke="#ffffff" strokeWidth={2} />
          {/* Callout diamond marker */}
          <polygon
            points={`${cx},${cy - 5} ${cx + 5},${cy} ${cx},${cy + 5} ${cx - 5},${cy}`}
            fill="#ffffff"
          />
        </g>
      );
    }
    return null;
  };

  return (
    <div id="forecast" className="rounded-xl border border-slate-800 bg-slate-900/80 p-5 sm:p-6">
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between pb-4 border-b border-slate-800 gap-3">
        <div>
          <div className="flex items-center gap-2">
            <Activity className="h-4 w-4 text-teal-400" />
            <h2 className="font-display text-base sm:text-lg font-bold uppercase tracking-tight text-white">
              Workload Forecast Chart
            </h2>
          </div>
          <p className="mt-1 text-xs text-slate-400 font-mono">
            {lookback} historical steps from Bitbrains VM telemetry + GRU near-term prediction
          </p>
        </div>

        {/* Legend / Info Badges */}
        <div className="flex items-center gap-4 text-xs font-mono text-slate-300">
          <div className="flex items-center gap-1.5">
            <span className="h-2 w-5 bg-teal-400 rounded-full inline-block" />
            <span>Actual CPU</span>
          </div>
          <div className="flex items-center gap-1.5">
            <span className="h-2.5 w-2.5 bg-emerald-400 border border-white rotate-45 inline-block" />
            <span className="text-emerald-300 font-semibold">GRU Prediction (+{horizonMinutes}m)</span>
          </div>
        </div>
      </div>

      <div className="mt-6 h-72 sm:h-80 w-full">
        <ResponsiveContainer width="100%" height="100%">
          <LineChart data={chartData} margin={{ top: 15, right: 25, left: -10, bottom: 5 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" vertical={false} />
            <XAxis
              dataKey="label"
              stroke="#64748b"
              tick={{ fill: '#94a3b8', fontSize: 11, fontFamily: 'JetBrains Mono' }}
              tickLine={{ stroke: '#334155' }}
              interval="preserveStartEnd"
            />
            <YAxis
              stroke="#64748b"
              tick={{ fill: '#94a3b8', fontSize: 11, fontFamily: 'JetBrains Mono' }}
              tickLine={{ stroke: '#334155' }}
              domain={[minVal, maxVal]}
              unit="%"
            />
            <Tooltip
              content={({ active, payload, label }) => {
                if (active && payload && payload.length) {
                  const item = payload[0].payload;
                  return (
                    <div className="rounded-lg border border-slate-700 bg-slate-950 p-3 shadow-xl font-mono text-xs text-slate-200">
                      <div className="text-slate-400 border-b border-slate-800 pb-1 mb-2 font-semibold">
                        {label} {item.isPrediction ? '(Predicted Horizon)' : ''}
                      </div>
                      {item.actualCpu !== null && item.actualCpu !== undefined && (
                        <div className="flex justify-between gap-4 py-0.5">
                          <span className="text-teal-400">Actual CPU:</span>
                          <span className="font-bold text-white tabular-nums">
                            {Number(item.actualCpu).toFixed(4)}%
                          </span>
                        </div>
                      )}
                      {item.isPrediction && (
                        <div className="flex justify-between gap-4 py-0.5 text-emerald-300">
                          <span className="font-semibold">GRU Prediction:</span>
                          <span className="font-bold text-emerald-400 tabular-nums">
                            {Number(item.predictedCpu).toFixed(4)}%
                          </span>
                        </div>
                      )}
                    </div>
                  );
                }
                return null;
              }}
            />
            <Line
              type="monotone"
              dataKey="actualCpu"
              name="Actual CPU"
              stroke="#14b8a6"
              strokeWidth={2.5}
              dot={{ r: 2.5, fill: '#14b8a6', stroke: '#042f2e' }}
              activeDot={{ r: 5, fill: '#2dd4bf', stroke: '#ffffff' }}
              isAnimationActive={false}
            />
            <Line
              type="linear"
              dataKey="predictedCpu"
              name="GRU Prediction"
              stroke="#34d399"
              strokeWidth={2.5}
              strokeDasharray="4 4"
              dot={renderCustomDot}
              activeDot={{ r: 7, fill: '#34d399' }}
              isAnimationActive={false}
            />
          </LineChart>
        </ResponsiveContainer>
      </div>

      <div className="mt-4 flex flex-wrap items-center justify-between text-xs font-mono text-slate-400 border-t border-slate-850 pt-3 gap-2">
        <div>
          <span>Model: <strong>Trained GRU (Gated Recurrent Unit)</strong></span>
          <span className="mx-2 text-slate-600">·</span>
          <span>Sequence Length: <strong>{lookback}</strong></span>
        </div>
        <div className="text-emerald-400">
          Target Horizon: +{horizonMinutes} min → Expected CPU: {predictedValue.toFixed(4)}%
        </div>
      </div>
    </div>
  );
};
