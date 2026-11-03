

double sqMMRiskFixedAccountPct(string symbol, int orderType, double price, double sl, double RiskInPercent, int decimals, int StopLossPips, double LotsIfNoMM, double MaximumLots, double multiplier, double sizeStep) {
   Verbose("Computing Money Management for order -  Risk fixed % of account");

   if(UseMoneyManagement == false) {
      Verbose("Use Money Management = false, MM not used");
      return (mmLotsIfNoMM);
   }
      
   symbol = correctSymbol(symbol);
   
   double openPrice = price > 0 ? price : (orderType == OP_BUY ? sqGetAsk(symbol) : sqGetBid(symbol));
   double LotSize = 0;

   if(RiskInPercent < 0 ) {
      Verbose("Computing Money Management - Incorrect RiskInPercent size, it must be above 0");
      return(0);
   }
   
   double PointValue = MarketInfo(symbol, MODE_TICKVALUE) / MarketInfo(symbol, MODE_TICKSIZE);   
   double Smallest_Lot = MarketInfo(symbol, MODE_MINLOT);
   double Largest_Lot = MarketInfo(symbol, MODE_MAXLOT);    
   double LotStep = MarketInfo(symbol, MODE_LOTSTEP);
   
   if(sl == 0){
      sl = openPrice - StopLossPips * sqGetPointCoef(symbol);
   }
   
   sl = NormalizeDouble(sl, (int) MarketInfo(symbol, MODE_DIGITS));
   
   //Maximum amount of money to risk 
   double moneyToRisk = NormalizeDouble(AccountEquity() * RiskInPercent / 100, 7);
		
   //Maximum drawdown of this order if we buy 1 lot 
   double oneLotSLDrawdown = NormalizeDouble(PointValue * MathAbs(openPrice - sl), 7);

   // CalcMode-aware conversion: no conversion for Forex, manual calculation for CFD/Futures
   sqApplyCalcModeAwareConversion(symbol, PointValue, oneLotSLDrawdown, openPrice, sl);

   if(oneLotSLDrawdown > 0) {
	  LotSize = moneyToRisk / oneLotSLDrawdown;
   }
   else {
	  LotSize = 0;
   }

    //Order size multiplier
    LotSize = LotSize * multiplier;
	
    // round computed trade size 
	LotSize = roundDown(LotSize, sizeStep, decimals);

   //--- MAXLOT and MINLOT management

   Verbose("MODE_TICKSIZE: ", DoubleToStr(MarketInfo(symbol, MODE_TICKSIZE)), ", MODE_TICKVALUE: ", DoubleToStr(MarketInfo(symbol, MODE_TICKVALUE)), ", MODE_POINT: ", DoubleToStr(MarketInfo(symbol, MODE_POINT)));
   Verbose("Computing Money Management - Smallest_Lot: ", DoubleToStr(Smallest_Lot), ", Largest_Lot: ", DoubleToStr(Largest_Lot),", Computed LotSize: ", DoubleToStr(LotSize));
   Verbose("Max money to risk: ", DoubleToStr(moneyToRisk), ", SL:", DoubleToStr(sl), ", One lot drawdown: ", DoubleToStr(oneLotSLDrawdown), ", Point value: ", DoubleToStr(PointValue));

   if(LotSize <= 0) {
      Verbose("Calculated LotSize is <= 0. Using LotsIfNoMM value: ", DoubleToStr(LotsIfNoMM), ")");
			LotSize = LotsIfNoMM;
	 }
   
   if(LotSize > MaximumLots) {
      Verbose("LotSize is too big. LotSize set to maximal allowed value (MaximumLots): ", DoubleToStr(MaximumLots));
      LotSize = MaximumLots;
   }

   //--------------------------------------------

   if (LotSize < Smallest_Lot) {
      Verbose("Calculated LotSize is too small. Minimal allowed lot size from the broker is: ", DoubleToStr(Smallest_Lot), ". Please, increase your risk or set fixed LotSize.");
      LotSize = 0;
   }
   else if (LotSize > Largest_Lot) {
      Verbose("LotSize is too big. LotSize set to maximal allowed market value: ", DoubleToStr(Largest_Lot));
      LotSize = Largest_Lot;
   }

   return (LotSize);
}
