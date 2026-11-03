<#-- Current minute equals #Minute# -> (sqClock(Time[0]).Minute == Minute) (current bar timestamp). See CurrentHour. -->
(sqClock(Time[0]).Minute == <@printParam block "#Minute#" />)
