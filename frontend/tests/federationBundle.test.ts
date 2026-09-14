/**
 * Guards the shape of the built federation bundle.
 *
 * bot-platform serves the addon's UI through a proxy that maps
 *   /api/addon/:id/addon-assets/<file>  ->  <addon>/dist/assets/<file>
 * so the entry chunk and every chunk it imports must live in `dist/assets/`
 * and reference each other as same-directory relative paths. Anything else -
 * an absolute `/assets/...`, or a `./assets/...` relative to the build root -
 * turns into a 404 inside the admin UI, with no failing test and no failing
 * build to warn you.
 *
 * Setting `base` in vite.config.ts is the usual way to break this.
 *
 * Run `pnpm build` before `pnpm test`; the test skips if there is no build.
 */
import { existsSync, readFileSync, readdirSync } from 'node:fs'
import { dirname, join, resolve } from 'node:path'
import { fileURLToPath } from 'node:url'
import { describe, expect, it } from 'vitest'

const DIST_ASSETS = resolve(dirname(fileURLToPath(import.meta.url)), '../dist/assets')
const ENTRY = join(DIST_ASSETS, 'addonBundle.js')

const hasBuild = existsSync(ENTRY)

describe.skipIf(!hasBuild)('the built federation bundle', () => {
  const entry = () => readFileSync(ENTRY, 'utf8')

  it('places the entry where the platform proxy looks for it', () => {
    expect(existsSync(ENTRY)).toBe(true)
  })

  it('exposes the mount function the platform calls', () => {
    expect(entry()).toContain('./mountConfiguration')
  })

  it('imports its chunks from its own directory', () => {
    const imports = [...entry().matchAll(/["'](\.\.?\/[^"']+\.js)["']/g)].map((match) => match[1])

    expect(imports.length).toBeGreaterThan(0)
    for (const specifier of imports) {
      // "./chunk.js" is right; "./assets/chunk.js" or "../chunk.js" is not.
      expect(specifier, `chunk import ${specifier} would 404 behind the addon-assets proxy`).toMatch(
        /^\.\/[^/]+\.js$/,
      )
    }
  })

  it('left no unsubstituted plugin placeholders', () => {
    // `@originjs/vite-plugin-federation` writes a `__v__css__<module id>` token
    // during the build and replaces it with the expose's CSS list afterwards.
    // On an incompatible Vite the replacement silently does not happen, the
    // token survives as a plain string, and the host dies at mount time with
    // `e.forEach is not a function`. The build reports nothing.
    expect(entry(), 'the federation plugin did not substitute __v__css__').not.toContain('__v__css__')
  })

  it('leaks no filesystem paths', () => {
    // The same failure embedded the author's absolute source path in an
    // artefact meant to be published. Worth failing on in its own right.
    for (const fragment of ['/Users/', '\\Users\\', '/home/', 'C:/', 'C:\\']) {
      expect(entry(), `${fragment} looks like a path from the build machine`).not.toContain(fragment)
    }
  })

  it('has no absolute asset URLs', () => {
    expect(entry(), 'an absolute /assets/ URL resolves against the platform origin').not.toMatch(
      /["'(]\/assets\//,
    )
  })

  it('ships every chunk the entry imports', () => {
    const present = new Set(readdirSync(DIST_ASSETS))
    const imports = [...entry().matchAll(/["'](\.\/[^"']+\.js)["']/g)].map((match) => match[1].slice(2))

    for (const chunk of imports) {
      expect(present.has(chunk), `${chunk} is imported but not in dist/assets`).toBe(true)
    }
  })
})
