/**
 * Navigation inside a host that already owns the URL.
 *
 * the platform's admin UI is itself a hash router. When it mounts the addon,
 * the browser is at something like
 *
 *   https://platform.example.com/#/instance/5/addons
 *
 * and it passes that prefix to `mountConfiguration` as `routerBasePath`. The
 * addon's own routes have to be **nested under it**:
 *
 *   local  #/settings
 *   actual #/instance/5/addons/settings
 *
 * Two rules follow, and breaking either one makes the addon's menu look dead
 * because the host navigates away from the page the addon is mounted on:
 *
 * 1. Never assign to `location.hash`. That replaces the host's route with
 *    yours. Use `history.pushState` / `replaceState`, keeping `pathname` and
 *    `search` intact.
 * 2. Never read `location.hash` directly. Strip the base off first, so the
 *    rest of the app only ever deals in local hashes like `#/settings`.
 *
 * Standalone (`pnpm dev`) there is no base, and everything below is a no-op
 * pass-through.
 */

let routerBasePath: string | undefined

const withHash = (hash: string) => `${globalThis.location.pathname}${globalThis.location.search}${hash}`

const normaliseBasePath = (value: string | undefined) => {
  const trimmed = value?.trim()

  if (!trimmed) {
    return undefined
  }

  return trimmed.endsWith('/') ? trimmed.slice(0, -1) : trimmed
}

const normaliseLocalHash = (hash: string) => {
  if (hash === '') return ''
  if (hash.startsWith('#')) return hash
  return hash.startsWith('/') ? `#${hash}` : `#/${hash}`
}

/** `#/settings` -> `#/instance/5/addons/settings` */
const toFullHash = (hash: string) => {
  const local = normaliseLocalHash(hash)

  if (routerBasePath === undefined) {
    return local
  }

  if (local === '' || local === '#') {
    return routerBasePath
  }

  return `${routerBasePath}${local.slice(1)}`
}

/** `#/instance/5/addons/settings` -> `#/settings` */
const toLocalHash = (hash: string) => {
  if (routerBasePath === undefined) {
    return hash
  }

  if (hash === routerBasePath) {
    return ''
  }

  if (hash.startsWith(`${routerBasePath}/`) || hash.startsWith(`${routerBasePath}?`)) {
    return `#${hash.slice(routerBasePath.length)}`
  }

  // Some other part of the host's UI - not ours to interpret.
  return hash
}

/** Call once with the `routerBasePath` the host passed to mountConfiguration. */
export const configureRouterBasePath = (value?: string) => {
  routerBasePath = normaliseBasePath(value)
}

export const getLocationHash = () => toLocalHash(globalThis.location.hash)

/** Href for an anchor, so middle-click and "copy link" produce a working URL. */
export const toNavigationHref = (hash: string) => toFullHash(hash)

export const replaceHash = (hash: string) => {
  globalThis.history.replaceState(null, '', withHash(toFullHash(hash)))
}

export const pushHash = (hash: string) => {
  globalThis.history.pushState(null, '', withHash(toFullHash(hash)))
}

export const addHashChangeListener = (listener: () => void) => {
  globalThis.addEventListener('hashchange', listener)
  return () => globalThis.removeEventListener('hashchange', listener)
}
