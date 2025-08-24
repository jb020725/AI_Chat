# Frontend Setup

## Environment Variables

Create a `.env` file in the `frontend/` directory with the following variables:

### Required
- `VITE_API_URL`: Backend API URL (default: `http://127.0.0.1:8000`)

### Optional
- `VITE_DEBUG`: Enable debug logging (default: `false`)

## Example .env file
```
VITE_API_URL=http://127.0.0.1:8000
VITE_DEBUG=true
```

## Installation

1. Install dependencies:
```bash
npm install
# or
yarn install
# or
bun install
```

2. Set up your `.env` file with the backend URL

3. Start the development server:
```bash
npm run dev
# or
yarn dev
# or
bun dev
```

## Troubleshooting

### Backend Connection Issues

1. **Check if backend is running:**
   - Backend should be running on `http://127.0.0.1:8000`
   - Test with: `curl http://127.0.0.1:8000/healthz`

2. **Check CORS configuration:**
   - Backend should allow requests from `http://localhost:3000`
   - Check browser console for CORS errors

3. **Verify API URL:**
   - Check browser console for the actual URL being requested
   - Ensure `VITE_API_URL` is set correctly in your `.env` file

### Common Issues

- **CORS errors**: Backend not running or CORS not configured properly
- **404 errors**: Check if backend routes are working
- **Connection refused**: Backend server not started

## Development

- **Build**: `npm run build`
- **Preview**: `npm run preview`
- **Lint**: `npm run lint`
