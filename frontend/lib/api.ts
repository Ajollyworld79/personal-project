import { useEffect, useState } from 'react';
import type { z } from 'zod';

export type Resource<T> = { status: 'loading' } | { status: 'ready'; data: T } | { status: 'error'; message: string };
export async function getJson<T>(url: string, schema: z.ZodType<T>, signal?: AbortSignal): Promise<T> {
  const response = await fetch(url, { signal: signal ?? null });
  if (!response.ok) throw new Error('Temporarily unavailable. Please try again.');
  return schema.parse(await response.json());
}
export function useResource<T>(url: string, schema: z.ZodType<T>): Resource<T> {
  const [state, setState] = useState<Resource<T>>({ status: 'loading' });
  useEffect(() => {
    const controller = new AbortController();
    void getJson(url, schema, controller.signal).then(data => {
      if (!controller.signal.aborted) setState({ status: 'ready', data });
    }).catch(() => {
      if (!controller.signal.aborted) setState({ status: 'error', message: 'Live data is temporarily unavailable.' });
    });
    return () => controller.abort();
  }, [url, schema]);
  return state;
}
