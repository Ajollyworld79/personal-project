import { useState } from 'react';
import { Dialog } from './Dialog';

export function Portrait({ name }: { name: string }): React.JSX.Element {
  const [open, setOpen] = useState(false);
  return <>
    <button type="button" className="portrait-trigger" aria-label={`Enlarge portrait of ${name}`} aria-haspopup="dialog" onClick={() => setOpen(true)}>
      <img src="/static/assets/images/me.jpg" alt={name} className="avatar small" width="120" height="120" />
      <span className="portrait-zoom" aria-hidden="true"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8"><path d="M14 4h6v6M20 4l-7 7M10 20H4v-6M4 20l7-7" /></svg></span>
    </button>
    {open ? <Dialog title={name} onClose={() => setOpen(false)}><img className="portrait-enlarged" src="/static/assets/images/me.jpg" alt={`Portrait of ${name}`} /></Dialog> : null}
  </>;
}
