/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  com.strategyquant.datalib.ChartDef
 *  com.strategyquant.datalib.DataInfo
 *  com.strategyquant.datalib.data.DataManager
 *  com.strategyquant.datalib.data.io.IDataLoader
 *  com.strategyquant.datalib.data.io.VersatileData
 *  com.strategyquant.lib.SQTime
 *  com.strategyquant.lib.XMLUtil
 *  org.jdom2.Element
 *  org.slf4j.Logger
 *  org.slf4j.LoggerFactory
 */
package com.strategyquant.tradinglib;

import com.strategyquant.datalib.ChartDef;
import com.strategyquant.datalib.DataInfo;
import com.strategyquant.datalib.data.DataManager;
import com.strategyquant.datalib.data.io.IDataLoader;
import com.strategyquant.datalib.data.io.VersatileData;
import com.strategyquant.lib.SQTime;
import com.strategyquant.lib.XMLUtil;
import com.strategyquant.tradinglib.BenchmarkResult;
import com.strategyquant.tradinglib.MoneyManagementMethod;
import com.strategyquant.tradinglib.ResultsGroup;
import com.strategyquant.tradinglib.StrategyBase;
import com.strategyquant.tradinglib.project.ProjectConfigHelper;
import org.jdom2.Element;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

public class Benchmark {
    public static final Logger Log = LoggerFactory.getLogger(Benchmark.class);

    public BenchmarkResult calculate(ResultsGroup resultsGroup, long l, long l2) throws Exception {
        try {
            BenchmarkResult benchmarkResult = new BenchmarkResult();
            Element element = XMLUtil.stringToElement((String)resultsGroup.getLastSettings());
            Element element2 = element.getChild("RiskMoneyManagement");
            MoneyManagementMethod moneyManagementMethod = ProjectConfigHelper.getMoneyManagement(element2.getChild("MoneyManagement"));
            double d = moneyManagementMethod.getInitialCapital();
            double d2 = 9.9999999E7;
            double d3 = 9.9999999E7;
            double d4 = d;
            double d5 = d;
            double d6 = 0.0;
            double d7 = 0.0;
            long l3 = 0L;
            double d8 = 0.0;
            int n = 0;
            String string = "SPY_benchmark.D";
            DataInfo dataInfo = DataManager.getDataInfo((String)"History", (String)string);
            if (dataInfo == null) {
                throw new Exception("Cannot get data info for symbol " + string);
            }
            Log.info(String.format("SPY benchmark from %s to %s ...", SQTime.toDateString((long)l), SQTime.toDateString((long)l2)));
            ChartDef chartDef = new ChartDef("History", string, "D1", l, l2, 2.5, "No Session");
            IDataLoader iDataLoader = DataManager.getDataLoader((ChartDef)chartDef, (int)1, null);
            iDataLoader.open();
            while (iDataLoader.hasNextTick()) {
                VersatileData versatileData = new VersatileData();
                iDataLoader.getNextTick(versatileData);
                long l4 = versatileData.time;
                double d9 = versatileData.close;
                if (n == 0) {
                    d7 = d9;
                    l3 = l4;
                    try {
                        if (moneyManagementMethod != null) {
                            StrategyBase strategyBase = StrategyBase.createXmlStrategy(resultsGroup.getStrategyXml());
                            strategyBase.accountBalance = d;
                            strategyBase.accountEquity = d;
                            d8 = moneyManagementMethod.computeTradeSize(strategyBase, dataInfo.symbol, (byte)1, d7, 0.0, dataInfo.symbolInfo.tickSize, dataInfo.symbolInfo.pointValue);
                        } else {
                            d8 = d / d7;
                        }
                    }
                    catch (Exception exception) {
                        throw new Exception("Failed to calculate initial buy amount from MoneyManagement method - " + exception.getMessage(), exception);
                    }
                }
                d6 = (d9 - d7) * d8;
                benchmarkResult.equity.put(l4, d6);
                d5 = d + d6;
                double d10 = (float)this.specialSubtraction(d4, d5);
                double d11 = (float)this.getPercentageDD(d10, d4);
                benchmarkResult.ddMapMoney.put(SQTime.getDateInMs((long)l4), d10);
                benchmarkResult.ddMapPct.put(SQTime.getDateInMs((long)l4), d11);
                if (d11 < d2) {
                    d2 = d11;
                }
                if (d10 < d3) {
                    d3 = d10;
                }
                if (d5 > d4) {
                    d4 = d5;
                }
                ++n;
            }
            return benchmarkResult;
        }
        catch (Exception exception) {
            Log.error("Cannot calculate benchmark performance. ", (Throwable)exception);
            throw new Exception("Cannot calculate benchmark performance. ", exception);
        }
    }

    private double specialSubtraction(double d, double d2) {
        double d3 = d - d2;
        if (d3 < 0.0) {
            d3 = 0.0;
        }
        return -1.0 * d3;
    }

    private double getPercentageDD(double d, double d2) {
        if (d2 <= 0.0 || d > d2) {
            return -1.0;
        }
        return d / (d2 / 100.0);
    }
}

