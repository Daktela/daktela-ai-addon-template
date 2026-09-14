import axios, { type AxiosRequestConfig } from 'axios'

// All addon API calls go through this instance.
//
// Inside the platform the addon's UI is served from the platform's own origin
// and requests are proxied to the addon at /api/addon/:id/proxy/*. The platform
// tells us that prefix when it mounts us (the `apiBasePath` mount argument),
// and injects the tenant and auth headers on the way through - the browser
// never sees them.
//
// Standalone (`pnpm dev`) there is no prefix, and vite.config.ts fakes the
// headers instead.
export const addonAxios = axios.create()

export const configureAddonApi = (basePath?: string) => {
  addonAxios.defaults.baseURL = basePath ?? ''
}

/** Mutator used by the Orval-generated client in `src/gen/`. */
export const customAxios = <T>(config: AxiosRequestConfig): Promise<T> =>
  addonAxios({ ...config }).then((response) => response.data)

export default customAxios
