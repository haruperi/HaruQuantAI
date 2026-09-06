# MQL5 Constants, Enumerations, and Structures Classification

## Purpose and scope

This catalogue classifies the identifiers documented in the MQL5 reference, pages 319–1040 inclusive, as design inputs for HaruQuantAI. The objective is familiar mental mapping—not MT5 interoperability, wire compatibility, or dependence on MetaTrader. Each recommendation remains subject to contract-level design and implementation review.

The inventory includes declared enumeration types and their members, standalone or named constants, predefined structures, and qualified structure fields. Repeated mentions and example-only declarations are excluded. Explicit documented values are retained at the start of the Description cell because the requested schema has no separate Value column.

## Classification rubric

- **Exact adoption:** the MQL5 identifier and bounded meaning are suitable as the HaruQuantAI contract without renaming.
- **Platform-neutral rename:** the concept is useful, but MQL/terminal/vendor wording or a platform-specific type name is replaced with HaruQuantAI-neutral terminology.
- **Semantic extension:** the identifier is retained while HaruQuantAI adds provider neutrality, provenance, lifecycle, validation, or richer error semantics.
- **Rejected adoption:** the construct is compiler-, runtime-, marketplace-, operating-system-, or otherwise platform-bound and should not become a HaruQuantAI public contract.
- **HaruQuantAI-native:** reserved for concepts originating in HaruQuantAI. No rows receive this classification because this is deliberately an MQL5-source inventory.

## Domain placement

Domains name the intended owning folder below `app/contracts/`. `ui` owns chart, graphical-object, theme, and dialog contracts; `indicator` owns calculation and plotting identifiers; `catalogue` owns instrument metadata; `data` owns market series, order-book, calendar, and history data; `broker` owns account/provider outcomes; `trading` owns orders, positions, deals, and execution intent; `risk` owns pre-trade checks; `analytics` owns test and performance statistics; `interfaces` owns files, encodings, network, and cryptographic I/O; `plugins` owns program lifecycle; `workspace` owns application runtime state; `research`, `notification`, and `common` own their corresponding neutral concerns. Rejected rows use `—` because no contract owner is proposed.

## Source coverage

The covered source sections are Chart Constants (320–400), Objects Constants (401–732), Indicator Constants (733–753), Environment State (754–896), Trade Constants (897–941), Named Constants (942–960), Data Structures (961–1001), Codes of Errors and Warnings (1002–1032), and Input/Output Constants (1033–1040). Page 319 is the section introduction; page 1041 begins the next reference chapter and is excluded.

## Classification catalogue

| Identifier | Description | Type | Category | Classification | Contract | Domain |
| --- | --- | --- | --- | --- | --- | --- |
| ENUM_CHART_EVENT | Defines the identifier set for chart event. | enum (int) | Enumerations | Exact adoption | ENUM_CHART_EVENT | ui |
| CHARTEVENT_KEYUP | Selects keyup in chart event. | ENUM_CHART_EVENT | Enumerations | Exact adoption | CHARTEVENT_KEYUP | ui |
| CHARTEVENT_KEYDOWN | Selects keydown in chart event. | ENUM_CHART_EVENT | Enumerations | Exact adoption | CHARTEVENT_KEYDOWN | ui |
| CHARTEVENT_MOUSE_MOVE | Selects mouse move in chart event. | ENUM_CHART_EVENT | Enumerations | Exact adoption | CHARTEVENT_MOUSE_MOVE | ui |
| CHARTEVENT_MOUSE_WHEEL | Selects mouse wheel in chart event. | ENUM_CHART_EVENT | Enumerations | Exact adoption | CHARTEVENT_MOUSE_WHEEL | ui |
| CHARTEVENT_OBJECT_CREATE | Selects object create in chart event. | ENUM_CHART_EVENT | Enumerations | Exact adoption | CHARTEVENT_OBJECT_CREATE | ui |
| CHARTEVENT_OBJECT_CHANGE | Selects object change in chart event. | ENUM_CHART_EVENT | Enumerations | Exact adoption | CHARTEVENT_OBJECT_CHANGE | ui |
| CHARTEVENT_OBJECT_DELETE | Selects object delete in chart event. | ENUM_CHART_EVENT | Enumerations | Exact adoption | CHARTEVENT_OBJECT_DELETE | ui |
| CHARTEVENT_CLICK | Selects click in chart event. | ENUM_CHART_EVENT | Enumerations | Exact adoption | CHARTEVENT_CLICK | ui |
| CHARTEVENT_OBJECT_CLICK | Selects object click in chart event. | ENUM_CHART_EVENT | Enumerations | Exact adoption | CHARTEVENT_OBJECT_CLICK | ui |
| CHARTEVENT_OBJECT_DRAG | Selects object drag in chart event. | ENUM_CHART_EVENT | Enumerations | Exact adoption | CHARTEVENT_OBJECT_DRAG | ui |
| CHARTEVENT_OBJECT_ENDEDIT | Selects object endedit in chart event. | ENUM_CHART_EVENT | Enumerations | Exact adoption | CHARTEVENT_OBJECT_ENDEDIT | ui |
| CHARTEVENT_CHART_CHANGE | Selects chart change in chart event. | ENUM_CHART_EVENT | Enumerations | Exact adoption | CHARTEVENT_CHART_CHANGE | ui |
| CHARTEVENT_CUSTOM | Selects custom in chart event. | ENUM_CHART_EVENT | Enumerations | Exact adoption | CHARTEVENT_CUSTOM | ui |
| CHARTEVENT_CUSTOM_LAST | Selects custom last in chart event. | ENUM_CHART_EVENT | Enumerations | Exact adoption | CHARTEVENT_CUSTOM_LAST | ui |
| ENUM_TIMEFRAMES | Defines the identifier set for timeframes. | enum (int) | Enumerations | Exact adoption | ENUM_TIMEFRAMES | data |
| PERIOD_CURRENT | Selects the current chart timeframe. | ENUM_TIMEFRAMES | Enumerations | Exact adoption | PERIOD_CURRENT | data |
| PERIOD_M1 | Selects a 1-minute timeframe. | ENUM_TIMEFRAMES | Enumerations | Exact adoption | PERIOD_M1 | data |
| PERIOD_M2 | Selects a 2-minute timeframe. | ENUM_TIMEFRAMES | Enumerations | Exact adoption | PERIOD_M2 | data |
| PERIOD_M3 | Selects a 3-minute timeframe. | ENUM_TIMEFRAMES | Enumerations | Exact adoption | PERIOD_M3 | data |
| PERIOD_M4 | Selects a 4-minute timeframe. | ENUM_TIMEFRAMES | Enumerations | Exact adoption | PERIOD_M4 | data |
| PERIOD_M5 | Selects a 5-minute timeframe. | ENUM_TIMEFRAMES | Enumerations | Exact adoption | PERIOD_M5 | data |
| PERIOD_M6 | Selects a 6-minute timeframe. | ENUM_TIMEFRAMES | Enumerations | Exact adoption | PERIOD_M6 | data |
| PERIOD_M10 | Selects a 10-minute timeframe. | ENUM_TIMEFRAMES | Enumerations | Exact adoption | PERIOD_M10 | data |
| PERIOD_M12 | Selects a 12-minute timeframe. | ENUM_TIMEFRAMES | Enumerations | Exact adoption | PERIOD_M12 | data |
| PERIOD_M15 | Selects a 15-minute timeframe. | ENUM_TIMEFRAMES | Enumerations | Exact adoption | PERIOD_M15 | data |
| PERIOD_M20 | Selects a 20-minute timeframe. | ENUM_TIMEFRAMES | Enumerations | Exact adoption | PERIOD_M20 | data |
| PERIOD_M30 | Selects a 30-minute timeframe. | ENUM_TIMEFRAMES | Enumerations | Exact adoption | PERIOD_M30 | data |
| PERIOD_H1 | Selects a 1-hour timeframe. | ENUM_TIMEFRAMES | Enumerations | Exact adoption | PERIOD_H1 | data |
| PERIOD_H2 | Selects a 2-hour timeframe. | ENUM_TIMEFRAMES | Enumerations | Exact adoption | PERIOD_H2 | data |
| PERIOD_H3 | Selects a 3-hour timeframe. | ENUM_TIMEFRAMES | Enumerations | Exact adoption | PERIOD_H3 | data |
| PERIOD_H4 | Selects a 4-hour timeframe. | ENUM_TIMEFRAMES | Enumerations | Exact adoption | PERIOD_H4 | data |
| PERIOD_H6 | Selects a 6-hour timeframe. | ENUM_TIMEFRAMES | Enumerations | Exact adoption | PERIOD_H6 | data |
| PERIOD_H8 | Selects an 8-hour timeframe. | ENUM_TIMEFRAMES | Enumerations | Exact adoption | PERIOD_H8 | data |
| PERIOD_H12 | Selects a 12-hour timeframe. | ENUM_TIMEFRAMES | Enumerations | Exact adoption | PERIOD_H12 | data |
| PERIOD_D1 | Selects a 1-day timeframe. | ENUM_TIMEFRAMES | Enumerations | Exact adoption | PERIOD_D1 | data |
| PERIOD_W1 | Selects a 1-week timeframe. | ENUM_TIMEFRAMES | Enumerations | Exact adoption | PERIOD_W1 | data |
| PERIOD_MN1 | Selects a 1-month timeframe. | ENUM_TIMEFRAMES | Enumerations | Exact adoption | PERIOD_MN1 | data |
| ENUM_SERIESMODE | Defines the identifier set for seriesmode. | enum (int) | Enumerations | Exact adoption | ENUM_SERIESMODE | data |
| MODE_OPEN | Selects open in seriesmode. | ENUM_SERIESMODE | Enumerations | Exact adoption | MODE_OPEN | data |
| MODE_LOW | Selects low in seriesmode. | ENUM_SERIESMODE | Enumerations | Exact adoption | MODE_LOW | data |
| MODE_HIGH | Selects high in seriesmode. | ENUM_SERIESMODE | Enumerations | Exact adoption | MODE_HIGH | data |
| MODE_CLOSE | Selects close in seriesmode. | ENUM_SERIESMODE | Enumerations | Exact adoption | MODE_CLOSE | data |
| MODE_VOLUME | Selects volume in seriesmode. | ENUM_SERIESMODE | Enumerations | Exact adoption | MODE_VOLUME | data |
| MODE_REAL_VOLUME | Selects real volume in seriesmode. | ENUM_SERIESMODE | Enumerations | Exact adoption | MODE_REAL_VOLUME | data |
| MODE_SPREAD | Selects spread in seriesmode. | ENUM_SERIESMODE | Enumerations | Exact adoption | MODE_SPREAD | data |
| ENUM_CHART_PROPERTY_INTEGER | Defines the identifier set for chart property integer. | enum (int) | Enumerations | Exact adoption | ENUM_CHART_PROPERTY_INTEGER | ui |
| CHART_SHOW | Selects show in chart property integer. | bool | Enumerations | Exact adoption | CHART_SHOW | ui |
| CHART_IS_OBJECT | Selects is object in chart property integer. | bool r/o | Enumerations | Exact adoption | CHART_IS_OBJECT | ui |
| CHART_BRING_TO_TOP | Selects bring to top in chart property integer. | bool | Enumerations | Exact adoption | CHART_BRING_TO_TOP | ui |
| CHART_CONTEXT_MENU | Selects context menu in chart property integer. | bool (default is true) | Enumerations | Exact adoption | CHART_CONTEXT_MENU | ui |
| CHART_CROSSHAIR_TOOL | Selects crosshair tool in chart property integer. | bool (default is true) | Enumerations | Exact adoption | CHART_CROSSHAIR_TOOL | ui |
| CHART_MOUSE_SCROLL | Selects mouse scroll in chart property integer. | bool | Enumerations | Exact adoption | CHART_MOUSE_SCROLL | ui |
| CHART_EVENT_MOUSE_WHEEL | Selects event mouse wheel in chart property integer. | bool (default is true) | Enumerations | Exact adoption | CHART_EVENT_MOUSE_WHEEL | ui |
| CHART_EVENT_MOUSE_MOVE | Selects event mouse move in chart property integer. | bool | Enumerations | Exact adoption | CHART_EVENT_MOUSE_MOVE | ui |
| CHART_EVENT_OBJECT_CREATE | Selects event object create in chart property integer. | bool | Enumerations | Exact adoption | CHART_EVENT_OBJECT_CREATE | ui |
| CHART_EVENT_OBJECT_DELETE | Selects event object delete in chart property integer. | bool | Enumerations | Exact adoption | CHART_EVENT_OBJECT_DELETE | ui |
| CHART_MODE | Selects mode in chart property integer. | enum ENUM_CHART_MODE | Enumerations | Exact adoption | CHART_MODE | ui |
| CHART_FOREGROUND | Selects foreground in chart property integer. | bool | Enumerations | Exact adoption | CHART_FOREGROUND | ui |
| CHART_SHIFT | Selects shift in chart property integer. | bool | Enumerations | Exact adoption | CHART_SHIFT | ui |
| CHART_AUTOSCROLL | Selects autoscroll in chart property integer. | bool | Enumerations | Exact adoption | CHART_AUTOSCROLL | ui |
| CHART_KEYBOARD_CONTROL | Selects keyboard control in chart property integer. | bool | Enumerations | Exact adoption | CHART_KEYBOARD_CONTROL | ui |
| CHART_QUICK_NAVIGATION | Selects quick navigation in chart property integer. | bool | Enumerations | Exact adoption | CHART_QUICK_NAVIGATION | ui |
| CHART_SCALE | Selects scale in chart property integer. | int from 0 to 5 | Enumerations | Exact adoption | CHART_SCALE | ui |
| CHART_SCALEFIX | Selects scalefix in chart property integer. | bool | Enumerations | Exact adoption | CHART_SCALEFIX | ui |
| CHART_SCALEFIX_11 | Selects scalefix 11 in chart property integer. | bool | Enumerations | Exact adoption | CHART_SCALEFIX_11 | ui |
| CHART_SCALE_PT_PER_BAR | Selects scale pt per bar in chart property integer. | bool | Enumerations | Exact adoption | CHART_SCALE_PT_PER_BAR | ui |
| CHART_SHOW_TICKER | Selects show ticker in chart property integer. | bool | Enumerations | Exact adoption | CHART_SHOW_TICKER | ui |
| CHART_SHOW_OHLC | Selects show OHLC in chart property integer. | bool | Enumerations | Exact adoption | CHART_SHOW_OHLC | ui |
| CHART_SHOW_BID_LINE | Selects show bid line in chart property integer. | bool | Enumerations | Exact adoption | CHART_SHOW_BID_LINE | ui |
| CHART_SHOW_ASK_LINE | Selects show ask line in chart property integer. | bool | Enumerations | Exact adoption | CHART_SHOW_ASK_LINE | ui |
| CHART_SHOW_LAST_LINE | Selects show last line in chart property integer. | bool | Enumerations | Exact adoption | CHART_SHOW_LAST_LINE | ui |
| CHART_SHOW_PERIOD_SEP | Selects show period sep in chart property integer. | bool | Enumerations | Exact adoption | CHART_SHOW_PERIOD_SEP | ui |
| CHART_SHOW_GRID | Selects show grid in chart property integer. | bool | Enumerations | Exact adoption | CHART_SHOW_GRID | ui |
| CHART_SHOW_VOLUMES | Selects show volumes in chart property integer. | enum ENUM_CHART_VOLUME_MODE | Enumerations | Exact adoption | CHART_SHOW_VOLUMES | ui |
| CHART_SHOW_OBJECT_DESCR | Selects show object descr in chart property integer. | bool | Enumerations | Exact adoption | CHART_SHOW_OBJECT_DESCR | ui |
| CHART_SHOW_TRADE_HISTORY | Selects show trade history in chart property integer. | bool | Enumerations | Exact adoption | CHART_SHOW_TRADE_HISTORY | ui |
| CHART_VISIBLE_BARS | Selects visible bars in chart property integer. | int r/o | Enumerations | Exact adoption | CHART_VISIBLE_BARS | ui |
| CHART_WINDOWS_TOTAL | Selects windows total in chart property integer. | int r/o | Enumerations | Exact adoption | CHART_WINDOWS_TOTAL | ui |
| CHART_WINDOW_IS_VISIBLE | Selects window is visible in chart property integer. | bool r/o modifier - subwindow number | Enumerations | Exact adoption | CHART_WINDOW_IS_VISIBLE | ui |
| CHART_WINDOW_HANDLE | Selects window handle in chart property integer. | int r/o | Enumerations | Exact adoption | CHART_WINDOW_HANDLE | ui |
| CHART_WINDOW_YDISTANCE | Selects window ydistance in chart property integer. | int r/o modifier - subwindow number | Enumerations | Exact adoption | CHART_WINDOW_YDISTANCE | ui |
| CHART_FIRST_VISIBLE_BAR | Selects first visible bar in chart property integer. | int r/o | Enumerations | Exact adoption | CHART_FIRST_VISIBLE_BAR | ui |
| CHART_WIDTH_IN_BARS | Selects width in bars in chart property integer. | int r/o | Enumerations | Exact adoption | CHART_WIDTH_IN_BARS | ui |
| CHART_WIDTH_IN_PIXELS | Selects width in pixels in chart property integer. | int r/o | Enumerations | Exact adoption | CHART_WIDTH_IN_PIXELS | ui |
| CHART_HEIGHT_IN_PIXELS | Selects height in pixels in chart property integer. | int modifier - subwindow number | Enumerations | Exact adoption | CHART_HEIGHT_IN_PIXELS | ui |
| CHART_COLOR_BACKGROUND | Selects color background in chart property integer. | color | Enumerations | Exact adoption | CHART_COLOR_BACKGROUND | ui |
| CHART_COLOR_FOREGROUND | Selects color foreground in chart property integer. | color | Enumerations | Exact adoption | CHART_COLOR_FOREGROUND | ui |
| CHART_COLOR_GRID | Selects color grid in chart property integer. | color | Enumerations | Exact adoption | CHART_COLOR_GRID | ui |
| CHART_COLOR_VOLUME | Selects color volume in chart property integer. | color | Enumerations | Exact adoption | CHART_COLOR_VOLUME | ui |
| CHART_COLOR_CHART_UP | Selects color chart up in chart property integer. | color | Enumerations | Exact adoption | CHART_COLOR_CHART_UP | ui |
| CHART_COLOR_CHART_DOWN | Selects color chart down in chart property integer. | color | Enumerations | Exact adoption | CHART_COLOR_CHART_DOWN | ui |
| CHART_COLOR_CHART_LINE | Selects color chart line in chart property integer. | color | Enumerations | Exact adoption | CHART_COLOR_CHART_LINE | ui |
| CHART_COLOR_CANDLE_BULL | Selects color candle bull in chart property integer. | color | Enumerations | Exact adoption | CHART_COLOR_CANDLE_BULL | ui |
| CHART_COLOR_CANDLE_BEAR | Selects color candle bear in chart property integer. | color | Enumerations | Exact adoption | CHART_COLOR_CANDLE_BEAR | ui |
| CHART_COLOR_BID | Selects color bid in chart property integer. | color | Enumerations | Exact adoption | CHART_COLOR_BID | ui |
| CHART_COLOR_ASK | Selects color ask in chart property integer. | color | Enumerations | Exact adoption | CHART_COLOR_ASK | ui |
| CHART_COLOR_LAST | Selects color last in chart property integer. | color | Enumerations | Exact adoption | CHART_COLOR_LAST | ui |
| CHART_COLOR_STOP_LEVEL | Selects color stop level in chart property integer. | color | Enumerations | Exact adoption | CHART_COLOR_STOP_LEVEL | ui |
| CHART_SHOW_TRADE_LEVELS | Selects show trade levels in chart property integer. | bool | Enumerations | Exact adoption | CHART_SHOW_TRADE_LEVELS | ui |
| CHART_DRAG_TRADE_LEVELS | Selects drag trade levels in chart property integer. | bool | Enumerations | Exact adoption | CHART_DRAG_TRADE_LEVELS | ui |
| CHART_SHOW_DATE_SCALE | Selects show date scale in chart property integer. | bool | Enumerations | Exact adoption | CHART_SHOW_DATE_SCALE | ui |
| CHART_SHOW_PRICE_SCALE | Selects show price scale in chart property integer. | bool | Enumerations | Exact adoption | CHART_SHOW_PRICE_SCALE | ui |
| CHART_SHOW_ONE_CLICK | Selects show one click in chart property integer. | bool | Enumerations | Exact adoption | CHART_SHOW_ONE_CLICK | ui |
| CHART_IS_MAXIMIZED | Selects is maximized in chart property integer. | bool r/o | Enumerations | Exact adoption | CHART_IS_MAXIMIZED | ui |
| CHART_IS_MINIMIZED | Selects is minimized in chart property integer. | bool r/o | Enumerations | Exact adoption | CHART_IS_MINIMIZED | ui |
| CHART_IS_DOCKED | Selects is docked in chart property integer. | bool | Enumerations | Exact adoption | CHART_IS_DOCKED | ui |
| CHART_FLOAT_LEFT | Selects float left in chart property integer. | int | Enumerations | Exact adoption | CHART_FLOAT_LEFT | ui |
| CHART_FLOAT_TOP | Selects float top in chart property integer. | int | Enumerations | Exact adoption | CHART_FLOAT_TOP | ui |
| CHART_FLOAT_RIGHT | Selects float right in chart property integer. | int | Enumerations | Exact adoption | CHART_FLOAT_RIGHT | ui |
| ENUM_CHART_PROPERTY_DOUBLE | Defines the identifier set for chart property double. | enum (int) | Enumerations | Exact adoption | ENUM_CHART_PROPERTY_DOUBLE | ui |
| CHART_FLOAT_BOTTOM | Selects float bottom in chart property double. | int | Enumerations | Exact adoption | CHART_FLOAT_BOTTOM | ui |
| CHART_SHIFT_SIZE | Selects shift size in chart property double. | double (from 10 to 50 percents) | Enumerations | Exact adoption | CHART_SHIFT_SIZE | ui |
| CHART_FIXED_POSITION | Selects fixed position in chart property double. | double | Enumerations | Exact adoption | CHART_FIXED_POSITION | ui |
| CHART_FIXED_MAX | Selects fixed max in chart property double. | double | Enumerations | Exact adoption | CHART_FIXED_MAX | ui |
| CHART_FIXED_MIN | Selects fixed min in chart property double. | double | Enumerations | Exact adoption | CHART_FIXED_MIN | ui |
| CHART_POINTS_PER_BAR | Selects points per bar in chart property double. | double | Enumerations | Exact adoption | CHART_POINTS_PER_BAR | ui |
| CHART_PRICE_MIN | Selects price min in chart property double. | double r/o modifier - subwindow number | Enumerations | Exact adoption | CHART_PRICE_MIN | ui |
| CHART_PRICE_MAX | Selects price max in chart property double. | double r/o modifier - subwindow number | Enumerations | Exact adoption | CHART_PRICE_MAX | ui |
| ENUM_CHART_PROPERTY_STRING | Defines the identifier set for chart property string. | enum (int) | Enumerations | Exact adoption | ENUM_CHART_PROPERTY_STRING | ui |
| CHART_COMMENT | Selects comment in chart property string. | string | Enumerations | Exact adoption | CHART_COMMENT | ui |
| CHART_EXPERT_NAME | Selects expert name in chart property string. | string r/o | Enumerations | Platform-neutral rename | CHART_AUTOMATION_NAME | ui |
| CHART_SCRIPT_NAME | Selects script name in chart property string. | string r/o | Enumerations | Exact adoption | CHART_SCRIPT_NAME | ui |
| ENUM_CHART_POSITION | Defines the identifier set for chart position. | enum (int) | Enumerations | Exact adoption | ENUM_CHART_POSITION | ui |
| CHART_BEGIN | Selects begin in chart position. | ENUM_CHART_POSITION | Enumerations | Exact adoption | CHART_BEGIN | ui |
| CHART_CURRENT_POS | Selects current pos in chart position. | ENUM_CHART_POSITION | Enumerations | Exact adoption | CHART_CURRENT_POS | ui |
| CHART_END | Selects end in chart position. | ENUM_CHART_POSITION | Enumerations | Exact adoption | CHART_END | ui |
| ENUM_CHART_MODE | Defines the identifier set for chart mode. | enum (int) | Enumerations | Exact adoption | ENUM_CHART_MODE | ui |
| ENUM_CHART_VOLUME_MODE | Defines the identifier set for chart volume mode. | enum (int) | Enumerations | Exact adoption | ENUM_CHART_VOLUME_MODE | ui |
| CHART_BARS | Selects bars in chart mode. | ENUM_CHART_MODE | Enumerations | Exact adoption | CHART_BARS | ui |
| CHART_CANDLES | Selects candles in chart volume mode. | ENUM_CHART_VOLUME_MODE | Enumerations | Exact adoption | CHART_CANDLES | ui |
| CHART_LINE | Selects line in chart mode. | ENUM_CHART_MODE | Enumerations | Exact adoption | CHART_LINE | ui |
| CHART_VOLUME_HIDE | Selects volume hide in chart volume mode. | ENUM_CHART_VOLUME_MODE | Enumerations | Exact adoption | CHART_VOLUME_HIDE | ui |
| CHART_VOLUME_TICK | Selects volume tick in chart volume mode. | ENUM_CHART_VOLUME_MODE | Enumerations | Exact adoption | CHART_VOLUME_TICK | ui |
| CHART_VOLUME_REAL | Selects volume real in chart volume mode. | ENUM_CHART_VOLUME_MODE | Enumerations | Exact adoption | CHART_VOLUME_REAL | ui |
| ENUM_OBJECT | Defines the identifier set for object. | enum (int) | Enumerations | Exact adoption | ENUM_OBJECT | ui |
| OBJ_VLINE | Selects vline in object. | ENUM_OBJECT | Enumerations | Exact adoption | OBJ_VLINE | ui |
| OBJ_HLINE | Selects hline in object. | ENUM_OBJECT | Enumerations | Exact adoption | OBJ_HLINE | ui |
| OBJ_TREND | Selects trend in object. | ENUM_OBJECT | Enumerations | Exact adoption | OBJ_TREND | ui |
| OBJ_TRENDBYANGLE | Selects trendbyangle in object. | ENUM_OBJECT | Enumerations | Exact adoption | OBJ_TRENDBYANGLE | ui |
| OBJ_CYCLES | Selects cycles in object. | ENUM_OBJECT | Enumerations | Exact adoption | OBJ_CYCLES | ui |
| OBJ_ARROWED_LINE | Selects arrowed line in object. | ENUM_OBJECT | Enumerations | Exact adoption | OBJ_ARROWED_LINE | ui |
| OBJ_CHANNEL | Selects channel in object. | ENUM_OBJECT | Enumerations | Exact adoption | OBJ_CHANNEL | ui |
| OBJ_STDDEVCHANNEL | Selects stddevchannel in object. | ENUM_OBJECT | Enumerations | Exact adoption | OBJ_STDDEVCHANNEL | ui |
| OBJ_REGRESSION | Selects regression in object. | ENUM_OBJECT | Enumerations | Exact adoption | OBJ_REGRESSION | ui |
| OBJ_PITCHFORK | Selects pitchfork in object. | ENUM_OBJECT | Enumerations | Exact adoption | OBJ_PITCHFORK | ui |
| OBJ_GANNLINE | Selects gannline in object. | ENUM_OBJECT | Enumerations | Exact adoption | OBJ_GANNLINE | ui |
| OBJ_GANNFAN | Selects gannfan in object. | ENUM_OBJECT | Enumerations | Exact adoption | OBJ_GANNFAN | ui |
| OBJ_GANNGRID | Selects ganngrid in object. | ENUM_OBJECT | Enumerations | Exact adoption | OBJ_GANNGRID | ui |
| OBJ_FIBO | Selects fibo in object. | ENUM_OBJECT | Enumerations | Exact adoption | OBJ_FIBO | ui |
| OBJ_FIBOTIMES | Selects fibotimes in object. | ENUM_OBJECT | Enumerations | Exact adoption | OBJ_FIBOTIMES | ui |
| OBJ_FIBOFAN | Selects fibofan in object. | ENUM_OBJECT | Enumerations | Exact adoption | OBJ_FIBOFAN | ui |
| OBJ_FIBOARC | Selects fiboarc in object. | ENUM_OBJECT | Enumerations | Exact adoption | OBJ_FIBOARC | ui |
| OBJ_FIBOCHANNEL | Selects fibochannel in object. | ENUM_OBJECT | Enumerations | Exact adoption | OBJ_FIBOCHANNEL | ui |
| OBJ_EXPANSION | Selects expansion in object. | ENUM_OBJECT | Enumerations | Exact adoption | OBJ_EXPANSION | ui |
| OBJ_ELLIOTWAVE5 | Selects elliotwave5 in object. | ENUM_OBJECT | Enumerations | Exact adoption | OBJ_ELLIOTWAVE5 | ui |
| OBJ_ELLIOTWAVE3 | Selects elliotwave3 in object. | ENUM_OBJECT | Enumerations | Exact adoption | OBJ_ELLIOTWAVE3 | ui |
| OBJ_RECTANGLE | Selects rectangle in object. | ENUM_OBJECT | Enumerations | Exact adoption | OBJ_RECTANGLE | ui |
| OBJ_TRIANGLE | Selects triangle in object. | ENUM_OBJECT | Enumerations | Exact adoption | OBJ_TRIANGLE | ui |
| OBJ_ELLIPSE | Selects ellipse in object. | ENUM_OBJECT | Enumerations | Exact adoption | OBJ_ELLIPSE | ui |
| OBJ_ARROW_THUMB_UP | Selects arrow thumb up in object. | ENUM_OBJECT | Enumerations | Exact adoption | OBJ_ARROW_THUMB_UP | ui |
| OBJ_ARROW_THUMB_DOWN | Selects arrow thumb down in object. | ENUM_OBJECT | Enumerations | Exact adoption | OBJ_ARROW_THUMB_DOWN | ui |
| OBJ_ARROW_UP | Selects arrow up in object. | ENUM_OBJECT | Enumerations | Exact adoption | OBJ_ARROW_UP | ui |
| OBJ_ARROW_DOWN | Selects arrow down in object. | ENUM_OBJECT | Enumerations | Exact adoption | OBJ_ARROW_DOWN | ui |
| OBJ_ARROW_STOP | Selects arrow stop in object. | ENUM_OBJECT | Enumerations | Exact adoption | OBJ_ARROW_STOP | ui |
| OBJ_ARROW_CHECK | Selects arrow check in object. | ENUM_OBJECT | Enumerations | Exact adoption | OBJ_ARROW_CHECK | ui |
| OBJ_ARROW_LEFT_PRICE | Selects arrow left price in object. | ENUM_OBJECT | Enumerations | Exact adoption | OBJ_ARROW_LEFT_PRICE | ui |
| OBJ_ARROW_RIGHT_PRICE | Selects arrow right price in object. | ENUM_OBJECT | Enumerations | Exact adoption | OBJ_ARROW_RIGHT_PRICE | ui |
| OBJ_ARROW_BUY | Selects arrow buy in object. | ENUM_OBJECT | Enumerations | Exact adoption | OBJ_ARROW_BUY | ui |
| OBJ_ARROW_SELL | Selects arrow sell in object. | ENUM_OBJECT | Enumerations | Exact adoption | OBJ_ARROW_SELL | ui |
| OBJ_ARROW | Selects arrow in object. | ENUM_OBJECT | Enumerations | Exact adoption | OBJ_ARROW | ui |
| OBJ_TEXT | Selects text in object. | ENUM_OBJECT | Enumerations | Exact adoption | OBJ_TEXT | ui |
| OBJ_LABEL | Selects label in object. | ENUM_OBJECT | Enumerations | Exact adoption | OBJ_LABEL | ui |
| OBJ_BUTTON | Selects button in object. | ENUM_OBJECT | Enumerations | Exact adoption | OBJ_BUTTON | ui |
| OBJ_CHART | Selects chart in object. | ENUM_OBJECT | Enumerations | Exact adoption | OBJ_CHART | ui |
| OBJ_BITMAP | Selects bitmap in object. | ENUM_OBJECT | Enumerations | Exact adoption | OBJ_BITMAP | ui |
| OBJ_BITMAP_LABEL | Selects bitmap label in object. | ENUM_OBJECT | Enumerations | Exact adoption | OBJ_BITMAP_LABEL | ui |
| OBJ_EDIT | Selects edit in object. | ENUM_OBJECT | Enumerations | Exact adoption | OBJ_EDIT | ui |
| OBJ_EVENT | Selects event in object. | ENUM_OBJECT | Enumerations | Exact adoption | OBJ_EVENT | ui |
| OBJ_RECTANGLE_LABEL | Selects rectangle label in object. | ENUM_OBJECT | Enumerations | Exact adoption | OBJ_RECTANGLE_LABEL | ui |
| ENUM_OBJECT_PROPERTY_INTEGER | Defines the identifier set for object property integer. | enum (int) | Enumerations | Exact adoption | ENUM_OBJECT_PROPERTY_INTEGER | ui |
| OBJPROP_COLOR | Selects color in object property integer. | color | Enumerations | Exact adoption | OBJPROP_COLOR | ui |
| OBJPROP_STYLE | Selects style in object property integer. | ENUM_LINE_STYLE | Enumerations | Exact adoption | OBJPROP_STYLE | ui |
| OBJPROP_WIDTH | Selects width in object property integer. | int | Enumerations | Exact adoption | OBJPROP_WIDTH | ui |
| OBJPROP_BACK | Selects back in object property integer. | bool | Enumerations | Exact adoption | OBJPROP_BACK | ui |
| OBJPROP_ZORDER | Selects zorder in object property integer. | long | Enumerations | Exact adoption | OBJPROP_ZORDER | ui |
| OBJPROP_FILL | Selects fill in object property integer. | bool | Enumerations | Exact adoption | OBJPROP_FILL | ui |
| OBJPROP_HIDDEN | Selects hidden in object property integer. | bool | Enumerations | Exact adoption | OBJPROP_HIDDEN | ui |
| OBJPROP_SELECTED | Selects selected in object property integer. | bool | Enumerations | Exact adoption | OBJPROP_SELECTED | ui |
| OBJPROP_READONLY | Selects readonly in object property integer. | bool | Enumerations | Exact adoption | OBJPROP_READONLY | ui |
| OBJPROP_TYPE | Selects type in object property integer. | ENUM_OBJECT r/o | Enumerations | Exact adoption | OBJPROP_TYPE | ui |
| OBJPROP_TIME | Selects time in object property integer. | datetime modifier=number of anchor point | Enumerations | Exact adoption | OBJPROP_TIME | ui |
| OBJPROP_SELECTABLE | Selects selectable in object property integer. | bool | Enumerations | Exact adoption | OBJPROP_SELECTABLE | ui |
| OBJPROP_CREATETIME | Selects createtime in object property integer. | datetime r/o | Enumerations | Exact adoption | OBJPROP_CREATETIME | ui |
| OBJPROP_LEVELS | Selects levels in object property integer. | int | Enumerations | Exact adoption | OBJPROP_LEVELS | ui |
| OBJPROP_LEVELCOLOR | Selects levelcolor in object property integer. | color modifier=level number | Enumerations | Exact adoption | OBJPROP_LEVELCOLOR | ui |
| OBJPROP_LEVELSTYLE | Selects levelstyle in object property integer. | ENUM_LINE_STYLE modifier=level number | Enumerations | Exact adoption | OBJPROP_LEVELSTYLE | ui |
| OBJPROP_LEVELWIDTH | Selects levelwidth in object property integer. | int modifier=level number | Enumerations | Exact adoption | OBJPROP_LEVELWIDTH | ui |
| OBJPROP_ALIGN | Selects align in object property integer. | ENUM_ALIGN_MODE | Enumerations | Exact adoption | OBJPROP_ALIGN | ui |
| OBJPROP_FONTSIZE | Selects fontsize in object property integer. | int | Enumerations | Exact adoption | OBJPROP_FONTSIZE | ui |
| OBJPROP_RAY_LEFT | Selects ray left in object property integer. | bool | Enumerations | Exact adoption | OBJPROP_RAY_LEFT | ui |
| OBJPROP_RAY_RIGHT | Selects ray right in object property integer. | bool | Enumerations | Exact adoption | OBJPROP_RAY_RIGHT | ui |
| OBJPROP_RAY | Selects ray in object property integer. | bool | Enumerations | Exact adoption | OBJPROP_RAY | ui |
| OBJPROP_ELLIPSE | Selects ellipse in object property integer. | bool | Enumerations | Exact adoption | OBJPROP_ELLIPSE | ui |
| OBJPROP_ARROWCODE | Selects arrowcode in object property integer. | uchar | Enumerations | Exact adoption | OBJPROP_ARROWCODE | ui |
| OBJPROP_TIMEFRAMES | Selects timeframes in object property integer. | set of flags flags | Enumerations | Exact adoption | OBJPROP_TIMEFRAMES | ui |
| OBJPROP_ANCHOR | Selects anchor in object property integer. | ENUM_ARROW_ANCHOR (for OBJ_ARROW), ENUM_ANCHOR_POINT (for OBJ_LABEL, OBJ_BITMAP_LABEL and OBJ_TEXT) | Enumerations | Exact adoption | OBJPROP_ANCHOR | ui |
| OBJPROP_XDISTANCE | Selects xdistance in object property integer. | int | Enumerations | Exact adoption | OBJPROP_XDISTANCE | ui |
| OBJPROP_YDISTANCE | Selects ydistance in object property integer. | int | Enumerations | Exact adoption | OBJPROP_YDISTANCE | ui |
| OBJPROP_DIRECTION | Selects direction in object property integer. | ENUM_GANN_DIRECTION | Enumerations | Exact adoption | OBJPROP_DIRECTION | ui |
| OBJPROP_DEGREE | Selects degree in object property integer. | ENUM_ELLIOT_WAVE_DEGREE | Enumerations | Exact adoption | OBJPROP_DEGREE | ui |
| OBJPROP_DRAWLINES | Selects drawlines in object property integer. | bool | Enumerations | Exact adoption | OBJPROP_DRAWLINES | ui |
| OBJPROP_STATE | Selects state in object property integer. | bool | Enumerations | Exact adoption | OBJPROP_STATE | ui |
| OBJPROP_CHART_ID | Selects chart ID in object property integer. | long r/o | Enumerations | Exact adoption | OBJPROP_CHART_ID | ui |
| OBJPROP_XSIZE | Selects xsize in object property integer. | int | Enumerations | Exact adoption | OBJPROP_XSIZE | ui |
| OBJPROP_YSIZE | Selects ysize in object property integer. | int | Enumerations | Exact adoption | OBJPROP_YSIZE | ui |
| OBJPROP_XOFFSET | Selects xoffset in object property integer. | int | Enumerations | Exact adoption | OBJPROP_XOFFSET | ui |
| OBJPROP_YOFFSET | Selects yoffset in object property integer. | int | Enumerations | Exact adoption | OBJPROP_YOFFSET | ui |
| OBJPROP_PERIOD | Selects period in object property integer. | ENUM_TIMEFRAMES | Enumerations | Exact adoption | OBJPROP_PERIOD | ui |
| OBJPROP_DATE_SCALE | Selects date scale in object property integer. | bool | Enumerations | Exact adoption | OBJPROP_DATE_SCALE | ui |
| OBJPROP_PRICE_SCALE | Selects price scale in object property integer. | bool | Enumerations | Exact adoption | OBJPROP_PRICE_SCALE | ui |
| OBJPROP_CHART_SCALE | Selects chart scale in object property integer. | int value in the range 0–5 | Enumerations | Exact adoption | OBJPROP_CHART_SCALE | ui |
| OBJPROP_BGCOLOR | Selects bgcolor in object property integer. | color | Enumerations | Exact adoption | OBJPROP_BGCOLOR | ui |
| OBJPROP_CORNER | Selects corner in object property integer. | ENUM_BASE_CORNER | Enumerations | Exact adoption | OBJPROP_CORNER | ui |
| OBJPROP_BORDER_TYPE | Selects border type in object property integer. | ENUM_BORDER_TYPE | Enumerations | Exact adoption | OBJPROP_BORDER_TYPE | ui |
| OBJPROP_BORDER_COLOR | Selects border color in object property integer. | color | Enumerations | Exact adoption | OBJPROP_BORDER_COLOR | ui |
| ENUM_OBJECT_PROPERTY_DOUBLE | Defines the identifier set for object property double. | enum (int) | Enumerations | Exact adoption | ENUM_OBJECT_PROPERTY_DOUBLE | ui |
| OBJPROP_PRICE | Selects price in object property double. | double modifier=number of anchor point | Enumerations | Exact adoption | OBJPROP_PRICE | ui |
| OBJPROP_LEVELVALUE | Selects levelvalue in object property double. | double modifier=level number | Enumerations | Exact adoption | OBJPROP_LEVELVALUE | ui |
| OBJPROP_SCALE | Selects scale in object property double. | double | Enumerations | Exact adoption | OBJPROP_SCALE | ui |
| OBJPROP_ANGLE | Selects angle in object property double. | double | Enumerations | Exact adoption | OBJPROP_ANGLE | ui |
| ENUM_OBJECT_PROPERTY_STRING | Defines the identifier set for object property string. | enum (int) | Enumerations | Exact adoption | ENUM_OBJECT_PROPERTY_STRING | ui |
| OBJPROP_DEVIATION | Selects deviation in object property double. | double | Enumerations | Exact adoption | OBJPROP_DEVIATION | ui |
| OBJPROP_NAME | Selects name in object property string. | string | Enumerations | Exact adoption | OBJPROP_NAME | ui |
| OBJPROP_TEXT | Selects text in object property string. | string | Enumerations | Exact adoption | OBJPROP_TEXT | ui |
| OBJPROP_TOOLTIP | Selects tooltip in object property string. | string | Enumerations | Exact adoption | OBJPROP_TOOLTIP | ui |
| OBJPROP_LEVELTEXT | Selects leveltext in object property string. | string modifier=level number | Enumerations | Exact adoption | OBJPROP_LEVELTEXT | ui |
| OBJPROP_FONT | Selects font in object property string. | string | Enumerations | Exact adoption | OBJPROP_FONT | ui |
| OBJPROP_BMPFILE | Selects bmpfile in object property string. | string modifier: 0-state ON, 1-state OFF | Enumerations | Exact adoption | OBJPROP_BMPFILE | ui |
| OBJPROP_SYMBOL | Selects symbol in object property string. | string | Enumerations | Exact adoption | OBJPROP_SYMBOL | ui |
| ENUM_BORDER_TYPE | Defines the identifier set for border type. | enum (int) | Enumerations | Exact adoption | ENUM_BORDER_TYPE | ui |
| ENUM_ALIGN_MODE | Defines the identifier set for align mode. | enum (int) | Enumerations | Exact adoption | ENUM_ALIGN_MODE | ui |
| BORDER_FLAT | Selects border flat in border type. | ENUM_BORDER_TYPE | Enumerations | Exact adoption | BORDER_FLAT | ui |
| BORDER_RAISED | Selects border raised in border type. | ENUM_BORDER_TYPE | Enumerations | Exact adoption | BORDER_RAISED | ui |
| BORDER_SUNKEN | Selects border sunken in border type. | ENUM_BORDER_TYPE | Enumerations | Exact adoption | BORDER_SUNKEN | ui |
| ALIGN_LEFT | Selects align left in align mode. | ENUM_ALIGN_MODE | Enumerations | Exact adoption | ALIGN_LEFT | ui |
| ALIGN_CENTER | Selects align center in align mode. | ENUM_ALIGN_MODE | Enumerations | Exact adoption | ALIGN_CENTER | ui |
| ALIGN_RIGHT | Selects align right in align mode. | ENUM_ALIGN_MODE | Enumerations | Exact adoption | ALIGN_RIGHT | ui |
| ENUM_ANCHOR_POINT | Defines the identifier set for anchor point. | enum (int) | Enumerations | Exact adoption | ENUM_ANCHOR_POINT | ui |
| ANCHOR_LEFT_UPPER | Selects anchor left upper in anchor point. | ENUM_ANCHOR_POINT | Enumerations | Exact adoption | ANCHOR_LEFT_UPPER | ui |
| ANCHOR_LEFT | Selects anchor left in anchor point. | ENUM_ANCHOR_POINT | Enumerations | Exact adoption | ANCHOR_LEFT | ui |
| ANCHOR_LEFT_LOWER | Selects anchor left lower in anchor point. | ENUM_ANCHOR_POINT | Enumerations | Exact adoption | ANCHOR_LEFT_LOWER | ui |
| ANCHOR_LOWER | Selects anchor lower in anchor point. | ENUM_ANCHOR_POINT | Enumerations | Exact adoption | ANCHOR_LOWER | ui |
| ANCHOR_RIGHT_LOWER | Selects anchor right lower in anchor point. | ENUM_ANCHOR_POINT | Enumerations | Exact adoption | ANCHOR_RIGHT_LOWER | ui |
| ANCHOR_RIGHT | Selects anchor right in anchor point. | ENUM_ANCHOR_POINT | Enumerations | Exact adoption | ANCHOR_RIGHT | ui |
| ANCHOR_RIGHT_UPPER | Selects anchor right upper in anchor point. | ENUM_ANCHOR_POINT | Enumerations | Exact adoption | ANCHOR_RIGHT_UPPER | ui |
| ANCHOR_UPPER | Selects anchor upper in anchor point. | ENUM_ANCHOR_POINT | Enumerations | Exact adoption | ANCHOR_UPPER | ui |
| ANCHOR_CENTER | Selects anchor center in anchor point. | ENUM_ANCHOR_POINT | Enumerations | Exact adoption | ANCHOR_CENTER | ui |
| ENUM_ARROW_ANCHOR | Defines the identifier set for arrow anchor. | enum (int) | Enumerations | Exact adoption | ENUM_ARROW_ANCHOR | ui |
| ANCHOR_TOP | Selects anchor top in arrow anchor. | ENUM_ARROW_ANCHOR | Enumerations | Exact adoption | ANCHOR_TOP | ui |
| ANCHOR_BOTTOM | Selects anchor bottom in arrow anchor. | ENUM_ARROW_ANCHOR | Enumerations | Exact adoption | ANCHOR_BOTTOM | ui |
| ENUM_BASE_CORNER | Defines the identifier set for base corner. | enum (int) | Enumerations | Exact adoption | ENUM_BASE_CORNER | ui |
| CORNER_LEFT_UPPER | Selects corner left upper in base corner. | ENUM_BASE_CORNER | Enumerations | Exact adoption | CORNER_LEFT_UPPER | ui |
| CORNER_LEFT_LOWER | Selects corner left lower in base corner. | ENUM_BASE_CORNER | Enumerations | Exact adoption | CORNER_LEFT_LOWER | ui |
| CORNER_RIGHT_LOWER | Selects corner right lower in base corner. | ENUM_BASE_CORNER | Enumerations | Exact adoption | CORNER_RIGHT_LOWER | ui |
| CORNER_RIGHT_UPPER | Selects corner right upper in base corner. | ENUM_BASE_CORNER | Enumerations | Exact adoption | CORNER_RIGHT_UPPER | ui |
| OBJ_NO_PERIODS | Value: 0. Represents obj no periods. | Not specified in reference | Constants | Exact adoption | OBJ_NO_PERIODS | ui |
| OBJ_PERIOD_M1 | Value: 0x00000001. Represents obj period m1. | Not specified in reference | Constants | Exact adoption | OBJ_PERIOD_M1 | ui |
| OBJ_PERIOD_M2 | Value: 0x00000002. Represents obj period m2. | Not specified in reference | Constants | Exact adoption | OBJ_PERIOD_M2 | ui |
| OBJ_PERIOD_M3 | Value: 0x00000004. Represents obj period m3. | Not specified in reference | Constants | Exact adoption | OBJ_PERIOD_M3 | ui |
| OBJ_PERIOD_M4 | Value: 0x00000008. Represents obj period m4. | Not specified in reference | Constants | Exact adoption | OBJ_PERIOD_M4 | ui |
| OBJ_PERIOD_M5 | Value: 0x00000010. Represents obj period m5. | Not specified in reference | Constants | Exact adoption | OBJ_PERIOD_M5 | ui |
| OBJ_PERIOD_M6 | Value: 0x00000020. Represents obj period m6. | Not specified in reference | Constants | Exact adoption | OBJ_PERIOD_M6 | ui |
| OBJ_PERIOD_M10 | Value: 0x00000040. Represents obj period m10. | Not specified in reference | Constants | Exact adoption | OBJ_PERIOD_M10 | ui |
| OBJ_PERIOD_M12 | Value: 0x00000080. Represents obj period m12. | Not specified in reference | Constants | Exact adoption | OBJ_PERIOD_M12 | ui |
| OBJ_PERIOD_M15 | Value: 0x00000100. Represents obj period m15. | Not specified in reference | Constants | Exact adoption | OBJ_PERIOD_M15 | ui |
| OBJ_PERIOD_M20 | Value: 0x00000200. Represents obj period m20. | Not specified in reference | Constants | Exact adoption | OBJ_PERIOD_M20 | ui |
| OBJ_PERIOD_M30 | Value: 0x00000400. Represents obj period m30. | Not specified in reference | Constants | Exact adoption | OBJ_PERIOD_M30 | ui |
| OBJ_PERIOD_H1 | Value: 0x00000800. Represents obj period h1. | Not specified in reference | Constants | Exact adoption | OBJ_PERIOD_H1 | ui |
| OBJ_PERIOD_H2 | Value: 0x00001000. Represents obj period h2. | Not specified in reference | Constants | Exact adoption | OBJ_PERIOD_H2 | ui |
| OBJ_PERIOD_H3 | Value: 0x00002000. Represents obj period h3. | Not specified in reference | Constants | Exact adoption | OBJ_PERIOD_H3 | ui |
| OBJ_PERIOD_H4 | Value: 0x00004000. Represents obj period h4. | Not specified in reference | Constants | Exact adoption | OBJ_PERIOD_H4 | ui |
| OBJ_PERIOD_H6 | Value: 0x00008000. Represents obj period h6. | Not specified in reference | Constants | Exact adoption | OBJ_PERIOD_H6 | ui |
| OBJ_PERIOD_H8 | Value: 0x00010000. Represents obj period h8. | Not specified in reference | Constants | Exact adoption | OBJ_PERIOD_H8 | ui |
| OBJ_PERIOD_H12 | Value: 0x00020000. Represents obj period h12. | Not specified in reference | Constants | Exact adoption | OBJ_PERIOD_H12 | ui |
| OBJ_PERIOD_D1 | Value: 0x00040000. Represents obj period d1. | Not specified in reference | Constants | Exact adoption | OBJ_PERIOD_D1 | ui |
| OBJ_PERIOD_W1 | Value: 0x00080000. Represents obj period w1. | Not specified in reference | Constants | Exact adoption | OBJ_PERIOD_W1 | ui |
| OBJ_PERIOD_MN1 | Value: 0x00100000. Represents obj period mn1. | Not specified in reference | Constants | Exact adoption | OBJ_PERIOD_MN1 | ui |
| OBJ_ALL_PERIODS | Value: 0x001fffff. Represents obj all periods. | Not specified in reference | Constants | Exact adoption | OBJ_ALL_PERIODS | ui |
| ENUM_ELLIOT_WAVE_DEGREE | Defines the identifier set for elliot wave degree. | enum (int) | Enumerations | Exact adoption | ENUM_ELLIOT_WAVE_DEGREE | ui |
| ELLIOTT_GRAND_SUPERCYCLE | Selects elliott grand supercycle in elliot wave degree. | ENUM_ELLIOT_WAVE_DEGREE | Enumerations | Exact adoption | ELLIOTT_GRAND_SUPERCYCLE | ui |
| ELLIOTT_SUPERCYCLE | Selects elliott supercycle in elliot wave degree. | ENUM_ELLIOT_WAVE_DEGREE | Enumerations | Exact adoption | ELLIOTT_SUPERCYCLE | ui |
| ELLIOTT_CYCLE | Selects elliott cycle in elliot wave degree. | ENUM_ELLIOT_WAVE_DEGREE | Enumerations | Exact adoption | ELLIOTT_CYCLE | ui |
| ELLIOTT_PRIMARY | Selects elliott primary in elliot wave degree. | ENUM_ELLIOT_WAVE_DEGREE | Enumerations | Exact adoption | ELLIOTT_PRIMARY | ui |
| ELLIOTT_INTERMEDIATE | Selects elliott intermediate in elliot wave degree. | ENUM_ELLIOT_WAVE_DEGREE | Enumerations | Exact adoption | ELLIOTT_INTERMEDIATE | ui |
| ELLIOTT_MINOR | Selects elliott minor in elliot wave degree. | ENUM_ELLIOT_WAVE_DEGREE | Enumerations | Exact adoption | ELLIOTT_MINOR | ui |
| ELLIOTT_MINUTE | Selects elliott minute in elliot wave degree. | ENUM_ELLIOT_WAVE_DEGREE | Enumerations | Exact adoption | ELLIOTT_MINUTE | ui |
| ELLIOTT_MINUETTE | Selects elliott minuette in elliot wave degree. | ENUM_ELLIOT_WAVE_DEGREE | Enumerations | Exact adoption | ELLIOTT_MINUETTE | ui |
| ELLIOTT_SUBMINUETTE | Selects elliott subminuette in elliot wave degree. | ENUM_ELLIOT_WAVE_DEGREE | Enumerations | Exact adoption | ELLIOTT_SUBMINUETTE | ui |
| ENUM_GANN_DIRECTION | Defines the identifier set for gann direction. | enum (int) | Enumerations | Exact adoption | ENUM_GANN_DIRECTION | ui |
| GANN_UP_TREND | Selects gann up trend in gann direction. | ENUM_GANN_DIRECTION | Enumerations | Exact adoption | GANN_UP_TREND | ui |
| GANN_DOWN_TREND | Selects gann down trend in gann direction. | ENUM_GANN_DIRECTION | Enumerations | Exact adoption | GANN_DOWN_TREND | ui |
| clrBlack | Provides the predefined Black UI color. | color | Constants | Exact adoption | clrBlack | ui |
| clrDarkGreen | Provides the predefined DarkGreen UI color. | color | Constants | Exact adoption | clrDarkGreen | ui |
| clrDarkSlateGray | Provides the predefined DarkSlateGray UI color. | color | Constants | Exact adoption | clrDarkSlateGray | ui |
| clrOlive | Provides the predefined Olive UI color. | color | Constants | Exact adoption | clrOlive | ui |
| clrGreen | Provides the predefined Green UI color. | color | Constants | Exact adoption | clrGreen | ui |
| clrTeal | Provides the predefined Teal UI color. | color | Constants | Exact adoption | clrTeal | ui |
| clrNavy | Provides the predefined Navy UI color. | color | Constants | Exact adoption | clrNavy | ui |
| clrPurple | Provides the predefined Purple UI color. | color | Constants | Exact adoption | clrPurple | ui |
| clrMaroon | Provides the predefined Maroon UI color. | color | Constants | Exact adoption | clrMaroon | ui |
| clrIndigo | Provides the predefined Indigo UI color. | color | Constants | Exact adoption | clrIndigo | ui |
| clrMidnightBlue | Provides the predefined MidnightBlue UI color. | color | Constants | Exact adoption | clrMidnightBlue | ui |
| clrDarkBlue | Provides the predefined DarkBlue UI color. | color | Constants | Exact adoption | clrDarkBlue | ui |
| clrDarkOliveGreen | Provides the predefined DarkOliveGreen UI color. | color | Constants | Exact adoption | clrDarkOliveGreen | ui |
| clrSaddleBrown | Provides the predefined SaddleBrown UI color. | color | Constants | Exact adoption | clrSaddleBrown | ui |
| clrForestGreen | Provides the predefined ForestGreen UI color. | color | Constants | Exact adoption | clrForestGreen | ui |
| clrOliveDrab | Provides the predefined OliveDrab UI color. | color | Constants | Exact adoption | clrOliveDrab | ui |
| clrSeaGreen | Provides the predefined SeaGreen UI color. | color | Constants | Exact adoption | clrSeaGreen | ui |
| clrDarkGoldenrod | Provides the predefined DarkGoldenrod UI color. | color | Constants | Exact adoption | clrDarkGoldenrod | ui |
| clrDarkSlateBlue | Provides the predefined DarkSlateBlue UI color. | color | Constants | Exact adoption | clrDarkSlateBlue | ui |
| clrSienna | Provides the predefined Sienna UI color. | color | Constants | Exact adoption | clrSienna | ui |
| clrMediumBlue | Provides the predefined MediumBlue UI color. | color | Constants | Exact adoption | clrMediumBlue | ui |
| clrBrown | Provides the predefined Brown UI color. | color | Constants | Exact adoption | clrBrown | ui |
| clrDarkTurquoise | Provides the predefined DarkTurquoise UI color. | color | Constants | Exact adoption | clrDarkTurquoise | ui |
| clrDimGray | Provides the predefined DimGray UI color. | color | Constants | Exact adoption | clrDimGray | ui |
| clrLightSeaGreen | Provides the predefined LightSeaGreen UI color. | color | Constants | Exact adoption | clrLightSeaGreen | ui |
| clrDarkViolet | Provides the predefined DarkViolet UI color. | color | Constants | Exact adoption | clrDarkViolet | ui |
| clrFireBrick | Provides the predefined FireBrick UI color. | color | Constants | Exact adoption | clrFireBrick | ui |
| clrMediumVioletRed | Provides the predefined MediumVioletRed UI color. | color | Constants | Exact adoption | clrMediumVioletRed | ui |
| clrMediumSeaGreen | Provides the predefined MediumSeaGreen UI color. | color | Constants | Exact adoption | clrMediumSeaGreen | ui |
| clrChocolate | Provides the predefined Chocolate UI color. | color | Constants | Exact adoption | clrChocolate | ui |
| clrCrimson | Provides the predefined Crimson UI color. | color | Constants | Exact adoption | clrCrimson | ui |
| clrSteelBlue | Provides the predefined SteelBlue UI color. | color | Constants | Exact adoption | clrSteelBlue | ui |
| clrGoldenrod | Provides the predefined Goldenrod UI color. | color | Constants | Exact adoption | clrGoldenrod | ui |
| clrMediumSpringGreen | Provides the predefined MediumSpringGreen UI color. | color | Constants | Exact adoption | clrMediumSpringGreen | ui |
| clrLawnGreen | Provides the predefined LawnGreen UI color. | color | Constants | Exact adoption | clrLawnGreen | ui |
| clrCadetBlue | Provides the predefined CadetBlue UI color. | color | Constants | Exact adoption | clrCadetBlue | ui |
| clrDarkOrchid | Provides the predefined DarkOrchid UI color. | color | Constants | Exact adoption | clrDarkOrchid | ui |
| clrYellowGreen | Provides the predefined YellowGreen UI color. | color | Constants | Exact adoption | clrYellowGreen | ui |
| clrLimeGreen | Provides the predefined LimeGreen UI color. | color | Constants | Exact adoption | clrLimeGreen | ui |
| clrOrangeRed | Provides the predefined OrangeRed UI color. | color | Constants | Exact adoption | clrOrangeRed | ui |
| clrDarkOrange | Provides the predefined DarkOrange UI color. | color | Constants | Exact adoption | clrDarkOrange | ui |
| clrOrange | Provides the predefined Orange UI color. | color | Constants | Exact adoption | clrOrange | ui |
| clrGold | Provides the predefined Gold UI color. | color | Constants | Exact adoption | clrGold | ui |
| clrYellow | Provides the predefined Yellow UI color. | color | Constants | Exact adoption | clrYellow | ui |
| clrChartreuse | Provides the predefined Chartreuse UI color. | color | Constants | Exact adoption | clrChartreuse | ui |
| clrLime | Provides the predefined Lime UI color. | color | Constants | Exact adoption | clrLime | ui |
| clrSpringGreen | Provides the predefined SpringGreen UI color. | color | Constants | Exact adoption | clrSpringGreen | ui |
| clrAqua | Provides the predefined Aqua UI color. | color | Constants | Exact adoption | clrAqua | ui |
| clrDeepSkyBlue | Provides the predefined DeepSkyBlue UI color. | color | Constants | Exact adoption | clrDeepSkyBlue | ui |
| clrBlue | Provides the predefined Blue UI color. | color | Constants | Exact adoption | clrBlue | ui |
| clrMagenta | Provides the predefined Magenta UI color. | color | Constants | Exact adoption | clrMagenta | ui |
| clrRed | Provides the predefined Red UI color. | color | Constants | Exact adoption | clrRed | ui |
| clrGray | Provides the predefined Gray UI color. | color | Constants | Exact adoption | clrGray | ui |
| clrSlateGray | Provides the predefined SlateGray UI color. | color | Constants | Exact adoption | clrSlateGray | ui |
| clrPeru | Provides the predefined Peru UI color. | color | Constants | Exact adoption | clrPeru | ui |
| clrBlueViolet | Provides the predefined BlueViolet UI color. | color | Constants | Exact adoption | clrBlueViolet | ui |
| clrLightSlateGray | Provides the predefined LightSlateGray UI color. | color | Constants | Exact adoption | clrLightSlateGray | ui |
| clrDeepPink | Provides the predefined DeepPink UI color. | color | Constants | Exact adoption | clrDeepPink | ui |
| clrMediumTurquoise | Provides the predefined MediumTurquoise UI color. | color | Constants | Exact adoption | clrMediumTurquoise | ui |
| clrDodgerBlue | Provides the predefined DodgerBlue UI color. | color | Constants | Exact adoption | clrDodgerBlue | ui |
| clrTurquoise | Provides the predefined Turquoise UI color. | color | Constants | Exact adoption | clrTurquoise | ui |
| clrRoyalBlue | Provides the predefined RoyalBlue UI color. | color | Constants | Exact adoption | clrRoyalBlue | ui |
| clrSlateBlue | Provides the predefined SlateBlue UI color. | color | Constants | Exact adoption | clrSlateBlue | ui |
| clrDarkKhaki | Provides the predefined DarkKhaki UI color. | color | Constants | Exact adoption | clrDarkKhaki | ui |
| clrIndianRed | Provides the predefined IndianRed UI color. | color | Constants | Exact adoption | clrIndianRed | ui |
| clrMediumOrchid | Provides the predefined MediumOrchid UI color. | color | Constants | Exact adoption | clrMediumOrchid | ui |
| clrGreenYellow | Provides the predefined GreenYellow UI color. | color | Constants | Exact adoption | clrGreenYellow | ui |
| clrMediumAquamarine | Provides the predefined MediumAquamarine UI color. | color | Constants | Exact adoption | clrMediumAquamarine | ui |
| clrDarkSeaGreen | Provides the predefined DarkSeaGreen UI color. | color | Constants | Exact adoption | clrDarkSeaGreen | ui |
| clrTomato | Provides the predefined Tomato UI color. | color | Constants | Exact adoption | clrTomato | ui |
| clrRosyBrown | Provides the predefined RosyBrown UI color. | color | Constants | Exact adoption | clrRosyBrown | ui |
| clrOrchid | Provides the predefined Orchid UI color. | color | Constants | Exact adoption | clrOrchid | ui |
| clrMediumPurple | Provides the predefined MediumPurple UI color. | color | Constants | Exact adoption | clrMediumPurple | ui |
| clrPaleVioletRed | Provides the predefined PaleVioletRed UI color. | color | Constants | Exact adoption | clrPaleVioletRed | ui |
| clrCoral | Provides the predefined Coral UI color. | color | Constants | Exact adoption | clrCoral | ui |
| clrCornflowerBlue | Provides the predefined CornflowerBlue UI color. | color | Constants | Exact adoption | clrCornflowerBlue | ui |
| clrDarkGray | Provides the predefined DarkGray UI color. | color | Constants | Exact adoption | clrDarkGray | ui |
| clrSandyBrown | Provides the predefined SandyBrown UI color. | color | Constants | Exact adoption | clrSandyBrown | ui |
| clrMediumSlateBlue | Provides the predefined MediumSlateBlue UI color. | color | Constants | Exact adoption | clrMediumSlateBlue | ui |
| clrTan | Provides the predefined Tan UI color. | color | Constants | Exact adoption | clrTan | ui |
| clrDarkSalmon | Provides the predefined DarkSalmon UI color. | color | Constants | Exact adoption | clrDarkSalmon | ui |
| clrBurlyWood | Provides the predefined BurlyWood UI color. | color | Constants | Exact adoption | clrBurlyWood | ui |
| clrHotPink | Provides the predefined HotPink UI color. | color | Constants | Exact adoption | clrHotPink | ui |
| clrSalmon | Provides the predefined Salmon UI color. | color | Constants | Exact adoption | clrSalmon | ui |
| clrViolet | Provides the predefined Violet UI color. | color | Constants | Exact adoption | clrViolet | ui |
| clrLightCoral | Provides the predefined LightCoral UI color. | color | Constants | Exact adoption | clrLightCoral | ui |
| clrSkyBlue | Provides the predefined SkyBlue UI color. | color | Constants | Exact adoption | clrSkyBlue | ui |
| clrLightSalmon | Provides the predefined LightSalmon UI color. | color | Constants | Exact adoption | clrLightSalmon | ui |
| clrPlum | Provides the predefined Plum UI color. | color | Constants | Exact adoption | clrPlum | ui |
| clrKhaki | Provides the predefined Khaki UI color. | color | Constants | Exact adoption | clrKhaki | ui |
| clrLightGreen | Provides the predefined LightGreen UI color. | color | Constants | Exact adoption | clrLightGreen | ui |
| clrAquamarine | Provides the predefined Aquamarine UI color. | color | Constants | Exact adoption | clrAquamarine | ui |
| clrSilver | Provides the predefined Silver UI color. | color | Constants | Exact adoption | clrSilver | ui |
| clrLightSkyBlue | Provides the predefined LightSkyBlue UI color. | color | Constants | Exact adoption | clrLightSkyBlue | ui |
| clrLightSteelBlue | Provides the predefined LightSteelBlue UI color. | color | Constants | Exact adoption | clrLightSteelBlue | ui |
| clrLightBlue | Provides the predefined LightBlue UI color. | color | Constants | Exact adoption | clrLightBlue | ui |
| clrPaleGreen | Provides the predefined PaleGreen UI color. | color | Constants | Exact adoption | clrPaleGreen | ui |
| clrThistle | Provides the predefined Thistle UI color. | color | Constants | Exact adoption | clrThistle | ui |
| clrPowderBlue | Provides the predefined PowderBlue UI color. | color | Constants | Exact adoption | clrPowderBlue | ui |
| clrPaleGoldenrod | Provides the predefined PaleGoldenrod UI color. | color | Constants | Exact adoption | clrPaleGoldenrod | ui |
| clrPaleTurquoise | Provides the predefined PaleTurquoise UI color. | color | Constants | Exact adoption | clrPaleTurquoise | ui |
| clrLightGray | Provides the predefined LightGray UI color. | color | Constants | Exact adoption | clrLightGray | ui |
| clrWheat | Provides the predefined Wheat UI color. | color | Constants | Exact adoption | clrWheat | ui |
| clrNavajoWhite | Provides the predefined NavajoWhite UI color. | color | Constants | Exact adoption | clrNavajoWhite | ui |
| clrMoccasin | Provides the predefined Moccasin UI color. | color | Constants | Exact adoption | clrMoccasin | ui |
| clrLightPink | Provides the predefined LightPink UI color. | color | Constants | Exact adoption | clrLightPink | ui |
| clrGainsboro | Provides the predefined Gainsboro UI color. | color | Constants | Exact adoption | clrGainsboro | ui |
| clrPeachPuff | Provides the predefined PeachPuff UI color. | color | Constants | Exact adoption | clrPeachPuff | ui |
| clrPink | Provides the predefined Pink UI color. | color | Constants | Exact adoption | clrPink | ui |
| clrBisque | Provides the predefined Bisque UI color. | color | Constants | Exact adoption | clrBisque | ui |
| clrLightGoldenrod | Provides the predefined LightGoldenrod UI color. | color | Constants | Exact adoption | clrLightGoldenrod | ui |
| clrBlanchedAlmond | Provides the predefined BlanchedAlmond UI color. | color | Constants | Exact adoption | clrBlanchedAlmond | ui |
| clrLemonChiffon | Provides the predefined LemonChiffon UI color. | color | Constants | Exact adoption | clrLemonChiffon | ui |
| clrBeige | Provides the predefined Beige UI color. | color | Constants | Exact adoption | clrBeige | ui |
| clrAntiqueWhite | Provides the predefined AntiqueWhite UI color. | color | Constants | Exact adoption | clrAntiqueWhite | ui |
| clrPapayaWhip | Provides the predefined PapayaWhip UI color. | color | Constants | Exact adoption | clrPapayaWhip | ui |
| clrCornsilk | Provides the predefined Cornsilk UI color. | color | Constants | Exact adoption | clrCornsilk | ui |
| clrLightYellow | Provides the predefined LightYellow UI color. | color | Constants | Exact adoption | clrLightYellow | ui |
| clrLightCyan | Provides the predefined LightCyan UI color. | color | Constants | Exact adoption | clrLightCyan | ui |
| clrLinen | Provides the predefined Linen UI color. | color | Constants | Exact adoption | clrLinen | ui |
| clrLavender | Provides the predefined Lavender UI color. | color | Constants | Exact adoption | clrLavender | ui |
| clrMistyRose | Provides the predefined MistyRose UI color. | color | Constants | Exact adoption | clrMistyRose | ui |
| clrOldLace | Provides the predefined OldLace UI color. | color | Constants | Exact adoption | clrOldLace | ui |
| clrWhiteSmoke | Provides the predefined WhiteSmoke UI color. | color | Constants | Exact adoption | clrWhiteSmoke | ui |
| clrSeashell | Provides the predefined Seashell UI color. | color | Constants | Exact adoption | clrSeashell | ui |
| clrIvory | Provides the predefined Ivory UI color. | color | Constants | Exact adoption | clrIvory | ui |
| clrHoneydew | Provides the predefined Honeydew UI color. | color | Constants | Exact adoption | clrHoneydew | ui |
| clrAliceBlue | Provides the predefined AliceBlue UI color. | color | Constants | Exact adoption | clrAliceBlue | ui |
| clrLavenderBlush | Provides the predefined LavenderBlush UI color. | color | Constants | Exact adoption | clrLavenderBlush | ui |
| clrMintCream | Provides the predefined MintCream UI color. | color | Constants | Exact adoption | clrMintCream | ui |
| clrSnow | Provides the predefined Snow UI color. | color | Constants | Exact adoption | clrSnow | ui |
| clrWhite | Provides the predefined White UI color. | color | Constants | Exact adoption | clrWhite | ui |
| ENUM_APPLIED_PRICE | Defines the identifier set for applied price. | enum (int) | Enumerations | Exact adoption | ENUM_APPLIED_PRICE | indicator |
| ENUM_APPLIED_VOLUME | Defines the identifier set for applied volume. | enum (int) | Enumerations | Exact adoption | ENUM_APPLIED_VOLUME | indicator |
| ENUM_STO_PRICE | Defines the identifier set for sto price. | enum (int) | Enumerations | Exact adoption | ENUM_STO_PRICE | indicator |
| PRICE_CLOSE | Selects close in applied price. | ENUM_APPLIED_PRICE | Enumerations | Exact adoption | PRICE_CLOSE | indicator |
| PRICE_OPEN | Selects open in applied price. | ENUM_APPLIED_PRICE | Enumerations | Exact adoption | PRICE_OPEN | indicator |
| PRICE_HIGH | Selects high in applied price. | ENUM_APPLIED_PRICE | Enumerations | Exact adoption | PRICE_HIGH | indicator |
| PRICE_LOW | Selects low in applied price. | ENUM_APPLIED_PRICE | Enumerations | Exact adoption | PRICE_LOW | indicator |
| PRICE_MEDIAN | Selects median in applied price. | ENUM_APPLIED_PRICE | Enumerations | Exact adoption | PRICE_MEDIAN | indicator |
| PRICE_TYPICAL | Selects typical in applied price. | ENUM_APPLIED_PRICE | Enumerations | Exact adoption | PRICE_TYPICAL | indicator |
| PRICE_WEIGHTED | Selects weighted in applied price. | ENUM_APPLIED_PRICE | Enumerations | Exact adoption | PRICE_WEIGHTED | indicator |
| VOLUME_TICK | Selects tick in applied volume. | ENUM_APPLIED_VOLUME | Enumerations | Exact adoption | VOLUME_TICK | indicator |
| VOLUME_REAL | Selects real in applied volume. | ENUM_APPLIED_VOLUME | Enumerations | Exact adoption | VOLUME_REAL | indicator |
| STO_LOWHIGH | Selects sto lowhigh in sto price. | ENUM_STO_PRICE | Enumerations | Exact adoption | STO_LOWHIGH | indicator |
| STO_CLOSECLOSE | Selects sto closeclose in sto price. | ENUM_STO_PRICE | Enumerations | Exact adoption | STO_CLOSECLOSE | indicator |
| ENUM_MA_METHOD | Defines the identifier set for ma method. | enum (int) | Enumerations | Exact adoption | ENUM_MA_METHOD | indicator |
| MODE_SMA | Selects sma in ma method. | ENUM_MA_METHOD | Enumerations | Exact adoption | MODE_SMA | indicator |
| MODE_EMA | Selects ema in ma method. | ENUM_MA_METHOD | Enumerations | Exact adoption | MODE_EMA | indicator |
| MODE_SMMA | Selects smma in ma method. | ENUM_MA_METHOD | Enumerations | Exact adoption | MODE_SMMA | indicator |
| MODE_LWMA | Selects lwma in ma method. | ENUM_MA_METHOD | Enumerations | Exact adoption | MODE_LWMA | indicator |
| MAIN_LINE | Value: 0. Represents main line. | Not specified in reference | Constants | Exact adoption | MAIN_LINE | indicator |
| SIGNAL_LINE | Value: 1. Represents signal line. Rejected because it belongs to the MQL5 Signals marketplace. | Not specified in reference | Constants | Rejected adoption | — | — |
| PLUSDI_LINE | Value: 1. Represents plusdi line. | Not specified in reference | Constants | Exact adoption | PLUSDI_LINE | indicator |
| MINUSDI_LINE | Value: 2. Represents minusdi line. | Not specified in reference | Constants | Exact adoption | MINUSDI_LINE | indicator |
| BASE_LINE | Value: 0. Represents base line. | Not specified in reference | Constants | Exact adoption | BASE_LINE | indicator |
| UPPER_BAND | Value: 1. Represents upper band. | Not specified in reference | Constants | Exact adoption | UPPER_BAND | indicator |
| LOWER_BAND | Value: 2. Represents lower band. | Not specified in reference | Constants | Exact adoption | LOWER_BAND | indicator |
| UPPER_LINE | Value: 0. Represents upper line. | Not specified in reference | Constants | Exact adoption | UPPER_LINE | indicator |
| LOWER_LINE | Value: 1. Represents lower line. | Not specified in reference | Constants | Exact adoption | LOWER_LINE | indicator |
| UPPER_HISTOGRAM | Value: 0. Represents upper histogram. | Not specified in reference | Constants | Exact adoption | UPPER_HISTOGRAM | indicator |
| LOWER_HISTOGRAM | Value: 2. Represents lower histogram. | Not specified in reference | Constants | Exact adoption | LOWER_HISTOGRAM | indicator |
| GATORJAW_LINE | Value: 0. Represents gatorjaw line. | Not specified in reference | Constants | Exact adoption | GATORJAW_LINE | indicator |
| GATORTEETH_LINE | Value: 1. Represents gatorteeth line. | Not specified in reference | Constants | Exact adoption | GATORTEETH_LINE | indicator |
| GATORLIPS_LINE | Value: 2. Represents gatorlips line. | Not specified in reference | Constants | Exact adoption | GATORLIPS_LINE | indicator |
| TENKANSEN_LINE | Value: 0. Represents tenkansen line. | Not specified in reference | Constants | Exact adoption | TENKANSEN_LINE | indicator |
| KIJUNSEN_LINE | Value: 1. Represents kijunsen line. | Not specified in reference | Constants | Exact adoption | KIJUNSEN_LINE | indicator |
| SENKOUSPANA_LINE | Value: 2. Represents senkouspana line. | Not specified in reference | Constants | Exact adoption | SENKOUSPANA_LINE | indicator |
| SENKOUSPANB_LINE | Value: 3. Represents senkouspanb line. | Not specified in reference | Constants | Exact adoption | SENKOUSPANB_LINE | indicator |
| CHIKOUSPAN_LINE | Value: 4. Represents chikouspan line. | Not specified in reference | Constants | Exact adoption | CHIKOUSPAN_LINE | indicator |
| ENUM_DRAW_TYPE | Defines the identifier set for draw type. | enum (int) | Enumerations | Exact adoption | ENUM_DRAW_TYPE | indicator |
| DRAW_NONE | Selects none in draw type. | ENUM_DRAW_TYPE | Enumerations | Exact adoption | DRAW_NONE | indicator |
| DRAW_LINE | Selects line in draw type. | ENUM_DRAW_TYPE | Enumerations | Exact adoption | DRAW_LINE | indicator |
| DRAW_SECTION | Selects section in draw type. | ENUM_DRAW_TYPE | Enumerations | Exact adoption | DRAW_SECTION | indicator |
| DRAW_HISTOGRAM | Selects histogram in draw type. | ENUM_DRAW_TYPE | Enumerations | Exact adoption | DRAW_HISTOGRAM | indicator |
| DRAW_HISTOGRAM2 | Selects histogram2 in draw type. | ENUM_DRAW_TYPE | Enumerations | Exact adoption | DRAW_HISTOGRAM2 | indicator |
| DRAW_ARROW | Selects arrow in draw type. | ENUM_DRAW_TYPE | Enumerations | Exact adoption | DRAW_ARROW | indicator |
| DRAW_ZIGZAG | Selects zigzag in draw type. | ENUM_DRAW_TYPE | Enumerations | Exact adoption | DRAW_ZIGZAG | indicator |
| DRAW_FILLING | Selects filling in draw type. | ENUM_DRAW_TYPE | Enumerations | Exact adoption | DRAW_FILLING | indicator |
| DRAW_BARS | Selects bars in draw type. | ENUM_DRAW_TYPE | Enumerations | Exact adoption | DRAW_BARS | indicator |
| DRAW_CANDLES | Selects candles in draw type. | ENUM_DRAW_TYPE | Enumerations | Exact adoption | DRAW_CANDLES | indicator |
| DRAW_COLOR_LINE | Selects color line in draw type. | ENUM_DRAW_TYPE | Enumerations | Exact adoption | DRAW_COLOR_LINE | indicator |
| DRAW_COLOR_SECTION | Selects color section in draw type. | ENUM_DRAW_TYPE | Enumerations | Exact adoption | DRAW_COLOR_SECTION | indicator |
| DRAW_COLOR_HISTOGRAM | Selects color histogram in draw type. | ENUM_DRAW_TYPE | Enumerations | Exact adoption | DRAW_COLOR_HISTOGRAM | indicator |
| DRAW_COLOR_HISTOGRAM2 | Selects color histogram2 in draw type. | ENUM_DRAW_TYPE | Enumerations | Exact adoption | DRAW_COLOR_HISTOGRAM2 | indicator |
| DRAW_COLOR_ARROW | Selects color arrow in draw type. | ENUM_DRAW_TYPE | Enumerations | Exact adoption | DRAW_COLOR_ARROW | indicator |
| DRAW_COLOR_ZIGZAG | Selects color zigzag in draw type. | ENUM_DRAW_TYPE | Enumerations | Exact adoption | DRAW_COLOR_ZIGZAG | indicator |
| DRAW_COLOR_BARS | Selects color bars in draw type. | ENUM_DRAW_TYPE | Enumerations | Exact adoption | DRAW_COLOR_BARS | indicator |
| DRAW_COLOR_CANDLES | Selects color candles in draw type. | ENUM_DRAW_TYPE | Enumerations | Exact adoption | DRAW_COLOR_CANDLES | indicator |
| ENUM_PLOT_PROPERTY_INTEGER | Defines the identifier set for plot property integer. | enum (int) | Enumerations | Exact adoption | ENUM_PLOT_PROPERTY_INTEGER | indicator |
| ENUM_PLOT_PROPERTY_DOUBLE | Defines the identifier set for plot property double. | enum (int) | Enumerations | Exact adoption | ENUM_PLOT_PROPERTY_DOUBLE | indicator |
| PLOT_ARROW | Selects arrow in plot property integer. | uchar | Enumerations | Exact adoption | PLOT_ARROW | indicator |
| PLOT_ARROW_SHIFT | Selects arrow shift in plot property integer. | int | Enumerations | Exact adoption | PLOT_ARROW_SHIFT | indicator |
| PLOT_DRAW_BEGIN | Selects draw begin in plot property integer. | int | Enumerations | Exact adoption | PLOT_DRAW_BEGIN | indicator |
| PLOT_DRAW_TYPE | Selects draw type in plot property integer. | ENUM_DRAW_TYPE | Enumerations | Exact adoption | PLOT_DRAW_TYPE | indicator |
| PLOT_SHOW_DATA | Selects show data in plot property integer. | bool | Enumerations | Exact adoption | PLOT_SHOW_DATA | indicator |
| PLOT_SHIFT | Selects shift in plot property integer. | int | Enumerations | Exact adoption | PLOT_SHIFT | indicator |
| PLOT_LINE_STYLE | Selects line style in plot property integer. | ENUM_LINE_STYLE | Enumerations | Exact adoption | PLOT_LINE_STYLE | indicator |
| PLOT_LINE_WIDTH | Selects line width in plot property integer. | int | Enumerations | Exact adoption | PLOT_LINE_WIDTH | indicator |
| PLOT_COLOR_INDEXES | Selects color indexes in plot property integer. | int | Enumerations | Exact adoption | PLOT_COLOR_INDEXES | indicator |
| PLOT_LINE_COLOR | Selects line color in plot property integer. | color modifier = index number of colors | Enumerations | Exact adoption | PLOT_LINE_COLOR | indicator |
| PLOT_EMPTY_VALUE | Selects empty value in plot property double. | double | Enumerations | Exact adoption | PLOT_EMPTY_VALUE | indicator |
| ENUM_PLOT_PROPERTY_STRING | Defines the identifier set for plot property string. | enum (int) | Enumerations | Exact adoption | ENUM_PLOT_PROPERTY_STRING | indicator |
| ENUM_LINE_STYLE | Defines the identifier set for line style. | enum (int) | Enumerations | Exact adoption | ENUM_LINE_STYLE | indicator |
| PLOT_LABEL | Selects label in plot property string. | string | Enumerations | Exact adoption | PLOT_LABEL | indicator |
| STYLE_SOLID | Selects style solid in line style. | ENUM_LINE_STYLE | Enumerations | Exact adoption | STYLE_SOLID | indicator |
| STYLE_DASH | Selects style dash in line style. | ENUM_LINE_STYLE | Enumerations | Exact adoption | STYLE_DASH | indicator |
| STYLE_DOT | Selects style dot in line style. | ENUM_LINE_STYLE | Enumerations | Exact adoption | STYLE_DOT | indicator |
| STYLE_DASHDOT | Selects style dashdot in line style. | ENUM_LINE_STYLE | Enumerations | Exact adoption | STYLE_DASHDOT | indicator |
| STYLE_DASHDOTDOT | Selects style dashdotdot in line style. | ENUM_LINE_STYLE | Enumerations | Exact adoption | STYLE_DASHDOTDOT | indicator |
| ENUM_INDEXBUFFER_TYPE | Defines the identifier set for indexbuffer type. | enum (int) | Enumerations | Exact adoption | ENUM_INDEXBUFFER_TYPE | indicator |
| ENUM_CUSTOMIND_PROPERTY_INTEGER | Defines the identifier set for customind property integer. | enum (int) | Enumerations | Exact adoption | ENUM_CUSTOMIND_PROPERTY_INTEGER | indicator |
| INDICATOR_DATA | Selects data in indexbuffer type. | ENUM_INDEXBUFFER_TYPE | Enumerations | Exact adoption | INDICATOR_DATA | indicator |
| INDICATOR_COLOR_INDEX | Selects color index in indexbuffer type. | ENUM_INDEXBUFFER_TYPE | Enumerations | Exact adoption | INDICATOR_COLOR_INDEX | indicator |
| INDICATOR_CALCULATIONS | Selects calculations in indexbuffer type. | ENUM_INDEXBUFFER_TYPE | Enumerations | Exact adoption | INDICATOR_CALCULATIONS | indicator |
| INDICATOR_DIGITS | Selects digits in customind property integer. | int | Enumerations | Exact adoption | INDICATOR_DIGITS | indicator |
| INDICATOR_HEIGHT | Selects height in customind property integer. | int | Enumerations | Exact adoption | INDICATOR_HEIGHT | indicator |
| INDICATOR_LEVELS | Selects levels in customind property integer. | int | Enumerations | Exact adoption | INDICATOR_LEVELS | indicator |
| INDICATOR_LEVELCOLOR | Selects levelcolor in customind property integer. | color modifier = level number | Enumerations | Exact adoption | INDICATOR_LEVELCOLOR | indicator |
| INDICATOR_LEVELSTYLE | Selects levelstyle in customind property integer. | ENUM_LINE_STYLE modifier = level number | Enumerations | Exact adoption | INDICATOR_LEVELSTYLE | indicator |
| INDICATOR_LEVELWIDTH | Selects levelwidth in customind property integer. | int modifier = level number | Enumerations | Exact adoption | INDICATOR_LEVELWIDTH | indicator |
| INDICATOR_FIXED_MINIMUM | Selects fixed minimum in customind property integer. | bool | Enumerations | Exact adoption | INDICATOR_FIXED_MINIMUM | indicator |
| INDICATOR_FIXED_MAXIMUM | Selects fixed maximum in customind property integer. | bool | Enumerations | Exact adoption | INDICATOR_FIXED_MAXIMUM | indicator |
| ENUM_CUSTOMIND_PROPERTY_DOUBLE | Defines the identifier set for customind property double. | enum (int) | Enumerations | Exact adoption | ENUM_CUSTOMIND_PROPERTY_DOUBLE | indicator |
| INDICATOR_MINIMUM | Selects minimum in customind property double. | double | Enumerations | Exact adoption | INDICATOR_MINIMUM | indicator |
| INDICATOR_MAXIMUM | Selects maximum in customind property double. | double | Enumerations | Exact adoption | INDICATOR_MAXIMUM | indicator |
| INDICATOR_LEVELVALUE | Selects levelvalue in customind property double. | double modifier = level number | Enumerations | Exact adoption | INDICATOR_LEVELVALUE | indicator |
| ENUM_CUSTOMIND_PROPERTY_STRING | Defines the identifier set for customind property string. | enum (int) | Enumerations | Exact adoption | ENUM_CUSTOMIND_PROPERTY_STRING | indicator |
| INDICATOR_SHORTNAME | Selects shortname in customind property string. | string | Enumerations | Exact adoption | INDICATOR_SHORTNAME | indicator |
| INDICATOR_LEVELTEXT | Selects leveltext in customind property string. | string modifier = level number | Enumerations | Exact adoption | INDICATOR_LEVELTEXT | indicator |
| ENUM_INDICATOR | Defines the identifier set for indicator. | enum (int) | Enumerations | Exact adoption | ENUM_INDICATOR | indicator |
| IND_AC | Selects ac in indicator. | ENUM_INDICATOR | Enumerations | Exact adoption | IND_AC | indicator |
| IND_AD | Selects ad in indicator. | ENUM_INDICATOR | Enumerations | Exact adoption | IND_AD | indicator |
| IND_ADX | Selects adx in indicator. | ENUM_INDICATOR | Enumerations | Exact adoption | IND_ADX | indicator |
| IND_ADXW | Selects adxw in indicator. | ENUM_INDICATOR | Enumerations | Exact adoption | IND_ADXW | indicator |
| IND_ALLIGATOR | Selects alligator in indicator. | ENUM_INDICATOR | Enumerations | Exact adoption | IND_ALLIGATOR | indicator |
| IND_AMA | Selects ama in indicator. | ENUM_INDICATOR | Enumerations | Exact adoption | IND_AMA | indicator |
| IND_AO | Selects ao in indicator. | ENUM_INDICATOR | Enumerations | Exact adoption | IND_AO | indicator |
| IND_ATR | Selects atr in indicator. | ENUM_INDICATOR | Enumerations | Exact adoption | IND_ATR | indicator |
| IND_BANDS | Selects bands in indicator. | ENUM_INDICATOR | Enumerations | Exact adoption | IND_BANDS | indicator |
| IND_BEARS | Selects bears in indicator. | ENUM_INDICATOR | Enumerations | Exact adoption | IND_BEARS | indicator |
| IND_BULLS | Selects bulls in indicator. | ENUM_INDICATOR | Enumerations | Exact adoption | IND_BULLS | indicator |
| IND_BWMFI | Selects bwmfi in indicator. | ENUM_INDICATOR | Enumerations | Exact adoption | IND_BWMFI | indicator |
| IND_CCI | Selects cci in indicator. | ENUM_INDICATOR | Enumerations | Exact adoption | IND_CCI | indicator |
| IND_CHAIKIN | Selects chaikin in indicator. | ENUM_INDICATOR | Enumerations | Exact adoption | IND_CHAIKIN | indicator |
| IND_CUSTOM | Selects custom in indicator. | ENUM_INDICATOR | Enumerations | Exact adoption | IND_CUSTOM | indicator |
| IND_DEMA | Selects dema in indicator. | ENUM_INDICATOR | Enumerations | Exact adoption | IND_DEMA | indicator |
| IND_DEMARKER | Selects demarker in indicator. | ENUM_INDICATOR | Enumerations | Exact adoption | IND_DEMARKER | indicator |
| IND_ENVELOPES | Selects envelopes in indicator. | ENUM_INDICATOR | Enumerations | Exact adoption | IND_ENVELOPES | indicator |
| IND_FORCE | Selects force in indicator. | ENUM_INDICATOR | Enumerations | Exact adoption | IND_FORCE | indicator |
| IND_FRACTALS | Selects fractals in indicator. | ENUM_INDICATOR | Enumerations | Exact adoption | IND_FRACTALS | indicator |
| IND_FRAMA | Selects frama in indicator. | ENUM_INDICATOR | Enumerations | Exact adoption | IND_FRAMA | indicator |
| IND_GATOR | Selects gator in indicator. | ENUM_INDICATOR | Enumerations | Exact adoption | IND_GATOR | indicator |
| IND_ICHIMOKU | Selects ichimoku in indicator. | ENUM_INDICATOR | Enumerations | Exact adoption | IND_ICHIMOKU | indicator |
| IND_MA | Selects ma in indicator. | ENUM_INDICATOR | Enumerations | Exact adoption | IND_MA | indicator |
| IND_MACD | Selects macd in indicator. | ENUM_INDICATOR | Enumerations | Exact adoption | IND_MACD | indicator |
| IND_MFI | Selects mfi in indicator. | ENUM_INDICATOR | Enumerations | Exact adoption | IND_MFI | indicator |
| IND_MOMENTUM | Selects momentum in indicator. | ENUM_INDICATOR | Enumerations | Exact adoption | IND_MOMENTUM | indicator |
| IND_OBV | Selects obv in indicator. | ENUM_INDICATOR | Enumerations | Exact adoption | IND_OBV | indicator |
| IND_OSMA | Selects osma in indicator. | ENUM_INDICATOR | Enumerations | Exact adoption | IND_OSMA | indicator |
| IND_RSI | Selects rsi in indicator. | ENUM_INDICATOR | Enumerations | Exact adoption | IND_RSI | indicator |
| IND_RVI | Selects rvi in indicator. | ENUM_INDICATOR | Enumerations | Exact adoption | IND_RVI | indicator |
| IND_SAR | Selects sar in indicator. | ENUM_INDICATOR | Enumerations | Exact adoption | IND_SAR | indicator |
| IND_STDDEV | Selects stddev in indicator. | ENUM_INDICATOR | Enumerations | Exact adoption | IND_STDDEV | indicator |
| IND_STOCHASTIC | Selects stochastic in indicator. | ENUM_INDICATOR | Enumerations | Exact adoption | IND_STOCHASTIC | indicator |
| IND_TEMA | Selects tema in indicator. | ENUM_INDICATOR | Enumerations | Exact adoption | IND_TEMA | indicator |
| IND_TRIX | Selects trix in indicator. | ENUM_INDICATOR | Enumerations | Exact adoption | IND_TRIX | indicator |
| IND_VIDYA | Selects vidya in indicator. | ENUM_INDICATOR | Enumerations | Exact adoption | IND_VIDYA | indicator |
| IND_VOLUMES | Selects volumes in indicator. | ENUM_INDICATOR | Enumerations | Exact adoption | IND_VOLUMES | indicator |
| IND_WPR | Selects wpr in indicator. | ENUM_INDICATOR | Enumerations | Exact adoption | IND_WPR | indicator |
| ENUM_DATATYPE | Defines the identifier set for datatype. | enum (int) | Enumerations | Exact adoption | ENUM_DATATYPE | indicator |
| TYPE_BOOL | Selects type bool in datatype. | bool | Enumerations | Exact adoption | TYPE_BOOL | indicator |
| TYPE_CHAR | Selects type char in datatype. | char | Enumerations | Exact adoption | TYPE_CHAR | indicator |
| TYPE_UCHAR | Selects type uchar in datatype. | uchar | Enumerations | Exact adoption | TYPE_UCHAR | indicator |
| TYPE_SHORT | Selects type short in datatype. | short | Enumerations | Exact adoption | TYPE_SHORT | indicator |
| TYPE_USHORT | Selects type ushort in datatype. | ushort | Enumerations | Exact adoption | TYPE_USHORT | indicator |
| TYPE_COLOR | Selects type color in datatype. | color | Enumerations | Exact adoption | TYPE_COLOR | indicator |
| TYPE_INT | Selects type int in datatype. | int | Enumerations | Exact adoption | TYPE_INT | indicator |
| TYPE_UINT | Selects type uint in datatype. | uint | Enumerations | Exact adoption | TYPE_UINT | indicator |
| TYPE_DATETIME | Selects type datetime in datatype. | datetime | Enumerations | Exact adoption | TYPE_DATETIME | indicator |
| TYPE_LONG | Selects type long in datatype. | long | Enumerations | Exact adoption | TYPE_LONG | indicator |
| TYPE_ULONG | Selects type ulong in datatype. | ulong | Enumerations | Exact adoption | TYPE_ULONG | indicator |
| TYPE_FLOAT | Selects type float in datatype. | float | Enumerations | Exact adoption | TYPE_FLOAT | indicator |
| TYPE_DOUBLE | Selects type double in datatype. | double | Enumerations | Exact adoption | TYPE_DOUBLE | indicator |
| TYPE_STRING | Selects type string in datatype. | string | Enumerations | Exact adoption | TYPE_STRING | indicator |
| ENUM_TERMINAL_INFO_INTEGER | Defines the identifier set for terminal info integer. | enum (int) | Enumerations | Platform-neutral rename | ENUM_RUNTIME_INFO_INTEGER | workspace |
| TERMINAL_BUILD | Selects build in terminal info integer. | int | Enumerations | Platform-neutral rename | RUNTIME_BUILD | workspace |
| TERMINAL_COMMUNITY_ACCOUNT | Selects community account in terminal info integer. Rejected because it is tied to MetaTrader-hosted terminal services. | bool | Enumerations | Rejected adoption | — | — |
| TERMINAL_COMMUNITY_CONNECTION | Selects community connection in terminal info integer. Rejected because it is tied to MetaTrader-hosted terminal services. | bool | Enumerations | Rejected adoption | — | — |
| TERMINAL_CONNECTED | Selects connected in terminal info integer. | bool | Enumerations | Platform-neutral rename | RUNTIME_CONNECTED | workspace |
| TERMINAL_DLLS_ALLOWED | Selects dlls allowed in terminal info integer. | bool | Enumerations | Platform-neutral rename | RUNTIME_DLLS_ALLOWED | workspace |
| TERMINAL_TRADE_ALLOWED | Selects trade allowed in terminal info integer. | bool | Enumerations | Platform-neutral rename | RUNTIME_TRADE_ALLOWED | workspace |
| TERMINAL_EMAIL_ENABLED | Selects email enabled in terminal info integer. | bool | Enumerations | Platform-neutral rename | RUNTIME_EMAIL_ENABLED | workspace |
| TERMINAL_FTP_ENABLED | Selects FTP enabled in terminal info integer. Rejected because it is tied to MetaTrader-hosted terminal services. | bool | Enumerations | Rejected adoption | — | — |
| TERMINAL_NOTIFICATIONS_ENABLED | Selects notifications enabled in terminal info integer. | bool | Enumerations | Platform-neutral rename | RUNTIME_NOTIFICATIONS_ENABLED | workspace |
| TERMINAL_MAXBARS | Selects maxbars in terminal info integer. | int | Enumerations | Platform-neutral rename | RUNTIME_MAXBARS | workspace |
| TERMINAL_MQID | Selects mqid in terminal info integer. Rejected because it is tied to MetaTrader-hosted terminal services. | bool | Enumerations | Rejected adoption | — | — |
| TERMINAL_CODEPAGE | Selects codepage in terminal info integer. | int | Enumerations | Platform-neutral rename | RUNTIME_CODEPAGE | workspace |
| TERMINAL_CPU_CORES | Selects CPU cores in terminal info integer. | int | Enumerations | Platform-neutral rename | RUNTIME_CPU_CORES | workspace |
| TERMINAL_DISK_SPACE | Selects disk space in terminal info integer. | int | Enumerations | Platform-neutral rename | RUNTIME_DISK_SPACE | workspace |
| TERMINAL_MEMORY_PHYSICAL | Selects memory physical in terminal info integer. | int | Enumerations | Platform-neutral rename | RUNTIME_MEMORY_PHYSICAL | workspace |
| TERMINAL_MEMORY_TOTAL | Selects memory total in terminal info integer. | int | Enumerations | Platform-neutral rename | RUNTIME_MEMORY_TOTAL | workspace |
| TERMINAL_MEMORY_AVAILABLE | Selects memory available in terminal info integer. | int | Enumerations | Platform-neutral rename | RUNTIME_MEMORY_AVAILABLE | workspace |
| TERMINAL_MEMORY_USED | Selects memory used in terminal info integer. | int | Enumerations | Platform-neutral rename | RUNTIME_MEMORY_USED | workspace |
| TERMINAL_X64 | Selects x64 in terminal info integer. | bool | Enumerations | Platform-neutral rename | RUNTIME_X64 | workspace |
| TERMINAL_OPENCL_SUPPORT | Selects opencl support in terminal info integer. | int | Enumerations | Platform-neutral rename | RUNTIME_OPENCL_SUPPORT | workspace |
| TERMINAL_SCREEN_DPI | Selects screen dpi in terminal info integer. | int | Enumerations | Platform-neutral rename | RUNTIME_SCREEN_DPI | workspace |
| TERMINAL_SCREEN_LEFT | Selects screen left in terminal info integer. | int | Enumerations | Platform-neutral rename | RUNTIME_SCREEN_LEFT | workspace |
| TERMINAL_SCREEN_TOP | Selects screen top in terminal info integer. | int | Enumerations | Platform-neutral rename | RUNTIME_SCREEN_TOP | workspace |
| TERMINAL_SCREEN_WIDTH | Selects screen width in terminal info integer. | int | Enumerations | Platform-neutral rename | RUNTIME_SCREEN_WIDTH | workspace |
| TERMINAL_SCREEN_HEIGHT | Selects screen height in terminal info integer. | int | Enumerations | Platform-neutral rename | RUNTIME_SCREEN_HEIGHT | workspace |
| TERMINAL_LEFT | Selects left in terminal info integer. | int | Enumerations | Platform-neutral rename | RUNTIME_LEFT | workspace |
| TERMINAL_TOP | Selects top in terminal info integer. | int | Enumerations | Platform-neutral rename | RUNTIME_TOP | workspace |
| TERMINAL_RIGHT | Selects right in terminal info integer. | int | Enumerations | Platform-neutral rename | RUNTIME_RIGHT | workspace |
| TERMINAL_BOTTOM | Selects bottom in terminal info integer. | int | Enumerations | Platform-neutral rename | RUNTIME_BOTTOM | workspace |
| TERMINAL_PING_LAST | Selects ping last in terminal info integer. | int | Enumerations | Platform-neutral rename | RUNTIME_PING_LAST | workspace |
| TERMINAL_VPS | Selects VPS in terminal info integer. | bool | Enumerations | Platform-neutral rename | RUNTIME_VPS | workspace |
| TERMINAL_KEYSTATE_LEFT | Selects keystate left in terminal info integer. | int | Enumerations | Platform-neutral rename | RUNTIME_KEYSTATE_LEFT | workspace |
| TERMINAL_KEYSTATE_UP | Selects keystate up in terminal info integer. | int | Enumerations | Platform-neutral rename | RUNTIME_KEYSTATE_UP | workspace |
| TERMINAL_KEYSTATE_RIGHT | Selects keystate right in terminal info integer. | int | Enumerations | Platform-neutral rename | RUNTIME_KEYSTATE_RIGHT | workspace |
| TERMINAL_KEYSTATE_DOWN | Selects keystate down in terminal info integer. | int | Enumerations | Platform-neutral rename | RUNTIME_KEYSTATE_DOWN | workspace |
| TERMINAL_KEYSTATE_SHIFT | Selects keystate shift in terminal info integer. | int | Enumerations | Platform-neutral rename | RUNTIME_KEYSTATE_SHIFT | workspace |
| TERMINAL_KEYSTATE_CONTROL | Selects keystate control in terminal info integer. | int | Enumerations | Platform-neutral rename | RUNTIME_KEYSTATE_CONTROL | workspace |
| TERMINAL_KEYSTATE_MENU | Selects keystate menu in terminal info integer. | int | Enumerations | Platform-neutral rename | RUNTIME_KEYSTATE_MENU | workspace |
| TERMINAL_KEYSTATE_CAPSLOCK | Selects keystate capslock in terminal info integer. | int | Enumerations | Platform-neutral rename | RUNTIME_KEYSTATE_CAPSLOCK | workspace |
| TERMINAL_KEYSTATE_NUMLOCK | Selects keystate numlock in terminal info integer. | int | Enumerations | Platform-neutral rename | RUNTIME_KEYSTATE_NUMLOCK | workspace |
| TERMINAL_KEYSTATE_SCRLOCK | Selects keystate scrlock in terminal info integer. | int | Enumerations | Platform-neutral rename | RUNTIME_KEYSTATE_SCRLOCK | workspace |
| TERMINAL_KEYSTATE_ENTER | Selects keystate enter in terminal info integer. | int | Enumerations | Platform-neutral rename | RUNTIME_KEYSTATE_ENTER | workspace |
| TERMINAL_KEYSTATE_INSERT | Selects keystate insert in terminal info integer. | int | Enumerations | Platform-neutral rename | RUNTIME_KEYSTATE_INSERT | workspace |
| TERMINAL_KEYSTATE_DELETE | Selects keystate delete in terminal info integer. | int | Enumerations | Platform-neutral rename | RUNTIME_KEYSTATE_DELETE | workspace |
| TERMINAL_KEYSTATE_HOME | Selects keystate home in terminal info integer. | int | Enumerations | Platform-neutral rename | RUNTIME_KEYSTATE_HOME | workspace |
| TERMINAL_KEYSTATE_END | Selects keystate end in terminal info integer. | int | Enumerations | Platform-neutral rename | RUNTIME_KEYSTATE_END | workspace |
| TERMINAL_KEYSTATE_TAB | Selects keystate tab in terminal info integer. | int | Enumerations | Platform-neutral rename | RUNTIME_KEYSTATE_TAB | workspace |
| TERMINAL_KEYSTATE_PAGEUP | Selects keystate pageup in terminal info integer. | int | Enumerations | Platform-neutral rename | RUNTIME_KEYSTATE_PAGEUP | workspace |
| TERMINAL_KEYSTATE_PAGEDOWN | Selects keystate pagedown in terminal info integer. | int | Enumerations | Platform-neutral rename | RUNTIME_KEYSTATE_PAGEDOWN | workspace |
| TERMINAL_KEYSTATE_ESCAPE | Selects keystate escape in terminal info integer. | int | Enumerations | Platform-neutral rename | RUNTIME_KEYSTATE_ESCAPE | workspace |
| ENUM_TERMINAL_INFO_DOUBLE | Defines the identifier set for terminal info double. | enum (int) | Enumerations | Platform-neutral rename | ENUM_RUNTIME_INFO_DOUBLE | workspace |
| ENUM_TERMINAL_INFO_STRING | Defines the identifier set for terminal info string. | enum (int) | Enumerations | Platform-neutral rename | ENUM_RUNTIME_INFO_STRING | workspace |
| TERMINAL_COMMUNITY_BALANCE | Selects community balance in terminal info double. Rejected because it is tied to MetaTrader-hosted terminal services. | double | Enumerations | Rejected adoption | — | — |
| TERMINAL_RETRANSMISSION | Selects retransmission in terminal info double. | double | Enumerations | Platform-neutral rename | RUNTIME_RETRANSMISSION | workspace |
| TERMINAL_LANGUAGE | Selects language in terminal info string. | string | Enumerations | Platform-neutral rename | RUNTIME_LANGUAGE | workspace |
| TERMINAL_COMPANY | Selects company in terminal info string. | string | Enumerations | Platform-neutral rename | RUNTIME_COMPANY | workspace |
| TERMINAL_NAME | Selects name in terminal info string. | string | Enumerations | Platform-neutral rename | RUNTIME_NAME | workspace |
| TERMINAL_PATH | Selects path in terminal info string. | string | Enumerations | Platform-neutral rename | RUNTIME_PATH | workspace |
| TERMINAL_DATA_PATH | Selects data path in terminal info string. | string | Enumerations | Platform-neutral rename | RUNTIME_DATA_PATH | workspace |
| TERMINAL_COMMONDATA_PATH | Selects commondata path in terminal info string. | string | Enumerations | Platform-neutral rename | RUNTIME_COMMONDATA_PATH | workspace |
| TERMINAL_CPU_NAME | Selects CPU name in terminal info string. | string | Enumerations | Platform-neutral rename | RUNTIME_CPU_NAME | workspace |
| TERMINAL_CPU_ARCHITECTURE | Selects CPU architecture in terminal info string. | string | Enumerations | Platform-neutral rename | RUNTIME_CPU_ARCHITECTURE | workspace |
| TERMINAL_OS_VERSION | Selects os version in terminal info string. | string | Enumerations | Platform-neutral rename | RUNTIME_OS_VERSION | workspace |
| TERMINAL_COLORTHEME_NAME | Selects colortheme name in terminal info string. | string | Enumerations | Platform-neutral rename | RUNTIME_COLORTHEME_NAME | workspace |
| THEME_COLOR_WINDOW | Selects window in terminal info integer. | color | Enumerations | Exact adoption | THEME_COLOR_WINDOW | ui |
| THEME_COLOR_WINDOWTEXT | Selects windowtext in terminal info integer. | color | Enumerations | Exact adoption | THEME_COLOR_WINDOWTEXT | ui |
| THEME_COLOR_BTNTEXT | Selects btntext in terminal info integer. | color | Enumerations | Exact adoption | THEME_COLOR_BTNTEXT | ui |
| THEME_COLOR_GRAYTEXT | Selects graytext in terminal info integer. | color | Enumerations | Exact adoption | THEME_COLOR_GRAYTEXT | ui |
| THEME_COLOR_INFOTEXT | Selects infotext in terminal info integer. | color | Enumerations | Exact adoption | THEME_COLOR_INFOTEXT | ui |
| THEME_COLOR_INFOBK | Selects infobk in terminal info integer. | color | Enumerations | Exact adoption | THEME_COLOR_INFOBK | ui |
| THEME_COLOR_3DFACE | Selects 3 dface in terminal info integer. | color | Enumerations | Exact adoption | THEME_COLOR_3DFACE | ui |
| THEME_COLOR_3DLIGHT | Selects 3 dlight in terminal info integer. | color | Enumerations | Exact adoption | THEME_COLOR_3DLIGHT | ui |
| THEME_COLOR_3DSHADOW | Selects 3 dshadow in terminal info integer. | color | Enumerations | Exact adoption | THEME_COLOR_3DSHADOW | ui |
| THEME_COLOR_3DDKSHADOW | Selects 3 ddkshadow in terminal info integer. | color | Enumerations | Exact adoption | THEME_COLOR_3DDKSHADOW | ui |
| THEME_COLOR_3DHILIGHT | Selects 3 dhilight in terminal info integer. | color | Enumerations | Exact adoption | THEME_COLOR_3DHILIGHT | ui |
| THEME_COLOR_HIGHLIGHT | Selects highlight in terminal info integer. | color | Enumerations | Exact adoption | THEME_COLOR_HIGHLIGHT | ui |
| THEME_COLOR_HIGHLIGHTTEXT | Selects highlighttext in terminal info integer. | color | Enumerations | Exact adoption | THEME_COLOR_HIGHLIGHTTEXT | ui |
| THEME_COLOR_BTNFACE | Selects btnface in terminal info integer. | color | Enumerations | Exact adoption | THEME_COLOR_BTNFACE | ui |
| THEME_COLOR_BTNHILIGHT | Selects btnhilight in terminal info integer. | color | Enumerations | Exact adoption | THEME_COLOR_BTNHILIGHT | ui |
| THEME_COLOR_BTNSHADOW | Selects btnshadow in terminal info integer. | color | Enumerations | Exact adoption | THEME_COLOR_BTNSHADOW | ui |
| THEME_COLOR_MENU | Selects menu in terminal info integer. | color | Enumerations | Exact adoption | THEME_COLOR_MENU | ui |
| THEME_COLOR_MENUBAR | Selects menubar in terminal info integer. | color | Enumerations | Exact adoption | THEME_COLOR_MENUBAR | ui |
| THEME_COLOR_MENUTEXT | Selects menutext in terminal info integer. | color | Enumerations | Exact adoption | THEME_COLOR_MENUTEXT | ui |
| THEME_COLOR_MENUHILIGHT | Selects menuhilight in terminal info integer. | color | Enumerations | Exact adoption | THEME_COLOR_MENUHILIGHT | ui |
| THEME_COLOR_ACTIVECAPTION | Selects activecaption in terminal info integer. | color | Enumerations | Exact adoption | THEME_COLOR_ACTIVECAPTION | ui |
| THEME_COLOR_INACTIVECAPTION | Selects inactivecaption in terminal info integer. | color | Enumerations | Exact adoption | THEME_COLOR_INACTIVECAPTION | ui |
| THEME_COLOR_GRADIENTINACTIVECAPTION | Selects gradientinactivecaption in terminal info integer. | color | Enumerations | Exact adoption | THEME_COLOR_GRADIENTINACTIVECAPTION | ui |
| THEME_COLOR_CAPTIONTEXT | Selects captiontext in terminal info integer. | color | Enumerations | Exact adoption | THEME_COLOR_CAPTIONTEXT | ui |
| THEME_COLOR_INACTIVECAPTIONTEXT | Selects inactivecaptiontext in terminal info integer. | color | Enumerations | Exact adoption | THEME_COLOR_INACTIVECAPTIONTEXT | ui |
| THEME_COLOR_HOTTEXT | Selects hottext in terminal info integer. | color | Enumerations | Exact adoption | THEME_COLOR_HOTTEXT | ui |
| THEME_COLOR_NONE | Selects none in terminal info integer. | color | Enumerations | Exact adoption | THEME_COLOR_NONE | ui |
| THEME_COLOR_SEPARATOR | Selects separator in terminal info integer. | color | Enumerations | Exact adoption | THEME_COLOR_SEPARATOR | ui |
| THEME_COLOR_SCROLLBACK | Selects scrollback in terminal info integer. | color | Enumerations | Exact adoption | THEME_COLOR_SCROLLBACK | ui |
| THEME_COLOR_LINE1 | Selects line1 in terminal info integer. | color | Enumerations | Exact adoption | THEME_COLOR_LINE1 | ui |
| THEME_COLOR_LINE2 | Selects line2 in terminal info integer. | color | Enumerations | Exact adoption | THEME_COLOR_LINE2 | ui |
| THEME_COLOR_GRID | Selects grid in terminal info integer. | color | Enumerations | Exact adoption | THEME_COLOR_GRID | ui |
| THEME_COLOR_SUMMARY | Selects summary in terminal info integer. | color | Enumerations | Exact adoption | THEME_COLOR_SUMMARY | ui |
| THEME_COLOR_ERROR | Selects error in terminal info integer. | color | Enumerations | Exact adoption | THEME_COLOR_ERROR | ui |
| THEME_COLOR_INVALID | Selects invalid in terminal info integer. | color | Enumerations | Exact adoption | THEME_COLOR_INVALID | ui |
| THEME_COLOR_NEGATIVE | Selects negative in terminal info integer. | color | Enumerations | Exact adoption | THEME_COLOR_NEGATIVE | ui |
| THEME_COLOR_POSITIVE | Selects positive in terminal info integer. | color | Enumerations | Exact adoption | THEME_COLOR_POSITIVE | ui |
| THEME_COLOR_LINK | Selects link in terminal info integer. | color | Enumerations | Exact adoption | THEME_COLOR_LINK | ui |
| THEME_COLOR_LINKHOVER | Selects linkhover in terminal info integer. | color | Enumerations | Exact adoption | THEME_COLOR_LINKHOVER | ui |
| THEME_COLOR_LINKTESTER | Selects linktester in terminal info integer. | color | Enumerations | Exact adoption | THEME_COLOR_LINKTESTER | ui |
| THEME_COLOR_TEXTUP | Selects textup in terminal info integer. | color | Enumerations | Exact adoption | THEME_COLOR_TEXTUP | ui |
| THEME_COLOR_TEXTDOWN | Selects textdown in terminal info integer. | color | Enumerations | Exact adoption | THEME_COLOR_TEXTDOWN | ui |
| THEME_COLOR_BACKUP | Selects backup in terminal info integer. | color | Enumerations | Exact adoption | THEME_COLOR_BACKUP | ui |
| THEME_COLOR_BACKDOWN | Selects backdown in terminal info integer. | color | Enumerations | Exact adoption | THEME_COLOR_BACKDOWN | ui |
| THEME_COLOR_CLOSE | Selects close in terminal info integer. | color | Enumerations | Exact adoption | THEME_COLOR_CLOSE | ui |
| THEME_COLOR_BUY | Selects buy in terminal info integer. | color | Enumerations | Exact adoption | THEME_COLOR_BUY | ui |
| THEME_COLOR_SELL | Selects sell in terminal info integer. | color | Enumerations | Exact adoption | THEME_COLOR_SELL | ui |
| THEME_COLOR_DEPOSIT | Selects deposit in terminal info integer. | color | Enumerations | Exact adoption | THEME_COLOR_DEPOSIT | ui |
| THEME_COLOR_WITHDRAWAL | Selects withdrawal in terminal info integer. | color | Enumerations | Exact adoption | THEME_COLOR_WITHDRAWAL | ui |
| THEME_COLOR_BID | Selects bid in terminal info integer. | color | Enumerations | Exact adoption | THEME_COLOR_BID | ui |
| THEME_COLOR_ASK | Selects ask in terminal info integer. | color | Enumerations | Exact adoption | THEME_COLOR_ASK | ui |
| THEME_COLOR_STOPS | Selects stops in terminal info integer. | color | Enumerations | Exact adoption | THEME_COLOR_STOPS | ui |
| THEME_COLOR_STOPS_RED | Selects stops red in terminal info integer. | color | Enumerations | Exact adoption | THEME_COLOR_STOPS_RED | ui |
| THEME_COLOR_STOPS_GREEN | Selects stops green in terminal info integer. | color | Enumerations | Exact adoption | THEME_COLOR_STOPS_GREEN | ui |
| THEME_COLOR_CONFIRM | Selects confirm in terminal info integer. | color | Enumerations | Exact adoption | THEME_COLOR_CONFIRM | ui |
| THEME_COLOR_REQUOTE | Selects requote in terminal info integer. | color | Enumerations | Exact adoption | THEME_COLOR_REQUOTE | ui |
| THEME_COLOR_REJECT | Selects reject in terminal info integer. | color | Enumerations | Exact adoption | THEME_COLOR_REJECT | ui |
| THEME_COLOR_NOTIFICATION | Selects notification in terminal info integer. | color | Enumerations | Exact adoption | THEME_COLOR_NOTIFICATION | ui |
| THEME_COLOR_RATING | Selects rating in terminal info integer. | color | Enumerations | Exact adoption | THEME_COLOR_RATING | ui |
| THEME_COLOR_BOOK_BUY | Selects book buy in terminal info integer. | color | Enumerations | Exact adoption | THEME_COLOR_BOOK_BUY | ui |
| THEME_COLOR_BOOK_SELL | Selects book sell in terminal info integer. | color | Enumerations | Exact adoption | THEME_COLOR_BOOK_SELL | ui |
| THEME_COLOR_BOOK_LAST | Selects book last in terminal info integer. | color | Enumerations | Exact adoption | THEME_COLOR_BOOK_LAST | ui |
| THEME_COLOR_BOOK_STOP | Selects book stop in terminal info integer. | color | Enumerations | Exact adoption | THEME_COLOR_BOOK_STOP | ui |
| THEME_COLOR_BOOK_SPREAD | Selects book spread in terminal info integer. | color | Enumerations | Exact adoption | THEME_COLOR_BOOK_SPREAD | ui |
| THEME_COLOR_TICKS_BID | Selects ticks bid in terminal info integer. | color | Enumerations | Exact adoption | THEME_COLOR_TICKS_BID | ui |
| THEME_COLOR_TICKS_ASK | Selects ticks ask in terminal info integer. | color | Enumerations | Exact adoption | THEME_COLOR_TICKS_ASK | ui |
| THEME_COLOR_TICKS_LAST | Selects ticks last in terminal info integer. | color | Enumerations | Exact adoption | THEME_COLOR_TICKS_LAST | ui |
| THEME_COLOR_TICKS_CROSS | Selects ticks cross in terminal info integer. | color | Enumerations | Exact adoption | THEME_COLOR_TICKS_CROSS | ui |
| THEME_COLOR_TICKS_SL | Selects ticks SL in terminal info integer. | color | Enumerations | Exact adoption | THEME_COLOR_TICKS_SL | ui |
| THEME_COLOR_TICKS_TP | Selects ticks TP in terminal info integer. | color | Enumerations | Exact adoption | THEME_COLOR_TICKS_TP | ui |
| THEME_COLOR_TESTER_START | Selects tester start in terminal info integer. | color | Enumerations | Exact adoption | THEME_COLOR_TESTER_START | ui |
| THEME_COLOR_TESTER_STOP | Selects tester stop in terminal info integer. | color | Enumerations | Exact adoption | THEME_COLOR_TESTER_STOP | ui |
| THEME_COLOR_TESTER_START_FRAME | Selects tester start frame in terminal info integer. | color | Enumerations | Exact adoption | THEME_COLOR_TESTER_START_FRAME | ui |
| THEME_COLOR_TESTER_STOP_FRAME | Selects tester stop frame in terminal info integer. | color | Enumerations | Exact adoption | THEME_COLOR_TESTER_STOP_FRAME | ui |
| THEME_COLOR_TESTER_PROGRESS | Selects tester progress in terminal info integer. | color | Enumerations | Exact adoption | THEME_COLOR_TESTER_PROGRESS | ui |
| THEME_COLOR_TESTER_BALANCE | Selects tester balance in terminal info integer. | color | Enumerations | Exact adoption | THEME_COLOR_TESTER_BALANCE | ui |
| THEME_COLOR_TESTER_EQUITY | Selects tester equity in terminal info integer. | color | Enumerations | Exact adoption | THEME_COLOR_TESTER_EQUITY | ui |
| THEME_COLOR_TESTER_MARGIN | Selects tester margin in terminal info integer. | color | Enumerations | Exact adoption | THEME_COLOR_TESTER_MARGIN | ui |
| THEME_COLOR_PROFILER_CALL | Selects profiler call in terminal info integer. | color | Enumerations | Exact adoption | THEME_COLOR_PROFILER_CALL | ui |
| THEME_COLOR_PROFILER_CALLSEL | Selects profiler callsel in terminal info integer. | color | Enumerations | Exact adoption | THEME_COLOR_PROFILER_CALLSEL | ui |
| THEME_COLOR_PROFILER_LINE | Selects profiler line in terminal info integer. | color | Enumerations | Exact adoption | THEME_COLOR_PROFILER_LINE | ui |
| THEME_COLOR_PROFILER_LINESEL | Selects profiler linesel in terminal info integer. | color | Enumerations | Exact adoption | THEME_COLOR_PROFILER_LINESEL | ui |
| ENUM_MQL_INFO_INTEGER | Defines the identifier set for MQL info integer. | enum (int) | Enumerations | Platform-neutral rename | ENUM_PROGRAM_INFO_INTEGER | workspace |
| MQL_HANDLES_USED | Selects MQL handles used in MQL info integer. | int | Enumerations | Platform-neutral rename | PROGRAM_HANDLES_USED | workspace |
| MQL_MEMORY_LIMIT | Selects MQL memory limit in MQL info integer. | int | Enumerations | Platform-neutral rename | PROGRAM_MEMORY_LIMIT | workspace |
| MQL_MEMORY_USED | Selects MQL memory used in MQL info integer. | int | Enumerations | Platform-neutral rename | PROGRAM_MEMORY_USED | workspace |
| MQL_PROGRAM_TYPE | Selects MQL program type in MQL info integer. | ENUM_PROGRAM_TYPE | Enumerations | Platform-neutral rename | PROGRAM_PROGRAM_TYPE | workspace |
| MQL_DLLS_ALLOWED | Selects MQL dlls allowed in MQL info integer. | bool | Enumerations | Platform-neutral rename | PROGRAM_DLLS_ALLOWED | workspace |
| MQL_TRADE_ALLOWED | Selects MQL trade allowed in MQL info integer. | bool | Enumerations | Platform-neutral rename | PROGRAM_TRADE_ALLOWED | workspace |
| MQL_SIGNALS_ALLOWED | Selects MQL signals allowed in MQL info integer. | bool | Enumerations | Platform-neutral rename | PROGRAM_SIGNALS_ALLOWED | workspace |
| MQL_DEBUG | Selects MQL debug in MQL info integer. | bool | Enumerations | Platform-neutral rename | PROGRAM_DEBUG | workspace |
| MQL_PROFILER | Selects MQL profiler in MQL info integer. | bool | Enumerations | Platform-neutral rename | PROGRAM_PROFILER | workspace |
| MQL_TESTER | Selects MQL tester in MQL info integer. | bool | Enumerations | Platform-neutral rename | PROGRAM_TESTER | workspace |
| MQL_FORWARD | Selects MQL forward in MQL info integer. | bool | Enumerations | Platform-neutral rename | PROGRAM_FORWARD | workspace |
| MQL_OPTIMIZATION | Selects MQL optimization in MQL info integer. | bool | Enumerations | Platform-neutral rename | PROGRAM_OPTIMIZATION | workspace |
| MQL_VISUAL_MODE | Selects MQL visual mode in MQL info integer. | bool | Enumerations | Platform-neutral rename | PROGRAM_VISUAL_MODE | workspace |
| MQL_FRAME_MODE | Selects MQL frame mode in MQL info integer. | bool | Enumerations | Platform-neutral rename | PROGRAM_FRAME_MODE | workspace |
| MQL_LICENSE_TYPE | Selects MQL license type in MQL info integer. | ENUM_LICENSE_TYPE | Enumerations | Platform-neutral rename | PROGRAM_LICENSE_TYPE | workspace |
| ENUM_MQL_INFO_STRING | Defines the identifier set for MQL info string. | enum (int) | Enumerations | Platform-neutral rename | ENUM_PROGRAM_INFO_STRING | workspace |
| ENUM_PROGRAM_TYPE | Defines the identifier set for program type. | enum (int) | Enumerations | Exact adoption | ENUM_PROGRAM_TYPE | workspace |
| ENUM_LICENSE_TYPE | Defines the identifier set for license type. Rejected because it models the MQL5 program-licensing system. | enum (int) | Enumerations | Rejected adoption | — | — |
| MQL_STARTED_FROM_CONFIG | Selects MQL started from config in MQL info integer. | bool | Enumerations | Platform-neutral rename | PROGRAM_STARTED_FROM_CONFIG | workspace |
| MQL_PROGRAM_NAME | Selects MQL program name in MQL info string. | string | Enumerations | Platform-neutral rename | PROGRAM_PROGRAM_NAME | workspace |
| MQL5_PROGRAM_PATH | Selects MQL5 program path in MQL info string. | string | Enumerations | Platform-neutral rename | PROGRAM_PROGRAM_PATH | workspace |
| PROGRAM_SCRIPT | Selects program script in program type. | ENUM_PROGRAM_TYPE | Enumerations | Exact adoption | PROGRAM_SCRIPT | workspace |
| PROGRAM_EXPERT | Selects program expert in program type. | ENUM_PROGRAM_TYPE | Enumerations | Exact adoption | PROGRAM_EXPERT | workspace |
| PROGRAM_INDICATOR | Selects program indicator in program type. | ENUM_PROGRAM_TYPE | Enumerations | Exact adoption | PROGRAM_INDICATOR | workspace |
| PROGRAM_SERVICE | Selects program service in program type. | ENUM_PROGRAM_TYPE | Enumerations | Exact adoption | PROGRAM_SERVICE | workspace |
| LICENSE_FREE | Selects license free in license type. Rejected because it models the MQL5 program-licensing system. | ENUM_LICENSE_TYPE | Enumerations | Rejected adoption | — | — |
| LICENSE_DEMO | Selects license demo in license type. Rejected because it models the MQL5 program-licensing system. | ENUM_LICENSE_TYPE | Enumerations | Rejected adoption | — | — |
| LICENSE_FULL | Selects license full in license type. Rejected because it models the MQL5 program-licensing system. | ENUM_LICENSE_TYPE | Enumerations | Rejected adoption | — | — |
| LICENSE_TIME | Selects license time in license type. Rejected because it models the MQL5 program-licensing system. | ENUM_LICENSE_TYPE | Enumerations | Rejected adoption | — | — |
| ENUM_SYMBOL_INFO_INTEGER | Defines the identifier set for symbol info integer. | enum (int) | Enumerations | Exact adoption | ENUM_SYMBOL_INFO_INTEGER | catalogue |
| SYMBOL_SUBSCRIPTION_DELAY | Selects subscription delay in symbol info integer. HaruQuantAI adds provider-neutral provenance and specification validation. | bool | Enumerations | Semantic extension | SYMBOL_SUBSCRIPTION_DELAY | catalogue |
| SYMBOL_SECTOR | Selects sector in symbol info integer. HaruQuantAI adds provider-neutral provenance and specification validation. | ENUM_SYMBOL_SECTOR | Enumerations | Semantic extension | SYMBOL_SECTOR | catalogue |
| SYMBOL_INDUSTRY | Selects industry in symbol info integer. HaruQuantAI adds provider-neutral provenance and specification validation. | ENUM_SYMBOL_INDUSTRY | Enumerations | Semantic extension | SYMBOL_INDUSTRY | catalogue |
| SYMBOL_CUSTOM | Selects custom in symbol info integer. HaruQuantAI adds provider-neutral provenance and specification validation. | bool | Enumerations | Semantic extension | SYMBOL_CUSTOM | catalogue |
| SYMBOL_BACKGROUND_COLOR | Selects background color in symbol info integer. HaruQuantAI adds provider-neutral provenance and specification validation. | color | Enumerations | Semantic extension | SYMBOL_BACKGROUND_COLOR | catalogue |
| SYMBOL_CHART_MODE | Selects chart mode in symbol info integer. HaruQuantAI adds provider-neutral provenance and specification validation. | ENUM_SYMBOL_CHART_MODE | Enumerations | Semantic extension | SYMBOL_CHART_MODE | catalogue |
| SYMBOL_EXIST | Selects exist in symbol info integer. HaruQuantAI adds provider-neutral provenance and specification validation. | bool | Enumerations | Semantic extension | SYMBOL_EXIST | catalogue |
| SYMBOL_SELECT | Selects select in symbol info integer. HaruQuantAI adds provider-neutral provenance and specification validation. | bool | Enumerations | Semantic extension | SYMBOL_SELECT | catalogue |
| SYMBOL_VISIBLE | Selects visible in symbol info integer. HaruQuantAI adds provider-neutral provenance and specification validation. | bool | Enumerations | Semantic extension | SYMBOL_VISIBLE | catalogue |
| SYMBOL_SESSION_DEALS | Selects session deals in symbol info integer. HaruQuantAI adds provider-neutral provenance and specification validation. | long | Enumerations | Semantic extension | SYMBOL_SESSION_DEALS | catalogue |
| SYMBOL_SESSION_BUY_ORDERS | Selects session buy orders in symbol info integer. HaruQuantAI adds provider-neutral provenance and specification validation. | long | Enumerations | Semantic extension | SYMBOL_SESSION_BUY_ORDERS | catalogue |
| SYMBOL_SESSION_SELL_ORDERS | Selects session sell orders in symbol info integer. HaruQuantAI adds provider-neutral provenance and specification validation. | long | Enumerations | Semantic extension | SYMBOL_SESSION_SELL_ORDERS | catalogue |
| SYMBOL_VOLUME | Selects volume in symbol info integer. HaruQuantAI adds provider-neutral provenance and specification validation. | long | Enumerations | Semantic extension | SYMBOL_VOLUME | catalogue |
| SYMBOL_VOLUMEHIGH | Selects volumehigh in symbol info integer. HaruQuantAI adds provider-neutral provenance and specification validation. | long | Enumerations | Semantic extension | SYMBOL_VOLUMEHIGH | catalogue |
| SYMBOL_VOLUMELOW | Selects volumelow in symbol info integer. HaruQuantAI adds provider-neutral provenance and specification validation. | long | Enumerations | Semantic extension | SYMBOL_VOLUMELOW | catalogue |
| SYMBOL_TIME | Selects time in symbol info integer. HaruQuantAI adds provider-neutral provenance and specification validation. | datetime | Enumerations | Semantic extension | SYMBOL_TIME | catalogue |
| SYMBOL_TIME_MSC | Selects time msc in symbol info integer. HaruQuantAI adds provider-neutral provenance and specification validation. | long | Enumerations | Semantic extension | SYMBOL_TIME_MSC | catalogue |
| SYMBOL_DIGITS | Selects digits in symbol info integer. HaruQuantAI adds provider-neutral provenance and specification validation. | int | Enumerations | Semantic extension | SYMBOL_DIGITS | catalogue |
| SYMBOL_SPREAD_FLOAT | Selects spread float in symbol info integer. HaruQuantAI adds provider-neutral provenance and specification validation. | bool | Enumerations | Semantic extension | SYMBOL_SPREAD_FLOAT | catalogue |
| SYMBOL_SPREAD | Selects spread in symbol info integer. HaruQuantAI adds provider-neutral provenance and specification validation. | int | Enumerations | Semantic extension | SYMBOL_SPREAD | catalogue |
| SYMBOL_TICKS_BOOKDEPTH | Selects ticks bookdepth in symbol info integer. HaruQuantAI adds provider-neutral provenance and specification validation. | int | Enumerations | Semantic extension | SYMBOL_TICKS_BOOKDEPTH | catalogue |
| SYMBOL_TRADE_CALC_MODE | Selects trade calc mode in symbol info integer. HaruQuantAI adds provider-neutral provenance and specification validation. | ENUM_SYMBOL_CALC_MODE | Enumerations | Semantic extension | SYMBOL_TRADE_CALC_MODE | catalogue |
| SYMBOL_TRADE_MODE | Selects trade mode in symbol info integer. HaruQuantAI adds provider-neutral provenance and specification validation. | ENUM_SYMBOL_TRADE_MODE | Enumerations | Semantic extension | SYMBOL_TRADE_MODE | catalogue |
| SYMBOL_START_TIME | Selects start time in symbol info integer. HaruQuantAI adds provider-neutral provenance and specification validation. | datetime | Enumerations | Semantic extension | SYMBOL_START_TIME | catalogue |
| SYMBOL_EXPIRATION_TIME | Selects expiration time in symbol info integer. HaruQuantAI adds provider-neutral provenance and specification validation. | datetime | Enumerations | Semantic extension | SYMBOL_EXPIRATION_TIME | catalogue |
| SYMBOL_TRADE_STOPS_LEVEL | Selects trade stops level in symbol info integer. HaruQuantAI adds provider-neutral provenance and specification validation. | int | Enumerations | Semantic extension | SYMBOL_TRADE_STOPS_LEVEL | catalogue |
| SYMBOL_TRADE_FREEZE_LEVEL | Selects trade freeze level in symbol info integer. HaruQuantAI adds provider-neutral provenance and specification validation. | int | Enumerations | Semantic extension | SYMBOL_TRADE_FREEZE_LEVEL | catalogue |
| SYMBOL_TRADE_EXEMODE | Selects trade exemode in symbol info integer. HaruQuantAI adds provider-neutral provenance and specification validation. | ENUM_SYMBOL_TRADE_EXECUTION | Enumerations | Semantic extension | SYMBOL_TRADE_EXEMODE | catalogue |
| SYMBOL_SWAP_MODE | Selects swap mode in symbol info integer. HaruQuantAI adds provider-neutral provenance and specification validation. | ENUM_SYMBOL_SWAP_MODE | Enumerations | Semantic extension | SYMBOL_SWAP_MODE | catalogue |
| SYMBOL_SWAP_ROLLOVER3DAYS | Selects swap rollover3 days in symbol info integer. HaruQuantAI adds provider-neutral provenance and specification validation. | ENUM_DAY_OF_WEEK | Enumerations | Semantic extension | SYMBOL_SWAP_ROLLOVER3DAYS | catalogue |
| SYMBOL_MARGIN_HEDGED_USE_LEG | Selects margin hedged use leg in symbol info integer. HaruQuantAI adds provider-neutral provenance and specification validation. | bool | Enumerations | Semantic extension | SYMBOL_MARGIN_HEDGED_USE_LEG | catalogue |
| SYMBOL_EXPIRATION_MODE | Selects expiration mode in symbol info integer. HaruQuantAI adds provider-neutral provenance and specification validation. | int | Enumerations | Semantic extension | SYMBOL_EXPIRATION_MODE | catalogue |
| SYMBOL_FILLING_MODE | Selects filling mode in symbol info integer. HaruQuantAI adds provider-neutral provenance and specification validation. | int | Enumerations | Semantic extension | SYMBOL_FILLING_MODE | catalogue |
| SYMBOL_ORDER_MODE | Selects order mode in symbol info integer. HaruQuantAI adds provider-neutral provenance and specification validation. | int | Enumerations | Semantic extension | SYMBOL_ORDER_MODE | catalogue |
| SYMBOL_ORDER_GTC_MODE | Selects order GTC mode in symbol info integer. HaruQuantAI adds provider-neutral provenance and specification validation. | ENUM_SYMBOL_ORDER_GTC_MODE | Enumerations | Semantic extension | SYMBOL_ORDER_GTC_MODE | catalogue |
| ENUM_SYMBOL_INFO_DOUBLE | Defines the identifier set for symbol info double. | enum (int) | Enumerations | Exact adoption | ENUM_SYMBOL_INFO_DOUBLE | catalogue |
| SYMBOL_OPTION_MODE | Selects option mode in symbol info integer. HaruQuantAI adds provider-neutral provenance and specification validation. | ENUM_SYMBOL_OPTION_MODE | Enumerations | Semantic extension | SYMBOL_OPTION_MODE | catalogue |
| SYMBOL_OPTION_RIGHT | Selects option right in symbol info integer. HaruQuantAI adds provider-neutral provenance and specification validation. | ENUM_SYMBOL_OPTION_RIGHT | Enumerations | Semantic extension | SYMBOL_OPTION_RIGHT | catalogue |
| SYMBOL_BID | Selects bid in symbol info double. HaruQuantAI adds provider-neutral provenance and specification validation. | double | Enumerations | Semantic extension | SYMBOL_BID | catalogue |
| SYMBOL_BIDHIGH | Selects bidhigh in symbol info double. HaruQuantAI adds provider-neutral provenance and specification validation. | double | Enumerations | Semantic extension | SYMBOL_BIDHIGH | catalogue |
| SYMBOL_BIDLOW | Selects bidlow in symbol info double. HaruQuantAI adds provider-neutral provenance and specification validation. | double | Enumerations | Semantic extension | SYMBOL_BIDLOW | catalogue |
| SYMBOL_ASK | Selects ask in symbol info double. HaruQuantAI adds provider-neutral provenance and specification validation. | double | Enumerations | Semantic extension | SYMBOL_ASK | catalogue |
| SYMBOL_ASKHIGH | Selects askhigh in symbol info double. HaruQuantAI adds provider-neutral provenance and specification validation. | double | Enumerations | Semantic extension | SYMBOL_ASKHIGH | catalogue |
| SYMBOL_ASKLOW | Selects asklow in symbol info double. HaruQuantAI adds provider-neutral provenance and specification validation. | double | Enumerations | Semantic extension | SYMBOL_ASKLOW | catalogue |
| SYMBOL_LAST | Selects last in symbol info double. HaruQuantAI adds provider-neutral provenance and specification validation. | double | Enumerations | Semantic extension | SYMBOL_LAST | catalogue |
| SYMBOL_LASTHIGH | Selects lasthigh in symbol info double. HaruQuantAI adds provider-neutral provenance and specification validation. | double | Enumerations | Semantic extension | SYMBOL_LASTHIGH | catalogue |
| SYMBOL_LASTLOW | Selects lastlow in symbol info double. HaruQuantAI adds provider-neutral provenance and specification validation. | double | Enumerations | Semantic extension | SYMBOL_LASTLOW | catalogue |
| SYMBOL_VOLUME_REAL | Selects volume real in symbol info double. HaruQuantAI adds provider-neutral provenance and specification validation. | double | Enumerations | Semantic extension | SYMBOL_VOLUME_REAL | catalogue |
| SYMBOL_VOLUMEHIGH_REAL | Selects volumehigh real in symbol info double. HaruQuantAI adds provider-neutral provenance and specification validation. | double | Enumerations | Semantic extension | SYMBOL_VOLUMEHIGH_REAL | catalogue |
| SYMBOL_VOLUMELOW_REAL | Selects volumelow real in symbol info double. HaruQuantAI adds provider-neutral provenance and specification validation. | double | Enumerations | Semantic extension | SYMBOL_VOLUMELOW_REAL | catalogue |
| SYMBOL_OPTION_STRIKE | Selects option strike in symbol info double. HaruQuantAI adds provider-neutral provenance and specification validation. | double | Enumerations | Semantic extension | SYMBOL_OPTION_STRIKE | catalogue |
| SYMBOL_POINT | Selects point in symbol info double. HaruQuantAI adds provider-neutral provenance and specification validation. | double | Enumerations | Semantic extension | SYMBOL_POINT | catalogue |
| SYMBOL_TRADE_TICK_VALUE | Selects trade tick value in symbol info double. HaruQuantAI adds provider-neutral provenance and specification validation. | double | Enumerations | Semantic extension | SYMBOL_TRADE_TICK_VALUE | catalogue |
| SYMBOL_TRADE_TICK_VALUE_PROFIT | Selects trade tick value profit in symbol info double. HaruQuantAI adds provider-neutral provenance and specification validation. | double | Enumerations | Semantic extension | SYMBOL_TRADE_TICK_VALUE_PROFIT | catalogue |
| SYMBOL_TRADE_TICK_VALUE_LOSS | Selects trade tick value loss in symbol info double. HaruQuantAI adds provider-neutral provenance and specification validation. | double | Enumerations | Semantic extension | SYMBOL_TRADE_TICK_VALUE_LOSS | catalogue |
| SYMBOL_TRADE_TICK_SIZE | Selects trade tick size in symbol info double. HaruQuantAI adds provider-neutral provenance and specification validation. | double | Enumerations | Semantic extension | SYMBOL_TRADE_TICK_SIZE | catalogue |
| SYMBOL_TRADE_CONTRACT_SIZE | Selects trade contract size in symbol info double. HaruQuantAI adds provider-neutral provenance and specification validation. | double | Enumerations | Semantic extension | SYMBOL_TRADE_CONTRACT_SIZE | catalogue |
| SYMBOL_TRADE_ACCRUED_INTEREST | Selects trade accrued interest in symbol info double. HaruQuantAI adds provider-neutral provenance and specification validation. | double | Enumerations | Semantic extension | SYMBOL_TRADE_ACCRUED_INTEREST | catalogue |
| SYMBOL_TRADE_FACE_VALUE | Selects trade face value in symbol info double. HaruQuantAI adds provider-neutral provenance and specification validation. | double | Enumerations | Semantic extension | SYMBOL_TRADE_FACE_VALUE | catalogue |
| SYMBOL_TRADE_LIQUIDITY_RATE | Selects trade liquidity rate in symbol info double. HaruQuantAI adds provider-neutral provenance and specification validation. | double | Enumerations | Semantic extension | SYMBOL_TRADE_LIQUIDITY_RATE | catalogue |
| SYMBOL_VOLUME_MIN | Selects volume min in symbol info double. HaruQuantAI adds provider-neutral provenance and specification validation. | double | Enumerations | Semantic extension | SYMBOL_VOLUME_MIN | catalogue |
| SYMBOL_VOLUME_MAX | Selects volume max in symbol info double. HaruQuantAI adds provider-neutral provenance and specification validation. | double | Enumerations | Semantic extension | SYMBOL_VOLUME_MAX | catalogue |
| SYMBOL_VOLUME_STEP | Selects volume step in symbol info double. HaruQuantAI adds provider-neutral provenance and specification validation. | double | Enumerations | Semantic extension | SYMBOL_VOLUME_STEP | catalogue |
| SYMBOL_VOLUME_LIMIT | Selects volume limit in symbol info double. HaruQuantAI adds provider-neutral provenance and specification validation. | double | Enumerations | Semantic extension | SYMBOL_VOLUME_LIMIT | catalogue |
| SYMBOL_SWAP_LONG | Selects swap long in symbol info double. HaruQuantAI adds provider-neutral provenance and specification validation. | double | Enumerations | Semantic extension | SYMBOL_SWAP_LONG | catalogue |
| SYMBOL_SWAP_SHORT | Selects swap short in symbol info double. HaruQuantAI adds provider-neutral provenance and specification validation. | double | Enumerations | Semantic extension | SYMBOL_SWAP_SHORT | catalogue |
| SYMBOL_SWAP_SUNDAY | Selects swap sunday in symbol info double. HaruQuantAI adds provider-neutral provenance and specification validation. | double | Enumerations | Semantic extension | SYMBOL_SWAP_SUNDAY | catalogue |
| SYMBOL_SWAP_MONDAY | Selects swap monday in symbol info double. HaruQuantAI adds provider-neutral provenance and specification validation. | double | Enumerations | Semantic extension | SYMBOL_SWAP_MONDAY | catalogue |
| SYMBOL_SWAP_TUESDAY | Selects swap tuesday in symbol info double. HaruQuantAI adds provider-neutral provenance and specification validation. | double | Enumerations | Semantic extension | SYMBOL_SWAP_TUESDAY | catalogue |
| SYMBOL_SWAP_WEDNESDAY | Selects swap wednesday in symbol info double. HaruQuantAI adds provider-neutral provenance and specification validation. | double | Enumerations | Semantic extension | SYMBOL_SWAP_WEDNESDAY | catalogue |
| SYMBOL_SWAP_THURSDAY | Selects swap thursday in symbol info double. HaruQuantAI adds provider-neutral provenance and specification validation. | double | Enumerations | Semantic extension | SYMBOL_SWAP_THURSDAY | catalogue |
| SYMBOL_SWAP_FRIDAY | Selects swap friday in symbol info double. HaruQuantAI adds provider-neutral provenance and specification validation. | double | Enumerations | Semantic extension | SYMBOL_SWAP_FRIDAY | catalogue |
| SYMBOL_SWAP_SATURDAY | Selects swap saturday in symbol info double. HaruQuantAI adds provider-neutral provenance and specification validation. | double | Enumerations | Semantic extension | SYMBOL_SWAP_SATURDAY | catalogue |
| SYMBOL_MARGIN_INITIAL | Selects margin initial in symbol info double. HaruQuantAI adds provider-neutral provenance and specification validation. | double | Enumerations | Semantic extension | SYMBOL_MARGIN_INITIAL | catalogue |
| SYMBOL_MARGIN_MAINTENANCE | Selects margin maintenance in symbol info double. HaruQuantAI adds provider-neutral provenance and specification validation. | double | Enumerations | Semantic extension | SYMBOL_MARGIN_MAINTENANCE | catalogue |
| SYMBOL_SESSION_VOLUME | Selects session volume in symbol info double. HaruQuantAI adds provider-neutral provenance and specification validation. | double | Enumerations | Semantic extension | SYMBOL_SESSION_VOLUME | catalogue |
| SYMBOL_SESSION_TURNOVER | Selects session turnover in symbol info double. HaruQuantAI adds provider-neutral provenance and specification validation. | double | Enumerations | Semantic extension | SYMBOL_SESSION_TURNOVER | catalogue |
| SYMBOL_SESSION_INTEREST | Selects session interest in symbol info double. HaruQuantAI adds provider-neutral provenance and specification validation. | double | Enumerations | Semantic extension | SYMBOL_SESSION_INTEREST | catalogue |
| SYMBOL_SESSION_BUY_ORDERS_VOLUME | Selects session buy orders volume in symbol info double. HaruQuantAI adds provider-neutral provenance and specification validation. | double | Enumerations | Semantic extension | SYMBOL_SESSION_BUY_ORDERS_VOLUME | catalogue |
| SYMBOL_SESSION_SELL_ORDERS_VOLUME | Selects session sell orders volume in symbol info double. HaruQuantAI adds provider-neutral provenance and specification validation. | double | Enumerations | Semantic extension | SYMBOL_SESSION_SELL_ORDERS_VOLUME | catalogue |
| SYMBOL_SESSION_OPEN | Selects session open in symbol info double. HaruQuantAI adds provider-neutral provenance and specification validation. | double | Enumerations | Semantic extension | SYMBOL_SESSION_OPEN | catalogue |
| SYMBOL_SESSION_CLOSE | Selects session close in symbol info double. HaruQuantAI adds provider-neutral provenance and specification validation. | double | Enumerations | Semantic extension | SYMBOL_SESSION_CLOSE | catalogue |
| SYMBOL_SESSION_AW | Selects session aw in symbol info double. HaruQuantAI adds provider-neutral provenance and specification validation. | double | Enumerations | Semantic extension | SYMBOL_SESSION_AW | catalogue |
| SYMBOL_SESSION_PRICE_SETTLEMENT | Selects session price settlement in symbol info double. HaruQuantAI adds provider-neutral provenance and specification validation. | double | Enumerations | Semantic extension | SYMBOL_SESSION_PRICE_SETTLEMENT | catalogue |
| SYMBOL_SESSION_PRICE_LIMIT_MIN | Selects session price limit min in symbol info double. HaruQuantAI adds provider-neutral provenance and specification validation. | double | Enumerations | Semantic extension | SYMBOL_SESSION_PRICE_LIMIT_MIN | catalogue |
| SYMBOL_SESSION_PRICE_LIMIT_MAX | Selects session price limit max in symbol info double. HaruQuantAI adds provider-neutral provenance and specification validation. | double | Enumerations | Semantic extension | SYMBOL_SESSION_PRICE_LIMIT_MAX | catalogue |
| SYMBOL_MARGIN_HEDGED | Selects margin hedged in symbol info double. HaruQuantAI adds provider-neutral provenance and specification validation. | double | Enumerations | Semantic extension | SYMBOL_MARGIN_HEDGED | catalogue |
| SYMBOL_PRICE_CHANGE | Selects price change in symbol info double. HaruQuantAI adds provider-neutral provenance and specification validation. | double | Enumerations | Semantic extension | SYMBOL_PRICE_CHANGE | catalogue |
| SYMBOL_PRICE_VOLATILITY | Selects price volatility in symbol info double. HaruQuantAI adds provider-neutral provenance and specification validation. | double | Enumerations | Semantic extension | SYMBOL_PRICE_VOLATILITY | catalogue |
| SYMBOL_PRICE_THEORETICAL | Selects price theoretical in symbol info double. HaruQuantAI adds provider-neutral provenance and specification validation. | double | Enumerations | Semantic extension | SYMBOL_PRICE_THEORETICAL | catalogue |
| SYMBOL_PRICE_DELTA | Selects price delta in symbol info double. HaruQuantAI adds provider-neutral provenance and specification validation. | double | Enumerations | Semantic extension | SYMBOL_PRICE_DELTA | catalogue |
| SYMBOL_PRICE_THETA | Selects price theta in symbol info double. HaruQuantAI adds provider-neutral provenance and specification validation. | double | Enumerations | Semantic extension | SYMBOL_PRICE_THETA | catalogue |
| SYMBOL_PRICE_GAMMA | Selects price gamma in symbol info double. HaruQuantAI adds provider-neutral provenance and specification validation. | double | Enumerations | Semantic extension | SYMBOL_PRICE_GAMMA | catalogue |
| SYMBOL_PRICE_VEGA | Selects price vega in symbol info double. HaruQuantAI adds provider-neutral provenance and specification validation. | double | Enumerations | Semantic extension | SYMBOL_PRICE_VEGA | catalogue |
| SYMBOL_PRICE_RHO | Selects price rho in symbol info double. HaruQuantAI adds provider-neutral provenance and specification validation. | double | Enumerations | Semantic extension | SYMBOL_PRICE_RHO | catalogue |
| SYMBOL_PRICE_OMEGA | Selects price omega in symbol info double. HaruQuantAI adds provider-neutral provenance and specification validation. | double | Enumerations | Semantic extension | SYMBOL_PRICE_OMEGA | catalogue |
| SYMBOL_PRICE_SENSITIVITY | Selects price sensitivity in symbol info double. HaruQuantAI adds provider-neutral provenance and specification validation. | double | Enumerations | Semantic extension | SYMBOL_PRICE_SENSITIVITY | catalogue |
| ENUM_SYMBOL_INFO_STRING | Defines the identifier set for symbol info string. | enum (int) | Enumerations | Exact adoption | ENUM_SYMBOL_INFO_STRING | catalogue |
| SYMBOL_BASIS | Selects basis in symbol info string. HaruQuantAI adds provider-neutral provenance and specification validation. | string | Enumerations | Semantic extension | SYMBOL_BASIS | catalogue |
| SYMBOL_CATEGORY | Selects category in symbol info string. HaruQuantAI adds provider-neutral provenance and specification validation. | string | Enumerations | Semantic extension | SYMBOL_CATEGORY | catalogue |
| SYMBOL_COUNTRY | Selects country in symbol info string. HaruQuantAI adds provider-neutral provenance and specification validation. | string | Enumerations | Semantic extension | SYMBOL_COUNTRY | catalogue |
| SYMBOL_SECTOR_NAME | Selects sector name in symbol info string. HaruQuantAI adds provider-neutral provenance and specification validation. | string | Enumerations | Semantic extension | SYMBOL_SECTOR_NAME | catalogue |
| SYMBOL_INDUSTRY_NAME | Selects industry name in symbol info string. HaruQuantAI adds provider-neutral provenance and specification validation. | string | Enumerations | Semantic extension | SYMBOL_INDUSTRY_NAME | catalogue |
| SYMBOL_CURRENCY_BASE | Selects currency base in symbol info string. HaruQuantAI adds provider-neutral provenance and specification validation. | string | Enumerations | Semantic extension | SYMBOL_CURRENCY_BASE | catalogue |
| SYMBOL_CURRENCY_PROFIT | Selects currency profit in symbol info string. HaruQuantAI adds provider-neutral provenance and specification validation. | string | Enumerations | Semantic extension | SYMBOL_CURRENCY_PROFIT | catalogue |
| SYMBOL_CURRENCY_MARGIN | Selects currency margin in symbol info string. HaruQuantAI adds provider-neutral provenance and specification validation. | string | Enumerations | Semantic extension | SYMBOL_CURRENCY_MARGIN | catalogue |
| SYMBOL_BANK | Selects bank in symbol info string. HaruQuantAI adds provider-neutral provenance and specification validation. | string | Enumerations | Semantic extension | SYMBOL_BANK | catalogue |
| SYMBOL_DESCRIPTION | Selects description in symbol info string. HaruQuantAI adds provider-neutral provenance and specification validation. | string | Enumerations | Semantic extension | SYMBOL_DESCRIPTION | catalogue |
| SYMBOL_EXCHANGE | Selects exchange in symbol info string. HaruQuantAI adds provider-neutral provenance and specification validation. | string | Enumerations | Semantic extension | SYMBOL_EXCHANGE | catalogue |
| SYMBOL_FORMULA | Selects formula in symbol info string. HaruQuantAI adds provider-neutral provenance and specification validation. | string | Enumerations | Semantic extension | SYMBOL_FORMULA | catalogue |
| SYMBOL_ISIN | Selects isin in symbol info string. HaruQuantAI adds provider-neutral provenance and specification validation. | string | Enumerations | Semantic extension | SYMBOL_ISIN | catalogue |
| SYMBOL_PAGE | Selects page in symbol info string. HaruQuantAI adds provider-neutral provenance and specification validation. | string | Enumerations | Semantic extension | SYMBOL_PAGE | catalogue |
| ENUM_SYMBOL_CHART_MODE | Defines the identifier set for symbol chart mode. | enum (int) | Enumerations | Exact adoption | ENUM_SYMBOL_CHART_MODE | catalogue |
| SYMBOL_PATH | Selects path in symbol info string. HaruQuantAI adds provider-neutral provenance and specification validation. | string | Enumerations | Semantic extension | SYMBOL_PATH | catalogue |
| SYMBOL_CHART_MODE_BID | Selects chart mode bid in symbol chart mode. | ENUM_SYMBOL_CHART_MODE | Enumerations | Exact adoption | SYMBOL_CHART_MODE_BID | catalogue |
| SYMBOL_CHART_MODE_LAST | Selects chart mode last in symbol chart mode. | ENUM_SYMBOL_CHART_MODE | Enumerations | Exact adoption | SYMBOL_CHART_MODE_LAST | catalogue |
| SYMBOL_EXPIRATION_GTC | Value: 1. Represents symbol expiration GTC. | Not specified in reference | Constants | Exact adoption | SYMBOL_EXPIRATION_GTC | catalogue |
| SYMBOL_EXPIRATION_DAY | Value: 2. Represents symbol expiration day. | Not specified in reference | Constants | Exact adoption | SYMBOL_EXPIRATION_DAY | catalogue |
| SYMBOL_EXPIRATION_SPECIFIED | Value: 4. Represents symbol expiration specified. | Not specified in reference | Constants | Exact adoption | SYMBOL_EXPIRATION_SPECIFIED | catalogue |
| SYMBOL_EXPIRATION_SPECIFIED_DAY | Value: 8. Represents symbol expiration specified day. | Not specified in reference | Constants | Exact adoption | SYMBOL_EXPIRATION_SPECIFIED_DAY | catalogue |
| ENUM_SYMBOL_ORDER_GTC_MODE | Defines the identifier set for symbol order GTC mode. | enum (int) | Enumerations | Exact adoption | ENUM_SYMBOL_ORDER_GTC_MODE | catalogue |
| SYMBOL_ORDERS_GTC | Selects orders GTC in symbol order GTC mode. | ENUM_SYMBOL_ORDER_GTC_MODE | Enumerations | Exact adoption | SYMBOL_ORDERS_GTC | catalogue |
| SYMBOL_ORDERS_DAILY | Selects orders daily in symbol order GTC mode. | ENUM_SYMBOL_ORDER_GTC_MODE | Enumerations | Exact adoption | SYMBOL_ORDERS_DAILY | catalogue |
| SYMBOL_ORDERS_DAILY_EXCLUDING_STOPS | Selects orders daily excluding stops in symbol order GTC mode. | ENUM_SYMBOL_ORDER_GTC_MODE | Enumerations | Exact adoption | SYMBOL_ORDERS_DAILY_EXCLUDING_STOPS | catalogue |
| SYMBOL_FILLING_FOK | Value: 1. Represents symbol filling FOK. | Not specified in reference | Constants | Exact adoption | SYMBOL_FILLING_FOK | catalogue |
| SYMBOL_FILLING_IOC | Value: 2. Represents symbol filling IOC. | Not specified in reference | Constants | Exact adoption | SYMBOL_FILLING_IOC | catalogue |
| SYMBOL_FILLING_BOC | Value: 4. Represents symbol filling boc. | Not specified in reference | Constants | Exact adoption | SYMBOL_FILLING_BOC | catalogue |
| SYMBOL_ORDER_MARKET | Value: 1. Represents symbol order market. | Not specified in reference | Constants | Exact adoption | SYMBOL_ORDER_MARKET | catalogue |
| SYMBOL_ORDER_LIMIT | Value: 2. Represents symbol order limit. | Not specified in reference | Constants | Exact adoption | SYMBOL_ORDER_LIMIT | catalogue |
| SYMBOL_ORDER_STOP | Value: 4. Represents symbol order stop. | Not specified in reference | Constants | Exact adoption | SYMBOL_ORDER_STOP | catalogue |
| SYMBOL_ORDER_STOP_LIMIT | Value: 8. Represents symbol order stop limit. | Not specified in reference | Constants | Exact adoption | SYMBOL_ORDER_STOP_LIMIT | catalogue |
| SYMBOL_ORDER_SL | Value: 16. Represents symbol order SL. | Not specified in reference | Constants | Exact adoption | SYMBOL_ORDER_SL | catalogue |
| SYMBOL_ORDER_TP | Value: 32. Represents symbol order TP. | Not specified in reference | Constants | Exact adoption | SYMBOL_ORDER_TP | catalogue |
| SYMBOL_ORDER_CLOSEBY | Value: 64. Represents symbol order closeby. | Not specified in reference | Constants | Exact adoption | SYMBOL_ORDER_CLOSEBY | catalogue |
| ENUM_SYMBOL_CALC_MODE | Defines the identifier set for symbol calc mode. | enum (int) | Enumerations | Exact adoption | ENUM_SYMBOL_CALC_MODE | catalogue |
| SYMBOL_CALC_MODE_FOREX | Selects calc mode forex in symbol calc mode. | ENUM_SYMBOL_CALC_MODE | Enumerations | Exact adoption | SYMBOL_CALC_MODE_FOREX | catalogue |
| SYMBOL_CALC_MODE_FOREX_NO_LEVERAGE | Selects calc mode forex no leverage in symbol calc mode. | ENUM_SYMBOL_CALC_MODE | Enumerations | Exact adoption | SYMBOL_CALC_MODE_FOREX_NO_LEVERAGE | catalogue |
| SYMBOL_CALC_MODE_FUTURES | Selects calc mode futures in symbol calc mode. | ENUM_SYMBOL_CALC_MODE | Enumerations | Exact adoption | SYMBOL_CALC_MODE_FUTURES | catalogue |
| SYMBOL_CALC_MODE_CFD | Selects calc mode cfd in symbol calc mode. | ENUM_SYMBOL_CALC_MODE | Enumerations | Exact adoption | SYMBOL_CALC_MODE_CFD | catalogue |
| SYMBOL_CALC_MODE_CFDINDEX | Selects calc mode cfdindex in symbol calc mode. | ENUM_SYMBOL_CALC_MODE | Enumerations | Exact adoption | SYMBOL_CALC_MODE_CFDINDEX | catalogue |
| SYMBOL_CALC_MODE_CFDLEVERAGE | Selects calc mode cfdleverage in symbol calc mode. | ENUM_SYMBOL_CALC_MODE | Enumerations | Exact adoption | SYMBOL_CALC_MODE_CFDLEVERAGE | catalogue |
| SYMBOL_CALC_MODE_EXCH_STOCKS | Selects calc mode exch stocks in symbol calc mode. | ENUM_SYMBOL_CALC_MODE | Enumerations | Exact adoption | SYMBOL_CALC_MODE_EXCH_STOCKS | catalogue |
| SYMBOL_CALC_MODE_EXCH_FUTURES | Selects calc mode exch futures in symbol calc mode. | ENUM_SYMBOL_CALC_MODE | Enumerations | Exact adoption | SYMBOL_CALC_MODE_EXCH_FUTURES | catalogue |
| SYMBOL_CALC_MODE_EXCH_FUTURES_FORTS | Selects calc mode exch futures forts in symbol calc mode. | ENUM_SYMBOL_CALC_MODE | Enumerations | Exact adoption | SYMBOL_CALC_MODE_EXCH_FUTURES_FORTS | catalogue |
| SYMBOL_CALC_MODE_EXCH_BONDS | Selects calc mode exch bonds in symbol calc mode. | ENUM_SYMBOL_CALC_MODE | Enumerations | Exact adoption | SYMBOL_CALC_MODE_EXCH_BONDS | catalogue |
| SYMBOL_CALC_MODE_EXCH_STOCKS_MOEX | Selects calc mode exch stocks moex in symbol calc mode. | ENUM_SYMBOL_CALC_MODE | Enumerations | Exact adoption | SYMBOL_CALC_MODE_EXCH_STOCKS_MOEX | catalogue |
| SYMBOL_CALC_MODE_EXCH_BONDS_MOEX | Selects calc mode exch bonds moex in symbol calc mode. | ENUM_SYMBOL_CALC_MODE | Enumerations | Exact adoption | SYMBOL_CALC_MODE_EXCH_BONDS_MOEX | catalogue |
| SYMBOL_CALC_MODE_SERV_COLLATERAL | Selects calc mode serv collateral in symbol calc mode. | ENUM_SYMBOL_CALC_MODE | Enumerations | Exact adoption | SYMBOL_CALC_MODE_SERV_COLLATERAL | catalogue |
| ENUM_SYMBOL_TRADE_MODE | Defines the identifier set for symbol trade mode. | enum (int) | Enumerations | Exact adoption | ENUM_SYMBOL_TRADE_MODE | catalogue |
| ENUM_SYMBOL_TRADE_EXECUTION | Defines the identifier set for symbol trade execution. | enum (int) | Enumerations | Exact adoption | ENUM_SYMBOL_TRADE_EXECUTION | catalogue |
| SYMBOL_TRADE_MODE_DISABLED | Selects trade mode disabled in symbol trade mode. | ENUM_SYMBOL_TRADE_MODE | Enumerations | Exact adoption | SYMBOL_TRADE_MODE_DISABLED | catalogue |
| SYMBOL_TRADE_MODE_LONGONLY | Selects trade mode longonly in symbol trade mode. | ENUM_SYMBOL_TRADE_MODE | Enumerations | Exact adoption | SYMBOL_TRADE_MODE_LONGONLY | catalogue |
| SYMBOL_TRADE_MODE_SHORTONLY | Selects trade mode shortonly in symbol trade mode. | ENUM_SYMBOL_TRADE_MODE | Enumerations | Exact adoption | SYMBOL_TRADE_MODE_SHORTONLY | catalogue |
| SYMBOL_TRADE_MODE_CLOSEONLY | Selects trade mode closeonly in symbol trade mode. | ENUM_SYMBOL_TRADE_MODE | Enumerations | Exact adoption | SYMBOL_TRADE_MODE_CLOSEONLY | catalogue |
| SYMBOL_TRADE_MODE_FULL | Selects trade mode full in symbol trade mode. | ENUM_SYMBOL_TRADE_MODE | Enumerations | Exact adoption | SYMBOL_TRADE_MODE_FULL | catalogue |
| SYMBOL_TRADE_EXECUTION_REQUEST | Selects trade execution request in symbol trade execution. | ENUM_SYMBOL_TRADE_EXECUTION | Enumerations | Exact adoption | SYMBOL_TRADE_EXECUTION_REQUEST | catalogue |
| SYMBOL_TRADE_EXECUTION_INSTANT | Selects trade execution instant in symbol trade execution. | ENUM_SYMBOL_TRADE_EXECUTION | Enumerations | Exact adoption | SYMBOL_TRADE_EXECUTION_INSTANT | catalogue |
| ENUM_SYMBOL_SWAP_MODE | Defines the identifier set for symbol swap mode. | enum (int) | Enumerations | Exact adoption | ENUM_SYMBOL_SWAP_MODE | catalogue |
| SYMBOL_TRADE_EXECUTION_MARKET | Selects trade execution market in symbol trade execution. | ENUM_SYMBOL_TRADE_EXECUTION | Enumerations | Exact adoption | SYMBOL_TRADE_EXECUTION_MARKET | catalogue |
| SYMBOL_TRADE_EXECUTION_EXCHANGE | Selects trade execution exchange in symbol trade execution. | ENUM_SYMBOL_TRADE_EXECUTION | Enumerations | Exact adoption | SYMBOL_TRADE_EXECUTION_EXCHANGE | catalogue |
| SYMBOL_SWAP_MODE_DISABLED | Selects swap mode disabled in symbol swap mode. | ENUM_SYMBOL_SWAP_MODE | Enumerations | Exact adoption | SYMBOL_SWAP_MODE_DISABLED | catalogue |
| SYMBOL_SWAP_MODE_POINTS | Selects swap mode points in symbol swap mode. | ENUM_SYMBOL_SWAP_MODE | Enumerations | Exact adoption | SYMBOL_SWAP_MODE_POINTS | catalogue |
| SYMBOL_SWAP_MODE_CURRENCY_SYMBOL | Selects swap mode currency symbol in symbol swap mode. | ENUM_SYMBOL_SWAP_MODE | Enumerations | Exact adoption | SYMBOL_SWAP_MODE_CURRENCY_SYMBOL | catalogue |
| SYMBOL_SWAP_MODE_CURRENCY_MARGIN | Selects swap mode currency margin in symbol swap mode. | ENUM_SYMBOL_SWAP_MODE | Enumerations | Exact adoption | SYMBOL_SWAP_MODE_CURRENCY_MARGIN | catalogue |
| SYMBOL_SWAP_MODE_CURRENCY_DEPOSIT | Selects swap mode currency deposit in symbol swap mode. | ENUM_SYMBOL_SWAP_MODE | Enumerations | Exact adoption | SYMBOL_SWAP_MODE_CURRENCY_DEPOSIT | catalogue |
| SYMBOL_SWAP_MODE_CURRENCY_PROFIT | Selects swap mode currency profit in symbol swap mode. | ENUM_SYMBOL_SWAP_MODE | Enumerations | Exact adoption | SYMBOL_SWAP_MODE_CURRENCY_PROFIT | catalogue |
| SYMBOL_SWAP_MODE_INTEREST_CURRENT | Selects swap mode interest current in symbol swap mode. | ENUM_SYMBOL_SWAP_MODE | Enumerations | Exact adoption | SYMBOL_SWAP_MODE_INTEREST_CURRENT | catalogue |
| SYMBOL_SWAP_MODE_INTEREST_OPEN | Selects swap mode interest open in symbol swap mode. | ENUM_SYMBOL_SWAP_MODE | Enumerations | Exact adoption | SYMBOL_SWAP_MODE_INTEREST_OPEN | catalogue |
| SYMBOL_SWAP_MODE_REOPEN_CURRENT | Selects swap mode reopen current in symbol swap mode. | ENUM_SYMBOL_SWAP_MODE | Enumerations | Exact adoption | SYMBOL_SWAP_MODE_REOPEN_CURRENT | catalogue |
| SYMBOL_SWAP_MODE_REOPEN_BID | Selects swap mode reopen bid in symbol swap mode. | ENUM_SYMBOL_SWAP_MODE | Enumerations | Exact adoption | SYMBOL_SWAP_MODE_REOPEN_BID | catalogue |
| ENUM_DAY_OF_WEEK | Defines the identifier set for day of week. | enum (int) | Enumerations | Exact adoption | ENUM_DAY_OF_WEEK | catalogue |
| ENUM_SYMBOL_OPTION_RIGHT | Defines the identifier set for symbol option right. | enum (int) | Enumerations | Exact adoption | ENUM_SYMBOL_OPTION_RIGHT | catalogue |
| ENUM_SYMBOL_OPTION_MODE | Defines the identifier set for symbol option mode. | enum (int) | Enumerations | Exact adoption | ENUM_SYMBOL_OPTION_MODE | catalogue |
| SUNDAY | Selects sunday in day of week. | ENUM_DAY_OF_WEEK | Enumerations | Exact adoption | SUNDAY | catalogue |
| MONDAY | Selects monday in day of week. | ENUM_DAY_OF_WEEK | Enumerations | Exact adoption | MONDAY | catalogue |
| TUESDAY | Selects tuesday in day of week. | ENUM_DAY_OF_WEEK | Enumerations | Exact adoption | TUESDAY | catalogue |
| WEDNESDAY | Selects wednesday in day of week. | ENUM_DAY_OF_WEEK | Enumerations | Exact adoption | WEDNESDAY | catalogue |
| THURSDAY | Selects thursday in day of week. | ENUM_DAY_OF_WEEK | Enumerations | Exact adoption | THURSDAY | catalogue |
| FRIDAY | Selects friday in day of week. | ENUM_DAY_OF_WEEK | Enumerations | Exact adoption | FRIDAY | catalogue |
| SATURDAY | Selects saturday in day of week. | ENUM_DAY_OF_WEEK | Enumerations | Exact adoption | SATURDAY | catalogue |
| SYMBOL_OPTION_RIGHT_CALL | Selects option right call in symbol option right. | ENUM_SYMBOL_OPTION_RIGHT | Enumerations | Exact adoption | SYMBOL_OPTION_RIGHT_CALL | catalogue |
| SYMBOL_OPTION_RIGHT_PUT | Selects option right put in symbol option right. | ENUM_SYMBOL_OPTION_RIGHT | Enumerations | Exact adoption | SYMBOL_OPTION_RIGHT_PUT | catalogue |
| SYMBOL_OPTION_MODE_EUROPEAN | Selects option mode european in symbol option mode. | ENUM_SYMBOL_OPTION_MODE | Enumerations | Exact adoption | SYMBOL_OPTION_MODE_EUROPEAN | catalogue |
| SYMBOL_OPTION_MODE_AMERICAN | Selects option mode american in symbol option mode. | ENUM_SYMBOL_OPTION_MODE | Enumerations | Exact adoption | SYMBOL_OPTION_MODE_AMERICAN | catalogue |
| ENUM_SYMBOL_SECTOR | Defines the identifier set for symbol sector. | enum (int) | Enumerations | Exact adoption | ENUM_SYMBOL_SECTOR | catalogue |
| ENUM_SYMBOL_INDUSTRY | Defines the identifier set for symbol industry. | enum (int) | Enumerations | Exact adoption | ENUM_SYMBOL_INDUSTRY | catalogue |
| SECTOR_UNDEFINED | Selects undefined in symbol sector. | ENUM_SYMBOL_SECTOR | Enumerations | Exact adoption | SECTOR_UNDEFINED | catalogue |
| SECTOR_BASIC_MATERIALS | Selects basic materials in symbol sector. | ENUM_SYMBOL_SECTOR | Enumerations | Exact adoption | SECTOR_BASIC_MATERIALS | catalogue |
| SECTOR_COMMUNICATION_SERVICES | Selects communication services in symbol sector. | ENUM_SYMBOL_SECTOR | Enumerations | Exact adoption | SECTOR_COMMUNICATION_SERVICES | catalogue |
| SECTOR_CONSUMER_CYCLICAL | Selects consumer cyclical in symbol sector. | ENUM_SYMBOL_SECTOR | Enumerations | Exact adoption | SECTOR_CONSUMER_CYCLICAL | catalogue |
| SECTOR_CONSUMER_DEFENSIVE | Selects consumer defensive in symbol sector. | ENUM_SYMBOL_SECTOR | Enumerations | Exact adoption | SECTOR_CONSUMER_DEFENSIVE | catalogue |
| SECTOR_CURRENCY | Selects currency in symbol sector. | ENUM_SYMBOL_SECTOR | Enumerations | Exact adoption | SECTOR_CURRENCY | catalogue |
| SECTOR_CURRENCY_CRYPTO | Selects currency crypto in symbol sector. | ENUM_SYMBOL_SECTOR | Enumerations | Exact adoption | SECTOR_CURRENCY_CRYPTO | catalogue |
| SECTOR_ENERGY | Selects energy in symbol sector. | ENUM_SYMBOL_SECTOR | Enumerations | Exact adoption | SECTOR_ENERGY | catalogue |
| SECTOR_FINANCIAL | Selects financial in symbol sector. | ENUM_SYMBOL_SECTOR | Enumerations | Exact adoption | SECTOR_FINANCIAL | catalogue |
| SECTOR_HEALTHCARE | Selects healthcare in symbol sector. | ENUM_SYMBOL_SECTOR | Enumerations | Exact adoption | SECTOR_HEALTHCARE | catalogue |
| SECTOR_INDUSTRIALS | Selects industrials in symbol sector. | ENUM_SYMBOL_SECTOR | Enumerations | Exact adoption | SECTOR_INDUSTRIALS | catalogue |
| SECTOR_REAL_ESTATE | Selects real estate in symbol sector. | ENUM_SYMBOL_SECTOR | Enumerations | Exact adoption | SECTOR_REAL_ESTATE | catalogue |
| SECTOR_TECHNOLOGY | Selects technology in symbol sector. | ENUM_SYMBOL_SECTOR | Enumerations | Exact adoption | SECTOR_TECHNOLOGY | catalogue |
| SECTOR_UTILITIES | Selects utilities in symbol sector. | ENUM_SYMBOL_SECTOR | Enumerations | Exact adoption | SECTOR_UTILITIES | catalogue |
| INDUSTRY_UNDEFINED | Selects undefined in symbol industry. | ENUM_SYMBOL_INDUSTRY | Enumerations | Exact adoption | INDUSTRY_UNDEFINED | catalogue |
| INDUSTRY_AGRICULTURAL_INPUTS | Selects agricultural inputs in symbol industry. | ENUM_SYMBOL_INDUSTRY | Enumerations | Exact adoption | INDUSTRY_AGRICULTURAL_INPUTS | catalogue |
| INDUSTRY_ALUMINIUM | Selects aluminium in symbol industry. | ENUM_SYMBOL_INDUSTRY | Enumerations | Exact adoption | INDUSTRY_ALUMINIUM | catalogue |
| INDUSTRY_BUILDING_MATERIALS | Selects building materials in symbol industry. | ENUM_SYMBOL_INDUSTRY | Enumerations | Exact adoption | INDUSTRY_BUILDING_MATERIALS | catalogue |
| INDUSTRY_CHEMICALS | Selects chemicals in symbol industry. | ENUM_SYMBOL_INDUSTRY | Enumerations | Exact adoption | INDUSTRY_CHEMICALS | catalogue |
| INDUSTRY_COKING_COAL | Selects coking coal in symbol industry. | ENUM_SYMBOL_INDUSTRY | Enumerations | Exact adoption | INDUSTRY_COKING_COAL | catalogue |
| INDUSTRY_COPPER | Selects copper in symbol industry. | ENUM_SYMBOL_INDUSTRY | Enumerations | Exact adoption | INDUSTRY_COPPER | catalogue |
| INDUSTRY_GOLD | Selects gold in symbol industry. | ENUM_SYMBOL_INDUSTRY | Enumerations | Exact adoption | INDUSTRY_GOLD | catalogue |
| INDUSTRY_LUMBER_WOOD | Selects lumber wood in symbol industry. | ENUM_SYMBOL_INDUSTRY | Enumerations | Exact adoption | INDUSTRY_LUMBER_WOOD | catalogue |
| INDUSTRY_INDUSTRIAL_METALS | Selects industrial metals in symbol industry. | ENUM_SYMBOL_INDUSTRY | Enumerations | Exact adoption | INDUSTRY_INDUSTRIAL_METALS | catalogue |
| INDUSTRY_PRECIOUS_METALS | Selects precious metals in symbol industry. | ENUM_SYMBOL_INDUSTRY | Enumerations | Exact adoption | INDUSTRY_PRECIOUS_METALS | catalogue |
| INDUSTRY_PAPER | Selects paper in symbol industry. | ENUM_SYMBOL_INDUSTRY | Enumerations | Exact adoption | INDUSTRY_PAPER | catalogue |
| INDUSTRY_SILVER | Selects silver in symbol industry. | ENUM_SYMBOL_INDUSTRY | Enumerations | Exact adoption | INDUSTRY_SILVER | catalogue |
| INDUSTRY_SPECIALTY_CHEMICALS | Selects specialty chemicals in symbol industry. | ENUM_SYMBOL_INDUSTRY | Enumerations | Exact adoption | INDUSTRY_SPECIALTY_CHEMICALS | catalogue |
| INDUSTRY_STEEL | Selects steel in symbol industry. | ENUM_SYMBOL_INDUSTRY | Enumerations | Exact adoption | INDUSTRY_STEEL | catalogue |
| INDUSTRY_ADVERTISING | Selects advertising in symbol industry. | ENUM_SYMBOL_INDUSTRY | Enumerations | Exact adoption | INDUSTRY_ADVERTISING | catalogue |
| INDUSTRY_BROADCASTING | Selects broadcasting in symbol industry. | ENUM_SYMBOL_INDUSTRY | Enumerations | Exact adoption | INDUSTRY_BROADCASTING | catalogue |
| INDUSTRY_GAMING_MULTIMEDIA | Selects gaming multimedia in symbol industry. | ENUM_SYMBOL_INDUSTRY | Enumerations | Exact adoption | INDUSTRY_GAMING_MULTIMEDIA | catalogue |
| INDUSTRY_ENTERTAINMENT | Selects entertainment in symbol industry. | ENUM_SYMBOL_INDUSTRY | Enumerations | Exact adoption | INDUSTRY_ENTERTAINMENT | catalogue |
| INDUSTRY_INTERNET_CONTENT | Selects internet content in symbol industry. | ENUM_SYMBOL_INDUSTRY | Enumerations | Exact adoption | INDUSTRY_INTERNET_CONTENT | catalogue |
| INDUSTRY_PUBLISHING | Selects publishing in symbol industry. | ENUM_SYMBOL_INDUSTRY | Enumerations | Exact adoption | INDUSTRY_PUBLISHING | catalogue |
| INDUSTRY_TELECOM | Selects telecom in symbol industry. | ENUM_SYMBOL_INDUSTRY | Enumerations | Exact adoption | INDUSTRY_TELECOM | catalogue |
| INDUSTRY_APPAREL_MANUFACTURING | Selects apparel manufacturing in symbol industry. | ENUM_SYMBOL_INDUSTRY | Enumerations | Exact adoption | INDUSTRY_APPAREL_MANUFACTURING | catalogue |
| INDUSTRY_APPAREL_RETAIL | Selects apparel retail in symbol industry. | ENUM_SYMBOL_INDUSTRY | Enumerations | Exact adoption | INDUSTRY_APPAREL_RETAIL | catalogue |
| INDUSTRY_AUTO_MANUFACTURERS | Selects auto manufacturers in symbol industry. | ENUM_SYMBOL_INDUSTRY | Enumerations | Exact adoption | INDUSTRY_AUTO_MANUFACTURERS | catalogue |
| INDUSTRY_AUTO_PARTS | Selects auto parts in symbol industry. | ENUM_SYMBOL_INDUSTRY | Enumerations | Exact adoption | INDUSTRY_AUTO_PARTS | catalogue |
| INDUSTRY_AUTO_DEALERSHIP | Selects auto dealership in symbol industry. | ENUM_SYMBOL_INDUSTRY | Enumerations | Exact adoption | INDUSTRY_AUTO_DEALERSHIP | catalogue |
| INDUSTRY_DEPARTMENT_STORES | Selects department stores in symbol industry. | ENUM_SYMBOL_INDUSTRY | Enumerations | Exact adoption | INDUSTRY_DEPARTMENT_STORES | catalogue |
| INDUSTRY_FOOTWEAR_ACCESSORIES | Selects footwear accessories in symbol industry. | ENUM_SYMBOL_INDUSTRY | Enumerations | Exact adoption | INDUSTRY_FOOTWEAR_ACCESSORIES | catalogue |
| INDUSTRY_FURNISHINGS | Selects furnishings in symbol industry. | ENUM_SYMBOL_INDUSTRY | Enumerations | Exact adoption | INDUSTRY_FURNISHINGS | catalogue |
| INDUSTRY_GAMBLING | Selects gambling in symbol industry. | ENUM_SYMBOL_INDUSTRY | Enumerations | Exact adoption | INDUSTRY_GAMBLING | catalogue |
| INDUSTRY_HOME_IMPROV_RETAIL | Selects home improv retail in symbol industry. | ENUM_SYMBOL_INDUSTRY | Enumerations | Exact adoption | INDUSTRY_HOME_IMPROV_RETAIL | catalogue |
| INDUSTRY_INTERNET_RETAIL | Selects internet retail in symbol industry. | ENUM_SYMBOL_INDUSTRY | Enumerations | Exact adoption | INDUSTRY_INTERNET_RETAIL | catalogue |
| INDUSTRY_LEISURE | Selects leisure in symbol industry. | ENUM_SYMBOL_INDUSTRY | Enumerations | Exact adoption | INDUSTRY_LEISURE | catalogue |
| INDUSTRY_LODGING | Selects lodging in symbol industry. | ENUM_SYMBOL_INDUSTRY | Enumerations | Exact adoption | INDUSTRY_LODGING | catalogue |
| INDUSTRY_LUXURY_GOODS | Selects luxury goods in symbol industry. | ENUM_SYMBOL_INDUSTRY | Enumerations | Exact adoption | INDUSTRY_LUXURY_GOODS | catalogue |
| INDUSTRY_PACKAGING_CONTAINERS | Selects packaging containers in symbol industry. | ENUM_SYMBOL_INDUSTRY | Enumerations | Exact adoption | INDUSTRY_PACKAGING_CONTAINERS | catalogue |
| INDUSTRY_PERSONAL_SERVICES | Selects personal services in symbol industry. | ENUM_SYMBOL_INDUSTRY | Enumerations | Exact adoption | INDUSTRY_PERSONAL_SERVICES | catalogue |
| INDUSTRY_RECREATIONAL_VEHICLES | Selects recreational vehicles in symbol industry. | ENUM_SYMBOL_INDUSTRY | Enumerations | Exact adoption | INDUSTRY_RECREATIONAL_VEHICLES | catalogue |
| INDUSTRY_RESIDENT_CONSTRUCTION | Selects resident construction in symbol industry. | ENUM_SYMBOL_INDUSTRY | Enumerations | Exact adoption | INDUSTRY_RESIDENT_CONSTRUCTION | catalogue |
| INDUSTRY_RESORTS_CASINOS | Selects resorts casinos in symbol industry. | ENUM_SYMBOL_INDUSTRY | Enumerations | Exact adoption | INDUSTRY_RESORTS_CASINOS | catalogue |
| INDUSTRY_RESTAURANTS | Selects restaurants in symbol industry. | ENUM_SYMBOL_INDUSTRY | Enumerations | Exact adoption | INDUSTRY_RESTAURANTS | catalogue |
| INDUSTRY_SPECIALTY_RETAIL | Selects specialty retail in symbol industry. | ENUM_SYMBOL_INDUSTRY | Enumerations | Exact adoption | INDUSTRY_SPECIALTY_RETAIL | catalogue |
| INDUSTRY_TEXTILE_MANUFACTURING | Selects textile manufacturing in symbol industry. | ENUM_SYMBOL_INDUSTRY | Enumerations | Exact adoption | INDUSTRY_TEXTILE_MANUFACTURING | catalogue |
| INDUSTRY_TRAVEL_SERVICES | Selects travel services in symbol industry. | ENUM_SYMBOL_INDUSTRY | Enumerations | Exact adoption | INDUSTRY_TRAVEL_SERVICES | catalogue |
| INDUSTRY_BEVERAGES_BREWERS | Selects beverages brewers in symbol industry. | ENUM_SYMBOL_INDUSTRY | Enumerations | Exact adoption | INDUSTRY_BEVERAGES_BREWERS | catalogue |
| INDUSTRY_BEVERAGES_NON_ALCO | Selects beverages non alco in symbol industry. | ENUM_SYMBOL_INDUSTRY | Enumerations | Exact adoption | INDUSTRY_BEVERAGES_NON_ALCO | catalogue |
| INDUSTRY_BEVERAGES_WINERIES | Selects beverages wineries in symbol industry. | ENUM_SYMBOL_INDUSTRY | Enumerations | Exact adoption | INDUSTRY_BEVERAGES_WINERIES | catalogue |
| INDUSTRY_CONFECTIONERS | Selects confectioners in symbol industry. | ENUM_SYMBOL_INDUSTRY | Enumerations | Exact adoption | INDUSTRY_CONFECTIONERS | catalogue |
| INDUSTRY_DISCOUNT_STORES | Selects discount stores in symbol industry. | ENUM_SYMBOL_INDUSTRY | Enumerations | Exact adoption | INDUSTRY_DISCOUNT_STORES | catalogue |
| INDUSTRY_EDUCATION_TRAINIG | Selects education trainig in symbol industry. | ENUM_SYMBOL_INDUSTRY | Enumerations | Exact adoption | INDUSTRY_EDUCATION_TRAINIG | catalogue |
| INDUSTRY_FARM_PRODUCTS | Selects farm products in symbol industry. | ENUM_SYMBOL_INDUSTRY | Enumerations | Exact adoption | INDUSTRY_FARM_PRODUCTS | catalogue |
| INDUSTRY_FOOD_DISTRIBUTION | Selects food distribution in symbol industry. | ENUM_SYMBOL_INDUSTRY | Enumerations | Exact adoption | INDUSTRY_FOOD_DISTRIBUTION | catalogue |
| INDUSTRY_GROCERY_STORES | Selects grocery stores in symbol industry. | ENUM_SYMBOL_INDUSTRY | Enumerations | Exact adoption | INDUSTRY_GROCERY_STORES | catalogue |
| INDUSTRY_HOUSEHOLD_PRODUCTS | Selects household products in symbol industry. | ENUM_SYMBOL_INDUSTRY | Enumerations | Exact adoption | INDUSTRY_HOUSEHOLD_PRODUCTS | catalogue |
| INDUSTRY_PACKAGED_FOODS | Selects packaged foods in symbol industry. | ENUM_SYMBOL_INDUSTRY | Enumerations | Exact adoption | INDUSTRY_PACKAGED_FOODS | catalogue |
| INDUSTRY_TOBACCO | Selects tobacco in symbol industry. | ENUM_SYMBOL_INDUSTRY | Enumerations | Exact adoption | INDUSTRY_TOBACCO | catalogue |
| INDUSTRY_OIL_GAS_DRILLING | Selects oil gas drilling in symbol industry. | ENUM_SYMBOL_INDUSTRY | Enumerations | Exact adoption | INDUSTRY_OIL_GAS_DRILLING | catalogue |
| INDUSTRY_OIL_GAS_EP | Selects oil gas ep in symbol industry. | ENUM_SYMBOL_INDUSTRY | Enumerations | Exact adoption | INDUSTRY_OIL_GAS_EP | catalogue |
| INDUSTRY_OIL_GAS_EQUIPMENT | Selects oil gas equipment in symbol industry. | ENUM_SYMBOL_INDUSTRY | Enumerations | Exact adoption | INDUSTRY_OIL_GAS_EQUIPMENT | catalogue |
| INDUSTRY_OIL_GAS_INTEGRATED | Selects oil gas integrated in symbol industry. | ENUM_SYMBOL_INDUSTRY | Enumerations | Exact adoption | INDUSTRY_OIL_GAS_INTEGRATED | catalogue |
| INDUSTRY_OIL_GAS_MIDSTREAM | Selects oil gas midstream in symbol industry. | ENUM_SYMBOL_INDUSTRY | Enumerations | Exact adoption | INDUSTRY_OIL_GAS_MIDSTREAM | catalogue |
| INDUSTRY_OIL_GAS_REFINING | Selects oil gas refining in symbol industry. | ENUM_SYMBOL_INDUSTRY | Enumerations | Exact adoption | INDUSTRY_OIL_GAS_REFINING | catalogue |
| INDUSTRY_THERMAL_COAL | Selects thermal coal in symbol industry. | ENUM_SYMBOL_INDUSTRY | Enumerations | Exact adoption | INDUSTRY_THERMAL_COAL | catalogue |
| INDUSTRY_URANIUM | Selects uranium in symbol industry. | ENUM_SYMBOL_INDUSTRY | Enumerations | Exact adoption | INDUSTRY_URANIUM | catalogue |
| INDUSTRY_EXCHANGE_TRADED_FUND | Selects exchange traded fund in symbol industry. | ENUM_SYMBOL_INDUSTRY | Enumerations | Exact adoption | INDUSTRY_EXCHANGE_TRADED_FUND | catalogue |
| INDUSTRY_ASSETS_MANAGEMENT | Selects assets management in symbol industry. | ENUM_SYMBOL_INDUSTRY | Enumerations | Exact adoption | INDUSTRY_ASSETS_MANAGEMENT | catalogue |
| INDUSTRY_BANKS_DIVERSIFIED | Selects banks diversified in symbol industry. | ENUM_SYMBOL_INDUSTRY | Enumerations | Exact adoption | INDUSTRY_BANKS_DIVERSIFIED | catalogue |
| INDUSTRY_BANKS_REGIONAL | Selects banks regional in symbol industry. | ENUM_SYMBOL_INDUSTRY | Enumerations | Exact adoption | INDUSTRY_BANKS_REGIONAL | catalogue |
| INDUSTRY_CAPITAL_MARKETS | Selects capital markets in symbol industry. | ENUM_SYMBOL_INDUSTRY | Enumerations | Exact adoption | INDUSTRY_CAPITAL_MARKETS | catalogue |
| INDUSTRY_CLOSE_END_FUND_DEBT | Selects close end fund debt in symbol industry. | ENUM_SYMBOL_INDUSTRY | Enumerations | Exact adoption | INDUSTRY_CLOSE_END_FUND_DEBT | catalogue |
| INDUSTRY_CLOSE_END_FUND_EQUITY | Selects close end fund equity in symbol industry. | ENUM_SYMBOL_INDUSTRY | Enumerations | Exact adoption | INDUSTRY_CLOSE_END_FUND_EQUITY | catalogue |
| INDUSTRY_CLOSE_END_FUND_FOREIGN | Selects close end fund foreign in symbol industry. | ENUM_SYMBOL_INDUSTRY | Enumerations | Exact adoption | INDUSTRY_CLOSE_END_FUND_FOREIGN | catalogue |
| INDUSTRY_CREDIT_SERVICES | Selects credit services in symbol industry. | ENUM_SYMBOL_INDUSTRY | Enumerations | Exact adoption | INDUSTRY_CREDIT_SERVICES | catalogue |
| INDUSTRY_FINANCIAL_CONGLOMERATE | Selects financial conglomerate in symbol industry. | ENUM_SYMBOL_INDUSTRY | Enumerations | Exact adoption | INDUSTRY_FINANCIAL_CONGLOMERATE | catalogue |
| INDUSTRY_FINANCIAL_DATA_EXCHANGE | Selects financial data exchange in symbol industry. | ENUM_SYMBOL_INDUSTRY | Enumerations | Exact adoption | INDUSTRY_FINANCIAL_DATA_EXCHANGE | catalogue |
| INDUSTRY_INSURANCE_BROKERS | Selects insurance brokers in symbol industry. | ENUM_SYMBOL_INDUSTRY | Enumerations | Exact adoption | INDUSTRY_INSURANCE_BROKERS | catalogue |
| INDUSTRY_INSURANCE_DIVERSIFIED | Selects insurance diversified in symbol industry. | ENUM_SYMBOL_INDUSTRY | Enumerations | Exact adoption | INDUSTRY_INSURANCE_DIVERSIFIED | catalogue |
| INDUSTRY_INSURANCE_LIFE | Selects insurance life in symbol industry. | ENUM_SYMBOL_INDUSTRY | Enumerations | Exact adoption | INDUSTRY_INSURANCE_LIFE | catalogue |
| INDUSTRY_INSURANCE_PROPERTY | Selects insurance property in symbol industry. | ENUM_SYMBOL_INDUSTRY | Enumerations | Exact adoption | INDUSTRY_INSURANCE_PROPERTY | catalogue |
| INDUSTRY_INSURANCE_REINSURANCE | Selects insurance reinsurance in symbol industry. | ENUM_SYMBOL_INDUSTRY | Enumerations | Exact adoption | INDUSTRY_INSURANCE_REINSURANCE | catalogue |
| INDUSTRY_INSURANCE_SPECIALTY | Selects insurance specialty in symbol industry. | ENUM_SYMBOL_INDUSTRY | Enumerations | Exact adoption | INDUSTRY_INSURANCE_SPECIALTY | catalogue |
| INDUSTRY_MORTGAGE_FINANCE | Selects mortgage finance in symbol industry. | ENUM_SYMBOL_INDUSTRY | Enumerations | Exact adoption | INDUSTRY_MORTGAGE_FINANCE | catalogue |
| INDUSTRY_SHELL_COMPANIES | Selects shell companies in symbol industry. | ENUM_SYMBOL_INDUSTRY | Enumerations | Exact adoption | INDUSTRY_SHELL_COMPANIES | catalogue |
| INDUSTRY_BIOTECHNOLOGY | Selects biotechnology in symbol industry. | ENUM_SYMBOL_INDUSTRY | Enumerations | Exact adoption | INDUSTRY_BIOTECHNOLOGY | catalogue |
| INDUSTRY_DIAGNOSTICS_RESEARCH | Selects diagnostics research in symbol industry. | ENUM_SYMBOL_INDUSTRY | Enumerations | Exact adoption | INDUSTRY_DIAGNOSTICS_RESEARCH | catalogue |
| INDUSTRY_DRUGS_MANUFACTURERS | Selects drugs manufacturers in symbol industry. | ENUM_SYMBOL_INDUSTRY | Enumerations | Exact adoption | INDUSTRY_DRUGS_MANUFACTURERS | catalogue |
| INDUSTRY_DRUGS_MANUFACTURERS_SPEC | Selects drugs manufacturers spec in symbol industry. | ENUM_SYMBOL_INDUSTRY | Enumerations | Exact adoption | INDUSTRY_DRUGS_MANUFACTURERS_SPEC | catalogue |
| INDUSTRY_HEALTHCARE_PLANS | Selects healthcare plans in symbol industry. | ENUM_SYMBOL_INDUSTRY | Enumerations | Exact adoption | INDUSTRY_HEALTHCARE_PLANS | catalogue |
| INDUSTRY_HEALTH_INFORMATION | Selects health information in symbol industry. | ENUM_SYMBOL_INDUSTRY | Enumerations | Exact adoption | INDUSTRY_HEALTH_INFORMATION | catalogue |
| INDUSTRY_MEDICAL_FACILITIES | Selects medical facilities in symbol industry. | ENUM_SYMBOL_INDUSTRY | Enumerations | Exact adoption | INDUSTRY_MEDICAL_FACILITIES | catalogue |
| INDUSTRY_MEDICAL_DEVICES | Selects medical devices in symbol industry. | ENUM_SYMBOL_INDUSTRY | Enumerations | Exact adoption | INDUSTRY_MEDICAL_DEVICES | catalogue |
| INDUSTRY_MEDICAL_DISTRIBUTION | Selects medical distribution in symbol industry. | ENUM_SYMBOL_INDUSTRY | Enumerations | Exact adoption | INDUSTRY_MEDICAL_DISTRIBUTION | catalogue |
| INDUSTRY_MEDICAL_INSTRUMENTS | Selects medical instruments in symbol industry. | ENUM_SYMBOL_INDUSTRY | Enumerations | Exact adoption | INDUSTRY_MEDICAL_INSTRUMENTS | catalogue |
| INDUSTRY_PHARM_RETAILERS | Selects pharm retailers in symbol industry. | ENUM_SYMBOL_INDUSTRY | Enumerations | Exact adoption | INDUSTRY_PHARM_RETAILERS | catalogue |
| INDUSTRY_AEROSPACE_DEFENSE | Selects aerospace defense in symbol industry. | ENUM_SYMBOL_INDUSTRY | Enumerations | Exact adoption | INDUSTRY_AEROSPACE_DEFENSE | catalogue |
| INDUSTRY_AIRLINES | Selects airlines in symbol industry. | ENUM_SYMBOL_INDUSTRY | Enumerations | Exact adoption | INDUSTRY_AIRLINES | catalogue |
| INDUSTRY_AIRPORTS_SERVICES | Selects airports services in symbol industry. | ENUM_SYMBOL_INDUSTRY | Enumerations | Exact adoption | INDUSTRY_AIRPORTS_SERVICES | catalogue |
| INDUSTRY_BUILDING_PRODUCTS | Selects building products in symbol industry. | ENUM_SYMBOL_INDUSTRY | Enumerations | Exact adoption | INDUSTRY_BUILDING_PRODUCTS | catalogue |
| INDUSTRY_BUSINESS_EQUIPMENT | Selects business equipment in symbol industry. | ENUM_SYMBOL_INDUSTRY | Enumerations | Exact adoption | INDUSTRY_BUSINESS_EQUIPMENT | catalogue |
| INDUSTRY_CONGLOMERATES | Selects conglomerates in symbol industry. | ENUM_SYMBOL_INDUSTRY | Enumerations | Exact adoption | INDUSTRY_CONGLOMERATES | catalogue |
| INDUSTRY_CONSULTING_SERVICES | Selects consulting services in symbol industry. | ENUM_SYMBOL_INDUSTRY | Enumerations | Exact adoption | INDUSTRY_CONSULTING_SERVICES | catalogue |
| INDUSTRY_ELECTRICAL_EQUIPMENT | Selects electrical equipment in symbol industry. | ENUM_SYMBOL_INDUSTRY | Enumerations | Exact adoption | INDUSTRY_ELECTRICAL_EQUIPMENT | catalogue |
| INDUSTRY_ENGINEERING_CONSTRUCTION | Selects engineering construction in symbol industry. | ENUM_SYMBOL_INDUSTRY | Enumerations | Exact adoption | INDUSTRY_ENGINEERING_CONSTRUCTION | catalogue |
| INDUSTRY_FARM_HEAVY_MACHINERY | Selects farm heavy machinery in symbol industry. | ENUM_SYMBOL_INDUSTRY | Enumerations | Exact adoption | INDUSTRY_FARM_HEAVY_MACHINERY | catalogue |
| INDUSTRY_INDUSTRIAL_DISTRIBUTION | Selects industrial distribution in symbol industry. | ENUM_SYMBOL_INDUSTRY | Enumerations | Exact adoption | INDUSTRY_INDUSTRIAL_DISTRIBUTION | catalogue |
| INDUSTRY_INFRASTRUCTURE_OPERATIONS | Selects infrastructure operations in symbol industry. | ENUM_SYMBOL_INDUSTRY | Enumerations | Exact adoption | INDUSTRY_INFRASTRUCTURE_OPERATIONS | catalogue |
| INDUSTRY_FREIGHT_LOGISTICS | Selects freight logistics in symbol industry. | ENUM_SYMBOL_INDUSTRY | Enumerations | Exact adoption | INDUSTRY_FREIGHT_LOGISTICS | catalogue |
| INDUSTRY_MARINE_SHIPPING | Selects marine shipping in symbol industry. | ENUM_SYMBOL_INDUSTRY | Enumerations | Exact adoption | INDUSTRY_MARINE_SHIPPING | catalogue |
| INDUSTRY_METAL_FABRICATION | Selects metal fabrication in symbol industry. | ENUM_SYMBOL_INDUSTRY | Enumerations | Exact adoption | INDUSTRY_METAL_FABRICATION | catalogue |
| INDUSTRY_POLLUTION_CONTROL | Selects pollution control in symbol industry. | ENUM_SYMBOL_INDUSTRY | Enumerations | Exact adoption | INDUSTRY_POLLUTION_CONTROL | catalogue |
| INDUSTRY_RAILROADS | Selects railroads in symbol industry. | ENUM_SYMBOL_INDUSTRY | Enumerations | Exact adoption | INDUSTRY_RAILROADS | catalogue |
| INDUSTRY_RENTAL_LEASING | Selects rental leasing in symbol industry. | ENUM_SYMBOL_INDUSTRY | Enumerations | Exact adoption | INDUSTRY_RENTAL_LEASING | catalogue |
| INDUSTRY_SECURITY_PROTECTION | Selects security protection in symbol industry. | ENUM_SYMBOL_INDUSTRY | Enumerations | Exact adoption | INDUSTRY_SECURITY_PROTECTION | catalogue |
| INDUSTRY_SPEALITY_BUSINESS_SERVICES | Selects speality business services in symbol industry. | ENUM_SYMBOL_INDUSTRY | Enumerations | Exact adoption | INDUSTRY_SPEALITY_BUSINESS_SERVICES | catalogue |
| INDUSTRY_SPEALITY_MACHINERY | Selects speality machinery in symbol industry. | ENUM_SYMBOL_INDUSTRY | Enumerations | Exact adoption | INDUSTRY_SPEALITY_MACHINERY | catalogue |
| INDUSTRY_STUFFING_EMPLOYMENT | Selects stuffing employment in symbol industry. | ENUM_SYMBOL_INDUSTRY | Enumerations | Exact adoption | INDUSTRY_STUFFING_EMPLOYMENT | catalogue |
| INDUSTRY_TOOLS_ACCESSORIES | Selects tools accessories in symbol industry. | ENUM_SYMBOL_INDUSTRY | Enumerations | Exact adoption | INDUSTRY_TOOLS_ACCESSORIES | catalogue |
| INDUSTRY_TRUCKING | Selects trucking in symbol industry. | ENUM_SYMBOL_INDUSTRY | Enumerations | Exact adoption | INDUSTRY_TRUCKING | catalogue |
| INDUSTRY_WASTE_MANAGEMENT | Selects waste management in symbol industry. | ENUM_SYMBOL_INDUSTRY | Enumerations | Exact adoption | INDUSTRY_WASTE_MANAGEMENT | catalogue |
| INDUSTRY_REAL_ESTATE_DEVELOPMENT | Selects real estate development in symbol industry. | ENUM_SYMBOL_INDUSTRY | Enumerations | Exact adoption | INDUSTRY_REAL_ESTATE_DEVELOPMENT | catalogue |
| INDUSTRY_REAL_ESTATE_DIVERSIFIED | Selects real estate diversified in symbol industry. | ENUM_SYMBOL_INDUSTRY | Enumerations | Exact adoption | INDUSTRY_REAL_ESTATE_DIVERSIFIED | catalogue |
| INDUSTRY_REAL_ESTATE_SERVICES | Selects real estate services in symbol industry. | ENUM_SYMBOL_INDUSTRY | Enumerations | Exact adoption | INDUSTRY_REAL_ESTATE_SERVICES | catalogue |
| INDUSTRY_REIT_DIVERSIFIED | Selects reit diversified in symbol industry. | ENUM_SYMBOL_INDUSTRY | Enumerations | Exact adoption | INDUSTRY_REIT_DIVERSIFIED | catalogue |
| INDUSTRY_REIT_HEALTCARE | Selects reit healtcare in symbol industry. | ENUM_SYMBOL_INDUSTRY | Enumerations | Exact adoption | INDUSTRY_REIT_HEALTCARE | catalogue |
| INDUSTRY_REIT_HOTEL_MOTEL | Selects reit hotel motel in symbol industry. | ENUM_SYMBOL_INDUSTRY | Enumerations | Exact adoption | INDUSTRY_REIT_HOTEL_MOTEL | catalogue |
| INDUSTRY_REIT_INDUSTRIAL | Selects reit industrial in symbol industry. | ENUM_SYMBOL_INDUSTRY | Enumerations | Exact adoption | INDUSTRY_REIT_INDUSTRIAL | catalogue |
| INDUSTRY_REIT_MORTAGE | Selects reit mortage in symbol industry. | ENUM_SYMBOL_INDUSTRY | Enumerations | Exact adoption | INDUSTRY_REIT_MORTAGE | catalogue |
| INDUSTRY_REIT_OFFICE | Selects reit office in symbol industry. | ENUM_SYMBOL_INDUSTRY | Enumerations | Exact adoption | INDUSTRY_REIT_OFFICE | catalogue |
| INDUSTRY_REIT_RESIDENTAL | Selects reit residental in symbol industry. | ENUM_SYMBOL_INDUSTRY | Enumerations | Exact adoption | INDUSTRY_REIT_RESIDENTAL | catalogue |
| INDUSTRY_REIT_RETAIL | Selects reit retail in symbol industry. | ENUM_SYMBOL_INDUSTRY | Enumerations | Exact adoption | INDUSTRY_REIT_RETAIL | catalogue |
| INDUSTRY_REIT_SPECIALITY | Selects reit speciality in symbol industry. | ENUM_SYMBOL_INDUSTRY | Enumerations | Exact adoption | INDUSTRY_REIT_SPECIALITY | catalogue |
| INDUSTRY_COMMUNICATION_EQUIPMENT | Selects communication equipment in symbol industry. | ENUM_SYMBOL_INDUSTRY | Enumerations | Exact adoption | INDUSTRY_COMMUNICATION_EQUIPMENT | catalogue |
| INDUSTRY_COMPUTER_HARDWARE | Selects computer hardware in symbol industry. | ENUM_SYMBOL_INDUSTRY | Enumerations | Exact adoption | INDUSTRY_COMPUTER_HARDWARE | catalogue |
| INDUSTRY_CONSUMER_ELECTRONICS | Selects consumer electronics in symbol industry. | ENUM_SYMBOL_INDUSTRY | Enumerations | Exact adoption | INDUSTRY_CONSUMER_ELECTRONICS | catalogue |
| INDUSTRY_ELECTRONIC_COMPONENTS | Selects electronic components in symbol industry. | ENUM_SYMBOL_INDUSTRY | Enumerations | Exact adoption | INDUSTRY_ELECTRONIC_COMPONENTS | catalogue |
| INDUSTRY_ELECTRONIC_DISTRIBUTION | Selects electronic distribution in symbol industry. | ENUM_SYMBOL_INDUSTRY | Enumerations | Exact adoption | INDUSTRY_ELECTRONIC_DISTRIBUTION | catalogue |
| INDUSTRY_IT_SERVICES | Selects it services in symbol industry. | ENUM_SYMBOL_INDUSTRY | Enumerations | Exact adoption | INDUSTRY_IT_SERVICES | catalogue |
| INDUSTRY_SCIENTIFIC_INSTRUMENTS | Selects scientific instruments in symbol industry. | ENUM_SYMBOL_INDUSTRY | Enumerations | Exact adoption | INDUSTRY_SCIENTIFIC_INSTRUMENTS | catalogue |
| INDUSTRY_SEMICONDUCTOR_EQUIPMENT | Selects semiconductor equipment in symbol industry. | ENUM_SYMBOL_INDUSTRY | Enumerations | Exact adoption | INDUSTRY_SEMICONDUCTOR_EQUIPMENT | catalogue |
| INDUSTRY_SEMICONDUCTORS | Selects semiconductors in symbol industry. | ENUM_SYMBOL_INDUSTRY | Enumerations | Exact adoption | INDUSTRY_SEMICONDUCTORS | catalogue |
| INDUSTRY_SOFTWARE_APPLICATION | Selects software application in symbol industry. | ENUM_SYMBOL_INDUSTRY | Enumerations | Exact adoption | INDUSTRY_SOFTWARE_APPLICATION | catalogue |
| INDUSTRY_SOFTWARE_INFRASTRUCTURE | Selects software infrastructure in symbol industry. | ENUM_SYMBOL_INDUSTRY | Enumerations | Exact adoption | INDUSTRY_SOFTWARE_INFRASTRUCTURE | catalogue |
| INDUSTRY_SOLAR | Selects solar in symbol industry. | ENUM_SYMBOL_INDUSTRY | Enumerations | Exact adoption | INDUSTRY_SOLAR | catalogue |
| INDUSTRY_UTILITIES_DIVERSIFIED | Selects utilities diversified in symbol industry. | ENUM_SYMBOL_INDUSTRY | Enumerations | Exact adoption | INDUSTRY_UTILITIES_DIVERSIFIED | catalogue |
| INDUSTRY_UTILITIES_POWERPRODUCERS | Selects utilities powerproducers in symbol industry. | ENUM_SYMBOL_INDUSTRY | Enumerations | Exact adoption | INDUSTRY_UTILITIES_POWERPRODUCERS | catalogue |
| INDUSTRY_UTILITIES_RENEWABLE | Selects utilities renewable in symbol industry. | ENUM_SYMBOL_INDUSTRY | Enumerations | Exact adoption | INDUSTRY_UTILITIES_RENEWABLE | catalogue |
| INDUSTRY_UTILITIES_REGULATED_ELECTRIC | Selects utilities regulated electric in symbol industry. | ENUM_SYMBOL_INDUSTRY | Enumerations | Exact adoption | INDUSTRY_UTILITIES_REGULATED_ELECTRIC | catalogue |
| INDUSTRY_UTILITIES_REGULATED_GAS | Selects utilities regulated gas in symbol industry. | ENUM_SYMBOL_INDUSTRY | Enumerations | Exact adoption | INDUSTRY_UTILITIES_REGULATED_GAS | catalogue |
| INDUSTRY_UTILITIES_REGULATED_WATER | Selects utilities regulated water in symbol industry. | ENUM_SYMBOL_INDUSTRY | Enumerations | Exact adoption | INDUSTRY_UTILITIES_REGULATED_WATER | catalogue |
| INDUSTRY_UTILITIES_FIRST | Selects utilities first in symbol industry. | ENUM_SYMBOL_INDUSTRY | Enumerations | Exact adoption | INDUSTRY_UTILITIES_FIRST | catalogue |
| INDUSTRY_UTILITIES_LAST | Selects utilities last in symbol industry. | ENUM_SYMBOL_INDUSTRY | Enumerations | Exact adoption | INDUSTRY_UTILITIES_LAST | catalogue |
| ENUM_ACCOUNT_INFO_INTEGER | Defines the identifier set for account info integer. | enum (int) | Enumerations | Exact adoption | ENUM_ACCOUNT_INFO_INTEGER | broker |
| ACCOUNT_LOGIN | Selects login in account info integer. HaruQuantAI adds provider identity, retryability, and audit evidence. | long | Enumerations | Semantic extension | ACCOUNT_LOGIN | broker |
| ACCOUNT_TRADE_MODE | Selects trade mode in account info integer. HaruQuantAI adds provider identity, retryability, and audit evidence. | ENUM_ACCOUNT_TRADE_MODE | Enumerations | Semantic extension | ACCOUNT_TRADE_MODE | broker |
| ACCOUNT_LEVERAGE | Selects leverage in account info integer. HaruQuantAI adds provider identity, retryability, and audit evidence. | long | Enumerations | Semantic extension | ACCOUNT_LEVERAGE | broker |
| ACCOUNT_LIMIT_ORDERS | Selects limit orders in account info integer. HaruQuantAI adds provider identity, retryability, and audit evidence. | int | Enumerations | Semantic extension | ACCOUNT_LIMIT_ORDERS | broker |
| ACCOUNT_MARGIN_SO_MODE | Selects margin so mode in account info integer. HaruQuantAI adds provider identity, retryability, and audit evidence. | ENUM_ACCOUNT_STOPOUT_MODE | Enumerations | Semantic extension | ACCOUNT_MARGIN_SO_MODE | broker |
| ACCOUNT_TRADE_ALLOWED | Selects trade allowed in account info integer. HaruQuantAI adds provider identity, retryability, and audit evidence. | bool | Enumerations | Semantic extension | ACCOUNT_TRADE_ALLOWED | broker |
| ACCOUNT_TRADE_EXPERT | Selects trade expert in account info integer. HaruQuantAI adds provider identity, retryability, and audit evidence. | bool | Enumerations | Semantic extension | ACCOUNT_TRADE_EXPERT | broker |
| ACCOUNT_MARGIN_MODE | Selects margin mode in account info integer. HaruQuantAI adds provider identity, retryability, and audit evidence. | ENUM_ACCOUNT_MARGIN_MODE | Enumerations | Semantic extension | ACCOUNT_MARGIN_MODE | broker |
| ACCOUNT_CURRENCY_DIGITS | Selects currency digits in account info integer. HaruQuantAI adds provider identity, retryability, and audit evidence. | int | Enumerations | Semantic extension | ACCOUNT_CURRENCY_DIGITS | broker |
| ACCOUNT_FIFO_CLOSE | Selects FIFO close in account info integer. HaruQuantAI adds provider identity, retryability, and audit evidence. | bool | Enumerations | Semantic extension | ACCOUNT_FIFO_CLOSE | broker |
| ENUM_ACCOUNT_INFO_DOUBLE | Defines the identifier set for account info double. | enum (int) | Enumerations | Exact adoption | ENUM_ACCOUNT_INFO_DOUBLE | broker |
| ACCOUNT_HEDGE_ALLOWED | Selects hedge allowed in account info integer. HaruQuantAI adds provider identity, retryability, and audit evidence. | bool | Enumerations | Semantic extension | ACCOUNT_HEDGE_ALLOWED | broker |
| ACCOUNT_BALANCE | Selects balance in account info double. HaruQuantAI adds provider identity, retryability, and audit evidence. | double | Enumerations | Semantic extension | ACCOUNT_BALANCE | broker |
| ACCOUNT_CREDIT | Selects credit in account info double. HaruQuantAI adds provider identity, retryability, and audit evidence. | double | Enumerations | Semantic extension | ACCOUNT_CREDIT | broker |
| ACCOUNT_PROFIT | Selects profit in account info double. HaruQuantAI adds provider identity, retryability, and audit evidence. | double | Enumerations | Semantic extension | ACCOUNT_PROFIT | broker |
| ACCOUNT_EQUITY | Selects equity in account info double. HaruQuantAI adds provider identity, retryability, and audit evidence. | double | Enumerations | Semantic extension | ACCOUNT_EQUITY | broker |
| ACCOUNT_MARGIN | Selects margin in account info double. HaruQuantAI adds provider identity, retryability, and audit evidence. | double | Enumerations | Semantic extension | ACCOUNT_MARGIN | broker |
| ACCOUNT_MARGIN_FREE | Selects margin free in account info double. HaruQuantAI adds provider identity, retryability, and audit evidence. | double | Enumerations | Semantic extension | ACCOUNT_MARGIN_FREE | broker |
| ACCOUNT_MARGIN_LEVEL | Selects margin level in account info double. HaruQuantAI adds provider identity, retryability, and audit evidence. | double | Enumerations | Semantic extension | ACCOUNT_MARGIN_LEVEL | broker |
| ACCOUNT_MARGIN_SO_CALL | Selects margin so call in account info double. HaruQuantAI adds provider identity, retryability, and audit evidence. | double | Enumerations | Semantic extension | ACCOUNT_MARGIN_SO_CALL | broker |
| ACCOUNT_MARGIN_SO_SO | Selects margin so so in account info double. HaruQuantAI adds provider identity, retryability, and audit evidence. | double | Enumerations | Semantic extension | ACCOUNT_MARGIN_SO_SO | broker |
| ACCOUNT_MARGIN_INITIAL | Selects margin initial in account info double. HaruQuantAI adds provider identity, retryability, and audit evidence. | double | Enumerations | Semantic extension | ACCOUNT_MARGIN_INITIAL | broker |
| ACCOUNT_MARGIN_MAINTENANCE | Selects margin maintenance in account info double. HaruQuantAI adds provider identity, retryability, and audit evidence. | double | Enumerations | Semantic extension | ACCOUNT_MARGIN_MAINTENANCE | broker |
| ENUM_ACCOUNT_INFO_STRING | Defines the identifier set for account info string. | enum (int) | Enumerations | Exact adoption | ENUM_ACCOUNT_INFO_STRING | broker |
| ACCOUNT_ASSETS | Selects assets in account info double. HaruQuantAI adds provider identity, retryability, and audit evidence. | double | Enumerations | Semantic extension | ACCOUNT_ASSETS | broker |
| ACCOUNT_LIABILITIES | Selects liabilities in account info double. HaruQuantAI adds provider identity, retryability, and audit evidence. | double | Enumerations | Semantic extension | ACCOUNT_LIABILITIES | broker |
| ACCOUNT_COMMISSION_BLOCKED | Selects commission blocked in account info double. HaruQuantAI adds provider identity, retryability, and audit evidence. | double | Enumerations | Semantic extension | ACCOUNT_COMMISSION_BLOCKED | broker |
| ACCOUNT_NAME | Selects name in account info string. HaruQuantAI adds provider identity, retryability, and audit evidence. | string | Enumerations | Semantic extension | ACCOUNT_NAME | broker |
| ACCOUNT_SERVER | Selects server in account info string. HaruQuantAI adds provider identity, retryability, and audit evidence. | string | Enumerations | Semantic extension | ACCOUNT_SERVER | broker |
| ACCOUNT_CURRENCY | Selects currency in account info string. HaruQuantAI adds provider identity, retryability, and audit evidence. | string | Enumerations | Semantic extension | ACCOUNT_CURRENCY | broker |
| ACCOUNT_COMPANY | Selects company in account info string. HaruQuantAI adds provider identity, retryability, and audit evidence. | string | Enumerations | Semantic extension | ACCOUNT_COMPANY | broker |
| ENUM_ACCOUNT_TRADE_MODE | Defines the identifier set for account trade mode. | enum (int) | Enumerations | Exact adoption | ENUM_ACCOUNT_TRADE_MODE | broker |
| ENUM_ACCOUNT_STOPOUT_MODE | Defines the identifier set for account stopout mode. | enum (int) | Enumerations | Exact adoption | ENUM_ACCOUNT_STOPOUT_MODE | broker |
| ENUM_ACCOUNT_MARGIN_MODE | Defines the identifier set for account margin mode. | enum (int) | Enumerations | Exact adoption | ENUM_ACCOUNT_MARGIN_MODE | broker |
| ACCOUNT_TRADE_MODE_DEMO | Selects trade mode demo in account trade mode. | ENUM_ACCOUNT_TRADE_MODE | Enumerations | Exact adoption | ACCOUNT_TRADE_MODE_DEMO | broker |
| ACCOUNT_TRADE_MODE_CONTEST | Selects trade mode contest in account trade mode. | ENUM_ACCOUNT_TRADE_MODE | Enumerations | Exact adoption | ACCOUNT_TRADE_MODE_CONTEST | broker |
| ACCOUNT_TRADE_MODE_REAL | Selects trade mode real in account trade mode. | ENUM_ACCOUNT_TRADE_MODE | Enumerations | Exact adoption | ACCOUNT_TRADE_MODE_REAL | broker |
| ACCOUNT_STOPOUT_MODE_PERCENT | Selects stopout mode percent in account stopout mode. | ENUM_ACCOUNT_STOPOUT_MODE | Enumerations | Exact adoption | ACCOUNT_STOPOUT_MODE_PERCENT | broker |
| ACCOUNT_STOPOUT_MODE_MONEY | Selects stopout mode money in account stopout mode. | ENUM_ACCOUNT_STOPOUT_MODE | Enumerations | Exact adoption | ACCOUNT_STOPOUT_MODE_MONEY | broker |
| ACCOUNT_MARGIN_MODE_RETAIL_NETTING | Selects margin mode retail netting in account margin mode. | ENUM_ACCOUNT_MARGIN_MODE | Enumerations | Exact adoption | ACCOUNT_MARGIN_MODE_RETAIL_NETTING | broker |
| ACCOUNT_MARGIN_MODE_EXCHANGE | Selects margin mode exchange in account margin mode. | ENUM_ACCOUNT_MARGIN_MODE | Enumerations | Exact adoption | ACCOUNT_MARGIN_MODE_EXCHANGE | broker |
| ACCOUNT_MARGIN_MODE_RETAIL_HEDGING | Selects margin mode retail hedging in account margin mode. | ENUM_ACCOUNT_MARGIN_MODE | Enumerations | Exact adoption | ACCOUNT_MARGIN_MODE_RETAIL_HEDGING | broker |
| ENUM_STATISTICS | Defines the identifier set for statistics. | enum (int) | Enumerations | Exact adoption | ENUM_STATISTICS | analytics |
| STAT_INITIAL_DEPOSIT | Selects initial deposit in statistics. HaruQuantAI adds deterministic metric provenance and evaluation context. | double | Enumerations | Semantic extension | STAT_INITIAL_DEPOSIT | analytics |
| STAT_WITHDRAWAL | Selects withdrawal in statistics. HaruQuantAI adds deterministic metric provenance and evaluation context. | double | Enumerations | Semantic extension | STAT_WITHDRAWAL | analytics |
| STAT_PROFIT | Selects profit in statistics. HaruQuantAI adds deterministic metric provenance and evaluation context. | double | Enumerations | Semantic extension | STAT_PROFIT | analytics |
| STAT_GROSS_PROFIT | Selects gross profit in statistics. HaruQuantAI adds deterministic metric provenance and evaluation context. | double | Enumerations | Semantic extension | STAT_GROSS_PROFIT | analytics |
| STAT_GROSS_LOSS | Selects gross loss in statistics. HaruQuantAI adds deterministic metric provenance and evaluation context. | double | Enumerations | Semantic extension | STAT_GROSS_LOSS | analytics |
| STAT_MAX_PROFITTRADE | Selects max profittrade in statistics. HaruQuantAI adds deterministic metric provenance and evaluation context. | double | Enumerations | Semantic extension | STAT_MAX_PROFITTRADE | analytics |
| STAT_MAX_LOSSTRADE | Selects max losstrade in statistics. HaruQuantAI adds deterministic metric provenance and evaluation context. | double | Enumerations | Semantic extension | STAT_MAX_LOSSTRADE | analytics |
| STAT_CONPROFITMAX | Selects conprofitmax in statistics. HaruQuantAI adds deterministic metric provenance and evaluation context. | double | Enumerations | Semantic extension | STAT_CONPROFITMAX | analytics |
| STAT_CONPROFITMAX_TRADES | Selects conprofitmax trades in statistics. HaruQuantAI adds deterministic metric provenance and evaluation context. | int | Enumerations | Semantic extension | STAT_CONPROFITMAX_TRADES | analytics |
| STAT_MAX_CONWINS | Selects max conwins in statistics. HaruQuantAI adds deterministic metric provenance and evaluation context. | double | Enumerations | Semantic extension | STAT_MAX_CONWINS | analytics |
| STAT_MAX_CONPROFIT_TRADES | Selects max conprofit trades in statistics. HaruQuantAI adds deterministic metric provenance and evaluation context. | int | Enumerations | Semantic extension | STAT_MAX_CONPROFIT_TRADES | analytics |
| STAT_CONLOSSMAX | Selects conlossmax in statistics. HaruQuantAI adds deterministic metric provenance and evaluation context. | double | Enumerations | Semantic extension | STAT_CONLOSSMAX | analytics |
| STAT_CONLOSSMAX_TRADES | Selects conlossmax trades in statistics. HaruQuantAI adds deterministic metric provenance and evaluation context. | int | Enumerations | Semantic extension | STAT_CONLOSSMAX_TRADES | analytics |
| STAT_MAX_CONLOSSES | Selects max conlosses in statistics. HaruQuantAI adds deterministic metric provenance and evaluation context. | double | Enumerations | Semantic extension | STAT_MAX_CONLOSSES | analytics |
| STAT_MAX_CONLOSS_TRADES | Selects max conloss trades in statistics. HaruQuantAI adds deterministic metric provenance and evaluation context. | int | Enumerations | Semantic extension | STAT_MAX_CONLOSS_TRADES | analytics |
| STAT_BALANCEMIN | Selects balancemin in statistics. HaruQuantAI adds deterministic metric provenance and evaluation context. | double | Enumerations | Semantic extension | STAT_BALANCEMIN | analytics |
| STAT_BALANCE_DD | Selects balance dd in statistics. HaruQuantAI adds deterministic metric provenance and evaluation context. | double | Enumerations | Semantic extension | STAT_BALANCE_DD | analytics |
| STAT_BALANCEDD_PERCENT | Selects balancedd percent in statistics. HaruQuantAI adds deterministic metric provenance and evaluation context. | double | Enumerations | Semantic extension | STAT_BALANCEDD_PERCENT | analytics |
| STAT_BALANCE_DDREL_PERCENT | Selects balance ddrel percent in statistics. HaruQuantAI adds deterministic metric provenance and evaluation context. | double | Enumerations | Semantic extension | STAT_BALANCE_DDREL_PERCENT | analytics |
| STAT_BALANCE_DD_RELATIVE | Selects balance dd relative in statistics. HaruQuantAI adds deterministic metric provenance and evaluation context. | double | Enumerations | Semantic extension | STAT_BALANCE_DD_RELATIVE | analytics |
| STAT_EQUITYMIN | Selects equitymin in statistics. HaruQuantAI adds deterministic metric provenance and evaluation context. | double | Enumerations | Semantic extension | STAT_EQUITYMIN | analytics |
| STAT_EQUITY_DD | Selects equity dd in statistics. HaruQuantAI adds deterministic metric provenance and evaluation context. | double | Enumerations | Semantic extension | STAT_EQUITY_DD | analytics |
| STAT_EQUITYDD_PERCENT | Selects equitydd percent in statistics. HaruQuantAI adds deterministic metric provenance and evaluation context. | double | Enumerations | Semantic extension | STAT_EQUITYDD_PERCENT | analytics |
| STAT_EQUITY_DDREL_PERCENT | Selects equity ddrel percent in statistics. HaruQuantAI adds deterministic metric provenance and evaluation context. | double | Enumerations | Semantic extension | STAT_EQUITY_DDREL_PERCENT | analytics |
| STAT_EQUITY_DD_RELATIVE | Selects equity dd relative in statistics. HaruQuantAI adds deterministic metric provenance and evaluation context. | double | Enumerations | Semantic extension | STAT_EQUITY_DD_RELATIVE | analytics |
| STAT_EXPECTED_PAYOFF | Selects expected payoff in statistics. HaruQuantAI adds deterministic metric provenance and evaluation context. | double | Enumerations | Semantic extension | STAT_EXPECTED_PAYOFF | analytics |
| STAT_PROFIT_FACTOR | Selects profit factor in statistics. HaruQuantAI adds deterministic metric provenance and evaluation context. | double | Enumerations | Semantic extension | STAT_PROFIT_FACTOR | analytics |
| STAT_RECOVERY_FACTOR | Selects recovery factor in statistics. HaruQuantAI adds deterministic metric provenance and evaluation context. | double | Enumerations | Semantic extension | STAT_RECOVERY_FACTOR | analytics |
| STAT_SHARPE_RATIO | Selects sharpe ratio in statistics. HaruQuantAI adds deterministic metric provenance and evaluation context. | double | Enumerations | Semantic extension | STAT_SHARPE_RATIO | analytics |
| STAT_MIN_MARGINLEVEL | Selects min marginlevel in statistics. HaruQuantAI adds deterministic metric provenance and evaluation context. | double | Enumerations | Semantic extension | STAT_MIN_MARGINLEVEL | analytics |
| STAT_CUSTOM_ONTESTER | Selects custom ontester in statistics. HaruQuantAI adds deterministic metric provenance and evaluation context. | double | Enumerations | Semantic extension | STAT_CUSTOM_ONTESTER | analytics |
| STAT_DEALS | Selects deals in statistics. HaruQuantAI adds deterministic metric provenance and evaluation context. | int | Enumerations | Semantic extension | STAT_DEALS | analytics |
| STAT_TRADES | Selects trades in statistics. HaruQuantAI adds deterministic metric provenance and evaluation context. | int | Enumerations | Semantic extension | STAT_TRADES | analytics |
| STAT_PROFIT_TRADES | Selects profit trades in statistics. HaruQuantAI adds deterministic metric provenance and evaluation context. | int | Enumerations | Semantic extension | STAT_PROFIT_TRADES | analytics |
| STAT_LOSS_TRADES | Selects loss trades in statistics. HaruQuantAI adds deterministic metric provenance and evaluation context. | int | Enumerations | Semantic extension | STAT_LOSS_TRADES | analytics |
| STAT_SHORT_TRADES | Selects short trades in statistics. HaruQuantAI adds deterministic metric provenance and evaluation context. | int | Enumerations | Semantic extension | STAT_SHORT_TRADES | analytics |
| STAT_LONG_TRADES | Selects long trades in statistics. HaruQuantAI adds deterministic metric provenance and evaluation context. | int | Enumerations | Semantic extension | STAT_LONG_TRADES | analytics |
| STAT_PROFIT_SHORTTRADES | Selects profit shorttrades in statistics. HaruQuantAI adds deterministic metric provenance and evaluation context. | int | Enumerations | Semantic extension | STAT_PROFIT_SHORTTRADES | analytics |
| STAT_PROFIT_LONGTRADES | Selects profit longtrades in statistics. HaruQuantAI adds deterministic metric provenance and evaluation context. | int | Enumerations | Semantic extension | STAT_PROFIT_LONGTRADES | analytics |
| STAT_PROFITTRADES_AVGCON | Selects profittrades avgcon in statistics. HaruQuantAI adds deterministic metric provenance and evaluation context. | int | Enumerations | Semantic extension | STAT_PROFITTRADES_AVGCON | analytics |
| STAT_LOSSTRADES_AVGCON | Selects losstrades avgcon in statistics. HaruQuantAI adds deterministic metric provenance and evaluation context. | int | Enumerations | Semantic extension | STAT_LOSSTRADES_AVGCON | analytics |
| STAT_COMPLEX_CRITERION | Selects complex criterion in statistics. HaruQuantAI adds deterministic metric provenance and evaluation context. | ENUM_STATISTICS | Enumerations | Semantic extension | STAT_COMPLEX_CRITERION | analytics |
| ENUM_SERIES_INFO_INTEGER | Defines the identifier set for series info integer. | enum (int) | Enumerations | Exact adoption | ENUM_SERIES_INFO_INTEGER | data |
| SERIES_BARS_COUNT | Selects bars count in series info integer. | long | Enumerations | Exact adoption | SERIES_BARS_COUNT | data |
| SERIES_FIRSTDATE | Selects firstdate in series info integer. | datetime | Enumerations | Exact adoption | SERIES_FIRSTDATE | data |
| SERIES_LASTBAR_DATE | Selects lastbar date in series info integer. | datetime | Enumerations | Exact adoption | SERIES_LASTBAR_DATE | data |
| SERIES_SERVER_FIRSTDATE | Selects server firstdate in series info integer. | datetime | Enumerations | Exact adoption | SERIES_SERVER_FIRSTDATE | data |
| SERIES_TERMINAL_FIRSTDATE | Selects terminal firstdate in series info integer. | datetime | Enumerations | Exact adoption | SERIES_TERMINAL_FIRSTDATE | data |
| SERIES_SYNCHRONIZED | Selects synchronized in series info integer. | bool | Enumerations | Exact adoption | SERIES_SYNCHRONIZED | data |
| ENUM_ORDER_PROPERTY_INTEGER | Defines the identifier set for order property integer. | enum (int) | Enumerations | Exact adoption | ENUM_ORDER_PROPERTY_INTEGER | trading |
| ORDER_TICKET | Selects ticket in order property integer. HaruQuantAI adds lifecycle, idempotency, and audit evidence. | long | Enumerations | Semantic extension | ORDER_TICKET | trading |
| ORDER_TIME_SETUP | Selects time setup in order property integer. HaruQuantAI adds lifecycle, idempotency, and audit evidence. | datetime | Enumerations | Semantic extension | ORDER_TIME_SETUP | trading |
| ORDER_TYPE | Selects type in order property integer. HaruQuantAI adds lifecycle, idempotency, and audit evidence. | ENUM_ORDER_TYPE | Enumerations | Semantic extension | ORDER_TYPE | trading |
| ORDER_STATE | Selects state in order property integer. HaruQuantAI adds lifecycle, idempotency, and audit evidence. | ENUM_ORDER_STATE | Enumerations | Semantic extension | ORDER_STATE | trading |
| ORDER_TIME_EXPIRATION | Selects time expiration in order property integer. HaruQuantAI adds lifecycle, idempotency, and audit evidence. | datetime | Enumerations | Semantic extension | ORDER_TIME_EXPIRATION | trading |
| ORDER_TIME_DONE | Selects time done in order property integer. HaruQuantAI adds lifecycle, idempotency, and audit evidence. | datetime | Enumerations | Semantic extension | ORDER_TIME_DONE | trading |
| ORDER_TIME_SETUP_MSC | Selects time setup msc in order property integer. HaruQuantAI adds lifecycle, idempotency, and audit evidence. | long | Enumerations | Semantic extension | ORDER_TIME_SETUP_MSC | trading |
| ORDER_TIME_DONE_MSC | Selects time done msc in order property integer. HaruQuantAI adds lifecycle, idempotency, and audit evidence. | long | Enumerations | Semantic extension | ORDER_TIME_DONE_MSC | trading |
| ORDER_TYPE_FILLING | Selects type filling in order property integer. HaruQuantAI adds lifecycle, idempotency, and audit evidence. | ENUM_ORDER_TYPE_FILLING | Enumerations | Semantic extension | ORDER_TYPE_FILLING | trading |
| ORDER_TYPE_TIME | Selects type time in order property integer. HaruQuantAI adds lifecycle, idempotency, and audit evidence. | ENUM_ORDER_TYPE_TIME | Enumerations | Semantic extension | ORDER_TYPE_TIME | trading |
| ENUM_ORDER_PROPERTY_DOUBLE | Defines the identifier set for order property double. | enum (int) | Enumerations | Exact adoption | ENUM_ORDER_PROPERTY_DOUBLE | trading |
| ORDER_MAGIC | Selects magic in order property integer. HaruQuantAI adds lifecycle, idempotency, and audit evidence. | long | Enumerations | Semantic extension | ORDER_MAGIC | trading |
| ORDER_REASON | Selects reason in order property integer. HaruQuantAI adds lifecycle, idempotency, and audit evidence. | ENUM_ORDER_REASON | Enumerations | Semantic extension | ORDER_REASON | trading |
| ORDER_POSITION_ID | Selects position ID in order property integer. HaruQuantAI adds lifecycle, idempotency, and audit evidence. | long | Enumerations | Semantic extension | ORDER_POSITION_ID | trading |
| ORDER_POSITION_BY_ID | Selects position by ID in order property integer. HaruQuantAI adds lifecycle, idempotency, and audit evidence. | long | Enumerations | Semantic extension | ORDER_POSITION_BY_ID | trading |
| ENUM_ORDER_PROPERTY_STRING | Defines the identifier set for order property string. | enum (int) | Enumerations | Exact adoption | ENUM_ORDER_PROPERTY_STRING | trading |
| ENUM_ORDER_TYPE | Defines the identifier set for order type. | enum (int) | Enumerations | Exact adoption | ENUM_ORDER_TYPE | trading |
| ORDER_VOLUME_INITIAL | Selects volume initial in order property double. HaruQuantAI adds lifecycle, idempotency, and audit evidence. | double | Enumerations | Semantic extension | ORDER_VOLUME_INITIAL | trading |
| ORDER_VOLUME_CURRENT | Selects volume current in order property double. HaruQuantAI adds lifecycle, idempotency, and audit evidence. | double | Enumerations | Semantic extension | ORDER_VOLUME_CURRENT | trading |
| ORDER_PRICE_OPEN | Selects price open in order property double. HaruQuantAI adds lifecycle, idempotency, and audit evidence. | double | Enumerations | Semantic extension | ORDER_PRICE_OPEN | trading |
| ORDER_SL | Selects SL in order property double. HaruQuantAI adds lifecycle, idempotency, and audit evidence. | double | Enumerations | Semantic extension | ORDER_SL | trading |
| ORDER_TP | Selects TP in order property double. HaruQuantAI adds lifecycle, idempotency, and audit evidence. | double | Enumerations | Semantic extension | ORDER_TP | trading |
| ORDER_PRICE_CURRENT | Selects price current in order property double. HaruQuantAI adds lifecycle, idempotency, and audit evidence. | double | Enumerations | Semantic extension | ORDER_PRICE_CURRENT | trading |
| ORDER_PRICE_STOPLIMIT | Selects price stoplimit in order property double. HaruQuantAI adds lifecycle, idempotency, and audit evidence. | double | Enumerations | Semantic extension | ORDER_PRICE_STOPLIMIT | trading |
| ORDER_SYMBOL | Selects symbol in order property string. HaruQuantAI adds lifecycle, idempotency, and audit evidence. | string | Enumerations | Semantic extension | ORDER_SYMBOL | trading |
| ORDER_COMMENT | Selects comment in order property string. HaruQuantAI adds lifecycle, idempotency, and audit evidence. | string | Enumerations | Semantic extension | ORDER_COMMENT | trading |
| ORDER_EXTERNAL_ID | Selects external ID in order property string. HaruQuantAI adds lifecycle, idempotency, and audit evidence. | string | Enumerations | Semantic extension | ORDER_EXTERNAL_ID | trading |
| ORDER_TYPE_BUY | Selects type buy in order type. | ENUM_ORDER_TYPE | Enumerations | Exact adoption | ORDER_TYPE_BUY | trading |
| ENUM_ORDER_STATE | Defines the identifier set for order state. | enum (int) | Enumerations | Exact adoption | ENUM_ORDER_STATE | trading |
| ORDER_TYPE_SELL | Selects type sell in order type. | ENUM_ORDER_TYPE | Enumerations | Exact adoption | ORDER_TYPE_SELL | trading |
| ORDER_TYPE_BUY_LIMIT | Selects type buy limit in order type. | ENUM_ORDER_TYPE | Enumerations | Exact adoption | ORDER_TYPE_BUY_LIMIT | trading |
| ORDER_TYPE_SELL_LIMIT | Selects type sell limit in order type. | ENUM_ORDER_TYPE | Enumerations | Exact adoption | ORDER_TYPE_SELL_LIMIT | trading |
| ORDER_TYPE_BUY_STOP | Selects type buy stop in order type. | ENUM_ORDER_TYPE | Enumerations | Exact adoption | ORDER_TYPE_BUY_STOP | trading |
| ORDER_TYPE_SELL_STOP | Selects type sell stop in order type. | ENUM_ORDER_TYPE | Enumerations | Exact adoption | ORDER_TYPE_SELL_STOP | trading |
| ORDER_TYPE_BUY_STOP_LIMIT | Selects type buy stop limit in order type. | ENUM_ORDER_TYPE | Enumerations | Exact adoption | ORDER_TYPE_BUY_STOP_LIMIT | trading |
| ORDER_TYPE_SELL_STOP_LIMIT | Selects type sell stop limit in order type. | ENUM_ORDER_TYPE | Enumerations | Exact adoption | ORDER_TYPE_SELL_STOP_LIMIT | trading |
| ORDER_TYPE_CLOSE_BY | Selects type close by in order type. | ENUM_ORDER_TYPE | Enumerations | Exact adoption | ORDER_TYPE_CLOSE_BY | trading |
| ORDER_STATE_STARTED | Selects state started in order state. | ENUM_ORDER_STATE | Enumerations | Exact adoption | ORDER_STATE_STARTED | trading |
| ORDER_STATE_PLACED | Selects state placed in order state. | ENUM_ORDER_STATE | Enumerations | Exact adoption | ORDER_STATE_PLACED | trading |
| ORDER_STATE_CANCELED | Selects state canceled in order state. | ENUM_ORDER_STATE | Enumerations | Exact adoption | ORDER_STATE_CANCELED | trading |
| ORDER_STATE_PARTIAL | Selects state partial in order state. | ENUM_ORDER_STATE | Enumerations | Exact adoption | ORDER_STATE_PARTIAL | trading |
| ORDER_STATE_FILLED | Selects state filled in order state. | ENUM_ORDER_STATE | Enumerations | Exact adoption | ORDER_STATE_FILLED | trading |
| ORDER_STATE_REJECTED | Selects state rejected in order state. | ENUM_ORDER_STATE | Enumerations | Exact adoption | ORDER_STATE_REJECTED | trading |
| ORDER_STATE_EXPIRED | Selects state expired in order state. | ENUM_ORDER_STATE | Enumerations | Exact adoption | ORDER_STATE_EXPIRED | trading |
| ORDER_STATE_REQUEST_ADD | Selects state request add in order state. | ENUM_ORDER_STATE | Enumerations | Exact adoption | ORDER_STATE_REQUEST_ADD | trading |
| ORDER_STATE_REQUEST_MODIFY | Selects state request modify in order state. | ENUM_ORDER_STATE | Enumerations | Exact adoption | ORDER_STATE_REQUEST_MODIFY | trading |
| ORDER_STATE_REQUEST_CANCEL | Selects state request cancel in order state. | ENUM_ORDER_STATE | Enumerations | Exact adoption | ORDER_STATE_REQUEST_CANCEL | trading |
| ENUM_ORDER_TYPE_FILLING | Defines the identifier set for order type filling. | enum (int) | Enumerations | Exact adoption | ENUM_ORDER_TYPE_FILLING | trading |
| ORDER_FILLING_FOK | Selects filling FOK in order type filling. | ENUM_ORDER_TYPE_FILLING | Enumerations | Exact adoption | ORDER_FILLING_FOK | trading |
| ORDER_FILLING_IOC | Selects filling IOC in order type filling. | ENUM_ORDER_TYPE_FILLING | Enumerations | Exact adoption | ORDER_FILLING_IOC | trading |
| ORDER_FILLING_BOC | Selects filling boc in order type filling. | ENUM_ORDER_TYPE_FILLING | Enumerations | Exact adoption | ORDER_FILLING_BOC | trading |
| ORDER_FILLING_RETURN | Selects filling return in order type filling. | ENUM_ORDER_TYPE_FILLING | Enumerations | Exact adoption | ORDER_FILLING_RETURN | trading |
| ENUM_ORDER_TYPE_TIME | Defines the identifier set for order type time. | enum (int) | Enumerations | Exact adoption | ENUM_ORDER_TYPE_TIME | trading |
| ENUM_ORDER_REASON | Defines the identifier set for order reason. | enum (int) | Enumerations | Exact adoption | ENUM_ORDER_REASON | trading |
| ORDER_TIME_GTC | Selects time GTC in order type time. | ENUM_ORDER_TYPE_TIME | Enumerations | Exact adoption | ORDER_TIME_GTC | trading |
| ORDER_TIME_DAY | Selects time day in order type time. | ENUM_ORDER_TYPE_TIME | Enumerations | Exact adoption | ORDER_TIME_DAY | trading |
| ORDER_TIME_SPECIFIED | Selects time specified in order type time. | ENUM_ORDER_TYPE_TIME | Enumerations | Exact adoption | ORDER_TIME_SPECIFIED | trading |
| ORDER_TIME_SPECIFIED_DAY | Selects time specified day in order type time. | ENUM_ORDER_TYPE_TIME | Enumerations | Exact adoption | ORDER_TIME_SPECIFIED_DAY | trading |
| ORDER_REASON_CLIENT | Selects reason client in order reason. | ENUM_ORDER_REASON | Enumerations | Exact adoption | ORDER_REASON_CLIENT | trading |
| ORDER_REASON_MOBILE | Selects reason mobile in order reason. | ENUM_ORDER_REASON | Enumerations | Exact adoption | ORDER_REASON_MOBILE | trading |
| ORDER_REASON_WEB | Selects reason web in order reason. | ENUM_ORDER_REASON | Enumerations | Exact adoption | ORDER_REASON_WEB | trading |
| ORDER_REASON_EXPERT | Selects reason expert in order reason. | ENUM_ORDER_REASON | Enumerations | Platform-neutral rename | ORDER_REASON_AUTOMATION | trading |
| ORDER_REASON_SL | Selects reason SL in order reason. | ENUM_ORDER_REASON | Enumerations | Exact adoption | ORDER_REASON_SL | trading |
| ORDER_REASON_TP | Selects reason TP in order reason. | ENUM_ORDER_REASON | Enumerations | Exact adoption | ORDER_REASON_TP | trading |
| ORDER_REASON_SO | Selects reason so in order reason. | ENUM_ORDER_REASON | Enumerations | Exact adoption | ORDER_REASON_SO | trading |
| ENUM_POSITION_PROPERTY_INTEGER | Defines the identifier set for position property integer. | enum (int) | Enumerations | Exact adoption | ENUM_POSITION_PROPERTY_INTEGER | trading |
| POSITION_TICKET | Selects ticket in position property integer. HaruQuantAI adds lifecycle, idempotency, and audit evidence. | long | Enumerations | Semantic extension | POSITION_TICKET | trading |
| POSITION_TIME | Selects time in position property integer. HaruQuantAI adds lifecycle, idempotency, and audit evidence. | datetime | Enumerations | Semantic extension | POSITION_TIME | trading |
| POSITION_TIME_MSC | Selects time msc in position property integer. HaruQuantAI adds lifecycle, idempotency, and audit evidence. | long | Enumerations | Semantic extension | POSITION_TIME_MSC | trading |
| POSITION_TIME_UPDATE | Selects time update in position property integer. HaruQuantAI adds lifecycle, idempotency, and audit evidence. | datetime | Enumerations | Semantic extension | POSITION_TIME_UPDATE | trading |
| POSITION_TIME_UPDATE_MSC | Selects time update msc in position property integer. HaruQuantAI adds lifecycle, idempotency, and audit evidence. | long | Enumerations | Semantic extension | POSITION_TIME_UPDATE_MSC | trading |
| POSITION_TYPE | Selects type in position property integer. HaruQuantAI adds lifecycle, idempotency, and audit evidence. | ENUM_POSITION_TYPE | Enumerations | Semantic extension | POSITION_TYPE | trading |
| POSITION_MAGIC | Selects magic in position property integer. HaruQuantAI adds lifecycle, idempotency, and audit evidence. | long | Enumerations | Semantic extension | POSITION_MAGIC | trading |
| POSITION_IDENTIFIER | Selects identifier in position property integer. HaruQuantAI adds lifecycle, idempotency, and audit evidence. | long | Enumerations | Semantic extension | POSITION_IDENTIFIER | trading |
| ENUM_POSITION_PROPERTY_DOUBLE | Defines the identifier set for position property double. | enum (int) | Enumerations | Exact adoption | ENUM_POSITION_PROPERTY_DOUBLE | trading |
| ENUM_POSITION_PROPERTY_STRING | Defines the identifier set for position property string. | enum (int) | Enumerations | Exact adoption | ENUM_POSITION_PROPERTY_STRING | trading |
| POSITION_REASON | Selects reason in position property integer. HaruQuantAI adds lifecycle, idempotency, and audit evidence. | ENUM_POSITION_REASON | Enumerations | Semantic extension | POSITION_REASON | trading |
| POSITION_VOLUME | Selects volume in position property double. HaruQuantAI adds lifecycle, idempotency, and audit evidence. | double | Enumerations | Semantic extension | POSITION_VOLUME | trading |
| POSITION_PRICE_OPEN | Selects price open in position property double. HaruQuantAI adds lifecycle, idempotency, and audit evidence. | double | Enumerations | Semantic extension | POSITION_PRICE_OPEN | trading |
| POSITION_SL | Selects SL in position property double. HaruQuantAI adds lifecycle, idempotency, and audit evidence. | double | Enumerations | Semantic extension | POSITION_SL | trading |
| POSITION_TP | Selects TP in position property double. HaruQuantAI adds lifecycle, idempotency, and audit evidence. | double | Enumerations | Semantic extension | POSITION_TP | trading |
| POSITION_PRICE_CURRENT | Selects price current in position property double. HaruQuantAI adds lifecycle, idempotency, and audit evidence. | double | Enumerations | Semantic extension | POSITION_PRICE_CURRENT | trading |
| POSITION_SWAP | Selects swap in position property double. HaruQuantAI adds lifecycle, idempotency, and audit evidence. | double | Enumerations | Semantic extension | POSITION_SWAP | trading |
| POSITION_PROFIT | Selects profit in position property double. HaruQuantAI adds lifecycle, idempotency, and audit evidence. | double | Enumerations | Semantic extension | POSITION_PROFIT | trading |
| POSITION_SYMBOL | Selects symbol in position property string. HaruQuantAI adds lifecycle, idempotency, and audit evidence. | string | Enumerations | Semantic extension | POSITION_SYMBOL | trading |
| POSITION_COMMENT | Selects comment in position property string. HaruQuantAI adds lifecycle, idempotency, and audit evidence. | string | Enumerations | Semantic extension | POSITION_COMMENT | trading |
| POSITION_EXTERNAL_ID | Selects external ID in position property string. HaruQuantAI adds lifecycle, idempotency, and audit evidence. | string | Enumerations | Semantic extension | POSITION_EXTERNAL_ID | trading |
| ENUM_POSITION_TYPE | Defines the identifier set for position type. | enum (int) | Enumerations | Exact adoption | ENUM_POSITION_TYPE | trading |
| ENUM_POSITION_REASON | Defines the identifier set for position reason. | enum (int) | Enumerations | Exact adoption | ENUM_POSITION_REASON | trading |
| POSITION_TYPE_BUY | Selects type buy in position type. | ENUM_POSITION_TYPE | Enumerations | Exact adoption | POSITION_TYPE_BUY | trading |
| POSITION_TYPE_SELL | Selects type sell in position type. | ENUM_POSITION_TYPE | Enumerations | Exact adoption | POSITION_TYPE_SELL | trading |
| POSITION_REASON_CLIENT | Selects reason client in position reason. | ENUM_POSITION_REASON | Enumerations | Exact adoption | POSITION_REASON_CLIENT | trading |
| POSITION_REASON_MOBILE | Selects reason mobile in position reason. | ENUM_POSITION_REASON | Enumerations | Exact adoption | POSITION_REASON_MOBILE | trading |
| POSITION_REASON_WEB | Selects reason web in position reason. | ENUM_POSITION_REASON | Enumerations | Exact adoption | POSITION_REASON_WEB | trading |
| POSITION_REASON_EXPERT | Selects reason expert in position reason. | ENUM_POSITION_REASON | Enumerations | Platform-neutral rename | POSITION_REASON_AUTOMATION | trading |
| ENUM_DEAL_PROPERTY_INTEGER | Defines the identifier set for deal property integer. | enum (int) | Enumerations | Exact adoption | ENUM_DEAL_PROPERTY_INTEGER | trading |
| ENUM_DEAL_PROPERTY_DOUBLE | Defines the identifier set for deal property double. | enum (int) | Enumerations | Exact adoption | ENUM_DEAL_PROPERTY_DOUBLE | trading |
| DEAL_TICKET | Selects ticket in deal property integer. HaruQuantAI adds lifecycle, idempotency, and audit evidence. | long | Enumerations | Semantic extension | DEAL_TICKET | trading |
| DEAL_ORDER | Selects order in deal property integer. HaruQuantAI adds lifecycle, idempotency, and audit evidence. | long | Enumerations | Semantic extension | DEAL_ORDER | trading |
| DEAL_TIME | Selects time in deal property integer. HaruQuantAI adds lifecycle, idempotency, and audit evidence. | datetime | Enumerations | Semantic extension | DEAL_TIME | trading |
| DEAL_TIME_MSC | Selects time msc in deal property integer. HaruQuantAI adds lifecycle, idempotency, and audit evidence. | long | Enumerations | Semantic extension | DEAL_TIME_MSC | trading |
| DEAL_TYPE | Selects type in deal property integer. HaruQuantAI adds lifecycle, idempotency, and audit evidence. | ENUM_DEAL_TYPE | Enumerations | Semantic extension | DEAL_TYPE | trading |
| DEAL_ENTRY | Selects entry in deal property integer. HaruQuantAI adds lifecycle, idempotency, and audit evidence. | ENUM_DEAL_ENTRY | Enumerations | Semantic extension | DEAL_ENTRY | trading |
| DEAL_MAGIC | Selects magic in deal property integer. HaruQuantAI adds lifecycle, idempotency, and audit evidence. | long | Enumerations | Semantic extension | DEAL_MAGIC | trading |
| DEAL_REASON | Selects reason in deal property integer. HaruQuantAI adds lifecycle, idempotency, and audit evidence. | ENUM_DEAL_REASON | Enumerations | Semantic extension | DEAL_REASON | trading |
| DEAL_POSITION_ID | Selects position ID in deal property integer. HaruQuantAI adds lifecycle, idempotency, and audit evidence. | long | Enumerations | Semantic extension | DEAL_POSITION_ID | trading |
| DEAL_VOLUME | Selects volume in deal property double. HaruQuantAI adds lifecycle, idempotency, and audit evidence. | double | Enumerations | Semantic extension | DEAL_VOLUME | trading |
| DEAL_PRICE | Selects price in deal property double. HaruQuantAI adds lifecycle, idempotency, and audit evidence. | double | Enumerations | Semantic extension | DEAL_PRICE | trading |
| DEAL_COMMISSION | Selects commission in deal property double. HaruQuantAI adds lifecycle, idempotency, and audit evidence. | double | Enumerations | Semantic extension | DEAL_COMMISSION | trading |
| DEAL_SWAP | Selects swap in deal property double. HaruQuantAI adds lifecycle, idempotency, and audit evidence. | double | Enumerations | Semantic extension | DEAL_SWAP | trading |
| DEAL_PROFIT | Selects profit in deal property double. HaruQuantAI adds lifecycle, idempotency, and audit evidence. | double | Enumerations | Semantic extension | DEAL_PROFIT | trading |
| DEAL_FEE | Selects fee in deal property double. HaruQuantAI adds lifecycle, idempotency, and audit evidence. | double | Enumerations | Semantic extension | DEAL_FEE | trading |
| ENUM_DEAL_PROPERTY_STRING | Defines the identifier set for deal property string. | enum (int) | Enumerations | Exact adoption | ENUM_DEAL_PROPERTY_STRING | trading |
| ENUM_DEAL_TYPE | Defines the identifier set for deal type. | enum (int) | Enumerations | Exact adoption | ENUM_DEAL_TYPE | trading |
| DEAL_SL | Selects SL in deal property double. HaruQuantAI adds lifecycle, idempotency, and audit evidence. | double | Enumerations | Semantic extension | DEAL_SL | trading |
| DEAL_TP | Selects TP in deal property double. HaruQuantAI adds lifecycle, idempotency, and audit evidence. | double | Enumerations | Semantic extension | DEAL_TP | trading |
| DEAL_SYMBOL | Selects symbol in deal property string. HaruQuantAI adds lifecycle, idempotency, and audit evidence. | string | Enumerations | Semantic extension | DEAL_SYMBOL | trading |
| DEAL_COMMENT | Selects comment in deal property string. HaruQuantAI adds lifecycle, idempotency, and audit evidence. | string | Enumerations | Semantic extension | DEAL_COMMENT | trading |
| DEAL_EXTERNAL_ID | Selects external ID in deal property string. HaruQuantAI adds lifecycle, idempotency, and audit evidence. | string | Enumerations | Semantic extension | DEAL_EXTERNAL_ID | trading |
| DEAL_TYPE_BUY | Selects type buy in deal type. | ENUM_DEAL_TYPE | Enumerations | Exact adoption | DEAL_TYPE_BUY | trading |
| DEAL_TYPE_SELL | Selects type sell in deal type. | ENUM_DEAL_TYPE | Enumerations | Exact adoption | DEAL_TYPE_SELL | trading |
| DEAL_TYPE_BALANCE | Selects type balance in deal type. | ENUM_DEAL_TYPE | Enumerations | Exact adoption | DEAL_TYPE_BALANCE | trading |
| DEAL_TYPE_CREDIT | Selects type credit in deal type. | ENUM_DEAL_TYPE | Enumerations | Exact adoption | DEAL_TYPE_CREDIT | trading |
| ENUM_DEAL_ENTRY | Defines the identifier set for deal entry. | enum (int) | Enumerations | Exact adoption | ENUM_DEAL_ENTRY | trading |
| DEAL_TYPE_CHARGE | Selects type charge in deal type. | ENUM_DEAL_TYPE | Enumerations | Exact adoption | DEAL_TYPE_CHARGE | trading |
| DEAL_TYPE_CORRECTION | Selects type correction in deal type. | ENUM_DEAL_TYPE | Enumerations | Exact adoption | DEAL_TYPE_CORRECTION | trading |
| DEAL_TYPE_BONUS | Selects type bonus in deal type. | ENUM_DEAL_TYPE | Enumerations | Exact adoption | DEAL_TYPE_BONUS | trading |
| DEAL_TYPE_COMMISSION | Selects type commission in deal type. | ENUM_DEAL_TYPE | Enumerations | Exact adoption | DEAL_TYPE_COMMISSION | trading |
| DEAL_TYPE_COMMISSION_DAILY | Selects type commission daily in deal type. | ENUM_DEAL_TYPE | Enumerations | Exact adoption | DEAL_TYPE_COMMISSION_DAILY | trading |
| DEAL_TYPE_COMMISSION_MONTHLY | Selects type commission monthly in deal type. | ENUM_DEAL_TYPE | Enumerations | Exact adoption | DEAL_TYPE_COMMISSION_MONTHLY | trading |
| DEAL_TYPE_COMMISSION_AGENT_DAILY | Selects type commission agent daily in deal type. | ENUM_DEAL_TYPE | Enumerations | Exact adoption | DEAL_TYPE_COMMISSION_AGENT_DAILY | trading |
| DEAL_TYPE_COMMISSION_AGENT_MONTHLY | Selects type commission agent monthly in deal type. | ENUM_DEAL_TYPE | Enumerations | Exact adoption | DEAL_TYPE_COMMISSION_AGENT_MONTHLY | trading |
| DEAL_TYPE_INTEREST | Selects type interest in deal type. | ENUM_DEAL_TYPE | Enumerations | Exact adoption | DEAL_TYPE_INTEREST | trading |
| DEAL_TYPE_BUY_CANCELED | Selects type buy canceled in deal type. | ENUM_DEAL_TYPE | Enumerations | Exact adoption | DEAL_TYPE_BUY_CANCELED | trading |
| DEAL_TYPE_SELL_CANCELED | Selects type sell canceled in deal type. | ENUM_DEAL_TYPE | Enumerations | Exact adoption | DEAL_TYPE_SELL_CANCELED | trading |
| DEAL_DIVIDEND | Selects dividend in deal type. | ENUM_DEAL_TYPE | Enumerations | Exact adoption | DEAL_DIVIDEND | trading |
| DEAL_DIVIDEND_FRANKED | Selects dividend franked in deal type. | ENUM_DEAL_TYPE | Enumerations | Exact adoption | DEAL_DIVIDEND_FRANKED | trading |
| DEAL_TAX | Selects tax in deal type. | ENUM_DEAL_TYPE | Enumerations | Exact adoption | DEAL_TAX | trading |
| ENUM_DEAL_REASON | Defines the identifier set for deal reason. | enum (int) | Enumerations | Exact adoption | ENUM_DEAL_REASON | trading |
| DEAL_ENTRY_IN | Selects entry in in deal entry. | ENUM_DEAL_ENTRY | Enumerations | Exact adoption | DEAL_ENTRY_IN | trading |
| DEAL_ENTRY_OUT | Selects entry out in deal entry. | ENUM_DEAL_ENTRY | Enumerations | Exact adoption | DEAL_ENTRY_OUT | trading |
| DEAL_ENTRY_INOUT | Selects entry inout in deal entry. | ENUM_DEAL_ENTRY | Enumerations | Exact adoption | DEAL_ENTRY_INOUT | trading |
| DEAL_ENTRY_OUT_BY | Selects entry out by in deal entry. | ENUM_DEAL_ENTRY | Enumerations | Exact adoption | DEAL_ENTRY_OUT_BY | trading |
| DEAL_REASON_CLIENT | Selects reason client in deal reason. | ENUM_DEAL_REASON | Enumerations | Exact adoption | DEAL_REASON_CLIENT | trading |
| DEAL_REASON_MOBILE | Selects reason mobile in deal reason. | ENUM_DEAL_REASON | Enumerations | Exact adoption | DEAL_REASON_MOBILE | trading |
| DEAL_REASON_WEB | Selects reason web in deal reason. | ENUM_DEAL_REASON | Enumerations | Exact adoption | DEAL_REASON_WEB | trading |
| DEAL_REASON_EXPERT | Selects reason expert in deal reason. | ENUM_DEAL_REASON | Enumerations | Platform-neutral rename | DEAL_REASON_AUTOMATION | trading |
| DEAL_REASON_SL | Selects reason SL in deal reason. | ENUM_DEAL_REASON | Enumerations | Exact adoption | DEAL_REASON_SL | trading |
| DEAL_REASON_TP | Selects reason TP in deal reason. | ENUM_DEAL_REASON | Enumerations | Exact adoption | DEAL_REASON_TP | trading |
| DEAL_REASON_SO | Selects reason so in deal reason. | ENUM_DEAL_REASON | Enumerations | Exact adoption | DEAL_REASON_SO | trading |
| DEAL_REASON_ROLLOVER | Selects reason rollover in deal reason. | ENUM_DEAL_REASON | Enumerations | Exact adoption | DEAL_REASON_ROLLOVER | trading |
| DEAL_REASON_VMARGIN | Selects reason vmargin in deal reason. | ENUM_DEAL_REASON | Enumerations | Exact adoption | DEAL_REASON_VMARGIN | trading |
| DEAL_REASON_SPLIT | Selects reason split in deal reason. | ENUM_DEAL_REASON | Enumerations | Exact adoption | DEAL_REASON_SPLIT | trading |
| DEAL_REASON_CORPORATE_ACTION | Selects reason corporate action in deal reason. | ENUM_DEAL_REASON | Enumerations | Exact adoption | DEAL_REASON_CORPORATE_ACTION | trading |
| ENUM_TRADE_REQUEST_ACTIONS | Defines the identifier set for trade request actions. | enum (int) | Enumerations | Exact adoption | ENUM_TRADE_REQUEST_ACTIONS | trading |
| TRADE_ACTION_DEAL | Selects deal in trade request actions. | ENUM_TRADE_REQUEST_ACTIONS | Enumerations | Exact adoption | TRADE_ACTION_DEAL | trading |
| TRADE_ACTION_PENDING | Selects pending in trade request actions. | ENUM_TRADE_REQUEST_ACTIONS | Enumerations | Exact adoption | TRADE_ACTION_PENDING | trading |
| TRADE_ACTION_SLTP | Selects sltp in trade request actions. | ENUM_TRADE_REQUEST_ACTIONS | Enumerations | Exact adoption | TRADE_ACTION_SLTP | trading |
| TRADE_ACTION_MODIFY | Selects modify in trade request actions. | ENUM_TRADE_REQUEST_ACTIONS | Enumerations | Exact adoption | TRADE_ACTION_MODIFY | trading |
| TRADE_ACTION_REMOVE | Selects remove in trade request actions. | ENUM_TRADE_REQUEST_ACTIONS | Enumerations | Exact adoption | TRADE_ACTION_REMOVE | trading |
| TRADE_ACTION_CLOSE_BY | Selects close by in trade request actions. | ENUM_TRADE_REQUEST_ACTIONS | Enumerations | Exact adoption | TRADE_ACTION_CLOSE_BY | trading |
| ENUM_TRADE_TRANSACTION_TYPE | Defines the identifier set for trade transaction type. | enum (int) | Enumerations | Exact adoption | ENUM_TRADE_TRANSACTION_TYPE | trading |
| TRADE_TRANSACTION_ORDER_ADD | Selects order add in trade transaction type. | ENUM_TRADE_TRANSACTION_TYPE | Enumerations | Exact adoption | TRADE_TRANSACTION_ORDER_ADD | trading |
| TRADE_TRANSACTION_ORDER_UPDATE | Selects order update in trade transaction type. | ENUM_TRADE_TRANSACTION_TYPE | Enumerations | Exact adoption | TRADE_TRANSACTION_ORDER_UPDATE | trading |
| TRADE_TRANSACTION_ORDER_DELETE | Selects order delete in trade transaction type. | ENUM_TRADE_TRANSACTION_TYPE | Enumerations | Exact adoption | TRADE_TRANSACTION_ORDER_DELETE | trading |
| TRADE_TRANSACTION_DEAL_ADD | Selects deal add in trade transaction type. | ENUM_TRADE_TRANSACTION_TYPE | Enumerations | Exact adoption | TRADE_TRANSACTION_DEAL_ADD | trading |
| TRADE_TRANSACTION_DEAL_UPDATE | Selects deal update in trade transaction type. | ENUM_TRADE_TRANSACTION_TYPE | Enumerations | Exact adoption | TRADE_TRANSACTION_DEAL_UPDATE | trading |
| TRADE_TRANSACTION_DEAL_DELETE | Selects deal delete in trade transaction type. | ENUM_TRADE_TRANSACTION_TYPE | Enumerations | Exact adoption | TRADE_TRANSACTION_DEAL_DELETE | trading |
| TRADE_TRANSACTION_HISTORY_ADD | Selects history add in trade transaction type. | ENUM_TRADE_TRANSACTION_TYPE | Enumerations | Exact adoption | TRADE_TRANSACTION_HISTORY_ADD | trading |
| TRADE_TRANSACTION_HISTORY_UPDATE | Selects history update in trade transaction type. | ENUM_TRADE_TRANSACTION_TYPE | Enumerations | Exact adoption | TRADE_TRANSACTION_HISTORY_UPDATE | trading |
| TRADE_TRANSACTION_HISTORY_DELETE | Selects history delete in trade transaction type. | ENUM_TRADE_TRANSACTION_TYPE | Enumerations | Exact adoption | TRADE_TRANSACTION_HISTORY_DELETE | trading |
| TRADE_TRANSACTION_POSITION | Selects position in trade transaction type. | ENUM_TRADE_TRANSACTION_TYPE | Enumerations | Exact adoption | TRADE_TRANSACTION_POSITION | trading |
| TRADE_TRANSACTION_REQUEST | Selects request in trade transaction type. | ENUM_TRADE_TRANSACTION_TYPE | Enumerations | Exact adoption | TRADE_TRANSACTION_REQUEST | trading |
| ENUM_BOOK_TYPE | Defines the identifier set for book type. | enum (int) | Enumerations | Exact adoption | ENUM_BOOK_TYPE | data |
| BOOK_TYPE_SELL | Selects type sell in book type. | ENUM_BOOK_TYPE | Enumerations | Exact adoption | BOOK_TYPE_SELL | data |
| BOOK_TYPE_BUY | Selects type buy in book type. | ENUM_BOOK_TYPE | Enumerations | Exact adoption | BOOK_TYPE_BUY | data |
| BOOK_TYPE_SELL_MARKET | Selects type sell market in book type. | ENUM_BOOK_TYPE | Enumerations | Exact adoption | BOOK_TYPE_SELL_MARKET | data |
| BOOK_TYPE_BUY_MARKET | Selects type buy market in book type. | ENUM_BOOK_TYPE | Enumerations | Exact adoption | BOOK_TYPE_BUY_MARKET | data |
| ENUM_SIGNAL_BASE_DOUBLE | Defines the identifier set for signal base double. Rejected because it belongs to the MQL5 Signals marketplace. | enum (int) | Enumerations | Rejected adoption | — | — |
| ENUM_SIGNAL_BASE_INTEGER | Defines the identifier set for signal base integer. Rejected because it belongs to the MQL5 Signals marketplace. | enum (int) | Enumerations | Rejected adoption | — | — |
| ENUM_SIGNAL_BASE_STRING | Defines the identifier set for signal base string. Rejected because it belongs to the MQL5 Signals marketplace. | enum (int) | Enumerations | Rejected adoption | — | — |
| SIGNAL_BASE_BALANCE | Selects signal base balance in signal base double. Rejected because it belongs to the MQL5 Signals marketplace. | ENUM_SIGNAL_BASE_DOUBLE | Enumerations | Rejected adoption | — | — |
| SIGNAL_BASE_EQUITY | Selects signal base equity in signal base double. Rejected because it belongs to the MQL5 Signals marketplace. | ENUM_SIGNAL_BASE_DOUBLE | Enumerations | Rejected adoption | — | — |
| SIGNAL_BASE_GAIN | Selects signal base gain in signal base double. Rejected because it belongs to the MQL5 Signals marketplace. | ENUM_SIGNAL_BASE_DOUBLE | Enumerations | Rejected adoption | — | — |
| SIGNAL_BASE_MAX_DRAWDOWN | Selects signal base max drawdown in signal base double. Rejected because it belongs to the MQL5 Signals marketplace. | ENUM_SIGNAL_BASE_DOUBLE | Enumerations | Rejected adoption | — | — |
| SIGNAL_BASE_PRICE | Selects signal base price in signal base double. Rejected because it belongs to the MQL5 Signals marketplace. | ENUM_SIGNAL_BASE_DOUBLE | Enumerations | Rejected adoption | — | — |
| SIGNAL_BASE_ROI | Selects signal base roi in signal base double. Rejected because it belongs to the MQL5 Signals marketplace. | ENUM_SIGNAL_BASE_DOUBLE | Enumerations | Rejected adoption | — | — |
| SIGNAL_BASE_DATE_PUBLISHED | Selects signal base date published in signal base integer. Rejected because it belongs to the MQL5 Signals marketplace. | ENUM_SIGNAL_BASE_INTEGER | Enumerations | Rejected adoption | — | — |
| SIGNAL_BASE_DATE_STARTED | Selects signal base date started in signal base integer. Rejected because it belongs to the MQL5 Signals marketplace. | ENUM_SIGNAL_BASE_INTEGER | Enumerations | Rejected adoption | — | — |
| SIGNAL_BASE_DATE_UPDATED | Selects signal base date updated in signal base integer. Rejected because it belongs to the MQL5 Signals marketplace. | ENUM_SIGNAL_BASE_INTEGER | Enumerations | Rejected adoption | — | — |
| SIGNAL_BASE_ID | Selects signal base ID in signal base integer. Rejected because it belongs to the MQL5 Signals marketplace. | ENUM_SIGNAL_BASE_INTEGER | Enumerations | Rejected adoption | — | — |
| SIGNAL_BASE_LEVERAGE | Selects signal base leverage in signal base integer. Rejected because it belongs to the MQL5 Signals marketplace. | ENUM_SIGNAL_BASE_INTEGER | Enumerations | Rejected adoption | — | — |
| SIGNAL_BASE_PIPS | Selects signal base pips in signal base integer. Rejected because it belongs to the MQL5 Signals marketplace. | ENUM_SIGNAL_BASE_INTEGER | Enumerations | Rejected adoption | — | — |
| SIGNAL_BASE_RATING | Selects signal base rating in signal base integer. Rejected because it belongs to the MQL5 Signals marketplace. | ENUM_SIGNAL_BASE_INTEGER | Enumerations | Rejected adoption | — | — |
| SIGNAL_BASE_SUBSCRIBERS | Selects signal base subscribers in signal base integer. Rejected because it belongs to the MQL5 Signals marketplace. | ENUM_SIGNAL_BASE_INTEGER | Enumerations | Rejected adoption | — | — |
| SIGNAL_BASE_TRADES | Selects signal base trades in signal base integer. Rejected because it belongs to the MQL5 Signals marketplace. | ENUM_SIGNAL_BASE_INTEGER | Enumerations | Rejected adoption | — | — |
| SIGNAL_BASE_TRADE_MODE | Selects signal base trade mode in signal base integer. Rejected because it belongs to the MQL5 Signals marketplace. | ENUM_SIGNAL_BASE_INTEGER | Enumerations | Rejected adoption | — | — |
| SIGNAL_BASE_AUTHOR_LOGIN | Selects signal base author login in signal base string. Rejected because it belongs to the MQL5 Signals marketplace. | ENUM_SIGNAL_BASE_STRING | Enumerations | Rejected adoption | — | — |
| SIGNAL_BASE_BROKER | Selects signal base broker in signal base string. Rejected because it belongs to the MQL5 Signals marketplace. | ENUM_SIGNAL_BASE_STRING | Enumerations | Rejected adoption | — | — |
| ENUM_SIGNAL_INFO_DOUBLE | Defines the identifier set for signal info double. Rejected because it belongs to the MQL5 Signals marketplace. | enum (int) | Enumerations | Rejected adoption | — | — |
| ENUM_SIGNAL_INFO_INTEGER | Defines the identifier set for signal info integer. Rejected because it belongs to the MQL5 Signals marketplace. | enum (int) | Enumerations | Rejected adoption | — | — |
| ENUM_SIGNAL_INFO_STRING | Defines the identifier set for signal info string. Rejected because it belongs to the MQL5 Signals marketplace. | enum (int) | Enumerations | Rejected adoption | — | — |
| SIGNAL_BASE_BROKER_SERVER | Selects signal base broker server in signal base string. Rejected because it belongs to the MQL5 Signals marketplace. | ENUM_SIGNAL_BASE_STRING | Enumerations | Rejected adoption | — | — |
| SIGNAL_BASE_NAME | Selects signal base name in signal base string. Rejected because it belongs to the MQL5 Signals marketplace. | ENUM_SIGNAL_BASE_STRING | Enumerations | Rejected adoption | — | — |
| SIGNAL_BASE_CURRENCY | Selects signal base currency in signal base string. Rejected because it belongs to the MQL5 Signals marketplace. | ENUM_SIGNAL_BASE_STRING | Enumerations | Rejected adoption | — | — |
| SIGNAL_INFO_EQUITY_LIMIT | Selects signal info equity limit in signal info double. Rejected because it belongs to the MQL5 Signals marketplace. | ENUM_SIGNAL_INFO_DOUBLE | Enumerations | Rejected adoption | — | — |
| SIGNAL_INFO_SLIPPAGE | Selects signal info slippage in signal info double. Rejected because it belongs to the MQL5 Signals marketplace. | ENUM_SIGNAL_INFO_DOUBLE | Enumerations | Rejected adoption | — | — |
| SIGNAL_INFO_VOLUME_PERCENT | Selects signal info volume percent in signal info double. Rejected because it belongs to the MQL5 Signals marketplace. | ENUM_SIGNAL_INFO_DOUBLE | Enumerations | Rejected adoption | — | — |
| SIGNAL_INFO_CONFIRMATIONS_DISABLED | Selects signal info confirmations disabled in signal info integer. Rejected because it belongs to the MQL5 Signals marketplace. | ENUM_SIGNAL_INFO_INTEGER | Enumerations | Rejected adoption | — | — |
| SIGNAL_INFO_COPY_SLTP | Selects signal info copy sltp in signal info integer. Rejected because it belongs to the MQL5 Signals marketplace. | ENUM_SIGNAL_INFO_INTEGER | Enumerations | Rejected adoption | — | — |
| SIGNAL_INFO_DEPOSIT_PERCENT | Selects signal info deposit percent in signal info integer. Rejected because it belongs to the MQL5 Signals marketplace. | ENUM_SIGNAL_INFO_INTEGER | Enumerations | Rejected adoption | — | — |
| SIGNAL_INFO_ID | Selects signal info ID in signal info integer. Rejected because it belongs to the MQL5 Signals marketplace. | ENUM_SIGNAL_INFO_INTEGER | Enumerations | Rejected adoption | — | — |
| SIGNAL_INFO_SUBSCRIPTION_ENABLED | Selects signal info subscription enabled in signal info integer. Rejected because it belongs to the MQL5 Signals marketplace. | ENUM_SIGNAL_INFO_INTEGER | Enumerations | Rejected adoption | — | — |
| SIGNAL_INFO_TERMS_AGREE | Selects signal info terms agree in signal info integer. Rejected because it belongs to the MQL5 Signals marketplace. | ENUM_SIGNAL_INFO_INTEGER | Enumerations | Rejected adoption | — | — |
| SIGNAL_INFO_NAME | Selects signal info name in signal info string. Rejected because it belongs to the MQL5 Signals marketplace. | ENUM_SIGNAL_INFO_STRING | Enumerations | Rejected adoption | — | — |
| __CPU_ARCHITECTURE__ | Provides the compile-time CPU architecture macro value. Rejected because it is an MQL5 compiler substitution. | Not specified in reference | Constants | Rejected adoption | — | — |
| __DATE__ | Provides the compile-time date macro value. Rejected because it is an MQL5 compiler substitution. | Not specified in reference | Constants | Rejected adoption | — | — |
| __DATETIME__ | Provides the compile-time datetime macro value. Rejected because it is an MQL5 compiler substitution. | Not specified in reference | Constants | Rejected adoption | — | — |
| __LINE__ | Provides the compile-time line macro value. Rejected because it is an MQL5 compiler substitution. | Not specified in reference | Constants | Rejected adoption | — | — |
| __FILE__ | Provides the compile-time file macro value. Rejected because it is an MQL5 compiler substitution. | Not specified in reference | Constants | Rejected adoption | — | — |
| __PATH__ | Provides the compile-time path macro value. Rejected because it is an MQL5 compiler substitution. | Not specified in reference | Constants | Rejected adoption | — | — |
| __FUNCTION__ | Provides the compile-time function macro value. Rejected because it is an MQL5 compiler substitution. | Not specified in reference | Constants | Rejected adoption | — | — |
| __FUNCSIG__ | Provides the compile-time funcsig macro value. Rejected because it is an MQL5 compiler substitution. | Not specified in reference | Constants | Rejected adoption | — | — |
| __MQLBUILD__ | Provides the compile-time mqlbuild macro value. Rejected because it is an MQL5 compiler substitution. | Not specified in reference | Constants | Rejected adoption | — | — |
| __MQL5BUILD__ | Provides the compile-time MQL5 build macro value. Rejected because it is an MQL5 compiler substitution. | Not specified in reference | Constants | Rejected adoption | — | — |
| __COUNTER__ | Provides the compile-time counter macro value. Rejected because it is an MQL5 compiler substitution. | Not specified in reference | Constants | Rejected adoption | — | — |
| __RANDOM__ | Provides the compile-time random macro value. Rejected because it is an MQL5 compiler substitution. | Not specified in reference | Constants | Rejected adoption | — | — |
| M_E | Value: 2.71828182845904523536. Represents m e. | Not specified in reference | Constants | Exact adoption | M_E | common |
| M_LOG2E | Value: 1.44269504088896340736. Represents m log2 e. | Not specified in reference | Constants | Exact adoption | M_LOG2E | common |
| M_LOG10E | Value: 0.434294481903251827651. Represents m log10 e. | Not specified in reference | Constants | Exact adoption | M_LOG10E | common |
| M_LN2 | Value: 0.693147180559945309417. Represents m ln2. | Not specified in reference | Constants | Exact adoption | M_LN2 | common |
| M_LN10 | Value: 2.30258509299404568402. Represents m ln10. | Not specified in reference | Constants | Exact adoption | M_LN10 | common |
| M_PI | Value: 3.14159265358979323846. Represents m pi. | Not specified in reference | Constants | Exact adoption | M_PI | common |
| M_PI_2 | Value: 1.57079632679489661923. Represents m pi 2. | Not specified in reference | Constants | Exact adoption | M_PI_2 | common |
| M_PI_4 | Value: 0.785398163397448309616. Represents m pi 4. | Not specified in reference | Constants | Exact adoption | M_PI_4 | common |
| M_1_PI | Value: 0.318309886183790671538. Represents m 1 pi. | Not specified in reference | Constants | Exact adoption | M_1_PI | common |
| M_2_PI | Value: 0.636619772367581343076. Represents m 2 pi. | Not specified in reference | Constants | Exact adoption | M_2_PI | common |
| M_2_SQRTPI | Value: 1.12837916709551257390. Represents m 2 sqrtpi. | Not specified in reference | Constants | Exact adoption | M_2_SQRTPI | common |
| M_SQRT2 | Value: 1.41421356237309504880. Represents m sqrt2. | Not specified in reference | Constants | Exact adoption | M_SQRT2 | common |
| M_SQRT1_2 | Value: 0.707106781186547524401. Represents m sqrt1 2. | Not specified in reference | Constants | Exact adoption | M_SQRT1_2 | common |
| CHAR_MIN | Value: -128. Represents char min. | Not specified in reference | Constants | Exact adoption | CHAR_MIN | common |
| CHAR_MAX | Value: 127. Represents char max. | Not specified in reference | Constants | Exact adoption | CHAR_MAX | common |
| UCHAR_MAX | Value: 255. Represents uchar max. | Not specified in reference | Constants | Exact adoption | UCHAR_MAX | common |
| SHORT_MIN | Value: -32768. Represents short min. | Not specified in reference | Constants | Exact adoption | SHORT_MIN | common |
| SHORT_MAX | Value: 32767. Represents short max. | Not specified in reference | Constants | Exact adoption | SHORT_MAX | common |
| USHORT_MAX | Value: 65535. Represents ushort max. | Not specified in reference | Constants | Exact adoption | USHORT_MAX | common |
| INT_MIN | Value: -2147483648. Represents int min. | Not specified in reference | Constants | Exact adoption | INT_MIN | common |
| INT_MAX | Value: 2147483647. Represents int max. | Not specified in reference | Constants | Exact adoption | INT_MAX | common |
| UINT_MAX | Value: 4294967295. Represents uint max. | Not specified in reference | Constants | Exact adoption | UINT_MAX | common |
| LONG_MIN | Value: -9223372036854775808. Represents long min. | Not specified in reference | Constants | Exact adoption | LONG_MIN | common |
| LONG_MAX | Value: 9223372036854775807. Represents long max. | Not specified in reference | Constants | Exact adoption | LONG_MAX | common |
| ULONG_MAX | Value: 18446744073709551615. Represents ulong max. | Not specified in reference | Constants | Exact adoption | ULONG_MAX | common |
| DBL_MIN | Value: 2.2250738585072014e-308. Represents dbl min. | Not specified in reference | Constants | Exact adoption | DBL_MIN | common |
| DBL_MAX | Value: 1.7976931348623158e+308. Represents dbl max. | Not specified in reference | Constants | Exact adoption | DBL_MAX | common |
| DBL_EPSILON | Value: 2.2204460492503131e-016. Represents dbl epsilon. | Not specified in reference | Constants | Exact adoption | DBL_EPSILON | common |
| DBL_DIG | Value: 15. Represents dbl dig. | Not specified in reference | Constants | Exact adoption | DBL_DIG | common |
| DBL_MANT_DIG | Value: 53. Represents dbl mant dig. | Not specified in reference | Constants | Exact adoption | DBL_MANT_DIG | common |
| DBL_MAX_10_EXP | Value: 308. Represents dbl max 10 exp. | Not specified in reference | Constants | Exact adoption | DBL_MAX_10_EXP | common |
| DBL_MAX_EXP | Value: 1024. Represents dbl max exp. | Not specified in reference | Constants | Exact adoption | DBL_MAX_EXP | common |
| DBL_MIN_10_EXP | Value: (-307). Represents dbl min 10 exp. | Not specified in reference | Constants | Exact adoption | DBL_MIN_10_EXP | common |
| DBL_MIN_EXP | Value: (-1021). Represents dbl min exp. | Not specified in reference | Constants | Exact adoption | DBL_MIN_EXP | common |
| FLT_MIN | Value: 1.175494351e-38. Represents flt min. | Not specified in reference | Constants | Exact adoption | FLT_MIN | common |
| FLT_MAX | Value: 3.402823466e+38. Represents flt max. | Not specified in reference | Constants | Exact adoption | FLT_MAX | common |
| FLT_EPSILON | Value: 1.192092896e–07. Represents flt epsilon. | Not specified in reference | Constants | Exact adoption | FLT_EPSILON | common |
| FLT_DIG | Value: 6. Represents flt dig. | Not specified in reference | Constants | Exact adoption | FLT_DIG | common |
| FLT_MANT_DIG | Value: 24. Represents flt mant dig. | Not specified in reference | Constants | Exact adoption | FLT_MANT_DIG | common |
| FLT_MAX_10_EXP | Value: 38. Represents flt max 10 exp. | Not specified in reference | Constants | Exact adoption | FLT_MAX_10_EXP | common |
| FLT_MAX_EXP | Value: 128. Represents flt max exp. | Not specified in reference | Constants | Exact adoption | FLT_MAX_EXP | common |
| FLT_MIN_10_EXP | Value: -37. Represents flt min 10 exp. | Not specified in reference | Constants | Exact adoption | FLT_MIN_10_EXP | common |
| FLT_MIN_EXP | Value: (-125). Represents flt min exp. | Not specified in reference | Constants | Exact adoption | FLT_MIN_EXP | common |
| REASON_PROGRAM | Value: 0. Represents reason program. | Not specified in reference | Constants | Platform-neutral rename | SHUTDOWN_REASON_PROGRAM | plugins |
| REASON_REMOVE | Value: 1. Represents reason remove. | Not specified in reference | Constants | Platform-neutral rename | SHUTDOWN_REASON_REMOVE | plugins |
| REASON_RECOMPILE | Value: 2. Represents reason recompile. | Not specified in reference | Constants | Platform-neutral rename | SHUTDOWN_REASON_RECOMPILE | plugins |
| REASON_CHARTCHANGE | Value: 3. Represents reason chartchange. | Not specified in reference | Constants | Platform-neutral rename | SHUTDOWN_REASON_CHARTCHANGE | plugins |
| REASON_CHARTCLOSE | Value: 4. Represents reason chartclose. | Not specified in reference | Constants | Platform-neutral rename | SHUTDOWN_REASON_CHARTCLOSE | plugins |
| REASON_PARAMETERS | Value: 5. Represents reason parameters. | Not specified in reference | Constants | Platform-neutral rename | SHUTDOWN_REASON_PARAMETERS | plugins |
| REASON_ACCOUNT | Value: 6. Represents reason account. | Not specified in reference | Constants | Platform-neutral rename | SHUTDOWN_REASON_ACCOUNT | plugins |
| REASON_TEMPLATE | Value: 7. Represents reason template. | Not specified in reference | Constants | Platform-neutral rename | SHUTDOWN_REASON_TEMPLATE | plugins |
| REASON_INITFAILED | Value: 8. Represents reason initfailed. | Not specified in reference | Constants | Platform-neutral rename | SHUTDOWN_REASON_INITFAILED | plugins |
| REASON_CLOSE | Value: 9. Represents reason close. | Not specified in reference | Constants | Platform-neutral rename | SHUTDOWN_REASON_CLOSE | plugins |
| ENUM_POINTER_TYPE | Defines the identifier set for pointer type. Rejected because it exposes MQL5 pointer-management semantics. | enum (int) | Enumerations | Rejected adoption | — | — |
| POINTER_INVALID | Selects invalid in pointer type. Rejected because it exposes MQL5 pointer-management semantics. | ENUM_POINTER_TYPE | Enumerations | Rejected adoption | — | — |
| POINTER_DYNAMIC | Selects dynamic in pointer type. Rejected because it exposes MQL5 pointer-management semantics. | ENUM_POINTER_TYPE | Enumerations | Rejected adoption | — | — |
| POINTER_AUTOMATIC | Selects automatic in pointer type. Rejected because it exposes MQL5 pointer-management semantics. | ENUM_POINTER_TYPE | Enumerations | Rejected adoption | — | — |
| CHARTS_MAX | Value: 100. Represents charts max. | Not specified in reference | Constants | Exact adoption | CHARTS_MAX | ui |
| clrNONE | Value: -1. Provides the predefined NONE UI color. | Not specified in reference | Constants | Exact adoption | clrNONE | common |
| EMPTY_VALUE | Value: DBL_MAX. Represents empty value. | Not specified in reference | Constants | Exact adoption | EMPTY_VALUE | common |
| INVALID_HANDLE | Value: -1. Represents invalid handle. | Not specified in reference | Constants | Exact adoption | INVALID_HANDLE | common |
| IS_DEBUG_MODE | Value: non zero in debug mode, otherwise zero. Represents is debug mode. | Not specified in reference | Constants | Exact adoption | IS_DEBUG_MODE | common |
| IS_PROFILE_MODE | Value: non zero in profiling mode, otherwise zero. Represents is profile mode. | Not specified in reference | Constants | Exact adoption | IS_PROFILE_MODE | common |
| NULL | Value: 0. Represents null. | Not specified in reference | Constants | Exact adoption | NULL | common |
| WHOLE_ARRAY | Value: -1. Represents whole array. | Not specified in reference | Constants | Exact adoption | WHOLE_ARRAY | common |
| WRONG_VALUE | Value: -1. Represents wrong value. | Not specified in reference | Constants | Exact adoption | WRONG_VALUE | common |
| ENUM_CRYPT_METHOD | Defines the identifier set for crypt method. HaruQuantAI adds managed I/O and explicit security policy. | enum (int) | Enumerations | Semantic extension | ENUM_CRYPT_METHOD | interfaces |
| CRYPT_BASE64 | Selects base64 in crypt method. HaruQuantAI adds managed I/O and explicit security policy. | ENUM_CRYPT_METHOD | Enumerations | Semantic extension | CRYPT_BASE64 | interfaces |
| CRYPT_AES128 | Selects AES128 in crypt method. HaruQuantAI adds managed I/O and explicit security policy. | ENUM_CRYPT_METHOD | Enumerations | Semantic extension | CRYPT_AES128 | interfaces |
| CRYPT_AES256 | Selects AES256 in crypt method. HaruQuantAI adds managed I/O and explicit security policy. | ENUM_CRYPT_METHOD | Enumerations | Semantic extension | CRYPT_AES256 | interfaces |
| CRYPT_DES | Selects des in crypt method. Rejected because the legacy algorithm is outside HaruQuantAI security policy. | ENUM_CRYPT_METHOD | Enumerations | Rejected adoption | — | — |
| CRYPT_HASH_SHA1 | Selects hash SHA1 in crypt method. Rejected because the legacy algorithm is outside HaruQuantAI security policy. | ENUM_CRYPT_METHOD | Enumerations | Rejected adoption | — | — |
| CRYPT_HASH_SHA256 | Selects hash SHA256 in crypt method. HaruQuantAI adds managed I/O and explicit security policy. | ENUM_CRYPT_METHOD | Enumerations | Semantic extension | CRYPT_HASH_SHA256 | interfaces |
| CRYPT_HASH_MD5 | Selects hash MD5 in crypt method. Rejected because the legacy algorithm is outside HaruQuantAI security policy. | ENUM_CRYPT_METHOD | Enumerations | Rejected adoption | — | — |
| CRYPT_ARCH_ZIP | Selects arch ZIP in crypt method. HaruQuantAI adds managed I/O and explicit security policy. | ENUM_CRYPT_METHOD | Enumerations | Semantic extension | CRYPT_ARCH_ZIP | interfaces |
| MqlDateTime | Carries the date time parts data record. | struct | Structures | Platform-neutral rename | DateTimeParts | common |
| MqlDateTime.year | Stores year in DateTimeParts. | int | Structures | Platform-neutral rename | DateTimeParts.year | common |
| MqlDateTime.mon | Stores mon in DateTimeParts. | int | Structures | Platform-neutral rename | DateTimeParts.month | common |
| MqlDateTime.day | Stores day in DateTimeParts. | int | Structures | Platform-neutral rename | DateTimeParts.day | common |
| MqlDateTime.hour | Stores hour in DateTimeParts. | int | Structures | Platform-neutral rename | DateTimeParts.hour | common |
| MqlDateTime.min | Stores min in DateTimeParts. | int | Structures | Platform-neutral rename | DateTimeParts.min | common |
| MqlDateTime.sec | Stores sec in DateTimeParts. | int | Structures | Platform-neutral rename | DateTimeParts.sec | common |
| MqlDateTime.day_of_week | Stores day of week in DateTimeParts. | int | Structures | Platform-neutral rename | DateTimeParts.day_of_week | common |
| MqlDateTime.day_of_year | Stores day of year in DateTimeParts. | int | Structures | Platform-neutral rename | DateTimeParts.day_of_year | common |
| MqlParam | Carries the indicator parameter data record. | struct | Structures | Platform-neutral rename | IndicatorParameter | indicator |
| MqlParam.type | Stores type in IndicatorParameter. | ENUM_DATATYPE | Structures | Platform-neutral rename | IndicatorParameter.type | indicator |
| MqlParam.integer_value | Stores integer value in IndicatorParameter. | long | Structures | Platform-neutral rename | IndicatorParameter.integer_value | indicator |
| MqlParam.double_value | Stores double value in IndicatorParameter. | double | Structures | Platform-neutral rename | IndicatorParameter.double_value | indicator |
| MqlParam.string_value | Stores string value in IndicatorParameter. | string | Structures | Platform-neutral rename | IndicatorParameter.string_value | indicator |
| MqlRates | Carries the rate bar data record. | struct | Structures | Platform-neutral rename | RateBar | data |
| MqlRates.time | Stores time in RateBar. | datetime | Structures | Platform-neutral rename | RateBar.time | data |
| MqlRates.open | Stores open in RateBar. | double | Structures | Platform-neutral rename | RateBar.open | data |
| MqlRates.high | Stores high in RateBar. | double | Structures | Platform-neutral rename | RateBar.high | data |
| MqlRates.low | Stores low in RateBar. | double | Structures | Platform-neutral rename | RateBar.low | data |
| MqlRates.close | Stores close in RateBar. | double | Structures | Platform-neutral rename | RateBar.close | data |
| MqlRates.tick_volume | Stores tick volume in RateBar. | long | Structures | Platform-neutral rename | RateBar.tick_volume | data |
| MqlRates.spread | Stores spread in RateBar. | int | Structures | Platform-neutral rename | RateBar.spread | data |
| MqlRates.real_volume | Stores real volume in RateBar. | long | Structures | Platform-neutral rename | RateBar.real_volume | data |
| MqlBookInfo | Carries the order book entry data record. | struct | Structures | Platform-neutral rename | OrderBookEntry | data |
| MqlBookInfo.type | Stores type in OrderBookEntry. | ENUM_BOOK_TYPE | Structures | Platform-neutral rename | OrderBookEntry.type | data |
| MqlBookInfo.price | Stores price in OrderBookEntry. | double | Structures | Platform-neutral rename | OrderBookEntry.price | data |
| MqlBookInfo.volume | Stores volume in OrderBookEntry. | long | Structures | Platform-neutral rename | OrderBookEntry.volume | data |
| MqlBookInfo.volume_real | Stores volume real in OrderBookEntry. | double | Structures | Platform-neutral rename | OrderBookEntry.volume_real | data |
| MqlTradeRequest | Carries the trade request data record. | struct | Structures | Platform-neutral rename | TradeRequest | trading |
| MqlTradeRequest.action | Stores action in TradeRequest. | ENUM_TRADE_REQUEST_ACTIONS | Structures | Platform-neutral rename | TradeRequest.action | trading |
| MqlTradeRequest.magic | Stores magic in TradeRequest. | ulong | Structures | Platform-neutral rename | TradeRequest.magic | trading |
| MqlTradeRequest.order | Stores order in TradeRequest. | ulong | Structures | Platform-neutral rename | TradeRequest.order | trading |
| MqlTradeRequest.symbol | Stores symbol in TradeRequest. | string | Structures | Platform-neutral rename | TradeRequest.symbol | trading |
| MqlTradeRequest.volume | Stores volume in TradeRequest. | double | Structures | Platform-neutral rename | TradeRequest.volume | trading |
| MqlTradeRequest.price | Stores price in TradeRequest. | double | Structures | Platform-neutral rename | TradeRequest.price | trading |
| MqlTradeRequest.stoplimit | Stores stoplimit in TradeRequest. | double | Structures | Platform-neutral rename | TradeRequest.stoplimit | trading |
| MqlTradeRequest.sl | Stores sl in TradeRequest. | double | Structures | Platform-neutral rename | TradeRequest.sl | trading |
| MqlTradeRequest.tp | Stores tp in TradeRequest. | double | Structures | Platform-neutral rename | TradeRequest.tp | trading |
| MqlTradeRequest.deviation | Stores deviation in TradeRequest. | ulong | Structures | Platform-neutral rename | TradeRequest.deviation | trading |
| MqlTradeRequest.type | Stores type in TradeRequest. | ENUM_ORDER_TYPE | Structures | Platform-neutral rename | TradeRequest.type | trading |
| MqlTradeRequest.type_filling | Stores type filling in TradeRequest. | ENUM_ORDER_TYPE_FILLING | Structures | Platform-neutral rename | TradeRequest.type_filling | trading |
| MqlTradeRequest.type_time | Stores type time in TradeRequest. | ENUM_ORDER_TYPE_TIME | Structures | Platform-neutral rename | TradeRequest.type_time | trading |
| MqlTradeRequest.expiration | Stores expiration in TradeRequest. | datetime | Structures | Platform-neutral rename | TradeRequest.expiration | trading |
| MqlTradeRequest.comment | Stores comment in TradeRequest. | string | Structures | Platform-neutral rename | TradeRequest.comment | trading |
| MqlTradeRequest.position | Stores position in TradeRequest. | ulong | Structures | Platform-neutral rename | TradeRequest.position | trading |
| MqlTradeRequest.position_by | Stores position by in TradeRequest. | ulong | Structures | Platform-neutral rename | TradeRequest.position_by | trading |
| MqlTradeCheckResult | Carries the trade check result data record. | struct | Structures | Platform-neutral rename | TradeCheckResult | risk |
| MqlTradeCheckResult.retcode | Stores retcode in TradeCheckResult. | uint | Structures | Platform-neutral rename | TradeCheckResult.retcode | risk |
| MqlTradeCheckResult.balance | Stores balance in TradeCheckResult. | double | Structures | Platform-neutral rename | TradeCheckResult.balance | risk |
| MqlTradeCheckResult.equity | Stores equity in TradeCheckResult. | double | Structures | Platform-neutral rename | TradeCheckResult.equity | risk |
| MqlTradeCheckResult.profit | Stores profit in TradeCheckResult. | double | Structures | Platform-neutral rename | TradeCheckResult.profit | risk |
| MqlTradeCheckResult.margin | Stores margin in TradeCheckResult. | double | Structures | Platform-neutral rename | TradeCheckResult.margin | risk |
| MqlTradeCheckResult.margin_free | Stores margin free in TradeCheckResult. | double | Structures | Platform-neutral rename | TradeCheckResult.margin_free | risk |
| MqlTradeCheckResult.margin_level | Stores margin level in TradeCheckResult. | double | Structures | Platform-neutral rename | TradeCheckResult.margin_level | risk |
| MqlTradeCheckResult.comment | Stores comment in TradeCheckResult. | string | Structures | Platform-neutral rename | TradeCheckResult.comment | risk |
| MqlTradeResult | Carries the trade result data record. | struct | Structures | Platform-neutral rename | TradeResult | broker |
| MqlTradeResult.retcode | Stores retcode in TradeResult. | uint | Structures | Platform-neutral rename | TradeResult.retcode | broker |
| MqlTradeResult.deal | Stores deal in TradeResult. | ulong | Structures | Platform-neutral rename | TradeResult.deal | broker |
| MqlTradeResult.order | Stores order in TradeResult. | ulong | Structures | Platform-neutral rename | TradeResult.order | broker |
| MqlTradeResult.volume | Stores volume in TradeResult. | double | Structures | Platform-neutral rename | TradeResult.volume | broker |
| MqlTradeResult.price | Stores price in TradeResult. | double | Structures | Platform-neutral rename | TradeResult.price | broker |
| MqlTradeResult.bid | Stores bid in TradeResult. | double | Structures | Platform-neutral rename | TradeResult.bid | broker |
| MqlTradeResult.ask | Stores ask in TradeResult. | double | Structures | Platform-neutral rename | TradeResult.ask | broker |
| MqlTradeResult.comment | Stores comment in TradeResult. | string | Structures | Platform-neutral rename | TradeResult.comment | broker |
| MqlTradeResult.request_id | Stores request id in TradeResult. | uint | Structures | Platform-neutral rename | TradeResult.request_id | broker |
| MqlTradeResult.retcode_external | Stores retcode external in TradeResult. | int | Structures | Platform-neutral rename | TradeResult.retcode_external | broker |
| MqlTradeTransaction | Carries the trade transaction data record. | struct | Structures | Platform-neutral rename | TradeTransaction | trading |
| MqlTradeTransaction.deal | Stores deal in TradeTransaction. | ulong | Structures | Platform-neutral rename | TradeTransaction.deal | trading |
| MqlTradeTransaction.order | Stores order in TradeTransaction. | ulong | Structures | Platform-neutral rename | TradeTransaction.order | trading |
| MqlTradeTransaction.symbol | Stores symbol in TradeTransaction. | string | Structures | Platform-neutral rename | TradeTransaction.symbol | trading |
| MqlTradeTransaction.type | Stores type in TradeTransaction. | ENUM_TRADE_TRANSACTION_TYPE | Structures | Platform-neutral rename | TradeTransaction.type | trading |
| MqlTradeTransaction.order_type | Stores order type in TradeTransaction. | ENUM_ORDER_TYPE | Structures | Platform-neutral rename | TradeTransaction.order_type | trading |
| MqlTradeTransaction.order_state | Stores order state in TradeTransaction. | ENUM_ORDER_STATE | Structures | Platform-neutral rename | TradeTransaction.order_state | trading |
| MqlTradeTransaction.deal_type | Stores deal type in TradeTransaction. | ENUM_DEAL_TYPE | Structures | Platform-neutral rename | TradeTransaction.deal_type | trading |
| MqlTradeTransaction.time_type | Stores time type in TradeTransaction. | ENUM_ORDER_TYPE_TIME | Structures | Platform-neutral rename | TradeTransaction.time_type | trading |
| MqlTradeTransaction.time_expiration | Stores time expiration in TradeTransaction. | datetime | Structures | Platform-neutral rename | TradeTransaction.time_expiration | trading |
| MqlTradeTransaction.price | Stores price in TradeTransaction. | double | Structures | Platform-neutral rename | TradeTransaction.price | trading |
| MqlTradeTransaction.price_trigger | Stores price trigger in TradeTransaction. | double | Structures | Platform-neutral rename | TradeTransaction.price_trigger | trading |
| MqlTradeTransaction.price_sl | Stores price sl in TradeTransaction. | double | Structures | Platform-neutral rename | TradeTransaction.price_sl | trading |
| MqlTradeTransaction.price_tp | Stores price tp in TradeTransaction. | double | Structures | Platform-neutral rename | TradeTransaction.price_tp | trading |
| MqlTradeTransaction.volume | Stores volume in TradeTransaction. | double | Structures | Platform-neutral rename | TradeTransaction.volume | trading |
| MqlTradeTransaction.position | Stores position in TradeTransaction. | ulong | Structures | Platform-neutral rename | TradeTransaction.position | trading |
| MqlTradeTransaction.position_by | Stores position by in TradeTransaction. | ulong | Structures | Platform-neutral rename | TradeTransaction.position_by | trading |
| MqlTick | Carries the tick data record. | struct | Structures | Platform-neutral rename | Tick | data |
| MqlTick.time | Stores time in Tick. | datetime | Structures | Platform-neutral rename | Tick.time | data |
| MqlTick.bid | Stores bid in Tick. | double | Structures | Platform-neutral rename | Tick.bid | data |
| MqlTick.ask | Stores ask in Tick. | double | Structures | Platform-neutral rename | Tick.ask | data |
| MqlTick.last | Stores last in Tick. | double | Structures | Platform-neutral rename | Tick.last | data |
| MqlTick.volume | Stores volume in Tick. | ulong | Structures | Platform-neutral rename | Tick.volume | data |
| MqlTick.time_msc | Stores time msc in Tick. | long | Structures | Platform-neutral rename | Tick.time_msc | data |
| MqlTick.flags | Stores flags in Tick. | uint | Structures | Platform-neutral rename | Tick.flags | data |
| MqlTick.volume_real | Stores volume real in Tick. | double | Structures | Platform-neutral rename | Tick.volume_real | data |
| MqlCalendarCountry | Carries the calendar country data record. | struct | Structures | Platform-neutral rename | CalendarCountry | data |
| MqlCalendarCountry.id | Stores id in CalendarCountry. | ulong | Structures | Platform-neutral rename | CalendarCountry.id | data |
| MqlCalendarCountry.name | Stores name in CalendarCountry. | string | Structures | Platform-neutral rename | CalendarCountry.name | data |
| MqlCalendarCountry.code | Stores code in CalendarCountry. | string | Structures | Platform-neutral rename | CalendarCountry.code | data |
| MqlCalendarCountry.currency | Stores currency in CalendarCountry. | string | Structures | Platform-neutral rename | CalendarCountry.currency | data |
| MqlCalendarCountry.currency_symbol | Stores currency symbol in CalendarCountry. | string | Structures | Platform-neutral rename | CalendarCountry.currency_symbol | data |
| MqlCalendarCountry.url_name | Stores url name in CalendarCountry. | string | Structures | Platform-neutral rename | CalendarCountry.url_name | data |
| MqlCalendarEvent | Carries the calendar event data record. | struct | Structures | Platform-neutral rename | CalendarEvent | data |
| MqlCalendarEvent.id | Stores id in CalendarEvent. | ulong | Structures | Platform-neutral rename | CalendarEvent.id | data |
| MqlCalendarEvent.type | Stores type in CalendarEvent. | ENUM_CALENDAR_EVENT_TYPE | Structures | Platform-neutral rename | CalendarEvent.type | data |
| MqlCalendarEvent.sector | Stores sector in CalendarEvent. | ENUM_CALENDAR_EVENT_SECTOR | Structures | Platform-neutral rename | CalendarEvent.sector | data |
| MqlCalendarEvent.frequency | Stores frequency in CalendarEvent. | ENUM_CALENDAR_EVENT_FREQUENCY | Structures | Platform-neutral rename | CalendarEvent.frequency | data |
| MqlCalendarEvent.time_mode | Stores time mode in CalendarEvent. | ENUM_CALENDAR_EVENT_TIMEMODE | Structures | Platform-neutral rename | CalendarEvent.time_mode | data |
| MqlCalendarEvent.country_id | Stores country id in CalendarEvent. | ulong | Structures | Platform-neutral rename | CalendarEvent.country_id | data |
| MqlCalendarEvent.unit | Stores unit in CalendarEvent. | ENUM_CALENDAR_EVENT_UNIT | Structures | Platform-neutral rename | CalendarEvent.unit | data |
| MqlCalendarEvent.importance | Stores importance in CalendarEvent. | ENUM_CALENDAR_EVENT_IMPORTANCE | Structures | Platform-neutral rename | CalendarEvent.importance | data |
| MqlCalendarEvent.multiplier | Stores multiplier in CalendarEvent. | ENUM_CALENDAR_EVENT_MULTIPLIER | Structures | Platform-neutral rename | CalendarEvent.multiplier | data |
| MqlCalendarEvent.digits | Stores digits in CalendarEvent. | uint | Structures | Platform-neutral rename | CalendarEvent.digits | data |
| MqlCalendarEvent.source_url | Stores source url in CalendarEvent. | string | Structures | Platform-neutral rename | CalendarEvent.source_url | data |
| MqlCalendarEvent.event_code | Stores event code in CalendarEvent. | string | Structures | Platform-neutral rename | CalendarEvent.event_code | data |
| MqlCalendarEvent.name | Stores name in CalendarEvent. | string | Structures | Platform-neutral rename | CalendarEvent.name | data |
| MqlCalendarValue | Carries the calendar value data record. | struct | Structures | Platform-neutral rename | CalendarValue | data |
| MqlCalendarValue.id | Stores id in CalendarValue. | ulong | Structures | Platform-neutral rename | CalendarValue.id | data |
| MqlCalendarValue.event_id | Stores event id in CalendarValue. | ulong | Structures | Platform-neutral rename | CalendarValue.event_id | data |
| MqlCalendarValue.time | Stores time in CalendarValue. | datetime | Structures | Platform-neutral rename | CalendarValue.time | data |
| MqlCalendarValue.period | Stores period in CalendarValue. | datetime | Structures | Platform-neutral rename | CalendarValue.period | data |
| MqlCalendarValue.revision | Stores revision in CalendarValue. | int | Structures | Platform-neutral rename | CalendarValue.revision | data |
| MqlCalendarValue.actual_value | Stores actual value in CalendarValue. | long | Structures | Platform-neutral rename | CalendarValue.actual_value | data |
| MqlCalendarValue.prev_value | Stores prev value in CalendarValue. | long | Structures | Platform-neutral rename | CalendarValue.prev_value | data |
| MqlCalendarValue.revised_prev_value | Stores revised prev value in CalendarValue. | long | Structures | Platform-neutral rename | CalendarValue.revised_prev_value | data |
| MqlCalendarValue.forecast_value | Stores forecast value in CalendarValue. | long | Structures | Platform-neutral rename | CalendarValue.forecast_value | data |
| MqlCalendarValue.impact_type | Stores impact type in CalendarValue. | ENUM_CALENDAR_EVENT_IMPACT | Structures | Platform-neutral rename | CalendarValue.impact_type | data |
| ENUM_CALENDAR_EVENT_FREQUENCY | Defines the identifier set for calendar event frequency. | enum (int) | Enumerations | Exact adoption | ENUM_CALENDAR_EVENT_FREQUENCY | data |
| ENUM_CALENDAR_EVENT_TYPE | Defines the identifier set for calendar event type. | enum (int) | Enumerations | Exact adoption | ENUM_CALENDAR_EVENT_TYPE | data |
| ENUM_CALENDAR_EVENT_SECTOR | Defines the identifier set for calendar event sector. | enum (int) | Enumerations | Exact adoption | ENUM_CALENDAR_EVENT_SECTOR | data |
| CALENDAR_FREQUENCY_NONE | Selects frequency none in calendar event frequency. | ENUM_CALENDAR_EVENT_FREQUENCY | Enumerations | Exact adoption | CALENDAR_FREQUENCY_NONE | data |
| CALENDAR_FREQUENCY_WEEK | Selects frequency week in calendar event frequency. | ENUM_CALENDAR_EVENT_FREQUENCY | Enumerations | Exact adoption | CALENDAR_FREQUENCY_WEEK | data |
| CALENDAR_FREQUENCY_MONTH | Selects frequency month in calendar event frequency. | ENUM_CALENDAR_EVENT_FREQUENCY | Enumerations | Exact adoption | CALENDAR_FREQUENCY_MONTH | data |
| CALENDAR_FREQUENCY_QUARTER | Selects frequency quarter in calendar event frequency. | ENUM_CALENDAR_EVENT_FREQUENCY | Enumerations | Exact adoption | CALENDAR_FREQUENCY_QUARTER | data |
| CALENDAR_FREQUENCY_YEAR | Selects frequency year in calendar event frequency. | ENUM_CALENDAR_EVENT_FREQUENCY | Enumerations | Exact adoption | CALENDAR_FREQUENCY_YEAR | data |
| CALENDAR_FREQUENCY_DAY | Selects frequency day in calendar event frequency. | ENUM_CALENDAR_EVENT_FREQUENCY | Enumerations | Exact adoption | CALENDAR_FREQUENCY_DAY | data |
| CALENDAR_TYPE_EVENT | Selects type event in calendar event type. | ENUM_CALENDAR_EVENT_TYPE | Enumerations | Exact adoption | CALENDAR_TYPE_EVENT | data |
| CALENDAR_TYPE_INDICATOR | Selects type indicator in calendar event type. | ENUM_CALENDAR_EVENT_TYPE | Enumerations | Exact adoption | CALENDAR_TYPE_INDICATOR | data |
| CALENDAR_TYPE_HOLIDAY | Selects type holiday in calendar event type. | ENUM_CALENDAR_EVENT_TYPE | Enumerations | Exact adoption | CALENDAR_TYPE_HOLIDAY | data |
| CALENDAR_SECTOR_NONE | Selects sector none in calendar event sector. | ENUM_CALENDAR_EVENT_SECTOR | Enumerations | Exact adoption | CALENDAR_SECTOR_NONE | data |
| ENUM_CALENDAR_EVENT_IMPORTANCE | Defines the identifier set for calendar event importance. | enum (int) | Enumerations | Exact adoption | ENUM_CALENDAR_EVENT_IMPORTANCE | data |
| ENUM_CALENDAR_EVENT_UNIT | Defines the identifier set for calendar event unit. | enum (int) | Enumerations | Exact adoption | ENUM_CALENDAR_EVENT_UNIT | data |
| CALENDAR_SECTOR_MARKET | Selects sector market in calendar event sector. | ENUM_CALENDAR_EVENT_SECTOR | Enumerations | Exact adoption | CALENDAR_SECTOR_MARKET | data |
| CALENDAR_SECTOR_GDP | Selects sector GDP in calendar event sector. | ENUM_CALENDAR_EVENT_SECTOR | Enumerations | Exact adoption | CALENDAR_SECTOR_GDP | data |
| CALENDAR_SECTOR_JOBS | Selects sector jobs in calendar event sector. | ENUM_CALENDAR_EVENT_SECTOR | Enumerations | Exact adoption | CALENDAR_SECTOR_JOBS | data |
| CALENDAR_SECTOR_PRICES | Selects sector prices in calendar event sector. | ENUM_CALENDAR_EVENT_SECTOR | Enumerations | Exact adoption | CALENDAR_SECTOR_PRICES | data |
| CALENDAR_SECTOR_MONEY | Selects sector money in calendar event sector. | ENUM_CALENDAR_EVENT_SECTOR | Enumerations | Exact adoption | CALENDAR_SECTOR_MONEY | data |
| CALENDAR_SECTOR_TRADE | Selects sector trade in calendar event sector. | ENUM_CALENDAR_EVENT_SECTOR | Enumerations | Exact adoption | CALENDAR_SECTOR_TRADE | data |
| CALENDAR_SECTOR_GOVERNMENT | Selects sector government in calendar event sector. | ENUM_CALENDAR_EVENT_SECTOR | Enumerations | Exact adoption | CALENDAR_SECTOR_GOVERNMENT | data |
| CALENDAR_SECTOR_BUSINESS | Selects sector business in calendar event sector. | ENUM_CALENDAR_EVENT_SECTOR | Enumerations | Exact adoption | CALENDAR_SECTOR_BUSINESS | data |
| CALENDAR_SECTOR_CONSUMER | Selects sector consumer in calendar event sector. | ENUM_CALENDAR_EVENT_SECTOR | Enumerations | Exact adoption | CALENDAR_SECTOR_CONSUMER | data |
| CALENDAR_SECTOR_HOUSING | Selects sector housing in calendar event sector. | ENUM_CALENDAR_EVENT_SECTOR | Enumerations | Exact adoption | CALENDAR_SECTOR_HOUSING | data |
| CALENDAR_SECTOR_TAXES | Selects sector taxes in calendar event sector. | ENUM_CALENDAR_EVENT_SECTOR | Enumerations | Exact adoption | CALENDAR_SECTOR_TAXES | data |
| CALENDAR_SECTOR_HOLIDAYS | Selects sector holidays in calendar event sector. | ENUM_CALENDAR_EVENT_SECTOR | Enumerations | Exact adoption | CALENDAR_SECTOR_HOLIDAYS | data |
| CALENDAR_IMPORTANCE_NONE | Selects importance none in calendar event importance. | ENUM_CALENDAR_EVENT_IMPORTANCE | Enumerations | Exact adoption | CALENDAR_IMPORTANCE_NONE | data |
| CALENDAR_IMPORTANCE_LOW | Selects importance low in calendar event importance. | ENUM_CALENDAR_EVENT_IMPORTANCE | Enumerations | Exact adoption | CALENDAR_IMPORTANCE_LOW | data |
| CALENDAR_IMPORTANCE_MODERATE | Selects importance moderate in calendar event importance. | ENUM_CALENDAR_EVENT_IMPORTANCE | Enumerations | Exact adoption | CALENDAR_IMPORTANCE_MODERATE | data |
| CALENDAR_IMPORTANCE_HIGH | Selects importance high in calendar event importance. | ENUM_CALENDAR_EVENT_IMPORTANCE | Enumerations | Exact adoption | CALENDAR_IMPORTANCE_HIGH | data |
| CALENDAR_UNIT_NONE | Selects unit none in calendar event unit. | ENUM_CALENDAR_EVENT_UNIT | Enumerations | Exact adoption | CALENDAR_UNIT_NONE | data |
| CALENDAR_UNIT_PERCENT | Selects unit percent in calendar event unit. | ENUM_CALENDAR_EVENT_UNIT | Enumerations | Exact adoption | CALENDAR_UNIT_PERCENT | data |
| CALENDAR_UNIT_CURRENCY | Selects unit currency in calendar event unit. | ENUM_CALENDAR_EVENT_UNIT | Enumerations | Exact adoption | CALENDAR_UNIT_CURRENCY | data |
| CALENDAR_UNIT_HOUR | Selects unit hour in calendar event unit. | ENUM_CALENDAR_EVENT_UNIT | Enumerations | Exact adoption | CALENDAR_UNIT_HOUR | data |
| CALENDAR_UNIT_JOB | Selects unit job in calendar event unit. | ENUM_CALENDAR_EVENT_UNIT | Enumerations | Exact adoption | CALENDAR_UNIT_JOB | data |
| CALENDAR_UNIT_RIG | Selects unit rig in calendar event unit. | ENUM_CALENDAR_EVENT_UNIT | Enumerations | Exact adoption | CALENDAR_UNIT_RIG | data |
| ENUM_CALENDAR_EVENT_MULTIPLIER | Defines the identifier set for calendar event multiplier. | enum (int) | Enumerations | Exact adoption | ENUM_CALENDAR_EVENT_MULTIPLIER | data |
| ENUM_CALENDAR_EVENT_IMPACT | Defines the identifier set for calendar event impact. | enum (int) | Enumerations | Exact adoption | ENUM_CALENDAR_EVENT_IMPACT | data |
| ENUM_CALENDAR_EVENT_TIMEMODE | Defines the identifier set for calendar event timemode. | enum (int) | Enumerations | Exact adoption | ENUM_CALENDAR_EVENT_TIMEMODE | data |
| CALENDAR_UNIT_USD | Selects unit USD in calendar event unit. | ENUM_CALENDAR_EVENT_UNIT | Enumerations | Exact adoption | CALENDAR_UNIT_USD | data |
| CALENDAR_UNIT_PEOPLE | Selects unit people in calendar event unit. | ENUM_CALENDAR_EVENT_UNIT | Enumerations | Exact adoption | CALENDAR_UNIT_PEOPLE | data |
| CALENDAR_UNIT_MORTGAGE | Selects unit mortgage in calendar event unit. | ENUM_CALENDAR_EVENT_UNIT | Enumerations | Exact adoption | CALENDAR_UNIT_MORTGAGE | data |
| CALENDAR_UNIT_VOTE | Selects unit vote in calendar event unit. | ENUM_CALENDAR_EVENT_UNIT | Enumerations | Exact adoption | CALENDAR_UNIT_VOTE | data |
| CALENDAR_UNIT_BARREL | Selects unit barrel in calendar event unit. | ENUM_CALENDAR_EVENT_UNIT | Enumerations | Exact adoption | CALENDAR_UNIT_BARREL | data |
| CALENDAR_UNIT_CUBICFEET | Selects unit cubicfeet in calendar event unit. | ENUM_CALENDAR_EVENT_UNIT | Enumerations | Exact adoption | CALENDAR_UNIT_CUBICFEET | data |
| CALENDAR_UNIT_POSITION | Selects unit position in calendar event unit. | ENUM_CALENDAR_EVENT_UNIT | Enumerations | Exact adoption | CALENDAR_UNIT_POSITION | data |
| CALENDAR_UNIT_BUILDING | Selects unit building in calendar event unit. | ENUM_CALENDAR_EVENT_UNIT | Enumerations | Exact adoption | CALENDAR_UNIT_BUILDING | data |
| CALENDAR_MULTIPLIER_NONE | Selects multiplier none in calendar event multiplier. | ENUM_CALENDAR_EVENT_MULTIPLIER | Enumerations | Exact adoption | CALENDAR_MULTIPLIER_NONE | data |
| CALENDAR_MULTIPLIER_THOUSANDS | Selects multiplier thousands in calendar event multiplier. | ENUM_CALENDAR_EVENT_MULTIPLIER | Enumerations | Exact adoption | CALENDAR_MULTIPLIER_THOUSANDS | data |
| CALENDAR_MULTIPLIER_MILLIONS | Selects multiplier millions in calendar event multiplier. | ENUM_CALENDAR_EVENT_MULTIPLIER | Enumerations | Exact adoption | CALENDAR_MULTIPLIER_MILLIONS | data |
| CALENDAR_MULTIPLIER_BILLIONS | Selects multiplier billions in calendar event multiplier. | ENUM_CALENDAR_EVENT_MULTIPLIER | Enumerations | Exact adoption | CALENDAR_MULTIPLIER_BILLIONS | data |
| CALENDAR_MULTIPLIER_TRILLIONS | Selects multiplier trillions in calendar event multiplier. | ENUM_CALENDAR_EVENT_MULTIPLIER | Enumerations | Exact adoption | CALENDAR_MULTIPLIER_TRILLIONS | data |
| CALENDAR_IMPACT_NA | Selects impact na in calendar event impact. | ENUM_CALENDAR_EVENT_IMPACT | Enumerations | Exact adoption | CALENDAR_IMPACT_NA | data |
| CALENDAR_IMPACT_POSITIVE | Selects impact positive in calendar event impact. | ENUM_CALENDAR_EVENT_IMPACT | Enumerations | Exact adoption | CALENDAR_IMPACT_POSITIVE | data |
| CALENDAR_IMPACT_NEGATIVE | Selects impact negative in calendar event impact. | ENUM_CALENDAR_EVENT_IMPACT | Enumerations | Exact adoption | CALENDAR_IMPACT_NEGATIVE | data |
| CALENDAR_TIMEMODE_DATETIME | Selects timemode datetime in calendar event timemode. | ENUM_CALENDAR_EVENT_TIMEMODE | Enumerations | Exact adoption | CALENDAR_TIMEMODE_DATETIME | data |
| CALENDAR_TIMEMODE_DATE | Selects timemode date in calendar event timemode. | ENUM_CALENDAR_EVENT_TIMEMODE | Enumerations | Exact adoption | CALENDAR_TIMEMODE_DATE | data |
| CALENDAR_TIMEMODE_NOTIME | Selects timemode notime in calendar event timemode. | ENUM_CALENDAR_EVENT_TIMEMODE | Enumerations | Exact adoption | CALENDAR_TIMEMODE_NOTIME | data |
| CALENDAR_TIMEMODE_TENTATIVE | Selects timemode tentative in calendar event timemode. | ENUM_CALENDAR_EVENT_TIMEMODE | Enumerations | Exact adoption | CALENDAR_TIMEMODE_TENTATIVE | data |
| TRADE_RETCODE_REQUOTE | Value: 10004. Reports the requote trade-server outcome. HaruQuantAI adds provider identity, retryability, and audit evidence. | Not specified in reference | Constants | Semantic extension | TRADE_RETCODE_REQUOTE | broker |
| TRADE_RETCODE_REJECT | Value: 10006. Reports the reject trade-server outcome. HaruQuantAI adds provider identity, retryability, and audit evidence. | Not specified in reference | Constants | Semantic extension | TRADE_RETCODE_REJECT | broker |
| TRADE_RETCODE_CANCEL | Value: 10007. Reports the cancel trade-server outcome. HaruQuantAI adds provider identity, retryability, and audit evidence. | Not specified in reference | Constants | Semantic extension | TRADE_RETCODE_CANCEL | broker |
| TRADE_RETCODE_PLACED | Value: 10008. Reports the placed trade-server outcome. HaruQuantAI adds provider identity, retryability, and audit evidence. | Not specified in reference | Constants | Semantic extension | TRADE_RETCODE_PLACED | broker |
| TRADE_RETCODE_DONE | Value: 10009. Reports the done trade-server outcome. HaruQuantAI adds provider identity, retryability, and audit evidence. | Not specified in reference | Constants | Semantic extension | TRADE_RETCODE_DONE | broker |
| TRADE_RETCODE_DONE_PARTIAL | Value: 10010. Reports the done partial trade-server outcome. HaruQuantAI adds provider identity, retryability, and audit evidence. | Not specified in reference | Constants | Semantic extension | TRADE_RETCODE_DONE_PARTIAL | broker |
| TRADE_RETCODE_ERROR | Value: 10011. Reports the error trade-server outcome. HaruQuantAI adds provider identity, retryability, and audit evidence. | Not specified in reference | Constants | Semantic extension | TRADE_RETCODE_ERROR | broker |
| TRADE_RETCODE_TIMEOUT | Value: 10012. Reports the timeout trade-server outcome. HaruQuantAI adds provider identity, retryability, and audit evidence. | Not specified in reference | Constants | Semantic extension | TRADE_RETCODE_TIMEOUT | broker |
| TRADE_RETCODE_INVALID | Value: 10013. Reports the invalid trade-server outcome. HaruQuantAI adds provider identity, retryability, and audit evidence. | Not specified in reference | Constants | Semantic extension | TRADE_RETCODE_INVALID | broker |
| TRADE_RETCODE_INVALID_VOLUME | Value: 10014. Reports the invalid volume trade-server outcome. HaruQuantAI adds provider identity, retryability, and audit evidence. | Not specified in reference | Constants | Semantic extension | TRADE_RETCODE_INVALID_VOLUME | broker |
| TRADE_RETCODE_INVALID_PRICE | Value: 10015. Reports the invalid price trade-server outcome. HaruQuantAI adds provider identity, retryability, and audit evidence. | Not specified in reference | Constants | Semantic extension | TRADE_RETCODE_INVALID_PRICE | broker |
| TRADE_RETCODE_INVALID_STOPS | Value: 10016. Reports the invalid stops trade-server outcome. HaruQuantAI adds provider identity, retryability, and audit evidence. | Not specified in reference | Constants | Semantic extension | TRADE_RETCODE_INVALID_STOPS | broker |
| TRADE_RETCODE_TRADE_DISABLED | Value: 10017. Reports the trade disabled trade-server outcome. HaruQuantAI adds provider identity, retryability, and audit evidence. | Not specified in reference | Constants | Semantic extension | TRADE_RETCODE_TRADE_DISABLED | broker |
| TRADE_RETCODE_MARKET_CLOSED | Value: 10018. Reports the market closed trade-server outcome. HaruQuantAI adds provider identity, retryability, and audit evidence. | Not specified in reference | Constants | Semantic extension | TRADE_RETCODE_MARKET_CLOSED | broker |
| TRADE_RETCODE_NO_MONEY | Value: 10019. Reports the no money trade-server outcome. HaruQuantAI adds provider identity, retryability, and audit evidence. | Not specified in reference | Constants | Semantic extension | TRADE_RETCODE_NO_MONEY | broker |
| TRADE_RETCODE_PRICE_CHANGED | Value: 10020. Reports the price changed trade-server outcome. HaruQuantAI adds provider identity, retryability, and audit evidence. | Not specified in reference | Constants | Semantic extension | TRADE_RETCODE_PRICE_CHANGED | broker |
| TRADE_RETCODE_PRICE_OFF | Value: 10021. Reports the price off trade-server outcome. HaruQuantAI adds provider identity, retryability, and audit evidence. | Not specified in reference | Constants | Semantic extension | TRADE_RETCODE_PRICE_OFF | broker |
| TRADE_RETCODE_INVALID_EXPIRATION | Value: 10022. Reports the invalid expiration trade-server outcome. HaruQuantAI adds provider identity, retryability, and audit evidence. | Not specified in reference | Constants | Semantic extension | TRADE_RETCODE_INVALID_EXPIRATION | broker |
| TRADE_RETCODE_ORDER_CHANGED | Value: 10023. Reports the order changed trade-server outcome. HaruQuantAI adds provider identity, retryability, and audit evidence. | Not specified in reference | Constants | Semantic extension | TRADE_RETCODE_ORDER_CHANGED | broker |
| TRADE_RETCODE_TOO_MANY_REQUESTS | Value: 10024. Reports the too many requests trade-server outcome. HaruQuantAI adds provider identity, retryability, and audit evidence. | Not specified in reference | Constants | Semantic extension | TRADE_RETCODE_TOO_MANY_REQUESTS | broker |
| TRADE_RETCODE_NO_CHANGES | Value: 10025. Reports the no changes trade-server outcome. HaruQuantAI adds provider identity, retryability, and audit evidence. | Not specified in reference | Constants | Semantic extension | TRADE_RETCODE_NO_CHANGES | broker |
| TRADE_RETCODE_SERVER_DISABLES_AT | Value: 10026. Reports the server disables at trade-server outcome. HaruQuantAI adds provider identity, retryability, and audit evidence. | Not specified in reference | Constants | Semantic extension | TRADE_RETCODE_SERVER_DISABLES_AT | broker |
| TRADE_RETCODE_CLIENT_DISABLES_AT | Value: 10027. Reports the client disables at trade-server outcome. HaruQuantAI adds provider identity, retryability, and audit evidence. | Not specified in reference | Constants | Semantic extension | TRADE_RETCODE_CLIENT_DISABLES_AT | broker |
| TRADE_RETCODE_LOCKED | Value: 10028. Reports the locked trade-server outcome. HaruQuantAI adds provider identity, retryability, and audit evidence. | Not specified in reference | Constants | Semantic extension | TRADE_RETCODE_LOCKED | broker |
| TRADE_RETCODE_FROZEN | Value: 10029. Reports the frozen trade-server outcome. HaruQuantAI adds provider identity, retryability, and audit evidence. | Not specified in reference | Constants | Semantic extension | TRADE_RETCODE_FROZEN | broker |
| TRADE_RETCODE_INVALID_FILL | Value: 10030. Reports the invalid fill trade-server outcome. HaruQuantAI adds provider identity, retryability, and audit evidence. | Not specified in reference | Constants | Semantic extension | TRADE_RETCODE_INVALID_FILL | broker |
| TRADE_RETCODE_CONNECTION | Value: 10031. Reports the connection trade-server outcome. HaruQuantAI adds provider identity, retryability, and audit evidence. | Not specified in reference | Constants | Semantic extension | TRADE_RETCODE_CONNECTION | broker |
| TRADE_RETCODE_ONLY_REAL | Value: 10032. Reports the only real trade-server outcome. HaruQuantAI adds provider identity, retryability, and audit evidence. | Not specified in reference | Constants | Semantic extension | TRADE_RETCODE_ONLY_REAL | broker |
| TRADE_RETCODE_LIMIT_ORDERS | Value: 10033. Reports the limit orders trade-server outcome. HaruQuantAI adds provider identity, retryability, and audit evidence. | Not specified in reference | Constants | Semantic extension | TRADE_RETCODE_LIMIT_ORDERS | broker |
| TRADE_RETCODE_LIMIT_VOLUME | Value: 10034. Reports the limit volume trade-server outcome. HaruQuantAI adds provider identity, retryability, and audit evidence. | Not specified in reference | Constants | Semantic extension | TRADE_RETCODE_LIMIT_VOLUME | broker |
| TRADE_RETCODE_INVALID_ORDER | Value: 10035. Reports the invalid order trade-server outcome. HaruQuantAI adds provider identity, retryability, and audit evidence. | Not specified in reference | Constants | Semantic extension | TRADE_RETCODE_INVALID_ORDER | broker |
| TRADE_RETCODE_POSITION_CLOSED | Value: 10036. Reports the position closed trade-server outcome. HaruQuantAI adds provider identity, retryability, and audit evidence. | Not specified in reference | Constants | Semantic extension | TRADE_RETCODE_POSITION_CLOSED | broker |
| TRADE_RETCODE_INVALID_CLOSE_VOLUME | Value: 10038. Reports the invalid close volume trade-server outcome. HaruQuantAI adds provider identity, retryability, and audit evidence. | Not specified in reference | Constants | Semantic extension | TRADE_RETCODE_INVALID_CLOSE_VOLUME | broker |
| TRADE_RETCODE_CLOSE_ORDER_EXIST | Value: 10039. Reports the close order exist trade-server outcome. HaruQuantAI adds provider identity, retryability, and audit evidence. | Not specified in reference | Constants | Semantic extension | TRADE_RETCODE_CLOSE_ORDER_EXIST | broker |
| TRADE_RETCODE_LIMIT_POSITIONS | Value: 10040. Reports the limit positions trade-server outcome. HaruQuantAI adds provider identity, retryability, and audit evidence. | Not specified in reference | Constants | Semantic extension | TRADE_RETCODE_LIMIT_POSITIONS | broker |
| TRADE_RETCODE_REJECT_CANCEL | Value: 10041. Reports the reject cancel trade-server outcome. HaruQuantAI adds provider identity, retryability, and audit evidence. | Not specified in reference | Constants | Semantic extension | TRADE_RETCODE_REJECT_CANCEL | broker |
| TRADE_RETCODE_LONG_ONLY | Value: 10042. Reports the long only trade-server outcome. HaruQuantAI adds provider identity, retryability, and audit evidence. | Not specified in reference | Constants | Semantic extension | TRADE_RETCODE_LONG_ONLY | broker |
| TRADE_RETCODE_SHORT_ONLY | Value: 10043. Reports the short only trade-server outcome. HaruQuantAI adds provider identity, retryability, and audit evidence. | Not specified in reference | Constants | Semantic extension | TRADE_RETCODE_SHORT_ONLY | broker |
| TRADE_RETCODE_CLOSE_ONLY | Value: 10044. Reports the close only trade-server outcome. HaruQuantAI adds provider identity, retryability, and audit evidence. | Not specified in reference | Constants | Semantic extension | TRADE_RETCODE_CLOSE_ONLY | broker |
| TRADE_RETCODE_FIFO_CLOSE | Value: 10045. Reports the FIFO close trade-server outcome. HaruQuantAI adds provider identity, retryability, and audit evidence. | Not specified in reference | Constants | Semantic extension | TRADE_RETCODE_FIFO_CLOSE | broker |
| TRADE_RETCODE_HEDGE_PROHIBITED | Value: 10046. Reports the hedge prohibited trade-server outcome. HaruQuantAI adds provider identity, retryability, and audit evidence. | Not specified in reference | Constants | Semantic extension | TRADE_RETCODE_HEDGE_PROHIBITED | broker |
| 21 | Value: 21. MQL5 compiler diagnostic for incomplete record of a date in the datetime string. Rejected because numeric compiler diagnostics are not stable application contracts. | Not specified in reference | Constants | Rejected adoption | — | — |
| 22 | Value: 22. MQL5 compiler diagnostic for invalid number in the datetime string for the date. Requirements: Year 1970 <= X <= 3000 Month 0 <X <= 12 Day 0 <X…. Rejected because numeric compiler diagnostics are not stable application contracts. | Not specified in reference | Constants | Rejected adoption | — | — |
| 23 | Value: 23. MQL5 compiler diagnostic for invalid number of datetime string for time. Requirements: Hour 0 <= X <24 Minute 0 <= X <60. Rejected because numeric compiler diagnostics are not stable application contracts. | Not specified in reference | Constants | Rejected adoption | — | — |
| 24 | Value: 24. MQL5 compiler diagnostic for invalid color in RGB format: one of RGB components is less than 0 or greater than 255. Rejected because numeric compiler diagnostics are not stable application contracts. | Not specified in reference | Constants | Rejected adoption | — | — |
| 25 | Value: 25. MQL5 compiler diagnostic for unknown character of the escape sequences. Known: \n \r \t \\ \" \' \X \x. Rejected because numeric compiler diagnostics are not stable application contracts. | Not specified in reference | Constants | Rejected adoption | — | — |
| 26 | Value: 26. MQL5 compiler diagnostic for exceeds the supported size volume of local variables (> 512Kb) of the function, reduce the number. Rejected because numeric compiler diagnostics are not stable application contracts. | Not specified in reference | Constants | Rejected adoption | — | — |
| 29 | Value: 29. MQL5 compiler diagnostic for enumeration has a duplicate definition (duplication) - members will be added to the first definition. Rejected because numeric compiler diagnostics are not stable application contracts. | Not specified in reference | Constants | Rejected adoption | — | — |
| 30 | Value: 30. MQL5 compiler diagnostic for overriding macro. Rejected because numeric compiler diagnostics are not stable application contracts. | Not specified in reference | Constants | Rejected adoption | — | — |
| 31 | Value: 31. MQL5 compiler diagnostic for the variable is declared but is unused. Rejected because numeric compiler diagnostics are not stable application contracts. | Not specified in reference | Constants | Rejected adoption | — | — |
| 32 | Value: 32. MQL5 compiler diagnostic for constructor must be of void type. Rejected because numeric compiler diagnostics are not stable application contracts. | Not specified in reference | Constants | Rejected adoption | — | — |
| 33 | Value: 33. MQL5 compiler diagnostic for destructor must be of void type. Rejected because numeric compiler diagnostics are not stable application contracts. | Not specified in reference | Constants | Rejected adoption | — | — |
| 34 | Value: 34. MQL5 compiler diagnostic for constant does not fit in the range of integers (X> _UI64_MAX / / X <_I64_MIN) and will be converted to the double type. Rejected because numeric compiler diagnostics are not stable application contracts. | Not specified in reference | Constants | Rejected adoption | — | — |
| 35 | Value: 35. MQL5 compiler diagnostic for exceeds the supported length HEX - more than 16 significant characters (senior nibbles are cut). Rejected because numeric compiler diagnostics are not stable application contracts. | Not specified in reference | Constants | Rejected adoption | — | — |
| 36 | Value: 36. MQL5 compiler diagnostic for no nibbles in HEX string "0x". Rejected because numeric compiler diagnostics are not stable application contracts. | Not specified in reference | Constants | Rejected adoption | — | — |
| 37 | Value: 37. MQL5 compiler diagnostic for no function - nothing to be performed. Rejected because numeric compiler diagnostics are not stable application contracts. | Not specified in reference | Constants | Rejected adoption | — | — |
| 38 | Value: 38. MQL5 compiler diagnostic for a non-initialized variable is used. Rejected because numeric compiler diagnostics are not stable application contracts. | Not specified in reference | Constants | Rejected adoption | — | — |
| 41 | Value: 41. MQL5 compiler diagnostic for function has no body, and is not called. Rejected because numeric compiler diagnostics are not stable application contracts. | Not specified in reference | Constants | Rejected adoption | — | — |
| 43 | Value: 43. MQL5 compiler diagnostic for possible loss of data at typecasting. Rejected because numeric compiler diagnostics are not stable application contracts. | Not specified in reference | Constants | Rejected adoption | — | — |
| 44 | Value: 44. MQL5 compiler diagnostic for loss of accuracy (of data) when converting a constant. Rejected because numeric compiler diagnostics are not stable application contracts. | Not specified in reference | Constants | Rejected adoption | — | — |
| 45 | Value: 45. MQL5 compiler diagnostic for difference between the signs of operands in the operations of comparison. Rejected because numeric compiler diagnostics are not stable application contracts. | Not specified in reference | Constants | Rejected adoption | — | — |
| 46 | Value: 46. MQL5 compiler diagnostic for problems with function importing - declaration of #import is required or import of functions is closed. Rejected because numeric compiler diagnostics are not stable application contracts. | Not specified in reference | Constants | Rejected adoption | — | — |
| 47 | Value: 47. MQL5 compiler diagnostic for exceeds the supported size description - extra characters will not be included in the executable file. Rejected because numeric compiler diagnostics are not stable application contracts. | Not specified in reference | Constants | Rejected adoption | — | — |
| 48 | Value: 48. MQL5 compiler diagnostic for the number of indicator buffers declared is less than required. Rejected because numeric compiler diagnostics are not stable application contracts. | Not specified in reference | Constants | Rejected adoption | — | — |
| 49 | Value: 49. MQL5 compiler diagnostic for no color to plot a graphical series in the indicator. Rejected because numeric compiler diagnostics are not stable application contracts. | Not specified in reference | Constants | Rejected adoption | — | — |
| 50 | Value: 50. MQL5 compiler diagnostic for no graphical series to draw the indicator. Rejected because numeric compiler diagnostics are not stable application contracts. | Not specified in reference | Constants | Rejected adoption | — | — |
| 51 | Value: 51. MQL5 compiler diagnostic for 'OnStart' handler function missing in the script. Rejected because numeric compiler diagnostics are not stable application contracts. | Not specified in reference | Constants | Rejected adoption | — | — |
| 52 | Value: 52. MQL5 compiler diagnostic for 'OnStart' handler function is defined with invalid parameters. Rejected because numeric compiler diagnostics are not stable application contracts. | Not specified in reference | Constants | Rejected adoption | — | — |
| 53 | Value: 53. MQL5 compiler diagnostic for 'OnStart' function can be defined only in a script. Rejected because numeric compiler diagnostics are not stable application contracts. | Not specified in reference | Constants | Rejected adoption | — | — |
| 54 | Value: 54. MQL5 compiler diagnostic for 'OnInit' function is defined with invalid parameters. Rejected because numeric compiler diagnostics are not stable application contracts. | Not specified in reference | Constants | Rejected adoption | — | — |
| 55 | Value: 55. MQL5 compiler diagnostic for 'OnInit' function is not used in scripts. Rejected because numeric compiler diagnostics are not stable application contracts. | Not specified in reference | Constants | Rejected adoption | — | — |
| 56 | Value: 56. MQL5 compiler diagnostic for 'OnDeinit' function is defined with invalid parameters. Rejected because numeric compiler diagnostics are not stable application contracts. | Not specified in reference | Constants | Rejected adoption | — | — |
| 57 | Value: 57. MQL5 compiler diagnostic for 'OnDeinit' function is not used in scripts. Rejected because numeric compiler diagnostics are not stable application contracts. | Not specified in reference | Constants | Rejected adoption | — | — |
| 58 | Value: 58. MQL5 compiler diagnostic for two 'OnCalculate' functions are defined. OnCalculate () at one price array will be used. Rejected because numeric compiler diagnostics are not stable application contracts. | Not specified in reference | Constants | Rejected adoption | — | — |
| 59 | Value: 59. MQL5 compiler diagnostic for overfilling detected when calculating a complex integer constant. Rejected because numeric compiler diagnostics are not stable application contracts. | Not specified in reference | Constants | Rejected adoption | — | — |
| 60 | Value: 60. MQL5 compiler diagnostic for probably, the variable is not initialized. Rejected because numeric compiler diagnostics are not stable application contracts. | Not specified in reference | Constants | Rejected adoption | — | — |
| 61 | Value: 61. MQL5 compiler diagnostic for this declaration makes it impossible to refer to the local variable declared on the specified line. Rejected because numeric compiler diagnostics are not stable application contracts. | Not specified in reference | Constants | Rejected adoption | — | — |
| 62 | Value: 62. MQL5 compiler diagnostic for this declaration makes it impossible to refer to the global variable declared on the specified line. Rejected because numeric compiler diagnostics are not stable application contracts. | Not specified in reference | Constants | Rejected adoption | — | — |
| 63 | Value: 63. MQL5 compiler diagnostic for unable to be used for static allocated array. Rejected because numeric compiler diagnostics are not stable application contracts. | Not specified in reference | Constants | Rejected adoption | — | — |
| 64 | Value: 64. MQL5 compiler diagnostic for this variable declaration hides predefined variable. Rejected because numeric compiler diagnostics are not stable application contracts. | Not specified in reference | Constants | Rejected adoption | — | — |
| 65 | Value: 65. MQL5 compiler diagnostic for the value of the expression is always true/false. Rejected because numeric compiler diagnostics are not stable application contracts. | Not specified in reference | Constants | Rejected adoption | — | — |
| 66 | Value: 66. MQL5 compiler diagnostic for using a variable or bool type expression in mathematical operations is unsafe. Rejected because numeric compiler diagnostics are not stable application contracts. | Not specified in reference | Constants | Rejected adoption | — | — |
| 67 | Value: 67. MQL5 compiler diagnostic for the result of applying the unary minus operator to an unsigned ulong type is undefined. Rejected because numeric compiler diagnostics are not stable application contracts. | Not specified in reference | Constants | Rejected adoption | — | — |
| 68 | Value: 68. MQL5 compiler diagnostic for the version specified in the #property version property is unacceptable for the Market section; the correct format…. Rejected because numeric compiler diagnostics are not stable application contracts. | Not specified in reference | Constants | Rejected adoption | — | — |
| 69 | Value: 69. MQL5 compiler diagnostic for empty controlled statement found. Rejected because numeric compiler diagnostics are not stable application contracts. | Not specified in reference | Constants | Rejected adoption | — | — |
| 70 | Value: 70. MQL5 compiler diagnostic for invalid function return type or incorrect parameters during declaration of the event handler function. Rejected because numeric compiler diagnostics are not stable application contracts. | Not specified in reference | Constants | Rejected adoption | — | — |
| 71 | Value: 71. MQL5 compiler diagnostic for an implicit cast of structures to one type is required. Rejected because numeric compiler diagnostics are not stable application contracts. | Not specified in reference | Constants | Rejected adoption | — | — |
| 72 | Value: 72. MQL5 compiler diagnostic for this declaration makes direct access to the member of a class declared in the specified string impossible. Access…. Rejected because numeric compiler diagnostics are not stable application contracts. | Not specified in reference | Constants | Rejected adoption | — | — |
| 73 | Value: 73. MQL5 compiler diagnostic for binary constant is too big, high-order digits will be truncated. Rejected because numeric compiler diagnostics are not stable application contracts. | Not specified in reference | Constants | Rejected adoption | — | — |
| 74 | Value: 74. MQL5 compiler diagnostic for parameter in the method of the inherited class has a different const modifier, the derived function has overloaded…. Rejected because numeric compiler diagnostics are not stable application contracts. | Not specified in reference | Constants | Rejected adoption | — | — |
| 75 | Value: 75. MQL5 compiler diagnostic for negative or exceeds the supported size shift value in shift bitwise operation, execution result is undefined. Rejected because numeric compiler diagnostics are not stable application contracts. | Not specified in reference | Constants | Rejected adoption | — | — |
| 76 | Value: 76. MQL5 compiler diagnostic for function must return a value. Rejected because numeric compiler diagnostics are not stable application contracts. | Not specified in reference | Constants | Rejected adoption | — | — |
| 77 | Value: 77. MQL5 compiler diagnostic for void function returns a value. Rejected because numeric compiler diagnostics are not stable application contracts. | Not specified in reference | Constants | Rejected adoption | — | — |
| 78 | Value: 78. MQL5 compiler diagnostic for not all control paths return a value. Rejected because numeric compiler diagnostics are not stable application contracts. | Not specified in reference | Constants | Rejected adoption | — | — |
| 79 | Value: 79. MQL5 compiler diagnostic for expressions are not allowed on a global scope. Rejected because numeric compiler diagnostics are not stable application contracts. | Not specified in reference | Constants | Rejected adoption | — | — |
| 80 | Value: 80. MQL5 compiler diagnostic for check operator precedence for possible error; use parentheses to clarify precedence. Rejected because numeric compiler diagnostics are not stable application contracts. | Not specified in reference | Constants | Rejected adoption | — | — |
| 81 | Value: 81. MQL5 compiler diagnostic for two OnCalCulate() are defined. OHLC version will be used. Rejected because numeric compiler diagnostics are not stable application contracts. | Not specified in reference | Constants | Rejected adoption | — | — |
| 82 | Value: 82. MQL5 compiler diagnostic for struct has no members, size assigned to 1 byte. Rejected because numeric compiler diagnostics are not stable application contracts. | Not specified in reference | Constants | Rejected adoption | — | — |
| 83 | Value: 83. MQL5 compiler diagnostic for return value of the function should be checked. Rejected because numeric compiler diagnostics are not stable application contracts. | Not specified in reference | Constants | Rejected adoption | — | — |
| 84 | Value: 84. MQL5 compiler diagnostic for resource indicator is compiled for debugging. That slows down the performance. Please recompile the indicator to…. Rejected because numeric compiler diagnostics are not stable application contracts. | Not specified in reference | Constants | Rejected adoption | — | — |
| 85 | Value: 85. MQL5 compiler diagnostic for too great character code in the string, must be in the range 0 to 65535. Rejected because numeric compiler diagnostics are not stable application contracts. | Not specified in reference | Constants | Rejected adoption | — | — |
| 86 | Value: 86. MQL5 compiler diagnostic for unrecognized character in the string. Rejected because numeric compiler diagnostics are not stable application contracts. | Not specified in reference | Constants | Rejected adoption | — | — |
| 87 | Value: 87. MQL5 compiler diagnostic for no indicator window property (setting the display in the main window or a subwindow) is defined. Property…. Rejected because numeric compiler diagnostics are not stable application contracts. | Not specified in reference | Constants | Rejected adoption | — | — |
| 100 | Value: 100. MQL5 compiler diagnostic for file reading error. Rejected because numeric compiler diagnostics are not stable application contracts. | Not specified in reference | Constants | Rejected adoption | — | — |
| 101 | Value: 101. MQL5 compiler diagnostic for error of opening an *. EX5 for writing. Rejected because numeric compiler diagnostics are not stable application contracts. | Not specified in reference | Constants | Rejected adoption | — | — |
| 103 | Value: 103. MQL5 compiler diagnostic for not enough free memory to complete compilation. Rejected because numeric compiler diagnostics are not stable application contracts. | Not specified in reference | Constants | Rejected adoption | — | — |
| 104 | Value: 104. MQL5 compiler diagnostic for empty syntactic unit unrecognized by compiler. Rejected because numeric compiler diagnostics are not stable application contracts. | Not specified in reference | Constants | Rejected adoption | — | — |
| 105 | Value: 105. MQL5 compiler diagnostic for incorrect file name in #include. Rejected because numeric compiler diagnostics are not stable application contracts. | Not specified in reference | Constants | Rejected adoption | — | — |
| 106 | Value: 106. MQL5 compiler diagnostic for error accessing a file in #include (probably the file is missing). Rejected because numeric compiler diagnostics are not stable application contracts. | Not specified in reference | Constants | Rejected adoption | — | — |
| 108 | Value: 108. MQL5 compiler diagnostic for inappropriate name for #define. Rejected because numeric compiler diagnostics are not stable application contracts. | Not specified in reference | Constants | Rejected adoption | — | — |
| 109 | Value: 109. MQL5 compiler diagnostic for unknown command of preprocessor (valid #include, #define, #property, #import). Rejected because numeric compiler diagnostics are not stable application contracts. | Not specified in reference | Constants | Rejected adoption | — | — |
| 110 | Value: 110. MQL5 compiler diagnostic for symbol unknown to compiler. Rejected because numeric compiler diagnostics are not stable application contracts. | Not specified in reference | Constants | Rejected adoption | — | — |
| 111 | Value: 111. MQL5 compiler diagnostic for function not implemented (description is present, but no body). Rejected because numeric compiler diagnostics are not stable application contracts. | Not specified in reference | Constants | Rejected adoption | — | — |
| 112 | Value: 112. MQL5 compiler diagnostic for double quote (") omitted. Rejected because numeric compiler diagnostics are not stable application contracts. | Not specified in reference | Constants | Rejected adoption | — | — |
| 113 | Value: 113. MQL5 compiler diagnostic for opening angle bracket (<) or double quote (") omitted. Rejected because numeric compiler diagnostics are not stable application contracts. | Not specified in reference | Constants | Rejected adoption | — | — |
| 114 | Value: 114. MQL5 compiler diagnostic for single quote (') omitted. Rejected because numeric compiler diagnostics are not stable application contracts. | Not specified in reference | Constants | Rejected adoption | — | — |
| 115 | Value: 115. MQL5 compiler diagnostic for closing angle bracket ">" omitted. Rejected because numeric compiler diagnostics are not stable application contracts. | Not specified in reference | Constants | Rejected adoption | — | — |
| 116 | Value: 116. MQL5 compiler diagnostic for type not specified in declaration. Rejected because numeric compiler diagnostics are not stable application contracts. | Not specified in reference | Constants | Rejected adoption | — | — |
| 117 | Value: 117. MQL5 compiler diagnostic for no return operator or return is found not in all branches of the implementation. Rejected because numeric compiler diagnostics are not stable application contracts. | Not specified in reference | Constants | Rejected adoption | — | — |
| 118 | Value: 118. MQL5 compiler diagnostic for opening bracket of call parameters was expected. Rejected because numeric compiler diagnostics are not stable application contracts. | Not specified in reference | Constants | Rejected adoption | — | — |
| 119 | Value: 119. MQL5 compiler diagnostic for error writing EX5. Rejected because numeric compiler diagnostics are not stable application contracts. | Not specified in reference | Constants | Rejected adoption | — | — |
| 120 | Value: 120. MQL5 compiler diagnostic for invalid access to an array. Rejected because numeric compiler diagnostics are not stable application contracts. | Not specified in reference | Constants | Rejected adoption | — | — |
| 121 | Value: 121. MQL5 compiler diagnostic for the function is not of void type and the return operator must return a value. Rejected because numeric compiler diagnostics are not stable application contracts. | Not specified in reference | Constants | Rejected adoption | — | — |
| 122 | Value: 122. MQL5 compiler diagnostic for incorrect declaration of the destructor. Rejected because numeric compiler diagnostics are not stable application contracts. | Not specified in reference | Constants | Rejected adoption | — | — |
| 123 | Value: 123. MQL5 compiler diagnostic for colon ":" is missing. Rejected because numeric compiler diagnostics are not stable application contracts. | Not specified in reference | Constants | Rejected adoption | — | — |
| 124 | Value: 124. MQL5 compiler diagnostic for variable is already declared. Rejected because numeric compiler diagnostics are not stable application contracts. | Not specified in reference | Constants | Rejected adoption | — | — |
| 125 | Value: 125. MQL5 compiler diagnostic for variable with such identifier already declared. Rejected because numeric compiler diagnostics are not stable application contracts. | Not specified in reference | Constants | Rejected adoption | — | — |
| 126 | Value: 126. MQL5 compiler diagnostic for variable name exceeds the supported length (> 250 characters). Rejected because numeric compiler diagnostics are not stable application contracts. | Not specified in reference | Constants | Rejected adoption | — | — |
| 127 | Value: 127. MQL5 compiler diagnostic for structure with such identifier has a duplicate definition. Rejected because numeric compiler diagnostics are not stable application contracts. | Not specified in reference | Constants | Rejected adoption | — | — |
| 128 | Value: 128. MQL5 compiler diagnostic for structure is not defined. Rejected because numeric compiler diagnostics are not stable application contracts. | Not specified in reference | Constants | Rejected adoption | — | — |
| 129 | Value: 129. MQL5 compiler diagnostic for structure member with the same name has a duplicate definition. Rejected because numeric compiler diagnostics are not stable application contracts. | Not specified in reference | Constants | Rejected adoption | — | — |
| 130 | Value: 130. MQL5 compiler diagnostic for no such structure member. Rejected because numeric compiler diagnostics are not stable application contracts. | Not specified in reference | Constants | Rejected adoption | — | — |
| 131 | Value: 131. MQL5 compiler diagnostic for breached pairing of brackets. Rejected because numeric compiler diagnostics are not stable application contracts. | Not specified in reference | Constants | Rejected adoption | — | — |
| 132 | Value: 132. MQL5 compiler diagnostic for opening parenthesis "(" expected. Rejected because numeric compiler diagnostics are not stable application contracts. | Not specified in reference | Constants | Rejected adoption | — | — |
| 133 | Value: 133. MQL5 compiler diagnostic for unbalanced braces (no "}"). Rejected because numeric compiler diagnostics are not stable application contracts. | Not specified in reference | Constants | Rejected adoption | — | — |
| 134 | Value: 134. MQL5 compiler diagnostic for difficult to compile (too much branching, internal stack levels are overfilled). Rejected because numeric compiler diagnostics are not stable application contracts. | Not specified in reference | Constants | Rejected adoption | — | — |
| 135 | Value: 135. MQL5 compiler diagnostic for error of file opening for reading. Rejected because numeric compiler diagnostics are not stable application contracts. | Not specified in reference | Constants | Rejected adoption | — | — |
| 136 | Value: 136. MQL5 compiler diagnostic for not enough memory to download the source file into memory. Rejected because numeric compiler diagnostics are not stable application contracts. | Not specified in reference | Constants | Rejected adoption | — | — |
| 137 | Value: 137. MQL5 compiler diagnostic for variable is expected. Rejected because numeric compiler diagnostics are not stable application contracts. | Not specified in reference | Constants | Rejected adoption | — | — |
| 138 | Value: 138. MQL5 compiler diagnostic for reference unable to be initialized. Rejected because numeric compiler diagnostics are not stable application contracts. | Not specified in reference | Constants | Rejected adoption | — | — |
| 140 | Value: 140. MQL5 compiler diagnostic for assignment expected (appears at declaration). Rejected because numeric compiler diagnostics are not stable application contracts. | Not specified in reference | Constants | Rejected adoption | — | — |
| 141 | Value: 141. MQL5 compiler diagnostic for opening brace "{" expected. Rejected because numeric compiler diagnostics are not stable application contracts. | Not specified in reference | Constants | Rejected adoption | — | — |
| 142 | Value: 142. MQL5 compiler diagnostic for parameter can be a dynamic array only. Rejected because numeric compiler diagnostics are not stable application contracts. | Not specified in reference | Constants | Rejected adoption | — | — |
| 143 | Value: 143. MQL5 compiler diagnostic for use of "void" type is unacceptable. Rejected because numeric compiler diagnostics are not stable application contracts. | Not specified in reference | Constants | Rejected adoption | — | — |
| 144 | Value: 144. MQL5 compiler diagnostic for no pair for ")" or "]", i.e. "(or" [ " is absent. Rejected because numeric compiler diagnostics are not stable application contracts. | Not specified in reference | Constants | Rejected adoption | — | — |
| 145 | Value: 145. MQL5 compiler diagnostic for no pair for "(or" [ ", i.e. ") "or"] " is absent. Rejected because numeric compiler diagnostics are not stable application contracts. | Not specified in reference | Constants | Rejected adoption | — | — |
| 146 | Value: 146. MQL5 compiler diagnostic for incorrect array size. Rejected because numeric compiler diagnostics are not stable application contracts. | Not specified in reference | Constants | Rejected adoption | — | — |
| 147 | Value: 147. MQL5 compiler diagnostic for too many parameters (> 64). Rejected because numeric compiler diagnostics are not stable application contracts. | Not specified in reference | Constants | Rejected adoption | — | — |
| 149 | Value: 149. MQL5 compiler diagnostic for this token is not expected here. Rejected because numeric compiler diagnostics are not stable application contracts. | Not specified in reference | Constants | Rejected adoption | — | — |
| 150 | Value: 150. MQL5 compiler diagnostic for invalid use of operation (invalid operands). Rejected because numeric compiler diagnostics are not stable application contracts. | Not specified in reference | Constants | Rejected adoption | — | — |
| 151 | Value: 151. MQL5 compiler diagnostic for expression of void type not allowed. Rejected because numeric compiler diagnostics are not stable application contracts. | Not specified in reference | Constants | Rejected adoption | — | — |
| 152 | Value: 152. MQL5 compiler diagnostic for operator is expected. Rejected because numeric compiler diagnostics are not stable application contracts. | Not specified in reference | Constants | Rejected adoption | — | — |
| 153 | Value: 153. MQL5 compiler diagnostic for misuse of break. Rejected because numeric compiler diagnostics are not stable application contracts. | Not specified in reference | Constants | Rejected adoption | — | — |
| 154 | Value: 154. MQL5 compiler diagnostic for semicolon ";" expected. Rejected because numeric compiler diagnostics are not stable application contracts. | Not specified in reference | Constants | Rejected adoption | — | — |
| 155 | Value: 155. MQL5 compiler diagnostic for comma "," expected. Rejected because numeric compiler diagnostics are not stable application contracts. | Not specified in reference | Constants | Rejected adoption | — | — |
| 156 | Value: 156. MQL5 compiler diagnostic for must be a class type, not struct. Rejected because numeric compiler diagnostics are not stable application contracts. | Not specified in reference | Constants | Rejected adoption | — | — |
| 157 | Value: 157. MQL5 compiler diagnostic for expression is expected. Rejected because numeric compiler diagnostics are not stable application contracts. | Not specified in reference | Constants | Rejected adoption | — | — |
| 158 | Value: 158. MQL5 compiler diagnostic for "non HEX character" found in HEX or exceeds the supported length number (number of digits> 511). Rejected because numeric compiler diagnostics are not stable application contracts. | Not specified in reference | Constants | Rejected adoption | — | — |
| 159 | Value: 159. MQL5 compiler diagnostic for string-constant has more than 65534 characters. Rejected because numeric compiler diagnostics are not stable application contracts. | Not specified in reference | Constants | Rejected adoption | — | — |
| 160 | Value: 160. MQL5 compiler diagnostic for function definition is unacceptable here. Rejected because numeric compiler diagnostics are not stable application contracts. | Not specified in reference | Constants | Rejected adoption | — | — |
| 161 | Value: 161. MQL5 compiler diagnostic for unexpected end of program. Rejected because numeric compiler diagnostics are not stable application contracts. | Not specified in reference | Constants | Rejected adoption | — | — |
| 162 | Value: 162. MQL5 compiler diagnostic for forward declaration is prohibited for structures. Rejected because numeric compiler diagnostics are not stable application contracts. | Not specified in reference | Constants | Rejected adoption | — | — |
| 163 | Value: 163. MQL5 compiler diagnostic for function with this name is has a duplicate definition and has another return type. Rejected because numeric compiler diagnostics are not stable application contracts. | Not specified in reference | Constants | Rejected adoption | — | — |
| 164 | Value: 164. MQL5 compiler diagnostic for function with this name is has a duplicate definition and has a different set of parameters. Rejected because numeric compiler diagnostics are not stable application contracts. | Not specified in reference | Constants | Rejected adoption | — | — |
| 165 | Value: 165. MQL5 compiler diagnostic for function with this name is has a duplicate definition and implemented. Rejected because numeric compiler diagnostics are not stable application contracts. | Not specified in reference | Constants | Rejected adoption | — | — |
| 166 | Value: 166. MQL5 compiler diagnostic for function overload for this call was missing. Rejected because numeric compiler diagnostics are not stable application contracts. | Not specified in reference | Constants | Rejected adoption | — | — |
| 167 | Value: 167. MQL5 compiler diagnostic for function with a return value of void type unable to return a value. Rejected because numeric compiler diagnostics are not stable application contracts. | Not specified in reference | Constants | Rejected adoption | — | — |
| 168 | Value: 168. MQL5 compiler diagnostic for function is not defined. Rejected because numeric compiler diagnostics are not stable application contracts. | Not specified in reference | Constants | Rejected adoption | — | — |
| 170 | Value: 170. MQL5 compiler diagnostic for value is expected. Rejected because numeric compiler diagnostics are not stable application contracts. | Not specified in reference | Constants | Rejected adoption | — | — |
| 171 | Value: 171. MQL5 compiler diagnostic for in case expression only integer constants are valid. Rejected because numeric compiler diagnostics are not stable application contracts. | Not specified in reference | Constants | Rejected adoption | — | — |
| 172 | Value: 172. MQL5 compiler diagnostic for the value of case in this switch is already used. Rejected because numeric compiler diagnostics are not stable application contracts. | Not specified in reference | Constants | Rejected adoption | — | — |
| 173 | Value: 173. MQL5 compiler diagnostic for integer is expected. Rejected because numeric compiler diagnostics are not stable application contracts. | Not specified in reference | Constants | Rejected adoption | — | — |
| 174 | Value: 174. MQL5 compiler diagnostic for in #import expression file name is expected. Rejected because numeric compiler diagnostics are not stable application contracts. | Not specified in reference | Constants | Rejected adoption | — | — |
| 175 | Value: 175. MQL5 compiler diagnostic for expressions are not allowed on global level. Rejected because numeric compiler diagnostics are not stable application contracts. | Not specified in reference | Constants | Rejected adoption | — | — |
| 176 | Value: 176. MQL5 compiler diagnostic for omitted parenthesis ")" before ";". Rejected because numeric compiler diagnostics are not stable application contracts. | Not specified in reference | Constants | Rejected adoption | — | — |
| 177 | Value: 177. MQL5 compiler diagnostic for to the left of equality sign a variable is expected. Rejected because numeric compiler diagnostics are not stable application contracts. | Not specified in reference | Constants | Rejected adoption | — | — |
| 178 | Value: 178. MQL5 compiler diagnostic for the result of expression is not used. Rejected because numeric compiler diagnostics are not stable application contracts. | Not specified in reference | Constants | Rejected adoption | — | — |
| 179 | Value: 179. MQL5 compiler diagnostic for declaring of variables is not allowed in case. Rejected because numeric compiler diagnostics are not stable application contracts. | Not specified in reference | Constants | Rejected adoption | — | — |
| 180 | Value: 180. MQL5 compiler diagnostic for implicit conversion from a string to a number. Rejected because numeric compiler diagnostics are not stable application contracts. | Not specified in reference | Constants | Rejected adoption | — | — |
| 181 | Value: 181. MQL5 compiler diagnostic for implicit conversion of a number to a string. Rejected because numeric compiler diagnostics are not stable application contracts. | Not specified in reference | Constants | Rejected adoption | — | — |
| 182 | Value: 182. MQL5 compiler diagnostic for ambiguous call of an overloaded function (several overloads fit). Rejected because numeric compiler diagnostics are not stable application contracts. | Not specified in reference | Constants | Rejected adoption | — | — |
| 183 | Value: 183. MQL5 compiler diagnostic for illegal else without proper if. Rejected because numeric compiler diagnostics are not stable application contracts. | Not specified in reference | Constants | Rejected adoption | — | — |
| 184 | Value: 184. MQL5 compiler diagnostic for invalid case or default without a switch. Rejected because numeric compiler diagnostics are not stable application contracts. | Not specified in reference | Constants | Rejected adoption | — | — |
| 185 | Value: 185. MQL5 compiler diagnostic for inappropriate use of ellipsis. Rejected because numeric compiler diagnostics are not stable application contracts. | Not specified in reference | Constants | Rejected adoption | — | — |
| 186 | Value: 186. MQL5 compiler diagnostic for the initializing sequence has more elements than the initialized variable. Rejected because numeric compiler diagnostics are not stable application contracts. | Not specified in reference | Constants | Rejected adoption | — | — |
| 187 | Value: 187. MQL5 compiler diagnostic for a constant for case expected. Rejected because numeric compiler diagnostics are not stable application contracts. | Not specified in reference | Constants | Rejected adoption | — | — |
| 188 | Value: 188. MQL5 compiler diagnostic for a constant expression required. Rejected because numeric compiler diagnostics are not stable application contracts. | Not specified in reference | Constants | Rejected adoption | — | — |
| 189 | Value: 189. MQL5 compiler diagnostic for a constant variable unable to be changed. Rejected because numeric compiler diagnostics are not stable application contracts. | Not specified in reference | Constants | Rejected adoption | — | — |
| 190 | Value: 190. MQL5 compiler diagnostic for closing bracket or a comma is expected (declaring array member). Rejected because numeric compiler diagnostics are not stable application contracts. | Not specified in reference | Constants | Rejected adoption | — | — |
| 191 | Value: 191. MQL5 compiler diagnostic for enumerator identifier has a duplicate definition. Rejected because numeric compiler diagnostics are not stable application contracts. | Not specified in reference | Constants | Rejected adoption | — | — |
| 192 | Value: 192. MQL5 compiler diagnostic for enumeration unable to have access modifiers (const, extern, static). Rejected because numeric compiler diagnostics are not stable application contracts. | Not specified in reference | Constants | Rejected adoption | — | — |
| 193 | Value: 193. MQL5 compiler diagnostic for enumeration member already declared with a different value. Rejected because numeric compiler diagnostics are not stable application contracts. | Not specified in reference | Constants | Rejected adoption | — | — |
| 194 | Value: 194. MQL5 compiler diagnostic for there is a variable defined with the same name. Rejected because numeric compiler diagnostics are not stable application contracts. | Not specified in reference | Constants | Rejected adoption | — | — |
| 195 | Value: 195. MQL5 compiler diagnostic for there is a structure defined with the same name. Rejected because numeric compiler diagnostics are not stable application contracts. | Not specified in reference | Constants | Rejected adoption | — | — |
| 196 | Value: 196. MQL5 compiler diagnostic for name of enumeration member expected. Rejected because numeric compiler diagnostics are not stable application contracts. | Not specified in reference | Constants | Rejected adoption | — | — |
| 197 | Value: 197. MQL5 compiler diagnostic for integer expression expected. Rejected because numeric compiler diagnostics are not stable application contracts. | Not specified in reference | Constants | Rejected adoption | — | — |
| 198 | Value: 198. MQL5 compiler diagnostic for division by zero in constant expression. Rejected because numeric compiler diagnostics are not stable application contracts. | Not specified in reference | Constants | Rejected adoption | — | — |
| 199 | Value: 199. MQL5 compiler diagnostic for invalid number of parameters in the function. Rejected because numeric compiler diagnostics are not stable application contracts. | Not specified in reference | Constants | Rejected adoption | — | — |
| 200 | Value: 200. MQL5 compiler diagnostic for parameter by reference must be a variable. Rejected because numeric compiler diagnostics are not stable application contracts. | Not specified in reference | Constants | Rejected adoption | — | — |
| 201 | Value: 201. MQL5 compiler diagnostic for variable of the same type to pass by reference expected. Rejected because numeric compiler diagnostics are not stable application contracts. | Not specified in reference | Constants | Rejected adoption | — | — |
| 202 | Value: 202. MQL5 compiler diagnostic for a constant variable unable to be passed by a non-constant reference. Rejected because numeric compiler diagnostics are not stable application contracts. | Not specified in reference | Constants | Rejected adoption | — | — |
| 203 | Value: 203. MQL5 compiler diagnostic for requires a positive integer constant. Rejected because numeric compiler diagnostics are not stable application contracts. | Not specified in reference | Constants | Rejected adoption | — | — |
| 204 | Value: 204. MQL5 compiler diagnostic for failed to access protected class member. Rejected because numeric compiler diagnostics are not stable application contracts. | Not specified in reference | Constants | Rejected adoption | — | — |
| 205 | Value: 205. MQL5 compiler diagnostic for import has a duplicate definition in another way. Rejected because numeric compiler diagnostics are not stable application contracts. | Not specified in reference | Constants | Rejected adoption | — | — |
| 208 | Value: 208. MQL5 compiler diagnostic for executable file not created. Rejected because numeric compiler diagnostics are not stable application contracts. | Not specified in reference | Constants | Rejected adoption | — | — |
| 209 | Value: 209. MQL5 compiler diagnostic for 'OnCalculate' entry point missing for the indicator. Rejected because numeric compiler diagnostics are not stable application contracts. | Not specified in reference | Constants | Rejected adoption | — | — |
| 210 | Value: 210. MQL5 compiler diagnostic for the continue operation can be used only inside a loop. Rejected because numeric compiler diagnostics are not stable application contracts. | Not specified in reference | Constants | Rejected adoption | — | — |
| 211 | Value: 211. MQL5 compiler diagnostic for error accessing private (closed) class member. Rejected because numeric compiler diagnostics are not stable application contracts. | Not specified in reference | Constants | Rejected adoption | — | — |
| 213 | Value: 213. MQL5 compiler diagnostic for method of structure or class is not declared. Rejected because numeric compiler diagnostics are not stable application contracts. | Not specified in reference | Constants | Rejected adoption | — | — |
| 214 | Value: 214. MQL5 compiler diagnostic for error accessing private (closed) class method. Rejected because numeric compiler diagnostics are not stable application contracts. | Not specified in reference | Constants | Rejected adoption | — | — |
| 216 | Value: 216. MQL5 compiler diagnostic for copying of structures with objects is not allowed. Rejected because numeric compiler diagnostics are not stable application contracts. | Not specified in reference | Constants | Rejected adoption | — | — |
| 218 | Value: 218. MQL5 compiler diagnostic for index out of array range. Rejected because numeric compiler diagnostics are not stable application contracts. | Not specified in reference | Constants | Rejected adoption | — | — |
| 219 | Value: 219. MQL5 compiler diagnostic for array initialization in structure or class declaration not allowed. Rejected because numeric compiler diagnostics are not stable application contracts. | Not specified in reference | Constants | Rejected adoption | — | — |
| 220 | Value: 220. MQL5 compiler diagnostic for class constructor unable to have parameters. Rejected because numeric compiler diagnostics are not stable application contracts. | Not specified in reference | Constants | Rejected adoption | — | — |
| 221 | Value: 221. MQL5 compiler diagnostic for class destructor can not have parameters. Rejected because numeric compiler diagnostics are not stable application contracts. | Not specified in reference | Constants | Rejected adoption | — | — |
| 222 | Value: 222. MQL5 compiler diagnostic for class method or structure with the same name and parameters have already been declared. Rejected because numeric compiler diagnostics are not stable application contracts. | Not specified in reference | Constants | Rejected adoption | — | — |
| 223 | Value: 223. MQL5 compiler diagnostic for operand expected. Rejected because numeric compiler diagnostics are not stable application contracts. | Not specified in reference | Constants | Rejected adoption | — | — |
| 224 | Value: 224. MQL5 compiler diagnostic for class method or structure with the same name exists, but with different parameters (declaration!=implementation). Rejected because numeric compiler diagnostics are not stable application contracts. | Not specified in reference | Constants | Rejected adoption | — | — |
| 225 | Value: 225. MQL5 compiler diagnostic for imported function is not described. Rejected because numeric compiler diagnostics are not stable application contracts. | Not specified in reference | Constants | Rejected adoption | — | — |
| 226 | Value: 226. MQL5 compiler diagnostic for zeroMemory() is not allowed for objects with protected members or inheritance. Rejected because numeric compiler diagnostics are not stable application contracts. | Not specified in reference | Constants | Rejected adoption | — | — |
| 227 | Value: 227. MQL5 compiler diagnostic for ambiguous call of the overloaded function (exact match of parameters for several overloads). Rejected because numeric compiler diagnostics are not stable application contracts. | Not specified in reference | Constants | Rejected adoption | — | — |
| 228 | Value: 228. MQL5 compiler diagnostic for variable name expected. Rejected because numeric compiler diagnostics are not stable application contracts. | Not specified in reference | Constants | Rejected adoption | — | — |
| 229 | Value: 229. MQL5 compiler diagnostic for a reference unable to be declared in this place. Rejected because numeric compiler diagnostics are not stable application contracts. | Not specified in reference | Constants | Rejected adoption | — | — |
| 230 | Value: 230. MQL5 compiler diagnostic for already used as the enumeration name. Rejected because numeric compiler diagnostics are not stable application contracts. | Not specified in reference | Constants | Rejected adoption | — | — |
| 232 | Value: 232. MQL5 compiler diagnostic for class or structure expected. Rejected because numeric compiler diagnostics are not stable application contracts. | Not specified in reference | Constants | Rejected adoption | — | — |
| 235 | Value: 235. MQL5 compiler diagnostic for unable to call 'delete' operator to delete the array. Rejected because numeric compiler diagnostics are not stable application contracts. | Not specified in reference | Constants | Rejected adoption | — | — |
| 236 | Value: 236. MQL5 compiler diagnostic for operator ' while' expected. Rejected because numeric compiler diagnostics are not stable application contracts. | Not specified in reference | Constants | Rejected adoption | — | — |
| 237 | Value: 237. MQL5 compiler diagnostic for operator 'delete' must have a pointer. Rejected because numeric compiler diagnostics are not stable application contracts. | Not specified in reference | Constants | Rejected adoption | — | — |
| 238 | Value: 238. MQL5 compiler diagnostic for there is 'default' for this 'switch' already. Rejected because numeric compiler diagnostics are not stable application contracts. | Not specified in reference | Constants | Rejected adoption | — | — |
| 239 | Value: 239. MQL5 compiler diagnostic for syntax error. Rejected because numeric compiler diagnostics are not stable application contracts. | Not specified in reference | Constants | Rejected adoption | — | — |
| 240 | Value: 240. MQL5 compiler diagnostic for escape-sequence can occur only in strings (starts with '\'). Rejected because numeric compiler diagnostics are not stable application contracts. | Not specified in reference | Constants | Rejected adoption | — | — |
| 241 | Value: 241. MQL5 compiler diagnostic for array required - square bracket '[' does not apply to an array, or non arrays are passed as array parameters. Rejected because numeric compiler diagnostics are not stable application contracts. | Not specified in reference | Constants | Rejected adoption | — | — |
| 242 | Value: 242. MQL5 compiler diagnostic for can not be initialized through the initialization sequence. Rejected because numeric compiler diagnostics are not stable application contracts. | Not specified in reference | Constants | Rejected adoption | — | — |
| 243 | Value: 243. MQL5 compiler diagnostic for import is not defined. Rejected because numeric compiler diagnostics are not stable application contracts. | Not specified in reference | Constants | Rejected adoption | — | — |
| 244 | Value: 244. MQL5 compiler diagnostic for optimizer error on the syntactic tree. Rejected because numeric compiler diagnostics are not stable application contracts. | Not specified in reference | Constants | Rejected adoption | — | — |
| 245 | Value: 245. MQL5 compiler diagnostic for declared too many structures (try to simplify the program). Rejected because numeric compiler diagnostics are not stable application contracts. | Not specified in reference | Constants | Rejected adoption | — | — |
| 246 | Value: 246. MQL5 compiler diagnostic for conversion of the parameter is not allowed. Rejected because numeric compiler diagnostics are not stable application contracts. | Not specified in reference | Constants | Rejected adoption | — | — |
| 247 | Value: 247. MQL5 compiler diagnostic for incorrect use of the 'delete' operator. Rejected because numeric compiler diagnostics are not stable application contracts. | Not specified in reference | Constants | Rejected adoption | — | — |
| 248 | Value: 248. MQL5 compiler diagnostic for it's not allowed to declare a pointer to a reference. Rejected because numeric compiler diagnostics are not stable application contracts. | Not specified in reference | Constants | Rejected adoption | — | — |
| 249 | Value: 249. MQL5 compiler diagnostic for it's not allowed to declare a reference to a reference. Rejected because numeric compiler diagnostics are not stable application contracts. | Not specified in reference | Constants | Rejected adoption | — | — |
| 250 | Value: 250. MQL5 compiler diagnostic for it's not allowed to declare a pointer to a pointer. Rejected because numeric compiler diagnostics are not stable application contracts. | Not specified in reference | Constants | Rejected adoption | — | — |
| 251 | Value: 251. MQL5 compiler diagnostic for structure declaration in the list of parameter is not allowed. Rejected because numeric compiler diagnostics are not stable application contracts. | Not specified in reference | Constants | Rejected adoption | — | — |
| 252 | Value: 252. MQL5 compiler diagnostic for invalid operation of typecasting. Rejected because numeric compiler diagnostics are not stable application contracts. | Not specified in reference | Constants | Rejected adoption | — | — |
| 253 | Value: 253. MQL5 compiler diagnostic for a pointer can be declared only for a class or structure. Rejected because numeric compiler diagnostics are not stable application contracts. | Not specified in reference | Constants | Rejected adoption | — | — |
| 256 | Value: 256. MQL5 compiler diagnostic for undeclared identifier. Rejected because numeric compiler diagnostics are not stable application contracts. | Not specified in reference | Constants | Rejected adoption | — | — |
| 257 | Value: 257. MQL5 compiler diagnostic for executable code optimizer error. Rejected because numeric compiler diagnostics are not stable application contracts. | Not specified in reference | Constants | Rejected adoption | — | — |
| 258 | Value: 258. MQL5 compiler diagnostic for executable code generation error. Rejected because numeric compiler diagnostics are not stable application contracts. | Not specified in reference | Constants | Rejected adoption | — | — |
| 260 | Value: 260. MQL5 compiler diagnostic for invalid expression for the 'switch' operator. Rejected because numeric compiler diagnostics are not stable application contracts. | Not specified in reference | Constants | Rejected adoption | — | — |
| 261 | Value: 261. MQL5 compiler diagnostic for pool of string constants overfilled, simplify program. Rejected because numeric compiler diagnostics are not stable application contracts. | Not specified in reference | Constants | Rejected adoption | — | — |
| 262 | Value: 262. MQL5 compiler diagnostic for unable to convert to enumeration. Rejected because numeric compiler diagnostics are not stable application contracts. | Not specified in reference | Constants | Rejected adoption | — | — |
| 263 | Value: 263. MQL5 compiler diagnostic for do not use 'virtual' for data (members of a class or structure). Rejected because numeric compiler diagnostics are not stable application contracts. | Not specified in reference | Constants | Rejected adoption | — | — |
| 264 | Value: 264. MQL5 compiler diagnostic for unable to call protected method of class. Rejected because numeric compiler diagnostics are not stable application contracts. | Not specified in reference | Constants | Rejected adoption | — | — |
| 265 | Value: 265. MQL5 compiler diagnostic for overridden virtual functions return a different type. Rejected because numeric compiler diagnostics are not stable application contracts. | Not specified in reference | Constants | Rejected adoption | — | — |
| 266 | Value: 266. MQL5 compiler diagnostic for class unable to be inherited from a structure. Rejected because numeric compiler diagnostics are not stable application contracts. | Not specified in reference | Constants | Rejected adoption | — | — |
| 267 | Value: 267. MQL5 compiler diagnostic for structure unable to be inherited from a class. Rejected because numeric compiler diagnostics are not stable application contracts. | Not specified in reference | Constants | Rejected adoption | — | — |
| 268 | Value: 268. MQL5 compiler diagnostic for constructor unable to be virtual (virtual specifier is not allowed). Rejected because numeric compiler diagnostics are not stable application contracts. | Not specified in reference | Constants | Rejected adoption | — | — |
| 269 | Value: 269. MQL5 compiler diagnostic for method of structure unable to be virtual. Rejected because numeric compiler diagnostics are not stable application contracts. | Not specified in reference | Constants | Rejected adoption | — | — |
| 270 | Value: 270. MQL5 compiler diagnostic for function must have a body. Rejected because numeric compiler diagnostics are not stable application contracts. | Not specified in reference | Constants | Rejected adoption | — | — |
| 271 | Value: 271. MQL5 compiler diagnostic for overloading of system functions (terminal functions) is prohibited. Rejected because numeric compiler diagnostics are not stable application contracts. | Not specified in reference | Constants | Rejected adoption | — | — |
| 272 | Value: 272. MQL5 compiler diagnostic for const specifier is invalid for functions that are not members of a class or structure. Rejected because numeric compiler diagnostics are not stable application contracts. | Not specified in reference | Constants | Rejected adoption | — | — |
| 274 | Value: 274. MQL5 compiler diagnostic for not allowed to change class members in constant method. Rejected because numeric compiler diagnostics are not stable application contracts. | Not specified in reference | Constants | Rejected adoption | — | — |
| 276 | Value: 276. MQL5 compiler diagnostic for inappropriate initialization sequence. Rejected because numeric compiler diagnostics are not stable application contracts. | Not specified in reference | Constants | Rejected adoption | — | — |
| 277 | Value: 277. MQL5 compiler diagnostic for missed default value for the parameter (specific declaration of default parameters). Rejected because numeric compiler diagnostics are not stable application contracts. | Not specified in reference | Constants | Rejected adoption | — | — |
| 278 | Value: 278. MQL5 compiler diagnostic for overriding the default parameter (different values in declaration and implementation). Rejected because numeric compiler diagnostics are not stable application contracts. | Not specified in reference | Constants | Rejected adoption | — | — |
| 279 | Value: 279. MQL5 compiler diagnostic for not allowed to call non-constant method for a constant object. Rejected because numeric compiler diagnostics are not stable application contracts. | Not specified in reference | Constants | Rejected adoption | — | — |
| 280 | Value: 280. MQL5 compiler diagnostic for an object is necessary for accessing members (a dot for a non class/structure is specified). Rejected because numeric compiler diagnostics are not stable application contracts. | Not specified in reference | Constants | Rejected adoption | — | — |
| 281 | Value: 281. MQL5 compiler diagnostic for the name of an already declared structure unable to be used in declaration. Rejected because numeric compiler diagnostics are not stable application contracts. | Not specified in reference | Constants | Rejected adoption | — | — |
| 284 | Value: 284. MQL5 compiler diagnostic for unauthorized conversion (at closed inheritance). Rejected because numeric compiler diagnostics are not stable application contracts. | Not specified in reference | Constants | Rejected adoption | — | — |
| 285 | Value: 285. MQL5 compiler diagnostic for structures and arrays unable to be used as input variables. Rejected because numeric compiler diagnostics are not stable application contracts. | Not specified in reference | Constants | Rejected adoption | — | — |
| 286 | Value: 286. MQL5 compiler diagnostic for const specifier is not valid for constructor/destructor. Rejected because numeric compiler diagnostics are not stable application contracts. | Not specified in reference | Constants | Rejected adoption | — | — |
| 287 | Value: 287. MQL5 compiler diagnostic for incorrect string expression for a datetime. Rejected because numeric compiler diagnostics are not stable application contracts. | Not specified in reference | Constants | Rejected adoption | — | — |
| 288 | Value: 288. MQL5 compiler diagnostic for unknown property (#property). Rejected because numeric compiler diagnostics are not stable application contracts. | Not specified in reference | Constants | Rejected adoption | — | — |
| 289 | Value: 289. MQL5 compiler diagnostic for incorrect value of a property. Rejected because numeric compiler diagnostics are not stable application contracts. | Not specified in reference | Constants | Rejected adoption | — | — |
| 290 | Value: 290. MQL5 compiler diagnostic for invalid index for a property in #property. Rejected because numeric compiler diagnostics are not stable application contracts. | Not specified in reference | Constants | Rejected adoption | — | — |
| 291 | Value: 291. MQL5 compiler diagnostic for call parameter omitted - <func (x,)>. Rejected because numeric compiler diagnostics are not stable application contracts. | Not specified in reference | Constants | Rejected adoption | — | — |
| 293 | Value: 293. MQL5 compiler diagnostic for object must be passed by reference. Rejected because numeric compiler diagnostics are not stable application contracts. | Not specified in reference | Constants | Rejected adoption | — | — |
| 294 | Value: 294. MQL5 compiler diagnostic for array must be passed by reference. Rejected because numeric compiler diagnostics are not stable application contracts. | Not specified in reference | Constants | Rejected adoption | — | — |
| 295 | Value: 295. MQL5 compiler diagnostic for function was declared as exportable. Rejected because numeric compiler diagnostics are not stable application contracts. | Not specified in reference | Constants | Rejected adoption | — | — |
| 296 | Value: 296. MQL5 compiler diagnostic for function was not declared as exportable. Rejected because numeric compiler diagnostics are not stable application contracts. | Not specified in reference | Constants | Rejected adoption | — | — |
| 297 | Value: 297. MQL5 compiler diagnostic for it is prohibited to export imported function. Rejected because numeric compiler diagnostics are not stable application contracts. | Not specified in reference | Constants | Rejected adoption | — | — |
| 298 | Value: 298. MQL5 compiler diagnostic for imported function unable to have this parameter (prohibited to pass a pointer, class or structure containing a…. Rejected because numeric compiler diagnostics are not stable application contracts. | Not specified in reference | Constants | Rejected adoption | — | — |
| 299 | Value: 299. MQL5 compiler diagnostic for must be a class. Rejected because numeric compiler diagnostics are not stable application contracts. | Not specified in reference | Constants | Rejected adoption | — | — |
| 300 | Value: 300. MQL5 compiler diagnostic for #import was not closed. Rejected because numeric compiler diagnostics are not stable application contracts. | Not specified in reference | Constants | Rejected adoption | — | — |
| 302 | Value: 302. MQL5 compiler diagnostic for type mismatch. Rejected because numeric compiler diagnostics are not stable application contracts. | Not specified in reference | Constants | Rejected adoption | — | — |
| 303 | Value: 303. MQL5 compiler diagnostic for extern variable is already initialized. Rejected because numeric compiler diagnostics are not stable application contracts. | Not specified in reference | Constants | Rejected adoption | — | — |
| 304 | Value: 304. MQL5 compiler diagnostic for no exported function or entry point found. Rejected because numeric compiler diagnostics are not stable application contracts. | Not specified in reference | Constants | Rejected adoption | — | — |
| 305 | Value: 305. MQL5 compiler diagnostic for explicit constructor call is not allowed. Rejected because numeric compiler diagnostics are not stable application contracts. | Not specified in reference | Constants | Rejected adoption | — | — |
| 306 | Value: 306. MQL5 compiler diagnostic for method was declared as constant. Rejected because numeric compiler diagnostics are not stable application contracts. | Not specified in reference | Constants | Rejected adoption | — | — |
| 307 | Value: 307. MQL5 compiler diagnostic for method was not declared as constant. Rejected because numeric compiler diagnostics are not stable application contracts. | Not specified in reference | Constants | Rejected adoption | — | — |
| 308 | Value: 308. MQL5 compiler diagnostic for incorrect size of the resource file. Rejected because numeric compiler diagnostics are not stable application contracts. | Not specified in reference | Constants | Rejected adoption | — | — |
| 309 | Value: 309. MQL5 compiler diagnostic for incorrect resource name. Rejected because numeric compiler diagnostics are not stable application contracts. | Not specified in reference | Constants | Rejected adoption | — | — |
| 310 | Value: 310. MQL5 compiler diagnostic for resource file opening error. Rejected because numeric compiler diagnostics are not stable application contracts. | Not specified in reference | Constants | Rejected adoption | — | — |
| 311 | Value: 311. MQL5 compiler diagnostic for resource file reading error. Rejected because numeric compiler diagnostics are not stable application contracts. | Not specified in reference | Constants | Rejected adoption | — | — |
| 312 | Value: 312. MQL5 compiler diagnostic for unknown resource type. Rejected because numeric compiler diagnostics are not stable application contracts. | Not specified in reference | Constants | Rejected adoption | — | — |
| 313 | Value: 313. MQL5 compiler diagnostic for incorrect path to the resource file. Rejected because numeric compiler diagnostics are not stable application contracts. | Not specified in reference | Constants | Rejected adoption | — | — |
| 314 | Value: 314. MQL5 compiler diagnostic for the specified resource name is already used. Rejected because numeric compiler diagnostics are not stable application contracts. | Not specified in reference | Constants | Rejected adoption | — | — |
| 315 | Value: 315. MQL5 compiler diagnostic for argument expected for the function-like macro. Rejected because numeric compiler diagnostics are not stable application contracts. | Not specified in reference | Constants | Rejected adoption | — | — |
| 316 | Value: 316. MQL5 compiler diagnostic for unexpected symbol in macro definition. Rejected because numeric compiler diagnostics are not stable application contracts. | Not specified in reference | Constants | Rejected adoption | — | — |
| 317 | Value: 317. MQL5 compiler diagnostic for error in formal parameters of the macro. Rejected because numeric compiler diagnostics are not stable application contracts. | Not specified in reference | Constants | Rejected adoption | — | — |
| 318 | Value: 318. MQL5 compiler diagnostic for invalid number of parameters for a macro. Rejected because numeric compiler diagnostics are not stable application contracts. | Not specified in reference | Constants | Rejected adoption | — | — |
| 319 | Value: 319. MQL5 compiler diagnostic for too many parameters for a macro. Rejected because numeric compiler diagnostics are not stable application contracts. | Not specified in reference | Constants | Rejected adoption | — | — |
| 320 | Value: 320. MQL5 compiler diagnostic for too complex, simplify the macro. Rejected because numeric compiler diagnostics are not stable application contracts. | Not specified in reference | Constants | Rejected adoption | — | — |
| 321 | Value: 321. MQL5 compiler diagnostic for parameter for EnumToString() can be only an enumeration. Rejected because numeric compiler diagnostics are not stable application contracts. | Not specified in reference | Constants | Rejected adoption | — | — |
| 322 | Value: 322. MQL5 compiler diagnostic for the resource name exceeds the supported length. Rejected because numeric compiler diagnostics are not stable application contracts. | Not specified in reference | Constants | Rejected adoption | — | — |
| 323 | Value: 323. MQL5 compiler diagnostic for unsupported image format (only BMP with 24 or 32 bit color depth is supported). Rejected because numeric compiler diagnostics are not stable application contracts. | Not specified in reference | Constants | Rejected adoption | — | — |
| 324 | Value: 324. MQL5 compiler diagnostic for an array unable to be declared in operator. Rejected because numeric compiler diagnostics are not stable application contracts. | Not specified in reference | Constants | Rejected adoption | — | — |
| 325 | Value: 325. MQL5 compiler diagnostic for the function can be declared only in the global scope. Rejected because numeric compiler diagnostics are not stable application contracts. | Not specified in reference | Constants | Rejected adoption | — | — |
| 326 | Value: 326. MQL5 compiler diagnostic for the declaration is not allowed for the current scope. Rejected because numeric compiler diagnostics are not stable application contracts. | Not specified in reference | Constants | Rejected adoption | — | — |
| 327 | Value: 327. MQL5 compiler diagnostic for initialization of static variables with the values of local variables is not allowed. Rejected because numeric compiler diagnostics are not stable application contracts. | Not specified in reference | Constants | Rejected adoption | — | — |
| 328 | Value: 328. MQL5 compiler diagnostic for illegal declaration of an array of objects that do not have a default constructor. Rejected because numeric compiler diagnostics are not stable application contracts. | Not specified in reference | Constants | Rejected adoption | — | — |
| 329 | Value: 329. MQL5 compiler diagnostic for initialization list allowed only for constructors. Rejected because numeric compiler diagnostics are not stable application contracts. | Not specified in reference | Constants | Rejected adoption | — | — |
| 330 | Value: 330. MQL5 compiler diagnostic for no function definition after initialization list. Rejected because numeric compiler diagnostics are not stable application contracts. | Not specified in reference | Constants | Rejected adoption | — | — |
| 331 | Value: 331. MQL5 compiler diagnostic for initialization list is empty. Rejected because numeric compiler diagnostics are not stable application contracts. | Not specified in reference | Constants | Rejected adoption | — | — |
| 332 | Value: 332. MQL5 compiler diagnostic for array initialization in a constructor is not allowed. Rejected because numeric compiler diagnostics are not stable application contracts. | Not specified in reference | Constants | Rejected adoption | — | — |
| 333 | Value: 333. MQL5 compiler diagnostic for initializing members of a parent class in the initialization list is not allowed. Rejected because numeric compiler diagnostics are not stable application contracts. | Not specified in reference | Constants | Rejected adoption | — | — |
| 334 | Value: 334. MQL5 compiler diagnostic for expression of the integer type expected. Rejected because numeric compiler diagnostics are not stable application contracts. | Not specified in reference | Constants | Rejected adoption | — | — |
| 335 | Value: 335. MQL5 compiler diagnostic for memory required for the array exceeds the maximum value. Rejected because numeric compiler diagnostics are not stable application contracts. | Not specified in reference | Constants | Rejected adoption | — | — |
| 336 | Value: 336. MQL5 compiler diagnostic for memory required for the structure exceeds the maximum value. Rejected because numeric compiler diagnostics are not stable application contracts. | Not specified in reference | Constants | Rejected adoption | — | — |
| 337 | Value: 337. MQL5 compiler diagnostic for memory required for the variables declared on the global level exceeds the maximum value. Rejected because numeric compiler diagnostics are not stable application contracts. | Not specified in reference | Constants | Rejected adoption | — | — |
| 338 | Value: 338. MQL5 compiler diagnostic for memory required for local variables exceeds the maximum value. Rejected because numeric compiler diagnostics are not stable application contracts. | Not specified in reference | Constants | Rejected adoption | — | — |
| 339 | Value: 339. MQL5 compiler diagnostic for constructor not defined. Rejected because numeric compiler diagnostics are not stable application contracts. | Not specified in reference | Constants | Rejected adoption | — | — |
| 340 | Value: 340. MQL5 compiler diagnostic for invalid name of the icon file. Rejected because numeric compiler diagnostics are not stable application contracts. | Not specified in reference | Constants | Rejected adoption | — | — |
| 341 | Value: 341. MQL5 compiler diagnostic for could not open the icon file at the specified path. Rejected because numeric compiler diagnostics are not stable application contracts. | Not specified in reference | Constants | Rejected adoption | — | — |
| 342 | Value: 342. MQL5 compiler diagnostic for the icon file is incorrect and is not of the ICO format. Rejected because numeric compiler diagnostics are not stable application contracts. | Not specified in reference | Constants | Rejected adoption | — | — |
| 343 | Value: 343. MQL5 compiler diagnostic for reinitialization of a member in a class/structure constructor using the initialization list. Rejected because numeric compiler diagnostics are not stable application contracts. | Not specified in reference | Constants | Rejected adoption | — | — |
| 344 | Value: 344. MQL5 compiler diagnostic for initialization of static members in the constructor initialization list is not allowed. Rejected because numeric compiler diagnostics are not stable application contracts. | Not specified in reference | Constants | Rejected adoption | — | — |
| 345 | Value: 345. MQL5 compiler diagnostic for initialization of a non-static member of a class/structure on a global level is not allowed. Rejected because numeric compiler diagnostics are not stable application contracts. | Not specified in reference | Constants | Rejected adoption | — | — |
| 346 | Value: 346. MQL5 compiler diagnostic for the name of the class/structure method matches the name of an earlier declared member. Rejected because numeric compiler diagnostics are not stable application contracts. | Not specified in reference | Constants | Rejected adoption | — | — |
| 347 | Value: 347. MQL5 compiler diagnostic for the name of the class/structure member matches the name of an earlier declared method. Rejected because numeric compiler diagnostics are not stable application contracts. | Not specified in reference | Constants | Rejected adoption | — | — |
| 348 | Value: 348. MQL5 compiler diagnostic for virtual function unable to be declared as static. Rejected because numeric compiler diagnostics are not stable application contracts. | Not specified in reference | Constants | Rejected adoption | — | — |
| 349 | Value: 349. MQL5 compiler diagnostic for the const modifier is not allowed for static functions. Rejected because numeric compiler diagnostics are not stable application contracts. | Not specified in reference | Constants | Rejected adoption | — | — |
| 350 | Value: 350. MQL5 compiler diagnostic for constructor or destructor unable to be static. Rejected because numeric compiler diagnostics are not stable application contracts. | Not specified in reference | Constants | Rejected adoption | — | — |
| 351 | Value: 351. MQL5 compiler diagnostic for non-static member/method of a class or a structure unable to be accessed from a static function. Rejected because numeric compiler diagnostics are not stable application contracts. | Not specified in reference | Constants | Rejected adoption | — | — |
| 352 | Value: 352. MQL5 compiler diagnostic for an overload operation (+,-,[],++,-- etc.) is expected after the operator keyword. Rejected because numeric compiler diagnostics are not stable application contracts. | Not specified in reference | Constants | Rejected adoption | — | — |
| 353 | Value: 353. MQL5 compiler diagnostic for not all operations can be overloaded in MQL5. Rejected because numeric compiler diagnostics are not stable application contracts. | Not specified in reference | Constants | Rejected adoption | — | — |
| 354 | Value: 354. MQL5 compiler diagnostic for definition does not match declaration. Rejected because numeric compiler diagnostics are not stable application contracts. | Not specified in reference | Constants | Rejected adoption | — | — |
| 355 | Value: 355. MQL5 compiler diagnostic for an invalid number of parameters is specified for the operator. Rejected because numeric compiler diagnostics are not stable application contracts. | Not specified in reference | Constants | Rejected adoption | — | — |
| 356 | Value: 356. MQL5 compiler diagnostic for event handling function missing. Rejected because numeric compiler diagnostics are not stable application contracts. | Not specified in reference | Constants | Rejected adoption | — | — |
| 357 | Value: 357. MQL5 compiler diagnostic for method unable to be exported. Rejected because numeric compiler diagnostics are not stable application contracts. | Not specified in reference | Constants | Rejected adoption | — | — |
| 358 | Value: 358. MQL5 compiler diagnostic for a pointer to the constant object unable to be normalized by a non-constant object. Rejected because numeric compiler diagnostics are not stable application contracts. | Not specified in reference | Constants | Rejected adoption | — | — |
| 359 | Value: 359. MQL5 compiler diagnostic for class templates are not supported yet. Rejected because numeric compiler diagnostics are not stable application contracts. | Not specified in reference | Constants | Rejected adoption | — | — |
| 360 | Value: 360. MQL5 compiler diagnostic for function template overload is not supported yet. Rejected because numeric compiler diagnostics are not stable application contracts. | Not specified in reference | Constants | Rejected adoption | — | — |
| 361 | Value: 361. MQL5 compiler diagnostic for function template unable to be applied. Rejected because numeric compiler diagnostics are not stable application contracts. | Not specified in reference | Constants | Rejected adoption | — | — |
| 362 | Value: 362. MQL5 compiler diagnostic for ambiguous parameter in function template (several parameter types can be applied). Rejected because numeric compiler diagnostics are not stable application contracts. | Not specified in reference | Constants | Rejected adoption | — | — |
| 363 | Value: 363. MQL5 compiler diagnostic for unable to determine the parameter type, by which the function template argument should be normalized. Rejected because numeric compiler diagnostics are not stable application contracts. | Not specified in reference | Constants | Rejected adoption | — | — |
| 364 | Value: 364. MQL5 compiler diagnostic for incorrect number of parameters in the function template. Rejected because numeric compiler diagnostics are not stable application contracts. | Not specified in reference | Constants | Rejected adoption | — | — |
| 365 | Value: 365. MQL5 compiler diagnostic for function template unable to be virtual. Rejected because numeric compiler diagnostics are not stable application contracts. | Not specified in reference | Constants | Rejected adoption | — | — |
| 366 | Value: 366. MQL5 compiler diagnostic for function templates unable to be exported. Rejected because numeric compiler diagnostics are not stable application contracts. | Not specified in reference | Constants | Rejected adoption | — | — |
| 367 | Value: 367. MQL5 compiler diagnostic for function templates unable to be imported. Rejected because numeric compiler diagnostics are not stable application contracts. | Not specified in reference | Constants | Rejected adoption | — | — |
| 368 | Value: 368. MQL5 compiler diagnostic for structures containing the objects are not allowed. Rejected because numeric compiler diagnostics are not stable application contracts. | Not specified in reference | Constants | Rejected adoption | — | — |
| 369 | Value: 369. MQL5 compiler diagnostic for string arrays and structures containing the objects are not allowed. Rejected because numeric compiler diagnostics are not stable application contracts. | Not specified in reference | Constants | Rejected adoption | — | — |
| 370 | Value: 370. MQL5 compiler diagnostic for a static class/structure member must be explicitly initialized. Rejected because numeric compiler diagnostics are not stable application contracts. | Not specified in reference | Constants | Rejected adoption | — | — |
| 371 | Value: 371. MQL5 compiler diagnostic for compiler limitation: the string unable to contain more than 65 535 characters. Rejected because numeric compiler diagnostics are not stable application contracts. | Not specified in reference | Constants | Rejected adoption | — | — |
| 372 | Value: 372. MQL5 compiler diagnostic for inconsistent #ifdef/#endif. Rejected because numeric compiler diagnostics are not stable application contracts. | Not specified in reference | Constants | Rejected adoption | — | — |
| 373 | Value: 373. MQL5 compiler diagnostic for object of class unable to be returned, copy constructor missing. Rejected because numeric compiler diagnostics are not stable application contracts. | Not specified in reference | Constants | Rejected adoption | — | — |
| 374 | Value: 374. MQL5 compiler diagnostic for non-static members and methods unable to be used. Rejected because numeric compiler diagnostics are not stable application contracts. | Not specified in reference | Constants | Rejected adoption | — | — |
| 375 | Value: 375. MQL5 compiler diagnostic for onTesterInit() impossible to use without OnTesterDeinit(). Rejected because numeric compiler diagnostics are not stable application contracts. | Not specified in reference | Constants | Rejected adoption | — | — |
| 376 | Value: 376. MQL5 compiler diagnostic for redefinition of formal parameter '%s'. Rejected because numeric compiler diagnostics are not stable application contracts. | Not specified in reference | Constants | Rejected adoption | — | — |
| 377 | Value: 377. MQL5 compiler diagnostic for macro __FUNCSIG__ and __FUNCTION__ unable to appear outside of a function body. Rejected because numeric compiler diagnostics are not stable application contracts. | Not specified in reference | Constants | Rejected adoption | — | — |
| 378 | Value: 378. MQL5 compiler diagnostic for invalid returned type. For example, this error will be produced for functions imported from DLL that return…. Rejected because numeric compiler diagnostics are not stable application contracts. | Not specified in reference | Constants | Rejected adoption | — | — |
| 379 | Value: 379. MQL5 compiler diagnostic for template usage error. Rejected because numeric compiler diagnostics are not stable application contracts. | Not specified in reference | Constants | Rejected adoption | — | — |
| 380 | Value: 380. MQL5 compiler diagnostic for not used. Rejected because numeric compiler diagnostics are not stable application contracts. | Not specified in reference | Constants | Rejected adoption | — | — |
| 381 | Value: 381. MQL5 compiler diagnostic for illegal syntax when declaring pure virtual function, only "=NULL" or "=0" are allowed. Rejected because numeric compiler diagnostics are not stable application contracts. | Not specified in reference | Constants | Rejected adoption | — | — |
| 382 | Value: 382. MQL5 compiler diagnostic for only virtual functions can be declared with the pure-specifier ("=NULL" or "=0"). Rejected because numeric compiler diagnostics are not stable application contracts. | Not specified in reference | Constants | Rejected adoption | — | — |
| 383 | Value: 383. MQL5 compiler diagnostic for abstract class unable to be instantiated. Rejected because numeric compiler diagnostics are not stable application contracts. | Not specified in reference | Constants | Rejected adoption | — | — |
| 384 | Value: 384. MQL5 compiler diagnostic for a pointer to a user-defined type should be applied as a target type for dynamic casting using the dynamic_cast…. Rejected because numeric compiler diagnostics are not stable application contracts. | Not specified in reference | Constants | Rejected adoption | — | — |
| 385 | Value: 385. MQL5 compiler diagnostic for "Pointer to function" type is expected. Rejected because numeric compiler diagnostics are not stable application contracts. | Not specified in reference | Constants | Rejected adoption | — | — |
| 386 | Value: 386. MQL5 compiler diagnostic for pointers to methods are not supported. Rejected because numeric compiler diagnostics are not stable application contracts. | Not specified in reference | Constants | Rejected adoption | — | — |
| 387 | Value: 387. MQL5 compiler diagnostic for error – unable to define the type of a pointer to function. Rejected because numeric compiler diagnostics are not stable application contracts. | Not specified in reference | Constants | Rejected adoption | — | — |
| 388 | Value: 388. MQL5 compiler diagnostic for type cast is not available due to private inheritance. Rejected because numeric compiler diagnostics are not stable application contracts. | Not specified in reference | Constants | Rejected adoption | — | — |
| 389 | Value: 389. MQL5 compiler diagnostic for a variable with const modifier should be initialized during declaration. Rejected because numeric compiler diagnostics are not stable application contracts. | Not specified in reference | Constants | Rejected adoption | — | — |
| 393 | Value: 393. MQL5 compiler diagnostic for only methods with public access can be declared in an interface. Rejected because numeric compiler diagnostics are not stable application contracts. | Not specified in reference | Constants | Rejected adoption | — | — |
| 394 | Value: 394. MQL5 compiler diagnostic for invalid nesting of an interface inside of another interface. Rejected because numeric compiler diagnostics are not stable application contracts. | Not specified in reference | Constants | Rejected adoption | — | — |
| 395 | Value: 395. MQL5 compiler diagnostic for an interface can only be derived from another interface. Rejected because numeric compiler diagnostics are not stable application contracts. | Not specified in reference | Constants | Rejected adoption | — | — |
| 396 | Value: 396. MQL5 compiler diagnostic for an interface is expected. Rejected because numeric compiler diagnostics are not stable application contracts. | Not specified in reference | Constants | Rejected adoption | — | — |
| 397 | Value: 397. MQL5 compiler diagnostic for interfaces only support public inheritance. Rejected because numeric compiler diagnostics are not stable application contracts. | Not specified in reference | Constants | Rejected adoption | — | — |
| 398 | Value: 398. MQL5 compiler diagnostic for an interface unable to contain members. Rejected because numeric compiler diagnostics are not stable application contracts. | Not specified in reference | Constants | Rejected adoption | — | — |
| 399 | Value: 399. MQL5 compiler diagnostic for interface objects unable to be created directly, only use inheritance. Rejected because numeric compiler diagnostics are not stable application contracts. | Not specified in reference | Constants | Rejected adoption | — | — |
| 400 | Value: 400. MQL5 compiler diagnostic for a specifier unable to be used in a forward declaration. Rejected because numeric compiler diagnostics are not stable application contracts. | Not specified in reference | Constants | Rejected adoption | — | — |
| 401 | Value: 401. MQL5 compiler diagnostic for inheritance from the class is impossible, since it is declared with the final specifier. Rejected because numeric compiler diagnostics are not stable application contracts. | Not specified in reference | Constants | Rejected adoption | — | — |
| 402 | Value: 402. MQL5 compiler diagnostic for unable to redefine a method declared with the final specifier. Rejected because numeric compiler diagnostics are not stable application contracts. | Not specified in reference | Constants | Rejected adoption | — | — |
| 403 | Value: 403. MQL5 compiler diagnostic for the final specifier can be applied only to virtual functions. Rejected because numeric compiler diagnostics are not stable application contracts. | Not specified in reference | Constants | Rejected adoption | — | — |
| 404 | Value: 404. MQL5 compiler diagnostic for the method marked by the override specifier actually does not override any base class function. Rejected because numeric compiler diagnostics are not stable application contracts. | Not specified in reference | Constants | Rejected adoption | — | — |
| 405 | Value: 405. MQL5 compiler diagnostic for a specifier is not allowed in defining a function, but only in declaring. Rejected because numeric compiler diagnostics are not stable application contracts. | Not specified in reference | Constants | Rejected adoption | — | — |
| 406 | Value: 406. MQL5 compiler diagnostic for unable to cast the type to the specified one. Rejected because numeric compiler diagnostics are not stable application contracts. | Not specified in reference | Constants | Rejected adoption | — | — |
| 407 | Value: 407. MQL5 compiler diagnostic for the type unable to be used for a resource variable. Rejected because numeric compiler diagnostics are not stable application contracts. | Not specified in reference | Constants | Rejected adoption | — | — |
| 408 | Value: 408. MQL5 compiler diagnostic for error in the project file. Rejected because numeric compiler diagnostics are not stable application contracts. | Not specified in reference | Constants | Rejected adoption | — | — |
| 409 | Value: 409. MQL5 compiler diagnostic for unable to be used as a union member. Rejected because numeric compiler diagnostics are not stable application contracts. | Not specified in reference | Constants | Rejected adoption | — | — |
| 410 | Value: 410. MQL5 compiler diagnostic for ambiguous choice for the name, the usage context should be explicitly defined. Rejected because numeric compiler diagnostics are not stable application contracts. | Not specified in reference | Constants | Rejected adoption | — | — |
| 411 | Value: 411. MQL5 compiler diagnostic for the structure unable to be used from DLL. Rejected because numeric compiler diagnostics are not stable application contracts. | Not specified in reference | Constants | Rejected adoption | — | — |
| 412 | Value: 412. MQL5 compiler diagnostic for unable to call a function marked by the delete specifier. Rejected because numeric compiler diagnostics are not stable application contracts. | Not specified in reference | Constants | Rejected adoption | — | — |
| 413 | Value: 413. MQL5 compiler diagnostic for mQL4 is not supported. To compile this program, use MetaEditor from your MetaTrader 4 installation folder. Rejected because numeric compiler diagnostics are not stable application contracts. | Not specified in reference | Constants | Rejected adoption | — | — |
| ERR_SUCCESS | Value: 0. Reports a success failure. HaruQuantAI adds typed context and structured recovery metadata. | Not specified in reference | Constants | Semantic extension | ERR_SUCCESS | common |
| ERR_INTERNAL_ERROR | Value: 4001. Reports the runtime condition: internal error failure. HaruQuantAI adds typed context and structured recovery metadata. | Not specified in reference | Constants | Semantic extension | ERR_INTERNAL_ERROR | common |
| ERR_WRONG_INTERNAL_PARAMETER | Value: 4002. Reports a wrong internal parameter failure. HaruQuantAI adds typed context and structured recovery metadata. | Not specified in reference | Constants | Semantic extension | ERR_WRONG_INTERNAL_PARAMETER | common |
| ERR_INVALID_PARAMETER | Value: 4003. Reports the runtime condition: invalid parameter failure. HaruQuantAI adds typed context and structured recovery metadata. | Not specified in reference | Constants | Semantic extension | ERR_INVALID_PARAMETER | common |
| ERR_NOT_ENOUGH_MEMORY | Value: 4004. Reports a not enough memory failure. HaruQuantAI adds typed context and structured recovery metadata. | Not specified in reference | Constants | Semantic extension | ERR_NOT_ENOUGH_MEMORY | common |
| ERR_STRUCT_WITHOBJECTS_ORCLASS | Value: 4005. Reports a struct withobjects orclass failure. HaruQuantAI adds typed context and structured recovery metadata. | Not specified in reference | Constants | Semantic extension | ERR_STRUCT_WITHOBJECTS_ORCLASS | common |
| ERR_INVALID_ARRAY | Value: 4006. Reports the runtime condition: invalid array failure. HaruQuantAI adds typed context and structured recovery metadata. | Not specified in reference | Constants | Semantic extension | ERR_INVALID_ARRAY | common |
| ERR_ARRAY_RESIZE_ERROR | Value: 4007. Reports the runtime condition: array resize error failure. HaruQuantAI adds typed context and structured recovery metadata. | Not specified in reference | Constants | Semantic extension | ERR_ARRAY_RESIZE_ERROR | common |
| ERR_STRING_RESIZE_ERROR | Value: 4008. Reports a string resize error failure. HaruQuantAI adds typed context and structured recovery metadata. | Not specified in reference | Constants | Semantic extension | ERR_STRING_RESIZE_ERROR | common |
| ERR_NOTINITIALIZED_STRING | Value: 4009. Reports a notinitialized string failure. HaruQuantAI adds typed context and structured recovery metadata. | Not specified in reference | Constants | Semantic extension | ERR_NOTINITIALIZED_STRING | common |
| ERR_INVALID_DATETIME | Value: 4010. Reports the runtime condition: invalid datetime failure. HaruQuantAI adds typed context and structured recovery metadata. | Not specified in reference | Constants | Semantic extension | ERR_INVALID_DATETIME | common |
| ERR_ARRAY_BAD_SIZE | Value: 4011. Reports the runtime condition: array bad size failure. HaruQuantAI adds typed context and structured recovery metadata. | Not specified in reference | Constants | Semantic extension | ERR_ARRAY_BAD_SIZE | common |
| ERR_INVALID_POINTER | Value: 4012. Reports the runtime condition: invalid pointer failure. HaruQuantAI adds typed context and structured recovery metadata. | Not specified in reference | Constants | Semantic extension | ERR_INVALID_POINTER | common |
| ERR_INVALID_POINTER_TYPE | Value: 4013. Reports the runtime condition: invalid pointer type failure. HaruQuantAI adds typed context and structured recovery metadata. | Not specified in reference | Constants | Semantic extension | ERR_INVALID_POINTER_TYPE | common |
| ERR_FUNCTION_NOT_ALLOWED | Value: 4014. Reports a function not allowed failure. HaruQuantAI adds typed context and structured recovery metadata. | Not specified in reference | Constants | Semantic extension | ERR_FUNCTION_NOT_ALLOWED | common |
| ERR_RESOURCE_NAME_DUPLICATED | Value: 4015. Reports a resource name duplicated failure. HaruQuantAI adds typed context and structured recovery metadata. | Not specified in reference | Constants | Semantic extension | ERR_RESOURCE_NAME_DUPLICATED | common |
| ERR_RESOURCE_NOT_FOUND | Value: 4016. Reports a resource not found failure. HaruQuantAI adds typed context and structured recovery metadata. | Not specified in reference | Constants | Semantic extension | ERR_RESOURCE_NOT_FOUND | common |
| ERR_RESOURCE_UNSUPPORTED_TYPE | Value: 4017. Reports a resource unsupported type failure. HaruQuantAI adds typed context and structured recovery metadata. | Not specified in reference | Constants | Semantic extension | ERR_RESOURCE_UNSUPPORTED_TYPE | common |
| ERR_RESOURCE_NAME_IS_TOO_LONG | Value: 4018. Reports a resource name is too long failure. HaruQuantAI adds typed context and structured recovery metadata. | Not specified in reference | Constants | Semantic extension | ERR_RESOURCE_NAME_IS_TOO_LONG | common |
| ERR_MATH_OVERFLOW | Value: 4019. Reports a math overflow failure. HaruQuantAI adds typed context and structured recovery metadata. | Not specified in reference | Constants | Semantic extension | ERR_MATH_OVERFLOW | common |
| ERR_SLEEP_ERROR | Value: 4020. Reports a sleep error failure. HaruQuantAI adds typed context and structured recovery metadata. | Not specified in reference | Constants | Semantic extension | ERR_SLEEP_ERROR | common |
| ERR_PROGRAM_STOPPED | Value: 4022. Reports a program stopped failure. HaruQuantAI adds typed context and structured recovery metadata. | Not specified in reference | Constants | Semantic extension | ERR_PROGRAM_STOPPED | common |
| ERR_INVALID_TYPE | Value: 4023. Reports the runtime condition: invalid type failure. HaruQuantAI adds typed context and structured recovery metadata. | Not specified in reference | Constants | Semantic extension | ERR_INVALID_TYPE | common |
| ERR_INVALID_HANDLE | Value: 4024. Reports the runtime condition: invalid handle failure. HaruQuantAI adds typed context and structured recovery metadata. | Not specified in reference | Constants | Semantic extension | ERR_INVALID_HANDLE | common |
| ERR_TOO_MANY_OBJECTS | Value: 4025. Reports a too many objects failure. HaruQuantAI adds typed context and structured recovery metadata. | Not specified in reference | Constants | Semantic extension | ERR_TOO_MANY_OBJECTS | common |
| ERR_CHART_WRONG_ID | Value: 4101. Reports a chart wrong ID failure. HaruQuantAI adds cross-platform, asynchronous UI semantics. | Not specified in reference | Constants | Semantic extension | ERR_CHART_WRONG_ID | ui |
| ERR_CHART_NO_REPLY | Value: 4102. Reports a chart no reply failure. HaruQuantAI adds cross-platform, asynchronous UI semantics. | Not specified in reference | Constants | Semantic extension | ERR_CHART_NO_REPLY | ui |
| ERR_CHART_NOT_FOUND | Value: 4103. Reports a chart not found failure. HaruQuantAI adds cross-platform, asynchronous UI semantics. | Not specified in reference | Constants | Semantic extension | ERR_CHART_NOT_FOUND | ui |
| ERR_CHART_NO_EXPERT | Value: 4104. Reports a chart no expert failure. HaruQuantAI adds cross-platform, asynchronous UI semantics. | Not specified in reference | Constants | Semantic extension | ERR_CHART_NO_EXPERT | ui |
| ERR_CHART_CANNOT_OPEN | Value: 4105. Reports a chart cannot open failure. HaruQuantAI adds cross-platform, asynchronous UI semantics. | Not specified in reference | Constants | Semantic extension | ERR_CHART_CANNOT_OPEN | ui |
| ERR_CHART_CANNOT_CHANGE | Value: 4106. Reports a chart cannot change failure. HaruQuantAI adds cross-platform, asynchronous UI semantics. | Not specified in reference | Constants | Semantic extension | ERR_CHART_CANNOT_CHANGE | ui |
| ERR_CHART_WRONG_PARAMETER | Value: 4107. Reports a chart wrong parameter failure. HaruQuantAI adds cross-platform, asynchronous UI semantics. | Not specified in reference | Constants | Semantic extension | ERR_CHART_WRONG_PARAMETER | ui |
| ERR_CHART_CANNOT_CREATE_TIMER | Value: 4108. Reports a chart cannot create timer failure. HaruQuantAI adds cross-platform, asynchronous UI semantics. | Not specified in reference | Constants | Semantic extension | ERR_CHART_CANNOT_CREATE_TIMER | ui |
| ERR_CHART_WRONG_PROPERTY | Value: 4109. Reports a chart wrong property failure. HaruQuantAI adds cross-platform, asynchronous UI semantics. | Not specified in reference | Constants | Semantic extension | ERR_CHART_WRONG_PROPERTY | ui |
| ERR_CHART_SCREENSHOT_FAILED | Value: 4110. Reports a chart screenshot failed failure. HaruQuantAI adds cross-platform, asynchronous UI semantics. | Not specified in reference | Constants | Semantic extension | ERR_CHART_SCREENSHOT_FAILED | ui |
| ERR_CHART_NAVIGATE_FAILED | Value: 4111. Reports a chart navigate failed failure. HaruQuantAI adds cross-platform, asynchronous UI semantics. | Not specified in reference | Constants | Semantic extension | ERR_CHART_NAVIGATE_FAILED | ui |
| ERR_CHART_TEMPLATE_FAILED | Value: 4112. Reports a chart template failed failure. HaruQuantAI adds cross-platform, asynchronous UI semantics. | Not specified in reference | Constants | Semantic extension | ERR_CHART_TEMPLATE_FAILED | ui |
| ERR_CHART_WINDOW_NOT_FOUND | Value: 4113. Reports a chart window not found failure. HaruQuantAI adds cross-platform, asynchronous UI semantics. | Not specified in reference | Constants | Semantic extension | ERR_CHART_WINDOW_NOT_FOUND | ui |
| ERR_CHART_INDICATOR_CANNOT_ADD | Value: 4114. Reports a chart indicator cannot add failure. HaruQuantAI adds cross-platform, asynchronous UI semantics. | Not specified in reference | Constants | Semantic extension | ERR_CHART_INDICATOR_CANNOT_ADD | ui |
| ERR_CHART_INDICATOR_CANNOT_DEL | Value: 4115. Reports a chart indicator cannot del failure. HaruQuantAI adds cross-platform, asynchronous UI semantics. | Not specified in reference | Constants | Semantic extension | ERR_CHART_INDICATOR_CANNOT_DEL | ui |
| ERR_CHART_INDICATOR_NOT_FOUND | Value: 4116. Reports a chart indicator not found failure. HaruQuantAI adds cross-platform, asynchronous UI semantics. | Not specified in reference | Constants | Semantic extension | ERR_CHART_INDICATOR_NOT_FOUND | ui |
| ERR_OBJECT_ERROR | Value: 4201. Reports the runtime condition: object error failure. HaruQuantAI adds typed context and structured recovery metadata. | Not specified in reference | Constants | Semantic extension | ERR_OBJECT_ERROR | common |
| ERR_OBJECT_NOT_FOUND | Value: 4202. Reports the runtime condition: object not found failure. HaruQuantAI adds typed context and structured recovery metadata. | Not specified in reference | Constants | Semantic extension | ERR_OBJECT_NOT_FOUND | common |
| ERR_OBJECT_WRONG_PROPERTY | Value: 4203. Reports the runtime condition: object wrong property failure. HaruQuantAI adds typed context and structured recovery metadata. | Not specified in reference | Constants | Semantic extension | ERR_OBJECT_WRONG_PROPERTY | common |
| ERR_OBJECT_GETDATE_FAILED | Value: 4204. Reports the runtime condition: object getdate failed failure. HaruQuantAI adds typed context and structured recovery metadata. | Not specified in reference | Constants | Semantic extension | ERR_OBJECT_GETDATE_FAILED | common |
| ERR_OBJECT_GETVALUE_FAILED | Value: 4205. Reports the runtime condition: object getvalue failed failure. HaruQuantAI adds typed context and structured recovery metadata. | Not specified in reference | Constants | Semantic extension | ERR_OBJECT_GETVALUE_FAILED | common |
| ERR_MARKET_UNKNOWN_SYMBOL | Value: 4301. Reports a market unknown symbol failure. HaruQuantAI adds provider-neutral provenance and specification validation. | Not specified in reference | Constants | Semantic extension | ERR_MARKET_UNKNOWN_SYMBOL | catalogue |
| ERR_MARKET_NOT_SELECTED | Value: 4302. Reports a market not selected failure. HaruQuantAI adds provider-neutral provenance and specification validation. | Not specified in reference | Constants | Semantic extension | ERR_MARKET_NOT_SELECTED | catalogue |
| ERR_MARKET_WRONG_PROPERTY | Value: 4303. Reports a market wrong property failure. HaruQuantAI adds provider-neutral provenance and specification validation. | Not specified in reference | Constants | Semantic extension | ERR_MARKET_WRONG_PROPERTY | catalogue |
| ERR_MARKET_LASTTIME_UNKNOWN | Value: 4304. Reports a market lasttime unknown failure. HaruQuantAI adds provider-neutral provenance and specification validation. | Not specified in reference | Constants | Semantic extension | ERR_MARKET_LASTTIME_UNKNOWN | catalogue |
| ERR_MARKET_SELECT_ERROR | Value: 4305. Reports a market select error failure. HaruQuantAI adds provider-neutral provenance and specification validation. | Not specified in reference | Constants | Semantic extension | ERR_MARKET_SELECT_ERROR | catalogue |
| ERR_MARKET_SELECT_LIMIT | Value: 4306. Reports a market select limit failure. HaruQuantAI adds provider-neutral provenance and specification validation. | Not specified in reference | Constants | Semantic extension | ERR_MARKET_SELECT_LIMIT | catalogue |
| ERR_MARKET_SESSION_INDEX | Value: 4307. Reports a market session index failure. HaruQuantAI adds provider-neutral provenance and specification validation. | Not specified in reference | Constants | Semantic extension | ERR_MARKET_SESSION_INDEX | catalogue |
| ERR_HISTORY_NOT_FOUND | Value: 4401. Reports a history not found failure. HaruQuantAI adds source lineage, freshness, and recovery metadata. | Not specified in reference | Constants | Semantic extension | ERR_HISTORY_NOT_FOUND | data |
| ERR_HISTORY_WRONG_PROPERTY | Value: 4402. Reports a history wrong property failure. HaruQuantAI adds source lineage, freshness, and recovery metadata. | Not specified in reference | Constants | Semantic extension | ERR_HISTORY_WRONG_PROPERTY | data |
| ERR_HISTORY_TIMEOUT | Value: 4403. Reports a history timeout failure. HaruQuantAI adds source lineage, freshness, and recovery metadata. | Not specified in reference | Constants | Semantic extension | ERR_HISTORY_TIMEOUT | data |
| ERR_HISTORY_BARS_LIMIT | Value: 4404. Reports a history bars limit failure. HaruQuantAI adds source lineage, freshness, and recovery metadata. | Not specified in reference | Constants | Semantic extension | ERR_HISTORY_BARS_LIMIT | data |
| ERR_HISTORY_LOAD_ERRORS | Value: 4405. Reports a history load errors failure. HaruQuantAI adds source lineage, freshness, and recovery metadata. | Not specified in reference | Constants | Semantic extension | ERR_HISTORY_LOAD_ERRORS | data |
| ERR_HISTORY_SMALL_BUFFER | Value: 4407. Reports a history small buffer failure. HaruQuantAI adds source lineage, freshness, and recovery metadata. | Not specified in reference | Constants | Semantic extension | ERR_HISTORY_SMALL_BUFFER | data |
| ERR_GLOBALVARIABLE_NOT_FOUND | Value: 4501. Reports a globalvariable not found failure. HaruQuantAI adds typed context and structured recovery metadata. | Not specified in reference | Constants | Semantic extension | ERR_GLOBALVARIABLE_NOT_FOUND | common |
| ERR_GLOBALVARIABLE_EXISTS | Value: 4502. Reports a globalvariable exists failure. HaruQuantAI adds typed context and structured recovery metadata. | Not specified in reference | Constants | Semantic extension | ERR_GLOBALVARIABLE_EXISTS | common |
| ERR_GLOBALVARIABLE_NOT_MODIFIED | Value: 4503. Reports a globalvariable not modified failure. HaruQuantAI adds typed context and structured recovery metadata. | Not specified in reference | Constants | Semantic extension | ERR_GLOBALVARIABLE_NOT_MODIFIED | common |
| ERR_GLOBALVARIABLE_CANNOTREAD | Value: 4504. Reports a globalvariable cannotread failure. HaruQuantAI adds typed context and structured recovery metadata. | Not specified in reference | Constants | Semantic extension | ERR_GLOBALVARIABLE_CANNOTREAD | common |
| ERR_GLOBALVARIABLE_CANNOTWRITE | Value: 4505. Reports a globalvariable cannotwrite failure. HaruQuantAI adds typed context and structured recovery metadata. | Not specified in reference | Constants | Semantic extension | ERR_GLOBALVARIABLE_CANNOTWRITE | common |
| ERR_MAIL_SEND_FAILED | Value: 4510. Reports a mail send failed failure. HaruQuantAI adds channel-neutral delivery and failure evidence. | Not specified in reference | Constants | Semantic extension | ERR_MAIL_SEND_FAILED | notification |
| ERR_PLAY_SOUND_FAILED | Value: 4511. Reports a play sound failed failure. HaruQuantAI adds typed context and structured recovery metadata. | Not specified in reference | Constants | Semantic extension | ERR_PLAY_SOUND_FAILED | common |
| ERR_MQL5_WRONG_PROPERTY | Value: 4512. Reports a MQL5 wrong property failure. Rejected because it is platform-specific and has no HaruQuantAI public-contract role. | Not specified in reference | Constants | Rejected adoption | — | — |
| ERR_TERMINAL_WRONG_PROPERTY | Value: 4513. Reports a terminal wrong property failure. HaruQuantAI adds typed context and structured recovery metadata. | Not specified in reference | Constants | Semantic extension | ERR_TERMINAL_WRONG_PROPERTY | common |
| ERR_FTP_SEND_FAILED | Value: 4514. Reports a FTP send failed failure. HaruQuantAI adds managed I/O and explicit security policy. | Not specified in reference | Constants | Semantic extension | ERR_FTP_SEND_FAILED | interfaces |
| ERR_NOTIFICATION_SEND_FAILED | Value: 4515. Reports a notification send failed failure. HaruQuantAI adds channel-neutral delivery and failure evidence. | Not specified in reference | Constants | Semantic extension | ERR_NOTIFICATION_SEND_FAILED | notification |
| ERR_NOTIFICATION_WRONG_PARAMETER | Value: 4516. Reports a notification wrong parameter failure. HaruQuantAI adds channel-neutral delivery and failure evidence. | Not specified in reference | Constants | Semantic extension | ERR_NOTIFICATION_WRONG_PARAMETER | notification |
| ERR_NOTIFICATION_WRONG_SETTINGS | Value: 4517. Reports a notification wrong settings failure. HaruQuantAI adds channel-neutral delivery and failure evidence. | Not specified in reference | Constants | Semantic extension | ERR_NOTIFICATION_WRONG_SETTINGS | notification |
| ERR_NOTIFICATION_TOO_FREQUENT | Value: 4518. Reports a notification too frequent failure. HaruQuantAI adds channel-neutral delivery and failure evidence. | Not specified in reference | Constants | Semantic extension | ERR_NOTIFICATION_TOO_FREQUENT | notification |
| ERR_FTP_NOSERVER | Value: 4519. Reports a FTP noserver failure. HaruQuantAI adds managed I/O and explicit security policy. | Not specified in reference | Constants | Semantic extension | ERR_FTP_NOSERVER | interfaces |
| ERR_FTP_NOLOGIN | Value: 4520. Reports a FTP nologin failure. HaruQuantAI adds managed I/O and explicit security policy. | Not specified in reference | Constants | Semantic extension | ERR_FTP_NOLOGIN | interfaces |
| ERR_FTP_FILE_ERROR | Value: 4521. Reports a FTP file error failure. HaruQuantAI adds managed I/O and explicit security policy. | Not specified in reference | Constants | Semantic extension | ERR_FTP_FILE_ERROR | interfaces |
| ERR_FTP_CONNECT_FAILED | Value: 4522. Reports a FTP connect failed failure. HaruQuantAI adds managed I/O and explicit security policy. | Not specified in reference | Constants | Semantic extension | ERR_FTP_CONNECT_FAILED | interfaces |
| ERR_FTP_CHANGEDIR | Value: 4523. Reports a FTP changedir failure. HaruQuantAI adds managed I/O and explicit security policy. | Not specified in reference | Constants | Semantic extension | ERR_FTP_CHANGEDIR | interfaces |
| ERR_BUFFERS_NO_MEMORY | Value: 4601. Reports a buffers no memory failure. HaruQuantAI adds calculation provenance and input validation. | Not specified in reference | Constants | Semantic extension | ERR_BUFFERS_NO_MEMORY | indicator |
| ERR_BUFFERS_WRONG_INDEX | Value: 4602. Reports a buffers wrong index failure. HaruQuantAI adds calculation provenance and input validation. | Not specified in reference | Constants | Semantic extension | ERR_BUFFERS_WRONG_INDEX | indicator |
| ERR_CUSTOM_WRONG_PROPERTY | Value: 4603. Reports a custom wrong property failure. HaruQuantAI adds typed context and structured recovery metadata. | Not specified in reference | Constants | Semantic extension | ERR_CUSTOM_WRONG_PROPERTY | common |
| ERR_ACCOUNT_WRONG_PROPERTY | Value: 4701. Reports the runtime condition: account wrong property failure. HaruQuantAI adds provider identity, retryability, and audit evidence. | Not specified in reference | Constants | Semantic extension | ERR_ACCOUNT_WRONG_PROPERTY | broker |
| ERR_TRADE_WRONG_PROPERTY | Value: 4751. Reports a trade wrong property failure. HaruQuantAI adds provider identity, retryability, and audit evidence. | Not specified in reference | Constants | Semantic extension | ERR_TRADE_WRONG_PROPERTY | broker |
| ERR_TRADE_DISABLED | Value: 4752. Reports a trade disabled failure. HaruQuantAI adds provider identity, retryability, and audit evidence. | Not specified in reference | Constants | Semantic extension | ERR_TRADE_DISABLED | broker |
| ERR_TRADE_POSITION_NOT_FOUND | Value: 4753. Reports a trade position not found failure. HaruQuantAI adds provider identity, retryability, and audit evidence. | Not specified in reference | Constants | Semantic extension | ERR_TRADE_POSITION_NOT_FOUND | broker |
| ERR_TRADE_ORDER_NOT_FOUND | Value: 4754. Reports a trade order not found failure. HaruQuantAI adds provider identity, retryability, and audit evidence. | Not specified in reference | Constants | Semantic extension | ERR_TRADE_ORDER_NOT_FOUND | broker |
| ERR_TRADE_DEAL_NOT_FOUND | Value: 4755. Reports a trade deal not found failure. HaruQuantAI adds provider identity, retryability, and audit evidence. | Not specified in reference | Constants | Semantic extension | ERR_TRADE_DEAL_NOT_FOUND | broker |
| ERR_TRADE_SEND_FAILED | Value: 4756. Reports a trade send failed failure. HaruQuantAI adds provider identity, retryability, and audit evidence. | Not specified in reference | Constants | Semantic extension | ERR_TRADE_SEND_FAILED | broker |
| ERR_TRADE_CALC_FAILED | Value: 4758. Reports a trade calc failed failure. HaruQuantAI adds provider identity, retryability, and audit evidence. | Not specified in reference | Constants | Semantic extension | ERR_TRADE_CALC_FAILED | broker |
| ERR_INDICATOR_UNKNOWN_SYMBOL | Value: 4801. Reports the runtime condition: indicator unknown symbol failure. HaruQuantAI adds calculation provenance and input validation. | Not specified in reference | Constants | Semantic extension | ERR_INDICATOR_UNKNOWN_SYMBOL | indicator |
| ERR_INDICATOR_CANNOT_CREATE | Value: 4802. Reports the runtime condition: indicator cannot create failure. HaruQuantAI adds calculation provenance and input validation. | Not specified in reference | Constants | Semantic extension | ERR_INDICATOR_CANNOT_CREATE | indicator |
| ERR_INDICATOR_NO_MEMORY | Value: 4803. Reports the runtime condition: indicator no memory failure. HaruQuantAI adds calculation provenance and input validation. | Not specified in reference | Constants | Semantic extension | ERR_INDICATOR_NO_MEMORY | indicator |
| ERR_INDICATOR_CANNOT_APPLY | Value: 4804. Reports the runtime condition: indicator cannot apply failure. HaruQuantAI adds calculation provenance and input validation. | Not specified in reference | Constants | Semantic extension | ERR_INDICATOR_CANNOT_APPLY | indicator |
| ERR_INDICATOR_CANNOT_ADD | Value: 4805. Reports the runtime condition: indicator cannot add failure. HaruQuantAI adds calculation provenance and input validation. | Not specified in reference | Constants | Semantic extension | ERR_INDICATOR_CANNOT_ADD | indicator |
| ERR_INDICATOR_DATA_NOT_FOUND | Value: 4806. Reports the runtime condition: indicator data not found failure. HaruQuantAI adds calculation provenance and input validation. | Not specified in reference | Constants | Semantic extension | ERR_INDICATOR_DATA_NOT_FOUND | indicator |
| ERR_INDICATOR_WRONG_HANDLE | Value: 4807. Reports the runtime condition: indicator wrong handle failure. HaruQuantAI adds calculation provenance and input validation. | Not specified in reference | Constants | Semantic extension | ERR_INDICATOR_WRONG_HANDLE | indicator |
| ERR_INDICATOR_WRONG_PARAMETERS | Value: 4808. Reports the runtime condition: indicator wrong parameters failure. HaruQuantAI adds calculation provenance and input validation. | Not specified in reference | Constants | Semantic extension | ERR_INDICATOR_WRONG_PARAMETERS | indicator |
| ERR_INDICATOR_PARAMETERS_MISSING | Value: 4809. Reports the runtime condition: indicator parameters missing failure. HaruQuantAI adds calculation provenance and input validation. | Not specified in reference | Constants | Semantic extension | ERR_INDICATOR_PARAMETERS_MISSING | indicator |
| ERR_INDICATOR_CUSTOM_NAME | Value: 4810. Reports the runtime condition: indicator custom name failure. HaruQuantAI adds calculation provenance and input validation. | Not specified in reference | Constants | Semantic extension | ERR_INDICATOR_CUSTOM_NAME | indicator |
| ERR_INDICATOR_PARAMETER_TYPE | Value: 4811. Reports the runtime condition: indicator parameter type failure. HaruQuantAI adds calculation provenance and input validation. | Not specified in reference | Constants | Semantic extension | ERR_INDICATOR_PARAMETER_TYPE | indicator |
| ERR_INDICATOR_WRONG_INDEX | Value: 4812. Reports the runtime condition: indicator wrong index failure. HaruQuantAI adds calculation provenance and input validation. | Not specified in reference | Constants | Semantic extension | ERR_INDICATOR_WRONG_INDEX | indicator |
| ERR_BOOKS_CANNOT_ADD | Value: 4901. Reports a books cannot add failure. HaruQuantAI adds provider identity, retryability, and audit evidence. | Not specified in reference | Constants | Semantic extension | ERR_BOOKS_CANNOT_ADD | broker |
| ERR_BOOKS_CANNOT_DELETE | Value: 4902. Reports a books cannot delete failure. HaruQuantAI adds provider identity, retryability, and audit evidence. | Not specified in reference | Constants | Semantic extension | ERR_BOOKS_CANNOT_DELETE | broker |
| ERR_BOOKS_CANNOT_GET | Value: 4903. Reports a books cannot get failure. HaruQuantAI adds provider identity, retryability, and audit evidence. | Not specified in reference | Constants | Semantic extension | ERR_BOOKS_CANNOT_GET | broker |
| ERR_BOOKS_CANNOT_SUBSCRIBE | Value: 4904. Reports a books cannot subscribe failure. HaruQuantAI adds provider identity, retryability, and audit evidence. | Not specified in reference | Constants | Semantic extension | ERR_BOOKS_CANNOT_SUBSCRIBE | broker |
| ERR_TOO_MANY_FILES | Value: 5001. Reports a too many files failure. HaruQuantAI adds managed I/O and explicit security policy. | Not specified in reference | Constants | Semantic extension | ERR_TOO_MANY_FILES | interfaces |
| ERR_WRONG_FILENAME | Value: 5002. Reports a wrong filename failure. HaruQuantAI adds managed I/O and explicit security policy. | Not specified in reference | Constants | Semantic extension | ERR_WRONG_FILENAME | interfaces |
| ERR_TOO_LONG_FILENAME | Value: 5003. Reports a too long filename failure. HaruQuantAI adds managed I/O and explicit security policy. | Not specified in reference | Constants | Semantic extension | ERR_TOO_LONG_FILENAME | interfaces |
| ERR_CANNOT_OPEN_FILE | Value: 5004. Reports a cannot open file failure. HaruQuantAI adds managed I/O and explicit security policy. | Not specified in reference | Constants | Semantic extension | ERR_CANNOT_OPEN_FILE | interfaces |
| ERR_FILE_CACHEBUFFER_ERROR | Value: 5005. Reports a file cachebuffer error failure. HaruQuantAI adds managed I/O and explicit security policy. | Not specified in reference | Constants | Semantic extension | ERR_FILE_CACHEBUFFER_ERROR | interfaces |
| ERR_CANNOT_DELETE_FILE | Value: 5006. Reports a cannot delete file failure. HaruQuantAI adds managed I/O and explicit security policy. | Not specified in reference | Constants | Semantic extension | ERR_CANNOT_DELETE_FILE | interfaces |
| ERR_INVALID_FILEHANDLE | Value: 5007. Reports the runtime condition: invalid filehandle failure. HaruQuantAI adds managed I/O and explicit security policy. | Not specified in reference | Constants | Semantic extension | ERR_INVALID_FILEHANDLE | interfaces |
| ERR_WRONG_FILEHANDLE | Value: 5008. Reports a wrong filehandle failure. HaruQuantAI adds managed I/O and explicit security policy. | Not specified in reference | Constants | Semantic extension | ERR_WRONG_FILEHANDLE | interfaces |
| ERR_FILE_NOTTOWRITE | Value: 5009. Reports a file nottowrite failure. HaruQuantAI adds managed I/O and explicit security policy. | Not specified in reference | Constants | Semantic extension | ERR_FILE_NOTTOWRITE | interfaces |
| ERR_FILE_NOTTOREAD | Value: 5010. Reports a file nottoread failure. HaruQuantAI adds managed I/O and explicit security policy. | Not specified in reference | Constants | Semantic extension | ERR_FILE_NOTTOREAD | interfaces |
| ERR_FILE_NOTBIN | Value: 5011. Reports a file notbin failure. HaruQuantAI adds managed I/O and explicit security policy. | Not specified in reference | Constants | Semantic extension | ERR_FILE_NOTBIN | interfaces |
| ERR_FILE_NOTTXT | Value: 5012. Reports a file nottxt failure. HaruQuantAI adds managed I/O and explicit security policy. | Not specified in reference | Constants | Semantic extension | ERR_FILE_NOTTXT | interfaces |
| ERR_FILE_NOTTXTORCSV | Value: 5013. Reports a file nottxtorcsv failure. HaruQuantAI adds managed I/O and explicit security policy. | Not specified in reference | Constants | Semantic extension | ERR_FILE_NOTTXTORCSV | interfaces |
| ERR_FILE_NOTCSV | Value: 5014. Reports a file notcsv failure. HaruQuantAI adds managed I/O and explicit security policy. | Not specified in reference | Constants | Semantic extension | ERR_FILE_NOTCSV | interfaces |
| ERR_FILE_READERROR | Value: 5015. Reports a file readerror failure. HaruQuantAI adds managed I/O and explicit security policy. | Not specified in reference | Constants | Semantic extension | ERR_FILE_READERROR | interfaces |
| ERR_FILE_BINSTRINGSIZE | Value: 5016. Reports a file binstringsize failure. HaruQuantAI adds managed I/O and explicit security policy. | Not specified in reference | Constants | Semantic extension | ERR_FILE_BINSTRINGSIZE | interfaces |
| ERR_INCOMPATIBLE_FILE | Value: 5017. Reports the runtime condition: incompatible file failure. HaruQuantAI adds managed I/O and explicit security policy. | Not specified in reference | Constants | Semantic extension | ERR_INCOMPATIBLE_FILE | interfaces |
| ERR_FILE_IS_DIRECTORY | Value: 5018. Reports a file is directory failure. HaruQuantAI adds managed I/O and explicit security policy. | Not specified in reference | Constants | Semantic extension | ERR_FILE_IS_DIRECTORY | interfaces |
| ERR_FILE_NOT_EXIST | Value: 5019. Reports a file not exist failure. HaruQuantAI adds managed I/O and explicit security policy. | Not specified in reference | Constants | Semantic extension | ERR_FILE_NOT_EXIST | interfaces |
| ERR_FILE_CANNOT_REWRITE | Value: 5020. Reports a file cannot rewrite failure. HaruQuantAI adds managed I/O and explicit security policy. | Not specified in reference | Constants | Semantic extension | ERR_FILE_CANNOT_REWRITE | interfaces |
| ERR_WRONG_DIRECTORYNAME | Value: 5021. Reports a wrong directoryname failure. HaruQuantAI adds managed I/O and explicit security policy. | Not specified in reference | Constants | Semantic extension | ERR_WRONG_DIRECTORYNAME | interfaces |
| ERR_DIRECTORY_NOT_EXIST | Value: 5022. Reports a directory not exist failure. HaruQuantAI adds managed I/O and explicit security policy. | Not specified in reference | Constants | Semantic extension | ERR_DIRECTORY_NOT_EXIST | interfaces |
| ERR_FILE_ISNOT_DIRECTORY | Value: 5023. Reports a file isnot directory failure. HaruQuantAI adds managed I/O and explicit security policy. | Not specified in reference | Constants | Semantic extension | ERR_FILE_ISNOT_DIRECTORY | interfaces |
| ERR_CANNOT_DELETE_DIRECTORY | Value: 5024. Reports a cannot delete directory failure. HaruQuantAI adds managed I/O and explicit security policy. | Not specified in reference | Constants | Semantic extension | ERR_CANNOT_DELETE_DIRECTORY | interfaces |
| ERR_CANNOT_CLEAN_DIRECTORY | Value: 5025. Reports a cannot clean directory failure. HaruQuantAI adds managed I/O and explicit security policy. | Not specified in reference | Constants | Semantic extension | ERR_CANNOT_CLEAN_DIRECTORY | interfaces |
| ERR_FILE_WRITEERROR | Value: 5026. Reports a file writeerror failure. HaruQuantAI adds managed I/O and explicit security policy. | Not specified in reference | Constants | Semantic extension | ERR_FILE_WRITEERROR | interfaces |
| ERR_FILE_ENDOFFILE | Value: 5027. Reports a file endoffile failure. HaruQuantAI adds managed I/O and explicit security policy. | Not specified in reference | Constants | Semantic extension | ERR_FILE_ENDOFFILE | interfaces |
| ERR_NO_STRING_DATE | Value: 5030. Reports a no string date failure. HaruQuantAI adds typed context and structured recovery metadata. | Not specified in reference | Constants | Semantic extension | ERR_NO_STRING_DATE | common |
| ERR_WRONG_STRING_DATE | Value: 5031. Reports a wrong string date failure. HaruQuantAI adds typed context and structured recovery metadata. | Not specified in reference | Constants | Semantic extension | ERR_WRONG_STRING_DATE | common |
| ERR_WRONG_STRING_TIME | Value: 5032. Reports a wrong string time failure. HaruQuantAI adds typed context and structured recovery metadata. | Not specified in reference | Constants | Semantic extension | ERR_WRONG_STRING_TIME | common |
| ERR_STRING_TIME_ERROR | Value: 5033. Reports a string time error failure. HaruQuantAI adds typed context and structured recovery metadata. | Not specified in reference | Constants | Semantic extension | ERR_STRING_TIME_ERROR | common |
| ERR_STRING_OUT_OF_MEMORY | Value: 5034. Reports a string out of memory failure. HaruQuantAI adds typed context and structured recovery metadata. | Not specified in reference | Constants | Semantic extension | ERR_STRING_OUT_OF_MEMORY | common |
| ERR_STRING_SMALL_LEN | Value: 5035. Reports a string small len failure. HaruQuantAI adds typed context and structured recovery metadata. | Not specified in reference | Constants | Semantic extension | ERR_STRING_SMALL_LEN | common |
| ERR_STRING_TOO_BIGNUMBER | Value: 5036. Reports a string too bignumber failure. HaruQuantAI adds typed context and structured recovery metadata. | Not specified in reference | Constants | Semantic extension | ERR_STRING_TOO_BIGNUMBER | common |
| ERR_WRONG_FORMATSTRING | Value: 5037. Reports a wrong formatstring failure. HaruQuantAI adds typed context and structured recovery metadata. | Not specified in reference | Constants | Semantic extension | ERR_WRONG_FORMATSTRING | common |
| ERR_TOO_MANY_FORMATTERS | Value: 5038. Reports a too many formatters failure. HaruQuantAI adds typed context and structured recovery metadata. | Not specified in reference | Constants | Semantic extension | ERR_TOO_MANY_FORMATTERS | common |
| ERR_TOO_MANY_PARAMETERS | Value: 5039. Reports a too many parameters failure. HaruQuantAI adds typed context and structured recovery metadata. | Not specified in reference | Constants | Semantic extension | ERR_TOO_MANY_PARAMETERS | common |
| ERR_WRONG_STRING_PARAMETER | Value: 5040. Reports a wrong string parameter failure. HaruQuantAI adds typed context and structured recovery metadata. | Not specified in reference | Constants | Semantic extension | ERR_WRONG_STRING_PARAMETER | common |
| ERR_STRINGPOS_OUTOFRANGE | Value: 5041. Reports a stringpos outofrange failure. HaruQuantAI adds typed context and structured recovery metadata. | Not specified in reference | Constants | Semantic extension | ERR_STRINGPOS_OUTOFRANGE | common |
| ERR_STRING_ZEROADDED | Value: 5042. Reports a string zeroadded failure. HaruQuantAI adds typed context and structured recovery metadata. | Not specified in reference | Constants | Semantic extension | ERR_STRING_ZEROADDED | common |
| ERR_STRING_UNKNOWNTYPE | Value: 5043. Reports a string unknowntype failure. HaruQuantAI adds typed context and structured recovery metadata. | Not specified in reference | Constants | Semantic extension | ERR_STRING_UNKNOWNTYPE | common |
| ERR_WRONG_STRING_OBJECT | Value: 5044. Reports a wrong string object failure. HaruQuantAI adds typed context and structured recovery metadata. | Not specified in reference | Constants | Semantic extension | ERR_WRONG_STRING_OBJECT | common |
| ERR_INCOMPATIBLE_ARRAYS | Value: 5050. Reports the runtime condition: incompatible arrays failure. HaruQuantAI adds typed context and structured recovery metadata. | Not specified in reference | Constants | Semantic extension | ERR_INCOMPATIBLE_ARRAYS | common |
| ERR_SMALL_ASSERIES_ARRAY | Value: 5051. Reports a small asseries array failure. HaruQuantAI adds typed context and structured recovery metadata. | Not specified in reference | Constants | Semantic extension | ERR_SMALL_ASSERIES_ARRAY | common |
| ERR_SMALL_ARRAY | Value: 5052. Reports a small array failure. HaruQuantAI adds typed context and structured recovery metadata. | Not specified in reference | Constants | Semantic extension | ERR_SMALL_ARRAY | common |
| ERR_ZEROSIZE_ARRAY | Value: 5053. Reports a zerosize array failure. HaruQuantAI adds typed context and structured recovery metadata. | Not specified in reference | Constants | Semantic extension | ERR_ZEROSIZE_ARRAY | common |
| ERR_NUMBER_ARRAYS_ONLY | Value: 5054. Reports a number arrays only failure. HaruQuantAI adds typed context and structured recovery metadata. | Not specified in reference | Constants | Semantic extension | ERR_NUMBER_ARRAYS_ONLY | common |
| ERR_ONEDIM_ARRAYS_ONLY | Value: 5055. Reports the runtime condition: onedim arrays only failure. HaruQuantAI adds typed context and structured recovery metadata. | Not specified in reference | Constants | Semantic extension | ERR_ONEDIM_ARRAYS_ONLY | common |
| ERR_SERIES_ARRAY | Value: 5056. Reports a series array failure. HaruQuantAI adds typed context and structured recovery metadata. | Not specified in reference | Constants | Semantic extension | ERR_SERIES_ARRAY | common |
| ERR_DOUBLE_ARRAY_ONLY | Value: 5057. Reports a double array only failure. HaruQuantAI adds typed context and structured recovery metadata. | Not specified in reference | Constants | Semantic extension | ERR_DOUBLE_ARRAY_ONLY | common |
| ERR_FLOAT_ARRAY_ONLY | Value: 5058. Reports a float array only failure. HaruQuantAI adds typed context and structured recovery metadata. | Not specified in reference | Constants | Semantic extension | ERR_FLOAT_ARRAY_ONLY | common |
| ERR_LONG_ARRAY_ONLY | Value: 5059. Reports a long array only failure. HaruQuantAI adds typed context and structured recovery metadata. | Not specified in reference | Constants | Semantic extension | ERR_LONG_ARRAY_ONLY | common |
| ERR_INT_ARRAY_ONLY | Value: 5060. Reports the runtime condition: int array only failure. HaruQuantAI adds typed context and structured recovery metadata. | Not specified in reference | Constants | Semantic extension | ERR_INT_ARRAY_ONLY | common |
| ERR_SHORT_ARRAY_ONLY | Value: 5061. Reports a short array only failure. HaruQuantAI adds typed context and structured recovery metadata. | Not specified in reference | Constants | Semantic extension | ERR_SHORT_ARRAY_ONLY | common |
| ERR_CHAR_ARRAY_ONLY | Value: 5062. Reports a char array only failure. HaruQuantAI adds typed context and structured recovery metadata. | Not specified in reference | Constants | Semantic extension | ERR_CHAR_ARRAY_ONLY | common |
| ERR_STRING_ARRAY_ONLY | Value: 5063. Reports a string array only failure. HaruQuantAI adds typed context and structured recovery metadata. | Not specified in reference | Constants | Semantic extension | ERR_STRING_ARRAY_ONLY | common |
| ERR_OPENCL_NOT_SUPPORTED | Value: 5100. Reports the runtime condition: opencl not supported failure. HaruQuantAI adds typed context and structured recovery metadata. | Not specified in reference | Constants | Semantic extension | ERR_OPENCL_NOT_SUPPORTED | common |
| ERR_OPENCL_INTERNAL | Value: 5101. Reports the runtime condition: opencl internal failure. HaruQuantAI adds typed context and structured recovery metadata. | Not specified in reference | Constants | Semantic extension | ERR_OPENCL_INTERNAL | common |
| ERR_OPENCL_INVALID_HANDLE | Value: 5102. Reports the runtime condition: opencl invalid handle failure. HaruQuantAI adds typed context and structured recovery metadata. | Not specified in reference | Constants | Semantic extension | ERR_OPENCL_INVALID_HANDLE | common |
| ERR_OPENCL_CONTEXT_CREATE | Value: 5103. Reports the runtime condition: opencl context create failure. HaruQuantAI adds typed context and structured recovery metadata. | Not specified in reference | Constants | Semantic extension | ERR_OPENCL_CONTEXT_CREATE | common |
| ERR_OPENCL_QUEUE_CREATE | Value: 5104. Reports the runtime condition: opencl queue create failure. HaruQuantAI adds typed context and structured recovery metadata. | Not specified in reference | Constants | Semantic extension | ERR_OPENCL_QUEUE_CREATE | common |
| ERR_OPENCL_PROGRAM_CREATE | Value: 5105. Reports the runtime condition: opencl program create failure. HaruQuantAI adds typed context and structured recovery metadata. | Not specified in reference | Constants | Semantic extension | ERR_OPENCL_PROGRAM_CREATE | common |
| ERR_OPENCL_TOO_LONG_KERNEL_NAME | Value: 5106. Reports the runtime condition: opencl too long kernel name failure. HaruQuantAI adds typed context and structured recovery metadata. | Not specified in reference | Constants | Semantic extension | ERR_OPENCL_TOO_LONG_KERNEL_NAME | common |
| ERR_OPENCL_KERNEL_CREATE | Value: 5107. Reports the runtime condition: opencl kernel create failure. HaruQuantAI adds typed context and structured recovery metadata. | Not specified in reference | Constants | Semantic extension | ERR_OPENCL_KERNEL_CREATE | common |
| ERR_OPENCL_SET_KERNEL_PARAMETER | Value: 5108. Reports the runtime condition: opencl set kernel parameter failure. HaruQuantAI adds typed context and structured recovery metadata. | Not specified in reference | Constants | Semantic extension | ERR_OPENCL_SET_KERNEL_PARAMETER | common |
| ERR_OPENCL_EXECUTE | Value: 5109. Reports the runtime condition: opencl execute failure. HaruQuantAI adds typed context and structured recovery metadata. | Not specified in reference | Constants | Semantic extension | ERR_OPENCL_EXECUTE | common |
| ERR_OPENCL_WRONG_BUFFER_SIZE | Value: 5110. Reports the runtime condition: opencl wrong buffer size failure. HaruQuantAI adds typed context and structured recovery metadata. | Not specified in reference | Constants | Semantic extension | ERR_OPENCL_WRONG_BUFFER_SIZE | common |
| ERR_OPENCL_WRONG_BUFFER_OFFSET | Value: 5111. Reports the runtime condition: opencl wrong buffer offset failure. HaruQuantAI adds typed context and structured recovery metadata. | Not specified in reference | Constants | Semantic extension | ERR_OPENCL_WRONG_BUFFER_OFFSET | common |
| ERR_OPENCL_BUFFER_CREATE | Value: 5112. Reports the runtime condition: opencl buffer create failure. HaruQuantAI adds typed context and structured recovery metadata. | Not specified in reference | Constants | Semantic extension | ERR_OPENCL_BUFFER_CREATE | common |
| ERR_OPENCL_TOO_MANY_OBJECTS | Value: 5113. Reports the runtime condition: opencl too many objects failure. HaruQuantAI adds typed context and structured recovery metadata. | Not specified in reference | Constants | Semantic extension | ERR_OPENCL_TOO_MANY_OBJECTS | common |
| ERR_OPENCL_SELECTDEVICE | Value: 5114. Reports the runtime condition: opencl selectdevice failure. HaruQuantAI adds typed context and structured recovery metadata. | Not specified in reference | Constants | Semantic extension | ERR_OPENCL_SELECTDEVICE | common |
| ERR_DATABASE_INTERNAL | Value: 5120. Reports a database internal failure. HaruQuantAI adds source lineage, freshness, and recovery metadata. | Not specified in reference | Constants | Semantic extension | ERR_DATABASE_INTERNAL | data |
| ERR_DATABASE_INVALID_HANDLE | Value: 5121. Reports a database invalid handle failure. HaruQuantAI adds source lineage, freshness, and recovery metadata. | Not specified in reference | Constants | Semantic extension | ERR_DATABASE_INVALID_HANDLE | data |
| ERR_DATABASE_TOO_MANY_OBJECTS | Value: 5122. Reports a database too many objects failure. HaruQuantAI adds source lineage, freshness, and recovery metadata. | Not specified in reference | Constants | Semantic extension | ERR_DATABASE_TOO_MANY_OBJECTS | data |
| ERR_DATABASE_CONNECT | Value: 5123. Reports a database connect failure. HaruQuantAI adds source lineage, freshness, and recovery metadata. | Not specified in reference | Constants | Semantic extension | ERR_DATABASE_CONNECT | data |
| ERR_DATABASE_EXECUTE | Value: 5124. Reports a database execute failure. HaruQuantAI adds source lineage, freshness, and recovery metadata. | Not specified in reference | Constants | Semantic extension | ERR_DATABASE_EXECUTE | data |
| ERR_DATABASE_PREPARE | Value: 5125. Reports a database prepare failure. HaruQuantAI adds source lineage, freshness, and recovery metadata. | Not specified in reference | Constants | Semantic extension | ERR_DATABASE_PREPARE | data |
| ERR_DATABASE_NO_MORE_DATA | Value: 5126. Reports a database no more data failure. HaruQuantAI adds source lineage, freshness, and recovery metadata. | Not specified in reference | Constants | Semantic extension | ERR_DATABASE_NO_MORE_DATA | data |
| ERR_DATABASE_STEP | Value: 5127. Reports a database step failure. HaruQuantAI adds source lineage, freshness, and recovery metadata. | Not specified in reference | Constants | Semantic extension | ERR_DATABASE_STEP | data |
| ERR_DATABASE_NOT_READY | Value: 5128. Reports a database not ready failure. HaruQuantAI adds source lineage, freshness, and recovery metadata. | Not specified in reference | Constants | Semantic extension | ERR_DATABASE_NOT_READY | data |
| ERR_DATABASE_BIND_PARAMETERS | Value: 5129. Reports a database bind parameters failure. HaruQuantAI adds source lineage, freshness, and recovery metadata. | Not specified in reference | Constants | Semantic extension | ERR_DATABASE_BIND_PARAMETERS | data |
| ERR_WEBREQUEST_INVALID_ADDRESS | Value: 5200. Reports a webrequest invalid address failure. HaruQuantAI adds managed I/O and explicit security policy. | Not specified in reference | Constants | Semantic extension | ERR_WEBREQUEST_INVALID_ADDRESS | interfaces |
| ERR_WEBREQUEST_CONNECT_FAILED | Value: 5201. Reports a webrequest connect failed failure. HaruQuantAI adds managed I/O and explicit security policy. | Not specified in reference | Constants | Semantic extension | ERR_WEBREQUEST_CONNECT_FAILED | interfaces |
| ERR_WEBREQUEST_TIMEOUT | Value: 5202. Reports a webrequest timeout failure. HaruQuantAI adds managed I/O and explicit security policy. | Not specified in reference | Constants | Semantic extension | ERR_WEBREQUEST_TIMEOUT | interfaces |
| ERR_WEBREQUEST_REQUEST_FAILED | Value: 5203. Reports a webrequest request failed failure. HaruQuantAI adds managed I/O and explicit security policy. | Not specified in reference | Constants | Semantic extension | ERR_WEBREQUEST_REQUEST_FAILED | interfaces |
| ERR_NETSOCKET_INVALIDHANDLE | Value: 5270. Reports a netsocket invalidhandle failure. HaruQuantAI adds managed I/O and explicit security policy. | Not specified in reference | Constants | Semantic extension | ERR_NETSOCKET_INVALIDHANDLE | interfaces |
| ERR_NETSOCKET_TOO_MANY_OPENED | Value: 5271. Reports a netsocket too many opened failure. HaruQuantAI adds managed I/O and explicit security policy. | Not specified in reference | Constants | Semantic extension | ERR_NETSOCKET_TOO_MANY_OPENED | interfaces |
| ERR_NETSOCKET_CANNOT_CONNECT | Value: 5272. Reports a netsocket cannot connect failure. HaruQuantAI adds managed I/O and explicit security policy. | Not specified in reference | Constants | Semantic extension | ERR_NETSOCKET_CANNOT_CONNECT | interfaces |
| ERR_NETSOCKET_IO_ERROR | Value: 5273. Reports a netsocket io error failure. HaruQuantAI adds managed I/O and explicit security policy. | Not specified in reference | Constants | Semantic extension | ERR_NETSOCKET_IO_ERROR | interfaces |
| ERR_NETSOCKET_HANDSHAKE_FAILED | Value: 5274. Reports a netsocket handshake failed failure. HaruQuantAI adds managed I/O and explicit security policy. | Not specified in reference | Constants | Semantic extension | ERR_NETSOCKET_HANDSHAKE_FAILED | interfaces |
| ERR_NETSOCKET_NO_CERTIFICATE | Value: 5275. Reports a netsocket no certificate failure. HaruQuantAI adds managed I/O and explicit security policy. | Not specified in reference | Constants | Semantic extension | ERR_NETSOCKET_NO_CERTIFICATE | interfaces |
| ERR_NOT_CUSTOM_SYMBOL | Value: 5300. Reports a not custom symbol failure. HaruQuantAI adds typed context and structured recovery metadata. | Not specified in reference | Constants | Semantic extension | ERR_NOT_CUSTOM_SYMBOL | common |
| ERR_CUSTOM_SYMBOL_WRONG_NAME | Value: 5301. Reports a custom symbol wrong name failure. HaruQuantAI adds provider-neutral provenance and specification validation. | Not specified in reference | Constants | Semantic extension | ERR_CUSTOM_SYMBOL_WRONG_NAME | catalogue |
| ERR_CUSTOM_SYMBOL_NAME_LONG | Value: 5302. Reports a custom symbol name long failure. HaruQuantAI adds provider-neutral provenance and specification validation. | Not specified in reference | Constants | Semantic extension | ERR_CUSTOM_SYMBOL_NAME_LONG | catalogue |
| ERR_CUSTOM_SYMBOL_PATH_LONG | Value: 5303. Reports a custom symbol path long failure. HaruQuantAI adds provider-neutral provenance and specification validation. | Not specified in reference | Constants | Semantic extension | ERR_CUSTOM_SYMBOL_PATH_LONG | catalogue |
| ERR_CUSTOM_SYMBOL_EXIST | Value: 5304. Reports a custom symbol exist failure. HaruQuantAI adds provider-neutral provenance and specification validation. | Not specified in reference | Constants | Semantic extension | ERR_CUSTOM_SYMBOL_EXIST | catalogue |
| ERR_CUSTOM_SYMBOL_ERROR | Value: 5305. Reports a custom symbol error failure. HaruQuantAI adds provider-neutral provenance and specification validation. | Not specified in reference | Constants | Semantic extension | ERR_CUSTOM_SYMBOL_ERROR | catalogue |
| ERR_CUSTOM_SYMBOL_SELECTED | Value: 5306. Reports a custom symbol selected failure. HaruQuantAI adds provider-neutral provenance and specification validation. | Not specified in reference | Constants | Semantic extension | ERR_CUSTOM_SYMBOL_SELECTED | catalogue |
| ERR_CUSTOM_SYMBOL_PROPERTY_WRONG | Value: 5307. Reports a custom symbol property wrong failure. HaruQuantAI adds provider-neutral provenance and specification validation. | Not specified in reference | Constants | Semantic extension | ERR_CUSTOM_SYMBOL_PROPERTY_WRONG | catalogue |
| ERR_CUSTOM_SYMBOL_PARAMETER_ERROR | Value: 5308. Reports a custom symbol parameter error failure. HaruQuantAI adds provider-neutral provenance and specification validation. | Not specified in reference | Constants | Semantic extension | ERR_CUSTOM_SYMBOL_PARAMETER_ERROR | catalogue |
| ERR_CUSTOM_SYMBOL_PARAMETER_LONG | Value: 5309. Reports a custom symbol parameter long failure. HaruQuantAI adds provider-neutral provenance and specification validation. | Not specified in reference | Constants | Semantic extension | ERR_CUSTOM_SYMBOL_PARAMETER_LONG | catalogue |
| ERR_CUSTOM_TICKS_WRONG_ORDER | Value: 5310. Reports a custom ticks wrong order failure. HaruQuantAI adds typed context and structured recovery metadata. | Not specified in reference | Constants | Semantic extension | ERR_CUSTOM_TICKS_WRONG_ORDER | common |
| ERR_CALENDAR_MORE_DATA | Value: 5400. Reports a calendar more data failure. HaruQuantAI adds source lineage, freshness, and recovery metadata. | Not specified in reference | Constants | Semantic extension | ERR_CALENDAR_MORE_DATA | data |
| ERR_CALENDAR_TIMEOUT | Value: 5401. Reports a calendar timeout failure. HaruQuantAI adds source lineage, freshness, and recovery metadata. | Not specified in reference | Constants | Semantic extension | ERR_CALENDAR_TIMEOUT | data |
| ERR_CALENDAR_NO_DATA | Value: 5402. Reports a calendar no data failure. HaruQuantAI adds source lineage, freshness, and recovery metadata. | Not specified in reference | Constants | Semantic extension | ERR_CALENDAR_NO_DATA | data |
| ERR_DATABASE_ERROR | Value: 5601. Reports a database error failure. HaruQuantAI adds source lineage, freshness, and recovery metadata. | Not specified in reference | Constants | Semantic extension | ERR_DATABASE_ERROR | data |
| ERR_DATABASE_LOGIC | Value: 5602. Reports a database logic failure. HaruQuantAI adds source lineage, freshness, and recovery metadata. | Not specified in reference | Constants | Semantic extension | ERR_DATABASE_LOGIC | data |
| ERR_DATABASE_PERM | Value: 5603. Reports a database perm failure. HaruQuantAI adds source lineage, freshness, and recovery metadata. | Not specified in reference | Constants | Semantic extension | ERR_DATABASE_PERM | data |
| ERR_DATABASE_ABORT | Value: 5604. Reports a database abort failure. HaruQuantAI adds source lineage, freshness, and recovery metadata. | Not specified in reference | Constants | Semantic extension | ERR_DATABASE_ABORT | data |
| ERR_DATABASE_BUSY | Value: 5605. Reports a database busy failure. HaruQuantAI adds source lineage, freshness, and recovery metadata. | Not specified in reference | Constants | Semantic extension | ERR_DATABASE_BUSY | data |
| ERR_DATABASE_LOCKED | Value: 5606. Reports a database locked failure. HaruQuantAI adds source lineage, freshness, and recovery metadata. | Not specified in reference | Constants | Semantic extension | ERR_DATABASE_LOCKED | data |
| ERR_DATABASE_NOMEM | Value: 5607. Reports a database nomem failure. HaruQuantAI adds source lineage, freshness, and recovery metadata. | Not specified in reference | Constants | Semantic extension | ERR_DATABASE_NOMEM | data |
| ERR_DATABASE_READONLY | Value: 5608. Reports a database readonly failure. HaruQuantAI adds source lineage, freshness, and recovery metadata. | Not specified in reference | Constants | Semantic extension | ERR_DATABASE_READONLY | data |
| ERR_DATABASE_INTERRUPT | Value: 5609. Reports a database interrupt failure. HaruQuantAI adds source lineage, freshness, and recovery metadata. | Not specified in reference | Constants | Semantic extension | ERR_DATABASE_INTERRUPT | data |
| ERR_DATABASE_IOERR | Value: 5610. Reports a database ioerr failure. HaruQuantAI adds source lineage, freshness, and recovery metadata. | Not specified in reference | Constants | Semantic extension | ERR_DATABASE_IOERR | data |
| ERR_DATABASE_CORRUPT | Value: 5611. Reports a database corrupt failure. HaruQuantAI adds source lineage, freshness, and recovery metadata. | Not specified in reference | Constants | Semantic extension | ERR_DATABASE_CORRUPT | data |
| ERR_DATABASE_NOTFOUND | Value: 5612. Reports a database notfound failure. HaruQuantAI adds source lineage, freshness, and recovery metadata. | Not specified in reference | Constants | Semantic extension | ERR_DATABASE_NOTFOUND | data |
| ERR_DATABASE_FULL | Value: 5613. Reports a database full failure. HaruQuantAI adds source lineage, freshness, and recovery metadata. | Not specified in reference | Constants | Semantic extension | ERR_DATABASE_FULL | data |
| ERR_DATABASE_CANTOPEN | Value: 5614. Reports a database cantopen failure. HaruQuantAI adds source lineage, freshness, and recovery metadata. | Not specified in reference | Constants | Semantic extension | ERR_DATABASE_CANTOPEN | data |
| ERR_DATABASE_PROTOCOL | Value: 5615. Reports a database protocol failure. HaruQuantAI adds source lineage, freshness, and recovery metadata. | Not specified in reference | Constants | Semantic extension | ERR_DATABASE_PROTOCOL | data |
| ERR_DATABASE_EMPTY | Value: 5616. Reports a database empty failure. HaruQuantAI adds source lineage, freshness, and recovery metadata. | Not specified in reference | Constants | Semantic extension | ERR_DATABASE_EMPTY | data |
| ERR_DATABASE_SCHEMA | Value: 5617. Reports a database schema failure. HaruQuantAI adds source lineage, freshness, and recovery metadata. | Not specified in reference | Constants | Semantic extension | ERR_DATABASE_SCHEMA | data |
| ERR_DATABASE_TOOBIG | Value: 5618. Reports a database toobig failure. HaruQuantAI adds source lineage, freshness, and recovery metadata. | Not specified in reference | Constants | Semantic extension | ERR_DATABASE_TOOBIG | data |
| ERR_DATABASE_CONSTRAINT | Value: 5619. Reports a database constraint failure. HaruQuantAI adds source lineage, freshness, and recovery metadata. | Not specified in reference | Constants | Semantic extension | ERR_DATABASE_CONSTRAINT | data |
| ERR_DATABASE_MISMATCH | Value: 5620. Reports a database mismatch failure. HaruQuantAI adds source lineage, freshness, and recovery metadata. | Not specified in reference | Constants | Semantic extension | ERR_DATABASE_MISMATCH | data |
| ERR_DATABASE_MISUSE | Value: 5621. Reports a database misuse failure. HaruQuantAI adds source lineage, freshness, and recovery metadata. | Not specified in reference | Constants | Semantic extension | ERR_DATABASE_MISUSE | data |
| ERR_DATABASE_NOLFS | Value: 5622. Reports a database nolfs failure. HaruQuantAI adds source lineage, freshness, and recovery metadata. | Not specified in reference | Constants | Semantic extension | ERR_DATABASE_NOLFS | data |
| ERR_DATABASE_AUTH | Value: 5623. Reports a database auth failure. HaruQuantAI adds source lineage, freshness, and recovery metadata. | Not specified in reference | Constants | Semantic extension | ERR_DATABASE_AUTH | data |
| ERR_DATABASE_FORMAT | Value: 5624. Reports a database format failure. HaruQuantAI adds source lineage, freshness, and recovery metadata. | Not specified in reference | Constants | Semantic extension | ERR_DATABASE_FORMAT | data |
| ERR_DATABASE_RANGE | Value: 5625. Reports a database range failure. HaruQuantAI adds source lineage, freshness, and recovery metadata. | Not specified in reference | Constants | Semantic extension | ERR_DATABASE_RANGE | data |
| ERR_DATABASE_NOTADB | Value: 5626. Reports a database notadb failure. HaruQuantAI adds source lineage, freshness, and recovery metadata. | Not specified in reference | Constants | Semantic extension | ERR_DATABASE_NOTADB | data |
| ERR_MATRIX_INTERNAL | Value: 5700. Reports a matrix internal failure. HaruQuantAI adds model provenance and reproducibility metadata. | Not specified in reference | Constants | Semantic extension | ERR_MATRIX_INTERNAL | research |
| ERR_MATRIX_NOT_INITIALIZED | Value: 5701. Reports a matrix not initialized failure. HaruQuantAI adds model provenance and reproducibility metadata. | Not specified in reference | Constants | Semantic extension | ERR_MATRIX_NOT_INITIALIZED | research |
| ERR_MATRIX_INCONSISTENT | Value: 5702. Reports a matrix inconsistent failure. HaruQuantAI adds model provenance and reproducibility metadata. | Not specified in reference | Constants | Semantic extension | ERR_MATRIX_INCONSISTENT | research |
| ERR_MATRIX_INVALID_SIZE | Value: 5703. Reports a matrix invalid size failure. HaruQuantAI adds model provenance and reproducibility metadata. | Not specified in reference | Constants | Semantic extension | ERR_MATRIX_INVALID_SIZE | research |
| ERR_MATRIX_INVALID_TYPE | Value: 5704. Reports a matrix invalid type failure. HaruQuantAI adds model provenance and reproducibility metadata. | Not specified in reference | Constants | Semantic extension | ERR_MATRIX_INVALID_TYPE | research |
| ERR_MATRIX_FUNC_NOT_ALLOWED | Value: 5705. Reports a matrix func not allowed failure. HaruQuantAI adds model provenance and reproducibility metadata. | Not specified in reference | Constants | Semantic extension | ERR_MATRIX_FUNC_NOT_ALLOWED | research |
| ERR_MATRIX_CONTAINS_NAN | Value: 5706. Reports a matrix contains nan failure. HaruQuantAI adds model provenance and reproducibility metadata. | Not specified in reference | Constants | Semantic extension | ERR_MATRIX_CONTAINS_NAN | research |
| ERR_ONNX_INTERNAL | Value: 5800. Reports a ONNX internal failure. HaruQuantAI adds model provenance and reproducibility metadata. | Not specified in reference | Constants | Semantic extension | ERR_ONNX_INTERNAL | research |
| ERR_ONNX_NOT_INITIALIZED | Value: 5801. Reports a ONNX not initialized failure. HaruQuantAI adds model provenance and reproducibility metadata. | Not specified in reference | Constants | Semantic extension | ERR_ONNX_NOT_INITIALIZED | research |
| ERR_ONNX_NOT_SUPPORTED | Value: 5802. Reports a ONNX not supported failure. HaruQuantAI adds model provenance and reproducibility metadata. | Not specified in reference | Constants | Semantic extension | ERR_ONNX_NOT_SUPPORTED | research |
| ERR_ONNX_RUN_FAILED | Value: 5803. Reports a ONNX run failed failure. HaruQuantAI adds model provenance and reproducibility metadata. | Not specified in reference | Constants | Semantic extension | ERR_ONNX_RUN_FAILED | research |
| ERR_ONNX_INVALID_PARAMETERS_COUNT | Value: 5804. Reports a ONNX invalid parameters count failure. HaruQuantAI adds model provenance and reproducibility metadata. | Not specified in reference | Constants | Semantic extension | ERR_ONNX_INVALID_PARAMETERS_COUNT | research |
| ERR_ONNX_INVALID_PARAMETER | Value: 5805. Reports a ONNX invalid parameter failure. HaruQuantAI adds model provenance and reproducibility metadata. | Not specified in reference | Constants | Semantic extension | ERR_ONNX_INVALID_PARAMETER | research |
| ERR_ONNX_INVALID_PARAMETER_TYPE | Value: 5806. Reports a ONNX invalid parameter type failure. HaruQuantAI adds model provenance and reproducibility metadata. | Not specified in reference | Constants | Semantic extension | ERR_ONNX_INVALID_PARAMETER_TYPE | research |
| ERR_ONNX_INVALID_PARAMETER_SIZE | Value: 5807. Reports a ONNX invalid parameter size failure. HaruQuantAI adds model provenance and reproducibility metadata. | Not specified in reference | Constants | Semantic extension | ERR_ONNX_INVALID_PARAMETER_SIZE | research |
| ERR_ONNX_WRONG_DIMENSION | Value: 5808. Reports a ONNX wrong dimension failure. HaruQuantAI adds model provenance and reproducibility metadata. | Not specified in reference | Constants | Semantic extension | ERR_ONNX_WRONG_DIMENSION | research |
| ERR_USER_ERROR_FIRST | Value: 65536. Reports the runtime condition: user error first failure. HaruQuantAI adds typed context and structured recovery metadata. | Not specified in reference | Constants | Semantic extension | ERR_USER_ERROR_FIRST | common |
| FILE_READ | Value: 1. Represents file read. | Not specified in reference | Constants | Exact adoption | FILE_READ | interfaces |
| FILE_WRITE | Value: 2. Represents file write. | Not specified in reference | Constants | Exact adoption | FILE_WRITE | interfaces |
| FILE_BIN | Value: 4. Represents file bin. | Not specified in reference | Constants | Exact adoption | FILE_BIN | interfaces |
| FILE_CSV | Value: 8. Represents file CSV. | Not specified in reference | Constants | Exact adoption | FILE_CSV | interfaces |
| FILE_TXT | Value: 16. Represents file txt. | Not specified in reference | Constants | Exact adoption | FILE_TXT | interfaces |
| FILE_ANSI | Value: 32. Represents file ANSI. | Not specified in reference | Constants | Exact adoption | FILE_ANSI | interfaces |
| FILE_UNICODE | Value: 64. Represents file unicode. | Not specified in reference | Constants | Exact adoption | FILE_UNICODE | interfaces |
| FILE_SHARE_READ | Value: 128. Represents file share read. | Not specified in reference | Constants | Exact adoption | FILE_SHARE_READ | interfaces |
| FILE_SHARE_WRITE | Value: 256. Represents file share write. | Not specified in reference | Constants | Exact adoption | FILE_SHARE_WRITE | interfaces |
| FILE_REWRITE | Value: 512. Represents file rewrite. | Not specified in reference | Constants | Exact adoption | FILE_REWRITE | interfaces |
| FILE_COMMON | Value: 4096. Represents file common. | Not specified in reference | Constants | Platform-neutral rename | FILE_SHARED | interfaces |
| ENUM_FILE_PROPERTY_INTEGER | Defines the identifier set for file property integer. | enum (int) | Enumerations | Exact adoption | ENUM_FILE_PROPERTY_INTEGER | interfaces |
| FILE_EXISTS | Selects exists in file property integer. | ENUM_FILE_PROPERTY_INTEGER | Enumerations | Exact adoption | FILE_EXISTS | interfaces |
| FILE_CREATE_DATE | Selects create date in file property integer. | ENUM_FILE_PROPERTY_INTEGER | Enumerations | Exact adoption | FILE_CREATE_DATE | interfaces |
| FILE_MODIFY_DATE | Selects modify date in file property integer. | ENUM_FILE_PROPERTY_INTEGER | Enumerations | Exact adoption | FILE_MODIFY_DATE | interfaces |
| FILE_ACCESS_DATE | Selects access date in file property integer. | ENUM_FILE_PROPERTY_INTEGER | Enumerations | Exact adoption | FILE_ACCESS_DATE | interfaces |
| FILE_SIZE | Selects size in file property integer. | ENUM_FILE_PROPERTY_INTEGER | Enumerations | Exact adoption | FILE_SIZE | interfaces |
| FILE_POSITION | Selects position in file property integer. | ENUM_FILE_PROPERTY_INTEGER | Enumerations | Exact adoption | FILE_POSITION | interfaces |
| FILE_END | Selects end in file property integer. | ENUM_FILE_PROPERTY_INTEGER | Enumerations | Exact adoption | FILE_END | interfaces |
| FILE_LINE_END | Selects line end in file property integer. | ENUM_FILE_PROPERTY_INTEGER | Enumerations | Exact adoption | FILE_LINE_END | interfaces |
| FILE_IS_COMMON | Selects is common in file property integer. | ENUM_FILE_PROPERTY_INTEGER | Enumerations | Exact adoption | FILE_IS_COMMON | interfaces |
| FILE_IS_TEXT | Selects is text in file property integer. | ENUM_FILE_PROPERTY_INTEGER | Enumerations | Exact adoption | FILE_IS_TEXT | interfaces |
| FILE_IS_BINARY | Selects is binary in file property integer. | ENUM_FILE_PROPERTY_INTEGER | Enumerations | Exact adoption | FILE_IS_BINARY | interfaces |
| FILE_IS_CSV | Selects is CSV in file property integer. | ENUM_FILE_PROPERTY_INTEGER | Enumerations | Exact adoption | FILE_IS_CSV | interfaces |
| FILE_IS_ANSI | Selects is ANSI in file property integer. | ENUM_FILE_PROPERTY_INTEGER | Enumerations | Exact adoption | FILE_IS_ANSI | interfaces |
| FILE_IS_READABLE | Selects is readable in file property integer. | ENUM_FILE_PROPERTY_INTEGER | Enumerations | Exact adoption | FILE_IS_READABLE | interfaces |
| FILE_IS_WRITABLE | Selects is writable in file property integer. | ENUM_FILE_PROPERTY_INTEGER | Enumerations | Exact adoption | FILE_IS_WRITABLE | interfaces |
| ENUM_FILE_POSITION | Defines the identifier set for file position. | enum (int) | Enumerations | Exact adoption | ENUM_FILE_POSITION | interfaces |
| SEEK_SET | Selects seek set in file position. | ENUM_FILE_POSITION | Enumerations | Exact adoption | SEEK_SET | interfaces |
| SEEK_CUR | Selects seek cur in file position. | ENUM_FILE_POSITION | Enumerations | Exact adoption | SEEK_CUR | interfaces |
| SEEK_END | Selects seek end in file position. | ENUM_FILE_POSITION | Enumerations | Exact adoption | SEEK_END | interfaces |
| CP_ACP | Value: 0. Selects the acp code page. Rejected because it is a legacy operating-system code page. | Not specified in reference | Constants | Rejected adoption | — | — |
| CP_OEMCP | Value: 1. Selects the oemcp code page. Rejected because it is a legacy operating-system code page. | Not specified in reference | Constants | Rejected adoption | — | — |
| CP_MACCP | Value: 2. Selects the maccp code page. Rejected because it is a legacy operating-system code page. | Not specified in reference | Constants | Rejected adoption | — | — |
| CP_THREAD_ACP | Value: 3. Selects the thread acp code page. Rejected because it is a legacy operating-system code page. | Not specified in reference | Constants | Rejected adoption | — | — |
| CP_SYMBOL | Value: 42. Selects the symbol code page. Rejected because it is a legacy operating-system code page. | Not specified in reference | Constants | Rejected adoption | — | — |
| CP_UTF7 | Value: 65000. Selects the UTF7 code page. Rejected because it is a legacy operating-system code page. | Not specified in reference | Constants | Rejected adoption | — | — |
| CP_UTF8 | Value: 65001. Selects the UTF8 code page. | Not specified in reference | Constants | Exact adoption | CP_UTF8 | interfaces |
| IDOK | Value: 1. Identifies the ok message-box result. | Not specified in reference | Constants | Exact adoption | IDOK | ui |
| IDCANCEL | Value: 2. Identifies the cancel message-box result. | Not specified in reference | Constants | Exact adoption | IDCANCEL | ui |
| IDABORT | Value: 3. Identifies the abort message-box result. | Not specified in reference | Constants | Exact adoption | IDABORT | ui |
| IDRETRY | Value: 4. Identifies the retry message-box result. | Not specified in reference | Constants | Exact adoption | IDRETRY | ui |
| IDIGNORE | Value: 5. Identifies the ignore message-box result. | Not specified in reference | Constants | Exact adoption | IDIGNORE | ui |
| IDYES | Value: 6. Identifies the yes message-box result. | Not specified in reference | Constants | Exact adoption | IDYES | ui |
| IDNO | Value: 7. Identifies the no message-box result. | Not specified in reference | Constants | Exact adoption | IDNO | ui |
| IDTRYAGAIN | Value: 10. Identifies the tryagain message-box result. | Not specified in reference | Constants | Exact adoption | IDTRYAGAIN | ui |
| IDCONTINUE | Value: 11. Identifies the continue message-box result. | Not specified in reference | Constants | Exact adoption | IDCONTINUE | ui |
| MB_OK | Value: 0x00000000. Configures the message box with ok. HaruQuantAI adds cross-platform, asynchronous UI semantics. | Not specified in reference | Constants | Semantic extension | MB_OK | ui |
| MB_OKCANCEL | Value: 0x00000001. Configures the message box with okcancel. HaruQuantAI adds cross-platform, asynchronous UI semantics. | Not specified in reference | Constants | Semantic extension | MB_OKCANCEL | ui |
| MB_ABORTRETRYIGNORE | Value: 0x00000002. Configures the message box with abortretryignore. HaruQuantAI adds cross-platform, asynchronous UI semantics. | Not specified in reference | Constants | Semantic extension | MB_ABORTRETRYIGNORE | ui |
| MB_YESNOCANCEL | Value: 0x00000003. Configures the message box with yesnocancel. HaruQuantAI adds cross-platform, asynchronous UI semantics. | Not specified in reference | Constants | Semantic extension | MB_YESNOCANCEL | ui |
| MB_YESNO | Value: 0x00000004. Configures the message box with yesno. HaruQuantAI adds cross-platform, asynchronous UI semantics. | Not specified in reference | Constants | Semantic extension | MB_YESNO | ui |
| MB_RETRYCANCEL | Value: 0x00000005. Configures the message box with retrycancel. HaruQuantAI adds cross-platform, asynchronous UI semantics. | Not specified in reference | Constants | Semantic extension | MB_RETRYCANCEL | ui |
| MB_CANCELTRYCONTINUE | Value: 0x00000006. Configures the message box with canceltrycontinue. HaruQuantAI adds cross-platform, asynchronous UI semantics. | Not specified in reference | Constants | Semantic extension | MB_CANCELTRYCONTINUE | ui |
| MB_ICONSTOP | Value: 0x00000010. Configures the message box with iconstop. HaruQuantAI adds cross-platform, asynchronous UI semantics. | Not specified in reference | Constants | Semantic extension | MB_ICONSTOP | ui |
| MB_ICONERROR | Value: 0x00000010. Configures the message box with iconerror. HaruQuantAI adds cross-platform, asynchronous UI semantics. | Not specified in reference | Constants | Semantic extension | MB_ICONERROR | ui |
| MB_ICONHAND | Value: 0x00000010. Configures the message box with iconhand. HaruQuantAI adds cross-platform, asynchronous UI semantics. | Not specified in reference | Constants | Semantic extension | MB_ICONHAND | ui |
| MB_ICONQUESTION | Value: 0x00000020. Configures the message box with iconquestion. HaruQuantAI adds cross-platform, asynchronous UI semantics. | Not specified in reference | Constants | Semantic extension | MB_ICONQUESTION | ui |
| MB_ICONEXCLAMATION | Value: 0x00000030. Configures the message box with iconexclamation. HaruQuantAI adds cross-platform, asynchronous UI semantics. | Not specified in reference | Constants | Semantic extension | MB_ICONEXCLAMATION | ui |
| MB_ICONWARNING | Value: 0x00000030. Configures the message box with iconwarning. HaruQuantAI adds cross-platform, asynchronous UI semantics. | Not specified in reference | Constants | Semantic extension | MB_ICONWARNING | ui |
| MB_ICONINFORMATION | Value: 0x00000040. Configures the message box with iconinformation. HaruQuantAI adds cross-platform, asynchronous UI semantics. | Not specified in reference | Constants | Semantic extension | MB_ICONINFORMATION | ui |
| MB_ICONASTERISK | Value: 0x00000040. Configures the message box with iconasterisk. HaruQuantAI adds cross-platform, asynchronous UI semantics. | Not specified in reference | Constants | Semantic extension | MB_ICONASTERISK | ui |
| MB_DEFBUTTON1 | Value: 0x00000000. Configures the message box with defbutton1. HaruQuantAI adds cross-platform, asynchronous UI semantics. | Not specified in reference | Constants | Semantic extension | MB_DEFBUTTON1 | ui |
| MB_DEFBUTTON2 | Value: 0x00000100. Configures the message box with defbutton2. HaruQuantAI adds cross-platform, asynchronous UI semantics. | Not specified in reference | Constants | Semantic extension | MB_DEFBUTTON2 | ui |
| MB_DEFBUTTON3 | Value: 0x00000200. Configures the message box with defbutton3. HaruQuantAI adds cross-platform, asynchronous UI semantics. | Not specified in reference | Constants | Semantic extension | MB_DEFBUTTON3 | ui |
| MB_DEFBUTTON4 | Value: 0x00000300. Configures the message box with defbutton4. HaruQuantAI adds cross-platform, asynchronous UI semantics. | Not specified in reference | Constants | Semantic extension | MB_DEFBUTTON4 | ui |

## Reconciliation

The catalogue contains **2,408 unique identifiers**. No duplicate qualified Identifier rows remain.

Category counts: Constants 953; Enumerations 1,331; Structures 124.

Classification counts: Exact adoption 1,201; Platform-neutral rename 219; Semantic extension 563; Rejected adoption 425; HaruQuantAI-native 0.

Domain counts: analytics 43; broker 107; catalogue 369; common 145; data 203; indicator 171; interfaces 81; notification 5; plugins 10; research 16; risk 9; trading 209; ui 530; workspace 85; — 425.

Source-section counts: Chart Constants 135; Objects Constants 299; Indicator Constants 153; Environment State 616; Trade Constants 223; Named Constants 87; Data Structures 184; Codes of Errors and Warnings 645; Input/Output Constants 66.

Type note: **821** rows use `Not specified in reference`; this is intentional where the source names a constant or diagnostic without declaring a data type. Types were not guessed from implementation conventions.

## Decision notes and limitations

- Four extraction-exception classes were reconciled: identifiers broken by PDF line wrapping; four enum declarations split from their tables by page breaks; web-color and filling-policy tables with nonstandard layouts; and structure fields presented as declarations rather than ordinary reference-table rows.
- Structure fields are qualified (for example, `MqlTradeRequest.action`) so every public identifier has a unique row. The proposed contract repeats the HaruQuantAI-neutral structure name.
- Compiler diagnostics whose only identifier is a numeric code are retained for source completeness but rejected as public contracts. Symbolic runtime and provider errors are retained only where HaruQuantAI has a corresponding concern.
- MQL5 Signals marketplace contracts, pointer-management semantics, insecure legacy cryptographic selections, and platform code-page constants are rejected.
- Classification is architectural intent, not a promise to reproduce undocumented numeric layouts or MT5 runtime behavior. Numeric values should be adopted during implementation only where the source states them explicitly and the HaruQuantAI contract specification ratifies them.
- The PDF contains long examples between reference tables. Example-local identifiers, helper structures, functions, and prose mentions are intentionally outside this catalogue.
