import { createRoot, hydrateRoot } from 'react-dom/client';
import { App } from './App';
import { contentSchema, pageSchema } from './types';
import './styles.css';

const root = document.getElementById('root');
const bootstrap = document.getElementById('site-content');
if (!root || !bootstrap) throw new Error('Missing page content.');
const content = contentSchema.parse(JSON.parse(bootstrap.textContent ?? ''));
const page = pageSchema.parse(root.dataset.page);
const app = <App page={page} content={content} />;
if (root.dataset.prerendered === 'true') hydrateRoot(root, app);
else createRoot(root).render(app);
