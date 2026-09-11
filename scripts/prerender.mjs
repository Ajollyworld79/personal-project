import { readFileSync, writeFileSync, mkdirSync, existsSync } from 'node:fs';
import { execFileSync } from 'node:child_process';
import { render } from '../.build/server/entry-server.js';

const python = process.env.PYTHON || (existsSync('.venv/bin/python') ? '.venv/bin/python' : 'python3');
const raw = process.env.CONTENT_FILE
  ? readFileSync(process.env.CONTENT_FILE, 'utf8')
  : execFileSync(python, ['scripts/export_content.py'], { encoding: 'utf8' });
const content = JSON.parse(raw);
mkdirSync('static/dist/prerender', { recursive: true });
for (const page of ['home', 'about', 'projects']) {
  writeFileSync(`static/dist/prerender/${page}.html`, render(page, content));
}
// Hydrate from precisely the same content as the prerendered HTML.
writeFileSync('static/dist/prerender/content.json', JSON.stringify(content));
console.log('Prerendered home, about and projects; public content exported.');
