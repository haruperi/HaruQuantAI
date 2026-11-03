<#-- Round to N decimals -> sqRound (half-up, mirrors SQUtils.round exactly - Round.java:46).
     NOT C# Math.Round: that is banker's rounding (to even) and differs from SQX at an exact .5
     boundary. -->
sqRound(<@printBlockChild block "#Value#" shift />, <@printParam block "#Decimals#" />)
