'use client';

/**
 * New-workspace template picker (FEAT-UI-01, FR-UI-195/196/198).
 *
 * Rendered by `WorkspaceGrid` as the whole content of a workspace that is
 * still pending its template choice. Mirrors the CME Group Simulator's
 * "NEW WORKSPACE / Select a template or begin from scratch" screen: one
 * labeled card per registered template, each card applying that template to
 * the active workspace.
 *
 * Card thumbnails are miniature renderings of the template's own widget grid
 * - tiny panels with header pills and per-type content glyphs (candles for
 * charts, depth bars for ladders, zebra rows for tables) - matching how the
 * CME picker previews each template with a screenshot of the real layout.
 * All glyph patterns below are fixed arrays so thumbnails are deterministic.
 */
import React from 'react';

import { useTradingStore } from '../../store/useTradingStore';
import { useWorkspaceStore } from './store';
import { WORKSPACE_TEMPLATES, type WorkspaceTemplate } from './templates';

const TEMPLATE_IMAGES: Record<string, { dark: string; light: string }> = {
  haruquant: {
    dark: '/templates/HaruQuant_Workspace-Dark.png',
    light: '/templates/HaruQuant_Workspace-Light.png',
  },
  'chart-ladder': {
    dark: '/templates/Chart_Ladder-Dark.png',
    light: '/templates/Chart_Ladder-Light.png',
  },
  'multicharts-ladder': {
    dark: '/templates/MultiCharts_Ladder-Dark.png',
    light: '/templates/MultiCharts_Ladder-Light.png',
  },
  options: {
    dark: '/templates/Options_Dark.png',
    light: '/templates/Options_Light.png',
  },
  charts: {
    dark: '/templates/Charts_Dark.png',
    light: '/templates/Charts_Light.png',
  },
};

const TemplateThumbnail: React.FC<{ template: WorkspaceTemplate }> = ({ template }) => {
  const theme = useTradingStore((state) => state.theme) || 'dark';
  const imgConfig = TEMPLATE_IMAGES[template.id];

  if (!imgConfig || template.widgets.length === 0) {
    return <div className="workspace-template-thumb is-blank" aria-hidden="true" />;
  }

  const src = theme === 'light' ? imgConfig.light : imgConfig.dark;

  return (
    <div className="workspace-template-thumb" aria-hidden="true">
      <img
        src={src}
        alt={`${template.name} preview`}
        className="workspace-template-thumb-img"
        loading="lazy"
      />
    </div>
  );
};

export const TemplatePicker: React.FC = () => {
  const applyWorkspaceTemplate = useWorkspaceStore((state) => state.applyWorkspaceTemplate);

  return (
    <main className="workspace-template-picker" aria-labelledby="workspace-template-heading">
      <h3 id="workspace-template-heading" className="workspace-template-heading">
        NEW WORKSPACE
      </h3>
      <p className="workspace-template-subtitle">Select a template or begin from scratch</p>
      <div className="workspace-template-cards">
        {WORKSPACE_TEMPLATES.map((template) => (
          <button
            key={template.id}
            type="button"
            className="workspace-template-card"
            aria-label={`Create workspace from the ${template.name} template`}
            onClick={() => applyWorkspaceTemplate(template.id)}
          >
            <span className="workspace-template-card-label">{template.name}</span>
            <TemplateThumbnail template={template} />
          </button>
        ))}
      </div>
    </main>
  );
};
