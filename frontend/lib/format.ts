/**
 * Presentation helpers lifted from the design files' `hum` / `humVal` /
 * `fmtCost` logic. Pure string/number formatting only — no data shaping.
 */

/** `lease_addresses_issue` -> `Lease addresses issue` */
export function hum(key: string | null | undefined): string {
  if (!key) return '';
  const s = String(key).replace(/_/g, ' ').trim();
  return s.charAt(0).toUpperCase() + s.slice(1);
}

/** `send_reply` -> `Send reply`, `true` -> `Yes`, leaves proper nouns alone. */
export function humVal(value: unknown): string {
  if (value === null || value === undefined) return '';
  const s = String(value);
  if (s === 'true') return 'Yes';
  if (s === 'false') return 'No';
  if (/^[$£€\d]/.test(s) || /[A-Z]/.test(s.charAt(0))) return s;
  const t = s.replace(/_/g, ' ');
  return t.charAt(0).toUpperCase() + t.slice(1);
}

/** `a: 1, b: "x"` -> `A: 1  ·  B: X` */
export function humArgs(text: string | null | undefined): string {
  if (!text) return '';
  return text
    .split(', ')
    .map((pair) => {
      const i = pair.indexOf(':');
      if (i < 0) return pair;
      const k = pair.slice(0, i).trim();
      const v = pair
        .slice(i + 1)
        .trim()
        .replace(/^"|"$/g, '');
      return `${hum(k)}: ${humVal(v)}`;
    })
    .join('  ·  ');
}

export function fmtCost(n: number): string {
  if (!n) return '$0.00';
  return `$${n < 0.001 ? n.toFixed(7).replace(/0+$/, '').replace(/\.$/, '') : n.toFixed(5)}`;
}

export function fmtTokens(n: number): string {
  return n.toLocaleString('en-US');
}

export function fmtElapsed(seconds: number): string {
  if (!seconds) return '0.00s';
  return `${seconds.toFixed(2)}s`;
}

export function fmtClock(iso: string): string {
  const d = new Date(iso);
  if (Number.isNaN(d.getTime())) return '';
  return d.toLocaleTimeString('en-GB', { hour: '2-digit', minute: '2-digit' });
}

const RELATIVE_STEPS: [limit: number, divisor: number, unit: string][] = [
  [60, 1, 'sec'],
  [3600, 60, 'min'],
  [86400, 3600, 'hr'],
];

export function fmtRelative(iso: string | null): string {
  if (!iso) return 'never';
  const then = new Date(iso).getTime();
  if (Number.isNaN(then)) return '';
  const seconds = Math.max(0, Math.round((Date.now() - then) / 1000));
  for (const [limit, divisor, unit] of RELATIVE_STEPS) {
    if (seconds < limit) {
      const value = Math.max(1, Math.floor(seconds / divisor));
      return `${value} ${unit} ago`;
    }
  }
  return `${Math.floor(seconds / 86400)} d ago`;
}

export function initials(name: string): string {
  return name
    .split(/\s+/)
    .filter(Boolean)
    .map((part) => part[0])
    .join('')
    .slice(0, 2)
    .toUpperCase();
}

export function preview(body: string, length = 96): string {
  const flat = body.replace(/\s+/g, ' ').trim();
  return flat.length > length ? `${flat.slice(0, length)}…` : flat;
}
