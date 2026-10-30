/** Native SQX 145 assistant presentation with ephemeral drafts and gated services. */
import { useEffect, useRef, useState, type ReactNode } from "react";
import {
  ArrowLeft,
  ArrowUp,
  BookOpen,
  BrainCircuit,
  ChartNoAxesCombined,
  ChevronRight,
  Code2,
  FileText,
  Folder,
  HelpCircle,
  Menu,
  MessageSquare,
  Monitor,
  MoreHorizontal,
  Paperclip,
  Package,
  Pin,
  Plus,
  Puzzle,
  Search,
  Trash2,
  WandSparkles,
  X,
  type LucideIcon,
} from "lucide-react";
import {
  brainSections,
  capabilities,
  serviceUnavailable,
  type Capability,
} from "./catalog";
import "./AIAssistant.css";

interface DraftSession {
  id: number;
  name: string;
  capabilityId: string | null;
  draft: string;
  files: File[];
  pinned: boolean;
  project: string;
}

const icons: Record<string, LucideIcon> = {
  wand: WandSparkles,
  chart: ChartNoAxesCombined,
  monitor: Monitor,
  code: Code2,
  book: BookOpen,
  puzzle: Puzzle,
  chat: MessageSquare,
  package: Package,
  "/SQAI/algocloud.png": ChartNoAxesCombined,
  "/SQAI/sqx.png": BookOpen,
};

function newSession(id: number): DraftSession {
  return {
    id,
    name: `New chat${id > 1 ? ` ${id}` : ""}`,
    capabilityId: null,
    draft: "",
    files: [],
    pinned: false,
    project: "",
  };
}

function AssistantDialog({
  title,
  children,
  onClose,
}: {
  title: string;
  children: ReactNode;
  onClose: () => void;
}) {
  const dialog = useRef<HTMLDialogElement>(null);
  useEffect(() => {
    const opener = document.activeElement;
    const element = dialog.current;
    element?.showModal();
    return () => {
      element?.close();
      if (opener instanceof HTMLElement && opener.isConnected) opener.focus();
    };
  }, []);
  return (
    <dialog
      ref={dialog}
      className="ai-dialog"
      aria-label={title}
      onCancel={onClose}
    >
      <header>
        <h2>{title}</h2>
        <button type="button" aria-label={`Close ${title}`} onClick={onClose}>
          <X />
        </button>
      </header>
      {children}
    </dialog>
  );
}

export function AIAssistantWorkspace() {
  const [sessions, setSessions] = useState<DraftSession[]>([newSession(1)]);
  const [activeId, setActiveId] = useState(1);
  const nextId = useRef(2);
  const [railOpen, setRailOpen] = useState(false);
  const [filter, setFilter] = useState("");
  const [projects, setProjects] = useState<string[]>([]);
  const [menuOpen, setMenuOpen] = useState(false);
  const [panel, setPanel] = useState<
    "brain" | "usage" | "help" | "rename" | "project" | "close" | "clear" | null
  >(null);
  const [dialogValue, setDialogValue] = useState("");
  const [brainTab, setBrainTab] =
    useState<(typeof brainSections)[number]["name"]>("Memory");
  const [view, setView] = useState<"Conversation" | "Reports" | "Files">(
    "Conversation",
  );
  const [notice, setNotice] = useState("");
  const [dragging, setDragging] = useState(false);
  const fileInput = useRef<HTMLInputElement>(null);
  const composer = useRef<HTMLTextAreaElement>(null);
  const session = sessions.find((item) => item.id === activeId)!;
  const capability = capabilities.find(
    (item) => item.id === session.capabilityId,
  );
  const BrainIcon = icons[capability?.icon ?? "chat"] ?? BrainCircuit;

  function patchSession(patch: Partial<DraftSession>) {
    setSessions((current) =>
      current.map((item) =>
        item.id === activeId ? { ...item, ...patch } : item,
      ),
    );
  }

  function selectSession(id: number) {
    setActiveId(id);
    setView("Conversation");
    setNotice("");
    setMenuOpen(false);
    setRailOpen(false);
  }

  function addSession(project = "") {
    const id = nextId.current++;
    setSessions((current) => [...current, { ...newSession(id), project }]);
    selectSession(id);
  }

  function selectCapability(item: Capability) {
    patchSession({
      capabilityId: item.id,
      name: session.name.startsWith("New chat") ? item.title : session.name,
    });
    setView("Conversation");
    setNotice("");
    composer.current?.focus();
  }

  function addFiles(files: File[]) {
    if (!files.length) return;
    // File references are local only; no reads, uploads, object URLs or persistence.
    setSessions((current) =>
      current.map((item) =>
        item.id === activeId
          ? { ...item, files: [...item.files, ...files] }
          : item,
      ),
    );
    setNotice("Files selected locally. Uploads require the assistant service.");
  }

  function closeSession() {
    const remaining = sessions.filter((item) => item.id !== activeId);
    if (remaining.length) {
      setSessions(remaining);
      selectSession(remaining[0].id);
    } else {
      const id = nextId.current++;
      setSessions([newSession(id)]);
      selectSession(id);
    }
    setPanel(null);
  }

  function clearDraft() {
    patchSession({ draft: "", files: [], capabilityId: null });
    setPanel(null);
    setNotice("Local draft cleared.");
  }

  function chooseStarter(starter: Capability["starters"][number]) {
    if (starter.action) {
      setNotice("Loading a strategy requires the assistant service.");
      return;
    }
    patchSession({ draft: starter.prompt ?? starter.label });
    composer.current?.focus();
  }

  function command(commandName: "help" | "clear") {
    if (commandName === "help") {
      setPanel("help");
    } else {
      setPanel("clear");
    }
  }

  function sessionRows(items: DraftSession[]) {
    return items
      .filter((item) => item.name.toLowerCase().includes(filter.toLowerCase()))
      .map((item) => (
        <button
          type="button"
          className={`ai-session-row ${item.id === activeId ? "selected" : ""}`}
          key={item.id}
          aria-label={`Open ${item.name}`}
          aria-current={item.id === activeId ? "page" : undefined}
          onClick={() => selectSession(item.id)}
        >
          {item.pinned ? <Pin /> : <MessageSquare />}
          <span>{item.name}</span>
        </button>
      ));
  }

  return (
    <section className="ai-workspace" aria-label="AI Assistant workspace">
      <header className="ai-header">
        <button
          type="button"
          className="ai-icon"
          aria-label="Conversations"
          aria-expanded={railOpen}
          onClick={() => setRailOpen(!railOpen)}
        >
          <Menu />
        </button>
        <div className="ai-brand">
          <BrainCircuit />
          <div>
            <strong>AI Assistant</strong>
            <span>Your trading co-worker</span>
          </div>
        </div>
        <span className="ai-context">
          <MessageSquare />
          {session.name}
          {session.project && ` · ${session.project}`}
        </span>
        <div className="ai-header-actions">
          <button
            type="button"
            className="ai-pill"
            onClick={() => setPanel("usage")}
            aria-label="View Usage & Credits"
          >
            <i /> <span>Credits unavailable</span>
          </button>
          <button
            type="button"
            className="ai-pill"
            onClick={() => setPanel("brain")}
          >
            <BrainCircuit />
            Brain
          </button>
          <button
            type="button"
            className="ai-icon"
            aria-label="Assistant guide"
            onClick={() => setPanel("help")}
          >
            <HelpCircle />
          </button>
        </div>
      </header>
      <div className="ai-body">
        {railOpen && (
          <button
            type="button"
            className="ai-rail-backdrop"
            aria-label="Hide conversations"
            onClick={() => setRailOpen(false)}
          />
        )}
        <aside
          className={`ai-conversations ${railOpen ? "open" : ""}`}
          aria-label="Assistant conversations"
        >
          <button
            type="button"
            className="ai-new-chat"
            onClick={() => addSession()}
          >
            <Plus />
            New chat
          </button>
          <label className="ai-search">
            <Search />
            <input
              aria-label="Search chats"
              placeholder="Search chats"
              value={filter}
              onChange={(event) => setFilter(event.target.value)}
            />
          </label>
          <div className="ai-conversation-list">
            <h3>Pinned</h3>
            {sessionRows(sessions.filter((item) => item.pinned))}
            {!sessions.some((item) => item.pinned) && (
              <p className="ai-rail-empty">No pinned chats</p>
            )}
            <div className="ai-rail-heading">
              <h3>Projects</h3>
              <button
                type="button"
                className="ai-icon"
                aria-label="New project"
                onClick={() => {
                  setDialogValue("");
                  setPanel("project");
                }}
              >
                <Plus />
              </button>
            </div>
            {!projects.length && (
              <p className="ai-rail-empty">Group your conversations</p>
            )}
            {projects.map((project) => (
              <div key={project} className="ai-project">
                <button
                  type="button"
                  aria-label={`New chat in ${project}`}
                  onClick={() => addSession(project)}
                >
                  <Folder />
                  {project}
                  <Plus />
                </button>
                {sessionRows(
                  sessions.filter(
                    (item) => item.project === project && !item.pinned,
                  ),
                )}
              </div>
            ))}
            <h3>Chats</h3>
            {sessionRows(
              sessions.filter((item) => !item.pinned && !item.project),
            )}
          </div>
          <div className="ai-rail-footer">
            <span className="ai-status-dot" /> Local drafts
            <span>Unsaved · this visit only</span>
          </div>
        </aside>
        <div className="ai-chat-area">
          <div className="ai-session-bar">
            <div
              className="ai-session-tabs"
              role="tablist"
              aria-label="Draft sessions"
            >
              {sessions.map((item) => (
                <button
                  type="button"
                  role="tab"
                  id={`ai-session-${item.id}`}
                  aria-controls="ai-session-content"
                  aria-selected={item.id === activeId}
                  tabIndex={item.id === activeId ? 0 : -1}
                  key={item.id}
                  onKeyDown={(event) => {
                    if (event.key !== "ArrowRight" && event.key !== "ArrowLeft")
                      return;
                    event.preventDefault();
                    const index = sessions.findIndex(
                      (value) => value.id === item.id,
                    );
                    const next =
                      sessions[
                        (index +
                          (event.key === "ArrowRight" ? 1 : -1) +
                          sessions.length) %
                          sessions.length
                      ];
                    selectSession(next.id);
                    document.getElementById(`ai-session-${next.id}`)?.focus();
                  }}
                  onClick={() => selectSession(item.id)}
                >
                  <MessageSquare />
                  <span>{item.name}</span>
                </button>
              ))}
            </div>
            <button
              type="button"
              className="ai-icon"
              aria-label="New session"
              onClick={() => addSession()}
            >
              <Plus />
            </button>
            <div className="ai-session-menu">
              <button
                type="button"
                className="ai-icon"
                aria-label="Session actions"
                aria-expanded={menuOpen}
                onClick={() => setMenuOpen(!menuOpen)}
              >
                <MoreHorizontal />
              </button>
              {menuOpen && (
                <div className="ai-menu">
                  <button
                    type="button"
                    onClick={() => {
                      setDialogValue(session.name);
                      setPanel("rename");
                      setMenuOpen(false);
                    }}
                  >
                    Rename session
                  </button>
                  <button
                    type="button"
                    onClick={() => {
                      patchSession({ pinned: !session.pinned });
                      setMenuOpen(false);
                    }}
                  >
                    {session.pinned ? "Unpin" : "Pin"}
                  </button>
                  <label>
                    Move to
                    <select
                      aria-label="Move chat to project"
                      value={session.project}
                      onChange={(event) => {
                        patchSession({ project: event.target.value });
                        setMenuOpen(false);
                      }}
                    >
                      <option value="">Chats</option>
                      {projects.map((project) => (
                        <option key={project}>{project}</option>
                      ))}
                    </select>
                  </label>
                  <button
                    type="button"
                    onClick={() => {
                      setPanel("clear");
                      setMenuOpen(false);
                    }}
                  >
                    Clear chat
                  </button>
                  <button
                    type="button"
                    onClick={() => {
                      setPanel("close");
                      setMenuOpen(false);
                    }}
                  >
                    Close session
                  </button>
                </div>
              )}
            </div>
          </div>
          <div
            id="ai-session-content"
            className="ai-session-content"
            role="tabpanel"
            aria-labelledby={`ai-session-${activeId}`}
          >
            <div className="ai-view-tabs" aria-label="Session views">
              {(["Conversation", "Reports", "Files"] as const).map((name) => (
                <button
                  type="button"
                  key={name}
                  aria-pressed={view === name}
                  onClick={() => setView(name)}
                >
                  {name}
                  {name === "Files" && session.files.length > 0
                    ? ` (${session.files.length})`
                    : ""}
                </button>
              ))}
            </div>
            <div className="ai-chat-scroll">
              {view === "Reports" ? (
                <div className="ai-empty">
                  <FileText />
                  <h2>No reports available</h2>
                  <p>
                    Reports will appear here when the assistant service is
                    connected.
                  </p>
                </div>
              ) : view === "Files" ? (
                <div className="ai-file-view">
                  <h2>Files in this draft</h2>
                  <p>Selected files remain local and have not been uploaded.</p>
                  {session.files.length ? (
                    session.files.map((file, index) => (
                      <div
                        className="ai-file-row"
                        key={`${file.name}-${index}`}
                      >
                        <FileText />
                        <span>
                          {file.name}
                          <small>{file.size.toLocaleString()} bytes</small>
                        </span>
                        <button
                          type="button"
                          className="ai-icon"
                          aria-label={`Remove ${file.name}`}
                          onClick={() =>
                            patchSession({
                              files: session.files.filter(
                                (_, position) => position !== index,
                              ),
                            })
                          }
                        >
                          <X />
                        </button>
                      </div>
                    ))
                  ) : (
                    <p>No files selected.</p>
                  )}
                </div>
              ) : capability ? (
                <div className="ai-capability-detail">
                  <button
                    type="button"
                    className="ai-back"
                    onClick={() => patchSession({ capabilityId: null })}
                  >
                    <ArrowLeft />
                    All capabilities
                  </button>
                  <div className="ai-detail-icon">
                    <BrainIcon />
                  </div>
                  <h1>{capability.title}</h1>
                  <p>{capability.description}</p>
                  <h3>Try one of these</h3>
                  <div className="ai-starters">
                    {capability.starters.map((starter) => (
                      <button
                        type="button"
                        key={starter.key}
                        onClick={() => chooseStarter(starter)}
                      >
                        <span>→</span>
                        {starter.label}
                      </button>
                    ))}
                  </div>
                </div>
              ) : (
                <div className="ai-home">
                  <div className="ai-home-intro">
                    <BrainCircuit />
                    <h1>What would you like to do?</h1>
                    <p>Select a task to begin, or describe your idea below.</p>
                  </div>
                  <div className="ai-capability-grid">
                    {capabilities.map((item) => {
                      const Icon = icons[item.icon] ?? BrainCircuit;
                      return (
                        <button
                          type="button"
                          className="ai-capability-card"
                          key={item.id}
                          onClick={() => selectCapability(item)}
                        >
                          <Icon />
                          <div>
                            <h2>{item.title}</h2>
                            <p>{item.shortDescription}</p>
                          </div>
                          <ChevronRight className="ai-card-arrow" />
                        </button>
                      );
                    })}
                  </div>
                  <button
                    type="button"
                    className="ai-guide-link"
                    onClick={() => setPanel("help")}
                  >
                    <BookOpen />
                    Quick introduction to AI
                  </button>
                </div>
              )}
            </div>
            <div className="ai-compose-section">
              <p className="ai-service-notice">
                <span className="ai-status-dot" />
                {serviceUnavailable}
              </p>
              {notice && (
                <p className="ai-action-notice" role="status">
                  {notice}
                </p>
              )}
              <div
                className={`ai-composer ${dragging ? "dragging" : ""}`}
                onDragOver={(event) => {
                  event.preventDefault();
                  setDragging(true);
                }}
                onDragLeave={(event) => {
                  if (
                    !event.currentTarget.contains(
                      event.relatedTarget as Node | null,
                    )
                  )
                    setDragging(false);
                }}
                onDrop={(event) => {
                  event.preventDefault();
                  setDragging(false);
                  addFiles(Array.from(event.dataTransfer.files));
                }}
              >
                {dragging && (
                  <div className="ai-drop-hint">
                    Drop files to add them to this draft
                  </div>
                )}
                {session.files.length > 0 && (
                  <div className="ai-attachments">
                    {session.files.map((file, index) => (
                      <span key={`${file.name}-${index}`}>
                        <Paperclip />
                        <span>{file.name}</span>
                        <button
                          type="button"
                          aria-label={`Remove attachment ${file.name}`}
                          onClick={() =>
                            patchSession({
                              files: session.files.filter(
                                (_, position) => position !== index,
                              ),
                            })
                          }
                        >
                          <X />
                        </button>
                      </span>
                    ))}
                  </div>
                )}
                <textarea
                  ref={composer}
                  aria-label="Message"
                  placeholder={
                    capability?.inputPlaceholder ??
                    "Type a message, or / for commands..."
                  }
                  value={session.draft}
                  onChange={(event) =>
                    patchSession({ draft: event.target.value })
                  }
                  onPaste={(event) => {
                    if (event.clipboardData.files.length) {
                      event.preventDefault();
                      addFiles(Array.from(event.clipboardData.files));
                    }
                  }}
                  onKeyDown={(event) => {
                    if (
                      event.key === "Enter" &&
                      !event.shiftKey &&
                      !event.nativeEvent.isComposing
                    ) {
                      event.preventDefault();
                      if (session.draft.trim() === "/help") command("help");
                      else if (session.draft.trim() === "/clear")
                        command("clear");
                      else
                        setNotice(
                          "Sending requires the assistant service. Your draft has been kept.",
                        );
                    }
                  }}
                />
                {session.draft.startsWith("/") && (
                  <div className="ai-commands" aria-label="Commands">
                    <span>Commands</span>
                    <button type="button" onClick={() => command("help")}>
                      /help <small>Show workspace help</small>
                    </button>
                    <button type="button" onClick={() => command("clear")}>
                      /clear <small>Clear this local draft</small>
                    </button>
                  </div>
                )}
                <div className="ai-composer-actions">
                  <button
                    type="button"
                    className="ai-icon"
                    aria-label="Add files"
                    title="Add files — paste or drag & drop also works"
                    onClick={() => fileInput.current?.click()}
                  >
                    <Paperclip />
                  </button>
                  <input
                    ref={fileInput}
                    type="file"
                    multiple
                    hidden
                    aria-label="Choose attachments"
                    onChange={(event) => {
                      addFiles(Array.from(event.target.files ?? []));
                      event.target.value = "";
                    }}
                  />
                  <label className="ai-model">
                    Model
                    <select aria-label="Model" disabled>
                      <option>No models available</option>
                    </select>
                  </label>
                  <button
                    type="button"
                    className="ai-send"
                    aria-label="Send"
                    disabled
                    title="Assistant service unavailable"
                  >
                    <ArrowUp />
                  </button>
                </div>
              </div>
              <p className="ai-footnote">
                AI can make mistakes. Review generated content before use.
              </p>
            </div>
          </div>
        </div>
      </div>
      {panel && (
        <AssistantDialog
          title={
            panel === "brain"
              ? "AI Brain"
              : panel === "usage"
                ? "Usage & Credits"
                : panel === "help"
                  ? "Assistant guide"
                  : panel === "rename"
                    ? "Rename session"
                    : panel === "project"
                      ? "New project"
                      : panel === "close"
                        ? "Close this session?"
                        : "Clear this chat?"
          }
          onClose={() => setPanel(null)}
        >
          {panel === "brain" ? (
            <>
              <p>
                What the assistant remembers, knows and learns between
                conversations.
              </p>
              <div className="ai-brain-layout">
                <nav aria-label="Brain sections">
                  {brainSections.map((section) => (
                    <button
                      type="button"
                      key={section.name}
                      aria-pressed={brainTab === section.name}
                      onClick={() => setBrainTab(section.name)}
                    >
                      <Folder />
                      {section.name}
                    </button>
                  ))}
                </nav>
                <div>
                  {brainSections
                    .filter((section) => section.name === brainTab)
                    .map((section) => (
                      <div key={section.name}>
                        <h3>{section.name}</h3>
                        <code>{section.path}</code>
                        <p>{section.description}</p>
                      </div>
                    ))}
                  <p className="ai-unavailable">
                    Workspace service unavailable. No memory or skill files have
                    been loaded.
                  </p>
                  <textarea
                    aria-label="Brain file editor"
                    disabled
                    placeholder="Connect the workspace service to read and edit files."
                  />
                  <div className="ai-brain-actions">
                    <button type="button" disabled>
                      Save
                    </button>
                    {brainTab === "Skills" && (
                      <>
                        <button type="button" disabled>
                          Promote
                        </button>
                        <button type="button" disabled>
                          Discard
                        </button>
                      </>
                    )}
                  </div>
                </div>
              </div>
            </>
          ) : panel === "usage" ? (
            <>
              <p>
                AI credits and model usage require a connected assistant
                provider.
              </p>
              <div className="ai-usage-summary">
                <span>
                  Credits available<strong>Unavailable</strong>
                </span>
                <span>
                  Usage history<strong>Unavailable</strong>
                </span>
              </div>
              <button type="button" disabled>
                Add credits
              </button>
            </>
          ) : panel === "help" ? (
            <>
              <p>
                Choose a capability to see its conversation starters. Starters
                populate your draft so you can refine your request.
              </p>
              <p>
                Create sessions and projects to organize drafts. Pin or rename
                sessions from Session actions. Drafts and selected files last
                only while this workspace stays open.
              </p>
              <p>
                Attach files with the paperclip, paste them, or drag them into
                the composer. Use Shift+Enter for a new line. Type /help or
                /clear for local commands.
              </p>
              <p>
                The assistant service is unavailable. Sending, models, credits,
                reports, strategy actions, and Brain file editing become
                available after backend integration.
              </p>
            </>
          ) : panel === "close" || panel === "clear" ? (
            <>
              <p>
                {panel === "close"
                  ? "This removes the local session and its draft attachments."
                  : "This clears the local draft, selected capability and attachments."}{" "}
                No server data is affected.
              </p>
              <div className="ai-dialog-actions">
                <button type="button" onClick={() => setPanel(null)}>
                  Keep it
                </button>
                <button
                  type="button"
                  className="ai-danger"
                  onClick={panel === "close" ? closeSession : clearDraft}
                >
                  <Trash2 />
                  {panel === "close" ? "Close draft" : "Clear draft"}
                </button>
              </div>
            </>
          ) : (
            <form
              onSubmit={(event) => {
                event.preventDefault();
                const value = dialogValue.trim();
                if (!value) return;
                if (panel === "rename") patchSession({ name: value });
                else if (projects.includes(value)) {
                  return;
                } else setProjects((current) => [...current, value]);
                setPanel(null);
              }}
            >
              <label className="ai-name-field">
                Name
                <input
                  autoFocus
                  aria-label="Name"
                  maxLength={80}
                  value={dialogValue}
                  onChange={(event) => setDialogValue(event.target.value)}
                />
              </label>
              {panel === "project" && projects.includes(dialogValue.trim()) && (
                <p role="alert">A project with this name already exists.</p>
              )}
              <div className="ai-dialog-actions">
                <button type="button" onClick={() => setPanel(null)}>
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={
                    !dialogValue.trim() ||
                    (panel === "project" &&
                      projects.includes(dialogValue.trim()))
                  }
                >
                  Save locally
                </button>
              </div>
            </form>
          )}
        </AssistantDialog>
      )}
    </section>
  );
}
