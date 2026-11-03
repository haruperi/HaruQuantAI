<#-- GEN-32 (plán 092): Crypto fixed % of balance MM (MT4). ⚠️ PARITA NEOVERENÁ (compile-only) -
     formula zrkadlí NT SQ.inc:184 sqMMBalancePctByPrice (= balance * min(risk,100)/100 / price),
     štruktúra zrkadlí MT4 CryptoSizeByPrice_class.tpl. Behaviorálnu paritu treba overiť na platforme. -->

double sqMMCryptoFixedBalancePct(string symbol, int orderType, double price, double riskPct, int decimals, double multiplier, double sizeStep) {
   Verbose("Computing Money Management for order - Crypto fixed % of balance");

   if(UseMoneyManagement == false) {
      Verbose("Use Money Management = false, MM not used");
      return (mmLotsIfNoMM);
   }

   symbol = correctSymbol(symbol);

   double openPrice = price > 0 ? price : (orderType == OP_BUY ? sqGetAsk(symbol) : sqGetBid(symbol));

   if(openPrice <= 0) {
      return(0);
   }

   //Crypto sizing by price (NT SQ.inc sqMMBalancePctByPrice): units = (balance * min(risk,100)/100) / price
   double moneyToRisk = AccountBalance() * (MathMin(riskPct, 100.0) / 100.0);
   double LotSize = moneyToRisk / openPrice;

   //Order size multiplier
   LotSize = LotSize * multiplier;

   //round computed trade size
   LotSize = roundDown(LotSize, sizeStep, decimals);

   double Smallest_Lot = MarketInfo(symbol, MODE_MINLOT);
   double Largest_Lot = MarketInfo(symbol, MODE_MAXLOT);

   Verbose("Computing Money Management - Smallest_Lot: ", DoubleToStr(Smallest_Lot), ", Largest_Lot: ", DoubleToStr(Largest_Lot), ", Computed LotSize: ", DoubleToStr(LotSize));

   if(LotSize <= 0) {
      return(0);
   }

   if (LotSize < Smallest_Lot) {
      Verbose("LotSize is too small. Minimal allowed lot size: ", DoubleToStr(Smallest_Lot));
      LotSize = 0;
   }
   else if (LotSize > Largest_Lot) {
      Verbose("LotSize is too big. LotSize set to maximal allowed market value: ", DoubleToStr(Largest_Lot));
      LotSize = Largest_Lot;
   }

   return (LotSize);
}
