import type { Content } from '../types';
import { Portrait } from '../components/Portrait';
const technologies: Record<string, string[]> = {
  'Data Engineer': ['Python','SQL','ETL','AI/LLM','Azure'],
  'IT Operations Specialist': ['SCOM','Orchestrator','Windows Server','SLA'],
  'IT Support Specialist': ['Support','Troubleshooting'],
};
export function About({ content }: { content: Content }): React.JSX.Element {
  const { cv } = content;
  return <section className="cv section" aria-labelledby="about-heading">
    <header className="cv__header"><div className="cv__head"><Portrait name={content.author} /><div className="cv__head-text"><p className="cv__eyebrow">gustav.about()</p><h1 id="about-heading" className="cv__title">{content.author}</h1><p className="cv__lede">{cv.headline}</p><ul className="actions cv__actions"><li><a href="/download_cv" className="button">$ download cv.pdf</a></li><li><a href="/#cv-chat" className="button alt">&gt;&gt;&gt; ask my cv</a></li></ul></div></div></header>
    <div className="cards"><article className="card"><h2>Contact</h2><address className="card__contact"><span>Email: <a href={`mailto:${cv.contact.email}`}>{cv.contact.email}</a></span><span>LinkedIn: <a href={`https://www.linkedin.com/in/${cv.contact.linkedin}`} target="_blank" rel="noopener noreferrer">gustav-wind-christensen</a></span><span>GitHub: <a href={`https://github.com/${cv.contact.github}`} target="_blank" rel="noopener noreferrer">@{cv.contact.github}</a></span><span>Location: {cv.contact.location}</span></address></article><article className="card"><h2>Top Skills</h2><ul>{cv.skills.map(skill => <li key={skill}>{skill}</li>)}</ul></article><article className="card"><h2>Languages</h2><ul>{cv.languages.map(language => <li key={language}>{language}</li>)}</ul></article></div>
    <hr className="separator" aria-hidden="true" /><h2>Summary</h2><p>{cv.summary}</p>
    <hr className="separator" aria-hidden="true" /><h2>Experience</h2><ol className="timeline" role="list">{cv.roles.map(role => <li className="timeline-item" key={role.role}><p className="timeline-date">{role.date}</p><div className="timeline-content"><h3 className="timeline-role">{role.role}</h3><p className="timeline-company">{role.company}</p><p>{role.summary}</p>{role.points.length ? <ul className="timeline-points">{role.points.map(point => <li key={point}>{point}</li>)}</ul> : null}<ul className="timeline-tech" aria-label="Technologies">{technologies[role.role]?.map(tech => <li key={tech}><span className="tech-badge">{tech}</span></li>)}</ul></div></li>)}</ol>
    <h3>Previous Roles</h3><ol className="timeline timeline-compact" role="list">{cv.previous_roles.map(role => {
      const [company,...rest] = role.text.split(' — ');
      return <li className="timeline-item" key={role.date}><p className="timeline-date">{role.date}</p><div className="timeline-content"><strong>{company}</strong> — {rest.join(' — ')}</div></li>;
    })}</ol>
    <hr className="separator" aria-hidden="true" /><h2>Certifications</h2><div className="cert-grid">{cv.certifications.map(cert => <article className="cert-card" key={cert.name}><span className="cert-abbr" aria-hidden="true">{cert.issuer.startsWith('Python') ? 'PCEP' : 'MCPS'}</span><p className="cert-name">{cert.url ? <a href={cert.url} target="_blank" rel="noopener noreferrer">{cert.name}</a> : cert.name}<span className="cert-issuer">{cert.issuer}</span></p></article>)}</div>
    <hr className="separator" aria-hidden="true" /><h2>Education &amp; Courses</h2><ul className="plain">{cv.education.map(item => {
      const year=item.match(/ (\d{4}(?:–\d{4})?)$/)?.[1];
      const title=year ? item.slice(0,-year.length-1) : item;
      return <li key={item}>{cv.education_links[item] ? <a href={cv.education_links[item]} target="_blank" rel="noopener noreferrer">{title}</a> : title}{year ? <> <span className="year">{year}</span></> : null}</li>;
    })}</ul><hr className="separator" aria-hidden="true" />
  </section>;
}
