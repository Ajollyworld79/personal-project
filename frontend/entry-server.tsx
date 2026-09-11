import { renderToString } from 'react-dom/server';
import { App } from './App';
import { contentSchema, pageSchema } from './types';

export function render(page: unknown, content: unknown): string {
  return renderToString(<App page={pageSchema.parse(page)} content={contentSchema.parse(content)} />);
}
