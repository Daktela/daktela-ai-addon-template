import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { useEffect, useState } from 'react'

import { configureAddonApi } from '../api/axiosInstance'
import AppLayout from '../components/AppLayout'
import {
  addHashChangeListener,
  configureRouterBasePath,
  getLocationHash,
  pushHash,
  replaceHash,
} from './browserHash'
import { type AppRoute, appRoutes, resolveRoute } from './routes'
import type { AppProps } from './types'

const createQueryClient = () =>
  new QueryClient({
    defaultOptions: {
      // A 404 from the settings endpoint means "not configured yet", which is
      // a normal state, not a transient failure worth retrying.
      queries: { retry: false },
    },
  })

export default function App({ apiBasePath, routerBasePath, hostContext }: AppProps) {
  // Before anything reads or writes the hash: teach browserHash which prefix
  // belongs to the host. See src/app/browserHash.ts.
  configureRouterBasePath(routerBasePath)

  const [queryClient] = useState(createQueryClient)
  const [route, setRoute] = useState<AppRoute>(() => resolveRoute(getLocationHash()))
  const [hostLanguage, setHostLanguage] = useState(hostContext?.ui?.language)

  useEffect(() => {
    configureAddonApi(apiBasePath)
  }, [apiBasePath])

  // The admin UI's language can change while the addon is mounted: the host
  // hands us a subscription instead of remounting. The initial value came from
  // useState above, so this only has to listen.
  useEffect(() => hostContext?.ui?.onLanguageChange(setHostLanguage), [hostContext])

  useEffect(() => {
    const syncFromHash = () => {
      const current = getLocationHash()
      const resolved = resolveRoute(current)

      // Landing on the addon with no route of ours yet (or an unknown one):
      // put the default route in the URL without adding a history entry.
      if (current !== resolved.hash) {
        replaceHash(resolved.hash)
      }

      setRoute(resolved)
    }

    syncFromHash()
    return addHashChangeListener(syncFromHash)
  }, [])

  const navigate = (next: AppRoute) => {
    // State first, then the URL: pushState does not fire `hashchange`, so the
    // listener above will not do it for us.
    setRoute(next)
    pushHash(next.hash)
  }

  return (
    <QueryClientProvider client={queryClient}>
      <AppLayout routes={appRoutes} activeKey={route.key} onNavigate={navigate}>
        {route.render(hostLanguage)}
      </AppLayout>
    </QueryClientProvider>
  )
}
