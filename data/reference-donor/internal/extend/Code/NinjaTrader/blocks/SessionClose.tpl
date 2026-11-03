<#-- Session Close -> close of the session ending at EndHours:EndMinutes, from the installed SqSessionOHLC indicator
     (Values[3]). #Shift# counts sessions back; the caller's bar offset is not applied, as
     SessionClose.java ignores it. Mirrors SessionClose.java.
     Output e.g.: SqSessionOHLC(Close, 9, 30, 16, 0, 0, SqSourceEndOfBar).Values[3][0] -->
<#global sqUsesIndicatorPackage = true>SqSessionOHLC(<@printInput block />, <@printParam block "#EndHours#" />, <@printParam block "#EndMinutes#" />, <@printParam block "#EndHours#" />, <@printParam block "#EndMinutes#" />, <@printParam block "#Shift#" "0" />, SqSourceEndOfBar).Values[3][0]
