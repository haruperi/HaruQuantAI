import { selectMockStrategies } from '../DatabankSelectService';

export const label = 'Failed';
/** Bind the existing Failed action to the shared mock selection adapter. */
export const selectFailedStrategies = (
  ...args: [Parameters<typeof selectMockStrategies>[0], Parameters<typeof selectMockStrategies>[2], Parameters<typeof selectMockStrategies>[3]]
): void => selectMockStrategies(args[0], false, args[1], args[2]);
