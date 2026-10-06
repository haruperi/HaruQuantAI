import { useState } from 'react';

export interface RenameValue {
  name?: string;
  prefix?: string;
  postfix?: string;
}

/** Preserve the existing single-name fallback and multi-name trimming. */
export function makeRenameValue(count: number, currentName: string, name: string, prefix: string, postfix: string): RenameValue {
  return count === 1 ? { name: name.trim() || currentName } : { prefix: prefix.trim(), postfix: postfix.trim() };
}

export function useDatabankRenamePopup(count: number, currentName: string, onRename: (value: RenameValue) => void, onClose: () => void) {
  const [name, setName] = useState(currentName);
  const [prefix, setPrefix] = useState('');
  const [postfix, setPostfix] = useState('');
  const confirm = () => {
    onRename(makeRenameValue(count, currentName, name, prefix, postfix));
    onClose();
  };
  return { name, setName, prefix, setPrefix, postfix, setPostfix, confirm };
}
