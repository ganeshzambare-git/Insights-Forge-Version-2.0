import './globals.css';
import { Suspense } from 'react';
import { Inter, Fraunces } from 'next/font/google';
import { SessionLifecycleProvider } from '../features/authentication/components/SessionLifecycleProvider';
import { ConnectivityProvider } from '../features/connectivity/components/ConnectivityProvider';

const inter = Inter({
  subsets: ['latin'],
  variable: '--font-inter',
  display: 'swap',
});

const fraunces = Fraunces({
  subsets: ['latin'],
  variable: '--font-fraunces',
  display: 'swap',
});

export const metadata = {
  title: 'Insight Forge',
  description: 'Educational Decision Intelligence Platform',
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" className={`${inter.variable} ${fraunces.variable}`}>
      <body>
        <Suspense
          fallback={
            <div style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', minHeight: '100vh', color: 'var(--muted)' }}>
              Loading workspace…
            </div>
          }
        >
          <ConnectivityProvider>
            <SessionLifecycleProvider>
              {children}
            </SessionLifecycleProvider>
          </ConnectivityProvider>
        </Suspense>
      </body>
    </html>
  );
}
