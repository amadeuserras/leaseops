import { SESSION_COOKIE, SESSION_HEADER } from '@/lib/session';
import { NextResponse, type NextRequest } from 'next/server';

const API_BASE = process.env.NEXT_PUBLIC_API_BASE_URL ?? 'http://localhost:8000';

export async function middleware(request: NextRequest) {
  const existing = request.cookies.get(SESSION_COOKIE)?.value;
  if (existing) {
    const headers = new Headers(request.headers);
    headers.set(SESSION_HEADER, existing);
    return NextResponse.next({ request: { headers } });
  }

  const created = await fetch(`${API_BASE}/sessions`, { method: 'POST' });
  if (!created.ok) {
    return NextResponse.next();
  }

  const body = (await created.json()) as { id: string };
  const headers = new Headers(request.headers);
  headers.set(SESSION_HEADER, body.id);

  const response = NextResponse.next({ request: { headers } });
  response.cookies.set(SESSION_COOKIE, body.id, {
    path: '/',
    sameSite: 'lax',
    // Readable by client fetch helpers; this is a demo nametag, not auth.
    httpOnly: false,
  });
  return response;
}

export const config = {
  matcher: ['/((?!_next/static|_next/image|favicon.ico).*)'],
};
