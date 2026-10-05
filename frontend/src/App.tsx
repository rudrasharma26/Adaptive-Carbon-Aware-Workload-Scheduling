import React, { useState, useEffect, useCallback } from 'react';
import { DemoAnalysisResponse } from './types';
import { getActiveBackendUrl } from './config';
import { Navbar } from './components/Navbar';
import { HeaderHero } from './components/HeaderHero';
import { TopMetricCards } from './components/TopMetricCards';
import { MainRecommendation } from './components/MainRecommendation';
import { WorkloadForecastChart } from './components/WorkloadForecastChart';
import { CarbonIntensityChart } from './components/CarbonIntensityChart';
import { Co2ComparisonChart } from './components/Co2ComparisonChart';
import { SystemDetails } from './components/SystemDetails';
import { HowItWorks } from './components/HowItWorks';
import { LoadingState } from './components/LoadingState';
import { ErrorState } from './components/ErrorState';

interface ScheduleResponse {
  zone: string;
  predicted_cpu_percent: number;
  current_carbon_intensity: number;
  current_carbon_timestamp: string;
  carbon_data_used: {
    timestamp: string;
    carbon_intensity: number;
  }[];
  workload_duration_minutes: number;
  deadline_minutes: number;
  decision: 'RUN_NOW' | 'DELAY' | string;
  delay_minutes: number;
  reason: string;
  run_now: {
    carbon_intensity: number;
    estimated_energy_kwh: number;
    estimated_co2_grams: number;
  };
  delayed: {
    carbon_intensity: number;
    estimated_energy_kwh: number;
    estimated_co2_grams: number;
  };
  co2_saved_grams: number;
  savings_percent: number;
  deadline_feasible: boolean;
}

export default function App() {
  const [data, setData] = useState<DemoAnalysisResponse | null>(null);
  const [replayData, setReplayData] = useState<DemoAnalysisResponse | null>(null);

  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [replayLoading, setReplayLoading] = useState<boolean>(false);

  const [error, setError] = useState<string | null>(null);
  const [replayError, setReplayError] = useState<string | null>(null);

  const [lastUpdated, setLastUpdated] = useState<string | null>(null);
  const [mode, setMode] = useState<'live' | 'historical'>('live');

  const fetchAnalysis = useCallback(async () => {
    setIsLoading(true);
    setError(null);

    const baseUrl = getActiveBackendUrl();
    const primaryUrl = `${baseUrl}/api/demo`;

    try {
      const res = await fetch(primaryUrl, {
        method: 'GET',
        headers: {
          Accept: 'application/json',
        },
      });

      if (!res.ok) {
        throw new Error(`Status ${res.status} ${res.statusText}`);
      }

      const json: DemoAnalysisResponse = await res.json();

      if (!json || typeof json !== 'object' || !json.decision) {
        throw new Error('Invalid response structure received from /api/demo');
      }

      setData(json);
      setLastUpdated(new Date().toLocaleTimeString());
      setError(null);
    } catch (err: any) {
      console.error('Failed to fetch live analysis:', err);
      setError(err?.message || 'Connection refused');
      setData(null);
    } finally {
      setIsLoading(false);
    }
  }, []);

  const runHistoricalReplay = useCallback(async () => {
    setReplayLoading(true);
    setReplayError(null);

    const baseUrl = getActiveBackendUrl();

    try {
      const res = await fetch(`${baseUrl}/api/schedule`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          Accept: 'application/json',
        },
        body: JSON.stringify({
          workload_duration_minutes: 15,
          deadline_minutes: 180,
          zone: 'FR',
        }),
      });

      if (!res.ok) {
        throw new Error(`Status ${res.status} ${res.statusText}`);
      }

      const json: ScheduleResponse = await res.json();

      const base = data;

      if (!base) {
        throw new Error('Live analysis must be loaded before historical replay.');
      }

      const replayView: DemoAnalysisResponse = {
        project_name: base.project_name,
        workload_name: base.workload_name,
        zone: json.zone,
        cpu_history: base.cpu_history,
        lookback: base.lookback,
        horizon_minutes: base.horizon_minutes,
        predicted_cpu_percent: json.predicted_cpu_percent,
        current_carbon_intensity: json.current_carbon_intensity,
        current_carbon_timestamp: json.current_carbon_timestamp,
        carbon_unit: base.carbon_unit,
        carbon_time_series: json.carbon_data_used,
        carbon_data_note:
          'Historical What-If Scenario: real Electricity Maps historical readings are used to demonstrate a feasible lower-carbon delay option.',
        workload_duration_minutes: json.workload_duration_minutes,
        deadline_minutes: json.deadline_minutes,
        decision: json.decision,
        delay_minutes: json.delay_minutes,
        reason: json.reason,
        run_now: json.run_now,
        delayed: json.delayed,
        co2_saved_grams: json.co2_saved_grams,
        savings_percent: json.savings_percent,
        deadline_feasible: json.deadline_feasible,
      };

      setReplayData(replayView);
      setMode('historical');
      setReplayError(null);
    } catch (err: any) {
      console.error('Historical replay failed:', err);
      setReplayError(err?.message || 'Historical replay failed');
    } finally {
      setReplayLoading(false);
    }
  }, [data]);

  useEffect(() => {
    fetchAnalysis();
  }, [fetchAnalysis]);

  const viewData =
    mode === 'historical' && replayData
      ? replayData
      : data;

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 flex flex-col font-sans">
      <Navbar
        isLoading={isLoading || replayLoading}
        onRefresh={mode === 'historical' ? runHistoricalReplay : fetchAnalysis}
        isBackendConnected={Boolean(data && !error)}
        lastUpdated={lastUpdated}
      />

      <main className="flex-1 max-w-7xl w-full mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-8">

        {isLoading && !data && <LoadingState />}

        {error && !data && (
          <ErrorState
            onRefresh={fetchAnalysis}
            isLoading={isLoading}
            errorMessage={error}
          />
        )}

        {data && (
          <>
            <HeaderHero data={viewData || data} />

            {/* Analysis mode selector */}
            <div className="rounded-xl border border-slate-800 bg-slate-900/80 p-4 sm:p-5">
              <div className="flex flex-col lg:flex-row lg:items-center lg:justify-between gap-4">
                <div>
                  <div className="text-xs font-mono uppercase tracking-widest text-slate-400">
                    Analysis Mode
                  </div>

                  <div className="mt-1 text-sm text-slate-200">
                    Compare the live decision with a real historical what-if scenario.
                  </div>
                </div>

                <div className="flex flex-wrap gap-2">
                  <button
                    onClick={() => setMode('live')}
                    className={`rounded-lg px-4 py-2.5 text-xs font-mono font-bold uppercase tracking-wider border transition ${
                      mode === 'live'
                        ? 'border-emerald-400 bg-emerald-400/10 text-emerald-300'
                        : 'border-slate-700 bg-slate-950 text-slate-400 hover:text-white'
                    }`}
                  >
                    Live Analysis
                  </button>

                  <button
                    onClick={runHistoricalReplay}
                    disabled={replayLoading}
                    className={`rounded-lg px-4 py-2.5 text-xs font-mono font-bold uppercase tracking-wider border transition ${
                      mode === 'historical'
                        ? 'border-cyan-400 bg-cyan-400/10 text-cyan-300'
                        : 'border-slate-700 bg-slate-950 text-slate-400 hover:text-white'
                    } ${replayLoading ? 'opacity-60 cursor-wait' : ''}`}
                  >
                    {replayLoading ? 'Running Replay...' : 'Historical What-If'}
                  </button>
                </div>
              </div>

              {mode === 'historical' && replayData && (
                <div className="mt-4 rounded-lg border border-cyan-500/30 bg-cyan-500/5 px-4 py-3 text-xs font-mono text-cyan-200">
                  Historical replay uses a 15-minute workload and a 180-minute deadline.
                  The backend evaluates real historical Electricity Maps readings to find a
                  feasible lower-carbon execution slot.
                </div>
              )}

              {replayError && (
                <div className="mt-4 rounded-lg border border-red-500/30 bg-red-500/5 px-4 py-3 text-xs font-mono text-red-300">
                  Historical replay error: {replayError}
                </div>
              )}
            </div>

            {/* Mode indicator */}
            <div className="flex items-center gap-3">
              <span className="h-2.5 w-2.5 rounded-full bg-emerald-400" />

              <span className="text-xs font-mono uppercase tracking-widest text-emerald-300">
                {mode === 'historical'
                  ? 'Historical What-If Scenario'
                  : 'Live Analysis'}
              </span>

              {mode === 'historical' && (
                <span className="text-xs font-mono text-slate-500">
                  Real historical carbon data · not a future forecast
                </span>
              )}
            </div>

            <TopMetricCards data={viewData || data} />

            <MainRecommendation data={viewData || data} />

            <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
              <WorkloadForecastChart data={viewData || data} />

              <CarbonIntensityChart
                timeSeries={(viewData || data).carbon_time_series}
                currentIntensity={(viewData || data).current_carbon_intensity}
                unit={(viewData || data).carbon_unit}
                dataNote={(viewData || data).carbon_data_note}
                zone={(viewData || data).zone}
              />
            </div>

            <Co2ComparisonChart data={viewData || data} />

            <SystemDetails data={viewData || data} />

            <HowItWorks />
          </>
        )}
      </main>

      <footer className="border-t border-slate-850 bg-slate-950 py-6 text-center text-xs font-mono text-slate-500">
        <div className="max-w-7xl mx-auto px-4 flex flex-col sm:flex-row items-center justify-between gap-3">
          <div>
            <span>Adaptive Carbon-Aware Workload Scheduling</span>
            <span aria-hidden="true" className="mx-2">·</span>
            <span>Bitbrains Trace Evaluation</span>
          </div>

          <div>
            Backend Target:{' '}
            <code className="text-slate-400">
              {getActiveBackendUrl()}/api/demo
            </code>
          </div>
        </div>
      </footer>
    </div>
  );
}