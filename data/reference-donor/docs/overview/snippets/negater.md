# Negater snippets — full catalog

> Reference enumeration of the built-in **Negater** classes the Builder engine uses to invert
> ("negate") a building block — e.g. to turn a Long entry setup into its Short counterpart, or
> flip a comparison's direction — when generating opposite-direction strategy variants.

## How the set is assembled

Each negater is a snippet class extending `com.strategyquant.tradinglib.Negater`
(`work_directory/StrategyQuant/internal/extend/Snippets/SQ/Negater/`), implementing `negate(...)`
and annotated with `@SortOrder(n)`. `NegatersList` iterates the loaded negaters **in ascending
`@SortOrder` order** and calls each one's `negate()` in turn; the first negater that returns a
non-`null` result "claims" the block, and its result is used. A negater returns `null` to say "not
my block type, try the next one." This means **lower `@SortOrder` = tried first = higher
priority**; the very generic `DefaultNegater` (`1000000`) sits last as the catch-all fallback.

Most negaters follow the same shape: look up the block's declared **opposite block**
(`Blocks.getOppositeBlock(block)`, driven by each block class's own `@OppositeBlock` annotation),
copy/negate its parameters (`ParametersHelper.negateParametersInClonedBlock`), and negate any
attached data series. A handful add block-type-specific fixups on top of that (oscillator
recentering, output-line remapping, field flips).

## The 15 negaters

| Class | SortOrder | Targets (blockType / class check) | How it negates |
|---|---|---|---|
| `AndOrNegater` | 100 | `AND` / `OR` comparison blocks | Clones the AND/OR block and recursively negates each child block. |
| `CBlockNegater` | 1000 | Custom blocks (`CBlock` instances) | Uses the block's author-defined "opposite block" (`CBlock.getOppositeBlock()`); if the opposite is a Left/Right comparison against an oscillator indicator and a number, recenters the number around the oscillator's middle value. |
| `CDataIndyNegater` | 1000 | `CDataIndy` blocks | Clones the block and calls `negateValueIndex()` to flip its internal value index. |
| `OscillatorComparisonsNegater` | 1000 | Left/Right comparison blocks with one side a `Number` and the other an oscillator indicator | Gets the standard opposite comparison, then recenters the `Number` operand around the oscillator's middle value (e.g. `RSI > 30` → `RSI < 70` for an oscillator centered at 50) instead of just flipping the comparison symbol. |
| `FormulaNegater` | 8000 | `Formula`-supertype blocks | Clones the block (no opposite-block lookup) and negates its parameters in place. |
| `FunctionsNegater` | 9000 | `Value`-supertype blocks returning `PriceOrNumber` ("functions") | Standard opposite-block lookup + parameter/data-series negation. |
| `ActionsNegater` | 10000 | `Action`-supertype blocks (e.g. order-open actions) | Clones the block, negates its parameters, negates any attached `ExitMethods[]`, and flips the `Direction` field (`*= -1`) if present. |
| `ComparisonsNegater` | 10000 | `Comparison` / `Property`-supertype blocks | Standard opposite-block lookup + parameter/data-series negation. |
| `ConditionsNegater` | 10000 | `Condition`-supertype blocks | Standard opposite-block lookup; if the block declares `@OppositeBlock(oscillator=true)`, recenters the tagged numeric/int field around the annotation's `middleValue()` (e.g. an oscillator threshold) instead of copying it verbatim. |
| `UpperLowerNegater` | 10100 | Any block with exactly two `@Output` fields named `Upper` and `Lower` | Standard opposite-block lookup + parameter negation, then flips the block's `OutputIndex` field (`0` ↔ `1`) to swap which channel line is read. |
| `FiboNegater` | 900000 | `Fibo` indicator blocks | Standard negation, then explicitly copies `FiboLevel` unchanged (it should not be inverted). |
| `FractalNegater` | 900000 | `Fractal` indicator blocks | Standard negation, then flips the block's `OutputIndex` field (`0` ↔ `1`) to swap up/down fractal. |
| `PivotsNegater` | 900000 | `Pivots` indicator blocks | Standard negation, then remaps `OutputIndex` per a fixed pivot-line table: Pivot→Pivot, R1↔S1, R2↔S2, R3↔S3. |
| `UlcerNegater` | 900000 | `UlcerIndex` blocks | Standard opposite-block lookup + parameter/data-series negation, then flips the `Mode` field (`1` ↔ `2`). |
| `DefaultNegater` | 1000000 | Anything not claimed by a more specific negater (fallback) | Standard opposite-block lookup + parameter/data-series negation only. |

## Related

- Building blocks & opposite-block concept: [`../settings/building-blocks.md`](../settings/building-blocks.md) · [`../settings/oppositeblocks.md`](../settings/oppositeblocks.md)
- Snippets hub: [`README.md`](README.md)
- Source: `work_directory/StrategyQuant/internal/extend/Snippets/SQ/Negater/`
