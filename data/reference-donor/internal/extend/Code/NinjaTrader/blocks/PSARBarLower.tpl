<#-- Price is below Parabolic SAR. Java: Input.Bid() < SAR.getRounded(Shift) -> Bid is the CURRENT
     price (no shift), SAR uses #Shift#. NT: Close[0] (Bid approx current Close) < SAR[shift], the SAR rounded to 6 decimals as getRounded. -->
(<@printSeries block "Close" />[0] < sqRound(<@printPSARValueAt block shift />, 6))