import { describe, expect, it } from 'vitest';
import { ServletBuilder } from '../../../workspaces/builder/ServletBuilder';

describe('ServletBuilder', () => {
  it('exports ServletBuilder component properly', () => {
    expect(ServletBuilder).toBeDefined();
    expect(typeof ServletBuilder).toBe('function');
  });
});
