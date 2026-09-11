import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';

export default defineConfig({
  plugins: [react()],
  base: '/static/dist/',
  build: {
    outDir: 'static/dist',
    emptyOutDir: true,
    manifest: true,
    rolldownOptions: { input: 'frontend/main.tsx' },
  },
  server: { port: 5173, strictPort: true, cors: { origin: 'http://127.0.0.1:8000' } },
});
