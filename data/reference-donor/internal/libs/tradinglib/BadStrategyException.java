/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  com.strategyquant.datalib.TradingException
 *  com.strategyquant.lib.L
 *  it.unimi.dsi.fastutil.ints.IntArrayList
 */
package com.strategyquant.tradinglib;

import com.strategyquant.datalib.TradingException;
import com.strategyquant.lib.L;
import com.strategyquant.tradinglib.crosscheck.CrossCheckMethod;
import com.strategyquant.tradinglib.exception.StrategyProblem;
import it.unimi.dsi.fastutil.ints.IntArrayList;
import java.util.ArrayList;

public class BadStrategyException
extends TradingException {
    public static final int ReasonNoTrades = 1;
    public static final int ReasonTooLittleTrades = 2;
    public static final int ReasonZeroPLTrades = 4;
    public static final int ReasonTooShortTrades = 8;
    public static final int ReasonZeroDurationTrades = 16;
    public static final int ReasonTooManyOpenTrades = 32;
    public static final int ReasonTooLongTrade = 64;
    public static final int ReasonNoFilledTrades = 256;
    public static final int ReasonOutlierTrade = 512;
    public static final int ReasonAmbiguousTrades = 1024;
    public static final int ReasonStockpickerShiftChanged = 2048;
    public static final int ReasonThreshold = 10000;
    public static final int ReasonBacktestException = 10001;
    public static final int ReasonStopped = 10002;
    public static final int ReasonExceptionEvaluatingConditions = 10003;
    public static final int ReasonCrossCheckException = 10004;
    public static final int ReasonInitialPopulation = 10005;
    public static final int ReasonStrategyTooSimilar = 10006;
    public static final int ReasonReplacedWithBetterStrategy = 10007;
    public static final int ReasonOptProfileProfitableOptimizations = 10008;
    public static final int ReasonOptProfileAvgProfit = 10009;
    public static final int ReasonOptProfileUniformDistribution = 10010;
    public static final int ReasonOptProfileBestOptimizationProfit = 10011;
    public static final int ReasonAdditionalMarketsFilter = 10012;
    public static final int ReasonWrongParamsException = 10013;
    public static final int ReasonCorrelationWithExistingPortfolio = 10014;
    public static final int ReasonPortfolioMasterCorrelationLimitation = 10015;
    public static final int ReasonPortfolioMasterSectorLimitation = 10016;
    public static final int ReasonStrategyRequireXreservedBars = 10017;
    public static final int ReasonCCExceptionMCManipulation = 10030;
    public static final int ReasonCCExceptionMCRetest = 10031;
    public static final int ReasonCCExceptionOptProfileSPP = 10032;
    public static final int ReasonCCExceptionAddMarkets = 10033;
    public static final int ReasonCCExceptionWFMatrix = 10034;
    public static final int ReasonCCExceptionWFOptim = 10035;
    public static final int ReasonCCExceptionHigherBacktestPrecis = 10036;
    public static final int ReasonCCExceptionWhatIf = 10037;
    public static final int ReasonCustomAnalysisFilter = 10038;
    public static final int ReasonCCExceptionSequentialOptimization = 10039;
    public static final String TxtShortReasonNoTrades = L.t((String)"no trades", (Object[])new Object[0]);
    public static final String TxtShortReasonTooLittleTrades = L.t((String)"too little trades", (Object[])new Object[0]);
    public static final String TxtShortReasonZeroPLTrades = L.t((String)"zero PL trades", (Object[])new Object[0]);
    public static final String TxtShortReasonTooShortTrades = L.t((String)"too many trades closing at the same bar", (Object[])new Object[0]);
    public static final String TxtShortReasonZeroDurationTrades = L.t((String)"zero duration trades", (Object[])new Object[0]);
    public static final String TxtShortReasonTooManyOpenTrades = L.t((String)"too many open trades", (Object[])new Object[0]);
    public static final String TxtShortReasonTooLongTrade = L.t((String)"unfinished trades", (Object[])new Object[0]);
    public static final String TxtShortReasonNoFilledTrades = L.t((String)"no filled trades", (Object[])new Object[0]);
    private static final String TxtShortReasonThreshold = L.t((String)"Fitness threshold not reached", (Object[])new Object[0]);
    private static final String TxtShortReasonBacktestException = L.t((String)"backtest exception", (Object[])new Object[0]);
    private static final String TxtReasonCrossCheckException = L.t((String)"cross check exception", (Object[])new Object[0]);
    private static final String TxtReasonCustomAnalysisFilter = L.t((String)"custom analysis filter failed", (Object[])new Object[0]);
    private static final String TxtShortReasonStopped = L.t((String)"test stopped", (Object[])new Object[0]);
    private static final String TxtShortReasonExceptionEvaluatingConditions = L.t((String)"exception evaluating conditions", (Object[])new Object[0]);
    public static final String TxtShortReasonInitialPopulation = L.t((String)"initial population", (Object[])new Object[0]);
    public static final String TxtShortReasonStrategyTooSimilar = L.t((String)"too similar strategy in databank", (Object[])new Object[0]);
    public static final String TxtShortReasonOutlierTrade = L.t((String)"outlier trade - one exceptionally big trade", (Object[])new Object[0]);
    public static final String TxtShortReasonAmbiguousTrades = L.t((String)"too many ambiguous trades", (Object[])new Object[0]);
    public static final String TxtShortReplacedWithBetterStrategy = L.t((String)"replaced with better strategy", (Object[])new Object[0]);
    public static final String TxtShortOptProfileProfitableOptimizations = L.t((String)"Cross Check filter in 'Opt. Profile / Sys. Param. Permutation': % of Profitable Optimizations", (Object[])new Object[0]);
    public static final String TxtShortOptProfileAvgProfit = L.t((String)"Cross Check filter in 'Opt. Profile / Sys. Param. Permutation': average profit", (Object[])new Object[0]);
    public static final String TxtShortOptProfileUniformDistribution = L.t((String)"Cross Check filter in 'Opt. Profile / Sys. Param. Permutation': uniform distribution", (Object[])new Object[0]);
    public static final String TxtShortOptProfileBestOptimizationProfit = L.t((String)"Cross Check filter in 'Opt. Profile / Sys. Param. Permutation': best Optimization profit", (Object[])new Object[0]);
    public static final String TxtShorAdditionalMarketsFilter = L.t((String)"Cross Check filter in 'Retest on additional markets': additional markets filter failed (multiple conditions)", (Object[])new Object[0]);
    private static final String TxtShortReasonWrongParamsException = L.t((String)"wrong params exception", (Object[])new Object[0]);
    public static final String TxtLongReasonNoTrades = L.t((String)"Strategy produces no trades", (Object[])new Object[0]);
    public static final String TxtLongReasonTooLittleTrades = L.t((String)"Strategy produces too little trades, results are not statistically significant", (Object[])new Object[0]);
    public static final String TxtLongReasonZeroPLTrades = L.t((String)"Strategy produces trades with zero P/L", (Object[])new Object[0]);
    public static final String TxtLongReasonTooShortTrades = L.t((String)"Strategy produces too many trades closing at the same bar", (Object[])new Object[0]);
    public static final String TxtLongReasonZeroDurationTrades = L.t((String)"Strategy produces trades with zero duration - trades that are closed immediately after they are opened", (Object[])new Object[0]);
    public static final String TxtLongReasonTooManyOpenTrades = L.t((String)"Strategy produces too many open trades", (Object[])new Object[0]);
    public static final String TxtLongReasonTooLongTrade = L.t((String)"Strategy produces unfinished trade(s) - trade that is not closed until the very end of trading", (Object[])new Object[0]);
    public static final String TxtLongReasonNoFilledTrades = L.t((String)"Strategy produces no filled trades", (Object[])new Object[0]);
    public static final String TxtLongReasonInitialPopulation = L.t((String)"initial population", (Object[])new Object[0]);
    public static final String TxtLongReasonStrategyTooSimilar = L.t((String)"Strategy is too similar or the same as some other strategy in databank", (Object[])new Object[0]);
    public static final String TxtLongReasonOutlierTrade = L.t((String)"Strategy produces outlier trade - one exceptionally big trade", (Object[])new Object[0]);
    public static final String TxtLongReasonAmbiguousTrades = L.t((String)"Strategy produces too many ambiguous trades - where it is not possible to determine if SL or PT is reached first", (Object[])new Object[0]);
    public static final String TxtLongReplacedWithBetterStrategy = L.t((String)"Replaced with better strategy", (Object[])new Object[0]);
    public static final String TxtLongOptProfileProfitableOptimizations = L.t((String)"Cross Check filter in 'Opt. Profile / Sys. Param. Permutation': % of Profitable Optimizations", (Object[])new Object[0]);
    public static final String TxtLongOptProfileAvgProfit = L.t((String)"Cross Check filter in 'Opt. Profile / Sys. Param. Permutation': average profit", (Object[])new Object[0]);
    public static final String TxtLongOptProfileUniformDistribution = L.t((String)"Cross Check filter in 'Opt. Profile / Sys. Param. Permutation': uniform distribution", (Object[])new Object[0]);
    public static final String TxtLongOptProfileBestOptimizationProfit = L.t((String)"Cross Check filter in 'Opt. Profile / Sys. Param. Permutation': best Optimization profit", (Object[])new Object[0]);
    public static final String TxtLongAdditionalMarketsFilter = L.t((String)"Cross Check filter in 'Retest on additional markets': additional markets filter failed (multiple conditions)", (Object[])new Object[0]);
    public static final String TxtReasonCCExceptionMCManipulation = L.t((String)"Cross Check filter in '%s': Automatic filter", (Object[])new Object[]{CrossCheckMethod.NameMCManipulation});
    public static final String TxtReasonCCExceptionMCRetest = L.t((String)"Cross Check filter in '%s': Automatic filter", (Object[])new Object[]{CrossCheckMethod.NameMCRetest});
    public static final String TxtReasonCCExceptionOptProfileSPP = L.t((String)"Cross Check filter in '%s': Automatic filter", (Object[])new Object[]{CrossCheckMethod.NameOptProfileSPP});
    public static final String TxtReasonCCExceptionAddMarkets = L.t((String)"Cross Check filter in '%s': Automatic filter", (Object[])new Object[]{CrossCheckMethod.NameAddMarkets});
    public static final String TxtReasonCCExceptionWFMatrix = L.t((String)"Cross Check filter in '%s': Automatic filter", (Object[])new Object[]{CrossCheckMethod.NameWFMatrix});
    public static final String TxtReasonCCExceptionWFOptim = L.t((String)"Cross Check filter in '%s': Automatic filter", (Object[])new Object[]{CrossCheckMethod.NameWFOptimization});
    public static final String TxtReasonCCExceptionSequentialOptimization = L.t((String)"Cross Check filter in '%s': Automatic filter", (Object[])new Object[]{CrossCheckMethod.NameSequentialOptimization});
    public static final String TxtReasonCCExceptionHigherBacktestPrecis = L.t((String)"Cross Check filter in '%s': Automatic filter", (Object[])new Object[]{CrossCheckMethod.NameHigherBacktestPrecis});
    public static final String TxtCorrelationWithExistingPortfolio = L.t((String)"Correlation with existing portfolio", (Object[])new Object[0]);
    public static final String TxtPortfolioMasterCorrelationLimitation = L.t((String)"Correlation limitation", (Object[])new Object[0]);
    public static final String TxtPortfolioMasterSectorLimitation = L.t((String)"Sector limitation", (Object[])new Object[0]);
    public static final String TxtStrategyRequireXreservedBars = L.t((String)"Strategy require X reserved bars", (Object[])new Object[0]);
    public static final int PrefixInitialConditions = 100000;
    public static final int PrefixNormalConditions = 200000;
    public static final int PrefixCrossCheckConditions = 300000;
    public static final String ExplanationUnknown = L.t((String)"Unknown", (Object[])new Object[0]);
    public static final String ReplacedWorseStrategy = "ReplacedWorseStrategy";
    public static final String TxtLongReasonStockpickerShiftChanged = L.t((String)"Your strategy contains condition that uses Close, High, Low, Typical, Median, Weighted with Shift=0 in combination with trigger On Bar Open.", (Object[])new Object[0]) + "<br>" + L.t((String)"This is not allowed, it would lead to incorrect backtests (looking into future). Shift for this condition was changed to 1.", (Object[])new Object[0]);
    private int reason;

    public BadStrategyException(int n) {
        this.reason = n;
    }

    public int getReason() {
        return this.reason;
    }

    public static String getReasonAsString(int n) {
        switch (n) {
            case 1: {
                return L.t((String)"Automatic filter", (Object[])new Object[0]) + ": " + TxtShortReasonNoTrades;
            }
            case 4: {
                return L.t((String)"Automatic filter", (Object[])new Object[0]) + ": " + TxtShortReasonZeroPLTrades;
            }
            case 8: {
                return L.t((String)"Automatic filter", (Object[])new Object[0]) + ": " + TxtShortReasonTooShortTrades;
            }
            case 16: {
                return L.t((String)"Automatic filter", (Object[])new Object[0]) + ": " + TxtShortReasonZeroDurationTrades;
            }
            case 32: {
                return L.t((String)"Automatic filter", (Object[])new Object[0]) + ": " + TxtShortReasonTooManyOpenTrades;
            }
            case 64: {
                return L.t((String)"Automatic filter", (Object[])new Object[0]) + ": " + TxtShortReasonTooLongTrade;
            }
            case 256: {
                return L.t((String)"Automatic filter", (Object[])new Object[0]) + ": " + TxtShortReasonNoFilledTrades;
            }
            case 2: {
                return L.t((String)"Automatic filter", (Object[])new Object[0]) + ": " + TxtShortReasonTooLittleTrades;
            }
            case 512: {
                return L.t((String)"Automatic filter", (Object[])new Object[0]) + ": " + TxtShortReasonOutlierTrade;
            }
            case 1024: {
                return L.t((String)"Automatic filter", (Object[])new Object[0]) + ": " + TxtShortReasonAmbiguousTrades;
            }
            case 10000: {
                return TxtShortReasonThreshold;
            }
            case 10001: {
                return TxtShortReasonBacktestException;
            }
            case 10004: {
                return TxtReasonCrossCheckException;
            }
            case 10002: {
                return TxtShortReasonStopped;
            }
            case 10003: {
                return TxtShortReasonExceptionEvaluatingConditions;
            }
            case 10005: {
                return TxtShortReasonInitialPopulation;
            }
            case 10006: {
                return TxtShortReasonStrategyTooSimilar;
            }
            case 10007: {
                return TxtShortReplacedWithBetterStrategy;
            }
            case 10014: {
                return TxtCorrelationWithExistingPortfolio;
            }
            case 10015: {
                return TxtPortfolioMasterCorrelationLimitation;
            }
            case 10016: {
                return TxtPortfolioMasterSectorLimitation;
            }
            case 10017: {
                return TxtStrategyRequireXreservedBars;
            }
            case 10008: {
                return TxtShortOptProfileProfitableOptimizations;
            }
            case 10009: {
                return TxtShortOptProfileAvgProfit;
            }
            case 10010: {
                return TxtShortOptProfileUniformDistribution;
            }
            case 10011: {
                return TxtShortOptProfileBestOptimizationProfit;
            }
            case 10012: {
                return TxtShorAdditionalMarketsFilter;
            }
            case 10013: {
                return TxtShortReasonWrongParamsException;
            }
            case 10030: {
                return TxtReasonCCExceptionMCManipulation;
            }
            case 10031: {
                return TxtReasonCCExceptionMCRetest;
            }
            case 10032: {
                return TxtReasonCCExceptionOptProfileSPP;
            }
            case 10033: {
                return TxtReasonCCExceptionAddMarkets;
            }
            case 10034: {
                return TxtReasonCCExceptionWFMatrix;
            }
            case 10035: {
                return TxtReasonCCExceptionWFOptim;
            }
            case 10036: {
                return TxtReasonCCExceptionHigherBacktestPrecis;
            }
            case 10039: {
                return TxtReasonCCExceptionSequentialOptimization;
            }
            case 10038: {
                return TxtReasonCustomAnalysisFilter;
            }
            case 2048: {
                return TxtLongReasonStockpickerShiftChanged;
            }
        }
        if (n >= 100000 && n < 200000) {
            return L.t((String)"initial condition: %d", (Object[])new Object[]{n - 100000});
        }
        if (n >= 200000 && n < 300000) {
            return L.t((String)"condition: %d", (Object[])new Object[]{n - 200000});
        }
        if (n >= 300000) {
            return L.t((String)"cross check condition: %d", (Object[])new Object[]{n - 300000});
        }
        return String.format("%s: %d", ExplanationUnknown, n);
    }

    public static boolean isBadStrategyException(int n) {
        switch (n) {
            case 1: 
            case 2: 
            case 4: 
            case 8: 
            case 16: 
            case 32: 
            case 64: 
            case 256: 
            case 512: 
            case 1024: {
                return true;
            }
        }
        return false;
    }

    public String getReasonAsString() {
        return BadStrategyException.getReasonAsString(this.reason);
    }

    public static boolean check(int n, int n2) {
        return (n & n2) != 0;
    }

    public static int setOrThrow(int n, boolean bl, int n2) throws BadStrategyException {
        if ((n & n2) != 0) {
            throw new BadStrategyException(n2);
        }
        return n2;
    }

    public static String getExplanation(int n) {
        switch (n) {
            case 1: {
                return TxtLongReasonNoTrades;
            }
            case 4: {
                return TxtLongReasonZeroPLTrades;
            }
            case 8: {
                return TxtLongReasonTooShortTrades;
            }
            case 16: {
                return TxtLongReasonZeroDurationTrades;
            }
            case 32: {
                return TxtLongReasonTooManyOpenTrades;
            }
            case 64: {
                return TxtLongReasonTooLongTrade;
            }
            case 256: {
                return TxtLongReasonNoFilledTrades;
            }
            case 2: {
                return TxtLongReasonTooLittleTrades;
            }
            case 512: {
                return TxtLongReasonOutlierTrade;
            }
            case 1024: {
                return TxtLongReasonAmbiguousTrades;
            }
            case 10005: {
                return TxtLongReasonInitialPopulation;
            }
            case 10006: {
                return TxtLongReasonStrategyTooSimilar;
            }
            case 10007: {
                return TxtLongReplacedWithBetterStrategy;
            }
            case 10014: {
                return TxtCorrelationWithExistingPortfolio;
            }
            case 10015: {
                return TxtPortfolioMasterCorrelationLimitation;
            }
            case 10016: {
                return TxtPortfolioMasterSectorLimitation;
            }
            case 10008: {
                return TxtLongOptProfileProfitableOptimizations;
            }
            case 10009: {
                return TxtLongOptProfileAvgProfit;
            }
            case 10010: {
                return TxtLongOptProfileUniformDistribution;
            }
            case 10011: {
                return TxtLongOptProfileBestOptimizationProfit;
            }
            case 10012: {
                return TxtLongAdditionalMarketsFilter;
            }
            case 10030: {
                return TxtReasonCCExceptionMCManipulation;
            }
            case 10031: {
                return TxtReasonCCExceptionMCRetest;
            }
            case 10032: {
                return TxtReasonCCExceptionOptProfileSPP;
            }
            case 10033: {
                return TxtReasonCCExceptionAddMarkets;
            }
            case 10034: {
                return TxtReasonCCExceptionWFMatrix;
            }
            case 10035: {
                return TxtReasonCCExceptionWFOptim;
            }
            case 10036: {
                return TxtReasonCCExceptionHigherBacktestPrecis;
            }
            case 10039: {
                return TxtReasonCCExceptionSequentialOptimization;
            }
            case 10038: {
                return TxtReasonCustomAnalysisFilter;
            }
            case 2048: {
                return TxtLongReasonStockpickerShiftChanged;
            }
        }
        return ExplanationUnknown;
    }

    public static String reasonToShortText(int n) {
        switch (n) {
            case 1: {
                return TxtShortReasonNoTrades;
            }
            case 4: {
                return TxtShortReasonZeroPLTrades;
            }
            case 8: {
                return TxtShortReasonTooShortTrades;
            }
            case 16: {
                return TxtShortReasonZeroDurationTrades;
            }
            case 32: {
                return TxtShortReasonTooManyOpenTrades;
            }
            case 64: {
                return TxtShortReasonTooLongTrade;
            }
            case 256: {
                return TxtShortReasonNoFilledTrades;
            }
            case 2: {
                return TxtShortReasonTooLittleTrades;
            }
            case 512: {
                return TxtShortReasonOutlierTrade;
            }
            case 1024: {
                return TxtShortReasonAmbiguousTrades;
            }
        }
        return ExplanationUnknown;
    }

    public static IntArrayList getSubReasons(int n) {
        IntArrayList intArrayList = new IntArrayList();
        if (n < 10000) {
            if ((n & 1) > 0) {
                intArrayList.add(1);
            }
            if ((n & 2) > 0) {
                intArrayList.add(2);
            }
            if ((n & 4) > 0) {
                intArrayList.add(4);
            }
            if ((n & 8) > 0) {
                intArrayList.add(8);
            }
            if ((n & 0x10) > 0) {
                intArrayList.add(16);
            }
            if ((n & 0x20) > 0) {
                intArrayList.add(32);
            }
            if ((n & 0x40) > 0) {
                intArrayList.add(64);
            }
            if ((n & 0x100) > 0) {
                intArrayList.add(256);
            }
            if ((n & 0x200) > 0) {
                intArrayList.add(512);
            }
            if ((n & 0x400) > 0) {
                intArrayList.add(1024);
            }
        } else {
            intArrayList.add(n);
        }
        return intArrayList;
    }

    public static ArrayList<StrategyProblem> listProblems() {
        ArrayList<StrategyProblem> arrayList = new ArrayList<StrategyProblem>();
        arrayList.add(new StrategyProblem(1, TxtShortReasonNoTrades, TxtLongReasonNoTrades));
        arrayList.add(new StrategyProblem(4, TxtShortReasonZeroPLTrades, TxtLongReasonZeroPLTrades));
        arrayList.add(new StrategyProblem(1024, TxtShortReasonAmbiguousTrades, TxtLongReasonAmbiguousTrades));
        arrayList.add(new StrategyProblem(16, TxtShortReasonZeroDurationTrades, TxtLongReasonZeroDurationTrades));
        arrayList.add(new StrategyProblem(32, TxtShortReasonTooManyOpenTrades, TxtLongReasonTooManyOpenTrades));
        arrayList.add(new StrategyProblem(64, TxtShortReasonTooLongTrade, TxtLongReasonTooLongTrade));
        arrayList.add(new StrategyProblem(256, TxtShortReasonNoFilledTrades, TxtLongReasonNoFilledTrades));
        arrayList.add(new StrategyProblem(2, TxtShortReasonTooLittleTrades, TxtLongReasonTooLittleTrades));
        arrayList.add(new StrategyProblem(512, TxtShortReasonOutlierTrade, TxtLongReasonOutlierTrade));
        arrayList.add(new StrategyProblem(8, TxtShortReasonTooShortTrades, TxtLongReasonTooShortTrades));
        return arrayList;
    }

    public static int getFirstReason(int n) {
        if ((n & 1) > 0) {
            return 1;
        }
        if ((n & 2) > 0) {
            return 2;
        }
        if ((n & 4) > 0) {
            return 4;
        }
        if ((n & 8) > 0) {
            return 8;
        }
        if ((n & 0x10) > 0) {
            return 16;
        }
        if ((n & 0x20) > 0) {
            return 32;
        }
        if ((n & 0x40) > 0) {
            return 64;
        }
        if ((n & 0x100) > 0) {
            return 256;
        }
        if ((n & 0x200) > 0) {
            return 512;
        }
        if ((n & 0x400) > 0) {
            return 1024;
        }
        return 0;
    }

    public static int getFirstReason(int n, int n2) {
        if ((n & 1) > 0 && (n2 & 1) > 0) {
            return 1;
        }
        if ((n & 2) > 0 && (n2 & 2) > 0) {
            return 2;
        }
        if ((n & 4) > 0 && (n2 & 4) > 0) {
            return 4;
        }
        if ((n & 8) > 0 && (n2 & 8) > 0) {
            return 8;
        }
        if ((n & 0x10) > 0 && (n2 & 0x10) > 0) {
            return 16;
        }
        if ((n & 0x20) > 0 && (n2 & 0x20) > 0) {
            return 32;
        }
        if ((n & 0x40) > 0 && (n2 & 0x40) > 0) {
            return 64;
        }
        if ((n & 0x100) > 0 && (n2 & 0x100) > 0) {
            return 256;
        }
        if ((n & 0x200) > 0 && (n2 & 0x200) > 0) {
            return 512;
        }
        if ((n & 0x400) > 0 && (n2 & 0x400) > 0) {
            return 1024;
        }
        return 0;
    }

    public String getMessage() {
        return BadStrategyException.getReasonAsString(this.reason);
    }
}

