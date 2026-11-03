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
 *  com.strategyquant.lib.SQUtils
 *  com.strategyquant.lib.SettingsMap
 *  com.strategyquant.lib.XMLUtil
 *  com.strategyquant.lib.app.MainApp
 *  com.strategyquant.pluginlib.annotations.Category
 *  com.strategyquant.pluginlib.annotations.HideDatabankChoice
 *  com.strategyquant.pluginlib.annotations.License
 *  com.strategyquant.pluginlib.annotations.Name
 *  com.strategyquant.pluginlib.annotations.ShortDesc
 *  com.strategyquant.tradinglib.ChartSetup
 *  com.strategyquant.tradinglib.MoneyManagementMethod
 *  com.strategyquant.tradinglib.Order
 *  com.strategyquant.tradinglib.OrdersList
 *  com.strategyquant.tradinglib.PlTypes
 *  com.strategyquant.tradinglib.ResultsGroup
 *  com.strategyquant.tradinglib.SQStats
 *  com.strategyquant.tradinglib.StatsTypeCombination
 *  com.strategyquant.tradinglib.StrategyBase
 *  com.strategyquant.tradinglib.charts.linechart.series.XYValue
 *  com.strategyquant.tradinglib.correlation.CorrelationComputer
 *  com.strategyquant.tradinglib.engine.ChartSetups
 *  com.strategyquant.tradinglib.equitychart.BenchmarkTable
 *  com.strategyquant.tradinglib.equitychart.ChartDataset
 *  com.strategyquant.tradinglib.equitychart.EquityChart
 *  com.strategyquant.tradinglib.equitychart.EquityChartUtils
 *  com.strategyquant.tradinglib.equitychart.MainChartDataset
 *  com.strategyquant.tradinglib.equitychart.SubChart
 *  com.strategyquant.tradinglib.equitychart.SubChartDataset
 *  com.strategyquant.tradinglib.equitychartnew.addons.IEquityChartAddon
 *  com.strategyquant.tradinglib.project.ProjectConfigHelper
 *  com.strategyquant.tradinglib.results.stats.StatsComputer
 *  com.strategyquant.tradinglib.results.stats.computer.OrderPLComputer
 *  it.unimi.dsi.fastutil.longs.Long2DoubleAVLTreeMap
 *  it.unimi.dsi.fastutil.objects.ObjectArrayList
 *  net.xeoh.plugins.base.annotations.PluginImplementation
 *  net.xeoh.plugins.base.annotations.meta.Author
 *  org.jdom2.Element
 *  org.slf4j.Logger
 *  org.slf4j.LoggerFactory
 */
package com.strategyquant.plugin.EquityChart.impl.Benchmark;

import com.strategyquant.datalib.ChartDef;
import com.strategyquant.datalib.DataInfo;
import com.strategyquant.datalib.data.DataManager;
import com.strategyquant.datalib.data.io.IDataLoader;
import com.strategyquant.datalib.data.io.VersatileData;
import com.strategyquant.lib.SQTime;
import com.strategyquant.lib.SQUtils;
import com.strategyquant.lib.SettingsMap;
import com.strategyquant.lib.XMLUtil;
import com.strategyquant.lib.app.MainApp;
import com.strategyquant.pluginlib.annotations.Category;
import com.strategyquant.pluginlib.annotations.HideDatabankChoice;
import com.strategyquant.pluginlib.annotations.License;
import com.strategyquant.pluginlib.annotations.Name;
import com.strategyquant.pluginlib.annotations.ShortDesc;
import com.strategyquant.tradinglib.ChartSetup;
import com.strategyquant.tradinglib.MoneyManagementMethod;
import com.strategyquant.tradinglib.Order;
import com.strategyquant.tradinglib.OrdersList;
import com.strategyquant.tradinglib.PlTypes;
import com.strategyquant.tradinglib.ResultsGroup;
import com.strategyquant.tradinglib.SQStats;
import com.strategyquant.tradinglib.StatsTypeCombination;
import com.strategyquant.tradinglib.StrategyBase;
import com.strategyquant.tradinglib.charts.linechart.series.XYValue;
import com.strategyquant.tradinglib.correlation.CorrelationComputer;
import com.strategyquant.tradinglib.engine.ChartSetups;
import com.strategyquant.tradinglib.equitychart.BenchmarkTable;
import com.strategyquant.tradinglib.equitychart.ChartDataset;
import com.strategyquant.tradinglib.equitychart.EquityChart;
import com.strategyquant.tradinglib.equitychart.EquityChartUtils;
import com.strategyquant.tradinglib.equitychart.MainChartDataset;
import com.strategyquant.tradinglib.equitychart.SubChart;
import com.strategyquant.tradinglib.equitychart.SubChartDataset;
import com.strategyquant.tradinglib.equitychartnew.addons.IEquityChartAddon;
import com.strategyquant.tradinglib.project.ProjectConfigHelper;
import com.strategyquant.tradinglib.results.stats.StatsComputer;
import com.strategyquant.tradinglib.results.stats.computer.OrderPLComputer;
import it.unimi.dsi.fastutil.longs.Long2DoubleAVLTreeMap;
import it.unimi.dsi.fastutil.objects.ObjectArrayList;
import java.util.Map;
import net.xeoh.plugins.base.annotations.PluginImplementation;
import net.xeoh.plugins.base.annotations.meta.Author;
import org.jdom2.Element;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

@Author(name="Tamas Takacs")
@Name(name="EquityChart Benchmark plugin")
@Category(name="EquityChart")
@License(text="")
@ShortDesc(text="Short description")
@HideDatabankChoice
@PluginImplementation
public class Benchmark
implements IEquityChartAddon {
    private static final String NormOff = "off";
    private static final String NormDD = "drawdown";
    private static final String NormDDPct = "drawdownPct";
    private static final String NormMM = "moneyManagement";
    private static final String NormExposure = "exposure";
    private static final Logger Log = LoggerFactory.getLogger(Benchmark.class);

    public String getProduct() {
        return "SQUANTAlgoWizardBACKTESTNODE";
    }

    public int getPreferredPosition() {
        return 300;
    }

    public void initPlugin() throws Exception {
    }

    public String getName() {
        return "Benchmark";
    }

    public void print(EquityChart chart, ResultsGroup resultsGroup, String resultKey, OrdersList orders, Map<String, String[]> params, String domainAxisType) throws Exception {
        boolean benchmarkActive = Boolean.parseBoolean(params.get("benchmarkActive")[0]);
        if (!benchmarkActive) {
            return;
        }
        if (!domainAxisType.equals("time")) {
            return;
        }
        try {
            double initialCapital;
            DataInfo dataInfo;
            BenchmarkTable benchmarkTable = chart.benchmark;
            String symbol = params.get("benchmarkSymbol")[0];
            String normalization = params.get("benchmarkNormalization")[0];
            boolean displayStats = false;
            if (MainApp.isBacktestNode()) {
                symbol = symbol.replace("_benchmark", "");
            }
            if ((dataInfo = DataManager.getDataInfo((String)"History", (String)symbol)) == null) {
                Log.info(String.format("Cannot print benchmark, missing '%s' data.", symbol));
                return;
            }
            byte direction = Byte.parseByte(params.get("direction")[0]);
            byte sampleType = Byte.parseByte(params.get("sampleType")[0]);
            long[] dateRange = EquityChartUtils.dateRange((OrdersList)orders, (boolean)resultsGroup.isStockpickerStrategy());
            long from = dateRange[0];
            long to = dateRange[1];
            Log.info(String.format("SPY benchmark from %s to %s ...", SQTime.toDateString((long)from), SQTime.toDateString((long)to)));
            double spread = 2.5;
            String session = "No Session";
            ChartDef chartDef = new ChartDef("History", symbol, "D1", from, to, spread, session);
            IDataLoader loader = DataManager.getDataLoader((ChartDef)chartDef, (int)1, null);
            loader.open();
            ObjectArrayList valuesSPY = new ObjectArrayList();
            while (loader.hasNextTick()) {
                VersatileData vd = new VersatileData();
                loader.getNextTick(vd);
                valuesSPY.add((Object)new XYValue(vd.time, vd.close));
            }
            double ratio = 1.0;
            SettingsMap settings = resultsGroup.portfolio().getSettings();
            Element elSettings = XMLUtil.stringToElement((String)resultsGroup.getLastSettings());
            Element elRiskMoneyManagement = elSettings.getChild("RiskMoneyManagement");
            MoneyManagementMethod mmMethod = ProjectConfigHelper.getMoneyManagement((Element)elRiskMoneyManagement.getChild("MoneyManagement"));
            double capital = initialCapital = mmMethod.getInitialCapital();
            SQStats statsStrategy = resultsGroup.portfolio().stats(direction, (byte)10, sampleType);
            double exposure = statsStrategy.getDouble("Exposure", 1.0);
            if (exposure == 0.0) {
                exposure = 1.0;
            }
            double dd = statsStrategy.getDouble("Drawdown", 1.0);
            double ddPct = statsStrategy.getDouble("DrawdownPct", 1.0);
            MainChartDataset dataset = new MainChartDataset("benchmark", valuesSPY.size());
            dataset.title = "SPY";
            dataset.color = "#ffb347";
            dataset.thickness = 3;
            chart.addMainChartDataset(dataset);
            NormalizedData ndSPY = this.normalizeByExposure((ObjectArrayList<XYValue>)valuesSPY, resultsGroup, null, dataInfo, initialCapital, 1.0, 100.0);
            double corr = this.calculateCorrelationStrategySPY(chart, ndSPY.equityMap);
            NormalizedData ndBenchmark = null;
            this.printHeader(chart, displayStats);
            double netProfit = statsStrategy.getDouble("NetProfit", 1.0);
            this.printLine(chart, "Strategy", "#3366CC", 85, netProfit, dd, ddPct, exposure, corr, displayStats);
            NormalizedData ndPctDD = this.computeNormalizedByPctDD(ddPct, ndSPY, (ObjectArrayList<XYValue>)valuesSPY, resultsGroup, dataInfo, initialCapital);
            if (normalization.equals(NormOff)) {
                this.printLine(chart, "SPY", "#A9A9A9", 110, ndSPY.equitySPY, ndSPY.dd, ndSPY.ddPct, 100.0, 0.0, displayStats);
                this.fillDatasetValues((ChartDataset)dataset, (ObjectArrayList<XYValue>)valuesSPY, ndSPY.equityMap);
                ndBenchmark = ndSPY;
            } else if (normalization.equals(NormDD)) {
                ratio = dd / ndSPY.dd;
                NormalizedData ndDD = this.normalizeByExposure((ObjectArrayList<XYValue>)valuesSPY, resultsGroup, null, dataInfo, initialCapital, ratio, 100.0);
                this.printLine(chart, "SPY (norm. $ drawdown)", "#A9A9A9", 160, ndDD.equitySPY, ndDD.dd, ndDD.ddPct, 100.0, 0.0, displayStats);
                this.fillDatasetValues((ChartDataset)dataset, (ObjectArrayList<XYValue>)valuesSPY, ndDD.equityMap);
                ndBenchmark = ndDD;
            } else if (normalization.equals(NormDDPct)) {
                this.printLine(chart, "SPY (norm. $ drawdown)", "#A9A9A9", 160, ndPctDD.equitySPY, ndPctDD.dd, ndPctDD.ddPct, 100.0, 0.0, displayStats);
                this.fillDatasetValues((ChartDataset)dataset, (ObjectArrayList<XYValue>)valuesSPY, ndPctDD.equityMap);
                ndBenchmark = ndPctDD;
            } else if (normalization.equals(NormMM)) {
                NormalizedData ndMM = this.normalizeByExposure((ObjectArrayList<XYValue>)valuesSPY, resultsGroup, mmMethod, dataInfo, initialCapital, 1.0, 100.0);
                this.printLine(chart, "SPY (norm. MM)", "#A9A9A9", 160, ndMM.equitySPY, ndMM.dd, ndMM.ddPct, 100.0, 0.0, displayStats);
                this.fillDatasetValues((ChartDataset)dataset, (ObjectArrayList<XYValue>)valuesSPY, ndMM.equityMap);
                ndBenchmark = ndMM;
            } else if (normalization.equals(NormExposure)) {
                capital = initialCapital / 100.0 * exposure;
                NormalizedData ndExp = this.normalizeByExposure((ObjectArrayList<XYValue>)valuesSPY, resultsGroup, null, dataInfo, capital, 1.0, exposure);
                double spyExposureDD = ndExp.dd;
                this.printLine(chart, "SPY (norm. exposure)", "#A9A9A9", 135, ndExp.equitySPY, ndExp.dd, ndExp.ddPct, exposure, 0.0, displayStats);
                this.fillDatasetValues((ChartDataset)dataset, (ObjectArrayList<XYValue>)valuesSPY, ndExp.equityMap);
                ndBenchmark = ndExp;
            }
            if (ndBenchmark == null) {
                throw new Exception("Normalization method was not recognized?!");
            }
            SQStats statsNorm = ndBenchmark.calculateStats(resultsGroup, elSettings, direction, (byte)10, sampleType);
            SQStats statsNormDDPct = ndPctDD.calculateStats(resultsGroup, elSettings, direction, (byte)10, sampleType);
            benchmarkTable.fill(resultsGroup, mmMethod, symbol, statsStrategy, corr, normalization, ndBenchmark.initBuyAmount, statsNorm, statsNormDDPct);
            byte ddType = Byte.parseByte(params.get(NormDD)[0]);
            SubChart ddChart = chart.findSubChartByKey("Drawdown");
            if (ddChart != null && (ddType == 10 || ddType == 40 || ddType == 20 || ddType == 50)) {
                SubChartDataset ddDataset = new SubChartDataset("DrawdownBenchmark", ndBenchmark.ddMapMoney.size());
                ddDataset.setName("Drawdown Benchmark");
                ddDataset.type = "line";
                ddDataset.color = "#ffb347";
                ddDataset.thickness = 3;
                ddChart.addDataset(ddDataset);
                if (ddType == 10 || ddType == 40) {
                    this.fillDatasetValues((ChartDataset)ddDataset, (ObjectArrayList<XYValue>)valuesSPY, ndBenchmark.ddMapMoney);
                } else if (ddType == 20 || ddType == 50) {
                    this.fillDatasetValues((ChartDataset)ddDataset, (ObjectArrayList<XYValue>)valuesSPY, ndBenchmark.ddMapPct);
                }
            }
            MainChartDataset mainDataset = (MainChartDataset)chart.getMainChartDatasets().get(0);
            mainDataset.thickness = 3;
        }
        catch (Exception e) {
            throw new Exception("Error while printing SPY benchmark. Exc.", e);
        }
    }

    private NormalizedData computeNormalizedByPctDD(double ddPct, NormalizedData ndSPY, ObjectArrayList<XYValue> valuesSPY, ResultsGroup resultsGroup, DataInfo dataInfo, double initialCapital) throws Exception {
        NormalizedData ndPctDDBest = new NormalizedData();
        ddPct = SQUtils.round2((double)ddPct);
        double ratio = ddPct / ndSPY.ddPct;
        NormalizedData nd = this.normalizeByExposure(valuesSPY, resultsGroup, null, dataInfo, initialCapital, ratio, 100.0);
        double bestDiff = ddPct - nd.ddPct;
        if (Math.abs(bestDiff) < 0.015) {
            Log.info("Matching PctDD found in cycles: 0");
            return nd;
        }
        double bestRatio = ratio;
        double diff = bestDiff;
        double ratioMult = 0.2;
        int cycles = 0;
        for (int i = 0; i < 30; ++i) {
            cycles = i;
            ratio = diff > 0.0 ? bestRatio * (1.0 + ratioMult) : bestRatio * (1.0 - ratioMult);
            nd = this.normalizeByExposure(valuesSPY, resultsGroup, null, dataInfo, initialCapital, ratio, 100.0);
            diff = ddPct - nd.ddPct;
            if (SQUtils.round2((double)nd.ddPct) == ddPct || Math.abs(diff) <= 0.01) {
                Log.debug("Matching PctDD found in cycles: {}", (Object)cycles);
                return nd;
            }
            if (Math.abs(diff) < Math.abs(bestDiff)) {
                bestDiff = Math.abs(diff);
                bestRatio = ratio;
                ndPctDDBest = nd;
                continue;
            }
            ratioMult /= 2.0;
        }
        Log.info("Matching PctDD found in cycles: {}", (Object)cycles);
        return ndPctDDBest;
    }

    private NormalizedData normalizeByExposure(ObjectArrayList<XYValue> valuesSPY, ResultsGroup resultsGroup, MoneyManagementMethod mmMethod, DataInfo dataInfo, double capital, double ratio, double exposure) throws Exception {
        OrdersList ordersList;
        Long2DoubleAVLTreeMap equityMapSPYNorm;
        NormalizedData nd = new NormalizedData();
        nd.equityMap = equityMapSPYNorm = new Long2DoubleAVLTreeMap();
        nd.ddMapMoney = new Long2DoubleAVLTreeMap();
        nd.ddMapPct = new Long2DoubleAVLTreeMap();
        nd.ddMapPips = new Long2DoubleAVLTreeMap();
        nd.ordersList = ordersList = new OrdersList("normalized");
        double openPrice = 0.0;
        long openTime = 0L;
        double size = 0.0;
        double equitySPYNorm = 0.0;
        double maxPctDD = 9.9999999E7;
        double maxDD = 9.9999999E7;
        double peakEquity = capital;
        double equityMoney = capital;
        for (int i = 0; i < valuesSPY.size(); ++i) {
            long currentTime = SQTime.getDateInMs((long)((XYValue)valuesSPY.get((int)i)).x);
            double currentPrice = ((XYValue)valuesSPY.get((int)i)).y;
            if (i == 0) {
                openPrice = currentPrice;
                openTime = currentTime;
                try {
                    if (mmMethod != null) {
                        StrategyBase sb = StrategyBase.createXmlStrategy((Element)resultsGroup.getStrategyXml());
                        sb.accountBalance = capital;
                        sb.accountEquity = capital;
                        size = mmMethod.computeTradeSize(sb, dataInfo.symbol, (byte)1, openPrice, 0.0, dataInfo.symbolInfo.tickSize, dataInfo.symbolInfo.pointValue);
                    } else {
                        size = capital / openPrice;
                    }
                    nd.initBuyAmount = size * openPrice / 100.0 * exposure * ratio;
                }
                catch (Exception e) {
                    throw new Exception("Failed to calculate initial buy amount from MoneyManagement method - " + e.getMessage(), e);
                }
            }
            equitySPYNorm = (currentPrice - openPrice) * size * ratio;
            equityMapSPYNorm.put(currentTime, equitySPYNorm);
            Order o = new Order();
            o.Type = 1;
            o.PL = (float)(capital + equitySPYNorm - equityMoney);
            o.PctPL = (float)OrderPLComputer.getPercentagePL((double)o.PL, (double)capital);
            o.OpenPrice = (float)openPrice;
            o.ClosePrice = (float)currentPrice;
            o.OpenTime = openTime;
            o.CloseTime = currentTime;
            ordersList.add(o);
            equityMoney = capital + equitySPYNorm;
            double DD = (float)this.specialSubtraction(peakEquity, equityMoney);
            double PctDD = (float)this.getPercentageDD(DD, peakEquity);
            nd.ddMapMoney.put(SQTime.getDateInMs((long)currentTime), DD);
            nd.ddMapPct.put(SQTime.getDateInMs((long)currentTime), PctDD);
            if (PctDD < maxPctDD) {
                maxPctDD = PctDD;
            }
            if (DD < maxDD) {
                maxDD = DD;
            }
            if (!(equityMoney > peakEquity)) continue;
            peakEquity = equityMoney;
        }
        nd.equitySPY = equitySPYNorm;
        nd.dd = SQUtils.round2((double)Math.abs(maxDD));
        nd.ddPct = SQUtils.round2((double)Math.abs(maxPctDD));
        return nd;
    }

    private void printHeader(EquityChart chart, boolean displayStats) {
        if (!displayStats) {
            return;
        }
        chart.drawText("Benchmark", "#A9A9A9", "11px Arial", 130, 60);
        chart.drawText("Profit", "#A9A9A9", "11px Arial", 330, 60);
        chart.drawText("Max DD", "#A9A9A9", "11px Arial", 480, 60);
        chart.drawText("Max DD %", "#A9A9A9", "11px Arial", 580, 60);
        chart.drawText("Return/DD", "#A9A9A9", "11px Arial", 680, 60);
        chart.drawText("Exposure", "#A9A9A9", "11px Arial", 780, 60);
        chart.drawText("Corr. with SPY", "#A9A9A9", "11px Arial", 880, 60);
    }

    private void printLine(EquityChart chart, String metricName, String color, int yPos, double netProfit, double dd, double ddPct, double exposure, double corr, boolean displayStats) {
        if (!displayStats) {
            return;
        }
        double retDDRatio = SQUtils.round2((double)SQUtils.safeDivide((double)netProfit, (double)dd));
        chart.drawText(metricName, color, "15px Arial", 130, yPos);
        chart.drawText(PlTypes.printPL((double)netProfit, (byte)10), color, "15px Arial", 330, yPos);
        chart.drawText(PlTypes.printPL((double)dd, (byte)10), color, "15px Arial", 480, yPos);
        chart.drawText(PlTypes.printPL((double)ddPct, (byte)20), color, "15px Arial", 580, yPos);
        chart.drawText(SQUtils.d2((double)retDDRatio), color, "15px Arial", 680, yPos);
        chart.drawText(PlTypes.printPL((double)exposure, (byte)20), color, "15px Arial", 780, yPos);
        if (corr != 0.0) {
            chart.drawText(SQUtils.d2((double)corr), color, "15px Arial", 880, yPos);
        }
    }

    private void fillDatasetValues(ChartDataset dataset, ObjectArrayList<XYValue> valuesSPY, Long2DoubleAVLTreeMap equityMap) {
        for (int i = 0; i < valuesSPY.size(); ++i) {
            long currentTime = ((XYValue)valuesSPY.get((int)i)).x;
            double value = equityMap.get(currentTime);
            dataset.addValue(currentTime, value);
        }
    }

    private double calculateCorrelationStrategySPY(EquityChart chart, Long2DoubleAVLTreeMap equityMapSPY) {
        MainChartDataset mainChartDataset = (MainChartDataset)chart.getMainChartDatasets().get(0);
        long[] corrDatesStrategy = mainChartDataset.xVals;
        double[] corrValuesStrategy = mainChartDataset.yVals;
        double[] corrValuesSPY = new double[corrValuesStrategy.length];
        for (int i = 0; i < corrDatesStrategy.length; ++i) {
            if (!equityMapSPY.containsKey(corrDatesStrategy[i])) continue;
            corrValuesSPY[i] = equityMapSPY.get(corrDatesStrategy[i]);
        }
        double corr = CorrelationComputer.calculateCorrelation((double[])corrValuesStrategy, (double[])corrValuesSPY);
        return corr;
    }

    private double specialSubtraction(double peak, double equity) {
        double dd = peak - equity;
        if (dd < 0.0) {
            dd = 0.0;
        }
        return -1.0 * dd;
    }

    private double getPercentageDD(double pl, double equity) {
        if (equity <= 0.0 || pl > equity) {
            return -1.0;
        }
        return pl / (equity / 100.0);
    }

    private class NormalizedData {
        public Long2DoubleAVLTreeMap equityMap;
        public double equitySPY;
        public double dd;
        public double ddPct;
        public OrdersList ordersList;
        public double initBuyAmount;
        public Long2DoubleAVLTreeMap ddMapMoney;
        public Long2DoubleAVLTreeMap ddMapPct;
        public Long2DoubleAVLTreeMap ddMapPips;

        private NormalizedData() {
        }

        public SQStats calculateStats(ResultsGroup resultsGroup, Element elSettings, byte direction, byte plType, byte sampleType) throws Exception {
            StatsComputer sc = new StatsComputer();
            sc.initializeWithOrders(this.ordersList, true);
            StatsTypeCombination combination = new StatsTypeCombination(direction, plType, sampleType);
            SettingsMap settings = resultsGroup.portfolio().getSettings();
            ChartSetup chartSetup = (ChartSetup)settings.get("BacktestChart");
            if (chartSetup == null) {
                try {
                    Element elData = elSettings.getChild("Data");
                    ChartSetups chartSetups = ProjectConfigHelper.getChartSetups((Element)elData);
                    settings.set("BacktestChart", (Object)chartSetups.getMainSetup());
                }
                catch (Exception e) {
                    Log.error("Failed to obtain ChartSetups object from  RG settings.", (Throwable)e);
                }
            }
            SQStats stats = sc.computeStats(null, combination, settings);
            return stats;
        }
    }
}

