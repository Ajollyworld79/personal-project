import type { Content, Page } from './types';
import { Home } from './pages/Home';
import { About } from './pages/About';
import { Projects } from './pages/Projects';

export function App({ page, content }: { page: Page; content: Content }): React.JSX.Element {
  const links = [
    { href: '/', label: 'Home', code: 'home' }, { href: '/about', label: 'About', code: 'about' },
    { href: '/projects', label: 'Projects', code: 'projects' }, { href: `https://github.com/${content.cv.contact.github}`, label: 'GitHub', code: 'github' },
    { href: content.projects.find(p => p.slug === 'document-intelligence-pipeline')?.live_url ?? '/projects', label: 'OCR Demo', code: 'ocr_demo' },
    { href: content.projects.find(p => p.slug === 'llm-assistant')?.live_url ?? '/projects', label: 'Chat Demo', code: 'chat_demo' },
    { href: '/download_cv', label: 'Download CV', code: 'download_cv()' },
  ];
  const path = page === 'home' ? '/' : `/${page}`;
  return <><a className="skip-link" href="#main">Skip to content</a><div className="nav-header-wrapper"><nav className="py-nav" aria-label="Main navigation">
    {[['nav', links.slice(0, 4)], ['demos', links.slice(4, 6)]].map(([name, entries]) => <div className="py-line" key={String(name)}><span className="py-var">{String(name)}</span> <span className="py-operator">=</span> <span className="py-bracket">[</span>{(entries as typeof links).map((link, i) => <span key={link.code}>{i > 0 ? <><span className="py-bracket">,</span>{' '}</> : null}<span className="py-string">"<a href={link.href} className={`py-link${path === link.href ? ' active' : ''}`} aria-label={link.label} aria-current={path === link.href ? 'page' : undefined} target={link.href.startsWith('https:') ? '_blank' : undefined} rel={link.href.startsWith('https:') ? 'noopener noreferrer' : undefined}>{link.code}</a>"</span></span>)}<span className="py-bracket">]</span></div>)}
    <div className="py-line"><span className="py-operator">&gt;&gt;&gt;</span> <a href="/download_cv" className="py-link">download_cv()</a><span className="nav-caret" aria-hidden="true" /></div>
  </nav><div className="py-nav-compact"><label className="nav-label" htmlFor="py-nav-select">Navigation</label><select id="py-nav-select" value={path} onChange={event => { window.location.href = event.target.value; }}>{links.map(link => <option key={link.code} value={link.href}>{link.label}</option>)}</select></div><noscript><nav className="nojs-nav" aria-label="Mobile navigation">{links.slice(0,3).map(link => <a key={link.code} href={link.href}>{link.label}</a>)}</nav></noscript></div>
    <div id="wrapper" className={page === 'projects' ? 'projects-page' : undefined}><main id="main" tabIndex={-1}><div className="inner">{page === 'home' ? <Home content={content} /> : page === 'about' ? <About content={content} /> : <Projects content={content} />}
      {page !== 'projects' ? <section className="cta-section"><div className="cta-banner"><h2>{page === 'home' ? 'See the work behind the systems' : 'Want the full picture?'}</h2><p>{page === 'about' ? 'Explore live demos and production AI projects — or ask the RAG assistant on the front page anything about my background.' : 'Explore architecture and live demos, or ask the CV assistant about the experience behind them.'}</p><div className="cta-actions"><a href="/projects" className="button big">View Projects</a><a href={page === 'home' ? '#cv-chat' : '/#cv-chat'} className="button big alt">Ask my CV</a><a href="/download_cv" className="button big alt">Download CV</a></div></div></section> : null}
    </div></main><footer id="footer"><div className="inner"><section><p>© {content.year} {content.author} • Built with Quart running on Uvicorn.<br /><code>async def build_portfolio():</code></p></section></div></footer></div>
  </>;
}
