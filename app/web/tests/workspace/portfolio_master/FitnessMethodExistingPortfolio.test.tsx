import React from 'react';
import { renderToStaticMarkup } from 'react-dom/server';
import { describe, expect, it } from 'vitest';
import { FitnessMethodExistingPortfolio } from '../../../workspaces/portfolio_master/FitnessMethodExistingPortfolio';

describe('FitnessMethodExistingPortfolio Component', () => {
  it('renders ranking criteria table and controls', () => {
    const html = renderToStaticMarkup(
      React.createElement(FitnessMethodExistingPortfolio, {
        criteria: [
          {
            id: '1',
            metricId: 'ReturnDD',
            valueType: 1,
            approximateType: 2,
            weight: 1.0,
            target: 0.0,
          },
        ],
      })
    );
    expect(html).toContain('Ranking Criteria');
    expect(html).toContain('Return / Drawdown ratio');
    expect(html).toContain('Maximize / Minimize');
    expect(html).toContain('disabled');
  });
});
