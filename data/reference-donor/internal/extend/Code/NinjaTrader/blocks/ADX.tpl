<#-- ADX / Directional Movement (multi-output) from the installed SqADX indicator; #Line# selects the
     ADX line (Values[0]) / +DI (Values[1]) / -DI (Values[2]). Native NT ADX/DM use a different
     Wilder seed and differ from ADX.java past 6 decimals. Mapping in printADXLine (Parameters.inc).
     Output e.g.: SqADX(Close, 14).Values[0][0] -->
<@printADXLine block shift />
