export class NotesPreview {
  static from_text(note_text: string | null, empty_label: string = 'Empty'): string {
    const text = note_text === null ? empty_label : note_text;
    const maxLength = 32;
    return text.length > maxLength ? text.slice(0, maxLength) + '...' : text;
  }
}
