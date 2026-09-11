import { lazy, Suspense, useEffect, useRef, useState } from 'react';
import type { ChatMeta } from '../types';
import { ChatError, fallbackAnswer, streamAnswer } from '../lib/chat';

const Markdown = lazy(() => import('./Markdown'));
const suggestions = ["What is Gustav's experience with LLMs and RAG?", 'Hvilke projekter har Gustav bygget?', 'What tech stack does Gustav use?'];
type Message = { id: number; role: 'user' | 'assistant'; text: string };

export function Chat(): React.JSX.Element {
  const [messages, setMessages] = useState<Message[]>([]);
  const [query, setQuery] = useState('');
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState('');
  const [meta, setMeta] = useState<ChatMeta | null>(null);
  const request = useRef<AbortController | null>(null);
  const nextId = useRef(0);
  const scroll = useRef<HTMLDivElement>(null);
  const input = useRef<HTMLInputElement>(null);
  useEffect(() => () => request.current?.abort(), []);
  useEffect(() => { const el = scroll.current; if (el) el.scrollTop = el.scrollHeight; }, [messages]);
  async function ask(question: string): Promise<void> {
    const clean = question.trim();
    if (!clean || request.current) return;
    const controller = new AbortController(); request.current = controller;
    const id = ++nextId.current;
    setMessages(current => [...current, { id: id * 2, role: 'user', text: clean }, { id: id * 2 + 1, role: 'assistant', text: '' }]);
    setQuery(''); setBusy(true); setError(''); setMeta(null);
    let receivedText = false;
    const onText = (text: string): void => {
      if (controller.signal.aborted) return;
      receivedText ||= Boolean(text);
      setMessages(current => current.map(message => message.id === id * 2 + 1 ? { ...message, text } : message));
    };
    try {
      try { await streamAnswer(clean, controller.signal, onText, setMeta); }
      catch (e) {
        if (controller.signal.aborted) return;
        if (receivedText || (e instanceof ChatError && !e.retryable)) throw e;
        const fallback = await fallbackAnswer(clean, controller.signal); onText(fallback.answer); setMeta(fallback.meta);
      }
    } catch (e) {
      if (!controller.signal.aborted) {
        setQuery(clean);
        setError(e instanceof ChatError ? e.message : 'Could not reach the assistant. Please try again.');
      }
    } finally {
      request.current = null;
      if (!controller.signal.aborted) { setBusy(false); input.current?.focus({ preventScroll: true }); }
    }
  }
  return <section className="chat-widget" id="cv-chat" aria-labelledby="chat-heading">
    <div className="chat-widget-header"><span className="meta" id="chat-heading"><span className="dot" aria-hidden="true" />cv-chat.py · live</span><span className="traffic-dots" aria-hidden="true"><span /><span /><span /></span></div>
    <div className="chat-widget-body" ref={scroll} role="log" aria-label="Conversation" aria-live="polite" aria-busy={busy}>
      {messages.length === 0 ? <><div className="chat-prompt"><span className="label">stdin</span>Ask anything about Gustav — his CV, projects, or LLM work. I'll answer in real time.</div><div className="chat-suggestions">{suggestions.map(q => <button className="chat-suggestion" type="button" key={q} onClick={() => void ask(q)}>{q}</button>)}</div></> : null}
      {messages.map(message => <div key={message.id} className={`chat-message chat-msg ${message.role === 'assistant' ? 'bot assistant' : 'user'}`}><span className="label">{message.role === 'user' ? 'You' : 'CV assistant'}</span>{message.role === 'assistant' ? <Suspense fallback={<p>{message.text}</p>}><Markdown text={message.text || (busy ? 'Looking through my CV…' : '')} /></Suspense> : <p>{message.text}</p>}</div>)}
    </div>
    {meta ? <details className="rag-trace chat-trace"><summary>{meta.source === 'rag' ? 'Answer sources' : 'Using saved CV facts'}</summary>
      {meta.source === 'rag' ? <><p>{meta.model} {meta.ai_ms != null ? `· ${(meta.ai_ms / 1000).toFixed(1)}s` : ''}</p><ul>{meta.sources?.map((source, i) => <li key={`${source.filename}-${i}`}><strong>{source.filename}</strong> · {source.score.toFixed(2)}<p>{source.excerpt}</p></li>)}</ul></> : <p>The live search is unavailable. This answer uses predefined facts about Gustav.</p>}
    </details> : null}
    {error ? <p className="error chat-error" role="alert">{error}</p> : null}
    <form className="chat-input-row" onSubmit={event => { event.preventDefault(); void ask(query); }}>
      <label className="sr-only" htmlFor="cv-question">Your question about Gustav</label>
      <span className="prefix" aria-hidden="true">&gt;&gt;&gt;</span><input ref={input} id="cv-question" value={query} maxLength={2000} onChange={event => setQuery(event.target.value)} placeholder="Ask my CV…" autoComplete="off" />
      <button disabled={busy || !query.trim()} type="submit">{busy ? 'WAIT' : 'RUN'}</button>
    </form>

  </section>;
}
