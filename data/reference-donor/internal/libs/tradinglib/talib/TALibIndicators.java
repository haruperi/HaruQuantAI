/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  com.strategyquant.datalib.TradingException
 *  com.strategyquant.lib.SettingsMap
 *  com.tictactec.ta.lib.Core
 *  com.tictactec.ta.lib.MAType
 *  com.tictactec.ta.lib.MInteger
 *  com.tictactec.ta.lib.RetCode
 *  it.unimi.dsi.fastutil.longs.Long2ObjectOpenHashMap
 *  org.slf4j.Logger
 *  org.slf4j.LoggerFactory
 */
package com.strategyquant.tradinglib.talib;

import com.strategyquant.datalib.TradingException;
import com.strategyquant.lib.SettingsMap;
import com.strategyquant.tradinglib.StrategyBase;
import com.strategyquant.tradinglib.engine.stockpicker.backtester.BacktestData;
import com.strategyquant.tradinglib.engine.stockpicker.data.symbols.LoadedSymbolData;
import com.strategyquant.tradinglib.engine.stockpicker.data.utils.PickerDataUtils;
import com.strategyquant.tradinglib.talib.TALibCustomIndicator;
import com.strategyquant.tradinglib.talib.TALibCustomIndicatorsList;
import com.strategyquant.tradinglib.talib.TALibIndicatorsCache;
import com.tictactec.ta.lib.Core;
import com.tictactec.ta.lib.MAType;
import com.tictactec.ta.lib.MInteger;
import com.tictactec.ta.lib.RetCode;
import it.unimi.dsi.fastutil.longs.Long2ObjectOpenHashMap;
import java.util.Set;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

public class TALibIndicators {
    private static final Logger Log = LoggerFactory.getLogger(TALibIndicators.class);
    private static final String PERIOD_IDENTIFIER = "period";
    private static final Set<String> HLC_INDICATORS = Set.of("AD", "ADX", "DX", "ADOSC", "ADXR", "BOP", "CDL3BLACKCROWS", "CCI", "CDL2CROWS", "ATR", "AROON", "AVGPRICE", "AROONOSC", "CDLRISEFALL3METHODS", "CDLXSIDEGAP3METHODS", "CDLGAPSIDESIDEWHITE", "CDLCONCEALBABYSWALL", "CDLDOJI", "CDLDRAGONFLYDOJI", "CDLEVENINGSTAR", "CDLDOJISTAR", "CDLGRAVESTONEDOJI", "CDLENGULFING", "CDLCOUNTERATTACK", "CDLEVENINGDOJISTAR", "CDLHAMMER", "CDLHANGINGMAN", "CDLHARAMI", "CDLDARKCLOUDCOVER", "CDL3WHITESOLDIERS", "CDL3OUTSIDE", "CDLBREAKAWAY", "CDL3LINESTRIKE", "CDL3STARSINSOUTH", "CDL3INSIDE", "CDLABANDONEDBABY", "CDLCLOSINGMARUBOZU", "CDLBELTHOLD", "CDLADVANCEBLOCK", "CDLMATCHINGLOW", "CDLLONGLINE", "CDLMORNINGDOJISTAR", "CDLONNECK", "CDLPIERCING", "CDLMATHOLD", "CDLMORNINGSTAR", "CDLSEPARATINGLINES", "CDLLONGLEGGEDDOJI", "CDLMARUBOZU", "CDLRICKSHAWMAN", "CDLSHOOTINGSTAR", "CDLHARAMICROSS", "CDLLADDERBOTTOM", "CDLHIGHWAVE", "CDLHIKKAKEMOD", "CDLKICKING", "CDLKICKINGBYLENGTH", "CDLINNECK", "CDLIDENTICAL3CROWS", "CDLHIKKAKE", "CDLINVERTEDHAMMER", "CDLHOMINGPIGEON", "CDLTHRUSTING", "CDLTAKURI", "CDLSTICKSANDWICH", "CDLTASUKIGAP", "CDLSTALLEDPATTERN", "CDLSPINNINGTOP", "CDLUPSIDEGAP2CROWS", "CDLTRISTAR", "CDLUNIQUE3RIVER", "CDLSHORTLINE", "STOCHF", "STOCH", "MINUS_DM", "MIDPRICE", "MEDPRICE", "MFI", "MINUS_DI", "NATR", "PLUS_DI", "PLUS_DM", "SAR", "SAREXT", "TRANGE", "TYPPRICE", "ULTOSC", "WCLPRICE", "WILLR");
    public static final int ValueNotDefined = -1;
    private Core core = new Core();
    public float[] o = null;
    public float[] h;
    public float[] l;
    public float[] c;
    public float[] v;
    public float[] m;
    public float[] t;
    public float[] w;
    private TALibIndicatorsCache cache = new TALibIndicatorsCache();

    public static boolean isHlcIndicator(String string) {
        return HLC_INDICATORS.contains(string);
    }

    public static boolean isPeriod(String string) {
        return string.toLowerCase().contains(PERIOD_IDENTIFIER);
    }

    public Long2ObjectOpenHashMap<Object[]> getIndicatorHashes() {
        return this.cache.getIndicatorHashes();
    }

    public float[][] getIndicatorValue(long l) {
        return this.cache.get(l);
    }

    public float[][] calculate(String string, SettingsMap settingsMap, StrategyBase strategyBase, int n, int n2, String string2) throws TradingException {
        String string3 = this.getSymbol(strategyBase, settingsMap);
        long l = this.cache.getHash(string3, string, settingsMap);
        if (!this.cache.containsKey(l)) {
            int n3 = settingsMap.getInt("Chart");
            int n4 = settingsMap.getInt("ComputedFrom");
            this.loadOHLC(strategyBase, n3, string3, n4);
            this.calculate(string3, string, settingsMap, strategyBase, n3, n, n4, n2, string2);
        }
        float[][] fArray = this.cache.get(l);
        return fArray;
    }

    public float[][] calculate(String string, String string2, SettingsMap settingsMap, StrategyBase strategyBase, int n, int n2, int n3, int n4, String string3) throws TradingException {
        long l = this.cache.getHash(string, string2, settingsMap);
        if (!this.cache.containsKey(l)) {
            this.loadOHLC(strategyBase, n, string, n3);
            this.calculate(l, n3, string2, string, settingsMap, strategyBase, n2, n4, string3);
        }
        float[][] fArray = this.cache.get(l);
        return fArray;
    }

    private String getSymbol(StrategyBase strategyBase, SettingsMap settingsMap) {
        if (strategyBase == null) {
            return "NA";
        }
        int n = settingsMap.getInt("Chart");
        BacktestData backtestData = strategyBase.Stockpicker.data;
        return backtestData.getSymbol(n);
    }

    private MAType getMAType(int n) {
        MAType[] mATypeArray = MAType.values();
        return mATypeArray[n];
    }

    private void calculate(long l, int n, String string, String string2, SettingsMap settingsMap, StrategyBase strategyBase, int n2, int n3, String string3) throws TradingException {
        float[] fArray;
        float[][] fArray2 = null;
        float[] fArray3 = fArray = this.computedFrom(strategyBase, settingsMap, n, n2);
        double[][] dArray = null;
        boolean[] blArray = null;
        int[][] nArray = null;
        MInteger mInteger = new MInteger();
        MInteger mInteger2 = new MInteger();
        int n4 = 0;
        int n5 = this.o.length - 1;
        RetCode retCode = null;
        switch (string) {
            case "ADD": {
                dArray = new double[1][this.o.length];
                blArray = new boolean[]{true};
                retCode = this.core.add(n4, n5, fArray, fArray3, mInteger, mInteger2, dArray[0]);
                break;
            }
            case "SIN": {
                dArray = new double[1][this.o.length];
                blArray = new boolean[]{true};
                retCode = this.core.sin(n4, n5, fArray, mInteger, mInteger2, dArray[0]);
                break;
            }
            case "COS": {
                dArray = new double[1][this.o.length];
                blArray = new boolean[]{true};
                retCode = this.core.cos(n4, n5, fArray, mInteger, mInteger2, dArray[0]);
                break;
            }
            case "TAN": {
                dArray = new double[1][this.o.length];
                blArray = new boolean[]{true};
                retCode = this.core.tan(n4, n5, fArray, mInteger, mInteger2, dArray[0]);
                break;
            }
            case "SQRT": {
                dArray = new double[1][this.o.length];
                blArray = new boolean[]{true};
                retCode = this.core.sqrt(n4, n5, fArray, mInteger, mInteger2, dArray[0]);
                break;
            }
            case "LOG10": {
                dArray = new double[1][this.o.length];
                blArray = new boolean[]{true};
                retCode = this.core.log10(n4, n5, fArray, mInteger, mInteger2, dArray[0]);
                break;
            }
            case "EXP": {
                dArray = new double[1][this.o.length];
                blArray = new boolean[]{true};
                retCode = this.core.exp(n4, n5, fArray, mInteger, mInteger2, dArray[0]);
                break;
            }
            case "MIN": {
                dArray = new double[1][this.o.length];
                blArray = new boolean[]{true};
                retCode = this.core.min(n4, n5, fArray, settingsMap.getInt("TimePeriod"), mInteger, mInteger2, dArray[0]);
                break;
            }
            case "MAX": {
                dArray = new double[1][this.o.length];
                blArray = new boolean[]{true};
                retCode = this.core.max(n4, n5, fArray, settingsMap.getInt("TimePeriod"), mInteger, mInteger2, dArray[0]);
                break;
            }
            case "FLOOR": {
                dArray = new double[1][this.o.length];
                blArray = new boolean[]{true};
                retCode = this.core.floor(n4, n5, fArray, mInteger, mInteger2, dArray[0]);
                break;
            }
            case "CEIL": {
                dArray = new double[1][this.o.length];
                blArray = new boolean[]{true};
                retCode = this.core.ceil(n4, n5, fArray, mInteger, mInteger2, dArray[0]);
                break;
            }
            case "AD": {
                dArray = new double[1][this.o.length];
                blArray = new boolean[]{true};
                retCode = this.core.ad(n4, n5, this.h, this.l, this.c, this.v, mInteger, mInteger2, dArray[0]);
                break;
            }
            case "SUM": {
                dArray = new double[1][this.o.length];
                blArray = new boolean[]{true};
                retCode = this.core.sum(n4, n5, fArray, settingsMap.getInt("TimePeriod"), mInteger, mInteger2, dArray[0]);
                break;
            }
            case "ASIN": {
                dArray = new double[1][this.o.length];
                blArray = new boolean[]{true};
                retCode = this.core.asin(n4, n5, fArray, mInteger, mInteger2, dArray[0]);
                break;
            }
            case "ACOS": {
                dArray = new double[1][this.o.length];
                blArray = new boolean[]{true};
                retCode = this.core.acos(n4, n5, fArray, mInteger, mInteger2, dArray[0]);
                break;
            }
            case "ATAN": {
                dArray = new double[1][this.o.length];
                blArray = new boolean[]{true};
                retCode = this.core.atan(n4, n5, fArray, mInteger, mInteger2, dArray[0]);
                break;
            }
            case "SINH": {
                dArray = new double[1][this.o.length];
                blArray = new boolean[]{true};
                retCode = this.core.sinh(n4, n5, fArray, mInteger, mInteger2, dArray[0]);
                break;
            }
            case "COSH": {
                dArray = new double[1][this.o.length];
                blArray = new boolean[]{true};
                retCode = this.core.cosh(n4, n5, fArray, mInteger, mInteger2, dArray[0]);
                break;
            }
            case "TANH": {
                dArray = new double[1][this.o.length];
                blArray = new boolean[]{true};
                retCode = this.core.tanh(n4, n5, fArray, mInteger, mInteger2, dArray[0]);
                break;
            }
            case "LN": {
                dArray = new double[1][this.o.length];
                blArray = new boolean[]{true};
                retCode = this.core.ln(n4, n5, fArray, mInteger, mInteger2, dArray[0]);
                break;
            }
            case "SUB": {
                dArray = new double[1][this.o.length];
                blArray = new boolean[]{true};
                retCode = this.core.sub(n4, n5, fArray, fArray3, mInteger, mInteger2, dArray[0]);
                break;
            }
            case "T3": {
                dArray = new double[1][this.o.length];
                blArray = new boolean[]{true};
                retCode = this.core.t3(n4, n5, fArray, settingsMap.getInt("TimePeriod"), settingsMap.getDouble("VFactor"), mInteger, mInteger2, dArray[0]);
                break;
            }
            case "MULT": {
                dArray = new double[1][this.o.length];
                blArray = new boolean[]{true};
                retCode = this.core.mult(n4, n5, fArray, fArray3, mInteger, mInteger2, dArray[0]);
                break;
            }
            case "DIV": {
                dArray = new double[1][this.o.length];
                blArray = new boolean[]{true};
                retCode = this.core.div(n4, n5, fArray, fArray3, mInteger, mInteger2, dArray[0]);
                break;
            }
            case "EMA": {
                dArray = new double[1][this.o.length];
                blArray = new boolean[]{true};
                retCode = this.core.ema(n4, n5, fArray, settingsMap.getInt("TimePeriod"), mInteger, mInteger2, dArray[0]);
                break;
            }
            case "TSF": {
                dArray = new double[1][this.o.length];
                blArray = new boolean[]{true};
                retCode = this.core.tsf(n4, n5, fArray, settingsMap.getInt("TimePeriod"), mInteger, mInteger2, dArray[0]);
                break;
            }
            case "ADX": {
                dArray = new double[1][this.o.length];
                blArray = new boolean[]{true};
                retCode = this.core.adx(n4, n5, this.h, this.l, this.c, settingsMap.getInt("TimePeriod"), mInteger, mInteger2, dArray[0]);
                break;
            }
            case "MOM": {
                dArray = new double[1][this.o.length];
                blArray = new boolean[]{true};
                retCode = this.core.mom(n4, n5, fArray, settingsMap.getInt("TimePeriod"), mInteger, mInteger2, dArray[0]);
                break;
            }
            case "SMA": {
                dArray = new double[1][this.o.length];
                blArray = new boolean[]{true};
                retCode = this.core.sma(n4, n5, fArray, settingsMap.getInt("TimePeriod"), mInteger, mInteger2, dArray[0]);
                break;
            }
            case "DX": {
                dArray = new double[1][this.o.length];
                blArray = new boolean[]{true};
                retCode = this.core.dx(n4, n5, this.h, this.l, this.c, settingsMap.getInt("TimePeriod"), mInteger, mInteger2, dArray[0]);
                break;
            }
            case "ADOSC": {
                dArray = new double[1][this.o.length];
                blArray = new boolean[]{true};
                retCode = this.core.adOsc(n4, n5, this.h, this.l, this.c, this.v, this.getMin(settingsMap.getInt("FastPeriod"), settingsMap.getInt("SlowPeriod")), this.getMax(settingsMap.getInt("SlowPeriod"), settingsMap.getInt("FastPeriod")), mInteger, mInteger2, dArray[0]);
                break;
            }
            case "ADXR": {
                dArray = new double[1][this.o.length];
                blArray = new boolean[]{true};
                retCode = this.core.adxr(n4, n5, this.h, this.l, this.c, settingsMap.getInt("TimePeriod"), mInteger, mInteger2, dArray[0]);
                break;
            }
            case "APO": {
                dArray = new double[1][this.o.length];
                blArray = new boolean[]{true};
                retCode = this.core.apo(n4, n5, fArray, this.getMin(settingsMap.getInt("FastPeriod"), settingsMap.getInt("SlowPeriod")), this.getMax(settingsMap.getInt("SlowPeriod"), settingsMap.getInt("FastPeriod")), this.getMAType(settingsMap.getInt("MAType")), mInteger, mInteger2, dArray[0]);
                break;
            }
            case "AROONOSC": {
                dArray = new double[1][this.o.length];
                blArray = new boolean[]{true};
                retCode = this.core.aroonOsc(n4, n5, this.h, this.l, settingsMap.getInt("TimePeriod"), mInteger, mInteger2, dArray[0]);
                break;
            }
            case "AROON": {
                dArray = new double[2][this.o.length];
                blArray = new boolean[]{true, true};
                retCode = this.core.aroon(n4, n5, this.h, this.l, settingsMap.getInt("TimePeriod"), mInteger, mInteger2, dArray[0], dArray[1]);
                break;
            }
            case "ATR": {
                dArray = new double[1][this.o.length];
                blArray = new boolean[]{true};
                retCode = this.core.atr(n4, n5, this.h, this.l, this.c, settingsMap.getInt("TimePeriod"), mInteger, mInteger2, dArray[0]);
                break;
            }
            case "AVGPRICE": {
                dArray = new double[1][this.o.length];
                blArray = new boolean[]{true};
                retCode = this.core.avgPrice(n4, n5, this.o, this.h, this.l, this.c, mInteger, mInteger2, dArray[0]);
                break;
            }
            case "BBANDS": {
                dArray = new double[3][this.o.length];
                blArray = new boolean[]{true, true, true};
                retCode = this.core.bbands(n4, n5, fArray, settingsMap.getInt("TimePeriod"), settingsMap.getDouble("NbDevUp"), settingsMap.getDouble("NbDevDn"), this.getMAType(settingsMap.getInt("MAType")), mInteger, mInteger2, dArray[0], dArray[1], dArray[2]);
                break;
            }
            case "CCI": {
                dArray = new double[1][this.o.length];
                blArray = new boolean[]{true};
                retCode = this.core.cci(n4, n5, this.h, this.l, this.c, settingsMap.getInt("TimePeriod"), mInteger, mInteger2, dArray[0]);
                break;
            }
            case "BETA": {
                dArray = new double[1][this.o.length];
                blArray = new boolean[]{true};
                retCode = this.core.beta(n4, n5, fArray, fArray3, settingsMap.getInt("TimePeriod"), mInteger, mInteger2, dArray[0]);
                break;
            }
            case "BOP": {
                dArray = new double[1][this.o.length];
                blArray = new boolean[]{true};
                retCode = this.core.bop(n4, n5, this.o, this.h, this.l, this.c, mInteger, mInteger2, dArray[0]);
                break;
            }
            case "CDLCONCEALBABYSWALL": {
                nArray = new int[1][this.o.length];
                blArray = new boolean[]{false};
                retCode = this.core.cdlConcealBabysWall(n4, n5, this.o, this.h, this.l, this.c, mInteger, mInteger2, nArray[0]);
                break;
            }
            case "CDLGAPSIDESIDEWHITE": {
                nArray = new int[1][this.o.length];
                blArray = new boolean[]{false};
                retCode = this.core.cdlGapSideSideWhite(n4, n5, this.o, this.h, this.l, this.c, mInteger, mInteger2, nArray[0]);
                break;
            }
            case "CDLADVANCEBLOCK": {
                nArray = new int[1][this.o.length];
                blArray = new boolean[]{false};
                retCode = this.core.cdlAdvanceBlock(n4, n5, this.o, this.h, this.l, this.c, mInteger, mInteger2, nArray[0]);
                break;
            }
            case "CDLBELTHOLD": {
                nArray = new int[1][this.o.length];
                blArray = new boolean[]{false};
                retCode = this.core.cdlBeltHold(n4, n5, this.o, this.h, this.l, this.c, mInteger, mInteger2, nArray[0]);
                break;
            }
            case "CDL3LINESTRIKE": {
                nArray = new int[1][this.o.length];
                blArray = new boolean[]{false};
                retCode = this.core.cdl3LineStrike(n4, n5, this.o, this.h, this.l, this.c, mInteger, mInteger2, nArray[0]);
                break;
            }
            case "CDL2CROWS": {
                nArray = new int[1][this.o.length];
                blArray = new boolean[]{false};
                retCode = this.core.cdl2Crows(n4, n5, this.o, this.h, this.l, this.c, mInteger, mInteger2, nArray[0]);
                break;
            }
            case "CDL3WHITESOLDIERS": {
                nArray = new int[1][this.o.length];
                blArray = new boolean[]{false};
                retCode = this.core.cdl3WhiteSoldiers(n4, n5, this.o, this.h, this.l, this.c, mInteger, mInteger2, nArray[0]);
                break;
            }
            case "CDL3BLACKCROWS": {
                nArray = new int[1][this.o.length];
                blArray = new boolean[]{false};
                retCode = this.core.cdl3BlackCrows(n4, n5, this.o, this.h, this.l, this.c, mInteger, mInteger2, nArray[0]);
                break;
            }
            case "CDL3INSIDE": {
                nArray = new int[1][this.o.length];
                blArray = new boolean[]{false};
                retCode = this.core.cdl3Inside(n4, n5, this.o, this.h, this.l, this.c, mInteger, mInteger2, nArray[0]);
                break;
            }
            case "CDL3STARSINSOUTH": {
                nArray = new int[1][this.o.length];
                blArray = new boolean[]{false};
                retCode = this.core.cdl3StarsInSouth(n4, n5, this.o, this.h, this.l, this.c, mInteger, mInteger2, nArray[0]);
                break;
            }
            case "CDLABANDONEDBABY": {
                nArray = new int[1][this.o.length];
                blArray = new boolean[]{false};
                retCode = this.core.cdlAbandonedBaby(n4, n5, this.o, this.h, this.l, this.c, settingsMap.getDouble("Penetration"), mInteger, mInteger2, nArray[0]);
                break;
            }
            case "CDL3OUTSIDE": {
                nArray = new int[1][this.o.length];
                blArray = new boolean[]{false};
                retCode = this.core.cdl3Outside(n4, n5, this.o, this.h, this.l, this.c, mInteger, mInteger2, nArray[0]);
                break;
            }
            case "CDLENGULFING": {
                nArray = new int[1][this.o.length];
                blArray = new boolean[]{false};
                retCode = this.core.cdlEngulfing(n4, n5, this.o, this.h, this.l, this.c, mInteger, mInteger2, nArray[0]);
                break;
            }
            case "CDLCOUNTERATTACK": {
                nArray = new int[1][this.o.length];
                blArray = new boolean[]{false};
                retCode = this.core.cdlCounterAttack(n4, n5, this.o, this.h, this.l, this.c, mInteger, mInteger2, nArray[0]);
                break;
            }
            case "CDLDOJI": {
                nArray = new int[1][this.o.length];
                blArray = new boolean[]{false};
                retCode = this.core.cdlDoji(n4, n5, this.o, this.h, this.l, this.c, mInteger, mInteger2, nArray[0]);
                break;
            }
            case "CDLEVENINGDOJISTAR": {
                nArray = new int[1][this.o.length];
                blArray = new boolean[]{false};
                retCode = this.core.cdlEveningDojiStar(n4, n5, this.o, this.h, this.l, this.c, settingsMap.getDouble("Penetration"), mInteger, mInteger2, nArray[0]);
                break;
            }
            case "CDLCLOSINGMARUBOZU": {
                nArray = new int[1][this.o.length];
                blArray = new boolean[]{false};
                retCode = this.core.cdlClosingMarubozu(n4, n5, this.o, this.h, this.l, this.c, mInteger, mInteger2, nArray[0]);
                break;
            }
            case "CDLBREAKAWAY": {
                nArray = new int[1][this.o.length];
                blArray = new boolean[]{false};
                retCode = this.core.cdlBreakaway(n4, n5, this.o, this.h, this.l, this.c, mInteger, mInteger2, nArray[0]);
                break;
            }
            case "CDLDOJISTAR": {
                nArray = new int[1][this.o.length];
                blArray = new boolean[]{false};
                retCode = this.core.cdlDojiStar(n4, n5, this.o, this.h, this.l, this.c, mInteger, mInteger2, nArray[0]);
                break;
            }
            case "CDLEVENINGSTAR": {
                nArray = new int[1][this.o.length];
                blArray = new boolean[]{false};
                retCode = this.core.cdlEveningStar(n4, n5, this.o, this.h, this.l, this.c, settingsMap.getDouble("Penetration"), mInteger, mInteger2, nArray[0]);
                break;
            }
            case "CDLDARKCLOUDCOVER": {
                nArray = new int[1][this.o.length];
                blArray = new boolean[]{false};
                retCode = this.core.cdlDarkCloudCover(n4, n5, this.o, this.h, this.l, this.c, settingsMap.getDouble("Penetration"), mInteger, mInteger2, nArray[0]);
                break;
            }
            case "CDLDRAGONFLYDOJI": {
                nArray = new int[1][this.o.length];
                blArray = new boolean[]{false};
                retCode = this.core.cdlDragonflyDoji(n4, n5, this.o, this.h, this.l, this.c, mInteger, mInteger2, nArray[0]);
                break;
            }
            case "CDLHIGHWAVE": {
                nArray = new int[1][this.o.length];
                blArray = new boolean[]{false};
                retCode = this.core.cdlHignWave(n4, n5, this.o, this.h, this.l, this.c, mInteger, mInteger2, nArray[0]);
                break;
            }
            case "CDLHIKKAKEMOD": {
                nArray = new int[1][this.o.length];
                blArray = new boolean[]{false};
                retCode = this.core.cdlHikkakeMod(n4, n5, this.o, this.h, this.l, this.c, mInteger, mInteger2, nArray[0]);
                break;
            }
            case "CDLHAMMER": {
                nArray = new int[1][this.o.length];
                blArray = new boolean[]{false};
                retCode = this.core.cdlHammer(n4, n5, this.o, this.h, this.l, this.c, mInteger, mInteger2, nArray[0]);
                break;
            }
            case "CDLHANGINGMAN": {
                nArray = new int[1][this.o.length];
                blArray = new boolean[]{false};
                retCode = this.core.cdlHangingMan(n4, n5, this.o, this.h, this.l, this.c, mInteger, mInteger2, nArray[0]);
                break;
            }
            case "CDLHIKKAKE": {
                nArray = new int[1][this.o.length];
                blArray = new boolean[]{false};
                retCode = this.core.cdlHikkake(n4, n5, this.o, this.h, this.l, this.c, mInteger, mInteger2, nArray[0]);
                break;
            }
            case "CDLIDENTICAL3CROWS": {
                nArray = new int[1][this.o.length];
                blArray = new boolean[]{false};
                retCode = this.core.cdlIdentical3Crows(n4, n5, this.o, this.h, this.l, this.c, mInteger, mInteger2, nArray[0]);
                break;
            }
            case "CDLINVERTEDHAMMER": {
                nArray = new int[1][this.o.length];
                blArray = new boolean[]{false};
                retCode = this.core.cdlInvertedHammer(n4, n5, this.o, this.h, this.l, this.c, mInteger, mInteger2, nArray[0]);
                break;
            }
            case "CDLINNECK": {
                nArray = new int[1][this.o.length];
                blArray = new boolean[]{false};
                retCode = this.core.cdlInNeck(n4, n5, this.o, this.h, this.l, this.c, mInteger, mInteger2, nArray[0]);
                break;
            }
            case "CDLHARAMI": {
                nArray = new int[1][this.o.length];
                blArray = new boolean[]{false};
                retCode = this.core.cdlHarami(n4, n5, this.o, this.h, this.l, this.c, mInteger, mInteger2, nArray[0]);
                break;
            }
            case "CDLHOMINGPIGEON": {
                nArray = new int[1][this.o.length];
                blArray = new boolean[]{false};
                retCode = this.core.cdlHomingPigeon(n4, n5, this.o, this.h, this.l, this.c, mInteger, mInteger2, nArray[0]);
                break;
            }
            case "CDLGRAVESTONEDOJI": {
                nArray = new int[1][this.o.length];
                blArray = new boolean[]{false};
                retCode = this.core.cdlGravestoneDoji(n4, n5, this.o, this.h, this.l, this.c, mInteger, mInteger2, nArray[0]);
                break;
            }
            case "CDLHARAMICROSS": {
                nArray = new int[1][this.o.length];
                blArray = new boolean[]{false};
                retCode = this.core.cdlHaramiCross(n4, n5, this.o, this.h, this.l, this.c, mInteger, mInteger2, nArray[0]);
                break;
            }
            case "CDLRISEFALL3METHODS": {
                nArray = new int[1][this.o.length];
                blArray = new boolean[]{false};
                retCode = this.core.cdlRiseFall3Methods(n4, n5, this.o, this.h, this.l, this.c, mInteger, mInteger2, nArray[0]);
                break;
            }
            case "CDLMORNINGSTAR": {
                nArray = new int[1][this.o.length];
                blArray = new boolean[]{false};
                retCode = this.core.cdlMorningStar(n4, n5, this.o, this.h, this.l, this.c, settingsMap.getDouble("Penetration"), mInteger, mInteger2, nArray[0]);
                break;
            }
            case "CDLLONGLINE": {
                nArray = new int[1][this.o.length];
                blArray = new boolean[]{false};
                retCode = this.core.cdlLongLine(n4, n5, this.o, this.h, this.l, this.c, mInteger, mInteger2, nArray[0]);
                break;
            }
            case "CDLLADDERBOTTOM": {
                nArray = new int[1][this.o.length];
                blArray = new boolean[]{false};
                retCode = this.core.cdlLadderBottom(n4, n5, this.o, this.h, this.l, this.c, mInteger, mInteger2, nArray[0]);
                break;
            }
            case "CDLLONGLEGGEDDOJI": {
                nArray = new int[1][this.o.length];
                blArray = new boolean[]{false};
                retCode = this.core.cdlLongLeggedDoji(n4, n5, this.o, this.h, this.l, this.c, mInteger, mInteger2, nArray[0]);
                break;
            }
            case "CDLMATHOLD": {
                nArray = new int[1][this.o.length];
                blArray = new boolean[]{false};
                retCode = this.core.cdlMatHold(n4, n5, this.o, this.h, this.l, this.c, settingsMap.getDouble("Penetration"), mInteger, mInteger2, nArray[0]);
                break;
            }
            case "CDLONNECK": {
                nArray = new int[1][this.o.length];
                blArray = new boolean[]{false};
                retCode = this.core.cdlOnNeck(n4, n5, this.o, this.h, this.l, this.c, mInteger, mInteger2, nArray[0]);
                break;
            }
            case "CDLMARUBOZU": {
                nArray = new int[1][this.o.length];
                blArray = new boolean[]{false};
                retCode = this.core.cdlMarubozu(n4, n5, this.o, this.h, this.l, this.c, mInteger, mInteger2, nArray[0]);
                break;
            }
            case "CDLMORNINGDOJISTAR": {
                nArray = new int[1][this.o.length];
                blArray = new boolean[]{false};
                retCode = this.core.cdlMorningDojiStar(n4, n5, this.o, this.h, this.l, this.c, settingsMap.getDouble("Penetration"), mInteger, mInteger2, nArray[0]);
                break;
            }
            case "CDLKICKINGBYLENGTH": {
                nArray = new int[1][this.o.length];
                blArray = new boolean[]{false};
                retCode = this.core.cdlKickingByLength(n4, n5, this.o, this.h, this.l, this.c, mInteger, mInteger2, nArray[0]);
                break;
            }
            case "CDLMATCHINGLOW": {
                nArray = new int[1][this.o.length];
                blArray = new boolean[]{false};
                retCode = this.core.cdlMatchingLow(n4, n5, this.o, this.h, this.l, this.c, mInteger, mInteger2, nArray[0]);
                break;
            }
            case "CDLKICKING": {
                nArray = new int[1][this.o.length];
                blArray = new boolean[]{false};
                retCode = this.core.cdlKicking(n4, n5, this.o, this.h, this.l, this.c, mInteger, mInteger2, nArray[0]);
                break;
            }
            case "CDLSHOOTINGSTAR": {
                nArray = new int[1][this.o.length];
                blArray = new boolean[]{false};
                retCode = this.core.cdlShootingStar(n4, n5, this.o, this.h, this.l, this.c, mInteger, mInteger2, nArray[0]);
                break;
            }
            case "CDLSHORTLINE": {
                nArray = new int[1][this.o.length];
                blArray = new boolean[]{false};
                retCode = this.core.cdlShortLine(n4, n5, this.o, this.h, this.l, this.c, mInteger, mInteger2, nArray[0]);
                break;
            }
            case "CDLSEPARATINGLINES": {
                nArray = new int[1][this.o.length];
                blArray = new boolean[]{false};
                retCode = this.core.cdlSeperatingLines(n4, n5, this.o, this.h, this.l, this.c, mInteger, mInteger2, nArray[0]);
                break;
            }
            case "CDLSPINNINGTOP": {
                nArray = new int[1][this.o.length];
                blArray = new boolean[]{false};
                retCode = this.core.cdlSpinningTop(n4, n5, this.o, this.h, this.l, this.c, mInteger, mInteger2, nArray[0]);
                break;
            }
            case "CDLTASUKIGAP": {
                nArray = new int[1][this.o.length];
                blArray = new boolean[]{false};
                retCode = this.core.cdlTasukiGap(n4, n5, this.o, this.h, this.l, this.c, mInteger, mInteger2, nArray[0]);
                break;
            }
            case "CDLSTALLEDPATTERN": {
                nArray = new int[1][this.o.length];
                blArray = new boolean[]{false};
                retCode = this.core.cdlStalledPattern(n4, n5, this.o, this.h, this.l, this.c, mInteger, mInteger2, nArray[0]);
                break;
            }
            case "CDLRICKSHAWMAN": {
                nArray = new int[1][this.o.length];
                blArray = new boolean[]{false};
                retCode = this.core.cdlRickshawMan(n4, n5, this.o, this.h, this.l, this.c, mInteger, mInteger2, nArray[0]);
                break;
            }
            case "CDLSTICKSANDWICH": {
                nArray = new int[1][this.o.length];
                blArray = new boolean[]{false};
                retCode = this.core.cdlStickSandwhich(n4, n5, this.o, this.h, this.l, this.c, mInteger, mInteger2, nArray[0]);
                break;
            }
            case "CDLTRISTAR": {
                nArray = new int[1][this.o.length];
                blArray = new boolean[]{false};
                retCode = this.core.cdlTristar(n4, n5, this.o, this.h, this.l, this.c, mInteger, mInteger2, nArray[0]);
                break;
            }
            case "CDLTAKURI": {
                nArray = new int[1][this.o.length];
                blArray = new boolean[]{false};
                retCode = this.core.cdlTakuri(n4, n5, this.o, this.h, this.l, this.c, mInteger, mInteger2, nArray[0]);
                break;
            }
            case "CDLTHRUSTING": {
                nArray = new int[1][this.o.length];
                blArray = new boolean[]{false};
                retCode = this.core.cdlThrusting(n4, n5, this.o, this.h, this.l, this.c, mInteger, mInteger2, nArray[0]);
                break;
            }
            case "CDLPIERCING": {
                nArray = new int[1][this.o.length];
                blArray = new boolean[]{false};
                retCode = this.core.cdlPiercing(n4, n5, this.o, this.h, this.l, this.c, mInteger, mInteger2, nArray[0]);
                break;
            }
            case "CDLXSIDEGAP3METHODS": {
                nArray = new int[1][this.o.length];
                blArray = new boolean[]{false};
                retCode = this.core.cdlXSideGap3Methods(n4, n5, this.o, this.h, this.l, this.c, mInteger, mInteger2, nArray[0]);
                break;
            }
            case "CDLUNIQUE3RIVER": {
                nArray = new int[1][this.o.length];
                blArray = new boolean[]{false};
                retCode = this.core.cdlUnique3River(n4, n5, this.o, this.h, this.l, this.c, mInteger, mInteger2, nArray[0]);
                break;
            }
            case "CDLUPSIDEGAP2CROWS": {
                nArray = new int[1][this.o.length];
                blArray = new boolean[]{false};
                retCode = this.core.cdlUpsideGap2Crows(n4, n5, this.o, this.h, this.l, this.c, mInteger, mInteger2, nArray[0]);
                break;
            }
            case "HT_DCPHASE": {
                dArray = new double[1][this.o.length];
                blArray = new boolean[]{true};
                retCode = this.core.htDcPhase(n4, n5, fArray, mInteger, mInteger2, dArray[0]);
                break;
            }
            case "DEMA": {
                dArray = new double[1][this.o.length];
                blArray = new boolean[]{true};
                retCode = this.core.dema(n4, n5, fArray, settingsMap.getInt("TimePeriod"), mInteger, mInteger2, dArray[0]);
                break;
            }
            case "CMO": {
                dArray = new double[1][this.o.length];
                blArray = new boolean[]{true};
                retCode = this.core.cmo(n4, n5, fArray, settingsMap.getInt("TimePeriod"), mInteger, mInteger2, dArray[0]);
                break;
            }
            case "HT_DCPERIOD": {
                dArray = new double[1][this.o.length];
                blArray = new boolean[]{true};
                retCode = this.core.htDcPeriod(n4, n5, fArray, mInteger, mInteger2, dArray[0]);
                break;
            }
            case "CORREL": {
                dArray = new double[1][this.o.length];
                blArray = new boolean[]{true};
                retCode = this.core.correl(n4, n5, fArray, fArray3, settingsMap.getInt("TimePeriod"), mInteger, mInteger2, dArray[0]);
                break;
            }
            case "HT_TRENDMODE": {
                nArray = new int[1][this.o.length];
                blArray = new boolean[]{false};
                retCode = this.core.htTrendMode(n4, n5, fArray, mInteger, mInteger2, nArray[0]);
                break;
            }
            case "LINEARREG_ANGLE": {
                dArray = new double[1][this.o.length];
                blArray = new boolean[]{true};
                retCode = this.core.linearRegAngle(n4, n5, fArray, settingsMap.getInt("TimePeriod"), mInteger, mInteger2, dArray[0]);
                break;
            }
            case "LINEARREG": {
                dArray = new double[1][this.o.length];
                blArray = new boolean[]{true};
                retCode = this.core.linearReg(n4, n5, fArray, settingsMap.getInt("TimePeriod"), mInteger, mInteger2, dArray[0]);
                break;
            }
            case "LINEARREG_SLOPE": {
                dArray = new double[1][this.o.length];
                blArray = new boolean[]{true};
                retCode = this.core.linearRegSlope(n4, n5, fArray, settingsMap.getInt("TimePeriod"), mInteger, mInteger2, dArray[0]);
                break;
            }
            case "HT_TRENDLINE": {
                dArray = new double[1][this.o.length];
                blArray = new boolean[]{true};
                retCode = this.core.htTrendline(n4, n5, fArray, mInteger, mInteger2, dArray[0]);
                break;
            }
            case "HT_SINE": {
                dArray = new double[2][this.o.length];
                blArray = new boolean[]{true, true};
                retCode = this.core.htSine(n4, n5, fArray, mInteger, mInteger2, dArray[0], dArray[1]);
                break;
            }
            case "HT_PHASOR": {
                dArray = new double[2][this.o.length];
                blArray = new boolean[]{true, true};
                retCode = this.core.htPhasor(n4, n5, fArray, mInteger, mInteger2, dArray[0], dArray[1]);
                break;
            }
            case "KAMA": {
                dArray = new double[1][this.o.length];
                blArray = new boolean[]{true};
                retCode = this.core.kama(n4, n5, fArray, settingsMap.getInt("TimePeriod"), mInteger, mInteger2, dArray[0]);
                break;
            }
            case "LINEARREG_INTERCEPT": {
                dArray = new double[1][this.o.length];
                blArray = new boolean[]{true};
                retCode = this.core.linearRegIntercept(n4, n5, fArray, settingsMap.getInt("TimePeriod"), mInteger, mInteger2, dArray[0]);
                break;
            }
            case "MIDPRICE": {
                dArray = new double[1][this.o.length];
                blArray = new boolean[]{true};
                retCode = this.core.midPrice(n4, n5, this.h, this.l, settingsMap.getInt("TimePeriod"), mInteger, mInteger2, dArray[0]);
                break;
            }
            case "MEDPRICE": {
                dArray = new double[1][this.o.length];
                blArray = new boolean[]{true};
                retCode = this.core.medPrice(n4, n5, this.h, this.l, mInteger, mInteger2, dArray[0]);
                break;
            }
            case "MAXINDEX": {
                nArray = new int[1][this.o.length];
                blArray = new boolean[]{false};
                retCode = this.core.maxIndex(n4, n5, fArray, settingsMap.getInt("TimePeriod"), mInteger, mInteger2, nArray[0]);
                break;
            }
            case "MIDPOINT": {
                dArray = new double[1][this.o.length];
                blArray = new boolean[]{true};
                retCode = this.core.midPoint(n4, n5, fArray, settingsMap.getInt("TimePeriod"), mInteger, mInteger2, dArray[0]);
                break;
            }
            case "MININDEX": {
                nArray = new int[1][this.o.length];
                blArray = new boolean[]{false};
                retCode = this.core.minIndex(n4, n5, fArray, settingsMap.getInt("TimePeriod"), mInteger, mInteger2, nArray[0]);
                break;
            }
            case "MFI": {
                dArray = new double[1][this.o.length];
                blArray = new boolean[]{true};
                retCode = this.core.mfi(n4, n5, this.h, this.l, this.c, this.v, settingsMap.getInt("TimePeriod"), mInteger, mInteger2, dArray[0]);
                break;
            }
            case "MINMAX": {
                dArray = new double[2][this.o.length];
                blArray = new boolean[]{true, true};
                retCode = this.core.minMax(n4, n5, fArray, settingsMap.getInt("TimePeriod"), mInteger, mInteger2, dArray[0], dArray[1]);
                break;
            }
            case "MACDFIX": {
                dArray = new double[3][this.o.length];
                blArray = new boolean[]{true, true, true};
                retCode = this.core.macdFix(n4, n5, fArray, settingsMap.getInt("SignalPeriod"), mInteger, mInteger2, dArray[0], dArray[1], dArray[2]);
                break;
            }
            case "MACDEXT": {
                dArray = new double[3][this.o.length];
                blArray = new boolean[]{true, true, true};
                retCode = this.core.macdExt(n4, n5, fArray, this.getMin(settingsMap.getInt("FastPeriod"), settingsMap.getInt("SlowPeriod")), this.getMAType(settingsMap.getInt("FastMAType")), this.getMax(settingsMap.getInt("SlowPeriod"), settingsMap.getInt("FastPeriod")), this.getMAType(settingsMap.getInt("SlowMAType")), settingsMap.getInt("SignalPeriod"), this.getMAType(settingsMap.getInt("SignalMAType")), mInteger, mInteger2, dArray[0], dArray[1], dArray[2]);
                break;
            }
            case "MACD": {
                dArray = new double[3][this.o.length];
                blArray = new boolean[]{true, true, true};
                retCode = this.core.macd(n4, n5, fArray, this.getMin(settingsMap.getInt("FastPeriod"), settingsMap.getInt("SlowPeriod")), this.getMax(settingsMap.getInt("SlowPeriod"), settingsMap.getInt("FastPeriod")), settingsMap.getInt("SignalPeriod"), mInteger, mInteger2, dArray[0], dArray[1], dArray[2]);
                break;
            }
            case "MA": {
                dArray = new double[1][this.o.length];
                blArray = new boolean[]{true};
                retCode = this.core.movingAverage(n4, n5, fArray, settingsMap.getInt("TimePeriod"), this.getMAType(settingsMap.getInt("MAType")), mInteger, mInteger2, dArray[0]);
                break;
            }
            case "MAMA": {
                dArray = new double[2][this.o.length];
                blArray = new boolean[]{true, true};
                retCode = this.core.mama(n4, n5, fArray, settingsMap.getDouble("FastLimit"), settingsMap.getDouble("SlowLimit"), mInteger, mInteger2, dArray[0], dArray[1]);
                break;
            }
            case "MAVP": {
                dArray = new double[1][this.o.length];
                blArray = new boolean[]{true};
                retCode = this.core.movingAverageVariablePeriod(n4, n5, fArray, this.o, this.getMin(settingsMap.getInt("MinPeriod"), settingsMap.getInt("MaxPeriod")), this.getMax(settingsMap.getInt("MaxPeriod"), settingsMap.getInt("MinPeriod")), this.getMAType(settingsMap.getInt("MAType")), mInteger, mInteger2, dArray[0]);
                break;
            }
            case "MINMAXINDEX": {
                nArray = new int[2][this.o.length];
                blArray = new boolean[]{false, false};
                retCode = this.core.minMaxIndex(n4, n5, fArray, settingsMap.getInt("TimePeriod"), mInteger, mInteger2, nArray[0], nArray[1]);
                break;
            }
            case "OBV": {
                dArray = new double[1][this.o.length];
                blArray = new boolean[]{true};
                retCode = this.core.obv(n4, n5, fArray, this.v, mInteger, mInteger2, dArray[0]);
                break;
            }
            case "MINUS_DM": {
                dArray = new double[1][this.o.length];
                blArray = new boolean[]{true};
                retCode = this.core.minusDM(n4, n5, this.h, this.l, settingsMap.getInt("TimePeriod"), mInteger, mInteger2, dArray[0]);
                break;
            }
            case "PLUS_DI": {
                dArray = new double[1][this.o.length];
                blArray = new boolean[]{true};
                retCode = this.core.plusDI(n4, n5, this.h, this.l, this.c, settingsMap.getInt("TimePeriod"), mInteger, mInteger2, dArray[0]);
                break;
            }
            case "NATR": {
                dArray = new double[1][this.o.length];
                blArray = new boolean[]{true};
                retCode = this.core.natr(n4, n5, this.h, this.l, this.c, settingsMap.getInt("TimePeriod"), mInteger, mInteger2, dArray[0]);
                break;
            }
            case "MINUS_DI": {
                dArray = new double[1][this.o.length];
                blArray = new boolean[]{true};
                retCode = this.core.minusDI(n4, n5, this.h, this.l, this.c, settingsMap.getInt("TimePeriod"), mInteger, mInteger2, dArray[0]);
                break;
            }
            case "PLUS_DM": {
                dArray = new double[1][this.o.length];
                blArray = new boolean[]{true};
                retCode = this.core.plusDM(n4, n5, this.h, this.l, settingsMap.getInt("TimePeriod"), mInteger, mInteger2, dArray[0]);
                break;
            }
            case "PPO": {
                dArray = new double[1][this.o.length];
                blArray = new boolean[]{true};
                retCode = this.core.ppo(n4, n5, fArray, this.getMin(settingsMap.getInt("FastPeriod"), settingsMap.getInt("SlowPeriod")), this.getMax(settingsMap.getInt("SlowPeriod"), settingsMap.getInt("FastPeriod")), this.getMAType(settingsMap.getInt("MAType")), mInteger, mInteger2, dArray[0]);
                break;
            }
            case "ROCP": {
                dArray = new double[1][this.o.length];
                blArray = new boolean[]{true};
                retCode = this.core.rocP(n4, n5, fArray, settingsMap.getInt("TimePeriod"), mInteger, mInteger2, dArray[0]);
                break;
            }
            case "SAR": {
                dArray = new double[1][this.o.length];
                blArray = new boolean[]{true};
                retCode = this.core.sar(n4, n5, this.h, this.l, settingsMap.getDouble("Acceleration"), settingsMap.getDouble("Maximum"), mInteger, mInteger2, dArray[0]);
                break;
            }
            case "SAREXT": {
                dArray = new double[1][this.o.length];
                blArray = new boolean[]{true};
                retCode = this.core.sarExt(n4, n5, this.h, this.l, settingsMap.getDouble("StartValue"), settingsMap.getDouble("OffsetOnReverse"), settingsMap.getDouble("AccelerationInitLong"), settingsMap.getDouble("AccelerationLong"), settingsMap.getDouble("AccelerationMaxLong"), settingsMap.getDouble("AccelerationInitShort"), settingsMap.getDouble("AccelerationShort"), settingsMap.getDouble("AccelerationMaxShort"), mInteger, mInteger2, dArray[0]);
                break;
            }
            case "ROC": {
                dArray = new double[1][this.o.length];
                blArray = new boolean[]{true};
                retCode = this.core.roc(n4, n5, fArray, settingsMap.getInt("TimePeriod"), mInteger, mInteger2, dArray[0]);
                break;
            }
            case "ROCR100": {
                dArray = new double[1][this.o.length];
                blArray = new boolean[]{true};
                retCode = this.core.rocR100(n4, n5, fArray, settingsMap.getInt("TimePeriod"), mInteger, mInteger2, dArray[0]);
                break;
            }
            case "RSI": {
                dArray = new double[1][this.o.length];
                blArray = new boolean[]{true};
                retCode = this.core.rsi(n4, n5, fArray, settingsMap.getInt("TimePeriod"), mInteger, mInteger2, dArray[0]);
                break;
            }
            case "ROCR": {
                dArray = new double[1][this.o.length];
                blArray = new boolean[]{true};
                retCode = this.core.rocR(n4, n5, fArray, settingsMap.getInt("TimePeriod"), mInteger, mInteger2, dArray[0]);
                break;
            }
            case "STOCHRSI": {
                dArray = new double[2][this.o.length];
                blArray = new boolean[]{true, true};
                retCode = this.core.stochRsi(n4, n5, fArray, settingsMap.getInt("TimePeriod"), settingsMap.getInt("FastK_Period"), settingsMap.getInt("FastD_Period"), this.getMAType(settingsMap.getInt("FastD_MAType")), mInteger, mInteger2, dArray[0], dArray[1]);
                break;
            }
            case "STOCHF": {
                dArray = new double[2][this.o.length];
                blArray = new boolean[]{true, true};
                retCode = this.core.stochF(n4, n5, this.h, this.l, this.c, settingsMap.getInt("FastK_Period"), settingsMap.getInt("FastD_Period"), this.getMAType(settingsMap.getInt("FastD_MAType")), mInteger, mInteger2, dArray[0], dArray[1]);
                break;
            }
            case "TEMA": {
                dArray = new double[1][this.o.length];
                blArray = new boolean[]{true};
                retCode = this.core.tema(n4, n5, fArray, settingsMap.getInt("TimePeriod"), mInteger, mInteger2, dArray[0]);
                break;
            }
            case "TRANGE": {
                dArray = new double[1][this.o.length];
                blArray = new boolean[]{true};
                retCode = this.core.trueRange(n4, n5, this.h, this.l, this.c, mInteger, mInteger2, dArray[0]);
                break;
            }
            case "STOCH": {
                dArray = new double[2][this.o.length];
                blArray = new boolean[]{true, true};
                retCode = this.core.stoch(n4, n5, this.h, this.l, this.c, settingsMap.getInt("FastK_Period"), settingsMap.getInt("SlowK_Period"), this.getMAType(settingsMap.getInt("SlowK_MAType")), settingsMap.getInt("SlowD_Period"), this.getMAType(settingsMap.getInt("SlowD_MAType")), mInteger, mInteger2, dArray[0], dArray[1]);
                break;
            }
            case "STDDEV": {
                dArray = new double[1][this.o.length];
                blArray = new boolean[]{true};
                retCode = this.core.stdDev(n4, n5, fArray, settingsMap.getInt("TimePeriod"), settingsMap.getDouble("NbDev"), mInteger, mInteger2, dArray[0]);
                break;
            }
            case "VAR": {
                dArray = new double[1][this.o.length];
                blArray = new boolean[]{true};
                retCode = this.core.variance(n4, n5, fArray, settingsMap.getInt("TimePeriod"), settingsMap.getDouble("NbDev"), mInteger, mInteger2, dArray[0]);
                break;
            }
            case "TRIMA": {
                dArray = new double[1][this.o.length];
                blArray = new boolean[]{true};
                retCode = this.core.trima(n4, n5, fArray, settingsMap.getInt("TimePeriod"), mInteger, mInteger2, dArray[0]);
                break;
            }
            case "WCLPRICE": {
                dArray = new double[1][this.o.length];
                blArray = new boolean[]{true};
                retCode = this.core.wclPrice(n4, n5, this.h, this.l, this.c, mInteger, mInteger2, dArray[0]);
                break;
            }
            case "TYPPRICE": {
                dArray = new double[1][this.o.length];
                blArray = new boolean[]{true};
                retCode = this.core.typPrice(n4, n5, this.h, this.l, this.c, mInteger, mInteger2, dArray[0]);
                break;
            }
            case "WILLR": {
                dArray = new double[1][this.o.length];
                blArray = new boolean[]{true};
                retCode = this.core.willR(n4, n5, this.h, this.l, this.c, settingsMap.getInt("TimePeriod"), mInteger, mInteger2, dArray[0]);
                break;
            }
            case "WMA": {
                dArray = new double[1][this.o.length];
                blArray = new boolean[]{true};
                retCode = this.core.wma(n4, n5, fArray, settingsMap.getInt("TimePeriod"), mInteger, mInteger2, dArray[0]);
                break;
            }
            case "TRIX": {
                dArray = new double[1][this.o.length];
                blArray = new boolean[]{true};
                retCode = this.core.trix(n4, n5, fArray, settingsMap.getInt("TimePeriod"), mInteger, mInteger2, dArray[0]);
                break;
            }
            case "ULTOSC": {
                dArray = new double[1][this.o.length];
                blArray = new boolean[]{true};
                retCode = this.core.ultOsc(n4, n5, this.h, this.l, this.c, settingsMap.getInt("TimePeriod1"), settingsMap.getInt("TimePeriod2"), settingsMap.getInt("TimePeriod3"), mInteger, mInteger2, dArray[0]);
                break;
            }
            default: {
                TALibCustomIndicator tALibCustomIndicator = null;
                try {
                    tALibCustomIndicator = (TALibCustomIndicator)TALibCustomIndicatorsList.getInstance().findClassByName(string);
                }
                catch (Exception exception) {
                    throw new TradingException(String.format("Indicator '%s' not implemented.", string));
                }
                try {
                    tALibCustomIndicator.init(settingsMap, strategyBase, this.o, this.h, this.l, this.c, this.v, fArray, fArray3);
                    fArray2 = tALibCustomIndicator.calculate();
                    this.cache.put(string2, string, l, fArray2, n2, n3, string3, settingsMap);
                    break;
                }
                catch (Exception exception) {
                    throw new TradingException(String.format("Error while calculating TALibCustomIndicator '%s'. %s", string, exception.getMessage()));
                }
            }
        }
        if (retCode != null) {
            if (retCode != RetCode.Success) {
                throw new TradingException(String.format("Error while calculating indicator '%s'. %s", string, retCode.toString()));
            }
            if (blArray != null) {
                int n6 = 0;
                int n7 = 0;
                fArray2 = new float[blArray.length][this.o.length];
                int n8 = 0;
                for (boolean bl : blArray) {
                    for (int i = mInteger.value; i < mInteger.value + mInteger2.value; ++i) {
                        fArray2[n8][i] = bl ? (float)dArray[n6][i - mInteger.value] : (float)nArray[n7][i - mInteger.value];
                    }
                    if (bl) {
                        ++n6;
                    } else {
                        ++n7;
                    }
                    ++n8;
                }
                this.cache.put(string2, string, l, fArray2, n2, n3, string3, settingsMap);
            }
        }
        this.o = null;
        this.h = null;
        this.l = null;
        this.c = null;
        this.v = null;
        this.m = null;
        this.t = null;
        this.w = null;
        fArray = null;
        fArray3 = null;
        dArray = null;
        nArray = null;
        blArray = null;
    }

    private int getMin(int n, int n2) {
        return n < n2 ? n : n2;
    }

    private int getMax(int n, int n2) {
        return n > n2 ? n : n2;
    }

    private float[] computedFrom(StrategyBase strategyBase, SettingsMap settingsMap, int n, int n2) throws TradingException {
        if (n == -1) {
            return null;
        }
        switch (n) {
            case 0: {
                return this.c;
            }
            case 1: {
                return this.o;
            }
            case 2: {
                return this.h;
            }
            case 3: {
                return this.l;
            }
            case 4: {
                return this.m;
            }
            case 5: {
                return this.t;
            }
            case 6: {
                return this.w;
            }
            case 7: {
                return this.v;
            }
        }
        throw new TradingException("Invalid ComputedFrom definition, unrecognized value " + n);
    }

    private void loadOHLC(StrategyBase strategyBase, int n, String string, int n2) {
        String string2;
        if (strategyBase == null) {
            return;
        }
        BacktestData backtestData = strategyBase.Stockpicker.data;
        LoadedSymbolData loadedSymbolData = backtestData.getChartSymbolData(n, string);
        switch (string2 = backtestData.getChartTimeframe(n)) {
            case "D1": {
                this.o = loadedSymbolData.OpenD;
                this.h = loadedSymbolData.HighD;
                this.l = loadedSymbolData.LowD;
                this.c = loadedSymbolData.CloseD;
                this.v = loadedSymbolData.VolumeD;
                if (n2 == 4) {
                    this.m = this.calculateMedianValues(loadedSymbolData.OpenD, loadedSymbolData.HighD, loadedSymbolData.LowD, loadedSymbolData.CloseD);
                }
                if (n2 == 5) {
                    this.t = this.calculateTypicalValues(loadedSymbolData.OpenD, loadedSymbolData.HighD, loadedSymbolData.LowD, loadedSymbolData.CloseD);
                }
                if (n2 != 6) break;
                this.w = this.calculateWeightedValues(loadedSymbolData.OpenD, loadedSymbolData.HighD, loadedSymbolData.LowD, loadedSymbolData.CloseD);
                break;
            }
            case "Weekly": {
                this.o = loadedSymbolData.OpenW;
                this.h = loadedSymbolData.HighW;
                this.l = loadedSymbolData.LowW;
                this.c = loadedSymbolData.CloseW;
                this.v = loadedSymbolData.VolumeW;
                if (n2 == 4) {
                    this.m = this.calculateMedianValues(loadedSymbolData.OpenW, loadedSymbolData.HighW, loadedSymbolData.LowW, loadedSymbolData.CloseW);
                }
                if (n2 == 5) {
                    this.t = this.calculateTypicalValues(loadedSymbolData.OpenW, loadedSymbolData.HighW, loadedSymbolData.LowW, loadedSymbolData.CloseW);
                }
                if (n2 != 6) break;
                this.w = this.calculateWeightedValues(loadedSymbolData.OpenW, loadedSymbolData.HighW, loadedSymbolData.LowW, loadedSymbolData.CloseW);
                break;
            }
            case "Monthly": {
                this.o = loadedSymbolData.OpenM;
                this.h = loadedSymbolData.HighM;
                this.l = loadedSymbolData.LowM;
                this.c = loadedSymbolData.CloseM;
                this.v = loadedSymbolData.VolumeM;
                if (n2 == 4) {
                    this.m = this.calculateMedianValues(loadedSymbolData.OpenM, loadedSymbolData.HighM, loadedSymbolData.LowM, loadedSymbolData.CloseM);
                }
                if (n2 == 5) {
                    this.t = this.calculateTypicalValues(loadedSymbolData.OpenM, loadedSymbolData.HighM, loadedSymbolData.LowM, loadedSymbolData.CloseM);
                }
                if (n2 != 6) break;
                this.w = this.calculateWeightedValues(loadedSymbolData.OpenM, loadedSymbolData.HighM, loadedSymbolData.LowM, loadedSymbolData.CloseM);
            }
        }
    }

    private float[] calculateWeightedValues(float[] fArray, float[] fArray2, float[] fArray3, float[] fArray4) {
        float[] fArray5 = new float[fArray.length];
        for (int i = 0; i < fArray.length; ++i) {
            fArray5[i] = PickerDataUtils.computeWeightedValue(fArray[i], fArray2[i], fArray3[i], fArray4[i]);
        }
        return fArray5;
    }

    private float[] calculateTypicalValues(float[] fArray, float[] fArray2, float[] fArray3, float[] fArray4) {
        float[] fArray5 = new float[fArray.length];
        for (int i = 0; i < fArray.length; ++i) {
            fArray5[i] = PickerDataUtils.computeTypicalValue(fArray[i], fArray2[i], fArray3[i], fArray4[i]);
        }
        return fArray5;
    }

    private float[] calculateMedianValues(float[] fArray, float[] fArray2, float[] fArray3, float[] fArray4) {
        float[] fArray5 = new float[fArray.length];
        for (int i = 0; i < fArray.length; ++i) {
            fArray5[i] = PickerDataUtils.computeMedianValue(fArray[i], fArray2[i], fArray3[i], fArray4[i]);
        }
        return fArray5;
    }

    public void clear() {
        if (this.cache != null) {
            this.cache.clear();
        }
    }
}

