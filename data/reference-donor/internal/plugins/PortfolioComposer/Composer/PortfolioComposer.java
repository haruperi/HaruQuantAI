/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  com.strategyquant.datalib.ChartDef
 *  com.strategyquant.datalib.DataInfo
 *  com.strategyquant.datalib.InstrumentInfo
 *  com.strategyquant.datalib.TradingException
 *  com.strategyquant.datalib.data.DataManager
 *  com.strategyquant.datalib.data.io.IDataLoader
 *  com.strategyquant.datalib.data.io.VersatileData
 *  com.strategyquant.lib.SQTime
 *  com.strategyquant.lib.SQUtils
 *  com.strategyquant.lib.XMLUtil
 *  com.strategyquant.tradinglib.MoneyManagementMethod
 *  com.strategyquant.tradinglib.Order
 *  com.strategyquant.tradinglib.OrderCloseTypes
 *  com.strategyquant.tradinglib.OrderTypes
 *  com.strategyquant.tradinglib.OrdersList
 *  com.strategyquant.tradinglib.PlTypes
 *  com.strategyquant.tradinglib.Result
 *  com.strategyquant.tradinglib.ResultsGroup
 *  com.strategyquant.tradinglib.StrategyBase
 *  com.strategyquant.tradinglib.TradeSizeSmallerThanOneException
 *  com.strategyquant.tradinglib.correlation.CorrelationComputer
 *  com.strategyquant.tradinglib.engine.stockpicker.Stockpicker
 *  com.strategyquant.tradinglib.moneymanagement.MoneyManagementMethodsList
 *  com.strategyquant.tradinglib.project.ProjectConfigHelper
 *  com.strategyquant.tradinglib.results.SpecialValues
 *  com.strategyquant.tradinglib.results.SymbolInfo
 *  com.strategyquant.tradinglib.results.stats.comparator.OrderComparatorByOpenTime
 *  com.strategyquant.tradinglib.results.stats.computer.OrderPLComputer
 *  it.unimi.dsi.fastutil.longs.Long2ObjectAVLTreeMap
 *  it.unimi.dsi.fastutil.longs.Long2ObjectMap$Entry
 *  it.unimi.dsi.fastutil.longs.Long2ObjectOpenHashMap
 *  it.unimi.dsi.fastutil.objects.Object2DoubleOpenHashMap
 *  it.unimi.dsi.fastutil.objects.Object2IntOpenHashMap
 *  it.unimi.dsi.fastutil.objects.Object2ObjectOpenHashMap
 *  it.unimi.dsi.fastutil.objects.ObjectArrayList
 *  it.unimi.dsi.fastutil.objects.ObjectListIterator
 *  org.apache.commons.math3.distribution.NormalDistribution
 *  org.apache.commons.math3.stat.descriptive.DescriptiveStatistics
 *  org.jdom2.Content
 *  org.jdom2.Element
 *  org.slf4j.Logger
 *  org.slf4j.LoggerFactory
 */
package com.strategyquant.plugin.Portfolio.impl.Composer;

import com.strategyquant.datalib.ChartDef;
import com.strategyquant.datalib.DataInfo;
import com.strategyquant.datalib.InstrumentInfo;
import com.strategyquant.datalib.TradingException;
import com.strategyquant.datalib.data.DataManager;
import com.strategyquant.datalib.data.io.IDataLoader;
import com.strategyquant.datalib.data.io.VersatileData;
import com.strategyquant.lib.SQTime;
import com.strategyquant.lib.SQUtils;
import com.strategyquant.lib.XMLUtil;
import com.strategyquant.plugin.Portfolio.impl.Composer.PortfolioComposerLog;
import com.strategyquant.plugin.Portfolio.impl.Composer.PortfolioComposerSettings;
import com.strategyquant.tradinglib.MoneyManagementMethod;
import com.strategyquant.tradinglib.Order;
import com.strategyquant.tradinglib.OrderCloseTypes;
import com.strategyquant.tradinglib.OrderTypes;
import com.strategyquant.tradinglib.OrdersList;
import com.strategyquant.tradinglib.PlTypes;
import com.strategyquant.tradinglib.Result;
import com.strategyquant.tradinglib.ResultsGroup;
import com.strategyquant.tradinglib.StrategyBase;
import com.strategyquant.tradinglib.TradeSizeSmallerThanOneException;
import com.strategyquant.tradinglib.correlation.CorrelationComputer;
import com.strategyquant.tradinglib.engine.stockpicker.Stockpicker;
import com.strategyquant.tradinglib.moneymanagement.MoneyManagementMethodsList;
import com.strategyquant.tradinglib.project.ProjectConfigHelper;
import com.strategyquant.tradinglib.results.SpecialValues;
import com.strategyquant.tradinglib.results.SymbolInfo;
import com.strategyquant.tradinglib.results.stats.comparator.OrderComparatorByOpenTime;
import com.strategyquant.tradinglib.results.stats.computer.OrderPLComputer;
import it.unimi.dsi.fastutil.longs.Long2ObjectAVLTreeMap;
import it.unimi.dsi.fastutil.longs.Long2ObjectMap;
import it.unimi.dsi.fastutil.longs.Long2ObjectOpenHashMap;
import it.unimi.dsi.fastutil.objects.Object2DoubleOpenHashMap;
import it.unimi.dsi.fastutil.objects.Object2IntOpenHashMap;
import it.unimi.dsi.fastutil.objects.Object2ObjectOpenHashMap;
import it.unimi.dsi.fastutil.objects.ObjectArrayList;
import it.unimi.dsi.fastutil.objects.ObjectListIterator;
import java.util.ArrayList;
import java.util.Arrays;
import java.util.Comparator;
import java.util.HashMap;
import java.util.HashSet;
import java.util.Iterator;
import java.util.Map;
import org.apache.commons.math3.distribution.NormalDistribution;
import org.apache.commons.math3.stat.descriptive.DescriptiveStatistics;
import org.jdom2.Content;
import org.jdom2.Element;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

public class PortfolioComposer {
    private static final Logger Log = LoggerFactory.getLogger(PortfolioComposer.class);
    public boolean isRunning = false;
    private boolean stopped;

    public ResultsGroup recalculate(String portfolioName, PortfolioComposerSettings settings, Double[] weights) throws Exception {
        Long2ObjectAVLTreeMap newOrdersMap = new Long2ObjectAVLTreeMap();
        Object2DoubleOpenHashMap weightStrMap = new Object2DoubleOpenHashMap();
        Object2ObjectOpenHashMap strMap = new Object2ObjectOpenHashMap();
        Object2ObjectOpenHashMap strbaseMap = new Object2ObjectOpenHashMap();
        Object2ObjectOpenHashMap mmStrMap = new Object2ObjectOpenHashMap();
        Object2IntOpenHashMap maxPosStrMap = new Object2IntOpenHashMap();
        Long2ObjectOpenHashMap orderIdMap = new Long2ObjectOpenHashMap();
        ObjectArrayList hodlResultKeys = new ObjectArrayList();
        this.stopped = false;
        try {
            MoneyManagementMethod mmMethod;
            double weight;
            StrategyBase sb;
            String name;
            double pct;
            Order order;
            OrdersList orders;
            ResultsGroup rg;
            double initialCapital = settings.initialCapital;
            int leverage = settings.leverage;
            long OrderId = 0L;
            int decimals = settings.decimals;
            long portfolioStartDate = -1L;
            long portfolioEndDate = -1L;
            int count = settings.strategies.size();
            for (int i = 0; i < count; ++i) {
                rg = settings.strategies.get(i);
                orders = rg.orders();
                for (int j = 0; j < orders.size(); ++j) {
                    order = orders.get(j);
                    order.OrderId = OrderId++;
                    if (rg.isHodlStrategy()) continue;
                    if (portfolioStartDate == -1L || order.OpenTime < portfolioStartDate) {
                        portfolioStartDate = order.OpenTime;
                    }
                    if (portfolioEndDate != -1L && order.CloseTime <= portfolioEndDate) continue;
                    portfolioEndDate = order.CloseTime;
                }
            }
            if (settings.dateRangeLimited) {
                portfolioStartDate = settings.startDay;
                portfolioEndDate = settings.endDay;
            } else {
                settings.startDay = SQTime.getDateInMs((long)portfolioStartDate);
                settings.endDay = SQTime.getDateInMs((long)portfolioEndDate);
            }
            ResultsGroup portfolio = ResultsGroup.merge(settings.strategies, (String[])new String[]{"AdditionalMarket", "CrossCheck_"}, null, (Long2ObjectOpenHashMap)orderIdMap, (ObjectArrayList)hodlResultKeys);
            portfolio.setName(portfolioName);
            portfolio.orders().clear();
            PortfolioComposerLog log = new PortfolioComposerLog(portfolioName, settings);
            long minDate = -1L;
            long maxDate = -1L;
            for (int i = 0; i < count; ++i) {
                pct = (double)i / (double)count * 100.0 / 4.0;
                if (this.stopped) break;
                rg = settings.strategies.get(i);
                name = rg.getName();
                strMap.put((Object)name, (Object)rg);
                Element elConfig = rg.getStrategyXml();
                sb = StrategyBase.createXmlStrategy((Element)elConfig);
                strbaseMap.put((Object)name, (Object)sb);
                weight = weights[i];
                weightStrMap.put((Object)name, weight);
                mmMethod = ProjectConfigHelper.getMoneyManagement((Element)XMLUtil.stringToElement((String)rg.getLastSettings()).getChild("RiskMoneyManagement").getChild("MoneyManagement"));
                if (mmMethod.getClass().getSimpleName().equals("ATRRiskBasedSizing")) {
                    throw new Exception("Strategy '" + name + "' uses ATRRiskBasedSizing MM which is not supported in Portfolio Composer.");
                }
                mmStrMap.put((Object)name, (Object)mmMethod);
                if (rg.isStockpickerStrategy()) {
                    int maxOpenPos = 1;
                    if (!rg.isHodlStrategy()) {
                        maxOpenPos = Stockpicker.getMaxOpenPosition((Element)elConfig, (int)1);
                        maxOpenPos += Stockpicker.getMaxOpenPosition((Element)elConfig, (int)-1);
                    }
                    maxPosStrMap.put((Object)name, maxOpenPos);
                }
                String hodlSymbol = rg.specialValues().getString(SpecialValues.PortfolioComposerHodlSymbol);
                orders = rg.orders();
                orders.sort((Comparator)new OrderComparatorByOpenTime());
                for (int j = 0; j < orders.size(); ++j) {
                    order = orders.get(j);
                    Order clonedOrder = new Order(order);
                    clonedOrder.StrategyName = name;
                    if (hodlSymbol != null) {
                        clonedOrder.Symbol = hodlSymbol;
                        clonedOrder.CloseType = 1;
                        this.modifyHodlOrder(clonedOrder, portfolioStartDate, portfolioEndDate);
                    }
                    long date = OrderTypes.isMarketOrder((byte)order.OriginalType) ? SQTime.getDateInMs((long)clonedOrder.OpenTime) : SQTime.getDateInMs((long)clonedOrder.OriginalOpenTime);
                    if (minDate == -1L || date < minDate) {
                        minDate = date;
                    }
                    if (maxDate == -1L || date > maxDate) {
                        maxDate = date;
                    }
                    if (!newOrdersMap.containsKey(date)) {
                        newOrdersMap.put(date, (Object)new ObjectArrayList());
                    }
                    ((ObjectArrayList)newOrdersMap.get(date)).add((Object)clonedOrder);
                }
            }
            DailyLog dailyLog = new DailyLog();
            double accountBalance = initialCapital;
            int maxOpenPositions = 1;
            double usedMargin = 0.0;
            double freeMargin = 0.0;
            if (settings.dateRangeLimited) {
                minDate = settings.startDay;
                maxDate = settings.endDay;
            }
            long daysTotal = SQTime.getDaysBetween((long)minDate, (long)maxDate);
            long dayNumber = 0L;
            long currentDate = minDate;
            Long2ObjectAVLTreeMap dailyProfitMap = new Long2ObjectAVLTreeMap();
            Long2ObjectAVLTreeMap marginUsedMap = new Long2ObjectAVLTreeMap();
            Long2ObjectAVLTreeMap dailyProfitPercentageMap = new Long2ObjectAVLTreeMap();
            Long2ObjectAVLTreeMap openTradesMap = new Long2ObjectAVLTreeMap();
            do {
                double margin;
                String orderInfo;
                double openPrice;
                InstrumentInfo instrumentInfo;
                usedMargin = this.calculateUsedMargin((Long2ObjectAVLTreeMap<ObjectArrayList<Order>>)openTradesMap, (Object2ObjectOpenHashMap<String, ResultsGroup>)strMap);
                freeMargin = accountBalance * (double)leverage - usedMargin;
                dailyLog.reset();
                dailyLog.print("\n=========================================================================================================");
                dailyLog.print(String.format("%s, Account balance: %s, Free margin: %s, Used margin %s", SQTime.toFullDateMinuteString((long)currentDate), PlTypes.printPL((double)accountBalance, (byte)10), PlTypes.printPL((double)freeMargin, (byte)10), PlTypes.printPL((double)usedMargin, (byte)10)));
                this.printOpenTrades((Long2ObjectAVLTreeMap<ObjectArrayList<Order>>)openTradesMap, dailyLog, (Object2ObjectOpenHashMap<String, ResultsGroup>)strMap, decimals);
                ObjectArrayList list = (ObjectArrayList)newOrdersMap.get(currentDate);
                if (list != null) {
                    for (int j = 0; j < list.size(); ++j) {
                        String SetupName;
                        float mmSize;
                        dailyLog.tradesModified();
                        order = (Order)list.get(j);
                        if (!orderIdMap.containsKey(order.OrderId)) continue;
                        name = order.StrategyName;
                        rg = (ResultsGroup)strMap.get((Object)name);
                        weight = weightStrMap.getDouble((Object)name);
                        mmMethod = (MoneyManagementMethod)mmStrMap.get((Object)name);
                        instrumentInfo = this.getInstrumentInfo(rg, order);
                        boolean isStockpickerStrategy = rg.isStockpickerStrategy();
                        sb = (StrategyBase)strbaseMap.get((Object)name);
                        sb.accountBalance = accountBalance;
                        sb.accountEquity = accountBalance;
                        sb.initialCapital = initialCapital;
                        sb.Symbol = order.Symbol;
                        sb.Instrument = instrumentInfo.instrument;
                        openPrice = OrderTypes.isMarketOrder((byte)order.OriginalType) ? (double)order.OpenPrice : (double)order.OriginalPrice;
                        if (openPrice == 0.0) continue;
                        try {
                            if (isStockpickerStrategy) {
                                maxOpenPositions = maxPosStrMap.getInt((Object)name);
                                mmMethod.setMaxOpenPositions((double)maxOpenPositions);
                            }
                            mmMethod.setWeight(weight / 100.0);
                            mmSize = (float)mmMethod.computeTradeSize(sb, order.Symbol, order.Type, openPrice, (double)order.StopLoss, instrumentInfo.tickSize, instrumentInfo.pointValue);
                        }
                        catch (TradeSizeSmallerThanOneException e) {
                            orderInfo = name + "/" + order.Symbol + "|OpenType=" + OrderTypes.toString((byte)order.OriginalType) + "|OpenTime=" + SQTime.toFullDateMinuteString((long)order.OpenTime) + "|OpenPrice=" + PlTypes.printPL((double)openPrice, (byte)10, (int)decimals) + "|MM=[" + mmMethod.printFormatedName() + ",Weight=" + weight + "%,MaxPos=" + maxOpenPositions + "]=0|CloseTime=" + SQTime.toFullDateMinuteString((long)order.CloseTime);
                            dailyLog.print(String.format("Order REJECTED '%s', %s (OriginalSize=%s).", orderInfo, e.getMessage(), Float.valueOf(order.Size)));
                            continue;
                        }
                        margin = this.calculateMargin(mmSize, openPrice, instrumentInfo);
                        orderInfo = isStockpickerStrategy ? name + "/" + order.Symbol + "|OpenType=" + OrderTypes.toString((byte)order.OriginalType) + "|OpenTime=" + SQTime.toFullDateMinuteString((long)order.OpenTime) + "|OpenPrice=" + PlTypes.printPL((double)openPrice, (byte)10, (int)decimals) + "|MM=[" + mmMethod.printFormatedName() + ",Weight=" + weight + "%,MaxPos=" + maxOpenPositions + "]=" + mmSize + "|CloseTime=" + SQTime.toFullDateMinuteString((long)order.CloseTime) + "|Margin=" + PlTypes.printPL((double)margin, (byte)10) : name + "/" + order.Symbol + "|OpenType=" + OrderTypes.toString((byte)order.OriginalType) + "|OpenTime=" + SQTime.toFullDateMinuteString((long)order.OpenTime) + "|OpenPrice=" + PlTypes.printPL((double)openPrice, (byte)10, (int)decimals) + "|MM=[" + mmMethod.printFormatedName() + ",Weight=" + weight + "%]=" + mmSize + "|CloseTime=" + SQTime.toFullDateMinuteString((long)order.CloseTime) + "|Margin=" + PlTypes.printPL((double)margin, (byte)10);
                        if (margin > freeMargin) {
                            dailyLog.print(String.format("Order REJECTED '%s', insufficient funds in the account. Free margin: %s", orderInfo, PlTypes.printPL((double)freeMargin, (byte)10)));
                            continue;
                        }
                        freeMargin = accountBalance * (double)leverage - (usedMargin += margin);
                        if (order.Size == mmSize) {
                            dailyLog.print(String.format("Order ACCEPTED '%s', order size not changed. Free margin: %s", orderInfo, PlTypes.printPL((double)freeMargin, (byte)10)));
                        } else {
                            dailyLog.print(String.format("Order ACCEPTED '%s', order size changed from %s to %s. Free margin: %s", orderInfo, Float.valueOf(order.Size), Float.valueOf(mmSize), PlTypes.printPL((double)freeMargin, (byte)10)));
                        }
                        order.CommSwap = order.Size != 0.0f ? (order.CommSwap *= mmSize / order.Size) : 0.0f;
                        order.Size = mmSize;
                        order.SetupName = SetupName = (String)orderIdMap.get(order.OrderId);
                        portfolio.orders().add(order);
                        PortfolioComposer.addProfit((Long2ObjectAVLTreeMap<Map<String, Double>>)dailyProfitMap, (Long2ObjectAVLTreeMap<Map<String, Double>>)marginUsedMap, (Long2ObjectAVLTreeMap<Map<String, Double>>)dailyProfitPercentageMap, currentDate, name, order.PL, accountBalance);
                        long closeTime = SQTime.getDateInMs((long)order.CloseTime);
                        if (!openTradesMap.containsKey(closeTime)) {
                            openTradesMap.put(closeTime, (Object)new ObjectArrayList());
                        }
                        ((ObjectArrayList)openTradesMap.get(closeTime)).add((Object)order);
                    }
                }
                dailyLog.print("-------------------------------------------");
                list = (ObjectArrayList)openTradesMap.get(currentDate);
                if (list != null) {
                    ObjectListIterator it = list.listIterator();
                    while (it.hasNext()) {
                        dailyLog.tradesModified();
                        order = (Order)it.next();
                        name = order.StrategyName;
                        rg = (ResultsGroup)strMap.get((Object)name);
                        instrumentInfo = this.getInstrumentInfo(rg, order);
                        double pl = order.PipsPL * order.Size * (float)(instrumentInfo.pointValue * instrumentInfo.tickSize);
                        openPrice = OrderTypes.isMarketOrder((byte)order.OriginalType) ? (double)order.OpenPrice : (double)order.OriginalPrice;
                        margin = this.calculateMargin(order.Size, openPrice, instrumentInfo);
                        freeMargin = (accountBalance += pl) * (double)leverage - (usedMargin -= margin);
                        orderInfo = name + "/" + order.Symbol + "|OpenType=" + OrderTypes.toString((byte)order.OriginalType) + "|OpenTime=" + SQTime.toFullDateMinuteString((long)order.OpenTime) + "|OpenPrice=" + PlTypes.printPL((double)order.OpenPrice, (byte)10, (int)decimals) + "|Size=" + order.Size + "|CloseTime=" + SQTime.toFullDateMinuteString((long)order.CloseTime) + "|ClosePrice=" + PlTypes.printPL((double)order.ClosePrice, (byte)10, (int)decimals) + "|CloseType=" + OrderCloseTypes.toString((byte)order.CloseType) + "|PL=" + PlTypes.printPL((double)pl, (byte)10) + "|Margin=" + PlTypes.printPL((double)margin, (byte)10);
                        dailyLog.print(String.format("Order CLOSED '%s'. Free margin: %s", orderInfo, PlTypes.printPL((double)freeMargin, (byte)10)));
                        it.remove();
                    }
                }
                if (dailyLog.tradesModified) {
                    log.printNoNewLine(dailyLog.toString());
                }
                currentDate = SQTime.addDays((long)currentDate, (int)1);
                pct = 25.0 + (double)(++dayNumber) / (double)daysTotal * 100.0 / 2.0;
            } while (!this.stopped && currentDate <= maxDate);
            dailyLog.print("-------------------------------------------");
            HashSet allStrategies = new HashSet();
            for (Map strategyProfits : dailyProfitMap.values()) {
                allStrategies.addAll(strategyProfits.keySet());
            }
            ArrayList strategyList = new ArrayList(allStrategies);
            double[] StdDeviation = new double[allStrategies.size()];
            double[] avgProfitPercentage1 = new double[allStrategies.size()];
            double[] avgProfit1 = new double[allStrategies.size()];
            double[] Var1 = new double[allStrategies.size()];
            int temp = 0;
            NormalDistribution normalDistribution = new NormalDistribution();
            double zScore = normalDistribution.inverseCumulativeProbability(settings.confidenceLevel);
            for (int i = 0; i < strategyList.size(); ++i) {
                double avgProfitPercentage;
                String strategy = (String)strategyList.get(i);
                double stdDevLastN = PortfolioComposer.calculateStandardDeviationLastNPeriods((Long2ObjectAVLTreeMap<Map<String, Double>>)dailyProfitPercentageMap, strategy, dailyProfitPercentageMap.size());
                avgProfitPercentage1[temp] = avgProfitPercentage = PortfolioComposer.getAverageProfitPercentage((Long2ObjectAVLTreeMap<Map<String, Double>>)dailyProfitPercentageMap, strategy, -1);
                double lastMarginUsed = PortfolioComposer.getLastMarginUsed((Long2ObjectAVLTreeMap<Map<String, Double>>)marginUsedMap, strategy);
                double averageMarginUsed = PortfolioComposer.getAverageMarginUsed((Long2ObjectAVLTreeMap<Map<String, Double>>)marginUsedMap, strategy);
                avgProfit1[temp] = avgProfitPercentage * averageMarginUsed;
                dailyLog.print("Strategy: " + strategy);
                dailyLog.print("Weight: " + SQUtils.d2String((double)weightStrMap.getDouble((Object)strategy), (int)2));
                dailyLog.print(" ");
                dailyLog.print("Daily expected return : " + PlTypes.printPL((double)(avgProfitPercentage * 100.0), (byte)20, (int)3));
                dailyLog.print("Daily expected return : " + PlTypes.printPL((double)(averageMarginUsed * avgProfitPercentage), (byte)10, (int)2));
                dailyLog.print(" ");
                dailyLog.print("Daily Standard Deviation return : " + PlTypes.printPL((double)(stdDevLastN * 100.0), (byte)20, (int)3));
                StdDeviation[temp] = stdDevLastN;
                dailyLog.print(" ");
                double SinglePositionVaR = -averageMarginUsed * (zScore * stdDevLastN);
                dailyLog.print("VaR (with a mean of zero): " + PlTypes.printPL((double)SinglePositionVaR, (byte)10, (int)2));
                SinglePositionVaR = averageMarginUsed * (avgProfitPercentage - zScore * stdDevLastN);
                dailyLog.print("VaR : " + PlTypes.printPL((double)SinglePositionVaR, (byte)10, (int)2));
                Var1[temp] = SinglePositionVaR;
                dailyLog.print(" ");
                dailyLog.print("Average Margin Used: " + PlTypes.printPL((double)averageMarginUsed, (byte)10, (int)2));
                dailyLog.print(" ");
                dailyLog.print(PlTypes.printPL((double)(settings.confidenceLevel * 100.0), (byte)20, (int)0) + " confidence level");
                dailyLog.print(SQUtils.d2String((double)((1.0 - settings.confidenceLevel) * 100.0), (int)0) + " days out of 100 days we can expect a loss of : " + PlTypes.printPL((double)SinglePositionVaR, (byte)10, (int)2));
                dailyLog.print("VaR with " + PlTypes.printPL((double)((1.0 - settings.confidenceLevel) * 100.0), (byte)20, (int)2) + " of the worse profitable return : " + PlTypes.printPL((double)SinglePositionVaR, (byte)10, (int)2));
                dailyLog.print(" ");
                for (String strategy2 : allStrategies) {
                    double correlation = PortfolioComposer.getCorrelation((Long2ObjectAVLTreeMap<Map<String, Double>>)dailyProfitPercentageMap, strategy, strategy2);
                    dailyLog.print("Correlation between " + strategy + " and " + strategy2 + " : " + SQUtils.d2String((double)correlation, (int)3));
                }
                dailyLog.print("----------------------------------------------------------------- ");
                dailyLog.print(" ");
                dailyLog.print(" ");
                ++temp;
            }
            double totalPart1 = 0.0;
            double totalPart2 = 0.0;
            double weight1 = 0.0;
            double weight2 = 0.0;
            double averageMarginUsed1 = 0.0;
            double avgProfitPercentage2 = 0.0;
            double avgProfit2 = 0.0;
            int strategyCount = strategyList.size();
            for (int i1 = 0; i1 < strategyList.size(); ++i1) {
                String strategy1 = (String)strategyList.get(i1);
                weight1 = weightStrMap.getDouble((Object)strategy1) / 100.0;
                totalPart1 += Math.pow(weight1, 2.0) * Math.pow(StdDeviation[i1], 2.0);
                averageMarginUsed1 += PortfolioComposer.getAverageMarginUsed((Long2ObjectAVLTreeMap<Map<String, Double>>)marginUsedMap, strategy1) * weight1;
                avgProfitPercentage2 += avgProfitPercentage1[i1] * weight1;
                avgProfit2 += avgProfit1[i1] * weight1;
                for (int i2 = i1 + 1; i2 < strategyList.size(); ++i2) {
                    String strategy2 = (String)strategyList.get(i2);
                    weight2 = weightStrMap.getDouble((Object)strategy2) / 100.0;
                    double correlation = PortfolioComposer.getCorrelation((Long2ObjectAVLTreeMap<Map<String, Double>>)dailyProfitPercentageMap, strategy1, strategy2);
                    totalPart2 += 2.0 * weight1 * weight2 * correlation * StdDeviation[i1] * StdDeviation[i2];
                }
            }
            dailyLog.print(" ");
            dailyLog.print(" ");
            dailyLog.print("Daily Portfolio expected return : " + PlTypes.printPL((double)(avgProfitPercentage2 * 100.0), (byte)20, (int)3));
            dailyLog.print("Daily expected return : " + PlTypes.printPL((double)avgProfit2, (byte)10, (int)2));
            double StdDeviationPortfolio = Math.sqrt(totalPart1 + totalPart2);
            dailyLog.print("StdDeviation Portfolio : " + PlTypes.printPL((double)(StdDeviationPortfolio * 100.0), (byte)20, (int)3));
            double PortfolioVaR = -averageMarginUsed1 * (zScore * StdDeviationPortfolio);
            dailyLog.print("Portfolio VaR (with a mean of zero): " + PlTypes.printPL((double)PortfolioVaR, (byte)10, (int)2));
            dailyLog.print(" ");
            double dailyRiskFreeRatePercent = settings.RiskFreeRate / 36500.0;
            dailyLog.print("Daily Risk Free Rate : " + PlTypes.printPL((double)(dailyRiskFreeRatePercent * 100.0), (byte)20, (int)5));
            dailyLog.print(" ");
            double ExcessReturn = avgProfitPercentage2 - dailyRiskFreeRatePercent;
            double SharpeRatio = 0.0;
            SharpeRatio = StdDeviationPortfolio != 0.0 ? ExcessReturn / StdDeviationPortfolio : -1.0;
            dailyLog.print("Daily Portfolio expected return : " + PlTypes.printPL((double)(avgProfitPercentage2 * 100.0), (byte)20, (int)3));
            dailyLog.print("Daily Portfolio ExcessReturn return : " + PlTypes.printPL((double)(ExcessReturn * 100.0), (byte)20, (int)3));
            dailyLog.print("Daily Portfolio SharpRatio : " + SQUtils.d2String((double)SharpeRatio, (int)4));
            dailyLog.print(" ");
            dailyLog.print(" ");
            portfolio.specialValues().set(SpecialValues.PortfolioComposerDailyExpectedReturnPct, (Object)String.valueOf(avgProfitPercentage2));
            portfolio.specialValues().set(SpecialValues.PortfolioComposerDailyExpectedReturnMny, (Object)String.valueOf(avgProfit2));
            portfolio.specialValues().set(SpecialValues.PortfolioComposerStdDeviation, (Object)String.valueOf(StdDeviationPortfolio));
            portfolio.specialValues().set(SpecialValues.PortfolioComposerSharpeRatio, (Object)String.valueOf(SharpeRatio));
            double confidenceLevel = settings.confidenceLevel;
            zScore = normalDistribution.inverseCumulativeProbability(confidenceLevel);
            double PortfolioVaR1 = avgProfitPercentage2 - zScore * StdDeviationPortfolio;
            dailyLog.print("Portfolio VaR : " + PlTypes.printPL((double)(PortfolioVaR1 * 100.0), (byte)20, (int)3));
            double PortfolioVaR2 = averageMarginUsed1 * (avgProfitPercentage2 - zScore * StdDeviationPortfolio);
            dailyLog.print("Portfolio VaR : " + PlTypes.printPL((double)PortfolioVaR2, (byte)10, (int)2));
            double expectedShortfall1 = PortfolioComposer.calculateExpectedShortfall(avgProfitPercentage2, StdDeviationPortfolio, confidenceLevel);
            dailyLog.print("Expected Shortfall (ES or CVaR) at % " + confidenceLevel * 100.0 + " confidence level: % " + PlTypes.printPL((double)(expectedShortfall1 * 100.0), (byte)20, (int)3));
            double expectedShortfall2 = averageMarginUsed1 * PortfolioComposer.calculateExpectedShortfall(avgProfitPercentage2, StdDeviationPortfolio, confidenceLevel);
            dailyLog.print("Expected Shortfall (ES or CVaR) at % " + confidenceLevel * 100.0 + " confidence level: % " + PlTypes.printPL((double)expectedShortfall2, (byte)10, (int)2));
            portfolio.specialValues().set(SpecialValues.PortfolioComposerWeights, (Object)Arrays.toString((Object[])weights));
            portfolio.specialValues().set(SpecialValues.PortfolioComposerValueAtRiskPct, (Object)String.valueOf(PortfolioVaR1));
            portfolio.specialValues().set(SpecialValues.PortfolioComposerValueAtRiskMny, (Object)String.valueOf(PortfolioVaR2));
            portfolio.specialValues().set(SpecialValues.PortfolioComposerConditionalValueatRiskPct, (Object)String.valueOf(expectedShortfall1));
            portfolio.specialValues().set(SpecialValues.PortfolioComposerConditionalValueatRiskMny, (Object)String.valueOf(expectedShortfall2));
            log.printNoNewLine(dailyLog.toString());
            this.updateHodlResults(portfolio, (ObjectArrayList<String>)hodlResultKeys);
            portfolio.specialValues().set(SpecialValues.PortfolioHistoryFrom, (Object)minDate);
            portfolio.specialValues().set(SpecialValues.PortfolioHistoryTo, (Object)maxDate);
            for (String resultKey : portfolio.getResultKeys()) {
                Result result = portfolio.subResult(resultKey);
                result.getSettings().set("PortfolioDataStart", (Object)minDate);
                result.getSettings().set("PortfolioDataEnd", (Object)maxDate);
            }
            portfolio.createPortfolioResult();
            portfolio.computeAllStats();
            portfolio.recalculateDailyEquity();
            portfolio.specialValues().set(SpecialValues.PortfolioComposerLog, (Object)log.toString());
            this.updateMM(portfolio, settings.initialCapital);
            portfolio.setNote("PortfolioComposerWeights=" + Arrays.toString((Object[])weights));
            ResultsGroup resultsGroup = portfolio;
            return resultsGroup;
        }
        catch (Error | Exception e) {
            Log.error("PortfolioComposer Exc.", e);
            throw new Exception("PortfolioComposer ERROR!!! " + e.getMessage(), e);
        }
        finally {
            newOrdersMap = new Long2ObjectAVLTreeMap();
            if (weightStrMap != null) {
                weightStrMap.clear();
            }
            if (strMap != null) {
                strMap.clear();
            }
            if (strbaseMap != null) {
                strbaseMap.clear();
            }
            if (mmStrMap != null) {
                mmStrMap.clear();
            }
            if (maxPosStrMap != null) {
                maxPosStrMap.clear();
            }
            if (orderIdMap != null) {
                orderIdMap.clear();
            }
            weightStrMap = null;
            strMap = null;
            strbaseMap = null;
            mmStrMap = null;
            maxPosStrMap = null;
        }
    }

    public static double calculateExpectedShortfall(double mu, double sigma, double confidenceLevel) {
        NormalDistribution normalDistribution = new NormalDistribution();
        double zScore = normalDistribution.inverseCumulativeProbability(confidenceLevel);
        double pdfAtZ = normalDistribution.density(zScore);
        double alpha = 1.0 - confidenceLevel;
        return mu - sigma * (pdfAtZ / alpha);
    }

    public static void addProfit(Long2ObjectAVLTreeMap<Map<String, Double>> dailyProfitMap, Long2ObjectAVLTreeMap<Map<String, Double>> marginUsedMap, Long2ObjectAVLTreeMap<Map<String, Double>> dailyProfitPercentageMap, long epochMillis, String strategy, double profit, double marginUsed) {
        Map strategyProfits = (Map)dailyProfitMap.getOrDefault(epochMillis, new HashMap());
        strategyProfits.put(strategy, strategyProfits.getOrDefault(strategy, 0.0) + profit);
        dailyProfitMap.put(epochMillis, (Object)strategyProfits);
        Map strategyMargins = (Map)marginUsedMap.getOrDefault(epochMillis, new HashMap());
        strategyMargins.put(strategy, marginUsed);
        marginUsedMap.put(epochMillis, (Object)strategyMargins);
        if (strategyMargins.containsKey(strategy)) {
            double margin = (Double)strategyMargins.get(strategy);
            double profitPercentage = 0.0;
            profitPercentage = margin != 0.0 ? (Double)strategyProfits.get(strategy) / margin : 0.0;
            Map strategyProfitPercentages = (Map)dailyProfitPercentageMap.getOrDefault(epochMillis, new HashMap());
            strategyProfitPercentages.put(strategy, profitPercentage);
            dailyProfitPercentageMap.put(epochMillis, (Object)strategyProfitPercentages);
        }
    }

    public static double calculateStandardDeviationLastNPeriods(Long2ObjectAVLTreeMap<Map<String, Double>> dailyProfitPercentageMap, String strategy, int n) {
        double sum = 0.0;
        double sumSquared = 0.0;
        int count = 0;
        int totalPeriods = dailyProfitPercentageMap.size();
        int startPeriod = Math.max(0, totalPeriods - n);
        DescriptiveStatistics stats = new DescriptiveStatistics();
        Iterator iterator = dailyProfitPercentageMap.keySet().stream().skip(startPeriod).toList().iterator();
        while (iterator.hasNext()) {
            long epochMillis = (Long)iterator.next();
            Map strategyProfitPercentages = (Map)dailyProfitPercentageMap.get(epochMillis);
            if (strategyProfitPercentages == null) continue;
            if (strategyProfitPercentages.containsKey(strategy)) {
                double value = (Double)strategyProfitPercentages.get(strategy);
                if (!Double.isNaN(value) && value != Double.NEGATIVE_INFINITY && value != Double.POSITIVE_INFINITY) {
                    stats.addValue(((Double)strategyProfitPercentages.get(strategy)).doubleValue());
                    sum += value;
                    ++count;
                    continue;
                }
                stats.addValue(0.0);
                sum += 0.0;
                ++count;
                continue;
            }
            stats.addValue(0.0);
            ++count;
        }
        if (count == 0 || sum == 0.0) {
            return 0.0;
        }
        double mean = sum / (double)count;
        Iterator iterator2 = dailyProfitPercentageMap.keySet().stream().skip(startPeriod).toList().iterator();
        while (iterator2.hasNext()) {
            long epochMillis = (Long)iterator2.next();
            Map strategyProfitPercentages = (Map)dailyProfitPercentageMap.get(epochMillis);
            if (strategyProfitPercentages == null) continue;
            if (strategyProfitPercentages.containsKey(strategy)) {
                double value = (Double)strategyProfitPercentages.get(strategy);
                if (!Double.isNaN(value) && value != Double.NEGATIVE_INFINITY && value != Double.POSITIVE_INFINITY) {
                    sumSquared += (value - mean) * (value - mean);
                    continue;
                }
                sumSquared += (0.0 - mean) * (0.0 - mean);
                continue;
            }
            sumSquared += (0.0 - mean) * (0.0 - mean);
        }
        double variance = sumSquared / (double)count;
        return Math.sqrt(variance);
    }

    public static double getAverageProfitPercentage(Long2ObjectAVLTreeMap<Map<String, Double>> dailyProfitPercentageMap, String strategy, int n) {
        DescriptiveStatistics stats = new DescriptiveStatistics();
        boolean count = false;
        if (n > 0) {
            int totalPeriods = dailyProfitPercentageMap.size();
            int startPeriod = Math.max(0, totalPeriods - n);
            Iterator iterator = dailyProfitPercentageMap.keySet().stream().skip(startPeriod).toList().iterator();
            while (iterator.hasNext()) {
                long epochMillis = (Long)iterator.next();
                Map strategyProfitPercentages = (Map)dailyProfitPercentageMap.get(epochMillis);
                if (strategyProfitPercentages == null) continue;
                if (strategyProfitPercentages.containsKey(strategy)) {
                    double value = (Double)strategyProfitPercentages.get(strategy);
                    if (!Double.isNaN(value) && value != Double.NEGATIVE_INFINITY && value != Double.POSITIVE_INFINITY) {
                        stats.addValue(value);
                        continue;
                    }
                    stats.addValue(0.0);
                    continue;
                }
                stats.addValue(0.0);
            }
        } else {
            for (Map.Entry entry : dailyProfitPercentageMap.entrySet()) {
                Map strategyProfitPercentages = (Map)entry.getValue();
                if (strategyProfitPercentages.containsKey(strategy)) {
                    double value = (Double)strategyProfitPercentages.get(strategy);
                    if (!Double.isNaN(value) && value != Double.NEGATIVE_INFINITY && value != Double.POSITIVE_INFINITY) {
                        stats.addValue(value);
                        continue;
                    }
                    stats.addValue(0.0);
                    continue;
                }
                stats.addValue(0.0);
            }
        }
        return stats.getMean();
    }

    public static double getLastMarginUsed(Long2ObjectAVLTreeMap<Map<String, Double>> marginUsedMap, String strategy) {
        if (marginUsedMap.isEmpty()) {
            return 0.0;
        }
        Iterator iterator = marginUsedMap.keySet().stream().sorted((a, b) -> Long.compare(b, a)).toList().iterator();
        while (iterator.hasNext()) {
            long epochMillis = (Long)iterator.next();
            Map strategyMargins = (Map)marginUsedMap.get(epochMillis);
            if (!strategyMargins.containsKey(strategy)) continue;
            return (Double)strategyMargins.get(strategy);
        }
        return 0.0;
    }

    public static double getAverageMarginUsed(Long2ObjectAVLTreeMap<Map<String, Double>> marginUsedMap, String strategy) {
        DescriptiveStatistics stats = new DescriptiveStatistics();
        for (Map.Entry entry : marginUsedMap.entrySet()) {
            Map strategyMargins = (Map)entry.getValue();
            if (!strategyMargins.containsKey(strategy)) continue;
            stats.addValue(((Double)strategyMargins.get(strategy)).doubleValue());
        }
        return stats.getMean();
    }

    public static double getCorrelation(Long2ObjectAVLTreeMap<Map<String, Double>> dailyProfitPercentageMap, String strategy1, String strategy2) {
        ArrayList<Double> tempListA = new ArrayList<Double>();
        ArrayList<Double> tempListB = new ArrayList<Double>();
        for (Map.Entry entry : dailyProfitPercentageMap.entrySet()) {
            Map strategyProfitPercentages = (Map)entry.getValue();
            if (!strategyProfitPercentages.containsKey(strategy1) || !strategyProfitPercentages.containsKey(strategy2)) continue;
            tempListA.add((Double)strategyProfitPercentages.get(strategy1));
            tempListB.add((Double)strategyProfitPercentages.get(strategy2));
        }
        if (tempListA.size() == 0 || tempListB.size() == 0) {
            return 0.0;
        }
        double[] valuesA = tempListA.stream().mapToDouble(Double::doubleValue).toArray();
        double[] valuesB = tempListB.stream().mapToDouble(Double::doubleValue).toArray();
        CorrelationComputer CorrelationComputer1 = new CorrelationComputer();
        double value = CorrelationComputer.calculateCorrelation((double[])valuesA, (double[])valuesB);
        if (!Double.isNaN(value) && value != Double.NEGATIVE_INFINITY && value != Double.POSITIVE_INFINITY) {
            return value;
        }
        return 0.0;
    }

    private void updateMM(ResultsGroup portfolio, double initialCapital) {
        try {
            String lastSettings = portfolio.getLastSettings();
            if (lastSettings == null) {
                return;
            }
            Element elSettings = XMLUtil.stringToElement((String)lastSettings);
            Element elRiskMoneyManagement = elSettings.getChild("RiskMoneyManagement");
            MoneyManagementMethod mm = MoneyManagementMethodsList.create((String)"RiskFixedPctOfAccount", (Object[])new Object[]{100, 0, 0, 0, 1000000});
            mm.setInitialCapital(initialCapital);
            Element elMM = mm.getXML();
            elRiskMoneyManagement.removeContent();
            elRiskMoneyManagement.addContent((Content)elMM);
            portfolio.setLastSettings(XMLUtil.elementToString((Element)elSettings));
        }
        catch (Exception e) {
            Log.error("Updating MM failed. Exc." + e.getMessage(), (Throwable)e);
        }
    }

    private void updateHodlResults(ResultsGroup portfolio, ObjectArrayList<String> hodlResultKeys) throws Exception {
        for (int i = 0; i < hodlResultKeys.size(); ++i) {
            String resultKey = (String)hodlResultKeys.get(i);
            OrdersList orders = portfolio.orders().filter(resultKey, (byte)0, (byte)127);
            if (orders.size() != 1) continue;
            Order hodlOrder = orders.get(0);
            portfolio.orders().removeById(hodlOrder.OrderId);
            ChartDef chartDef = new ChartDef("History", hodlOrder.Symbol, "D1", hodlOrder.OpenTime, hodlOrder.CloseTime, 0.0, "No Session");
            IDataLoader loader = DataManager.getDataLoader((ChartDef)chartDef, (int)1, null);
            loader.open();
            double lastClosePrice = -1.0;
            double capital = 0.0;
            int ticket = 1;
            while (loader.hasNextTick()) {
                VersatileData vd = new VersatileData();
                loader.getNextTick(vd);
                long time = SQTime.getDateInMs((long)vd.time);
                double open = vd.open;
                double close = vd.close;
                Order o = new Order();
                o.Ticket = ticket;
                o.Symbol = hodlOrder.Symbol;
                o.SetupName = hodlOrder.SetupName;
                o.Size = hodlOrder.Size;
                o.Type = 1;
                o.OpenPrice = (float)(lastClosePrice == -1.0 ? open : lastClosePrice);
                o.ClosePrice = (float)close;
                o.OpenTime = time;
                o.CloseTime = time;
                o.PL = (o.ClosePrice - o.OpenPrice) * o.Size;
                o.PctPL = (float)OrderPLComputer.getPercentagePL((double)o.PL, (double)capital);
                o.CloseType = 1;
                portfolio.orders().add(o);
                lastClosePrice = close;
                ++ticket;
            }
        }
    }

    private void modifyHodlOrder(Order hodlOrder, long startDate, long endDate) throws Exception {
        try {
            String symbol = hodlOrder.Symbol;
            DataInfo dataInfo = DataManager.getDataInfo((String)"History", (String)symbol);
            if (dataInfo == null || dataInfo.symbolInfo == null) {
                throw new TradingException(String.format("Instrument info for symbol '%s doesn't exist", symbol));
            }
            ChartDef chartDef = new ChartDef("History", symbol, "D1", startDate, endDate, 0.0, "No Session");
            IDataLoader loader = DataManager.getDataLoader((ChartDef)chartDef, (int)1, null);
            loader.open();
            hodlOrder.OpenTime = -1L;
            hodlOrder.CloseTime = -1L;
            while (loader.hasNextTick()) {
                VersatileData vd = new VersatileData();
                loader.getNextTick(vd);
                long time = SQTime.getDateInMs((long)vd.time);
                if (hodlOrder.OpenTime == -1L || time <= startDate) {
                    hodlOrder.OpenTime = time;
                    hodlOrder.OpenPrice = (float)vd.open;
                }
                if (hodlOrder.CloseTime != -1L && time > endDate) continue;
                hodlOrder.CloseTime = time;
                hodlOrder.ClosePrice = (float)vd.close;
            }
            Log.info("HODL order: " + hodlOrder.toString());
        }
        catch (Exception e) {
            Log.error("Hodl order Exc.", (Throwable)e);
            throw new Exception(String.format("Error occurred while loading symbol '%s' data for the Buy & Hold strategy '%s'. Reason: %s", hodlOrder.Symbol, hodlOrder.StrategyName, e.getMessage()), e);
        }
    }

    private double calculateMargin(float size, double price, InstrumentInfo instrumentInfo) {
        return (double)size * price * instrumentInfo.pointValue;
    }

    private InstrumentInfo getInstrumentInfo(ResultsGroup rg, Order order) throws Exception {
        InstrumentInfo instrumentInfo = null;
        SymbolInfo si = rg.symbols().get(order.Symbol);
        if (si != null) {
            instrumentInfo = si.InstrumentInfo();
        }
        if (instrumentInfo == null) {
            instrumentInfo = rg.symbols().getDefaultInstrumentInfo();
        }
        if (instrumentInfo == null) {
            throw new Exception(String.format("Instrument info not found for %s / %s", rg.getName(), order.Symbol));
        }
        return instrumentInfo;
    }

    private double calculateUsedMargin(Long2ObjectAVLTreeMap<ObjectArrayList<Order>> openTradesMap, Object2ObjectOpenHashMap<String, ResultsGroup> strMap) throws Exception {
        double usedMargin = 0.0;
        for (Long2ObjectMap.Entry item : openTradesMap.long2ObjectEntrySet()) {
            ObjectArrayList list = (ObjectArrayList)item.getValue();
            for (int j = 0; j < list.size(); ++j) {
                Order order = (Order)list.get(j);
                double openPrice = OrderTypes.isMarketOrder((byte)order.OriginalType) ? (double)order.OpenPrice : (double)order.OriginalPrice;
                ResultsGroup rg = (ResultsGroup)strMap.get((Object)order.StrategyName);
                InstrumentInfo instrumentInfo = this.getInstrumentInfo(rg, order);
                usedMargin += this.calculateMargin(order.Size, openPrice, instrumentInfo);
            }
        }
        return usedMargin;
    }

    private void printOpenTrades(Long2ObjectAVLTreeMap<ObjectArrayList<Order>> openTradesMap, DailyLog log, Object2ObjectOpenHashMap<String, ResultsGroup> strMap, int decimals) throws Exception {
        log.print("Open trades (used margin)");
        int total = 0;
        for (Long2ObjectMap.Entry item : openTradesMap.long2ObjectEntrySet()) {
            ObjectArrayList list = (ObjectArrayList)item.getValue();
            for (int j = 0; j < list.size(); ++j) {
                Order order = (Order)list.get(j);
                double openPrice = OrderTypes.isMarketOrder((byte)order.OriginalType) ? (double)order.OpenPrice : (double)order.OriginalPrice;
                order = (Order)list.get(j);
                ResultsGroup rg = (ResultsGroup)strMap.get((Object)order.StrategyName);
                InstrumentInfo instrumentInfo = this.getInstrumentInfo(rg, order);
                double margin = this.calculateMargin(order.Size, openPrice, instrumentInfo);
                String orderInfo = order.StrategyName + "/" + order.Symbol + "|OpenType=" + OrderTypes.toString((byte)order.OriginalType) + "|OpenTime=" + SQTime.toFullDateMinuteString((long)order.OpenTime) + "|OpenPrice=" + PlTypes.printPL((double)openPrice, (byte)10, (int)decimals) + "|Size=" + order.Size + "|CloseTime=" + SQTime.toFullDateMinuteString((long)order.CloseTime) + "|Margin=" + SQUtils.d2((double)margin);
                log.print(++total + ": " + orderInfo);
            }
        }
        if (total == 0) {
            log.print("No open trades");
        }
        log.print("-------------------------------------------");
    }

    public void stop() {
        this.stopped = true;
    }

    private class DailyLog {
        public boolean tradesModified = false;
        private StringBuilder b = new StringBuilder();

        private DailyLog() {
        }

        public void print(String log) {
            this.b.append(log + "\n");
        }

        public void tradesModified() {
            this.tradesModified = true;
        }

        public void reset() {
            this.b = new StringBuilder();
            this.tradesModified = false;
        }

        public String toString() {
            String text = this.b.toString();
            return text;
        }
    }
}

