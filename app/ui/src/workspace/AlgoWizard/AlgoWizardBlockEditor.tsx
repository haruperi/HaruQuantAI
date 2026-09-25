import { useState } from "react";
import { AWField, AWModal } from "./AlgoWizardControls";
import { blockGroups } from "./algoWizardFixtures";
export function AlgoWizardBlockEditor({
  initial = "",
  action = false,
  onClose,
  onSave,
}: {
  initial?: string;
  action?: boolean;
  onClose: () => void;
  onSave: (text: string) => void;
}) {
  const [search, setSearch] = useState("");
  const [category, setCategory] = useState(
    action ? "Order actions" : "Comparisons",
  );
  const [selected, setSelected] = useState(
    action ? "Enter at Market" : "Crosses above",
  );
  const [left, setLeft] = useState("EMA(FastEMA)[1]");
  const [right, setRight] = useState("EMA(SlowEMA)[1]");
  const [op, setOp] = useState("crosses above");
  const [period, setPeriod] = useState("14");
  const [shift, setShift] = useState("1");
  const [direction, setDirection] = useState("Long");
  const [lots, setLots] = useState("0.1");
  const [expression, setExpression] = useState(
    initial ||
      (action ? "Enter at Market (Long, 0.1 lots)" : `${left} ${op} ${right}`),
  );
  const select = (name: string, cat: string) => {
    setSelected(name);
    setCategory(cat);
    if (cat.includes("actions"))
      setExpression(`${name} (${direction}, ${lots} lots)`);
    else if (cat === "Comparisons") {
      const operator =
        (
          {
            "Is greater (>)": ">",
            "Is lower (<)": "<",
            "Equals (=)": "=",
          } as Record<string, string>
        )[name] ?? name.toLowerCase();
      setOp(operator);
      setExpression(`${left} ${operator} ${right}`);
    } else
      setExpression(
        cat === "Indicators"
          ? `${name}(${period})[${shift}]`
          : cat === "Prices"
            ? `${name}[${shift}]`
            : name,
      );
  };
  return (
    <AWModal
      wide
      title={action ? "Add / edit action" : "Add / edit condition"}
      onClose={onClose}
      footer={
        <>
          <span className="aw-muted">Local example block catalog</span>
          <button onClick={onClose}>Cancel</button>
          <button
            className="aw-primary"
            disabled={!expression.trim()}
            onClick={() => onSave(expression.trim())}
          >
            Select
          </button>
        </>
      }
    >
      <div className="aw-block-search">
        <input
          aria-label="Search blocks"
          placeholder="Search in all..."
          value={search}
          onChange={(e) => setSearch(e.target.value)}
        />
      </div>
      <div className="aw-block-picker">
        <nav>
          {Object.keys(blockGroups).map((cat) => (
            <button
              key={cat}
              className={category === cat ? "active" : ""}
              onClick={() => {
                setCategory(cat);
                setSearch("");
              }}
            >
              {cat}
            </button>
          ))}
        </nav>
        <div className="aw-block-list">
          {Object.entries(blockGroups)
            .filter(([cat]) => search || cat === category)
            .flatMap(([cat, names]) =>
              names
                .filter((name) =>
                  name.toLowerCase().includes(search.toLowerCase()),
                )
                .map((name) => (
                  <button
                    key={name}
                    className={selected === name ? "active" : ""}
                    onClick={() => select(name, cat)}
                    onDoubleClick={() => select(name, cat)}
                  >
                    {name}
                  </button>
                )),
            )}
        </div>
        <div className="aw-block-parameters">
          <h3>{selected}</h3>
          {category === "Comparisons" ? (
            <>
              <AWField
                label="Left value"
                value={left}
                onChange={(v) => {
                  setLeft(v);
                  setExpression(`${v} ${op} ${right}`);
                }}
              />
              <AWField
                label="Comparison"
                value={op}
                options={[
                  "crosses above",
                  "crosses below",
                  ">",
                  "<",
                  "=",
                  ">=",
                  "<=",
                  "is rising",
                  "is falling",
                ]}
                onChange={(v) => {
                  setOp(v);
                  setExpression(`${left} ${v} ${right}`);
                }}
              />
              <AWField
                label="Right value"
                value={right}
                onChange={(v) => {
                  setRight(v);
                  setExpression(`${left} ${op} ${v}`);
                }}
              />
            </>
          ) : category.includes("actions") ? (
            <>
              <AWField
                label="Direction"
                value={direction}
                options={["Long", "Short", "Both"]}
                onChange={(v) => {
                  setDirection(v);
                  setExpression(`${selected} (${v}, ${lots} lots)`);
                }}
              />
              <AWField
                label="Order size"
                type="number"
                value={lots}
                onChange={(v) => {
                  setLots(v);
                  setExpression(`${selected} (${direction}, ${v} lots)`);
                }}
              />
            </>
          ) : (
            <>
              <AWField
                label="Period"
                value={period}
                onChange={(v) => {
                  setPeriod(v);
                  setExpression(`${selected}(${v})[${shift}]`);
                }}
              />
              <AWField
                label="Shift"
                value={shift}
                onChange={(v) => {
                  setShift(v);
                  setExpression(
                    category === "Prices"
                      ? `${selected}[${v}]`
                      : `${selected}(${period})[${v}]`,
                  );
                }}
              />
            </>
          )}
          <p className="aw-muted">
            Edit the expression below for variables, chart references or
            additional parameters.
          </p>
        </div>
      </div>
      <label className="aw-expression">
        Selected expression
        <input
          aria-label="Selected expression"
          value={expression}
          onChange={(e) => setExpression(e.target.value)}
        />
      </label>
    </AWModal>
  );
}
