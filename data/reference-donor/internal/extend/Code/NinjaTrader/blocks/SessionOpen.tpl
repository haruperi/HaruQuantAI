<#-- Session Open -> open of the session starting at StartHours:StartMinutes, from the installed SqSessionOHLC indicator
     (Values[0]). #Shift# counts sessions back; the caller's bar offset is not applied, as
     SessionOpen.java ignores it. Mirrors SessionOpen.java.
     Output e.g.: SqSessionOHLC(Close, 9, 30, 16, 0, 0, SqSourceEndOfBar).Values[0][0] -->
<#global sqUsesIndicatorPackage = true>SqSessionOHLC(<@printInput block />, <@printParam block "#StartHours#" />, <@printParam block "#StartMinutes#" />, <@printParam block "#StartHours#" />, <@printParam block "#StartMinutes#" />, <@printParam block "#Shift#" "0" />, SqSourceEndOfBar).Values[0][0]
