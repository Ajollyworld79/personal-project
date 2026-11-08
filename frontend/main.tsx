import { createRoot, hydrateRoot } from 'react-dom/client';
import { App } from './App';
import { contentSchema, pageSchema } from './types';
// Self-hosted fonts: same families and weights the site used from Google Fonts,
// without sending visitors' IP addresses to Google.
import '@fontsource/inter/400.css';
import '@fontsource/inter/500.css';
import '@fontsource/inter/600.css';
import '@fontsource/inter/700.css';
import '@fontsource/inter/800.css';
import '@fontsource/jetbrains-mono/400.css';
import '@fontsource/jetbrains-mono/500.css';
import '@fontsource/jetbrains-mono/600.css';
import '@fontsource/jetbrains-mono/700.css';
import './styles.css';

const root = document.getElementById('root');
const bootstrap = document.getElementById('site-content');
if (!root || !bootstrap) throw new Error('Missing page content.');
const content = contentSchema.parse(JSON.parse(bootstrap.textContent ?? ''));
const page = pageSchema.parse(root.dataset.page);
const app = <App page={page} content={content} />;
if (root.dataset.prerendered === 'true') hydrateRoot(root, app);
else createRoot(root).render(app);
