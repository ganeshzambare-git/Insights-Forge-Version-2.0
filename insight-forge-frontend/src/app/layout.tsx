import './globals.css';
import { Suspense } from 'react';
import { SessionLifecycleProvider } from '../features/authentication/components/SessionLifecycleProvider';
import { ConnectivityProvider } from '../features/connectivity/components/ConnectivityProvider';

export const metadata = {
  title: 'InsightForge AI',
  description: 'Enterprise Decision Intelligence Platform',
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body className="bg-slate-950 text-slate-100 min-h-screen">
        <Suspense fallback={<div style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', minHeight: '100vh', color: '#64748b' }}>Loading context...</div>}>
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
