# Other — variable/constant building block catalog

> Reference enumeration of the `Other` building-block snippets (5 classes): literal constants and
> named-variable readers used to inject a value into a rule, price expression, or another block's
> parameter. This is a lookup table; for the general building-block model see
> [`README.md`](README.md).

## How this file is organized

All classes live in `SQ.Blocks.Other` and extend `ValueBlock`. The `*Variable` blocks don't hold a
literal — their `@Editor(type=Editors.SelectionVariables)` parameter lets the user pick, in the
dropdown, one of the named variables the strategy previously wrote with the `AssignVariable` action
block (see `order-actions.md`); the block then reads that variable's current value. `Boolean` and
`Number` instead hold a literal value typed directly into the block. All are marked
`@NotFirstValue`, meaning they can't be the left-hand operand of a comparison — they're meant to sit
on the right-hand side (or as a nested value) of an expression.

| Display name | Class | Parameters | Description |
|---|---|---|---|
| (NUM) Number | `Number` | Number: double, default 0, range −999999999…999999999 | A literal numeric constant typed into the block, used anywhere a `Number`/`Price` value is expected. |
| (BOOL) Boolean | `Boolean` | Value: bool, default false | A literal true/false constant. |
| (IVAR) Int Variable | `IntVariable` | Variable: int, selected from strategy variables | Reads the current value of a user-defined integer variable set elsewhere via `AssignVariable`. |
| (DVAR) Double Variable | `DoubleVariable` | Variable: double, selected from strategy variables | Reads the current value of a user-defined double variable set elsewhere via `AssignVariable`. |
| (BVAR) Boolean Variable | `BooleanVariable` | Variable: bool, selected from strategy variables | Reads the current value of a user-defined boolean variable set elsewhere via `AssignVariable`. |

## Related

- Building-block model overview: [`README.md`](README.md)
- `AssignVariable` and other actions that write these variables: [`order-actions.md`](order-actions.md)
- Comparison operators these constants/variables are typically compared against: [`comparisons.md`](comparisons.md)
- Math/utility functions that can further transform a variable's value: [`functions.md`](functions.md)
