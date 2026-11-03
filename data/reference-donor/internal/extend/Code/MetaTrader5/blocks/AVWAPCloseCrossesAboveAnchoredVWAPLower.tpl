<@compress_single_line>
(sqClose(<@printInput block true />, <@printShift block "1" />) < sqGetIndicatorValue(${getIndyShortName(getIndicatorId(block))}, 2, <@printShift block "1" />, true) && sqClose(<@printInput block true />, <@printShift block "0" />) > sqGetIndicatorValue(${getIndyShortName(getIndicatorId(block))}, 2, <@printShift block "0" />, true))
</@compress_single_line>
