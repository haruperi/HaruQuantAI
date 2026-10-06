import { selectMockStrategies } from '../DatabankSelectService';

export const label = 'Passed';
/** Bind the existing Passed action to the shared mock selection adapter. */
export const selectPassedStrategies = (
  ...args: [Parameters<typeof selectMockStrategies>[0], Parameters<typeof selectMockStrategies>[2], Parameters<typeof selectMockStrategies>[3]]
): void => selectMockStrategies(args[0], true, args[1], args[2]);
