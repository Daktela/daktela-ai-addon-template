import federation from '@originjs/vite-plugin-federation'
import react from '@vitejs/plugin-react'
import { defineConfig } from 'vitest/config'

const backendPort = process.env.BACKEND_PORT ?? '8000'

// Module Federation is how bot-platform loads this addon's UI.
//
// The host is on @module-federation/vite with `type: 'module'` remotes, so the
// addon must use the same plugin - the older @originjs plugin emits a remote
// entry the host's runtime cannot consume.
//
// The build produces `dist/assets/addonBundle.js`, which bot-platform fetches
// through its own proxy at /api/addon/:id/addon-assets/addonBundle.js and then
// calls:
//
//   mountConfiguration(element, ...)  -> the addon's settings page
//
// Adding another entry point means adding it to `exposes` below.
export default defineConfig({
  // Do NOT set `base` here. With base: './' the federation plugin emits chunk
  // imports relative to the build root ('./assets/chunk.js') rather than to
  // the entry chunk, and since the entry is itself served from .../addon-assets/
  // the platform then requests .../addon-assets/assets/chunk.js and gets a 404.
  // The default leaves same-directory relative imports, which resolve
  // correctly behind bot-platform's proxy.
  plugins: [
    react(),
    federation({
      name: 'example_addon',
      // Emitted as dist/assets/addonBundle.js. That path matters: bot-platform
      // maps /api/addon/:id/addon-assets/<file> to <addon>/dist/assets/<file>,
      // so the entry and every chunk it pulls in must sit in that one
      // directory and reference each other relatively.
      filename: 'addonBundle.js',
      exposes: {
        './mountConfiguration': './src/mountConfiguration.tsx',
      },
      shared: [],
    }),
  ],
  server: {
    // Running `pnpm dev` standalone: proxy API calls to the local backend and
    // fake the headers bot-platform would normally inject, so the settings
    // page works outside the platform.
    proxy: {
      '/api': {
        target: `http://localhost:${backendPort}`,
        headers: {
          // Stand-ins for what the platform injects when it proxies a request
          // from the admin. You never run the platform locally, so these are
          // only plausible values - of these, just X-Api-Key has to be real.
          'X-Api-Key': 'default',
          'X-Customer': 'local-dev',
          'X-Bot-Url': 'https://your-instance.bot.daktela.com',
          'X-Instance-Id': '1',
          'X-Instance-Name': 'local-dev',
        },
      },
    },
  },
  build: {
    // Module Federation needs top-level await support.
    target: 'esnext',
  },
  test: {
    environment: 'jsdom',
    globals: true,
    setupFiles: ['./tests/setup.ts'],
    include: ['tests/**/*.test.{ts,tsx}'],
  },
})
