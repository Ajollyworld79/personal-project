import ReactMarkdown from 'react-markdown';

export default function Markdown({ text }: { text: string }): React.JSX.Element {
  // Raw HTML is deliberately disabled; React escapes all model/user text.
  return <ReactMarkdown skipHtml components={{ a: ({ children, href }) => <a href={href} target="_blank" rel="noopener noreferrer">{children}</a> }}>{text}</ReactMarkdown>;
}
