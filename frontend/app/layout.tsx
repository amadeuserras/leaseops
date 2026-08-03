import './globals.css';
import { Sidebar } from '@/components/sidebar';
import { AppProvider } from '@/context/app-context';
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

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en" className={`${inter.variable} ${jetbrainsMono.variable}`}>
      <body className="text-ink font-sans antialiased">
        <AppProvider>
          <div className="bg-page flex h-screen w-full overflow-hidden">
            <Sidebar />
            <main className="flex min-w-0 flex-1 flex-col overflow-hidden">{children}</main>
          </div>
        </AppProvider>
      </body>
    </html>
  );
}
