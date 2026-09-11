import { useState } from 'react';
import type { Project } from '../types';
import { apologySchema } from '../types';
import { getJson } from '../lib/api';
import { Dialog } from './Dialog';
import { RepoIcon, LockIcon, PlayIcon } from './OriginalIcons';

export function ProjectCard({ project, featured = false }: { project: Project; featured?: boolean }): React.JSX.Element {
  const [dialog,setDialog]=useState<'diagram'|'apology'|null>(null);
  const [apology,setApology]=useState<{apology:string;meta:string}|null>(null);
  const [busy,setBusy]=useState(false);
  const [error,setError]=useState('');
  const [summary='',details='']=project.description.split('<!--more-->');
  const image=project.image ? '/static/'+project.image : null;
  async function generateApology(): Promise<void> {
    if(busy) return;
    setBusy(true);setError('');
    try {setApology(await getJson('/api/get-apology',apologySchema));setDialog('apology');}
    catch {setError('Could not load the demo. Please try again.');}
    finally {setBusy(false);}
  }
  const more=details ? <details className="project-more"><summary>Read more</summary><div className="project-more-body" dangerouslySetInnerHTML={{__html:details}} /></details> : null;
  return <><article className={featured ? 'featured project-visible' : 'project-card project-visible'} id={project.slug}>
    {image ? image.endsWith('.svg') ? <button type="button" className="project-thumb thumb-zoom" aria-label={`Enlarge architecture diagram: ${project.title}`} onClick={()=>setDialog('diagram')}><img src={image} alt={`${project.title} — architecture diagram`} loading="lazy" /><span className="thumb-hint">⤢ view diagram</span></button> : <a className={featured ? 'featured-thumb' : 'project-thumb thumb-link'} href={project.live_url ?? project.repo_url ?? '#'+project.slug} target="_blank" rel="noopener noreferrer" aria-label={`Open ${project.title}`}><img src={image} alt={`${project.title} — preview`} loading="lazy" />{!featured ? <span className="thumb-hint">{project.live_url ? '↗ open live demo' : '↗ view on github'}</span> : null}</a> : null}
    {featured ? <h3>{project.title}</h3> : <div className="project-header"><div className="project-icon"><svg viewBox="0 0 24 24" fill="none" aria-hidden="true"><path d="M12 2L2 7L12 12L22 7L12 2ZM2 17L12 22L22 17M2 12L12 17L22 12" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" /></svg></div><h2 className="project-title">{project.title.includes('RAG') ? <>{project.title.replace(' with RAG','')}<span className="rag-badge">RAG</span></> : project.title}</h2></div>}
    {featured ? <><p dangerouslySetInnerHTML={{__html:summary}} />{more}</> : <div className="project-description"><p dangerouslySetInnerHTML={{__html:summary}} />{more}</div>}
    {featured ? <p className="tech-tags">{project.technologies.map(tech=><span key={tech}><span className="tech-badge">{tech}</span>{' '}</span>)}</p> : <div className="project-tech">{project.technologies.map(tech=><span key={tech} className="tech-badge">{tech}</span>)}</div>}
    <div className="project-actions">{project.repo_url ? <a href={project.repo_url} target="_blank" rel="noopener noreferrer" className={featured ? 'button' : 'button project-btn'}>{!featured ? <RepoIcon /> : null}View Code</a> : !featured ? <span className="button project-btn-alt is-disabled" aria-disabled="true" title="Private repository — contact guch79@gmail.com"><LockIcon />Private repo</span> : null}
      {project.slug === 'apology-service' ? <button className="button project-btn-alt" onClick={()=>void generateApology()} disabled={busy}><PlayIcon />{busy ? 'Generating…' : 'Generate Live Apology'}</button> : project.live_url ? <a className={featured ? 'button primary' : 'button project-btn-alt'} href={project.live_url} target="_blank" rel="noopener noreferrer">{featured ? 'Demo' : 'Live Demo'}</a> : null}
    </div>{error ? <p className="error" role="alert">{error}</p> : null}
  </article>
  {dialog === 'diagram' && image ? <Dialog title={`${project.title} · architecture`} wide onClose={()=>setDialog(null)}><img className="dialog-diagram" src={image} alt={`${project.title} architecture diagram`} /></Dialog> : null}
  {dialog === 'apology' && apology ? <Dialog title="Apology-as-a-Service" onClose={()=>setDialog(null)}><div className="dialog-body"><p className="apology-text">{apology.apology}</p><p className="subtle">{apology.meta}</p></div></Dialog> : null}
  </>;
}
