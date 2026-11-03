<#-- Momentum value. SQX Momentum is a RATIO (Input[0]*100/Input[Period]), NOT the native NT
     Momentum (absolute Close - Close[n]); the other platforms use their own Sq* impl.
     Emitted inline via printIndValueAt (Parameters.inc), which special-cases "Momentum".
     Output e.g.: (Close[0] * 100.0 / Close[0 + Math.Min(14, CurrentBar - (0))]) -->
<@printIndValueAt block "Momentum" shift />