<#-- Commodity Channel Index (Lambert) of the #ComputedFrom# series from the installed SqCCI indicator,
     via printIndValueAt (Parameters.inc), which routes "CCI" to it.
     Output e.g.: SqCCI(Close, 14).Values[0][0] -->
<@printIndValueAt block "CCI" shift />
