import { chatAnswerSchema, chatEventSchema } from '../types';
import type { ChatMeta } from '../types';

export class ChatError extends Error {
  constructor(message: string, public readonly retryable: boolean) { super(message); }
}
export async function streamAnswer(question: string, signal: AbortSignal, onText: (text: string) => void, onMeta: (meta: ChatMeta) => void): Promise<void> {
  const response = await fetch('/api/cv-chat-stream', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ query: question }), signal });
  if (response.status === 429) throw new ChatError('Too many questions. Please wait a moment and try again.', false);
  if (!response.ok || !response.body) throw new ChatError('The assistant is temporarily unavailable.', true);
  const reader = response.body.getReader();
  const decoder = new TextDecoder();
  let buffer = '', answer = '', finished = false;
  function consume(frame: string): void {
    const raw = frame.split('\n').filter(line => line.startsWith('data:')).map(line => line.slice(5).trimStart()).join('\n');
    if (!raw) return;
    const event = chatEventSchema.parse(JSON.parse(raw));
    if (event.type === 'meta') onMeta(event);
    if (event.type === 'token') { answer += event.t; onText(answer); }
    if (event.type === 'done') finished = true;
  }
  try {
    while (!finished) {
      const { value, done } = await reader.read();
      buffer += decoder.decode(value, { stream: !done });
      buffer = buffer.replace(/\r\n/g, '\n');
      let boundary = buffer.indexOf('\n\n');
      while (boundary !== -1) {
        consume(buffer.slice(0, boundary)); buffer = buffer.slice(boundary + 2); boundary = buffer.indexOf('\n\n');
      }
      if (done) { if (buffer.trim()) consume(buffer); break; }
    }
    if (!finished || !answer.trim()) throw new ChatError('The answer was interrupted. Please try again.', !answer);
  } finally { await reader.cancel().catch(() => {}); reader.releaseLock(); }
}
export async function fallbackAnswer(question: string, signal: AbortSignal): Promise<{ answer: string; meta: ChatMeta }> {
  const response = await fetch('/api/cv-chat', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ query: question }), signal });
  if (response.status === 429) throw new ChatError('Too many questions. Please wait a moment and try again.', false);
  if (!response.ok) throw new ChatError('Could not reach the assistant. Please try again.', false);
  const data = chatAnswerSchema.parse(await response.json());
  return { answer: data.answer, meta: data };
}
