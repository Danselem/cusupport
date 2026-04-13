import { RootLayout } from '@/components/root-layout';

interface RootLayoutProps {
  children: React.ReactNode;
}

export default async function Layout({ children }: RootLayoutProps) {
  return (
    <RootLayout className="bg-background">
      <header className="fixed top-0 left-0 z-50 hidden w-full flex-row justify-between p-6 md:flex">
        <a
          target="_blank"
          rel="noopener noreferrer"
          href="https://alphaproxima.co"
          className="flex items-center gap-2 scale-100 transition-transform duration-300 hover:scale-105"
        >
          <span className="text-lg font-bold tracking-tight text-[#6366f1]">Alpha</span>
          <span className="text-lg font-bold tracking-tight">Proxima</span>
        </a>
        <span className="text-foreground font-mono text-xs font-bold tracking-wider uppercase">
          Powered by{' '}
          <a
            target="_blank"
            rel="noopener noreferrer"
            href="https://docs.livekit.io/agents"
            className="underline underline-offset-4"
          >
            LiveKit
          </a>
        </span>
      </header>
      {children}
      <footer className="fixed bottom-0 left-0 flex w-full justify-center p-6">
        <p className="text-fg1 w-full max-w-prose pt-1 text-center text-xs leading-5 font-normal text-pretty md:text-sm">
          Powered by{' '}
          <a
            target="_blank"
            rel="noopener noreferrer"
            href="https://alphaproxima.co"
            className="underline"
          >
            Alpha Proxima
          </a>
          {' '} & LiveKit
        </p>
      </footer>
    </RootLayout>
  );
}
