<#-- Current date -> (Year-1900)*10000 + Month*100 + Day from sqClock(Time[0]) (current bar). -1900 offset per
     SQX getYmd/getYear. See BarDate/CurrentHour. -->
((sqClock(Time[0]).Year - 1900) * 10000 + sqClock(Time[0]).Month * 100 + sqClock(Time[0]).Day)
