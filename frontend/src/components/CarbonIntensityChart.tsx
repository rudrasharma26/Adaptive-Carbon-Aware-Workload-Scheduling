import React from 'react';
import {
  ResponsiveContainer,
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
} from 'recharts';
import { CarbonTimeSeriesPoint } from '../types';
import { Zap, Info } from 'lucide-react';

interface CarbonIntensityChartProps {
  timeSeries: CarbonTimeSeriesPoint[];
  currentIntensity: number;
  unit: string;
  dataNote?: string;
  zone: string;
}

export const CarbonIntensityChart: React.FC<CarbonIntensityChartProps> = ({
  timeSeries,
  currentIntensity,
  unit,
  dataNote,
  zone,
}) => {
  // Map points strictly preserving raw intensity values without smoothing
  const chartData = (timeSeries || []).map((point, idx) => {
    let formattedTime = `Point ${idx + 1}`;
    try {
      const d = new Date(point.timestamp);
      if (!isNaN(d.getTime())) {
        formattedTime = d.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
      }
    } catch {
      formattedTime = point.timestamp || `#${idx + 1}`;
    }

    return {
      rawTimestamp: point.timestamp,
      displayTime: formattedTime,
      intensity: point.carbon_intensity,
      index: idx,
    };
  });

  const intensities = chartData.map((d) => d.intensity).filter((v) => !isNaN(v));
  const minVal = intensities.length ? Math.floor(Math.min(...intensities) * 0.9) : 0;
  const maxVal = intensities.length ? Math.ceil(Math.max(...intensities) * 1.1) : 100;

  return (
    <div id="carbon" className="rounded-xl border border-slate-800 bg-slate-900/80 p-5 sm:p-6">
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between pb-4 border-b border-slate-800 gap-3">
        <div>
          <div className="flex items-center gap-2">
            <Zap className="h-4 w-4 text-emerald-400" />
            <h2 className="font-display text-base sm:text-lg font-bold uppercase tracking-tight text-white">
              Carbon Intensity Profile
            </h2>
          </div>
          <p className="mt-1 text-xs text-slate-400 font-mono">
            Grid emission intensity time series for zone: <strong className="text-slate-200">{zone}</strong>
          </p>
        </div>

        <div className="flex items-center gap-2 text-xs font-mono text-slate-300">
          <span className="text-slate-500">Current Reading:</span>
          <span className="font-bold text-emerald-400 font-mono-numbers">
            {currentIntensity} {unit || 'gCO₂eq/kWh'}
          </span>
        </div>
      </div>

      <div className="mt-6 h-72 sm:h-80 w-full">
        {chartData.length === 0 ? (
          <div className="h-full flex items-center justify-center text-xs font-mono text-slate-500">
            No carbon time series data returned.
          </div>
        ) : (
          <ResponsiveContainer width="100%" height="100%">
            {/* Linear type preserves real, unmodified values without curve smoothing */}
            <LineChart data={chartData} margin={{ top: 15, right: 25, left: -10, bottom: 5 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" vertical={false} />
              <XAxis
                dataKey="displayTime"
                stroke="#64748b"
                tick={{ fill: '#94a3b8', fontSize: 11, fontFamily: 'JetBrains Mono' }}
                tickLine={{ stroke: '#334155' }}
              />
              <YAxis
                stroke="#64748b"
                tick={{ fill: '#94a3b8', fontSize: 11, fontFamily: 'JetBrains Mono' }}
                tickLine={{ stroke: '#334155' }}
                domain={[minVal, maxVal]}
                unit={` ${unit ? unit.split('/')[0] : 'g'}`}
              />
              <Tooltip
                content={({ active, payload }) => {
                  if (active && payload && payload.length) {
                    const item = payload[0].payload;
                    return (
                      <div className="rounded-lg border border-slate-700 bg-slate-950 p-3 shadow-xl font-mono text-xs text-slate-200">
                        <div className="text-slate-400 border-b border-slate-800 pb-1 mb-2 font-semibold">
                          Timestamp: {item.rawTimestamp}
                        </div>
                        <div className="flex justify-between gap-4 py-0.5 text-emerald-400">
                          <span>Carbon Intensity:</span>
                          <span className="font-bold text-white tabular-nums">
                            {item.intensity} {unit || 'gCO₂eq/kWh'}
                          </span>
                        </div>
                      </div>
                    );
                  }
                  return null;
                }}
              />
              <Line
                type="linear"
                dataKey="intensity"
                name="Carbon Intensity"
                stroke="#10b981"
                strokeWidth={2.5}
                dot={{ r: 3.5, fill: '#10b981', stroke: '#064e3b' }}
                activeDot={{ r: 6, fill: '#34d399', stroke: '#ffffff' }}
                isAnimationActive={false}
              />
            </LineChart>
          </ResponsiveContainer>
        )}
      </div>

      {dataNote && (
        <div className="mt-4 flex items-start gap-2 rounded-lg border border-slate-800 bg-slate-950/60 p-3 text-xs font-mono text-slate-400">
          <Info className="h-4 w-4 text-emerald-400 shrink-0 mt-0.5" />
          <span>{dataNote}</span>
        </div>
      )}
    </div>
  );
};
