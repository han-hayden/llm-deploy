import { useEffect, useRef } from 'react';

interface TerminalLogProps {
  content: string;
  maxHeight?: number;
}

export default function TerminalLog({
  content,
  maxHeight = 320,
}: TerminalLogProps) {
  const containerRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (containerRef.current) {
      containerRef.current.scrollTop = containerRef.current.scrollHeight;
    }
  }, [content]);

  return (
    <div
      ref={containerRef}
      style={{
        background: '#1e1e1e',
        color: '#d4d4d4',
        fontFamily:
          "'Cascadia Code', 'Fira Code', 'Consolas', 'Monaco', monospace",
        fontSize: 13,
        lineHeight: 1.6,
        padding: 16,
        borderRadius: 6,
        maxHeight,
        overflowY: 'auto',
        whiteSpace: 'pre-wrap',
        wordBreak: 'break-all',
      }}
    >
      {content || <span style={{ color: '#6A6A6A' }}>等待输出...</span>}
    </div>
  );
}
