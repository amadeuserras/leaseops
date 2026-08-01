const TIME_FORMAT = new Intl.DateTimeFormat('en-GB', { hour: '2-digit', minute: '2-digit' });
const DATE_FORMAT = new Intl.DateTimeFormat('en-GB', { day: '2-digit', month: 'short' });

const isToday = (date: Date): boolean => {
  const now = new Date();
  return (
    date.getFullYear() === now.getFullYear() &&
    date.getMonth() === now.getMonth() &&
    date.getDate() === now.getDate()
  );
};

export const formatReceived = (iso: string): string => {
  const date = new Date(iso);
  return isToday(date) ? TIME_FORMAT.format(date) : DATE_FORMAT.format(date);
};

export const formatDateTime = (iso: string): string => {
  const date = new Date(iso);
  return `${DATE_FORMAT.format(date)} ${TIME_FORMAT.format(date)}`;
};

export const formatRelativeTime = (iso: string): string => {
  const minutes = Math.max(0, Math.round((Date.now() - new Date(iso).getTime()) / 60_000));
  if (minutes < 1) return 'just now';
  if (minutes < 60) return `${minutes} min ago`;
  const hours = Math.round(minutes / 60);
  if (hours < 24) return `${hours} hr ago`;
  return formatDateTime(iso);
};

export const formatTokens = (tokens: number): string => tokens.toLocaleString('en-US');

export const formatCost = (usd: number): string => {
  if (usd === 0) return '$0.00';
  if (usd < 0.001) return `$${usd.toFixed(7).replace(/0+$/, '').replace(/\.$/, '')}`;
  return `$${usd.toFixed(5)}`;
};

export const formatDuration = (ms: number): string => `${(ms / 1000).toFixed(2)}s`;

export const initialsOf = (name: string): string =>
  name
    .split(/\s+/)
    .map((part) => part[0] ?? '')
    .join('')
    .slice(0, 2)
    .toUpperCase();

export const shortId = (id: string): string => id.replaceAll('-', '').slice(0, 8);

export const previewOf = (body: string, limit = 120): string => {
  const flat = body.replace(/\s+/g, ' ').trim();
  return flat.length > limit ? `${flat.slice(0, limit)}…` : flat;
};

export const nameFromAddress = (address: string): string =>
  address
    .split('@')[0]
    .split(/[._-]+/)
    .filter(Boolean)
    .map((part) => part[0].toUpperCase() + part.slice(1))
    .join(' ');

export const splitCitations = (answer: string): { text: string; citations: string[] } => {
  const citations: string[] = [];
  const text = answer.replace(/\s*\[([^\]]+)\]/g, (_match: string, citation: string) => {
    if (!citations.includes(citation)) citations.push(citation);
    return '';
  });
  return { text: text.replace(/\s+([.,;])/g, '$1').trim(), citations };
};

export const humanize = (value: string): string => value.replaceAll('_', ' ');
