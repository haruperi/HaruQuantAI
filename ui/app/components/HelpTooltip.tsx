import React, { useEffect, useId, useRef, useState } from 'react';

export interface HelpTutorialItem {
  id: string;
  test_id?: string;
  title: string;
  summary: string;
  steps?: string[];
}

export interface HelpGuidePayload {
  topic: string;
  title: string;
  summary: string;
  available_topics?: string[];
  tutorials: HelpTutorialItem[];
}

export interface HelpTooltipProps {
  title?: string;
  summary?: string;
  topic?: string;
  availableTopics?: string[];
  tutorials?: HelpTutorialItem[];
  guide?: HelpGuidePayload | null;
  defaultActiveTutorialId?: string | null;
  initialError?: string | null;
  loadGuide?: (topic: string) => Promise<HelpGuidePayload>;
  defaultOpen?: boolean;
  testId?: string;
  panelTestId?: string;
}

export function resolveActiveTutorial(
  tutorials: readonly HelpTutorialItem[],
  activeTutorialId: string | null,
): HelpTutorialItem | null {
  return (
    tutorials.find((item) => item.id === activeTutorialId) ??
    tutorials[0] ??
    null
  );
}

export const HelpTooltip: React.FC<HelpTooltipProps> = ({
  title = 'Contextual Help',
  summary = 'Select a topic or tutorial to view step-by-step guidance.',
  topic = 'overview',
  availableTopics = [],
  tutorials = [],
  guide: externalGuide = null,
  defaultActiveTutorialId = null,
  initialError = null,
  loadGuide,
  defaultOpen = false,
  testId = 'help-tooltip-trigger',
  panelTestId = 'help-tooltip-panel',
}) => {
  const [open, setOpen] = useState<boolean>(defaultOpen);
  const [selectedTopic, setSelectedTopic] = useState<string>(topic);
  const [guide, setGuide] = useState<HelpGuidePayload | null>(externalGuide);
  const [activeTutorialId, setActiveTutorialId] = useState<string | null>(
    defaultActiveTutorialId,
  );
  const [loading, setLoading] = useState<boolean>(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(initialError);
  const containerRef = useRef<HTMLDivElement | null>(null);
  const dialogId = useId();

  useEffect(() => {
    setSelectedTopic(topic);
  }, [topic]);

  useEffect(() => {
    if (!open || !loadGuide) return;
    let cancelled = false;
    setLoading(true);
    setErrorMessage(null);
    void loadGuide(selectedTopic)
      .then((payload) => {
        if (cancelled) return;
        setGuide(payload);
        if (payload.tutorials.length > 0 && !activeTutorialId) {
          setActiveTutorialId(payload.tutorials[0].id);
        }
      })
      .catch((err: unknown) => {
        if (cancelled) return;
        setErrorMessage(err instanceof Error ? err.message : 'Unable to load contextual help.');
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });
    return () => {
      cancelled = true;
    };
  }, [open, selectedTopic, loadGuide]);

  useEffect(() => {
    if (!open) return;
    const onKeyDown = (event: KeyboardEvent) => {
      if (event.key === 'Escape') {
        setOpen(false);
      }
    };
    const onMouseDown = (event: MouseEvent) => {
      if (
        containerRef.current &&
        event.target instanceof Node &&
        !containerRef.current.contains(event.target)
      ) {
        setOpen(false);
      }
    };
    window.addEventListener('keydown', onKeyDown);
    window.addEventListener('mousedown', onMouseDown);
    return () => {
      window.removeEventListener('keydown', onKeyDown);
      window.removeEventListener('mousedown', onMouseDown);
    };
  }, [open]);

  const effectiveGuide = guide ?? externalGuide;
  const effectiveTitle = effectiveGuide?.title ?? title;
  const effectiveSummary = effectiveGuide?.summary ?? summary;
  const effectiveTopics = effectiveGuide?.available_topics ?? availableTopics;
  const effectiveTutorials = effectiveGuide?.tutorials ?? tutorials;
  const activeTutorial = resolveActiveTutorial(effectiveTutorials, activeTutorialId);

  return (
    <div ref={containerRef} style={{ position: 'relative', display: 'inline-flex' }}>
      <button
        type="button"
        data-testid={testId}
        aria-label={effectiveTitle}
        aria-expanded={open}
        aria-controls={open ? dialogId : undefined}
        onClick={() => setOpen((prev) => !prev)}
        style={{
          display: 'inline-flex',
          alignItems: 'center',
          gap: '4px',
          padding: '4px 10px',
          borderRadius: '4px',
          border: '1px solid #334155',
          background: open ? '#1d4ed8' : '#1e293b',
          color: '#f8fafc',
          fontSize: '12px',
          fontWeight: 600,
          cursor: 'pointer',
        }}
      >
        <span aria-hidden="true">?</span>
        <span>Help</span>
      </button>

      {open ? (
        <div
          id={dialogId}
          role="dialog"
          aria-label={effectiveTitle}
          data-testid={panelTestId}
          style={{
            position: 'absolute',
            top: 'calc(100% + 6px)',
            right: 0,
            width: '380px',
            maxWidth: '90vw',
            zIndex: 50,
            padding: '12px',
            borderRadius: '6px',
            border: '1px solid #334155',
            background: '#0f172a',
            color: '#e2e8f0',
            boxShadow: '0 10px 25px rgba(0, 0, 0, 0.45)',
          }}
        >
          <div
            style={{
              display: 'flex',
              justifyContent: 'space-between',
              alignItems: 'center',
              gap: '8px',
              marginBottom: '6px',
            }}
          >
            <strong style={{ fontSize: '13px', color: '#f8fafc' }}>{effectiveTitle}</strong>
            <button
              type="button"
              data-testid="help-tooltip-close"
              aria-label="Close help"
              onClick={() => setOpen(false)}
              style={{
                border: '1px solid #334155',
                borderRadius: '4px',
                background: '#1e293b',
                color: '#cbd5e1',
                fontSize: '11px',
                padding: '2px 6px',
                cursor: 'pointer',
              }}
            >
              Close
            </button>
          </div>

          <p style={{ margin: '0 0 10px', fontSize: '12px', color: '#94a3b8' }}>
            {effectiveSummary}
          </p>

          {effectiveTopics.length > 0 ? (
            <div style={{ marginBottom: '10px' }}>
              <label
                htmlFor={`${dialogId}-topic`}
                style={{ display: 'block', fontSize: '11px', color: '#94a3b8', marginBottom: '4px' }}
              >
                Topic
              </label>
              <select
                id={`${dialogId}-topic`}
                data-testid="help-topic-select"
                value={selectedTopic}
                onChange={(e) => setSelectedTopic(e.target.value)}
                style={{
                  width: '100%',
                  padding: '4px 6px',
                  borderRadius: '4px',
                  border: '1px solid #334155',
                  background: '#1e293b',
                  color: '#f8fafc',
                  fontSize: '12px',
                }}
              >
                {effectiveTopics.map((topicKey) => (
                  <option key={topicKey} value={topicKey}>
                    {topicKey}
                  </option>
                ))}
              </select>
            </div>
          ) : null}

          {loading ? (
            <div data-testid="help-tooltip-loading" style={{ fontSize: '12px', color: '#94a3b8' }}>
              Loading guidance...
            </div>
          ) : null}

          {errorMessage ? (
            <div
              role="alert"
              data-testid="help-tooltip-error"
              style={{ fontSize: '12px', color: '#fca5a5', marginBottom: '8px' }}
            >
              {errorMessage}
            </div>
          ) : null}

          {effectiveTutorials.length > 0 ? (
            <div style={{ display: 'grid', gap: '6px' }}>
              <div style={{ fontSize: '11px', fontWeight: 600, color: '#cbd5e1' }}>
                Tutorials & Guides
              </div>
              {effectiveTutorials.map((item) => {
                const isSelected = activeTutorial?.id === item.id;
                return (
                  <div
                    key={item.id}
                    style={{
                      padding: '8px',
                      borderRadius: '4px',
                      border: isSelected ? '1px solid #3b82f6' : '1px solid #1e293b',
                      background: '#111827',
                    }}
                  >
                    <div
                      style={{
                        display: 'flex',
                        justifyContent: 'space-between',
                        alignItems: 'center',
                        gap: '8px',
                      }}
                    >
                      <span style={{ fontSize: '12px', fontWeight: 600, color: '#f8fafc' }}>
                        {item.title}
                      </span>
                      <button
                        type="button"
                        data-testid={item.test_id ?? `help-tutorial-btn-${item.id}`}
                        onClick={() => setActiveTutorialId(item.id)}
                        style={{
                          border: '1px solid #2563eb',
                          borderRadius: '4px',
                          background: isSelected ? '#2563eb' : '#1e293b',
                          color: '#f8fafc',
                          fontSize: '11px',
                          padding: '2px 8px',
                          cursor: 'pointer',
                          whiteSpace: 'nowrap',
                        }}
                      >
                        Read tutorial
                      </button>
                    </div>
                    <div style={{ fontSize: '11px', color: '#94a3b8', marginTop: '4px' }}>
                      {item.summary}
                    </div>
                    {isSelected && item.steps && item.steps.length > 0 ? (
                      <ol
                        data-testid={`help-tutorial-steps-${item.id}`}
                        style={{
                          margin: '6px 0 0',
                          paddingLeft: '18px',
                          fontSize: '11px',
                          color: '#cbd5e1',
                        }}
                      >
                        {item.steps.map((step, index) => (
                          <li key={index}>{step}</li>
                        ))}
                      </ol>
                    ) : null}
                  </div>
                );
              })}
            </div>
          ) : null}
        </div>
      ) : null}
    </div>
  );
};

export default HelpTooltip;
