double sqMMATRRiskBasedSizing(string symbol, int orderType, double price, double sl, double RiskInPercent, int ATRPeriod, double ATRMultiplier, int decimals, double LotsIfNoMM, double MaximumLots, double multiplier, double sizeStep) {
   Verbose("Computing Money Management - ATR Risk-Based Sizing");

   if(UseMoneyManagement == false) {
      Verbose("Use Money Management = false, MM not used");
      return (mmLotsIfNoMM);
   }
      
   symbol = correctSymbol(symbol);
   
   double openPrice = price > 0 ? price : (orderType == OP_BUY ? sqGetAsk(symbol) : sqGetBid(symbol));
   double LotSize = 0;

   if(RiskInPercent < 0) {
      Verbose("Computing Money Management - Incorrect RiskInPercent size, it must be above 0");
      return(0);
   }
   
   // Get ATR value
   double atrValue = iATR(symbol, 0, ATRPeriod, 1);
   
   if(atrValue <= 0) {
      Verbose("ATR value is invalid or 0, using LotsIfNoMM");
      return(LotsIfNoMM);
   }
   
   double TickSize = MarketInfo(symbol, MODE_TICKSIZE);
   double PointValue = MarketInfo(symbol, MODE_TICKVALUE) / TickSize;   
   double Smallest_Lot = MarketInfo(symbol, MODE_MINLOT);
   double Largest_Lot = MarketInfo(symbol, MODE_MAXLOT);    
   double LotStep = MarketInfo(symbol, MODE_LOTSTEP);
   
   // Calculate stop distance in ticks (ATR × ATRMult) ÷ tickSize
   double stopDistanceTicks = (atrValue * ATRMultiplier) / TickSize;
   
   // Stop loss in money (using PointValue which is in deposit currency for Forex)
   double slInMoney = NormalizeDouble(stopDistanceTicks * TickSize * PointValue, 7);
   
   // CalcMode-aware conversion for CFD/Futures
   // For ATR-based sizing, we use a synthetic SL to apply the same conversion logic
   int profitCalcMode = (int) MarketInfo(symbol, MODE_PROFITCALCMODE);
   string calcModeStr = (profitCalcMode == 0) ? "Forex" : (profitCalcMode == 1) ? "CFD" : "Futures";
   
   if(profitCalcMode != 0) {
      string quote_currency = SymbolInfoString(symbol, SYMBOL_CURRENCY_PROFIT);
      string account_currency = AccountInfoString(ACCOUNT_CURRENCY);
      
      Verbose("Profit calc mode: ", calcModeStr, ", Quote currency: ", quote_currency, ", Account currency: ", account_currency);
      
      if(quote_currency != "" && account_currency != "" && quote_currency != account_currency) {
         // Manual tick value calculation to avoid MODE_TICKVALUE ambiguity for non-Forex
         double contractSize = MarketInfo(symbol, MODE_LOTSIZE);
         double rawTickValue = contractSize * TickSize;  // tick value in quote currency
         
         double conversionRate = 0;
         bool converted = sqGetCurrencyConversionRate(quote_currency, account_currency, conversionRate);
         if(converted && conversionRate > 0 && rawTickValue > 0) {
            double convertedTickValue = rawTickValue * conversionRate;  // now in deposit currency
            PointValue = convertedTickValue / TickSize;  // = contractSize * conversionRate
            slInMoney = NormalizeDouble(stopDistanceTicks * TickSize * PointValue, 7);
            
            Verbose(calcModeStr, " cross-currency: manual tick value used.");
            Verbose("ContractSize: ", DoubleToStr(contractSize, 2), ", RawTickValue(", quote_currency, "): ", DoubleToStr(rawTickValue, 8),
                    ", ConvertedTickValue(", account_currency, "): ", DoubleToStr(convertedTickValue, 8),
                    ", ConversionRate: ", DoubleToStr(conversionRate, 8));
         } else {
            Verbose("WARNING: Could not find conversion rate from ", quote_currency, " to ", account_currency,
                    ". Using MODE_TICKVALUE as-is (documented as deposit currency).");
         }
      } else {
         Verbose(calcModeStr, " mode: quote_currency matches account_currency, no conversion needed.");
      }
   } else {
      Verbose("Forex mode: MODE_TICKVALUE in deposit currency. No conversion applied.");
   }
   
   // Maximum amount of money to risk 
   double moneyToRisk = NormalizeDouble(AccountEquity() * RiskInPercent / 100, 7);
   
   if(slInMoney > 0) {
      LotSize = moneyToRisk / slInMoney;
   }
   else {
      LotSize = 0;
   }

   // Order size multiplier
   LotSize = LotSize * multiplier;
   
   // Round computed trade size 
   LotSize = roundDown(LotSize, sizeStep, decimals);

   //--- MAXLOT and MINLOT management

   Verbose("MODE_TICKSIZE: ", DoubleToStr(TickSize), ", MODE_TICKVALUE: ", DoubleToStr(MarketInfo(symbol, MODE_TICKVALUE)), ", ATR: ", DoubleToStr(atrValue));
   Verbose("Computing Money Management - Smallest_Lot: ", DoubleToStr(Smallest_Lot), ", Largest_Lot: ", DoubleToStr(Largest_Lot), ", Computed LotSize: ", DoubleToStr(LotSize));
   Verbose("Max money to risk: ", DoubleToStr(moneyToRisk), ", ATR Stop Distance (ticks): ", DoubleToStr(stopDistanceTicks), ", SL in money: ", DoubleToStr(slInMoney), ", Point value: ", DoubleToStr(PointValue));

   if(LotSize <= 0) {
      Verbose("Calculated LotSize is <= 0. Using LotsIfNoMM value: ", DoubleToStr(LotsIfNoMM));
      LotSize = LotsIfNoMM;
   }
   
   if(LotSize > MaximumLots) {
      Verbose("LotSize is too big. LotSize set to maximal allowed value (MaximumLots): ", DoubleToStr(MaximumLots));
      LotSize = MaximumLots;
   }

   //--------------------------------------------

   if(LotSize < Smallest_Lot) {
      Verbose("Calculated LotSize is too small. Minimal allowed lot size from the broker is: ", DoubleToStr(Smallest_Lot), ". Please, increase your risk or set fixed LotSize.");
      LotSize = 0;
   }
   else if(LotSize > Largest_Lot) {
      Verbose("LotSize is too big. LotSize set to maximal allowed market value: ", DoubleToStr(Largest_Lot));
      LotSize = Largest_Lot;
   }

   return (LotSize);
}