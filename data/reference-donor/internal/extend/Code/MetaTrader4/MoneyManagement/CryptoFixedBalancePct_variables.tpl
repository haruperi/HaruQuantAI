
extern string smm = "----------- Money Management - Crypto Fixed % Of Balance -----------";
extern bool UseMoneyManagement = true;
extern double mmRiskPercent = <@printMMVariableNumber "#Risk#" />;
extern int mmDecimals = <@printMMVariableNumber "#Decimals#" />;
extern double mmLotsIfNoMM = 1;
extern double mmMultiplier = ${orderSizeMultiplier};
extern double mmStep = ${orderSizeStep};
