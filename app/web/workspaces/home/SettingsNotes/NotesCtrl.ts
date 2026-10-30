import { useRef, useState } from 'react';
import type { Dispatch, RefObject, SetStateAction } from 'react';

/** Retained browser formatting commands, not a persistence/editor engine. */
export const TOOLS: { cmd: string; label: string; title: string }[] = [
  { cmd: 'bold', label: 'B', title: 'Bold' },
  { cmd: 'italic', label: 'I', title: 'Italic' },
  { cmd: 'underline', label: 'U', title: 'Underline' },
  { cmd: 'justifyLeft', label: '⯇', title: 'Align left' },
  { cmd: 'justifyCenter', label: '≡', title: 'Align center' },
  { cmd: 'justifyRight', label: '⯈', title: 'Align right' },
  { cmd: 'indent', label: '→', title: 'Indent more' },
  { cmd: 'outdent', label: '←', title: 'Indent less' },
  { cmd: 'insertHorizontalRule', label: '―', title: 'Horizontal rule' },
  { cmd: 'insertOrderedList', label: '1.', title: 'Ordered list' },
  { cmd: 'insertUnorderedList', label: '•', title: 'Unordered list' },
];

export interface NotesController {
  areaRef: RefObject<HTMLDivElement | null>;
  saved: boolean;
  setSaved: Dispatch<SetStateAction<boolean>>;
  exec: (cmd: string) => void;
  addLink: () => void;
}

export function useNotesController(): NotesController {
  const areaRef = useRef<HTMLDivElement | null>(null);
  const [saved, setSaved] = useState(false);

  const exec = (cmd: string) => {
    areaRef.current?.focus();
    document.execCommand(cmd);
  };

  const addLink = () => {
    const url = window.prompt('Link URL');
    if (url) document.execCommand('createLink', false, url);
  };

  return { areaRef, saved, setSaved, exec, addLink };
}
