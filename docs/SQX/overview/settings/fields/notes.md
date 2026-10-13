# Notes — field reference (for UI tests)

> Exact controls and persistence mechanism for the Notes settings tab, extracted from the web plugin source.

Source: `internal/plugins/SettingsNotes/` (`notes.html`, `NotesCtrl.js`, `module.js`). Tab is registered as
`SettingsTab` id `100`, `dataItem: 'settings-notes'`, `configElemName: 'Notes'`, task:
`Build,Optimize,Retest,NeuralNetworkTrainer`. No `testId` is set on the tab and **no element in this plugin
carries a `data-testid`** — a UI test must select by CSS class (`.notesContainer`, `.notesToolbar`, etc.).

This tab has no AngularJS `ng-model` bindings at all — it is a single `contenteditable` rich-text region wired
up with plain jQuery/`document.execCommand` calls, not Angular two-way binding.

## Content

| Label | Selector | Type | Default | Options / notes |
|---|---|---|---|---|
| Notes text | `.notesContainer` (`contenteditable` `<div>`) | rich-text editable div | empty string | Not an `ng-model`. On `blur`/`keyup`/`paste`/`input` (only if content actually changed since `focus`), `NotesCtrl.noteEdited(html)` is called, which stores the raw inner HTML into the task's XML `Notes` element via `addNode('Notes', htmlContent, ...)`. Loaded on tab activation from `Notes` element's first child text node. |
| Save | `.notesToolbar button.btn.btn-primary` ("Save") | button, `ng-click="onSave()"` | — | Forces `AppService.updateTaskXML()` and shows a "Notes saved" / "Notes saving failed" toast. Auto-save also happens via `shouldSaveSettings()` / the settings-changed flag whenever content is edited, so this button is a manual/explicit save, not the only save path. |

## Formatting toolbar

These are rich-text formatting commands (`document.execCommand`), not persisted settings/fields in their own
right — they just mutate the HTML inside `.notesContainer`. Each is a `<span>` wrapping a small icon `<img>`,
bound via `onmousedown` (not `ng-click`), so standard Angular click helpers won't fire them in a test; use a
mouse-down/click event on the element.

| Toolbar button | Selector | Action |
|---|---|---|
| Bold | `.notesBold` | `document.execCommand('bold')` |
| Italic | `.notesItalic` | `document.execCommand('italic')` |
| Underline | `.notesUnderline` | `document.execCommand('underline')` |
| Align left | `.notesLeft` | `document.execCommand('justifyLeft')` |
| Align center | `.notesCenter` | `document.execCommand('justifyCenter')` |
| Align right | `.notesRight` | `document.execCommand('justifyRight')` |
| Indent more | `.notesIndentMore` | `document.execCommand('indent')` |
| Indent less | `.notesIndentLess` | `document.execCommand('outdent')` |
| Horizontal rule | `.notesHr` | `document.execCommand('insertHTML', null, '<hr/>')` |
| Ordered list | `.notesOl` | `document.execCommand('insertOrderedList')` |
| Unordered list | `.notesUl` | `document.execCommand('insertUnorderedList')` |
| Link | `.notesLink` | Prompts (`prompt("URL:", "http://")`) then `document.execCommand('createLink', null, linkUrl)` |

## How it affects generation

None — confirmed by the plugin: there is no code path from `Notes` content into build/optimize/retest logic;
it is stored and redisplayed only.

## Related

- Prose page: [../notes.md](../notes.md)
- Fields hub: [README.md](README.md)
