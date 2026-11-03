/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  com.strategyquant.datalib.ChartDef
 *  com.strategyquant.datalib.DataInfo
 *  com.strategyquant.datalib.consts.Precisions
 *  com.strategyquant.datalib.data.DataException
 *  com.strategyquant.datalib.data.DataManager
 *  com.strategyquant.gridlib.client.GridJob
 *  com.strategyquant.lib.L
 *  com.strategyquant.lib.SettingsMap
 *  com.strategyquant.lib.XMLUtil
 *  com.strategyquant.tradinglib.ChartSetup
 *  com.strategyquant.tradinglib.DatabankColumn
 *  com.strategyquant.tradinglib.Directions
 *  com.strategyquant.tradinglib.PlTypes
 *  com.strategyquant.tradinglib.Result
 *  com.strategyquant.tradinglib.ResultsGroup
 *  com.strategyquant.tradinglib.SQStats
 *  com.strategyquant.tradinglib.SampleTypes
 *  com.strategyquant.tradinglib.backtestrunner.IBacktestProgressListener
 *  com.strategyquant.tradinglib.conditions.Condition
 *  com.strategyquant.tradinglib.crosscheck.CrossCheckDataNotExistException
 *  com.strategyquant.tradinglib.crosscheck.CrossCheckMethod
 *  com.strategyquant.tradinglib.crosscheck.ICrossCheck
 *  com.strategyquant.tradinglib.databank.DatabankColumns
 *  com.strategyquant.tradinglib.engine.BacktestEngine
 *  com.strategyquant.tradinglib.engine.ChartSetups
 *  com.strategyquant.tradinglib.engine.stockpicker.StockpickerBacktestEngine
 *  com.strategyquant.tradinglib.fitnessfunction.IFitnessFunction
 *  com.strategyquant.tradinglib.optimization.MetricForFitness
 *  com.strategyquant.tradinglib.project.ILastEventListener
 *  com.strategyquant.tradinglib.project.ProjectConfigHelper
 *  com.strategyquant.tradinglib.servlet.IServletPlugin
 *  com.strategyquant.tradinglib.simulator.ITradingSimulator
 *  com.strategyquant.tradinglib.simulator.impl.TraderSimulators
 *  com.strategyquant.tradinglib.task.settings.TaskSettingsData
 *  jakarta.servlet.Servlet
 *  net.xeoh.plugins.base.annotations.PluginImplementation
 *  org.eclipse.jetty.server.Handler
 *  org.eclipse.jetty.servlet.ServletContextHandler
 *  org.eclipse.jetty.servlet.ServletHolder
 *  org.jdom2.Element
 */
package com.strategyquant.plugin.CrossCheck.impl.RetestOnAdditionalMarkets;

import com.strategyquant.datalib.ChartDef;
import com.strategyquant.datalib.DataInfo;
import com.strategyquant.datalib.consts.Precisions;
import com.strategyquant.datalib.data.DataException;
import com.strategyquant.datalib.data.DataManager;
import com.strategyquant.gridlib.client.GridJob;
import com.strategyquant.lib.L;
import com.strategyquant.lib.SettingsMap;
import com.strategyquant.lib.XMLUtil;
import com.strategyquant.plugin.CrossCheck.impl.RetestOnAdditionalMarkets.RetestOnAdditionalMarketsServlet;
import com.strategyquant.tradinglib.ChartSetup;
import com.strategyquant.tradinglib.DatabankColumn;
import com.strategyquant.tradinglib.Directions;
import com.strategyquant.tradinglib.PlTypes;
import com.strategyquant.tradinglib.Result;
import com.strategyquant.tradinglib.ResultsGroup;
import com.strategyquant.tradinglib.SQStats;
import com.strategyquant.tradinglib.SampleTypes;
import com.strategyquant.tradinglib.backtestrunner.IBacktestProgressListener;
import com.strategyquant.tradinglib.conditions.Condition;
import com.strategyquant.tradinglib.crosscheck.CrossCheckDataNotExistException;
import com.strategyquant.tradinglib.crosscheck.CrossCheckMethod;
import com.strategyquant.tradinglib.crosscheck.ICrossCheck;
import com.strategyquant.tradinglib.databank.DatabankColumns;
import com.strategyquant.tradinglib.engine.BacktestEngine;
import com.strategyquant.tradinglib.engine.ChartSetups;
import com.strategyquant.tradinglib.engine.stockpicker.StockpickerBacktestEngine;
import com.strategyquant.tradinglib.fitnessfunction.IFitnessFunction;
import com.strategyquant.tradinglib.optimization.MetricForFitness;
import com.strategyquant.tradinglib.project.ILastEventListener;
import com.strategyquant.tradinglib.project.ProjectConfigHelper;
import com.strategyquant.tradinglib.servlet.IServletPlugin;
import com.strategyquant.tradinglib.simulator.ITradingSimulator;
import com.strategyquant.tradinglib.simulator.impl.TraderSimulators;
import com.strategyquant.tradinglib.task.settings.TaskSettingsData;
import jakarta.servlet.Servlet;
import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;
import net.xeoh.plugins.base.annotations.PluginImplementation;
import org.eclipse.jetty.server.Handler;
import org.eclipse.jetty.servlet.ServletContextHandler;
import org.eclipse.jetty.servlet.ServletHolder;
import org.jdom2.Element;

@PluginImplementation
public class RetestOnAdditionalMarkets
extends CrossCheckMethod
implements IFitnessFunction,
IServletPlugin {
    private ServletContextHandler dataContext;
    private static final String SETTING_SLIPPAGES = "CS_ROAM_SLIPPAGES";
    private static final String SETTING_MIN_DISTANCES = "CS_ROAM_MIN_DISTANCES";
    private static final String SETTING_COMMISSIONS = "CS_ROAM_COMMISSIONS";
    private static final String SETTING_SWAPS = "CS_ROAM_SWAPS";
    private static final String SETTING_USE_MAIN_TEST_DATE = "CS_ROAM_USE_MAINTETS_DATE";
    private static final String ConditionsCheckAdditionalMarkets = "ConditionsCheckMarkets";
    private static final String ConditionsMinConds = "ConditionsMinConds";
    private static final String ConditionsMinMarkets = "ConditionsMinMarkets";
    private String databankColumnName = null;
    private ArrayList<Goal> weightedGoals = new ArrayList();

    public ICrossCheck clone(SettingsMap settings) {
        RetestOnAdditionalMarkets crossCheck = new RetestOnAdditionalMarkets();
        crossCheck.settings = settings != null ? settings : this.settings.clone();
        return crossCheck;
    }

    public String getName() {
        return NameAddMarkets;
    }

    public String getShortName() {
        return L.t((String)"Add. markets", (Object[])new Object[0]);
    }

    public String getDescription() {
        return L.tsq((String)"This cross check retest the strategy on multiple additional markets (symbols).<br/>It allows you to compare the performance on multiple symbols, ideally you want to find the strategy that will work on multiple markets.");
    }

    public Handler getHandler() {
        if (this.dataContext == null) {
            this.dataContext = new ServletContextHandler(1);
            this.dataContext.setContextPath("/retestOnAdditionalMarkets/");
            this.dataContext.addServlet(new ServletHolder((Servlet)new RetestOnAdditionalMarketsServlet()), "/*");
        }
        return this.dataContext;
    }

    public String getSettingName() {
        return "RetestOnAdditionalMarkets";
    }

    public int getType() {
        return 1;
    }

    public int getPreferredPosition() {
        return 210;
    }

    public int getNumberOfSimulations() {
        ChartSetups chartSetups = (ChartSetups)this.settings.get("AdditionalChartSetups");
        if (chartSetups == null) {
            return 0;
        }
        return chartSetups.size();
    }

    public boolean doesRetest() {
        return true;
    }

    public boolean doesForEverySetup() {
        return false;
    }

    public void fixSettings(Element elSettings) {
        super.fixSettings(elSettings);
        String mainTF = null;
        try {
            Element elTaskSettings = elSettings.getParentElement().getParentElement();
            Element elData = elTaskSettings.getChild("Data");
            if (elData == null) {
                elData = elTaskSettings.getChild("CustomData");
            }
            Element elChart = elData.getChild("Setups").getChild("Setup").getChild("Chart");
            mainTF = elChart.getAttributeValue("timeframe");
        }
        catch (Exception e) {
            Log.error("Incorrect Main data. Cannot get main data timeframe.", (Throwable)e);
        }
        Element elAdditionalData = elSettings.getChild("Settings");
        for (Element elChartSetup : elAdditionalData.getChild("Setups").getChildren("Setup")) {
            List chartElems = elChartSetup.getChildren("Chart");
            for (int i = 0; i < chartElems.size(); ++i) {
                Element elChart = (Element)chartElems.get(i);
                String tf = elChart.getAttributeValue("timeframe");
                if (tf == null || mainTF == null || !tf.equals("Same as main data")) continue;
                elChart.setAttribute("timeframe", mainTF);
            }
        }
    }

    public void readSettings(Element elSettings, TaskSettingsData data) throws Exception {
        try {
            Element elAdditionalData = elSettings.getChild("Settings");
            List elSetups = elAdditionalData.getChild("Setups").getChildren("Setup");
            if (elSetups.size() == 0) {
                throw new Exception();
            }
        }
        catch (Exception e) {
            throw new Exception(L.t((String)"No additional setups defined", (Object[])new Object[0]));
        }
        try {
            this.fixSettings(elSettings);
        }
        catch (Exception e) {
            Log.error("Cannot fix settings", (Throwable)e);
            throw new Exception(L.t((String)"Invalid additional setups settings", (Object[])new Object[0]));
        }
        Element elMethodSettings = elSettings.getChild("Settings");
        this.settings.set("AdditionalChartSetups", (Object)ProjectConfigHelper.getChartSetups((Element)elMethodSettings));
        this.settings.set(SETTING_SLIPPAGES, (Object)ProjectConfigHelper.getChartSetupValues((Element)elMethodSettings, (String)"slippage"));
        this.settings.set(SETTING_MIN_DISTANCES, (Object)ProjectConfigHelper.getChartSetupValues((Element)elMethodSettings, (String)"minDist"));
        this.settings.set(SETTING_COMMISSIONS, (Object)ProjectConfigHelper.getChartSetupCommissions((Element)elMethodSettings));
        this.settings.set(SETTING_SWAPS, (Object)ProjectConfigHelper.getChartSetupSwaps((Element)elMethodSettings));
        this.settings.set(SETTING_USE_MAIN_TEST_DATE, (Object)ProjectConfigHelper.getChartSetupMainTestValues((Element)elMethodSettings, (String)"dates"));
        this.readConditions(elSettings);
        Element elAcceptanceSettings = XMLUtil.tryAddElement((Element)elSettings, (String)"AcceptanceSettings");
        this.settings.set(ConditionsCheckAdditionalMarkets, (Object)XMLUtil.getNodeValue((Element)elAcceptanceSettings, (String)"Check", (String)"all").equals("markets"));
        this.settings.set(ConditionsMinConds, (Object)XMLUtil.getNodeIntValue((Element)elAcceptanceSettings, (String)"MinConditions", (int)0));
        this.settings.set(ConditionsMinMarkets, (Object)XMLUtil.getNodeIntValue((Element)elAcceptanceSettings, (String)"MinMarkets", (int)0));
    }

    public boolean runTest(ResultsGroup mainResultsGroup, int index, double globalATR, GridJob parentGridJob, boolean singleThreaded, ILastEventListener lastEventListener, String strategyName) throws Exception {
        int i;
        ChartSetups chartSetups = (ChartSetups)this.settings.get("AdditionalChartSetups");
        if (chartSetups == null || chartSetups.size() < 1) {
            return true;
        }
        String mainResultKey = mainResultsGroup.getMainResultKey();
        Result result = mainResultsGroup.subResult(mainResultKey);
        SettingsMap settings = result.getSettings();
        ArrayList<ResultsGroup> additionalResults = new ArrayList<ResultsGroup>();
        ArrayList slippages = (ArrayList)this.settings.get(SETTING_SLIPPAGES);
        ArrayList minDistances = (ArrayList)this.settings.get(SETTING_MIN_DISTANCES);
        ArrayList useMainTestDates = (ArrayList)this.settings.get(SETTING_USE_MAIN_TEST_DATE);
        ArrayList commissionMethods = (ArrayList)this.settings.get(SETTING_COMMISSIONS);
        ArrayList swapMethods = (ArrayList)this.settings.get(SETTING_SWAPS);
        for (i = 0; i < chartSetups.size() && !this.stopPauseEngine.isStopped(); ++i) {
            ChartSetup additionalChartSetup = (ChartSetup)chartSetups.get(i);
            int additionalEngine = additionalChartSetup.getBacktestEngine();
            if (!(additionalEngine != 1316847364 && additionalEngine != -1816889229 || DataManager.isGroupAlias((String)additionalChartSetup.getSymbol()))) {
                Log.warn("Skipping additional market '" + additionalChartSetup.getSymbol() + "' - not a stock group, incompatible with the Stockpicker engine.");
                continue;
            }
            SettingsMap clonedSettings = this.cloneSettings(settings);
            ChartSetup chartSetup = (ChartSetup)clonedSettings.get("BacktestChart");
            if (lastEventListener != null) {
                String symbol = ((ChartDef)chartSetup.getCharts().get(0)).getSymbol();
                String tf = ((ChartDef)chartSetup.getCharts().get(0)).getTimeframe();
                String event = L.t((String)"Running additional market backtest on %s/%s for %s", (Object[])new Object[]{symbol, tf, strategyName});
                lastEventListener.setLastEvent(event);
            }
            chartSetup = this.applyAdditionalChart(chartSetup, additionalChartSetup, (String)useMainTestDates.get(i));
            clonedSettings.set("BacktestChart", (Object)chartSetup);
            clonedSettings.set("Slippage", (Object)Double.parseDouble((String)slippages.get(i)));
            clonedSettings.set("MinDistance", (Object)Double.parseDouble((String)minDistances.get(i)));
            clonedSettings.set("Commission", commissionMethods.get(i));
            clonedSettings.set("Swap", swapMethods.get(i));
            ResultsGroup tempRG = this.testWithThisSetup(clonedSettings, chartSetup, mainResultKey);
            additionalResults.add(tempRG);
        }
        if (additionalResults.size() > 0) {
            for (i = 0; i < additionalResults.size(); ++i) {
                ResultsGroup additionalRG = (ResultsGroup)additionalResults.get(i);
                mainResultsGroup.mergeWith(additionalRG);
            }
            mainResultsGroup.createPortfolioResult();
        }
        double mainResultFitness = result.getFitness((byte)127);
        mainResultsGroup.portfolio().setFitness((byte)127, mainResultFitness);
        mainResultsGroup.portfolio().setFitness((byte)10, mainResultFitness);
        mainResultsGroup.portfolio().setFitness((byte)20, mainResultFitness);
        mainResultsGroup.portfolio().setFitness((byte)11, mainResultFitness);
        mainResultsGroup.portfolio().setFitness((byte)40, mainResultFitness);
        return this.checkConditions(mainResultsGroup, index);
    }

    private ResultsGroup testWithThisSetup(SettingsMap clonedSettings, ChartSetup chartSetup, String mainResultKey) throws Exception {
        StockpickerBacktestEngine backtestEngine = null;
        if (chartSetup.getBacktestEngine() == 1316847364 || chartSetup.getBacktestEngine() == -1816889229) {
            backtestEngine = new StockpickerBacktestEngine();
        } else {
            ITradingSimulator simulator = TraderSimulators.getSimulator((ChartSetup)chartSetup);
            backtestEngine = new BacktestEngine(simulator);
            backtestEngine.setUsePreparedData(true);
        }
        backtestEngine.setSingleThreaded(true);
        backtestEngine.setStopPauseEngine(this.stopPauseEngine);
        backtestEngine.registerProgressListener(new IBacktestProgressListener(){

            public void setProgress(int progress) {
                RetestOnAdditionalMarkets.this.setJobProgress(progress);
            }

            public void increaseProgressStep() {
            }
        });
        backtestEngine.addSetup(clonedSettings);
        String desiredResultKey = "AdditionalMarket: " + chartSetup.getMainChart().getSymbol() + "/" + chartSetup.getMainChart().getTimeframe();
        ResultsGroup newRg = backtestEngine.runBacktest(desiredResultKey, desiredResultKey, false).getResults();
        return newRg;
    }

    private ChartSetup applyAdditionalChart(ChartSetup mainChartSetup, ChartSetup additionalChartSetup, String useMainTestDates) throws Exception {
        ArrayList mainChartDefs = mainChartSetup.getCharts();
        ArrayList additionalChartDefs = additionalChartSetup.getCharts();
        if (mainChartDefs.size() != additionalChartDefs.size()) {
            throw new Exception(L.t((String)"Additional charts don't have the same number of subcharts as main data!", (Object[])new Object[0]));
        }
        ChartDef mainChartDef = (ChartDef)mainChartDefs.get(0);
        ChartDef additionalChartDef = (ChartDef)additionalChartDefs.get(0);
        DataInfo dataInfo = DataManager.getDataInfo((String)additionalChartDef.getConnectionName(), (String)additionalChartDef.getSymbol());
        if (dataInfo == null) {
            throw new DataException(2, "Data for connection '" + additionalChartDef.getConnectionName() + "' and symbol '" + additionalChartDef.getSymbol() + "' cannot be found!");
        }
        long historyFrom = this.checkHistoryFrom(dataInfo, mainChartDef.getHistoryFrom());
        long historyTo = this.checkHistoryTo(dataInfo, mainChartDef.getHistoryTo());
        if (useMainTestDates.equals("false")) {
            historyFrom = this.checkHistoryFrom(dataInfo, additionalChartDef.getHistoryFrom());
            historyTo = this.checkHistoryTo(dataInfo, additionalChartDef.getHistoryTo());
        }
        ChartSetup newChartSetup = new ChartSetup(additionalChartDef.getConnectionName(), additionalChartDef.getSymbol(), additionalChartDef.getTimeframe(), historyFrom, historyTo, additionalChartDef.getSpread(), additionalChartDef.getSession());
        newChartSetup.setTestPrecision(additionalChartSetup.getTestPrecision());
        newChartSetup.setBacktestEngine(mainChartSetup.getBacktestEngine());
        for (int i = 1; i < mainChartDefs.size(); ++i) {
            additionalChartDef = (ChartDef)additionalChartDefs.get(i);
            newChartSetup.addChart(additionalChartDef.getConnectionName(), additionalChartDef.getSymbol(), additionalChartDef.getTimeframe());
        }
        return newChartSetup;
    }

    private long checkHistoryFrom(DataInfo dataInfo, long additionalDateFrom) {
        if (additionalDateFrom >= dataInfo.dateFrom && additionalDateFrom < dataInfo.dateTo) {
            return additionalDateFrom;
        }
        return dataInfo.dateFrom;
    }

    private long checkHistoryTo(DataInfo dataInfo, long additionalDateTo) {
        if (additionalDateTo <= dataInfo.dateTo && additionalDateTo > dataInfo.dateFrom) {
            return additionalDateTo;
        }
        return dataInfo.dateTo;
    }

    protected boolean checkConditions(ResultsGroup rg, int index) {
        if (((Boolean)this.settings.get(ConditionsCheckAdditionalMarkets)).booleanValue()) {
            return this.checkAdditionalMarketConditions(rg, index);
        }
        return super.checkConditions(rg, index);
    }

    protected boolean checkAdditionalMarketConditions(ResultsGroup rg, int index) {
        int totalMarkets = 0;
        try {
            totalMarkets = rg.additionalMarketKeys().size();
        }
        catch (Exception exception) {
            // empty catch block
        }
        int[] marketConditionsPassed = new int[totalMarkets];
        ArrayList conditions = (ArrayList)this.settings.get("Conditions");
        boolean marketConditionUsed = false;
        if (conditions != null && conditions.size() > 0 && totalMarkets > 0) {
            for (int i = 0; i < conditions.size(); ++i) {
                Condition condition = (Condition)conditions.get(i);
                if (!condition.isUsed() || !condition.isCrossCheckCondition(this.getSettingName())) continue;
                try {
                    this.conditionsChecker.leftValues.clear();
                    this.conditionsChecker.rightValues.clear();
                    byte[] leftSampleType = this.conditionsChecker.getSampleType(condition.getLeftSideConditionValue());
                    byte[] rightSampleType = this.conditionsChecker.getSampleType(condition.getRightSideConditionValue());
                    int[] leftAdditionalMarket = this.conditionsChecker.getAdditionalMarket(condition.getLeftSideConditionValue(), rg);
                    int[] rightAdditionalMarket = this.conditionsChecker.getAdditionalMarket(condition.getRightSideConditionValue(), rg);
                    for (int leftDataIndex = 0; leftDataIndex < leftAdditionalMarket.length; ++leftDataIndex) {
                        for (int rightDataIndex = 0; rightDataIndex < rightAdditionalMarket.length; ++rightDataIndex) {
                            boolean passed = true;
                            block8: for (int leftSampleIndex = 0; leftSampleIndex < leftSampleType.length && passed; ++leftSampleIndex) {
                                for (int rightSampleIndex = 0; rightSampleIndex < rightSampleType.length; ++rightSampleIndex) {
                                    this.conditionsChecker.leftValues.put("SampleType", leftSampleType[leftSampleIndex]);
                                    this.conditionsChecker.leftValues.put("AdditionalMarket", leftAdditionalMarket[leftDataIndex]);
                                    this.conditionsChecker.rightValues.put("SampleType", rightSampleType[rightSampleIndex]);
                                    this.conditionsChecker.rightValues.put("AdditionalMarket", rightAdditionalMarket[rightDataIndex]);
                                    if (condition.isCrossCheckCondition("RetestOnAdditionalMarkets")) {
                                        marketConditionUsed = true;
                                    }
                                    if (condition.isMet(rg, (Object)this.conditionsChecker.leftValues, (Object)this.conditionsChecker.rightValues)) continue;
                                    passed = false;
                                    continue block8;
                                }
                            }
                            if (!passed) continue;
                            if (leftAdditionalMarket[leftDataIndex] > 0) {
                                int n = leftAdditionalMarket[leftDataIndex] - 1;
                                marketConditionsPassed[n] = marketConditionsPassed[n] + 1;
                            }
                            if (rightAdditionalMarket[rightDataIndex] <= 0) continue;
                            int n = rightAdditionalMarket[rightDataIndex] - 1;
                            marketConditionsPassed[n] = marketConditionsPassed[n] + 1;
                        }
                    }
                    continue;
                }
                catch (CrossCheckDataNotExistException leftSampleType) {
                    continue;
                }
                catch (Exception e) {
                    Log.error("Error while checking condition", (Throwable)e);
                    this.dismissalReason = 10003;
                    this.dismissalMessage = L.t((String)"Cross Check filter in '%s': Error evaluating conditions: %s", (Object[])new Object[]{this.getName(), e.getMessage()});
                    return false;
                }
            }
        }
        if (marketConditionUsed) {
            int minConditions = (Integer)this.settings.get(ConditionsMinConds);
            int minMarkets = (Integer)this.settings.get(ConditionsMinMarkets);
            int marketsPassed = 0;
            for (int i = 0; i < marketConditionsPassed.length; ++i) {
                if (marketConditionsPassed[i] < minConditions) continue;
                ++marketsPassed;
            }
            if (marketsPassed < minMarkets) {
                this.dismissalReason = 10012;
                this.dismissalMessage = L.t((String)"Cross Check filter in '%s': %s", (Object[])new Object[]{this.getName(), L.t((String)"Failed - less than %d conditions passed on %d markets", (Object[])new Object[]{minConditions, minMarkets})});
                return false;
            }
        }
        return true;
    }

    public double getStatsValue(ResultsGroup rg, String columnName, Element elColumn, Object ... params) throws Exception {
        int index = this.getMarketIndex(elColumn, params);
        byte direction = XMLUtil.getByteAttr((Element)elColumn, (String)"direction", (byte)0);
        byte sampleType = this.getSampleType(elColumn, params);
        byte plType = XMLUtil.getByteAttr((Element)elColumn, (String)"plType", (byte)10);
        List keys = rg.additionalMarketKeys();
        if (keys.size() > 0 && index < keys.size()) {
            String resultKey = (String)keys.get(index);
            DatabankColumn column = (DatabankColumn)DatabankColumns.get().findClassByName(columnName);
            return column.getNumericValue(rg, resultKey, direction, plType, sampleType);
        }
        throw new CrossCheckDataNotExistException(this.getName());
    }

    private int getMarketIndex(Element elColumn, Object ... inputs) {
        HashMap map;
        int market = XMLUtil.getIntAttr((Element)elColumn, (String)"market", (int)1);
        if (market == 0 && inputs.length > 1 && inputs[1] instanceof HashMap && (map = (HashMap)inputs[1]).containsKey("AdditionalMarket")) {
            market = (Integer)map.get("AdditionalMarket");
        }
        return market - 1;
    }

    public boolean hasStatsValue(ResultsGroup rg, String columnName, Element elColumn, Object ... params) throws Exception {
        int index = this.getMarketIndex(elColumn, params);
        List keys = rg.additionalMarketKeys();
        if (keys.size() > 0 && index < keys.size()) {
            String resultKey = (String)keys.get(index);
            byte direction = XMLUtil.getByteAttr((Element)elColumn, (String)"direction", (byte)0);
            byte sampleType = this.getSampleType(elColumn, params);
            byte plType = XMLUtil.getByteAttr((Element)elColumn, (String)"plType", (byte)10);
            DatabankColumn column = (DatabankColumn)DatabankColumns.get().findClassByName(columnName);
            SQStats stats = column.getStats(rg, resultKey, direction, plType, sampleType);
            return stats != null;
        }
        return false;
    }

    public String printSpecialValue(ResultsGroup rg, String columnName, Element elColumn, Object ... params) throws Exception {
        int index = this.getMarketIndex(elColumn, params);
        byte direction = XMLUtil.getByteAttr((Element)elColumn, (String)"direction", (byte)0);
        byte sampleType = this.getSampleType(elColumn, params);
        byte plType = XMLUtil.getByteAttr((Element)elColumn, (String)"plType", (byte)10);
        List keys = rg.additionalMarketKeys();
        if (keys.size() > 0 && index < keys.size()) {
            String resultKey = (String)keys.get(index);
            DatabankColumn column = (DatabankColumn)DatabankColumns.get().findClassByName(columnName);
            return column.getValue(rg, resultKey, direction, plType, sampleType);
        }
        throw new CrossCheckDataNotExistException(this.getName());
    }

    public String getColumnTitle(String columnName, Element elColumn, Object ... params) {
        int market = this.getMarketIndex(elColumn, params) + 1;
        String marketTitle = market == 0 ? "Every market" : "Market " + market;
        byte direction = XMLUtil.getByteAttr((Element)elColumn, (String)"direction", (byte)0);
        byte sampleType = this.getSampleType(elColumn, params);
        byte plType = XMLUtil.getByteAttr((Element)elColumn, (String)"plType", (byte)10);
        String title = this.getColumnTitleTemplate();
        title = title.replace("#columnName#", columnName);
        title = title.replace("#market#", marketTitle);
        title = title.replace(", #sampleType#", sampleType == 127 ? "" : ", " + SampleTypes.typeToString((byte)sampleType));
        title = title.replace(", #direction#", direction == 0 ? "" : ", " + Directions.typeToString((byte)direction));
        title = title.replace(", #plType#", plType == 10 ? "" : ", " + PlTypes.typeToString((byte)plType));
        return title;
    }

    public String getColumnTitleTemplate() {
        return "#columnName# (" + this.getShortName() + ", #market#, #sampleType#, #direction#, #plType#)";
    }

    public double computeFitness(ResultsGroup results, byte direction, byte sampleType) throws Exception {
        return this.computeFitness(results, direction, sampleType, true);
    }

    public double computeFitness(ResultsGroup results, byte direction, byte sampleType, boolean useRatioByTrades) throws Exception {
        if (this.databankColumnName.equals("Weighted")) {
            return this.computeWeightedFitness(results, direction, sampleType);
        }
        return this.getFitnessValue(results, direction, sampleType, this.databankColumnName, 0.0, (byte)0);
    }

    private double getFitnessValue(ResultsGroup results, byte direction, byte sampleType, String databankColumnName, double target, byte valueType) throws Exception {
        double val;
        DatabankColumn c = (DatabankColumn)DatabankColumns.get().findClassByName(databankColumnName);
        double fitness = c.transformToFitnessRange(val = c.getNumericValue(results, "Portfolio", direction, (byte)10, sampleType), target, valueType);
        if (fitness < 0.0) {
            fitness = 0.0;
        }
        if (fitness > 1.0) {
            fitness = 1.0;
        }
        return fitness;
    }

    private double computeWeightedFitness(ResultsGroup results, byte direction, byte sampleType) throws Exception {
        float totalWeight = 0.0f;
        for (int i = 0; i < this.weightedGoals.size(); ++i) {
            if (!this.weightedGoals.get((int)i).use) continue;
            totalWeight = (float)((double)totalWeight + this.weightedGoals.get((int)i).weight);
        }
        float weightedFitness = 0.0f;
        for (int i = 0; i < this.weightedGoals.size(); ++i) {
            Goal goal = this.weightedGoals.get(i);
            if (!goal.use) continue;
            double rankingFitness = this.getFitnessValue(results, direction, sampleType, goal.statsValueName, goal.target, goal.valueType);
            weightedFitness = (float)((double)weightedFitness + goal.weight / (double)totalWeight * rankingFitness);
        }
        return weightedFitness;
    }

    public String getFitnessKey() {
        return this.getSettingName();
    }

    public String getFitnessName() {
        return "Portfolio";
    }

    public void initFitnessFromXml(Element elSettings) {
        this.weightedGoals.clear();
        Element elRanking = elSettings.getChild("Ranking");
        this.databankColumnName = elRanking.getAttributeValue("type");
        for (Element elGoal : elRanking.getChildren("Goal")) {
            Goal goal = new Goal();
            String use = elGoal.getAttributeValue("use");
            goal.use = use.equals("true") || use.equalsIgnoreCase("1");
            goal.statsValueName = elGoal.getAttributeValue("type");
            goal.weight = XMLUtil.getDoubleAttr((Element)elGoal, (String)"weight", (double)1.0);
            goal.valueType = XMLUtil.getByteAttr((Element)elGoal, (String)"valueType", (byte)0);
            goal.target = XMLUtil.getDoubleAttr((Element)elGoal, (String)"target", (double)0.0);
            this.weightedGoals.add(goal);
        }
    }

    public byte getFitnessType() throws Exception {
        if (this.databankColumnName.equals("Weighted")) {
            return 1;
        }
        return ((DatabankColumn)DatabankColumns.get().findClassByName((String)this.databankColumnName)).valueType;
    }

    public String getFitnessDatabankColumnName() {
        return this.databankColumnName;
    }

    public ArrayList<DatabankColumn> getUsedStatValues() throws Exception {
        throw new Exception(L.t((String)"This fitness method cannot be used in Walk-Forward!", (Object[])new Object[0]));
    }

    public ChartSetups getChartSetups(ChartSetup mainChartSetup) {
        ChartSetups setups = (ChartSetups)this.settings.get("AdditionalChartSetups");
        for (ChartSetup cs : setups) {
            cs.setBacktestEngine(mainChartSetup.getBacktestEngine());
        }
        return setups;
    }

    public boolean doesCreateSubjobs() {
        return false;
    }

    public String printSettings(Element elMethod) throws Exception {
        if (elMethod == null) {
            throw new NullPointerException();
        }
        if (!XMLUtil.elementIs((Element)elMethod, (String)"use")) {
            return "Not used";
        }
        Element settingsEl = elMethod.getChild("Settings");
        String settings = "";
        List elSetups = settingsEl.getChild("Setups").getChildren("Setup");
        for (int i = 0; i < elSetups.size(); ++i) {
            Element elSetup = (Element)elSetups.get(i);
            Element elChart = elSetup.getChild("Chart");
            settings = settings + L.t((String)"Additional backtest (%d): ", (Object[])new Object[]{i + 1});
            settings = settings + L.t((String)"Symbol: %s", (Object[])new Object[]{elChart.getAttributeValue("symbol")});
            settings = settings + "," + L.t((String)"Timeframe: %s", (Object[])new Object[]{elChart.getAttributeValue("timeframe")});
            settings = settings + "," + L.t((String)"Start date: %s", (Object[])new Object[]{elSetup.getAttributeValue("dateFrom")});
            settings = settings + "," + L.t((String)"End date: %s", (Object[])new Object[]{elSetup.getAttributeValue("dateTo")});
            settings = settings + "," + L.t((String)"Test precision: %s", (Object[])new Object[]{Precisions.toString((int)Integer.parseInt(elSetup.getAttributeValue("testPrecision")))});
            settings = settings + "," + L.t((String)"Spread: %s", (Object[])new Object[]{elChart.getAttributeValue("spread")});
            settings = settings + "," + L.t((String)"Slippage: %s", (Object[])new Object[]{elSetup.getAttributeValue("slippage")});
            settings = settings + "," + L.t((String)"Min distance: %s", (Object[])new Object[]{elSetup.getAttributeValue("minDist")});
            String commission = ProjectConfigHelper.getCommissionsMethod((Element)elSetup).printFormatedName();
            settings = settings + "," + L.t((String)"Commission: %s", (Object[])new Object[]{commission});
            String swap = ProjectConfigHelper.getSwapMethod((Element)elSetup).printFormatedName();
            settings = settings + "," + L.t((String)"Swap: %s", (Object[])new Object[]{swap});
            List subchartEls = elSetup.getChildren("Chart");
            String subcharts = subchartEls.size() - 1 + "";
            if (subchartEls.size() > 0) {
                for (int j = 1; j < subchartEls.size(); ++j) {
                    settings = settings + "\n";
                    settings = settings + L.t((String)"Subcharts (%d): ", (Object[])new Object[]{j});
                    settings = settings + String.format("%s, %s", ((Element)subchartEls.get(j)).getAttributeValue("symbol"), ((Element)subchartEls.get(j)).getAttributeValue("timeframe"));
                }
            }
            if (i >= elSetups.size() - 1) continue;
            settings = settings + "\n\n";
        }
        settings = settings + "\n";
        Element conditionsEl = elMethod.getChild("AcceptanceSettings").getChild("Conditions");
        ArrayList conditions = ProjectConfigHelper.getConditions((Element)conditionsEl);
        for (int i = 0; i < conditions.size(); ++i) {
            Condition condition = (Condition)conditions.get(i);
            if (!condition.isUsed()) continue;
            settings = settings + condition.toString();
            settings = settings + "\n";
        }
        return settings;
    }

    public String printWeightedGoals() throws Exception {
        return null;
    }

    public ArrayList<MetricForFitness> getMetricsForFitness() {
        return null;
    }

    public double getMetricValue(ResultsGroup results, byte direction, byte sampleType, String databankColumnName) throws Exception {
        return 0.0;
    }

    public int getBadStrategyReason() {
        return 10033;
    }

    public IFitnessFunction clone() {
        return this;
    }

    private class Goal {
        public boolean use;
        public String statsValueName;
        public double weight;
        public double target;
        public byte valueType;

        private Goal() {
        }
    }
}

