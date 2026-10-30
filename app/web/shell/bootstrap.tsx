import React from 'react';
import { createRoot } from 'react-dom/client';
import { BrowserRouter } from 'react-router-dom';
import { App } from './App';
import './styles.css';
import 'dockview/dist/styles/dockview.css';

export function Bootstrap(): React.ReactElement {
  return (
    <React.StrictMode>
      <BrowserRouter>
        <App />
      </BrowserRouter>
    </React.StrictMode>
  );
}

if (typeof document !== 'undefined') {
  const rootElement = document.getElementById('root');
  if (rootElement) createRoot(rootElement).render(<Bootstrap />);
}
