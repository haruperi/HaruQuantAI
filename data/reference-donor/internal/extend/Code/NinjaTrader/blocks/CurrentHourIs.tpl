<#-- Current hour equals #Hour# -> (sqClock(Time[0]).Hour == Hour) (current bar timestamp). See CurrentHour. -->
(sqClock(Time[0]).Hour == <@printParam block "#Hour#" />)
