import React from 'react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import { Components } from 'react-markdown';

interface MarkdownRendererProps {
  content: string;
}

export function MarkdownRenderer({ content }: MarkdownRendererProps) {
  const components: Components = {
    // Custom table styling
    table: ({ children }) => (
      <div className="overflow-x-auto my-4 w-full">
        <table className="min-w-full border-collapse border border-gray-300 dark:border-gray-600">
          {children}
        </table>
      </div>
    ),
    thead: ({ children }) => (
      <thead className="bg-gray-50 dark:bg-gray-800">
        {children}
      </thead>
    ),
    tbody: ({ children }) => (
      <tbody className="bg-white dark:bg-gray-900">
        {children}
      </tbody>
    ),
    tr: ({ children }) => (
      <tr className="border-b border-gray-200 dark:border-gray-700">
        {children}
      </tr>
    ),
    th: ({ children }) => (
      <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider border-r border-gray-300 dark:border-gray-600 last:border-r-0 break-words break-all">
        {children}
      </th>
    ),
    td: ({ children }) => (
      <td className="px-4 py-3 text-sm text-gray-900 dark:text-gray-100 border-r border-gray-200 dark:border-gray-700 last:border-r-0 break-words break-all whitespace-pre-wrap">
        {children}
      </td>
    ),
    
    // Custom heading styling
    h1: ({ children }) => (
      <h1 className="text-2xl font-bold text-gray-900 dark:text-gray-100 mt-6 mb-4 first:mt-0 break-words">
        {children}
      </h1>
    ),
    h2: ({ children }) => (
      <h2 className="text-xl font-bold text-gray-900 dark:text-gray-100 mt-5 mb-3 first:mt-0 break-words">
        {children}
      </h2>
    ),
    h3: ({ children }) => (
      <h3 className="text-lg font-semibold text-gray-900 dark:text-gray-100 mt-4 mb-2 first:mt-0 break-words">
        {children}
      </h3>
    ),
    h4: ({ children }) => (
      <h4 className="text-base font-semibold text-gray-900 dark:text-gray-100 mt-3 mb-2 first:mt-0 break-words">
        {children}
      </h4>
    ),
    
    // Custom paragraph styling
    p: ({ children }) => (
      <p className="text-sm text-gray-700 dark:text-gray-300 mb-3 leading-relaxed break-words break-all whitespace-pre-wrap">
        {children}
      </p>
    ),
    
    // Custom list styling
    ul: ({ children }) => (
      <ul className="list-disc list-inside text-sm text-gray-700 dark:text-gray-300 mb-3 space-y-1">
        {children}
      </ul>
    ),
    ol: ({ children }) => (
      <ol className="list-decimal list-inside text-sm text-gray-700 dark:text-gray-300 mb-3 space-y-1">
        {children}
      </ol>
    ),
    li: ({ children }) => (
      <li className="ml-2">
        {children}
      </li>
    ),
    
    // Custom emphasis styling
    strong: ({ children }) => (
      <strong className="font-semibold text-gray-900 dark:text-gray-100">
        {children}
      </strong>
    ),
    em: ({ children }) => (
      <em className="italic text-gray-800 dark:text-gray-200">
        {children}
      </em>
    ),
    
    // Custom code styling
    code: ({ children, className }) => {
      const isInline = !className;
      if (isInline) {
        return (
          <code className="bg-gray-100 dark:bg-gray-800 text-gray-800 dark:text-gray-200 px-1.5 py-0.5 rounded text-xs font-mono">
            {children}
          </code>
        );
      }
      return (
        <code className="block bg-gray-100 dark:bg-gray-800 text-gray-800 dark:text-gray-200 p-3 rounded-lg text-xs font-mono overflow-x-auto whitespace-pre break-words">
          {children}
        </code>
      );
    },
    
    // Custom blockquote styling
    blockquote: ({ children }) => (
      <blockquote className="border-l-4 border-blue-500 pl-4 py-2 my-4 bg-blue-50 dark:bg-blue-900/20 text-gray-700 dark:text-gray-300 italic">
        {children}
      </blockquote>
    ),
    
    // Custom horizontal rule
    hr: () => (
      <hr className="border-gray-300 dark:border-gray-600 my-6" />
    ),
    
    // Handle images (including base64)
    img: ({ src, alt }) => {
      if (src?.startsWith('data:image')) {
        return (
          <div className="w-full my-4">
            <img 
              src={src} 
              alt={alt || "Visualization"} 
              className="max-w-full h-auto rounded-lg border border-gray-200 dark:border-gray-700"
              style={{ maxHeight: '400px' }}
            />
          </div>
        );
      }
      return (
        <img 
          src={src} 
          alt={alt || ""} 
          className="max-w-full h-auto rounded-lg border border-gray-200 dark:border-gray-700 my-4"
        />
      );
    },
  };

  return (
    <div className="markdown-content max-w-none break-words">
      <ReactMarkdown 
        components={components}
        remarkPlugins={[remarkGfm]}
      >
        {content}
      </ReactMarkdown>
    </div>
  );
}