import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'

import App from './app/App'
import type { AddonMountContext } from './app/types'

// The entry point the Daktela AI bot platform calls to render this addon's
// settings page inside its admin UI.
//
// The call is **positional** - the platform passes plain values with no names
// attached (see AddonDetailView.tsx on the platform side), so the order and
// count below are the contract; the names are ours. Older addons call these
// `cwUrl` / `cwInstanceId` / `cwNamespace` / `cwBasePath`; same positions.
//
// New host data arrives as an optional field on the last argument,
// `hostContext`, never as an eighth positional argument, so older bundles
// keep working.
//
// Return an unmount function. The platform calls it when it tears the addon
// down (navigating away, switching instance); without it the React root leaks.
type MountArgs = [
  platformOrigin?: string,
  instanceId?: number,
  environmentType?: string,
  apiBasePath?: string,
  routerBasePath?: string,
  hostContext?: AddonMountContext,
]

const mountConfiguration = (element: HTMLElement, ...args: MountArgs): (() => void) => {
  const [platformOrigin, instanceId, , apiBasePath, routerBasePath, hostContext] = args

  const root = createRoot(element)

  root.render(
    <StrictMode>
      <App
        platformOrigin={platformOrigin}
        instanceId={instanceId}
        apiBasePath={apiBasePath}
        routerBasePath={routerBasePath}
        hostContext={hostContext}
      />
    </StrictMode>,
  )

  return () => root.unmount()
}

export default mountConfiguration
