import { createSession, lookupSession } from '@/lib/api';
import { SESSION_COOKIE, SESSION_HEADER } from '@/lib/session';
import { NextResponse, type NextRequest } from 'next/server';

const COOKIE_OPTIONS = {
  path: '/',
  sameSite: 'lax' as const,
  // Readable by client fetch helpers; this is a demo nametag, not auth.
  httpOnly: false,
};

function attachSession(request: NextRequest, sessionId: string, setCookie: boolean) {
  const headers = new Headers(request.headers);
  headers.set(SESSION_HEADER, sessionId);
  const response = NextResponse.next({ request: { headers } });
  if (setCookie) {
    response.cookies.set(SESSION_COOKIE, sessionId, COOKIE_OPTIONS);
  }
  return response;
}

export async function middleware(request: NextRequest) {
  const existing = request.cookies.get(SESSION_COOKIE)?.value;
  if (existing) {
    const status = await lookupSession(existing);
    if (status === 'ok' || status === 'error') {
      return attachSession(request, existing, false);
    }
  }

  const sessionId = await createSession();
  if (sessionId === null) {
    return NextResponse.next();
  }
  return attachSession(request, sessionId, true);
}

export const config = {
  matcher: ['/((?!_next/static|_next/image|favicon.ico).*)'],
};
