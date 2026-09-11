import type { Content } from '../types';
import { ProjectCard } from '../components/ProjectCard';
export function Projects({ content }: { content: Content }): React.JSX.Element {
  return <section className="section"><header className="major"><p className="cv__eyebrow">gustav.projects()</p><h1>Projects</h1><p className="lead">Systems I have built and shipped — from autonomous LLM workflows and RAG to document intelligence and data pipelines.</p></header><div className="projects-grid">{content.projects.map(project => <ProjectCard key={project.slug} project={project} />)}</div></section>;
}
