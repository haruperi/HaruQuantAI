import { test, expect } from 'vitest';
import { createElement } from 'react';
import { renderToStaticMarkup } from 'react-dom/server';
import { Bootstrap } from '../shell/bootstrap';

test('Bootstrap renders application identity', () => {
  const rendered = renderToStaticMarkup(createElement(Bootstrap));
  expect(rendered).toBe('<main>HaruQuantAI</main>');
});
