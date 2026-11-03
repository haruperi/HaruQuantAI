
extern string smm = "----------- Money Management - Crypto Fixed Amount -----------";
extern bool UseMoneyManagement = true;
extern double mmRiskedMoney = <@printMMVariableNumber "#RiskedMoney#" />;
extern int mmDecimals = <@printMMVariableNumber "#Decimals#" />;
extern double mmLotsIfNoMM = 1;
extern double mmMultiplier = ${orderSizeMultiplier};
extern double mmStep = ${orderSizeStep};
