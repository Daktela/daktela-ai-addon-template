import { Alert, Box, Paper, Stack, Typography } from '@mui/material'

// The page an operator sees first. Replace it with something useful for your
// addon - a status summary, a link to your docs, a health indicator.
type Props = {
  /** Admin UI language reported by the host, absent when running standalone. */
  hostLanguage?: string
}

export default function GettingStartedPage({ hostLanguage }: Props) {
  return (
    <Stack spacing={2}>
      <Typography variant="h5" component="h1">
        Example Addon
      </Typography>
      <Typography color="text.secondary">
        This page is served by the addon itself and mounted into the Daktela AI admin through Module
        Federation. Everything you see here lives in <code>frontend/src/</code>.
      </Typography>

      <Alert severity="info">
        Open <strong>Settings</strong> to store credentials for this instance. Until you do,{' '}
        <code>GET /instance-configured</code> answers 409 and the platform reports the addon as not
        configured.
      </Alert>

      <Paper variant="outlined" sx={{ p: 2 }}>
        <Typography variant="h6" component="h2" gutterBottom>
          What this addon ships
        </Typography>
        <Box component="ul" sx={{ pl: 3, m: 0 }}>
          <li>
            Four builder modules to start from: <code>hello_world</code>, <code>exchange_rate</code>,{' '}
            <code>interaction_event</code> and <code>tenant_settings</code>.
          </li>
          <li>
            Two advanced ones: <code>streaming_echo</code> streams its answer as it is produced, and{' '}
            <code>local_tag</code> runs inside the platform without calling this addon at all.
          </li>
          <li>
            One integration, <code>order_lookup</code> — a tool the AI agent can decide to call.
          </li>
          <li>
            One dynamic list, <code>example_list</code>, backing a searchable select in the builder.
          </li>
        </Box>
      </Paper>

      <Typography variant="body2" color="text.secondary">
        {hostLanguage
          ? `Mounted by Daktela AI; admin language is "${hostLanguage}".`
          : 'Running standalone - nothing mounted this page, so there is no host context.'}
      </Typography>

      <Typography variant="body2" color="text.secondary">
        The full developer guide lives in the repository under <code>docs/</code> - start with
        <code> docs/01-quickstart.md</code>.
      </Typography>
    </Stack>
  )
}
