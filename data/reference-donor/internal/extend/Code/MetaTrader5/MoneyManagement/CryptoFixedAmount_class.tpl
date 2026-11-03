<#-- GEN-32 (plán 092): Crypto fixed amount MM. ⚠️ PARITA NEOVERENÁ (compile-only) - formula
     zrkadlí autoritatívne NT SQ.inc:175 sqMMFixedAmountByPrice (= RiskedMoney / price), štruktúra
     zrkadlí MT5 CryptoSizeByPrice_class.tpl (crypto sizing, round, min/max clamp). Behaviorálnu
     paritu treba overiť na platforme. -->

double sqMMCryptoFixedAmount(string symbol, ENUM_ORDER_TYPE orderType, double price, double RiskedMoney, int decimals, double multiplier, double sizeStep) {
   Verbose("Computing Money Management for order - Crypto fixed amount");

   if(UseMoneyManagement == false) {
      Verbose("Use Money Management = false, MM not used");
      return (mmLotsIfNoMM);
   }

   string correctedSymbol = correctSymbol(symbol);
   double openPrice = price > 0 ? price : SymbolInfoDouble(correctedSymbol, isLongOrder(orderType) ? SYMBOL_ASK : SYMBOL_BID);

   if(RiskedMoney <= 0 || openPrice <= 0) {
      Verbose("Computing Money Management - Incorrect RiskedMoney or price value");
      return(0);
   }

   //Crypto sizing by price (NT SQ.inc sqMMFixedAmountByPrice): units = RiskedMoney / price
   double LotSize = RiskedMoney / openPrice;

   //Order size multiplier
   LotSize = LotSize * multiplier;

   //round computed trade size
   LotSize = roundDown(LotSize, sizeStep, decimals, symbol);

   double Smallest_Lot = SymbolInfoDouble(correctedSymbol, SYMBOL_VOLUME_MIN);
   double Largest_Lot = SymbolInfoDouble(correctedSymbol, SYMBOL_VOLUME_MAX);

   Verbose("Computing Money Management - Smallest_Lot: ", DoubleToString(Smallest_Lot), ", Largest_Lot: ", DoubleToString(Largest_Lot), ", Computed LotSize: ", DoubleToString(LotSize));

   if(LotSize <= 0) {
      return(0);
   }

   if (LotSize < Smallest_Lot) {
      Verbose("LotSize is too small. Minimal allowed lot size: ", DoubleToString(Smallest_Lot));
      LotSize = 0;
   }
   else if (LotSize > Largest_Lot) {
      Verbose("LotSize is too big. LotSize set to maximal allowed market value: ", DoubleToString(Largest_Lot));
      LotSize = Largest_Lot;
   }

   return (LotSize);
}
