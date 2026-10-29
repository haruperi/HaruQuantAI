import { test, expect } from 'vitest';
import { NotesPreview } from '../../../workspaces/home/notesPreview';

test('notes null and empty', () => {
  expect(NotesPreview.from_text(null)).toBe('Empty');
  expect(NotesPreview.from_text(null, 'Vacant')).toBe('Vacant');
  expect(NotesPreview.from_text('')).toBe('');
});

test('notes 32 code-unit boundary', () => {
  expect(NotesPreview.from_text('x'.repeat(32))).toBe('x'.repeat(32));
  expect(NotesPreview.from_text('x'.repeat(33))).toBe('x'.repeat(32) + '...');
});

test('notes retains donor UTF16 slicing', () => {
  const input = 'a'.repeat(31) + '\ud83d\ude00';
  expect(NotesPreview.from_text(input)).toBe('a'.repeat(31) + '\ud83d...');
});
