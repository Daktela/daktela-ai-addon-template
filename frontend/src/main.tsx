// The shared theme asks for Noto Sans. Inside the Daktela AI admin the host
// already provides it; standalone, nothing would, so load it here - this file
// is only the standalone entry point.
import '@fontsource/noto-sans/400.css'
import '@fontsource/noto-sans/500.css'
import '@fontsource/noto-sans/600.css'
import '@fontsource/noto-sans/700.css'

import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'

import App from './app/App'

// Standalone development entry point (`pnpm dev`), NOT used by the platform.
// It renders the same App that mountConfiguration.tsx mounts, so you can
// build the settings page without the platform running.
const root = document.getElementById('root')

if (root) {
  createRoot(root).render(
    <StrictMode>
      <App />
    </StrictMode>,
  )
}
