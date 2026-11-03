<#-- OSMA (moving average of oscillator) from the installed SqMACD indicator: the MACD main line minus
     its signal line, both read at the same bar. See printOSMAValueAt (Parameters.inc).
     Output e.g.: (SqMACD(Close, 12, 26, 9).Values[0][0] - SqMACD(Close, 12, 26, 9).Values[1][0]) -->
<@printOSMAValueAt block shift />
