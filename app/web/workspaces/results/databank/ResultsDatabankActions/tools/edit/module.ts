import { label as parameters, requestEditParameters } from './editParameters/module';
import { label as strategy, requestEditStrategy } from './editStrategy/module';

export const EDIT_MENU = { label: 'Edit', children: [parameters, strategy] };
export function handleEditItem(item: string, deferred: (label: string) => void): boolean {
  if (item === 'Edit:Parameters') requestEditParameters(deferred);
  else if (item === 'Edit:Strategy') requestEditStrategy(deferred);
  else return false;
  return true;
}
