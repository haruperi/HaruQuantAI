<#-- Current month equals #Month# (1-12) -> (sqClock(Time[0]).Month == Month) (current bar timestamp). See BarMonthIs. -->
(sqClock(Time[0]).Month == <@printParam block "#Month#" />)
