'use client';

interface CitationBadgeProps {
  citation: string;
  documentId: string | null;
  question?: string | null;
  className?: string;
  onClick?: (e: React.MouseEvent) => void;
}

function citationHref(question: string, documentId: string | null): string | null {
  if (!documentId) return null;
  const base = process.env.NEXT_PUBLIC_LEASECLEAR_BASE_URL;
  return `${base}/demo?q=${encodeURIComponent(question)}&doc=${encodeURIComponent(documentId)}`;
}

export function CitationBadge({
  citation,
  documentId,
  question,
  className,
  onClick,
}: CitationBadgeProps) {
  const label = citation.replace(/^\[|\]$/g, '');
  const href = citationHref(question ?? label, documentId);
  const base =
    'text-ink-50 hover:text-ink inline-flex cursor-pointer items-center gap-1 rounded-[20px] bg-black/[0.055] px-2 py-px text-[11.5px] font-medium whitespace-nowrap hover:bg-black/10';
  const cls = className ? `${base} ${className}` : base;

  return href ? (
    <a
      href={href}
      target="_blank"
      rel="noopener noreferrer"
      className={cls}
      onClick={(e) => {
        e.stopPropagation();
        onClick?.(e);
      }}
    >
      {label}
    </a>
  ) : (
    <span className={cls} onClick={onClick}>
      {label}
    </span>
  );
}
