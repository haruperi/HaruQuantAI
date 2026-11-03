<#-- Current hour (0-23) -> sqClock(Time[0]).Hour. SQX CurrentHour: SQTime.getHour(getCurrentTime()), where
     getCurrentTime() is the CURRENT BAR timestamp in a backtest (not wall-clock). NinjaScript Time[0]
     is the current bar time, read through sqClock so a bar ending at midnight keeps its own day; DateTime.Now would be non-deterministic and is wrong for backtest parity. -->
sqClock(Time[0]).Hour
