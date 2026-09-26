import { useRef, useState } from "react";
import { AWConfirm, AWField, AWModal } from "./AlgoWizardControls";
import { AlgoWizardBlockEditor } from "./AlgoWizardBlockEditor";
import { downloadText, uid, uniqueName } from "./algoWizardModel";
export interface Resource {
  id: string;
  name: string;
  kind: string;
  category: string;
  content: string[];
}
export function AlgoWizardResources({
  kind,
  resources,
  onChange,
  onClose,
  onKind,
}: {
  kind: string;
  resources: Resource[];
  onChange: (r: Resource[]) => void;
  onClose: () => void;
  onKind: (kind: string) => void;
}) {
  const [selection, setSelection] = useState<string | null>(null);
  const [search, setSearch] = useState("");
  const [form, setForm] = useState<Resource | null>(null);
  const [editing, setEditing] = useState<number | "new" | null>(null);
  const [remove, setRemove] = useState(false);
  const [error, setError] = useState("");
  const file = useRef<HTMLInputElement>(null);
  const items = resources.filter((r) => r.kind === kind);
  const current = items.find((r) => r.id === selection);
  const change = (r: Resource) =>
    onChange(resources.map((x) => (x.id === r.id ? r : x)));
  return (
    <div className="aw-resource-page">
      <div className="aw-resource-header">
        <button className="aw-old" onClick={onClose}>
          ‹ Back to editor
        </button>
        <h2>{kind}</h2>
        <span className="aw-spacer" />
        <a
          href="https://help.algowizard.io/index.html"
          target="_blank"
          rel="noreferrer"
        >
          Help
        </a>
      </div>
      <nav className="aw-settings-tabs">
        {["Random groups", "Custom blocks"].map((k) => (
          <button
            key={k}
            className={kind === k ? "active" : ""}
            onClick={() => {
              onKind(k);
              setSelection(null);
            }}
          >
            {k}
          </button>
        ))}
      </nav>
      <div className="aw-resource-tools">
        <button
          className="aw-old"
          onClick={() =>
            setForm({
              id: uid(),
              name: "",
              kind,
              category: "My blocks",
              content: [],
            })
          }
        >
          Create new
        </button>
        <button className="aw-old" onClick={() => file.current?.click()}>
          Load from file
        </button>
        <button
          className="aw-old"
          onClick={() =>
            downloadText(
              "algowizard-resources.json",
              JSON.stringify(
                {
                  format: "haruquantai.algowizard.resources",
                  version: 1,
                  items,
                },
                null,
                2,
              ),
            )
          }
        >
          Save to file
        </button>
        <button
          className="aw-old"
          disabled={!current}
          onClick={() => current && setForm({ ...current })}
        >
          Rename
        </button>
        <button
          className="aw-old"
          disabled={!current}
          onClick={() => {
            if (current) {
              const r = {
                ...structuredClone(current),
                id: uid(),
                name: uniqueName(
                  current.name,
                  items.map((x) => x.name),
                ),
              };
              onChange([...resources, r]);
              setSelection(r.id);
            }
          }}
        >
          Duplicate
        </button>
        <button
          className="aw-old"
          disabled={!current}
          onClick={() => setRemove(true)}
        >
          Delete
        </button>
        <input
          aria-label="Search resources"
          placeholder="Search..."
          value={search}
          onChange={(e) => setSearch(e.target.value)}
        />
      </div>
      <input
        type="file"
        accept=".json"
        hidden
        ref={file}
        onChange={async (e) => {
          const selectedFile = e.target.files?.[0];
          e.target.value = "";
          if (!selectedFile) return;
          try {
            const data = JSON.parse(await selectedFile.text());
            if (
              data.format !== "haruquantai.algowizard.resources" ||
              data.version !== 1 ||
              !Array.isArray(data.items) ||
              !data.items.every(
                (r: Resource) =>
                  r &&
                  typeof r.name === "string" &&
                  typeof r.category === "string" &&
                  ["Custom blocks", "Random groups"].includes(r.kind) &&
                  Array.isArray(r.content) &&
                  r.content.every((v) => typeof v === "string"),
              )
            )
              throw new Error("Unsupported resource file");
            const names = resources.map((r) => r.name);
            const imported = data.items.map((r: Resource) => {
              const name = uniqueName(r.name, names);
              names.push(name);
              return { ...r, id: uid(), name };
            });
            onChange([...resources, ...imported]);
            setError("");
          } catch {
            setError(
              "Could not load resources. Choose a valid prototype resource JSON file.",
            );
          }
        }}
      />
      <div className="aw-resource-content">
        <div className="aw-resource-list">
          <table>
            <thead>
              <tr>
                <th>Name</th>
                <th>Category</th>
              </tr>
            </thead>
            <tbody>
              {items
                .filter((r) =>
                  r.name.toLowerCase().includes(search.toLowerCase()),
                )
                .map((r) => (
                  <tr
                    key={r.id}
                    className={r.id === current?.id ? "active" : ""}
                  >
                    <td>
                      <button onClick={() => setSelection(r.id)}>
                        {r.name}
                      </button>
                    </td>
                    <td>{r.category}</td>
                  </tr>
                ))}
            </tbody>
          </table>
          {!items.length && <p>No {kind.toLowerCase()} defined</p>}
        </div>
        <div className="aw-resource-detail">
          {current ? (
            <>
              <h3>{current.name}</h3>
              <p>
                {kind === "Random groups"
                  ? "Group content"
                  : "Custom block conditions"}
              </p>
              {current.content.map((text, i) => (
                <div className="aw-block-row" key={i}>
                  <button
                    className="aw-expression-link"
                    onClick={() => setEditing(i)}
                  >
                    {text}
                  </button>
                  <button
                    aria-label={`Remove resource condition ${i + 1}`}
                    onClick={() =>
                      change({
                        ...current,
                        content: current.content.filter((_, j) => j !== i),
                      })
                    }
                  >
                    ×
                  </button>
                </div>
              ))}
              <button className="aw-old" onClick={() => setEditing("new")}>
                Add condition(s)
              </button>
              <p className="aw-muted">
                Local prototype resource. Available during this workspace
                session.
              </p>
            </>
          ) : (
            <p>Select an item to edit its content.</p>
          )}
        </div>
      </div>
      {error && (
        <p className="aw-error" role="alert">
          {error}
        </p>
      )}
      {form && (
        <AWModal
          title={
            items.some((r) => r.id === form.id)
              ? "Rename resource"
              : `New ${kind === "Random groups" ? "random group" : "custom block"}`
          }
          onClose={() => setForm(null)}
          footer={
            <>
              <button onClick={() => setForm(null)}>Cancel</button>
              <button
                className="aw-primary"
                disabled={
                  !form.name.trim() ||
                  items.some(
                    (r) => r.name === form.name.trim() && r.id !== form.id,
                  )
                }
                onClick={() => {
                  const next = { ...form, name: form.name.trim() };
                  if (resources.some((r) => r.id === next.id)) change(next);
                  else onChange([...resources, next]);
                  setSelection(next.id);
                  setForm(null);
                }}
              >
                Save
              </button>
            </>
          }
        >
          <AWField
            label="Name"
            value={form.name}
            onChange={(name) => setForm({ ...form, name })}
          />
          <AWField
            label="Category"
            value={form.category}
            onChange={(category) => setForm({ ...form, category })}
          />
        </AWModal>
      )}
      {editing !== null && current && (
        <AlgoWizardBlockEditor
          initial={editing === "new" ? "" : current.content[editing]}
          onClose={() => setEditing(null)}
          onSave={(text) => {
            change({
              ...current,
              content:
                editing === "new"
                  ? [...current.content, text]
                  : current.content.map((v, i) => (i === editing ? text : v)),
            });
            setEditing(null);
          }}
        />
      )}
      {remove && current && (
        <AWConfirm
          title={`Remove ${kind.toLowerCase()}`}
          message={`Remove ${current.name}?`}
          onClose={() => setRemove(false)}
          onConfirm={() => {
            onChange(resources.filter((r) => r.id !== current.id));
            setSelection(null);
            setRemove(false);
          }}
        />
      )}
    </div>
  );
}
