import type { Metadata } from 'next';
import './globals.css';
import { AuthProvider } from '@/context';

export const metadata: Metadata = {
  title: 'HaruQuantAI | Trading Simulator',
  description: 'Real-time HaruQuantAI & algorithmic trading simulation, analytics, and strategy governance platform.',
  icons: {
    icon: 'data:image/svg+xml,<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100"><text y=".9em" font-size="90">📈</text></svg>',
  },
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <head>
        <link rel="preconnect" href="https://fonts.googleapis.com" />
        <link rel="preconnect" href="https://fonts.gstatic.com" crossOrigin="anonymous" />
        <link
          href="https://fonts.googleapis.com/css2?family=Be+Vietnam+Pro:wght@400;500;600;700&family=Roboto+Mono:wght@400;500;600&display=swap"
          rel="stylesheet"
        />
      </head>
      <body>
        <div id="root">
          <AuthProvider>{children}</AuthProvider>
        </div>
      </body>
    </html>
  );
}
