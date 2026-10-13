# SQLib Specification Catalog

- **Package Root:** `com.strategyquant.lib.*`
- **Total Classes:** 52
- **Total Methods / Functions:** 943
- **Donor Reference:** `SQX_REFERENCE_ROOT`
- **Evidence Standard:** Paraphrased clean-room specification (`contains_proprietary_source: false`).

## Overview and Architectural Responsibility

`SQLib` provides foundational utilities, low-level data structures, and memory/system primitives. It encompasses financial timestamp algorithms (`SQTime`), extensible hierarchical dictionaries (`ValuesMap`, `SettingsMap`), memory safety guards, XML serialization, and OS/network utilities.

---

## Table of Subsystems & Packages

| Subsystem / Subpackage | Classes Count | Description |
| :--- | :--- | :--- |
| [`(root)`](#subsystem-(root)) | 11 | Root classes of `com.strategyquant.lib` |
| [`memory`](#subsystem-memory) | 5 | Components belonging to `com.strategyquant.lib.memory` |
| [`utils`](#subsystem-utils) | 36 | Components belonging to `com.strategyquant.lib.utils` |

---

## Subsystem: `(root)`

### `IRandomGenerator`
- **Full Qualified Name:** `com.strategyquant.lib.IRandomGenerator`
- **Primary Job / Responsibility:** Foundational utility and data structure container (`IRandomGenerator`).

#### Methods & Functions
| Modifiers | Method Name | Parameter Signatures | Return Type | Functional Description / Job |
| :--- | :--- | :--- | :--- | :--- |
| `instance` | `clone` | `(arg0: long)` | `IRandomGenerator` | Performs clone operation |
| `instance` | `newInstance` | `(arg0: long)` | `IRandomGenerator` | Performs new instance operation |
| `instance` | `nextDouble` | `()` | `double` | Performs next double operation |
| `instance` | `nextDouble` | `(arg0: double, arg1: double, arg2: double, arg3: int)` | `double` | Performs next double operation |
| `instance` | `nextInt` | `(arg0: int, arg1: int, arg2: int)` | `int` | Performs next int operation |
| `instance` | `nextInt` | `(arg0: int)` | `int` | Performs next int operation |
| `instance` | `nextLong` | `()` | `long` | Performs next long operation |
| `instance` | `nextGaussian` | `()` | `double` | Performs next gaussian operation |
| `instance` | `probability` | `(arg0: double)` | `boolean` | Performs probability operation |
| `instance` | `nextBool` | `()` | `boolean` | Performs next bool operation |
| `instance` | `getRandom` | `()` | `Random` | Retrieves `Random` property from `IRandomGenerator` |

---

### `L`
- **Full Qualified Name:** `com.strategyquant.lib.L`
- **Primary Job / Responsibility:** Language translation class for Java backend.    Usage is simple -whenever you write a string that should be translated use L.t("String to be translated").

#### Fields
| Scope | Field Name | Type |
| :--- | :--- | :--- |
| `static` | `ENG_LANG` | `String` |
| `static` | `FILE_EXTENSION` | `String` |
| `static` | `Log` | `Logger` |
| `static` | `SEPARATOR` | `String` |
| `static` | `SemicolonReplacement` | `String` |
| `static` | `debug` | `boolean` |
| `static` | `flagsMap` | `Map` |
| `static` | `fontsMap` | `Map` |
| `static` | `lang` | `String` |
| `static` | `langDirFile` | `File` |
| `static` | `langList` | `ArrayList` |
| `static` | `translations` | `TreeMap` |

#### Methods & Functions
| Modifiers | Method Name | Parameter Signatures | Return Type | Functional Description / Job |
| :--- | :--- | :--- | :--- | :--- |
| `instance` | `equals` | `(arg0: Object)` | `boolean` | Performs equals operation |
| `instance` | `toString` | `()` | `String` | Converts/serializes representation via `toString` |
| `instance` | `hashCode` | `()` | `int` | Evaluates boolean predicate `hashCode` on `L` |
| `instance` | `getClass` | `()` | `Class` | Retrieves `Class` property from `L` |
| `instance` | `notify` | `()` | `void` | Performs notify operation |
| `instance` | `notifyAll` | `()` | `void` | Performs notify all operation |
| `instance` | `wait` | `(arg0: long)` | `void` | Performs wait operation |
| `instance` | `wait` | `(arg0: long, arg1: int)` | `void` | Performs wait operation |
| `instance` | `wait` | `()` | `void` | Performs wait operation |
| `static` | `t` | `(arg0: String, arg1: Object[])` | `String` | T. |
| `static` | `tsq` | `(arg0: String)` | `String` | Performs tsq operation |
| `static` | `tnp` | `(arg0: String, arg1: Object[])` | `String` | Performs tnp operation |
| `static` | `getFilePath` | `(arg0: String)` | `String` | Retrieves `FilePath` property from `L` |
| `static` | `isAvailable` | `(arg0: String)` | `boolean` | Evaluates boolean predicate `isAvailable` on `L` |
| `static` | `checkPlaceholders` | `(arg0: String)` | `boolean` | Performs check placeholders operation |
| `static` | `tHtml` | `(arg0: String)` | `String` | T html. |
| `static` | `loadLangFileToMap` | `(arg0: String)` | `void` | Load lang file to map. |
| `static` | `loadAvailableLangs` | `(arg0: File)` | `void` | Load available langs. |
| `static` | `getCurLangShortCut` | `()` | `String` | Retrieves `CurLangShortCut` property from `L` |
| `static` | `getFont` | `()` | `String` | Retrieves `Font` property from `L` |

---

### `MemoryInfo`
- **Full Qualified Name:** `com.strategyquant.lib.MemoryInfo`
- **Primary Job / Responsibility:** Foundational utility and data structure container (`MemoryInfo`).

#### Fields
| Scope | Field Name | Type |
| :--- | :--- | :--- |
| `instance` | `allocatedMemory` | `long` |
| `instance` | `allocatedObjects` | `int` |
| `instance` | `reallocations` | `int` |
| `instance` | `totalAllocatedMemory` | `long` |
| `instance` | `totalAllocatedObjects` | `int` |
| `instance` | `totalDeallocatedMemory` | `long` |
| `instance` | `totalDeallocatedObjects` | `int` |

#### Methods & Functions
| Modifiers | Method Name | Parameter Signatures | Return Type | Functional Description / Job |
| :--- | :--- | :--- | :--- | :--- |
| `instance` | `toString` | `()` | `String` | Converts/serializes representation via `toString` |
| `instance` | `copyFrom` | `(arg0: MemoryInfo)` | `void` | Performs copy from operation |
| `instance` | `equals` | `(arg0: Object)` | `boolean` | Performs equals operation |
| `instance` | `hashCode` | `()` | `int` | Evaluates boolean predicate `hashCode` on `MemoryInfo` |
| `instance` | `getClass` | `()` | `Class` | Retrieves `Class` property from `MemoryInfo` |
| `instance` | `notify` | `()` | `void` | Performs notify operation |
| `instance` | `notifyAll` | `()` | `void` | Performs notify all operation |
| `instance` | `wait` | `(arg0: long)` | `void` | Performs wait operation |
| `instance` | `wait` | `(arg0: long, arg1: int)` | `void` | Performs wait operation |
| `instance` | `wait` | `()` | `void` | Performs wait operation |

---

### `SQTime`
- **Full Qualified Name:** `com.strategyquant.lib.SQTime`
- **Primary Job / Responsibility:** High-precision financial timestamp manipulation and timezone normalization (`SQTime`).

#### Fields
| Scope | Field Name | Type |
| :--- | :--- | :--- |
| `static` | `DAY_MILLIS` | `long` |
| `static` | `FRIDAY` | `int` |
| `static` | `Log` | `Logger` |
| `static` | `MONDAY` | `int` |
| `static` | `SATURDAY` | `int` |
| `static` | `SUNDAY` | `int` |
| `static` | `THURSDAY` | `int` |
| `static` | `TUESDAY` | `int` |
| `static` | `WEDNESDAY` | `int` |
| `static` | `longDateFormat` | `String` |
| `static` | `shortDateFormat` | `String` |

#### Methods & Functions
| Modifiers | Method Name | Parameter Signatures | Return Type | Functional Description / Job |
| :--- | :--- | :--- | :--- | :--- |
| `instance` | `equals` | `(arg0: Object)` | `boolean` | Performs equals operation |
| `instance` | `toString` | `()` | `String` | Converts/serializes representation via `toString` |
| `instance` | `hashCode` | `()` | `int` | Evaluates boolean predicate `hashCode` on `SQTime` |
| `instance` | `getClass` | `()` | `Class` | Retrieves `Class` property from `SQTime` |
| `instance` | `notify` | `()` | `void` | Performs notify operation |
| `instance` | `notifyAll` | `()` | `void` | Performs notify all operation |
| `instance` | `wait` | `(arg0: long)` | `void` | Performs wait operation |
| `instance` | `wait` | `(arg0: long, arg1: int)` | `void` | Performs wait operation |
| `instance` | `wait` | `()` | `void` | Performs wait operation |
| `static` | `toString` | `(arg0: long)` | `String` | Converts/serializes representation via `toString` |
| `static` | `toString` | `(arg0: long, arg1: String)` | `String` | Converts/serializes representation via `toString` |
| `static` | `toString` | `(arg0: long, arg1: DateTimeFormatter)` | `String` | Converts/serializes representation via `toString` |
| `static` | `add` | `(arg0: long, arg1: int, arg2: int)` | `long` | Appends/registers element via `add` |
| `static` | `init` | `()` | `void` | Instantiates/initializes `init` resource |
| `static` | `getYear` | `(arg0: long)` | `int` | Retrieves `Year` property from `SQTime` |
| `static` | `getHour` | `(arg0: long)` | `int` | Retrieves `Hour` property from `SQTime` |
| `static` | `getMinute` | `(arg0: long)` | `int` | Retrieves `Minute` property from `SQTime` |
| `static` | `getSecond` | `(arg0: long)` | `int` | Retrieves `Second` property from `SQTime` |
| `static` | `minus` | `(arg0: long, arg1: int, arg2: int)` | `long` | Performs minus operation |
| `static` | `setTime` | `(arg0: long, arg1: int, arg2: int, arg3: int, arg4: int)` | `long` | Sets `Time` configuration/state on `SQTime` |
| `static` | `setTime` | `(arg0: long, arg1: int, arg2: int, arg3: int)` | `long` | Sets `Time` configuration/state on `SQTime` |
| `static` | `toHours` | `(arg0: long)` | `long` | Converts/serializes representation via `toHours` |
| `static` | `getMonth` | `(arg0: long)` | `int` | Retrieves `Month` property from `SQTime` |
| `static` | `getDayOfWeek` | `(arg0: long)` | `int` | Retrieves `DayOfWeek` property from `SQTime` |
| `static` | `getDayOfYear` | `(arg0: long)` | `int` | Retrieves `DayOfYear` property from `SQTime` |
| `static` | `addMonths` | `(arg0: long, arg1: int)` | `long` | Appends/registers element via `addMonths` |
| `static` | `addDays` | `(arg0: long, arg1: int)` | `long` | Appends/registers element via `addDays` |
| `static` | `setFirstDayOfWeek` | `(arg0: long)` | `long` | Sets `FirstDayOfWeek` configuration/state on `SQTime` |
| `static` | `setDayOfMonth` | `(arg0: long, arg1: int)` | `long` | Sets `DayOfMonth` configuration/state on `SQTime` |
| `static` | `getDay` | `(arg0: long)` | `int` | Retrieves `Day` property from `SQTime` |
| `static` | `setDayOfWeek` | `(arg0: long, arg1: int)` | `long` | Sets `DayOfWeek` configuration/state on `SQTime` |
| `static` | `addHours` | `(arg0: long, arg1: int)` | `long` | Appends/registers element via `addHours` |
| `static` | `getYmd` | `(arg0: int, arg1: int, arg2: int)` | `int` | Retrieves `Ymd` property from `SQTime` |
| `static` | `getYmd` | `(arg0: long)` | `int` | Retrieves `Ymd` property from `SQTime` |
| `static` | `getMonthOriginal` | `(arg0: long)` | `int` | Retrieves `MonthOriginal` property from `SQTime` |
| `static` | `getDayOfWeekOriginal` | `(arg0: long)` | `int` | Retrieves `DayOfWeekOriginal` property from `SQTime` |
| `static` | `getHHMM` | `(arg0: long)` | `int[]` | Retrieves `HHMM` property from `SQTime` |
| `static` | `getHHMM` | `(arg0: String)` | `int[]` | Retrieves `HHMM` property from `SQTime` |
| `static` | `getWeekOfMonth` | `(arg0: long)` | `int` | Retrieves `WeekOfMonth` property from `SQTime` |
| `static` | `getDateInMs` | `(arg0: long)` | `long` | Retrieves `DateInMs` property from `SQTime` |
| `static` | `getDaysInMonth` | `(arg0: long)` | `int` | Retrieves `DaysInMonth` property from `SQTime` |
| `static` | `getHms` | `(arg0: int, arg1: int, arg2: int)` | `double` | Retrieves `Hms` property from `SQTime` |
| `static` | `correctDayStart` | `(arg0: long)` | `long` | Performs correct day start operation |
| `static` | `toFullDateTimeString` | `(arg0: long)` | `String` | Converts/serializes representation via `toFullDateTimeString` |
| `static` | `setMonthOfYear` | `(arg0: long, arg1: int)` | `long` | Sets `MonthOfYear` configuration/state on `SQTime` |
| `static` | `addYears` | `(arg0: long, arg1: int)` | `long` | Appends/registers element via `addYears` |
| `static` | `getFullYear` | `(arg0: long)` | `int` | Retrieves `FullYear` property from `SQTime` |
| `static` | `getDiffInDays` | `(arg0: long, arg1: long)` | `int` | Retrieves `DiffInDays` property from `SQTime` |
| `static` | `isSameDay` | `(arg0: long, arg1: long)` | `boolean` | Evaluates boolean predicate `isSameDay` on `SQTime` |
| `static` | `isSameMonth` | `(arg0: long, arg1: long)` | `boolean` | Evaluates boolean predicate `isSameMonth` on `SQTime` |
| `static` | `isSameWeek` | `(arg0: long, arg1: long)` | `int` | Evaluates boolean predicate `isSameWeek` on `SQTime` |
| `static` | `setSecond` | `(arg0: long, arg1: int)` | `long` | Sets `Second` configuration/state on `SQTime` |
| `static` | `setMiliSeconds` | `(arg0: long, arg1: int)` | `long` | Sets `MiliSeconds` configuration/state on `SQTime` |
| `static` | `toFullDateMinuteString` | `(arg0: long)` | `String` | Converts/serializes representation via `toFullDateMinuteString` |
| `static` | `getDaysBetween` | `(arg0: long, arg1: long)` | `int` | Retrieves `DaysBetween` property from `SQTime` |
| `static` | `getMonthsBetween` | `(arg0: long, arg1: long)` | `int` | Retrieves `MonthsBetween` property from `SQTime` |
| `static` | `getYearsBetween` | `(arg0: long, arg1: long)` | `int` | Retrieves `YearsBetween` property from `SQTime` |
| `static` | `formatDateTime` | `(arg0: long)` | `String` | Converts/serializes representation via `formatDateTime` |
| `static` | `toDateMinuteString` | `(arg0: long)` | `String` | Converts/serializes representation via `toDateMinuteString` |
| `static` | `toDateString` | `(arg0: long)` | `String` | Converts/serializes representation via `toDateString` |
| `static` | `correctDayEnd` | `(arg0: long)` | `long` | Performs correct day end operation |
| `static` | `setHour` | `(arg0: long, arg1: int)` | `long` | Sets `Hour` configuration/state on `SQTime` |
| `static` | `setMinute` | `(arg0: long, arg1: int)` | `long` | Sets `Minute` configuration/state on `SQTime` |
| `static` | `formatDate` | `(arg0: long)` | `String` | Converts/serializes representation via `formatDate` |
| `static` | `formatDate` | `(arg0: long, arg1: DateTimeFormatter)` | `String` | Converts/serializes representation via `formatDate` |
| `static` | `getMilis` | `(arg0: long)` | `long` | Retrieves `Milis` property from `SQTime` |
| `static` | `setHHMM` | `(arg0: long, arg1: int)` | `long` | Sets `HHMM` configuration/state on `SQTime` |
| `static` | `correctDayEndMT` | `(arg0: long)` | `long` | Performs correct day end mt operation |
| `static` | `getMinutesBetween` | `(arg0: long, arg1: long)` | `int` | Retrieves `MinutesBetween` property from `SQTime` |
| `static` | `addWeeks` | `(arg0: long, arg1: int)` | `long` | Appends/registers element via `addWeeks` |
| `static` | `getWeekOfYear` | `(arg0: long)` | `int` | Retrieves `WeekOfYear` property from `SQTime` |
| `static` | `getLocalCurrentTimeInMs` | `()` | `long` | Retrieves `LocalCurrentTimeInMs` property from `SQTime` |
| `static` | `parseDateToMilis` | `(arg0: String)` | `long` | Converts/serializes representation via `parseDateToMilis` |
| `static` | `toTime` | `(arg0: long)` | `Date` | Converts/serializes representation via `toTime` |
| `static` | `toLong` | `(arg0: int, arg1: int, arg2: int, arg3: int, arg4: int, arg5: int)` | `long` | Converts/serializes representation via `toLong` |
| `static` | `toLong` | `(arg0: int, arg1: int, arg2: int)` | `long` | Converts/serializes representation via `toLong` |
| `static` | `HHMMToMinutes` | `(arg0: int)` | `int` | Performs hhmm to minutes operation |
| `static` | `addSeconds` | `(arg0: long, arg1: int)` | `long` | Appends/registers element via `addSeconds` |
| `static` | `getLogTime` | `(arg0: boolean, arg1: boolean)` | `String` | Retrieves `LogTime` property from `SQTime` |
| `static` | `toDate` | `(arg0: long)` | `Date` | Converts/serializes representation via `toDate` |
| `static` | `getDateTime` | `(arg0: long)` | `int` | Retrieves `DateTime` property from `SQTime` |
| `static` | `getWeeksBetween` | `(arg0: long, arg1: long)` | `int` | Retrieves `WeeksBetween` property from `SQTime` |
| `static` | `formatTime` | `(arg0: long)` | `String` | Converts/serializes representation via `formatTime` |
| `static` | `formatDateQuick` | `(arg0: long)` | `String` | Converts/serializes representation via `formatDateQuick` |
| `static` | `parseToMilis` | `(arg0: String, arg1: String)` | `long` | Converts/serializes representation via `parseToMilis` |
| `static` | `minutesToHHMM` | `(arg0: int)` | `int` | Performs minutes to hhmm operation |
| `static` | `toUIDateString` | `(arg0: long)` | `String` | Converts/serializes representation via `toUIDateString` |
| `static` | `getTimeAsTSTime` | `(arg0: long)` | `int` | Retrieves `TimeAsTSTime` property from `SQTime` |
| `static` | `addMinutes` | `(arg0: long, arg1: int)` | `long` | Appends/registers element via `addMinutes` |
| `static` | `getMiliSecond` | `(arg0: long)` | `int` | Retrieves `MiliSecond` property from `SQTime` |
| `static` | `toFullTime` | `(arg0: long)` | `String` | Converts/serializes representation via `toFullTime` |
| `static` | `dowToMetatrader` | `(arg0: int)` | `int` | Performs dow to metatrader operation |
| `static` | `dowToString` | `(arg0: int)` | `String` | Performs dow to string operation |
| `static` | `timesInSameMinute` | `(arg0: int, arg1: int)` | `boolean` | Performs times in same minute operation |
| `static` | `toNumberTime` | `(arg0: long)` | `int` | Converts/serializes representation via `toNumberTime` |
| `static` | `setTimeToTSTime` | `(arg0: long, arg1: int)` | `long` | Sets `TimeToTSTime` configuration/state on `SQTime` |
| `static` | `getTSDiffInMinutes` | `(arg0: int, arg1: int)` | `int` | Retrieves `TSDiffInMinutes` property from `SQTime` |
| `static` | `toHHMMString` | `(arg0: long)` | `String` | Converts/serializes representation via `toHHMMString` |
| `static` | `getDurationText` | `(arg0: long)` | `String` | Retrieves `DurationText` property from `SQTime` |

---

### `SQUtils`
- **Full Qualified Name:** `com.strategyquant.lib.SQUtils`
- **Primary Job / Responsibility:** The Class SQUtils.

#### Methods & Functions
| Modifiers | Method Name | Parameter Signatures | Return Type | Functional Description / Job |
| :--- | :--- | :--- | :--- | :--- |
| `instance` | `equals` | `(arg0: Object)` | `boolean` | Performs equals operation |
| `instance` | `toString` | `()` | `String` | Converts/serializes representation via `toString` |
| `instance` | `hashCode` | `()` | `int` | Evaluates boolean predicate `hashCode` on `SQUtils` |
| `instance` | `getClass` | `()` | `Class` | Retrieves `Class` property from `SQUtils` |
| `instance` | `notify` | `()` | `void` | Performs notify operation |
| `instance` | `notifyAll` | `()` | `void` | Performs notify all operation |
| `instance` | `wait` | `(arg0: long)` | `void` | Performs wait operation |
| `instance` | `wait` | `(arg0: long, arg1: int)` | `void` | Performs wait operation |
| `instance` | `wait` | `()` | `void` | Performs wait operation |
| `static` | `getStackTrace` | `(arg0: Throwable)` | `String` | Retrieves `StackTrace` property from `SQUtils` |
| `static` | `getStackTrace` | `()` | `String` | Retrieves `StackTrace` property from `SQUtils` |
| `static` | `round` | `(arg0: double, arg1: int)` | `Integer` | Round. |
| `static` | `round` | `(arg0: double)` | `Integer` | Round. |
| `static` | `compare` | `(arg0: double, arg1: double, arg2: int)` | `int` | Performs compare operation |
| `static` | `replaceAll` | `(arg0: String, arg1: String, arg2: String)` | `String` | Performs replace all operation |
| `static` | `format` | `(arg0: double, arg1: int)` | `String` | Converts/serializes representation via `format` |
| `static` | `getClasses` | `(arg0: Class)` | `String` | Retrieves `Classes` property from `SQUtils` |
| `static` | `writeUTF` | `(arg0: ObjectOutput, arg1: String)` | `void` | Performs write utf operation |
| `static` | `readUTF` | `(arg0: ObjectInput)` | `String` | Performs read utf operation |
| `static` | `d2` | `(arg0: Number)` | `String` | Performs d 2 operation |
| `static` | `d2` | `(arg0: double)` | `String` | Performs d 2 operation |
| `static` | `createFile` | `(arg0: String)` | `File` | Creates a new file including parent folders |
| `static` | `getExtension` | `(arg0: String)` | `String` | Get extension. |
| `static` | `invokeUnchecked` | `(arg0: Constructor, arg1: Object[])` | `Object` | Performs invoke unchecked operation |
| `static` | `round6` | `(arg0: double)` | `double` | Performs round 6 operation |
| `static` | `fixAllowedRange` | `(arg0: int, arg1: int, arg2: int, arg3: int)` | `int` | Performs fix allowed range operation |
| `static` | `doubleToString` | `(arg0: double)` | `String` | Performs double to string operation |
| `static` | `longHashCode` | `(arg0: String)` | `long` | Performs long hash code operation |
| `static` | `safeDivide` | `(arg0: double, arg1: double)` | `double` | Safe divide. |
| `static` | `fixPrice` | `(arg0: double, arg1: double)` | `double` | method checks if the price is valid (is within defined tickStep), and if not it rounds the price to the tickStep |
| `static` | `fixPrice` | `(arg0: double, arg1: double, arg2: int)` | `double` | method checks if the price is valid (is within defined tickStep), and if not it rounds the price to the tickStep |
| `static` | `round2` | `(arg0: double)` | `double` | Round2. |
| `static` | `extractNumber` | `(arg0: String)` | `String` | Removes all non-numeric characters |
| `static` | `d2String` | `(arg0: double, arg1: int)` | `String` | Performs d 2 string operation |
| `static` | `formatBytesToHumanFormat` | `(arg0: long)` | `String` | Converts/serializes representation via `formatBytesToHumanFormat` |
| `static` | `insertUppercaseSpaces` | `(arg0: String)` | `String` | add space before every capital letter |
| `static` | `intsHash` | `(arg0: int[])` | `int` | Performs ints hash operation |
| `static` | `booleansHash` | `(arg0: boolean[])` | `int` | Performs booleans hash operation |
| `static` | `doublesHash` | `(arg0: double[])` | `int` | Performs doubles hash operation |
| `static` | `checkEngine` | `(arg0: String, arg1: String)` | `boolean` | Performs check engine operation |
| `static` | `round7` | `(arg0: double)` | `double` | Performs round 7 operation |
| `static` | `fixExitmethodAttributes` | `(arg0: Element)` | `void` | Performs fix exitmethod attributes operation |
| `static` | `renameActionParams` | `(arg0: String)` | `String` | Performs rename action params operation |
| `static` | `shortenWord` | `(arg0: String, arg1: int)` | `String` | Performs shorten word operation |
| `static` | `roundDown` | `(arg0: double, arg1: int)` | `double` | Round down. |
| `static` | `formatDate` | `(arg0: long, arg1: String)` | `String` | Returns formatted Date string |
| `static` | `fileToString` | `(arg0: File)` | `String` | File to string. |
| `static` | `fileToString` | `(arg0: String)` | `String` | File to string. |
| `static` | `fileToString` | `(arg0: File, arg1: String)` | `String` | File to string. |
| `static` | `removeHtmlTags` | `(arg0: String)` | `String` | Removes all html tags |
| `static` | `cloneValuesMap` | `(arg0: Int2ObjectOpenHashMap)` | `Int2ObjectOpenHashMap` | Performs clone values map operation |
| `static` | `betterHashCode` | `(arg0: String)` | `int` | standard String.hashCode() produces collisions - "ATR".hashCode() and "ADX".hashCode() hashes differ only by few hundreds.    This solution is combination of:  https://medium.com/@vaibhav0109/https-medium-com-vaibhav0109-java-hashcode-collision-how-uniform-is-its-distribution-ee4e5e8dc894  https://vanilla-java.github.io/2018/08/15/Looking-at-randomness-and-performance-for-hash-codes.html |
| `static` | `cloneObject` | `(arg0: Object)` | `Object` | Performs clone object operation |
| `static` | `readUTFIntern` | `(arg0: ObjectInput)` | `String` | Performs read utf intern operation |
| `static` | `decodeXmlKey` | `(arg0: String)` | `String` | Performs decode xml key operation |
| `static` | `ensureDirExists` | `(arg0: String)` | `void` | Performs ensure dir exists operation |
| `static` | `generateUniqueName` | `(arg0: String, arg1: IUniqueNameChecker)` | `String` | checks if this name isn't occupied already, if yes it will create a new name by adding (or increasing) number to it  Name, Name (2), Name (3) and so on. |
| `static` | `encodeXmlKey` | `(arg0: String)` | `String` | Performs encode xml key operation |
| `static` | `joinStrings` | `(arg0: String[])` | `String` | Join strings. |
| `static` | `stringToFile` | `(arg0: File, arg1: String)` | `void` | String to file. |
| `static` | `stringToFile` | `(arg0: String, arg1: String)` | `void` | String to file. |
| `static` | `getDecimalPlaces` | `(arg0: double)` | `int` | Retrieves `DecimalPlaces` property from `SQUtils` |
| `static` | `deleteDirectory` | `(arg0: String)` | `boolean` | Delete directory. |
| `static` | `stripExtension` | `(arg0: String)` | `String` | Strip extension. |
| `static` | `createAndHandleBackupFiles` | `(arg0: String, arg1: String, arg2: int)` | `void` | Instantiates/initializes `createAndHandleBackupFiles` resource |
| `static` | `createAndHandleBackupFiles` | `(arg0: String)` | `void` | Instantiates/initializes `createAndHandleBackupFiles` resource |
| `static` | `listBackupFiles` | `(arg0: String)` | `JSONArray` | Performs list backup files operation |
| `static` | `fileToArrayList` | `(arg0: ArrayList, arg1: String, arg2: String)` | `void` | Performs file to array list operation |
| `static` | `replaceLast` | `(arg0: String, arg1: String, arg2: String)` | `String` | Replace last. |
| `static` | `betterHashNumbers` | `(arg0: int[])` | `int` | Performs better hash numbers operation |
| `static` | `correctResultKeyToDirname` | `(arg0: String)` | `String` | Performs correct result key to dirname operation |
| `static` | `inputStreamToString` | `(arg0: InputStream)` | `String` | Input stream to string. |
| `static` | `removeUTF8BOM` | `(arg0: String)` | `String` | Removes BOM character that causes SAX ParseException error |
| `static` | `adjustToTickSize` | `(arg0: double, arg1: double)` | `double` | Rounds the price to the nearest tick |
| `static` | `isInStringArray` | `(arg0: String, arg1: ArrayList)` | `boolean` | Evaluates boolean predicate `isInStringArray` on `SQUtils` |
| `static` | `stackTraceToString` | `(arg0: Throwable)` | `String` | Performs stack trace to string operation |
| `static` | `deleteRecursive` | `(arg0: File)` | `boolean` | By default File#delete fails for non-empty directories, it works like "rm".   We need something a little more brutual - this does the equivalent of "rm -r" |
| `static` | `correctClassName` | `(arg0: String)` | `String` | Performs correct class name operation |
| `static` | `formatDuration` | `(arg0: long)` | `String` | Converts/serializes representation via `formatDuration` |
| `static` | `isInByteArray` | `(arg0: byte, arg1: byte[])` | `boolean` | Evaluates boolean predicate `isInByteArray` on `SQUtils` |
| `static` | `optimizeLastSettings` | `(arg0: String)` | `String` | Performs optimize last settings operation |
| `static` | `fixRenamedActionParams` | `(arg0: String)` | `String` | Performs fix renamed action params operation |
| `static` | `removeXmlns` | `(arg0: String)` | `String` | Removes/resets elements via `removeXmlns` |
| `static` | `fixHeikenAshi` | `(arg0: String)` | `String` | Performs fix heiken ashi operation |
| `static` | `listSubdirectories` | `(arg0: String)` | `ArrayList` | returns list of subdirectories in given directory (recursive) |
| `static` | `arrayListToFile` | `(arg0: ArrayList, arg1: String, arg2: String)` | `void` | Performs array list to file operation |
| `static` | `roundLong` | `(arg0: double)` | `Long` | Performs round long operation |
| `static` | `levenshteinDistance` | `(arg0: CharSequence, arg1: CharSequence)` | `int` | Performs levenshtein distance operation |
| `static` | `trimFilePath` | `(arg0: String, arg1: String)` | `String` | Performs trim file path operation |
| `static` | `getFirstFileFromDir` | `(arg0: File)` | `File` | Gets the first file from dir. |
| `static` | `deleteNestedFiles` | `(arg0: File)` | `boolean` | Performs delete nested files operation |
| `static` | `inputStreamToBytes` | `(arg0: InputStream)` | `byte[]` | Input stream to bytes. |
| `static` | `dCommon` | `(arg0: double, arg1: long)` | `String` | Performs d common operation |
| `static` | `isVowel` | `(arg0: char)` | `boolean` | Evaluates boolean predicate `isVowel` on `SQUtils` |
| `static` | `httpGet` | `(arg0: String, arg1: int)` | `String` | Performs http get operation |
| `static` | `httpGet` | `(arg0: String)` | `String` | Performs http get operation |
| `static` | `cloneArrayList` | `(arg0: ArrayList)` | `ArrayList` | Performs clone array list operation |
| `static` | `openUrlInDefaultWebBrowser` | `(arg0: String)` | `void` | Open url in default web browser. |
| `static` | `forceOpenUrlInDefaultWebBrowser` | `(arg0: String, arg1: Component)` | `void` | Force open url in default web browser. |
| `static` | `fileToBytes` | `(arg0: File)` | `byte[]` | File to bytes. |
| `static` | `md5CheckSum` | `(arg0: byte[])` | `String` | Md5 check sum. |
| `static` | `file2md5Hash` | `(arg0: File)` | `String` | Performs file 2 md 5 hash operation |
| `static` | `toFileUrl` | `(arg0: String)` | `String` | Converts/serializes representation via `toFileUrl` |
| `static` | `checkWorkDirectoryIsWritable` | `(arg0: String)` | `boolean` | Check work directory is writable. |
| `static` | `convertPriceToInt` | `(arg0: double, arg1: int)` | `int` | Performs convert price to int operation |
| `static` | `remapFilePathByMap` | `(arg0: String, arg1: Map)` | `String` | Performs remap file path by map operation |
| `static` | `listToStringArray` | `(arg0: ArrayList)` | `String[]` | List to string array. |
| `static` | `loadDataFromServer` | `(arg0: String)` | `byte[]` | Load data from server. |
| `static` | `inputStreamToFile` | `(arg0: InputStream, arg1: File)` | `void` | Input stream to file. |
| `static` | `saveFileAs` | `(arg0: byte[], arg1: String, arg2: String)` | `String` | Save file as. |
| `static` | `getTimeFromDate` | `(arg0: String, arg1: String)` | `long` | Transforms date string to long |
| `static` | `dateFormatValid` | `(arg0: String, arg1: String)` | `boolean` | Performs date format valid operation |
| `static` | `callMethod` | `(arg0: Object, arg1: String, arg2: Object[], arg3: boolean)` | `Object` | Performs call method operation |
| `static` | `callMethod` | `(arg0: Object, arg1: String, arg2: Object[], arg3: Class[])` | `Object` | Performs call method operation |
| `static` | `callMethod` | `(arg0: Object, arg1: String, arg2: Object, arg3: Class)` | `Object` | Performs call method operation |
| `static` | `callMethod` | `(arg0: Object, arg1: String, arg2: Object)` | `Object` | Performs call method operation |
| `static` | `correctDirnameToResultKey` | `(arg0: String)` | `String` | Performs correct dirname to result key operation |
| `static` | `fixPriceSpecial` | `(arg0: int, arg1: double, arg2: double, arg3: int)` | `double` | Performs fix price special operation |
| `static` | `countFilesInDirectory` | `(arg0: String)` | `int` | Performs count files in directory operation |
| `static` | `correctNullString` | `(arg0: String)` | `String` | Performs correct null string operation |
| `static` | `computeFileHash` | `(arg0: String, arg1: int)` | `int` | Executes calculation for `computeFileHash` |
| `static` | `addToErrors` | `(arg0: ArrayList, arg1: String)` | `ArrayList` | Appends/registers element via `addToErrors` |
| `static` | `loadLines` | `(arg0: String, arg1: String)` | `ArrayList` | Performs load lines operation |
| `static` | `pctToDouble` | `(arg0: int)` | `double` | Performs pct to double operation |
| `static` | `httpUploadFile` | `(arg0: String, arg1: String, arg2: Map, arg3: String, arg4: String, arg5: byte[])` | `String` | Performs http upload file operation |
| `static` | `httpPost` | `(arg0: String, arg1: String, arg2: Map)` | `String` | Performs http post operation |
| `static` | `httpsPost` | `(arg0: String, arg1: List, arg2: boolean)` | `String` | Performs https post operation |
| `static` | `doublesAreEqual` | `(arg0: double, arg1: double)` | `boolean` | Performs doubles are equal operation |
| `static` | `convertIntTimetoHHMM` | `(arg0: int)` | `String` | Performs convert int timeto hhmm operation |
| `static` | `cloneHashMap` | `(arg0: HashMap)` | `HashMap` | Performs clone hash map operation |
| `static` | `cloneValuesMapOld` | `(arg0: HashMap)` | `HashMap` | Performs clone values map old operation |
| `static` | `waitForKey` | `(arg0: String)` | `void` | Performs wait for key operation |
| `static` | `toJSONArray` | `(arg0: String)` | `JSONArray` | Converts/serializes representation via `toJSONArray` |
| `static` | `xmlPrettyFormat` | `(arg0: String)` | `String` | Performs xml pretty format operation |
| `static` | `getFileCrc` | `(arg0: File)` | `long` | Retrieves `FileCrc` property from `SQUtils` |

---

### `SettingsMap`
- **Full Qualified Name:** `com.strategyquant.lib.SettingsMap`
- **Primary Job / Responsibility:** Foundational utility and data structure container (`SettingsMap`).

#### Fields
| Scope | Field Name | Type |
| :--- | :--- | :--- |
| `static` | `BYTE_MISSING` | `byte` |
| `static` | `DOUBLE_MISSING` | `double` |
| `static` | `FLOAT_MISSING` | `float` |
| `static` | `INT_MISSING` | `int` |
| `static` | `LONG_MISSING` | `long` |
| `static` | `Log` | `Logger` |

#### Methods & Functions
| Modifiers | Method Name | Parameter Signatures | Return Type | Functional Description / Job |
| :--- | :--- | :--- | :--- | :--- |
| `instance` | `clone` | `()` | `ValuesMap` | Performs clone operation |
| `instance` | `clone` | `()` | `ValuesMap` | Performs clone operation |
| `instance` | `clone` | `()` | `ValuesMap` | Performs clone operation |
| `instance` | `getXML` | `()` | `Element` | Retrieves `XML` property from `SettingsMap` |
| `instance` | `setIfNotExists` | `(arg0: String, arg1: Object)` | `void` | Sets `IfNotExists` configuration/state on `SettingsMap` |
| `instance` | `remove` | `(arg0: String)` | `void` | Removes/resets elements via `remove` |
| `instance` | `remove` | `(arg0: int)` | `void` | Removes/resets elements via `remove` |
| `instance` | `get` | `(arg0: String)` | `Object` | Retrieves `` property from `SettingsMap` |
| `instance` | `get` | `(arg0: String, arg1: Object)` | `Object` | Retrieves `` property from `SettingsMap` |
| `instance` | `get` | `(arg0: int)` | `Object` | Retrieves `` property from `SettingsMap` |
| `instance` | `hashCode` | `()` | `int` | Evaluates boolean predicate `hashCode` on `SettingsMap` |
| `instance` | `getBoolean` | `(arg0: String)` | `boolean` | Retrieves `Boolean` property from `SettingsMap` |
| `instance` | `getBoolean` | `(arg0: String, arg1: boolean)` | `boolean` | Retrieves `Boolean` property from `SettingsMap` |
| `instance` | `getInt` | `(arg0: String, arg1: int)` | `int` | Retrieves `Int` property from `SettingsMap` |
| `instance` | `getInt` | `(arg0: String)` | `int` | Retrieves `Int` property from `SettingsMap` |
| `instance` | `getLong` | `(arg0: String, arg1: long)` | `long` | Retrieves `Long` property from `SettingsMap` |
| `instance` | `getLong` | `(arg0: String)` | `long` | Retrieves `Long` property from `SettingsMap` |
| `instance` | `getDouble` | `(arg0: String, arg1: double)` | `double` | Retrieves `Double` property from `SettingsMap` |
| `instance` | `getDouble` | `(arg0: String)` | `double` | Retrieves `Double` property from `SettingsMap` |
| `instance` | `clear` | `()` | `void` | Removes/resets elements via `clear` |
| `instance` | `set` | `(arg0: String, arg1: Object)` | `void` | Sets `` configuration/state on `SettingsMap` |
| `instance` | `set` | `(arg0: int, arg1: Object)` | `void` | Sets `` configuration/state on `SettingsMap` |
| `instance` | `containsKey` | `(arg0: int)` | `boolean` | Performs contains key operation |
| `instance` | `containsKey` | `(arg0: String)` | `boolean` | Performs contains key operation |
| `instance` | `getString` | `(arg0: String)` | `String` | Retrieves `String` property from `SettingsMap` |
| `instance` | `getString` | `(arg0: String, arg1: String)` | `String` | Retrieves `String` property from `SettingsMap` |
| `instance` | `toJSON` | `()` | `JSONObject` | Converts/serializes representation via `toJSON` |
| `instance` | `setString` | `(arg0: String, arg1: String)` | `void` | Sets `String` configuration/state on `SettingsMap` |
| `instance` | `setFromXML` | `(arg0: Element, arg1: int[])` | `void` | Sets `FromXML` configuration/state on `SettingsMap` |
| `instance` | `setFromXML` | `(arg0: Element)` | `void` | Sets `FromXML` configuration/state on `SettingsMap` |
| `instance` | `getAllKeys` | `()` | `String[]` | Retrieves `AllKeys` property from `SettingsMap` |
| `instance` | `removeUnsavableValues` | `()` | `void` | Removes/resets elements via `removeUnsavableValues` |
| `instance` | `removeIgnoredKeys` | `(arg0: int[])` | `void` | Removes/resets elements via `removeIgnoredKeys` |
| `instance` | `equals` | `(arg0: Object)` | `boolean` | Performs equals operation |
| `instance` | `toString` | `()` | `String` | Converts/serializes representation via `toString` |
| `instance` | `getClass` | `()` | `Class` | Retrieves `Class` property from `SettingsMap` |
| `instance` | `notify` | `()` | `void` | Performs notify operation |
| `instance` | `notifyAll` | `()` | `void` | Performs notify all operation |
| `instance` | `wait` | `(arg0: long)` | `void` | Performs wait operation |
| `instance` | `wait` | `(arg0: long, arg1: int)` | `void` | Performs wait operation |
| `instance` | `wait` | `()` | `void` | Performs wait operation |
| `static` | `getInt` | `(arg0: Object, arg1: int)` | `int` | Retrieves `Int` property from `SettingsMap` |
| `static` | `getLong` | `(arg0: Object, arg1: long)` | `long` | Retrieves `Long` property from `SettingsMap` |
| `static` | `getDouble` | `(arg0: Object, arg1: double)` | `double` | Retrieves `Double` property from `SettingsMap` |
| `static` | `getBool` | `(arg0: Object, arg1: boolean)` | `boolean` | Retrieves `Bool` property from `SettingsMap` |
| `static` | `getStatsIntKeyFromString` | `(arg0: String)` | `int` | Retrieves `StatsIntKeyFromString` property from `SettingsMap` |
| `static` | `fromJSON` | `(arg0: JSONObject)` | `ValuesMap` | Performs from json operation |

---

### `TaskStoppedException`
- **Full Qualified Name:** `com.strategyquant.lib.TaskStoppedException`
- **Primary Job / Responsibility:** Foundational utility and data structure container (`TaskStoppedException`).

#### Methods & Functions
| Modifiers | Method Name | Parameter Signatures | Return Type | Functional Description / Job |
| :--- | :--- | :--- | :--- | :--- |
| `instance` | `printStackTrace` | `()` | `void` | Performs print stack trace operation |
| `instance` | `printStackTrace` | `(arg0: PrintWriter)` | `void` | Performs print stack trace operation |
| `instance` | `printStackTrace` | `(arg0: PrintStream)` | `void` | Performs print stack trace operation |
| `instance` | `getStackTrace` | `()` | `StackTraceElement[]` | Retrieves `StackTrace` property from `TaskStoppedException` |
| `instance` | `fillInStackTrace` | `()` | `Throwable` | Performs fill in stack trace operation |
| `instance` | `getCause` | `()` | `Throwable` | Retrieves `Cause` property from `TaskStoppedException` |
| `instance` | `initCause` | `(arg0: Throwable)` | `Throwable` | Instantiates/initializes `initCause` resource |
| `instance` | `toString` | `()` | `String` | Converts/serializes representation via `toString` |
| `instance` | `getMessage` | `()` | `String` | Retrieves `Message` property from `TaskStoppedException` |
| `instance` | `getSuppressed` | `()` | `Throwable[]` | Retrieves `Suppressed` property from `TaskStoppedException` |
| `instance` | `getLocalizedMessage` | `()` | `String` | Retrieves `LocalizedMessage` property from `TaskStoppedException` |
| `instance` | `setStackTrace` | `(arg0: StackTraceElement[])` | `void` | Sets `StackTrace` configuration/state on `TaskStoppedException` |
| `instance` | `addSuppressed` | `(arg0: Throwable)` | `void` | Appends/registers element via `addSuppressed` |
| `instance` | `equals` | `(arg0: Object)` | `boolean` | Performs equals operation |
| `instance` | `hashCode` | `()` | `int` | Evaluates boolean predicate `hashCode` on `TaskStoppedException` |
| `instance` | `getClass` | `()` | `Class` | Retrieves `Class` property from `TaskStoppedException` |
| `instance` | `notify` | `()` | `void` | Performs notify operation |
| `instance` | `notifyAll` | `()` | `void` | Performs notify all operation |
| `instance` | `wait` | `(arg0: long)` | `void` | Performs wait operation |
| `instance` | `wait` | `(arg0: long, arg1: int)` | `void` | Performs wait operation |
| `instance` | `wait` | `()` | `void` | Performs wait operation |

---

### `TimePeriod`
- **Full Qualified Name:** `com.strategyquant.lib.TimePeriod`
- **Primary Job / Responsibility:** High-precision financial timestamp manipulation and timezone normalization (`TimePeriod`).

#### Fields
| Scope | Field Name | Type |
| :--- | :--- | :--- |
| `instance` | `from` | `long` |
| `instance` | `name` | `String` |
| `instance` | `note` | `String` |
| `instance` | `to` | `long` |
| `instance` | `type` | `byte` |
| `instance` | `value` | `double` |

#### Methods & Functions
| Modifiers | Method Name | Parameter Signatures | Return Type | Functional Description / Job |
| :--- | :--- | :--- | :--- | :--- |
| `instance` | `clone` | `()` | `TimePeriod` | Performs clone operation |
| `instance` | `clone` | `()` | `TimePeriod` | Performs clone operation |
| `instance` | `equals` | `(arg0: Object)` | `boolean` | Performs equals operation |
| `instance` | `toString` | `()` | `String` | Converts/serializes representation via `toString` |
| `instance` | `hashCode` | `()` | `int` | Evaluates boolean predicate `hashCode` on `TimePeriod` |
| `instance` | `getClass` | `()` | `Class` | Retrieves `Class` property from `TimePeriod` |
| `instance` | `notify` | `()` | `void` | Performs notify operation |
| `instance` | `notifyAll` | `()` | `void` | Performs notify all operation |
| `instance` | `wait` | `(arg0: long)` | `void` | Performs wait operation |
| `instance` | `wait` | `(arg0: long, arg1: int)` | `void` | Performs wait operation |
| `instance` | `wait` | `()` | `void` | Performs wait operation |

---

### `TimePeriods`
- **Full Qualified Name:** `com.strategyquant.lib.TimePeriods`
- **Primary Job / Responsibility:** High-precision financial timestamp manipulation and timezone normalization (`TimePeriods`).

#### Fields
| Scope | Field Name | Type |
| :--- | :--- | :--- |
| `static` | `Log` | `Logger` |

#### Methods & Functions
| Modifiers | Method Name | Parameter Signatures | Return Type | Functional Description / Job |
| :--- | :--- | :--- | :--- | :--- |
| `instance` | `clone` | `()` | `TimePeriods` | Performs clone operation |
| `instance` | `clone` | `()` | `TimePeriods` | Performs clone operation |
| `instance` | `clone` | `()` | `TimePeriods` | Performs clone operation |
| `instance` | `print` | `()` | `void` | Performs print operation |
| `instance` | `remove` | `(arg0: long)` | `boolean` | Removes/resets elements via `remove` |
| `instance` | `remove` | `(arg0: Object)` | `boolean` | Removes/resets elements via `remove` |
| `instance` | `remove` | `(arg0: long, arg1: Object)` | `boolean` | Removes/resets elements via `remove` |
| `instance` | `remove` | `(arg0: Object, arg1: Object)` | `boolean` | Removes/resets elements via `remove` |
| `instance` | `size` | `()` | `int` | Performs size operation |
| `instance` | `get` | `(arg0: long)` | `Object` | Retrieves `` property from `TimePeriods` |
| `instance` | `get` | `(arg0: Object)` | `Object` | Retrieves `` property from `TimePeriods` |
| `instance` | `put` | `(arg0: long, arg1: Object)` | `Object` | Performs put operation |
| `instance` | `put` | `(arg0: Object, arg1: Object)` | `Object` | Performs put operation |
| `instance` | `put` | `(arg0: Long, arg1: Object)` | `Object` | Performs put operation |
| `instance` | `values` | `()` | `ObjectCollection` | Performs values operation |
| `instance` | `values` | `()` | `ObjectCollection` | Performs values operation |
| `instance` | `clear` | `()` | `void` | Removes/resets elements via `clear` |
| `instance` | `isEmpty` | `()` | `boolean` | Evaluates boolean predicate `isEmpty` on `TimePeriods` |
| `instance` | `keySet` | `()` | `LongSortedSet` | Performs key set operation |
| `instance` | `keySet` | `()` | `LongSortedSet` | Performs key set operation |
| `instance` | `keySet` | `()` | `LongSortedSet` | Performs key set operation |
| `instance` | `containsValue` | `(arg0: Object)` | `boolean` | Performs contains value operation |
| `instance` | `containsKey` | `(arg0: long)` | `boolean` | Performs contains key operation |
| `instance` | `containsKey` | `(arg0: Object)` | `boolean` | Performs contains key operation |
| `instance` | `comparator` | `()` | `LongComparator` | Performs comparator operation |
| `instance` | `comparator` | `()` | `LongComparator` | Performs comparator operation |
| `instance` | `subMap` | `(arg0: long, arg1: long)` | `SortedMap` | Performs sub map operation |
| `instance` | `subMap` | `(arg0: Long, arg1: Long)` | `SortedMap` | Performs sub map operation |
| `instance` | `subMap` | `(arg0: Object, arg1: Object)` | `SortedMap` | Performs sub map operation |
| `instance` | `headMap` | `(arg0: long)` | `Long2ObjectSortedMap` | Performs head map operation |
| `instance` | `headMap` | `(arg0: Object)` | `Long2ObjectSortedMap` | Performs head map operation |
| `instance` | `headMap` | `(arg0: Long)` | `Long2ObjectSortedMap` | Performs head map operation |
| `instance` | `tailMap` | `(arg0: long)` | `SortedMap` | Performs tail map operation |
| `instance` | `tailMap` | `(arg0: Long)` | `SortedMap` | Performs tail map operation |
| `instance` | `tailMap` | `(arg0: Object)` | `SortedMap` | Performs tail map operation |
| `instance` | `long2ObjectEntrySet` | `()` | `ObjectSet` | Performs long 2 object entry set operation |
| `instance` | `long2ObjectEntrySet` | `()` | `ObjectSet` | Performs long 2 object entry set operation |
| `instance` | `firstLongKey` | `()` | `long` | Performs first long key operation |
| `instance` | `lastLongKey` | `()` | `long` | Performs last long key operation |
| `instance` | `equals` | `(arg0: Object)` | `boolean` | Performs equals operation |
| `instance` | `toString` | `()` | `String` | Converts/serializes representation via `toString` |
| `instance` | `hashCode` | `()` | `int` | Evaluates boolean predicate `hashCode` on `TimePeriods` |
| `instance` | `putAll` | `(arg0: Map)` | `void` | Performs put all operation |
| `instance` | `defaultReturnValue` | `(arg0: Object)` | `Object` | Performs default return value operation |
| `instance` | `defaultReturnValue` | `()` | `Object` | Performs default return value operation |
| `instance` | `getClass` | `()` | `Class` | Retrieves `Class` property from `TimePeriods` |
| `instance` | `notify` | `()` | `void` | Performs notify operation |
| `instance` | `notifyAll` | `()` | `void` | Performs notify all operation |
| `instance` | `wait` | `(arg0: long)` | `void` | Performs wait operation |
| `instance` | `wait` | `(arg0: long, arg1: int)` | `void` | Performs wait operation |
| `instance` | `wait` | `()` | `void` | Performs wait operation |
| `instance` | `apply` | `(arg0: long)` | `Object` | Performs apply operation |
| `instance` | `apply` | `(arg0: Object)` | `Object` | Performs apply operation |
| `instance` | `compose` | `(arg0: Function)` | `Function` | Performs compose operation |
| `instance` | `andThen` | `(arg0: Function)` | `Function` | Performs and then operation |
| `instance` | `replace` | `(arg0: Long, arg1: Object)` | `Object` | Performs replace operation |
| `instance` | `replace` | `(arg0: long, arg1: Object, arg2: Object)` | `Object` | Performs replace operation |
| `instance` | `replace` | `(arg0: long, arg1: Object)` | `Object` | Performs replace operation |
| `instance` | `replace` | `(arg0: Long, arg1: Object, arg2: Object)` | `Object` | Performs replace operation |
| `instance` | `replace` | `(arg0: Object, arg1: Object, arg2: Object)` | `Object` | Performs replace operation |
| `instance` | `replace` | `(arg0: Object, arg1: Object)` | `Object` | Performs replace operation |
| `instance` | `merge` | `(arg0: long, arg1: Object, arg2: BiFunction)` | `Object` | Performs merge operation |
| `instance` | `merge` | `(arg0: Long, arg1: Object, arg2: BiFunction)` | `Object` | Performs merge operation |
| `instance` | `merge` | `(arg0: Object, arg1: Object, arg2: BiFunction)` | `Object` | Performs merge operation |
| `instance` | `entrySet` | `()` | `Set` | Performs entry set operation |
| `instance` | `entrySet` | `()` | `Set` | Performs entry set operation |
| `instance` | `entrySet` | `()` | `Set` | Performs entry set operation |
| `instance` | `putIfAbsent` | `(arg0: Long, arg1: Object)` | `Object` | Performs put if absent operation |
| `instance` | `putIfAbsent` | `(arg0: Object, arg1: Object)` | `Object` | Performs put if absent operation |
| `instance` | `putIfAbsent` | `(arg0: long, arg1: Object)` | `Object` | Performs put if absent operation |
| `instance` | `compute` | `(arg0: Long, arg1: BiFunction)` | `Object` | Executes calculation for `compute` |
| `instance` | `compute` | `(arg0: Object, arg1: BiFunction)` | `Object` | Executes calculation for `compute` |
| `instance` | `compute` | `(arg0: long, arg1: BiFunction)` | `Object` | Executes calculation for `compute` |
| `instance` | `computeIfAbsent` | `(arg0: Object, arg1: Function)` | `Object` | Executes calculation for `computeIfAbsent` |
| `instance` | `computeIfAbsent` | `(arg0: Long, arg1: Function)` | `Object` | Executes calculation for `computeIfAbsent` |
| `instance` | `computeIfAbsent` | `(arg0: long, arg1: LongFunction)` | `Object` | Executes calculation for `computeIfAbsent` |
| `instance` | `getOrDefault` | `(arg0: Object, arg1: Object)` | `Object` | Retrieves `OrDefault` property from `TimePeriods` |
| `instance` | `getOrDefault` | `(arg0: long, arg1: Object)` | `Object` | Retrieves `OrDefault` property from `TimePeriods` |
| `instance` | `computeIfPresent` | `(arg0: Long, arg1: BiFunction)` | `Object` | Executes calculation for `computeIfPresent` |
| `instance` | `computeIfPresent` | `(arg0: long, arg1: BiFunction)` | `Object` | Executes calculation for `computeIfPresent` |
| `instance` | `computeIfPresent` | `(arg0: Object, arg1: BiFunction)` | `Object` | Executes calculation for `computeIfPresent` |
| `instance` | `computeIfAbsentPartial` | `(arg0: long, arg1: Long2ObjectFunction)` | `Object` | Executes calculation for `computeIfAbsentPartial` |
| `instance` | `replaceAll` | `(arg0: BiFunction)` | `void` | Performs replace all operation |
| `instance` | `forEach` | `(arg0: BiConsumer)` | `void` | Performs for each operation |
| `instance` | `firstKey` | `()` | `Long` | Performs first key operation |
| `instance` | `firstKey` | `()` | `Long` | Performs first key operation |
| `instance` | `lastKey` | `()` | `Long` | Performs last key operation |
| `instance` | `lastKey` | `()` | `Long` | Performs last key operation |
| `instance` | `reversed` | `()` | `SequencedMap` | Performs reversed operation |
| `instance` | `reversed` | `()` | `SequencedMap` | Performs reversed operation |
| `instance` | `putFirst` | `(arg0: Object, arg1: Object)` | `Object` | Performs put first operation |
| `instance` | `putLast` | `(arg0: Object, arg1: Object)` | `Object` | Performs put last operation |
| `instance` | `sequencedKeySet` | `()` | `SequencedSet` | Performs sequenced key set operation |
| `instance` | `sequencedValues` | `()` | `SequencedCollection` | Performs sequenced values operation |
| `instance` | `sequencedEntrySet` | `()` | `SequencedSet` | Performs sequenced entry set operation |
| `instance` | `firstEntry` | `()` | `Entry` | Performs first entry operation |
| `instance` | `lastEntry` | `()` | `Entry` | Performs last entry operation |
| `instance` | `pollFirstEntry` | `()` | `Entry` | Performs poll first entry operation |
| `instance` | `pollLastEntry` | `()` | `Entry` | Performs poll last entry operation |

---

### `ValuesMap`
- **Full Qualified Name:** `com.strategyquant.lib.ValuesMap`
- **Primary Job / Responsibility:** Foundational utility and data structure container (`ValuesMap`).

#### Fields
| Scope | Field Name | Type |
| :--- | :--- | :--- |
| `static` | `BYTE_MISSING` | `byte` |
| `static` | `DOUBLE_MISSING` | `double` |
| `static` | `FLOAT_MISSING` | `float` |
| `static` | `INT_MISSING` | `int` |
| `static` | `LONG_MISSING` | `long` |
| `static` | `Log` | `Logger` |

#### Methods & Functions
| Modifiers | Method Name | Parameter Signatures | Return Type | Functional Description / Job |
| :--- | :--- | :--- | :--- | :--- |
| `instance` | `remove` | `(arg0: String)` | `void` | Removes/resets elements via `remove` |
| `instance` | `remove` | `(arg0: int)` | `void` | Removes/resets elements via `remove` |
| `instance` | `get` | `(arg0: String)` | `Object` | Retrieves `` property from `ValuesMap` |
| `instance` | `get` | `(arg0: String, arg1: Object)` | `Object` | Retrieves `` property from `ValuesMap` |
| `instance` | `get` | `(arg0: int)` | `Object` | Retrieves `` property from `ValuesMap` |
| `instance` | `hashCode` | `()` | `int` | Evaluates boolean predicate `hashCode` on `ValuesMap` |
| `instance` | `clone` | `()` | `ValuesMap` | Performs clone operation |
| `instance` | `clone` | `()` | `ValuesMap` | Performs clone operation |
| `instance` | `getBoolean` | `(arg0: String)` | `boolean` | Retrieves `Boolean` property from `ValuesMap` |
| `instance` | `getBoolean` | `(arg0: String, arg1: boolean)` | `boolean` | Retrieves `Boolean` property from `ValuesMap` |
| `instance` | `getInt` | `(arg0: String, arg1: int)` | `int` | Retrieves `Int` property from `ValuesMap` |
| `instance` | `getInt` | `(arg0: String)` | `int` | Retrieves `Int` property from `ValuesMap` |
| `instance` | `getLong` | `(arg0: String, arg1: long)` | `long` | Retrieves `Long` property from `ValuesMap` |
| `instance` | `getLong` | `(arg0: String)` | `long` | Retrieves `Long` property from `ValuesMap` |
| `instance` | `getDouble` | `(arg0: String, arg1: double)` | `double` | Retrieves `Double` property from `ValuesMap` |
| `instance` | `getDouble` | `(arg0: String)` | `double` | Retrieves `Double` property from `ValuesMap` |
| `instance` | `clear` | `()` | `void` | Removes/resets elements via `clear` |
| `instance` | `set` | `(arg0: String, arg1: Object)` | `void` | Sets `` configuration/state on `ValuesMap` |
| `instance` | `set` | `(arg0: int, arg1: Object)` | `void` | Sets `` configuration/state on `ValuesMap` |
| `instance` | `containsKey` | `(arg0: int)` | `boolean` | Performs contains key operation |
| `instance` | `containsKey` | `(arg0: String)` | `boolean` | Performs contains key operation |
| `instance` | `getString` | `(arg0: String)` | `String` | Retrieves `String` property from `ValuesMap` |
| `instance` | `getString` | `(arg0: String, arg1: String)` | `String` | Retrieves `String` property from `ValuesMap` |
| `instance` | `toJSON` | `()` | `JSONObject` | Converts/serializes representation via `toJSON` |
| `instance` | `setString` | `(arg0: String, arg1: String)` | `void` | Sets `String` configuration/state on `ValuesMap` |
| `instance` | `setFromXML` | `(arg0: Element, arg1: int[])` | `void` | Sets `FromXML` configuration/state on `ValuesMap` |
| `instance` | `setFromXML` | `(arg0: Element)` | `void` | Sets `FromXML` configuration/state on `ValuesMap` |
| `instance` | `getAllKeys` | `()` | `String[]` | Retrieves `AllKeys` property from `ValuesMap` |
| `instance` | `getXML` | `()` | `Element` | Retrieves `XML` property from `ValuesMap` |
| `instance` | `removeUnsavableValues` | `()` | `void` | Removes/resets elements via `removeUnsavableValues` |
| `instance` | `removeIgnoredKeys` | `(arg0: int[])` | `void` | Removes/resets elements via `removeIgnoredKeys` |
| `instance` | `equals` | `(arg0: Object)` | `boolean` | Performs equals operation |
| `instance` | `toString` | `()` | `String` | Converts/serializes representation via `toString` |
| `instance` | `getClass` | `()` | `Class` | Retrieves `Class` property from `ValuesMap` |
| `instance` | `notify` | `()` | `void` | Performs notify operation |
| `instance` | `notifyAll` | `()` | `void` | Performs notify all operation |
| `instance` | `wait` | `(arg0: long)` | `void` | Performs wait operation |
| `instance` | `wait` | `(arg0: long, arg1: int)` | `void` | Performs wait operation |
| `instance` | `wait` | `()` | `void` | Performs wait operation |
| `static` | `getStatsIntKeyFromString` | `(arg0: String)` | `int` | Retrieves `StatsIntKeyFromString` property from `ValuesMap` |
| `static` | `fromJSON` | `(arg0: JSONObject)` | `ValuesMap` | Performs from json operation |

---

### `XMLUtil`
- **Full Qualified Name:** `com.strategyquant.lib.XMLUtil`
- **Primary Job / Responsibility:** Foundational utility and data structure container (`XMLUtil`).

#### Methods & Functions
| Modifiers | Method Name | Parameter Signatures | Return Type | Functional Description / Job |
| :--- | :--- | :--- | :--- | :--- |
| `instance` | `equals` | `(arg0: Object)` | `boolean` | Performs equals operation |
| `instance` | `toString` | `()` | `String` | Converts/serializes representation via `toString` |
| `instance` | `hashCode` | `()` | `int` | Evaluates boolean predicate `hashCode` on `XMLUtil` |
| `instance` | `getClass` | `()` | `Class` | Retrieves `Class` property from `XMLUtil` |
| `instance` | `notify` | `()` | `void` | Performs notify operation |
| `instance` | `notifyAll` | `()` | `void` | Performs notify all operation |
| `instance` | `wait` | `(arg0: long)` | `void` | Performs wait operation |
| `instance` | `wait` | `(arg0: long, arg1: int)` | `void` | Performs wait operation |
| `instance` | `wait` | `()` | `void` | Performs wait operation |
| `static` | `getBoolean` | `(arg0: Element, arg1: String, arg2: boolean)` | `boolean` | Retrieves `Boolean` property from `XMLUtil` |
| `static` | `getByte` | `(arg0: Element, arg1: String, arg2: byte)` | `byte` | Retrieves `Byte` property from `XMLUtil` |
| `static` | `getInt` | `(arg0: Element, arg1: String, arg2: int)` | `int` | Retrieves `Int` property from `XMLUtil` |
| `static` | `getLong` | `(arg0: Element, arg1: String, arg2: int)` | `long` | Retrieves `Long` property from `XMLUtil` |
| `static` | `getFloat` | `(arg0: Element, arg1: String, arg2: float)` | `float` | Retrieves `Float` property from `XMLUtil` |
| `static` | `getDouble` | `(arg0: Element, arg1: String, arg2: double)` | `double` | Retrieves `Double` property from `XMLUtil` |
| `static` | `findAll` | `(arg0: Element, arg1: String, arg2: ArrayList)` | `void` | Performs find all operation |
| `static` | `findFirst` | `(arg0: Element, arg1: String)` | `Element` | Performs find first operation |
| `static` | `valueHash` | `(arg0: int, arg1: Object)` | `int` | Performs value hash operation |
| `static` | `elementsEqual` | `(arg0: Element, arg1: Element)` | `boolean` | Performs elements equal operation |
| `static` | `elementToString` | `(arg0: Element)` | `String` | Performs element to string operation |
| `static` | `elementToString` | `(arg0: Element, arg1: boolean)` | `String` | Performs element to string operation |
| `static` | `xmlToStringRaw` | `(arg0: Element)` | `String` | Performs xml to string raw operation |
| `static` | `getNestedElements` | `(arg0: Element, arg1: String, arg2: String, arg3: String)` | `ArrayList` | Retrieves `NestedElements` property from `XMLUtil` |
| `static` | `getNestedElements` | `(arg0: Element, arg1: String)` | `ArrayList` | Retrieves `NestedElements` property from `XMLUtil` |
| `static` | `getItemParameterNoException` | `(arg0: Element, arg1: String)` | `Element` | Retrieves `ItemParameterNoException` property from `XMLUtil` |
| `static` | `removeAttribute` | `(arg0: Element, arg1: String)` | `void` | Removes/resets elements via `removeAttribute` |
| `static` | `getStringAttr` | `(arg0: Element, arg1: String, arg2: String)` | `String` | Retrieves `StringAttr` property from `XMLUtil` |
| `static` | `getBooleanAttr` | `(arg0: Element, arg1: String, arg2: boolean)` | `boolean` | Retrieves `BooleanAttr` property from `XMLUtil` |
| `static` | `getBooleanAttr` | `(arg0: Element, arg1: String)` | `boolean` | Retrieves `BooleanAttr` property from `XMLUtil` |
| `static` | `stringToElement` | `(arg0: String)` | `Element` | Performs string to element operation |
| `static` | `findFirstParent` | `(arg0: Element, arg1: String)` | `Element` | Performs find first parent operation |
| `static` | `getChildElem` | `(arg0: Element, arg1: String)` | `Element` | Retrieves `ChildElem` property from `XMLUtil` |
| `static` | `getChildElem` | `(arg0: Element, arg1: String, arg2: String)` | `Element` | Retrieves `ChildElem` property from `XMLUtil` |
| `static` | `elementIs` | `(arg0: Element, arg1: String)` | `boolean` | Performs element is operation |
| `static` | `elementIsNot` | `(arg0: Element, arg1: String)` | `boolean` | Performs element is not operation |
| `static` | `getIntAttr` | `(arg0: Element, arg1: String)` | `byte` | Retrieves `IntAttr` property from `XMLUtil` |
| `static` | `getIntAttr` | `(arg0: Element, arg1: String, arg2: int)` | `byte` | Retrieves `IntAttr` property from `XMLUtil` |
| `static` | `getIntAttr` | `(arg0: Element, arg1: String, arg2: byte)` | `byte` | Retrieves `IntAttr` property from `XMLUtil` |
| `static` | `getDoubleAttr` | `(arg0: Element, arg1: String, arg2: double)` | `double` | Retrieves `DoubleAttr` property from `XMLUtil` |
| `static` | `tryGetBoolAttr` | `(arg0: Element, arg1: String)` | `boolean` | Performs try get bool attr operation |
| `static` | `trySetAttr` | `(arg0: Element, arg1: String, arg2: Object)` | `void` | Performs try set attr operation |
| `static` | `elementToValue` | `(arg0: Element)` | `Object` | Performs element to value operation |
| `static` | `valueToElement` | `(arg0: String, arg1: Object)` | `Element` | Performs value to element operation |
| `static` | `tryGetLongAttr` | `(arg0: Element, arg1: String)` | `long` | Performs try get long attr operation |
| `static` | `tryGetIntAttr` | `(arg0: Element, arg1: String)` | `int` | Performs try get int attr operation |
| `static` | `getNodeValue` | `(arg0: Element, arg1: String)` | `String` | Retrieves `NodeValue` property from `XMLUtil` |
| `static` | `getNodeValue` | `(arg0: Element, arg1: String, arg2: String)` | `String` | Retrieves `NodeValue` property from `XMLUtil` |
| `static` | `stringToXmlElement` | `(arg0: String)` | `Element` | Performs string to xml element operation |
| `static` | `getNodeBooleanValue` | `(arg0: Element, arg1: String, arg2: boolean)` | `boolean` | Retrieves `NodeBooleanValue` property from `XMLUtil` |
| `static` | `getAttr` | `(arg0: Element, arg1: String)` | `String` | Retrieves `Attr` property from `XMLUtil` |
| `static` | `getAttr` | `(arg0: Element, arg1: String, arg2: String)` | `String` | Retrieves `Attr` property from `XMLUtil` |
| `static` | `getItemDoubleParam` | `(arg0: Element, arg1: String, arg2: double)` | `double` | Retrieves `ItemDoubleParam` property from `XMLUtil` |
| `static` | `setItemDoubleParam` | `(arg0: Element, arg1: String, arg2: double)` | `void` | Sets `ItemDoubleParam` configuration/state on `XMLUtil` |
| `static` | `getItemBoolParam` | `(arg0: Element, arg1: String, arg2: boolean)` | `boolean` | Retrieves `ItemBoolParam` property from `XMLUtil` |
| `static` | `getItemIntParam` | `(arg0: Element, arg1: String, arg2: int)` | `int` | Retrieves `ItemIntParam` property from `XMLUtil` |
| `static` | `setItemBoolParam` | `(arg0: Element, arg1: String, arg2: boolean)` | `void` | Sets `ItemBoolParam` configuration/state on `XMLUtil` |
| `static` | `setItemIntParam` | `(arg0: Element, arg1: String, arg2: int)` | `void` | Sets `ItemIntParam` configuration/state on `XMLUtil` |
| `static` | `tryAddElement` | `(arg0: Element, arg1: String)` | `Element` | Performs try add element operation |
| `static` | `fileToXmlElement` | `(arg0: File)` | `Element` | Performs file to xml element operation |
| `static` | `xmlToFile` | `(arg0: Document, arg1: File)` | `void` | Performs xml to file operation |
| `static` | `xmlToFile` | `(arg0: Element, arg1: File)` | `void` | Performs xml to file operation |
| `static` | `copyAttributes` | `(arg0: Element, arg1: Element, arg2: boolean)` | `void` | Performs copy attributes operation |
| `static` | `tryGetDoubleAttr` | `(arg0: Element, arg1: String)` | `double` | Performs try get double attr operation |
| `static` | `getByteAttr` | `(arg0: Element, arg1: String, arg2: byte)` | `byte` | Retrieves `ByteAttr` property from `XMLUtil` |
| `static` | `parseDate` | `(arg0: String)` | `long` | Converts/serializes representation via `parseDate` |
| `static` | `readXmlFile` | `(arg0: InputStream)` | `Element` | Performs read xml file operation |
| `static` | `findFirstWithKey` | `(arg0: Element, arg1: String, arg2: String)` | `Element` | Performs find first with key operation |
| `static` | `findAllWithKey` | `(arg0: Element, arg1: String, arg2: String, arg3: ArrayList)` | `void` | Performs find all with key operation |
| `static` | `xmlToString` | `(arg0: Element)` | `String` | Performs xml to string operation |
| `static` | `getItemParameter` | `(arg0: Element, arg1: String, arg2: boolean)` | `Element` | Retrieves `ItemParameter` property from `XMLUtil` |
| `static` | `tryGetAttr` | `(arg0: Element, arg1: String, arg2: String)` | `String` | Performs try get attr operation |
| `static` | `copyElement` | `(arg0: Element)` | `Element` | Performs copy element operation |
| `static` | `getOptionParameter` | `(arg0: Element, arg1: String)` | `Element` | Retrieves `OptionParameter` property from `XMLUtil` |
| `static` | `removeXMLCharacters` | `(arg0: String)` | `String` | Removes/resets elements via `removeXMLCharacters` |
| `static` | `getOrCreateChild` | `(arg0: Element, arg1: String)` | `Element` | Retrieves `OrCreateChild` property from `XMLUtil` |
| `static` | `replaceElementsWithAttribute` | `(arg0: Element, arg1: String, arg2: String, arg3: Element, arg4: String)` | `void` | Performs replace elements with attribute operation |
| `static` | `getLongAttr` | `(arg0: Element, arg1: String)` | `long` | Retrieves `LongAttr` property from `XMLUtil` |
| `static` | `elementLineToString` | `(arg0: Element)` | `String` | Performs element line to string operation |
| `static` | `tryAddNode` | `(arg0: Element, arg1: String, arg2: String)` | `Element` | Performs try add node operation |
| `static` | `stringToXml` | `(arg0: String)` | `Document` | Performs string to xml operation |
| `static` | `attributesEqual` | `(arg0: Element, arg1: Element)` | `boolean` | Performs attributes equal operation |
| `static` | `JSValuesEqual` | `(arg0: String, arg1: String)` | `boolean` | Performs js values equal operation |
| `static` | `countElements` | `(arg0: String, arg1: Element, arg2: int)` | `int` | Performs count elements operation |
| `static` | `getSubchildElementEx` | `(arg0: Element, arg1: String, arg2: String)` | `Element` | Retrieves `SubchildElementEx` property from `XMLUtil` |
| `static` | `hasChildElem` | `(arg0: Element, arg1: String)` | `boolean` | Evaluates boolean predicate `hasChildElem` on `XMLUtil` |
| `static` | `tryGetByteAttr` | `(arg0: Element, arg1: String)` | `byte` | Performs try get byte attr operation |
| `static` | `fileToXml` | `(arg0: File)` | `Document` | Performs file to xml operation |
| `static` | `tryAddBooleanNode` | `(arg0: Element, arg1: String, arg2: boolean)` | `Element` | Performs try add boolean node operation |
| `static` | `tryAddIntNode` | `(arg0: Element, arg1: String, arg2: int)` | `Element` | Performs try add int node operation |
| `static` | `tryAddDoubleNode` | `(arg0: Element, arg1: String, arg2: double)` | `Element` | Performs try add double node operation |
| `static` | `getNodeIntValue` | `(arg0: Element, arg1: String)` | `int` | Retrieves `NodeIntValue` property from `XMLUtil` |
| `static` | `getNodeIntValue` | `(arg0: Element, arg1: String, arg2: int)` | `int` | Retrieves `NodeIntValue` property from `XMLUtil` |
| `static` | `printXml` | `(arg0: Element)` | `void` | Performs print xml operation |
| `static` | `copySettings` | `(arg0: Element, arg1: Element, arg2: String)` | `void` | Performs copy settings operation |
| `static` | `getSubchildElement` | `(arg0: Element, arg1: String, arg2: String)` | `Element` | Retrieves `SubchildElement` property from `XMLUtil` |
| `static` | `getBooleanFromElText` | `(arg0: Element, arg1: boolean)` | `boolean` | Retrieves `BooleanFromElText` property from `XMLUtil` |
| `static` | `attributeValid` | `(arg0: Element, arg1: String)` | `boolean` | Performs attribute valid operation |

---

## Subsystem: `memory`

### `CpuInfo`
- **Full Qualified Name:** `com.strategyquant.lib.memory.CpuInfo`
- **Primary Job / Responsibility:** JVM and off-heap memory monitoring, allocation guards, and protection (`CpuInfo`).

#### Methods & Functions
| Modifiers | Method Name | Parameter Signatures | Return Type | Functional Description / Job |
| :--- | :--- | :--- | :--- | :--- |
| `instance` | `equals` | `(arg0: Object)` | `boolean` | Performs equals operation |
| `instance` | `toString` | `()` | `String` | Converts/serializes representation via `toString` |
| `instance` | `hashCode` | `()` | `int` | Evaluates boolean predicate `hashCode` on `CpuInfo` |
| `instance` | `getClass` | `()` | `Class` | Retrieves `Class` property from `CpuInfo` |
| `instance` | `notify` | `()` | `void` | Performs notify operation |
| `instance` | `notifyAll` | `()` | `void` | Performs notify all operation |
| `instance` | `wait` | `(arg0: long)` | `void` | Performs wait operation |
| `instance` | `wait` | `(arg0: long, arg1: int)` | `void` | Performs wait operation |
| `instance` | `wait` | `()` | `void` | Performs wait operation |
| `static` | `getAvailableProcessors` | `()` | `int` | Retrieves `AvailableProcessors` property from `CpuInfo` |

---

### `MemoryUsageChecker`
- **Full Qualified Name:** `com.strategyquant.lib.memory.MemoryUsageChecker`
- **Primary Job / Responsibility:** JVM and off-heap memory monitoring, allocation guards, and protection (`MemoryUsageChecker`).

#### Fields
| Scope | Field Name | Type |
| :--- | :--- | :--- |
| `static` | `Log` | `Logger` |

#### Methods & Functions
| Modifiers | Method Name | Parameter Signatures | Return Type | Functional Description / Job |
| :--- | :--- | :--- | :--- | :--- |
| `instance` | `equals` | `(arg0: Object)` | `boolean` | Performs equals operation |
| `instance` | `toString` | `()` | `String` | Converts/serializes representation via `toString` |
| `instance` | `hashCode` | `()` | `int` | Evaluates boolean predicate `hashCode` on `MemoryUsageChecker` |
| `instance` | `getClass` | `()` | `Class` | Retrieves `Class` property from `MemoryUsageChecker` |
| `instance` | `notify` | `()` | `void` | Performs notify operation |
| `instance` | `notifyAll` | `()` | `void` | Performs notify all operation |
| `instance` | `wait` | `(arg0: long)` | `void` | Performs wait operation |
| `instance` | `wait` | `(arg0: long, arg1: int)` | `void` | Performs wait operation |
| `instance` | `wait` | `()` | `void` | Performs wait operation |
| `static` | `init` | `()` | `void` | Instantiates/initializes `init` resource |
| `static` | `getCurrentUsage` | `()` | `double` | Retrieves `CurrentUsage` property from `MemoryUsageChecker` |
| `static` | `checkAvailableMemory` | `()` | `void` | Performs check available memory operation |

---

### `OffHeapMemory`
- **Full Qualified Name:** `com.strategyquant.lib.memory.OffHeapMemory`
- **Primary Job / Responsibility:** JVM and off-heap memory monitoring, allocation guards, and protection (`OffHeapMemory`).

#### Fields
| Scope | Field Name | Type |
| :--- | :--- | :--- |
| `static` | `AddressDeallocated` | `long` |
| `static` | `AddressUnset` | `long` |
| `static` | `Log` | `Logger` |

#### Methods & Functions
| Modifiers | Method Name | Parameter Signatures | Return Type | Functional Description / Job |
| :--- | :--- | :--- | :--- | :--- |
| `instance` | `equals` | `(arg0: Object)` | `boolean` | Performs equals operation |
| `instance` | `toString` | `()` | `String` | Converts/serializes representation via `toString` |
| `instance` | `hashCode` | `()` | `int` | Evaluates boolean predicate `hashCode` on `OffHeapMemory` |
| `instance` | `getClass` | `()` | `Class` | Retrieves `Class` property from `OffHeapMemory` |
| `instance` | `notify` | `()` | `void` | Performs notify operation |
| `instance` | `notifyAll` | `()` | `void` | Performs notify all operation |
| `instance` | `wait` | `(arg0: long)` | `void` | Performs wait operation |
| `instance` | `wait` | `(arg0: long, arg1: int)` | `void` | Performs wait operation |
| `instance` | `wait` | `()` | `void` | Performs wait operation |
| `static` | `getByte` | `(arg0: long)` | `byte` | Retrieves `Byte` property from `OffHeapMemory` |
| `static` | `putByte` | `(arg0: long, arg1: byte)` | `void` | Performs put byte operation |
| `static` | `getShort` | `(arg0: long)` | `short` | Retrieves `Short` property from `OffHeapMemory` |
| `static` | `putShort` | `(arg0: long, arg1: short)` | `void` | Performs put short operation |
| `static` | `getInt` | `(arg0: long)` | `int` | Retrieves `Int` property from `OffHeapMemory` |
| `static` | `putInt` | `(arg0: long, arg1: int)` | `void` | Performs put int operation |
| `static` | `getLong` | `(arg0: long)` | `long` | Retrieves `Long` property from `OffHeapMemory` |
| `static` | `putLong` | `(arg0: long, arg1: long)` | `void` | Performs put long operation |
| `static` | `getFloat` | `(arg0: long)` | `float` | Retrieves `Float` property from `OffHeapMemory` |
| `static` | `getDouble` | `(arg0: long)` | `double` | Retrieves `Double` property from `OffHeapMemory` |
| `static` | `putDouble` | `(arg0: long, arg1: double)` | `void` | Performs put double operation |
| `static` | `copyMemory` | `(arg0: Object, arg1: long, arg2: Object, arg3: long, arg4: long)` | `void` | Performs copy memory operation |
| `static` | `copyMemory` | `(arg0: long, arg1: long, arg2: long)` | `void` | Performs copy memory operation |
| `static` | `allocate` | `(arg0: IOffHeapCallback, arg1: long)` | `long` | Performs allocate operation |
| `static` | `getInfo` | `(arg0: MemoryInfo)` | `void` | Retrieves `Info` property from `OffHeapMemory` |
| `static` | `deallocate` | `(arg0: IOffHeapCallback, arg1: long)` | `void` | Performs deallocate operation |
| `static` | `reallocate` | `(arg0: IOffHeapCallback, arg1: long, arg2: long)` | `long` | Performs reallocate operation |
| `static` | `throwMemoryException` | `(arg0: long, arg1: String)` | `void` | Performs throw memory exception operation |
| `static` | `throwMemoryException` | `(arg0: long)` | `void` | Performs throw memory exception operation |
| `static` | `getByteArrayOffset` | `()` | `long` | Retrieves `ByteArrayOffset` property from `OffHeapMemory` |
| `static` | `getOffHeapObjects` | `()` | `String` | Retrieves `OffHeapObjects` property from `OffHeapMemory` |

---

### `OffHeapObject`
- **Full Qualified Name:** `com.strategyquant.lib.memory.OffHeapMemory.OffHeapObject`
- **Primary Job / Responsibility:** JVM and off-heap memory monitoring, allocation guards, and protection (`OffHeapObject`).

#### Fields
| Scope | Field Name | Type |
| :--- | :--- | :--- |
| `instance` | `object` | `IOffHeapCallback` |
| `instance` | `size` | `long` |

#### Methods & Functions
| Modifiers | Method Name | Parameter Signatures | Return Type | Functional Description / Job |
| :--- | :--- | :--- | :--- | :--- |
| `instance` | `equals` | `(arg0: Object)` | `boolean` | Performs equals operation |
| `instance` | `toString` | `()` | `String` | Converts/serializes representation via `toString` |
| `instance` | `hashCode` | `()` | `int` | Evaluates boolean predicate `hashCode` on `OffHeapObject` |
| `instance` | `getClass` | `()` | `Class` | Retrieves `Class` property from `OffHeapObject` |
| `instance` | `notify` | `()` | `void` | Performs notify operation |
| `instance` | `notifyAll` | `()` | `void` | Performs notify all operation |
| `instance` | `wait` | `(arg0: long)` | `void` | Performs wait operation |
| `instance` | `wait` | `(arg0: long, arg1: int)` | `void` | Performs wait operation |
| `instance` | `wait` | `()` | `void` | Performs wait operation |

---

### `SQMemoryProtectionError`
- **Full Qualified Name:** `com.strategyquant.lib.memory.SQMemoryProtectionError`
- **Primary Job / Responsibility:** JVM and off-heap memory monitoring, allocation guards, and protection (`SQMemoryProtectionError`).

#### Methods & Functions
| Modifiers | Method Name | Parameter Signatures | Return Type | Functional Description / Job |
| :--- | :--- | :--- | :--- | :--- |
| `instance` | `printStackTrace` | `()` | `void` | Performs print stack trace operation |
| `instance` | `printStackTrace` | `(arg0: PrintWriter)` | `void` | Performs print stack trace operation |
| `instance` | `printStackTrace` | `(arg0: PrintStream)` | `void` | Performs print stack trace operation |
| `instance` | `getStackTrace` | `()` | `StackTraceElement[]` | Retrieves `StackTrace` property from `SQMemoryProtectionError` |
| `instance` | `fillInStackTrace` | `()` | `Throwable` | Performs fill in stack trace operation |
| `instance` | `getCause` | `()` | `Throwable` | Retrieves `Cause` property from `SQMemoryProtectionError` |
| `instance` | `initCause` | `(arg0: Throwable)` | `Throwable` | Instantiates/initializes `initCause` resource |
| `instance` | `toString` | `()` | `String` | Converts/serializes representation via `toString` |
| `instance` | `getMessage` | `()` | `String` | Retrieves `Message` property from `SQMemoryProtectionError` |
| `instance` | `getSuppressed` | `()` | `Throwable[]` | Retrieves `Suppressed` property from `SQMemoryProtectionError` |
| `instance` | `getLocalizedMessage` | `()` | `String` | Retrieves `LocalizedMessage` property from `SQMemoryProtectionError` |
| `instance` | `setStackTrace` | `(arg0: StackTraceElement[])` | `void` | Sets `StackTrace` configuration/state on `SQMemoryProtectionError` |
| `instance` | `addSuppressed` | `(arg0: Throwable)` | `void` | Appends/registers element via `addSuppressed` |
| `instance` | `equals` | `(arg0: Object)` | `boolean` | Performs equals operation |
| `instance` | `hashCode` | `()` | `int` | Evaluates boolean predicate `hashCode` on `SQMemoryProtectionError` |
| `instance` | `getClass` | `()` | `Class` | Retrieves `Class` property from `SQMemoryProtectionError` |
| `instance` | `notify` | `()` | `void` | Performs notify operation |
| `instance` | `notifyAll` | `()` | `void` | Performs notify all operation |
| `instance` | `wait` | `(arg0: long)` | `void` | Performs wait operation |
| `instance` | `wait` | `(arg0: long, arg1: int)` | `void` | Performs wait operation |
| `instance` | `wait` | `()` | `void` | Performs wait operation |

---

## Subsystem: `utils`

### `ComponentResizer`
- **Full Qualified Name:** `com.strategyquant.lib.utils.ComponentResizer`
- **Primary Job / Responsibility:** General utility subsystem (compression, file I/O, networking, OS inspection) (`ComponentResizer`).

#### Methods & Functions
| Modifiers | Method Name | Parameter Signatures | Return Type | Functional Description / Job |
| :--- | :--- | :--- | :--- | :--- |
| `instance` | `setDragInsets` | `(arg0: Insets)` | `void` | Sets `DragInsets` configuration/state on `ComponentResizer` |
| `instance` | `setSnapSize` | `(arg0: Dimension)` | `void` | Sets `SnapSize` configuration/state on `ComponentResizer` |
| `instance` | `registerComponent` | `(arg0: Component[])` | `void` | Performs register component operation |
| `instance` | `getDragInsets` | `()` | `Insets` | Retrieves `DragInsets` property from `ComponentResizer` |
| `instance` | `getMaximumSize` | `()` | `Dimension` | Retrieves `MaximumSize` property from `ComponentResizer` |
| `instance` | `setMaximumSize` | `(arg0: Dimension)` | `void` | Sets `MaximumSize` configuration/state on `ComponentResizer` |
| `instance` | `getMinimumSize` | `()` | `Dimension` | Retrieves `MinimumSize` property from `ComponentResizer` |
| `instance` | `setMinimumSize` | `(arg0: Dimension)` | `void` | Sets `MinimumSize` configuration/state on `ComponentResizer` |
| `instance` | `deregisterComponent` | `(arg0: Component[])` | `void` | Performs deregister component operation |
| `instance` | `getSnapSize` | `()` | `Dimension` | Retrieves `SnapSize` property from `ComponentResizer` |
| `instance` | `mouseMoved` | `(arg0: MouseEvent)` | `void` | Performs mouse moved operation |
| `instance` | `mouseEntered` | `(arg0: MouseEvent)` | `void` | Performs mouse entered operation |
| `instance` | `mouseExited` | `(arg0: MouseEvent)` | `void` | Performs mouse exited operation |
| `instance` | `mousePressed` | `(arg0: MouseEvent)` | `void` | Performs mouse pressed operation |
| `instance` | `mouseReleased` | `(arg0: MouseEvent)` | `void` | Performs mouse released operation |
| `instance` | `mouseDragged` | `(arg0: MouseEvent)` | `void` | Performs mouse dragged operation |
| `instance` | `mouseClicked` | `(arg0: MouseEvent)` | `void` | Performs mouse clicked operation |
| `instance` | `mouseWheelMoved` | `(arg0: MouseWheelEvent)` | `void` | Performs mouse wheel moved operation |
| `instance` | `equals` | `(arg0: Object)` | `boolean` | Performs equals operation |
| `instance` | `toString` | `()` | `String` | Converts/serializes representation via `toString` |
| `instance` | `hashCode` | `()` | `int` | Evaluates boolean predicate `hashCode` on `ComponentResizer` |
| `instance` | `getClass` | `()` | `Class` | Retrieves `Class` property from `ComponentResizer` |
| `instance` | `notify` | `()` | `void` | Performs notify operation |
| `instance` | `notifyAll` | `()` | `void` | Performs notify all operation |
| `instance` | `wait` | `(arg0: long)` | `void` | Performs wait operation |
| `instance` | `wait` | `(arg0: long, arg1: int)` | `void` | Performs wait operation |
| `instance` | `wait` | `()` | `void` | Performs wait operation |

---

### `DirectoryHash`
- **Full Qualified Name:** `com.strategyquant.lib.utils.DirectoryHash`
- **Primary Job / Responsibility:** General utility subsystem (compression, file I/O, networking, OS inspection) (`DirectoryHash`).

#### Methods & Functions
| Modifiers | Method Name | Parameter Signatures | Return Type | Functional Description / Job |
| :--- | :--- | :--- | :--- | :--- |
| `instance` | `equals` | `(arg0: Object)` | `boolean` | Performs equals operation |
| `instance` | `toString` | `()` | `String` | Converts/serializes representation via `toString` |
| `instance` | `hashCode` | `()` | `int` | Evaluates boolean predicate `hashCode` on `DirectoryHash` |
| `instance` | `getClass` | `()` | `Class` | Retrieves `Class` property from `DirectoryHash` |
| `instance` | `notify` | `()` | `void` | Performs notify operation |
| `instance` | `notifyAll` | `()` | `void` | Performs notify all operation |
| `instance` | `wait` | `(arg0: long)` | `void` | Performs wait operation |
| `instance` | `wait` | `(arg0: long, arg1: int)` | `void` | Performs wait operation |
| `instance` | `wait` | `()` | `void` | Performs wait operation |
| `static` | `calculate` | `(arg0: File)` | `int` | Executes calculation for `calculate` |

---

### `EmailSender`
- **Full Qualified Name:** `com.strategyquant.lib.utils.EmailSender`
- **Primary Job / Responsibility:** General utility subsystem (compression, file I/O, networking, OS inspection) (`EmailSender`).

#### Methods & Functions
| Modifiers | Method Name | Parameter Signatures | Return Type | Functional Description / Job |
| :--- | :--- | :--- | :--- | :--- |
| `instance` | `equals` | `(arg0: Object)` | `boolean` | Performs equals operation |
| `instance` | `toString` | `()` | `String` | Converts/serializes representation via `toString` |
| `instance` | `hashCode` | `()` | `int` | Evaluates boolean predicate `hashCode` on `EmailSender` |
| `instance` | `getClass` | `()` | `Class` | Retrieves `Class` property from `EmailSender` |
| `instance` | `notify` | `()` | `void` | Performs notify operation |
| `instance` | `notifyAll` | `()` | `void` | Performs notify all operation |
| `instance` | `wait` | `(arg0: long)` | `void` | Performs wait operation |
| `instance` | `wait` | `(arg0: long, arg1: int)` | `void` | Performs wait operation |
| `instance` | `wait` | `()` | `void` | Performs wait operation |
| `static` | `sendTo` | `(arg0: String, arg1: int, arg2: String, arg3: String, arg4: String, arg5: String, arg6: String, arg7: String, arg8: boolean)` | `void` | Performs send to operation |
| `static` | `isValidEmailAddress` | `(arg0: String)` | `boolean` | Evaluates boolean predicate `isValidEmailAddress` on `EmailSender` |

---

### `FileLoader`
- **Full Qualified Name:** `com.strategyquant.lib.utils.FileLoader`
- **Primary Job / Responsibility:** General utility subsystem (compression, file I/O, networking, OS inspection) (`FileLoader`).

#### Methods & Functions
| Modifiers | Method Name | Parameter Signatures | Return Type | Functional Description / Job |
| :--- | :--- | :--- | :--- | :--- |
| `instance` | `hasNext` | `()` | `boolean` | Evaluates boolean predicate `hasNext` on `FileLoader` |
| `instance` | `getNext` | `()` | `File` | Retrieves `Next` property from `FileLoader` |
| `instance` | `equals` | `(arg0: Object)` | `boolean` | Performs equals operation |
| `instance` | `toString` | `()` | `String` | Converts/serializes representation via `toString` |
| `instance` | `hashCode` | `()` | `int` | Evaluates boolean predicate `hashCode` on `FileLoader` |
| `instance` | `getClass` | `()` | `Class` | Retrieves `Class` property from `FileLoader` |
| `instance` | `notify` | `()` | `void` | Performs notify operation |
| `instance` | `notifyAll` | `()` | `void` | Performs notify all operation |
| `instance` | `wait` | `(arg0: long)` | `void` | Performs wait operation |
| `instance` | `wait` | `(arg0: long, arg1: int)` | `void` | Performs wait operation |
| `instance` | `wait` | `()` | `void` | Performs wait operation |

---

### `FullData`
- **Full Qualified Name:** `com.strategyquant.lib.utils.FullData`
- **Primary Job / Responsibility:** General utility subsystem (compression, file I/O, networking, OS inspection) (`FullData`).

#### Fields
| Scope | Field Name | Type |
| :--- | :--- | :--- |
| `instance` | `close` | `double` |
| `instance` | `connection` | `String` |
| `instance` | `connectionHash` | `int` |
| `instance` | `high` | `double` |
| `instance` | `low` | `double` |
| `instance` | `open` | `double` |
| `instance` | `symbol` | `String` |
| `instance` | `symbolHash` | `int` |
| `instance` | `time` | `long` |
| `instance` | `timeframe` | `String` |

#### Methods & Functions
| Modifiers | Method Name | Parameter Signatures | Return Type | Functional Description / Job |
| :--- | :--- | :--- | :--- | :--- |
| `instance` | `equals` | `(arg0: Object)` | `boolean` | Performs equals operation |
| `instance` | `toString` | `()` | `String` | Converts/serializes representation via `toString` |
| `instance` | `hashCode` | `()` | `int` | Evaluates boolean predicate `hashCode` on `FullData` |
| `instance` | `getClass` | `()` | `Class` | Retrieves `Class` property from `FullData` |
| `instance` | `notify` | `()` | `void` | Performs notify operation |
| `instance` | `notifyAll` | `()` | `void` | Performs notify all operation |
| `instance` | `wait` | `(arg0: long)` | `void` | Performs wait operation |
| `instance` | `wait` | `(arg0: long, arg1: int)` | `void` | Performs wait operation |
| `instance` | `wait` | `()` | `void` | Performs wait operation |

---

### `GCChecker`
- **Full Qualified Name:** `com.strategyquant.lib.utils.GCChecker`
- **Primary Job / Responsibility:** General utility subsystem (compression, file I/O, networking, OS inspection) (`GCChecker`).

#### Methods & Functions
| Modifiers | Method Name | Parameter Signatures | Return Type | Functional Description / Job |
| :--- | :--- | :--- | :--- | :--- |
| `instance` | `equals` | `(arg0: Object)` | `boolean` | Performs equals operation |
| `instance` | `toString` | `()` | `String` | Converts/serializes representation via `toString` |
| `instance` | `hashCode` | `()` | `int` | Evaluates boolean predicate `hashCode` on `GCChecker` |
| `instance` | `getClass` | `()` | `Class` | Retrieves `Class` property from `GCChecker` |
| `instance` | `notify` | `()` | `void` | Performs notify operation |
| `instance` | `notifyAll` | `()` | `void` | Performs notify all operation |
| `instance` | `wait` | `(arg0: long)` | `void` | Performs wait operation |
| `instance` | `wait` | `(arg0: long, arg1: int)` | `void` | Performs wait operation |
| `instance` | `wait` | `()` | `void` | Performs wait operation |
| `static` | `checkG1GCUsed` | `()` | `boolean` | Performs check g 1 gc used operation |

---

### `IProgressListener`
- **Full Qualified Name:** `com.strategyquant.lib.utils.IProgressListener`
- **Primary Job / Responsibility:** General utility subsystem (compression, file I/O, networking, OS inspection) (`IProgressListener`).

#### Methods & Functions
| Modifiers | Method Name | Parameter Signatures | Return Type | Functional Description / Job |
| :--- | :--- | :--- | :--- | :--- |
| `instance` | `onContinue` | `()` | `void` | Performs on continue operation |
| `instance` | `onStart` | `()` | `void` | Performs on start operation |
| `instance` | `setStep` | `(arg0: int)` | `void` | Sets `Step` configuration/state on `IProgressListener` |
| `instance` | `onError` | `(arg0: String)` | `void` | Performs on error operation |
| `instance` | `onProgress` | `(arg0: double)` | `void` | Performs on progress operation |
| `instance` | `setMessage` | `(arg0: String)` | `void` | Sets `Message` configuration/state on `IProgressListener` |
| `instance` | `onPause` | `()` | `void` | Performs on pause operation |
| `instance` | `onFinish` | `()` | `void` | Performs on finish operation |
| `instance` | `onConfirm` | `(arg0: String)` | `void` | Performs on confirm operation |

---

### `ISQCloneable`
- **Full Qualified Name:** `com.strategyquant.lib.utils.ISQCloneable`
- **Primary Job / Responsibility:** General utility subsystem (compression, file I/O, networking, OS inspection) (`ISQCloneable`).

#### Methods & Functions
| Modifiers | Method Name | Parameter Signatures | Return Type | Functional Description / Job |
| :--- | :--- | :--- | :--- | :--- |
| `instance` | `getClone` | `()` | `Object` | Retrieves `Clone` property from `ISQCloneable` |

---

### `IUniqueNameChecker`
- **Full Qualified Name:** `com.strategyquant.lib.utils.IUniqueNameChecker`
- **Primary Job / Responsibility:** General utility subsystem (compression, file I/O, networking, OS inspection) (`IUniqueNameChecker`).

#### Methods & Functions
| Modifiers | Method Name | Parameter Signatures | Return Type | Functional Description / Job |
| :--- | :--- | :--- | :--- | :--- |
| `instance` | `checkNameExist` | `(arg0: String)` | `boolean` | Performs check name exist operation |

---

### `JsonCreator`
- **Full Qualified Name:** `com.strategyquant.lib.utils.JsonCreator`
- **Primary Job / Responsibility:** General utility subsystem (compression, file I/O, networking, OS inspection) (`JsonCreator`).

#### Methods & Functions
| Modifiers | Method Name | Parameter Signatures | Return Type | Functional Description / Job |
| :--- | :--- | :--- | :--- | :--- |
| `instance` | `put` | `(arg0: String)` | `void` | Performs put operation |
| `instance` | `put` | `(arg0: String, arg1: Object, arg2: boolean)` | `void` | Performs put operation |
| `instance` | `toString` | `()` | `String` | Converts/serializes representation via `toString` |
| `instance` | `add` | `(arg0: Collection, arg1: boolean)` | `void` | Appends/registers element via `add` |
| `instance` | `setValue` | `(arg0: Object, arg1: boolean)` | `void` | Sets `Value` configuration/state on `JsonCreator` |
| `instance` | `separator` | `()` | `void` | Performs separator operation |
| `instance` | `beginArray` | `()` | `void` | Performs begin array operation |
| `instance` | `beginObject` | `()` | `void` | Performs begin object operation |
| `instance` | `endArray` | `(arg0: boolean)` | `void` | Performs end array operation |
| `instance` | `endObject` | `(arg0: boolean)` | `void` | Performs end object operation |
| `instance` | `toJson` | `()` | `String` | Converts/serializes representation via `toJson` |
| `instance` | `putRaw` | `(arg0: String, arg1: Object, arg2: boolean)` | `void` | Performs put raw operation |
| `instance` | `putBeginObject` | `(arg0: String)` | `void` | Performs put begin object operation |
| `instance` | `putBeginArray` | `(arg0: String)` | `void` | Performs put begin array operation |
| `instance` | `addArray` | `(arg0: Object, arg1: boolean)` | `void` | Appends/registers element via `addArray` |
| `instance` | `equals` | `(arg0: Object)` | `boolean` | Performs equals operation |
| `instance` | `hashCode` | `()` | `int` | Evaluates boolean predicate `hashCode` on `JsonCreator` |
| `instance` | `getClass` | `()` | `Class` | Retrieves `Class` property from `JsonCreator` |
| `instance` | `notify` | `()` | `void` | Performs notify operation |
| `instance` | `notifyAll` | `()` | `void` | Performs notify all operation |
| `instance` | `wait` | `(arg0: long)` | `void` | Performs wait operation |
| `instance` | `wait` | `(arg0: long, arg1: int)` | `void` | Performs wait operation |
| `instance` | `wait` | `()` | `void` | Performs wait operation |

---

### `LimitedList`
- **Full Qualified Name:** `com.strategyquant.lib.utils.LimitedList`
- **Primary Job / Responsibility:** General utility subsystem (compression, file I/O, networking, OS inspection) (`LimitedList`).

#### Methods & Functions
| Modifiers | Method Name | Parameter Signatures | Return Type | Functional Description / Job |
| :--- | :--- | :--- | :--- | :--- |
| `instance` | `add` | `(arg0: Object)` | `void` | Appends/registers element via `add` |
| `instance` | `add` | `(arg0: int, arg1: Object)` | `void` | Appends/registers element via `add` |
| `instance` | `remove` | `(arg0: Object)` | `Object` | Removes/resets elements via `remove` |
| `instance` | `remove` | `(arg0: int)` | `Object` | Removes/resets elements via `remove` |
| `instance` | `size` | `()` | `int` | Performs size operation |
| `instance` | `get` | `(arg0: int)` | `Object` | Retrieves `` property from `LimitedList` |
| `instance` | `equals` | `(arg0: Object)` | `boolean` | Performs equals operation |
| `instance` | `hashCode` | `()` | `int` | Evaluates boolean predicate `hashCode` on `LimitedList` |
| `instance` | `clone` | `()` | `Object` | Performs clone operation |
| `instance` | `sort` | `(arg0: Comparator)` | `void` | Performs sort operation |
| `instance` | `indexOf` | `(arg0: Object)` | `int` | Performs index of operation |
| `instance` | `clear` | `()` | `void` | Removes/resets elements via `clear` |
| `instance` | `lastIndexOf` | `(arg0: Object)` | `int` | Performs last index of operation |
| `instance` | `isEmpty` | `()` | `boolean` | Evaluates boolean predicate `isEmpty` on `LimitedList` |
| `instance` | `replaceAll` | `(arg0: UnaryOperator)` | `void` | Performs replace all operation |
| `instance` | `subList` | `(arg0: int, arg1: int)` | `List` | Performs sub list operation |
| `instance` | `toArray` | `(arg0: Object[])` | `Object[]` | Converts/serializes representation via `toArray` |
| `instance` | `toArray` | `()` | `Object[]` | Converts/serializes representation via `toArray` |
| `instance` | `toArray` | `(arg0: IntFunction)` | `Object[]` | Converts/serializes representation via `toArray` |
| `instance` | `iterator` | `()` | `Iterator` | Performs iterator operation |
| `instance` | `contains` | `(arg0: Object)` | `boolean` | Performs contains operation |
| `instance` | `spliterator` | `()` | `Spliterator` | Performs spliterator operation |
| `instance` | `addAll` | `(arg0: Collection)` | `boolean` | Appends/registers element via `addAll` |
| `instance` | `addAll` | `(arg0: int, arg1: Collection)` | `boolean` | Appends/registers element via `addAll` |
| `instance` | `trimToSize` | `()` | `void` | Performs trim to size operation |
| `instance` | `set` | `(arg0: int, arg1: Object)` | `Object` | Sets `` configuration/state on `LimitedList` |
| `instance` | `forEach` | `(arg0: Consumer)` | `void` | Performs for each operation |
| `instance` | `ensureCapacity` | `(arg0: int)` | `void` | Performs ensure capacity operation |
| `instance` | `removeIf` | `(arg0: Predicate)` | `boolean` | Removes/resets elements via `removeIf` |
| `instance` | `getFirst` | `()` | `Object` | Retrieves `First` property from `LimitedList` |
| `instance` | `getLast` | `()` | `Object` | Retrieves `Last` property from `LimitedList` |
| `instance` | `addFirst` | `(arg0: Object)` | `void` | Appends/registers element via `addFirst` |
| `instance` | `addLast` | `(arg0: Object)` | `void` | Appends/registers element via `addLast` |
| `instance` | `removeFirst` | `()` | `Object` | Removes/resets elements via `removeFirst` |
| `instance` | `removeLast` | `()` | `Object` | Removes/resets elements via `removeLast` |
| `instance` | `removeAll` | `(arg0: Collection)` | `boolean` | Removes/resets elements via `removeAll` |
| `instance` | `retainAll` | `(arg0: Collection)` | `boolean` | Performs retain all operation |
| `instance` | `listIterator` | `(arg0: int)` | `ListIterator` | Performs list iterator operation |
| `instance` | `listIterator` | `()` | `ListIterator` | Performs list iterator operation |
| `instance` | `toString` | `()` | `String` | Converts/serializes representation via `toString` |
| `instance` | `containsAll` | `(arg0: Collection)` | `boolean` | Performs contains all operation |
| `instance` | `getClass` | `()` | `Class` | Retrieves `Class` property from `LimitedList` |
| `instance` | `notify` | `()` | `void` | Performs notify operation |
| `instance` | `notifyAll` | `()` | `void` | Performs notify all operation |
| `instance` | `wait` | `(arg0: long)` | `void` | Performs wait operation |
| `instance` | `wait` | `(arg0: long, arg1: int)` | `void` | Performs wait operation |
| `instance` | `wait` | `()` | `void` | Performs wait operation |
| `instance` | `stream` | `()` | `Stream` | Performs stream operation |
| `instance` | `parallelStream` | `()` | `Stream` | Performs parallel stream operation |
| `instance` | `reversed` | `()` | `List` | Performs reversed operation |
| `instance` | `reversed` | `()` | `List` | Performs reversed operation |

---

### `OSUtils`
- **Full Qualified Name:** `com.strategyquant.lib.utils.OSUtils`
- **Primary Job / Responsibility:** General utility subsystem (compression, file I/O, networking, OS inspection) (`OSUtils`).

#### Fields
| Scope | Field Name | Type |
| :--- | :--- | :--- |
| `static` | `isWindows` | `boolean` |
| `static` | `isX64` | `boolean` |

#### Methods & Functions
| Modifiers | Method Name | Parameter Signatures | Return Type | Functional Description / Job |
| :--- | :--- | :--- | :--- | :--- |
| `instance` | `equals` | `(arg0: Object)` | `boolean` | Performs equals operation |
| `instance` | `toString` | `()` | `String` | Converts/serializes representation via `toString` |
| `instance` | `hashCode` | `()` | `int` | Evaluates boolean predicate `hashCode` on `OSUtils` |
| `instance` | `getClass` | `()` | `Class` | Retrieves `Class` property from `OSUtils` |
| `instance` | `notify` | `()` | `void` | Performs notify operation |
| `instance` | `notifyAll` | `()` | `void` | Performs notify all operation |
| `instance` | `wait` | `(arg0: long)` | `void` | Performs wait operation |
| `instance` | `wait` | `(arg0: long, arg1: int)` | `void` | Performs wait operation |
| `instance` | `wait` | `()` | `void` | Performs wait operation |
| `static` | `executeCommand` | `(arg0: String[])` | `InputStream` | Performs execute command operation |
| `static` | `executeAndRead` | `(arg0: String[])` | `String` | Performs execute and read operation |
| `static` | `addLibraryPath` | `(arg0: String)` | `void` | Appends/registers element via `addLibraryPath` |
| `static` | `getProcess` | `()` | `Process` | Retrieves `Process` property from `OSUtils` |

---

### `Pair`
- **Full Qualified Name:** `com.strategyquant.lib.utils.Pair`
- **Primary Job / Responsibility:** General utility subsystem (compression, file I/O, networking, OS inspection) (`Pair`).

#### Methods & Functions
| Modifiers | Method Name | Parameter Signatures | Return Type | Functional Description / Job |
| :--- | :--- | :--- | :--- | :--- |
| `instance` | `getA` | `()` | `Object` | Retrieves `A` property from `Pair` |
| `instance` | `getB` | `()` | `Object` | Retrieves `B` property from `Pair` |
| `instance` | `setA` | `(arg0: Object)` | `void` | Sets `A` configuration/state on `Pair` |
| `instance` | `setB` | `(arg0: Object)` | `void` | Sets `B` configuration/state on `Pair` |
| `instance` | `equals` | `(arg0: Object)` | `boolean` | Performs equals operation |
| `instance` | `toString` | `()` | `String` | Converts/serializes representation via `toString` |
| `instance` | `hashCode` | `()` | `int` | Evaluates boolean predicate `hashCode` on `Pair` |
| `instance` | `getClass` | `()` | `Class` | Retrieves `Class` property from `Pair` |
| `instance` | `notify` | `()` | `void` | Performs notify operation |
| `instance` | `notifyAll` | `()` | `void` | Performs notify all operation |
| `instance` | `wait` | `(arg0: long)` | `void` | Performs wait operation |
| `instance` | `wait` | `(arg0: long, arg1: int)` | `void` | Performs wait operation |
| `instance` | `wait` | `()` | `void` | Performs wait operation |

---

### `SQFileChooserFactory`
- **Full Qualified Name:** `com.strategyquant.lib.utils.SQFileChooserFactory`
- **Primary Job / Responsibility:** General utility subsystem (compression, file I/O, networking, OS inspection) (`SQFileChooserFactory`).

#### Methods & Functions
| Modifiers | Method Name | Parameter Signatures | Return Type | Functional Description / Job |
| :--- | :--- | :--- | :--- | :--- |
| `instance` | `equals` | `(arg0: Object)` | `boolean` | Performs equals operation |
| `instance` | `toString` | `()` | `String` | Converts/serializes representation via `toString` |
| `instance` | `hashCode` | `()` | `int` | Evaluates boolean predicate `hashCode` on `SQFileChooserFactory` |
| `instance` | `getClass` | `()` | `Class` | Retrieves `Class` property from `SQFileChooserFactory` |
| `instance` | `notify` | `()` | `void` | Performs notify operation |
| `instance` | `notifyAll` | `()` | `void` | Performs notify all operation |
| `instance` | `wait` | `(arg0: long)` | `void` | Performs wait operation |
| `instance` | `wait` | `(arg0: long, arg1: int)` | `void` | Performs wait operation |
| `instance` | `wait` | `()` | `void` | Performs wait operation |
| `static` | `createPersistingJFileChooser` | `(arg0: String)` | `ISQFileChooser` | Instantiates/initializes `createPersistingJFileChooser` resource |

---

### `ISQFileChooser`
- **Full Qualified Name:** `com.strategyquant.lib.utils.SQFileChooserFactory.ISQFileChooser`
- **Primary Job / Responsibility:** General utility subsystem (compression, file I/O, networking, OS inspection) (`ISQFileChooser`).

#### Methods & Functions
| Modifiers | Method Name | Parameter Signatures | Return Type | Functional Description / Job |
| :--- | :--- | :--- | :--- | :--- |
| `instance` | `close` | `()` | `void` | Performs close operation |
| `instance` | `getJFileChooser` | `()` | `JFileChooser` | Retrieves `JFileChooser` property from `ISQFileChooser` |

---

### `JFileChooserPersisterImpl`
- **Full Qualified Name:** `com.strategyquant.lib.utils.SQFileChooserFactory.JFileChooserPersisterImpl`
- **Primary Job / Responsibility:** General utility subsystem (compression, file I/O, networking, OS inspection) (`JFileChooserPersisterImpl`).

#### Methods & Functions
| Modifiers | Method Name | Parameter Signatures | Return Type | Functional Description / Job |
| :--- | :--- | :--- | :--- | :--- |
| `instance` | `init` | `()` | `void` | Instantiates/initializes `init` resource |
| `instance` | `close` | `()` | `void` | Performs close operation |
| `instance` | `getJFileChooser` | `()` | `JFileChooser` | Retrieves `JFileChooser` property from `JFileChooserPersisterImpl` |
| `instance` | `equals` | `(arg0: Object)` | `boolean` | Performs equals operation |
| `instance` | `toString` | `()` | `String` | Converts/serializes representation via `toString` |
| `instance` | `hashCode` | `()` | `int` | Evaluates boolean predicate `hashCode` on `JFileChooserPersisterImpl` |
| `instance` | `getClass` | `()` | `Class` | Retrieves `Class` property from `JFileChooserPersisterImpl` |
| `instance` | `notify` | `()` | `void` | Performs notify operation |
| `instance` | `notifyAll` | `()` | `void` | Performs notify all operation |
| `instance` | `wait` | `(arg0: long)` | `void` | Performs wait operation |
| `instance` | `wait` | `(arg0: long, arg1: int)` | `void` | Performs wait operation |
| `instance` | `wait` | `()` | `void` | Performs wait operation |

---

### `OnChooserClosing`
- **Full Qualified Name:** `com.strategyquant.lib.utils.SQFileChooserFactory.JFileChooserPersisterImpl.OnChooserClosing`
- **Primary Job / Responsibility:** General utility subsystem (compression, file I/O, networking, OS inspection) (`OnChooserClosing`).

#### Methods & Functions
| Modifiers | Method Name | Parameter Signatures | Return Type | Functional Description / Job |
| :--- | :--- | :--- | :--- | :--- |
| `instance` | `propertyChange` | `(arg0: PropertyChangeEvent)` | `void` | Performs property change operation |
| `instance` | `equals` | `(arg0: Object)` | `boolean` | Performs equals operation |
| `instance` | `toString` | `()` | `String` | Converts/serializes representation via `toString` |
| `instance` | `hashCode` | `()` | `int` | Evaluates boolean predicate `hashCode` on `OnChooserClosing` |
| `instance` | `getClass` | `()` | `Class` | Retrieves `Class` property from `OnChooserClosing` |
| `instance` | `notify` | `()` | `void` | Performs notify operation |
| `instance` | `notifyAll` | `()` | `void` | Performs notify all operation |
| `instance` | `wait` | `(arg0: long)` | `void` | Performs wait operation |
| `instance` | `wait` | `(arg0: long, arg1: int)` | `void` | Performs wait operation |
| `instance` | `wait` | `()` | `void` | Performs wait operation |

---

### `OnViewTypeChanged`
- **Full Qualified Name:** `com.strategyquant.lib.utils.SQFileChooserFactory.JFileChooserPersisterImpl.OnViewTypeChanged`
- **Primary Job / Responsibility:** General utility subsystem (compression, file I/O, networking, OS inspection) (`OnViewTypeChanged`).

#### Methods & Functions
| Modifiers | Method Name | Parameter Signatures | Return Type | Functional Description / Job |
| :--- | :--- | :--- | :--- | :--- |
| `instance` | `propertyChange` | `(arg0: PropertyChangeEvent)` | `void` | Performs property change operation |
| `instance` | `equals` | `(arg0: Object)` | `boolean` | Performs equals operation |
| `instance` | `toString` | `()` | `String` | Converts/serializes representation via `toString` |
| `instance` | `hashCode` | `()` | `int` | Evaluates boolean predicate `hashCode` on `OnViewTypeChanged` |
| `instance` | `getClass` | `()` | `Class` | Retrieves `Class` property from `OnViewTypeChanged` |
| `instance` | `notify` | `()` | `void` | Performs notify operation |
| `instance` | `notifyAll` | `()` | `void` | Performs notify all operation |
| `instance` | `wait` | `(arg0: long)` | `void` | Performs wait operation |
| `instance` | `wait` | `(arg0: long, arg1: int)` | `void` | Performs wait operation |
| `instance` | `wait` | `()` | `void` | Performs wait operation |

---

### `SortOrderInfo`
- **Full Qualified Name:** `com.strategyquant.lib.utils.SQFileChooserFactory.JFileChooserPersisterImpl.SortOrderInfo`
- **Primary Job / Responsibility:** General utility subsystem (compression, file I/O, networking, OS inspection) (`SortOrderInfo`).

#### Methods & Functions
| Modifiers | Method Name | Parameter Signatures | Return Type | Functional Description / Job |
| :--- | :--- | :--- | :--- | :--- |
| `instance` | `setSortOrder` | `(arg0: RowSorter)` | `void` | Sets `SortOrder` configuration/state on `SortOrderInfo` |
| `instance` | `equals` | `(arg0: Object)` | `boolean` | Performs equals operation |
| `instance` | `toString` | `()` | `String` | Converts/serializes representation via `toString` |
| `instance` | `hashCode` | `()` | `int` | Evaluates boolean predicate `hashCode` on `SortOrderInfo` |
| `instance` | `getClass` | `()` | `Class` | Retrieves `Class` property from `SortOrderInfo` |
| `instance` | `notify` | `()` | `void` | Performs notify operation |
| `instance` | `notifyAll` | `()` | `void` | Performs notify all operation |
| `instance` | `wait` | `(arg0: long)` | `void` | Performs wait operation |
| `instance` | `wait` | `(arg0: long, arg1: int)` | `void` | Performs wait operation |
| `instance` | `wait` | `()` | `void` | Performs wait operation |

---

### `ColumnSortInfo`
- **Full Qualified Name:** `com.strategyquant.lib.utils.SQFileChooserFactory.JFileChooserPersisterImpl.SortOrderInfo.ColumnSortInfo`
- **Primary Job / Responsibility:** General utility subsystem (compression, file I/O, networking, OS inspection) (`ColumnSortInfo`).

#### Methods & Functions
| Modifiers | Method Name | Parameter Signatures | Return Type | Functional Description / Job |
| :--- | :--- | :--- | :--- | :--- |
| `instance` | `makeSortKey` | `()` | `SortKey` | Performs make sort key operation |
| `instance` | `equals` | `(arg0: Object)` | `boolean` | Performs equals operation |
| `instance` | `toString` | `()` | `String` | Converts/serializes representation via `toString` |
| `instance` | `hashCode` | `()` | `int` | Evaluates boolean predicate `hashCode` on `ColumnSortInfo` |
| `instance` | `getClass` | `()` | `Class` | Retrieves `Class` property from `ColumnSortInfo` |
| `instance` | `notify` | `()` | `void` | Performs notify operation |
| `instance` | `notifyAll` | `()` | `void` | Performs notify all operation |
| `instance` | `wait` | `(arg0: long)` | `void` | Performs wait operation |
| `instance` | `wait` | `(arg0: long, arg1: int)` | `void` | Performs wait operation |
| `instance` | `wait` | `()` | `void` | Performs wait operation |

---

### `SQUUID`
- **Full Qualified Name:** `com.strategyquant.lib.utils.SQUUID`
- **Primary Job / Responsibility:** General utility subsystem (compression, file I/O, networking, OS inspection) (`SQUUID`).

#### Methods & Functions
| Modifiers | Method Name | Parameter Signatures | Return Type | Functional Description / Job |
| :--- | :--- | :--- | :--- | :--- |
| `instance` | `equals` | `(arg0: Object)` | `boolean` | Performs equals operation |
| `instance` | `toString` | `()` | `String` | Converts/serializes representation via `toString` |
| `instance` | `hashCode` | `()` | `int` | Evaluates boolean predicate `hashCode` on `SQUUID` |
| `instance` | `getClass` | `()` | `Class` | Retrieves `Class` property from `SQUUID` |
| `instance` | `notify` | `()` | `void` | Performs notify operation |
| `instance` | `notifyAll` | `()` | `void` | Performs notify all operation |
| `instance` | `wait` | `(arg0: long)` | `void` | Performs wait operation |
| `instance` | `wait` | `(arg0: long, arg1: int)` | `void` | Performs wait operation |
| `instance` | `wait` | `()` | `void` | Performs wait operation |
| `static` | `randomUUID` | `()` | `String` | Performs random uuid operation |

---

### `StringComparator`
- **Full Qualified Name:** `com.strategyquant.lib.utils.StringComparator`
- **Primary Job / Responsibility:** General utility subsystem (compression, file I/O, networking, OS inspection) (`StringComparator`).

#### Methods & Functions
| Modifiers | Method Name | Parameter Signatures | Return Type | Functional Description / Job |
| :--- | :--- | :--- | :--- | :--- |
| `instance` | `compare` | `(arg0: Object, arg1: Object)` | `int` | Performs compare operation |
| `instance` | `compare` | `(arg0: String, arg1: String)` | `int` | Performs compare operation |
| `instance` | `equals` | `(arg0: Object)` | `boolean` | Performs equals operation |
| `instance` | `toString` | `()` | `String` | Converts/serializes representation via `toString` |
| `instance` | `hashCode` | `()` | `int` | Evaluates boolean predicate `hashCode` on `StringComparator` |
| `instance` | `getClass` | `()` | `Class` | Retrieves `Class` property from `StringComparator` |
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

### `StringOutputStream`
- **Full Qualified Name:** `com.strategyquant.lib.utils.StringOutputStream`
- **Primary Job / Responsibility:** General utility subsystem (compression, file I/O, networking, OS inspection) (`StringOutputStream`).

#### Methods & Functions
| Modifiers | Method Name | Parameter Signatures | Return Type | Functional Description / Job |
| :--- | :--- | :--- | :--- | :--- |
| `instance` | `toString` | `()` | `String` | Converts/serializes representation via `toString` |
| `instance` | `write` | `(arg0: byte[])` | `void` | Performs write operation |
| `instance` | `write` | `(arg0: int)` | `void` | Performs write operation |
| `instance` | `write` | `(arg0: byte[], arg1: int, arg2: int)` | `void` | Performs write operation |
| `instance` | `getCharacterSet` | `()` | `Charset` | Retrieves `CharacterSet` property from `StringOutputStream` |
| `instance` | `setCharacterSet` | `(arg0: Charset)` | `void` | Sets `CharacterSet` configuration/state on `StringOutputStream` |
| `instance` | `flush` | `()` | `void` | Performs flush operation |
| `instance` | `close` | `()` | `void` | Performs close operation |
| `instance` | `equals` | `(arg0: Object)` | `boolean` | Performs equals operation |
| `instance` | `hashCode` | `()` | `int` | Evaluates boolean predicate `hashCode` on `StringOutputStream` |
| `instance` | `getClass` | `()` | `Class` | Retrieves `Class` property from `StringOutputStream` |
| `instance` | `notify` | `()` | `void` | Performs notify operation |
| `instance` | `notifyAll` | `()` | `void` | Performs notify all operation |
| `instance` | `wait` | `(arg0: long)` | `void` | Performs wait operation |
| `instance` | `wait` | `(arg0: long, arg1: int)` | `void` | Performs wait operation |
| `instance` | `wait` | `()` | `void` | Performs wait operation |
| `static` | `nullOutputStream` | `()` | `OutputStream` | Performs null output stream operation |

---

### `SwingUtils`
- **Full Qualified Name:** `com.strategyquant.lib.utils.SwingUtils`
- **Primary Job / Responsibility:** General utility subsystem (compression, file I/O, networking, OS inspection) (`SwingUtils`).

#### Methods & Functions
| Modifiers | Method Name | Parameter Signatures | Return Type | Functional Description / Job |
| :--- | :--- | :--- | :--- | :--- |
| `instance` | `equals` | `(arg0: Object)` | `boolean` | Performs equals operation |
| `instance` | `toString` | `()` | `String` | Converts/serializes representation via `toString` |
| `instance` | `hashCode` | `()` | `int` | Evaluates boolean predicate `hashCode` on `SwingUtils` |
| `instance` | `getClass` | `()` | `Class` | Retrieves `Class` property from `SwingUtils` |
| `instance` | `notify` | `()` | `void` | Performs notify operation |
| `instance` | `notifyAll` | `()` | `void` | Performs notify all operation |
| `instance` | `wait` | `(arg0: long)` | `void` | Performs wait operation |
| `instance` | `wait` | `(arg0: long, arg1: int)` | `void` | Performs wait operation |
| `instance` | `wait` | `()` | `void` | Performs wait operation |
| `static` | `equals` | `(arg0: Object, arg1: Object)` | `boolean` | Performs equals operation |
| `static` | `getProperties` | `(arg0: JComponent)` | `Map` | Retrieves `Properties` property from `SwingUtils` |
| `static` | `getDescendantsOfType` | `(arg0: Class, arg1: Container)` | `List` | Retrieves `DescendantsOfType` property from `SwingUtils` |
| `static` | `getDescendantsOfType` | `(arg0: Class, arg1: Container, arg2: boolean)` | `List` | Retrieves `DescendantsOfType` property from `SwingUtils` |
| `static` | `getDescendantOfType` | `(arg0: Class, arg1: Container, arg2: String, arg3: Object, arg4: boolean)` | `JComponent` | Retrieves `DescendantOfType` property from `SwingUtils` |
| `static` | `getDescendantOfType` | `(arg0: Class, arg1: Container, arg2: String, arg3: Object)` | `JComponent` | Retrieves `DescendantOfType` property from `SwingUtils` |
| `static` | `getDescendantsOfClass` | `(arg0: Class, arg1: Container, arg2: boolean)` | `List` | Retrieves `DescendantsOfClass` property from `SwingUtils` |
| `static` | `getDescendantsOfClass` | `(arg0: Class, arg1: Container)` | `List` | Retrieves `DescendantsOfClass` property from `SwingUtils` |
| `static` | `getDescendantOfClass` | `(arg0: Class, arg1: Container, arg2: String, arg3: Object)` | `JComponent` | Retrieves `DescendantOfClass` property from `SwingUtils` |
| `static` | `getDescendantOfClass` | `(arg0: Class, arg1: Container, arg2: String, arg3: Object, arg4: boolean)` | `JComponent` | Retrieves `DescendantOfClass` property from `SwingUtils` |
| `static` | `getComponentMap` | `(arg0: JComponent, arg1: boolean)` | `Map` | Retrieves `ComponentMap` property from `SwingUtils` |
| `static` | `getUIDefaultsOfClass` | `(arg0: Class)` | `UIDefaults` | Retrieves `UIDefaultsOfClass` property from `SwingUtils` |
| `static` | `getUIDefaultsOfClass` | `(arg0: String)` | `UIDefaults` | Retrieves `UIDefaultsOfClass` property from `SwingUtils` |
| `static` | `getUIDefaultOfClass` | `(arg0: Class, arg1: String)` | `Object` | Retrieves `UIDefaultOfClass` property from `SwingUtils` |
| `static` | `getJClass` | `(arg0: JComponent)` | `Class` | Retrieves `JClass` property from `SwingUtils` |

---

### `TimeLocalObjects`
- **Full Qualified Name:** `com.strategyquant.lib.utils.TimeLocalObjects`
- **Primary Job / Responsibility:** General utility subsystem (compression, file I/O, networking, OS inspection) (`TimeLocalObjects`).

#### Fields
| Scope | Field Name | Type |
| :--- | :--- | :--- |
| `instance` | `chronology` | `ISOChronology` |
| `instance` | `computerTimeZone` | `DateTimeZone` |
| `instance` | `defaultTimezoneSet` | `boolean` |

#### Methods & Functions
| Modifiers | Method Name | Parameter Signatures | Return Type | Functional Description / Job |
| :--- | :--- | :--- | :--- | :--- |
| `instance` | `equals` | `(arg0: Object)` | `boolean` | Performs equals operation |
| `instance` | `toString` | `()` | `String` | Converts/serializes representation via `toString` |
| `instance` | `hashCode` | `()` | `int` | Evaluates boolean predicate `hashCode` on `TimeLocalObjects` |
| `instance` | `getClass` | `()` | `Class` | Retrieves `Class` property from `TimeLocalObjects` |
| `instance` | `notify` | `()` | `void` | Performs notify operation |
| `instance` | `notifyAll` | `()` | `void` | Performs notify all operation |
| `instance` | `wait` | `(arg0: long)` | `void` | Performs wait operation |
| `instance` | `wait` | `(arg0: long, arg1: int)` | `void` | Performs wait operation |
| `instance` | `wait` | `()` | `void` | Performs wait operation |

---

### `UnremovableArrayList`
- **Full Qualified Name:** `com.strategyquant.lib.utils.UnremovableArrayList`
- **Primary Job / Responsibility:** General utility subsystem (compression, file I/O, networking, OS inspection) (`UnremovableArrayList`).

#### Methods & Functions
| Modifiers | Method Name | Parameter Signatures | Return Type | Functional Description / Job |
| :--- | :--- | :--- | :--- | :--- |
| `instance` | `size` | `()` | `int` | Performs size operation |
| `instance` | `add` | `(arg0: Object)` | `void` | Appends/registers element via `add` |
| `instance` | `iterator` | `()` | `Iterator` | Performs iterator operation |
| `instance` | `addAll` | `(arg0: ArrayList)` | `void` | Appends/registers element via `addAll` |
| `instance` | `addAll` | `(arg0: UnremovableArrayList)` | `void` | Appends/registers element via `addAll` |
| `instance` | `equals` | `(arg0: Object)` | `boolean` | Performs equals operation |
| `instance` | `toString` | `()` | `String` | Converts/serializes representation via `toString` |
| `instance` | `hashCode` | `()` | `int` | Evaluates boolean predicate `hashCode` on `UnremovableArrayList` |
| `instance` | `getClass` | `()` | `Class` | Retrieves `Class` property from `UnremovableArrayList` |
| `instance` | `notify` | `()` | `void` | Performs notify operation |
| `instance` | `notifyAll` | `()` | `void` | Performs notify all operation |
| `instance` | `wait` | `(arg0: long)` | `void` | Performs wait operation |
| `instance` | `wait` | `(arg0: long, arg1: int)` | `void` | Performs wait operation |
| `instance` | `wait` | `()` | `void` | Performs wait operation |
| `instance` | `spliterator` | `()` | `Spliterator` | Performs spliterator operation |
| `instance` | `forEach` | `(arg0: Consumer)` | `void` | Performs for each operation |

---

### `Unzipper`
- **Full Qualified Name:** `com.strategyquant.lib.utils.Unzipper`
- **Primary Job / Responsibility:** General utility subsystem (compression, file I/O, networking, OS inspection) (`Unzipper`).

#### Fields
| Scope | Field Name | Type |
| :--- | :--- | :--- |
| `static` | `Log` | `Logger` |

#### Methods & Functions
| Modifiers | Method Name | Parameter Signatures | Return Type | Functional Description / Job |
| :--- | :--- | :--- | :--- | :--- |
| `instance` | `equals` | `(arg0: Object)` | `boolean` | Performs equals operation |
| `instance` | `toString` | `()` | `String` | Converts/serializes representation via `toString` |
| `instance` | `hashCode` | `()` | `int` | Evaluates boolean predicate `hashCode` on `Unzipper` |
| `instance` | `getClass` | `()` | `Class` | Retrieves `Class` property from `Unzipper` |
| `instance` | `notify` | `()` | `void` | Performs notify operation |
| `instance` | `notifyAll` | `()` | `void` | Performs notify all operation |
| `instance` | `wait` | `(arg0: long)` | `void` | Performs wait operation |
| `instance` | `wait` | `(arg0: long, arg1: int)` | `void` | Performs wait operation |
| `instance` | `wait` | `()` | `void` | Performs wait operation |
| `static` | `unzip` | `(arg0: String, arg1: String, arg2: boolean)` | `void` | Performs unzip operation |
| `static` | `unzip` | `(arg0: byte[], arg1: File)` | `void` | Performs unzip operation |

---

### `WizardConfigWorker`
- **Full Qualified Name:** `com.strategyquant.lib.utils.WizardConfigWorker`
- **Primary Job / Responsibility:** General utility subsystem (compression, file I/O, networking, OS inspection) (`WizardConfigWorker`).

#### Methods & Functions
| Modifiers | Method Name | Parameter Signatures | Return Type | Functional Description / Job |
| :--- | :--- | :--- | :--- | :--- |
| `instance` | `equals` | `(arg0: Object)` | `boolean` | Performs equals operation |
| `instance` | `toString` | `()` | `String` | Converts/serializes representation via `toString` |
| `instance` | `hashCode` | `()` | `int` | Evaluates boolean predicate `hashCode` on `WizardConfigWorker` |
| `instance` | `getClass` | `()` | `Class` | Retrieves `Class` property from `WizardConfigWorker` |
| `instance` | `notify` | `()` | `void` | Performs notify operation |
| `instance` | `notifyAll` | `()` | `void` | Performs notify all operation |
| `instance` | `wait` | `(arg0: long)` | `void` | Performs wait operation |
| `instance` | `wait` | `(arg0: long, arg1: int)` | `void` | Performs wait operation |
| `instance` | `wait` | `()` | `void` | Performs wait operation |
| `static` | `getWizardConfig` | `()` | `Element` | Retrieves `WizardConfig` property from `WizardConfigWorker` |
| `static` | `getElementsFromElement` | `(arg0: Element, arg1: String, arg2: String)` | `ArrayList` | Retrieves `ElementsFromElement` property from `WizardConfigWorker` |
| `static` | `getElementsFromCategory` | `(arg0: Element, arg1: String, arg2: String)` | `ArrayList` | Retrieves `ElementsFromCategory` property from `WizardConfigWorker` |
| `static` | `getBlockInfo` | `(arg0: Element, arg1: int)` | `JSONObject` | Retrieves `BlockInfo` property from `WizardConfigWorker` |
| `static` | `getSpecialItemInfo` | `(arg0: Element)` | `JSONObject` | Retrieves `SpecialItemInfo` property from `WizardConfigWorker` |

---

### `Zipper`
- **Full Qualified Name:** `com.strategyquant.lib.utils.Zipper`
- **Primary Job / Responsibility:** General utility subsystem (compression, file I/O, networking, OS inspection) (`Zipper`).

#### Methods & Functions
| Modifiers | Method Name | Parameter Signatures | Return Type | Functional Description / Job |
| :--- | :--- | :--- | :--- | :--- |
| `instance` | `equals` | `(arg0: Object)` | `boolean` | Performs equals operation |
| `instance` | `toString` | `()` | `String` | Converts/serializes representation via `toString` |
| `instance` | `hashCode` | `()` | `int` | Evaluates boolean predicate `hashCode` on `Zipper` |
| `instance` | `getClass` | `()` | `Class` | Retrieves `Class` property from `Zipper` |
| `instance` | `notify` | `()` | `void` | Performs notify operation |
| `instance` | `notifyAll` | `()` | `void` | Performs notify all operation |
| `instance` | `wait` | `(arg0: long)` | `void` | Performs wait operation |
| `instance` | `wait` | `(arg0: long, arg1: int)` | `void` | Performs wait operation |
| `instance` | `wait` | `()` | `void` | Performs wait operation |
| `static` | `zipDir` | `(arg0: File, arg1: File)` | `void` | Performs zip dir operation |
| `static` | `addFilesToExistingZip` | `(arg0: File, arg1: File)` | `void` | Appends/registers element via `addFilesToExistingZip` |

---

### `IMouseHookListener`
- **Full Qualified Name:** `com.strategyquant.lib.utils.mousehook.IMouseHookListener`
- **Primary Job / Responsibility:** General utility subsystem (compression, file I/O, networking, OS inspection) (`IMouseHookListener`).

#### Methods & Functions
| Modifiers | Method Name | Parameter Signatures | Return Type | Functional Description / Job |
| :--- | :--- | :--- | :--- | :--- |
| `instance` | `onGlobalMousePress` | `(arg0: Point)` | `void` | Performs on global mouse press operation |
| `instance` | `onComponentMousePress` | `(arg0: Point)` | `void` | Performs on component mouse press operation |
| `instance` | `onGlobalMouseRelease` | `(arg0: Point)` | `void` | Performs on global mouse release operation |
| `instance` | `onComponentMouseRelease` | `(arg0: Point)` | `void` | Performs on component mouse release operation |
| `instance` | `onGlobalMouseDrag` | `(arg0: Point, arg1: int, arg2: int)` | `void` | Performs on global mouse drag operation |
| `instance` | `onComponentMouseDrag` | `(arg0: Point, arg1: int, arg2: int)` | `void` | Performs on component mouse drag operation |
| `instance` | `onGlobalMouseMove` | `(arg0: Point)` | `void` | Performs on global mouse move operation |
| `instance` | `onComponentMouseMove` | `(arg0: Point)` | `void` | Performs on component mouse move operation |

---

### `MouseHook`
- **Full Qualified Name:** `com.strategyquant.lib.utils.mousehook.MouseHook`
- **Primary Job / Responsibility:** General utility subsystem (compression, file I/O, networking, OS inspection) (`MouseHook`).

#### Fields
| Scope | Field Name | Type |
| :--- | :--- | :--- |
| `static` | `Log` | `Logger` |
| `static` | `MAX_PRIORITY` | `int` |
| `static` | `MIN_PRIORITY` | `int` |
| `static` | `NORM_PRIORITY` | `int` |

#### Methods & Functions
| Modifiers | Method Name | Parameter Signatures | Return Type | Functional Description / Job |
| :--- | :--- | :--- | :--- | :--- |
| `instance` | `run` | `()` | `void` | Controls lifecycle execution: `run` |
| `instance` | `destroy` | `()` | `void` | Performs destroy operation |
| `instance` | `addListener` | `(arg0: IMouseHookListener)` | `void` | Appends/registers element via `addListener` |
| `instance` | `removeListener` | `(arg0: IMouseHookListener)` | `void` | Removes/resets elements via `removeListener` |
| `instance` | `getName` | `()` | `String` | Retrieves `Name` property from `MouseHook` |
| `instance` | `getStackTrace` | `()` | `StackTraceElement[]` | Retrieves `StackTrace` property from `MouseHook` |
| `instance` | `interrupt` | `()` | `void` | Performs interrupt operation |
| `instance` | `toString` | `()` | `String` | Converts/serializes representation via `toString` |
| `instance` | `join` | `(arg0: Duration)` | `void` | Performs join operation |
| `instance` | `join` | `(arg0: long, arg1: int)` | `void` | Performs join operation |
| `instance` | `join` | `()` | `void` | Performs join operation |
| `instance` | `join` | `(arg0: long)` | `void` | Performs join operation |
| `instance` | `setContextClassLoader` | `(arg0: ClassLoader)` | `void` | Sets `ContextClassLoader` configuration/state on `MouseHook` |
| `instance` | `setPriority` | `(arg0: int)` | `void` | Sets `Priority` configuration/state on `MouseHook` |
| `instance` | `setDaemon` | `(arg0: boolean)` | `void` | Sets `Daemon` configuration/state on `MouseHook` |
| `instance` | `start` | `()` | `void` | Controls lifecycle execution: `start` |
| `instance` | `getThreadGroup` | `()` | `ThreadGroup` | Retrieves `ThreadGroup` property from `MouseHook` |
| `instance` | `getPriority` | `()` | `int` | Retrieves `Priority` property from `MouseHook` |
| `instance` | `isDaemon` | `()` | `boolean` | Evaluates boolean predicate `isDaemon` on `MouseHook` |
| `instance` | `getContextClassLoader` | `()` | `ClassLoader` | Retrieves `ContextClassLoader` property from `MouseHook` |
| `instance` | `isVirtual` | `()` | `boolean` | Evaluates boolean predicate `isVirtual` on `MouseHook` |
| `instance` | `isAlive` | `()` | `boolean` | Evaluates boolean predicate `isAlive` on `MouseHook` |
| `instance` | `threadId` | `()` | `long` | Performs thread id operation |
| `instance` | `getUncaughtExceptionHandler` | `()` | `UncaughtExceptionHandler` | Retrieves `UncaughtExceptionHandler` property from `MouseHook` |
| `instance` | `stop` | `()` | `void` | Controls lifecycle execution: `stop` |
| `instance` | `isInterrupted` | `()` | `boolean` | Evaluates boolean predicate `isInterrupted` on `MouseHook` |
| `instance` | `setName` | `(arg0: String)` | `void` | Sets `Name` configuration/state on `MouseHook` |
| `instance` | `checkAccess` | `()` | `void` | Performs check access operation |
| `instance` | `getId` | `()` | `long` | Retrieves `Id` property from `MouseHook` |
| `instance` | `getState` | `()` | `State` | Retrieves `State` property from `MouseHook` |
| `instance` | `setUncaughtExceptionHandler` | `(arg0: UncaughtExceptionHandler)` | `void` | Sets `UncaughtExceptionHandler` configuration/state on `MouseHook` |
| `instance` | `equals` | `(arg0: Object)` | `boolean` | Performs equals operation |
| `instance` | `hashCode` | `()` | `int` | Evaluates boolean predicate `hashCode` on `MouseHook` |
| `instance` | `getClass` | `()` | `Class` | Retrieves `Class` property from `MouseHook` |
| `instance` | `notify` | `()` | `void` | Performs notify operation |
| `instance` | `notifyAll` | `()` | `void` | Performs notify all operation |
| `instance` | `wait` | `(arg0: long)` | `void` | Performs wait operation |
| `instance` | `wait` | `(arg0: long, arg1: int)` | `void` | Performs wait operation |
| `instance` | `wait` | `()` | `void` | Performs wait operation |
| `static` | `getComponentPoint` | `(arg0: Point, arg1: Component)` | `Point` | Retrieves `ComponentPoint` property from `MouseHook` |
| `static` | `currentThread` | `()` | `Thread` | Performs current thread operation |
| `static` | `onSpinWait` | `()` | `void` | Performs on spin wait operation |
| `static` | `holdsLock` | `(arg0: Object)` | `boolean` | Performs holds lock operation |
| `static` | `interrupted` | `()` | `boolean` | Performs interrupted operation |
| `static` | `activeCount` | `()` | `int` | Performs active count operation |
| `static` | `enumerate` | `(arg0: Thread[])` | `int` | Performs enumerate operation |
| `static` | `yield` | `()` | `void` | Performs yield operation |
| `static` | `sleep` | `(arg0: long)` | `void` | Performs sleep operation |
| `static` | `sleep` | `(arg0: long, arg1: int)` | `void` | Performs sleep operation |
| `static` | `sleep` | `(arg0: Duration)` | `void` | Performs sleep operation |
| `static` | `ofPlatform` | `()` | `OfPlatform` | Performs of platform operation |
| `static` | `ofVirtual` | `()` | `OfVirtual` | Performs of virtual operation |
| `static` | `startVirtualThread` | `(arg0: Runnable)` | `Thread` | Performs start virtual thread operation |
| `static` | `dumpStack` | `()` | `void` | Performs dump stack operation |
| `static` | `getAllStackTraces` | `()` | `Map` | Retrieves `AllStackTraces` property from `MouseHook` |
| `static` | `setDefaultUncaughtExceptionHandler` | `(arg0: UncaughtExceptionHandler)` | `void` | Sets `DefaultUncaughtExceptionHandler` configuration/state on `MouseHook` |
| `static` | `getDefaultUncaughtExceptionHandler` | `()` | `UncaughtExceptionHandler` | Retrieves `DefaultUncaughtExceptionHandler` property from `MouseHook` |

---

### `MouseHookAdapter`
- **Full Qualified Name:** `com.strategyquant.lib.utils.mousehook.MouseHookAdapter`
- **Primary Job / Responsibility:** General utility subsystem (compression, file I/O, networking, OS inspection) (`MouseHookAdapter`).

#### Methods & Functions
| Modifiers | Method Name | Parameter Signatures | Return Type | Functional Description / Job |
| :--- | :--- | :--- | :--- | :--- |
| `instance` | `onGlobalMousePress` | `(arg0: Point)` | `void` | Performs on global mouse press operation |
| `instance` | `onComponentMousePress` | `(arg0: Point)` | `void` | Performs on component mouse press operation |
| `instance` | `onGlobalMouseRelease` | `(arg0: Point)` | `void` | Performs on global mouse release operation |
| `instance` | `onComponentMouseRelease` | `(arg0: Point)` | `void` | Performs on component mouse release operation |
| `instance` | `onGlobalMouseDrag` | `(arg0: Point, arg1: int, arg2: int)` | `void` | Performs on global mouse drag operation |
| `instance` | `onComponentMouseDrag` | `(arg0: Point, arg1: int, arg2: int)` | `void` | Performs on component mouse drag operation |
| `instance` | `onGlobalMouseMove` | `(arg0: Point)` | `void` | Performs on global mouse move operation |
| `instance` | `onComponentMouseMove` | `(arg0: Point)` | `void` | Performs on component mouse move operation |
| `instance` | `equals` | `(arg0: Object)` | `boolean` | Performs equals operation |
| `instance` | `toString` | `()` | `String` | Converts/serializes representation via `toString` |
| `instance` | `hashCode` | `()` | `int` | Evaluates boolean predicate `hashCode` on `MouseHookAdapter` |
| `instance` | `getClass` | `()` | `Class` | Retrieves `Class` property from `MouseHookAdapter` |
| `instance` | `notify` | `()` | `void` | Performs notify operation |
| `instance` | `notifyAll` | `()` | `void` | Performs notify all operation |
| `instance` | `wait` | `(arg0: long)` | `void` | Performs wait operation |
| `instance` | `wait` | `(arg0: long, arg1: int)` | `void` | Performs wait operation |
| `instance` | `wait` | `()` | `void` | Performs wait operation |

---

### `DataDownloader`
- **Full Qualified Name:** `com.strategyquant.lib.utils.network.DataDownloader`
- **Primary Job / Responsibility:** General utility subsystem (compression, file I/O, networking, OS inspection) (`DataDownloader`).

#### Methods & Functions
| Modifiers | Method Name | Parameter Signatures | Return Type | Functional Description / Job |
| :--- | :--- | :--- | :--- | :--- |
| `instance` | `toFile` | `(arg0: String, arg1: String, arg2: IDataDownloader)` | `void` | Converts/serializes representation via `toFile` |
| `instance` | `getContentLength` | `(arg0: String)` | `long` | Retrieves `ContentLength` property from `DataDownloader` |
| `instance` | `equals` | `(arg0: Object)` | `boolean` | Performs equals operation |
| `instance` | `toString` | `()` | `String` | Converts/serializes representation via `toString` |
| `instance` | `hashCode` | `()` | `int` | Evaluates boolean predicate `hashCode` on `DataDownloader` |
| `instance` | `getClass` | `()` | `Class` | Retrieves `Class` property from `DataDownloader` |
| `instance` | `notify` | `()` | `void` | Performs notify operation |
| `instance` | `notifyAll` | `()` | `void` | Performs notify all operation |
| `instance` | `wait` | `(arg0: long)` | `void` | Performs wait operation |
| `instance` | `wait` | `(arg0: long, arg1: int)` | `void` | Performs wait operation |
| `instance` | `wait` | `()` | `void` | Performs wait operation |

---

### `HttpUtil`
- **Full Qualified Name:** `com.strategyquant.lib.utils.network.HttpUtil`
- **Primary Job / Responsibility:** General utility subsystem (compression, file I/O, networking, OS inspection) (`HttpUtil`).

#### Methods & Functions
| Modifiers | Method Name | Parameter Signatures | Return Type | Functional Description / Job |
| :--- | :--- | :--- | :--- | :--- |
| `instance` | `equals` | `(arg0: Object)` | `boolean` | Performs equals operation |
| `instance` | `toString` | `()` | `String` | Converts/serializes representation via `toString` |
| `instance` | `hashCode` | `()` | `int` | Evaluates boolean predicate `hashCode` on `HttpUtil` |
| `instance` | `getClass` | `()` | `Class` | Retrieves `Class` property from `HttpUtil` |
| `instance` | `notify` | `()` | `void` | Performs notify operation |
| `instance` | `notifyAll` | `()` | `void` | Performs notify all operation |
| `instance` | `wait` | `(arg0: long)` | `void` | Performs wait operation |
| `instance` | `wait` | `(arg0: long, arg1: int)` | `void` | Performs wait operation |
| `instance` | `wait` | `()` | `void` | Performs wait operation |
| `static` | `sendRequest` | `(arg0: String, arg1: String)` | `HttpResponse` | Performs send request operation |
| `static` | `sendAsyncRequest` | `(arg0: String, arg1: IHttpRequestListener)` | `void` | Performs send async request operation |

---

### `IDataDownloader`
- **Full Qualified Name:** `com.strategyquant.lib.utils.network.IDataDownloader`
- **Primary Job / Responsibility:** General utility subsystem (compression, file I/O, networking, OS inspection) (`IDataDownloader`).

#### Methods & Functions
| Modifiers | Method Name | Parameter Signatures | Return Type | Functional Description / Job |
| :--- | :--- | :--- | :--- | :--- |
| `instance` | `onProgress` | `(arg0: int, arg1: long, arg2: long, arg3: long)` | `void` | Performs on progress operation |

---

### `IHttpRequestListener`
- **Full Qualified Name:** `com.strategyquant.lib.utils.network.IHttpRequestListener`
- **Primary Job / Responsibility:** General utility subsystem (compression, file I/O, networking, OS inspection) (`IHttpRequestListener`).

#### Methods & Functions
| Modifiers | Method Name | Parameter Signatures | Return Type | Functional Description / Job |
| :--- | :--- | :--- | :--- | :--- |
| `instance` | `onResponse` | `(arg0: HttpResponse)` | `void` | Performs on response operation |

---
