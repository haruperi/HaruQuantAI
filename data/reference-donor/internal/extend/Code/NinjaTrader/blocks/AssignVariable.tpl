<#-- AssignVariable -> assign a formula value to a strategy variable:  <var> = <formula>;
     Target variable (#Variable#) is rendered via printVariableName (sanitized C# identifier);
     the value (#Value#) is a formula rendered by printFormulaParam (delegates to printBlock).
     Strategy variables are declared by their type (int/double) - see printVariableDeclarations.
     An int target needs an explicit (int) cast because the formula RHS is a
     double expression and C# has no implicit double->int narrowing; the cast truncates toward
     zero, matching the MT5 AssignVariable cast (SQX assignment semantics). This is plain C#
     assignment, not a NinjaScript API call, so no Docs link applies. -->
<#list block.* as param><#if param.@key == "#Variable#"><@printVariableName param /></#if></#list> = <#if assignTargetIsInt(block)>(int)(</#if><@printFormulaParam block "#Value#" /><#if assignTargetIsInt(block)>)</#if>;