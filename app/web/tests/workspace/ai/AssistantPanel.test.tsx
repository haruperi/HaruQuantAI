import { renderToString } from 'react-dom/server';
import { describe, expect, it } from 'vitest';
import { AIAssistantWorkspace } from '../../../workspaces/ai/AIAssistantWorkspace';

describe('AssistantPanel & AIAssistantWorkspace (Phase 19.2: I-ServletSQAI)', () => {
  it('renders AI assistant workspace with navigation and conversation layout', () => {
    const html = renderToString(<AIAssistantWorkspace />);

    // Renders new chat and sidebar items
    expect(html).toContain('New chat');
    expect(html).toContain('Brain');
    expect(html).toContain('Search chats');
  });

  it('renders capability starter tiles and prompts', () => {
    const html = renderToString(<AIAssistantWorkspace />);

    // Shipped capability tiles from catalog.ts
    expect(html).toContain('What would you like to do?');
    expect(html).toContain('Text to Strategy');
    expect(html).toContain('Build &amp; Automate Workflows');
  });

  it('renders chat message composer and input actions', () => {
    const html = renderToString(<AIAssistantWorkspace />);

    // Composer textarea and action triggers
    expect(html).toContain('Type a message, or / for commands...');
    expect(html).toContain('Add files');
    expect(html).toContain('Send');
  });
});
