import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import type { ReactNode } from 'react'
import { beforeEach, describe, expect, it, vi } from 'vitest'

import { addonAxios } from '../src/api/axiosInstance'
import ExampleSettingsPage from '../src/pages/ExampleSettingsPage'

const notFound = { response: { status: 404 } }

const wrapper = ({ children }: { children: ReactNode }) => {
  const client = new QueryClient({ defaultOptions: { queries: { retry: false } } })
  return <QueryClientProvider client={client}>{children}</QueryClientProvider>
}

describe('ExampleSettingsPage', () => {
  beforeEach(() => {
    vi.restoreAllMocks()
  })

  it('shows an empty form when the instance has no credentials yet', async () => {
    vi.spyOn(addonAxios, 'get').mockRejectedValue(notFound)

    render(<ExampleSettingsPage />, { wrapper })

    await waitFor(() => expect(screen.getByLabelText('API URL')).toHaveValue(''))
  })

  it('prefills the form with stored credentials', async () => {
    vi.spyOn(addonAxios, 'get').mockResolvedValue({
      data: { api_url: 'https://api.example.com', api_token: 'token-1', display_name: 'Acme' },
    })

    render(<ExampleSettingsPage />, { wrapper })

    await waitFor(() => expect(screen.getByLabelText('API URL')).toHaveValue('https://api.example.com'))
  })

  it('posts the form to the addon backend', async () => {
    vi.spyOn(addonAxios, 'get').mockRejectedValue(notFound)
    const post = vi.spyOn(addonAxios, 'post').mockResolvedValue({ data: {} })

    render(<ExampleSettingsPage />, { wrapper })

    await userEvent.type(screen.getByLabelText('API URL'), 'https://api.example.com')
    await userEvent.type(screen.getByLabelText('API token'), 'token-1')
    await userEvent.type(screen.getByLabelText('Display name'), 'Acme')
    await userEvent.click(screen.getByRole('button', { name: 'Save' }))

    await waitFor(() =>
      expect(post).toHaveBeenCalledWith('/api/example_credentials', {
        api_url: 'https://api.example.com',
        api_token: 'token-1',
        display_name: 'Acme',
      }),
    )
  })

  it('refuses to submit an invalid payload', async () => {
    vi.spyOn(addonAxios, 'get').mockRejectedValue(notFound)
    const post = vi.spyOn(addonAxios, 'post').mockResolvedValue({ data: {} })

    render(<ExampleSettingsPage />, { wrapper })

    await userEvent.type(screen.getByLabelText('API URL'), 'x')
    await userEvent.click(screen.getByRole('button', { name: 'Save' }))

    await waitFor(() => expect(screen.getAllByText(/too small/i).length).toBeGreaterThan(0))
    expect(post).not.toHaveBeenCalled()
  })
})
