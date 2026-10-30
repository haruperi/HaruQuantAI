import { label as passedLabel, selectPassedStrategies } from './passed/module';
import { label as failedLabel, selectFailedStrategies } from './failed/module';

export const SELECT_MENU = { label: 'Select', children: [passedLabel, failedLabel] };
export { strategyPassesMockChecks } from './DatabankSelectService';

export function handleSelectItem(
  item: string,
  ...args: Parameters<typeof selectPassedStrategies>
): boolean {
  if (item === 'Select:Passed') selectPassedStrategies(...args);
  else if (item === 'Select:Failed') selectFailedStrategies(...args);
  else return false;
  return true;
}
