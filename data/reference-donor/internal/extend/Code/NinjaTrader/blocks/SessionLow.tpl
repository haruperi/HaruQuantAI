<#-- Session Low -> lowest Low of the [Start, End] session, from the installed SqSessionOHLC indicator
     (Values[2]). #Shift# counts sessions back; the caller's bar offset is not applied, as
     SessionLow.java ignores it. Mirrors SessionLow.java.
     Output e.g.: SqSessionOHLC(Close, 9, 30, 16, 0, 0, SqSourceEndOfBar).Values[2][0] -->
<#global sqUsesIndicatorPackage = true>SqSessionOHLC(<@printInput block />, <@printParam block "#StartHours#" />, <@printParam block "#StartMinutes#" />, <@printParam block "#EndHours#" />, <@printParam block "#EndMinutes#" />, <@printParam block "#Shift#" "0" />, SqSourceEndOfBar).Values[2][0]
