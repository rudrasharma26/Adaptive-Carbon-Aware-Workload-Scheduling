export interface CarbonTimeSeriesPoint {
  timestamp: string;
  carbon_intensity: number;
}

export interface ExecutionOption {
  carbon_intensity: number;
  estimated_energy_kwh: number;
  estimated_co2_grams: number;
}

export interface DemoAnalysisResponse {
  project_name: string;
  workload_name: string;
  zone: string;
  cpu_history: number[];
  lookback: number;
  horizon_minutes: number;
  predicted_cpu_percent: number;
  current_carbon_intensity: number;
  current_carbon_timestamp: string;
  carbon_unit: string;
  carbon_time_series: CarbonTimeSeriesPoint[];
  carbon_data_note?: string;
  workload_duration_minutes: number;
  deadline_minutes: number;
  decision: 'RUN_NOW' | 'DELAY' | string;
  delay_minutes: number;
  reason: string;
  run_now: ExecutionOption;
  delayed: ExecutionOption;
  co2_saved_grams: number;
  savings_percent: number;
  deadline_feasible: boolean;
}
