/**
 * Data the host passes into the addon as the last argument of
 * mountConfiguration.
 *
 * Everything here is optional: an older host simply does not send it, and new
 * host data is added as a new optional field rather than a new positional
 * argument. Treat every field as possibly absent.
 */
export type AddonMountContext = {
  /** The instance's multilingual configuration, if the feature is on. */
  languages?: {
    defaultLanguage: string
    availableLanguages: string[]
  }
  /** The instance's dialogs, as a snapshot taken at mount time. */
  dialogs?: Array<{
    id: number
    name: string
  }>
  /** The admin UI's own language - separate from the `languages` feature. */
  ui?: {
    language: string
    /** Subscribe to language switches. Returns an unsubscribe function. */
    onLanguageChange: (callback: (language: string) => void) => () => void
  }
}

/** Props the platform passes when it mounts the configuration page. */
export type AppProps = {
  /** Prefix every API call must go through, e.g. `/api/addon/12/proxy`. */
  apiBasePath?: string
  /** Origin of the platform instance embedding the addon. */
  platformOrigin?: string
  /** Numeric id of that instance. */
  instanceId?: number
  /**
   * The host's own hash prefix, e.g. `#/instance/5/addons`. The addon's routes
   * nest under it - see src/app/browserHash.ts.
   */
  routerBasePath?: string
  /** Host data - see above. Absent when running standalone (`pnpm dev`). */
  hostContext?: AddonMountContext
}
