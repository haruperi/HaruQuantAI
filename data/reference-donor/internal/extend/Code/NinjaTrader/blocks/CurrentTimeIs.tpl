<#-- Current time equals #Hour#:#Minute# -> (sqClock(Time[0]).Hour == Hour && sqClock(Time[0]).Minute == Minute) (current bar). See BarTimeIs. -->
(sqClock(Time[0]).Hour == <@printParam block "#Hour#" /> && sqClock(Time[0]).Minute == <@printParam block "#Minute#" />)
