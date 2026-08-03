import './globals.css';
import { Sidebar } from '@/components/sidebar';
import { getBuildInfo, listApprovals } from '@/lib/api';
import type { Metadata } from 'next';
import { Inter, JetBrains_Mono } from 'next/font/google';

const inter = Inter({
  subsets: ['latin'],
  weight: ['400', '500', '600', '700'],
  variable: '--font-inter',
});

const jetbrainsMono = JetBrains_Mono({
  subsets: ['latin'],
  weight: ['400', '500', '600'],
  variable: '--font-jetbrains-mono',
});

export const metadata: Metadata = {
  title: 'LeaseOps',
  description: 'Agent triage for tenant email',
};

// The shell is data-driven too (pending badge), so it must not be cached either.
export const dynamic = 'force-dynamic';

export default async function RootLayout({ children }: { children: React.ReactNode }) {
  // The sidebar badge is the one piece of data the shell owns. It is loaded
  // here rather than in each page so no page has to know about it.
  const approvals = await listApprovals().catch(() => ({ items: [] }));

  return (
    <html lang="en" className={`${inter.variable} ${jetbrainsMono.variable}`}>
      <body className="text-ink font-sans antialiased">
        <div className="bg-page flex h-screen w-full overflow-hidden">
          <Sidebar pendingCount={approvals.items.length} buildInfo={getBuildInfo()} />
          <main className="flex min-w-0 flex-1 flex-col overflow-hidden">{children}</main>
        </div>
      </body>
    </html>
  );
}
