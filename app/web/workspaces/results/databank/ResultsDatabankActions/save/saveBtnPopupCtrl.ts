import { useState } from 'react';

/** Prefix and suffix remain unused local prototype drafts. */
export function useSaveDraft() {
  const [prefix, setPrefix] = useState('Strategy');
  const [suffix, setSuffix] = useState('');
  return { prefix, setPrefix, suffix, setSuffix };
}
