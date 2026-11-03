
	// Money Management - ATR risk-based sizing
	@Configurable(value = "--------- Money Management ---------", readOnly = true)
	public String mmType = "ATR risk-based sizing";
	@Configurable("Use Money Management")
	public boolean UseMoneyManagement = true;
	@Configurable(value = "Risk in %", stepSize = 0.1)
	public double mmRiskPercent = <@printMMVariableNumber "#Risk#" />;
	@Configurable(value = "ATR period", stepSize = 1)
	public int mmAtrPeriod = <@printMMVariableNumber "#ATRPeriod#" />;
	@Configurable(value = "ATR multiplier", stepSize = 0.1)
	public double mmAtrMult = <@printMMVariableNumber "#ATRMult#" />;
	@Configurable(value = "Size Decimals", stepSize = 1)
	public int mmDecimals = <@printMMVariableNumber "#Decimals#" />;
	@Configurable(value = "Size if no MM", stepSize = 0.1)
	public double mmLotsIfNoMM = <@printMMVariableNumber "#LotsIfNoMM#" />;
	@Configurable(value = "Maximum lots", stepSize = 0.1)
	public double mmMaxLots = <@printMMVariableNumber "#MaxLots#" />;