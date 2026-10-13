# SQDataLib Specification Catalog

- **Package Root:** `com.strategyquant.datalib.*`
- **Total Classes:** 191
- **Total Methods / Functions:** 3136
- **Donor Reference:** `SQX_REFERENCE_ROOT`
- **Evidence Standard:** Paraphrased clean-room specification (`contains_proprietary_source: false`).

## Overview and Architectural Responsibility

`SQDataLib` manages all market data structures within StrategyQuant X. It encapsulates price timeframes, tick and OHLCV bar structures, session calendars, broker instruments, data feed streaming abstractions, and data validation exception handling.

---

## Table of Subsystems & Packages

| Subsystem / Subpackage | Classes Count | Description |
| :--- | :--- | :--- |
| [`(root)`](#subsystem-(root)) | 9 | Root classes of `com.strategyquant.datalib` |
| [`bartype`](#subsystem-bartype) | 9 | Components belonging to `com.strategyquant.datalib.bartype` |
| [`basket`](#subsystem-basket) | 5 | Components belonging to `com.strategyquant.datalib.basket` |
| [`broker`](#subsystem-broker) | 3 | Components belonging to `com.strategyquant.datalib.broker` |
| [`consts`](#subsystem-consts) | 5 | Components belonging to `com.strategyquant.datalib.consts` |
| [`customData`](#subsystem-customdata) | 13 | Components belonging to `com.strategyquant.datalib.customData` |
| [`darwinex`](#subsystem-darwinex) | 1 | Components belonging to `com.strategyquant.datalib.darwinex` |
| [`data`](#subsystem-data) | 82 | Components belonging to `com.strategyquant.datalib.data` |
| [`dataseries`](#subsystem-dataseries) | 19 | Components belonging to `com.strategyquant.datalib.dataseries` |
| [`historyData`](#subsystem-historydata) | 9 | Components belonging to `com.strategyquant.datalib.historyData` |
| [`indicators`](#subsystem-indicators) | 6 | Components belonging to `com.strategyquant.datalib.indicators` |
| [`instrument`](#subsystem-instrument) | 5 | Components belonging to `com.strategyquant.datalib.instrument` |
| [`metatrader4`](#subsystem-metatrader4) | 4 | Components belonging to `com.strategyquant.datalib.metatrader4` |
| [`session`](#subsystem-session) | 10 | Components belonging to `com.strategyquant.datalib.session` |
| [`ticksimulator`](#subsystem-ticksimulator) | 4 | Components belonging to `com.strategyquant.datalib.ticksimulator` |
| [`timeframe`](#subsystem-timeframe) | 1 | Components belonging to `com.strategyquant.datalib.timeframe` |
| [`timezone`](#subsystem-timezone) | 2 | Components belonging to `com.strategyquant.datalib.timezone` |
| [`validation`](#subsystem-validation) | 4 | Components belonging to `com.strategyquant.datalib.validation` |

---

## Subsystem: `(root)`

### `ChartDef`
- **Full Qualified Name:** `com.strategyquant.datalib.ChartDef`
- **Primary Job / Responsibility:** Market data abstraction and time-series container (`ChartDef`).

#### Methods & Functions
| Modifiers | Method Name | Parameter Signatures | Return Type | Functional Description / Job |
| :--- | :--- | :--- | :--- | :--- |
| `instance` | `isRegistered` | `()` | `boolean` | Evaluates boolean predicate `isRegistered` on `ChartDef` |
| `instance` | `getSymbol` | `()` | `String` | Retrieves `Symbol` property from `ChartDef` |
| `instance` | `getInstrumentInfo` | `()` | `InstrumentInfo` | Retrieves `InstrumentInfo` property from `ChartDef` |
| `instance` | `getHistoryFrom` | `()` | `long` | Retrieves `HistoryFrom` property from `ChartDef` |
| `instance` | `getHistoryTo` | `()` | `long` | Retrieves `HistoryTo` property from `ChartDef` |
| `instance` | `getClone` | `()` | `ChartDef` | Retrieves `Clone` property from `ChartDef` |
| `instance` | `getClone` | `()` | `ChartDef` | Retrieves `Clone` property from `ChartDef` |
| `instance` | `getClone` | `(arg0: String)` | `ChartDef` | Retrieves `Clone` property from `ChartDef` |
| `instance` | `getClone` | `(arg0: long, arg1: long)` | `ChartDef` | Retrieves `Clone` property from `ChartDef` |
| `instance` | `getMinDistance` | `()` | `double` | Retrieves `MinDistance` property from `ChartDef` |
| `instance` | `setFromXML` | `(arg0: Element)` | `void` | Sets `FromXML` configuration/state on `ChartDef` |
| `instance` | `getXML` | `()` | `Element` | Retrieves `XML` property from `ChartDef` |
| `instance` | `getConnectionName` | `()` | `String` | Retrieves `ConnectionName` property from `ChartDef` |
| `instance` | `getInstrument` | `()` | `String` | Retrieves `Instrument` property from `ChartDef` |
| `instance` | `getConnectionHash` | `()` | `int` | Retrieves `ConnectionHash` property from `ChartDef` |
| `instance` | `getSymbolHash` | `()` | `int` | Retrieves `SymbolHash` property from `ChartDef` |
| `instance` | `getTimeframe` | `()` | `String` | Retrieves `Timeframe` property from `ChartDef` |
| `instance` | `getSession` | `()` | `String` | Retrieves `Session` property from `ChartDef` |
| `instance` | `getSymbolInfo` | `()` | `InstrumentInfo` | Retrieves `SymbolInfo` property from `ChartDef` |
| `instance` | `getEffectiveBarTimeType` | `()` | `int` | Retrieves `EffectiveBarTimeType` property from `ChartDef` |
| `instance` | `getBarTimeType` | `()` | `int` | Retrieves `BarTimeType` property from `ChartDef` |
| `instance` | `setSymbol` | `(arg0: String)` | `void` | Sets `Symbol` configuration/state on `ChartDef` |
| `instance` | `getSpread` | `()` | `double` | Retrieves `Spread` property from `ChartDef` |
| `instance` | `modifySpread` | `(arg0: double)` | `void` | Performs modify spread operation |
| `instance` | `setRealSpread` | `(arg0: boolean)` | `void` | Sets `RealSpread` configuration/state on `ChartDef` |
| `instance` | `setSpread` | `(arg0: double)` | `void` | Sets `Spread` configuration/state on `ChartDef` |
| `instance` | `setSession` | `(arg0: String)` | `void` | Sets `Session` configuration/state on `ChartDef` |
| `instance` | `getBackloadType` | `()` | `int` | Retrieves `BackloadType` property from `ChartDef` |
| `instance` | `setMinDistance` | `(arg0: double)` | `void` | Sets `MinDistance` configuration/state on `ChartDef` |
| `instance` | `getChartsHash` | `()` | `String` | Retrieves `ChartsHash` property from `ChartDef` |
| `instance` | `setLoadedHistoryFrom` | `(arg0: long)` | `void` | Sets `LoadedHistoryFrom` configuration/state on `ChartDef` |
| `instance` | `isSmallerThan` | `(arg0: ChartDef)` | `boolean` | Evaluates boolean predicate `isSmallerThan` on `ChartDef` |
| `instance` | `canBeComputedFrom` | `(arg0: ChartDef)` | `boolean` | Evaluates boolean predicate `canBeComputedFrom` on `ChartDef` |
| `instance` | `getLoadedHistoryFrom` | `()` | `long` | Retrieves `LoadedHistoryFrom` property from `ChartDef` |
| `instance` | `setHistoryTo` | `(arg0: long)` | `void` | Sets `HistoryTo` configuration/state on `ChartDef` |
| `instance` | `isSameConnectionSymbol` | `(arg0: ChartDef)` | `boolean` | Evaluates boolean predicate `isSameConnectionSymbol` on `ChartDef` |
| `instance` | `setRegistered` | `()` | `void` | Sets `Registered` configuration/state on `ChartDef` |
| `instance` | `getBackloadNumber` | `()` | `long` | Retrieves `BackloadNumber` property from `ChartDef` |
| `instance` | `isSymbolRecognized` | `()` | `boolean` | Evaluates boolean predicate `isSymbolRecognized` on `ChartDef` |
| `instance` | `setHistoryFrom` | `(arg0: long)` | `void` | Sets `HistoryFrom` configuration/state on `ChartDef` |
| `instance` | `isBacktestDataDef` | `()` | `boolean` | Evaluates boolean predicate `isBacktestDataDef` on `ChartDef` |
| `instance` | `equals` | `(arg0: Object)` | `boolean` | Performs equals operation |
| `instance` | `toString` | `()` | `String` | Converts/serializes representation via `toString` |
| `instance` | `hashCode` | `()` | `int` | Evaluates boolean predicate `hashCode` on `ChartDef` |
| `instance` | `getClass` | `()` | `Class` | Retrieves `Class` property from `ChartDef` |
| `instance` | `notify` | `()` | `void` | Performs notify operation |
| `instance` | `notifyAll` | `()` | `void` | Performs notify all operation |
| `instance` | `wait` | `(arg0: long)` | `void` | Performs wait operation |
| `instance` | `wait` | `(arg0: long, arg1: int)` | `void` | Performs wait operation |
| `instance` | `wait` | `()` | `void` | Performs wait operation |

---

### `DataInfo`
- **Full Qualified Name:** `com.strategyquant.datalib.DataInfo`
- **Primary Job / Responsibility:** Market data abstraction and time-series container (`DataInfo`).

#### Fields
| Scope | Field Name | Type |
| :--- | :--- | :--- |
| `instance` | `barTimeType` | `int` |
| `instance` | `basketId` | `int` |
| `instance` | `brokerId` | `int` |
| `instance` | `connection` | `String` |
| `instance` | `dateFrom` | `long` |
| `instance` | `dateFromStr` | `String` |
| `instance` | `dateTo` | `long` |
| `instance` | `dateToStr` | `String` |
| `instance` | `decimals` | `int` |
| `instance` | `fileHash` | `long` |
| `instance` | `filename` | `String` |
| `instance` | `id` | `int` |
| `instance` | `instrument` | `String` |
| `instance` | `originalSymbol` | `String` |
| `instance` | `removeWeekends` | `boolean` |
| `instance` | `rows` | `int` |
| `instance` | `secondsRecords` | `long` |
| `instance` | `show` | `boolean` |
| `instance` | `source` | `int` |
| `instance` | `sourceDataId` | `int` |
| `instance` | `symbol` | `String` |
| `instance` | `symbolInfo` | `InstrumentInfo` |
| `instance` | `timeframe` | `String` |
| `instance` | `timezone` | `String` |
| `instance` | `totalDays` | `int` |
| `instance` | `uSymbol` | `String` |
| `instance` | `uSymbolName` | `String` |

#### Methods & Functions
| Modifiers | Method Name | Parameter Signatures | Return Type | Functional Description / Job |
| :--- | :--- | :--- | :--- | :--- |
| `instance` | `toString` | `()` | `String` | Converts/serializes representation via `toString` |
| `instance` | `clone` | `()` | `DataInfo` | Performs clone operation |
| `instance` | `clone` | `()` | `DataInfo` | Performs clone operation |
| `instance` | `setFromXML` | `(arg0: Element)` | `void` | Sets `FromXML` configuration/state on `DataInfo` |
| `instance` | `getXML` | `()` | `Element` | Retrieves `XML` property from `DataInfo` |
| `instance` | `equals` | `(arg0: Object)` | `boolean` | Performs equals operation |
| `instance` | `hashCode` | `()` | `int` | Evaluates boolean predicate `hashCode` on `DataInfo` |
| `instance` | `getClass` | `()` | `Class` | Retrieves `Class` property from `DataInfo` |
| `instance` | `notify` | `()` | `void` | Performs notify operation |
| `instance` | `notifyAll` | `()` | `void` | Performs notify all operation |
| `instance` | `wait` | `(arg0: long)` | `void` | Performs wait operation |
| `instance` | `wait` | `(arg0: long, arg1: int)` | `void` | Performs wait operation |
| `instance` | `wait` | `()` | `void` | Performs wait operation |

---

### `DataSeries`
- **Full Qualified Name:** `com.strategyquant.datalib.DataSeries`
- **Primary Job / Responsibility:** Market data abstraction and time-series container (`DataSeries`).

#### Fields
| Scope | Field Name | Type |
| :--- | :--- | :--- |
| `static` | `Log` | `Logger` |

#### Methods & Functions
| Modifiers | Method Name | Parameter Signatures | Return Type | Functional Description / Job |
| :--- | :--- | :--- | :--- | :--- |
| `instance` | `get` | `(arg0: int)` | `double` | Retrieves `` property from `DataSeries` |
| `instance` | `add` | `(arg0: double)` | `void` | Appends/registers element via `add` |
| `instance` | `set` | `(arg0: int, arg1: double)` | `void` | Sets `` configuration/state on `DataSeries` |
| `instance` | `set` | `(arg0: int, arg1: double, arg2: boolean)` | `void` | Sets `` configuration/state on `DataSeries` |
| `instance` | `set` | `(arg0: double)` | `void` | Sets `` configuration/state on `DataSeries` |
| `instance` | `getRounded` | `(arg0: int, arg1: int)` | `double` | Retrieves `Rounded` property from `DataSeries` |
| `instance` | `getRounded` | `(arg0: int)` | `double` | Retrieves `Rounded` property from `DataSeries` |
| `instance` | `addValues` | `(arg0: int)` | `void` | Appends/registers element via `addValues` |
| `instance` | `chartHashCode` | `()` | `int` | Performs chart hash code operation |
| `instance` | `getName` | `()` | `String` | Retrieves `Name` property from `DataSeries` |
| `instance` | `size` | `()` | `int` | Performs size operation |
| `instance` | `setName` | `(arg0: String)` | `void` | Sets `Name` configuration/state on `DataSeries` |
| `instance` | `setName` | `(arg0: String, arg1: ChartDef)` | `void` | Sets `Name` configuration/state on `DataSeries` |
| `instance` | `destroy` | `()` | `void` | Performs destroy operation |
| `instance` | `setColor` | `(arg0: String)` | `void` | Sets `Color` configuration/state on `DataSeries` |
| `instance` | `getInstrumentInfo` | `()` | `InstrumentInfo` | Retrieves `InstrumentInfo` property from `DataSeries` |
| `instance` | `Symbol` | `()` | `String` | Performs symbol operation |
| `instance` | `getIndyStartingBar` | `()` | `int` | Retrieves `IndyStartingBar` property from `DataSeries` |
| `instance` | `setIndyStartingBar` | `(arg0: int)` | `void` | Sets `IndyStartingBar` configuration/state on `DataSeries` |
| `instance` | `getShift` | `()` | `int` | Retrieves `Shift` property from `DataSeries` |
| `instance` | `addChangeListener` | `(arg0: int, arg1: IDataSeriesChangeListener)` | `void` | Appends/registers element via `addChangeListener` |
| `instance` | `setDataComputer` | `(arg0: IDataSeriesComputer)` | `void` | Sets `DataComputer` configuration/state on `DataSeries` |
| `instance` | `specialSize` | `()` | `int` | Performs special size operation |
| `instance` | `addDoubleValues` | `(arg0: int, arg1: double)` | `void` | Appends/registers element via `addDoubleValues` |
| `instance` | `addLongValues` | `(arg0: int, arg1: long)` | `void` | Appends/registers element via `addLongValues` |
| `instance` | `updateComputedUntil` | `(arg0: int)` | `void` | Performs update computed until operation |
| `instance` | `setComputedUntil` | `(arg0: int)` | `void` | Sets `ComputedUntil` configuration/state on `DataSeries` |
| `instance` | `setShift` | `(arg0: int)` | `void` | Sets `Shift` configuration/state on `DataSeries` |
| `instance` | `setLineName` | `(arg0: String)` | `void` | Sets `LineName` configuration/state on `DataSeries` |
| `instance` | `setShowInChart` | `(arg0: boolean)` | `void` | Sets `ShowInChart` configuration/state on `DataSeries` |
| `instance` | `setShowZeroValues` | `(arg0: boolean)` | `void` | Sets `ShowZeroValues` configuration/state on `DataSeries` |
| `instance` | `setChartType` | `(arg0: String)` | `void` | Sets `ChartType` configuration/state on `DataSeries` |
| `instance` | `callDataChangeListeners` | `()` | `void` | Performs call data change listeners operation |
| `instance` | `getColor` | `()` | `String` | Retrieves `Color` property from `DataSeries` |
| `instance` | `isShowInChart` | `()` | `boolean` | Evaluates boolean predicate `isShowInChart` on `DataSeries` |
| `instance` | `isShowZeroValues` | `()` | `boolean` | Evaluates boolean predicate `isShowZeroValues` on `DataSeries` |
| `instance` | `getChartType` | `()` | `String` | Retrieves `ChartType` property from `DataSeries` |
| `instance` | `getLineName` | `()` | `String` | Retrieves `LineName` property from `DataSeries` |
| `instance` | `getComputedUntilIndex` | `()` | `int` | Retrieves `ComputedUntilIndex` property from `DataSeries` |
| `instance` | `_getDouble` | `(arg0: int)` | `double` | Performs get double operation |
| `instance` | `_writeDoubleToOffheapRealIndex` | `(arg0: int, arg1: double)` | `void` | Performs write double to offheap real index operation |
| `instance` | `equals` | `(arg0: Object)` | `boolean` | Performs equals operation |
| `instance` | `toString` | `()` | `String` | Converts/serializes representation via `toString` |
| `instance` | `hashCode` | `()` | `int` | Evaluates boolean predicate `hashCode` on `DataSeries` |
| `instance` | `getClass` | `()` | `Class` | Retrieves `Class` property from `DataSeries` |
| `instance` | `notify` | `()` | `void` | Performs notify operation |
| `instance` | `notifyAll` | `()` | `void` | Performs notify all operation |
| `instance` | `wait` | `(arg0: long)` | `void` | Performs wait operation |
| `instance` | `wait` | `(arg0: long, arg1: int)` | `void` | Performs wait operation |
| `instance` | `wait` | `()` | `void` | Performs wait operation |

---

### `InstrumentInfo`
- **Full Qualified Name:** `com.strategyquant.datalib.InstrumentInfo`
- **Primary Job / Responsibility:** Symbol specifications, pip values, margins, and contract specifications (`InstrumentInfo`).

#### Fields
| Scope | Field Name | Type |
| :--- | :--- | :--- |
| `static` | `Log` | `Logger` |
| `instance` | `alias` | `String` |
| `instance` | `broker` | `int` |
| `instance` | `commissions` | `String` |
| `instance` | `connection` | `String` |
| `instance` | `cot` | `String` |
| `instance` | `country` | `String` |
| `instance` | `dataType` | `int` |
| `instance` | `dateFrom` | `long` |
| `instance` | `dateTo` | `long` |
| `instance` | `decimals` | `int` |
| `instance` | `defaultSlippage` | `double` |
| `instance` | `defaultSpread` | `double` |
| `instance` | `description` | `String` |
| `instance` | `exchange` | `String` |
| `instance` | `filename` | `String` |
| `instance` | `instrument` | `String` |
| `instance` | `minDistance` | `double` |
| `instance` | `orderSizeMultiplier` | `double` |
| `instance` | `orderSizeStep` | `double` |
| `instance` | `pointValue` | `double` |
| `instance` | `recognizedFromOrders` | `boolean` |
| `instance` | `rows` | `int` |
| `instance` | `sector` | `String` |
| `instance` | `swap` | `String` |
| `instance` | `tickSize` | `double` |
| `instance` | `tickStep` | `double` |
| `instance` | `tickValueInMoney` | `double` |
| `instance` | `timeframe` | `String` |
| `instance` | `totalDays` | `int` |

#### Methods & Functions
| Modifiers | Method Name | Parameter Signatures | Return Type | Functional Description / Job |
| :--- | :--- | :--- | :--- | :--- |
| `instance` | `clone` | `()` | `Object` | Performs clone operation |
| `instance` | `clone` | `()` | `Object` | Performs clone operation |
| `instance` | `setFromXML` | `(arg0: Element)` | `void` | Sets `FromXML` configuration/state on `InstrumentInfo` |
| `instance` | `getXML` | `()` | `Element` | Retrieves `XML` property from `InstrumentInfo` |
| `instance` | `equals` | `(arg0: Object)` | `boolean` | Performs equals operation |
| `instance` | `toString` | `()` | `String` | Converts/serializes representation via `toString` |
| `instance` | `hashCode` | `()` | `int` | Evaluates boolean predicate `hashCode` on `InstrumentInfo` |
| `instance` | `getClass` | `()` | `Class` | Retrieves `Class` property from `InstrumentInfo` |
| `instance` | `notify` | `()` | `void` | Performs notify operation |
| `instance` | `notifyAll` | `()` | `void` | Performs notify all operation |
| `instance` | `wait` | `(arg0: long)` | `void` | Performs wait operation |
| `instance` | `wait` | `(arg0: long, arg1: int)` | `void` | Performs wait operation |
| `instance` | `wait` | `()` | `void` | Performs wait operation |

---

### `SymbolData`
- **Full Qualified Name:** `com.strategyquant.datalib.SymbolData`
- **Primary Job / Responsibility:** Market data abstraction and time-series container (`SymbolData`).

#### Fields
| Scope | Field Name | Type |
| :--- | :--- | :--- |
| `instance` | `category` | `String` |
| `instance` | `dateFrom` | `long` |
| `instance` | `dateFromM1` | `long` |
| `instance` | `decimals` | `int` |
| `instance` | `defaultSlippage` | `double` |
| `instance` | `defaultSpread` | `double` |
| `instance` | `instrumentType` | `byte` |
| `instance` | `name` | `String` |
| `instance` | `subcategory` | `String` |
| `instance` | `symbol` | `String` |
| `instance` | `tickSize` | `double` |
| `instance` | `tickStep` | `double` |
| `instance` | `tickValue` | `double` |

#### Methods & Functions
| Modifiers | Method Name | Parameter Signatures | Return Type | Functional Description / Job |
| :--- | :--- | :--- | :--- | :--- |
| `instance` | `equals` | `(arg0: Object)` | `boolean` | Performs equals operation |
| `instance` | `toString` | `()` | `String` | Converts/serializes representation via `toString` |
| `instance` | `hashCode` | `()` | `int` | Evaluates boolean predicate `hashCode` on `SymbolData` |
| `instance` | `getClass` | `()` | `Class` | Retrieves `Class` property from `SymbolData` |
| `instance` | `notify` | `()` | `void` | Performs notify operation |
| `instance` | `notifyAll` | `()` | `void` | Performs notify all operation |
| `instance` | `wait` | `(arg0: long)` | `void` | Performs wait operation |
| `instance` | `wait` | `(arg0: long, arg1: int)` | `void` | Performs wait operation |
| `instance` | `wait` | `()` | `void` | Performs wait operation |

---

### `TickEvent`
- **Full Qualified Name:** `com.strategyquant.datalib.TickEvent`
- **Primary Job / Responsibility:** Market data abstraction and time-series container (`TickEvent`).

#### Methods & Functions
| Modifiers | Method Name | Parameter Signatures | Return Type | Functional Description / Job |
| :--- | :--- | :--- | :--- | :--- |
| `instance` | `toString` | `()` | `String` | Converts/serializes representation via `toString` |
| `instance` | `set` | `(arg0: TickEvent)` | `void` | Sets `` configuration/state on `TickEvent` |
| `instance` | `set` | `(arg0: long, arg1: int, arg2: int, arg3: double, arg4: double, arg5: double, arg6: long, arg7: long, arg8: boolean, arg9: boolean)` | `void` | Sets `` configuration/state on `TickEvent` |
| `instance` | `set` | `(arg0: long, arg1: int, arg2: int, arg3: double, arg4: double, arg5: double, arg6: long, arg7: boolean, arg8: boolean)` | `void` | Sets `` configuration/state on `TickEvent` |
| `instance` | `getTime` | `()` | `long` | Retrieves `Time` property from `TickEvent` |
| `instance` | `setTime` | `(arg0: long)` | `void` | Sets `Time` configuration/state on `TickEvent` |
| `instance` | `isSet` | `()` | `boolean` | Evaluates boolean predicate `isSet` on `TickEvent` |
| `instance` | `setAsk` | `(arg0: double)` | `void` | Sets `Ask` configuration/state on `TickEvent` |
| `instance` | `setBid` | `(arg0: double)` | `void` | Sets `Bid` configuration/state on `TickEvent` |
| `instance` | `getConnectionHash` | `()` | `int` | Retrieves `ConnectionHash` property from `TickEvent` |
| `instance` | `getSymbolHash` | `()` | `int` | Retrieves `SymbolHash` property from `TickEvent` |
| `instance` | `copyValues` | `(arg0: TickEvent)` | `void` | Performs copy values operation |
| `instance` | `getBid` | `()` | `double` | Retrieves `Bid` property from `TickEvent` |
| `instance` | `getAsk` | `()` | `double` | Retrieves `Ask` property from `TickEvent` |
| `instance` | `getVolume` | `()` | `double` | Retrieves `Volume` property from `TickEvent` |
| `instance` | `isBarOpen` | `()` | `boolean` | Evaluates boolean predicate `isBarOpen` on `TickEvent` |
| `instance` | `isBarClose` | `()` | `boolean` | Evaluates boolean predicate `isBarClose` on `TickEvent` |
| `instance` | `getSessionStartTime` | `()` | `long` | Retrieves `SessionStartTime` property from `TickEvent` |
| `instance` | `setSessionStartTime` | `(arg0: long)` | `void` | Sets `SessionStartTime` configuration/state on `TickEvent` |
| `instance` | `setSessionEndTime` | `(arg0: long)` | `void` | Sets `SessionEndTime` configuration/state on `TickEvent` |
| `instance` | `setIsSet` | `(arg0: boolean)` | `void` | Sets `IsSet` configuration/state on `TickEvent` |
| `instance` | `setSymbolHash` | `(arg0: int)` | `void` | Sets `SymbolHash` configuration/state on `TickEvent` |
| `instance` | `getSessionEndTime` | `()` | `long` | Retrieves `SessionEndTime` property from `TickEvent` |
| `instance` | `setConnectionHash` | `(arg0: int)` | `void` | Sets `ConnectionHash` configuration/state on `TickEvent` |
| `instance` | `setVolume` | `(arg0: double)` | `void` | Sets `Volume` configuration/state on `TickEvent` |
| `instance` | `equals` | `(arg0: Object)` | `boolean` | Performs equals operation |
| `instance` | `hashCode` | `()` | `int` | Evaluates boolean predicate `hashCode` on `TickEvent` |
| `instance` | `getClass` | `()` | `Class` | Retrieves `Class` property from `TickEvent` |
| `instance` | `notify` | `()` | `void` | Performs notify operation |
| `instance` | `notifyAll` | `()` | `void` | Performs notify all operation |
| `instance` | `wait` | `(arg0: long)` | `void` | Performs wait operation |
| `instance` | `wait` | `(arg0: long, arg1: int)` | `void` | Performs wait operation |
| `instance` | `wait` | `()` | `void` | Performs wait operation |

---

### `TimeframeManager`
- **Full Qualified Name:** `com.strategyquant.datalib.TimeframeManager`
- **Primary Job / Responsibility:** Market data abstraction and time-series container (`TimeframeManager`).

#### Fields
| Scope | Field Name | Type |
| :--- | :--- | :--- |
| `static` | `Log` | `Logger` |
| `static` | `PRECISION_BASE_TF` | `int` |
| `static` | `PRECISION_SELECTED_TF` | `int` |
| `static` | `TF_D1` | `String` |
| `static` | `TF_H1` | `String` |
| `static` | `TF_H12` | `String` |
| `static` | `TF_H2` | `String` |
| `static` | `TF_H3` | `String` |
| `static` | `TF_H4` | `String` |
| `static` | `TF_H6` | `String` |
| `static` | `TF_H8` | `String` |
| `static` | `TF_INTRADAY` | `String` |
| `static` | `TF_INT_UNKNOWN` | `int` |
| `static` | `TF_M1` | `String` |
| `static` | `TF_M15` | `String` |
| `static` | `TF_M3` | `String` |
| `static` | `TF_M30` | `String` |
| `static` | `TF_M5` | `String` |
| `static` | `TF_MONTHLY` | `String` |
| `static` | `TF_TICK` | `String` |
| `static` | `TF_UNKNOWN` | `String` |
| `static` | `TF_WEEKLY` | `String` |
| `static` | `filePath` | `String` |

#### Methods & Functions
| Modifiers | Method Name | Parameter Signatures | Return Type | Functional Description / Job |
| :--- | :--- | :--- | :--- | :--- |
| `instance` | `equals` | `(arg0: Object)` | `boolean` | Performs equals operation |
| `instance` | `toString` | `()` | `String` | Converts/serializes representation via `toString` |
| `instance` | `hashCode` | `()` | `int` | Evaluates boolean predicate `hashCode` on `TimeframeManager` |
| `instance` | `getClass` | `()` | `Class` | Retrieves `Class` property from `TimeframeManager` |
| `instance` | `notify` | `()` | `void` | Performs notify operation |
| `instance` | `notifyAll` | `()` | `void` | Performs notify all operation |
| `instance` | `wait` | `(arg0: long)` | `void` | Performs wait operation |
| `instance` | `wait` | `(arg0: long, arg1: int)` | `void` | Performs wait operation |
| `instance` | `wait` | `()` | `void` | Performs wait operation |
| `static` | `getInstance` | `()` | `TimeframeManager` | Retrieves `Instance` property from `TimeframeManager` |
| `static` | `getMillis` | `(arg0: String)` | `long` | Retrieves `Millis` property from `TimeframeManager` |
| `static` | `M` | `(arg0: int)` | `String` | Performs m operation |
| `static` | `TFExists` | `(arg0: String)` | `boolean` | Performs tf exists operation |
| `static` | `addTimeframe` | `(arg0: String)` | `void` | Appends/registers element via `addTimeframe` |
| `static` | `getTimeframes` | `()` | `ArrayList` | Retrieves `Timeframes` property from `TimeframeManager` |
| `static` | `getPredefinedTimeframes` | `()` | `ArrayList` | Retrieves `PredefinedTimeframes` property from `TimeframeManager` |
| `static` | `translateToMTConstant` | `(arg0: String)` | `int` | Performs translate to mt constant operation |
| `static` | `translateSQ3TFToString` | `(arg0: int)` | `String` | Performs translate sq 3 tf to string operation |
| `static` | `isTimeFrameLessThen` | `(arg0: String, arg1: String)` | `boolean` | Evaluates boolean predicate `isTimeFrameLessThen` on `TimeframeManager` |
| `static` | `getTFHash` | `(arg0: String)` | `long` | Retrieves `TFHash` property from `TimeframeManager` |
| `static` | `getTFName` | `(arg0: long)` | `String` | Retrieves `TFName` property from `TimeframeManager` |

---

### `TradingException`
- **Full Qualified Name:** `com.strategyquant.datalib.TradingException`
- **Primary Job / Responsibility:** Market data abstraction and time-series container (`TradingException`).

#### Fields
| Scope | Field Name | Type |
| :--- | :--- | :--- |
| `static` | `IndicatorCalculationFailed` | `int` |

#### Methods & Functions
| Modifiers | Method Name | Parameter Signatures | Return Type | Functional Description / Job |
| :--- | :--- | :--- | :--- | :--- |
| `instance` | `addCall` | `(arg0: String)` | `TradingException` | Appends/registers element via `addCall` |
| `instance` | `getErrorCode` | `()` | `int` | Retrieves `ErrorCode` property from `TradingException` |
| `instance` | `printStackTrace` | `()` | `void` | Performs print stack trace operation |
| `instance` | `printStackTrace` | `(arg0: PrintWriter)` | `void` | Performs print stack trace operation |
| `instance` | `printStackTrace` | `(arg0: PrintStream)` | `void` | Performs print stack trace operation |
| `instance` | `getStackTrace` | `()` | `StackTraceElement[]` | Retrieves `StackTrace` property from `TradingException` |
| `instance` | `fillInStackTrace` | `()` | `Throwable` | Performs fill in stack trace operation |
| `instance` | `getCause` | `()` | `Throwable` | Retrieves `Cause` property from `TradingException` |
| `instance` | `initCause` | `(arg0: Throwable)` | `Throwable` | Instantiates/initializes `initCause` resource |
| `instance` | `toString` | `()` | `String` | Converts/serializes representation via `toString` |
| `instance` | `getMessage` | `()` | `String` | Retrieves `Message` property from `TradingException` |
| `instance` | `getSuppressed` | `()` | `Throwable[]` | Retrieves `Suppressed` property from `TradingException` |
| `instance` | `getLocalizedMessage` | `()` | `String` | Retrieves `LocalizedMessage` property from `TradingException` |
| `instance` | `setStackTrace` | `(arg0: StackTraceElement[])` | `void` | Sets `StackTrace` configuration/state on `TradingException` |
| `instance` | `addSuppressed` | `(arg0: Throwable)` | `void` | Appends/registers element via `addSuppressed` |
| `instance` | `equals` | `(arg0: Object)` | `boolean` | Performs equals operation |
| `instance` | `hashCode` | `()` | `int` | Evaluates boolean predicate `hashCode` on `TradingException` |
| `instance` | `getClass` | `()` | `Class` | Retrieves `Class` property from `TradingException` |
| `instance` | `notify` | `()` | `void` | Performs notify operation |
| `instance` | `notifyAll` | `()` | `void` | Performs notify all operation |
| `instance` | `wait` | `(arg0: long)` | `void` | Performs wait operation |
| `instance` | `wait` | `(arg0: long, arg1: int)` | `void` | Performs wait operation |
| `instance` | `wait` | `()` | `void` | Performs wait operation |

---

### `UpdateEventTypes`
- **Full Qualified Name:** `com.strategyquant.datalib.UpdateEventTypes`
- **Primary Job / Responsibility:** Market data abstraction and time-series container (`UpdateEventTypes`).

#### Fields
| Scope | Field Name | Type |
| :--- | :--- | :--- |
| `static` | `BarClose` | `int` |
| `static` | `BarOpen` | `int` |
| `static` | `BarTick` | `int` |
| `static` | `BarTickWithCloseTick` | `int` |
| `static` | `Multiple` | `int` |
| `static` | `None` | `int` |
| `static` | `OrderFilled` | `int` |
| `static` | `Unknown` | `int` |

#### Methods & Functions
| Modifiers | Method Name | Parameter Signatures | Return Type | Functional Description / Job |
| :--- | :--- | :--- | :--- | :--- |
| `instance` | `equals` | `(arg0: Object)` | `boolean` | Performs equals operation |
| `instance` | `toString` | `()` | `String` | Converts/serializes representation via `toString` |
| `instance` | `hashCode` | `()` | `int` | Evaluates boolean predicate `hashCode` on `UpdateEventTypes` |
| `instance` | `getClass` | `()` | `Class` | Retrieves `Class` property from `UpdateEventTypes` |
| `instance` | `notify` | `()` | `void` | Performs notify operation |
| `instance` | `notifyAll` | `()` | `void` | Performs notify all operation |
| `instance` | `wait` | `(arg0: long)` | `void` | Performs wait operation |
| `instance` | `wait` | `(arg0: long, arg1: int)` | `void` | Performs wait operation |
| `instance` | `wait` | `()` | `void` | Performs wait operation |

---

## Subsystem: `bartype`

### `BarType`
- **Full Qualified Name:** `com.strategyquant.datalib.bartype.BarType`
- **Primary Job / Responsibility:** Time-series price history, OHLCV bar storage, and chart data management (`BarType`).

#### Methods & Functions
| Modifiers | Method Name | Parameter Signatures | Return Type | Functional Description / Job |
| :--- | :--- | :--- | :--- | :--- |
| `instance` | `toString` | `(arg0: String)` | `String` | Converts/serializes representation via `toString` |
| `instance` | `toString` | `()` | `String` | Converts/serializes representation via `toString` |
| `instance` | `clone` | `()` | `BarType` | Performs clone operation |
| `instance` | `clone` | `()` | `BarType` | Performs clone operation |
| `instance` | `clone` | `(arg0: String)` | `BarType` | Performs clone operation |
| `instance` | `getTimeframe` | `()` | `String` | Retrieves `Timeframe` property from `BarType` |
| `instance` | `processTick` | `(arg0: TickEvent, arg1: BarTypeStatus, arg2: int)` | `void` | Performs process tick operation |
| `instance` | `getBarTimeType` | `()` | `int` | Retrieves `BarTimeType` property from `BarType` |
| `instance` | `estimateStartDate` | `(arg0: int, arg1: long)` | `long` | Performs estimate start date operation |
| `instance` | `checkCanBeComputedFrom` | `(arg0: String)` | `String` | Performs check can be computed from operation |
| `instance` | `getPeriodInMS` | `()` | `int` | Retrieves `PeriodInMS` property from `BarType` |
| `instance` | `processTickImplementation` | `(arg0: TickEvent, arg1: BarTypeStatus, arg2: int)` | `void` | Performs process tick implementation operation |
| `instance` | `isTickBar` | `()` | `boolean` | Evaluates boolean predicate `isTickBar` on `BarType` |
| `instance` | `getBaseTF` | `()` | `String` | Retrieves `BaseTF` property from `BarType` |
| `instance` | `getTickTF` | `()` | `String` | Retrieves `TickTF` property from `BarType` |
| `instance` | `checkTimeframeIsSupported` | `(arg0: String)` | `boolean` | Performs check timeframe is supported operation |
| `instance` | `toStr` | `()` | `String` | Converts/serializes representation via `toStr` |
| `instance` | `equals` | `(arg0: Object)` | `boolean` | Performs equals operation |
| `instance` | `hashCode` | `()` | `int` | Evaluates boolean predicate `hashCode` on `BarType` |
| `instance` | `getClass` | `()` | `Class` | Retrieves `Class` property from `BarType` |
| `instance` | `notify` | `()` | `void` | Performs notify operation |
| `instance` | `notifyAll` | `()` | `void` | Performs notify all operation |
| `instance` | `wait` | `(arg0: long)` | `void` | Performs wait operation |
| `instance` | `wait` | `(arg0: long, arg1: int)` | `void` | Performs wait operation |
| `instance` | `wait` | `()` | `void` | Performs wait operation |

---

### `BarTypeFactory`
- **Full Qualified Name:** `com.strategyquant.datalib.bartype.BarTypeFactory`
- **Primary Job / Responsibility:** Time-series price history, OHLCV bar storage, and chart data management (`BarTypeFactory`).

#### Fields
| Scope | Field Name | Type |
| :--- | :--- | :--- |
| `static` | `Log` | `Logger` |

#### Methods & Functions
| Modifiers | Method Name | Parameter Signatures | Return Type | Functional Description / Job |
| :--- | :--- | :--- | :--- | :--- |
| `instance` | `equals` | `(arg0: Object)` | `boolean` | Performs equals operation |
| `instance` | `toString` | `()` | `String` | Converts/serializes representation via `toString` |
| `instance` | `hashCode` | `()` | `int` | Evaluates boolean predicate `hashCode` on `BarTypeFactory` |
| `instance` | `getClass` | `()` | `Class` | Retrieves `Class` property from `BarTypeFactory` |
| `instance` | `notify` | `()` | `void` | Performs notify operation |
| `instance` | `notifyAll` | `()` | `void` | Performs notify all operation |
| `instance` | `wait` | `(arg0: long)` | `void` | Performs wait operation |
| `instance` | `wait` | `(arg0: long, arg1: int)` | `void` | Performs wait operation |
| `instance` | `wait` | `()` | `void` | Performs wait operation |
| `static` | `getBarType` | `(arg0: String, arg1: int)` | `BarType` | Retrieves `BarType` property from `BarTypeFactory` |
| `static` | `checkTimeframeIsValid` | `(arg0: String)` | `void` | Performs check timeframe is valid operation |

---

### `BarTypeStatus`
- **Full Qualified Name:** `com.strategyquant.datalib.bartype.BarTypeStatus`
- **Primary Job / Responsibility:** Time-series price history, OHLCV bar storage, and chart data management (`BarTypeStatus`).

#### Fields
| Scope | Field Name | Type |
| :--- | :--- | :--- |
| `static` | `EXISTING_BAR` | `int` |
| `static` | `NEW_BAR` | `int` |
| `static` | `NOT_IN_SESSION` | `int` |
| `instance` | `barTime` | `long` |
| `instance` | `convertingToHigherTF` | `boolean` |
| `instance` | `sessionStatus` | `SessionStatus` |
| `instance` | `status` | `int` |

#### Methods & Functions
| Modifiers | Method Name | Parameter Signatures | Return Type | Functional Description / Job |
| :--- | :--- | :--- | :--- | :--- |
| `instance` | `equals` | `(arg0: Object)` | `boolean` | Performs equals operation |
| `instance` | `toString` | `()` | `String` | Converts/serializes representation via `toString` |
| `instance` | `hashCode` | `()` | `int` | Evaluates boolean predicate `hashCode` on `BarTypeStatus` |
| `instance` | `getClass` | `()` | `Class` | Retrieves `Class` property from `BarTypeStatus` |
| `instance` | `notify` | `()` | `void` | Performs notify operation |
| `instance` | `notifyAll` | `()` | `void` | Performs notify all operation |
| `instance` | `wait` | `(arg0: long)` | `void` | Performs wait operation |
| `instance` | `wait` | `(arg0: long, arg1: int)` | `void` | Performs wait operation |
| `instance` | `wait` | `()` | `void` | Performs wait operation |

---

### `TimeframeNotSupportedException`
- **Full Qualified Name:** `com.strategyquant.datalib.bartype.TimeframeNotSupportedException`
- **Primary Job / Responsibility:** Time-series price history, OHLCV bar storage, and chart data management (`TimeframeNotSupportedException`).

#### Methods & Functions
| Modifiers | Method Name | Parameter Signatures | Return Type | Functional Description / Job |
| :--- | :--- | :--- | :--- | :--- |
| `instance` | `printStackTrace` | `()` | `void` | Performs print stack trace operation |
| `instance` | `printStackTrace` | `(arg0: PrintWriter)` | `void` | Performs print stack trace operation |
| `instance` | `printStackTrace` | `(arg0: PrintStream)` | `void` | Performs print stack trace operation |
| `instance` | `getStackTrace` | `()` | `StackTraceElement[]` | Retrieves `StackTrace` property from `TimeframeNotSupportedException` |
| `instance` | `fillInStackTrace` | `()` | `Throwable` | Performs fill in stack trace operation |
| `instance` | `getCause` | `()` | `Throwable` | Retrieves `Cause` property from `TimeframeNotSupportedException` |
| `instance` | `initCause` | `(arg0: Throwable)` | `Throwable` | Instantiates/initializes `initCause` resource |
| `instance` | `toString` | `()` | `String` | Converts/serializes representation via `toString` |
| `instance` | `getMessage` | `()` | `String` | Retrieves `Message` property from `TimeframeNotSupportedException` |
| `instance` | `getSuppressed` | `()` | `Throwable[]` | Retrieves `Suppressed` property from `TimeframeNotSupportedException` |
| `instance` | `getLocalizedMessage` | `()` | `String` | Retrieves `LocalizedMessage` property from `TimeframeNotSupportedException` |
| `instance` | `setStackTrace` | `(arg0: StackTraceElement[])` | `void` | Sets `StackTrace` configuration/state on `TimeframeNotSupportedException` |
| `instance` | `addSuppressed` | `(arg0: Throwable)` | `void` | Appends/registers element via `addSuppressed` |
| `instance` | `equals` | `(arg0: Object)` | `boolean` | Performs equals operation |
| `instance` | `hashCode` | `()` | `int` | Evaluates boolean predicate `hashCode` on `TimeframeNotSupportedException` |
| `instance` | `getClass` | `()` | `Class` | Retrieves `Class` property from `TimeframeNotSupportedException` |
| `instance` | `notify` | `()` | `void` | Performs notify operation |
| `instance` | `notifyAll` | `()` | `void` | Performs notify all operation |
| `instance` | `wait` | `(arg0: long)` | `void` | Performs wait operation |
| `instance` | `wait` | `(arg0: long, arg1: int)` | `void` | Performs wait operation |
| `instance` | `wait` | `()` | `void` | Performs wait operation |

---

### `FuturesIntradayBar`
- **Full Qualified Name:** `com.strategyquant.datalib.bartype.impl.FuturesIntradayBar`
- **Primary Job / Responsibility:** Time-series price history, OHLCV bar storage, and chart data management (`FuturesIntradayBar`).

#### Fields
| Scope | Field Name | Type |
| :--- | :--- | :--- |
| `static` | `Log` | `Logger` |

#### Methods & Functions
| Modifiers | Method Name | Parameter Signatures | Return Type | Functional Description / Job |
| :--- | :--- | :--- | :--- | :--- |
| `instance` | `clone` | `()` | `BarType` | Performs clone operation |
| `instance` | `clone` | `()` | `BarType` | Performs clone operation |
| `instance` | `clone` | `(arg0: String)` | `BarType` | Performs clone operation |
| `instance` | `estimateStartDate` | `(arg0: int, arg1: long)` | `long` | Performs estimate start date operation |
| `instance` | `checkCanBeComputedFrom` | `(arg0: String)` | `String` | Performs check can be computed from operation |
| `instance` | `getPeriodInMS` | `()` | `int` | Retrieves `PeriodInMS` property from `FuturesIntradayBar` |
| `instance` | `processTickImplementation` | `(arg0: TickEvent, arg1: BarTypeStatus, arg2: int)` | `void` | Performs process tick implementation operation |
| `instance` | `isTickBar` | `()` | `boolean` | Evaluates boolean predicate `isTickBar` on `FuturesIntradayBar` |
| `instance` | `getBaseTF` | `()` | `String` | Retrieves `BaseTF` property from `FuturesIntradayBar` |
| `instance` | `getTickTF` | `()` | `String` | Retrieves `TickTF` property from `FuturesIntradayBar` |
| `instance` | `checkTimeframeIsSupported` | `(arg0: String)` | `boolean` | Performs check timeframe is supported operation |
| `instance` | `toString` | `(arg0: String)` | `String` | Converts/serializes representation via `toString` |
| `instance` | `toString` | `()` | `String` | Converts/serializes representation via `toString` |
| `instance` | `getTimeframe` | `()` | `String` | Retrieves `Timeframe` property from `FuturesIntradayBar` |
| `instance` | `processTick` | `(arg0: TickEvent, arg1: BarTypeStatus, arg2: int)` | `void` | Performs process tick operation |
| `instance` | `getBarTimeType` | `()` | `int` | Retrieves `BarTimeType` property from `FuturesIntradayBar` |
| `instance` | `toStr` | `()` | `String` | Converts/serializes representation via `toStr` |
| `instance` | `equals` | `(arg0: Object)` | `boolean` | Performs equals operation |
| `instance` | `hashCode` | `()` | `int` | Evaluates boolean predicate `hashCode` on `FuturesIntradayBar` |
| `instance` | `getClass` | `()` | `Class` | Retrieves `Class` property from `FuturesIntradayBar` |
| `instance` | `notify` | `()` | `void` | Performs notify operation |
| `instance` | `notifyAll` | `()` | `void` | Performs notify all operation |
| `instance` | `wait` | `(arg0: long)` | `void` | Performs wait operation |
| `instance` | `wait` | `(arg0: long, arg1: int)` | `void` | Performs wait operation |
| `instance` | `wait` | `()` | `void` | Performs wait operation |

---

### `FuturesTimeBar`
- **Full Qualified Name:** `com.strategyquant.datalib.bartype.impl.FuturesTimeBar`
- **Primary Job / Responsibility:** Time-series price history, OHLCV bar storage, and chart data management (`FuturesTimeBar`).

#### Fields
| Scope | Field Name | Type |
| :--- | :--- | :--- |
| `static` | `Log` | `Logger` |
| `instance` | `LoadAsIs` | `boolean` |
| `instance` | `MetaTraderEngineUsed` | `boolean` |

#### Methods & Functions
| Modifiers | Method Name | Parameter Signatures | Return Type | Functional Description / Job |
| :--- | :--- | :--- | :--- | :--- |
| `instance` | `clone` | `()` | `BarType` | Performs clone operation |
| `instance` | `clone` | `()` | `BarType` | Performs clone operation |
| `instance` | `clone` | `(arg0: String)` | `BarType` | Performs clone operation |
| `instance` | `processTickImplementation` | `(arg0: TickEvent, arg1: BarTypeStatus, arg2: int)` | `void` | Performs process tick implementation operation |
| `instance` | `getPeriod` | `()` | `long` | Retrieves `Period` property from `FuturesTimeBar` |
| `instance` | `estimateStartDate` | `(arg0: int, arg1: long)` | `long` | Performs estimate start date operation |
| `instance` | `checkCanBeComputedFrom` | `(arg0: String)` | `String` | Performs check can be computed from operation |
| `instance` | `getPeriodInMS` | `()` | `int` | Retrieves `PeriodInMS` property from `FuturesTimeBar` |
| `instance` | `isTickBar` | `()` | `boolean` | Evaluates boolean predicate `isTickBar` on `FuturesTimeBar` |
| `instance` | `getBaseTF` | `()` | `String` | Retrieves `BaseTF` property from `FuturesTimeBar` |
| `instance` | `getTickTF` | `()` | `String` | Retrieves `TickTF` property from `FuturesTimeBar` |
| `instance` | `checkTimeframeIsSupported` | `(arg0: String)` | `boolean` | Performs check timeframe is supported operation |
| `instance` | `getPeriodInSeconds` | `(arg0: String, arg1: boolean)` | `long` | Retrieves `PeriodInSeconds` property from `FuturesTimeBar` |
| `instance` | `getPeriodMillis` | `()` | `long` | Retrieves `PeriodMillis` property from `FuturesTimeBar` |
| `instance` | `toString` | `(arg0: String)` | `String` | Converts/serializes representation via `toString` |
| `instance` | `toString` | `()` | `String` | Converts/serializes representation via `toString` |
| `instance` | `getTimeframe` | `()` | `String` | Retrieves `Timeframe` property from `FuturesTimeBar` |
| `instance` | `processTick` | `(arg0: TickEvent, arg1: BarTypeStatus, arg2: int)` | `void` | Performs process tick operation |
| `instance` | `getBarTimeType` | `()` | `int` | Retrieves `BarTimeType` property from `FuturesTimeBar` |
| `instance` | `toStr` | `()` | `String` | Converts/serializes representation via `toStr` |
| `instance` | `equals` | `(arg0: Object)` | `boolean` | Performs equals operation |
| `instance` | `hashCode` | `()` | `int` | Evaluates boolean predicate `hashCode` on `FuturesTimeBar` |
| `instance` | `getClass` | `()` | `Class` | Retrieves `Class` property from `FuturesTimeBar` |
| `instance` | `notify` | `()` | `void` | Performs notify operation |
| `instance` | `notifyAll` | `()` | `void` | Performs notify all operation |
| `instance` | `wait` | `(arg0: long)` | `void` | Performs wait operation |
| `instance` | `wait` | `(arg0: long, arg1: int)` | `void` | Performs wait operation |
| `instance` | `wait` | `()` | `void` | Performs wait operation |

---

### `FxIntradayBar`
- **Full Qualified Name:** `com.strategyquant.datalib.bartype.impl.FxIntradayBar`
- **Primary Job / Responsibility:** Time-series price history, OHLCV bar storage, and chart data management (`FxIntradayBar`).

#### Fields
| Scope | Field Name | Type |
| :--- | :--- | :--- |
| `static` | `Log` | `Logger` |

#### Methods & Functions
| Modifiers | Method Name | Parameter Signatures | Return Type | Functional Description / Job |
| :--- | :--- | :--- | :--- | :--- |
| `instance` | `clone` | `()` | `BarType` | Performs clone operation |
| `instance` | `clone` | `()` | `BarType` | Performs clone operation |
| `instance` | `clone` | `(arg0: String)` | `BarType` | Performs clone operation |
| `instance` | `estimateStartDate` | `(arg0: int, arg1: long)` | `long` | Performs estimate start date operation |
| `instance` | `checkCanBeComputedFrom` | `(arg0: String)` | `String` | Performs check can be computed from operation |
| `instance` | `getPeriodInMS` | `()` | `int` | Retrieves `PeriodInMS` property from `FxIntradayBar` |
| `instance` | `processTickImplementation` | `(arg0: TickEvent, arg1: BarTypeStatus, arg2: int)` | `void` | Performs process tick implementation operation |
| `instance` | `isTickBar` | `()` | `boolean` | Evaluates boolean predicate `isTickBar` on `FxIntradayBar` |
| `instance` | `getBaseTF` | `()` | `String` | Retrieves `BaseTF` property from `FxIntradayBar` |
| `instance` | `getTickTF` | `()` | `String` | Retrieves `TickTF` property from `FxIntradayBar` |
| `instance` | `checkTimeframeIsSupported` | `(arg0: String)` | `boolean` | Performs check timeframe is supported operation |
| `instance` | `toString` | `(arg0: String)` | `String` | Converts/serializes representation via `toString` |
| `instance` | `toString` | `()` | `String` | Converts/serializes representation via `toString` |
| `instance` | `getTimeframe` | `()` | `String` | Retrieves `Timeframe` property from `FxIntradayBar` |
| `instance` | `processTick` | `(arg0: TickEvent, arg1: BarTypeStatus, arg2: int)` | `void` | Performs process tick operation |
| `instance` | `getBarTimeType` | `()` | `int` | Retrieves `BarTimeType` property from `FxIntradayBar` |
| `instance` | `toStr` | `()` | `String` | Converts/serializes representation via `toStr` |
| `instance` | `equals` | `(arg0: Object)` | `boolean` | Performs equals operation |
| `instance` | `hashCode` | `()` | `int` | Evaluates boolean predicate `hashCode` on `FxIntradayBar` |
| `instance` | `getClass` | `()` | `Class` | Retrieves `Class` property from `FxIntradayBar` |
| `instance` | `notify` | `()` | `void` | Performs notify operation |
| `instance` | `notifyAll` | `()` | `void` | Performs notify all operation |
| `instance` | `wait` | `(arg0: long)` | `void` | Performs wait operation |
| `instance` | `wait` | `(arg0: long, arg1: int)` | `void` | Performs wait operation |
| `instance` | `wait` | `()` | `void` | Performs wait operation |

---

### `FxTimeBar`
- **Full Qualified Name:** `com.strategyquant.datalib.bartype.impl.FxTimeBar`
- **Primary Job / Responsibility:** Time-series price history, OHLCV bar storage, and chart data management (`FxTimeBar`).

#### Fields
| Scope | Field Name | Type |
| :--- | :--- | :--- |
| `static` | `Log` | `Logger` |

#### Methods & Functions
| Modifiers | Method Name | Parameter Signatures | Return Type | Functional Description / Job |
| :--- | :--- | :--- | :--- | :--- |
| `instance` | `clone` | `()` | `BarType` | Performs clone operation |
| `instance` | `clone` | `()` | `BarType` | Performs clone operation |
| `instance` | `clone` | `(arg0: String)` | `BarType` | Performs clone operation |
| `instance` | `processTickImplementation` | `(arg0: TickEvent, arg1: BarTypeStatus, arg2: int)` | `void` | Performs process tick implementation operation |
| `instance` | `getPeriod` | `()` | `long` | Retrieves `Period` property from `FxTimeBar` |
| `instance` | `estimateStartDate` | `(arg0: int, arg1: long)` | `long` | Performs estimate start date operation |
| `instance` | `checkCanBeComputedFrom` | `(arg0: String)` | `String` | Performs check can be computed from operation |
| `instance` | `getPeriodInMS` | `()` | `int` | Retrieves `PeriodInMS` property from `FxTimeBar` |
| `instance` | `isTickBar` | `()` | `boolean` | Evaluates boolean predicate `isTickBar` on `FxTimeBar` |
| `instance` | `getBaseTF` | `()` | `String` | Retrieves `BaseTF` property from `FxTimeBar` |
| `instance` | `getTickTF` | `()` | `String` | Retrieves `TickTF` property from `FxTimeBar` |
| `instance` | `checkTimeframeIsSupported` | `(arg0: String)` | `boolean` | Performs check timeframe is supported operation |
| `instance` | `getPeriodInSeconds` | `(arg0: String, arg1: boolean)` | `long` | Retrieves `PeriodInSeconds` property from `FxTimeBar` |
| `instance` | `getPeriodMillis` | `()` | `long` | Retrieves `PeriodMillis` property from `FxTimeBar` |
| `instance` | `toString` | `(arg0: String)` | `String` | Converts/serializes representation via `toString` |
| `instance` | `toString` | `()` | `String` | Converts/serializes representation via `toString` |
| `instance` | `getTimeframe` | `()` | `String` | Retrieves `Timeframe` property from `FxTimeBar` |
| `instance` | `processTick` | `(arg0: TickEvent, arg1: BarTypeStatus, arg2: int)` | `void` | Performs process tick operation |
| `instance` | `getBarTimeType` | `()` | `int` | Retrieves `BarTimeType` property from `FxTimeBar` |
| `instance` | `toStr` | `()` | `String` | Converts/serializes representation via `toStr` |
| `instance` | `equals` | `(arg0: Object)` | `boolean` | Performs equals operation |
| `instance` | `hashCode` | `()` | `int` | Evaluates boolean predicate `hashCode` on `FxTimeBar` |
| `instance` | `getClass` | `()` | `Class` | Retrieves `Class` property from `FxTimeBar` |
| `instance` | `notify` | `()` | `void` | Performs notify operation |
| `instance` | `notifyAll` | `()` | `void` | Performs notify all operation |
| `instance` | `wait` | `(arg0: long)` | `void` | Performs wait operation |
| `instance` | `wait` | `(arg0: long, arg1: int)` | `void` | Performs wait operation |
| `instance` | `wait` | `()` | `void` | Performs wait operation |

---

### `TimeBar`
- **Full Qualified Name:** `com.strategyquant.datalib.bartype.impl.TimeBar`
- **Primary Job / Responsibility:** Time-series price history, OHLCV bar storage, and chart data management (`TimeBar`).

#### Fields
| Scope | Field Name | Type |
| :--- | :--- | :--- |
| `static` | `Log` | `Logger` |

#### Methods & Functions
| Modifiers | Method Name | Parameter Signatures | Return Type | Functional Description / Job |
| :--- | :--- | :--- | :--- | :--- |
| `instance` | `clone` | `()` | `BarType` | Performs clone operation |
| `instance` | `clone` | `()` | `BarType` | Performs clone operation |
| `instance` | `clone` | `(arg0: String)` | `BarType` | Performs clone operation |
| `instance` | `getPeriod` | `()` | `long` | Retrieves `Period` property from `TimeBar` |
| `instance` | `estimateStartDate` | `(arg0: int, arg1: long)` | `long` | Performs estimate start date operation |
| `instance` | `checkCanBeComputedFrom` | `(arg0: String)` | `String` | Performs check can be computed from operation |
| `instance` | `getPeriodInMS` | `()` | `int` | Retrieves `PeriodInMS` property from `TimeBar` |
| `instance` | `processTickImplementation` | `(arg0: TickEvent, arg1: BarTypeStatus, arg2: int)` | `void` | Performs process tick implementation operation |
| `instance` | `isTickBar` | `()` | `boolean` | Evaluates boolean predicate `isTickBar` on `TimeBar` |
| `instance` | `getBaseTF` | `()` | `String` | Retrieves `BaseTF` property from `TimeBar` |
| `instance` | `getTickTF` | `()` | `String` | Retrieves `TickTF` property from `TimeBar` |
| `instance` | `checkTimeframeIsSupported` | `(arg0: String)` | `boolean` | Performs check timeframe is supported operation |
| `instance` | `getPeriodInSeconds` | `(arg0: String, arg1: boolean)` | `long` | Retrieves `PeriodInSeconds` property from `TimeBar` |
| `instance` | `getPeriodMillis` | `()` | `long` | Retrieves `PeriodMillis` property from `TimeBar` |
| `instance` | `toString` | `(arg0: String)` | `String` | Converts/serializes representation via `toString` |
| `instance` | `toString` | `()` | `String` | Converts/serializes representation via `toString` |
| `instance` | `getTimeframe` | `()` | `String` | Retrieves `Timeframe` property from `TimeBar` |
| `instance` | `processTick` | `(arg0: TickEvent, arg1: BarTypeStatus, arg2: int)` | `void` | Performs process tick operation |
| `instance` | `getBarTimeType` | `()` | `int` | Retrieves `BarTimeType` property from `TimeBar` |
| `instance` | `toStr` | `()` | `String` | Converts/serializes representation via `toStr` |
| `instance` | `equals` | `(arg0: Object)` | `boolean` | Performs equals operation |
| `instance` | `hashCode` | `()` | `int` | Evaluates boolean predicate `hashCode` on `TimeBar` |
| `instance` | `getClass` | `()` | `Class` | Retrieves `Class` property from `TimeBar` |
| `instance` | `notify` | `()` | `void` | Performs notify operation |
| `instance` | `notifyAll` | `()` | `void` | Performs notify all operation |
| `instance` | `wait` | `(arg0: long)` | `void` | Performs wait operation |
| `instance` | `wait` | `(arg0: long, arg1: int)` | `void` | Performs wait operation |
| `instance` | `wait` | `()` | `void` | Performs wait operation |

---

## Subsystem: `basket`

### `BasketBrokerDev`
- **Full Qualified Name:** `com.strategyquant.datalib.basket.BasketBrokerDev`
- **Primary Job / Responsibility:** Market data abstraction and time-series container (`BasketBrokerDev`).

#### Methods & Functions
| Modifiers | Method Name | Parameter Signatures | Return Type | Functional Description / Job |
| :--- | :--- | :--- | :--- | :--- |
| `instance` | `isDev` | `()` | `boolean` | Evaluates boolean predicate `isDev` on `BasketBrokerDev` |
| `instance` | `equals` | `(arg0: Object)` | `boolean` | Performs equals operation |
| `instance` | `toString` | `()` | `String` | Converts/serializes representation via `toString` |
| `instance` | `hashCode` | `()` | `int` | Evaluates boolean predicate `hashCode` on `BasketBrokerDev` |
| `instance` | `getClass` | `()` | `Class` | Retrieves `Class` property from `BasketBrokerDev` |
| `instance` | `notify` | `()` | `void` | Performs notify operation |
| `instance` | `notifyAll` | `()` | `void` | Performs notify all operation |
| `instance` | `wait` | `(arg0: long)` | `void` | Performs wait operation |
| `instance` | `wait` | `(arg0: long, arg1: int)` | `void` | Performs wait operation |
| `instance` | `wait` | `()` | `void` | Performs wait operation |
| `static` | `getInstance` | `()` | `BasketBrokerDev` | Retrieves `Instance` property from `BasketBrokerDev` |

---

### `BasketDto`
- **Full Qualified Name:** `com.strategyquant.datalib.basket.BasketDto`
- **Primary Job / Responsibility:** Market data abstraction and time-series container (`BasketDto`).

#### Methods & Functions
| Modifiers | Method Name | Parameter Signatures | Return Type | Functional Description / Job |
| :--- | :--- | :--- | :--- | :--- |
| `instance` | `getName` | `()` | `String` | Retrieves `Name` property from `BasketDto` |
| `instance` | `setName` | `(arg0: String)` | `void` | Sets `Name` configuration/state on `BasketDto` |
| `instance` | `getId` | `()` | `Integer` | Retrieves `Id` property from `BasketDto` |
| `instance` | `getCount` | `()` | `int` | Retrieves `Count` property from `BasketDto` |
| `instance` | `isDefault` | `()` | `boolean` | Evaluates boolean predicate `isDefault` on `BasketDto` |
| `instance` | `setSystem` | `(arg0: boolean)` | `void` | Sets `System` configuration/state on `BasketDto` |
| `instance` | `isSystem` | `()` | `boolean` | Evaluates boolean predicate `isSystem` on `BasketDto` |
| `instance` | `setCount` | `(arg0: int)` | `void` | Sets `Count` configuration/state on `BasketDto` |
| `instance` | `setDesc` | `(arg0: String)` | `void` | Sets `Desc` configuration/state on `BasketDto` |
| `instance` | `setId` | `(arg0: Integer)` | `void` | Sets `Id` configuration/state on `BasketDto` |
| `instance` | `getDesc` | `()` | `String` | Retrieves `Desc` property from `BasketDto` |
| `instance` | `getTotal` | `()` | `int` | Retrieves `Total` property from `BasketDto` |
| `instance` | `setTotal` | `(arg0: int)` | `void` | Sets `Total` configuration/state on `BasketDto` |
| `instance` | `equals` | `(arg0: Object)` | `boolean` | Performs equals operation |
| `instance` | `toString` | `()` | `String` | Converts/serializes representation via `toString` |
| `instance` | `hashCode` | `()` | `int` | Evaluates boolean predicate `hashCode` on `BasketDto` |
| `instance` | `getClass` | `()` | `Class` | Retrieves `Class` property from `BasketDto` |
| `instance` | `notify` | `()` | `void` | Performs notify operation |
| `instance` | `notifyAll` | `()` | `void` | Performs notify all operation |
| `instance` | `wait` | `(arg0: long)` | `void` | Performs wait operation |
| `instance` | `wait` | `(arg0: long, arg1: int)` | `void` | Performs wait operation |
| `instance` | `wait` | `()` | `void` | Performs wait operation |

---

### `BasketOfStocksManager`
- **Full Qualified Name:** `com.strategyquant.datalib.basket.BasketOfStocksManager`
- **Primary Job / Responsibility:** Market data abstraction and time-series container (`BasketOfStocksManager`).

#### Fields
| Scope | Field Name | Type |
| :--- | :--- | :--- |
| `static` | `LimitedGroupName` | `String` |
| `static` | `Log` | `Logger` |

#### Methods & Functions
| Modifiers | Method Name | Parameter Signatures | Return Type | Functional Description / Job |
| :--- | :--- | :--- | :--- | :--- |
| `instance` | `sync` | `(arg0: Runnable)` | `void` | Performs sync operation |
| `instance` | `getBasket` | `(arg0: String)` | `BasketDto` | Retrieves `Basket` property from `BasketOfStocksManager` |
| `instance` | `getBasket` | `(arg0: Integer)` | `BasketDto` | Retrieves `Basket` property from `BasketOfStocksManager` |
| `instance` | `getStocks` | `(arg0: int)` | `List` | Retrieves `Stocks` property from `BasketOfStocksManager` |
| `instance` | `getStocks` | `(arg0: int, arg1: List)` | `List` | Retrieves `Stocks` property from `BasketOfStocksManager` |
| `instance` | `initDatabase` | `()` | `void` | Instantiates/initializes `initDatabase` resource |
| `instance` | `updateGroupsOfSymbols` | `()` | `Set` | Performs update groups of symbols operation |
| `instance` | `getGroupsForStock` | `(arg0: String)` | `Set` | Retrieves `GroupsForStock` property from `BasketOfStocksManager` |
| `instance` | `createCustomGroup` | `(arg0: String, arg1: int, arg2: String, arg3: boolean, arg4: String)` | `BasketDto` | Instantiates/initializes `createCustomGroup` resource |
| `instance` | `getGroups` | `()` | `List` | Retrieves `Groups` property from `BasketOfStocksManager` |
| `instance` | `saveGroup` | `(arg0: BasketDto)` | `void` | Performs save group operation |
| `instance` | `importFromCsv` | `(arg0: String, arg1: Integer, arg2: String, arg3: String)` | `void` | Performs import from csv operation |
| `instance` | `importFromCsv` | `(arg0: String, arg1: Integer, arg2: String)` | `void` | Performs import from csv operation |
| `instance` | `deleteGroup` | `(arg0: int)` | `BasketDto` | Performs delete group operation |
| `instance` | `synhronizeAsync` | `(arg0: Runnable)` | `void` | Performs synhronize async operation |
| `instance` | `readStocksFromCsv` | `(arg0: String, arg1: String)` | `List` | Performs read stocks from csv operation |
| `instance` | `getSystemBasket` | `(arg0: String)` | `BasketDto` | Retrieves `SystemBasket` property from `BasketOfStocksManager` |
| `instance` | `saveStocks` | `(arg0: int, arg1: List)` | `void` | Performs save stocks operation |
| `instance` | `updateGroupRange` | `(arg0: Integer)` | `void` | Performs update group range operation |
| `instance` | `saveCustomStocks` | `(arg0: int, arg1: List)` | `void` | Performs save custom stocks operation |
| `instance` | `updateStocksFromStr` | `(arg0: String, arg1: Integer, arg2: String)` | `List` | Performs update stocks from str operation |
| `instance` | `close` | `(arg0: ResultSet)` | `void` | Performs close operation |
| `instance` | `close` | `(arg0: Statement)` | `void` | Performs close operation |
| `instance` | `close` | `(arg0: Connection)` | `void` | Performs close operation |
| `instance` | `getConnection` | `()` | `Connection` | Retrieves `Connection` property from `BasketOfStocksManager` |
| `instance` | `sqlCheckRecordExists` | `(arg0: Connection, arg1: String)` | `boolean` | Performs sql check record exists operation |
| `instance` | `sqlCommand` | `(arg0: Connection, arg1: PreparedStatement)` | `void` | Performs sql command operation |
| `instance` | `sqlCommand` | `(arg0: String)` | `void` | Performs sql command operation |
| `instance` | `sqlCommand` | `(arg0: Connection, arg1: String)` | `void` | Performs sql command operation |
| `instance` | `sqlInsertReturnAutoId` | `(arg0: Connection, arg1: PreparedStatement)` | `int` | Performs sql insert return auto id operation |
| `instance` | `sqlInsertReturnAutoId` | `(arg0: Connection, arg1: String)` | `int` | Performs sql insert return auto id operation |
| `instance` | `_getDirectory` | `()` | `String` | Performs get directory operation |
| `instance` | `getDbPath` | `()` | `String` | Retrieves `DbPath` property from `BasketOfStocksManager` |
| `instance` | `isDbExist` | `()` | `boolean` | Evaluates boolean predicate `isDbExist` on `BasketOfStocksManager` |
| `instance` | `columnExists` | `(arg0: String, arg1: String)` | `boolean` | Performs column exists operation |
| `instance` | `tableExists` | `(arg0: String)` | `boolean` | Performs table exists operation |
| `instance` | `equals` | `(arg0: Object)` | `boolean` | Performs equals operation |
| `instance` | `toString` | `()` | `String` | Converts/serializes representation via `toString` |
| `instance` | `hashCode` | `()` | `int` | Evaluates boolean predicate `hashCode` on `BasketOfStocksManager` |
| `instance` | `getClass` | `()` | `Class` | Retrieves `Class` property from `BasketOfStocksManager` |
| `instance` | `notify` | `()` | `void` | Performs notify operation |
| `instance` | `notifyAll` | `()` | `void` | Performs notify all operation |
| `instance` | `wait` | `(arg0: long)` | `void` | Performs wait operation |
| `instance` | `wait` | `(arg0: long, arg1: int)` | `void` | Performs wait operation |
| `instance` | `wait` | `()` | `void` | Performs wait operation |
| `static` | `getInstance` | `()` | `BasketOfStocksManager` | Retrieves `Instance` property from `BasketOfStocksManager` |
| `static` | `init` | `(arg0: String)` | `void` | Instantiates/initializes `init` resource |
| `static` | `getDownloaded` | `(arg0: Map, arg1: Integer)` | `int` | Retrieves `Downloaded` property from `BasketOfStocksManager` |
| `static` | `isReadyForUse` | `(arg0: int, arg1: int)` | `boolean` | Evaluates boolean predicate `isReadyForUse` on `BasketOfStocksManager` |
| `static` | `getNumberOfSymbolsInGroup` | `(arg0: Set, arg1: BasketDto)` | `int` | Retrieves `NumberOfSymbolsInGroup` property from `BasketOfStocksManager` |
| `static` | `getMissingSymbols` | `(arg0: Map, arg1: Integer)` | `List` | Retrieves `MissingSymbols` property from `BasketOfStocksManager` |

---

### `MinMax`
- **Full Qualified Name:** `com.strategyquant.datalib.basket.BasketOfStocksManager.MinMax`
- **Primary Job / Responsibility:** Market data abstraction and time-series container (`MinMax`).

#### Fields
| Scope | Field Name | Type |
| :--- | :--- | :--- |
| `instance` | `max` | `long` |
| `instance` | `min` | `long` |

#### Methods & Functions
| Modifiers | Method Name | Parameter Signatures | Return Type | Functional Description / Job |
| :--- | :--- | :--- | :--- | :--- |
| `instance` | `equals` | `(arg0: Object)` | `boolean` | Performs equals operation |
| `instance` | `toString` | `()` | `String` | Converts/serializes representation via `toString` |
| `instance` | `hashCode` | `()` | `int` | Evaluates boolean predicate `hashCode` on `MinMax` |
| `instance` | `getClass` | `()` | `Class` | Retrieves `Class` property from `MinMax` |
| `instance` | `notify` | `()` | `void` | Performs notify operation |
| `instance` | `notifyAll` | `()` | `void` | Performs notify all operation |
| `instance` | `wait` | `(arg0: long)` | `void` | Performs wait operation |
| `instance` | `wait` | `(arg0: long, arg1: int)` | `void` | Performs wait operation |
| `instance` | `wait` | `()` | `void` | Performs wait operation |

---

### `StockDto`
- **Full Qualified Name:** `com.strategyquant.datalib.basket.StockDto`
- **Primary Job / Responsibility:** Market data abstraction and time-series container (`StockDto`).

#### Fields
| Scope | Field Name | Type |
| :--- | :--- | :--- |
| `static` | `TimeNotDefined` | `long` |

#### Methods & Functions
| Modifiers | Method Name | Parameter Signatures | Return Type | Functional Description / Job |
| :--- | :--- | :--- | :--- | :--- |
| `instance` | `toString` | `()` | `String` | Converts/serializes representation via `toString` |
| `instance` | `getId` | `()` | `Integer` | Retrieves `Id` property from `StockDto` |
| `instance` | `isActive` | `()` | `boolean` | Evaluates boolean predicate `isActive` on `StockDto` |
| `instance` | `getDateFrom` | `()` | `Long` | Retrieves `DateFrom` property from `StockDto` |
| `instance` | `getDateTo` | `()` | `Long` | Retrieves `DateTo` property from `StockDto` |
| `instance` | `getTicker` | `()` | `String` | Retrieves `Ticker` property from `StockDto` |
| `instance` | `setId` | `(arg0: Integer)` | `void` | Sets `Id` configuration/state on `StockDto` |
| `instance` | `setDateFrom` | `(arg0: Long)` | `void` | Sets `DateFrom` configuration/state on `StockDto` |
| `instance` | `setTicker` | `(arg0: String)` | `void` | Sets `Ticker` configuration/state on `StockDto` |
| `instance` | `setDateTo` | `(arg0: Long)` | `void` | Sets `DateTo` configuration/state on `StockDto` |
| `instance` | `equals` | `(arg0: Object)` | `boolean` | Performs equals operation |
| `instance` | `hashCode` | `()` | `int` | Evaluates boolean predicate `hashCode` on `StockDto` |
| `instance` | `getClass` | `()` | `Class` | Retrieves `Class` property from `StockDto` |
| `instance` | `notify` | `()` | `void` | Performs notify operation |
| `instance` | `notifyAll` | `()` | `void` | Performs notify all operation |
| `instance` | `wait` | `(arg0: long)` | `void` | Performs wait operation |
| `instance` | `wait` | `(arg0: long, arg1: int)` | `void` | Performs wait operation |
| `instance` | `wait` | `()` | `void` | Performs wait operation |

---

## Subsystem: `broker`

### `BrokerDto`
- **Full Qualified Name:** `com.strategyquant.datalib.broker.BrokerDto`
- **Primary Job / Responsibility:** Market data abstraction and time-series container (`BrokerDto`).

#### Methods & Functions
| Modifiers | Method Name | Parameter Signatures | Return Type | Functional Description / Job |
| :--- | :--- | :--- | :--- | :--- |
| `instance` | `getName` | `()` | `String` | Retrieves `Name` property from `BrokerDto` |
| `instance` | `setName` | `(arg0: String)` | `void` | Sets `Name` configuration/state on `BrokerDto` |
| `instance` | `getId` | `()` | `Integer` | Retrieves `Id` property from `BrokerDto` |
| `instance` | `setSystem` | `(arg0: boolean)` | `void` | Sets `System` configuration/state on `BrokerDto` |
| `instance` | `isSystem` | `()` | `boolean` | Evaluates boolean predicate `isSystem` on `BrokerDto` |
| `instance` | `getMtTimezone` | `()` | `String` | Retrieves `MtTimezone` property from `BrokerDto` |
| `instance` | `isMtUse` | `()` | `boolean` | Evaluates boolean predicate `isMtUse` on `BrokerDto` |
| `instance` | `isStockPickerUse` | `()` | `boolean` | Evaluates boolean predicate `isStockPickerUse` on `BrokerDto` |
| `instance` | `getPostfix` | `()` | `String` | Retrieves `Postfix` property from `BrokerDto` |
| `instance` | `setDesc` | `(arg0: String)` | `void` | Sets `Desc` configuration/state on `BrokerDto` |
| `instance` | `setMtTimezone` | `(arg0: String)` | `void` | Sets `MtTimezone` configuration/state on `BrokerDto` |
| `instance` | `setMtUse` | `(arg0: boolean)` | `void` | Sets `MtUse` configuration/state on `BrokerDto` |
| `instance` | `setPostfix` | `(arg0: String)` | `void` | Sets `Postfix` configuration/state on `BrokerDto` |
| `instance` | `setStockPickerUse` | `(arg0: boolean)` | `void` | Sets `StockPickerUse` configuration/state on `BrokerDto` |
| `instance` | `setId` | `(arg0: Integer)` | `void` | Sets `Id` configuration/state on `BrokerDto` |
| `instance` | `getDesc` | `()` | `String` | Retrieves `Desc` property from `BrokerDto` |
| `instance` | `getCustomizedStocks` | `()` | `int` | Retrieves `CustomizedStocks` property from `BrokerDto` |
| `instance` | `setCustomizedStocks` | `(arg0: int)` | `void` | Sets `CustomizedStocks` configuration/state on `BrokerDto` |
| `instance` | `getCustomizedInstruments` | `()` | `int` | Retrieves `CustomizedInstruments` property from `BrokerDto` |
| `instance` | `setCustomizedInstruments` | `(arg0: int)` | `void` | Sets `CustomizedInstruments` configuration/state on `BrokerDto` |
| `instance` | `getCustomizedSessions` | `()` | `int` | Retrieves `CustomizedSessions` property from `BrokerDto` |
| `instance` | `setCustomizedSessions` | `(arg0: int)` | `void` | Sets `CustomizedSessions` configuration/state on `BrokerDto` |
| `instance` | `equals` | `(arg0: Object)` | `boolean` | Performs equals operation |
| `instance` | `toString` | `()` | `String` | Converts/serializes representation via `toString` |
| `instance` | `hashCode` | `()` | `int` | Evaluates boolean predicate `hashCode` on `BrokerDto` |
| `instance` | `getClass` | `()` | `Class` | Retrieves `Class` property from `BrokerDto` |
| `instance` | `notify` | `()` | `void` | Performs notify operation |
| `instance` | `notifyAll` | `()` | `void` | Performs notify all operation |
| `instance` | `wait` | `(arg0: long)` | `void` | Performs wait operation |
| `instance` | `wait` | `(arg0: long, arg1: int)` | `void` | Performs wait operation |
| `instance` | `wait` | `()` | `void` | Performs wait operation |

---

### `BrokerManager`
- **Full Qualified Name:** `com.strategyquant.datalib.broker.BrokerManager`
- **Primary Job / Responsibility:** Market data abstraction and time-series container (`BrokerManager`).

#### Fields
| Scope | Field Name | Type |
| :--- | :--- | :--- |
| `static` | `DEFAULT_BROKER` | `String` |
| `static` | `Log` | `Logger` |
| `static` | `NO_BROKER` | `String` |

#### Methods & Functions
| Modifiers | Method Name | Parameter Signatures | Return Type | Functional Description / Job |
| :--- | :--- | :--- | :--- | :--- |
| `instance` | `getStocks` | `(arg0: int)` | `List` | Retrieves `Stocks` property from `BrokerManager` |
| `instance` | `getBroker` | `(arg0: Integer)` | `BrokerDto` | Retrieves `Broker` property from `BrokerManager` |
| `instance` | `getBroker` | `(arg0: String)` | `BrokerDto` | Retrieves `Broker` property from `BrokerManager` |
| `instance` | `initDatabase` | `()` | `void` | Instantiates/initializes `initDatabase` resource |
| `instance` | `getDefaultBroker` | `()` | `BrokerDto` | Retrieves `DefaultBroker` property from `BrokerManager` |
| `instance` | `checkBrokerExists` | `(arg0: String)` | `boolean` | Performs check broker exists operation |
| `instance` | `saveBroker` | `(arg0: BrokerDto)` | `void` | Performs save broker operation |
| `instance` | `getBrokerName` | `(arg0: int)` | `String` | Retrieves `BrokerName` property from `BrokerManager` |
| `instance` | `getAllBrokers` | `()` | `List` | Retrieves `AllBrokers` property from `BrokerManager` |
| `instance` | `importFromCsv` | `(arg0: String, arg1: Integer, arg2: String)` | `void` | Performs import from csv operation |
| `instance` | `synhronizeAsync` | `(arg0: Runnable)` | `void` | Performs synhronize async operation |
| `instance` | `readStocksFromCsv` | `(arg0: String, arg1: String)` | `List` | Performs read stocks from csv operation |
| `instance` | `saveStocks` | `(arg0: int, arg1: List)` | `void` | Performs save stocks operation |
| `instance` | `refresh` | `()` | `void` | Performs refresh operation |
| `instance` | `isUsedByMt` | `(arg0: int)` | `boolean` | Evaluates boolean predicate `isUsedByMt` on `BrokerManager` |
| `instance` | `deleteBroker` | `(arg0: int, arg1: boolean)` | `BrokerDto` | Performs delete broker operation |
| `instance` | `getSystemBroker` | `(arg0: String)` | `BrokerDto` | Retrieves `SystemBroker` property from `BrokerManager` |
| `instance` | `getBrokerDependantName` | `(arg0: String, arg1: int)` | `String` | Retrieves `BrokerDependantName` property from `BrokerManager` |
| `instance` | `updateStocksFromStr` | `(arg0: String, arg1: Integer, arg2: String)` | `List` | Performs update stocks from str operation |
| `instance` | `close` | `(arg0: ResultSet)` | `void` | Performs close operation |
| `instance` | `close` | `(arg0: Statement)` | `void` | Performs close operation |
| `instance` | `close` | `(arg0: Connection)` | `void` | Performs close operation |
| `instance` | `getConnection` | `()` | `Connection` | Retrieves `Connection` property from `BrokerManager` |
| `instance` | `sqlCheckRecordExists` | `(arg0: Connection, arg1: String)` | `boolean` | Performs sql check record exists operation |
| `instance` | `sqlCommand` | `(arg0: Connection, arg1: PreparedStatement)` | `void` | Performs sql command operation |
| `instance` | `sqlCommand` | `(arg0: String)` | `void` | Performs sql command operation |
| `instance` | `sqlCommand` | `(arg0: Connection, arg1: String)` | `void` | Performs sql command operation |
| `instance` | `sqlInsertReturnAutoId` | `(arg0: Connection, arg1: PreparedStatement)` | `int` | Performs sql insert return auto id operation |
| `instance` | `sqlInsertReturnAutoId` | `(arg0: Connection, arg1: String)` | `int` | Performs sql insert return auto id operation |
| `instance` | `_getDirectory` | `()` | `String` | Performs get directory operation |
| `instance` | `getDbPath` | `()` | `String` | Retrieves `DbPath` property from `BrokerManager` |
| `instance` | `isDbExist` | `()` | `boolean` | Evaluates boolean predicate `isDbExist` on `BrokerManager` |
| `instance` | `columnExists` | `(arg0: String, arg1: String)` | `boolean` | Performs column exists operation |
| `instance` | `tableExists` | `(arg0: String)` | `boolean` | Performs table exists operation |
| `instance` | `equals` | `(arg0: Object)` | `boolean` | Performs equals operation |
| `instance` | `toString` | `()` | `String` | Converts/serializes representation via `toString` |
| `instance` | `hashCode` | `()` | `int` | Evaluates boolean predicate `hashCode` on `BrokerManager` |
| `instance` | `getClass` | `()` | `Class` | Retrieves `Class` property from `BrokerManager` |
| `instance` | `notify` | `()` | `void` | Performs notify operation |
| `instance` | `notifyAll` | `()` | `void` | Performs notify all operation |
| `instance` | `wait` | `(arg0: long)` | `void` | Performs wait operation |
| `instance` | `wait` | `(arg0: long, arg1: int)` | `void` | Performs wait operation |
| `instance` | `wait` | `()` | `void` | Performs wait operation |
| `static` | `getInstance` | `()` | `BrokerManager` | Retrieves `Instance` property from `BrokerManager` |
| `static` | `init` | `(arg0: String)` | `void` | Instantiates/initializes `init` resource |

---

### `BrokerStockDto`
- **Full Qualified Name:** `com.strategyquant.datalib.broker.BrokerStockDto`
- **Primary Job / Responsibility:** Market data abstraction and time-series container (`BrokerStockDto`).

#### Methods & Functions
| Modifiers | Method Name | Parameter Signatures | Return Type | Functional Description / Job |
| :--- | :--- | :--- | :--- | :--- |
| `instance` | `toString` | `()` | `String` | Converts/serializes representation via `toString` |
| `instance` | `getId` | `()` | `Integer` | Retrieves `Id` property from `BrokerStockDto` |
| `instance` | `getTicker` | `()` | `String` | Retrieves `Ticker` property from `BrokerStockDto` |
| `instance` | `setId` | `(arg0: Integer)` | `void` | Sets `Id` configuration/state on `BrokerStockDto` |
| `instance` | `setTicker` | `(arg0: String)` | `void` | Sets `Ticker` configuration/state on `BrokerStockDto` |
| `instance` | `equals` | `(arg0: Object)` | `boolean` | Performs equals operation |
| `instance` | `hashCode` | `()` | `int` | Evaluates boolean predicate `hashCode` on `BrokerStockDto` |
| `instance` | `getClass` | `()` | `Class` | Retrieves `Class` property from `BrokerStockDto` |
| `instance` | `notify` | `()` | `void` | Performs notify operation |
| `instance` | `notifyAll` | `()` | `void` | Performs notify all operation |
| `instance` | `wait` | `(arg0: long)` | `void` | Performs wait operation |
| `instance` | `wait` | `(arg0: long, arg1: int)` | `void` | Performs wait operation |
| `instance` | `wait` | `()` | `void` | Performs wait operation |

---

## Subsystem: `consts`

### `Backload`
- **Full Qualified Name:** `com.strategyquant.datalib.consts.Backload`
- **Primary Job / Responsibility:** Market data abstraction and time-series container (`Backload`).

#### Fields
| Scope | Field Name | Type |
| :--- | :--- | :--- |
| `static` | `BACKLOAD_BARS` | `int` |
| `static` | `BACKLOAD_DAYS` | `int` |
| `static` | `BACKLOAD_FROMDATE` | `int` |

#### Methods & Functions
| Modifiers | Method Name | Parameter Signatures | Return Type | Functional Description / Job |
| :--- | :--- | :--- | :--- | :--- |
| `instance` | `equals` | `(arg0: Object)` | `boolean` | Performs equals operation |
| `instance` | `toString` | `()` | `String` | Converts/serializes representation via `toString` |
| `instance` | `hashCode` | `()` | `int` | Evaluates boolean predicate `hashCode` on `Backload` |
| `instance` | `getClass` | `()` | `Class` | Retrieves `Class` property from `Backload` |
| `instance` | `notify` | `()` | `void` | Performs notify operation |
| `instance` | `notifyAll` | `()` | `void` | Performs notify all operation |
| `instance` | `wait` | `(arg0: long)` | `void` | Performs wait operation |
| `instance` | `wait` | `(arg0: long, arg1: int)` | `void` | Performs wait operation |
| `instance` | `wait` | `()` | `void` | Performs wait operation |

---

### `BackloadType`
- **Full Qualified Name:** `com.strategyquant.datalib.consts.BackloadType`
- **Primary Job / Responsibility:** Market data abstraction and time-series container (`BackloadType`).

#### Fields
| Scope | Field Name | Type |
| :--- | :--- | :--- |
| `static` | `Bars` | `int` |
| `static` | `Days` | `int` |
| `static` | `FromDate` | `int` |

#### Methods & Functions
| Modifiers | Method Name | Parameter Signatures | Return Type | Functional Description / Job |
| :--- | :--- | :--- | :--- | :--- |
| `instance` | `equals` | `(arg0: Object)` | `boolean` | Performs equals operation |
| `instance` | `toString` | `()` | `String` | Converts/serializes representation via `toString` |
| `instance` | `hashCode` | `()` | `int` | Evaluates boolean predicate `hashCode` on `BackloadType` |
| `instance` | `getClass` | `()` | `Class` | Retrieves `Class` property from `BackloadType` |
| `instance` | `notify` | `()` | `void` | Performs notify operation |
| `instance` | `notifyAll` | `()` | `void` | Performs notify all operation |
| `instance` | `wait` | `(arg0: long)` | `void` | Performs wait operation |
| `instance` | `wait` | `(arg0: long, arg1: int)` | `void` | Performs wait operation |
| `instance` | `wait` | `()` | `void` | Performs wait operation |

---

### `BarTimeTypes`
- **Full Qualified Name:** `com.strategyquant.datalib.consts.BarTimeTypes`
- **Primary Job / Responsibility:** Time-series price history, OHLCV bar storage, and chart data management (`BarTimeTypes`).

#### Fields
| Scope | Field Name | Type |
| :--- | :--- | :--- |
| `static` | `TimeIsEndOfBar` | `int` |
| `static` | `TimeIsStartOfBar` | `int` |

#### Methods & Functions
| Modifiers | Method Name | Parameter Signatures | Return Type | Functional Description / Job |
| :--- | :--- | :--- | :--- | :--- |
| `instance` | `equals` | `(arg0: Object)` | `boolean` | Performs equals operation |
| `instance` | `toString` | `()` | `String` | Converts/serializes representation via `toString` |
| `instance` | `hashCode` | `()` | `int` | Evaluates boolean predicate `hashCode` on `BarTimeTypes` |
| `instance` | `getClass` | `()` | `Class` | Retrieves `Class` property from `BarTimeTypes` |
| `instance` | `notify` | `()` | `void` | Performs notify operation |
| `instance` | `notifyAll` | `()` | `void` | Performs notify all operation |
| `instance` | `wait` | `(arg0: long)` | `void` | Performs wait operation |
| `instance` | `wait` | `(arg0: long, arg1: int)` | `void` | Performs wait operation |
| `instance` | `wait` | `()` | `void` | Performs wait operation |
| `static` | `isEndOfBar` | `(arg0: int)` | `boolean` | Evaluates boolean predicate `isEndOfBar` on `BarTimeTypes` |

---

### `DataTypes`
- **Full Qualified Name:** `com.strategyquant.datalib.consts.DataTypes`
- **Primary Job / Responsibility:** Market data abstraction and time-series container (`DataTypes`).

#### Fields
| Scope | Field Name | Type |
| :--- | :--- | :--- |
| `static` | `Bond` | `byte` |
| `static` | `CFDs` | `byte` |
| `static` | `Crypto` | `byte` |
| `static` | `DATATYPE_BOND` | `String` |
| `static` | `DATATYPE_CFDS` | `String` |
| `static` | `DATATYPE_CRYPTO` | `String` |
| `static` | `DATATYPE_ETF` | `String` |
| `static` | `DATATYPE_FOREX` | `String` |
| `static` | `DATATYPE_FUTURES` | `String` |
| `static` | `DATATYPE_INDEX` | `String` |
| `static` | `DATATYPE_STOCK` | `String` |
| `static` | `ETF` | `byte` |
| `static` | `Forex` | `byte` |
| `static` | `Futures` | `byte` |
| `static` | `Index` | `byte` |
| `static` | `Stock` | `byte` |

#### Methods & Functions
| Modifiers | Method Name | Parameter Signatures | Return Type | Functional Description / Job |
| :--- | :--- | :--- | :--- | :--- |
| `instance` | `equals` | `(arg0: Object)` | `boolean` | Performs equals operation |
| `instance` | `toString` | `()` | `String` | Converts/serializes representation via `toString` |
| `instance` | `hashCode` | `()` | `int` | Evaluates boolean predicate `hashCode` on `DataTypes` |
| `instance` | `getClass` | `()` | `Class` | Retrieves `Class` property from `DataTypes` |
| `instance` | `notify` | `()` | `void` | Performs notify operation |
| `instance` | `notifyAll` | `()` | `void` | Performs notify all operation |
| `instance` | `wait` | `(arg0: long)` | `void` | Performs wait operation |
| `instance` | `wait` | `(arg0: long, arg1: int)` | `void` | Performs wait operation |
| `instance` | `wait` | `()` | `void` | Performs wait operation |
| `static` | `toString` | `(arg0: int)` | `String` | Converts/serializes representation via `toString` |
| `static` | `getDataType` | `(arg0: String)` | `byte` | Retrieves `DataType` property from `DataTypes` |

---

### `Precisions`
- **Full Qualified Name:** `com.strategyquant.datalib.consts.Precisions`
- **Primary Job / Responsibility:** Market data abstraction and time-series container (`Precisions`).

#### Fields
| Scope | Field Name | Type |
| :--- | :--- | :--- |
| `static` | `BaseTF` | `int` |
| `static` | `OpenPrices` | `int` |
| `static` | `PRECISION_BASE_TF` | `String` |
| `static` | `PRECISION_OPEN_PRICES` | `String` |
| `static` | `PRECISION_SELECTED_TF` | `String` |
| `static` | `PRECISION_TICK_CUSTOM_SPREADS` | `String` |
| `static` | `PRECISION_TICK_REAL_SPREADS` | `String` |
| `static` | `SelectedTF` | `int` |
| `static` | `TickCustomSpread` | `int` |
| `static` | `TickRealSpread` | `int` |

#### Methods & Functions
| Modifiers | Method Name | Parameter Signatures | Return Type | Functional Description / Job |
| :--- | :--- | :--- | :--- | :--- |
| `instance` | `equals` | `(arg0: Object)` | `boolean` | Performs equals operation |
| `instance` | `toString` | `()` | `String` | Converts/serializes representation via `toString` |
| `instance` | `hashCode` | `()` | `int` | Evaluates boolean predicate `hashCode` on `Precisions` |
| `instance` | `getClass` | `()` | `Class` | Retrieves `Class` property from `Precisions` |
| `instance` | `notify` | `()` | `void` | Performs notify operation |
| `instance` | `notifyAll` | `()` | `void` | Performs notify all operation |
| `instance` | `wait` | `(arg0: long)` | `void` | Performs wait operation |
| `instance` | `wait` | `(arg0: long, arg1: int)` | `void` | Performs wait operation |
| `instance` | `wait` | `()` | `void` | Performs wait operation |
| `static` | `toString` | `(arg0: int)` | `String` | Converts/serializes representation via `toString` |
| `static` | `getPrecision` | `(arg0: String)` | `int` | Retrieves `Precision` property from `Precisions` |
| `static` | `getPrecision` | `(arg0: int)` | `int` | Retrieves `Precision` property from `Precisions` |
| `static` | `isRealTick` | `(arg0: int)` | `boolean` | Evaluates boolean predicate `isRealTick` on `Precisions` |

---

## Subsystem: `customData`

### `AvailableCustomDataFormats`
- **Full Qualified Name:** `com.strategyquant.datalib.customData.AvailableCustomDataFormats`
- **Primary Job / Responsibility:** Market data abstraction and time-series container (`AvailableCustomDataFormats`).

#### Fields
| Scope | Field Name | Type |
| :--- | :--- | :--- |
| `static` | `Log` | `Logger` |

#### Methods & Functions
| Modifiers | Method Name | Parameter Signatures | Return Type | Functional Description / Job |
| :--- | :--- | :--- | :--- | :--- |
| `instance` | `getAvailableFileFormats` | `()` | `ArrayList` | Retrieves `AvailableFileFormats` property from `AvailableCustomDataFormats` |
| `instance` | `registerFileFormats` | `()` | `void` | Performs register file formats operation |
| `instance` | `formatExists` | `(arg0: String)` | `boolean` | Converts/serializes representation via `formatExists` |
| `instance` | `addDataFormat` | `(arg0: CustomDataFormat)` | `void` | Appends/registers element via `addDataFormat` |
| `instance` | `deleteDataFormat` | `(arg0: String)` | `void` | Performs delete data format operation |
| `instance` | `updateDataFormat` | `(arg0: CustomDataFormat)` | `void` | Performs update data format operation |
| `instance` | `findFileFormatByName` | `(arg0: String)` | `CustomDataFormat` | Performs find file format by name operation |
| `instance` | `equals` | `(arg0: Object)` | `boolean` | Performs equals operation |
| `instance` | `toString` | `()` | `String` | Converts/serializes representation via `toString` |
| `instance` | `hashCode` | `()` | `int` | Evaluates boolean predicate `hashCode` on `AvailableCustomDataFormats` |
| `instance` | `getClass` | `()` | `Class` | Retrieves `Class` property from `AvailableCustomDataFormats` |
| `instance` | `notify` | `()` | `void` | Performs notify operation |
| `instance` | `notifyAll` | `()` | `void` | Performs notify all operation |
| `instance` | `wait` | `(arg0: long)` | `void` | Performs wait operation |
| `instance` | `wait` | `(arg0: long, arg1: int)` | `void` | Performs wait operation |
| `instance` | `wait` | `()` | `void` | Performs wait operation |
| `static` | `getInstance` | `()` | `AvailableCustomDataFormats` | Retrieves `Instance` property from `AvailableCustomDataFormats` |

---

### `CustomData`
- **Full Qualified Name:** `com.strategyquant.datalib.customData.CustomData`
- **Primary Job / Responsibility:** Market data abstraction and time-series container (`CustomData`).

#### Fields
| Scope | Field Name | Type |
| :--- | :--- | :--- |
| `instance` | `time` | `long` |
| `instance` | `values` | `double[]` |

#### Methods & Functions
| Modifiers | Method Name | Parameter Signatures | Return Type | Functional Description / Job |
| :--- | :--- | :--- | :--- | :--- |
| `instance` | `reset` | `()` | `void` | Performs reset operation |
| `instance` | `toString` | `()` | `String` | Converts/serializes representation via `toString` |
| `instance` | `equals` | `(arg0: Object)` | `boolean` | Performs equals operation |
| `instance` | `hashCode` | `()` | `int` | Evaluates boolean predicate `hashCode` on `CustomData` |
| `instance` | `getClass` | `()` | `Class` | Retrieves `Class` property from `CustomData` |
| `instance` | `notify` | `()` | `void` | Performs notify operation |
| `instance` | `notifyAll` | `()` | `void` | Performs notify all operation |
| `instance` | `wait` | `(arg0: long)` | `void` | Performs wait operation |
| `instance` | `wait` | `(arg0: long, arg1: int)` | `void` | Performs wait operation |
| `instance` | `wait` | `()` | `void` | Performs wait operation |

---

### `CustomDataBinReader`
- **Full Qualified Name:** `com.strategyquant.datalib.customData.CustomDataBinReader`
- **Primary Job / Responsibility:** Market data abstraction and time-series container (`CustomDataBinReader`).

#### Fields
| Scope | Field Name | Type |
| :--- | :--- | :--- |
| `instance` | `loadedData` | `CustomData` |

#### Methods & Functions
| Modifiers | Method Name | Parameter Signatures | Return Type | Functional Description / Job |
| :--- | :--- | :--- | :--- | :--- |
| `instance` | `close` | `()` | `void` | Performs close operation |
| `instance` | `open` | `()` | `void` | Performs open operation |
| `instance` | `loadData` | `()` | `void` | Performs load data operation |
| `instance` | `hasNextData` | `()` | `boolean` | Evaluates boolean predicate `hasNextData` on `CustomDataBinReader` |
| `instance` | `equals` | `(arg0: Object)` | `boolean` | Performs equals operation |
| `instance` | `toString` | `()` | `String` | Converts/serializes representation via `toString` |
| `instance` | `hashCode` | `()` | `int` | Evaluates boolean predicate `hashCode` on `CustomDataBinReader` |
| `instance` | `getClass` | `()` | `Class` | Retrieves `Class` property from `CustomDataBinReader` |
| `instance` | `notify` | `()` | `void` | Performs notify operation |
| `instance` | `notifyAll` | `()` | `void` | Performs notify all operation |
| `instance` | `wait` | `(arg0: long)` | `void` | Performs wait operation |
| `instance` | `wait` | `(arg0: long, arg1: int)` | `void` | Performs wait operation |
| `instance` | `wait` | `()` | `void` | Performs wait operation |

---

### `CustomDataBinWriter`
- **Full Qualified Name:** `com.strategyquant.datalib.customData.CustomDataBinWriter`
- **Primary Job / Responsibility:** Market data abstraction and time-series container (`CustomDataBinWriter`).

#### Methods & Functions
| Modifiers | Method Name | Parameter Signatures | Return Type | Functional Description / Job |
| :--- | :--- | :--- | :--- | :--- |
| `instance` | `close` | `()` | `void` | Performs close operation |
| `instance` | `open` | `()` | `void` | Performs open operation |
| `instance` | `getFileName` | `()` | `String` | Retrieves `FileName` property from `CustomDataBinWriter` |
| `instance` | `setFileName` | `(arg0: String)` | `void` | Sets `FileName` configuration/state on `CustomDataBinWriter` |
| `instance` | `writeData` | `(arg0: CustomData)` | `void` | Performs write data operation |
| `instance` | `equals` | `(arg0: Object)` | `boolean` | Performs equals operation |
| `instance` | `toString` | `()` | `String` | Converts/serializes representation via `toString` |
| `instance` | `hashCode` | `()` | `int` | Evaluates boolean predicate `hashCode` on `CustomDataBinWriter` |
| `instance` | `getClass` | `()` | `Class` | Retrieves `Class` property from `CustomDataBinWriter` |
| `instance` | `notify` | `()` | `void` | Performs notify operation |
| `instance` | `notifyAll` | `()` | `void` | Performs notify all operation |
| `instance` | `wait` | `(arg0: long)` | `void` | Performs wait operation |
| `instance` | `wait` | `(arg0: long, arg1: int)` | `void` | Performs wait operation |
| `instance` | `wait` | `()` | `void` | Performs wait operation |

---

### `CustomDataCsv`
- **Full Qualified Name:** `com.strategyquant.datalib.customData.CustomDataCsv`
- **Primary Job / Responsibility:** Market data abstraction and time-series container (`CustomDataCsv`).

#### Methods & Functions
| Modifiers | Method Name | Parameter Signatures | Return Type | Functional Description / Job |
| :--- | :--- | :--- | :--- | :--- |
| `instance` | `equals` | `(arg0: Object)` | `boolean` | Performs equals operation |
| `instance` | `toString` | `()` | `String` | Converts/serializes representation via `toString` |
| `instance` | `hashCode` | `()` | `int` | Evaluates boolean predicate `hashCode` on `CustomDataCsv` |
| `instance` | `getClass` | `()` | `Class` | Retrieves `Class` property from `CustomDataCsv` |
| `instance` | `notify` | `()` | `void` | Performs notify operation |
| `instance` | `notifyAll` | `()` | `void` | Performs notify all operation |
| `instance` | `wait` | `(arg0: long)` | `void` | Performs wait operation |
| `instance` | `wait` | `(arg0: long, arg1: int)` | `void` | Performs wait operation |
| `instance` | `wait` | `()` | `void` | Performs wait operation |
| `static` | `write` | `(arg0: CustomDataInfo, arg1: File)` | `int` | Performs write operation |
| `static` | `valueNames` | `(arg0: CustomDataInfo)` | `String[]` | Performs value names operation |

---

### `CustomDataDb`
- **Full Qualified Name:** `com.strategyquant.datalib.customData.CustomDataDb`
- **Primary Job / Responsibility:** Market data abstraction and time-series container (`CustomDataDb`).

#### Methods & Functions
| Modifiers | Method Name | Parameter Signatures | Return Type | Functional Description / Job |
| :--- | :--- | :--- | :--- | :--- |
| `instance` | `initDatabase` | `()` | `void` | Instantiates/initializes `initDatabase` resource |
| `instance` | `close` | `(arg0: ResultSet)` | `void` | Performs close operation |
| `instance` | `close` | `(arg0: Statement)` | `void` | Performs close operation |
| `instance` | `close` | `(arg0: Connection)` | `void` | Performs close operation |
| `instance` | `getConnection` | `()` | `Connection` | Retrieves `Connection` property from `CustomDataDb` |
| `instance` | `sqlCheckRecordExists` | `(arg0: Connection, arg1: String)` | `boolean` | Performs sql check record exists operation |
| `instance` | `sqlCommand` | `(arg0: Connection, arg1: PreparedStatement)` | `void` | Performs sql command operation |
| `instance` | `sqlCommand` | `(arg0: String)` | `void` | Performs sql command operation |
| `instance` | `sqlCommand` | `(arg0: Connection, arg1: String)` | `void` | Performs sql command operation |
| `instance` | `sqlInsertReturnAutoId` | `(arg0: Connection, arg1: PreparedStatement)` | `int` | Performs sql insert return auto id operation |
| `instance` | `sqlInsertReturnAutoId` | `(arg0: Connection, arg1: String)` | `int` | Performs sql insert return auto id operation |
| `instance` | `_getDirectory` | `()` | `String` | Performs get directory operation |
| `instance` | `getDbPath` | `()` | `String` | Retrieves `DbPath` property from `CustomDataDb` |
| `instance` | `isDbExist` | `()` | `boolean` | Evaluates boolean predicate `isDbExist` on `CustomDataDb` |
| `instance` | `columnExists` | `(arg0: String, arg1: String)` | `boolean` | Performs column exists operation |
| `instance` | `tableExists` | `(arg0: String)` | `boolean` | Performs table exists operation |
| `instance` | `equals` | `(arg0: Object)` | `boolean` | Performs equals operation |
| `instance` | `toString` | `()` | `String` | Converts/serializes representation via `toString` |
| `instance` | `hashCode` | `()` | `int` | Evaluates boolean predicate `hashCode` on `CustomDataDb` |
| `instance` | `getClass` | `()` | `Class` | Retrieves `Class` property from `CustomDataDb` |
| `instance` | `notify` | `()` | `void` | Performs notify operation |
| `instance` | `notifyAll` | `()` | `void` | Performs notify all operation |
| `instance` | `wait` | `(arg0: long)` | `void` | Performs wait operation |
| `instance` | `wait` | `(arg0: long, arg1: int)` | `void` | Performs wait operation |
| `instance` | `wait` | `()` | `void` | Performs wait operation |

---

### `CustomDataInfo`
- **Full Qualified Name:** `com.strategyquant.datalib.customData.CustomDataInfo`
- **Primary Job / Responsibility:** Market data abstraction and time-series container (`CustomDataInfo`).

#### Fields
| Scope | Field Name | Type |
| :--- | :--- | :--- |
| `static` | `CodeEL` | `String` |
| `static` | `CodeMT4` | `String` |
| `static` | `CodeMT5` | `String` |
| `static` | `Name` | `String` |
| `instance` | `dataType` | `int` |
| `instance` | `dateFrom` | `long` |
| `instance` | `dateTo` | `long` |
| `instance` | `filename` | `String` |
| `instance` | `id` | `int` |
| `instance` | `name` | `String` |
| `instance` | `rows` | `int` |
| `instance` | `timeframe` | `String` |
| `instance` | `totalDays` | `int` |
| `instance` | `values` | `int` |
| `instance` | `valuesObject` | `JSONArray` |

#### Methods & Functions
| Modifiers | Method Name | Parameter Signatures | Return Type | Functional Description / Job |
| :--- | :--- | :--- | :--- | :--- |
| `instance` | `getValue` | `(arg0: int, arg1: String)` | `String` | Retrieves `Value` property from `CustomDataInfo` |
| `instance` | `setFromXML` | `(arg0: Element)` | `void` | Sets `FromXML` configuration/state on `CustomDataInfo` |
| `instance` | `getXML` | `()` | `Element` | Retrieves `XML` property from `CustomDataInfo` |
| `instance` | `setValues` | `(arg0: String)` | `void` | Sets `Values` configuration/state on `CustomDataInfo` |
| `instance` | `equals` | `(arg0: Object)` | `boolean` | Performs equals operation |
| `instance` | `toString` | `()` | `String` | Converts/serializes representation via `toString` |
| `instance` | `hashCode` | `()` | `int` | Evaluates boolean predicate `hashCode` on `CustomDataInfo` |
| `instance` | `getClass` | `()` | `Class` | Retrieves `Class` property from `CustomDataInfo` |
| `instance` | `notify` | `()` | `void` | Performs notify operation |
| `instance` | `notifyAll` | `()` | `void` | Performs notify all operation |
| `instance` | `wait` | `(arg0: long)` | `void` | Performs wait operation |
| `instance` | `wait` | `(arg0: long, arg1: int)` | `void` | Performs wait operation |
| `instance` | `wait` | `()` | `void` | Performs wait operation |

---

### `CustomDataManager`
- **Full Qualified Name:** `com.strategyquant.datalib.customData.CustomDataManager`
- **Primary Job / Responsibility:** Market data abstraction and time-series container (`CustomDataManager`).

#### Fields
| Scope | Field Name | Type |
| :--- | :--- | :--- |
| `static` | `Log` | `Logger` |

#### Methods & Functions
| Modifiers | Method Name | Parameter Signatures | Return Type | Functional Description / Job |
| :--- | :--- | :--- | :--- | :--- |
| `instance` | `initDatabase` | `()` | `void` | Instantiates/initializes `initDatabase` resource |
| `instance` | `_add` | `(arg0: String, arg1: String, arg2: int)` | `void` | Performs add operation |
| `instance` | `_update` | `(arg0: String, arg1: String, arg2: String, arg3: int)` | `void` | Performs update operation |
| `instance` | `_updateData` | `(arg0: String, arg1: long, arg2: long, arg3: int, arg4: String)` | `void` | Performs update data operation |
| `instance` | `close` | `(arg0: ResultSet)` | `void` | Performs close operation |
| `instance` | `close` | `(arg0: Statement)` | `void` | Performs close operation |
| `instance` | `close` | `(arg0: Connection)` | `void` | Performs close operation |
| `instance` | `getConnection` | `()` | `Connection` | Retrieves `Connection` property from `CustomDataManager` |
| `instance` | `sqlCheckRecordExists` | `(arg0: Connection, arg1: String)` | `boolean` | Performs sql check record exists operation |
| `instance` | `sqlCommand` | `(arg0: Connection, arg1: PreparedStatement)` | `void` | Performs sql command operation |
| `instance` | `sqlCommand` | `(arg0: String)` | `void` | Performs sql command operation |
| `instance` | `sqlCommand` | `(arg0: Connection, arg1: String)` | `void` | Performs sql command operation |
| `instance` | `sqlInsertReturnAutoId` | `(arg0: Connection, arg1: PreparedStatement)` | `int` | Performs sql insert return auto id operation |
| `instance` | `sqlInsertReturnAutoId` | `(arg0: Connection, arg1: String)` | `int` | Performs sql insert return auto id operation |
| `instance` | `_getDirectory` | `()` | `String` | Performs get directory operation |
| `instance` | `getDbPath` | `()` | `String` | Retrieves `DbPath` property from `CustomDataManager` |
| `instance` | `isDbExist` | `()` | `boolean` | Evaluates boolean predicate `isDbExist` on `CustomDataManager` |
| `instance` | `columnExists` | `(arg0: String, arg1: String)` | `boolean` | Performs column exists operation |
| `instance` | `tableExists` | `(arg0: String)` | `boolean` | Performs table exists operation |
| `instance` | `equals` | `(arg0: Object)` | `boolean` | Performs equals operation |
| `instance` | `toString` | `()` | `String` | Converts/serializes representation via `toString` |
| `instance` | `hashCode` | `()` | `int` | Evaluates boolean predicate `hashCode` on `CustomDataManager` |
| `instance` | `getClass` | `()` | `Class` | Retrieves `Class` property from `CustomDataManager` |
| `instance` | `notify` | `()` | `void` | Performs notify operation |
| `instance` | `notifyAll` | `()` | `void` | Performs notify all operation |
| `instance` | `wait` | `(arg0: long)` | `void` | Performs wait operation |
| `instance` | `wait` | `(arg0: long, arg1: int)` | `void` | Performs wait operation |
| `instance` | `wait` | `()` | `void` | Performs wait operation |
| `static` | `update` | `(arg0: CustomDataInfo)` | `void` | Performs update operation |
| `static` | `update` | `(arg0: String, arg1: String, arg2: String, arg3: int)` | `void` | Performs update operation |
| `static` | `clear` | `(arg0: String)` | `void` | Removes/resets elements via `clear` |
| `static` | `add` | `(arg0: CustomDataInfo)` | `void` | Appends/registers element via `add` |
| `static` | `add` | `(arg0: SCustomIndicator)` | `void` | Appends/registers element via `add` |
| `static` | `add` | `(arg0: String, arg1: String, arg2: int)` | `void` | Appends/registers element via `add` |
| `static` | `list` | `()` | `Collection` | Performs list operation |
| `static` | `init` | `(arg0: String)` | `void` | Instantiates/initializes `init` resource |
| `static` | `delete` | `(arg0: String)` | `void` | Performs delete operation |
| `static` | `getDataInfo` | `(arg0: String)` | `CustomDataInfo` | Retrieves `DataInfo` property from `CustomDataManager` |
| `static` | `updateData` | `(arg0: String, arg1: long, arg2: long, arg3: int, arg4: String)` | `void` | Performs update data operation |
| `static` | `checkDataExists` | `(arg0: String)` | `boolean` | Performs check data exists operation |
| `static` | `getDataFileName` | `(arg0: String)` | `String` | Retrieves `DataFileName` property from `CustomDataManager` |
| `static` | `checkData` | `()` | `void` | Performs check data operation |
| `static` | `fixFilename` | `(arg0: String)` | `String` | Performs fix filename operation |
| `static` | `getCDataIndyId` | `(arg0: String)` | `String` | Retrieves `CDataIndyId` property from `CustomDataManager` |
| `static` | `createCDataValues` | `(arg0: int, arg1: CustomDataInfo)` | `String` | Instantiates/initializes `createCDataValues` resource |
| `static` | `addCDataIndySourceCodes` | `(arg0: Element)` | `void` | Appends/registers element via `addCDataIndySourceCodes` |
| `static` | `updateConfigFile` | `()` | `void` | Performs update config file operation |
| `static` | `configFileExists` | `()` | `boolean` | Performs config file exists operation |
| `static` | `removeDataFile` | `(arg0: String)` | `void` | Removes/resets elements via `removeDataFile` |
| `static` | `upgradeLegacyCotEL` | `(arg0: String)` | `String` | Performs upgrade legacy cot el operation |
| `static` | `cotELCode` | `(arg0: String, arg1: int)` | `String` | Performs cot el code operation |

---

### `CustomDataTypes`
- **Full Qualified Name:** `com.strategyquant.datalib.customData.CustomDataTypes`
- **Primary Job / Responsibility:** Market data abstraction and time-series container (`CustomDataTypes`).

#### Fields
| Scope | Field Name | Type |
| :--- | :--- | :--- |
| `static` | `IndicatorValueNumber` | `byte` |
| `static` | `IndicatorValueNumberKey` | `String` |
| `static` | `IndicatorValueNumberName` | `String` |
| `static` | `IndicatorValuePrice` | `byte` |
| `static` | `IndicatorValuePriceKey` | `String` |
| `static` | `IndicatorValuePriceName` | `String` |
| `static` | `IndicatorValuePriceRange` | `byte` |
| `static` | `IndicatorValuePriceRangeKey` | `String` |
| `static` | `IndicatorValuePriceRangeName` | `String` |
| `static` | `SignalValueAction` | `byte` |
| `static` | `SignalValueActionKey` | `String` |
| `static` | `SignalValueBoolean` | `byte` |
| `static` | `SignalValueBooleanKey` | `String` |
| `static` | `SignalValueBooleanName` | `String` |

#### Methods & Functions
| Modifiers | Method Name | Parameter Signatures | Return Type | Functional Description / Job |
| :--- | :--- | :--- | :--- | :--- |
| `instance` | `equals` | `(arg0: Object)` | `boolean` | Performs equals operation |
| `instance` | `toString` | `()` | `String` | Converts/serializes representation via `toString` |
| `instance` | `hashCode` | `()` | `int` | Evaluates boolean predicate `hashCode` on `CustomDataTypes` |
| `instance` | `getClass` | `()` | `Class` | Retrieves `Class` property from `CustomDataTypes` |
| `instance` | `notify` | `()` | `void` | Performs notify operation |
| `instance` | `notifyAll` | `()` | `void` | Performs notify all operation |
| `instance` | `wait` | `(arg0: long)` | `void` | Performs wait operation |
| `instance` | `wait` | `(arg0: long, arg1: int)` | `void` | Performs wait operation |
| `instance` | `wait` | `()` | `void` | Performs wait operation |
| `static` | `toString` | `(arg0: byte)` | `String` | Converts/serializes representation via `toString` |
| `static` | `translateDataType` | `(arg0: byte)` | `String` | Performs translate data type operation |
| `static` | `availableDataTypes` | `()` | `List` | Performs available data types operation |

---

### `CTCustomIndicator`
- **Full Qualified Name:** `com.strategyquant.datalib.customData.ct.CTCustomIndicator`
- **Primary Job / Responsibility:** Market data abstraction and time-series container (`CTCustomIndicator`).

#### Fields
| Scope | Field Name | Type |
| :--- | :--- | :--- |
| `instance` | `fileName` | `String` |
| `instance` | `longName` | `String` |
| `instance` | `outputs` | `Map` |
| `instance` | `params` | `List` |
| `instance` | `returnType` | `String` |
| `instance` | `shortName` | `String` |

#### Methods & Functions
| Modifiers | Method Name | Parameter Signatures | Return Type | Functional Description / Job |
| :--- | :--- | :--- | :--- | :--- |
| `instance` | `equals` | `(arg0: Object)` | `boolean` | Performs equals operation |
| `instance` | `toString` | `()` | `String` | Converts/serializes representation via `toString` |
| `instance` | `hashCode` | `()` | `int` | Evaluates boolean predicate `hashCode` on `CTCustomIndicator` |
| `instance` | `getClass` | `()` | `Class` | Retrieves `Class` property from `CTCustomIndicator` |
| `instance` | `notify` | `()` | `void` | Performs notify operation |
| `instance` | `notifyAll` | `()` | `void` | Performs notify all operation |
| `instance` | `wait` | `(arg0: long)` | `void` | Performs wait operation |
| `instance` | `wait` | `(arg0: long, arg1: int)` | `void` | Performs wait operation |
| `instance` | `wait` | `()` | `void` | Performs wait operation |

---

### `CTCustomIndicatorOutput`
- **Full Qualified Name:** `com.strategyquant.datalib.customData.ct.CTCustomIndicatorOutput`
- **Primary Job / Responsibility:** Market data abstraction and time-series container (`CTCustomIndicatorOutput`).

#### Fields
| Scope | Field Name | Type |
| :--- | :--- | :--- |
| `instance` | `el` | `String` |
| `instance` | `jf` | `String` |
| `instance` | `mt4` | `String` |
| `instance` | `mt5` | `String` |
| `instance` | `name` | `String` |

#### Methods & Functions
| Modifiers | Method Name | Parameter Signatures | Return Type | Functional Description / Job |
| :--- | :--- | :--- | :--- | :--- |
| `instance` | `equals` | `(arg0: Object)` | `boolean` | Performs equals operation |
| `instance` | `toString` | `()` | `String` | Converts/serializes representation via `toString` |
| `instance` | `hashCode` | `()` | `int` | Evaluates boolean predicate `hashCode` on `CTCustomIndicatorOutput` |
| `instance` | `getClass` | `()` | `Class` | Retrieves `Class` property from `CTCustomIndicatorOutput` |
| `instance` | `notify` | `()` | `void` | Performs notify operation |
| `instance` | `notifyAll` | `()` | `void` | Performs notify all operation |
| `instance` | `wait` | `(arg0: long)` | `void` | Performs wait operation |
| `instance` | `wait` | `(arg0: long, arg1: int)` | `void` | Performs wait operation |
| `instance` | `wait` | `()` | `void` | Performs wait operation |

---

### `CTCustomIndicatorParam`
- **Full Qualified Name:** `com.strategyquant.datalib.customData.ct.CTCustomIndicatorParam`
- **Primary Job / Responsibility:** Market data abstraction and time-series container (`CTCustomIndicatorParam`).

#### Fields
| Scope | Field Name | Type |
| :--- | :--- | :--- |
| `instance` | `name` | `String` |
| `instance` | `type` | `String` |
| `instance` | `value` | `String` |

#### Methods & Functions
| Modifiers | Method Name | Parameter Signatures | Return Type | Functional Description / Job |
| :--- | :--- | :--- | :--- | :--- |
| `instance` | `equals` | `(arg0: Object)` | `boolean` | Performs equals operation |
| `instance` | `toString` | `()` | `String` | Converts/serializes representation via `toString` |
| `instance` | `hashCode` | `()` | `int` | Evaluates boolean predicate `hashCode` on `CTCustomIndicatorParam` |
| `instance` | `getClass` | `()` | `Class` | Retrieves `Class` property from `CTCustomIndicatorParam` |
| `instance` | `notify` | `()` | `void` | Performs notify operation |
| `instance` | `notifyAll` | `()` | `void` | Performs notify all operation |
| `instance` | `wait` | `(arg0: long)` | `void` | Performs wait operation |
| `instance` | `wait` | `(arg0: long, arg1: int)` | `void` | Performs wait operation |
| `instance` | `wait` | `()` | `void` | Performs wait operation |

---

### `CTCustomIndicators`
- **Full Qualified Name:** `com.strategyquant.datalib.customData.ct.CTCustomIndicators`
- **Primary Job / Responsibility:** Market data abstraction and time-series container (`CTCustomIndicators`).

#### Fields
| Scope | Field Name | Type |
| :--- | :--- | :--- |
| `static` | `Log` | `Logger` |

#### Methods & Functions
| Modifiers | Method Name | Parameter Signatures | Return Type | Functional Description / Job |
| :--- | :--- | :--- | :--- | :--- |
| `instance` | `addSourceCodesToItem` | `(arg0: Element, arg1: String)` | `void` | Appends/registers element via `addSourceCodesToItem` |
| `instance` | `remove` | `(arg0: Object)` | `boolean` | Removes/resets elements via `remove` |
| `instance` | `remove` | `(arg0: Object, arg1: Object)` | `boolean` | Removes/resets elements via `remove` |
| `instance` | `size` | `()` | `int` | Performs size operation |
| `instance` | `get` | `(arg0: Object)` | `Object` | Retrieves `` property from `CTCustomIndicators` |
| `instance` | `put` | `(arg0: Object, arg1: Object)` | `Object` | Performs put operation |
| `instance` | `values` | `()` | `Collection` | Performs values operation |
| `instance` | `clone` | `()` | `Object` | Performs clone operation |
| `instance` | `clear` | `()` | `void` | Removes/resets elements via `clear` |
| `instance` | `isEmpty` | `()` | `boolean` | Evaluates boolean predicate `isEmpty` on `CTCustomIndicators` |
| `instance` | `replace` | `(arg0: Object, arg1: Object)` | `boolean` | Performs replace operation |
| `instance` | `replace` | `(arg0: Object, arg1: Object, arg2: Object)` | `boolean` | Performs replace operation |
| `instance` | `replaceAll` | `(arg0: BiFunction)` | `void` | Performs replace all operation |
| `instance` | `merge` | `(arg0: Object, arg1: Object, arg2: BiFunction)` | `Object` | Performs merge operation |
| `instance` | `entrySet` | `()` | `Set` | Performs entry set operation |
| `instance` | `putAll` | `(arg0: Map)` | `void` | Performs put all operation |
| `instance` | `putIfAbsent` | `(arg0: Object, arg1: Object)` | `Object` | Performs put if absent operation |
| `instance` | `compute` | `(arg0: Object, arg1: BiFunction)` | `Object` | Executes calculation for `compute` |
| `instance` | `computeIfAbsent` | `(arg0: Object, arg1: Function)` | `Object` | Executes calculation for `computeIfAbsent` |
| `instance` | `forEach` | `(arg0: BiConsumer)` | `void` | Performs for each operation |
| `instance` | `keySet` | `()` | `Set` | Performs key set operation |
| `instance` | `containsValue` | `(arg0: Object)` | `boolean` | Performs contains value operation |
| `instance` | `containsKey` | `(arg0: Object)` | `boolean` | Performs contains key operation |
| `instance` | `getOrDefault` | `(arg0: Object, arg1: Object)` | `Object` | Retrieves `OrDefault` property from `CTCustomIndicators` |
| `instance` | `computeIfPresent` | `(arg0: Object, arg1: BiFunction)` | `Object` | Executes calculation for `computeIfPresent` |
| `instance` | `equals` | `(arg0: Object)` | `boolean` | Performs equals operation |
| `instance` | `toString` | `()` | `String` | Converts/serializes representation via `toString` |
| `instance` | `hashCode` | `()` | `int` | Evaluates boolean predicate `hashCode` on `CTCustomIndicators` |
| `instance` | `getClass` | `()` | `Class` | Retrieves `Class` property from `CTCustomIndicators` |
| `instance` | `notify` | `()` | `void` | Performs notify operation |
| `instance` | `notifyAll` | `()` | `void` | Performs notify all operation |
| `instance` | `wait` | `(arg0: long)` | `void` | Performs wait operation |
| `instance` | `wait` | `(arg0: long, arg1: int)` | `void` | Performs wait operation |
| `instance` | `wait` | `()` | `void` | Performs wait operation |
| `static` | `newHashMap` | `(arg0: int)` | `HashMap` | Performs new hash map operation |

---

## Subsystem: `darwinex`

### `DarwinexUtils`
- **Full Qualified Name:** `com.strategyquant.datalib.darwinex.DarwinexUtils`
- **Primary Job / Responsibility:** Market data abstraction and time-series container (`DarwinexUtils`).

#### Fields
| Scope | Field Name | Type |
| :--- | :--- | :--- |
| `static` | `Log` | `Logger` |

#### Methods & Functions
| Modifiers | Method Name | Parameter Signatures | Return Type | Functional Description / Job |
| :--- | :--- | :--- | :--- | :--- |
| `instance` | `equals` | `(arg0: Object)` | `boolean` | Performs equals operation |
| `instance` | `toString` | `()` | `String` | Converts/serializes representation via `toString` |
| `instance` | `hashCode` | `()` | `int` | Evaluates boolean predicate `hashCode` on `DarwinexUtils` |
| `instance` | `getClass` | `()` | `Class` | Retrieves `Class` property from `DarwinexUtils` |
| `instance` | `notify` | `()` | `void` | Performs notify operation |
| `instance` | `notifyAll` | `()` | `void` | Performs notify all operation |
| `instance` | `wait` | `(arg0: long)` | `void` | Performs wait operation |
| `instance` | `wait` | `(arg0: long, arg1: int)` | `void` | Performs wait operation |
| `instance` | `wait` | `()` | `void` | Performs wait operation |
| `static` | `getTickData` | `(arg0: File, arg1: Long2ObjectAVLTreeMap, arg2: boolean)` | `void` | Retrieves `TickData` property from `DarwinexUtils` |

---

## Subsystem: `data`

### `BatchProgressController`
- **Full Qualified Name:** `com.strategyquant.datalib.data.BatchProgressController`
- **Primary Job / Responsibility:** Market data abstraction and time-series container (`BatchProgressController`).

#### Methods & Functions
| Modifiers | Method Name | Parameter Signatures | Return Type | Functional Description / Job |
| :--- | :--- | :--- | :--- | :--- |
| `instance` | `finished` | `()` | `void` | Performs finished operation |
| `instance` | `updateProgress` | `(arg0: int, arg1: int, arg2: String)` | `void` | Performs update progress operation |
| `instance` | `isCancel` | `()` | `boolean` | Evaluates boolean predicate `isCancel` on `BatchProgressController` |

---

### `DataCloner`
- **Full Qualified Name:** `com.strategyquant.datalib.data.DataCloner`
- **Primary Job / Responsibility:** Market data abstraction and time-series container (`DataCloner`).

#### Fields
| Scope | Field Name | Type |
| :--- | :--- | :--- |
| `static` | `Log` | `Logger` |

#### Methods & Functions
| Modifiers | Method Name | Parameter Signatures | Return Type | Functional Description / Job |
| :--- | :--- | :--- | :--- | :--- |
| `instance` | `cancel` | `()` | `void` | Evaluates boolean predicate `cancel` on `DataCloner` |
| `instance` | `isRunning` | `()` | `boolean` | Evaluates boolean predicate `isRunning` on `DataCloner` |
| `instance` | `pause` | `()` | `void` | Performs pause operation |
| `instance` | `restart` | `()` | `void` | Performs restart operation |
| `instance` | `cloneToTimezone` | `(arg0: String, arg1: String, arg2: String, arg3: int, arg4: boolean, arg5: TickerDto, arg6: IProgressListener)` | `void` | Performs clone to timezone operation |
| `instance` | `createSymbol` | `(arg0: String, arg1: DataInfo)` | `void` | Instantiates/initializes `createSymbol` resource |
| `instance` | `equals` | `(arg0: Object)` | `boolean` | Performs equals operation |
| `instance` | `toString` | `()` | `String` | Converts/serializes representation via `toString` |
| `instance` | `hashCode` | `()` | `int` | Evaluates boolean predicate `hashCode` on `DataCloner` |
| `instance` | `getClass` | `()` | `Class` | Retrieves `Class` property from `DataCloner` |
| `instance` | `notify` | `()` | `void` | Performs notify operation |
| `instance` | `notifyAll` | `()` | `void` | Performs notify all operation |
| `instance` | `wait` | `(arg0: long)` | `void` | Performs wait operation |
| `instance` | `wait` | `(arg0: long, arg1: int)` | `void` | Performs wait operation |
| `instance` | `wait` | `()` | `void` | Performs wait operation |

---

### `DataComparator`
- **Full Qualified Name:** `com.strategyquant.datalib.data.DataComparator`
- **Primary Job / Responsibility:** Market data abstraction and time-series container (`DataComparator`).

#### Methods & Functions
| Modifiers | Method Name | Parameter Signatures | Return Type | Functional Description / Job |
| :--- | :--- | :--- | :--- | :--- |
| `instance` | `compare` | `(arg0: DataInfo, arg1: DataInfo)` | `int` | Performs compare operation |
| `instance` | `compare` | `(arg0: Object, arg1: Object)` | `int` | Performs compare operation |
| `instance` | `equals` | `(arg0: Object)` | `boolean` | Performs equals operation |
| `instance` | `toString` | `()` | `String` | Converts/serializes representation via `toString` |
| `instance` | `hashCode` | `()` | `int` | Evaluates boolean predicate `hashCode` on `DataComparator` |
| `instance` | `getClass` | `()` | `Class` | Retrieves `Class` property from `DataComparator` |
| `instance` | `notify` | `()` | `void` | Performs notify operation |
| `instance` | `notifyAll` | `()` | `void` | Performs notify all operation |
| `instance` | `wait` | `(arg0: long)` | `void` | Performs wait operation |
| `instance` | `wait` | `(arg0: long, arg1: int)` | `void` | Performs wait operation |
| `instance` | `wait` | `()` | `void` | Performs wait operation |
| `instance` | `reversed` | `()` | `Comparator` | Performs reversed operation |
| `instance` | `thenComparing` | `(arg0: Function, arg1: Comparator)` | `Comparator` | Performs then comparing operation |
| `instance` | `thenComparing` | `(arg0: Comparator)` | `Comparator` | Performs then comparing operation |
| `instance` | `thenComparing` | `(arg0: Function)` | `Comparator` | Performs then comparing operation |
| `instance` | `thenComparingInt` | `(arg0: ToIntFunction)` | `Comparator` | Performs then comparing int operation |
| `instance` | `thenComparingLong` | `(arg0: ToLongFunction)` | `Comparator` | Performs then comparing long operation |
| `instance` | `thenComparingDouble` | `(arg0: ToDoubleFunction)` | `Comparator` | Performs then comparing double operation |

---

### `DataDb`
- **Full Qualified Name:** `com.strategyquant.datalib.data.DataDb`
- **Primary Job / Responsibility:** Market data abstraction and time-series container (`DataDb`).

#### Fields
| Scope | Field Name | Type |
| :--- | :--- | :--- |
| `static` | `Log` | `Logger` |

#### Methods & Functions
| Modifiers | Method Name | Parameter Signatures | Return Type | Functional Description / Job |
| :--- | :--- | :--- | :--- | :--- |
| `instance` | `initDatabase` | `()` | `void` | Instantiates/initializes `initDatabase` resource |
| `instance` | `close` | `(arg0: ResultSet)` | `void` | Performs close operation |
| `instance` | `close` | `(arg0: Statement)` | `void` | Performs close operation |
| `instance` | `close` | `(arg0: Connection)` | `void` | Performs close operation |
| `instance` | `getConnection` | `()` | `Connection` | Retrieves `Connection` property from `DataDb` |
| `instance` | `sqlCheckRecordExists` | `(arg0: Connection, arg1: String)` | `boolean` | Performs sql check record exists operation |
| `instance` | `sqlCommand` | `(arg0: Connection, arg1: PreparedStatement)` | `void` | Performs sql command operation |
| `instance` | `sqlCommand` | `(arg0: String)` | `void` | Performs sql command operation |
| `instance` | `sqlCommand` | `(arg0: Connection, arg1: String)` | `void` | Performs sql command operation |
| `instance` | `sqlInsertReturnAutoId` | `(arg0: Connection, arg1: PreparedStatement)` | `int` | Performs sql insert return auto id operation |
| `instance` | `sqlInsertReturnAutoId` | `(arg0: Connection, arg1: String)` | `int` | Performs sql insert return auto id operation |
| `instance` | `_getDirectory` | `()` | `String` | Performs get directory operation |
| `instance` | `getDbPath` | `()` | `String` | Retrieves `DbPath` property from `DataDb` |
| `instance` | `isDbExist` | `()` | `boolean` | Evaluates boolean predicate `isDbExist` on `DataDb` |
| `instance` | `columnExists` | `(arg0: String, arg1: String)` | `boolean` | Performs column exists operation |
| `instance` | `tableExists` | `(arg0: String)` | `boolean` | Performs table exists operation |
| `instance` | `equals` | `(arg0: Object)` | `boolean` | Performs equals operation |
| `instance` | `toString` | `()` | `String` | Converts/serializes representation via `toString` |
| `instance` | `hashCode` | `()` | `int` | Evaluates boolean predicate `hashCode` on `DataDb` |
| `instance` | `getClass` | `()` | `Class` | Retrieves `Class` property from `DataDb` |
| `instance` | `notify` | `()` | `void` | Performs notify operation |
| `instance` | `notifyAll` | `()` | `void` | Performs notify all operation |
| `instance` | `wait` | `(arg0: long)` | `void` | Performs wait operation |
| `instance` | `wait` | `(arg0: long, arg1: int)` | `void` | Performs wait operation |
| `instance` | `wait` | `()` | `void` | Performs wait operation |

---

### `DataException`
- **Full Qualified Name:** `com.strategyquant.datalib.data.DataException`
- **Primary Job / Responsibility:** Market data abstraction and time-series container (`DataException`).

#### Fields
| Scope | Field Name | Type |
| :--- | :--- | :--- |
| `static` | `BARTYPE` | `int` |
| `static` | `CONNECTION` | `int` |
| `static` | `DATA` | `int` |
| `static` | `INSTRUMENT` | `int` |
| `static` | `SERIES` | `int` |
| `static` | `TIMEFRAME` | `int` |

#### Methods & Functions
| Modifiers | Method Name | Parameter Signatures | Return Type | Functional Description / Job |
| :--- | :--- | :--- | :--- | :--- |
| `instance` | `printStackTrace` | `()` | `void` | Performs print stack trace operation |
| `instance` | `printStackTrace` | `(arg0: PrintWriter)` | `void` | Performs print stack trace operation |
| `instance` | `printStackTrace` | `(arg0: PrintStream)` | `void` | Performs print stack trace operation |
| `instance` | `getStackTrace` | `()` | `StackTraceElement[]` | Retrieves `StackTrace` property from `DataException` |
| `instance` | `fillInStackTrace` | `()` | `Throwable` | Performs fill in stack trace operation |
| `instance` | `getCause` | `()` | `Throwable` | Retrieves `Cause` property from `DataException` |
| `instance` | `initCause` | `(arg0: Throwable)` | `Throwable` | Instantiates/initializes `initCause` resource |
| `instance` | `toString` | `()` | `String` | Converts/serializes representation via `toString` |
| `instance` | `getMessage` | `()` | `String` | Retrieves `Message` property from `DataException` |
| `instance` | `getSuppressed` | `()` | `Throwable[]` | Retrieves `Suppressed` property from `DataException` |
| `instance` | `getLocalizedMessage` | `()` | `String` | Retrieves `LocalizedMessage` property from `DataException` |
| `instance` | `setStackTrace` | `(arg0: StackTraceElement[])` | `void` | Sets `StackTrace` configuration/state on `DataException` |
| `instance` | `addSuppressed` | `(arg0: Throwable)` | `void` | Appends/registers element via `addSuppressed` |
| `instance` | `equals` | `(arg0: Object)` | `boolean` | Performs equals operation |
| `instance` | `hashCode` | `()` | `int` | Evaluates boolean predicate `hashCode` on `DataException` |
| `instance` | `getClass` | `()` | `Class` | Retrieves `Class` property from `DataException` |
| `instance` | `notify` | `()` | `void` | Performs notify operation |
| `instance` | `notifyAll` | `()` | `void` | Performs notify all operation |
| `instance` | `wait` | `(arg0: long)` | `void` | Performs wait operation |
| `instance` | `wait` | `(arg0: long, arg1: int)` | `void` | Performs wait operation |
| `instance` | `wait` | `()` | `void` | Performs wait operation |

---

### `DataExporter`
- **Full Qualified Name:** `com.strategyquant.datalib.data.DataExporter`
- **Primary Job / Responsibility:** Market data abstraction and time-series container (`DataExporter`).

#### Methods & Functions
| Modifiers | Method Name | Parameter Signatures | Return Type | Functional Description / Job |
| :--- | :--- | :--- | :--- | :--- |
| `instance` | `exportTick` | `(arg0: String, arg1: long, arg2: long, arg3: String)` | `void` | Performs export tick operation |
| `instance` | `exportM1` | `(arg0: String, arg1: long, arg2: long, arg3: String)` | `void` | Performs export m 1 operation |
| `instance` | `equals` | `(arg0: Object)` | `boolean` | Performs equals operation |
| `instance` | `toString` | `()` | `String` | Converts/serializes representation via `toString` |
| `instance` | `hashCode` | `()` | `int` | Evaluates boolean predicate `hashCode` on `DataExporter` |
| `instance` | `getClass` | `()` | `Class` | Retrieves `Class` property from `DataExporter` |
| `instance` | `notify` | `()` | `void` | Performs notify operation |
| `instance` | `notifyAll` | `()` | `void` | Performs notify all operation |
| `instance` | `wait` | `(arg0: long)` | `void` | Performs wait operation |
| `instance` | `wait` | `(arg0: long, arg1: int)` | `void` | Performs wait operation |
| `instance` | `wait` | `()` | `void` | Performs wait operation |

---

### `DataFolderSweeper`
- **Full Qualified Name:** `com.strategyquant.datalib.data.DataFolderSweeper`
- **Primary Job / Responsibility:** Market data abstraction and time-series container (`DataFolderSweeper`).

#### Fields
| Scope | Field Name | Type |
| :--- | :--- | :--- |
| `static` | `Log` | `Logger` |

#### Methods & Functions
| Modifiers | Method Name | Parameter Signatures | Return Type | Functional Description / Job |
| :--- | :--- | :--- | :--- | :--- |
| `instance` | `init` | `()` | `void` | Instantiates/initializes `init` resource |
| `instance` | `setSkip` | `(arg0: boolean)` | `void` | Sets `Skip` configuration/state on `DataFolderSweeper` |
| `instance` | `equals` | `(arg0: Object)` | `boolean` | Performs equals operation |
| `instance` | `toString` | `()` | `String` | Converts/serializes representation via `toString` |
| `instance` | `hashCode` | `()` | `int` | Evaluates boolean predicate `hashCode` on `DataFolderSweeper` |
| `instance` | `getClass` | `()` | `Class` | Retrieves `Class` property from `DataFolderSweeper` |
| `instance` | `notify` | `()` | `void` | Performs notify operation |
| `instance` | `notifyAll` | `()` | `void` | Performs notify all operation |
| `instance` | `wait` | `(arg0: long)` | `void` | Performs wait operation |
| `instance` | `wait` | `(arg0: long, arg1: int)` | `void` | Performs wait operation |
| `instance` | `wait` | `()` | `void` | Performs wait operation |
| `static` | `get` | `()` | `DataFolderSweeper` | Retrieves `` property from `DataFolderSweeper` |

---

### `DataInfoCache`
- **Full Qualified Name:** `com.strategyquant.datalib.data.DataInfoCache`
- **Primary Job / Responsibility:** Market data abstraction and time-series container (`DataInfoCache`).

#### Fields
| Scope | Field Name | Type |
| :--- | :--- | :--- |
| `instance` | `lastTimeUpdated` | `long` |

#### Methods & Functions
| Modifiers | Method Name | Parameter Signatures | Return Type | Functional Description / Job |
| :--- | :--- | :--- | :--- | :--- |
| `instance` | `remove` | `(arg0: Object)` | `boolean` | Removes/resets elements via `remove` |
| `instance` | `remove` | `(arg0: Object, arg1: Object)` | `boolean` | Removes/resets elements via `remove` |
| `instance` | `size` | `()` | `int` | Performs size operation |
| `instance` | `get` | `(arg0: Object)` | `Object` | Retrieves `` property from `DataInfoCache` |
| `instance` | `put` | `(arg0: Object, arg1: Object)` | `Object` | Performs put operation |
| `instance` | `values` | `()` | `Collection` | Performs values operation |
| `instance` | `clone` | `()` | `Object` | Performs clone operation |
| `instance` | `clear` | `()` | `void` | Removes/resets elements via `clear` |
| `instance` | `isEmpty` | `()` | `boolean` | Evaluates boolean predicate `isEmpty` on `DataInfoCache` |
| `instance` | `replace` | `(arg0: Object, arg1: Object)` | `boolean` | Performs replace operation |
| `instance` | `replace` | `(arg0: Object, arg1: Object, arg2: Object)` | `boolean` | Performs replace operation |
| `instance` | `replaceAll` | `(arg0: BiFunction)` | `void` | Performs replace all operation |
| `instance` | `merge` | `(arg0: Object, arg1: Object, arg2: BiFunction)` | `Object` | Performs merge operation |
| `instance` | `entrySet` | `()` | `Set` | Performs entry set operation |
| `instance` | `putAll` | `(arg0: Map)` | `void` | Performs put all operation |
| `instance` | `putIfAbsent` | `(arg0: Object, arg1: Object)` | `Object` | Performs put if absent operation |
| `instance` | `compute` | `(arg0: Object, arg1: BiFunction)` | `Object` | Executes calculation for `compute` |
| `instance` | `computeIfAbsent` | `(arg0: Object, arg1: Function)` | `Object` | Executes calculation for `computeIfAbsent` |
| `instance` | `forEach` | `(arg0: BiConsumer)` | `void` | Performs for each operation |
| `instance` | `keySet` | `()` | `Set` | Performs key set operation |
| `instance` | `containsValue` | `(arg0: Object)` | `boolean` | Performs contains value operation |
| `instance` | `containsKey` | `(arg0: Object)` | `boolean` | Performs contains key operation |
| `instance` | `getOrDefault` | `(arg0: Object, arg1: Object)` | `Object` | Retrieves `OrDefault` property from `DataInfoCache` |
| `instance` | `computeIfPresent` | `(arg0: Object, arg1: BiFunction)` | `Object` | Executes calculation for `computeIfPresent` |
| `instance` | `equals` | `(arg0: Object)` | `boolean` | Performs equals operation |
| `instance` | `toString` | `()` | `String` | Converts/serializes representation via `toString` |
| `instance` | `hashCode` | `()` | `int` | Evaluates boolean predicate `hashCode` on `DataInfoCache` |
| `instance` | `getClass` | `()` | `Class` | Retrieves `Class` property from `DataInfoCache` |
| `instance` | `notify` | `()` | `void` | Performs notify operation |
| `instance` | `notifyAll` | `()` | `void` | Performs notify all operation |
| `instance` | `wait` | `(arg0: long)` | `void` | Performs wait operation |
| `instance` | `wait` | `(arg0: long, arg1: int)` | `void` | Performs wait operation |
| `instance` | `wait` | `()` | `void` | Performs wait operation |
| `static` | `newHashMap` | `(arg0: int)` | `HashMap` | Performs new hash map operation |

---

### `DataManager`
- **Full Qualified Name:** `com.strategyquant.datalib.data.DataManager`
- **Primary Job / Responsibility:** Market data abstraction and time-series container (`DataManager`).

#### Fields
| Scope | Field Name | Type |
| :--- | :--- | :--- |
| `static` | `EQUITY_FOLDER` | `String` |
| `static` | `FUTURES_FOLDER` | `String` |
| `static` | `Log` | `Logger` |
| `static` | `SpreadTypePips` | `String` |
| `static` | `SpreadTypePoints` | `String` |
| `static` | `SpreadTypeReal` | `String` |

#### Methods & Functions
| Modifiers | Method Name | Parameter Signatures | Return Type | Functional Description / Job |
| :--- | :--- | :--- | :--- | :--- |
| `instance` | `refreshDataInfoCache` | `()` | `void` | Performs refresh data info cache operation |
| `instance` | `initDatabase` | `()` | `void` | Instantiates/initializes `initDatabase` resource |
| `instance` | `_updateData` | `(arg0: String, arg1: String, arg2: long, arg3: long, arg4: int, arg5: long, arg6: int, arg7: String, arg8: String, arg9: int, arg10: boolean)` | `void` | Performs update data operation |
| `instance` | `_addData` | `(arg0: String, arg1: String, arg2: String, arg3: int, arg4: int, arg5: String, arg6: String, arg7: int, arg8: int)` | `void` | Performs add data operation |
| `instance` | `_addDataInBatch` | `(arg0: String, arg1: List, arg2: BatchProgressController)` | `void` | Performs add data in batch operation |
| `instance` | `_getSymbolsForInstrument` | `(arg0: String)` | `ArrayList` | Performs get symbols for instrument operation |
| `instance` | `_updateInstrument` | `(arg0: String, arg1: String, arg2: String)` | `void` | Performs update instrument operation |
| `instance` | `_updateInstrumentSwap` | `(arg0: String, arg1: String, arg2: String, arg3: String)` | `void` | Performs update instrument swap operation |
| `instance` | `_updateSecondsRecords` | `(arg0: String, arg1: String, arg2: long)` | `void` | Performs update seconds records operation |
| `instance` | `_renameData` | `(arg0: String, arg1: String, arg2: String)` | `void` | Performs rename data operation |
| `instance` | `_renameUnderlayingData` | `(arg0: String, arg1: String, arg2: String)` | `String` | Performs rename underlaying data operation |
| `instance` | `_getDataLoader` | `(arg0: ChartDef, arg1: int, arg2: IStopPauseStatus)` | `IDataLoader` | Performs get data loader operation |
| `instance` | `_isFilenameValid` | `(arg0: String)` | `boolean` | Performs is filename valid operation |
| `instance` | `removeRecordFromCacheForInstrument` | `(arg0: String)` | `void` | Removes/resets elements via `removeRecordFromCacheForInstrument` |
| `instance` | `close` | `(arg0: ResultSet)` | `void` | Performs close operation |
| `instance` | `close` | `(arg0: Statement)` | `void` | Performs close operation |
| `instance` | `close` | `(arg0: Connection)` | `void` | Performs close operation |
| `instance` | `getConnection` | `()` | `Connection` | Retrieves `Connection` property from `DataManager` |
| `instance` | `sqlCheckRecordExists` | `(arg0: Connection, arg1: String)` | `boolean` | Performs sql check record exists operation |
| `instance` | `sqlCommand` | `(arg0: Connection, arg1: PreparedStatement)` | `void` | Performs sql command operation |
| `instance` | `sqlCommand` | `(arg0: String)` | `void` | Performs sql command operation |
| `instance` | `sqlCommand` | `(arg0: Connection, arg1: String)` | `void` | Performs sql command operation |
| `instance` | `sqlInsertReturnAutoId` | `(arg0: Connection, arg1: PreparedStatement)` | `int` | Performs sql insert return auto id operation |
| `instance` | `sqlInsertReturnAutoId` | `(arg0: Connection, arg1: String)` | `int` | Performs sql insert return auto id operation |
| `instance` | `_getDirectory` | `()` | `String` | Performs get directory operation |
| `instance` | `getDbPath` | `()` | `String` | Retrieves `DbPath` property from `DataManager` |
| `instance` | `isDbExist` | `()` | `boolean` | Evaluates boolean predicate `isDbExist` on `DataManager` |
| `instance` | `columnExists` | `(arg0: String, arg1: String)` | `boolean` | Performs column exists operation |
| `instance` | `tableExists` | `(arg0: String)` | `boolean` | Performs table exists operation |
| `instance` | `equals` | `(arg0: Object)` | `boolean` | Performs equals operation |
| `instance` | `toString` | `()` | `String` | Converts/serializes representation via `toString` |
| `instance` | `hashCode` | `()` | `int` | Evaluates boolean predicate `hashCode` on `DataManager` |
| `instance` | `getClass` | `()` | `Class` | Retrieves `Class` property from `DataManager` |
| `instance` | `notify` | `()` | `void` | Performs notify operation |
| `instance` | `notifyAll` | `()` | `void` | Performs notify all operation |
| `instance` | `wait` | `(arg0: long)` | `void` | Performs wait operation |
| `instance` | `wait` | `(arg0: long, arg1: int)` | `void` | Performs wait operation |
| `instance` | `wait` | `()` | `void` | Performs wait operation |
| `static` | `get` | `()` | `DataManager` | Retrieves `` property from `DataManager` |
| `static` | `list` | `()` | `ArrayList` | Performs list operation |
| `static` | `init` | `(arg0: String)` | `void` | Instantiates/initializes `init` resource |
| `static` | `getDataInfo` | `(arg0: String, arg1: String)` | `DataInfo` | Retrieves `DataInfo` property from `DataManager` |
| `static` | `getDataInfo` | `(arg0: String, arg1: String, arg2: boolean)` | `DataInfo` | Retrieves `DataInfo` property from `DataManager` |
| `static` | `getDataInfo` | `(arg0: String, arg1: int)` | `DataInfo` | Retrieves `DataInfo` property from `DataManager` |
| `static` | `updateData` | `(arg0: String, arg1: String, arg2: long, arg3: long, arg4: int, arg5: long, arg6: int, arg7: String, arg8: String, arg9: int, arg10: boolean)` | `void` | Performs update data operation |
| `static` | `updateData` | `(arg0: String, arg1: String, arg2: long, arg3: long, arg4: int, arg5: long, arg6: int, arg7: String, arg8: String)` | `void` | Performs update data operation |
| `static` | `getDataLoader` | `(arg0: ChartDef, arg1: int)` | `IDataLoader` | Retrieves `DataLoader` property from `DataManager` |
| `static` | `getDataLoader` | `(arg0: ChartDef, arg1: int, arg2: IStopPauseStatus)` | `IDataLoader` | Retrieves `DataLoader` property from `DataManager` |
| `static` | `isGroupAlias` | `(arg0: String)` | `boolean` | Evaluates boolean predicate `isGroupAlias` on `DataManager` |
| `static` | `clearData` | `(arg0: String, arg1: String)` | `void` | Removes/resets elements via `clearData` |
| `static` | `checkConnectionExists` | `(arg0: String)` | `boolean` | Performs check connection exists operation |
| `static` | `checkDataExists` | `(arg0: String, arg1: String)` | `boolean` | Performs check data exists operation |
| `static` | `getHistoryData` | `(arg0: String, arg1: String, arg2: long, arg3: long, arg4: String)` | `HistoryOHLCData` | Retrieves `HistoryData` property from `DataManager` |
| `static` | `getDataFileName` | `(arg0: String, arg1: String, arg2: String, arg3: String)` | `String` | Retrieves `DataFileName` property from `DataManager` |
| `static` | `getDataFileName` | `(arg0: String, arg1: String, arg2: String, arg3: String, arg4: DataInfo)` | `String` | Retrieves `DataFileName` property from `DataManager` |
| `static` | `deleteData` | `(arg0: String, arg1: String)` | `void` | Performs delete data operation |
| `static` | `addData` | `(arg0: String, arg1: String, arg2: String, arg3: int, arg4: int)` | `void` | Appends/registers element via `addData` |
| `static` | `addData` | `(arg0: String, arg1: String, arg2: String, arg3: int, arg4: int, arg5: String, arg6: String, arg7: int, arg8: int)` | `void` | Appends/registers element via `addData` |
| `static` | `addData` | `(arg0: String, arg1: String, arg2: String, arg3: int, arg4: int, arg5: int, arg6: int)` | `void` | Appends/registers element via `addData` |
| `static` | `addData` | `(arg0: String, arg1: String, arg2: String, arg3: int, arg4: int, arg5: String, arg6: String)` | `void` | Appends/registers element via `addData` |
| `static` | `listCloned` | `(arg0: int)` | `ArrayList` | Performs list cloned operation |
| `static` | `checkData` | `()` | `void` | Performs check data operation |
| `static` | `generateName` | `(arg0: String)` | `String` | Performs generate name operation |
| `static` | `getSymbolFolderName` | `(arg0: String, arg1: String, arg2: String, arg3: DataInfo)` | `String` | Retrieves `SymbolFolderName` property from `DataManager` |
| `static` | `getSymbolFolderName` | `(arg0: String, arg1: String, arg2: String)` | `String` | Retrieves `SymbolFolderName` property from `DataManager` |
| `static` | `fixFilename` | `(arg0: String)` | `String` | Performs fix filename operation |
| `static` | `flushUpdatedData` | `()` | `void` | Performs flush updated data operation |
| `static` | `addCustomData` | `(arg0: String, arg1: String, arg2: int, arg3: String)` | `DataInfo` | Appends/registers element via `addCustomData` |
| `static` | `updateUnderlyingSymbolName` | `(arg0: String, arg1: String, arg2: String)` | `void` | Performs update underlying symbol name operation |
| `static` | `updateDataInBatch` | `(arg0: String, arg1: String, arg2: long, arg3: long, arg4: int, arg5: long, arg6: int, arg7: String, arg8: String)` | `void` | Performs update data in batch operation |
| `static` | `updateDataInBatch` | `(arg0: String, arg1: String, arg2: long, arg3: long, arg4: int, arg5: long, arg6: int, arg7: String, arg8: String, arg9: int, arg10: boolean)` | `void` | Performs update data in batch operation |
| `static` | `getUnadjustedDataFileName` | `(arg0: String, arg1: String, arg2: String, arg3: String)` | `String` | Retrieves `UnadjustedDataFileName` property from `DataManager` |
| `static` | `getUnadjustedDataFileName` | `(arg0: String, arg1: String, arg2: String, arg3: String, arg4: DataInfo)` | `String` | Retrieves `UnadjustedDataFileName` property from `DataManager` |
| `static` | `addDataInBatch` | `(arg0: String, arg1: List, arg2: BatchProgressController)` | `void` | Appends/registers element via `addDataInBatch` |
| `static` | `listSafe` | `()` | `ArrayList` | Performs list safe operation |
| `static` | `renameUnderlayingData` | `(arg0: String, arg1: String, arg2: String)` | `String` | Performs rename underlaying data operation |
| `static` | `checkDataExport` | `(arg0: ICryptable, arg1: int)` | `void` | Performs check data export operation |
| `static` | `updateInstrument` | `(arg0: String, arg1: String, arg2: String)` | `void` | Performs update instrument operation |
| `static` | `getPrecisionToLoad` | `(arg0: String, arg1: String, arg2: String, arg3: int)` | `int` | Retrieves `PrecisionToLoad` property from `DataManager` |
| `static` | `createGroupAlias` | `(arg0: String, arg1: int)` | `boolean` | Instantiates/initializes `createGroupAlias` resource |
| `static` | `getTempFileName` | `(arg0: String)` | `String` | Retrieves `TempFileName` property from `DataManager` |
| `static` | `removeDataFiles` | `(arg0: String, arg1: String)` | `void` | Removes/resets elements via `removeDataFiles` |
| `static` | `removeDataFilesWithFolder` | `(arg0: String, arg1: String)` | `void` | Removes/resets elements via `removeDataFilesWithFolder` |
| `static` | `isLimited` | `(arg0: String)` | `boolean` | Evaluates boolean predicate `isLimited` on `DataManager` |
| `static` | `exportTick` | `(arg0: String, arg1: long, arg2: long, arg3: String)` | `void` | Performs export tick operation |
| `static` | `exportM1` | `(arg0: String, arg1: long, arg2: long, arg3: String)` | `void` | Performs export m 1 operation |
| `static` | `deleteGroupAlias` | `(arg0: int, arg1: String)` | `void` | Performs delete group alias operation |
| `static` | `renameDataFiles` | `(arg0: String, arg1: String, arg2: String)` | `void` | Performs rename data files operation |
| `static` | `updateSecondsRecords` | `(arg0: DataInfo)` | `void` | Performs update seconds records operation |
| `static` | `updateSecondsRecords` | `(arg0: String, arg1: String, arg2: long)` | `void` | Performs update seconds records operation |
| `static` | `deleteForGroup` | `(arg0: String, arg1: String, arg2: int)` | `void` | Performs delete for group operation |
| `static` | `listForSource` | `(arg0: int)` | `ArrayList` | Performs list for source operation |
| `static` | `getSymbolsForInstrument` | `(arg0: String)` | `ArrayList` | Retrieves `SymbolsForInstrument` property from `DataManager` |
| `static` | `clearDataInBatch` | `(arg0: String, arg1: String)` | `void` | Removes/resets elements via `clearDataInBatch` |
| `static` | `deleteDataInBatch` | `(arg0: String[], arg1: String[], arg2: BatchProgressController)` | `void` | Performs delete data in batch operation |
| `static` | `updateInstrumentSwap` | `(arg0: String, arg1: String, arg2: String, arg3: String)` | `void` | Performs update instrument swap operation |
| `static` | `updateTimeframe` | `(arg0: String, arg1: String, arg2: String)` | `void` | Performs update timeframe operation |
| `static` | `updateBroker` | `(arg0: String, arg1: String, arg2: int)` | `void` | Performs update broker operation |
| `static` | `renameData` | `(arg0: String, arg1: String, arg2: String)` | `void` | Performs rename data operation |
| `static` | `showData` | `(arg0: String, arg1: String, arg2: boolean)` | `void` | Performs show data operation |
| `static` | `getTimeframeToLoad` | `(arg0: String, arg1: String, arg2: String, arg3: int)` | `String` | Retrieves `TimeframeToLoad` property from `DataManager` |
| `static` | `cleanHigherTFFiles` | `(arg0: String)` | `void` | Performs clean higher tf files operation |

---

### `DateShifter`
- **Full Qualified Name:** `com.strategyquant.datalib.data.DateShifter`
- **Primary Job / Responsibility:** Market data abstraction and time-series container (`DateShifter`).

#### Methods & Functions
| Modifiers | Method Name | Parameter Signatures | Return Type | Functional Description / Job |
| :--- | :--- | :--- | :--- | :--- |
| `instance` | `transformToTimeZone` | `(arg0: VersatileData)` | `void` | Performs transform to time zone operation |
| `instance` | `equals` | `(arg0: Object)` | `boolean` | Performs equals operation |
| `instance` | `toString` | `()` | `String` | Converts/serializes representation via `toString` |
| `instance` | `hashCode` | `()` | `int` | Evaluates boolean predicate `hashCode` on `DateShifter` |
| `instance` | `getClass` | `()` | `Class` | Retrieves `Class` property from `DateShifter` |
| `instance` | `notify` | `()` | `void` | Performs notify operation |
| `instance` | `notifyAll` | `()` | `void` | Performs notify all operation |
| `instance` | `wait` | `(arg0: long)` | `void` | Performs wait operation |
| `instance` | `wait` | `(arg0: long, arg1: int)` | `void` | Performs wait operation |
| `instance` | `wait` | `()` | `void` | Performs wait operation |

---

### `DownloadSemaphore`
- **Full Qualified Name:** `com.strategyquant.datalib.data.DownloadSemaphore`
- **Primary Job / Responsibility:** Market data abstraction and time-series container (`DownloadSemaphore`).

#### Methods & Functions
| Modifiers | Method Name | Parameter Signatures | Return Type | Functional Description / Job |
| :--- | :--- | :--- | :--- | :--- |
| `instance` | `downloadFinished` | `()` | `void` | Performs download finished operation |
| `instance` | `startDownloadData` | `(arg0: int)` | `boolean` | Performs start download data operation |
| `instance` | `equals` | `(arg0: Object)` | `boolean` | Performs equals operation |
| `instance` | `toString` | `()` | `String` | Converts/serializes representation via `toString` |
| `instance` | `hashCode` | `()` | `int` | Evaluates boolean predicate `hashCode` on `DownloadSemaphore` |
| `instance` | `getClass` | `()` | `Class` | Retrieves `Class` property from `DownloadSemaphore` |
| `instance` | `notify` | `()` | `void` | Performs notify operation |
| `instance` | `notifyAll` | `()` | `void` | Performs notify all operation |
| `instance` | `wait` | `(arg0: long)` | `void` | Performs wait operation |
| `instance` | `wait` | `(arg0: long, arg1: int)` | `void` | Performs wait operation |
| `instance` | `wait` | `()` | `void` | Performs wait operation |
| `static` | `getInstance` | `()` | `DownloadSemaphore` | Retrieves `Instance` property from `DownloadSemaphore` |

---

### `DukasDataManager`
- **Full Qualified Name:** `com.strategyquant.datalib.data.DukasDataManager`
- **Primary Job / Responsibility:** Market data abstraction and time-series container (`DukasDataManager`).

#### Fields
| Scope | Field Name | Type |
| :--- | :--- | :--- |
| `static` | `Log` | `Logger` |

#### Methods & Functions
| Modifiers | Method Name | Parameter Signatures | Return Type | Functional Description / Job |
| :--- | :--- | :--- | :--- | :--- |
| `instance` | `addData` | `(arg0: TickerDto, arg1: String, arg2: String, arg3: TickerKind, arg4: String, arg5: byte, arg6: double, arg7: double, arg8: double, arg9: int)` | `String` | Appends/registers element via `addData` |
| `instance` | `addData` | `(arg0: String, arg1: String, arg2: int, arg3: String)` | `String` | Appends/registers element via `addData` |
| `instance` | `getAvailableDataInfo` | `(arg0: String)` | `SymbolData` | Retrieves `AvailableDataInfo` property from `DukasDataManager` |
| `instance` | `getAvailableDataList` | `()` | `ArrayList` | Retrieves `AvailableDataList` property from `DukasDataManager` |
| `instance` | `addBatch` | `(arg0: List, arg1: Map, arg2: InstrumentValueEvaluator, arg3: BatchProgressController)` | `void` | Appends/registers element via `addBatch` |
| `instance` | `equals` | `(arg0: Object)` | `boolean` | Performs equals operation |
| `instance` | `toString` | `()` | `String` | Converts/serializes representation via `toString` |
| `instance` | `hashCode` | `()` | `int` | Evaluates boolean predicate `hashCode` on `DukasDataManager` |
| `instance` | `getClass` | `()` | `Class` | Retrieves `Class` property from `DukasDataManager` |
| `instance` | `notify` | `()` | `void` | Performs notify operation |
| `instance` | `notifyAll` | `()` | `void` | Performs notify all operation |
| `instance` | `wait` | `(arg0: long)` | `void` | Performs wait operation |
| `instance` | `wait` | `(arg0: long, arg1: int)` | `void` | Performs wait operation |
| `instance` | `wait` | `()` | `void` | Performs wait operation |
| `static` | `get` | `()` | `DukasDataManager` | Retrieves `` property from `DukasDataManager` |

---

### `ExchangeTimezone`
- **Full Qualified Name:** `com.strategyquant.datalib.data.ExchangeTimezone`
- **Primary Job / Responsibility:** Market data abstraction and time-series container (`ExchangeTimezone`).

#### Methods & Functions
| Modifiers | Method Name | Parameter Signatures | Return Type | Functional Description / Job |
| :--- | :--- | :--- | :--- | :--- |
| `instance` | `getTimezone` | `(arg0: String)` | `String` | Retrieves `Timezone` property from `ExchangeTimezone` |
| `instance` | `equals` | `(arg0: Object)` | `boolean` | Performs equals operation |
| `instance` | `toString` | `()` | `String` | Converts/serializes representation via `toString` |
| `instance` | `hashCode` | `()` | `int` | Evaluates boolean predicate `hashCode` on `ExchangeTimezone` |
| `instance` | `getClass` | `()` | `Class` | Retrieves `Class` property from `ExchangeTimezone` |
| `instance` | `notify` | `()` | `void` | Performs notify operation |
| `instance` | `notifyAll` | `()` | `void` | Performs notify all operation |
| `instance` | `wait` | `(arg0: long)` | `void` | Performs wait operation |
| `instance` | `wait` | `(arg0: long, arg1: int)` | `void` | Performs wait operation |
| `instance` | `wait` | `()` | `void` | Performs wait operation |
| `static` | `get` | `()` | `ExchangeTimezone` | Retrieves `` property from `ExchangeTimezone` |

---

### `IDataBuffer`
- **Full Qualified Name:** `com.strategyquant.datalib.data.IDataBuffer`
- **Primary Job / Responsibility:** Market data abstraction and time-series container (`IDataBuffer`).

#### Methods & Functions
| Modifiers | Method Name | Parameter Signatures | Return Type | Functional Description / Job |
| :--- | :--- | :--- | :--- | :--- |
| `instance` | `get` | `(arg0: long, arg1: TickEvent[])` | `long` | Retrieves `` property from `IDataBuffer` |
| `instance` | `put` | `(arg0: TickEvent)` | `void` | Performs put operation |
| `instance` | `getOne` | `(arg0: long, arg1: TickEvent)` | `long` | Retrieves `One` property from `IDataBuffer` |
| `instance` | `printRing` | `()` | `void` | Performs print ring operation |

---

### `InstrumentValueEvaluator`
- **Full Qualified Name:** `com.strategyquant.datalib.data.InstrumentValueEvaluator`
- **Primary Job / Responsibility:** Symbol specifications, pip values, margins, and contract specifications (`InstrumentValueEvaluator`).

#### Methods & Functions
| Modifiers | Method Name | Parameter Signatures | Return Type | Functional Description / Job |
| :--- | :--- | :--- | :--- | :--- |
| `instance` | `getPointValue` | `(arg0: TickerDto)` | `double` | Retrieves `PointValue` property from `InstrumentValueEvaluator` |
| `instance` | `getTickSize` | `(arg0: TickerDto)` | `double` | Retrieves `TickSize` property from `InstrumentValueEvaluator` |
| `instance` | `getTickStep` | `(arg0: TickerDto)` | `double` | Retrieves `TickStep` property from `InstrumentValueEvaluator` |
| `instance` | `getInstrumentType` | `(arg0: TickerDto)` | `byte` | Retrieves `InstrumentType` property from `InstrumentValueEvaluator` |
| `instance` | `getOrderSizeMultiplier` | `(arg0: TickerDto)` | `double` | Retrieves `OrderSizeMultiplier` property from `InstrumentValueEvaluator` |
| `instance` | `getOrderSizeStep` | `(arg0: TickerDto)` | `double` | Retrieves `OrderSizeStep` property from `InstrumentValueEvaluator` |
| `instance` | `getDescriptions` | `(arg0: TickerDto)` | `String` | Retrieves `Descriptions` property from `InstrumentValueEvaluator` |

---

### `StockGroupUpdateErrorManager`
- **Full Qualified Name:** `com.strategyquant.datalib.data.StockGroupUpdateErrorManager`
- **Primary Job / Responsibility:** Market data abstraction and time-series container (`StockGroupUpdateErrorManager`).

#### Methods & Functions
| Modifiers | Method Name | Parameter Signatures | Return Type | Functional Description / Job |
| :--- | :--- | :--- | :--- | :--- |
| `instance` | `start` | `()` | `void` | Controls lifecycle execution: `start` |
| `instance` | `finished` | `()` | `Map` | Performs finished operation |
| `instance` | `logError` | `(arg0: String, arg1: String)` | `void` | Performs log error operation |
| `instance` | `equals` | `(arg0: Object)` | `boolean` | Performs equals operation |
| `instance` | `toString` | `()` | `String` | Converts/serializes representation via `toString` |
| `instance` | `hashCode` | `()` | `int` | Evaluates boolean predicate `hashCode` on `StockGroupUpdateErrorManager` |
| `instance` | `getClass` | `()` | `Class` | Retrieves `Class` property from `StockGroupUpdateErrorManager` |
| `instance` | `notify` | `()` | `void` | Performs notify operation |
| `instance` | `notifyAll` | `()` | `void` | Performs notify all operation |
| `instance` | `wait` | `(arg0: long)` | `void` | Performs wait operation |
| `instance` | `wait` | `(arg0: long, arg1: int)` | `void` | Performs wait operation |
| `instance` | `wait` | `()` | `void` | Performs wait operation |
| `static` | `getInstance` | `()` | `StockGroupUpdateErrorManager` | Retrieves `Instance` property from `StockGroupUpdateErrorManager` |

---

### `SymbolInfo`
- **Full Qualified Name:** `com.strategyquant.datalib.data.SymbolInfo`
- **Primary Job / Responsibility:** Market data abstraction and time-series container (`SymbolInfo`).

#### Fields
| Scope | Field Name | Type |
| :--- | :--- | :--- |
| `instance` | `barType` | `int` |
| `instance` | `connection` | `String` |
| `instance` | `dateFrom` | `long` |
| `instance` | `dateTo` | `long` |
| `instance` | `removeWeekends` | `boolean` |
| `instance` | `rows` | `int` |
| `instance` | `secondsRecords` | `long` |
| `instance` | `sourceDataId` | `int` |
| `instance` | `symbol` | `String` |
| `instance` | `timeframe` | `String` |
| `instance` | `timezone` | `String` |

#### Methods & Functions
| Modifiers | Method Name | Parameter Signatures | Return Type | Functional Description / Job |
| :--- | :--- | :--- | :--- | :--- |
| `instance` | `equals` | `(arg0: Object)` | `boolean` | Performs equals operation |
| `instance` | `toString` | `()` | `String` | Converts/serializes representation via `toString` |
| `instance` | `hashCode` | `()` | `int` | Evaluates boolean predicate `hashCode` on `SymbolInfo` |
| `instance` | `getClass` | `()` | `Class` | Retrieves `Class` property from `SymbolInfo` |
| `instance` | `notify` | `()` | `void` | Performs notify operation |
| `instance` | `notifyAll` | `()` | `void` | Performs notify all operation |
| `instance` | `wait` | `(arg0: long)` | `void` | Performs wait operation |
| `instance` | `wait` | `(arg0: long, arg1: int)` | `void` | Performs wait operation |
| `instance` | `wait` | `()` | `void` | Performs wait operation |

---

### `ConcurrentDataBuffer`
- **Full Qualified Name:** `com.strategyquant.datalib.data.impl.ConcurrentDataBuffer`
- **Primary Job / Responsibility:** Market data abstraction and time-series container (`ConcurrentDataBuffer`).

#### Methods & Functions
| Modifiers | Method Name | Parameter Signatures | Return Type | Functional Description / Job |
| :--- | :--- | :--- | :--- | :--- |
| `instance` | `get` | `(arg0: long, arg1: TickEvent[])` | `long` | Retrieves `` property from `ConcurrentDataBuffer` |
| `instance` | `put` | `(arg0: TickEvent)` | `void` | Performs put operation |
| `instance` | `getOne` | `(arg0: long, arg1: TickEvent)` | `long` | Retrieves `One` property from `ConcurrentDataBuffer` |
| `instance` | `printRing` | `()` | `void` | Performs print ring operation |
| `instance` | `equals` | `(arg0: Object)` | `boolean` | Performs equals operation |
| `instance` | `toString` | `()` | `String` | Converts/serializes representation via `toString` |
| `instance` | `hashCode` | `()` | `int` | Evaluates boolean predicate `hashCode` on `ConcurrentDataBuffer` |
| `instance` | `getClass` | `()` | `Class` | Retrieves `Class` property from `ConcurrentDataBuffer` |
| `instance` | `notify` | `()` | `void` | Performs notify operation |
| `instance` | `notifyAll` | `()` | `void` | Performs notify all operation |
| `instance` | `wait` | `(arg0: long)` | `void` | Performs wait operation |
| `instance` | `wait` | `(arg0: long, arg1: int)` | `void` | Performs wait operation |
| `instance` | `wait` | `()` | `void` | Performs wait operation |

---

### `SimpleDataBuffer`
- **Full Qualified Name:** `com.strategyquant.datalib.data.impl.SimpleDataBuffer`
- **Primary Job / Responsibility:** Market data abstraction and time-series container (`SimpleDataBuffer`).

#### Methods & Functions
| Modifiers | Method Name | Parameter Signatures | Return Type | Functional Description / Job |
| :--- | :--- | :--- | :--- | :--- |
| `instance` | `get` | `(arg0: long, arg1: TickEvent[])` | `long` | Retrieves `` property from `SimpleDataBuffer` |
| `instance` | `put` | `(arg0: TickEvent)` | `void` | Performs put operation |
| `instance` | `getOne` | `(arg0: long, arg1: TickEvent)` | `long` | Retrieves `One` property from `SimpleDataBuffer` |
| `instance` | `printRing` | `()` | `void` | Performs print ring operation |
| `instance` | `equals` | `(arg0: Object)` | `boolean` | Performs equals operation |
| `instance` | `toString` | `()` | `String` | Converts/serializes representation via `toString` |
| `instance` | `hashCode` | `()` | `int` | Evaluates boolean predicate `hashCode` on `SimpleDataBuffer` |
| `instance` | `getClass` | `()` | `Class` | Retrieves `Class` property from `SimpleDataBuffer` |
| `instance` | `notify` | `()` | `void` | Performs notify operation |
| `instance` | `notifyAll` | `()` | `void` | Performs notify all operation |
| `instance` | `wait` | `(arg0: long)` | `void` | Performs wait operation |
| `instance` | `wait` | `(arg0: long, arg1: int)` | `void` | Performs wait operation |
| `instance` | `wait` | `()` | `void` | Performs wait operation |

---

### `AvailableDataFormats`
- **Full Qualified Name:** `com.strategyquant.datalib.data.imports.AvailableDataFormats`
- **Primary Job / Responsibility:** Market data abstraction and time-series container (`AvailableDataFormats`).

#### Fields
| Scope | Field Name | Type |
| :--- | :--- | :--- |
| `static` | `Log` | `Logger` |
| `static` | `MT5TickData` | `String` |

#### Methods & Functions
| Modifiers | Method Name | Parameter Signatures | Return Type | Functional Description / Job |
| :--- | :--- | :--- | :--- | :--- |
| `instance` | `getAvailableFileFormats` | `()` | `ArrayList` | Retrieves `AvailableFileFormats` property from `AvailableDataFormats` |
| `instance` | `registerFileFormats` | `()` | `void` | Performs register file formats operation |
| `instance` | `formatExists` | `(arg0: String)` | `boolean` | Converts/serializes representation via `formatExists` |
| `instance` | `addDataFormat` | `(arg0: CustomDataFormat)` | `void` | Appends/registers element via `addDataFormat` |
| `instance` | `deleteDataFormat` | `(arg0: String)` | `void` | Performs delete data format operation |
| `instance` | `updateDataFormat` | `(arg0: CustomDataFormat)` | `void` | Performs update data format operation |
| `instance` | `findFileFormatByName` | `(arg0: String)` | `CustomDataFormat` | Performs find file format by name operation |
| `instance` | `equals` | `(arg0: Object)` | `boolean` | Performs equals operation |
| `instance` | `toString` | `()` | `String` | Converts/serializes representation via `toString` |
| `instance` | `hashCode` | `()` | `int` | Evaluates boolean predicate `hashCode` on `AvailableDataFormats` |
| `instance` | `getClass` | `()` | `Class` | Retrieves `Class` property from `AvailableDataFormats` |
| `instance` | `notify` | `()` | `void` | Performs notify operation |
| `instance` | `notifyAll` | `()` | `void` | Performs notify all operation |
| `instance` | `wait` | `(arg0: long)` | `void` | Performs wait operation |
| `instance` | `wait` | `(arg0: long, arg1: int)` | `void` | Performs wait operation |
| `instance` | `wait` | `()` | `void` | Performs wait operation |
| `static` | `getInstance` | `()` | `AvailableDataFormats` | Retrieves `Instance` property from `AvailableDataFormats` |

---

### `CsvFileReader`
- **Full Qualified Name:** `com.strategyquant.datalib.data.imports.CsvFileReader`
- **Primary Job / Responsibility:** Market data abstraction and time-series container (`CsvFileReader`).

#### Methods & Functions
| Modifiers | Method Name | Parameter Signatures | Return Type | Functional Description / Job |
| :--- | :--- | :--- | :--- | :--- |
| `instance` | `read` | `(arg0: Boolean)` | `String[][]` | Performs read operation |
| `instance` | `getSeparator` | `()` | `String` | Retrieves `Separator` property from `CsvFileReader` |
| `instance` | `getDateFormat` | `()` | `String` | Retrieves `DateFormat` property from `CsvFileReader` |
| `instance` | `getDigitsCount` | `(arg0: String)` | `int` | Retrieves `DigitsCount` property from `CsvFileReader` |
| `instance` | `getAlphabeticsCount` | `(arg0: String)` | `int` | Retrieves `AlphabeticsCount` property from `CsvFileReader` |
| `instance` | `equals` | `(arg0: Object)` | `boolean` | Performs equals operation |
| `instance` | `toString` | `()` | `String` | Converts/serializes representation via `toString` |
| `instance` | `hashCode` | `()` | `int` | Evaluates boolean predicate `hashCode` on `CsvFileReader` |
| `instance` | `getClass` | `()` | `Class` | Retrieves `Class` property from `CsvFileReader` |
| `instance` | `notify` | `()` | `void` | Performs notify operation |
| `instance` | `notifyAll` | `()` | `void` | Performs notify all operation |
| `instance` | `wait` | `(arg0: long)` | `void` | Performs wait operation |
| `instance` | `wait` | `(arg0: long, arg1: int)` | `void` | Performs wait operation |
| `instance` | `wait` | `()` | `void` | Performs wait operation |
| `static` | `findSeparator` | `(arg0: String[], arg1: int)` | `String` | Performs find separator operation |

---

### `CustomDataFormat`
- **Full Qualified Name:** `com.strategyquant.datalib.data.imports.CustomDataFormat`
- **Primary Job / Responsibility:** Market data abstraction and time-series container (`CustomDataFormat`).

#### Methods & Functions
| Modifiers | Method Name | Parameter Signatures | Return Type | Functional Description / Job |
| :--- | :--- | :--- | :--- | :--- |
| `instance` | `getName` | `()` | `String` | Retrieves `Name` property from `CustomDataFormat` |
| `instance` | `toString` | `()` | `String` | Converts/serializes representation via `toString` |
| `instance` | `setName` | `(arg0: String)` | `void` | Sets `Name` configuration/state on `CustomDataFormat` |
| `instance` | `getSeparator` | `()` | `String` | Retrieves `Separator` property from `CustomDataFormat` |
| `instance` | `getOrder` | `()` | `int` | Retrieves `Order` property from `CustomDataFormat` |
| `instance` | `isPredefined` | `()` | `boolean` | Evaluates boolean predicate `isPredefined` on `CustomDataFormat` |
| `instance` | `setOrder` | `(arg0: int)` | `void` | Sets `Order` configuration/state on `CustomDataFormat` |
| `instance` | `getColumns` | `()` | `HashMap` | Retrieves `Columns` property from `CustomDataFormat` |
| `instance` | `getDateFormat` | `()` | `String` | Retrieves `DateFormat` property from `CustomDataFormat` |
| `instance` | `getSkipRows` | `()` | `int` | Retrieves `SkipRows` property from `CustomDataFormat` |
| `instance` | `getSkipColumns` | `()` | `int` | Retrieves `SkipColumns` property from `CustomDataFormat` |
| `instance` | `columTypesToString` | `()` | `String` | Performs colum types to string operation |
| `instance` | `setSeparator` | `(arg0: String)` | `void` | Sets `Separator` configuration/state on `CustomDataFormat` |
| `instance` | `setSkipColumns` | `(arg0: int)` | `void` | Sets `SkipColumns` configuration/state on `CustomDataFormat` |
| `instance` | `setSkipRows` | `(arg0: int)` | `void` | Sets `SkipRows` configuration/state on `CustomDataFormat` |
| `instance` | `setDateFormat` | `(arg0: String)` | `void` | Sets `DateFormat` configuration/state on `CustomDataFormat` |
| `instance` | `setPredefined` | `(arg0: boolean)` | `void` | Sets `Predefined` configuration/state on `CustomDataFormat` |
| `instance` | `setColumns` | `(arg0: HashMap)` | `void` | Sets `Columns` configuration/state on `CustomDataFormat` |
| `instance` | `setTimeFormat` | `(arg0: String)` | `void` | Sets `TimeFormat` configuration/state on `CustomDataFormat` |
| `instance` | `getTimeFormat` | `()` | `String` | Retrieves `TimeFormat` property from `CustomDataFormat` |
| `instance` | `equals` | `(arg0: Object)` | `boolean` | Performs equals operation |
| `instance` | `hashCode` | `()` | `int` | Evaluates boolean predicate `hashCode` on `CustomDataFormat` |
| `instance` | `getClass` | `()` | `Class` | Retrieves `Class` property from `CustomDataFormat` |
| `instance` | `notify` | `()` | `void` | Performs notify operation |
| `instance` | `notifyAll` | `()` | `void` | Performs notify all operation |
| `instance` | `wait` | `(arg0: long)` | `void` | Performs wait operation |
| `instance` | `wait` | `(arg0: long, arg1: int)` | `void` | Performs wait operation |
| `instance` | `wait` | `()` | `void` | Performs wait operation |

---

### `DataColumns`
- **Full Qualified Name:** `com.strategyquant.datalib.data.imports.DataColumns`
- **Primary Job / Responsibility:** Market data abstraction and time-series container (`DataColumns`).

#### Methods & Functions
| Modifiers | Method Name | Parameter Signatures | Return Type | Functional Description / Job |
| :--- | :--- | :--- | :--- | :--- |
| `instance` | `findColTypeByName` | `(arg0: String)` | `DefaultCol` | Performs find col type by name operation |
| `instance` | `getAvailableColTypes` | `()` | `ArrayList` | Retrieves `AvailableColTypes` property from `DataColumns` |
| `instance` | `equals` | `(arg0: Object)` | `boolean` | Performs equals operation |
| `instance` | `toString` | `()` | `String` | Converts/serializes representation via `toString` |
| `instance` | `hashCode` | `()` | `int` | Evaluates boolean predicate `hashCode` on `DataColumns` |
| `instance` | `getClass` | `()` | `Class` | Retrieves `Class` property from `DataColumns` |
| `instance` | `notify` | `()` | `void` | Performs notify operation |
| `instance` | `notifyAll` | `()` | `void` | Performs notify all operation |
| `instance` | `wait` | `(arg0: long)` | `void` | Performs wait operation |
| `instance` | `wait` | `(arg0: long, arg1: int)` | `void` | Performs wait operation |
| `instance` | `wait` | `()` | `void` | Performs wait operation |
| `static` | `getInstance` | `()` | `DataColumns` | Retrieves `Instance` property from `DataColumns` |

---

### `DataImportEngine`
- **Full Qualified Name:** `com.strategyquant.datalib.data.imports.DataImportEngine`
- **Primary Job / Responsibility:** Market data abstraction and time-series container (`DataImportEngine`).

#### Fields
| Scope | Field Name | Type |
| :--- | :--- | :--- |
| `static` | `Log` | `Logger` |

#### Methods & Functions
| Modifiers | Method Name | Parameter Signatures | Return Type | Functional Description / Job |
| :--- | :--- | :--- | :--- | :--- |
| `instance` | `equals` | `(arg0: Object)` | `boolean` | Performs equals operation |
| `instance` | `toString` | `()` | `String` | Converts/serializes representation via `toString` |
| `instance` | `hashCode` | `()` | `int` | Evaluates boolean predicate `hashCode` on `DataImportEngine` |
| `instance` | `getClass` | `()` | `Class` | Retrieves `Class` property from `DataImportEngine` |
| `instance` | `notify` | `()` | `void` | Performs notify operation |
| `instance` | `notifyAll` | `()` | `void` | Performs notify all operation |
| `instance` | `wait` | `(arg0: long)` | `void` | Performs wait operation |
| `instance` | `wait` | `(arg0: long, arg1: int)` | `void` | Performs wait operation |
| `instance` | `wait` | `()` | `void` | Performs wait operation |
| `static` | `waitUntilFinished` | `()` | `void` | Performs wait until finished operation |
| `static` | `importData` | `(arg0: String, arg1: String, arg2: String, arg3: ImportDataInfo, arg4: IProgressListener)` | `void` | Performs import data operation |
| `static` | `cancelImport` | `()` | `void` | Evaluates boolean predicate `cancelImport` on `DataImportEngine` |
| `static` | `getFileFormat` | `(arg0: String, arg1: ArrayList, arg2: CustomDataFormat)` | `CustomDataFormat` | Retrieves `FileFormat` property from `DataImportEngine` |
| `static` | `continueImport` | `()` | `void` | Performs continue import operation |
| `static` | `getRowsCount` | `()` | `int` | Retrieves `RowsCount` property from `DataImportEngine` |

---

### `Separators`
- **Full Qualified Name:** `com.strategyquant.datalib.data.imports.Separators`
- **Primary Job / Responsibility:** Market data abstraction and time-series container (`Separators`).

#### Fields
| Scope | Field Name | Type |
| :--- | :--- | :--- |
| `static` | `TYPE_COMMA` | `String` |
| `static` | `TYPE_SEMICOLON` | `String` |
| `static` | `TYPE_SPACE` | `String` |
| `static` | `TYPE_TAB` | `String` |
| `static` | `VALUE_COMMA` | `String` |
| `static` | `VALUE_SEMICOLON` | `String` |
| `static` | `VALUE_SPACE` | `String` |
| `static` | `VALUE_TAB` | `String` |

#### Methods & Functions
| Modifiers | Method Name | Parameter Signatures | Return Type | Functional Description / Job |
| :--- | :--- | :--- | :--- | :--- |
| `instance` | `equals` | `(arg0: Object)` | `boolean` | Performs equals operation |
| `instance` | `toString` | `()` | `String` | Converts/serializes representation via `toString` |
| `instance` | `hashCode` | `()` | `int` | Evaluates boolean predicate `hashCode` on `Separators` |
| `instance` | `getClass` | `()` | `Class` | Retrieves `Class` property from `Separators` |
| `instance` | `notify` | `()` | `void` | Performs notify operation |
| `instance` | `notifyAll` | `()` | `void` | Performs notify all operation |
| `instance` | `wait` | `(arg0: long)` | `void` | Performs wait operation |
| `instance` | `wait` | `(arg0: long, arg1: int)` | `void` | Performs wait operation |
| `instance` | `wait` | `()` | `void` | Performs wait operation |
| `static` | `getValue` | `(arg0: String)` | `String` | Retrieves `Value` property from `Separators` |
| `static` | `getType` | `(arg0: String)` | `String` | Retrieves `Type` property from `Separators` |
| `static` | `toJSON` | `()` | `JSONArray` | Converts/serializes representation via `toJSON` |
| `static` | `listValues` | `()` | `String[]` | Performs list values operation |
| `static` | `listTypes` | `()` | `String[]` | Performs list types operation |

---

### `AbstractDataCsvLoader`
- **Full Qualified Name:** `com.strategyquant.datalib.data.io.AbstractDataCsvLoader`
- **Primary Job / Responsibility:** Market data abstraction and time-series container (`AbstractDataCsvLoader`).

#### Fields
| Scope | Field Name | Type |
| :--- | :--- | :--- |
| `static` | `InvalidTimeConsecution` | `String` |
| `static` | `Log` | `Logger` |
| `instance` | `loadedRows` | `int` |

#### Methods & Functions
| Modifiers | Method Name | Parameter Signatures | Return Type | Functional Description / Job |
| :--- | :--- | :--- | :--- | :--- |
| `instance` | `cancel` | `()` | `void` | Evaluates boolean predicate `cancel` on `AbstractDataCsvLoader` |
| `instance` | `close` | `()` | `void` | Performs close operation |
| `instance` | `parseLine` | `(arg0: String[], arg1: ImportDataInfo)` | `Object[]` | Converts/serializes representation via `parseLine` |
| `instance` | `pause` | `()` | `void` | Performs pause operation |
| `instance` | `openFile` | `()` | `void` | Performs open file operation |
| `instance` | `readData` | `()` | `boolean` | Performs read data operation |
| `instance` | `restart` | `()` | `void` | Performs restart operation |
| `instance` | `recognizeTimeframe` | `()` | `String` | Performs recognize timeframe operation |
| `instance` | `countRows` | `(arg0: String)` | `int` | Performs count rows operation |
| `instance` | `equals` | `(arg0: Object)` | `boolean` | Performs equals operation |
| `instance` | `toString` | `()` | `String` | Converts/serializes representation via `toString` |
| `instance` | `hashCode` | `()` | `int` | Evaluates boolean predicate `hashCode` on `AbstractDataCsvLoader` |
| `instance` | `getClass` | `()` | `Class` | Retrieves `Class` property from `AbstractDataCsvLoader` |
| `instance` | `notify` | `()` | `void` | Performs notify operation |
| `instance` | `notifyAll` | `()` | `void` | Performs notify all operation |
| `instance` | `wait` | `(arg0: long)` | `void` | Performs wait operation |
| `instance` | `wait` | `(arg0: long, arg1: int)` | `void` | Performs wait operation |
| `instance` | `wait` | `()` | `void` | Performs wait operation |
| `static` | `intValueOf` | `(arg0: String)` | `int` | Performs int value of operation |

---

### `BinaryDataLoader`
- **Full Qualified Name:** `com.strategyquant.datalib.data.io.BinaryDataLoader`
- **Primary Job / Responsibility:** Market data abstraction and time-series container (`BinaryDataLoader`).

#### Fields
| Scope | Field Name | Type |
| :--- | :--- | :--- |
| `static` | `Log` | `Logger` |

#### Methods & Functions
| Modifiers | Method Name | Parameter Signatures | Return Type | Functional Description / Job |
| :--- | :--- | :--- | :--- | :--- |
| `instance` | `close` | `()` | `void` | Performs close operation |
| `instance` | `open` | `()` | `void` | Performs open operation |
| `instance` | `seek` | `(arg0: int)` | `void` | Performs seek operation |
| `instance` | `getDateFrom` | `()` | `long` | Retrieves `DateFrom` property from `BinaryDataLoader` |
| `instance` | `hasNextTick` | `()` | `boolean` | Evaluates boolean predicate `hasNextTick` on `BinaryDataLoader` |
| `instance` | `getNextTick` | `(arg0: VersatileData)` | `void` | Retrieves `NextTick` property from `BinaryDataLoader` |
| `instance` | `nextTickTime` | `()` | `long` | Performs next tick time operation |
| `instance` | `isOHLCData` | `()` | `boolean` | Evaluates boolean predicate `isOHLCData` on `BinaryDataLoader` |
| `instance` | `getDecimalPlaces` | `()` | `int` | Retrieves `DecimalPlaces` property from `BinaryDataLoader` |
| `instance` | `isCrypted` | `()` | `boolean` | Evaluates boolean predicate `isCrypted` on `BinaryDataLoader` |
| `instance` | `getTotalRecords` | `()` | `long` | Retrieves `TotalRecords` property from `BinaryDataLoader` |
| `instance` | `getDataFilePath` | `()` | `String` | Retrieves `DataFilePath` property from `BinaryDataLoader` |
| `instance` | `equals` | `(arg0: Object)` | `boolean` | Performs equals operation |
| `instance` | `toString` | `()` | `String` | Converts/serializes representation via `toString` |
| `instance` | `hashCode` | `()` | `int` | Evaluates boolean predicate `hashCode` on `BinaryDataLoader` |
| `instance` | `getClass` | `()` | `Class` | Retrieves `Class` property from `BinaryDataLoader` |
| `instance` | `notify` | `()` | `void` | Performs notify operation |
| `instance` | `notifyAll` | `()` | `void` | Performs notify all operation |
| `instance` | `wait` | `(arg0: long)` | `void` | Performs wait operation |
| `instance` | `wait` | `(arg0: long, arg1: int)` | `void` | Performs wait operation |
| `instance` | `wait` | `()` | `void` | Performs wait operation |

---

### `DataBinReader`
- **Full Qualified Name:** `com.strategyquant.datalib.data.io.DataBinReader`
- **Primary Job / Responsibility:** Market data abstraction and time-series container (`DataBinReader`).

#### Fields
| Scope | Field Name | Type |
| :--- | :--- | :--- |
| `instance` | `tickData` | `VersatileData` |

#### Methods & Functions
| Modifiers | Method Name | Parameter Signatures | Return Type | Functional Description / Job |
| :--- | :--- | :--- | :--- | :--- |
| `instance` | `readHeader` | `()` | `void` | Performs read header operation |
| `instance` | `setParams` | `(arg0: ImportDataInfo, arg1: DataInfo, arg2: JProgressBar)` | `void` | Sets `Params` configuration/state on `DataBinReader` |
| `instance` | `openFile` | `()` | `void` | Performs open file operation |
| `instance` | `readData` | `()` | `boolean` | Performs read data operation |
| `instance` | `closeFile` | `()` | `void` | Performs close file operation |
| `instance` | `setFileName` | `(arg0: String)` | `void` | Sets `FileName` configuration/state on `DataBinReader` |
| `instance` | `isDataCorrect` | `()` | `boolean` | Evaluates boolean predicate `isDataCorrect` on `DataBinReader` |
| `instance` | `getColumnsCount` | `()` | `int` | Retrieves `ColumnsCount` property from `DataBinReader` |
| `instance` | `equals` | `(arg0: Object)` | `boolean` | Performs equals operation |
| `instance` | `toString` | `()` | `String` | Converts/serializes representation via `toString` |
| `instance` | `hashCode` | `()` | `int` | Evaluates boolean predicate `hashCode` on `DataBinReader` |
| `instance` | `getClass` | `()` | `Class` | Retrieves `Class` property from `DataBinReader` |
| `instance` | `notify` | `()` | `void` | Performs notify operation |
| `instance` | `notifyAll` | `()` | `void` | Performs notify all operation |
| `instance` | `wait` | `(arg0: long)` | `void` | Performs wait operation |
| `instance` | `wait` | `(arg0: long, arg1: int)` | `void` | Performs wait operation |
| `instance` | `wait` | `()` | `void` | Performs wait operation |
| `static` | `getInstance` | `(arg0: int, arg1: int)` | `DataBinReader` | Retrieves `Instance` property from `DataBinReader` |

---

### `DataBinWriter`
- **Full Qualified Name:** `com.strategyquant.datalib.data.io.DataBinWriter`
- **Primary Job / Responsibility:** Market data abstraction and time-series container (`DataBinWriter`).

#### Fields
| Scope | Field Name | Type |
| :--- | :--- | :--- |
| `static` | `Log` | `Logger` |

#### Methods & Functions
| Modifiers | Method Name | Parameter Signatures | Return Type | Functional Description / Job |
| :--- | :--- | :--- | :--- | :--- |
| `instance` | `close` | `()` | `void` | Performs close operation |
| `instance` | `open` | `()` | `void` | Performs open operation |
| `instance` | `setParams` | `(arg0: ImportDataInfo, arg1: InstrumentInfo, arg2: JProgressBar)` | `void` | Sets `Params` configuration/state on `DataBinWriter` |
| `instance` | `setFileName` | `(arg0: String)` | `void` | Sets `FileName` configuration/state on `DataBinWriter` |
| `instance` | `writeData` | `(arg0: VersatileData)` | `void` | Performs write data operation |
| `instance` | `renameTempFile` | `(arg0: String)` | `void` | Performs rename temp file operation |
| `instance` | `getColumnsCount` | `()` | `int` | Retrieves `ColumnsCount` property from `DataBinWriter` |
| `instance` | `equals` | `(arg0: Object)` | `boolean` | Performs equals operation |
| `instance` | `toString` | `()` | `String` | Converts/serializes representation via `toString` |
| `instance` | `hashCode` | `()` | `int` | Evaluates boolean predicate `hashCode` on `DataBinWriter` |
| `instance` | `getClass` | `()` | `Class` | Retrieves `Class` property from `DataBinWriter` |
| `instance` | `notify` | `()` | `void` | Performs notify operation |
| `instance` | `notifyAll` | `()` | `void` | Performs notify all operation |
| `instance` | `wait` | `(arg0: long)` | `void` | Performs wait operation |
| `instance` | `wait` | `(arg0: long, arg1: int)` | `void` | Performs wait operation |
| `instance` | `wait` | `()` | `void` | Performs wait operation |
| `static` | `getInstance` | `(arg0: int, arg1: String, arg2: InstrumentInfo)` | `DataBinWriter` | Retrieves `Instance` property from `DataBinWriter` |

---

### `DataCsvLoader`
- **Full Qualified Name:** `com.strategyquant.datalib.data.io.DataCsvLoader`
- **Primary Job / Responsibility:** Market data abstraction and time-series container (`DataCsvLoader`).

#### Fields
| Scope | Field Name | Type |
| :--- | :--- | :--- |
| `static` | `InvalidTimeConsecution` | `String` |
| `static` | `Log` | `Logger` |
| `instance` | `beginTimeNewFile` | `long` |
| `instance` | `endTimeNewFile` | `long` |
| `instance` | `loadedRows` | `int` |
| `instance` | `tickData` | `VersatileData` |

#### Methods & Functions
| Modifiers | Method Name | Parameter Signatures | Return Type | Functional Description / Job |
| :--- | :--- | :--- | :--- | :--- |
| `instance` | `setParams` | `(arg0: ImportDataInfo, arg1: DataInfo, arg2: JProgressBar)` | `void` | Sets `Params` configuration/state on `DataCsvLoader` |
| `instance` | `openFile` | `()` | `void` | Performs open file operation |
| `instance` | `readData` | `()` | `boolean` | Performs read data operation |
| `instance` | `getIndicatorsCount` | `()` | `int` | Retrieves `IndicatorsCount` property from `DataCsvLoader` |
| `instance` | `checkFile` | `(arg0: IProgressListener)` | `ImportDataInfo` | Performs check file operation |
| `instance` | `isDataCorrect` | `()` | `boolean` | Evaluates boolean predicate `isDataCorrect` on `DataCsvLoader` |
| `instance` | `getLoadedRows` | `()` | `int` | Retrieves `LoadedRows` property from `DataCsvLoader` |
| `instance` | `getCurrentLine` | `()` | `String` | Retrieves `CurrentLine` property from `DataCsvLoader` |
| `instance` | `getAveragePriceValue` | `()` | `double` | Retrieves `AveragePriceValue` property from `DataCsvLoader` |
| `instance` | `cancel` | `()` | `void` | Evaluates boolean predicate `cancel` on `DataCsvLoader` |
| `instance` | `close` | `()` | `void` | Performs close operation |
| `instance` | `parseLine` | `(arg0: String[], arg1: ImportDataInfo)` | `Object[]` | Converts/serializes representation via `parseLine` |
| `instance` | `pause` | `()` | `void` | Performs pause operation |
| `instance` | `restart` | `()` | `void` | Performs restart operation |
| `instance` | `recognizeTimeframe` | `()` | `String` | Performs recognize timeframe operation |
| `instance` | `countRows` | `(arg0: String)` | `int` | Performs count rows operation |
| `instance` | `equals` | `(arg0: Object)` | `boolean` | Performs equals operation |
| `instance` | `toString` | `()` | `String` | Converts/serializes representation via `toString` |
| `instance` | `hashCode` | `()` | `int` | Evaluates boolean predicate `hashCode` on `DataCsvLoader` |
| `instance` | `getClass` | `()` | `Class` | Retrieves `Class` property from `DataCsvLoader` |
| `instance` | `notify` | `()` | `void` | Performs notify operation |
| `instance` | `notifyAll` | `()` | `void` | Performs notify all operation |
| `instance` | `wait` | `(arg0: long)` | `void` | Performs wait operation |
| `instance` | `wait` | `(arg0: long, arg1: int)` | `void` | Performs wait operation |
| `instance` | `wait` | `()` | `void` | Performs wait operation |
| `static` | `reset` | `()` | `void` | Performs reset operation |
| `static` | `intValueOf` | `(arg0: String)` | `int` | Performs int value of operation |

---

### `DataCsvWriter`
- **Full Qualified Name:** `com.strategyquant.datalib.data.io.DataCsvWriter`
- **Primary Job / Responsibility:** Market data abstraction and time-series container (`DataCsvWriter`).

#### Methods & Functions
| Modifiers | Method Name | Parameter Signatures | Return Type | Functional Description / Job |
| :--- | :--- | :--- | :--- | :--- |
| `instance` | `write` | `(arg0: VersatileData)` | `void` | Performs write operation |
| `instance` | `openFile` | `()` | `void` | Performs open file operation |
| `instance` | `closeFile` | `()` | `void` | Performs close file operation |
| `instance` | `equals` | `(arg0: Object)` | `boolean` | Performs equals operation |
| `instance` | `toString` | `()` | `String` | Converts/serializes representation via `toString` |
| `instance` | `hashCode` | `()` | `int` | Evaluates boolean predicate `hashCode` on `DataCsvWriter` |
| `instance` | `getClass` | `()` | `Class` | Retrieves `Class` property from `DataCsvWriter` |
| `instance` | `notify` | `()` | `void` | Performs notify operation |
| `instance` | `notifyAll` | `()` | `void` | Performs notify all operation |
| `instance` | `wait` | `(arg0: long)` | `void` | Performs wait operation |
| `instance` | `wait` | `(arg0: long, arg1: int)` | `void` | Performs wait operation |
| `instance` | `wait` | `()` | `void` | Performs wait operation |

---

### `FileChannelReader`
- **Full Qualified Name:** `com.strategyquant.datalib.data.io.FileChannelReader`
- **Primary Job / Responsibility:** Market data abstraction and time-series container (`FileChannelReader`).

#### Methods & Functions
| Modifiers | Method Name | Parameter Signatures | Return Type | Functional Description / Job |
| :--- | :--- | :--- | :--- | :--- |
| `instance` | `position` | `(arg0: long)` | `long` | Performs position operation |
| `instance` | `position` | `()` | `long` | Performs position operation |
| `instance` | `getData` | `(arg0: VersatileData)` | `VersatileData` | Retrieves `Data` property from `FileChannelReader` |
| `instance` | `equals` | `(arg0: Object)` | `boolean` | Performs equals operation |
| `instance` | `toString` | `()` | `String` | Converts/serializes representation via `toString` |
| `instance` | `hashCode` | `()` | `int` | Evaluates boolean predicate `hashCode` on `FileChannelReader` |
| `instance` | `getClass` | `()` | `Class` | Retrieves `Class` property from `FileChannelReader` |
| `instance` | `notify` | `()` | `void` | Performs notify operation |
| `instance` | `notifyAll` | `()` | `void` | Performs notify all operation |
| `instance` | `wait` | `(arg0: long)` | `void` | Performs wait operation |
| `instance` | `wait` | `(arg0: long, arg1: int)` | `void` | Performs wait operation |
| `instance` | `wait` | `()` | `void` | Performs wait operation |
| `static` | `getDataSize` | `()` | `int` | Retrieves `DataSize` property from `FileChannelReader` |

---

### `FuturesVersatileData`
- **Full Qualified Name:** `com.strategyquant.datalib.data.io.FuturesVersatileData`
- **Primary Job / Responsibility:** Market data abstraction and time-series container (`FuturesVersatileData`).

#### Fields
| Scope | Field Name | Type |
| :--- | :--- | :--- |
| `static` | `ASK` | `int` |
| `static` | `BID` | `int` |
| `static` | `DT_ASK` | `int` |
| `static` | `DT_BID` | `int` |
| `static` | `DT_CLOSE` | `int` |
| `static` | `DT_CUSTOM_VALUE` | `int` |
| `static` | `DT_HIGH` | `int` |
| `static` | `DT_INDICATOR_VALUE` | `int` |
| `static` | `DT_LOW` | `int` |
| `static` | `DT_OPEN` | `int` |
| `static` | `DT_TIME` | `int` |
| `static` | `DT_UNUSED` | `int` |
| `static` | `DT_VOLUME` | `int` |
| `static` | `MINUTE_DATA` | `int` |
| `static` | `TICK_DATA` | `int` |
| `static` | `TimeNotDefined` | `long` |
| `static` | `UNKNOWN_DATA` | `int` |
| `instance` | `ask` | `double` |
| `instance` | `bid` | `double` |
| `instance` | `close` | `double` |
| `instance` | `connectionHash` | `int` |
| `instance` | `high` | `double` |
| `instance` | `low` | `double` |
| `instance` | `open` | `double` |
| `instance` | `openInterest` | `double` |
| `instance` | `sessionStartTime` | `long` |
| `instance` | `spread` | `double` |
| `instance` | `symbolHash` | `int` |
| `instance` | `time` | `long` |
| `instance` | `type` | `int` |
| `instance` | `volume` | `double` |

#### Methods & Functions
| Modifiers | Method Name | Parameter Signatures | Return Type | Functional Description / Job |
| :--- | :--- | :--- | :--- | :--- |
| `instance` | `reset` | `()` | `void` | Performs reset operation |
| `instance` | `toString` | `()` | `String` | Converts/serializes representation via `toString` |
| `instance` | `set` | `(arg0: int, arg1: long, arg2: int, arg3: int, arg4: double, arg5: double, arg6: double, arg7: double, arg8: double, arg9: double)` | `void` | Sets `` configuration/state on `FuturesVersatileData` |
| `instance` | `set` | `(arg0: int, arg1: long, arg2: int, arg3: int, arg4: double, arg5: double, arg6: double)` | `void` | Sets `` configuration/state on `FuturesVersatileData` |
| `instance` | `set` | `(arg0: int, arg1: long, arg2: int, arg3: int, arg4: double, arg5: double, arg6: double, arg7: double, arg8: double)` | `void` | Sets `` configuration/state on `FuturesVersatileData` |
| `instance` | `print` | `()` | `String` | Performs print operation |
| `instance` | `copyFrom` | `(arg0: FuturesVersatileData)` | `void` | Performs copy from operation |
| `instance` | `copyFrom` | `(arg0: VersatileData)` | `void` | Performs copy from operation |
| `instance` | `getCheckSum` | `()` | `int` | Retrieves `CheckSum` property from `FuturesVersatileData` |
| `instance` | `equals` | `(arg0: Object)` | `boolean` | Performs equals operation |
| `instance` | `hashCode` | `()` | `int` | Evaluates boolean predicate `hashCode` on `FuturesVersatileData` |
| `instance` | `getClass` | `()` | `Class` | Retrieves `Class` property from `FuturesVersatileData` |
| `instance` | `notify` | `()` | `void` | Performs notify operation |
| `instance` | `notifyAll` | `()` | `void` | Performs notify all operation |
| `instance` | `wait` | `(arg0: long)` | `void` | Performs wait operation |
| `instance` | `wait` | `(arg0: long, arg1: int)` | `void` | Performs wait operation |
| `instance` | `wait` | `()` | `void` | Performs wait operation |

---

### `ICanSeek`
- **Full Qualified Name:** `com.strategyquant.datalib.data.io.ICanSeek`
- **Primary Job / Responsibility:** Market data abstraction and time-series container (`ICanSeek`).

#### Methods & Functions
| Modifiers | Method Name | Parameter Signatures | Return Type | Functional Description / Job |
| :--- | :--- | :--- | :--- | :--- |
| `instance` | `seek` | `(arg0: int)` | `void` | Performs seek operation |

---

### `IDataLoader`
- **Full Qualified Name:** `com.strategyquant.datalib.data.io.IDataLoader`
- **Primary Job / Responsibility:** Market data abstraction and time-series container (`IDataLoader`).

#### Methods & Functions
| Modifiers | Method Name | Parameter Signatures | Return Type | Functional Description / Job |
| :--- | :--- | :--- | :--- | :--- |
| `instance` | `close` | `()` | `void` | Performs close operation |
| `instance` | `open` | `()` | `void` | Performs open operation |
| `instance` | `getDateFrom` | `()` | `long` | Retrieves `DateFrom` property from `IDataLoader` |
| `instance` | `hasNextTick` | `()` | `boolean` | Evaluates boolean predicate `hasNextTick` on `IDataLoader` |
| `instance` | `getNextTick` | `(arg0: VersatileData)` | `void` | Retrieves `NextTick` property from `IDataLoader` |
| `instance` | `nextTickTime` | `()` | `long` | Performs next tick time operation |
| `instance` | `isOHLCData` | `()` | `boolean` | Evaluates boolean predicate `isOHLCData` on `IDataLoader` |
| `instance` | `getDecimalPlaces` | `()` | `int` | Retrieves `DecimalPlaces` property from `IDataLoader` |
| `instance` | `isCrypted` | `()` | `boolean` | Evaluates boolean predicate `isCrypted` on `IDataLoader` |
| `instance` | `getTotalRecords` | `()` | `long` | Retrieves `TotalRecords` property from `IDataLoader` |
| `instance` | `getDataFilePath` | `()` | `String` | Retrieves `DataFilePath` property from `IDataLoader` |
| `instance` | `seek` | `(arg0: int)` | `void` | Performs seek operation |

---

### `ImportDataInfo`
- **Full Qualified Name:** `com.strategyquant.datalib.data.io.ImportDataInfo`
- **Primary Job / Responsibility:** Market data abstraction and time-series container (`ImportDataInfo`).

#### Fields
| Scope | Field Name | Type |
| :--- | :--- | :--- |
| `static` | `DT_OHLC` | `int` |
| `static` | `DT_TICK` | `int` |
| `instance` | `beginTimeNewFile` | `long` |
| `instance` | `columnTypes` | `ArrayList` |
| `instance` | `dataType` | `int` |
| `instance` | `dateFormat` | `String` |
| `instance` | `endTimeNewFile` | `long` |
| `instance` | `errorHandling` | `int` |
| `instance` | `filePath` | `String` |
| `instance` | `hasTwoVolumes` | `boolean` |
| `instance` | `importFileRows` | `int` |
| `instance` | `name` | `String` |
| `instance` | `reversedFile` | `boolean` |
| `instance` | `rowCount` | `int` |
| `instance` | `separator` | `String` |
| `instance` | `skipCols` | `int` |
| `instance` | `skipRows` | `int` |
| `instance` | `timeFormat` | `String` |
| `instance` | `timeframe` | `String` |
| `instance` | `timezone` | `String` |
| `instance` | `uniqImportString` | `String` |

#### Methods & Functions
| Modifiers | Method Name | Parameter Signatures | Return Type | Functional Description / Job |
| :--- | :--- | :--- | :--- | :--- |
| `instance` | `resetLastAskBid` | `()` | `void` | Performs reset last ask bid operation |
| `instance` | `isMT5TickImport` | `()` | `boolean` | Evaluates boolean predicate `isMT5TickImport` on `ImportDataInfo` |
| `instance` | `correctMT5TickData` | `(arg0: String[])` | `String[]` | Performs correct mt 5 tick data operation |
| `instance` | `equals` | `(arg0: Object)` | `boolean` | Performs equals operation |
| `instance` | `toString` | `()` | `String` | Converts/serializes representation via `toString` |
| `instance` | `hashCode` | `()` | `int` | Evaluates boolean predicate `hashCode` on `ImportDataInfo` |
| `instance` | `getClass` | `()` | `Class` | Retrieves `Class` property from `ImportDataInfo` |
| `instance` | `notify` | `()` | `void` | Performs notify operation |
| `instance` | `notifyAll` | `()` | `void` | Performs notify all operation |
| `instance` | `wait` | `(arg0: long)` | `void` | Performs wait operation |
| `instance` | `wait` | `(arg0: long, arg1: int)` | `void` | Performs wait operation |
| `instance` | `wait` | `()` | `void` | Performs wait operation |

---

### `MassImportDataInfo`
- **Full Qualified Name:** `com.strategyquant.datalib.data.io.MassImportDataInfo`
- **Primary Job / Responsibility:** Market data abstraction and time-series container (`MassImportDataInfo`).

#### Methods & Functions
| Modifiers | Method Name | Parameter Signatures | Return Type | Functional Description / Job |
| :--- | :--- | :--- | :--- | :--- |
| `instance` | `getPath` | `()` | `String` | Retrieves `Path` property from `MassImportDataInfo` |
| `instance` | `setFormat` | `(arg0: String)` | `void` | Sets `Format` configuration/state on `MassImportDataInfo` |
| `instance` | `getFormat` | `()` | `String` | Retrieves `Format` property from `MassImportDataInfo` |
| `instance` | `getInstrument` | `()` | `String` | Retrieves `Instrument` property from `MassImportDataInfo` |
| `instance` | `getTimeframe` | `()` | `String` | Retrieves `Timeframe` property from `MassImportDataInfo` |
| `instance` | `getBarType` | `()` | `int` | Retrieves `BarType` property from `MassImportDataInfo` |
| `instance` | `getConnection` | `()` | `String` | Retrieves `Connection` property from `MassImportDataInfo` |
| `instance` | `getPostfix` | `()` | `String` | Retrieves `Postfix` property from `MassImportDataInfo` |
| `instance` | `setPostfix` | `(arg0: String)` | `void` | Sets `Postfix` configuration/state on `MassImportDataInfo` |
| `instance` | `setConnection` | `(arg0: String)` | `void` | Sets `Connection` configuration/state on `MassImportDataInfo` |
| `instance` | `getTimezone` | `()` | `String` | Retrieves `Timezone` property from `MassImportDataInfo` |
| `instance` | `getDateFormat` | `()` | `String` | Retrieves `DateFormat` property from `MassImportDataInfo` |
| `instance` | `setTimeframe` | `(arg0: String)` | `void` | Sets `Timeframe` configuration/state on `MassImportDataInfo` |
| `instance` | `setDateFormat` | `(arg0: String)` | `void` | Sets `DateFormat` configuration/state on `MassImportDataInfo` |
| `instance` | `setPath` | `(arg0: String)` | `void` | Sets `Path` configuration/state on `MassImportDataInfo` |
| `instance` | `setBarType` | `(arg0: int)` | `void` | Sets `BarType` configuration/state on `MassImportDataInfo` |
| `instance` | `getOverwriteStrategy` | `()` | `OverwriteStrategy` | Retrieves `OverwriteStrategy` property from `MassImportDataInfo` |
| `instance` | `setOverwriteStrategy` | `(arg0: OverwriteStrategy)` | `void` | Sets `OverwriteStrategy` configuration/state on `MassImportDataInfo` |
| `instance` | `setInstrument` | `(arg0: String)` | `void` | Sets `Instrument` configuration/state on `MassImportDataInfo` |
| `instance` | `setTimezone` | `(arg0: String)` | `void` | Sets `Timezone` configuration/state on `MassImportDataInfo` |
| `instance` | `isCreateStockGroup` | `()` | `boolean` | Evaluates boolean predicate `isCreateStockGroup` on `MassImportDataInfo` |
| `instance` | `setCreateStockGroup` | `(arg0: boolean)` | `void` | Sets `CreateStockGroup` configuration/state on `MassImportDataInfo` |
| `instance` | `equals` | `(arg0: Object)` | `boolean` | Performs equals operation |
| `instance` | `toString` | `()` | `String` | Converts/serializes representation via `toString` |
| `instance` | `hashCode` | `()` | `int` | Evaluates boolean predicate `hashCode` on `MassImportDataInfo` |
| `instance` | `getClass` | `()` | `Class` | Retrieves `Class` property from `MassImportDataInfo` |
| `instance` | `notify` | `()` | `void` | Performs notify operation |
| `instance` | `notifyAll` | `()` | `void` | Performs notify all operation |
| `instance` | `wait` | `(arg0: long)` | `void` | Performs wait operation |
| `instance` | `wait` | `(arg0: long, arg1: int)` | `void` | Performs wait operation |
| `instance` | `wait` | `()` | `void` | Performs wait operation |

---

### `OverwriteStrategy`
- **Full Qualified Name:** `com.strategyquant.datalib.data.io.MassImportDataInfo.OverwriteStrategy`
- **Primary Job / Responsibility:** Market data abstraction and time-series container (`OverwriteStrategy`).

#### Fields
| Scope | Field Name | Type |
| :--- | :--- | :--- |
| `static` | `create` | `OverwriteStrategy` |
| `static` | `overwrite` | `OverwriteStrategy` |
| `static` | `skip` | `OverwriteStrategy` |

#### Methods & Functions
| Modifiers | Method Name | Parameter Signatures | Return Type | Functional Description / Job |
| :--- | :--- | :--- | :--- | :--- |
| `instance` | `name` | `()` | `String` | Performs name operation |
| `instance` | `equals` | `(arg0: Object)` | `boolean` | Performs equals operation |
| `instance` | `toString` | `()` | `String` | Converts/serializes representation via `toString` |
| `instance` | `hashCode` | `()` | `int` | Evaluates boolean predicate `hashCode` on `OverwriteStrategy` |
| `instance` | `compareTo` | `(arg0: Object)` | `int` | Performs compare to operation |
| `instance` | `compareTo` | `(arg0: Enum)` | `int` | Performs compare to operation |
| `instance` | `describeConstable` | `()` | `Optional` | Performs describe constable operation |
| `instance` | `getDeclaringClass` | `()` | `Class` | Retrieves `DeclaringClass` property from `OverwriteStrategy` |
| `instance` | `ordinal` | `()` | `int` | Performs ordinal operation |
| `instance` | `getClass` | `()` | `Class` | Retrieves `Class` property from `OverwriteStrategy` |
| `instance` | `notify` | `()` | `void` | Performs notify operation |
| `instance` | `notifyAll` | `()` | `void` | Performs notify all operation |
| `instance` | `wait` | `(arg0: long)` | `void` | Performs wait operation |
| `instance` | `wait` | `(arg0: long, arg1: int)` | `void` | Performs wait operation |
| `instance` | `wait` | `()` | `void` | Performs wait operation |
| `static` | `values` | `()` | `OverwriteStrategy[]` | Performs values operation |
| `static` | `valueOf` | `(arg0: String)` | `Enum` | Performs value of operation |
| `static` | `valueOf` | `(arg0: Class, arg1: String)` | `Enum` | Performs value of operation |

---

### `OhlcDataBinReader`
- **Full Qualified Name:** `com.strategyquant.datalib.data.io.OhlcDataBinReader`
- **Primary Job / Responsibility:** Market data abstraction and time-series container (`OhlcDataBinReader`).

#### Fields
| Scope | Field Name | Type |
| :--- | :--- | :--- |
| `instance` | `tickData` | `VersatileData` |

#### Methods & Functions
| Modifiers | Method Name | Parameter Signatures | Return Type | Functional Description / Job |
| :--- | :--- | :--- | :--- | :--- |
| `instance` | `readHeader` | `()` | `void` | Performs read header operation |
| `instance` | `readData` | `()` | `boolean` | Performs read data operation |
| `instance` | `getColumnsCount` | `()` | `int` | Retrieves `ColumnsCount` property from `OhlcDataBinReader` |
| `instance` | `setParams` | `(arg0: ImportDataInfo, arg1: DataInfo, arg2: JProgressBar)` | `void` | Sets `Params` configuration/state on `OhlcDataBinReader` |
| `instance` | `openFile` | `()` | `void` | Performs open file operation |
| `instance` | `closeFile` | `()` | `void` | Performs close file operation |
| `instance` | `setFileName` | `(arg0: String)` | `void` | Sets `FileName` configuration/state on `OhlcDataBinReader` |
| `instance` | `isDataCorrect` | `()` | `boolean` | Evaluates boolean predicate `isDataCorrect` on `OhlcDataBinReader` |
| `instance` | `equals` | `(arg0: Object)` | `boolean` | Performs equals operation |
| `instance` | `toString` | `()` | `String` | Converts/serializes representation via `toString` |
| `instance` | `hashCode` | `()` | `int` | Evaluates boolean predicate `hashCode` on `OhlcDataBinReader` |
| `instance` | `getClass` | `()` | `Class` | Retrieves `Class` property from `OhlcDataBinReader` |
| `instance` | `notify` | `()` | `void` | Performs notify operation |
| `instance` | `notifyAll` | `()` | `void` | Performs notify all operation |
| `instance` | `wait` | `(arg0: long)` | `void` | Performs wait operation |
| `instance` | `wait` | `(arg0: long, arg1: int)` | `void` | Performs wait operation |
| `instance` | `wait` | `()` | `void` | Performs wait operation |
| `static` | `getInstance` | `(arg0: int, arg1: int)` | `DataBinReader` | Retrieves `Instance` property from `OhlcDataBinReader` |

---

### `OhlcDataBinWriter`
- **Full Qualified Name:** `com.strategyquant.datalib.data.io.OhlcDataBinWriter`
- **Primary Job / Responsibility:** Market data abstraction and time-series container (`OhlcDataBinWriter`).

#### Fields
| Scope | Field Name | Type |
| :--- | :--- | :--- |
| `static` | `Log` | `Logger` |

#### Methods & Functions
| Modifiers | Method Name | Parameter Signatures | Return Type | Functional Description / Job |
| :--- | :--- | :--- | :--- | :--- |
| `instance` | `writeData` | `(arg0: VersatileData)` | `void` | Performs write data operation |
| `instance` | `getColumnsCount` | `()` | `int` | Retrieves `ColumnsCount` property from `OhlcDataBinWriter` |
| `instance` | `close` | `()` | `void` | Performs close operation |
| `instance` | `open` | `()` | `void` | Performs open operation |
| `instance` | `setParams` | `(arg0: ImportDataInfo, arg1: InstrumentInfo, arg2: JProgressBar)` | `void` | Sets `Params` configuration/state on `OhlcDataBinWriter` |
| `instance` | `setFileName` | `(arg0: String)` | `void` | Sets `FileName` configuration/state on `OhlcDataBinWriter` |
| `instance` | `renameTempFile` | `(arg0: String)` | `void` | Performs rename temp file operation |
| `instance` | `equals` | `(arg0: Object)` | `boolean` | Performs equals operation |
| `instance` | `toString` | `()` | `String` | Converts/serializes representation via `toString` |
| `instance` | `hashCode` | `()` | `int` | Evaluates boolean predicate `hashCode` on `OhlcDataBinWriter` |
| `instance` | `getClass` | `()` | `Class` | Retrieves `Class` property from `OhlcDataBinWriter` |
| `instance` | `notify` | `()` | `void` | Performs notify operation |
| `instance` | `notifyAll` | `()` | `void` | Performs notify all operation |
| `instance` | `wait` | `(arg0: long)` | `void` | Performs wait operation |
| `instance` | `wait` | `(arg0: long, arg1: int)` | `void` | Performs wait operation |
| `instance` | `wait` | `()` | `void` | Performs wait operation |
| `static` | `getInstance` | `(arg0: int, arg1: String, arg2: InstrumentInfo)` | `DataBinWriter` | Retrieves `Instance` property from `OhlcDataBinWriter` |

---

### `TickDataBinReader`
- **Full Qualified Name:** `com.strategyquant.datalib.data.io.TickDataBinReader`
- **Primary Job / Responsibility:** Market data abstraction and time-series container (`TickDataBinReader`).

#### Fields
| Scope | Field Name | Type |
| :--- | :--- | :--- |
| `instance` | `tickData` | `VersatileData` |

#### Methods & Functions
| Modifiers | Method Name | Parameter Signatures | Return Type | Functional Description / Job |
| :--- | :--- | :--- | :--- | :--- |
| `instance` | `readHeader` | `()` | `void` | Performs read header operation |
| `instance` | `openFile` | `()` | `void` | Performs open file operation |
| `instance` | `readData` | `()` | `boolean` | Performs read data operation |
| `instance` | `closeFile` | `()` | `void` | Performs close file operation |
| `instance` | `getColumnsCount` | `()` | `int` | Retrieves `ColumnsCount` property from `TickDataBinReader` |
| `instance` | `setParams` | `(arg0: ImportDataInfo, arg1: DataInfo, arg2: JProgressBar)` | `void` | Sets `Params` configuration/state on `TickDataBinReader` |
| `instance` | `setFileName` | `(arg0: String)` | `void` | Sets `FileName` configuration/state on `TickDataBinReader` |
| `instance` | `isDataCorrect` | `()` | `boolean` | Evaluates boolean predicate `isDataCorrect` on `TickDataBinReader` |
| `instance` | `equals` | `(arg0: Object)` | `boolean` | Performs equals operation |
| `instance` | `toString` | `()` | `String` | Converts/serializes representation via `toString` |
| `instance` | `hashCode` | `()` | `int` | Evaluates boolean predicate `hashCode` on `TickDataBinReader` |
| `instance` | `getClass` | `()` | `Class` | Retrieves `Class` property from `TickDataBinReader` |
| `instance` | `notify` | `()` | `void` | Performs notify operation |
| `instance` | `notifyAll` | `()` | `void` | Performs notify all operation |
| `instance` | `wait` | `(arg0: long)` | `void` | Performs wait operation |
| `instance` | `wait` | `(arg0: long, arg1: int)` | `void` | Performs wait operation |
| `instance` | `wait` | `()` | `void` | Performs wait operation |
| `static` | `getInstance` | `(arg0: int, arg1: int)` | `DataBinReader` | Retrieves `Instance` property from `TickDataBinReader` |

---

### `TickDataBinWriter`
- **Full Qualified Name:** `com.strategyquant.datalib.data.io.TickDataBinWriter`
- **Primary Job / Responsibility:** Market data abstraction and time-series container (`TickDataBinWriter`).

#### Fields
| Scope | Field Name | Type |
| :--- | :--- | :--- |
| `static` | `Log` | `Logger` |

#### Methods & Functions
| Modifiers | Method Name | Parameter Signatures | Return Type | Functional Description / Job |
| :--- | :--- | :--- | :--- | :--- |
| `instance` | `writeData` | `(arg0: VersatileData)` | `void` | Performs write data operation |
| `instance` | `writeHeader` | `()` | `void` | Performs write header operation |
| `instance` | `getColumnsCount` | `()` | `int` | Retrieves `ColumnsCount` property from `TickDataBinWriter` |
| `instance` | `close` | `()` | `void` | Performs close operation |
| `instance` | `open` | `()` | `void` | Performs open operation |
| `instance` | `setParams` | `(arg0: ImportDataInfo, arg1: InstrumentInfo, arg2: JProgressBar)` | `void` | Sets `Params` configuration/state on `TickDataBinWriter` |
| `instance` | `setFileName` | `(arg0: String)` | `void` | Sets `FileName` configuration/state on `TickDataBinWriter` |
| `instance` | `renameTempFile` | `(arg0: String)` | `void` | Performs rename temp file operation |
| `instance` | `equals` | `(arg0: Object)` | `boolean` | Performs equals operation |
| `instance` | `toString` | `()` | `String` | Converts/serializes representation via `toString` |
| `instance` | `hashCode` | `()` | `int` | Evaluates boolean predicate `hashCode` on `TickDataBinWriter` |
| `instance` | `getClass` | `()` | `Class` | Retrieves `Class` property from `TickDataBinWriter` |
| `instance` | `notify` | `()` | `void` | Performs notify operation |
| `instance` | `notifyAll` | `()` | `void` | Performs notify all operation |
| `instance` | `wait` | `(arg0: long)` | `void` | Performs wait operation |
| `instance` | `wait` | `(arg0: long, arg1: int)` | `void` | Performs wait operation |
| `instance` | `wait` | `()` | `void` | Performs wait operation |
| `static` | `getInstance` | `(arg0: int, arg1: String, arg2: InstrumentInfo)` | `DataBinWriter` | Retrieves `Instance` property from `TickDataBinWriter` |

---

### `TimeframeRecognizer`
- **Full Qualified Name:** `com.strategyquant.datalib.data.io.TimeframeRecognizer`
- **Primary Job / Responsibility:** Market data abstraction and time-series container (`TimeframeRecognizer`).

#### Fields
| Scope | Field Name | Type |
| :--- | :--- | :--- |
| `static` | `Log` | `Logger` |

#### Methods & Functions
| Modifiers | Method Name | Parameter Signatures | Return Type | Functional Description / Job |
| :--- | :--- | :--- | :--- | :--- |
| `instance` | `reset` | `()` | `void` | Performs reset operation |
| `instance` | `getTimeframe` | `()` | `String` | Retrieves `Timeframe` property from `TimeframeRecognizer` |
| `instance` | `processTime` | `(arg0: long)` | `void` | Performs process time operation |
| `instance` | `equals` | `(arg0: Object)` | `boolean` | Performs equals operation |
| `instance` | `toString` | `()` | `String` | Converts/serializes representation via `toString` |
| `instance` | `hashCode` | `()` | `int` | Evaluates boolean predicate `hashCode` on `TimeframeRecognizer` |
| `instance` | `getClass` | `()` | `Class` | Retrieves `Class` property from `TimeframeRecognizer` |
| `instance` | `notify` | `()` | `void` | Performs notify operation |
| `instance` | `notifyAll` | `()` | `void` | Performs notify all operation |
| `instance` | `wait` | `(arg0: long)` | `void` | Performs wait operation |
| `instance` | `wait` | `(arg0: long, arg1: int)` | `void` | Performs wait operation |
| `instance` | `wait` | `()` | `void` | Performs wait operation |

---

### `VersatileData`
- **Full Qualified Name:** `com.strategyquant.datalib.data.io.VersatileData`
- **Primary Job / Responsibility:** Market data abstraction and time-series container (`VersatileData`).

#### Fields
| Scope | Field Name | Type |
| :--- | :--- | :--- |
| `static` | `ASK` | `int` |
| `static` | `BID` | `int` |
| `static` | `DT_ASK` | `int` |
| `static` | `DT_BID` | `int` |
| `static` | `DT_CLOSE` | `int` |
| `static` | `DT_CUSTOM_VALUE` | `int` |
| `static` | `DT_HIGH` | `int` |
| `static` | `DT_INDICATOR_VALUE` | `int` |
| `static` | `DT_LOW` | `int` |
| `static` | `DT_OPEN` | `int` |
| `static` | `DT_TIME` | `int` |
| `static` | `DT_UNUSED` | `int` |
| `static` | `DT_VOLUME` | `int` |
| `static` | `MINUTE_DATA` | `int` |
| `static` | `TICK_DATA` | `int` |
| `static` | `TimeNotDefined` | `long` |
| `static` | `UNKNOWN_DATA` | `int` |
| `instance` | `ask` | `double` |
| `instance` | `bid` | `double` |
| `instance` | `close` | `double` |
| `instance` | `connectionHash` | `int` |
| `instance` | `high` | `double` |
| `instance` | `low` | `double` |
| `instance` | `open` | `double` |
| `instance` | `sessionStartTime` | `long` |
| `instance` | `spread` | `double` |
| `instance` | `symbolHash` | `int` |
| `instance` | `time` | `long` |
| `instance` | `type` | `int` |
| `instance` | `volume` | `double` |

#### Methods & Functions
| Modifiers | Method Name | Parameter Signatures | Return Type | Functional Description / Job |
| :--- | :--- | :--- | :--- | :--- |
| `instance` | `reset` | `()` | `void` | Performs reset operation |
| `instance` | `set` | `(arg0: int, arg1: long, arg2: int, arg3: int, arg4: double, arg5: double, arg6: double)` | `void` | Sets `` configuration/state on `VersatileData` |
| `instance` | `set` | `(arg0: int, arg1: long, arg2: int, arg3: int, arg4: double, arg5: double, arg6: double, arg7: double, arg8: double)` | `void` | Sets `` configuration/state on `VersatileData` |
| `instance` | `print` | `()` | `String` | Performs print operation |
| `instance` | `copyFrom` | `(arg0: VersatileData)` | `void` | Performs copy from operation |
| `instance` | `getCheckSum` | `()` | `int` | Retrieves `CheckSum` property from `VersatileData` |
| `instance` | `equals` | `(arg0: Object)` | `boolean` | Performs equals operation |
| `instance` | `toString` | `()` | `String` | Converts/serializes representation via `toString` |
| `instance` | `hashCode` | `()` | `int` | Evaluates boolean predicate `hashCode` on `VersatileData` |
| `instance` | `getClass` | `()` | `Class` | Retrieves `Class` property from `VersatileData` |
| `instance` | `notify` | `()` | `void` | Performs notify operation |
| `instance` | `notifyAll` | `()` | `void` | Performs notify all operation |
| `instance` | `wait` | `(arg0: long)` | `void` | Performs wait operation |
| `instance` | `wait` | `(arg0: long, arg1: int)` | `void` | Performs wait operation |
| `instance` | `wait` | `()` | `void` | Performs wait operation |

---

### `AskCol`
- **Full Qualified Name:** `com.strategyquant.datalib.data.io.columns.AskCol`
- **Primary Job / Responsibility:** Market data abstraction and time-series container (`AskCol`).

#### Methods & Functions
| Modifiers | Method Name | Parameter Signatures | Return Type | Functional Description / Job |
| :--- | :--- | :--- | :--- | :--- |
| `instance` | `getType` | `()` | `int` | Retrieves `Type` property from `AskCol` |
| `instance` | `getDataType` | `()` | `int` | Retrieves `DataType` property from `AskCol` |
| `instance` | `getName` | `()` | `String` | Retrieves `Name` property from `AskCol` |
| `instance` | `getClassName` | `()` | `String` | Retrieves `ClassName` property from `AskCol` |
| `instance` | `getCode` | `()` | `String` | Retrieves `Code` property from `AskCol` |
| `instance` | `equals` | `(arg0: Object)` | `boolean` | Performs equals operation |
| `instance` | `toString` | `()` | `String` | Converts/serializes representation via `toString` |
| `instance` | `hashCode` | `()` | `int` | Evaluates boolean predicate `hashCode` on `AskCol` |
| `instance` | `getClass` | `()` | `Class` | Retrieves `Class` property from `AskCol` |
| `instance` | `notify` | `()` | `void` | Performs notify operation |
| `instance` | `notifyAll` | `()` | `void` | Performs notify all operation |
| `instance` | `wait` | `(arg0: long)` | `void` | Performs wait operation |
| `instance` | `wait` | `(arg0: long, arg1: int)` | `void` | Performs wait operation |
| `instance` | `wait` | `()` | `void` | Performs wait operation |

---

### `BidCol`
- **Full Qualified Name:** `com.strategyquant.datalib.data.io.columns.BidCol`
- **Primary Job / Responsibility:** Market data abstraction and time-series container (`BidCol`).

#### Methods & Functions
| Modifiers | Method Name | Parameter Signatures | Return Type | Functional Description / Job |
| :--- | :--- | :--- | :--- | :--- |
| `instance` | `getType` | `()` | `int` | Retrieves `Type` property from `BidCol` |
| `instance` | `getDataType` | `()` | `int` | Retrieves `DataType` property from `BidCol` |
| `instance` | `getName` | `()` | `String` | Retrieves `Name` property from `BidCol` |
| `instance` | `getClassName` | `()` | `String` | Retrieves `ClassName` property from `BidCol` |
| `instance` | `getCode` | `()` | `String` | Retrieves `Code` property from `BidCol` |
| `instance` | `equals` | `(arg0: Object)` | `boolean` | Performs equals operation |
| `instance` | `toString` | `()` | `String` | Converts/serializes representation via `toString` |
| `instance` | `hashCode` | `()` | `int` | Evaluates boolean predicate `hashCode` on `BidCol` |
| `instance` | `getClass` | `()` | `Class` | Retrieves `Class` property from `BidCol` |
| `instance` | `notify` | `()` | `void` | Performs notify operation |
| `instance` | `notifyAll` | `()` | `void` | Performs notify all operation |
| `instance` | `wait` | `(arg0: long)` | `void` | Performs wait operation |
| `instance` | `wait` | `(arg0: long, arg1: int)` | `void` | Performs wait operation |
| `instance` | `wait` | `()` | `void` | Performs wait operation |

---

### `CloseCol`
- **Full Qualified Name:** `com.strategyquant.datalib.data.io.columns.CloseCol`
- **Primary Job / Responsibility:** Market data abstraction and time-series container (`CloseCol`).

#### Fields
| Scope | Field Name | Type |
| :--- | :--- | :--- |
| `static` | `NAME` | `String` |

#### Methods & Functions
| Modifiers | Method Name | Parameter Signatures | Return Type | Functional Description / Job |
| :--- | :--- | :--- | :--- | :--- |
| `instance` | `getType` | `()` | `int` | Retrieves `Type` property from `CloseCol` |
| `instance` | `getDataType` | `()` | `int` | Retrieves `DataType` property from `CloseCol` |
| `instance` | `getName` | `()` | `String` | Retrieves `Name` property from `CloseCol` |
| `instance` | `getClassName` | `()` | `String` | Retrieves `ClassName` property from `CloseCol` |
| `instance` | `getCode` | `()` | `String` | Retrieves `Code` property from `CloseCol` |
| `instance` | `equals` | `(arg0: Object)` | `boolean` | Performs equals operation |
| `instance` | `toString` | `()` | `String` | Converts/serializes representation via `toString` |
| `instance` | `hashCode` | `()` | `int` | Evaluates boolean predicate `hashCode` on `CloseCol` |
| `instance` | `getClass` | `()` | `Class` | Retrieves `Class` property from `CloseCol` |
| `instance` | `notify` | `()` | `void` | Performs notify operation |
| `instance` | `notifyAll` | `()` | `void` | Performs notify all operation |
| `instance` | `wait` | `(arg0: long)` | `void` | Performs wait operation |
| `instance` | `wait` | `(arg0: long, arg1: int)` | `void` | Performs wait operation |
| `instance` | `wait` | `()` | `void` | Performs wait operation |

---

### `CustomValue`
- **Full Qualified Name:** `com.strategyquant.datalib.data.io.columns.CustomValue`
- **Primary Job / Responsibility:** Market data abstraction and time-series container (`CustomValue`).

#### Methods & Functions
| Modifiers | Method Name | Parameter Signatures | Return Type | Functional Description / Job |
| :--- | :--- | :--- | :--- | :--- |
| `instance` | `getType` | `()` | `int` | Retrieves `Type` property from `CustomValue` |
| `instance` | `getDataType` | `()` | `int` | Retrieves `DataType` property from `CustomValue` |
| `instance` | `getName` | `()` | `String` | Retrieves `Name` property from `CustomValue` |
| `instance` | `getClassName` | `()` | `String` | Retrieves `ClassName` property from `CustomValue` |
| `instance` | `getCode` | `()` | `String` | Retrieves `Code` property from `CustomValue` |
| `instance` | `equals` | `(arg0: Object)` | `boolean` | Performs equals operation |
| `instance` | `toString` | `()` | `String` | Converts/serializes representation via `toString` |
| `instance` | `hashCode` | `()` | `int` | Evaluates boolean predicate `hashCode` on `CustomValue` |
| `instance` | `getClass` | `()` | `Class` | Retrieves `Class` property from `CustomValue` |
| `instance` | `notify` | `()` | `void` | Performs notify operation |
| `instance` | `notifyAll` | `()` | `void` | Performs notify all operation |
| `instance` | `wait` | `(arg0: long)` | `void` | Performs wait operation |
| `instance` | `wait` | `(arg0: long, arg1: int)` | `void` | Performs wait operation |
| `instance` | `wait` | `()` | `void` | Performs wait operation |

---

### `DateCol`
- **Full Qualified Name:** `com.strategyquant.datalib.data.io.columns.DateCol`
- **Primary Job / Responsibility:** Market data abstraction and time-series container (`DateCol`).

#### Fields
| Scope | Field Name | Type |
| :--- | :--- | :--- |
| `static` | `NAME` | `String` |

#### Methods & Functions
| Modifiers | Method Name | Parameter Signatures | Return Type | Functional Description / Job |
| :--- | :--- | :--- | :--- | :--- |
| `instance` | `getType` | `()` | `int` | Retrieves `Type` property from `DateCol` |
| `instance` | `getDataType` | `()` | `int` | Retrieves `DataType` property from `DateCol` |
| `instance` | `getName` | `()` | `String` | Retrieves `Name` property from `DateCol` |
| `instance` | `getClassName` | `()` | `String` | Retrieves `ClassName` property from `DateCol` |
| `instance` | `getCode` | `()` | `String` | Retrieves `Code` property from `DateCol` |
| `instance` | `equals` | `(arg0: Object)` | `boolean` | Performs equals operation |
| `instance` | `toString` | `()` | `String` | Converts/serializes representation via `toString` |
| `instance` | `hashCode` | `()` | `int` | Evaluates boolean predicate `hashCode` on `DateCol` |
| `instance` | `getClass` | `()` | `Class` | Retrieves `Class` property from `DateCol` |
| `instance` | `notify` | `()` | `void` | Performs notify operation |
| `instance` | `notifyAll` | `()` | `void` | Performs notify all operation |
| `instance` | `wait` | `(arg0: long)` | `void` | Performs wait operation |
| `instance` | `wait` | `(arg0: long, arg1: int)` | `void` | Performs wait operation |
| `instance` | `wait` | `()` | `void` | Performs wait operation |

---

### `DateTimeCol`
- **Full Qualified Name:** `com.strategyquant.datalib.data.io.columns.DateTimeCol`
- **Primary Job / Responsibility:** Market data abstraction and time-series container (`DateTimeCol`).

#### Methods & Functions
| Modifiers | Method Name | Parameter Signatures | Return Type | Functional Description / Job |
| :--- | :--- | :--- | :--- | :--- |
| `instance` | `getType` | `()` | `int` | Retrieves `Type` property from `DateTimeCol` |
| `instance` | `getDataType` | `()` | `int` | Retrieves `DataType` property from `DateTimeCol` |
| `instance` | `getName` | `()` | `String` | Retrieves `Name` property from `DateTimeCol` |
| `instance` | `getClassName` | `()` | `String` | Retrieves `ClassName` property from `DateTimeCol` |
| `instance` | `getCode` | `()` | `String` | Retrieves `Code` property from `DateTimeCol` |
| `instance` | `equals` | `(arg0: Object)` | `boolean` | Performs equals operation |
| `instance` | `toString` | `()` | `String` | Converts/serializes representation via `toString` |
| `instance` | `hashCode` | `()` | `int` | Evaluates boolean predicate `hashCode` on `DateTimeCol` |
| `instance` | `getClass` | `()` | `Class` | Retrieves `Class` property from `DateTimeCol` |
| `instance` | `notify` | `()` | `void` | Performs notify operation |
| `instance` | `notifyAll` | `()` | `void` | Performs notify all operation |
| `instance` | `wait` | `(arg0: long)` | `void` | Performs wait operation |
| `instance` | `wait` | `(arg0: long, arg1: int)` | `void` | Performs wait operation |
| `instance` | `wait` | `()` | `void` | Performs wait operation |

---

### `DefaultCol`
- **Full Qualified Name:** `com.strategyquant.datalib.data.io.columns.DefaultCol`
- **Primary Job / Responsibility:** Market data abstraction and time-series container (`DefaultCol`).

#### Methods & Functions
| Modifiers | Method Name | Parameter Signatures | Return Type | Functional Description / Job |
| :--- | :--- | :--- | :--- | :--- |
| `instance` | `getName` | `()` | `String` | Retrieves `Name` property from `DefaultCol` |
| `instance` | `getType` | `()` | `int` | Retrieves `Type` property from `DefaultCol` |
| `instance` | `getClassName` | `()` | `String` | Retrieves `ClassName` property from `DefaultCol` |
| `instance` | `getDataType` | `()` | `int` | Retrieves `DataType` property from `DefaultCol` |
| `instance` | `getCode` | `()` | `String` | Retrieves `Code` property from `DefaultCol` |
| `instance` | `equals` | `(arg0: Object)` | `boolean` | Performs equals operation |
| `instance` | `toString` | `()` | `String` | Converts/serializes representation via `toString` |
| `instance` | `hashCode` | `()` | `int` | Evaluates boolean predicate `hashCode` on `DefaultCol` |
| `instance` | `getClass` | `()` | `Class` | Retrieves `Class` property from `DefaultCol` |
| `instance` | `notify` | `()` | `void` | Performs notify operation |
| `instance` | `notifyAll` | `()` | `void` | Performs notify all operation |
| `instance` | `wait` | `(arg0: long)` | `void` | Performs wait operation |
| `instance` | `wait` | `(arg0: long, arg1: int)` | `void` | Performs wait operation |
| `instance` | `wait` | `()` | `void` | Performs wait operation |

---

### `FileFormat`
- **Full Qualified Name:** `com.strategyquant.datalib.data.io.columns.FileFormat`
- **Primary Job / Responsibility:** Market data abstraction and time-series container (`FileFormat`).

#### Fields
| Scope | Field Name | Type |
| :--- | :--- | :--- |
| `static` | `FF_DATE` | `int` |
| `static` | `FF_DATETIME` | `int` |
| `static` | `FF_DOUBLE` | `int` |
| `static` | `FF_INT` | `int` |
| `static` | `FF_INT_OR_DOUBLE` | `int` |
| `static` | `FF_LONG` | `int` |
| `static` | `FF_STRING` | `int` |
| `static` | `FF_TIME` | `int` |
| `static` | `FF_UNUSED` | `int` |

#### Methods & Functions
| Modifiers | Method Name | Parameter Signatures | Return Type | Functional Description / Job |
| :--- | :--- | :--- | :--- | :--- |
| `instance` | `equals` | `(arg0: Object)` | `boolean` | Performs equals operation |
| `instance` | `toString` | `()` | `String` | Converts/serializes representation via `toString` |
| `instance` | `hashCode` | `()` | `int` | Evaluates boolean predicate `hashCode` on `FileFormat` |
| `instance` | `getClass` | `()` | `Class` | Retrieves `Class` property from `FileFormat` |
| `instance` | `notify` | `()` | `void` | Performs notify operation |
| `instance` | `notifyAll` | `()` | `void` | Performs notify all operation |
| `instance` | `wait` | `(arg0: long)` | `void` | Performs wait operation |
| `instance` | `wait` | `(arg0: long, arg1: int)` | `void` | Performs wait operation |
| `instance` | `wait` | `()` | `void` | Performs wait operation |

---

### `HighCol`
- **Full Qualified Name:** `com.strategyquant.datalib.data.io.columns.HighCol`
- **Primary Job / Responsibility:** Market data abstraction and time-series container (`HighCol`).

#### Methods & Functions
| Modifiers | Method Name | Parameter Signatures | Return Type | Functional Description / Job |
| :--- | :--- | :--- | :--- | :--- |
| `instance` | `getType` | `()` | `int` | Retrieves `Type` property from `HighCol` |
| `instance` | `getDataType` | `()` | `int` | Retrieves `DataType` property from `HighCol` |
| `instance` | `getName` | `()` | `String` | Retrieves `Name` property from `HighCol` |
| `instance` | `getClassName` | `()` | `String` | Retrieves `ClassName` property from `HighCol` |
| `instance` | `getCode` | `()` | `String` | Retrieves `Code` property from `HighCol` |
| `instance` | `equals` | `(arg0: Object)` | `boolean` | Performs equals operation |
| `instance` | `toString` | `()` | `String` | Converts/serializes representation via `toString` |
| `instance` | `hashCode` | `()` | `int` | Evaluates boolean predicate `hashCode` on `HighCol` |
| `instance` | `getClass` | `()` | `Class` | Retrieves `Class` property from `HighCol` |
| `instance` | `notify` | `()` | `void` | Performs notify operation |
| `instance` | `notifyAll` | `()` | `void` | Performs notify all operation |
| `instance` | `wait` | `(arg0: long)` | `void` | Performs wait operation |
| `instance` | `wait` | `(arg0: long, arg1: int)` | `void` | Performs wait operation |
| `instance` | `wait` | `()` | `void` | Performs wait operation |

---

### `LowCol`
- **Full Qualified Name:** `com.strategyquant.datalib.data.io.columns.LowCol`
- **Primary Job / Responsibility:** Market data abstraction and time-series container (`LowCol`).

#### Methods & Functions
| Modifiers | Method Name | Parameter Signatures | Return Type | Functional Description / Job |
| :--- | :--- | :--- | :--- | :--- |
| `instance` | `getType` | `()` | `int` | Retrieves `Type` property from `LowCol` |
| `instance` | `getDataType` | `()` | `int` | Retrieves `DataType` property from `LowCol` |
| `instance` | `getName` | `()` | `String` | Retrieves `Name` property from `LowCol` |
| `instance` | `getClassName` | `()` | `String` | Retrieves `ClassName` property from `LowCol` |
| `instance` | `getCode` | `()` | `String` | Retrieves `Code` property from `LowCol` |
| `instance` | `equals` | `(arg0: Object)` | `boolean` | Performs equals operation |
| `instance` | `toString` | `()` | `String` | Converts/serializes representation via `toString` |
| `instance` | `hashCode` | `()` | `int` | Evaluates boolean predicate `hashCode` on `LowCol` |
| `instance` | `getClass` | `()` | `Class` | Retrieves `Class` property from `LowCol` |
| `instance` | `notify` | `()` | `void` | Performs notify operation |
| `instance` | `notifyAll` | `()` | `void` | Performs notify all operation |
| `instance` | `wait` | `(arg0: long)` | `void` | Performs wait operation |
| `instance` | `wait` | `(arg0: long, arg1: int)` | `void` | Performs wait operation |
| `instance` | `wait` | `()` | `void` | Performs wait operation |

---

### `OpenCol`
- **Full Qualified Name:** `com.strategyquant.datalib.data.io.columns.OpenCol`
- **Primary Job / Responsibility:** Market data abstraction and time-series container (`OpenCol`).

#### Methods & Functions
| Modifiers | Method Name | Parameter Signatures | Return Type | Functional Description / Job |
| :--- | :--- | :--- | :--- | :--- |
| `instance` | `getType` | `()` | `int` | Retrieves `Type` property from `OpenCol` |
| `instance` | `getDataType` | `()` | `int` | Retrieves `DataType` property from `OpenCol` |
| `instance` | `getName` | `()` | `String` | Retrieves `Name` property from `OpenCol` |
| `instance` | `getClassName` | `()` | `String` | Retrieves `ClassName` property from `OpenCol` |
| `instance` | `getCode` | `()` | `String` | Retrieves `Code` property from `OpenCol` |
| `instance` | `equals` | `(arg0: Object)` | `boolean` | Performs equals operation |
| `instance` | `toString` | `()` | `String` | Converts/serializes representation via `toString` |
| `instance` | `hashCode` | `()` | `int` | Evaluates boolean predicate `hashCode` on `OpenCol` |
| `instance` | `getClass` | `()` | `Class` | Retrieves `Class` property from `OpenCol` |
| `instance` | `notify` | `()` | `void` | Performs notify operation |
| `instance` | `notifyAll` | `()` | `void` | Performs notify all operation |
| `instance` | `wait` | `(arg0: long)` | `void` | Performs wait operation |
| `instance` | `wait` | `(arg0: long, arg1: int)` | `void` | Performs wait operation |
| `instance` | `wait` | `()` | `void` | Performs wait operation |

---

### `TimeCol`
- **Full Qualified Name:** `com.strategyquant.datalib.data.io.columns.TimeCol`
- **Primary Job / Responsibility:** Market data abstraction and time-series container (`TimeCol`).

#### Fields
| Scope | Field Name | Type |
| :--- | :--- | :--- |
| `static` | `NAME` | `String` |

#### Methods & Functions
| Modifiers | Method Name | Parameter Signatures | Return Type | Functional Description / Job |
| :--- | :--- | :--- | :--- | :--- |
| `instance` | `getType` | `()` | `int` | Retrieves `Type` property from `TimeCol` |
| `instance` | `getDataType` | `()` | `int` | Retrieves `DataType` property from `TimeCol` |
| `instance` | `getName` | `()` | `String` | Retrieves `Name` property from `TimeCol` |
| `instance` | `getClassName` | `()` | `String` | Retrieves `ClassName` property from `TimeCol` |
| `instance` | `getCode` | `()` | `String` | Retrieves `Code` property from `TimeCol` |
| `instance` | `equals` | `(arg0: Object)` | `boolean` | Performs equals operation |
| `instance` | `toString` | `()` | `String` | Converts/serializes representation via `toString` |
| `instance` | `hashCode` | `()` | `int` | Evaluates boolean predicate `hashCode` on `TimeCol` |
| `instance` | `getClass` | `()` | `Class` | Retrieves `Class` property from `TimeCol` |
| `instance` | `notify` | `()` | `void` | Performs notify operation |
| `instance` | `notifyAll` | `()` | `void` | Performs notify all operation |
| `instance` | `wait` | `(arg0: long)` | `void` | Performs wait operation |
| `instance` | `wait` | `(arg0: long, arg1: int)` | `void` | Performs wait operation |
| `instance` | `wait` | `()` | `void` | Performs wait operation |

---

### `UnusedCol`
- **Full Qualified Name:** `com.strategyquant.datalib.data.io.columns.UnusedCol`
- **Primary Job / Responsibility:** Market data abstraction and time-series container (`UnusedCol`).

#### Methods & Functions
| Modifiers | Method Name | Parameter Signatures | Return Type | Functional Description / Job |
| :--- | :--- | :--- | :--- | :--- |
| `instance` | `getType` | `()` | `int` | Retrieves `Type` property from `UnusedCol` |
| `instance` | `getDataType` | `()` | `int` | Retrieves `DataType` property from `UnusedCol` |
| `instance` | `getName` | `()` | `String` | Retrieves `Name` property from `UnusedCol` |
| `instance` | `getClassName` | `()` | `String` | Retrieves `ClassName` property from `UnusedCol` |
| `instance` | `getCode` | `()` | `String` | Retrieves `Code` property from `UnusedCol` |
| `instance` | `equals` | `(arg0: Object)` | `boolean` | Performs equals operation |
| `instance` | `toString` | `()` | `String` | Converts/serializes representation via `toString` |
| `instance` | `hashCode` | `()` | `int` | Evaluates boolean predicate `hashCode` on `UnusedCol` |
| `instance` | `getClass` | `()` | `Class` | Retrieves `Class` property from `UnusedCol` |
| `instance` | `notify` | `()` | `void` | Performs notify operation |
| `instance` | `notifyAll` | `()` | `void` | Performs notify all operation |
| `instance` | `wait` | `(arg0: long)` | `void` | Performs wait operation |
| `instance` | `wait` | `(arg0: long, arg1: int)` | `void` | Performs wait operation |
| `instance` | `wait` | `()` | `void` | Performs wait operation |

---

### `VolumeCol`
- **Full Qualified Name:** `com.strategyquant.datalib.data.io.columns.VolumeCol`
- **Primary Job / Responsibility:** Market data abstraction and time-series container (`VolumeCol`).

#### Methods & Functions
| Modifiers | Method Name | Parameter Signatures | Return Type | Functional Description / Job |
| :--- | :--- | :--- | :--- | :--- |
| `instance` | `getType` | `()` | `int` | Retrieves `Type` property from `VolumeCol` |
| `instance` | `getDataType` | `()` | `int` | Retrieves `DataType` property from `VolumeCol` |
| `instance` | `getName` | `()` | `String` | Retrieves `Name` property from `VolumeCol` |
| `instance` | `getClassName` | `()` | `String` | Retrieves `ClassName` property from `VolumeCol` |
| `instance` | `getCode` | `()` | `String` | Retrieves `Code` property from `VolumeCol` |
| `instance` | `equals` | `(arg0: Object)` | `boolean` | Performs equals operation |
| `instance` | `toString` | `()` | `String` | Converts/serializes representation via `toString` |
| `instance` | `hashCode` | `()` | `int` | Evaluates boolean predicate `hashCode` on `VolumeCol` |
| `instance` | `getClass` | `()` | `Class` | Retrieves `Class` property from `VolumeCol` |
| `instance` | `notify` | `()` | `void` | Performs notify operation |
| `instance` | `notifyAll` | `()` | `void` | Performs notify all operation |
| `instance` | `wait` | `(arg0: long)` | `void` | Performs wait operation |
| `instance` | `wait` | `(arg0: long, arg1: int)` | `void` | Performs wait operation |
| `instance` | `wait` | `()` | `void` | Performs wait operation |

---

### `DataBinReaderNew`
- **Full Qualified Name:** `com.strategyquant.datalib.data.io.newDataFormat.DataBinReaderNew`
- **Primary Job / Responsibility:** Market data abstraction and time-series container (`DataBinReaderNew`).

#### Fields
| Scope | Field Name | Type |
| :--- | :--- | :--- |
| `static` | `CRYPTED_DATA_TYPE` | `String` |
| `static` | `DATA_TYPE` | `String` |
| `static` | `HEADER_PREFIX` | `String` |
| `static` | `HEADER_SUFFIX` | `String` |
| `static` | `SUPPORTED_OLD_VERSION` | `String` |
| `static` | `VERSION` | `String` |
| `instance` | `tickData` | `VersatileData` |

#### Methods & Functions
| Modifiers | Method Name | Parameter Signatures | Return Type | Functional Description / Job |
| :--- | :--- | :--- | :--- | :--- |
| `instance` | `seek` | `(arg0: int)` | `void` | Performs seek operation |
| `instance` | `readHeader` | `()` | `void` | Performs read header operation |
| `instance` | `setParams` | `(arg0: ImportDataInfo, arg1: DataInfo, arg2: JProgressBar)` | `void` | Sets `Params` configuration/state on `DataBinReaderNew` |
| `instance` | `openFile` | `()` | `void` | Performs open file operation |
| `instance` | `dataRemaining` | `()` | `boolean` | Performs data remaining operation |
| `instance` | `readData` | `()` | `boolean` | Performs read data operation |
| `instance` | `closeFile` | `()` | `void` | Performs close file operation |
| `instance` | `setFileName` | `(arg0: String)` | `void` | Sets `FileName` configuration/state on `DataBinReaderNew` |
| `instance` | `setData` | `(arg0: byte[])` | `void` | Sets `Data` configuration/state on `DataBinReaderNew` |
| `instance` | `getTotalRecords` | `()` | `long` | Retrieves `TotalRecords` property from `DataBinReaderNew` |
| `instance` | `isDataCorrect` | `()` | `boolean` | Evaluates boolean predicate `isDataCorrect` on `DataBinReaderNew` |
| `instance` | `getColumnsCount` | `()` | `int` | Retrieves `ColumnsCount` property from `DataBinReaderNew` |
| `instance` | `isCrypted` | `()` | `boolean` | Evaluates boolean predicate `isCrypted` on `DataBinReaderNew` |
| `instance` | `setPassword` | `(arg0: String)` | `void` | Sets `Password` configuration/state on `DataBinReaderNew` |
| `instance` | `overrideDecimals` | `(arg0: int)` | `void` | Performs override decimals operation |
| `instance` | `equals` | `(arg0: Object)` | `boolean` | Performs equals operation |
| `instance` | `toString` | `()` | `String` | Converts/serializes representation via `toString` |
| `instance` | `hashCode` | `()` | `int` | Evaluates boolean predicate `hashCode` on `DataBinReaderNew` |
| `instance` | `getClass` | `()` | `Class` | Retrieves `Class` property from `DataBinReaderNew` |
| `instance` | `notify` | `()` | `void` | Performs notify operation |
| `instance` | `notifyAll` | `()` | `void` | Performs notify all operation |
| `instance` | `wait` | `(arg0: long)` | `void` | Performs wait operation |
| `instance` | `wait` | `(arg0: long, arg1: int)` | `void` | Performs wait operation |
| `instance` | `wait` | `()` | `void` | Performs wait operation |
| `static` | `getInstance` | `(arg0: int, arg1: InstrumentInfo)` | `DataBinReaderNew` | Retrieves `Instance` property from `DataBinReaderNew` |
| `static` | `setDecimals` | `(arg0: InstrumentInfo, arg1: DataManipulatorNew)` | `void` | Sets `Decimals` configuration/state on `DataBinReaderNew` |

---

### `DataBinWriterNew`
- **Full Qualified Name:** `com.strategyquant.datalib.data.io.newDataFormat.DataBinWriterNew`
- **Primary Job / Responsibility:** Market data abstraction and time-series container (`DataBinWriterNew`).

#### Fields
| Scope | Field Name | Type |
| :--- | :--- | :--- |
| `static` | `CRYPTED_DATA_TYPE` | `String` |
| `static` | `DATA_TYPE` | `String` |
| `static` | `HEADER_PREFIX` | `String` |
| `static` | `HEADER_SUFFIX` | `String` |
| `static` | `Log` | `Logger` |
| `static` | `SUPPORTED_OLD_VERSION` | `String` |
| `static` | `VERSION` | `String` |

#### Methods & Functions
| Modifiers | Method Name | Parameter Signatures | Return Type | Functional Description / Job |
| :--- | :--- | :--- | :--- | :--- |
| `instance` | `reset` | `()` | `void` | Performs reset operation |
| `instance` | `close` | `()` | `void` | Performs close operation |
| `instance` | `open` | `()` | `void` | Performs open operation |
| `instance` | `getFileName` | `()` | `String` | Retrieves `FileName` property from `DataBinWriterNew` |
| `instance` | `setFileName` | `(arg0: String)` | `void` | Sets `FileName` configuration/state on `DataBinWriterNew` |
| `instance` | `writeData` | `(arg0: VersatileData)` | `void` | Performs write data operation |
| `instance` | `renameTempFile` | `(arg0: String)` | `void` | Performs rename temp file operation |
| `instance` | `getColumnsCount` | `()` | `int` | Retrieves `ColumnsCount` property from `DataBinWriterNew` |
| `instance` | `isCrypted` | `()` | `boolean` | Evaluates boolean predicate `isCrypted` on `DataBinWriterNew` |
| `instance` | `setPassword` | `(arg0: String)` | `void` | Sets `Password` configuration/state on `DataBinWriterNew` |
| `instance` | `overrideDecimals` | `(arg0: int)` | `void` | Performs override decimals operation |
| `instance` | `equals` | `(arg0: Object)` | `boolean` | Performs equals operation |
| `instance` | `toString` | `()` | `String` | Converts/serializes representation via `toString` |
| `instance` | `hashCode` | `()` | `int` | Evaluates boolean predicate `hashCode` on `DataBinWriterNew` |
| `instance` | `getClass` | `()` | `Class` | Retrieves `Class` property from `DataBinWriterNew` |
| `instance` | `notify` | `()` | `void` | Performs notify operation |
| `instance` | `notifyAll` | `()` | `void` | Performs notify all operation |
| `instance` | `wait` | `(arg0: long)` | `void` | Performs wait operation |
| `instance` | `wait` | `(arg0: long, arg1: int)` | `void` | Performs wait operation |
| `instance` | `wait` | `()` | `void` | Performs wait operation |
| `static` | `getInstance` | `(arg0: int, arg1: String, arg2: InstrumentInfo)` | `DataBinWriterNew` | Retrieves `Instance` property from `DataBinWriterNew` |
| `static` | `getCryptedInstance` | `(arg0: int, arg1: String, arg2: InstrumentInfo)` | `DataBinWriterNew` | Retrieves `CryptedInstance` property from `DataBinWriterNew` |
| `static` | `setDecimals` | `(arg0: InstrumentInfo, arg1: DataManipulatorNew)` | `void` | Sets `Decimals` configuration/state on `DataBinWriterNew` |

---

### `DataManipulatorNew`
- **Full Qualified Name:** `com.strategyquant.datalib.data.io.newDataFormat.DataManipulatorNew`
- **Primary Job / Responsibility:** Market data abstraction and time-series container (`DataManipulatorNew`).

#### Fields
| Scope | Field Name | Type |
| :--- | :--- | :--- |
| `static` | `CRYPTED_DATA_TYPE` | `String` |
| `static` | `DATA_TYPE` | `String` |
| `static` | `HEADER_PREFIX` | `String` |
| `static` | `HEADER_SUFFIX` | `String` |
| `static` | `SUPPORTED_OLD_VERSION` | `String` |
| `static` | `VERSION` | `String` |

#### Methods & Functions
| Modifiers | Method Name | Parameter Signatures | Return Type | Functional Description / Job |
| :--- | :--- | :--- | :--- | :--- |
| `instance` | `isCrypted` | `()` | `boolean` | Evaluates boolean predicate `isCrypted` on `DataManipulatorNew` |
| `instance` | `setPassword` | `(arg0: String)` | `void` | Sets `Password` configuration/state on `DataManipulatorNew` |
| `instance` | `overrideDecimals` | `(arg0: int)` | `void` | Performs override decimals operation |
| `instance` | `equals` | `(arg0: Object)` | `boolean` | Performs equals operation |
| `instance` | `toString` | `()` | `String` | Converts/serializes representation via `toString` |
| `instance` | `hashCode` | `()` | `int` | Evaluates boolean predicate `hashCode` on `DataManipulatorNew` |
| `instance` | `getClass` | `()` | `Class` | Retrieves `Class` property from `DataManipulatorNew` |
| `instance` | `notify` | `()` | `void` | Performs notify operation |
| `instance` | `notifyAll` | `()` | `void` | Performs notify all operation |
| `instance` | `wait` | `(arg0: long)` | `void` | Performs wait operation |
| `instance` | `wait` | `(arg0: long, arg1: int)` | `void` | Performs wait operation |
| `instance` | `wait` | `()` | `void` | Performs wait operation |
| `static` | `setDecimals` | `(arg0: InstrumentInfo, arg1: DataManipulatorNew)` | `void` | Sets `Decimals` configuration/state on `DataManipulatorNew` |

---

### `FuturesDataBinReaderNew`
- **Full Qualified Name:** `com.strategyquant.datalib.data.io.newDataFormat.FuturesDataBinReaderNew`
- **Primary Job / Responsibility:** Market data abstraction and time-series container (`FuturesDataBinReaderNew`).

#### Fields
| Scope | Field Name | Type |
| :--- | :--- | :--- |
| `static` | `CRYPTED_DATA_TYPE` | `String` |
| `static` | `DATA_TYPE` | `String` |
| `static` | `HEADER_PREFIX` | `String` |
| `static` | `HEADER_SUFFIX` | `String` |
| `static` | `SUPPORTED_OLD_VERSION` | `String` |
| `static` | `VERSION` | `String` |
| `instance` | `tickData` | `VersatileData` |

#### Methods & Functions
| Modifiers | Method Name | Parameter Signatures | Return Type | Functional Description / Job |
| :--- | :--- | :--- | :--- | :--- |
| `instance` | `seek` | `(arg0: int)` | `void` | Performs seek operation |
| `instance` | `readHeader` | `()` | `void` | Performs read header operation |
| `instance` | `readData` | `()` | `boolean` | Performs read data operation |
| `instance` | `getTotalRecords` | `()` | `long` | Retrieves `TotalRecords` property from `FuturesDataBinReaderNew` |
| `instance` | `getColumnsCount` | `()` | `int` | Retrieves `ColumnsCount` property from `FuturesDataBinReaderNew` |
| `instance` | `overrideDecimals` | `(arg0: int)` | `void` | Performs override decimals operation |
| `instance` | `setParams` | `(arg0: ImportDataInfo, arg1: DataInfo, arg2: JProgressBar)` | `void` | Sets `Params` configuration/state on `FuturesDataBinReaderNew` |
| `instance` | `openFile` | `()` | `void` | Performs open file operation |
| `instance` | `dataRemaining` | `()` | `boolean` | Performs data remaining operation |
| `instance` | `closeFile` | `()` | `void` | Performs close file operation |
| `instance` | `setFileName` | `(arg0: String)` | `void` | Sets `FileName` configuration/state on `FuturesDataBinReaderNew` |
| `instance` | `setData` | `(arg0: byte[])` | `void` | Sets `Data` configuration/state on `FuturesDataBinReaderNew` |
| `instance` | `isDataCorrect` | `()` | `boolean` | Evaluates boolean predicate `isDataCorrect` on `FuturesDataBinReaderNew` |
| `instance` | `isCrypted` | `()` | `boolean` | Evaluates boolean predicate `isCrypted` on `FuturesDataBinReaderNew` |
| `instance` | `setPassword` | `(arg0: String)` | `void` | Sets `Password` configuration/state on `FuturesDataBinReaderNew` |
| `instance` | `equals` | `(arg0: Object)` | `boolean` | Performs equals operation |
| `instance` | `toString` | `()` | `String` | Converts/serializes representation via `toString` |
| `instance` | `hashCode` | `()` | `int` | Evaluates boolean predicate `hashCode` on `FuturesDataBinReaderNew` |
| `instance` | `getClass` | `()` | `Class` | Retrieves `Class` property from `FuturesDataBinReaderNew` |
| `instance` | `notify` | `()` | `void` | Performs notify operation |
| `instance` | `notifyAll` | `()` | `void` | Performs notify all operation |
| `instance` | `wait` | `(arg0: long)` | `void` | Performs wait operation |
| `instance` | `wait` | `(arg0: long, arg1: int)` | `void` | Performs wait operation |
| `instance` | `wait` | `()` | `void` | Performs wait operation |
| `static` | `getInstance` | `(arg0: int, arg1: InstrumentInfo)` | `DataBinReaderNew` | Retrieves `Instance` property from `FuturesDataBinReaderNew` |
| `static` | `setDecimals` | `(arg0: InstrumentInfo, arg1: DataManipulatorNew)` | `void` | Sets `Decimals` configuration/state on `FuturesDataBinReaderNew` |

---

### `FuturesDataBinWriterNew`
- **Full Qualified Name:** `com.strategyquant.datalib.data.io.newDataFormat.FuturesDataBinWriterNew`
- **Primary Job / Responsibility:** Market data abstraction and time-series container (`FuturesDataBinWriterNew`).

#### Fields
| Scope | Field Name | Type |
| :--- | :--- | :--- |
| `static` | `CRYPTED_DATA_TYPE` | `String` |
| `static` | `DATA_TYPE` | `String` |
| `static` | `HEADER_PREFIX` | `String` |
| `static` | `HEADER_SUFFIX` | `String` |
| `static` | `Log` | `Logger` |
| `static` | `SUPPORTED_OLD_VERSION` | `String` |
| `static` | `VERSION` | `String` |

#### Methods & Functions
| Modifiers | Method Name | Parameter Signatures | Return Type | Functional Description / Job |
| :--- | :--- | :--- | :--- | :--- |
| `instance` | `reset` | `()` | `void` | Performs reset operation |
| `instance` | `close` | `()` | `void` | Performs close operation |
| `instance` | `writeData` | `(arg0: VersatileData)` | `void` | Performs write data operation |
| `instance` | `getColumnsCount` | `()` | `int` | Retrieves `ColumnsCount` property from `FuturesDataBinWriterNew` |
| `instance` | `overrideDecimals` | `(arg0: int)` | `void` | Performs override decimals operation |
| `instance` | `open` | `()` | `void` | Performs open operation |
| `instance` | `getFileName` | `()` | `String` | Retrieves `FileName` property from `FuturesDataBinWriterNew` |
| `instance` | `setFileName` | `(arg0: String)` | `void` | Sets `FileName` configuration/state on `FuturesDataBinWriterNew` |
| `instance` | `renameTempFile` | `(arg0: String)` | `void` | Performs rename temp file operation |
| `instance` | `isCrypted` | `()` | `boolean` | Evaluates boolean predicate `isCrypted` on `FuturesDataBinWriterNew` |
| `instance` | `setPassword` | `(arg0: String)` | `void` | Sets `Password` configuration/state on `FuturesDataBinWriterNew` |
| `instance` | `equals` | `(arg0: Object)` | `boolean` | Performs equals operation |
| `instance` | `toString` | `()` | `String` | Converts/serializes representation via `toString` |
| `instance` | `hashCode` | `()` | `int` | Evaluates boolean predicate `hashCode` on `FuturesDataBinWriterNew` |
| `instance` | `getClass` | `()` | `Class` | Retrieves `Class` property from `FuturesDataBinWriterNew` |
| `instance` | `notify` | `()` | `void` | Performs notify operation |
| `instance` | `notifyAll` | `()` | `void` | Performs notify all operation |
| `instance` | `wait` | `(arg0: long)` | `void` | Performs wait operation |
| `instance` | `wait` | `(arg0: long, arg1: int)` | `void` | Performs wait operation |
| `instance` | `wait` | `()` | `void` | Performs wait operation |
| `static` | `getInstance` | `(arg0: int, arg1: String, arg2: InstrumentInfo)` | `DataBinWriterNew` | Retrieves `Instance` property from `FuturesDataBinWriterNew` |
| `static` | `getCryptedInstance` | `(arg0: int, arg1: String, arg2: InstrumentInfo)` | `DataBinWriterNew` | Retrieves `CryptedInstance` property from `FuturesDataBinWriterNew` |
| `static` | `setDecimals` | `(arg0: InstrumentInfo, arg1: DataManipulatorNew)` | `void` | Sets `Decimals` configuration/state on `FuturesDataBinWriterNew` |

---

### `FuturesDataReader`
- **Full Qualified Name:** `com.strategyquant.datalib.data.io.newDataFormat.FuturesDataReader`
- **Primary Job / Responsibility:** Market data abstraction and time-series container (`FuturesDataReader`).

#### Fields
| Scope | Field Name | Type |
| :--- | :--- | :--- |
| `static` | `ASIS` | `int` |
| `static` | `BLOCK_LENGTH` | `int` |
| `static` | `BYTE` | `int` |
| `static` | `INT` | `int` |
| `static` | `LONG` | `int` |
| `static` | `MINUS` | `int` |
| `static` | `OLD_VOLUME_CONSTANT` | `double` |
| `static` | `PLUS` | `int` |
| `static` | `SHORT` | `int` |
| `static` | `VOLUME_CONSTANT` | `double` |

#### Methods & Functions
| Modifiers | Method Name | Parameter Signatures | Return Type | Functional Description / Job |
| :--- | :--- | :--- | :--- | :--- |
| `instance` | `readData` | `(arg0: IRandomAccessReader, arg1: FuturesVersatileData)` | `void` | Performs read data operation |
| `instance` | `seek` | `(arg0: IRandomAccessReader, arg1: long)` | `void` | Performs seek operation |
| `instance` | `setDataStartPosition` | `(arg0: long)` | `void` | Sets `DataStartPosition` configuration/state on `FuturesDataReader` |
| `instance` | `reset` | `()` | `void` | Performs reset operation |
| `instance` | `getDecimals` | `()` | `int` | Retrieves `Decimals` property from `FuturesDataReader` |
| `instance` | `setVolumeConstant` | `(arg0: double)` | `void` | Sets `VolumeConstant` configuration/state on `FuturesDataReader` |
| `instance` | `overrideDecimals` | `(arg0: int)` | `void` | Performs override decimals operation |
| `instance` | `equals` | `(arg0: Object)` | `boolean` | Performs equals operation |
| `instance` | `toString` | `()` | `String` | Converts/serializes representation via `toString` |
| `instance` | `hashCode` | `()` | `int` | Evaluates boolean predicate `hashCode` on `FuturesDataReader` |
| `instance` | `getClass` | `()` | `Class` | Retrieves `Class` property from `FuturesDataReader` |
| `instance` | `notify` | `()` | `void` | Performs notify operation |
| `instance` | `notifyAll` | `()` | `void` | Performs notify all operation |
| `instance` | `wait` | `(arg0: long)` | `void` | Performs wait operation |
| `instance` | `wait` | `(arg0: long, arg1: int)` | `void` | Performs wait operation |
| `instance` | `wait` | `()` | `void` | Performs wait operation |
| `static` | `getDataType` | `(arg0: long)` | `int` | Retrieves `DataType` property from `FuturesDataReader` |
| `static` | `getLogicType` | `(arg0: long)` | `int` | Retrieves `LogicType` property from `FuturesDataReader` |
| `static` | `printBits` | `(arg0: byte)` | `void` | Performs print bits operation |

---

### `FuturesDataWriter`
- **Full Qualified Name:** `com.strategyquant.datalib.data.io.newDataFormat.FuturesDataWriter`
- **Primary Job / Responsibility:** Market data abstraction and time-series container (`FuturesDataWriter`).

#### Fields
| Scope | Field Name | Type |
| :--- | :--- | :--- |
| `static` | `ASIS` | `int` |
| `static` | `BLOCK_LENGTH` | `int` |
| `static` | `BLOCK_START_MAGIC` | `byte[]` |
| `static` | `BYTE` | `int` |
| `static` | `INT` | `int` |
| `static` | `LONG` | `int` |
| `static` | `MINUS` | `int` |
| `static` | `OLD_VOLUME_CONSTANT` | `double` |
| `static` | `PLUS` | `int` |
| `static` | `SHORT` | `int` |
| `static` | `VOLUME_CONSTANT` | `double` |

#### Methods & Functions
| Modifiers | Method Name | Parameter Signatures | Return Type | Functional Description / Job |
| :--- | :--- | :--- | :--- | :--- |
| `instance` | `writeData` | `(arg0: DataOutputStream, arg1: FuturesVersatileData)` | `void` | Performs write data operation |
| `instance` | `getSavedCount` | `()` | `long` | Retrieves `SavedCount` property from `FuturesDataWriter` |
| `instance` | `reset` | `()` | `void` | Performs reset operation |
| `instance` | `getDecimals` | `()` | `int` | Retrieves `Decimals` property from `FuturesDataWriter` |
| `instance` | `setVolumeConstant` | `(arg0: double)` | `void` | Sets `VolumeConstant` configuration/state on `FuturesDataWriter` |
| `instance` | `overrideDecimals` | `(arg0: int)` | `void` | Performs override decimals operation |
| `instance` | `equals` | `(arg0: Object)` | `boolean` | Performs equals operation |
| `instance` | `toString` | `()` | `String` | Converts/serializes representation via `toString` |
| `instance` | `hashCode` | `()` | `int` | Evaluates boolean predicate `hashCode` on `FuturesDataWriter` |
| `instance` | `getClass` | `()` | `Class` | Retrieves `Class` property from `FuturesDataWriter` |
| `instance` | `notify` | `()` | `void` | Performs notify operation |
| `instance` | `notifyAll` | `()` | `void` | Performs notify all operation |
| `instance` | `wait` | `(arg0: long)` | `void` | Performs wait operation |
| `instance` | `wait` | `(arg0: long, arg1: int)` | `void` | Performs wait operation |
| `instance` | `wait` | `()` | `void` | Performs wait operation |
| `static` | `getDataType` | `(arg0: long)` | `int` | Retrieves `DataType` property from `FuturesDataWriter` |
| `static` | `getLogicType` | `(arg0: long)` | `int` | Retrieves `LogicType` property from `FuturesDataWriter` |
| `static` | `printBits` | `(arg0: byte)` | `void` | Performs print bits operation |

---

### `IRandomAccessReader`
- **Full Qualified Name:** `com.strategyquant.datalib.data.io.newDataFormat.IRandomAccessReader`
- **Primary Job / Responsibility:** Market data abstraction and time-series container (`IRandomAccessReader`).

#### Methods & Functions
| Modifiers | Method Name | Parameter Signatures | Return Type | Functional Description / Job |
| :--- | :--- | :--- | :--- | :--- |
| `instance` | `getLength` | `()` | `long` | Retrieves `Length` property from `IRandomAccessReader` |
| `instance` | `readInt` | `()` | `int` | Performs read int operation |
| `instance` | `readUTF` | `()` | `String` | Performs read utf operation |
| `instance` | `readLong` | `()` | `long` | Performs read long operation |
| `instance` | `readByte` | `()` | `byte` | Performs read byte operation |
| `instance` | `readShort` | `()` | `short` | Performs read short operation |
| `instance` | `readBytes` | `(arg0: byte[])` | `void` | Performs read bytes operation |
| `instance` | `readFloat` | `()` | `float` | Performs read float operation |
| `instance` | `readDouble` | `()` | `double` | Performs read double operation |
| `instance` | `seek` | `(arg0: long)` | `void` | Performs seek operation |
| `instance` | `getPosition` | `()` | `long` | Retrieves `Position` property from `IRandomAccessReader` |
| `instance` | `dataRemaining` | `()` | `boolean` | Performs data remaining operation |

---

### `NewDataFormat`
- **Full Qualified Name:** `com.strategyquant.datalib.data.io.newDataFormat.NewDataFormat`
- **Primary Job / Responsibility:** Market data abstraction and time-series container (`NewDataFormat`).

#### Fields
| Scope | Field Name | Type |
| :--- | :--- | :--- |
| `static` | `ASIS` | `int` |
| `static` | `BLOCK_LENGTH` | `int` |
| `static` | `BYTE` | `int` |
| `static` | `INT` | `int` |
| `static` | `LONG` | `int` |
| `static` | `MINUS` | `int` |
| `static` | `OLD_VOLUME_CONSTANT` | `double` |
| `static` | `PLUS` | `int` |
| `static` | `SHORT` | `int` |
| `static` | `VOLUME_CONSTANT` | `double` |

#### Methods & Functions
| Modifiers | Method Name | Parameter Signatures | Return Type | Functional Description / Job |
| :--- | :--- | :--- | :--- | :--- |
| `instance` | `reset` | `()` | `void` | Performs reset operation |
| `instance` | `getDecimals` | `()` | `int` | Retrieves `Decimals` property from `NewDataFormat` |
| `instance` | `setVolumeConstant` | `(arg0: double)` | `void` | Sets `VolumeConstant` configuration/state on `NewDataFormat` |
| `instance` | `overrideDecimals` | `(arg0: int)` | `void` | Performs override decimals operation |
| `instance` | `equals` | `(arg0: Object)` | `boolean` | Performs equals operation |
| `instance` | `toString` | `()` | `String` | Converts/serializes representation via `toString` |
| `instance` | `hashCode` | `()` | `int` | Evaluates boolean predicate `hashCode` on `NewDataFormat` |
| `instance` | `getClass` | `()` | `Class` | Retrieves `Class` property from `NewDataFormat` |
| `instance` | `notify` | `()` | `void` | Performs notify operation |
| `instance` | `notifyAll` | `()` | `void` | Performs notify all operation |
| `instance` | `wait` | `(arg0: long)` | `void` | Performs wait operation |
| `instance` | `wait` | `(arg0: long, arg1: int)` | `void` | Performs wait operation |
| `instance` | `wait` | `()` | `void` | Performs wait operation |
| `static` | `getDataType` | `(arg0: long)` | `int` | Retrieves `DataType` property from `NewDataFormat` |
| `static` | `getLogicType` | `(arg0: long)` | `int` | Retrieves `LogicType` property from `NewDataFormat` |
| `static` | `printBits` | `(arg0: byte)` | `void` | Performs print bits operation |

---

### `NewDataFormatReader`
- **Full Qualified Name:** `com.strategyquant.datalib.data.io.newDataFormat.NewDataFormatReader`
- **Primary Job / Responsibility:** Market data abstraction and time-series container (`NewDataFormatReader`).

#### Fields
| Scope | Field Name | Type |
| :--- | :--- | :--- |
| `static` | `ASIS` | `int` |
| `static` | `BLOCK_LENGTH` | `int` |
| `static` | `BYTE` | `int` |
| `static` | `INT` | `int` |
| `static` | `LONG` | `int` |
| `static` | `MINUS` | `int` |
| `static` | `OLD_VOLUME_CONSTANT` | `double` |
| `static` | `PLUS` | `int` |
| `static` | `SHORT` | `int` |
| `static` | `VOLUME_CONSTANT` | `double` |

#### Methods & Functions
| Modifiers | Method Name | Parameter Signatures | Return Type | Functional Description / Job |
| :--- | :--- | :--- | :--- | :--- |
| `instance` | `seek` | `(arg0: IRandomAccessReader, arg1: long)` | `void` | Performs seek operation |
| `instance` | `setDataStartPosition` | `(arg0: long)` | `void` | Sets `DataStartPosition` configuration/state on `NewDataFormatReader` |
| `instance` | `reset` | `()` | `void` | Performs reset operation |
| `instance` | `getDecimals` | `()` | `int` | Retrieves `Decimals` property from `NewDataFormatReader` |
| `instance` | `setVolumeConstant` | `(arg0: double)` | `void` | Sets `VolumeConstant` configuration/state on `NewDataFormatReader` |
| `instance` | `overrideDecimals` | `(arg0: int)` | `void` | Performs override decimals operation |
| `instance` | `equals` | `(arg0: Object)` | `boolean` | Performs equals operation |
| `instance` | `toString` | `()` | `String` | Converts/serializes representation via `toString` |
| `instance` | `hashCode` | `()` | `int` | Evaluates boolean predicate `hashCode` on `NewDataFormatReader` |
| `instance` | `getClass` | `()` | `Class` | Retrieves `Class` property from `NewDataFormatReader` |
| `instance` | `notify` | `()` | `void` | Performs notify operation |
| `instance` | `notifyAll` | `()` | `void` | Performs notify all operation |
| `instance` | `wait` | `(arg0: long)` | `void` | Performs wait operation |
| `instance` | `wait` | `(arg0: long, arg1: int)` | `void` | Performs wait operation |
| `instance` | `wait` | `()` | `void` | Performs wait operation |
| `static` | `getDataType` | `(arg0: long)` | `int` | Retrieves `DataType` property from `NewDataFormatReader` |
| `static` | `getLogicType` | `(arg0: long)` | `int` | Retrieves `LogicType` property from `NewDataFormatReader` |
| `static` | `printBits` | `(arg0: byte)` | `void` | Performs print bits operation |

---

### `NewDataFormatWritter`
- **Full Qualified Name:** `com.strategyquant.datalib.data.io.newDataFormat.NewDataFormatWritter`
- **Primary Job / Responsibility:** Market data abstraction and time-series container (`NewDataFormatWritter`).

#### Fields
| Scope | Field Name | Type |
| :--- | :--- | :--- |
| `static` | `ASIS` | `int` |
| `static` | `BLOCK_LENGTH` | `int` |
| `static` | `BLOCK_START_MAGIC` | `byte[]` |
| `static` | `BYTE` | `int` |
| `static` | `INT` | `int` |
| `static` | `LONG` | `int` |
| `static` | `MINUS` | `int` |
| `static` | `OLD_VOLUME_CONSTANT` | `double` |
| `static` | `PLUS` | `int` |
| `static` | `SHORT` | `int` |
| `static` | `VOLUME_CONSTANT` | `double` |

#### Methods & Functions
| Modifiers | Method Name | Parameter Signatures | Return Type | Functional Description / Job |
| :--- | :--- | :--- | :--- | :--- |
| `instance` | `getSavedCount` | `()` | `long` | Retrieves `SavedCount` property from `NewDataFormatWritter` |
| `instance` | `reset` | `()` | `void` | Performs reset operation |
| `instance` | `getDecimals` | `()` | `int` | Retrieves `Decimals` property from `NewDataFormatWritter` |
| `instance` | `setVolumeConstant` | `(arg0: double)` | `void` | Sets `VolumeConstant` configuration/state on `NewDataFormatWritter` |
| `instance` | `overrideDecimals` | `(arg0: int)` | `void` | Performs override decimals operation |
| `instance` | `equals` | `(arg0: Object)` | `boolean` | Performs equals operation |
| `instance` | `toString` | `()` | `String` | Converts/serializes representation via `toString` |
| `instance` | `hashCode` | `()` | `int` | Evaluates boolean predicate `hashCode` on `NewDataFormatWritter` |
| `instance` | `getClass` | `()` | `Class` | Retrieves `Class` property from `NewDataFormatWritter` |
| `instance` | `notify` | `()` | `void` | Performs notify operation |
| `instance` | `notifyAll` | `()` | `void` | Performs notify all operation |
| `instance` | `wait` | `(arg0: long)` | `void` | Performs wait operation |
| `instance` | `wait` | `(arg0: long, arg1: int)` | `void` | Performs wait operation |
| `instance` | `wait` | `()` | `void` | Performs wait operation |
| `static` | `getDataType` | `(arg0: long)` | `int` | Retrieves `DataType` property from `NewDataFormatWritter` |
| `static` | `getLogicType` | `(arg0: long)` | `int` | Retrieves `LogicType` property from `NewDataFormatWritter` |
| `static` | `printBits` | `(arg0: byte)` | `void` | Performs print bits operation |

---

### `OhlcDataBinReaderNew`
- **Full Qualified Name:** `com.strategyquant.datalib.data.io.newDataFormat.OhlcDataBinReaderNew`
- **Primary Job / Responsibility:** Market data abstraction and time-series container (`OhlcDataBinReaderNew`).

#### Fields
| Scope | Field Name | Type |
| :--- | :--- | :--- |
| `static` | `CRYPTED_DATA_TYPE` | `String` |
| `static` | `DATA_TYPE` | `String` |
| `static` | `HEADER_PREFIX` | `String` |
| `static` | `HEADER_SUFFIX` | `String` |
| `static` | `SUPPORTED_OLD_VERSION` | `String` |
| `static` | `VERSION` | `String` |
| `instance` | `tickData` | `VersatileData` |

#### Methods & Functions
| Modifiers | Method Name | Parameter Signatures | Return Type | Functional Description / Job |
| :--- | :--- | :--- | :--- | :--- |
| `instance` | `seek` | `(arg0: int)` | `void` | Performs seek operation |
| `instance` | `readHeader` | `()` | `void` | Performs read header operation |
| `instance` | `readData` | `()` | `boolean` | Performs read data operation |
| `instance` | `getTotalRecords` | `()` | `long` | Retrieves `TotalRecords` property from `OhlcDataBinReaderNew` |
| `instance` | `getColumnsCount` | `()` | `int` | Retrieves `ColumnsCount` property from `OhlcDataBinReaderNew` |
| `instance` | `overrideDecimals` | `(arg0: int)` | `void` | Performs override decimals operation |
| `instance` | `setParams` | `(arg0: ImportDataInfo, arg1: DataInfo, arg2: JProgressBar)` | `void` | Sets `Params` configuration/state on `OhlcDataBinReaderNew` |
| `instance` | `openFile` | `()` | `void` | Performs open file operation |
| `instance` | `dataRemaining` | `()` | `boolean` | Performs data remaining operation |
| `instance` | `closeFile` | `()` | `void` | Performs close file operation |
| `instance` | `setFileName` | `(arg0: String)` | `void` | Sets `FileName` configuration/state on `OhlcDataBinReaderNew` |
| `instance` | `setData` | `(arg0: byte[])` | `void` | Sets `Data` configuration/state on `OhlcDataBinReaderNew` |
| `instance` | `isDataCorrect` | `()` | `boolean` | Evaluates boolean predicate `isDataCorrect` on `OhlcDataBinReaderNew` |
| `instance` | `isCrypted` | `()` | `boolean` | Evaluates boolean predicate `isCrypted` on `OhlcDataBinReaderNew` |
| `instance` | `setPassword` | `(arg0: String)` | `void` | Sets `Password` configuration/state on `OhlcDataBinReaderNew` |
| `instance` | `equals` | `(arg0: Object)` | `boolean` | Performs equals operation |
| `instance` | `toString` | `()` | `String` | Converts/serializes representation via `toString` |
| `instance` | `hashCode` | `()` | `int` | Evaluates boolean predicate `hashCode` on `OhlcDataBinReaderNew` |
| `instance` | `getClass` | `()` | `Class` | Retrieves `Class` property from `OhlcDataBinReaderNew` |
| `instance` | `notify` | `()` | `void` | Performs notify operation |
| `instance` | `notifyAll` | `()` | `void` | Performs notify all operation |
| `instance` | `wait` | `(arg0: long)` | `void` | Performs wait operation |
| `instance` | `wait` | `(arg0: long, arg1: int)` | `void` | Performs wait operation |
| `instance` | `wait` | `()` | `void` | Performs wait operation |
| `static` | `getInstance` | `(arg0: int, arg1: InstrumentInfo)` | `DataBinReaderNew` | Retrieves `Instance` property from `OhlcDataBinReaderNew` |
| `static` | `setDecimals` | `(arg0: InstrumentInfo, arg1: DataManipulatorNew)` | `void` | Sets `Decimals` configuration/state on `OhlcDataBinReaderNew` |

---

### `OhlcDataBinWriterNew`
- **Full Qualified Name:** `com.strategyquant.datalib.data.io.newDataFormat.OhlcDataBinWriterNew`
- **Primary Job / Responsibility:** Market data abstraction and time-series container (`OhlcDataBinWriterNew`).

#### Fields
| Scope | Field Name | Type |
| :--- | :--- | :--- |
| `static` | `CRYPTED_DATA_TYPE` | `String` |
| `static` | `DATA_TYPE` | `String` |
| `static` | `HEADER_PREFIX` | `String` |
| `static` | `HEADER_SUFFIX` | `String` |
| `static` | `Log` | `Logger` |
| `static` | `SUPPORTED_OLD_VERSION` | `String` |
| `static` | `VERSION` | `String` |

#### Methods & Functions
| Modifiers | Method Name | Parameter Signatures | Return Type | Functional Description / Job |
| :--- | :--- | :--- | :--- | :--- |
| `instance` | `reset` | `()` | `void` | Performs reset operation |
| `instance` | `close` | `()` | `void` | Performs close operation |
| `instance` | `writeData` | `(arg0: VersatileData)` | `void` | Performs write data operation |
| `instance` | `getColumnsCount` | `()` | `int` | Retrieves `ColumnsCount` property from `OhlcDataBinWriterNew` |
| `instance` | `overrideDecimals` | `(arg0: int)` | `void` | Performs override decimals operation |
| `instance` | `open` | `()` | `void` | Performs open operation |
| `instance` | `getFileName` | `()` | `String` | Retrieves `FileName` property from `OhlcDataBinWriterNew` |
| `instance` | `setFileName` | `(arg0: String)` | `void` | Sets `FileName` configuration/state on `OhlcDataBinWriterNew` |
| `instance` | `renameTempFile` | `(arg0: String)` | `void` | Performs rename temp file operation |
| `instance` | `isCrypted` | `()` | `boolean` | Evaluates boolean predicate `isCrypted` on `OhlcDataBinWriterNew` |
| `instance` | `setPassword` | `(arg0: String)` | `void` | Sets `Password` configuration/state on `OhlcDataBinWriterNew` |
| `instance` | `equals` | `(arg0: Object)` | `boolean` | Performs equals operation |
| `instance` | `toString` | `()` | `String` | Converts/serializes representation via `toString` |
| `instance` | `hashCode` | `()` | `int` | Evaluates boolean predicate `hashCode` on `OhlcDataBinWriterNew` |
| `instance` | `getClass` | `()` | `Class` | Retrieves `Class` property from `OhlcDataBinWriterNew` |
| `instance` | `notify` | `()` | `void` | Performs notify operation |
| `instance` | `notifyAll` | `()` | `void` | Performs notify all operation |
| `instance` | `wait` | `(arg0: long)` | `void` | Performs wait operation |
| `instance` | `wait` | `(arg0: long, arg1: int)` | `void` | Performs wait operation |
| `instance` | `wait` | `()` | `void` | Performs wait operation |
| `static` | `getInstance` | `(arg0: int, arg1: String, arg2: InstrumentInfo)` | `DataBinWriterNew` | Retrieves `Instance` property from `OhlcDataBinWriterNew` |
| `static` | `getCryptedInstance` | `(arg0: int, arg1: String, arg2: InstrumentInfo)` | `DataBinWriterNew` | Retrieves `CryptedInstance` property from `OhlcDataBinWriterNew` |
| `static` | `setDecimals` | `(arg0: InstrumentInfo, arg1: DataManipulatorNew)` | `void` | Sets `Decimals` configuration/state on `OhlcDataBinWriterNew` |

---

### `OhlcDataReader`
- **Full Qualified Name:** `com.strategyquant.datalib.data.io.newDataFormat.OhlcDataReader`
- **Primary Job / Responsibility:** Market data abstraction and time-series container (`OhlcDataReader`).

#### Fields
| Scope | Field Name | Type |
| :--- | :--- | :--- |
| `static` | `ASIS` | `int` |
| `static` | `BLOCK_LENGTH` | `int` |
| `static` | `BYTE` | `int` |
| `static` | `INT` | `int` |
| `static` | `LONG` | `int` |
| `static` | `MINUS` | `int` |
| `static` | `OLD_VOLUME_CONSTANT` | `double` |
| `static` | `PLUS` | `int` |
| `static` | `SHORT` | `int` |
| `static` | `VOLUME_CONSTANT` | `double` |

#### Methods & Functions
| Modifiers | Method Name | Parameter Signatures | Return Type | Functional Description / Job |
| :--- | :--- | :--- | :--- | :--- |
| `instance` | `readData` | `(arg0: IRandomAccessReader, arg1: VersatileData)` | `void` | Performs read data operation |
| `instance` | `seek` | `(arg0: IRandomAccessReader, arg1: long)` | `void` | Performs seek operation |
| `instance` | `setDataStartPosition` | `(arg0: long)` | `void` | Sets `DataStartPosition` configuration/state on `OhlcDataReader` |
| `instance` | `reset` | `()` | `void` | Performs reset operation |
| `instance` | `getDecimals` | `()` | `int` | Retrieves `Decimals` property from `OhlcDataReader` |
| `instance` | `setVolumeConstant` | `(arg0: double)` | `void` | Sets `VolumeConstant` configuration/state on `OhlcDataReader` |
| `instance` | `overrideDecimals` | `(arg0: int)` | `void` | Performs override decimals operation |
| `instance` | `equals` | `(arg0: Object)` | `boolean` | Performs equals operation |
| `instance` | `toString` | `()` | `String` | Converts/serializes representation via `toString` |
| `instance` | `hashCode` | `()` | `int` | Evaluates boolean predicate `hashCode` on `OhlcDataReader` |
| `instance` | `getClass` | `()` | `Class` | Retrieves `Class` property from `OhlcDataReader` |
| `instance` | `notify` | `()` | `void` | Performs notify operation |
| `instance` | `notifyAll` | `()` | `void` | Performs notify all operation |
| `instance` | `wait` | `(arg0: long)` | `void` | Performs wait operation |
| `instance` | `wait` | `(arg0: long, arg1: int)` | `void` | Performs wait operation |
| `instance` | `wait` | `()` | `void` | Performs wait operation |
| `static` | `getDataType` | `(arg0: long)` | `int` | Retrieves `DataType` property from `OhlcDataReader` |
| `static` | `getLogicType` | `(arg0: long)` | `int` | Retrieves `LogicType` property from `OhlcDataReader` |
| `static` | `printBits` | `(arg0: byte)` | `void` | Performs print bits operation |

---

### `OhlcDataWriter`
- **Full Qualified Name:** `com.strategyquant.datalib.data.io.newDataFormat.OhlcDataWriter`
- **Primary Job / Responsibility:** Market data abstraction and time-series container (`OhlcDataWriter`).

#### Fields
| Scope | Field Name | Type |
| :--- | :--- | :--- |
| `static` | `ASIS` | `int` |
| `static` | `BLOCK_LENGTH` | `int` |
| `static` | `BLOCK_START_MAGIC` | `byte[]` |
| `static` | `BYTE` | `int` |
| `static` | `INT` | `int` |
| `static` | `LONG` | `int` |
| `static` | `MINUS` | `int` |
| `static` | `OLD_VOLUME_CONSTANT` | `double` |
| `static` | `PLUS` | `int` |
| `static` | `SHORT` | `int` |
| `static` | `VOLUME_CONSTANT` | `double` |

#### Methods & Functions
| Modifiers | Method Name | Parameter Signatures | Return Type | Functional Description / Job |
| :--- | :--- | :--- | :--- | :--- |
| `instance` | `putData` | `(arg0: RandomAccessReaderOffheap, arg1: VersatileData)` | `void` | Performs put data operation |
| `instance` | `putData` | `(arg0: ByteBuffer, arg1: VersatileData)` | `void` | Performs put data operation |
| `instance` | `writeData` | `(arg0: DataOutputStream, arg1: VersatileData)` | `void` | Performs write data operation |
| `instance` | `getSavedCount` | `()` | `long` | Retrieves `SavedCount` property from `OhlcDataWriter` |
| `instance` | `reset` | `()` | `void` | Performs reset operation |
| `instance` | `getDecimals` | `()` | `int` | Retrieves `Decimals` property from `OhlcDataWriter` |
| `instance` | `setVolumeConstant` | `(arg0: double)` | `void` | Sets `VolumeConstant` configuration/state on `OhlcDataWriter` |
| `instance` | `overrideDecimals` | `(arg0: int)` | `void` | Performs override decimals operation |
| `instance` | `equals` | `(arg0: Object)` | `boolean` | Performs equals operation |
| `instance` | `toString` | `()` | `String` | Converts/serializes representation via `toString` |
| `instance` | `hashCode` | `()` | `int` | Evaluates boolean predicate `hashCode` on `OhlcDataWriter` |
| `instance` | `getClass` | `()` | `Class` | Retrieves `Class` property from `OhlcDataWriter` |
| `instance` | `notify` | `()` | `void` | Performs notify operation |
| `instance` | `notifyAll` | `()` | `void` | Performs notify all operation |
| `instance` | `wait` | `(arg0: long)` | `void` | Performs wait operation |
| `instance` | `wait` | `(arg0: long, arg1: int)` | `void` | Performs wait operation |
| `instance` | `wait` | `()` | `void` | Performs wait operation |
| `static` | `getDataType` | `(arg0: long)` | `int` | Retrieves `DataType` property from `OhlcDataWriter` |
| `static` | `getLogicType` | `(arg0: long)` | `int` | Retrieves `LogicType` property from `OhlcDataWriter` |
| `static` | `printBits` | `(arg0: byte)` | `void` | Performs print bits operation |

---

### `OhlcToCsvExporter`
- **Full Qualified Name:** `com.strategyquant.datalib.data.io.newDataFormat.OhlcToCsvExporter`
- **Primary Job / Responsibility:** Market data abstraction and time-series container (`OhlcToCsvExporter`).

#### Methods & Functions
| Modifiers | Method Name | Parameter Signatures | Return Type | Functional Description / Job |
| :--- | :--- | :--- | :--- | :--- |
| `instance` | `equals` | `(arg0: Object)` | `boolean` | Performs equals operation |
| `instance` | `toString` | `()` | `String` | Converts/serializes representation via `toString` |
| `instance` | `hashCode` | `()` | `int` | Evaluates boolean predicate `hashCode` on `OhlcToCsvExporter` |
| `instance` | `getClass` | `()` | `Class` | Retrieves `Class` property from `OhlcToCsvExporter` |
| `instance` | `notify` | `()` | `void` | Performs notify operation |
| `instance` | `notifyAll` | `()` | `void` | Performs notify all operation |
| `instance` | `wait` | `(arg0: long)` | `void` | Performs wait operation |
| `instance` | `wait` | `(arg0: long, arg1: int)` | `void` | Performs wait operation |
| `instance` | `wait` | `()` | `void` | Performs wait operation |
| `static` | `main` | `(arg0: String[])` | `void` | Performs main operation |

---

### `RandomAccessReaderArray`
- **Full Qualified Name:** `com.strategyquant.datalib.data.io.newDataFormat.RandomAccessReaderArray`
- **Primary Job / Responsibility:** Market data abstraction and time-series container (`RandomAccessReaderArray`).

#### Methods & Functions
| Modifiers | Method Name | Parameter Signatures | Return Type | Functional Description / Job |
| :--- | :--- | :--- | :--- | :--- |
| `instance` | `getLength` | `()` | `long` | Retrieves `Length` property from `RandomAccessReaderArray` |
| `instance` | `readInt` | `()` | `int` | Performs read int operation |
| `instance` | `readUTF` | `()` | `String` | Performs read utf operation |
| `instance` | `readLong` | `()` | `long` | Performs read long operation |
| `instance` | `readByte` | `()` | `byte` | Performs read byte operation |
| `instance` | `readShort` | `()` | `short` | Performs read short operation |
| `instance` | `readBytes` | `(arg0: byte[])` | `void` | Performs read bytes operation |
| `instance` | `readFloat` | `()` | `float` | Performs read float operation |
| `instance` | `readDouble` | `()` | `double` | Performs read double operation |
| `instance` | `seek` | `(arg0: long)` | `void` | Performs seek operation |
| `instance` | `getPosition` | `()` | `long` | Retrieves `Position` property from `RandomAccessReaderArray` |
| `instance` | `dataRemaining` | `()` | `boolean` | Performs data remaining operation |
| `instance` | `equals` | `(arg0: Object)` | `boolean` | Performs equals operation |
| `instance` | `toString` | `()` | `String` | Converts/serializes representation via `toString` |
| `instance` | `hashCode` | `()` | `int` | Evaluates boolean predicate `hashCode` on `RandomAccessReaderArray` |
| `instance` | `getClass` | `()` | `Class` | Retrieves `Class` property from `RandomAccessReaderArray` |
| `instance` | `notify` | `()` | `void` | Performs notify operation |
| `instance` | `notifyAll` | `()` | `void` | Performs notify all operation |
| `instance` | `wait` | `(arg0: long)` | `void` | Performs wait operation |
| `instance` | `wait` | `(arg0: long, arg1: int)` | `void` | Performs wait operation |
| `instance` | `wait` | `()` | `void` | Performs wait operation |

---

### `RandomAccessReaderFile`
- **Full Qualified Name:** `com.strategyquant.datalib.data.io.newDataFormat.RandomAccessReaderFile`
- **Primary Job / Responsibility:** Market data abstraction and time-series container (`RandomAccessReaderFile`).

#### Methods & Functions
| Modifiers | Method Name | Parameter Signatures | Return Type | Functional Description / Job |
| :--- | :--- | :--- | :--- | :--- |
| `instance` | `getLength` | `()` | `long` | Retrieves `Length` property from `RandomAccessReaderFile` |
| `instance` | `readInt` | `()` | `int` | Performs read int operation |
| `instance` | `readUTF` | `()` | `String` | Performs read utf operation |
| `instance` | `readLong` | `()` | `long` | Performs read long operation |
| `instance` | `readByte` | `()` | `byte` | Performs read byte operation |
| `instance` | `readShort` | `()` | `short` | Performs read short operation |
| `instance` | `readBytes` | `(arg0: byte[])` | `void` | Performs read bytes operation |
| `instance` | `readFloat` | `()` | `float` | Performs read float operation |
| `instance` | `readDouble` | `()` | `double` | Performs read double operation |
| `instance` | `seek` | `(arg0: long)` | `void` | Performs seek operation |
| `instance` | `getPosition` | `()` | `long` | Retrieves `Position` property from `RandomAccessReaderFile` |
| `instance` | `openFile` | `()` | `void` | Performs open file operation |
| `instance` | `dataRemaining` | `()` | `boolean` | Performs data remaining operation |
| `instance` | `closeFile` | `()` | `void` | Performs close file operation |
| `instance` | `equals` | `(arg0: Object)` | `boolean` | Performs equals operation |
| `instance` | `toString` | `()` | `String` | Converts/serializes representation via `toString` |
| `instance` | `hashCode` | `()` | `int` | Evaluates boolean predicate `hashCode` on `RandomAccessReaderFile` |
| `instance` | `getClass` | `()` | `Class` | Retrieves `Class` property from `RandomAccessReaderFile` |
| `instance` | `notify` | `()` | `void` | Performs notify operation |
| `instance` | `notifyAll` | `()` | `void` | Performs notify all operation |
| `instance` | `wait` | `(arg0: long)` | `void` | Performs wait operation |
| `instance` | `wait` | `(arg0: long, arg1: int)` | `void` | Performs wait operation |
| `instance` | `wait` | `()` | `void` | Performs wait operation |

---

### `RandomAccessReaderOffheap`
- **Full Qualified Name:** `com.strategyquant.datalib.data.io.newDataFormat.RandomAccessReaderOffheap`
- **Primary Job / Responsibility:** Market data abstraction and time-series container (`RandomAccessReaderOffheap`).

#### Methods & Functions
| Modifiers | Method Name | Parameter Signatures | Return Type | Functional Description / Job |
| :--- | :--- | :--- | :--- | :--- |
| `instance` | `put` | `(arg0: byte[])` | `void` | Performs put operation |
| `instance` | `put` | `(arg0: byte)` | `void` | Performs put operation |
| `instance` | `getLength` | `()` | `long` | Retrieves `Length` property from `RandomAccessReaderOffheap` |
| `instance` | `putShort` | `(arg0: short)` | `void` | Performs put short operation |
| `instance` | `putInt` | `(arg0: int)` | `void` | Performs put int operation |
| `instance` | `putLong` | `(arg0: long)` | `void` | Performs put long operation |
| `instance` | `readInt` | `()` | `int` | Performs read int operation |
| `instance` | `readUTF` | `()` | `String` | Performs read utf operation |
| `instance` | `readLong` | `()` | `long` | Performs read long operation |
| `instance` | `readByte` | `()` | `byte` | Performs read byte operation |
| `instance` | `readShort` | `()` | `short` | Performs read short operation |
| `instance` | `readBytes` | `(arg0: byte[])` | `void` | Performs read bytes operation |
| `instance` | `readFloat` | `()` | `float` | Performs read float operation |
| `instance` | `readDouble` | `()` | `double` | Performs read double operation |
| `instance` | `seek` | `(arg0: long)` | `void` | Performs seek operation |
| `instance` | `getPosition` | `()` | `long` | Retrieves `Position` property from `RandomAccessReaderOffheap` |
| `instance` | `checkOffHeap` | `()` | `void` | Performs check off heap operation |
| `instance` | `dataRemaining` | `()` | `boolean` | Performs data remaining operation |
| `instance` | `equals` | `(arg0: Object)` | `boolean` | Performs equals operation |
| `instance` | `toString` | `()` | `String` | Converts/serializes representation via `toString` |
| `instance` | `hashCode` | `()` | `int` | Evaluates boolean predicate `hashCode` on `RandomAccessReaderOffheap` |
| `instance` | `getClass` | `()` | `Class` | Retrieves `Class` property from `RandomAccessReaderOffheap` |
| `instance` | `notify` | `()` | `void` | Performs notify operation |
| `instance` | `notifyAll` | `()` | `void` | Performs notify all operation |
| `instance` | `wait` | `(arg0: long)` | `void` | Performs wait operation |
| `instance` | `wait` | `(arg0: long, arg1: int)` | `void` | Performs wait operation |
| `instance` | `wait` | `()` | `void` | Performs wait operation |

---

### `TickDataBinReaderNew`
- **Full Qualified Name:** `com.strategyquant.datalib.data.io.newDataFormat.TickDataBinReaderNew`
- **Primary Job / Responsibility:** Market data abstraction and time-series container (`TickDataBinReaderNew`).

#### Fields
| Scope | Field Name | Type |
| :--- | :--- | :--- |
| `static` | `CRYPTED_DATA_TYPE` | `String` |
| `static` | `DATA_TYPE` | `String` |
| `static` | `HEADER_PREFIX` | `String` |
| `static` | `HEADER_SUFFIX` | `String` |
| `static` | `SUPPORTED_OLD_VERSION` | `String` |
| `static` | `VERSION` | `String` |
| `instance` | `tickData` | `VersatileData` |

#### Methods & Functions
| Modifiers | Method Name | Parameter Signatures | Return Type | Functional Description / Job |
| :--- | :--- | :--- | :--- | :--- |
| `instance` | `seek` | `(arg0: int)` | `void` | Performs seek operation |
| `instance` | `readHeader` | `()` | `void` | Performs read header operation |
| `instance` | `readData` | `()` | `boolean` | Performs read data operation |
| `instance` | `getTotalRecords` | `()` | `long` | Retrieves `TotalRecords` property from `TickDataBinReaderNew` |
| `instance` | `getColumnsCount` | `()` | `int` | Retrieves `ColumnsCount` property from `TickDataBinReaderNew` |
| `instance` | `overrideDecimals` | `(arg0: int)` | `void` | Performs override decimals operation |
| `instance` | `setParams` | `(arg0: ImportDataInfo, arg1: DataInfo, arg2: JProgressBar)` | `void` | Sets `Params` configuration/state on `TickDataBinReaderNew` |
| `instance` | `openFile` | `()` | `void` | Performs open file operation |
| `instance` | `dataRemaining` | `()` | `boolean` | Performs data remaining operation |
| `instance` | `closeFile` | `()` | `void` | Performs close file operation |
| `instance` | `setFileName` | `(arg0: String)` | `void` | Sets `FileName` configuration/state on `TickDataBinReaderNew` |
| `instance` | `setData` | `(arg0: byte[])` | `void` | Sets `Data` configuration/state on `TickDataBinReaderNew` |
| `instance` | `isDataCorrect` | `()` | `boolean` | Evaluates boolean predicate `isDataCorrect` on `TickDataBinReaderNew` |
| `instance` | `isCrypted` | `()` | `boolean` | Evaluates boolean predicate `isCrypted` on `TickDataBinReaderNew` |
| `instance` | `setPassword` | `(arg0: String)` | `void` | Sets `Password` configuration/state on `TickDataBinReaderNew` |
| `instance` | `equals` | `(arg0: Object)` | `boolean` | Performs equals operation |
| `instance` | `toString` | `()` | `String` | Converts/serializes representation via `toString` |
| `instance` | `hashCode` | `()` | `int` | Evaluates boolean predicate `hashCode` on `TickDataBinReaderNew` |
| `instance` | `getClass` | `()` | `Class` | Retrieves `Class` property from `TickDataBinReaderNew` |
| `instance` | `notify` | `()` | `void` | Performs notify operation |
| `instance` | `notifyAll` | `()` | `void` | Performs notify all operation |
| `instance` | `wait` | `(arg0: long)` | `void` | Performs wait operation |
| `instance` | `wait` | `(arg0: long, arg1: int)` | `void` | Performs wait operation |
| `instance` | `wait` | `()` | `void` | Performs wait operation |
| `static` | `getInstance` | `(arg0: int, arg1: InstrumentInfo)` | `DataBinReaderNew` | Retrieves `Instance` property from `TickDataBinReaderNew` |
| `static` | `setDecimals` | `(arg0: InstrumentInfo, arg1: DataManipulatorNew)` | `void` | Sets `Decimals` configuration/state on `TickDataBinReaderNew` |

---

### `TickDataBinWriterNew`
- **Full Qualified Name:** `com.strategyquant.datalib.data.io.newDataFormat.TickDataBinWriterNew`
- **Primary Job / Responsibility:** Market data abstraction and time-series container (`TickDataBinWriterNew`).

#### Fields
| Scope | Field Name | Type |
| :--- | :--- | :--- |
| `static` | `CRYPTED_DATA_TYPE` | `String` |
| `static` | `DATA_TYPE` | `String` |
| `static` | `HEADER_PREFIX` | `String` |
| `static` | `HEADER_SUFFIX` | `String` |
| `static` | `Log` | `Logger` |
| `static` | `SUPPORTED_OLD_VERSION` | `String` |
| `static` | `VERSION` | `String` |

#### Methods & Functions
| Modifiers | Method Name | Parameter Signatures | Return Type | Functional Description / Job |
| :--- | :--- | :--- | :--- | :--- |
| `instance` | `reset` | `()` | `void` | Performs reset operation |
| `instance` | `writeData` | `(arg0: VersatileData)` | `void` | Performs write data operation |
| `instance` | `getColumnsCount` | `()` | `int` | Retrieves `ColumnsCount` property from `TickDataBinWriterNew` |
| `instance` | `overrideDecimals` | `(arg0: int)` | `void` | Performs override decimals operation |
| `instance` | `close` | `()` | `void` | Performs close operation |
| `instance` | `open` | `()` | `void` | Performs open operation |
| `instance` | `getFileName` | `()` | `String` | Retrieves `FileName` property from `TickDataBinWriterNew` |
| `instance` | `setFileName` | `(arg0: String)` | `void` | Sets `FileName` configuration/state on `TickDataBinWriterNew` |
| `instance` | `renameTempFile` | `(arg0: String)` | `void` | Performs rename temp file operation |
| `instance` | `isCrypted` | `()` | `boolean` | Evaluates boolean predicate `isCrypted` on `TickDataBinWriterNew` |
| `instance` | `setPassword` | `(arg0: String)` | `void` | Sets `Password` configuration/state on `TickDataBinWriterNew` |
| `instance` | `equals` | `(arg0: Object)` | `boolean` | Performs equals operation |
| `instance` | `toString` | `()` | `String` | Converts/serializes representation via `toString` |
| `instance` | `hashCode` | `()` | `int` | Evaluates boolean predicate `hashCode` on `TickDataBinWriterNew` |
| `instance` | `getClass` | `()` | `Class` | Retrieves `Class` property from `TickDataBinWriterNew` |
| `instance` | `notify` | `()` | `void` | Performs notify operation |
| `instance` | `notifyAll` | `()` | `void` | Performs notify all operation |
| `instance` | `wait` | `(arg0: long)` | `void` | Performs wait operation |
| `instance` | `wait` | `(arg0: long, arg1: int)` | `void` | Performs wait operation |
| `instance` | `wait` | `()` | `void` | Performs wait operation |
| `static` | `getInstance` | `(arg0: int, arg1: String, arg2: InstrumentInfo)` | `DataBinWriterNew` | Retrieves `Instance` property from `TickDataBinWriterNew` |
| `static` | `getCryptedInstance` | `(arg0: int, arg1: String, arg2: InstrumentInfo)` | `DataBinWriterNew` | Retrieves `CryptedInstance` property from `TickDataBinWriterNew` |
| `static` | `setDecimals` | `(arg0: InstrumentInfo, arg1: DataManipulatorNew)` | `void` | Sets `Decimals` configuration/state on `TickDataBinWriterNew` |

---

### `TickDataReader`
- **Full Qualified Name:** `com.strategyquant.datalib.data.io.newDataFormat.TickDataReader`
- **Primary Job / Responsibility:** Market data abstraction and time-series container (`TickDataReader`).

#### Fields
| Scope | Field Name | Type |
| :--- | :--- | :--- |
| `static` | `ASIS` | `int` |
| `static` | `BLOCK_LENGTH` | `int` |
| `static` | `BYTE` | `int` |
| `static` | `INT` | `int` |
| `static` | `LONG` | `int` |
| `static` | `MINUS` | `int` |
| `static` | `OLD_VOLUME_CONSTANT` | `double` |
| `static` | `PLUS` | `int` |
| `static` | `SHORT` | `int` |
| `static` | `VOLUME_CONSTANT` | `double` |

#### Methods & Functions
| Modifiers | Method Name | Parameter Signatures | Return Type | Functional Description / Job |
| :--- | :--- | :--- | :--- | :--- |
| `instance` | `readData` | `(arg0: IRandomAccessReader, arg1: VersatileData)` | `void` | Performs read data operation |
| `instance` | `seek` | `(arg0: IRandomAccessReader, arg1: long)` | `void` | Performs seek operation |
| `instance` | `setDataStartPosition` | `(arg0: long)` | `void` | Sets `DataStartPosition` configuration/state on `TickDataReader` |
| `instance` | `reset` | `()` | `void` | Performs reset operation |
| `instance` | `getDecimals` | `()` | `int` | Retrieves `Decimals` property from `TickDataReader` |
| `instance` | `setVolumeConstant` | `(arg0: double)` | `void` | Sets `VolumeConstant` configuration/state on `TickDataReader` |
| `instance` | `overrideDecimals` | `(arg0: int)` | `void` | Performs override decimals operation |
| `instance` | `equals` | `(arg0: Object)` | `boolean` | Performs equals operation |
| `instance` | `toString` | `()` | `String` | Converts/serializes representation via `toString` |
| `instance` | `hashCode` | `()` | `int` | Evaluates boolean predicate `hashCode` on `TickDataReader` |
| `instance` | `getClass` | `()` | `Class` | Retrieves `Class` property from `TickDataReader` |
| `instance` | `notify` | `()` | `void` | Performs notify operation |
| `instance` | `notifyAll` | `()` | `void` | Performs notify all operation |
| `instance` | `wait` | `(arg0: long)` | `void` | Performs wait operation |
| `instance` | `wait` | `(arg0: long, arg1: int)` | `void` | Performs wait operation |
| `instance` | `wait` | `()` | `void` | Performs wait operation |
| `static` | `getDataType` | `(arg0: long)` | `int` | Retrieves `DataType` property from `TickDataReader` |
| `static` | `getLogicType` | `(arg0: long)` | `int` | Retrieves `LogicType` property from `TickDataReader` |
| `static` | `printBits` | `(arg0: byte)` | `void` | Performs print bits operation |

---

### `TickDataWriter`
- **Full Qualified Name:** `com.strategyquant.datalib.data.io.newDataFormat.TickDataWriter`
- **Primary Job / Responsibility:** Market data abstraction and time-series container (`TickDataWriter`).

#### Fields
| Scope | Field Name | Type |
| :--- | :--- | :--- |
| `static` | `ASIS` | `int` |
| `static` | `BLOCK_LENGTH` | `int` |
| `static` | `BLOCK_START_MAGIC` | `byte[]` |
| `static` | `BYTE` | `int` |
| `static` | `INT` | `int` |
| `static` | `LONG` | `int` |
| `static` | `MINUS` | `int` |
| `static` | `OLD_VOLUME_CONSTANT` | `double` |
| `static` | `PLUS` | `int` |
| `static` | `SHORT` | `int` |
| `static` | `VOLUME_CONSTANT` | `double` |

#### Methods & Functions
| Modifiers | Method Name | Parameter Signatures | Return Type | Functional Description / Job |
| :--- | :--- | :--- | :--- | :--- |
| `instance` | `putData` | `(arg0: RandomAccessReaderOffheap, arg1: VersatileData)` | `void` | Performs put data operation |
| `instance` | `putData` | `(arg0: ByteBuffer, arg1: VersatileData)` | `void` | Performs put data operation |
| `instance` | `writeData` | `(arg0: DataOutputStream, arg1: VersatileData)` | `void` | Performs write data operation |
| `instance` | `getSavedCount` | `()` | `long` | Retrieves `SavedCount` property from `TickDataWriter` |
| `instance` | `reset` | `()` | `void` | Performs reset operation |
| `instance` | `getDecimals` | `()` | `int` | Retrieves `Decimals` property from `TickDataWriter` |
| `instance` | `setVolumeConstant` | `(arg0: double)` | `void` | Sets `VolumeConstant` configuration/state on `TickDataWriter` |
| `instance` | `overrideDecimals` | `(arg0: int)` | `void` | Performs override decimals operation |
| `instance` | `equals` | `(arg0: Object)` | `boolean` | Performs equals operation |
| `instance` | `toString` | `()` | `String` | Converts/serializes representation via `toString` |
| `instance` | `hashCode` | `()` | `int` | Evaluates boolean predicate `hashCode` on `TickDataWriter` |
| `instance` | `getClass` | `()` | `Class` | Retrieves `Class` property from `TickDataWriter` |
| `instance` | `notify` | `()` | `void` | Performs notify operation |
| `instance` | `notifyAll` | `()` | `void` | Performs notify all operation |
| `instance` | `wait` | `(arg0: long)` | `void` | Performs wait operation |
| `instance` | `wait` | `(arg0: long, arg1: int)` | `void` | Performs wait operation |
| `instance` | `wait` | `()` | `void` | Performs wait operation |
| `static` | `getDataType` | `(arg0: long)` | `int` | Retrieves `DataType` property from `TickDataWriter` |
| `static` | `getLogicType` | `(arg0: long)` | `int` | Retrieves `LogicType` property from `TickDataWriter` |
| `static` | `printBits` | `(arg0: byte)` | `void` | Performs print bits operation |

---

### `TickFuturesRoundtrip`
- **Full Qualified Name:** `com.strategyquant.datalib.data.io.newDataFormat.TickFuturesRoundtrip`
- **Primary Job / Responsibility:** Market data abstraction and time-series container (`TickFuturesRoundtrip`).

#### Methods & Functions
| Modifiers | Method Name | Parameter Signatures | Return Type | Functional Description / Job |
| :--- | :--- | :--- | :--- | :--- |
| `instance` | `equals` | `(arg0: Object)` | `boolean` | Performs equals operation |
| `instance` | `toString` | `()` | `String` | Converts/serializes representation via `toString` |
| `instance` | `hashCode` | `()` | `int` | Evaluates boolean predicate `hashCode` on `TickFuturesRoundtrip` |
| `instance` | `getClass` | `()` | `Class` | Retrieves `Class` property from `TickFuturesRoundtrip` |
| `instance` | `notify` | `()` | `void` | Performs notify operation |
| `instance` | `notifyAll` | `()` | `void` | Performs notify all operation |
| `instance` | `wait` | `(arg0: long)` | `void` | Performs wait operation |
| `instance` | `wait` | `(arg0: long, arg1: int)` | `void` | Performs wait operation |
| `instance` | `wait` | `()` | `void` | Performs wait operation |
| `static` | `main` | `(arg0: String[])` | `void` | Performs main operation |

---

## Subsystem: `dataseries`

### `ComputedDataSeries`
- **Full Qualified Name:** `com.strategyquant.datalib.dataseries.ComputedDataSeries`
- **Primary Job / Responsibility:** Market data abstraction and time-series container (`ComputedDataSeries`).

#### Fields
| Scope | Field Name | Type |
| :--- | :--- | :--- |
| `static` | `Log` | `Logger` |
| `instance` | `Close` | `DataSeries` |
| `instance` | `High` | `DataSeries` |
| `instance` | `Low` | `DataSeries` |
| `instance` | `Open` | `DataSeries` |
| `instance` | `Volume` | `DataSeries` |

#### Methods & Functions
| Modifiers | Method Name | Parameter Signatures | Return Type | Functional Description / Job |
| :--- | :--- | :--- | :--- | :--- |
| `instance` | `size` | `()` | `int` | Performs size operation |
| `instance` | `get` | `(arg0: int)` | `double` | Retrieves `` property from `ComputedDataSeries` |
| `instance` | `destroy` | `()` | `void` | Performs destroy operation |
| `instance` | `computeValue` | `(arg0: int)` | `double` | Executes calculation for `computeValue` |
| `instance` | `add` | `(arg0: double)` | `void` | Appends/registers element via `add` |
| `instance` | `set` | `(arg0: int, arg1: double)` | `void` | Sets `` configuration/state on `ComputedDataSeries` |
| `instance` | `set` | `(arg0: int, arg1: double, arg2: boolean)` | `void` | Sets `` configuration/state on `ComputedDataSeries` |
| `instance` | `set` | `(arg0: double)` | `void` | Sets `` configuration/state on `ComputedDataSeries` |
| `instance` | `getRounded` | `(arg0: int, arg1: int)` | `double` | Retrieves `Rounded` property from `ComputedDataSeries` |
| `instance` | `getRounded` | `(arg0: int)` | `double` | Retrieves `Rounded` property from `ComputedDataSeries` |
| `instance` | `addValues` | `(arg0: int)` | `void` | Appends/registers element via `addValues` |
| `instance` | `chartHashCode` | `()` | `int` | Performs chart hash code operation |
| `instance` | `getName` | `()` | `String` | Retrieves `Name` property from `ComputedDataSeries` |
| `instance` | `setName` | `(arg0: String)` | `void` | Sets `Name` configuration/state on `ComputedDataSeries` |
| `instance` | `setName` | `(arg0: String, arg1: ChartDef)` | `void` | Sets `Name` configuration/state on `ComputedDataSeries` |
| `instance` | `setColor` | `(arg0: String)` | `void` | Sets `Color` configuration/state on `ComputedDataSeries` |
| `instance` | `getInstrumentInfo` | `()` | `InstrumentInfo` | Retrieves `InstrumentInfo` property from `ComputedDataSeries` |
| `instance` | `Symbol` | `()` | `String` | Performs symbol operation |
| `instance` | `getIndyStartingBar` | `()` | `int` | Retrieves `IndyStartingBar` property from `ComputedDataSeries` |
| `instance` | `setIndyStartingBar` | `(arg0: int)` | `void` | Sets `IndyStartingBar` configuration/state on `ComputedDataSeries` |
| `instance` | `getShift` | `()` | `int` | Retrieves `Shift` property from `ComputedDataSeries` |
| `instance` | `addChangeListener` | `(arg0: int, arg1: IDataSeriesChangeListener)` | `void` | Appends/registers element via `addChangeListener` |
| `instance` | `setDataComputer` | `(arg0: IDataSeriesComputer)` | `void` | Sets `DataComputer` configuration/state on `ComputedDataSeries` |
| `instance` | `specialSize` | `()` | `int` | Performs special size operation |
| `instance` | `addDoubleValues` | `(arg0: int, arg1: double)` | `void` | Appends/registers element via `addDoubleValues` |
| `instance` | `addLongValues` | `(arg0: int, arg1: long)` | `void` | Appends/registers element via `addLongValues` |
| `instance` | `updateComputedUntil` | `(arg0: int)` | `void` | Performs update computed until operation |
| `instance` | `setComputedUntil` | `(arg0: int)` | `void` | Sets `ComputedUntil` configuration/state on `ComputedDataSeries` |
| `instance` | `setShift` | `(arg0: int)` | `void` | Sets `Shift` configuration/state on `ComputedDataSeries` |
| `instance` | `setLineName` | `(arg0: String)` | `void` | Sets `LineName` configuration/state on `ComputedDataSeries` |
| `instance` | `setShowInChart` | `(arg0: boolean)` | `void` | Sets `ShowInChart` configuration/state on `ComputedDataSeries` |
| `instance` | `setShowZeroValues` | `(arg0: boolean)` | `void` | Sets `ShowZeroValues` configuration/state on `ComputedDataSeries` |
| `instance` | `setChartType` | `(arg0: String)` | `void` | Sets `ChartType` configuration/state on `ComputedDataSeries` |
| `instance` | `callDataChangeListeners` | `()` | `void` | Performs call data change listeners operation |
| `instance` | `getColor` | `()` | `String` | Retrieves `Color` property from `ComputedDataSeries` |
| `instance` | `isShowInChart` | `()` | `boolean` | Evaluates boolean predicate `isShowInChart` on `ComputedDataSeries` |
| `instance` | `isShowZeroValues` | `()` | `boolean` | Evaluates boolean predicate `isShowZeroValues` on `ComputedDataSeries` |
| `instance` | `getChartType` | `()` | `String` | Retrieves `ChartType` property from `ComputedDataSeries` |
| `instance` | `getLineName` | `()` | `String` | Retrieves `LineName` property from `ComputedDataSeries` |
| `instance` | `getComputedUntilIndex` | `()` | `int` | Retrieves `ComputedUntilIndex` property from `ComputedDataSeries` |
| `instance` | `_getDouble` | `(arg0: int)` | `double` | Performs get double operation |
| `instance` | `_writeDoubleToOffheapRealIndex` | `(arg0: int, arg1: double)` | `void` | Performs write double to offheap real index operation |
| `instance` | `equals` | `(arg0: Object)` | `boolean` | Performs equals operation |
| `instance` | `toString` | `()` | `String` | Converts/serializes representation via `toString` |
| `instance` | `hashCode` | `()` | `int` | Evaluates boolean predicate `hashCode` on `ComputedDataSeries` |
| `instance` | `getClass` | `()` | `Class` | Retrieves `Class` property from `ComputedDataSeries` |
| `instance` | `notify` | `()` | `void` | Performs notify operation |
| `instance` | `notifyAll` | `()` | `void` | Performs notify all operation |
| `instance` | `wait` | `(arg0: long)` | `void` | Performs wait operation |
| `instance` | `wait` | `(arg0: long, arg1: int)` | `void` | Performs wait operation |
| `instance` | `wait` | `()` | `void` | Performs wait operation |

---

### `DataSeriesBase`
- **Full Qualified Name:** `com.strategyquant.datalib.dataseries.DataSeriesBase`
- **Primary Job / Responsibility:** Market data abstraction and time-series container (`DataSeriesBase`).

#### Fields
| Scope | Field Name | Type |
| :--- | :--- | :--- |
| `static` | `Log` | `Logger` |

#### Methods & Functions
| Modifiers | Method Name | Parameter Signatures | Return Type | Functional Description / Job |
| :--- | :--- | :--- | :--- | :--- |
| `instance` | `getName` | `()` | `String` | Retrieves `Name` property from `DataSeriesBase` |
| `instance` | `size` | `()` | `int` | Performs size operation |
| `instance` | `setName` | `(arg0: String)` | `void` | Sets `Name` configuration/state on `DataSeriesBase` |
| `instance` | `setName` | `(arg0: String, arg1: ChartDef)` | `void` | Sets `Name` configuration/state on `DataSeriesBase` |
| `instance` | `destroy` | `()` | `void` | Performs destroy operation |
| `instance` | `setColor` | `(arg0: String)` | `void` | Sets `Color` configuration/state on `DataSeriesBase` |
| `instance` | `getInstrumentInfo` | `()` | `InstrumentInfo` | Retrieves `InstrumentInfo` property from `DataSeriesBase` |
| `instance` | `Symbol` | `()` | `String` | Performs symbol operation |
| `instance` | `getIndyStartingBar` | `()` | `int` | Retrieves `IndyStartingBar` property from `DataSeriesBase` |
| `instance` | `setIndyStartingBar` | `(arg0: int)` | `void` | Sets `IndyStartingBar` configuration/state on `DataSeriesBase` |
| `instance` | `getShift` | `()` | `int` | Retrieves `Shift` property from `DataSeriesBase` |
| `instance` | `addChangeListener` | `(arg0: int, arg1: IDataSeriesChangeListener)` | `void` | Appends/registers element via `addChangeListener` |
| `instance` | `setDataComputer` | `(arg0: IDataSeriesComputer)` | `void` | Sets `DataComputer` configuration/state on `DataSeriesBase` |
| `instance` | `specialSize` | `()` | `int` | Performs special size operation |
| `instance` | `addDoubleValues` | `(arg0: int, arg1: double)` | `void` | Appends/registers element via `addDoubleValues` |
| `instance` | `addLongValues` | `(arg0: int, arg1: long)` | `void` | Appends/registers element via `addLongValues` |
| `instance` | `updateComputedUntil` | `(arg0: int)` | `void` | Performs update computed until operation |
| `instance` | `setComputedUntil` | `(arg0: int)` | `void` | Sets `ComputedUntil` configuration/state on `DataSeriesBase` |
| `instance` | `setShift` | `(arg0: int)` | `void` | Sets `Shift` configuration/state on `DataSeriesBase` |
| `instance` | `setLineName` | `(arg0: String)` | `void` | Sets `LineName` configuration/state on `DataSeriesBase` |
| `instance` | `setShowInChart` | `(arg0: boolean)` | `void` | Sets `ShowInChart` configuration/state on `DataSeriesBase` |
| `instance` | `setShowZeroValues` | `(arg0: boolean)` | `void` | Sets `ShowZeroValues` configuration/state on `DataSeriesBase` |
| `instance` | `setChartType` | `(arg0: String)` | `void` | Sets `ChartType` configuration/state on `DataSeriesBase` |
| `instance` | `callDataChangeListeners` | `()` | `void` | Performs call data change listeners operation |
| `instance` | `getColor` | `()` | `String` | Retrieves `Color` property from `DataSeriesBase` |
| `instance` | `isShowInChart` | `()` | `boolean` | Evaluates boolean predicate `isShowInChart` on `DataSeriesBase` |
| `instance` | `isShowZeroValues` | `()` | `boolean` | Evaluates boolean predicate `isShowZeroValues` on `DataSeriesBase` |
| `instance` | `getChartType` | `()` | `String` | Retrieves `ChartType` property from `DataSeriesBase` |
| `instance` | `getLineName` | `()` | `String` | Retrieves `LineName` property from `DataSeriesBase` |
| `instance` | `getComputedUntilIndex` | `()` | `int` | Retrieves `ComputedUntilIndex` property from `DataSeriesBase` |
| `instance` | `_getDouble` | `(arg0: int)` | `double` | Performs get double operation |
| `instance` | `_writeDoubleToOffheapRealIndex` | `(arg0: int, arg1: double)` | `void` | Performs write double to offheap real index operation |
| `instance` | `equals` | `(arg0: Object)` | `boolean` | Performs equals operation |
| `instance` | `toString` | `()` | `String` | Converts/serializes representation via `toString` |
| `instance` | `hashCode` | `()` | `int` | Evaluates boolean predicate `hashCode` on `DataSeriesBase` |
| `instance` | `getClass` | `()` | `Class` | Retrieves `Class` property from `DataSeriesBase` |
| `instance` | `notify` | `()` | `void` | Performs notify operation |
| `instance` | `notifyAll` | `()` | `void` | Performs notify all operation |
| `instance` | `wait` | `(arg0: long)` | `void` | Performs wait operation |
| `instance` | `wait` | `(arg0: long, arg1: int)` | `void` | Performs wait operation |
| `instance` | `wait` | `()` | `void` | Performs wait operation |

---

### `DataSeriesTypes`
- **Full Qualified Name:** `com.strategyquant.datalib.dataseries.DataSeriesTypes`
- **Primary Job / Responsibility:** Market data abstraction and time-series container (`DataSeriesTypes`).

#### Fields
| Scope | Field Name | Type |
| :--- | :--- | :--- |
| `static` | `Close` | `int` |
| `static` | `High` | `int` |
| `static` | `Log` | `Logger` |
| `static` | `Low` | `int` |
| `static` | `Median` | `int` |
| `static` | `Open` | `int` |
| `static` | `Typical` | `int` |
| `static` | `Volume` | `int` |
| `static` | `Weighted` | `int` |

#### Methods & Functions
| Modifiers | Method Name | Parameter Signatures | Return Type | Functional Description / Job |
| :--- | :--- | :--- | :--- | :--- |
| `instance` | `getName` | `()` | `String` | Retrieves `Name` property from `DataSeriesTypes` |
| `instance` | `size` | `()` | `int` | Performs size operation |
| `instance` | `setName` | `(arg0: String)` | `void` | Sets `Name` configuration/state on `DataSeriesTypes` |
| `instance` | `setName` | `(arg0: String, arg1: ChartDef)` | `void` | Sets `Name` configuration/state on `DataSeriesTypes` |
| `instance` | `destroy` | `()` | `void` | Performs destroy operation |
| `instance` | `setColor` | `(arg0: String)` | `void` | Sets `Color` configuration/state on `DataSeriesTypes` |
| `instance` | `getInstrumentInfo` | `()` | `InstrumentInfo` | Retrieves `InstrumentInfo` property from `DataSeriesTypes` |
| `instance` | `Symbol` | `()` | `String` | Performs symbol operation |
| `instance` | `getIndyStartingBar` | `()` | `int` | Retrieves `IndyStartingBar` property from `DataSeriesTypes` |
| `instance` | `setIndyStartingBar` | `(arg0: int)` | `void` | Sets `IndyStartingBar` configuration/state on `DataSeriesTypes` |
| `instance` | `getShift` | `()` | `int` | Retrieves `Shift` property from `DataSeriesTypes` |
| `instance` | `addChangeListener` | `(arg0: int, arg1: IDataSeriesChangeListener)` | `void` | Appends/registers element via `addChangeListener` |
| `instance` | `setDataComputer` | `(arg0: IDataSeriesComputer)` | `void` | Sets `DataComputer` configuration/state on `DataSeriesTypes` |
| `instance` | `specialSize` | `()` | `int` | Performs special size operation |
| `instance` | `addDoubleValues` | `(arg0: int, arg1: double)` | `void` | Appends/registers element via `addDoubleValues` |
| `instance` | `addLongValues` | `(arg0: int, arg1: long)` | `void` | Appends/registers element via `addLongValues` |
| `instance` | `updateComputedUntil` | `(arg0: int)` | `void` | Performs update computed until operation |
| `instance` | `setComputedUntil` | `(arg0: int)` | `void` | Sets `ComputedUntil` configuration/state on `DataSeriesTypes` |
| `instance` | `setShift` | `(arg0: int)` | `void` | Sets `Shift` configuration/state on `DataSeriesTypes` |
| `instance` | `setLineName` | `(arg0: String)` | `void` | Sets `LineName` configuration/state on `DataSeriesTypes` |
| `instance` | `setShowInChart` | `(arg0: boolean)` | `void` | Sets `ShowInChart` configuration/state on `DataSeriesTypes` |
| `instance` | `setShowZeroValues` | `(arg0: boolean)` | `void` | Sets `ShowZeroValues` configuration/state on `DataSeriesTypes` |
| `instance` | `setChartType` | `(arg0: String)` | `void` | Sets `ChartType` configuration/state on `DataSeriesTypes` |
| `instance` | `callDataChangeListeners` | `()` | `void` | Performs call data change listeners operation |
| `instance` | `getColor` | `()` | `String` | Retrieves `Color` property from `DataSeriesTypes` |
| `instance` | `isShowInChart` | `()` | `boolean` | Evaluates boolean predicate `isShowInChart` on `DataSeriesTypes` |
| `instance` | `isShowZeroValues` | `()` | `boolean` | Evaluates boolean predicate `isShowZeroValues` on `DataSeriesTypes` |
| `instance` | `getChartType` | `()` | `String` | Retrieves `ChartType` property from `DataSeriesTypes` |
| `instance` | `getLineName` | `()` | `String` | Retrieves `LineName` property from `DataSeriesTypes` |
| `instance` | `getComputedUntilIndex` | `()` | `int` | Retrieves `ComputedUntilIndex` property from `DataSeriesTypes` |
| `instance` | `_getDouble` | `(arg0: int)` | `double` | Performs get double operation |
| `instance` | `_writeDoubleToOffheapRealIndex` | `(arg0: int, arg1: double)` | `void` | Performs write double to offheap real index operation |
| `instance` | `equals` | `(arg0: Object)` | `boolean` | Performs equals operation |
| `instance` | `toString` | `()` | `String` | Converts/serializes representation via `toString` |
| `instance` | `hashCode` | `()` | `int` | Evaluates boolean predicate `hashCode` on `DataSeriesTypes` |
| `instance` | `getClass` | `()` | `Class` | Retrieves `Class` property from `DataSeriesTypes` |
| `instance` | `notify` | `()` | `void` | Performs notify operation |
| `instance` | `notifyAll` | `()` | `void` | Performs notify all operation |
| `instance` | `wait` | `(arg0: long)` | `void` | Performs wait operation |
| `instance` | `wait` | `(arg0: long, arg1: int)` | `void` | Performs wait operation |
| `instance` | `wait` | `()` | `void` | Performs wait operation |
| `static` | `toString` | `(arg0: int)` | `String` | Converts/serializes representation via `toString` |

---

### `DoubleListCache`
- **Full Qualified Name:** `com.strategyquant.datalib.dataseries.DoubleListCache`
- **Primary Job / Responsibility:** Market data abstraction and time-series container (`DoubleListCache`).

#### Fields
| Scope | Field Name | Type |
| :--- | :--- | :--- |
| `static` | `Log` | `Logger` |

#### Methods & Functions
| Modifiers | Method Name | Parameter Signatures | Return Type | Functional Description / Job |
| :--- | :--- | :--- | :--- | :--- |
| `instance` | `equals` | `(arg0: Object)` | `boolean` | Performs equals operation |
| `instance` | `toString` | `()` | `String` | Converts/serializes representation via `toString` |
| `instance` | `hashCode` | `()` | `int` | Evaluates boolean predicate `hashCode` on `DoubleListCache` |
| `instance` | `getClass` | `()` | `Class` | Retrieves `Class` property from `DoubleListCache` |
| `instance` | `notify` | `()` | `void` | Performs notify operation |
| `instance` | `notifyAll` | `()` | `void` | Performs notify all operation |
| `instance` | `wait` | `(arg0: long)` | `void` | Performs wait operation |
| `instance` | `wait` | `(arg0: long, arg1: int)` | `void` | Performs wait operation |
| `instance` | `wait` | `()` | `void` | Performs wait operation |
| `static` | `get` | `(arg0: int)` | `IDoubleValuesList` | Retrieves `` property from `DoubleListCache` |
| `static` | `clear` | `(arg0: IDoubleValuesList)` | `void` | Removes/resets elements via `clear` |
| `static` | `resetStats` | `()` | `void` | Performs reset stats operation |
| `static` | `getWaitingForAllocationObjects` | `()` | `int` | Retrieves `WaitingForAllocationObjects` property from `DoubleListCache` |

---

### `HeapDoubleValuesList`
- **Full Qualified Name:** `com.strategyquant.datalib.dataseries.HeapDoubleValuesList`
- **Primary Job / Responsibility:** Market data abstraction and time-series container (`HeapDoubleValuesList`).

#### Methods & Functions
| Modifiers | Method Name | Parameter Signatures | Return Type | Functional Description / Job |
| :--- | :--- | :--- | :--- | :--- |
| `instance` | `size` | `()` | `int` | Performs size operation |
| `instance` | `getDouble` | `(arg0: int)` | `double` | Retrieves `Double` property from `HeapDoubleValuesList` |
| `instance` | `clear` | `()` | `void` | Removes/resets elements via `clear` |
| `instance` | `setDouble` | `(arg0: int, arg1: double)` | `void` | Sets `Double` configuration/state on `HeapDoubleValuesList` |
| `instance` | `release` | `()` | `void` | Performs release operation |
| `instance` | `addDoubleValues` | `(arg0: int, arg1: double)` | `void` | Appends/registers element via `addDoubleValues` |
| `instance` | `addDouble` | `(arg0: double)` | `void` | Appends/registers element via `addDouble` |
| `instance` | `getCapacity` | `()` | `long` | Retrieves `Capacity` property from `HeapDoubleValuesList` |
| `instance` | `equals` | `(arg0: Object)` | `boolean` | Performs equals operation |
| `instance` | `toString` | `()` | `String` | Converts/serializes representation via `toString` |
| `instance` | `hashCode` | `()` | `int` | Evaluates boolean predicate `hashCode` on `HeapDoubleValuesList` |
| `instance` | `getClass` | `()` | `Class` | Retrieves `Class` property from `HeapDoubleValuesList` |
| `instance` | `notify` | `()` | `void` | Performs notify operation |
| `instance` | `notifyAll` | `()` | `void` | Performs notify all operation |
| `instance` | `wait` | `(arg0: long)` | `void` | Performs wait operation |
| `instance` | `wait` | `(arg0: long, arg1: int)` | `void` | Performs wait operation |
| `instance` | `wait` | `()` | `void` | Performs wait operation |

---

### `HeapLongValuesList`
- **Full Qualified Name:** `com.strategyquant.datalib.dataseries.HeapLongValuesList`
- **Primary Job / Responsibility:** Market data abstraction and time-series container (`HeapLongValuesList`).

#### Methods & Functions
| Modifiers | Method Name | Parameter Signatures | Return Type | Functional Description / Job |
| :--- | :--- | :--- | :--- | :--- |
| `instance` | `size` | `()` | `int` | Performs size operation |
| `instance` | `getLong` | `(arg0: int)` | `long` | Retrieves `Long` property from `HeapLongValuesList` |
| `instance` | `clear` | `()` | `void` | Removes/resets elements via `clear` |
| `instance` | `setLong` | `(arg0: int, arg1: long)` | `void` | Sets `Long` configuration/state on `HeapLongValuesList` |
| `instance` | `addLong` | `(arg0: long)` | `void` | Appends/registers element via `addLong` |
| `instance` | `equals` | `(arg0: Object)` | `boolean` | Performs equals operation |
| `instance` | `toString` | `()` | `String` | Converts/serializes representation via `toString` |
| `instance` | `hashCode` | `()` | `int` | Evaluates boolean predicate `hashCode` on `HeapLongValuesList` |
| `instance` | `getClass` | `()` | `Class` | Retrieves `Class` property from `HeapLongValuesList` |
| `instance` | `notify` | `()` | `void` | Performs notify operation |
| `instance` | `notifyAll` | `()` | `void` | Performs notify all operation |
| `instance` | `wait` | `(arg0: long)` | `void` | Performs wait operation |
| `instance` | `wait` | `(arg0: long, arg1: int)` | `void` | Performs wait operation |
| `instance` | `wait` | `()` | `void` | Performs wait operation |

---

### `IDataSeriesChangeListener`
- **Full Qualified Name:** `com.strategyquant.datalib.dataseries.IDataSeriesChangeListener`
- **Primary Job / Responsibility:** Market data abstraction and time-series container (`IDataSeriesChangeListener`).

#### Methods & Functions
| Modifiers | Method Name | Parameter Signatures | Return Type | Functional Description / Job |
| :--- | :--- | :--- | :--- | :--- |
| `instance` | `changed` | `(arg0: int, arg1: int)` | `void` | Performs changed operation |

---

### `IDataSeriesComputer`
- **Full Qualified Name:** `com.strategyquant.datalib.dataseries.IDataSeriesComputer`
- **Primary Job / Responsibility:** Market data abstraction and time-series container (`IDataSeriesComputer`).

#### Methods & Functions
| Modifiers | Method Name | Parameter Signatures | Return Type | Functional Description / Job |
| :--- | :--- | :--- | :--- | :--- |
| `instance` | `compute` | `(arg0: int, arg1: int)` | `void` | Executes calculation for `compute` |

---

### `IDoubleValuesList`
- **Full Qualified Name:** `com.strategyquant.datalib.dataseries.IDoubleValuesList`
- **Primary Job / Responsibility:** Market data abstraction and time-series container (`IDoubleValuesList`).

#### Methods & Functions
| Modifiers | Method Name | Parameter Signatures | Return Type | Functional Description / Job |
| :--- | :--- | :--- | :--- | :--- |
| `instance` | `size` | `()` | `int` | Performs size operation |
| `instance` | `getDouble` | `(arg0: int)` | `double` | Retrieves `Double` property from `IDoubleValuesList` |
| `instance` | `clear` | `()` | `void` | Removes/resets elements via `clear` |
| `instance` | `setDouble` | `(arg0: int, arg1: double)` | `void` | Sets `Double` configuration/state on `IDoubleValuesList` |
| `instance` | `release` | `()` | `void` | Performs release operation |
| `instance` | `addDoubleValues` | `(arg0: int, arg1: double)` | `void` | Appends/registers element via `addDoubleValues` |
| `instance` | `addDouble` | `(arg0: double)` | `void` | Appends/registers element via `addDouble` |
| `instance` | `getCapacity` | `()` | `long` | Retrieves `Capacity` property from `IDoubleValuesList` |

---

### `ILongValuesList`
- **Full Qualified Name:** `com.strategyquant.datalib.dataseries.ILongValuesList`
- **Primary Job / Responsibility:** Market data abstraction and time-series container (`ILongValuesList`).

#### Methods & Functions
| Modifiers | Method Name | Parameter Signatures | Return Type | Functional Description / Job |
| :--- | :--- | :--- | :--- | :--- |
| `instance` | `size` | `()` | `int` | Performs size operation |
| `instance` | `getLong` | `(arg0: int)` | `long` | Retrieves `Long` property from `ILongValuesList` |
| `instance` | `clear` | `()` | `void` | Removes/resets elements via `clear` |
| `instance` | `setLong` | `(arg0: int, arg1: long)` | `void` | Sets `Long` configuration/state on `ILongValuesList` |
| `instance` | `addLong` | `(arg0: long)` | `void` | Appends/registers element via `addLong` |

---

### `LongListCache`
- **Full Qualified Name:** `com.strategyquant.datalib.dataseries.LongListCache`
- **Primary Job / Responsibility:** Market data abstraction and time-series container (`LongListCache`).

#### Fields
| Scope | Field Name | Type |
| :--- | :--- | :--- |
| `static` | `Log` | `Logger` |

#### Methods & Functions
| Modifiers | Method Name | Parameter Signatures | Return Type | Functional Description / Job |
| :--- | :--- | :--- | :--- | :--- |
| `instance` | `equals` | `(arg0: Object)` | `boolean` | Performs equals operation |
| `instance` | `toString` | `()` | `String` | Converts/serializes representation via `toString` |
| `instance` | `hashCode` | `()` | `int` | Evaluates boolean predicate `hashCode` on `LongListCache` |
| `instance` | `getClass` | `()` | `Class` | Retrieves `Class` property from `LongListCache` |
| `instance` | `notify` | `()` | `void` | Performs notify operation |
| `instance` | `notifyAll` | `()` | `void` | Performs notify all operation |
| `instance` | `wait` | `(arg0: long)` | `void` | Performs wait operation |
| `instance` | `wait` | `(arg0: long, arg1: int)` | `void` | Performs wait operation |
| `instance` | `wait` | `()` | `void` | Performs wait operation |
| `static` | `get` | `(arg0: int)` | `ILongValuesList` | Retrieves `` property from `LongListCache` |
| `static` | `clear` | `(arg0: ILongValuesList)` | `void` | Removes/resets elements via `clear` |
| `static` | `resetStats` | `()` | `void` | Performs reset stats operation |

---

### `MedianDataSeries`
- **Full Qualified Name:** `com.strategyquant.datalib.dataseries.MedianDataSeries`
- **Primary Job / Responsibility:** Market data abstraction and time-series container (`MedianDataSeries`).

#### Fields
| Scope | Field Name | Type |
| :--- | :--- | :--- |
| `static` | `Log` | `Logger` |
| `instance` | `Close` | `DataSeries` |
| `instance` | `High` | `DataSeries` |
| `instance` | `Low` | `DataSeries` |
| `instance` | `Open` | `DataSeries` |
| `instance` | `Volume` | `DataSeries` |

#### Methods & Functions
| Modifiers | Method Name | Parameter Signatures | Return Type | Functional Description / Job |
| :--- | :--- | :--- | :--- | :--- |
| `instance` | `computeValue` | `(arg0: int)` | `double` | Executes calculation for `computeValue` |
| `instance` | `size` | `()` | `int` | Performs size operation |
| `instance` | `get` | `(arg0: int)` | `double` | Retrieves `` property from `MedianDataSeries` |
| `instance` | `destroy` | `()` | `void` | Performs destroy operation |
| `instance` | `add` | `(arg0: double)` | `void` | Appends/registers element via `add` |
| `instance` | `set` | `(arg0: int, arg1: double)` | `void` | Sets `` configuration/state on `MedianDataSeries` |
| `instance` | `set` | `(arg0: int, arg1: double, arg2: boolean)` | `void` | Sets `` configuration/state on `MedianDataSeries` |
| `instance` | `set` | `(arg0: double)` | `void` | Sets `` configuration/state on `MedianDataSeries` |
| `instance` | `getRounded` | `(arg0: int, arg1: int)` | `double` | Retrieves `Rounded` property from `MedianDataSeries` |
| `instance` | `getRounded` | `(arg0: int)` | `double` | Retrieves `Rounded` property from `MedianDataSeries` |
| `instance` | `addValues` | `(arg0: int)` | `void` | Appends/registers element via `addValues` |
| `instance` | `chartHashCode` | `()` | `int` | Performs chart hash code operation |
| `instance` | `getName` | `()` | `String` | Retrieves `Name` property from `MedianDataSeries` |
| `instance` | `setName` | `(arg0: String)` | `void` | Sets `Name` configuration/state on `MedianDataSeries` |
| `instance` | `setName` | `(arg0: String, arg1: ChartDef)` | `void` | Sets `Name` configuration/state on `MedianDataSeries` |
| `instance` | `setColor` | `(arg0: String)` | `void` | Sets `Color` configuration/state on `MedianDataSeries` |
| `instance` | `getInstrumentInfo` | `()` | `InstrumentInfo` | Retrieves `InstrumentInfo` property from `MedianDataSeries` |
| `instance` | `Symbol` | `()` | `String` | Performs symbol operation |
| `instance` | `getIndyStartingBar` | `()` | `int` | Retrieves `IndyStartingBar` property from `MedianDataSeries` |
| `instance` | `setIndyStartingBar` | `(arg0: int)` | `void` | Sets `IndyStartingBar` configuration/state on `MedianDataSeries` |
| `instance` | `getShift` | `()` | `int` | Retrieves `Shift` property from `MedianDataSeries` |
| `instance` | `addChangeListener` | `(arg0: int, arg1: IDataSeriesChangeListener)` | `void` | Appends/registers element via `addChangeListener` |
| `instance` | `setDataComputer` | `(arg0: IDataSeriesComputer)` | `void` | Sets `DataComputer` configuration/state on `MedianDataSeries` |
| `instance` | `specialSize` | `()` | `int` | Performs special size operation |
| `instance` | `addDoubleValues` | `(arg0: int, arg1: double)` | `void` | Appends/registers element via `addDoubleValues` |
| `instance` | `addLongValues` | `(arg0: int, arg1: long)` | `void` | Appends/registers element via `addLongValues` |
| `instance` | `updateComputedUntil` | `(arg0: int)` | `void` | Performs update computed until operation |
| `instance` | `setComputedUntil` | `(arg0: int)` | `void` | Sets `ComputedUntil` configuration/state on `MedianDataSeries` |
| `instance` | `setShift` | `(arg0: int)` | `void` | Sets `Shift` configuration/state on `MedianDataSeries` |
| `instance` | `setLineName` | `(arg0: String)` | `void` | Sets `LineName` configuration/state on `MedianDataSeries` |
| `instance` | `setShowInChart` | `(arg0: boolean)` | `void` | Sets `ShowInChart` configuration/state on `MedianDataSeries` |
| `instance` | `setShowZeroValues` | `(arg0: boolean)` | `void` | Sets `ShowZeroValues` configuration/state on `MedianDataSeries` |
| `instance` | `setChartType` | `(arg0: String)` | `void` | Sets `ChartType` configuration/state on `MedianDataSeries` |
| `instance` | `callDataChangeListeners` | `()` | `void` | Performs call data change listeners operation |
| `instance` | `getColor` | `()` | `String` | Retrieves `Color` property from `MedianDataSeries` |
| `instance` | `isShowInChart` | `()` | `boolean` | Evaluates boolean predicate `isShowInChart` on `MedianDataSeries` |
| `instance` | `isShowZeroValues` | `()` | `boolean` | Evaluates boolean predicate `isShowZeroValues` on `MedianDataSeries` |
| `instance` | `getChartType` | `()` | `String` | Retrieves `ChartType` property from `MedianDataSeries` |
| `instance` | `getLineName` | `()` | `String` | Retrieves `LineName` property from `MedianDataSeries` |
| `instance` | `getComputedUntilIndex` | `()` | `int` | Retrieves `ComputedUntilIndex` property from `MedianDataSeries` |
| `instance` | `_getDouble` | `(arg0: int)` | `double` | Performs get double operation |
| `instance` | `_writeDoubleToOffheapRealIndex` | `(arg0: int, arg1: double)` | `void` | Performs write double to offheap real index operation |
| `instance` | `equals` | `(arg0: Object)` | `boolean` | Performs equals operation |
| `instance` | `toString` | `()` | `String` | Converts/serializes representation via `toString` |
| `instance` | `hashCode` | `()` | `int` | Evaluates boolean predicate `hashCode` on `MedianDataSeries` |
| `instance` | `getClass` | `()` | `Class` | Retrieves `Class` property from `MedianDataSeries` |
| `instance` | `notify` | `()` | `void` | Performs notify operation |
| `instance` | `notifyAll` | `()` | `void` | Performs notify all operation |
| `instance` | `wait` | `(arg0: long)` | `void` | Performs wait operation |
| `instance` | `wait` | `(arg0: long, arg1: int)` | `void` | Performs wait operation |
| `instance` | `wait` | `()` | `void` | Performs wait operation |

---

### `PreparedDataSeries`
- **Full Qualified Name:** `com.strategyquant.datalib.dataseries.PreparedDataSeries`
- **Primary Job / Responsibility:** Market data abstraction and time-series container (`PreparedDataSeries`).

#### Fields
| Scope | Field Name | Type |
| :--- | :--- | :--- |
| `static` | `Log` | `Logger` |

#### Methods & Functions
| Modifiers | Method Name | Parameter Signatures | Return Type | Functional Description / Job |
| :--- | :--- | :--- | :--- | :--- |
| `instance` | `get` | `(arg0: int)` | `double` | Retrieves `` property from `PreparedDataSeries` |
| `instance` | `add` | `(arg0: double)` | `void` | Appends/registers element via `add` |
| `instance` | `set` | `(arg0: double)` | `void` | Sets `` configuration/state on `PreparedDataSeries` |
| `instance` | `set` | `(arg0: int, arg1: double)` | `void` | Sets `` configuration/state on `PreparedDataSeries` |
| `instance` | `set` | `(arg0: int, arg1: double, arg2: boolean)` | `void` | Sets `` configuration/state on `PreparedDataSeries` |
| `instance` | `destroy` | `()` | `void` | Performs destroy operation |
| `instance` | `addChangeListener` | `(arg0: int, arg1: IDataSeriesChangeListener)` | `void` | Appends/registers element via `addChangeListener` |
| `instance` | `addValues` | `(arg0: int)` | `void` | Appends/registers element via `addValues` |
| `instance` | `callDataChangeListeners` | `()` | `void` | Performs call data change listeners operation |
| `instance` | `addValuesBefore` | `(arg0: int)` | `void` | Appends/registers element via `addValuesBefore` |
| `instance` | `addValuesBefore` | `(arg0: int, arg1: double)` | `void` | Appends/registers element via `addValuesBefore` |
| `instance` | `getRounded` | `(arg0: int, arg1: int)` | `double` | Retrieves `Rounded` property from `PreparedDataSeries` |
| `instance` | `getRounded` | `(arg0: int)` | `double` | Retrieves `Rounded` property from `PreparedDataSeries` |
| `instance` | `chartHashCode` | `()` | `int` | Performs chart hash code operation |
| `instance` | `getName` | `()` | `String` | Retrieves `Name` property from `PreparedDataSeries` |
| `instance` | `size` | `()` | `int` | Performs size operation |
| `instance` | `setName` | `(arg0: String)` | `void` | Sets `Name` configuration/state on `PreparedDataSeries` |
| `instance` | `setName` | `(arg0: String, arg1: ChartDef)` | `void` | Sets `Name` configuration/state on `PreparedDataSeries` |
| `instance` | `setColor` | `(arg0: String)` | `void` | Sets `Color` configuration/state on `PreparedDataSeries` |
| `instance` | `getInstrumentInfo` | `()` | `InstrumentInfo` | Retrieves `InstrumentInfo` property from `PreparedDataSeries` |
| `instance` | `Symbol` | `()` | `String` | Performs symbol operation |
| `instance` | `getIndyStartingBar` | `()` | `int` | Retrieves `IndyStartingBar` property from `PreparedDataSeries` |
| `instance` | `setIndyStartingBar` | `(arg0: int)` | `void` | Sets `IndyStartingBar` configuration/state on `PreparedDataSeries` |
| `instance` | `getShift` | `()` | `int` | Retrieves `Shift` property from `PreparedDataSeries` |
| `instance` | `setDataComputer` | `(arg0: IDataSeriesComputer)` | `void` | Sets `DataComputer` configuration/state on `PreparedDataSeries` |
| `instance` | `specialSize` | `()` | `int` | Performs special size operation |
| `instance` | `addDoubleValues` | `(arg0: int, arg1: double)` | `void` | Appends/registers element via `addDoubleValues` |
| `instance` | `addLongValues` | `(arg0: int, arg1: long)` | `void` | Appends/registers element via `addLongValues` |
| `instance` | `updateComputedUntil` | `(arg0: int)` | `void` | Performs update computed until operation |
| `instance` | `setComputedUntil` | `(arg0: int)` | `void` | Sets `ComputedUntil` configuration/state on `PreparedDataSeries` |
| `instance` | `setShift` | `(arg0: int)` | `void` | Sets `Shift` configuration/state on `PreparedDataSeries` |
| `instance` | `setLineName` | `(arg0: String)` | `void` | Sets `LineName` configuration/state on `PreparedDataSeries` |
| `instance` | `setShowInChart` | `(arg0: boolean)` | `void` | Sets `ShowInChart` configuration/state on `PreparedDataSeries` |
| `instance` | `setShowZeroValues` | `(arg0: boolean)` | `void` | Sets `ShowZeroValues` configuration/state on `PreparedDataSeries` |
| `instance` | `setChartType` | `(arg0: String)` | `void` | Sets `ChartType` configuration/state on `PreparedDataSeries` |
| `instance` | `getColor` | `()` | `String` | Retrieves `Color` property from `PreparedDataSeries` |
| `instance` | `isShowInChart` | `()` | `boolean` | Evaluates boolean predicate `isShowInChart` on `PreparedDataSeries` |
| `instance` | `isShowZeroValues` | `()` | `boolean` | Evaluates boolean predicate `isShowZeroValues` on `PreparedDataSeries` |
| `instance` | `getChartType` | `()` | `String` | Retrieves `ChartType` property from `PreparedDataSeries` |
| `instance` | `getLineName` | `()` | `String` | Retrieves `LineName` property from `PreparedDataSeries` |
| `instance` | `getComputedUntilIndex` | `()` | `int` | Retrieves `ComputedUntilIndex` property from `PreparedDataSeries` |
| `instance` | `_getDouble` | `(arg0: int)` | `double` | Performs get double operation |
| `instance` | `_writeDoubleToOffheapRealIndex` | `(arg0: int, arg1: double)` | `void` | Performs write double to offheap real index operation |
| `instance` | `equals` | `(arg0: Object)` | `boolean` | Performs equals operation |
| `instance` | `toString` | `()` | `String` | Converts/serializes representation via `toString` |
| `instance` | `hashCode` | `()` | `int` | Evaluates boolean predicate `hashCode` on `PreparedDataSeries` |
| `instance` | `getClass` | `()` | `Class` | Retrieves `Class` property from `PreparedDataSeries` |
| `instance` | `notify` | `()` | `void` | Performs notify operation |
| `instance` | `notifyAll` | `()` | `void` | Performs notify all operation |
| `instance` | `wait` | `(arg0: long)` | `void` | Performs wait operation |
| `instance` | `wait` | `(arg0: long, arg1: int)` | `void` | Performs wait operation |
| `instance` | `wait` | `()` | `void` | Performs wait operation |

---

### `PreparedTimeDataSeries`
- **Full Qualified Name:** `com.strategyquant.datalib.dataseries.PreparedTimeDataSeries`
- **Primary Job / Responsibility:** Market data abstraction and time-series container (`PreparedTimeDataSeries`).

#### Fields
| Scope | Field Name | Type |
| :--- | :--- | :--- |
| `static` | `Log` | `Logger` |

#### Methods & Functions
| Modifiers | Method Name | Parameter Signatures | Return Type | Functional Description / Job |
| :--- | :--- | :--- | :--- | :--- |
| `instance` | `get` | `(arg0: int)` | `long` | Retrieves `` property from `PreparedTimeDataSeries` |
| `instance` | `add` | `(arg0: long)` | `void` | Appends/registers element via `add` |
| `instance` | `set` | `(arg0: long)` | `void` | Sets `` configuration/state on `PreparedTimeDataSeries` |
| `instance` | `set` | `(arg0: int, arg1: long, arg2: boolean)` | `void` | Sets `` configuration/state on `PreparedTimeDataSeries` |
| `instance` | `set` | `(arg0: int, arg1: long)` | `void` | Sets `` configuration/state on `PreparedTimeDataSeries` |
| `instance` | `destroy` | `()` | `void` | Performs destroy operation |
| `instance` | `addChangeListener` | `(arg0: int, arg1: IDataSeriesChangeListener)` | `void` | Appends/registers element via `addChangeListener` |
| `instance` | `addValues` | `(arg0: int)` | `void` | Appends/registers element via `addValues` |
| `instance` | `addValuesBefore` | `(arg0: int)` | `void` | Appends/registers element via `addValuesBefore` |
| `instance` | `addValuesBefore` | `(arg0: int, arg1: long)` | `void` | Appends/registers element via `addValuesBefore` |
| `instance` | `size` | `()` | `int` | Performs size operation |
| `instance` | `specialSize` | `()` | `int` | Performs special size operation |
| `instance` | `addLongValues` | `(arg0: int, arg1: long)` | `void` | Appends/registers element via `addLongValues` |
| `instance` | `getDateBarsFromDate` | `(arg0: long, arg1: int)` | `long` | Retrieves `DateBarsFromDate` property from `PreparedTimeDataSeries` |
| `instance` | `getName` | `()` | `String` | Retrieves `Name` property from `PreparedTimeDataSeries` |
| `instance` | `setName` | `(arg0: String)` | `void` | Sets `Name` configuration/state on `PreparedTimeDataSeries` |
| `instance` | `setName` | `(arg0: String, arg1: ChartDef)` | `void` | Sets `Name` configuration/state on `PreparedTimeDataSeries` |
| `instance` | `setColor` | `(arg0: String)` | `void` | Sets `Color` configuration/state on `PreparedTimeDataSeries` |
| `instance` | `getInstrumentInfo` | `()` | `InstrumentInfo` | Retrieves `InstrumentInfo` property from `PreparedTimeDataSeries` |
| `instance` | `Symbol` | `()` | `String` | Performs symbol operation |
| `instance` | `getIndyStartingBar` | `()` | `int` | Retrieves `IndyStartingBar` property from `PreparedTimeDataSeries` |
| `instance` | `setIndyStartingBar` | `(arg0: int)` | `void` | Sets `IndyStartingBar` configuration/state on `PreparedTimeDataSeries` |
| `instance` | `getShift` | `()` | `int` | Retrieves `Shift` property from `PreparedTimeDataSeries` |
| `instance` | `setDataComputer` | `(arg0: IDataSeriesComputer)` | `void` | Sets `DataComputer` configuration/state on `PreparedTimeDataSeries` |
| `instance` | `addDoubleValues` | `(arg0: int, arg1: double)` | `void` | Appends/registers element via `addDoubleValues` |
| `instance` | `updateComputedUntil` | `(arg0: int)` | `void` | Performs update computed until operation |
| `instance` | `setComputedUntil` | `(arg0: int)` | `void` | Sets `ComputedUntil` configuration/state on `PreparedTimeDataSeries` |
| `instance` | `setShift` | `(arg0: int)` | `void` | Sets `Shift` configuration/state on `PreparedTimeDataSeries` |
| `instance` | `setLineName` | `(arg0: String)` | `void` | Sets `LineName` configuration/state on `PreparedTimeDataSeries` |
| `instance` | `setShowInChart` | `(arg0: boolean)` | `void` | Sets `ShowInChart` configuration/state on `PreparedTimeDataSeries` |
| `instance` | `setShowZeroValues` | `(arg0: boolean)` | `void` | Sets `ShowZeroValues` configuration/state on `PreparedTimeDataSeries` |
| `instance` | `setChartType` | `(arg0: String)` | `void` | Sets `ChartType` configuration/state on `PreparedTimeDataSeries` |
| `instance` | `callDataChangeListeners` | `()` | `void` | Performs call data change listeners operation |
| `instance` | `getColor` | `()` | `String` | Retrieves `Color` property from `PreparedTimeDataSeries` |
| `instance` | `isShowInChart` | `()` | `boolean` | Evaluates boolean predicate `isShowInChart` on `PreparedTimeDataSeries` |
| `instance` | `isShowZeroValues` | `()` | `boolean` | Evaluates boolean predicate `isShowZeroValues` on `PreparedTimeDataSeries` |
| `instance` | `getChartType` | `()` | `String` | Retrieves `ChartType` property from `PreparedTimeDataSeries` |
| `instance` | `getLineName` | `()` | `String` | Retrieves `LineName` property from `PreparedTimeDataSeries` |
| `instance` | `getComputedUntilIndex` | `()` | `int` | Retrieves `ComputedUntilIndex` property from `PreparedTimeDataSeries` |
| `instance` | `_getDouble` | `(arg0: int)` | `double` | Performs get double operation |
| `instance` | `_writeDoubleToOffheapRealIndex` | `(arg0: int, arg1: double)` | `void` | Performs write double to offheap real index operation |
| `instance` | `equals` | `(arg0: Object)` | `boolean` | Performs equals operation |
| `instance` | `toString` | `()` | `String` | Converts/serializes representation via `toString` |
| `instance` | `hashCode` | `()` | `int` | Evaluates boolean predicate `hashCode` on `PreparedTimeDataSeries` |
| `instance` | `getClass` | `()` | `Class` | Retrieves `Class` property from `PreparedTimeDataSeries` |
| `instance` | `notify` | `()` | `void` | Performs notify operation |
| `instance` | `notifyAll` | `()` | `void` | Performs notify all operation |
| `instance` | `wait` | `(arg0: long)` | `void` | Performs wait operation |
| `instance` | `wait` | `(arg0: long, arg1: int)` | `void` | Performs wait operation |
| `instance` | `wait` | `()` | `void` | Performs wait operation |

---

### `SQDoubleArrayList`
- **Full Qualified Name:** `com.strategyquant.datalib.dataseries.SQDoubleArrayList`
- **Primary Job / Responsibility:** Market data abstraction and time-series container (`SQDoubleArrayList`).

#### Fields
| Scope | Field Name | Type |
| :--- | :--- | :--- |
| `static` | `DEFAULT_CAPACITY` | `int` |
| `static` | `Log` | `Logger` |
| `instance` | `buffer` | `double[]` |
| `instance` | `elementsCount` | `int` |

#### Methods & Functions
| Modifiers | Method Name | Parameter Signatures | Return Type | Functional Description / Job |
| :--- | :--- | :--- | :--- | :--- |
| `instance` | `getDouble` | `(arg0: int)` | `double` | Retrieves `Double` property from `SQDoubleArrayList` |
| `instance` | `clear` | `()` | `void` | Removes/resets elements via `clear` |
| `instance` | `add` | `(arg0: double)` | `void` | Appends/registers element via `add` |
| `instance` | `set` | `(arg0: int, arg1: double)` | `double` | Sets `` configuration/state on `SQDoubleArrayList` |
| `instance` | `ensureCapacity` | `(arg0: int)` | `void` | Performs ensure capacity operation |
| `instance` | `release` | `()` | `void` | Performs release operation |
| `instance` | `addValues` | `(arg0: int, arg1: double)` | `void` | Appends/registers element via `addValues` |
| `instance` | `getCapacity` | `()` | `long` | Retrieves `Capacity` property from `SQDoubleArrayList` |
| `instance` | `equals` | `(arg0: Object)` | `boolean` | Performs equals operation |
| `instance` | `toString` | `()` | `String` | Converts/serializes representation via `toString` |
| `instance` | `hashCode` | `()` | `int` | Evaluates boolean predicate `hashCode` on `SQDoubleArrayList` |
| `instance` | `getClass` | `()` | `Class` | Retrieves `Class` property from `SQDoubleArrayList` |
| `instance` | `notify` | `()` | `void` | Performs notify operation |
| `instance` | `notifyAll` | `()` | `void` | Performs notify all operation |
| `instance` | `wait` | `(arg0: long)` | `void` | Performs wait operation |
| `instance` | `wait` | `(arg0: long, arg1: int)` | `void` | Performs wait operation |
| `instance` | `wait` | `()` | `void` | Performs wait operation |

---

### `TimeDataSeries`
- **Full Qualified Name:** `com.strategyquant.datalib.dataseries.TimeDataSeries`
- **Primary Job / Responsibility:** Market data abstraction and time-series container (`TimeDataSeries`).

#### Fields
| Scope | Field Name | Type |
| :--- | :--- | :--- |
| `static` | `Log` | `Logger` |

#### Methods & Functions
| Modifiers | Method Name | Parameter Signatures | Return Type | Functional Description / Job |
| :--- | :--- | :--- | :--- | :--- |
| `instance` | `get` | `(arg0: int)` | `long` | Retrieves `` property from `TimeDataSeries` |
| `instance` | `add` | `(arg0: long)` | `void` | Appends/registers element via `add` |
| `instance` | `set` | `(arg0: int, arg1: long)` | `void` | Sets `` configuration/state on `TimeDataSeries` |
| `instance` | `addValues` | `(arg0: int)` | `void` | Appends/registers element via `addValues` |
| `instance` | `size` | `()` | `int` | Performs size operation |
| `instance` | `destroy` | `()` | `void` | Performs destroy operation |
| `instance` | `specialSize` | `()` | `int` | Performs special size operation |
| `instance` | `addLongValues` | `(arg0: int, arg1: long)` | `void` | Appends/registers element via `addLongValues` |
| `instance` | `getDateBarsFromDate` | `(arg0: long, arg1: int)` | `long` | Retrieves `DateBarsFromDate` property from `TimeDataSeries` |
| `instance` | `getName` | `()` | `String` | Retrieves `Name` property from `TimeDataSeries` |
| `instance` | `setName` | `(arg0: String)` | `void` | Sets `Name` configuration/state on `TimeDataSeries` |
| `instance` | `setName` | `(arg0: String, arg1: ChartDef)` | `void` | Sets `Name` configuration/state on `TimeDataSeries` |
| `instance` | `setColor` | `(arg0: String)` | `void` | Sets `Color` configuration/state on `TimeDataSeries` |
| `instance` | `getInstrumentInfo` | `()` | `InstrumentInfo` | Retrieves `InstrumentInfo` property from `TimeDataSeries` |
| `instance` | `Symbol` | `()` | `String` | Performs symbol operation |
| `instance` | `getIndyStartingBar` | `()` | `int` | Retrieves `IndyStartingBar` property from `TimeDataSeries` |
| `instance` | `setIndyStartingBar` | `(arg0: int)` | `void` | Sets `IndyStartingBar` configuration/state on `TimeDataSeries` |
| `instance` | `getShift` | `()` | `int` | Retrieves `Shift` property from `TimeDataSeries` |
| `instance` | `addChangeListener` | `(arg0: int, arg1: IDataSeriesChangeListener)` | `void` | Appends/registers element via `addChangeListener` |
| `instance` | `setDataComputer` | `(arg0: IDataSeriesComputer)` | `void` | Sets `DataComputer` configuration/state on `TimeDataSeries` |
| `instance` | `addDoubleValues` | `(arg0: int, arg1: double)` | `void` | Appends/registers element via `addDoubleValues` |
| `instance` | `updateComputedUntil` | `(arg0: int)` | `void` | Performs update computed until operation |
| `instance` | `setComputedUntil` | `(arg0: int)` | `void` | Sets `ComputedUntil` configuration/state on `TimeDataSeries` |
| `instance` | `setShift` | `(arg0: int)` | `void` | Sets `Shift` configuration/state on `TimeDataSeries` |
| `instance` | `setLineName` | `(arg0: String)` | `void` | Sets `LineName` configuration/state on `TimeDataSeries` |
| `instance` | `setShowInChart` | `(arg0: boolean)` | `void` | Sets `ShowInChart` configuration/state on `TimeDataSeries` |
| `instance` | `setShowZeroValues` | `(arg0: boolean)` | `void` | Sets `ShowZeroValues` configuration/state on `TimeDataSeries` |
| `instance` | `setChartType` | `(arg0: String)` | `void` | Sets `ChartType` configuration/state on `TimeDataSeries` |
| `instance` | `callDataChangeListeners` | `()` | `void` | Performs call data change listeners operation |
| `instance` | `getColor` | `()` | `String` | Retrieves `Color` property from `TimeDataSeries` |
| `instance` | `isShowInChart` | `()` | `boolean` | Evaluates boolean predicate `isShowInChart` on `TimeDataSeries` |
| `instance` | `isShowZeroValues` | `()` | `boolean` | Evaluates boolean predicate `isShowZeroValues` on `TimeDataSeries` |
| `instance` | `getChartType` | `()` | `String` | Retrieves `ChartType` property from `TimeDataSeries` |
| `instance` | `getLineName` | `()` | `String` | Retrieves `LineName` property from `TimeDataSeries` |
| `instance` | `getComputedUntilIndex` | `()` | `int` | Retrieves `ComputedUntilIndex` property from `TimeDataSeries` |
| `instance` | `_getDouble` | `(arg0: int)` | `double` | Performs get double operation |
| `instance` | `_writeDoubleToOffheapRealIndex` | `(arg0: int, arg1: double)` | `void` | Performs write double to offheap real index operation |
| `instance` | `equals` | `(arg0: Object)` | `boolean` | Performs equals operation |
| `instance` | `toString` | `()` | `String` | Converts/serializes representation via `toString` |
| `instance` | `hashCode` | `()` | `int` | Evaluates boolean predicate `hashCode` on `TimeDataSeries` |
| `instance` | `getClass` | `()` | `Class` | Retrieves `Class` property from `TimeDataSeries` |
| `instance` | `notify` | `()` | `void` | Performs notify operation |
| `instance` | `notifyAll` | `()` | `void` | Performs notify all operation |
| `instance` | `wait` | `(arg0: long)` | `void` | Performs wait operation |
| `instance` | `wait` | `(arg0: long, arg1: int)` | `void` | Performs wait operation |
| `instance` | `wait` | `()` | `void` | Performs wait operation |

---

### `TimeDataSeriesBase`
- **Full Qualified Name:** `com.strategyquant.datalib.dataseries.TimeDataSeriesBase`
- **Primary Job / Responsibility:** Market data abstraction and time-series container (`TimeDataSeriesBase`).

#### Fields
| Scope | Field Name | Type |
| :--- | :--- | :--- |
| `static` | `Log` | `Logger` |

#### Methods & Functions
| Modifiers | Method Name | Parameter Signatures | Return Type | Functional Description / Job |
| :--- | :--- | :--- | :--- | :--- |
| `instance` | `size` | `()` | `int` | Performs size operation |
| `instance` | `destroy` | `()` | `void` | Performs destroy operation |
| `instance` | `specialSize` | `()` | `int` | Performs special size operation |
| `instance` | `addLongValues` | `(arg0: int, arg1: long)` | `void` | Appends/registers element via `addLongValues` |
| `instance` | `getDateBarsFromDate` | `(arg0: long, arg1: int)` | `long` | Retrieves `DateBarsFromDate` property from `TimeDataSeriesBase` |
| `instance` | `getName` | `()` | `String` | Retrieves `Name` property from `TimeDataSeriesBase` |
| `instance` | `setName` | `(arg0: String)` | `void` | Sets `Name` configuration/state on `TimeDataSeriesBase` |
| `instance` | `setName` | `(arg0: String, arg1: ChartDef)` | `void` | Sets `Name` configuration/state on `TimeDataSeriesBase` |
| `instance` | `setColor` | `(arg0: String)` | `void` | Sets `Color` configuration/state on `TimeDataSeriesBase` |
| `instance` | `getInstrumentInfo` | `()` | `InstrumentInfo` | Retrieves `InstrumentInfo` property from `TimeDataSeriesBase` |
| `instance` | `Symbol` | `()` | `String` | Performs symbol operation |
| `instance` | `getIndyStartingBar` | `()` | `int` | Retrieves `IndyStartingBar` property from `TimeDataSeriesBase` |
| `instance` | `setIndyStartingBar` | `(arg0: int)` | `void` | Sets `IndyStartingBar` configuration/state on `TimeDataSeriesBase` |
| `instance` | `getShift` | `()` | `int` | Retrieves `Shift` property from `TimeDataSeriesBase` |
| `instance` | `addChangeListener` | `(arg0: int, arg1: IDataSeriesChangeListener)` | `void` | Appends/registers element via `addChangeListener` |
| `instance` | `setDataComputer` | `(arg0: IDataSeriesComputer)` | `void` | Sets `DataComputer` configuration/state on `TimeDataSeriesBase` |
| `instance` | `addDoubleValues` | `(arg0: int, arg1: double)` | `void` | Appends/registers element via `addDoubleValues` |
| `instance` | `updateComputedUntil` | `(arg0: int)` | `void` | Performs update computed until operation |
| `instance` | `setComputedUntil` | `(arg0: int)` | `void` | Sets `ComputedUntil` configuration/state on `TimeDataSeriesBase` |
| `instance` | `setShift` | `(arg0: int)` | `void` | Sets `Shift` configuration/state on `TimeDataSeriesBase` |
| `instance` | `setLineName` | `(arg0: String)` | `void` | Sets `LineName` configuration/state on `TimeDataSeriesBase` |
| `instance` | `setShowInChart` | `(arg0: boolean)` | `void` | Sets `ShowInChart` configuration/state on `TimeDataSeriesBase` |
| `instance` | `setShowZeroValues` | `(arg0: boolean)` | `void` | Sets `ShowZeroValues` configuration/state on `TimeDataSeriesBase` |
| `instance` | `setChartType` | `(arg0: String)` | `void` | Sets `ChartType` configuration/state on `TimeDataSeriesBase` |
| `instance` | `callDataChangeListeners` | `()` | `void` | Performs call data change listeners operation |
| `instance` | `getColor` | `()` | `String` | Retrieves `Color` property from `TimeDataSeriesBase` |
| `instance` | `isShowInChart` | `()` | `boolean` | Evaluates boolean predicate `isShowInChart` on `TimeDataSeriesBase` |
| `instance` | `isShowZeroValues` | `()` | `boolean` | Evaluates boolean predicate `isShowZeroValues` on `TimeDataSeriesBase` |
| `instance` | `getChartType` | `()` | `String` | Retrieves `ChartType` property from `TimeDataSeriesBase` |
| `instance` | `getLineName` | `()` | `String` | Retrieves `LineName` property from `TimeDataSeriesBase` |
| `instance` | `getComputedUntilIndex` | `()` | `int` | Retrieves `ComputedUntilIndex` property from `TimeDataSeriesBase` |
| `instance` | `_getDouble` | `(arg0: int)` | `double` | Performs get double operation |
| `instance` | `_writeDoubleToOffheapRealIndex` | `(arg0: int, arg1: double)` | `void` | Performs write double to offheap real index operation |
| `instance` | `equals` | `(arg0: Object)` | `boolean` | Performs equals operation |
| `instance` | `toString` | `()` | `String` | Converts/serializes representation via `toString` |
| `instance` | `hashCode` | `()` | `int` | Evaluates boolean predicate `hashCode` on `TimeDataSeriesBase` |
| `instance` | `getClass` | `()` | `Class` | Retrieves `Class` property from `TimeDataSeriesBase` |
| `instance` | `notify` | `()` | `void` | Performs notify operation |
| `instance` | `notifyAll` | `()` | `void` | Performs notify all operation |
| `instance` | `wait` | `(arg0: long)` | `void` | Performs wait operation |
| `instance` | `wait` | `(arg0: long, arg1: int)` | `void` | Performs wait operation |
| `instance` | `wait` | `()` | `void` | Performs wait operation |

---

### `TypicalDataSeries`
- **Full Qualified Name:** `com.strategyquant.datalib.dataseries.TypicalDataSeries`
- **Primary Job / Responsibility:** Market data abstraction and time-series container (`TypicalDataSeries`).

#### Fields
| Scope | Field Name | Type |
| :--- | :--- | :--- |
| `static` | `Log` | `Logger` |
| `instance` | `Close` | `DataSeries` |
| `instance` | `High` | `DataSeries` |
| `instance` | `Low` | `DataSeries` |
| `instance` | `Open` | `DataSeries` |
| `instance` | `Volume` | `DataSeries` |

#### Methods & Functions
| Modifiers | Method Name | Parameter Signatures | Return Type | Functional Description / Job |
| :--- | :--- | :--- | :--- | :--- |
| `instance` | `computeValue` | `(arg0: int)` | `double` | Executes calculation for `computeValue` |
| `instance` | `size` | `()` | `int` | Performs size operation |
| `instance` | `get` | `(arg0: int)` | `double` | Retrieves `` property from `TypicalDataSeries` |
| `instance` | `destroy` | `()` | `void` | Performs destroy operation |
| `instance` | `add` | `(arg0: double)` | `void` | Appends/registers element via `add` |
| `instance` | `set` | `(arg0: int, arg1: double)` | `void` | Sets `` configuration/state on `TypicalDataSeries` |
| `instance` | `set` | `(arg0: int, arg1: double, arg2: boolean)` | `void` | Sets `` configuration/state on `TypicalDataSeries` |
| `instance` | `set` | `(arg0: double)` | `void` | Sets `` configuration/state on `TypicalDataSeries` |
| `instance` | `getRounded` | `(arg0: int, arg1: int)` | `double` | Retrieves `Rounded` property from `TypicalDataSeries` |
| `instance` | `getRounded` | `(arg0: int)` | `double` | Retrieves `Rounded` property from `TypicalDataSeries` |
| `instance` | `addValues` | `(arg0: int)` | `void` | Appends/registers element via `addValues` |
| `instance` | `chartHashCode` | `()` | `int` | Performs chart hash code operation |
| `instance` | `getName` | `()` | `String` | Retrieves `Name` property from `TypicalDataSeries` |
| `instance` | `setName` | `(arg0: String)` | `void` | Sets `Name` configuration/state on `TypicalDataSeries` |
| `instance` | `setName` | `(arg0: String, arg1: ChartDef)` | `void` | Sets `Name` configuration/state on `TypicalDataSeries` |
| `instance` | `setColor` | `(arg0: String)` | `void` | Sets `Color` configuration/state on `TypicalDataSeries` |
| `instance` | `getInstrumentInfo` | `()` | `InstrumentInfo` | Retrieves `InstrumentInfo` property from `TypicalDataSeries` |
| `instance` | `Symbol` | `()` | `String` | Performs symbol operation |
| `instance` | `getIndyStartingBar` | `()` | `int` | Retrieves `IndyStartingBar` property from `TypicalDataSeries` |
| `instance` | `setIndyStartingBar` | `(arg0: int)` | `void` | Sets `IndyStartingBar` configuration/state on `TypicalDataSeries` |
| `instance` | `getShift` | `()` | `int` | Retrieves `Shift` property from `TypicalDataSeries` |
| `instance` | `addChangeListener` | `(arg0: int, arg1: IDataSeriesChangeListener)` | `void` | Appends/registers element via `addChangeListener` |
| `instance` | `setDataComputer` | `(arg0: IDataSeriesComputer)` | `void` | Sets `DataComputer` configuration/state on `TypicalDataSeries` |
| `instance` | `specialSize` | `()` | `int` | Performs special size operation |
| `instance` | `addDoubleValues` | `(arg0: int, arg1: double)` | `void` | Appends/registers element via `addDoubleValues` |
| `instance` | `addLongValues` | `(arg0: int, arg1: long)` | `void` | Appends/registers element via `addLongValues` |
| `instance` | `updateComputedUntil` | `(arg0: int)` | `void` | Performs update computed until operation |
| `instance` | `setComputedUntil` | `(arg0: int)` | `void` | Sets `ComputedUntil` configuration/state on `TypicalDataSeries` |
| `instance` | `setShift` | `(arg0: int)` | `void` | Sets `Shift` configuration/state on `TypicalDataSeries` |
| `instance` | `setLineName` | `(arg0: String)` | `void` | Sets `LineName` configuration/state on `TypicalDataSeries` |
| `instance` | `setShowInChart` | `(arg0: boolean)` | `void` | Sets `ShowInChart` configuration/state on `TypicalDataSeries` |
| `instance` | `setShowZeroValues` | `(arg0: boolean)` | `void` | Sets `ShowZeroValues` configuration/state on `TypicalDataSeries` |
| `instance` | `setChartType` | `(arg0: String)` | `void` | Sets `ChartType` configuration/state on `TypicalDataSeries` |
| `instance` | `callDataChangeListeners` | `()` | `void` | Performs call data change listeners operation |
| `instance` | `getColor` | `()` | `String` | Retrieves `Color` property from `TypicalDataSeries` |
| `instance` | `isShowInChart` | `()` | `boolean` | Evaluates boolean predicate `isShowInChart` on `TypicalDataSeries` |
| `instance` | `isShowZeroValues` | `()` | `boolean` | Evaluates boolean predicate `isShowZeroValues` on `TypicalDataSeries` |
| `instance` | `getChartType` | `()` | `String` | Retrieves `ChartType` property from `TypicalDataSeries` |
| `instance` | `getLineName` | `()` | `String` | Retrieves `LineName` property from `TypicalDataSeries` |
| `instance` | `getComputedUntilIndex` | `()` | `int` | Retrieves `ComputedUntilIndex` property from `TypicalDataSeries` |
| `instance` | `_getDouble` | `(arg0: int)` | `double` | Performs get double operation |
| `instance` | `_writeDoubleToOffheapRealIndex` | `(arg0: int, arg1: double)` | `void` | Performs write double to offheap real index operation |
| `instance` | `equals` | `(arg0: Object)` | `boolean` | Performs equals operation |
| `instance` | `toString` | `()` | `String` | Converts/serializes representation via `toString` |
| `instance` | `hashCode` | `()` | `int` | Evaluates boolean predicate `hashCode` on `TypicalDataSeries` |
| `instance` | `getClass` | `()` | `Class` | Retrieves `Class` property from `TypicalDataSeries` |
| `instance` | `notify` | `()` | `void` | Performs notify operation |
| `instance` | `notifyAll` | `()` | `void` | Performs notify all operation |
| `instance` | `wait` | `(arg0: long)` | `void` | Performs wait operation |
| `instance` | `wait` | `(arg0: long, arg1: int)` | `void` | Performs wait operation |
| `instance` | `wait` | `()` | `void` | Performs wait operation |

---

### `WeightedDataSeries`
- **Full Qualified Name:** `com.strategyquant.datalib.dataseries.WeightedDataSeries`
- **Primary Job / Responsibility:** Market data abstraction and time-series container (`WeightedDataSeries`).

#### Fields
| Scope | Field Name | Type |
| :--- | :--- | :--- |
| `static` | `Log` | `Logger` |
| `instance` | `Close` | `DataSeries` |
| `instance` | `High` | `DataSeries` |
| `instance` | `Low` | `DataSeries` |
| `instance` | `Open` | `DataSeries` |
| `instance` | `Volume` | `DataSeries` |

#### Methods & Functions
| Modifiers | Method Name | Parameter Signatures | Return Type | Functional Description / Job |
| :--- | :--- | :--- | :--- | :--- |
| `instance` | `computeValue` | `(arg0: int)` | `double` | Executes calculation for `computeValue` |
| `instance` | `size` | `()` | `int` | Performs size operation |
| `instance` | `get` | `(arg0: int)` | `double` | Retrieves `` property from `WeightedDataSeries` |
| `instance` | `destroy` | `()` | `void` | Performs destroy operation |
| `instance` | `add` | `(arg0: double)` | `void` | Appends/registers element via `add` |
| `instance` | `set` | `(arg0: int, arg1: double)` | `void` | Sets `` configuration/state on `WeightedDataSeries` |
| `instance` | `set` | `(arg0: int, arg1: double, arg2: boolean)` | `void` | Sets `` configuration/state on `WeightedDataSeries` |
| `instance` | `set` | `(arg0: double)` | `void` | Sets `` configuration/state on `WeightedDataSeries` |
| `instance` | `getRounded` | `(arg0: int, arg1: int)` | `double` | Retrieves `Rounded` property from `WeightedDataSeries` |
| `instance` | `getRounded` | `(arg0: int)` | `double` | Retrieves `Rounded` property from `WeightedDataSeries` |
| `instance` | `addValues` | `(arg0: int)` | `void` | Appends/registers element via `addValues` |
| `instance` | `chartHashCode` | `()` | `int` | Performs chart hash code operation |
| `instance` | `getName` | `()` | `String` | Retrieves `Name` property from `WeightedDataSeries` |
| `instance` | `setName` | `(arg0: String)` | `void` | Sets `Name` configuration/state on `WeightedDataSeries` |
| `instance` | `setName` | `(arg0: String, arg1: ChartDef)` | `void` | Sets `Name` configuration/state on `WeightedDataSeries` |
| `instance` | `setColor` | `(arg0: String)` | `void` | Sets `Color` configuration/state on `WeightedDataSeries` |
| `instance` | `getInstrumentInfo` | `()` | `InstrumentInfo` | Retrieves `InstrumentInfo` property from `WeightedDataSeries` |
| `instance` | `Symbol` | `()` | `String` | Performs symbol operation |
| `instance` | `getIndyStartingBar` | `()` | `int` | Retrieves `IndyStartingBar` property from `WeightedDataSeries` |
| `instance` | `setIndyStartingBar` | `(arg0: int)` | `void` | Sets `IndyStartingBar` configuration/state on `WeightedDataSeries` |
| `instance` | `getShift` | `()` | `int` | Retrieves `Shift` property from `WeightedDataSeries` |
| `instance` | `addChangeListener` | `(arg0: int, arg1: IDataSeriesChangeListener)` | `void` | Appends/registers element via `addChangeListener` |
| `instance` | `setDataComputer` | `(arg0: IDataSeriesComputer)` | `void` | Sets `DataComputer` configuration/state on `WeightedDataSeries` |
| `instance` | `specialSize` | `()` | `int` | Performs special size operation |
| `instance` | `addDoubleValues` | `(arg0: int, arg1: double)` | `void` | Appends/registers element via `addDoubleValues` |
| `instance` | `addLongValues` | `(arg0: int, arg1: long)` | `void` | Appends/registers element via `addLongValues` |
| `instance` | `updateComputedUntil` | `(arg0: int)` | `void` | Performs update computed until operation |
| `instance` | `setComputedUntil` | `(arg0: int)` | `void` | Sets `ComputedUntil` configuration/state on `WeightedDataSeries` |
| `instance` | `setShift` | `(arg0: int)` | `void` | Sets `Shift` configuration/state on `WeightedDataSeries` |
| `instance` | `setLineName` | `(arg0: String)` | `void` | Sets `LineName` configuration/state on `WeightedDataSeries` |
| `instance` | `setShowInChart` | `(arg0: boolean)` | `void` | Sets `ShowInChart` configuration/state on `WeightedDataSeries` |
| `instance` | `setShowZeroValues` | `(arg0: boolean)` | `void` | Sets `ShowZeroValues` configuration/state on `WeightedDataSeries` |
| `instance` | `setChartType` | `(arg0: String)` | `void` | Sets `ChartType` configuration/state on `WeightedDataSeries` |
| `instance` | `callDataChangeListeners` | `()` | `void` | Performs call data change listeners operation |
| `instance` | `getColor` | `()` | `String` | Retrieves `Color` property from `WeightedDataSeries` |
| `instance` | `isShowInChart` | `()` | `boolean` | Evaluates boolean predicate `isShowInChart` on `WeightedDataSeries` |
| `instance` | `isShowZeroValues` | `()` | `boolean` | Evaluates boolean predicate `isShowZeroValues` on `WeightedDataSeries` |
| `instance` | `getChartType` | `()` | `String` | Retrieves `ChartType` property from `WeightedDataSeries` |
| `instance` | `getLineName` | `()` | `String` | Retrieves `LineName` property from `WeightedDataSeries` |
| `instance` | `getComputedUntilIndex` | `()` | `int` | Retrieves `ComputedUntilIndex` property from `WeightedDataSeries` |
| `instance` | `_getDouble` | `(arg0: int)` | `double` | Performs get double operation |
| `instance` | `_writeDoubleToOffheapRealIndex` | `(arg0: int, arg1: double)` | `void` | Performs write double to offheap real index operation |
| `instance` | `equals` | `(arg0: Object)` | `boolean` | Performs equals operation |
| `instance` | `toString` | `()` | `String` | Converts/serializes representation via `toString` |
| `instance` | `hashCode` | `()` | `int` | Evaluates boolean predicate `hashCode` on `WeightedDataSeries` |
| `instance` | `getClass` | `()` | `Class` | Retrieves `Class` property from `WeightedDataSeries` |
| `instance` | `notify` | `()` | `void` | Performs notify operation |
| `instance` | `notifyAll` | `()` | `void` | Performs notify all operation |
| `instance` | `wait` | `(arg0: long)` | `void` | Performs wait operation |
| `instance` | `wait` | `(arg0: long, arg1: int)` | `void` | Performs wait operation |
| `instance` | `wait` | `()` | `void` | Performs wait operation |

---

## Subsystem: `historyData`

### `AbstractHistoryDataDao`
- **Full Qualified Name:** `com.strategyquant.datalib.historyData.AbstractHistoryDataDao`
- **Primary Job / Responsibility:** Time-series price history, OHLCV bar storage, and chart data management (`AbstractHistoryDataDao`).

#### Fields
| Scope | Field Name | Type |
| :--- | :--- | :--- |
| `static` | `Log` | `Logger` |

#### Methods & Functions
| Modifiers | Method Name | Parameter Signatures | Return Type | Functional Description / Job |
| :--- | :--- | :--- | :--- | :--- |
| `instance` | `dispose` | `()` | `void` | Performs dispose operation |
| `instance` | `getTicker` | `(arg0: String)` | `TickerDto` | Retrieves `Ticker` property from `AbstractHistoryDataDao` |
| `instance` | `getTicker` | `(arg0: Long)` | `TickerDto` | Retrieves `Ticker` property from `AbstractHistoryDataDao` |
| `instance` | `getTicker` | `(arg0: String, arg1: Long)` | `TickerDto` | Retrieves `Ticker` property from `AbstractHistoryDataDao` |
| `instance` | `getTicker` | `(arg0: String, arg1: String)` | `TickerDto` | Retrieves `Ticker` property from `AbstractHistoryDataDao` |
| `instance` | `getChangeDate` | `()` | `Date` | Retrieves `ChangeDate` property from `AbstractHistoryDataDao` |
| `instance` | `getChangeDate` | `(arg0: String)` | `Date` | Retrieves `ChangeDate` property from `AbstractHistoryDataDao` |
| `instance` | `createIndexes` | `()` | `void` | Instantiates/initializes `createIndexes` resource |
| `instance` | `getAllMarkets` | `()` | `List` | Retrieves `AllMarkets` property from `AbstractHistoryDataDao` |
| `instance` | `getTickers` | `(arg0: TickerFilterDto)` | `List` | Retrieves `Tickers` property from `AbstractHistoryDataDao` |
| `instance` | `getTickers` | `(arg0: String, arg1: TickerFilterDto)` | `List` | Retrieves `Tickers` property from `AbstractHistoryDataDao` |
| `instance` | `getExchangeForTicker` | `(arg0: String)` | `String` | Retrieves `ExchangeForTicker` property from `AbstractHistoryDataDao` |
| `instance` | `getAliasesForAlias` | `(arg0: Collection)` | `List` | Retrieves `AliasesForAlias` property from `AbstractHistoryDataDao` |
| `instance` | `getAliasesMapForAlias` | `(arg0: Collection)` | `Map` | Retrieves `AliasesMapForAlias` property from `AbstractHistoryDataDao` |
| `instance` | `equals` | `(arg0: Object)` | `boolean` | Performs equals operation |
| `instance` | `toString` | `()` | `String` | Converts/serializes representation via `toString` |
| `instance` | `hashCode` | `()` | `int` | Evaluates boolean predicate `hashCode` on `AbstractHistoryDataDao` |
| `instance` | `getClass` | `()` | `Class` | Retrieves `Class` property from `AbstractHistoryDataDao` |
| `instance` | `notify` | `()` | `void` | Performs notify operation |
| `instance` | `notifyAll` | `()` | `void` | Performs notify all operation |
| `instance` | `wait` | `(arg0: long)` | `void` | Performs wait operation |
| `instance` | `wait` | `(arg0: long, arg1: int)` | `void` | Performs wait operation |
| `instance` | `wait` | `()` | `void` | Performs wait operation |

---

### `FuturesHistoryDataDao`
- **Full Qualified Name:** `com.strategyquant.datalib.historyData.FuturesHistoryDataDao`
- **Primary Job / Responsibility:** Time-series price history, OHLCV bar storage, and chart data management (`FuturesHistoryDataDao`).

#### Fields
| Scope | Field Name | Type |
| :--- | :--- | :--- |
| `static` | `BMF_ID` | `Long` |
| `static` | `Log` | `Logger` |

#### Methods & Functions
| Modifiers | Method Name | Parameter Signatures | Return Type | Functional Description / Job |
| :--- | :--- | :--- | :--- | :--- |
| `instance` | `getTicker` | `(arg0: String)` | `TickerDto` | Retrieves `Ticker` property from `FuturesHistoryDataDao` |
| `instance` | `getTicker` | `(arg0: Long)` | `TickerDto` | Retrieves `Ticker` property from `FuturesHistoryDataDao` |
| `instance` | `getTicker` | `(arg0: String, arg1: Long)` | `TickerDto` | Retrieves `Ticker` property from `FuturesHistoryDataDao` |
| `instance` | `getTicker` | `(arg0: String, arg1: String)` | `TickerDto` | Retrieves `Ticker` property from `FuturesHistoryDataDao` |
| `instance` | `createIndexes` | `()` | `void` | Instantiates/initializes `createIndexes` resource |
| `instance` | `getAllMarkets` | `()` | `List` | Retrieves `AllMarkets` property from `FuturesHistoryDataDao` |
| `instance` | `getTickers` | `(arg0: TickerFilterDto)` | `List` | Retrieves `Tickers` property from `FuturesHistoryDataDao` |
| `instance` | `getTickers` | `(arg0: String, arg1: TickerFilterDto)` | `List` | Retrieves `Tickers` property from `FuturesHistoryDataDao` |
| `instance` | `getCommodity` | `(arg0: Long)` | `CommodityDto` | Retrieves `Commodity` property from `FuturesHistoryDataDao` |
| `instance` | `getCommodityForFuture` | `(arg0: String)` | `CommodityDto` | Retrieves `CommodityForFuture` property from `FuturesHistoryDataDao` |
| `instance` | `getCommoditiesForFutures` | `(arg0: String[])` | `List` | Retrieves `CommoditiesForFutures` property from `FuturesHistoryDataDao` |
| `instance` | `getCommodities` | `(arg0: Set)` | `List` | Retrieves `Commodities` property from `FuturesHistoryDataDao` |
| `instance` | `dispose` | `()` | `void` | Performs dispose operation |
| `instance` | `getChangeDate` | `()` | `Date` | Retrieves `ChangeDate` property from `FuturesHistoryDataDao` |
| `instance` | `getChangeDate` | `(arg0: String)` | `Date` | Retrieves `ChangeDate` property from `FuturesHistoryDataDao` |
| `instance` | `getExchangeForTicker` | `(arg0: String)` | `String` | Retrieves `ExchangeForTicker` property from `FuturesHistoryDataDao` |
| `instance` | `getAliasesForAlias` | `(arg0: Collection)` | `List` | Retrieves `AliasesForAlias` property from `FuturesHistoryDataDao` |
| `instance` | `getAliasesMapForAlias` | `(arg0: Collection)` | `Map` | Retrieves `AliasesMapForAlias` property from `FuturesHistoryDataDao` |
| `instance` | `equals` | `(arg0: Object)` | `boolean` | Performs equals operation |
| `instance` | `toString` | `()` | `String` | Converts/serializes representation via `toString` |
| `instance` | `hashCode` | `()` | `int` | Evaluates boolean predicate `hashCode` on `FuturesHistoryDataDao` |
| `instance` | `getClass` | `()` | `Class` | Retrieves `Class` property from `FuturesHistoryDataDao` |
| `instance` | `notify` | `()` | `void` | Performs notify operation |
| `instance` | `notifyAll` | `()` | `void` | Performs notify all operation |
| `instance` | `wait` | `(arg0: long)` | `void` | Performs wait operation |
| `instance` | `wait` | `(arg0: long, arg1: int)` | `void` | Performs wait operation |
| `instance` | `wait` | `()` | `void` | Performs wait operation |

---

### `StockHistoryDataDao`
- **Full Qualified Name:** `com.strategyquant.datalib.historyData.StockHistoryDataDao`
- **Primary Job / Responsibility:** Time-series price history, OHLCV bar storage, and chart data management (`StockHistoryDataDao`).

#### Fields
| Scope | Field Name | Type |
| :--- | :--- | :--- |
| `static` | `Log` | `Logger` |

#### Methods & Functions
| Modifiers | Method Name | Parameter Signatures | Return Type | Functional Description / Job |
| :--- | :--- | :--- | :--- | :--- |
| `instance` | `getTickerRenamed` | `()` | `Map` | Retrieves `TickerRenamed` property from `StockHistoryDataDao` |
| `instance` | `dispose` | `()` | `void` | Performs dispose operation |
| `instance` | `getTicker` | `(arg0: String)` | `TickerDto` | Retrieves `Ticker` property from `StockHistoryDataDao` |
| `instance` | `getTicker` | `(arg0: Long)` | `TickerDto` | Retrieves `Ticker` property from `StockHistoryDataDao` |
| `instance` | `getTicker` | `(arg0: String, arg1: Long)` | `TickerDto` | Retrieves `Ticker` property from `StockHistoryDataDao` |
| `instance` | `getTicker` | `(arg0: String, arg1: String)` | `TickerDto` | Retrieves `Ticker` property from `StockHistoryDataDao` |
| `instance` | `getChangeDate` | `()` | `Date` | Retrieves `ChangeDate` property from `StockHistoryDataDao` |
| `instance` | `getChangeDate` | `(arg0: String)` | `Date` | Retrieves `ChangeDate` property from `StockHistoryDataDao` |
| `instance` | `createIndexes` | `()` | `void` | Instantiates/initializes `createIndexes` resource |
| `instance` | `getAllMarkets` | `()` | `List` | Retrieves `AllMarkets` property from `StockHistoryDataDao` |
| `instance` | `getTickers` | `(arg0: TickerFilterDto)` | `List` | Retrieves `Tickers` property from `StockHistoryDataDao` |
| `instance` | `getTickers` | `(arg0: String, arg1: TickerFilterDto)` | `List` | Retrieves `Tickers` property from `StockHistoryDataDao` |
| `instance` | `getExchangeForTicker` | `(arg0: String)` | `String` | Retrieves `ExchangeForTicker` property from `StockHistoryDataDao` |
| `instance` | `getAliasesForAlias` | `(arg0: Collection)` | `List` | Retrieves `AliasesForAlias` property from `StockHistoryDataDao` |
| `instance` | `getAliasesMapForAlias` | `(arg0: Collection)` | `Map` | Retrieves `AliasesMapForAlias` property from `StockHistoryDataDao` |
| `instance` | `equals` | `(arg0: Object)` | `boolean` | Performs equals operation |
| `instance` | `toString` | `()` | `String` | Converts/serializes representation via `toString` |
| `instance` | `hashCode` | `()` | `int` | Evaluates boolean predicate `hashCode` on `StockHistoryDataDao` |
| `instance` | `getClass` | `()` | `Class` | Retrieves `Class` property from `StockHistoryDataDao` |
| `instance` | `notify` | `()` | `void` | Performs notify operation |
| `instance` | `notifyAll` | `()` | `void` | Performs notify all operation |
| `instance` | `wait` | `(arg0: long)` | `void` | Performs wait operation |
| `instance` | `wait` | `(arg0: long, arg1: int)` | `void` | Performs wait operation |
| `instance` | `wait` | `()` | `void` | Performs wait operation |

---

### `TickerFilterDto`
- **Full Qualified Name:** `com.strategyquant.datalib.historyData.TickerFilterDto`
- **Primary Job / Responsibility:** Time-series price history, OHLCV bar storage, and chart data management (`TickerFilterDto`).

#### Methods & Functions
| Modifiers | Method Name | Parameter Signatures | Return Type | Functional Description / Job |
| :--- | :--- | :--- | :--- | :--- |
| `instance` | `setNames` | `(arg0: String[])` | `void` | Sets `Names` configuration/state on `TickerFilterDto` |
| `instance` | `setSearchInTicker` | `(arg0: boolean)` | `void` | Sets `SearchInTicker` configuration/state on `TickerFilterDto` |
| `instance` | `setExactMatch` | `(arg0: boolean)` | `void` | Sets `ExactMatch` configuration/state on `TickerFilterDto` |
| `instance` | `getMarketId` | `()` | `Long` | Retrieves `MarketId` property from `TickerFilterDto` |
| `instance` | `getNames` | `()` | `String[]` | Retrieves `Names` property from `TickerFilterDto` |
| `instance` | `isExactMatch` | `()` | `boolean` | Evaluates boolean predicate `isExactMatch` on `TickerFilterDto` |
| `instance` | `isSearchInTicker` | `()` | `boolean` | Evaluates boolean predicate `isSearchInTicker` on `TickerFilterDto` |
| `instance` | `isSearchInName` | `()` | `boolean` | Evaluates boolean predicate `isSearchInName` on `TickerFilterDto` |
| `instance` | `setSearchInName` | `(arg0: boolean)` | `void` | Sets `SearchInName` configuration/state on `TickerFilterDto` |
| `instance` | `setOnlyContFutures` | `(arg0: boolean)` | `void` | Sets `OnlyContFutures` configuration/state on `TickerFilterDto` |
| `instance` | `isOnlyContFutures` | `()` | `boolean` | Evaluates boolean predicate `isOnlyContFutures` on `TickerFilterDto` |
| `instance` | `setMarketId` | `(arg0: Long)` | `void` | Sets `MarketId` configuration/state on `TickerFilterDto` |
| `instance` | `equals` | `(arg0: Object)` | `boolean` | Performs equals operation |
| `instance` | `toString` | `()` | `String` | Converts/serializes representation via `toString` |
| `instance` | `hashCode` | `()` | `int` | Evaluates boolean predicate `hashCode` on `TickerFilterDto` |
| `instance` | `getClass` | `()` | `Class` | Retrieves `Class` property from `TickerFilterDto` |
| `instance` | `notify` | `()` | `void` | Performs notify operation |
| `instance` | `notifyAll` | `()` | `void` | Performs notify all operation |
| `instance` | `wait` | `(arg0: long)` | `void` | Performs wait operation |
| `instance` | `wait` | `(arg0: long, arg1: int)` | `void` | Performs wait operation |
| `instance` | `wait` | `()` | `void` | Performs wait operation |

---

### `TickerRenameInfo`
- **Full Qualified Name:** `com.strategyquant.datalib.historyData.TickerRenameInfo`
- **Primary Job / Responsibility:** Time-series price history, OHLCV bar storage, and chart data management (`TickerRenameInfo`).

#### Methods & Functions
| Modifiers | Method Name | Parameter Signatures | Return Type | Functional Description / Job |
| :--- | :--- | :--- | :--- | :--- |
| `instance` | `toString` | `()` | `String` | Converts/serializes representation via `toString` |
| `instance` | `setDate` | `(arg0: Long)` | `void` | Sets `Date` configuration/state on `TickerRenameInfo` |
| `instance` | `getDate` | `()` | `Long` | Retrieves `Date` property from `TickerRenameInfo` |
| `instance` | `getTickerTo` | `()` | `String` | Retrieves `TickerTo` property from `TickerRenameInfo` |
| `instance` | `setTickerFrom` | `(arg0: String)` | `void` | Sets `TickerFrom` configuration/state on `TickerRenameInfo` |
| `instance` | `setTickerTo` | `(arg0: String)` | `void` | Sets `TickerTo` configuration/state on `TickerRenameInfo` |
| `instance` | `getTickerFrom` | `()` | `String` | Retrieves `TickerFrom` property from `TickerRenameInfo` |
| `instance` | `equals` | `(arg0: Object)` | `boolean` | Performs equals operation |
| `instance` | `hashCode` | `()` | `int` | Evaluates boolean predicate `hashCode` on `TickerRenameInfo` |
| `instance` | `getClass` | `()` | `Class` | Retrieves `Class` property from `TickerRenameInfo` |
| `instance` | `notify` | `()` | `void` | Performs notify operation |
| `instance` | `notifyAll` | `()` | `void` | Performs notify all operation |
| `instance` | `wait` | `(arg0: long)` | `void` | Performs wait operation |
| `instance` | `wait` | `(arg0: long, arg1: int)` | `void` | Performs wait operation |
| `instance` | `wait` | `()` | `void` | Performs wait operation |

---

### `AliasDto`
- **Full Qualified Name:** `com.strategyquant.datalib.historyData.dto.AliasDto`
- **Primary Job / Responsibility:** Time-series price history, OHLCV bar storage, and chart data management (`AliasDto`).

#### Methods & Functions
| Modifiers | Method Name | Parameter Signatures | Return Type | Functional Description / Job |
| :--- | :--- | :--- | :--- | :--- |
| `instance` | `setOriginal` | `(arg0: String)` | `void` | Sets `Original` configuration/state on `AliasDto` |
| `instance` | `setAlias` | `(arg0: String)` | `void` | Sets `Alias` configuration/state on `AliasDto` |
| `instance` | `getOriginal` | `()` | `String` | Retrieves `Original` property from `AliasDto` |
| `instance` | `getAlias` | `()` | `String` | Retrieves `Alias` property from `AliasDto` |
| `instance` | `equals` | `(arg0: Object)` | `boolean` | Performs equals operation |
| `instance` | `toString` | `()` | `String` | Converts/serializes representation via `toString` |
| `instance` | `hashCode` | `()` | `int` | Evaluates boolean predicate `hashCode` on `AliasDto` |
| `instance` | `getClass` | `()` | `Class` | Retrieves `Class` property from `AliasDto` |
| `instance` | `notify` | `()` | `void` | Performs notify operation |
| `instance` | `notifyAll` | `()` | `void` | Performs notify all operation |
| `instance` | `wait` | `(arg0: long)` | `void` | Performs wait operation |
| `instance` | `wait` | `(arg0: long, arg1: int)` | `void` | Performs wait operation |
| `instance` | `wait` | `()` | `void` | Performs wait operation |

---

### `CommodityDto`
- **Full Qualified Name:** `com.strategyquant.datalib.historyData.dto.CommodityDto`
- **Primary Job / Responsibility:** Time-series price history, OHLCV bar storage, and chart data management (`CommodityDto`).

#### Methods & Functions
| Modifiers | Method Name | Parameter Signatures | Return Type | Functional Description / Job |
| :--- | :--- | :--- | :--- | :--- |
| `instance` | `getName` | `()` | `String` | Retrieves `Name` property from `CommodityDto` |
| `instance` | `setName` | `(arg0: String)` | `void` | Sets `Name` configuration/state on `CommodityDto` |
| `instance` | `getId` | `()` | `Long` | Retrieves `Id` property from `CommodityDto` |
| `instance` | `getCode` | `()` | `String` | Retrieves `Code` property from `CommodityDto` |
| `instance` | `setId` | `(arg0: Long)` | `void` | Sets `Id` configuration/state on `CommodityDto` |
| `instance` | `getPointValue` | `()` | `BigDecimal` | Retrieves `PointValue` property from `CommodityDto` |
| `instance` | `setPointValue` | `(arg0: BigDecimal)` | `void` | Sets `PointValue` configuration/state on `CommodityDto` |
| `instance` | `getTickSize` | `()` | `BigDecimal` | Retrieves `TickSize` property from `CommodityDto` |
| `instance` | `setTickSize` | `(arg0: BigDecimal)` | `void` | Sets `TickSize` configuration/state on `CommodityDto` |
| `instance` | `getTickStep` | `()` | `BigDecimal` | Retrieves `TickStep` property from `CommodityDto` |
| `instance` | `setTickStep` | `(arg0: BigDecimal)` | `void` | Sets `TickStep` configuration/state on `CommodityDto` |
| `instance` | `getDefaultSpread` | `()` | `BigDecimal` | Retrieves `DefaultSpread` property from `CommodityDto` |
| `instance` | `setDefaultSpread` | `(arg0: BigDecimal)` | `void` | Sets `DefaultSpread` configuration/state on `CommodityDto` |
| `instance` | `getOrderSizeStep` | `()` | `BigDecimal` | Retrieves `OrderSizeStep` property from `CommodityDto` |
| `instance` | `getCommision` | `()` | `BigDecimal` | Retrieves `Commision` property from `CommodityDto` |
| `instance` | `setCommision` | `(arg0: BigDecimal)` | `void` | Sets `Commision` configuration/state on `CommodityDto` |
| `instance` | `getOrderSizeMulti` | `()` | `BigDecimal` | Retrieves `OrderSizeMulti` property from `CommodityDto` |
| `instance` | `setCode` | `(arg0: String)` | `void` | Sets `Code` configuration/state on `CommodityDto` |
| `instance` | `setOrderSizeMulti` | `(arg0: BigDecimal)` | `void` | Sets `OrderSizeMulti` configuration/state on `CommodityDto` |
| `instance` | `setOrderSizeStep` | `(arg0: BigDecimal)` | `void` | Sets `OrderSizeStep` configuration/state on `CommodityDto` |
| `instance` | `equals` | `(arg0: Object)` | `boolean` | Performs equals operation |
| `instance` | `toString` | `()` | `String` | Converts/serializes representation via `toString` |
| `instance` | `hashCode` | `()` | `int` | Evaluates boolean predicate `hashCode` on `CommodityDto` |
| `instance` | `getClass` | `()` | `Class` | Retrieves `Class` property from `CommodityDto` |
| `instance` | `notify` | `()` | `void` | Performs notify operation |
| `instance` | `notifyAll` | `()` | `void` | Performs notify all operation |
| `instance` | `wait` | `(arg0: long)` | `void` | Performs wait operation |
| `instance` | `wait` | `(arg0: long, arg1: int)` | `void` | Performs wait operation |
| `instance` | `wait` | `()` | `void` | Performs wait operation |

---

### `TickerDto`
- **Full Qualified Name:** `com.strategyquant.datalib.historyData.dto.TickerDto`
- **Primary Job / Responsibility:** Time-series price history, OHLCV bar storage, and chart data management (`TickerDto`).

#### Methods & Functions
| Modifiers | Method Name | Parameter Signatures | Return Type | Functional Description / Job |
| :--- | :--- | :--- | :--- | :--- |
| `instance` | `getName` | `()` | `String` | Retrieves `Name` property from `TickerDto` |
| `instance` | `setName` | `(arg0: String)` | `void` | Sets `Name` configuration/state on `TickerDto` |
| `instance` | `getId` | `()` | `Long` | Retrieves `Id` property from `TickerDto` |
| `instance` | `getType` | `()` | `String` | Retrieves `Type` property from `TickerDto` |
| `instance` | `setType` | `(arg0: String)` | `void` | Sets `Type` configuration/state on `TickerDto` |
| `instance` | `getDateFrom` | `()` | `Date` | Retrieves `DateFrom` property from `TickerDto` |
| `instance` | `getDateTo` | `()` | `Date` | Retrieves `DateTo` property from `TickerDto` |
| `instance` | `getTicker` | `()` | `String` | Retrieves `Ticker` property from `TickerDto` |
| `instance` | `getMarketName` | `()` | `String` | Retrieves `MarketName` property from `TickerDto` |
| `instance` | `setId` | `(arg0: Long)` | `void` | Sets `Id` configuration/state on `TickerDto` |
| `instance` | `getAliasTickerId` | `()` | `Long` | Retrieves `AliasTickerId` property from `TickerDto` |
| `instance` | `isEod` | `()` | `boolean` | Evaluates boolean predicate `isEod` on `TickerDto` |
| `instance` | `setDateFrom` | `(arg0: Date)` | `void` | Sets `DateFrom` configuration/state on `TickerDto` |
| `instance` | `setTicker` | `(arg0: String)` | `void` | Sets `Ticker` configuration/state on `TickerDto` |
| `instance` | `getMarketId` | `()` | `Long` | Retrieves `MarketId` property from `TickerDto` |
| `instance` | `setDateTo` | `(arg0: Date)` | `void` | Sets `DateTo` configuration/state on `TickerDto` |
| `instance` | `getCommodityId` | `()` | `Long` | Retrieves `CommodityId` property from `TickerDto` |
| `instance` | `setMarketId` | `(arg0: Long)` | `void` | Sets `MarketId` configuration/state on `TickerDto` |
| `instance` | `setMarketName` | `(arg0: String)` | `void` | Sets `MarketName` configuration/state on `TickerDto` |
| `instance` | `setCommodityId` | `(arg0: Long)` | `void` | Sets `CommodityId` configuration/state on `TickerDto` |
| `instance` | `setEod` | `(arg0: boolean)` | `void` | Sets `Eod` configuration/state on `TickerDto` |
| `instance` | `setAliasTickerId` | `(arg0: Long)` | `void` | Sets `AliasTickerId` configuration/state on `TickerDto` |
| `instance` | `equals` | `(arg0: Object)` | `boolean` | Performs equals operation |
| `instance` | `toString` | `()` | `String` | Converts/serializes representation via `toString` |
| `instance` | `hashCode` | `()` | `int` | Evaluates boolean predicate `hashCode` on `TickerDto` |
| `instance` | `getClass` | `()` | `Class` | Retrieves `Class` property from `TickerDto` |
| `instance` | `notify` | `()` | `void` | Performs notify operation |
| `instance` | `notifyAll` | `()` | `void` | Performs notify all operation |
| `instance` | `wait` | `(arg0: long)` | `void` | Performs wait operation |
| `instance` | `wait` | `(arg0: long, arg1: int)` | `void` | Performs wait operation |
| `instance` | `wait` | `()` | `void` | Performs wait operation |

---

### `TickerKind`
- **Full Qualified Name:** `com.strategyquant.datalib.historyData.dto.TickerKind`
- **Primary Job / Responsibility:** Time-series price history, OHLCV bar storage, and chart data management (`TickerKind`).

#### Fields
| Scope | Field Name | Type |
| :--- | :--- | :--- |
| `static` | `FUTURES` | `TickerKind` |
| `static` | `STOCK` | `TickerKind` |

#### Methods & Functions
| Modifiers | Method Name | Parameter Signatures | Return Type | Functional Description / Job |
| :--- | :--- | :--- | :--- | :--- |
| `instance` | `getId` | `()` | `Long` | Retrieves `Id` property from `TickerKind` |
| `instance` | `forDownload` | `()` | `String` | Performs for download operation |
| `instance` | `name` | `()` | `String` | Performs name operation |
| `instance` | `equals` | `(arg0: Object)` | `boolean` | Performs equals operation |
| `instance` | `toString` | `()` | `String` | Converts/serializes representation via `toString` |
| `instance` | `hashCode` | `()` | `int` | Evaluates boolean predicate `hashCode` on `TickerKind` |
| `instance` | `compareTo` | `(arg0: Object)` | `int` | Performs compare to operation |
| `instance` | `compareTo` | `(arg0: Enum)` | `int` | Performs compare to operation |
| `instance` | `describeConstable` | `()` | `Optional` | Performs describe constable operation |
| `instance` | `getDeclaringClass` | `()` | `Class` | Retrieves `DeclaringClass` property from `TickerKind` |
| `instance` | `ordinal` | `()` | `int` | Performs ordinal operation |
| `instance` | `getClass` | `()` | `Class` | Retrieves `Class` property from `TickerKind` |
| `instance` | `notify` | `()` | `void` | Performs notify operation |
| `instance` | `notifyAll` | `()` | `void` | Performs notify all operation |
| `instance` | `wait` | `(arg0: long)` | `void` | Performs wait operation |
| `instance` | `wait` | `(arg0: long, arg1: int)` | `void` | Performs wait operation |
| `instance` | `wait` | `()` | `void` | Performs wait operation |
| `static` | `values` | `()` | `TickerKind[]` | Performs values operation |
| `static` | `valueOf` | `(arg0: String)` | `Enum` | Performs value of operation |
| `static` | `valueOf` | `(arg0: Class, arg1: String)` | `Enum` | Performs value of operation |
| `static` | `forId` | `(arg0: Long)` | `TickerKind` | Performs for id operation |
| `static` | `tryEvalTickerFromName` | `(arg0: String)` | `TickerKind` | Performs try eval ticker from name operation |

---

## Subsystem: `indicators`

### `CustomIndicatorFileImporter`
- **Full Qualified Name:** `com.strategyquant.datalib.indicators.CustomIndicatorFileImporter`
- **Primary Job / Responsibility:** Market data abstraction and time-series container (`CustomIndicatorFileImporter`).

#### Methods & Functions
| Modifiers | Method Name | Parameter Signatures | Return Type | Functional Description / Job |
| :--- | :--- | :--- | :--- | :--- |
| `instance` | `load` | `(arg0: File)` | `String` | Performs load operation |
| `instance` | `equals` | `(arg0: Object)` | `boolean` | Performs equals operation |
| `instance` | `toString` | `()` | `String` | Converts/serializes representation via `toString` |
| `instance` | `hashCode` | `()` | `int` | Evaluates boolean predicate `hashCode` on `CustomIndicatorFileImporter` |
| `instance` | `getClass` | `()` | `Class` | Retrieves `Class` property from `CustomIndicatorFileImporter` |
| `instance` | `notify` | `()` | `void` | Performs notify operation |
| `instance` | `notifyAll` | `()` | `void` | Performs notify all operation |
| `instance` | `wait` | `(arg0: long)` | `void` | Performs wait operation |
| `instance` | `wait` | `(arg0: long, arg1: int)` | `void` | Performs wait operation |
| `instance` | `wait` | `()` | `void` | Performs wait operation |

---

### `SCustomIndicator`
- **Full Qualified Name:** `com.strategyquant.datalib.indicators.SCustomIndicator`
- **Primary Job / Responsibility:** Market data abstraction and time-series container (`SCustomIndicator`).

#### Fields
| Scope | Field Name | Type |
| :--- | :--- | :--- |
| `instance` | `fileName` | `String` |
| `instance` | `longName` | `String` |
| `instance` | `outputList` | `ArrayList` |
| `instance` | `parameterList` | `ArrayList` |
| `instance` | `returnType` | `int` |
| `instance` | `shortName` | `String` |

#### Methods & Functions
| Modifiers | Method Name | Parameter Signatures | Return Type | Functional Description / Job |
| :--- | :--- | :--- | :--- | :--- |
| `instance` | `toString` | `()` | `String` | Converts/serializes representation via `toString` |
| `instance` | `equals` | `(arg0: Object)` | `boolean` | Performs equals operation |
| `instance` | `hashCode` | `()` | `int` | Evaluates boolean predicate `hashCode` on `SCustomIndicator` |
| `instance` | `getClass` | `()` | `Class` | Retrieves `Class` property from `SCustomIndicator` |
| `instance` | `notify` | `()` | `void` | Performs notify operation |
| `instance` | `notifyAll` | `()` | `void` | Performs notify all operation |
| `instance` | `wait` | `(arg0: long)` | `void` | Performs wait operation |
| `instance` | `wait` | `(arg0: long, arg1: int)` | `void` | Performs wait operation |
| `instance` | `wait` | `()` | `void` | Performs wait operation |

---

### `SCustomIndicatorFileParser`
- **Full Qualified Name:** `com.strategyquant.datalib.indicators.SCustomIndicatorFileParser`
- **Primary Job / Responsibility:** Market data abstraction and time-series container (`SCustomIndicatorFileParser`).

#### Methods & Functions
| Modifiers | Method Name | Parameter Signatures | Return Type | Functional Description / Job |
| :--- | :--- | :--- | :--- | :--- |
| `instance` | `equals` | `(arg0: Object)` | `boolean` | Performs equals operation |
| `instance` | `toString` | `()` | `String` | Converts/serializes representation via `toString` |
| `instance` | `hashCode` | `()` | `int` | Evaluates boolean predicate `hashCode` on `SCustomIndicatorFileParser` |
| `instance` | `getClass` | `()` | `Class` | Retrieves `Class` property from `SCustomIndicatorFileParser` |
| `instance` | `notify` | `()` | `void` | Performs notify operation |
| `instance` | `notifyAll` | `()` | `void` | Performs notify all operation |
| `instance` | `wait` | `(arg0: long)` | `void` | Performs wait operation |
| `instance` | `wait` | `(arg0: long, arg1: int)` | `void` | Performs wait operation |
| `instance` | `wait` | `()` | `void` | Performs wait operation |
| `static` | `parse` | `(arg0: File)` | `SCustomIndicator` | Converts/serializes representation via `parse` |

---

### `SParameter`
- **Full Qualified Name:** `com.strategyquant.datalib.indicators.SParameter`
- **Primary Job / Responsibility:** Market data abstraction and time-series container (`SParameter`).

#### Fields
| Scope | Field Name | Type |
| :--- | :--- | :--- |
| `instance` | `index` | `int` |
| `instance` | `name` | `String` |
| `instance` | `type` | `String` |
| `instance` | `value` | `String` |

#### Methods & Functions
| Modifiers | Method Name | Parameter Signatures | Return Type | Functional Description / Job |
| :--- | :--- | :--- | :--- | :--- |
| `instance` | `toString` | `()` | `String` | Converts/serializes representation via `toString` |
| `instance` | `equals` | `(arg0: Object)` | `boolean` | Performs equals operation |
| `instance` | `hashCode` | `()` | `int` | Evaluates boolean predicate `hashCode` on `SParameter` |
| `instance` | `getClass` | `()` | `Class` | Retrieves `Class` property from `SParameter` |
| `instance` | `notify` | `()` | `void` | Performs notify operation |
| `instance` | `notifyAll` | `()` | `void` | Performs notify all operation |
| `instance` | `wait` | `(arg0: long)` | `void` | Performs wait operation |
| `instance` | `wait` | `(arg0: long, arg1: int)` | `void` | Performs wait operation |
| `instance` | `wait` | `()` | `void` | Performs wait operation |

---

### `SParametersParser`
- **Full Qualified Name:** `com.strategyquant.datalib.indicators.SParametersParser`
- **Primary Job / Responsibility:** Market data abstraction and time-series container (`SParametersParser`).

#### Fields
| Scope | Field Name | Type |
| :--- | :--- | :--- |
| `instance` | `list` | `ArrayList` |
| `instance` | `type` | `String` |

#### Methods & Functions
| Modifiers | Method Name | Parameter Signatures | Return Type | Functional Description / Job |
| :--- | :--- | :--- | :--- | :--- |
| `instance` | `parse` | `()` | `void` | Converts/serializes representation via `parse` |
| `instance` | `equals` | `(arg0: Object)` | `boolean` | Performs equals operation |
| `instance` | `toString` | `()` | `String` | Converts/serializes representation via `toString` |
| `instance` | `hashCode` | `()` | `int` | Evaluates boolean predicate `hashCode` on `SParametersParser` |
| `instance` | `getClass` | `()` | `Class` | Retrieves `Class` property from `SParametersParser` |
| `instance` | `notify` | `()` | `void` | Performs notify operation |
| `instance` | `notifyAll` | `()` | `void` | Performs notify all operation |
| `instance` | `wait` | `(arg0: long)` | `void` | Performs wait operation |
| `instance` | `wait` | `(arg0: long, arg1: int)` | `void` | Performs wait operation |
| `instance` | `wait` | `()` | `void` | Performs wait operation |

---

### `InputParameter`
- **Full Qualified Name:** `com.strategyquant.datalib.indicators.SParametersParser.InputParameter`
- **Primary Job / Responsibility:** Market data abstraction and time-series container (`InputParameter`).

#### Fields
| Scope | Field Name | Type |
| :--- | :--- | :--- |
| `instance` | `name` | `String` |
| `instance` | `value` | `String` |

#### Methods & Functions
| Modifiers | Method Name | Parameter Signatures | Return Type | Functional Description / Job |
| :--- | :--- | :--- | :--- | :--- |
| `instance` | `equals` | `(arg0: Object)` | `boolean` | Performs equals operation |
| `instance` | `toString` | `()` | `String` | Converts/serializes representation via `toString` |
| `instance` | `hashCode` | `()` | `int` | Evaluates boolean predicate `hashCode` on `InputParameter` |
| `instance` | `getClass` | `()` | `Class` | Retrieves `Class` property from `InputParameter` |
| `instance` | `notify` | `()` | `void` | Performs notify operation |
| `instance` | `notifyAll` | `()` | `void` | Performs notify all operation |
| `instance` | `wait` | `(arg0: long)` | `void` | Performs wait operation |
| `instance` | `wait` | `(arg0: long, arg1: int)` | `void` | Performs wait operation |
| `instance` | `wait` | `()` | `void` | Performs wait operation |

---

## Subsystem: `instrument`

### `AliasManager`
- **Full Qualified Name:** `com.strategyquant.datalib.instrument.AliasManager`
- **Primary Job / Responsibility:** Symbol specifications, pip values, margins, and contract specifications (`AliasManager`).

#### Methods & Functions
| Modifiers | Method Name | Parameter Signatures | Return Type | Functional Description / Job |
| :--- | :--- | :--- | :--- | :--- |
| `instance` | `equals` | `(arg0: Object)` | `boolean` | Performs equals operation |
| `instance` | `toString` | `()` | `String` | Converts/serializes representation via `toString` |
| `instance` | `hashCode` | `()` | `int` | Evaluates boolean predicate `hashCode` on `AliasManager` |
| `instance` | `getClass` | `()` | `Class` | Retrieves `Class` property from `AliasManager` |
| `instance` | `notify` | `()` | `void` | Performs notify operation |
| `instance` | `notifyAll` | `()` | `void` | Performs notify all operation |
| `instance` | `wait` | `(arg0: long)` | `void` | Performs wait operation |
| `instance` | `wait` | `(arg0: long, arg1: int)` | `void` | Performs wait operation |
| `instance` | `wait` | `()` | `void` | Performs wait operation |
| `static` | `getAliases` | `()` | `ArrayList` | Retrieves `Aliases` property from `AliasManager` |
| `static` | `getAlias` | `(arg0: String)` | `InstrumentAlias` | Retrieves `Alias` property from `AliasManager` |
| `static` | `checkAliasExists` | `(arg0: String)` | `boolean` | Performs check alias exists operation |
| `static` | `getAliasInstrument` | `(arg0: String)` | `String` | Retrieves `AliasInstrument` property from `AliasManager` |
| `static` | `listInstrumentAliases` | `(arg0: String)` | `ArrayList` | Performs list instrument aliases operation |
| `static` | `removeInstrumentAliases` | `(arg0: String)` | `void` | Removes/resets elements via `removeInstrumentAliases` |
| `static` | `addAlias` | `(arg0: String, arg1: String, arg2: String)` | `void` | Appends/registers element via `addAlias` |
| `static` | `updateAlias` | `(arg0: String, arg1: String, arg2: String)` | `void` | Performs update alias operation |
| `static` | `removeAlias` | `(arg0: String)` | `void` | Removes/resets elements via `removeAlias` |

---

### `InstrumentAlias`
- **Full Qualified Name:** `com.strategyquant.datalib.instrument.InstrumentAlias`
- **Primary Job / Responsibility:** Symbol specifications, pip values, margins, and contract specifications (`InstrumentAlias`).

#### Fields
| Scope | Field Name | Type |
| :--- | :--- | :--- |
| `instance` | `alias` | `String` |
| `instance` | `description` | `String` |
| `instance` | `instrument` | `String` |

#### Methods & Functions
| Modifiers | Method Name | Parameter Signatures | Return Type | Functional Description / Job |
| :--- | :--- | :--- | :--- | :--- |
| `instance` | `equals` | `(arg0: Object)` | `boolean` | Performs equals operation |
| `instance` | `toString` | `()` | `String` | Converts/serializes representation via `toString` |
| `instance` | `hashCode` | `()` | `int` | Evaluates boolean predicate `hashCode` on `InstrumentAlias` |
| `instance` | `getClass` | `()` | `Class` | Retrieves `Class` property from `InstrumentAlias` |
| `instance` | `notify` | `()` | `void` | Performs notify operation |
| `instance` | `notifyAll` | `()` | `void` | Performs notify all operation |
| `instance` | `wait` | `(arg0: long)` | `void` | Performs wait operation |
| `instance` | `wait` | `(arg0: long, arg1: int)` | `void` | Performs wait operation |
| `instance` | `wait` | `()` | `void` | Performs wait operation |

---

### `InstrumentManager`
- **Full Qualified Name:** `com.strategyquant.datalib.instrument.InstrumentManager`
- **Primary Job / Responsibility:** Symbol specifications, pip values, margins, and contract specifications (`InstrumentManager`).

#### Fields
| Scope | Field Name | Type |
| :--- | :--- | :--- |
| `static` | `Log` | `Logger` |
| `static` | `defaultCommissionsMethod` | `String` |

#### Methods & Functions
| Modifiers | Method Name | Parameter Signatures | Return Type | Functional Description / Job |
| :--- | :--- | :--- | :--- | :--- |
| `instance` | `initDatabase` | `()` | `void` | Instantiates/initializes `initDatabase` resource |
| `instance` | `_getInstrumentInfo` | `(arg0: String)` | `InstrumentInfo` | Performs get instrument info operation |
| `instance` | `close` | `(arg0: ResultSet)` | `void` | Performs close operation |
| `instance` | `close` | `(arg0: Statement)` | `void` | Performs close operation |
| `instance` | `close` | `(arg0: Connection)` | `void` | Performs close operation |
| `instance` | `getConnection` | `()` | `Connection` | Retrieves `Connection` property from `InstrumentManager` |
| `instance` | `sqlCheckRecordExists` | `(arg0: Connection, arg1: String)` | `boolean` | Performs sql check record exists operation |
| `instance` | `sqlCommand` | `(arg0: Connection, arg1: PreparedStatement)` | `void` | Performs sql command operation |
| `instance` | `sqlCommand` | `(arg0: String)` | `void` | Performs sql command operation |
| `instance` | `sqlCommand` | `(arg0: Connection, arg1: String)` | `void` | Performs sql command operation |
| `instance` | `sqlInsertReturnAutoId` | `(arg0: Connection, arg1: PreparedStatement)` | `int` | Performs sql insert return auto id operation |
| `instance` | `sqlInsertReturnAutoId` | `(arg0: Connection, arg1: String)` | `int` | Performs sql insert return auto id operation |
| `instance` | `_getDirectory` | `()` | `String` | Performs get directory operation |
| `instance` | `getDbPath` | `()` | `String` | Retrieves `DbPath` property from `InstrumentManager` |
| `instance` | `isDbExist` | `()` | `boolean` | Evaluates boolean predicate `isDbExist` on `InstrumentManager` |
| `instance` | `columnExists` | `(arg0: String, arg1: String)` | `boolean` | Performs column exists operation |
| `instance` | `tableExists` | `(arg0: String)` | `boolean` | Performs table exists operation |
| `instance` | `equals` | `(arg0: Object)` | `boolean` | Performs equals operation |
| `instance` | `toString` | `()` | `String` | Converts/serializes representation via `toString` |
| `instance` | `hashCode` | `()` | `int` | Evaluates boolean predicate `hashCode` on `InstrumentManager` |
| `instance` | `getClass` | `()` | `Class` | Retrieves `Class` property from `InstrumentManager` |
| `instance` | `notify` | `()` | `void` | Performs notify operation |
| `instance` | `notifyAll` | `()` | `void` | Performs notify all operation |
| `instance` | `wait` | `(arg0: long)` | `void` | Performs wait operation |
| `instance` | `wait` | `(arg0: long, arg1: int)` | `void` | Performs wait operation |
| `instance` | `wait` | `()` | `void` | Performs wait operation |
| `static` | `list` | `()` | `ArrayList` | Performs list operation |
| `static` | `init` | `(arg0: String)` | `void` | Instantiates/initializes `init` resource |
| `static` | `getInstrumentInfo` | `(arg0: String)` | `InstrumentInfo` | Retrieves `InstrumentInfo` property from `InstrumentManager` |
| `static` | `checkInstrumentExists` | `(arg0: String)` | `boolean` | Performs check instrument exists operation |
| `static` | `checkInstrumentExists` | `(arg0: String, arg1: boolean)` | `boolean` | Performs check instrument exists operation |
| `static` | `addInstrument` | `(arg0: String, arg1: String, arg2: double, arg3: double, arg4: double, arg5: double, arg6: double, arg7: String, arg8: byte, arg9: String, arg10: String, arg11: String, arg12: String, arg13: double, arg14: double)` | `void` | Appends/registers element via `addInstrument` |
| `static` | `addInstrument` | `(arg0: InstrumentInfo)` | `void` | Appends/registers element via `addInstrument` |
| `static` | `addInstrument` | `(arg0: String, arg1: int, arg2: String, arg3: double, arg4: double, arg5: double, arg6: double, arg7: double, arg8: double, arg9: String, arg10: byte, arg11: String, arg12: String, arg13: String, arg14: String, arg15: double, arg16: double)` | `void` | Appends/registers element via `addInstrument` |
| `static` | `addInstrument` | `(arg0: String, arg1: int, arg2: String, arg3: double, arg4: double, arg5: double, arg6: double, arg7: double, arg8: double, arg9: String, arg10: byte, arg11: String, arg12: String, arg13: String, arg14: String, arg15: double, arg16: double, arg17: String)` | `void` | Appends/registers element via `addInstrument` |
| `static` | `addInstrument` | `(arg0: String, arg1: String, arg2: double, arg3: double, arg4: double, arg5: double, arg6: double, arg7: String, arg8: byte)` | `void` | Appends/registers element via `addInstrument` |
| `static` | `updateInstrument` | `(arg0: String, arg1: String, arg2: double, arg3: double, arg4: double, arg5: double, arg6: double, arg7: double, arg8: String, arg9: byte, arg10: String, arg11: String, arg12: String, arg13: String, arg14: double, arg15: double)` | `void` | Performs update instrument operation |
| `static` | `updateInstrument` | `(arg0: String, arg1: String, arg2: double, arg3: double, arg4: double, arg5: double, arg6: double, arg7: double, arg8: String, arg9: byte, arg10: String, arg11: String, arg12: String, arg13: String, arg14: double, arg15: double, arg16: String)` | `void` | Performs update instrument operation |
| `static` | `updateInstrument` | `(arg0: InstrumentInfo)` | `void` | Performs update instrument operation |
| `static` | `getExchanges` | `()` | `ArrayList` | Retrieves `Exchanges` property from `InstrumentManager` |
| `static` | `removeInstrument` | `(arg0: String)` | `void` | Removes/resets elements via `removeInstrument` |
| `static` | `getCountries` | `()` | `ArrayList` | Retrieves `Countries` property from `InstrumentManager` |
| `static` | `getSectors` | `()` | `ArrayList` | Retrieves `Sectors` property from `InstrumentManager` |
| `static` | `updateDataType` | `(arg0: String, arg1: byte)` | `void` | Performs update data type operation |
| `static` | `addInstrumentInBatch` | `(arg0: List)` | `void` | Appends/registers element via `addInstrumentInBatch` |
| `static` | `checkAliasExists` | `(arg0: String)` | `boolean` | Performs check alias exists operation |
| `static` | `listInstrumentAliases` | `(arg0: String)` | `ArrayList` | Performs list instrument aliases operation |
| `static` | `removeInstrumentAliases` | `(arg0: String)` | `void` | Removes/resets elements via `removeInstrumentAliases` |
| `static` | `addAlias` | `(arg0: String, arg1: String, arg2: String)` | `void` | Appends/registers element via `addAlias` |
| `static` | `updateAlias` | `(arg0: String, arg1: String, arg2: String)` | `void` | Performs update alias operation |
| `static` | `removeAlias` | `(arg0: String)` | `void` | Removes/resets elements via `removeAlias` |
| `static` | `listAliases` | `()` | `ArrayList` | Performs list aliases operation |
| `static` | `trySaveExchange` | `(arg0: String)` | `boolean` | Performs try save exchange operation |
| `static` | `trySaveCountry` | `(arg0: String)` | `boolean` | Performs try save country operation |
| `static` | `trySaveSector` | `(arg0: String)` | `boolean` | Performs try save sector operation |
| `static` | `findClosestInstrument` | `(arg0: String)` | `InstrumentInfo` | Performs find closest instrument operation |

---

### `InstrumentCache`
- **Full Qualified Name:** `com.strategyquant.datalib.instrument.InstrumentManager.InstrumentCache`
- **Primary Job / Responsibility:** Symbol specifications, pip values, margins, and contract specifications (`InstrumentCache`).

#### Methods & Functions
| Modifiers | Method Name | Parameter Signatures | Return Type | Functional Description / Job |
| :--- | :--- | :--- | :--- | :--- |
| `instance` | `remove` | `(arg0: String)` | `InstrumentInfo` | Removes/resets elements via `remove` |
| `instance` | `get` | `(arg0: String)` | `InstrumentInfo` | Retrieves `` property from `InstrumentCache` |
| `instance` | `store` | `(arg0: String, arg1: Integer, arg2: String, arg3: double, arg4: double, arg5: double, arg6: double, arg7: double, arg8: double, arg9: String, arg10: byte, arg11: String, arg12: String, arg13: String, arg14: String, arg15: double, arg16: double, arg17: String)` | `InstrumentInfo` | Performs store operation |
| `instance` | `store` | `(arg0: InstrumentInfo)` | `InstrumentInfo` | Performs store operation |
| `instance` | `contains` | `(arg0: String)` | `boolean` | Performs contains operation |
| `instance` | `list` | `()` | `ArrayList` | Performs list operation |
| `instance` | `equals` | `(arg0: Object)` | `boolean` | Performs equals operation |
| `instance` | `toString` | `()` | `String` | Converts/serializes representation via `toString` |
| `instance` | `hashCode` | `()` | `int` | Evaluates boolean predicate `hashCode` on `InstrumentCache` |
| `instance` | `getClass` | `()` | `Class` | Retrieves `Class` property from `InstrumentCache` |
| `instance` | `notify` | `()` | `void` | Performs notify operation |
| `instance` | `notifyAll` | `()` | `void` | Performs notify all operation |
| `instance` | `wait` | `(arg0: long)` | `void` | Performs wait operation |
| `instance` | `wait` | `(arg0: long, arg1: int)` | `void` | Performs wait operation |
| `instance` | `wait` | `()` | `void` | Performs wait operation |

---

### `YahooInstruments`
- **Full Qualified Name:** `com.strategyquant.datalib.instrument.imports.YahooInstruments`
- **Primary Job / Responsibility:** Symbol specifications, pip values, margins, and contract specifications (`YahooInstruments`).

#### Fields
| Scope | Field Name | Type |
| :--- | :--- | :--- |
| `static` | `Log` | `Logger` |

#### Methods & Functions
| Modifiers | Method Name | Parameter Signatures | Return Type | Functional Description / Job |
| :--- | :--- | :--- | :--- | :--- |
| `instance` | `importData` | `(arg0: byte, arg1: String)` | `void` | Performs import data operation |
| `instance` | `checkData` | `(arg0: String)` | `void` | Performs check data operation |
| `instance` | `equals` | `(arg0: Object)` | `boolean` | Performs equals operation |
| `instance` | `toString` | `()` | `String` | Converts/serializes representation via `toString` |
| `instance` | `hashCode` | `()` | `int` | Evaluates boolean predicate `hashCode` on `YahooInstruments` |
| `instance` | `getClass` | `()` | `Class` | Retrieves `Class` property from `YahooInstruments` |
| `instance` | `notify` | `()` | `void` | Performs notify operation |
| `instance` | `notifyAll` | `()` | `void` | Performs notify all operation |
| `instance` | `wait` | `(arg0: long)` | `void` | Performs wait operation |
| `instance` | `wait` | `(arg0: long, arg1: int)` | `void` | Performs wait operation |
| `instance` | `wait` | `()` | `void` | Performs wait operation |

---

## Subsystem: `metatrader4`

### `MT4Utils`
- **Full Qualified Name:** `com.strategyquant.datalib.metatrader4.MT4Utils`
- **Primary Job / Responsibility:** Market data abstraction and time-series container (`MT4Utils`).

#### Methods & Functions
| Modifiers | Method Name | Parameter Signatures | Return Type | Functional Description / Job |
| :--- | :--- | :--- | :--- | :--- |
| `instance` | `equals` | `(arg0: Object)` | `boolean` | Performs equals operation |
| `instance` | `toString` | `()` | `String` | Converts/serializes representation via `toString` |
| `instance` | `hashCode` | `()` | `int` | Evaluates boolean predicate `hashCode` on `MT4Utils` |
| `instance` | `getClass` | `()` | `Class` | Retrieves `Class` property from `MT4Utils` |
| `instance` | `notify` | `()` | `void` | Performs notify operation |
| `instance` | `notifyAll` | `()` | `void` | Performs notify all operation |
| `instance` | `wait` | `(arg0: long)` | `void` | Performs wait operation |
| `instance` | `wait` | `(arg0: long, arg1: int)` | `void` | Performs wait operation |
| `instance` | `wait` | `()` | `void` | Performs wait operation |
| `static` | `main` | `(arg0: String[])` | `void` | Performs main operation |
| `static` | `getServerNames` | `(arg0: String)` | `String[]` | Retrieves `ServerNames` property from `MT4Utils` |
| `static` | `getDataFolder` | `(arg0: String)` | `MetaTraderLocation` | Retrieves `DataFolder` property from `MT4Utils` |
| `static` | `getDataFolderFile` | `()` | `File` | Retrieves `DataFolderFile` property from `MT4Utils` |
| `static` | `getTerminalHash` | `(arg0: String)` | `String` | Retrieves `TerminalHash` property from `MT4Utils` |

---

### `MetaTraderLocation`
- **Full Qualified Name:** `com.strategyquant.datalib.metatrader4.MT4Utils.MetaTraderLocation`
- **Primary Job / Responsibility:** Market data abstraction and time-series container (`MetaTraderLocation`).

#### Methods & Functions
| Modifiers | Method Name | Parameter Signatures | Return Type | Functional Description / Job |
| :--- | :--- | :--- | :--- | :--- |
| `instance` | `getServerNames` | `()` | `String[]` | Retrieves `ServerNames` property from `MetaTraderLocation` |
| `instance` | `getDataFolder` | `()` | `String` | Retrieves `DataFolder` property from `MetaTraderLocation` |
| `instance` | `equals` | `(arg0: Object)` | `boolean` | Performs equals operation |
| `instance` | `toString` | `()` | `String` | Converts/serializes representation via `toString` |
| `instance` | `hashCode` | `()` | `int` | Evaluates boolean predicate `hashCode` on `MetaTraderLocation` |
| `instance` | `getClass` | `()` | `Class` | Retrieves `Class` property from `MetaTraderLocation` |
| `instance` | `notify` | `()` | `void` | Performs notify operation |
| `instance` | `notifyAll` | `()` | `void` | Performs notify all operation |
| `instance` | `wait` | `(arg0: long)` | `void` | Performs wait operation |
| `instance` | `wait` | `(arg0: long, arg1: int)` | `void` | Performs wait operation |
| `instance` | `wait` | `()` | `void` | Performs wait operation |

---

### `Mt4Properties`
- **Full Qualified Name:** `com.strategyquant.datalib.metatrader4.Mt4Properties`
- **Primary Job / Responsibility:** Market data abstraction and time-series container (`Mt4Properties`).

#### Methods & Functions
| Modifiers | Method Name | Parameter Signatures | Return Type | Functional Description / Job |
| :--- | :--- | :--- | :--- | :--- |
| `instance` | `toJSON` | `()` | `JSONArray` | Converts/serializes representation via `toJSON` |
| `instance` | `findBySymbol` | `(arg0: String)` | `String` | Performs find by symbol operation |
| `instance` | `equals` | `(arg0: Object)` | `boolean` | Performs equals operation |
| `instance` | `toString` | `()` | `String` | Converts/serializes representation via `toString` |
| `instance` | `hashCode` | `()` | `int` | Evaluates boolean predicate `hashCode` on `Mt4Properties` |
| `instance` | `getClass` | `()` | `Class` | Retrieves `Class` property from `Mt4Properties` |
| `instance` | `notify` | `()` | `void` | Performs notify operation |
| `instance` | `notifyAll` | `()` | `void` | Performs notify all operation |
| `instance` | `wait` | `(arg0: long)` | `void` | Performs wait operation |
| `instance` | `wait` | `(arg0: long, arg1: int)` | `void` | Performs wait operation |
| `instance` | `wait` | `()` | `void` | Performs wait operation |

---

### `Mt4SymbolProperties`
- **Full Qualified Name:** `com.strategyquant.datalib.metatrader4.Mt4SymbolProperties`
- **Primary Job / Responsibility:** Market data abstraction and time-series container (`Mt4SymbolProperties`).

#### Methods & Functions
| Modifiers | Method Name | Parameter Signatures | Return Type | Functional Description / Job |
| :--- | :--- | :--- | :--- | :--- |
| `instance` | `put` | `(arg0: String, arg1: String)` | `void` | Performs put operation |
| `instance` | `toString` | `()` | `String` | Converts/serializes representation via `toString` |
| `instance` | `parse` | `(arg0: String)` | `void` | Converts/serializes representation via `parse` |
| `instance` | `exists` | `(arg0: String)` | `boolean` | Performs exists operation |
| `instance` | `toJSON` | `()` | `JSONArray` | Converts/serializes representation via `toJSON` |
| `instance` | `getDoubleValue` | `(arg0: String)` | `double` | Retrieves `DoubleValue` property from `Mt4SymbolProperties` |
| `instance` | `getIntValue` | `(arg0: String)` | `int` | Retrieves `IntValue` property from `Mt4SymbolProperties` |
| `instance` | `getStrValue` | `(arg0: String)` | `String` | Retrieves `StrValue` property from `Mt4SymbolProperties` |
| `instance` | `equals` | `(arg0: Object)` | `boolean` | Performs equals operation |
| `instance` | `hashCode` | `()` | `int` | Evaluates boolean predicate `hashCode` on `Mt4SymbolProperties` |
| `instance` | `getClass` | `()` | `Class` | Retrieves `Class` property from `Mt4SymbolProperties` |
| `instance` | `notify` | `()` | `void` | Performs notify operation |
| `instance` | `notifyAll` | `()` | `void` | Performs notify all operation |
| `instance` | `wait` | `(arg0: long)` | `void` | Performs wait operation |
| `instance` | `wait` | `(arg0: long, arg1: int)` | `void` | Performs wait operation |
| `instance` | `wait` | `()` | `void` | Performs wait operation |

---

## Subsystem: `session`

### `MonthlyRangeCalculator`
- **Full Qualified Name:** `com.strategyquant.datalib.session.MonthlyRangeCalculator`
- **Primary Job / Responsibility:** Exchange trading session timing, rollover, and weekend holiday definitions (`MonthlyRangeCalculator`).

#### Methods & Functions
| Modifiers | Method Name | Parameter Signatures | Return Type | Functional Description / Job |
| :--- | :--- | :--- | :--- | :--- |
| `instance` | `equals` | `(arg0: Object)` | `boolean` | Performs equals operation |
| `instance` | `toString` | `()` | `String` | Converts/serializes representation via `toString` |
| `instance` | `hashCode` | `()` | `int` | Evaluates boolean predicate `hashCode` on `MonthlyRangeCalculator` |
| `instance` | `getClass` | `()` | `Class` | Retrieves `Class` property from `MonthlyRangeCalculator` |
| `instance` | `notify` | `()` | `void` | Performs notify operation |
| `instance` | `notifyAll` | `()` | `void` | Performs notify all operation |
| `instance` | `wait` | `(arg0: long)` | `void` | Performs wait operation |
| `instance` | `wait` | `(arg0: long, arg1: int)` | `void` | Performs wait operation |
| `instance` | `wait` | `()` | `void` | Performs wait operation |
| `static` | `getSessionStartTime` | `(arg0: long, arg1: long, arg2: long, arg3: ZoneId)` | `long` | Retrieves `SessionStartTime` property from `MonthlyRangeCalculator` |
| `static` | `getSessionStartTime` | `(arg0: long, arg1: long, arg2: long)` | `long` | Retrieves `SessionStartTime` property from `MonthlyRangeCalculator` |
| `static` | `getSessionEndTime` | `(arg0: long, arg1: long, arg2: long, arg3: ZoneId)` | `long` | Retrieves `SessionEndTime` property from `MonthlyRangeCalculator` |
| `static` | `getSessionEndTime` | `(arg0: long, arg1: long, arg2: long)` | `long` | Retrieves `SessionEndTime` property from `MonthlyRangeCalculator` |

---

### `NinjaTraderSessionReader`
- **Full Qualified Name:** `com.strategyquant.datalib.session.NinjaTraderSessionReader`
- **Primary Job / Responsibility:** Exchange trading session timing, rollover, and weekend holiday definitions (`NinjaTraderSessionReader`).

#### Fields
| Scope | Field Name | Type |
| :--- | :--- | :--- |
| `static` | `Log` | `Logger` |

#### Methods & Functions
| Modifiers | Method Name | Parameter Signatures | Return Type | Functional Description / Job |
| :--- | :--- | :--- | :--- | :--- |
| `instance` | `equals` | `(arg0: Object)` | `boolean` | Performs equals operation |
| `instance` | `toString` | `()` | `String` | Converts/serializes representation via `toString` |
| `instance` | `hashCode` | `()` | `int` | Evaluates boolean predicate `hashCode` on `NinjaTraderSessionReader` |
| `instance` | `getClass` | `()` | `Class` | Retrieves `Class` property from `NinjaTraderSessionReader` |
| `instance` | `notify` | `()` | `void` | Performs notify operation |
| `instance` | `notifyAll` | `()` | `void` | Performs notify all operation |
| `instance` | `wait` | `(arg0: long)` | `void` | Performs wait operation |
| `instance` | `wait` | `(arg0: long, arg1: int)` | `void` | Performs wait operation |
| `instance` | `wait` | `()` | `void` | Performs wait operation |
| `static` | `read` | `(arg0: File)` | `Result` | Performs read operation |

---

### `Result`
- **Full Qualified Name:** `com.strategyquant.datalib.session.NinjaTraderSessionReader.Result`
- **Primary Job / Responsibility:** Exchange trading session timing, rollover, and weekend holiday definitions (`Result`).

#### Fields
| Scope | Field Name | Type |
| :--- | :--- | :--- |
| `instance` | `droppedHolidays` | `int` |
| `instance` | `droppedPartialHolidays` | `int` |
| `instance` | `session` | `Session` |
| `instance` | `windowsTimeZone` | `String` |

#### Methods & Functions
| Modifiers | Method Name | Parameter Signatures | Return Type | Functional Description / Job |
| :--- | :--- | :--- | :--- | :--- |
| `instance` | `anythingDropped` | `()` | `boolean` | Performs anything dropped operation |
| `instance` | `describeDropped` | `()` | `String` | Performs describe dropped operation |
| `instance` | `equals` | `(arg0: Object)` | `boolean` | Performs equals operation |
| `instance` | `toString` | `()` | `String` | Converts/serializes representation via `toString` |
| `instance` | `hashCode` | `()` | `int` | Evaluates boolean predicate `hashCode` on `Result` |
| `instance` | `getClass` | `()` | `Class` | Retrieves `Class` property from `Result` |
| `instance` | `notify` | `()` | `void` | Performs notify operation |
| `instance` | `notifyAll` | `()` | `void` | Performs notify all operation |
| `instance` | `wait` | `(arg0: long)` | `void` | Performs wait operation |
| `instance` | `wait` | `(arg0: long, arg1: int)` | `void` | Performs wait operation |
| `instance` | `wait` | `()` | `void` | Performs wait operation |

---

### `Session`
- **Full Qualified Name:** `com.strategyquant.datalib.session.Session`
- **Primary Job / Responsibility:** Exchange trading session timing, rollover, and weekend holiday definitions (`Session`).

#### Fields
| Scope | Field Name | Type |
| :--- | :--- | :--- |
| `static` | `Forex_245` | `String` |
| `static` | `Forex_247` | `String` |
| `static` | `Log` | `Logger` |
| `static` | `NoSession` | `String` |
| `static` | `US_Index_Futures` | `String` |
| `static` | `US_Stocks` | `String` |
| `static` | `WEEK_MILLIS` | `long` |

#### Methods & Functions
| Modifiers | Method Name | Parameter Signatures | Return Type | Functional Description / Job |
| :--- | :--- | :--- | :--- | :--- |
| `instance` | `clone` | `()` | `Session` | Performs clone operation |
| `instance` | `clone` | `()` | `Session` | Performs clone operation |
| `instance` | `setTimeZone` | `(arg0: String)` | `void` | Sets `TimeZone` configuration/state on `Session` |
| `instance` | `getTimeZone` | `()` | `String` | Retrieves `TimeZone` property from `Session` |
| `instance` | `setFromXML` | `(arg0: Element)` | `void` | Sets `FromXML` configuration/state on `Session` |
| `instance` | `getXML` | `()` | `Element` | Retrieves `XML` property from `Session` |
| `instance` | `clearSessionTempData` | `()` | `void` | Removes/resets elements via `clearSessionTempData` |
| `instance` | `fixD1DataTime` | `(arg0: VersatileData)` | `void` | Performs fix d 1 data time operation |
| `instance` | `fixD1DataTime` | `(arg0: TickEvent)` | `void` | Performs fix d 1 data time operation |
| `instance` | `checkTimeIsInSession` | `(arg0: long, arg1: SessionStatus, arg2: String)` | `void` | Performs check time is in session operation |
| `instance` | `getElements` | `()` | `ArrayList` | Retrieves `Elements` property from `Session` |
| `instance` | `getBroker` | `()` | `int` | Retrieves `Broker` property from `Session` |
| `instance` | `getSessionName` | `()` | `String` | Retrieves `SessionName` property from `Session` |
| `instance` | `hasTimeZone` | `()` | `boolean` | Evaluates boolean predicate `hasTimeZone` on `Session` |
| `instance` | `cloneElements` | `()` | `ArrayList` | Performs clone elements operation |
| `instance` | `getZoneId` | `()` | `ZoneId` | Retrieves `ZoneId` property from `Session` |
| `instance` | `toText` | `()` | `String` | Converts/serializes representation via `toText` |
| `instance` | `setBroker` | `(arg0: int)` | `void` | Sets `Broker` configuration/state on `Session` |
| `instance` | `equals` | `(arg0: Object)` | `boolean` | Performs equals operation |
| `instance` | `toString` | `()` | `String` | Converts/serializes representation via `toString` |
| `instance` | `hashCode` | `()` | `int` | Evaluates boolean predicate `hashCode` on `Session` |
| `instance` | `getClass` | `()` | `Class` | Retrieves `Class` property from `Session` |
| `instance` | `notify` | `()` | `void` | Performs notify operation |
| `instance` | `notifyAll` | `()` | `void` | Performs notify all operation |
| `instance` | `wait` | `(arg0: long)` | `void` | Performs wait operation |
| `instance` | `wait` | `(arg0: long, arg1: int)` | `void` | Performs wait operation |
| `instance` | `wait` | `()` | `void` | Performs wait operation |

---

### `SessionComparator`
- **Full Qualified Name:** `com.strategyquant.datalib.session.SessionComparator`
- **Primary Job / Responsibility:** Exchange trading session timing, rollover, and weekend holiday definitions (`SessionComparator`).

#### Methods & Functions
| Modifiers | Method Name | Parameter Signatures | Return Type | Functional Description / Job |
| :--- | :--- | :--- | :--- | :--- |
| `instance` | `compare` | `(arg0: Session, arg1: Session)` | `int` | Performs compare operation |
| `instance` | `compare` | `(arg0: Object, arg1: Object)` | `int` | Performs compare operation |
| `instance` | `equals` | `(arg0: Object)` | `boolean` | Performs equals operation |
| `instance` | `toString` | `()` | `String` | Converts/serializes representation via `toString` |
| `instance` | `hashCode` | `()` | `int` | Evaluates boolean predicate `hashCode` on `SessionComparator` |
| `instance` | `getClass` | `()` | `Class` | Retrieves `Class` property from `SessionComparator` |
| `instance` | `notify` | `()` | `void` | Performs notify operation |
| `instance` | `notifyAll` | `()` | `void` | Performs notify all operation |
| `instance` | `wait` | `(arg0: long)` | `void` | Performs wait operation |
| `instance` | `wait` | `(arg0: long, arg1: int)` | `void` | Performs wait operation |
| `instance` | `wait` | `()` | `void` | Performs wait operation |
| `instance` | `reversed` | `()` | `Comparator` | Performs reversed operation |
| `instance` | `thenComparing` | `(arg0: Function, arg1: Comparator)` | `Comparator` | Performs then comparing operation |
| `instance` | `thenComparing` | `(arg0: Comparator)` | `Comparator` | Performs then comparing operation |
| `instance` | `thenComparing` | `(arg0: Function)` | `Comparator` | Performs then comparing operation |
| `instance` | `thenComparingInt` | `(arg0: ToIntFunction)` | `Comparator` | Performs then comparing int operation |
| `instance` | `thenComparingLong` | `(arg0: ToLongFunction)` | `Comparator` | Performs then comparing long operation |
| `instance` | `thenComparingDouble` | `(arg0: ToDoubleFunction)` | `Comparator` | Performs then comparing double operation |

---

### `SessionElement`
- **Full Qualified Name:** `com.strategyquant.datalib.session.SessionElement`
- **Primary Job / Responsibility:** Exchange trading session timing, rollover, and weekend holiday definitions (`SessionElement`).

#### Methods & Functions
| Modifiers | Method Name | Parameter Signatures | Return Type | Functional Description / Job |
| :--- | :--- | :--- | :--- | :--- |
| `instance` | `clone` | `()` | `SessionElement` | Performs clone operation |
| `instance` | `clone` | `()` | `SessionElement` | Performs clone operation |
| `instance` | `clearSessionTempData` | `()` | `void` | Removes/resets elements via `clearSessionTempData` |
| `instance` | `fixD1DataTime` | `(arg0: VersatileData)` | `void` | Performs fix d 1 data time operation |
| `instance` | `fixD1DataTime` | `(arg0: TickEvent)` | `void` | Performs fix d 1 data time operation |
| `instance` | `getStartTime` | `()` | `long` | Retrieves `StartTime` property from `SessionElement` |
| `instance` | `getDayFromStr` | `()` | `String` | Retrieves `DayFromStr` property from `SessionElement` |
| `instance` | `getTimeFromStr` | `()` | `String` | Retrieves `TimeFromStr` property from `SessionElement` |
| `instance` | `getDayToStr` | `()` | `String` | Retrieves `DayToStr` property from `SessionElement` |
| `instance` | `getTimeToStr` | `()` | `String` | Retrieves `TimeToStr` property from `SessionElement` |
| `instance` | `isEOD` | `()` | `boolean` | Evaluates boolean predicate `isEOD` on `SessionElement` |
| `instance` | `setEod` | `(arg0: boolean)` | `void` | Sets `Eod` configuration/state on `SessionElement` |
| `instance` | `getDayFrom` | `()` | `int` | Retrieves `DayFrom` property from `SessionElement` |
| `instance` | `getDayTo` | `()` | `int` | Retrieves `DayTo` property from `SessionElement` |
| `instance` | `getTimeFrom` | `()` | `int` | Retrieves `TimeFrom` property from `SessionElement` |
| `instance` | `getTimeTo` | `()` | `int` | Retrieves `TimeTo` property from `SessionElement` |
| `instance` | `includesDay` | `(arg0: int)` | `boolean` | Performs includes day operation |
| `instance` | `includesTime` | `(arg0: long, arg1: ZoneId)` | `boolean` | Performs includes time operation |
| `instance` | `includesTime` | `(arg0: long)` | `boolean` | Performs includes time operation |
| `instance` | `getEndTime` | `()` | `long` | Retrieves `EndTime` property from `SessionElement` |
| `instance` | `equals` | `(arg0: Object)` | `boolean` | Performs equals operation |
| `instance` | `toString` | `()` | `String` | Converts/serializes representation via `toString` |
| `instance` | `hashCode` | `()` | `int` | Evaluates boolean predicate `hashCode` on `SessionElement` |
| `instance` | `getClass` | `()` | `Class` | Retrieves `Class` property from `SessionElement` |
| `instance` | `notify` | `()` | `void` | Performs notify operation |
| `instance` | `notifyAll` | `()` | `void` | Performs notify all operation |
| `instance` | `wait` | `(arg0: long)` | `void` | Performs wait operation |
| `instance` | `wait` | `(arg0: long, arg1: int)` | `void` | Performs wait operation |
| `instance` | `wait` | `()` | `void` | Performs wait operation |
| `static` | `getTimeInt` | `(arg0: String)` | `int` | Retrieves `TimeInt` property from `SessionElement` |

---

### `SessionException`
- **Full Qualified Name:** `com.strategyquant.datalib.session.SessionException`
- **Primary Job / Responsibility:** Exchange trading session timing, rollover, and weekend holiday definitions (`SessionException`).

#### Methods & Functions
| Modifiers | Method Name | Parameter Signatures | Return Type | Functional Description / Job |
| :--- | :--- | :--- | :--- | :--- |
| `instance` | `printStackTrace` | `()` | `void` | Performs print stack trace operation |
| `instance` | `printStackTrace` | `(arg0: PrintWriter)` | `void` | Performs print stack trace operation |
| `instance` | `printStackTrace` | `(arg0: PrintStream)` | `void` | Performs print stack trace operation |
| `instance` | `getStackTrace` | `()` | `StackTraceElement[]` | Retrieves `StackTrace` property from `SessionException` |
| `instance` | `fillInStackTrace` | `()` | `Throwable` | Performs fill in stack trace operation |
| `instance` | `getCause` | `()` | `Throwable` | Retrieves `Cause` property from `SessionException` |
| `instance` | `initCause` | `(arg0: Throwable)` | `Throwable` | Instantiates/initializes `initCause` resource |
| `instance` | `toString` | `()` | `String` | Converts/serializes representation via `toString` |
| `instance` | `getMessage` | `()` | `String` | Retrieves `Message` property from `SessionException` |
| `instance` | `getSuppressed` | `()` | `Throwable[]` | Retrieves `Suppressed` property from `SessionException` |
| `instance` | `getLocalizedMessage` | `()` | `String` | Retrieves `LocalizedMessage` property from `SessionException` |
| `instance` | `setStackTrace` | `(arg0: StackTraceElement[])` | `void` | Sets `StackTrace` configuration/state on `SessionException` |
| `instance` | `addSuppressed` | `(arg0: Throwable)` | `void` | Appends/registers element via `addSuppressed` |
| `instance` | `equals` | `(arg0: Object)` | `boolean` | Performs equals operation |
| `instance` | `hashCode` | `()` | `int` | Evaluates boolean predicate `hashCode` on `SessionException` |
| `instance` | `getClass` | `()` | `Class` | Retrieves `Class` property from `SessionException` |
| `instance` | `notify` | `()` | `void` | Performs notify operation |
| `instance` | `notifyAll` | `()` | `void` | Performs notify all operation |
| `instance` | `wait` | `(arg0: long)` | `void` | Performs wait operation |
| `instance` | `wait` | `(arg0: long, arg1: int)` | `void` | Performs wait operation |
| `instance` | `wait` | `()` | `void` | Performs wait operation |

---

### `SessionManager`
- **Full Qualified Name:** `com.strategyquant.datalib.session.SessionManager`
- **Primary Job / Responsibility:** Exchange trading session timing, rollover, and weekend holiday definitions (`SessionManager`).

#### Fields
| Scope | Field Name | Type |
| :--- | :--- | :--- |
| `static` | `Log` | `Logger` |

#### Methods & Functions
| Modifiers | Method Name | Parameter Signatures | Return Type | Functional Description / Job |
| :--- | :--- | :--- | :--- | :--- |
| `instance` | `initDatabase` | `()` | `void` | Instantiates/initializes `initDatabase` resource |
| `instance` | `close` | `(arg0: ResultSet)` | `void` | Performs close operation |
| `instance` | `close` | `(arg0: Statement)` | `void` | Performs close operation |
| `instance` | `close` | `(arg0: Connection)` | `void` | Performs close operation |
| `instance` | `getConnection` | `()` | `Connection` | Retrieves `Connection` property from `SessionManager` |
| `instance` | `sqlCheckRecordExists` | `(arg0: Connection, arg1: String)` | `boolean` | Performs sql check record exists operation |
| `instance` | `sqlCommand` | `(arg0: Connection, arg1: PreparedStatement)` | `void` | Performs sql command operation |
| `instance` | `sqlCommand` | `(arg0: String)` | `void` | Performs sql command operation |
| `instance` | `sqlCommand` | `(arg0: Connection, arg1: String)` | `void` | Performs sql command operation |
| `instance` | `sqlInsertReturnAutoId` | `(arg0: Connection, arg1: PreparedStatement)` | `int` | Performs sql insert return auto id operation |
| `instance` | `sqlInsertReturnAutoId` | `(arg0: Connection, arg1: String)` | `int` | Performs sql insert return auto id operation |
| `instance` | `_getDirectory` | `()` | `String` | Performs get directory operation |
| `instance` | `getDbPath` | `()` | `String` | Retrieves `DbPath` property from `SessionManager` |
| `instance` | `isDbExist` | `()` | `boolean` | Evaluates boolean predicate `isDbExist` on `SessionManager` |
| `instance` | `columnExists` | `(arg0: String, arg1: String)` | `boolean` | Performs column exists operation |
| `instance` | `tableExists` | `(arg0: String)` | `boolean` | Performs table exists operation |
| `instance` | `equals` | `(arg0: Object)` | `boolean` | Performs equals operation |
| `instance` | `toString` | `()` | `String` | Converts/serializes representation via `toString` |
| `instance` | `hashCode` | `()` | `int` | Evaluates boolean predicate `hashCode` on `SessionManager` |
| `instance` | `getClass` | `()` | `Class` | Retrieves `Class` property from `SessionManager` |
| `instance` | `notify` | `()` | `void` | Performs notify operation |
| `instance` | `notifyAll` | `()` | `void` | Performs notify all operation |
| `instance` | `wait` | `(arg0: long)` | `void` | Performs wait operation |
| `instance` | `wait` | `(arg0: long, arg1: int)` | `void` | Performs wait operation |
| `instance` | `wait` | `()` | `void` | Performs wait operation |
| `static` | `init` | `(arg0: String)` | `void` | Instantiates/initializes `init` resource |
| `static` | `getSession` | `(arg0: String)` | `Session` | Retrieves `Session` property from `SessionManager` |
| `static` | `getSessions` | `()` | `ArrayList` | Retrieves `Sessions` property from `SessionManager` |
| `static` | `addSession` | `(arg0: Session)` | `void` | Appends/registers element via `addSession` |
| `static` | `updateSession` | `(arg0: String, arg1: ArrayList)` | `void` | Performs update session operation |
| `static` | `updateSession` | `(arg0: Session)` | `void` | Performs update session operation |
| `static` | `checkSessionExists` | `(arg0: String)` | `boolean` | Performs check session exists operation |
| `static` | `removeSession` | `(arg0: String)` | `void` | Removes/resets elements via `removeSession` |

---

### `SessionNoSession`
- **Full Qualified Name:** `com.strategyquant.datalib.session.SessionNoSession`
- **Primary Job / Responsibility:** Exchange trading session timing, rollover, and weekend holiday definitions (`SessionNoSession`).

#### Fields
| Scope | Field Name | Type |
| :--- | :--- | :--- |
| `static` | `Forex_245` | `String` |
| `static` | `Forex_247` | `String` |
| `static` | `Log` | `Logger` |
| `static` | `NoSession` | `String` |
| `static` | `US_Index_Futures` | `String` |
| `static` | `US_Stocks` | `String` |
| `static` | `WEEK_MILLIS` | `long` |

#### Methods & Functions
| Modifiers | Method Name | Parameter Signatures | Return Type | Functional Description / Job |
| :--- | :--- | :--- | :--- | :--- |
| `instance` | `checkTimeIsInSession` | `(arg0: long, arg1: SessionStatus)` | `void` | Performs check time is in session operation |
| `instance` | `checkTimeIsInSession` | `(arg0: long, arg1: SessionStatus, arg2: String)` | `void` | Performs check time is in session operation |
| `instance` | `clone` | `()` | `Session` | Performs clone operation |
| `instance` | `clone` | `()` | `Session` | Performs clone operation |
| `instance` | `setTimeZone` | `(arg0: String)` | `void` | Sets `TimeZone` configuration/state on `SessionNoSession` |
| `instance` | `getTimeZone` | `()` | `String` | Retrieves `TimeZone` property from `SessionNoSession` |
| `instance` | `setFromXML` | `(arg0: Element)` | `void` | Sets `FromXML` configuration/state on `SessionNoSession` |
| `instance` | `getXML` | `()` | `Element` | Retrieves `XML` property from `SessionNoSession` |
| `instance` | `clearSessionTempData` | `()` | `void` | Removes/resets elements via `clearSessionTempData` |
| `instance` | `fixD1DataTime` | `(arg0: VersatileData)` | `void` | Performs fix d 1 data time operation |
| `instance` | `fixD1DataTime` | `(arg0: TickEvent)` | `void` | Performs fix d 1 data time operation |
| `instance` | `getElements` | `()` | `ArrayList` | Retrieves `Elements` property from `SessionNoSession` |
| `instance` | `getBroker` | `()` | `int` | Retrieves `Broker` property from `SessionNoSession` |
| `instance` | `getSessionName` | `()` | `String` | Retrieves `SessionName` property from `SessionNoSession` |
| `instance` | `hasTimeZone` | `()` | `boolean` | Evaluates boolean predicate `hasTimeZone` on `SessionNoSession` |
| `instance` | `cloneElements` | `()` | `ArrayList` | Performs clone elements operation |
| `instance` | `getZoneId` | `()` | `ZoneId` | Retrieves `ZoneId` property from `SessionNoSession` |
| `instance` | `toText` | `()` | `String` | Converts/serializes representation via `toText` |
| `instance` | `setBroker` | `(arg0: int)` | `void` | Sets `Broker` configuration/state on `SessionNoSession` |
| `instance` | `equals` | `(arg0: Object)` | `boolean` | Performs equals operation |
| `instance` | `toString` | `()` | `String` | Converts/serializes representation via `toString` |
| `instance` | `hashCode` | `()` | `int` | Evaluates boolean predicate `hashCode` on `SessionNoSession` |
| `instance` | `getClass` | `()` | `Class` | Retrieves `Class` property from `SessionNoSession` |
| `instance` | `notify` | `()` | `void` | Performs notify operation |
| `instance` | `notifyAll` | `()` | `void` | Performs notify all operation |
| `instance` | `wait` | `(arg0: long)` | `void` | Performs wait operation |
| `instance` | `wait` | `(arg0: long, arg1: int)` | `void` | Performs wait operation |
| `instance` | `wait` | `()` | `void` | Performs wait operation |

---

### `SessionStatus`
- **Full Qualified Name:** `com.strategyquant.datalib.session.SessionStatus`
- **Primary Job / Responsibility:** Exchange trading session timing, rollover, and weekend holiday definitions (`SessionStatus`).

#### Fields
| Scope | Field Name | Type |
| :--- | :--- | :--- |
| `instance` | `isInSession` | `boolean` |
| `instance` | `sessionEndTime` | `long` |
| `instance` | `sessionStartTime` | `long` |

#### Methods & Functions
| Modifiers | Method Name | Parameter Signatures | Return Type | Functional Description / Job |
| :--- | :--- | :--- | :--- | :--- |
| `instance` | `equals` | `(arg0: Object)` | `boolean` | Performs equals operation |
| `instance` | `toString` | `()` | `String` | Converts/serializes representation via `toString` |
| `instance` | `hashCode` | `()` | `int` | Evaluates boolean predicate `hashCode` on `SessionStatus` |
| `instance` | `getClass` | `()` | `Class` | Retrieves `Class` property from `SessionStatus` |
| `instance` | `notify` | `()` | `void` | Performs notify operation |
| `instance` | `notifyAll` | `()` | `void` | Performs notify all operation |
| `instance` | `wait` | `(arg0: long)` | `void` | Performs wait operation |
| `instance` | `wait` | `(arg0: long, arg1: int)` | `void` | Performs wait operation |
| `instance` | `wait` | `()` | `void` | Performs wait operation |

---

## Subsystem: `ticksimulator`

### `DefaultTickSimulator`
- **Full Qualified Name:** `com.strategyquant.datalib.ticksimulator.DefaultTickSimulator`
- **Primary Job / Responsibility:** Market data abstraction and time-series container (`DefaultTickSimulator`).

#### Methods & Functions
| Modifiers | Method Name | Parameter Signatures | Return Type | Functional Description / Job |
| :--- | :--- | :--- | :--- | :--- |
| `instance` | `init` | `(arg0: VersatileData)` | `void` | Instantiates/initializes `init` resource |
| `instance` | `getNextTick` | `(arg0: TickEvent)` | `boolean` | Retrieves `NextTick` property from `DefaultTickSimulator` |
| `instance` | `setSymbolsSpread` | `(arg0: SpreadsMap)` | `void` | Sets `SymbolsSpread` configuration/state on `DefaultTickSimulator` |
| `instance` | `equals` | `(arg0: Object)` | `boolean` | Performs equals operation |
| `instance` | `toString` | `()` | `String` | Converts/serializes representation via `toString` |
| `instance` | `hashCode` | `()` | `int` | Evaluates boolean predicate `hashCode` on `DefaultTickSimulator` |
| `instance` | `getClass` | `()` | `Class` | Retrieves `Class` property from `DefaultTickSimulator` |
| `instance` | `notify` | `()` | `void` | Performs notify operation |
| `instance` | `notifyAll` | `()` | `void` | Performs notify all operation |
| `instance` | `wait` | `(arg0: long)` | `void` | Performs wait operation |
| `instance` | `wait` | `(arg0: long, arg1: int)` | `void` | Performs wait operation |
| `instance` | `wait` | `()` | `void` | Performs wait operation |

---

### `ITickSimulator`
- **Full Qualified Name:** `com.strategyquant.datalib.ticksimulator.ITickSimulator`
- **Primary Job / Responsibility:** Market data abstraction and time-series container (`ITickSimulator`).

#### Methods & Functions
| Modifiers | Method Name | Parameter Signatures | Return Type | Functional Description / Job |
| :--- | :--- | :--- | :--- | :--- |
| `instance` | `init` | `(arg0: VersatileData)` | `void` | Instantiates/initializes `init` resource |
| `instance` | `getNextTick` | `(arg0: TickEvent)` | `boolean` | Retrieves `NextTick` property from `ITickSimulator` |
| `instance` | `setSymbolsSpread` | `(arg0: SpreadsMap)` | `void` | Sets `SymbolsSpread` configuration/state on `ITickSimulator` |

---

### `SpreadsMap`
- **Full Qualified Name:** `com.strategyquant.datalib.ticksimulator.SpreadsMap`
- **Primary Job / Responsibility:** Market data abstraction and time-series container (`SpreadsMap`).

#### Methods & Functions
| Modifiers | Method Name | Parameter Signatures | Return Type | Functional Description / Job |
| :--- | :--- | :--- | :--- | :--- |
| `instance` | `containsKey` | `(arg0: int)` | `boolean` | Performs contains key operation |
| `instance` | `getSpread` | `(arg0: int)` | `double` | Retrieves `Spread` property from `SpreadsMap` |
| `instance` | `equals` | `(arg0: Object)` | `boolean` | Performs equals operation |
| `instance` | `toString` | `()` | `String` | Converts/serializes representation via `toString` |
| `instance` | `hashCode` | `()` | `int` | Evaluates boolean predicate `hashCode` on `SpreadsMap` |
| `instance` | `getClass` | `()` | `Class` | Retrieves `Class` property from `SpreadsMap` |
| `instance` | `notify` | `()` | `void` | Performs notify operation |
| `instance` | `notifyAll` | `()` | `void` | Performs notify all operation |
| `instance` | `wait` | `(arg0: long)` | `void` | Performs wait operation |
| `instance` | `wait` | `(arg0: long, arg1: int)` | `void` | Performs wait operation |
| `instance` | `wait` | `()` | `void` | Performs wait operation |

---

### `TSTickSimulator`
- **Full Qualified Name:** `com.strategyquant.datalib.ticksimulator.TSTickSimulator`
- **Primary Job / Responsibility:** Market data abstraction and time-series container (`TSTickSimulator`).

#### Methods & Functions
| Modifiers | Method Name | Parameter Signatures | Return Type | Functional Description / Job |
| :--- | :--- | :--- | :--- | :--- |
| `instance` | `init` | `(arg0: VersatileData)` | `void` | Instantiates/initializes `init` resource |
| `instance` | `getNextTick` | `(arg0: TickEvent)` | `boolean` | Retrieves `NextTick` property from `TSTickSimulator` |
| `instance` | `setSymbolsSpread` | `(arg0: SpreadsMap)` | `void` | Sets `SymbolsSpread` configuration/state on `TSTickSimulator` |
| `instance` | `equals` | `(arg0: Object)` | `boolean` | Performs equals operation |
| `instance` | `toString` | `()` | `String` | Converts/serializes representation via `toString` |
| `instance` | `hashCode` | `()` | `int` | Evaluates boolean predicate `hashCode` on `TSTickSimulator` |
| `instance` | `getClass` | `()` | `Class` | Retrieves `Class` property from `TSTickSimulator` |
| `instance` | `notify` | `()` | `void` | Performs notify operation |
| `instance` | `notifyAll` | `()` | `void` | Performs notify all operation |
| `instance` | `wait` | `(arg0: long)` | `void` | Performs wait operation |
| `instance` | `wait` | `(arg0: long, arg1: int)` | `void` | Performs wait operation |
| `instance` | `wait` | `()` | `void` | Performs wait operation |

---

## Subsystem: `timeframe`

### `TimeframesComparator`
- **Full Qualified Name:** `com.strategyquant.datalib.timeframe.TimeframesComparator`
- **Primary Job / Responsibility:** Market data abstraction and time-series container (`TimeframesComparator`).

#### Methods & Functions
| Modifiers | Method Name | Parameter Signatures | Return Type | Functional Description / Job |
| :--- | :--- | :--- | :--- | :--- |
| `instance` | `compare` | `(arg0: Object, arg1: Object)` | `int` | Performs compare operation |
| `instance` | `compare` | `(arg0: String, arg1: String)` | `int` | Performs compare operation |
| `instance` | `equals` | `(arg0: Object)` | `boolean` | Performs equals operation |
| `instance` | `toString` | `()` | `String` | Converts/serializes representation via `toString` |
| `instance` | `hashCode` | `()` | `int` | Evaluates boolean predicate `hashCode` on `TimeframesComparator` |
| `instance` | `getClass` | `()` | `Class` | Retrieves `Class` property from `TimeframesComparator` |
| `instance` | `notify` | `()` | `void` | Performs notify operation |
| `instance` | `notifyAll` | `()` | `void` | Performs notify all operation |
| `instance` | `wait` | `(arg0: long)` | `void` | Performs wait operation |
| `instance` | `wait` | `(arg0: long, arg1: int)` | `void` | Performs wait operation |
| `instance` | `wait` | `()` | `void` | Performs wait operation |
| `instance` | `reversed` | `()` | `Comparator` | Performs reversed operation |
| `instance` | `thenComparing` | `(arg0: Function, arg1: Comparator)` | `Comparator` | Performs then comparing operation |
| `instance` | `thenComparing` | `(arg0: Comparator)` | `Comparator` | Performs then comparing operation |
| `instance` | `thenComparing` | `(arg0: Function)` | `Comparator` | Performs then comparing operation |
| `instance` | `thenComparingInt` | `(arg0: ToIntFunction)` | `Comparator` | Performs then comparing int operation |
| `instance` | `thenComparingLong` | `(arg0: ToLongFunction)` | `Comparator` | Performs then comparing long operation |
| `instance` | `thenComparingDouble` | `(arg0: ToDoubleFunction)` | `Comparator` | Performs then comparing double operation |
| `static` | `getSecondsCount` | `(arg0: String)` | `int` | Retrieves `SecondsCount` property from `TimeframesComparator` |

---

## Subsystem: `timezone`

### `Timezone`
- **Full Qualified Name:** `com.strategyquant.datalib.timezone.Timezone`
- **Primary Job / Responsibility:** Market data abstraction and time-series container (`Timezone`).

#### Fields
| Scope | Field Name | Type |
| :--- | :--- | :--- |
| `static` | `DEFAULT` | `String` |
| `instance` | `dst` | `boolean` |

#### Methods & Functions
| Modifiers | Method Name | Parameter Signatures | Return Type | Functional Description / Job |
| :--- | :--- | :--- | :--- | :--- |
| `instance` | `getName` | `()` | `String` | Retrieves `Name` property from `Timezone` |
| `instance` | `toString` | `()` | `String` | Converts/serializes representation via `toString` |
| `instance` | `getId` | `()` | `String` | Retrieves `Id` property from `Timezone` |
| `instance` | `printShortName` | `()` | `String` | Performs print short name operation |
| `instance` | `equals` | `(arg0: Object)` | `boolean` | Performs equals operation |
| `instance` | `hashCode` | `()` | `int` | Evaluates boolean predicate `hashCode` on `Timezone` |
| `instance` | `getClass` | `()` | `Class` | Retrieves `Class` property from `Timezone` |
| `instance` | `notify` | `()` | `void` | Performs notify operation |
| `instance` | `notifyAll` | `()` | `void` | Performs notify all operation |
| `instance` | `wait` | `(arg0: long)` | `void` | Performs wait operation |
| `instance` | `wait` | `(arg0: long, arg1: int)` | `void` | Performs wait operation |
| `instance` | `wait` | `()` | `void` | Performs wait operation |
| `static` | `print` | `(arg0: String, arg1: int, arg2: boolean)` | `String` | Performs print operation |
| `static` | `shiftHours` | `(arg0: String, arg1: int)` | `String` | Performs shift hours operation |
| `static` | `parseId` | `(arg0: String)` | `String` | Converts/serializes representation via `parseId` |

---

### `Timezones`
- **Full Qualified Name:** `com.strategyquant.datalib.timezone.Timezones`
- **Primary Job / Responsibility:** Market data abstraction and time-series container (`Timezones`).

#### Fields
| Scope | Field Name | Type |
| :--- | :--- | :--- |
| `static` | `Log` | `Logger` |

#### Methods & Functions
| Modifiers | Method Name | Parameter Signatures | Return Type | Functional Description / Job |
| :--- | :--- | :--- | :--- | :--- |
| `instance` | `equals` | `(arg0: Object)` | `boolean` | Performs equals operation |
| `instance` | `toString` | `()` | `String` | Converts/serializes representation via `toString` |
| `instance` | `hashCode` | `()` | `int` | Evaluates boolean predicate `hashCode` on `Timezones` |
| `instance` | `getClass` | `()` | `Class` | Retrieves `Class` property from `Timezones` |
| `instance` | `notify` | `()` | `void` | Performs notify operation |
| `instance` | `notifyAll` | `()` | `void` | Performs notify all operation |
| `instance` | `wait` | `(arg0: long)` | `void` | Performs wait operation |
| `instance` | `wait` | `(arg0: long, arg1: int)` | `void` | Performs wait operation |
| `instance` | `wait` | `()` | `void` | Performs wait operation |
| `static` | `findByKey` | `(arg0: String)` | `Timezone` | Performs find by key operation |
| `static` | `getTimezones` | `()` | `ArrayList` | Retrieves `Timezones` property from `Timezones` |

---

## Subsystem: `validation`

### `BarStampProbe`
- **Full Qualified Name:** `com.strategyquant.datalib.validation.BarStampProbe`
- **Primary Job / Responsibility:** Time-series price history, OHLCV bar storage, and chart data management (`BarStampProbe`).

#### Fields
| Scope | Field Name | Type |
| :--- | :--- | :--- |
| `static` | `Anchors` | `int` |
| `static` | `BoundariesPerAnchor` | `int` |
| `static` | `DefaultMillisCap` | `long` |
| `static` | `DefaultRecordCap` | `int` |
| `static` | `Log` | `Logger` |

#### Methods & Functions
| Modifiers | Method Name | Parameter Signatures | Return Type | Functional Description / Job |
| :--- | :--- | :--- | :--- | :--- |
| `instance` | `equals` | `(arg0: Object)` | `boolean` | Performs equals operation |
| `instance` | `toString` | `()` | `String` | Converts/serializes representation via `toString` |
| `instance` | `hashCode` | `()` | `int` | Evaluates boolean predicate `hashCode` on `BarStampProbe` |
| `instance` | `getClass` | `()` | `Class` | Retrieves `Class` property from `BarStampProbe` |
| `instance` | `notify` | `()` | `void` | Performs notify operation |
| `instance` | `notifyAll` | `()` | `void` | Performs notify all operation |
| `instance` | `wait` | `(arg0: long)` | `void` | Performs wait operation |
| `instance` | `wait` | `(arg0: long, arg1: int)` | `void` | Performs wait operation |
| `instance` | `wait` | `()` | `void` | Performs wait operation |
| `static` | `measure` | `(arg0: DataInfo)` | `BarStampVerdict` | Performs measure operation |
| `static` | `measure` | `(arg0: DataInfo, arg1: int, arg2: long)` | `BarStampVerdict` | Performs measure operation |

---

### `BarStampRules`
- **Full Qualified Name:** `com.strategyquant.datalib.validation.BarStampRules`
- **Primary Job / Responsibility:** Time-series price history, OHLCV bar storage, and chart data management (`BarStampRules`).

#### Fields
| Scope | Field Name | Type |
| :--- | :--- | :--- |
| `static` | `BoundaryUnitMillis` | `long` |
| `static` | `ConventionUnknown` | `int` |
| `static` | `DayMillis` | `long` |

#### Methods & Functions
| Modifiers | Method Name | Parameter Signatures | Return Type | Functional Description / Job |
| :--- | :--- | :--- | :--- | :--- |
| `instance` | `equals` | `(arg0: Object)` | `boolean` | Performs equals operation |
| `instance` | `toString` | `()` | `String` | Converts/serializes representation via `toString` |
| `instance` | `hashCode` | `()` | `int` | Evaluates boolean predicate `hashCode` on `BarStampRules` |
| `instance` | `getClass` | `()` | `Class` | Retrieves `Class` property from `BarStampRules` |
| `instance` | `notify` | `()` | `void` | Performs notify operation |
| `instance` | `notifyAll` | `()` | `void` | Performs notify all operation |
| `instance` | `wait` | `(arg0: long)` | `void` | Performs wait operation |
| `instance` | `wait` | `(arg0: long, arg1: int)` | `void` | Performs wait operation |
| `instance` | `wait` | `()` | `void` | Performs wait operation |
| `static` | `dayEnd` | `(arg0: long, arg1: long)` | `long` | Performs day end operation |
| `static` | `canReadBoundary` | `(arg0: long)` | `boolean` | Evaluates boolean predicate `canReadBoundary` on `BarStampRules` |
| `static` | `boundaryAtOrBefore` | `(arg0: long)` | `long` | Performs boundary at or before operation |
| `static` | `conventionOfFirstBar` | `(arg0: long, arg1: long, arg2: long)` | `int` | Performs convention of first bar operation |
| `static` | `boundaryAtOrAfter` | `(arg0: long)` | `long` | Performs boundary at or after operation |
| `static` | `conventionOfLastBar` | `(arg0: long, arg1: long, arg2: long, arg3: long)` | `int` | Performs convention of last bar operation |
| `static` | `gridStart` | `(arg0: long, arg1: long, arg2: long)` | `long` | Performs grid start operation |
| `static` | `isSessionStartOnGrid` | `(arg0: long, arg1: long)` | `boolean` | Evaluates boolean predicate `isSessionStartOnGrid` on `BarStampRules` |
| `static` | `expectedFirstBarTime` | `(arg0: long, arg1: long, arg2: int)` | `long` | Performs expected first bar time operation |
| `static` | `expectedLastBarTime` | `(arg0: long, arg1: long, arg2: long, arg3: int)` | `long` | Performs expected last bar time operation |
| `static` | `isOnGrid` | `(arg0: long, arg1: long, arg2: long)` | `boolean` | Evaluates boolean predicate `isOnGrid` on `BarStampRules` |
| `static` | `conventionOfResumeStamp` | `(arg0: long, arg1: long)` | `int` | Performs convention of resume stamp operation |
| `static` | `conventionOfCloseStamp` | `(arg0: long, arg1: long)` | `int` | Performs convention of close stamp operation |

---

### `BarStampTally`
- **Full Qualified Name:** `com.strategyquant.datalib.validation.BarStampTally`
- **Primary Job / Responsibility:** Time-series price history, OHLCV bar storage, and chart data management (`BarStampTally`).

#### Fields
| Scope | Field Name | Type |
| :--- | :--- | :--- |
| `static` | `AgreementPercent` | `int` |
| `static` | `MinimumVotingBoundaries` | `int` |

#### Methods & Functions
| Modifiers | Method Name | Parameter Signatures | Return Type | Functional Description / Job |
| :--- | :--- | :--- | :--- | :--- |
| `instance` | `accept` | `(arg0: long)` | `void` | Performs accept operation |
| `instance` | `finish` | `(arg0: int, arg1: long)` | `BarStampVerdict` | Performs finish operation |
| `instance` | `startAnchor` | `()` | `void` | Performs start anchor operation |
| `instance` | `getBoundariesAtAnchor` | `()` | `int` | Retrieves `BoundariesAtAnchor` property from `BarStampTally` |
| `instance` | `equals` | `(arg0: Object)` | `boolean` | Performs equals operation |
| `instance` | `toString` | `()` | `String` | Converts/serializes representation via `toString` |
| `instance` | `hashCode` | `()` | `int` | Evaluates boolean predicate `hashCode` on `BarStampTally` |
| `instance` | `getClass` | `()` | `Class` | Retrieves `Class` property from `BarStampTally` |
| `instance` | `notify` | `()` | `void` | Performs notify operation |
| `instance` | `notifyAll` | `()` | `void` | Performs notify all operation |
| `instance` | `wait` | `(arg0: long)` | `void` | Performs wait operation |
| `instance` | `wait` | `(arg0: long, arg1: int)` | `void` | Performs wait operation |
| `instance` | `wait` | `()` | `void` | Performs wait operation |

---

### `BarStampVerdict`
- **Full Qualified Name:** `com.strategyquant.datalib.validation.BarStampVerdict`
- **Primary Job / Responsibility:** Time-series price history, OHLCV bar storage, and chart data management (`BarStampVerdict`).

#### Methods & Functions
| Modifiers | Method Name | Parameter Signatures | Return Type | Functional Description / Job |
| :--- | :--- | :--- | :--- | :--- |
| `instance` | `getMillis` | `()` | `long` | Retrieves `Millis` property from `BarStampVerdict` |
| `instance` | `hasVerdict` | `()` | `boolean` | Evaluates boolean predicate `hasVerdict` on `BarStampVerdict` |
| `instance` | `getConvention` | `()` | `int` | Retrieves `Convention` property from `BarStampVerdict` |
| `instance` | `getStartVotes` | `()` | `int` | Retrieves `StartVotes` property from `BarStampVerdict` |
| `instance` | `getEndVotes` | `()` | `int` | Retrieves `EndVotes` property from `BarStampVerdict` |
| `instance` | `getVotingBoundaries` | `()` | `int` | Retrieves `VotingBoundaries` property from `BarStampVerdict` |
| `instance` | `getContradictoryBoundaries` | `()` | `int` | Retrieves `ContradictoryBoundaries` property from `BarStampVerdict` |
| `instance` | `getOffGridStamps` | `()` | `int` | Retrieves `OffGridStamps` property from `BarStampVerdict` |
| `instance` | `getOffGridExample` | `()` | `long` | Retrieves `OffGridExample` property from `BarStampVerdict` |
| `instance` | `getSkipReason` | `()` | `String` | Retrieves `SkipReason` property from `BarStampVerdict` |
| `instance` | `getSilentBoundaries` | `()` | `int` | Retrieves `SilentBoundaries` property from `BarStampVerdict` |
| `instance` | `getRecordsRead` | `()` | `int` | Retrieves `RecordsRead` property from `BarStampVerdict` |
| `instance` | `equals` | `(arg0: Object)` | `boolean` | Performs equals operation |
| `instance` | `toString` | `()` | `String` | Converts/serializes representation via `toString` |
| `instance` | `hashCode` | `()` | `int` | Evaluates boolean predicate `hashCode` on `BarStampVerdict` |
| `instance` | `getClass` | `()` | `Class` | Retrieves `Class` property from `BarStampVerdict` |
| `instance` | `notify` | `()` | `void` | Performs notify operation |
| `instance` | `notifyAll` | `()` | `void` | Performs notify all operation |
| `instance` | `wait` | `(arg0: long)` | `void` | Performs wait operation |
| `instance` | `wait` | `(arg0: long, arg1: int)` | `void` | Performs wait operation |
| `instance` | `wait` | `()` | `void` | Performs wait operation |

---
