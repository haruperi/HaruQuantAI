import type { ReactElement } from 'react';
import { createRoot } from 'react-dom/client';

export function Bootstrap(): ReactElement {
  return <main>HaruQuantAI</main>;
}

if (typeof document !== 'undefined') {
  const rootElement = document.getElementById('root');
  if (rootElement) {
    createRoot(rootElement).render(<Bootstrap />);
  }
}
