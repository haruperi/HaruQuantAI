import { useState } from "react";
import { AWField, AWModal } from "./AlgoWizardControls";
import { makeRule, type Rule, type RuleKind } from "./algoWizardModel";
export function AlgoWizardRuleDialog({
  rule,
  names,
  onClose,
  onSave,
}: {
  rule?: Rule;
  names: string[];
  onClose: () => void;
  onSave: (rule: Rule) => void;
}) {
  const [name, setName] = useState(rule?.name ?? `Rule ${names.length + 1}`);
  const [kind, setKind] = useState<RuleKind>(rule?.kind ?? "If - Then");
  const [trigger, setTrigger] = useState(rule?.trigger ?? "On Bar Open");
  const invalid =
    !name.trim() || (name !== rule?.name && names.includes(name.trim()));
  return (
    <AWModal
      title={rule ? "Edit rule" : "Add new rule"}
      onClose={onClose}
      footer={
        <>
          <button onClick={onClose}>Close</button>
          <button
            className="aw-primary"
            disabled={invalid}
            onClick={() =>
              onSave({
                ...(rule ?? makeRule(name, kind)),
                name: name.trim(),
                kind,
                trigger,
              })
            }
          >
            {rule ? "Save" : "Add"}
          </button>
        </>
      }
    >
      <AWField label="Rule name" value={name} onChange={setName} />
      <AWField
        label="Rule type"
        value={kind}
        options={[
          "If - Then",
          "If - Then - Else",
          "Action only",
          "Signal",
          "Fuzzy Logic Signals",
        ]}
        onChange={(v) => setKind(v as RuleKind)}
      />
      <AWField
        label="Rule is triggered"
        value={trigger}
        options={[
          "On Bar Open",
          "On Bar Close",
          "On Every Tick",
          "On Init",
          "On Deinit",
        ]}
        onChange={setTrigger}
      />
      {invalid && <p role="alert">Use a unique, non-empty rule name.</p>}
    </AWModal>
  );
}
