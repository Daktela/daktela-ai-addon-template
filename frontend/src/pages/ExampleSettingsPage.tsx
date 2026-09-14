import { zodResolver } from '@hookform/resolvers/zod'
import { Alert, Button, Paper, Stack, TextField, Typography } from '@mui/material'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { useForm } from 'react-hook-form'
import { z } from 'zod'

import { addonAxios } from '../api/axiosInstance'

// Mirrors `ExampleCredentials` in server/settings/models.py. Once you point
// Orval at your own backend (`make orval`) you can import the generated zod
// schema and hooks from `src/gen/` instead of hand-writing this.
const schema = z.object({
  api_url: z.string().min(3).max(200),
  api_token: z.string().min(3).max(200),
  display_name: z.string().min(1).max(100),
})

type Credentials = z.infer<typeof schema>

const EMPTY: Credentials = { api_url: '', api_token: '', display_name: '' }
const ENDPOINT = '/api/example_credentials'

const isNotFound = (error: unknown): boolean =>
  typeof error === 'object' && error !== null && 'response' in error
    ? (error as { response?: { status?: number } }).response?.status === 404
    : false

export default function ExampleSettingsPage() {
  const queryClient = useQueryClient()

  const existing = useQuery({
    queryKey: [ENDPOINT],
    queryFn: async () => {
      try {
        const response = await addonAxios.get<Credentials>(ENDPOINT)
        return response.data
      } catch (error) {
        // 404 means "this instance has not been configured yet" - a normal
        // first-run state, so show an empty form rather than an error.
        if (isNotFound(error)) return null
        throw error
      }
    },
  })

  const save = useMutation({
    mutationFn: (values: Credentials) => addonAxios.post(ENDPOINT, values),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: [ENDPOINT] }),
  })

  const remove = useMutation({
    mutationFn: () => addonAxios.delete(ENDPOINT),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: [ENDPOINT] }),
  })

  const form = useForm<Credentials>({
    resolver: zodResolver(schema),
    values: existing.data ?? EMPTY,
    resetOptions: { keepDirtyValues: true },
  })

  return (
    <Stack spacing={2}>
      <Typography variant="h5" component="h1">
        Settings
      </Typography>
      <Typography color="text.secondary">
        Stored per the platform instance. Saving these makes <code>/instance-configured</code> answer 200,
        which is how the platform knows the addon is ready to use.
      </Typography>

      {save.isSuccess && <Alert severity="success">Saved.</Alert>}
      {save.isError && <Alert severity="error">Could not save. Check the addon logs.</Alert>}

      <Paper variant="outlined" sx={{ p: 2 }}>
        <form onSubmit={form.handleSubmit((values) => save.mutate(values))} noValidate>
          <Stack spacing={2}>
            <TextField
              label="API URL"
              placeholder="https://api.example.com"
              error={Boolean(form.formState.errors.api_url)}
              helperText={form.formState.errors.api_url?.message}
              {...form.register('api_url')}
            />
            <TextField
              label="API token"
              type="password"
              error={Boolean(form.formState.errors.api_token)}
              helperText={form.formState.errors.api_token?.message}
              {...form.register('api_token')}
            />
            <TextField
              label="Display name"
              error={Boolean(form.formState.errors.display_name)}
              helperText={form.formState.errors.display_name?.message}
              {...form.register('display_name')}
            />
            <Stack direction="row" spacing={1}>
              <Button type="submit" variant="contained" disabled={save.isPending}>
                Save
              </Button>
              <Button
                type="button"
                color="inherit"
                disabled={!existing.data || remove.isPending}
                onClick={() => remove.mutate()}
              >
                Clear
              </Button>
            </Stack>
          </Stack>
        </form>
      </Paper>
    </Stack>
  )
}
