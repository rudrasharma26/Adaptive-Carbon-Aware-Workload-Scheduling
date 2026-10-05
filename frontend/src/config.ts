/**
 * Backend Configuration
 * Keep the backend URL in ONE configuration constant so it can easily be changed later.
 */
export const BACKEND_URL = '/api';

/**
 * Storage key for optional URL override if running in a different container/host.
 */
const BACKEND_URL_STORAGE_KEY = 'carbon_scheduler_backend_url';

export function getActiveBackendUrl(): string {
  if (typeof window !== 'undefined') {
    const override = localStorage.getItem(BACKEND_URL_STORAGE_KEY);
    if (override && override.trim()) {
      return override.trim().replace(/\/+$/, '');
    }
  }
  return BACKEND_URL;
}

export function setActiveBackendUrl(url: string): void {
  if (typeof window !== 'undefined') {
    if (!url || url.trim() === BACKEND_URL) {
      localStorage.removeItem(BACKEND_URL_STORAGE_KEY);
    } else {
      localStorage.setItem(BACKEND_URL_STORAGE_KEY, url.trim().replace(/\/+$/, ''));
    }
  }
}
