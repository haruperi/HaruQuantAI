<#-- Aroon (multi-output) value. SQX Aroon uses an EXACTLY Period-bar window (Aroon.java), while the
     native NT Aroon scans a Period+1-bar window, so it is numerically different. Computed by the
     installed SqAroon indicator: #Line# selects the line (0 = Up, 1 = Down). Mapping in printAroonLine
     (Parameters.inc).
     Output e.g.: SqAroon(Close, 14).Values[0][0] -->
<@printAroonLine block shift />
