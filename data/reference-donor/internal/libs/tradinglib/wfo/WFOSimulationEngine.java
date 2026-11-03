/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  com.strategyquant.datalib.ChartDef
 *  com.strategyquant.lib.L
 *  com.strategyquant.lib.SQTime
 *  com.strategyquant.lib.SettingsMap
 *  com.strategyquant.lib.app.MainApp
 *  it.unimi.dsi.fastutil.ints.Int2ObjectOpenHashMap
 *  org.slf4j.Logger
 *  org.slf4j.LoggerFactory
 */
package com.strategyquant.tradinglib.wfo;

import com.strategyquant.datalib.ChartDef;
import com.strategyquant.lib.L;
import com.strategyquant.lib.SQTime;
import com.strategyquant.lib.SettingsMap;
import com.strategyquant.lib.app.MainApp;
import com.strategyquant.tradinglib.Order;
import com.strategyquant.tradinglib.OrderCloseTypes;
import com.strategyquant.tradinglib.OrdersList;
import com.strategyquant.tradinglib.Result;
import com.strategyquant.tradinglib.ResultsGroup;
import com.strategyquant.tradinglib.SQStats;
import com.strategyquant.tradinglib.StatsTypeCombination;
import com.strategyquant.tradinglib.engine.ChartSetups;
import com.strategyquant.tradinglib.optimization.VariantComparatorByName;
import com.strategyquant.tradinglib.results.SymbolsMap;
import com.strategyquant.tradinglib.results.stats.StatsComputer;
import com.strategyquant.tradinglib.wfo.SimulationOrdersList;
import com.strategyquant.tradinglib.wfo.WFVariant;
import it.unimi.dsi.fastutil.ints.Int2ObjectOpenHashMap;
import java.io.BufferedWriter;
import java.io.FileWriter;
import java.nio.charset.StandardCharsets;
import java.util.ArrayList;
import java.util.Collections;
import java.util.Comparator;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

public class WFOSimulationEngine {
    public static final Logger Log = LoggerFactory.getLogger((String)"WFOSimulationEngine");
    public static final String DefaultSetupName = "Setup 1";
    private ArrayList<WFVariant> variants = new ArrayList();
    private Int2ObjectOpenHashMap<SimulationOrdersList> simulationsMap = new Int2ObjectOpenHashMap();
    private Comparator<WFVariant> variantComparatorByName = new VariantComparatorByName();
    public boolean periodTypeBars = false;

    public WFOSimulationEngine() throws Exception {
        this(false);
    }

    public WFOSimulationEngine(boolean bl) throws Exception {
        this.periodTypeBars = bl;
    }

    public synchronized void saveTestToFile(ResultsGroup resultsGroup) throws Exception {
        String string = resultsGroup.specialValues().getString("OptimizationParameters");
        if (string == null) {
            throw new Exception(L.t((String)"No params set in the result!", (Object[])new Object[0]));
        }
        short[] sArray = (short[])resultsGroup.specialValues().get("OptimizationParametersArray");
        if (sArray == null) {
            throw new Exception(L.t((String)"No indexes set in the result!", (Object[])new Object[0]));
        }
        String string2 = this.convertParamsToFilename(string);
        this.saveOrdersToFile(string, string2, sArray, resultsGroup);
    }

    private void saveOrdersToTxtFile(String string, String string2, short[] sArray, ResultsGroup resultsGroup) throws Exception {
        String string3 = MainApp.getDataPath() + "tests/tmp/wfosim/" + string2 + ".txt";
        BufferedWriter bufferedWriter = new BufferedWriter(new FileWriter(string3, StandardCharsets.UTF_8));
        double d = 0.0;
        for (int i = 0; i < resultsGroup.orders().size(); ++i) {
            Order order = resultsGroup.orders().get(i);
            bufferedWriter.write(this.orderToString(order, d += (double)order.PL));
            bufferedWriter.write("\n");
        }
        bufferedWriter.close();
    }

    public String orderToString(Order order, double d) {
        StringBuilder stringBuilder = new StringBuilder();
        stringBuilder.append(order.Order);
        stringBuilder.append(" - ");
        stringBuilder.append(order.Ticket);
        stringBuilder.append(" - ");
        stringBuilder.append(SQTime.toDateMinuteString((long)order.OriginalOpenTime));
        stringBuilder.append("/");
        stringBuilder.append(SQTime.toDateMinuteString((long)order.OpenTime));
        stringBuilder.append(" : ");
        stringBuilder.append(SQTime.toDateMinuteString((long)order.CloseTime));
        stringBuilder.append(" : ");
        stringBuilder.append(OrderCloseTypes.toString(order.CloseType));
        stringBuilder.append(", PL: ");
        stringBuilder.append(order.PL);
        stringBuilder.append(", Running PL: ");
        stringBuilder.append(d);
        return stringBuilder.toString();
    }

    private String convertParamsToFilename(String string) {
        StringBuilder stringBuilder = new StringBuilder("p");
        String[] stringArray = string.split(",");
        for (int i = 0; i < stringArray.length; ++i) {
            if (stringArray[i].length() <= 1) continue;
            String string2 = stringArray[i].replace("=", "_");
            if (string2.endsWith(".0")) {
                string2 = string2.replace(".0", "");
            }
            stringBuilder.append("_");
            stringBuilder.append(string2);
        }
        return stringBuilder.toString();
    }

    private void saveOrdersToFile(String string, String string2, short[] sArray, ResultsGroup resultsGroup) throws Exception {
        int n;
        SimulationOrdersList simulationOrdersList = new SimulationOrdersList(resultsGroup.orders().size());
        new Order();
        for (n = 0; n < resultsGroup.orders().size(); ++n) {
            Order order = resultsGroup.orders().get(n);
            simulationOrdersList.add(order.OpenTime, order.CloseTime, order.Type, order.CloseType, order.PL, order.Size, order.OpenPrice, order.ClosePrice, order.BarsInTrade, order.Symbol, order.MAE, order.MFE, order.CommSwap, order.StopLoss);
        }
        n = simulationOrdersList.getHash();
        if (!this.simulationsMap.containsKey(n)) {
            this.simulationsMap.put(n, (Object)simulationOrdersList);
        }
        this.variants.add(new WFVariant(string, sArray, string2, n));
        if (Log.isDebugEnabled()) {
            Log.debug("WF Saved orders: {}", (Object)resultsGroup.orders().size());
        }
    }

    private synchronized OrdersList loadOrders(int n, long l, long l2, String string) throws Exception {
        long l3;
        if (!this.simulationsMap.containsKey(n)) {
            throw new Exception(L.t((String)"Simulation: %d not found!", (Object[])new Object[]{n}));
        }
        SimulationOrdersList simulationOrdersList = (SimulationOrdersList)this.simulationsMap.get(n);
        OrdersList ordersList = new OrdersList("loadOrders", simulationOrdersList.openTime.length);
        for (int i = 0; i < simulationOrdersList.openTime.length && (l3 = this.periodTypeBars ? simulationOrdersList.closeTime[i] : simulationOrdersList.openTime[i]) < l2; ++i) {
            if (l3 < l) continue;
            Order order = new Order();
            order.OpenTime = simulationOrdersList.openTime[i];
            order.CloseTime = simulationOrdersList.closeTime[i];
            order.Type = simulationOrdersList.type[i];
            order.CloseType = simulationOrdersList.closeType[i];
            order.PL = simulationOrdersList.pL[i];
            order.Size = simulationOrdersList.size[i];
            order.OpenPrice = simulationOrdersList.openPrice[i];
            order.ClosePrice = simulationOrdersList.closePrice[i];
            order.BarsInTrade = simulationOrdersList.barsInTrade[i];
            order.Symbol = simulationOrdersList.symbol[i];
            order.MAE = simulationOrdersList.mae[i];
            order.MFE = simulationOrdersList.mfe[i];
            order.SampleType = (byte)10;
            order.SetupName = string;
            order.CommSwap = simulationOrdersList.commswap[i];
            order.StopLoss = simulationOrdersList.stoploss[i];
            if (this.periodTypeBars && order.CloseType == 4) continue;
            ordersList.add(order);
        }
        return ordersList;
    }

    public ArrayList<WFVariant> getVariants() {
        return this.variants;
    }

    public ResultsGroup simulateTestCandidate(StatsComputer statsComputer, WFVariant wFVariant, long l, long l2, SettingsMap settingsMap) throws Exception {
        if (wFVariant == null) {
            Log.error("Variant is null!!!");
            return null;
        }
        String string = DefaultSetupName;
        OrdersList ordersList = this.loadOrders(wFVariant.simulationOLHash, l, l2, string);
        ResultsGroup resultsGroup = new ResultsGroup("Variant " + wFVariant.paramsFile);
        resultsGroup.addSubresult(string, settingsMap);
        ChartSetups chartSetups = (ChartSetups)settingsMap.get("ChartSetups");
        for (ChartDef object2 : chartSetups.getMainSetup().getCharts()) {
            resultsGroup.symbols().add(object2.getSymbol(), object2.getSymbolInfo().instrument, object2.getSymbolInfo());
            resultsGroup.addResultSymbol(string, object2.getSymbol());
        }
        SettingsMap settingsMap2 = resultsGroup.portfolio().getSettings();
        settingsMap2.setIfNotExists("MoneyManagement.InitialCapital", (Object)20000.0);
        resultsGroup.orders().replaceWithList(ordersList);
        Result result = resultsGroup.subResult(string);
        SettingsMap settingsMap3 = result.getSettings();
        settingsMap3.set("PortfolioDataStart", (Object)l);
        settingsMap3.set("PortfolioDataEnd", (Object)l2);
        WFOSimulationEngine.computeStatsRequiredForFitness(statsComputer, string, result, ordersList, resultsGroup.symbols());
        resultsGroup.specialValues().set("OptimizationParameters", (Object)wFVariant.params);
        resultsGroup.specialValues().set("OptimizationParametersArray", (Object)wFVariant.indexes);
        return resultsGroup;
    }

    public static void computeStatsRequiredForFitness(StatsComputer statsComputer, String string, Result result, OrdersList ordersList, SymbolsMap symbolsMap) throws Exception {
        SettingsMap settingsMap = result.getSettings();
        settingsMap.set("AddCommissionSwapToPL", (Object)true);
        statsComputer.initializeWithOrders(ordersList);
        StatsTypeCombination statsTypeCombination = new StatsTypeCombination(1, 10, 127);
        statsComputer.filterBy(string, (byte)1, (byte)127);
        statsComputer.sortAndComputeOrderValues(settingsMap, symbolsMap);
        WFOSimulationEngine.computeStats(result, statsComputer, statsTypeCombination.set((byte)1, (byte)10, (byte)127), settingsMap);
        WFOSimulationEngine.computeStats(result, statsComputer, statsTypeCombination.set((byte)1, (byte)20, (byte)127), settingsMap);
        WFOSimulationEngine.computeStats(result, statsComputer, statsTypeCombination.set((byte)1, (byte)30, (byte)127), settingsMap);
        statsComputer.filterBy(string, (byte)-1, (byte)127);
        statsComputer.sortAndComputeOrderValues(settingsMap, symbolsMap);
        WFOSimulationEngine.computeStats(result, statsComputer, statsTypeCombination.set((byte)-1, (byte)10, (byte)127), settingsMap);
        WFOSimulationEngine.computeStats(result, statsComputer, statsTypeCombination.set((byte)-1, (byte)20, (byte)127), settingsMap);
        WFOSimulationEngine.computeStats(result, statsComputer, statsTypeCombination.set((byte)-1, (byte)30, (byte)127), settingsMap);
        statsComputer.filterBy(string, (byte)0, (byte)127);
        statsComputer.sortAndComputeOrderValues(settingsMap, symbolsMap);
        WFOSimulationEngine.computeStats(result, statsComputer, statsTypeCombination.set((byte)0, (byte)10, (byte)127), settingsMap);
        WFOSimulationEngine.computeStats(result, statsComputer, statsTypeCombination.set((byte)0, (byte)20, (byte)127), settingsMap);
        WFOSimulationEngine.computeStats(result, statsComputer, statsTypeCombination.set((byte)0, (byte)30, (byte)127), settingsMap);
    }

    private static void computeStats(Result result, StatsComputer statsComputer, StatsTypeCombination statsTypeCombination, SettingsMap settingsMap) throws Exception {
        SQStats sQStats = statsComputer.computeStats(result, statsTypeCombination, settingsMap);
        int n = statsTypeCombination.getKey();
        result.set(n, sQStats);
        statsTypeCombination.set(statsTypeCombination.getDirection(), statsTypeCombination.getPLType(), (byte)10);
        n = statsTypeCombination.getKey();
        result.set(n, sQStats);
        statsTypeCombination.set(statsTypeCombination.getDirection(), statsTypeCombination.getPLType(), (byte)20);
        n = statsTypeCombination.getKey();
        result.set(n, sQStats);
    }

    public void sortVariants() {
        Collections.sort(this.variants, this.variantComparatorByName);
    }

    public boolean isPeriodTypeBars() {
        return this.periodTypeBars;
    }
}

