import type { Content } from '../types';
import { githubSchema } from '../types';
import { useResource } from '../lib/api';
import { ProjectCard } from '../components/ProjectCard';
import { Chat } from '../components/Chat';
import { ColdFile, GitHubActivity, ProductionStatus } from '../components/Live';
import { TokenBackground, Skills } from '../components/OriginalDecor';

export function Home({ content }: { content: Content }): React.JSX.Element {
  const github = useResource('/api/github-activity', githubSchema);
  return <>
    <header className="major" role="banner"><TokenBackground /><div className="container hero"><div className="hero-left"><div className="hero-eyebrow">python · llm · production systems</div><h1>Gustav <span className="accent">Christensen</span><span className="dot">.</span><br /><span className="dim">Production AI engineer</span></h1><p className="lead">I build autonomous LLM workflows, RAG systems, and data pipelines that run in production. Python at the core. Based in Denmark.</p><ul className="actions hero-actions"><li><a href="/projects" className="button big">$ view production systems</a></li><li><a href="#cv-chat" className="button big alt">&gt;&gt;&gt; ask my cv</a></li></ul><p className="hero-tertiary"><a href="/download_cv">download cv.pdf ↓</a></p></div><div className="hero-right"><Chat /><p className="subtle" style={{ marginTop: '.75rem', textAlign: 'center' }}>// live RAG: fastembed → qdrant → gemini · watch the trace</p></div></div></header>
    <section className="stats-strip reveal revealed">{[['20','+','years_in_it'],['5','','systems_in_production'],['20','+','technologies'],[github.status === 'ready' ? String(Math.floor(github.data.total/50)*50) : '—',github.status === 'ready' ? '+' : '','commits_last_year']].map(([number,suffix,label]) => <div className="stat-item" key={label}><span className="stat-number">{number}</span><span className="stat-suffix">{suffix}</span><span className="stat-label">{label}</span></div>)}</section>
    <ProductionStatus /><Skills />
    <section className="reveal revealed"><header className="major"><h2>Featured Projects</h2></header><div className="posts duo">{content.projects.filter(p => ['the-cold-file','llm-assistant'].includes(p.slug)).map(project => <ProjectCard key={project.slug} project={project} featured />)}</div><p className="subtle" style={{ marginTop: 'var(--s-5)' }}><a href="/projects">See all projects →</a></p></section>
    <ColdFile /><GitHubActivity resource={github} />
  </>;
}
