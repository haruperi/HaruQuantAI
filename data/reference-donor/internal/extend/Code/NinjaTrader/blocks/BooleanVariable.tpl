<#-- Boolean variable reference. A boolean strategy variable is declared as a C# bool field
     (printVariableDeclarations maps var.type == "boolean" -> bool), so it is emitted directly as
     the boolean value - no "!= 0" comparison (that would be CS0019 on a bool). Mirrors the MT5
     export, which likewise emits the bare variable name for a BooleanVariable. -->
<@printParam block "#Variable#" />
