import { describe, expect, it } from "vitest";
import {
  block,
  canSimplify,
  decodeDraft,
  dirty,
  encodeDraft,
  makeDraft,
  makeRule,
  revise,
  startHistory,
  travel,
  uniqueName,
} from "../../../../src/workspace/AlgoWizard/algoWizardModel";
import {
  exampleDraft,
  examples,
} from "../../../../src/workspace/AlgoWizard/algoWizardFixtures";

describe("AlgoWizard local draft lifecycle", () => {
  it("keeps histories independent and drops redo after a new edit", () => {
    const a = startHistory(makeDraft("A", "Full", true));
    const b = startHistory(makeDraft("B", "Simple"));
    const changed = revise(a, { ...a.present, name: "Edited" });
    expect(dirty(changed)).toBe(true);
    const undone = travel(changed, "undo");
    expect(undone.present.name).toBe("A");
    expect(dirty(undone)).toBe(false);
    expect(travel(undone, "redo").present.name).toBe("Edited");
    expect(
      revise(undone, { ...undone.present, name: "Different" }).future,
    ).toEqual([]);
    expect(b.present.name).toBe("B");
    expect(b.past).toEqual([]);
  });
  it("round-trips documents and rejects malformed nested contents without accepting SQX archives", () => {
    const d = exampleDraft(0);
    const decoded = decodeDraft(encodeDraft(d));
    expect(decoded.id).not.toBe(d.id);
    expect(decoded.rules).toEqual(d.rules);
    for (const text of [
      "PK binary",
      "{}",
      '{"format":"haruquantai.algowizard.ui","version":2}',
      encodeDraft({
        ...d,
        rules: [{ ...d.rules[0], signals: [{ id: "broken" }] as never }],
      }),
      encodeDraft({ ...d, rules: [...d.rules, d.rules[0]] }),
    ])
      expect(() => decodeDraft(text)).toThrow("Invalid prototype");
  });
  it("allocates unique names and guards lossy Simple conversion", () => {
    expect(uniqueName("A", ["A", "A 2"])).toBe("A 3");
    expect(uniqueName(" ", [])).toBe("New strategy");
    const d = exampleDraft(0);
    expect(canSimplify(d)).toBe(true);
    expect(
      canSimplify({
        ...d,
        rules: [...d.rules, makeRule("Custom", "Action only")],
      }),
    ).toBe(false);
    expect(
      canSimplify({
        ...d,
        rules: [{ ...d.rules[0], trigger: "On Every Tick" }],
      }),
    ).toBe(false);
  });
  it("all example drafts have unique node ids and do not share mutable state", () => {
    examples.forEach((_, i) => {
      const first = exampleDraft(i);
      const second = exampleDraft(i);
      first.rules[0].signals[0].conditions.push(block("Extra condition"));
      expect(second.rules[0].signals[0].conditions).toHaveLength(1);
      expect(decodeDraft(encodeDraft(first)).name).toBe(first.name);
    });
  });
});
