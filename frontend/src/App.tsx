import React, { useState, useEffect, useCallback } from 'react';
import { DemoAnalysisResponse } from './types';
import { BACKEND_URL, getActiveBackendUrl } from './config';
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

export default function App() {
  const [data, setData] = useState<DemoAnalysisResponse | null>(null);
  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);
  const [lastUpdated, setLastUpdated] = useState<string | null>(null);

  const fetchAnalysis = useCallback(async () => {
    setIsLoading(true);
    setError(null);

    const baseUrl = getActiveBackendUrl();
    const primaryUrl = `${baseUrl}/api/demo`;

    try {
      // First attempt: fetch from the configured base URL (default http://127.0.0.1:8008/api/demo)
      let res: Response | null = null;
      let fetchError: any = null;

      try {
        res = await fetch(primaryUrl, {
          method: 'GET',
          headers: {
            Accept: 'application/json',
          },
        });
      } catch (err: any) {
        fetchError = err;
        // If in browser and direct localhost fetch is blocked or fails, try relative proxy /api/demo
        if (typeof window !== 'undefined' && window.location.origin !== baseUrl) {
          try {
            res = await fetch('/api/demo', {
              method: 'GET',
              headers: {
                Accept: 'application/json',
              },
            });
          } catch {
            // keep original error
          }
        }
      }

      if (!res || !res.ok) {
        const statusText = res ? `Status ${res.status} ${res.statusText}` : fetchError?.message || 'Network connection failed';
        throw new Error(statusText);
      }

      const json: DemoAnalysisResponse = await res.json();
      
      // Basic sanity check to ensure response shape is valid
      if (!json || typeof json !== 'object' || !json.decision) {
        throw new Error('Invalid response structure received from /api/demo');
      }

      setData(json);
      setLastUpdated(new Date().toLocaleTimeString());
      setError(null);
    } catch (err: any) {
      console.error('Failed to fetch from backend:', err);
      setError(err?.message || 'Connection refused');
      setData(null);
    } finally {
      setIsLoading(false);
    }
  }, []);

  // Fetch on initial page load
  useEffect(() => {
    fetchAnalysis();
  }, [fetchAnalysis]);

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 flex flex-col font-sans">
      {/* Top Bar Navigation */}
      <Navbar
        isLoading={isLoading}
        onRefresh={fetchAnalysis}
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
            {/* Header & Meta */}
            <HeaderHero data={data} />

            {/* Top Metric Cards */}
            <TopMetricCards data={data} />

            {/* Main Centerpiece Recommendation */}
            <MainRecommendation data={data} />

            {/* Charts Section: 2 Columns */}
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
              {/* Workload Forecast Line Chart */}
              <WorkloadForecastChart data={data} />

              {/* Carbon Intensity Profile Chart */}
              <CarbonIntensityChart
                timeSeries={data.carbon_time_series}
                currentIntensity={data.current_carbon_intensity}
                unit={data.carbon_unit}
                dataNote={data.carbon_data_note}
                zone={data.zone}
              />
            </div>

            {/* CO2 Emissions Comparison Bar Chart */}
            <Co2ComparisonChart data={data} />

            {/* System Details / Specifications */}
            <SystemDetails data={data} />

            {/* How It Works Explanation */}
            <HowItWorks />
          </>
        )}
      </main>

      {/* Quiet Academic / Research Footer */}
      <footer className="border-t border-slate-850 bg-slate-950 py-6 text-center text-xs font-mono text-slate-500">
        <div className="max-w-7xl mx-auto px-4 flex flex-col sm:flex-row items-center justify-between gap-3">
          <div>
            <span>Adaptive Carbon-Aware Workload Scheduling</span>
            <span aria-hidden="true" className="mx-2">·</span>
            <span>Bitbrains Trace Evaluation</span>
          </div>
          <div>
            Backend Target: <code className="text-slate-400">{getActiveBackendUrl()}/api/demo</code>
          </div>
        </div>
      </footer>
    </div>
  );
}
