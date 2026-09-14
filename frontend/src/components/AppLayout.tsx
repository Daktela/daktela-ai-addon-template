import { theme } from '@coworkers/cw-utils'
import {
  Box,
  List,
  ListItemButton,
  ListItemText,
  ScopedCssBaseline,
  ThemeProvider,
  Typography,
} from '@mui/material'
import type { ReactNode } from 'react'

import type { AppRoute } from '../app/routes'

// The shared Daktela AI Material UI theme. Using it is what makes a
// configuration page look like part of the platform instead of a bolted-on
// page - the admin itself and the other addons render with the same one.
// See docs/10-configuration-page.md for how to extend it.
//
// ScopedCssBaseline, not CssBaseline: your page renders *inside* the
// platform's own document, and a global baseline would reset the host's
// styles along with yours.

type Props = {
  routes: AppRoute[]
  activeKey: string
  onNavigate: (route: AppRoute) => void
  children: ReactNode
}

export default function AppLayout({ routes, activeKey, onNavigate, children }: Props) {
  return (
    <ThemeProvider theme={theme}>
      <ScopedCssBaseline sx={{ bgcolor: 'background.default' }}>
        <Box sx={{ display: 'flex', minHeight: '100%' }}>
          <Box
            component="nav"
            sx={{ width: 220, flexShrink: 0, borderRight: 1, borderColor: 'divider', p: 2 }}
          >
            <Typography variant="subtitle1" component="h2" sx={{ px: 1, pb: 1, fontWeight: 600 }}>
              Example Addon
            </Typography>
            <List disablePadding>
              {routes.map((route) => (
                <ListItemButton
                  key={route.key}
                  selected={route.key === activeKey}
                  onClick={() => onNavigate(route)}
                  sx={{ borderRadius: 1 }}
                >
                  <ListItemText primary={route.label} />
                </ListItemButton>
              ))}
            </List>
          </Box>
          <Box component="main" sx={{ flexGrow: 1, p: 3, maxWidth: 760 }}>
            {children}
          </Box>
        </Box>
      </ScopedCssBaseline>
    </ThemeProvider>
  )
}
