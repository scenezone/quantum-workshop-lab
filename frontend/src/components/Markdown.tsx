import ReactMarkdown from 'react-markdown';
import remarkMath from 'remark-math';
import remarkGfm from 'remark-gfm';
import remarkBreaks from 'remark-breaks';
import rehypeKatex from 'rehype-katex';
import 'katex/dist/katex.min.css';

export default function Markdown({ children }: { children: string }) {
  // LLMs commonly emit LaTeX delimiters instead of Markdown math delimiters.
  // Preserve code examples while normalizing only prose.
  const content = children.split(/(```[\s\S]*?```|`[^`]*`)/g).map((part) => part.startsWith('`') ? part : part
    .replace(/\\\[([\s\S]+?)\\\]/g, (_, math: string) => `\n$$\n${math}\n$$\n`)
    .replace(/\\\(([\s\S]+?)\\\)/g, (_, math: string) => `$${math}$`)).join('');
  return <div className="markdown-content"><ReactMarkdown
    remarkPlugins={[remarkMath, remarkGfm, remarkBreaks]}
    rehypePlugins={[rehypeKatex]}
    components={{
      table: ({ children }) => <div className="markdown-table-scroll" role="region" aria-label="Scrollable table" tabIndex={0}>
        <table>{children}</table>
      </div>,
      pre: ({ children }) => <pre tabIndex={0} aria-label="Code example">{children}</pre>,
    }}
  >{content}</ReactMarkdown></div>;
}
