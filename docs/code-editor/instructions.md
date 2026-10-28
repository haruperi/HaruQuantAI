# AppCodeEditor User & Developer Instructions

Welcome to the **AppCodeEditor** workspace instruction manual. This guide covers everything needed to create, edit, compile, verify, and package custom trading building blocks, indicators, money management algorithms, and databank analysis extensions for the HaruQuantAI platform.

---

## 1. Overview & Architecture

**AppCodeEditor** is an embedded development environment engineered for high-performance quantitative strategy customization. It achieves 100% functional parity with the StrategyQuant X Code Editor while running on a modern Python 3.14+ runtime with Monaco editor ergonomics.

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                            AppCodeEditor Shell                              │
│                                                                             │
│  ┌───────────────────────────────────────────────────────────────────────┐  │
│  │ Top Action Menu: New | Save | Compile | Template | Test | Export/Import│  │
│  └───────────────────────────────────────────────────────────────────────┘  │
│  ┌───────────────┬───────────────────────────────────────┬───────────────┐  │
│  │ File System   │ Monaco Code Editor                    │ AST Symbol    │  │
│  │ Navigator     │ - Multi-tab document session          │ Outline       │  │
│  │               │ - Syntax highlighting (Python/JSON)   │ - Classes     │  │
│  │ - Snippets    │ - Line numbers & dirty tracking       │ - Methods     │  │
│  │ - Indicators  │ - Context menu actions                │ - Attributes  │  │
│  │ - Blocks      ├───────────────────────────────────────┤ - Imports     │  │
│  │ - Analysis    │ Bottom Dock Panel                     │               │  │
│  │               │ [Problems] [Output] [Search] [Term]   │               │  │
│  └───────────────┴───────────────────────────────────────┴───────────────┘  │
│  ┌───────────────────────────────────────────────────────────────────────┐  │
│  │ Status Bar: Path | Ln, Col | UTF-8 | Python 3.14 | AST Ready          │  │
│  └───────────────────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Key Technical Characteristics
- **Root Snippets Location:** All user extensions reside inside `app/include/snippets/` to guarantee clean separation between platform internals and user customizations.
- **Dynamic Module Reloading:** When a snippet is compiled, the backend automatically invokes Python's dynamic module reloader (`importlib.reload`). The strategy builder, AlgoWizard, and databank engines immediately recognize modified extensions without restarting the server.
- **Path Confinement:** Sandboxed directory safety prevents directory traversal beyond authorized workspace folders.
- **REST & UI Bridge:** The workspace communicates through strongly-typed API endpoints mounted under `/api/v1/code-editor`.

---

## 2. Workspace Layout & Dock Panels

The workspace consists of five responsive docked panels designed for rapid strategy extension authoring:

![AppCodeEditor Main Layout](file:///c:/Users/rharu/AppDev/HaruQuantAI/docs/dev/images/Overview1.png)

1. **Top Action Menu & Toolbar**: Quick-access buttons for project creation, atomic saving, compilation, testing, and pack management.
2. **File Navigator (Left Panel)**: Tree representation of all folders and snippet files under `app/include/snippets/`.
3. **Editor Area (Center Panel)**: Multi-tab Monaco editor with syntax checking, code folding, bracket matching, and unsaved change (`●`) indicators.
4. **Symbol Outline (Right Panel)**: Real-time Python AST tree listing classes, functions, instance methods, class attributes, and module imports.
5. **Bottom Dock Panel**:
   - **Problems**: Real-time Python AST parsing diagnostics showing error severity, line number, column, and error description.
   - **Output**: Build, compilation, and dynamic module reload execution logs.
   - **Search**: Workspace-wide Find-in-Files search results with match highlights and jump-to-line navigation.
   - **Terminal**: Headless shell access for UV, Pytest, and CLI utilities.
6. **Status Bar (Bottom Footer)**: Shows current file path, cursor position (Ln, Col), character encoding (`UTF-8`), active language mode (`Python`), and compilation status.

---

## 3. Toolbar Actions

The top toolbar provides direct access to primary workspace workflows:

![Top Menu Action Bar](file:///c:/Users/rharu/AppDev/HaruQuantAI/docs/dev/images/Top-menu.png)

| Action | Shortcut | Description |
| :--- | :---: | :--- |
| **New ▾** | `Ctrl+N` | Opens a dropdown to create a blank **New File** or **New Directory**. |
| **Open ▾** | `Ctrl+O` | Opens an existing snippet or external file into an active editor tab. |
| **Save** | `Ctrl+S` | Flushes the active tab to disk atomically and executes AST validation. |
| **Save All** | `Ctrl+Shift+S` | Flushes all open modified tabs to disk simultaneously. |
| **Create from Template ▾** | `Ctrl+T` | Opens the 12-snippet StrategyQuant X creation wizard. |
| **Compile** | `F7` | Parses file AST, checks syntax, and hot-reloads the module into the Python runtime. |
| **Test Indicator** | `F5` | Opens the interactive Indicator Tester modal over synthetic or historical market data. |
| **+ Import ▾** | `Ctrl+I` | Imports `.zip` extension packages with collision resolution. |
| **Export ▾** | `Ctrl+E` | Bundles selected extensions into a portable `.zip` package with `manifest.json`. |
| **More ▾** | — | Options to split editor tabs, toggle navigators, or format code. |

---

## 4. File Navigator & Context Menu

The left navigator organizes all custom extensions. Right-clicking any file or directory opens the 14-action context menu:

![File Navigator Context Menu](file:///c:/Users/rharu/AppDev/HaruQuantAI/docs/dev/images/File%20Context%20Menu.png)

### Context Menu Actions
1. **Open**: Opens the file into the central editor panel.
2. **Open in Split View**: Opens the document in a side-by-side split editor panel.
3. **New File**: Prompts for a file name and creates a new `.py` file in the selected directory.
4. **New Directory**: Creates a subfolder in the selected directory.
5. **Clone / Duplicate**: Creates an exact duplicate of the file with `_copy.py` suffix.
6. **Rename**: Inline rename of the target file or directory with automatic tab title sync.
7. **Delete**: Removes the file or directory with confirmation prompt.
8. **Compile File**: Validates AST and dynamically reloads the target file.
9. **Test Indicator**: Directly launches the Indicator Tester on the selected indicator file.
10. **Find in Directory**: Pre-populates the bottom search panel with the selected folder path.
11. **Export Package**: Pre-selects the file/directory for export pack creation.
12. **Inspect Package**: (ZIP archives only) Views internal files and manifest metadata.
13. **Copy Relative Path**: Copies the relative path from project root to the clipboard.
14. **Refresh Navigator**: Reloads the directory tree from the file system.

---

## 5. Creating Extensions from Templates

AppCodeEditor includes full support for all **12 StrategyQuant X Extension Templates**. Click **Create from Template** in the toolbar to launch the wizard:

![Create from Template Modal](file:///c:/Users/rharu/AppDev/HaruQuantAI/docs/dev/images/Create-From-Template.png)

### Available Template Types

| Category | Template ID | Description | Target Path |
| :--- | :--- | :--- | :--- |
| **Blocks** | `BlocksIndicators` | Custom technical indicator with period params and series calculation. | `app/include/snippets/indicators/` |
| **Blocks** | `BlocksSignal` | Entry or exit signal evaluation returning boolean conditions. | `app/include/snippets/blocks/` |
| **Blocks** | `BlocksOrder` | Custom order creation, position sizing, and stop/limit logic. | `app/include/snippets/blocks/` |
| **Blocks** | `BlocksOtherActions`| Action execution block (e.g., trailing stop, partial close, alerts). | `app/include/snippets/blocks/` |
| **Columns** | `ColumnsDatabanks` | Custom databank metric calculated across all trades in a backtest. | `app/include/snippets/columns/` |
| **Columns** | `ColumnsTrades` | Custom databank column calculated per individual trade. | `app/include/snippets/columns/` |
| **Money Management**| `MoneyManagement` | Position sizing algorithm (Fixed Risk %, Kelly, Volatility-Adjusted). | `app/include/snippets/money_management/` |
| **Monte Carlo** | `MonteCarloManipulation` | Resampling, trade shuffling, and slippage stress-testing. | `app/include/snippets/monte_carlo/` |
| **Monte Carlo** | `MonteCarloRetest` | Parameter variance and random-history retesting. | `app/include/snippets/monte_carlo/` |
| **Analysis & AI** | `WhatIf` | What-if scenario simulation (e.g., skip trades on Mondays). | `app/include/snippets/what_if/` |
| **Analysis & AI** | `CustomAnalysis` | Portfolio aggregation, correlation analysis, and custom charting. | `app/include/snippets/custom_analysis/` |
| **Analysis & AI** | `AITools` | Machine learning model hooks, genetic operators, and AI fitness. | `app/include/snippets/ai_tools/` |

### Step-by-Step: Creating a Custom Indicator
1. Click **Create from Template ▾** on the top toolbar.
2. Select **Technical Indicator** (`BlocksIndicators`).
3. Enter a snippet name (e.g., `CustomKeltnerChannel`).
4. Preview the generated Python code in the right preview pane.
5. Click **Create Snippet**. The file will be written to `app/include/snippets/indicators/custom_keltner_channel.py` and immediately opened in a new editor tab.

```python
"""Custom Keltner Channel technical indicator."""

from dataclasses import dataclass
import numpy as np
from app.include.indicators.base import IndicatorSeries

@dataclass
class CustomKeltnerChannel:
    period: int = 20
    multiplier: float = 2.0

    def calculate(self, bars) -> IndicatorSeries:
        close = np.array([bars.close(i) for i in range(bars.count)])
        # Compute baseline moving average
        basis = np.convolve(close, np.ones(self.period) / self.period, mode="same")
        return IndicatorSeries(name="KeltnerBasis", values=basis)
```

---

## 6. Compilation & Dynamic Reloading

Press **F7** or click **Compile** to trigger the build pipeline:

![Compilation and Symbol Outline](file:///c:/Users/rharu/AppDev/HaruQuantAI/docs/dev/images/Overview2.png)

1. **AST Parsing**: The backend checks the file using Python's `ast` module.
2. **Diagnostics Generation**: If a syntax error exists, the exact line, column, and source preview are displayed in the **Problems** tab. Clicking an error jumps directly to that line in Monaco.
3. **Dynamic Reload**: If syntax is valid, `importlib.reload` hot-reloads the module into the running process. The **Output** tab logs:
   ```
   [2026-10-28 11:30:15] Compiling: app/include/snippets/indicators/custom_keltner_channel.py
   [2026-10-28 11:30:15] Syntax check passed (0 errors, 0 warnings).
   [2026-10-28 11:30:15] Dynamic reload: module 'app.include.snippets.indicators.custom_keltner_channel' reloaded successfully.
   ```

---

## 7. Indicator Testing & Verification

Press **F5** or click **Test Indicator** to open the **Indicator Tester Modal**:

![Indicator Tester Configuration](file:///c:/Users/rharu/AppDev/HaruQuantAI/docs/dev/images/Indicator-Test-Chart-Params.png)

### Test Configuration Parameters
- **Indicator Name**: The class or function name to test (defaults to the active editor file).
- **Symbol**: Target symbol (e.g., `EURUSD`, `GBPUSD`, `BTCUSD`).
- **Timeframe**: Timeframe for bar aggregation (`M1`, `M5`, `M15`, `H1`, `D1`).
- **Bar Count**: Number of evaluation bars to generate (e.g., 150).
- **Warmup Reserve Bars (`bars_to_reserve`)**: StrategyQuant X reserve bars (default `50`). Essential for indicators like SMA, EMA, and MACD to ensure that the visible chart bars begin after the indicator has fully warmed up.
- **Dynamic Parameters**: Edit parameter values (e.g., `period = 20`, `multiplier = 2.5`) directly in the sidebar.

### Test Results & Verification
Click **Run Test** to compute the indicator values. The results view opens:

![Indicator Tester Results & Chart](file:///c:/Users/rharu/AppDev/HaruQuantAI/docs/dev/images/Indicator-Test-Results.png)

- **Interactive Candlestick Chart**: Shows price candles alongside the calculated indicator plot line.
- **Summary Metrics**: Status, calculated bars, average value, min/max values, and compute execution time.
- **Bar-by-Bar Data Table**: Paginated inspection table showing `Time`, `Open`, `High`, `Low`, `Close`, and `Indicator Value`.
- **Discrepancy Table**: Compares calculated values against reference benchmark values and highlights differences that exceed tolerance (`diff > 1e-4`).

---

## 8. Extension Packages: Import & Export

Click **Export ▾** or **+ Import ▾** to open the package management dialog:

![Import and Export Dialogs](file:///c:/Users/rharu/AppDev/HaruQuantAI/docs/dev/images/Import-Export-Dialogs.png)

### Exporting an Extension Pack
1. Select the files or folders to include from the project tree.
2. Enter a **Package Name**, **Author**, and **Description**.
3. Specify the destination archive path (e.g., `dist/my_indicators_v1.zip`).
4. Click **Export Package**. The backend generates a standard ZIP package containing:
   - All selected `.py` snippet files.
   - A `manifest.json` file specifying package metadata, dependencies, and file hash checksums.

### Importing an Extension Pack
1. In the **Import Pack** tab, select a `.zip` archive.
2. Click **Inspect Package**. The dialog lists all enclosed files, file sizes, and flags whether each file already exists locally.
3. Select a collision resolution rule:
   - **Overwrite**: Replaces local files with package contents.
   - **Skip**: Retains existing local files and imports only new snippets.
   - **Rename**: Appends `_imported` to filenames that conflict.
4. Click **Import Package**. The files are extracted into `app/include/snippets/` and the navigator tree refreshes automatically.

---

## 9. Search & Find in Files

To search across all project files:
1. Open the **Search** tab in the bottom panel (or press `Ctrl+Shift+F`).
2. Type your search query.
3. Use the toggle buttons:
   - `Aa` — **Match Case**: Case-sensitive search.
   - `\b` — **Match Whole Word**: Restricts matches to complete word boundaries.
   - `.*` — **Use Regular Expression**: Enables full regex search patterns.
4. Filter by directory if desired (e.g., `app/include/snippets/indicators`).
5. Click any match in the results list to open the corresponding file and highlight the matched line in the editor.

---

## 10. Keyboard Shortcuts Reference

| Shortcut | Command |
| :--- | :--- |
| `Ctrl+S` / `Cmd+S` | Save Active File & Check Syntax |
| `Ctrl+Shift+S` | Save All Open Files |
| `F7` | Compile Active File & Reload Module |
| `F5` | Open Indicator Tester Dialog |
| `Ctrl+T` | Open Create-from-Template Wizard |
| `Ctrl+Shift+F` | Focus Find-in-Files Search Panel |
| `Ctrl+N` | Create New File |
| `Ctrl+W` | Close Active Tab |
| `Ctrl+F` | Find in Active Editor |
| `Ctrl+H` | Replace in Active Editor |
| `Alt+Up` / `Alt+Down` | Move Line Up / Down |
| `Shift+Alt+Down` | Copy Line Down |
| `Ctrl+/` | Toggle Line Comment |

---

## 11. REST API Reference

For automated testing, CI/CD pipelines, or headless scripting, all Code Editor operations can be invoked via HTTP:

| Method | Endpoint | Description |
| :--- | :--- | :--- |
| `GET` | `/api/v1/code-editor/init` | Initializes workspace layout and loads session tabs. |
| `GET` | `/api/v1/code-editor/navigator` | Returns the directory tree structure for a given root. |
| `GET` | `/api/v1/code-editor/tabs` | Lists all open editor tabs. |
| `POST` | `/api/v1/code-editor/tabs/open` | Opens a file tab (`file_path`, `mode`). |
| `POST` | `/api/v1/code-editor/tabs/close` | Closes a file tab (`file_path`, `force`). |
| `POST` | `/api/v1/code-editor/file/save` | Flushes content to disk atomically and returns diagnostics. |
| `POST` | `/api/v1/code-editor/file/save-all` | Saves all dirty files in a single atomic transaction. |
| `POST` | `/api/v1/code-editor/file/new` | Creates a new file at `file_path`. |
| `POST` | `/api/v1/code-editor/file/new-dir` | Creates a new folder at `dir_path`. |
| `POST` | `/api/v1/code-editor/file/clone` | Duplicates `source_path` to `target_path`. |
| `POST` | `/api/v1/code-editor/file/rename` | Renames `old_path` to `new_path`. |
| `POST` | `/api/v1/code-editor/file/delete` | Deletes file at `file_path`. |
| `POST` | `/api/v1/code-editor/compile` | Compiles file, validates AST, and dynamically reloads module. |
| `POST` | `/api/v1/code-editor/compile-all` | Validates syntax across all snippet files in the workspace. |
| `POST` | `/api/v1/code-editor/search` | Performs multi-file pattern search with regex and case filters. |
| `GET` | `/api/v1/code-editor/templates` | Lists all 12 StrategyQuant X snippet template metadata. |
| `POST` | `/api/v1/code-editor/templates/render` | Returns source preview of a template given a snippet name. |
| `POST` | `/api/v1/code-editor/templates/create` | Instantiates template, writes to disk, and opens tab. |
| `POST` | `/api/v1/code-editor/import-export/export` | Packages selected files into a ZIP archive with manifest. |
| `POST` | `/api/v1/code-editor/import-export/inspect` | Inspects archive contents and checks local collisions. |
| `POST` | `/api/v1/code-editor/import-export/import` | Extracts archive with collision resolution rules. |
| `POST` | `/api/v1/code-editor/indicator-test/run` | Runs indicator calculation over OHLCV data with reserve bars. |
| `POST` | `/api/v1/code-editor/indicator-test/edit-params` | Updates test parameters and re-executes calculation. |

---

## 12. Best Practices & Troubleshooting

### Best Practices
- **Reserve Bars**: Always ensure `bars_to_reserve` is at least as large as the indicator's longest lookback period (e.g., if testing a 50-period EMA, use `bars_to_reserve >= 50`). This prevents initial `NaN` values from distorting visual plots and statistics.
- **Use Typed Contracts**: Import standard contract classes such as `IndicatorSeries` from `app.include.indicators.base` and `OrderType` from `app.include.enums`.
- **Modular Snippets**: Keep each custom block, indicator, or column in its own dedicated file under `app/include/snippets/<category>/` for clean packaging and version tracking.

### Common Pitfalls
- **Path Traversal Error**: Attempting to save, create, or clone a file outside `app/include/snippets/` will raise `CodeEditorError: Path is outside authorized root`. Keep all custom extensions within the designated snippets directory.
- **Syntax Diagnostics**: If the compiler reports a syntax error, check the **Problems** tab. Monaco will mark the offending line with a red squiggly indicator.
- **Name Collisions during Import**: When importing third-party packs, use **Rename** mode if you want to inspect differences before overwriting your existing code.
