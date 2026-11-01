import { renderToString } from 'react-dom/server';
import { describe, expect, it, vi } from 'vitest';
import { NotesTab } from '../../../workspaces/home/SettingsNotes/notes';
import { executeSaveNotes } from '../../../workspaces/home/SettingsNotes/NotesCtrl';
import type { homeClient } from '../../../workspaces/home/homeClient';

describe('NotesTab rendering and controller integration', () => {
  it('renders NotesTab without demo indicator when project is provided', () => {
    const html = renderToString(<NotesTab projectId="test-project" initialNotes="Project notes content" />);
    expect(html).toContain('Save');
    expect(html).not.toContain('Saved (demo)');
    expect(html).toContain('sqd-notes-toolbar');
  });

  it('saves notes via API and updates revision', async () => {
    const mockSaveNotes = vi.fn().mockResolvedValue({
      status: 'saved',
      notes: 'Sample content',
      revision: 4,
    });
    const client = {
      saveNotes: mockSaveNotes,
    } as unknown as ReturnType<typeof homeClient>;

    const result = await executeSaveNotes('test-proj', 'Sample content', 3, client);

    expect(mockSaveNotes).toHaveBeenCalledWith('test-proj', 'Sample content', 3);
    expect(result.revision).toBe(4);
    expect(result.saveState).toBe('saved');
    expect(result.error).toBeNull();
  });

  it('handles 409 conflict correctly', async () => {
    const mockSaveNotes = vi.fn().mockRejectedValue(new Error('HTTP 409: Revision conflict'));
    const client = {
      saveNotes: mockSaveNotes,
    } as unknown as ReturnType<typeof homeClient>;

    const result = await executeSaveNotes('test-proj', 'Concurrent edit', 1, client);

    expect(result.saveState).toBe('conflict');
    expect(result.error).toContain('Revision conflict');
    expect(result.revision).toBe(1);
  });

  it('rejects save when no project is bound', async () => {
    const result = await executeSaveNotes(undefined, 'Local draft', 0);
    expect(result.saveState).toBe('error');
    expect(result.error).toContain('Cannot save notes: No active project is loaded');
  });

  it('renders disabled Save button when no project is loaded', () => {
    const html = renderToString(<NotesTab projectId="" initialNotes="Local draft" />);
    expect(html).toContain('disabled');
    expect(html).toContain('Cannot save notes: No active project is loaded');
  });
});
