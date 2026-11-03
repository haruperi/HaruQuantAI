<#-- Division -> (right != 0 ? left / right : double.MaxValue). SQX sqSafeDivide returns Double.MAX_VALUE
     on divide-by-zero (NOT Infinity), so the guard is required for parity. See Division.java.
     The (double) cast on the dividend is REQUIRED for SQX parity: SQX evaluates every block in double
     (Division.java operates on double operands), but with two int-typed operands (int literals with the
     ".0" stripped, or int-typed strategy variables) C# int/int would TRUNCATE (5 / 2 = 2 instead of 2.5)
     - silently, with no compile error. The cast widens the whole division to double for any operand mix. -->
(<@printBlockChild block "#Right#" shift /> != 0 ? (double)(<@printBlockChild block "#Left#" shift />) / <@printBlockChild block "#Right#" shift /> : double.MaxValue)
