import type { JSX } from 'react'

import ExampleSettingsPage from '../pages/ExampleSettingsPage'
import GettingStartedPage from '../pages/GettingStartedPage'

// Hash routing, nested under the host's own hash route. Every hash here is a
// LOCAL one ('#/settings'); src/app/browserHash.ts translates to and from the
// real URL, which also contains the platform's prefix. Never read or write
// location.hash from a page - go through browserHash.
export type AppRoute = {
  key: string
  hash: string
  label: string
  render: (hostLanguage?: string) => JSX.Element
}

export const appRoutes: AppRoute[] = [
  {
    key: 'getting-started',
    hash: '#/getting-started',
    label: 'Getting started',
    render: (hostLanguage?: string) => <GettingStartedPage hostLanguage={hostLanguage} />,
  },
  {
    key: 'settings',
    hash: '#/settings',
    label: 'Settings',
    render: () => <ExampleSettingsPage />,
  },
]

export const defaultRoute = appRoutes[0]

/** Local hash -> route, ignoring any query string. Unknown hashes land on the default. */
export const resolveRoute = (hash: string): AppRoute =>
  appRoutes.find((route) => route.hash === stripQuery(hash)) ?? defaultRoute

const stripQuery = (hash: string) => {
  const queryStart = hash.indexOf('?')
  return queryStart === -1 ? hash : hash.slice(0, queryStart)
}
