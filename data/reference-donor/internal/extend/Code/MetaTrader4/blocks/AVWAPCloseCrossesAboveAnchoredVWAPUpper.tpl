<@compress_single_line>
(sqGetValue(<@printInput block true />, PRICE_CLOSE, <@printShift block "1" />) < iCustom(<@printInput block />, "SqAnchoredVWAP", <@printParam block "#SessionType#" />, <@printParam block "#StdDevMult#" />,1,<@printShift block "1" />)) &&
(sqGetValue(<@printInput block true />, PRICE_CLOSE, <@printShift block "0" />) > iCustom(<@printInput block />, "SqAnchoredVWAP", <@printParam block "#SessionType#" />, <@printParam block "#StdDevMult#" />,1,<@printShift block "0" />))
</@compress_single_line>
