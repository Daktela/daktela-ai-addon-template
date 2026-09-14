// Generates the typed API client in src/gen/ from the backend's
// frontend-only OpenAPI schema. Run `make orval` with the backend running.
//
// Only routes tagged `frontend` end up here - see server/api/example_credentials.py.
export default {
  addon: {
    input: {
      target: `http://localhost:${process.env.BACKEND_PORT ?? '8000'}/openapi-frontend.json`,
    },
    output: {
      mode: 'split',
      target: 'src/gen/addon.ts',
      client: 'react-query',
      httpClient: 'axios',
      override: {
        mutator: {
          path: './src/api/axiosInstance.ts',
          name: 'customAxios',
        },
      },
    },
  },
}
