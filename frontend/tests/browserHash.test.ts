/**
 * The addon shares the URL with bot-platform's own hash router, so these rules
 * are not cosmetic: get them wrong and clicking the addon's menu navigates the
 * host away from the page the addon is mounted on, which looks exactly like
 * "the menu does nothing".
 */
import { beforeEach, describe, expect, it } from 'vitest'

import {
  addHashChangeListener,
  configureRouterBasePath,
  getLocationHash,
  pushHash,
  replaceHash,
  toNavigationHref,
} from '../src/app/browserHash'

const HOST_BASE = '#/instance/5/addons'

const goTo = (url: string) => window.history.replaceState(null, '', url)

describe('mounted inside bot-platform', () => {
  beforeEach(() => {
    configureRouterBasePath(HOST_BASE)
    goTo('/admin')
  })

  it('nests a local route under the host prefix', () => {
    expect(toNavigationHref('#/settings')).toBe('#/instance/5/addons/settings')
  })

  it('reads the local route back out of the real hash', () => {
    goTo(`/admin${HOST_BASE}/settings`)

    expect(getLocationHash()).toBe('#/settings')
  })

  it('treats the bare host route as "no local route yet"', () => {
    goTo(`/admin${HOST_BASE}`)

    expect(getLocationHash()).toBe('')
  })

  it('keeps the host prefix when navigating', () => {
    pushHash('#/settings')

    expect(window.location.hash).toBe('#/instance/5/addons/settings')
  })

  it('preserves the path and query string', () => {
    goTo('/admin?instance=5')

    pushHash('#/settings')

    expect(window.location.pathname).toBe('/admin')
    expect(window.location.search).toBe('?instance=5')
  })

  it('replaceHash does not add a history entry', () => {
    const before = window.history.length

    replaceHash('#/settings')

    expect(window.history.length).toBe(before)
    expect(window.location.hash).toBe('#/instance/5/addons/settings')
  })

  it('leaves a hash belonging to some other part of the host alone', () => {
    goTo('/admin#/instance/5/dialogs')

    expect(getLocationHash()).toBe('#/instance/5/dialogs')
  })

  it('tolerates a trailing slash on the base path', () => {
    configureRouterBasePath(`${HOST_BASE}/`)

    expect(toNavigationHref('#/settings')).toBe('#/instance/5/addons/settings')
  })
})

describe('running standalone', () => {
  beforeEach(() => {
    configureRouterBasePath(undefined)
    goTo('/')
  })

  it('uses local hashes unchanged', () => {
    expect(toNavigationHref('#/settings')).toBe('#/settings')

    pushHash('#/settings')

    expect(window.location.hash).toBe('#/settings')
    expect(getLocationHash()).toBe('#/settings')
  })

  it('treats an empty base path as no base path', () => {
    configureRouterBasePath('   ')

    expect(toNavigationHref('#/settings')).toBe('#/settings')
  })
})

describe('hash change subscription', () => {
  it('notifies and unsubscribes', () => {
    configureRouterBasePath(undefined)
    let calls = 0

    const unsubscribe = addHashChangeListener(() => {
      calls += 1
    })
    window.dispatchEvent(new HashChangeEvent('hashchange'))
    unsubscribe()
    window.dispatchEvent(new HashChangeEvent('hashchange'))

    expect(calls).toBe(1)
  })
})
