/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  it.unimi.dsi.fastutil.ints.Int2IntOpenHashMap
 *  it.unimi.dsi.fastutil.ints.Int2ObjectOpenHashMap
 *  org.slf4j.Logger
 *  org.slf4j.LoggerFactory
 */
package com.strategyquant.tradinglib.results;

import it.unimi.dsi.fastutil.ints.Int2IntOpenHashMap;
import it.unimi.dsi.fastutil.ints.Int2ObjectOpenHashMap;
import java.util.concurrent.locks.StampedLock;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

public class StatsKeyCache {
    public static final Logger Log = LoggerFactory.getLogger((String)"StatsKeyCache");
    public static final byte TypeInt = 1;
    public static final byte TypeLong = 2;
    public static final byte TypeDouble = 3;
    public static final byte TypeObject = 4;
    public static final Int2IntOpenHashMap defaultShortKeysMap = new Int2IntOpenHashMap(new int[]{"NmbLss".hashCode(), "MxCnsLss".hashCode(), "TtlTrdMons".hashCode(), "StgntnPrd".hashCode(), "MxCnsWns".hashCode(), "NmbPrfts".hashCode(), "TtlTrdYrs".hashCode(), "NmbCncld".hashCode(), "TtlTrdDs".hashCode(), "DgrsFrdm".hashCode(), "NmbTrds".hashCode(), "MxLss".hashCode(), "ShrpRt".hashCode(), "Cmmsn".hashCode(), "AvgCnsLss".hashCode(), "ZPrbb".hashCode(), "ZScr".hashCode(), "RXpScr".hashCode(), "Ahpr".hashCode(), "ClmrRt".hashCode(), "DD".hashCode(), "NtPrft".hashCode(), "Stblt".hashCode(), "AvgTrdsMnt".hashCode(), "PipDD".hashCode(), "AvgPrftYr".hashCode(), "GrsLss".hashCode(), "AvgPrftMnt".hashCode(), "AvgTrd".hashCode(), "AvgAbsTrd".hashCode(), "AvgPrftD".hashCode(), "AvgCnsWn".hashCode(), "PctDD".hashCode(), "WnLssRt".hashCode(), "AarDDRt".hashCode(), "AnnPctRet".hashCode(), "RetDDRt".hashCode(), "PayRt".hashCode(), "PrfFctr".hashCode(), "AvgBrWn".hashCode(), "Sng".hashCode(), "AvgBrTrd".hashCode(), "AvgWn".hashCode(), "AvfLss".hashCode(), "CAGR".hashCode(), "RXpctnc".hashCode(), "RXpctncScr".hashCode(), "Smmtr".hashCode(), "SqnScr".hashCode(), "AvgTrdsD".hashCode(), "AvgTrdsY".hashCode(), "Expc".hashCode(), "GrssPrft".hashCode(), "AvrBrLss".hashCode(), "WinPct".hashCode(), "StagPct".hashCode(), "MxPrft".hashCode(), "Expsr".hashCode(), "IntDep".hashCode(), "Fitness".hashCode(), "StdDev".hashCode(), "StagFrm".hashCode(), "StagTo".hashCode(), "SHPR".hashCode(), "AmbTrd".hashCode(), "AmbTrdPct".hashCode(), "BckDur".hashCode(), "FiltRes".hashCode(), "MinEC".hashCode(), "RSQR".hashCode(), "StabSQ3".hashCode(), "TrdSym".hashCode(), "WYP".hashCode(), "ActDD".hashCode(), "ActDDPct".hashCode(), "NSym".hashCode(), "StgTo".hashCode(), "StgFrom".hashCode(), "TF".hashCode(), "Sym".hashCode(), "ResNam".hashCode(), "Note".hashCode(), "WFMaxDDbyRun".hashCode(), "WFMaxPctDDbyRun".hashCode(), "WFMaxProfitByRun".hashCode(), "WFMaxProfitByRunInPct".hashCode(), "WFMaxStagnationInPct".hashCode(), "WFMinTradesInRun".hashCode(), "WFPctOfProfitableRuns".hashCode(), "NetPrPct".hashCode(), "NetPrPips".hashCode(), "AvgPctPrYr".hashCode(), "CommSwapM".hashCode(), "SlipM".hashCode(), "LongestTrade".hashCode(), "ProfitableMonths".hashCode(), "ProfitableMonthsPct".hashCode(), "TtlDDs".hashCode(), "TtlDMs".hashCode(), "TtlDYs".hashCode(), "ASTDR".hashCode(), "APS".hashCode(), "WPS".hashCode(), "Effic".hashCode(), "KllFrm".hashCode(), "MID".hashCode(), "TSI".hashCode(), "ODDPct".hashCode(), "DG".hashCode(), "DLM".hashCode()}, new int[]{"NumberOfLosses".hashCode(), "MaxConsecLosses".hashCode(), "TotalTradingMonths".hashCode(), "Stagnation".hashCode(), "MaxConsecWins".hashCode(), "NumberOfProfits".hashCode(), "TotalTradingYears".hashCode(), "NumberOfCanceled".hashCode(), "TotalTradingDays".hashCode(), "DegreesOfFreedom".hashCode(), "NumberOfTrades".hashCode(), "MaxLoss".hashCode(), "SharpeRatio".hashCode(), "Commission".hashCode(), "AvgConsecLosses".hashCode(), "ZProbability".hashCode(), "ZScore".hashCode(), "RExpectancyscore".hashCode(), "AHPR".hashCode(), "CalmarRatio".hashCode(), "Drawdown".hashCode(), "NetProfit".hashCode(), "Stability".hashCode(), "AvgTradesPerMonth".hashCode(), "DrawdownPips".hashCode(), "AvgProfitPerYear".hashCode(), "GrossLoss".hashCode(), "AvgProfitPerMonth".hashCode(), "AvgTrade".hashCode(), "AvgAbsTrade".hashCode(), "AvgProfitPerDay".hashCode(), "AvgConsecWins".hashCode(), "DrawdownPct".hashCode(), "WinLossRatio".hashCode(), "AnnualPctReturnDDRatio".hashCode(), "AnnualPctReturn".hashCode(), "ReturnDDRatio".hashCode(), "PayoutRatio".hashCode(), "ProfitFactor".hashCode(), "AvgBarsWin".hashCode(), "SQN".hashCode(), "AvgBarsInTrade".hashCode(), "AvgWin".hashCode(), "AvgLoss".hashCode(), "CAGR".hashCode(), "RExpectancy".hashCode(), "RExpectancyScore".hashCode(), "Symmetry".hashCode(), "SQNScore".hashCode(), "AvgTradesPerDay".hashCode(), "AvgTradesPerYear".hashCode(), "Expectancy".hashCode(), "GrossProfit".hashCode(), "AvgBarsLoss".hashCode(), "WinningPct".hashCode(), "StagnationPct".hashCode(), "MaxProfit".hashCode(), "Exposure".hashCode(), "InitialDeposit".hashCode(), "Fitness".hashCode(), "StandardDev".hashCode(), "StagnationTo".hashCode(), "StagnationFrom".hashCode(), "SHPR".hashCode(), "AmbiguousTrades".hashCode(), "AmbiguousTradesPct".hashCode(), "BacktestDuration".hashCode(), "FiltersResult".hashCode(), "MiniEquityChart".hashCode(), "RSquared".hashCode(), "StabilitySQ3".hashCode(), "TradesSymmetry".hashCode(), "WorstYearProfit".hashCode(), "ActualDD".hashCode(), "ActualDrawdownPct".hashCode(), "NSymmetry".hashCode(), "StagnationTo".hashCode(), "StagnationFrom".hashCode(), "TimeFrame".hashCode(), "Symbol".hashCode(), "ResultsName".hashCode(), "Note".hashCode(), "WFMaxDDbyRun".hashCode(), "WFMaxPctDDbyRun".hashCode(), "WFMaxProfitByRun".hashCode(), "WFMaxProfitByRunInPct".hashCode(), "WFMaxStagnationInPct".hashCode(), "WFMinTradesInRun".hashCode(), "WFPctOfProfitableRuns".hashCode(), "NetProfitInPct".hashCode(), "NetProfitInPips".hashCode(), "AvgPctProfitPerYear".hashCode(), "CommSwapInMoney".hashCode(), "SlippageInMoney".hashCode(), "LongestTrade".hashCode(), "ProfitableMonths".hashCode(), "ProfitableMonthsPct".hashCode(), "TotalDataDays".hashCode(), "TotalDataMonths".hashCode(), "TotalDataYears".hashCode(), "AvgTrStddevRatio".hashCode(), "AvgParametersStability".hashCode(), "WorstParametersStability".hashCode(), "Efficiency".hashCode(), "KellyFormula".hashCode(), "MaxIntradayDrawdown".hashCode(), "TSIndex".hashCode(), "OpenDrawdownPct".hashCode(), "DateGenerated".hashCode(), "DateLastModified".hashCode()});
    public static final Int2ObjectOpenHashMap<StatInfo> defaultKeysMap = new Int2ObjectOpenHashMap(new int[]{"NumberOfLosses".hashCode(), "MaxConsecLosses".hashCode(), "TotalTradingMonths".hashCode(), "Stagnation".hashCode(), "MaxConsecWins".hashCode(), "NumberOfProfits".hashCode(), "TotalTradingYears".hashCode(), "NumberOfCanceled".hashCode(), "TotalTradingDays".hashCode(), "DegreesOfFreedom".hashCode(), "NumberOfTrades".hashCode(), "Complexity".hashCode(), "LongestTrade".hashCode(), "ProfitableMonths".hashCode(), "TotalDataDays".hashCode(), "TotalDataMonths".hashCode(), "TotalDataYears".hashCode(), "MaxLoss".hashCode(), "SharpeRatio".hashCode(), "Commission".hashCode(), "AvgConsecLosses".hashCode(), "ZProbability".hashCode(), "ZScore".hashCode(), "RExpectancyscore".hashCode(), "AHPR".hashCode(), "CalmarRatio".hashCode(), "Drawdown".hashCode(), "NetProfit".hashCode(), "Stability".hashCode(), "AvgTradesPerMonth".hashCode(), "DrawdownPips".hashCode(), "AvgProfitPerYear".hashCode(), "GrossLoss".hashCode(), "AvgProfitPerMonth".hashCode(), "AvgTrade".hashCode(), "AvgAbsTrade".hashCode(), "AvgProfitPerDay".hashCode(), "AvgConsecWins".hashCode(), "DrawdownPct".hashCode(), "WinLossRatio".hashCode(), "AnnualPctReturnDDRatio".hashCode(), "AnnualPctReturn".hashCode(), "ReturnDDRatio".hashCode(), "PayoutRatio".hashCode(), "ProfitFactor".hashCode(), "AvgBarsWin".hashCode(), "SQN".hashCode(), "AvgBarsInTrade".hashCode(), "AvgWin".hashCode(), "AvgLoss".hashCode(), "CAGR".hashCode(), "RExpectancy".hashCode(), "RExpectancyScore".hashCode(), "Symmetry".hashCode(), "SQNScore".hashCode(), "AvgTradesPerDay".hashCode(), "AvgTradesPerYear".hashCode(), "Expectancy".hashCode(), "GrossProfit".hashCode(), "AvgBarsLoss".hashCode(), "WinningPct".hashCode(), "StagnationPct".hashCode(), "MaxProfit".hashCode(), "Exposure".hashCode(), "InitialDeposit".hashCode(), "Fitness".hashCode(), "StandardDev".hashCode(), "SHPR".hashCode(), "AmbiguousTrades".hashCode(), "AmbiguousTradesPct".hashCode(), "BacktestDuration".hashCode(), "FiltersResult".hashCode(), "MiniEquityChart".hashCode(), "RSquared".hashCode(), "StabilitySQ3".hashCode(), "TradesSymmetry".hashCode(), "WorstYearProfit".hashCode(), "ActualDD".hashCode(), "ActualDrawdownPct".hashCode(), "NSymmetry".hashCode(), "TimeFrame".hashCode(), "Symbol".hashCode(), "ResultsName".hashCode(), "Note".hashCode(), "WFMaxDDbyRun".hashCode(), "WFMaxPctDDbyRun".hashCode(), "WFMaxProfitByRun".hashCode(), "WFMaxProfitByRunInPct".hashCode(), "WFMaxStagnationInPct".hashCode(), "WFMinTradesInRun".hashCode(), "WFPctOfProfitableRuns".hashCode(), "ExitIndicators".hashCode(), "EntryIndicators".hashCode(), "MagicNumber".hashCode(), "WFScore".hashCode(), "PriceIndicators".hashCode(), "BiggestMAE".hashCode(), "NetProfitInPct".hashCode(), "NetProfitInPips".hashCode(), "AvgPctProfitPerYear".hashCode(), "CommSwapInMoney".hashCode(), "SlippageInMoney".hashCode(), "OpenDrawdown".hashCode(), "ProfitableMonthsPct".hashCode(), "AvgTrStddevRatio".hashCode(), "AvgParametersStability".hashCode(), "WorstParametersStability".hashCode(), "Efficiency".hashCode(), "KellyFormula".hashCode(), "MaxIntradayDrawdown".hashCode(), "TSIndex".hashCode(), "OpenDrawdownPct".hashCode(), "StagnationTo".hashCode(), "StagnationFrom".hashCode(), "DateGenerated".hashCode(), "DateLastModified".hashCode()}, (Object[])new StatInfo[]{new StatInfo(0, "NumberOfLosses", "NmbLss", 1), new StatInfo(1, "MaxConsecLosses", "MxCnsLss", 1), new StatInfo(2, "TotalTradingMonths", "TtlTrdMons", 1), new StatInfo(3, "Stagnation", "StgntnPrd", 1), new StatInfo(4, "MaxConsecWins", "MxCnsWns", 1), new StatInfo(5, "NumberOfProfits", "NmbPrfts", 1), new StatInfo(6, "TotalTradingYears", "TtlTrdYrs", 1), new StatInfo(7, "NumberOfCanceled", "NmbCncld", 1), new StatInfo(8, "TotalTradingDays", "TtlTrdDs", 1), new StatInfo(9, "DegreesOfFreedom", "DgrsFrdm", 1), new StatInfo(10, "NumberOfTrades", "NmbTrds", 1), new StatInfo(11, "Complexity", "Cmplxt", 1), new StatInfo(12, "LongestTrade", "LongestTrade", 1), new StatInfo(13, "ProfitableMonths", "ProfitableMonths", 1), new StatInfo(14, "TotalDataDays", "TtlDDs", 1), new StatInfo(15, "TotalDataMonths", "TtlDMs", 1), new StatInfo(16, "TotalDataYears", "TtlDYs", 1), new StatInfo(0, "MaxLoss", "MxLss", 3), new StatInfo(1, "SharpeRatio", "ShrpRt", 3), new StatInfo(2, "Commission", "Cmmsn", 3), new StatInfo(3, "AvgConsecLosses", "AvgCnsLss", 3), new StatInfo(4, "ZProbability", "ZPrbb", 3), new StatInfo(5, "ZScore", "ZScr", 3), new StatInfo(6, "RExpectancyscore", "RXpScr", 3), new StatInfo(7, "AHPR", "Ahpr", 3), new StatInfo(8, "CalmarRatio", "ClmrRt", 3), new StatInfo(9, "Drawdown", "DD", 3), new StatInfo(10, "NetProfit", "NtPrft", 3), new StatInfo(11, "Stability", "Stblt", 3), new StatInfo(12, "AvgTradesPerMonth", "AvgTrdsMnt", 3), new StatInfo(13, "DrawdownPips", "PipDD", 3), new StatInfo(14, "AvgProfitPerYear", "AvgPrftYr", 3), new StatInfo(15, "GrossLoss", "GrsLss", 3), new StatInfo(16, "AvgProfitPerMonth", "AvgPrftMnt", 3), new StatInfo(17, "AvgTrade", "AvgTrd", 3), new StatInfo(18, "AvgAbsTrade", "AvgAbsTrd", 3), new StatInfo(19, "AvgProfitPerDay", "AvgPrftD", 3), new StatInfo(20, "AvgConsecWins", "AvgCnsWn", 3), new StatInfo(21, "DrawdownPct", "PctDD", 3), new StatInfo(22, "WinLossRatio", "WnLssRt", 3), new StatInfo(23, "AnnualPctReturnDDRatio", "AarDDRt", 3), new StatInfo(24, "AnnualPctReturn", "AnnPctRet", 3), new StatInfo(25, "ReturnDDRatio", "RetDDRt", 3), new StatInfo(26, "PayoutRatio", "PayRt", 3), new StatInfo(27, "ProfitFactor", "PrfFctr", 3), new StatInfo(28, "AvgBarsWin", "AvgBrWn", 3), new StatInfo(29, "SQN", "Sng", 3), new StatInfo(30, "AvgBarsInTrade", "AvgBrTrd", 3), new StatInfo(31, "AvgWin", "AvgWn", 3), new StatInfo(32, "AvgLoss", "AvfLss", 3), new StatInfo(33, "CAGR", "CAGR", 3), new StatInfo(34, "RExpectancy", "RXpctnc", 3), new StatInfo(35, "RExpectancyScore", "RXpctncScr", 3), new StatInfo(36, "Symmetry", "Smmtr", 3), new StatInfo(37, "SQNScore", "SqnScr", 3), new StatInfo(38, "AvgTradesPerDay", "AvgTrdsD", 3), new StatInfo(39, "AvgTradesPerYear", "AvgTrdsY", 3), new StatInfo(40, "Expectancy", "Expc", 3), new StatInfo(41, "GrossProfit", "GrssPrft", 3), new StatInfo(42, "AvgBarsLoss", "AvrBrLss", 3), new StatInfo(43, "WinningPct", "WinPct", 3), new StatInfo(44, "StagnationPct", "StagPct", 3), new StatInfo(45, "MaxProfit", "MxPrft", 3), new StatInfo(46, "Exposure", "Expsr", 3), new StatInfo(47, "InitialDeposit", "IntDep", 3), new StatInfo(48, "Fitness", "Fitness", 3), new StatInfo(49, "StandardDev", "StdDev", 3), new StatInfo(50, "SHPR", "SHPR", 3), new StatInfo(51, "AmbiguousTrades", "AmbTrd", 3), new StatInfo(52, "AmbiguousTradesPct", "AmbTrdPct", 3), new StatInfo(53, "BacktestDuration", "BckDur", 3), new StatInfo(54, "FiltersResult", "FiltRes", 3), new StatInfo(55, "MiniEquityChart", "MinEC", 3), new StatInfo(56, "RSquared", "RSQR", 3), new StatInfo(57, "StabilitySQ3", "StabSQ3", 3), new StatInfo(58, "TradesSymmetry", "TrdSym", 3), new StatInfo(59, "WorstYearProfit", "WYP", 3), new StatInfo(60, "ActualDD", "ActDD", 3), new StatInfo(61, "ActualDrawdownPct", "ActDDPct", 3), new StatInfo(62, "NSymmetry", "NSym", 3), new StatInfo(63, "TimeFrame", "TF", 3), new StatInfo(64, "Symbol", "Sym", 3), new StatInfo(65, "ResultsName", "ResNam", 3), new StatInfo(66, "Note", "Note", 3), new StatInfo(67, "WFMaxDDbyRun", "WFMaxDDbyRun", 3), new StatInfo(68, "WFMaxPctDDbyRun", "WFMaxPctDDbyRun", 3), new StatInfo(69, "WFMaxProfitByRun", "WFMaxProfitByRun", 3), new StatInfo(70, "WFMaxProfitByRunInPct", "WFMaxProfitByRunInPct", 3), new StatInfo(71, "WFMaxStagnationInPct", "WFMaxStagnationInPct", 3), new StatInfo(72, "WFMinTradesInRun", "WFMinTradesInRun", 3), new StatInfo(73, "WFPctOfProfitableRuns", "WFPctOfProfitableRuns", 3), new StatInfo(74, "ExitIndicators", "ExitI", 3), new StatInfo(75, "EntryIndicators", "EntryI", 3), new StatInfo(76, "MagicNumber", "MagNum", 3), new StatInfo(77, "WFScore", "WFScore", 3), new StatInfo(78, "PriceIndicators", "PriceI", 3), new StatInfo(79, "BiggestMAE", "BOL", 3), new StatInfo(80, "NetProfitInPct", "NetPrPct", 3), new StatInfo(81, "NetProfitInPips", "NetPrPips", 3), new StatInfo(82, "AvgPctProfitPerYear", "AvgPctPrYr", 3), new StatInfo(83, "CommSwapInMoney", "CommSwapM", 3), new StatInfo(84, "SlippageInMoney", "SlipM", 3), new StatInfo(85, "OpenDrawdown", "ODD", 3), new StatInfo(86, "ProfitableMonthsPct", "ProfitableMonthsPct", 3), new StatInfo(87, "AvgTrStddevRatio", "ASTDR", 3), new StatInfo(88, "AvgParametersStability", "APS", 3), new StatInfo(89, "WorstParametersStability", "WPS", 3), new StatInfo(90, "Efficiency", "Effic", 3), new StatInfo(91, "KellyFormula", "KllFrm", 3), new StatInfo(92, "MaxIntradayDrawdown", "MID", 3), new StatInfo(93, "TSIndex", "TSI", 3), new StatInfo(94, "OpenDrawdownPct", "ODDPct", 3), new StatInfo(0, "StagnationTo", "StagFrm", 2), new StatInfo(1, "StagnationFrom", "StagTo", 2), new StatInfo(2, "DateGenerated", "DG", 2), new StatInfo(3, "DateLastModified", "DLM", 2)});
    private static final Int2ObjectOpenHashMap<Object> unknownKeysMap = new Int2ObjectOpenHashMap();
    private static final StampedLock stampedLock = new StampedLock();
    private static int intsCount = 17;
    private static int doublesCount = 95;
    private static int longsCount = 4;

    public static StatInfo getKey(String string) {
        int n = string.hashCode();
        return StatsKeyCache.getKey(n);
    }

    public static StatInfo getKey(int n) {
        if (defaultKeysMap.containsKey(n)) {
            return (StatInfo)defaultKeysMap.get(n);
        }
        return null;
    }

    public static StatInfo getShortKey(int n) {
        int n2 = -1111111111;
        if (defaultShortKeysMap.containsKey(n)) {
            n2 = defaultShortKeysMap.get(n);
        }
        if (n2 == -1111111111) {
            return null;
        }
        return StatsKeyCache.getKey(n2);
    }

    /*
     * WARNING - Removed try catching itself - possible behaviour change.
     */
    public static int registerKey(String string, byte by) {
        int n = string.hashCode();
        if (defaultKeysMap.containsKey(n)) {
            throw new IllegalArgumentException("Key " + string + "is known, use getKey() instead!");
        }
        long l = stampedLock.tryOptimisticRead();
        if (unknownKeysMap.containsKey(n) && stampedLock.validate(l)) {
            return n;
        }
        l = stampedLock.writeLock();
        try {
            Log.debug("Unknown {} key added {}", (Object)StatsKeyCache.typeToString(by), (Object)string);
            if (unknownKeysMap.containsKey(n)) {
                int n2 = n;
                return n2;
            }
            unknownKeysMap.put(n, (Object)string);
            Log.debug("Unknown {} key added {}", (Object)StatsKeyCache.typeToString(by), (Object)string);
            int n3 = n;
            return n3;
        }
        finally {
            stampedLock.unlockWrite(l);
        }
    }

    public static String typeToString(byte by) {
        switch (by) {
            case 1: {
                return "int";
            }
            case 3: {
                return "double";
            }
            case 2: {
                return "long";
            }
        }
        return "object";
    }

    /*
     * WARNING - Removed try catching itself - possible behaviour change.
     */
    public static String getUnknownKeyName(int n) {
        if (defaultKeysMap.containsKey(n)) {
            throw new IllegalArgumentException("Key with hash " + n + "is known, use getKey() instead!");
        }
        long l = stampedLock.tryOptimisticRead();
        String string = (String)unknownKeysMap.get(n);
        if (!stampedLock.validate(l)) {
            l = stampedLock.readLock();
            try {
                string = (String)unknownKeysMap.get(n);
            }
            finally {
                stampedLock.unlockRead(l);
            }
        }
        return string;
    }

    public static boolean isDefaultValue(int n) {
        return defaultKeysMap.containsKey(n);
    }

    public static int getIntsCount() {
        return intsCount;
    }

    public static int getDoublesCount() {
        return doublesCount;
    }

    public static int getLongsCount() {
        return longsCount;
    }

    public static class StatInfo {
        public int index;
        public int type;
        public String name;
        public String shortName;

        public StatInfo(int n, String string, String string2, int n2) {
            this.index = n;
            this.name = string;
            this.shortName = string2;
            this.type = n2;
        }
    }
}

