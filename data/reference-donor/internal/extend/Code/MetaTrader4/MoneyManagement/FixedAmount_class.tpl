

double sqMMFixedAmount(string symbol, int orderType, double price, double sl, double RiskedMoney, int decimals, double LotsIfNoMM, double MaximumLots, double multiplier, double sizeStep) {
   Verbose("Computing Money Management for order - Fixed amount");
   
   if(UseMoneyManagement == false) {
      Verbose("Use Money Management = false, MM not used");
      return (mmLotsIfNoMM);
   }
   
   symbol = correctSymbol(symbol);
   sl = NormalizeDouble(sl, (int) MarketInfo(symbol, MODE_DIGITS));
   
   double openPrice = price > 0 ? price : (orderType == OP_BUY ? sqGetAsk(symbol) : sqGetBid(symbol));
   double LotSize=0;

   if(RiskedMoney <= 0 ) {
      Verbose("Computing Money Management - Incorrect RiskedMoney value, it must be above 0");
      return(0);
   }
   
   double PointValue = MarketInfo(symbol, MODE_TICKVALUE) / MarketInfo(symbol, MODE_TICKSIZE);   
   double Smallest_Lot = MarketInfo(symbol, MODE_MINLOT);
   double Largest_Lot = MarketInfo(symbol, MODE_MAXLOT);    
   double LotStep = MarketInfo(symbol, MODE_LOTSTEP);
		
   //Maximum drawdown of this order if we buy 1 lot 
   double oneLotSLDrawdown = PointValue * MathAbs(openPrice - sl);

   // CalcMode-aware conversion: no conversion for Forex, manual calculation for CFD/Futures
   sqApplyCalcModeAwareConversion(symbol, PointValue, oneLotSLDrawdown, openPrice, sl);

   if(oneLotSLDrawdown > 0) {
	  LotSize = RiskedMoney / oneLotSLDrawdown;
   }
   else {
	  LotSize = 0;
   }
   
   //Order size multiplier
   LotSize = LotSize * multiplier;

   //round computed trade size 
   LotSize = roundDown(LotSize, sizeStep, decimals);

   //--- MAXLOT and MINLOT management

   Verbose("Computing Money Management - Smallest_Lot: ", DoubleToStr(Smallest_Lot), ", Largest_Lot: ", DoubleToStr(Largest_Lot),", Computed LotSize: ", DoubleToStr(LotSize));
   Verbose("Money to risk: ", DoubleToStr(RiskedMoney), ", Max Trade drawdown: ", DoubleToStr(oneLotSLDrawdown), ", Point value: ", DoubleToStr(PointValue));

   if(LotSize <= 0) {
      Verbose("Calculated LotSize is <= 0. Using LotsIfNoMM value: ", DoubleToStr(LotsIfNoMM), ")");
			LotSize = LotsIfNoMM;
	 }

   if (LotSize < Smallest_Lot) {
      Verbose("Calculated LotSize is too small. Minimal allowed lot size from the broker is: ", DoubleToStr(Smallest_Lot), ". Please, increase your risk or set fixed LotSize.");
      LotSize = 0;
   }
   else if (LotSize > Largest_Lot) {
      Verbose("LotSize is too big. LotSize set to maximal allowed market value: ", DoubleToStr(Largest_Lot));
      LotSize = Largest_Lot;
   }

   if(LotSize > MaximumLots) {
      Verbose("LotSize is too big. LotSize set to maximal allowed value (MaximumLots): ", DoubleToStr(MaximumLots));
      LotSize = MaximumLots;
   }

   //--------------------------------------------

   return (LotSize);
}
