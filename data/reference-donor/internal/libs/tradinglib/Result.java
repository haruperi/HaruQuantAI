/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  com.strategyquant.lib.SQUtils
 *  com.strategyquant.lib.SettingsMap
 *  com.strategyquant.lib.TimePeriod
 *  com.strategyquant.lib.ValuesMap
 *  com.strategyquant.lib.XMLUtil
 *  com.strategyquant.lib.app.MainApp
 *  it.unimi.dsi.fastutil.ints.Int2ObjectOpenHashMap
 *  it.unimi.dsi.fastutil.longs.Long2FloatRBTreeMap
 *  org.jdom2.Content
 *  org.jdom2.Element
 *  org.slf4j.Logger
 *  org.slf4j.LoggerFactory
 */
package com.strategyquant.tradinglib;

import com.strategyquant.lib.SQUtils;
import com.strategyquant.lib.SettingsMap;
import com.strategyquant.lib.TimePeriod;
import com.strategyquant.lib.ValuesMap;
import com.strategyquant.lib.XMLUtil;
import com.strategyquant.lib.app.MainApp;
import com.strategyquant.tradinglib.BadStrategyException;
import com.strategyquant.tradinglib.FitnessCollection;
import com.strategyquant.tradinglib.OrdersList;
import com.strategyquant.tradinglib.ResultsGroup;
import com.strategyquant.tradinglib.SQStats;
import com.strategyquant.tradinglib.SampleTypes;
import com.strategyquant.tradinglib.StatsDontExistException;
import com.strategyquant.tradinglib.StatsTypeCombination;
import com.strategyquant.tradinglib.StrategyBase;
import com.strategyquant.tradinglib.engine.TradingSetup;
import com.strategyquant.tradinglib.engine.stockpicker.Stockpicker;
import com.strategyquant.tradinglib.engine.stockpicker.data.LoadedPickerData;
import com.strategyquant.tradinglib.equitychart.Periods;
import com.strategyquant.tradinglib.results.stats.StatsComputer;
import com.strategyquant.tradinglib.robustnesstests.MCSimulations;
import com.strategyquant.tradinglib.robustnesstests.RobustnessResults;
import com.strategyquant.tradinglib.robustnesstests.SequentialOptimizationResults;
import com.strategyquant.tradinglib.stockchart.StockSaverForStockPicking;
import com.strategyquant.tradinglib.stockchart.StockSaverOriginalFormat;
import com.strategyquant.tradinglib.strategy.OutOfSample;
import com.strategyquant.tradinglib.util.TradingLibUtil;
import it.unimi.dsi.fastutil.ints.Int2ObjectOpenHashMap;
import it.unimi.dsi.fastutil.longs.Long2FloatRBTreeMap;
import java.io.BufferedInputStream;
import java.io.BufferedOutputStream;
import java.io.File;
import java.io.FileInputStream;
import java.io.FileOutputStream;
import java.io.IOException;
import java.io.InputStream;
import java.io.OutputStream;
import java.nio.file.Files;
import java.util.List;
import java.util.concurrent.locks.ReentrantLock;
import java.util.jar.Attributes;
import java.util.jar.JarOutputStream;
import java.util.jar.Manifest;
import org.jdom2.Content;
import org.jdom2.Element;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

public class Result
extends ValuesMap {
    public static final Logger Log = LoggerFactory.getLogger((String)"Result");
    private static final int[] ignoredSettings = new int[]{"Commission".hashCode(), "BacktestChart".hashCode(), "MoneyManagement.Method".hashCode(), "RiskManagement".hashCode(), "OutOfSample".hashCode(), "StrategyXml".hashCode()};
    private ResultsGroup resultsGroup;
    private String resultKey;
    private transient SettingsMap settings;
    private transient StrategyBase strategyObj;
    private Element strategyXml = null;
    private ReentrantLock chartsDataLock = new ReentrantLock();
    private ReentrantLock dailyEquityLock = new ReentrantLock();
    private ReentrantLock maxDailyDDLock = new ReentrantLock();
    private ReentrantLock maxDailyDDPctLock = new ReentrantLock();
    private String stockChartPath;
    private Long2FloatRBTreeMap worstDailyEquity;
    private Long2FloatRBTreeMap maxDailyDD;
    private Long2FloatRBTreeMap maxDailyDDPct;
    private boolean specialResult = false;
    private MCSimulations mcManipulationSimulations;
    private MCSimulations mcRetestSimulations;
    private FitnessCollection fitnessCollection = new FitnessCollection();
    private SequentialOptimizationResults sequentialOptimizationResults;

    public Result(ResultsGroup resultsGroup) {
        this.resultsGroup = resultsGroup;
    }

    public Result(String string, ResultsGroup resultsGroup, SettingsMap settingsMap) {
        this.resultKey = string;
        if (!string.equals("Portfolio")) {
            String[] stringArray = string.split("/");
        }
        this.resultsGroup = resultsGroup;
        this.settings = settingsMap;
    }

    public Result clone(ResultsGroup resultsGroup) {
        Result result = new Result(resultsGroup);
        result.resultKey = this.resultKey;
        result.strategyObj = this.strategyObj;
        result.strategyXml = this.strategyXml != null ? this.strategyXml.clone() : this.strategyXml;
        result.stockChartPath = this.cloneStockChart(this.stockChartPath);
        if (this.fitnessCollection != null) {
            result.fitnessCollection = this.fitnessCollection.clone();
        }
        if (this.getWorstDailyEquity() != null) {
            result.setWorstDailyEquity(this.getWorstDailyEquity().clone());
        }
        if (this.getMaxDailyDD() != null) {
            result.setMaxDailyDD(this.getMaxDailyDD().clone());
        }
        if (this.getMaxDailyDDPct() != null) {
            result.setMaxDailyDDPct(this.getMaxDailyDDPct().clone());
        }
        if (this.settings != null) {
            result.settings = this.settings.clone();
        }
        result.values = SQUtils.cloneValuesMap((Int2ObjectOpenHashMap)this.values);
        try {
            if (this.mcManipulationSimulations != null) {
                result.mcManipulationSimulations = this.mcManipulationSimulations.getClone();
            }
            if (this.mcRetestSimulations != null) {
                result.mcRetestSimulations = this.mcRetestSimulations.getClone();
            }
            if (this.sequentialOptimizationResults != null) {
                result.sequentialOptimizationResults = this.sequentialOptimizationResults.getClone();
            }
        }
        catch (Exception exception) {
            Log.error("Cannot clone MC simulation results!", (Throwable)exception);
        }
        return result;
    }

    /*
     * WARNING - Removed try catching itself - possible behaviour change.
     */
    private String cloneStockChart(String string) {
        if (string == null) {
            return null;
        }
        File file = new File(string);
        if (file != null && file.exists()) {
            InputStream inputStream = null;
            OutputStream outputStream = null;
            try {
                int n;
                inputStream = new BufferedInputStream(new FileInputStream(file));
                File file2 = new File(file.getParent());
                File file3 = File.createTempFile("sq4-stock-", ".jar", file2);
                outputStream = new BufferedOutputStream(new FileOutputStream(file3));
                file3.deleteOnExit();
                byte[] byArray = new byte[1024];
                while ((n = inputStream.read(byArray)) > 0) {
                    outputStream.write(byArray, 0, n);
                    outputStream.flush();
                }
                String string2 = file3.getAbsolutePath();
                return string2;
            }
            catch (Exception exception) {
                Log.error("Cannot copy chart file " + string, (Throwable)exception);
            }
            finally {
                if (inputStream != null) {
                    try {
                        inputStream.close();
                    }
                    catch (Exception exception) {
                        Log.error("Failed to close InputStream", (Throwable)exception);
                    }
                }
                if (outputStream != null) {
                    try {
                        outputStream.close();
                    }
                    catch (Exception exception) {
                        Log.error("Failed to close OutputStream", (Throwable)exception);
                    }
                }
            }
        }
        return null;
    }

    public void setFrom(Result result, String string) {
        this.resultKey = string;
        this.strategyObj = result.strategyObj;
        this.strategyXml = result.strategyXml;
        this.stockChartPath = result.stockChartPath;
        if (result.settings != null) {
            this.settings = result.settings.clone();
        }
        this.mcManipulationSimulations = result.mcManipulationSimulations;
        this.mcRetestSimulations = result.mcRetestSimulations;
        this.values = result.values.clone();
    }

    public SQStats stats(StatsTypeCombination statsTypeCombination) throws Exception {
        return this.stats(statsTypeCombination.getDirection(), statsTypeCombination.getPLType(), statsTypeCombination.getSampleType());
    }

    public SQStats stats(byte by, byte by2, byte by3) throws StatsDontExistException {
        int n = StatsTypeCombination.createKey(by, by2, by3);
        if (!this.containsKey(n)) {
            throw new StatsDontExistException("Result doesn't contain stats for '" + n + "', call rg.computeAllStats() before calling this method! D: " + by + ", PL: " + by2 + ", S: " + by3);
        }
        return (SQStats)this.get(n);
    }

    public SQStats statsOrNull(byte by, byte by2, byte by3) {
        int n = StatsTypeCombination.createKey(by, by2, by3);
        if (!this.containsKey(n)) {
            return null;
        }
        return (SQStats)this.get(n);
    }

    public void addStrategy(StrategyBase strategyBase) {
        this.strategyObj = strategyBase;
    }

    public StrategyBase getStrategy() {
        return this.strategyObj;
    }

    public void addStrategyXml(Element element) {
        this.strategyXml = element;
    }

    public Element getStrategyXml() {
        return this.strategyXml;
    }

    public SettingsMap getSettings() {
        return this.settings;
    }

    public void setSettings(SettingsMap settingsMap) {
        this.settings = settingsMap;
    }

    public String getResultKey() {
        return this.resultKey;
    }

    public Element getXML() {
        Element element = new Element("Result");
        XMLUtil.trySetAttr((Element)element, (String)"resultKey", (Object)this.resultKey);
        XMLUtil.trySetAttr((Element)element, (String)"special", (Object)Boolean.toString(this.isSpecial()));
        element.addContent((Content)this.fitnessCollection.getXML());
        Element element2 = super.getXML();
        element.addContent((Content)element2);
        if (this.settings != null) {
            Element element3 = this.settings.getXML();
            element.addContent((Content)element3);
        }
        return element;
    }

    public void setFromXML(Element element) {
        Element element2 = element.getChild("SettingsMap");
        Element element3 = element.getChild("ValuesMap");
        this.fitnessCollection.setFromXML(element);
        this.values.clear();
        Object object = element3.getChildren().iterator();
        while (object.hasNext()) {
            Element element4 = (Element)object.next();
            String string = SQUtils.decodeXmlKey((String)element4.getName());
            Object object2 = null;
            if (element4.getContentSize() > 0) {
                object2 = TradingLibUtil.elementToValue(element4);
            }
            if (string.startsWith("stats")) {
                int n = ValuesMap.getStatsIntKeyFromString((String)string);
                this.set(n, object2);
                continue;
            }
            this.set(string, object2);
        }
        this.resultKey = element.getAttributeValue("resultKey").intern();
        this.settings = new SettingsMap();
        if (element2 != null) {
            this.settings.setFromXML(element2, ignoredSettings);
        }
        this.specialResult = (object = element.getAttributeValue("special")) != null ? Boolean.parseBoolean((String)object) : false;
    }

    public void computeAllStats(SettingsMap settingsMap, OutOfSample outOfSample) throws Exception {
        OrdersList ordersList = this.resultsGroup.orders().filter(this.resultKey, (byte)0, (byte)127);
        this.settings.set("AddCommissionSwapToPL", (Object)true);
        if (outOfSample == null) {
            outOfSample = this.saveChartOOSSettings(ordersList);
        }
        StatsComputer statsComputer = new StatsComputer();
        statsComputer.setRGSpecialValues(settingsMap);
        statsComputer.initializeWithOrders(ordersList);
        StatsTypeCombination statsTypeCombination = new StatsTypeCombination(1, 10, 127);
        boolean bl = MainApp.settings().getBoolean("ComputePipsMetrics", false);
        boolean bl2 = MainApp.settings().getBoolean("ComputePctsMetrics", false);
        boolean bl3 = MainApp.settings().getBoolean("ComputeSeparateMetrics", true);
        this.computeSubStats(statsComputer, statsTypeCombination, (byte)10, bl, bl2, bl3, outOfSample);
        if (outOfSample == null || outOfSample.isEmpty()) {
            this.computeNoOOSStats(statsComputer, statsTypeCombination, bl, bl2, bl3);
        } else {
            this.computeSubStats(statsComputer, statsTypeCombination, (byte)20, bl, bl2, bl3, outOfSample);
            this.computeSubStats(statsComputer, statsTypeCombination, (byte)127, bl, bl2, bl3, outOfSample);
        }
        if (!this.resultKey.equals("Portfolio") && !this.specialResult) {
            int n = statsComputer.checkStrategyProblems(this.resultKey, this.getStrategyProblems());
            int n2 = this.getSettings().getInt("StrategyDismissSettings", 0);
            if ((n2 & n) != 0) {
                throw new BadStrategyException(512);
            }
        }
    }

    private void computeNoOOSStats(StatsComputer statsComputer, StatsTypeCombination statsTypeCombination, boolean bl, boolean bl2, boolean bl3) {
        this.copyStats(statsTypeCombination, (byte)10, (byte)127, bl, bl2);
        SQStats sQStats = statsComputer.computeZeroStats();
        this.setZeroStats(sQStats, statsTypeCombination.set((byte)1, (byte)10, (byte)20));
        if (bl2) {
            this.setZeroStats(sQStats, statsTypeCombination.set((byte)1, (byte)20, (byte)20));
        }
        if (bl) {
            this.setZeroStats(sQStats, statsTypeCombination.set((byte)1, (byte)30, (byte)20));
        }
        this.setZeroStats(sQStats, statsTypeCombination.set((byte)-1, (byte)10, (byte)20));
        if (bl2) {
            this.setZeroStats(sQStats, statsTypeCombination.set((byte)-1, (byte)20, (byte)20));
        }
        if (bl) {
            this.setZeroStats(sQStats, statsTypeCombination.set((byte)-1, (byte)30, (byte)20));
        }
        this.setZeroStats(sQStats, statsTypeCombination.set((byte)0, (byte)10, (byte)20));
        if (bl2) {
            this.setZeroStats(sQStats, statsTypeCombination.set((byte)0, (byte)20, (byte)20));
        }
        if (bl) {
            this.setZeroStats(sQStats, statsTypeCombination.set((byte)0, (byte)30, (byte)20));
        }
    }

    private void setZeroStats(SQStats sQStats, StatsTypeCombination statsTypeCombination) {
        int n = statsTypeCombination.getKey();
        this.set(n, sQStats);
    }

    private OutOfSample saveChartOOSSettings(OrdersList ordersList) {
        try {
            Periods periods = new Periods();
            List<TimePeriod> list = periods.getAvailablePeriods(ordersList, "time");
            OutOfSample outOfSample = new OutOfSample();
            for (int i = 0; i < list.size(); ++i) {
                TimePeriod timePeriod = list.get(i);
                if (timePeriod.type == 11) continue;
                outOfSample.addRange(timePeriod.from, timePeriod.to, timePeriod.type);
            }
            this.settings.set("ChartOOS", (Object)outOfSample);
            return outOfSample;
        }
        catch (Exception exception) {
            Log.error("Cannot save chart oos time periods", (Throwable)exception);
            return null;
        }
    }

    private void computeSubStats(StatsComputer statsComputer, StatsTypeCombination statsTypeCombination, byte by, boolean bl, boolean bl2, boolean bl3, OutOfSample outOfSample) throws Exception {
        if (outOfSample == null) {
            this.computeSubSubStats(statsComputer, statsTypeCombination, by, bl, bl2);
            return;
        }
        if (by == 20) {
            int n;
            for (n = 0; n < 10; ++n) {
                this.cleanStats(statsTypeCombination, (byte)20, n, bl, bl2);
            }
            n = outOfSample.getRangesCount();
            int n2 = 0;
            if (bl3) {
                for (int i = 0; i < n; ++i) {
                    byte by2 = outOfSample.getPartType(i);
                    if (!SampleTypes.isOOS(by2)) continue;
                    ++n2;
                    this.computeSubSubStats(statsComputer, statsTypeCombination, by2, bl, bl2);
                }
            }
            if (n2 == 1) {
                this.copyStats(statsTypeCombination, (byte)21, (byte)20, bl, bl2);
            } else {
                this.computeSubSubStats(statsComputer, statsTypeCombination, (byte)20, bl, bl2);
            }
        } else if (by == 10) {
            int n;
            for (n = 0; n < 10; ++n) {
                this.cleanStats(statsTypeCombination, (byte)10, n, bl, bl2);
            }
            n = outOfSample.getRangesCount();
            int n3 = 0;
            if (bl3) {
                for (int i = 0; i < n; ++i) {
                    byte by3 = outOfSample.getPartType(i);
                    if (!SampleTypes.isISV(by3)) continue;
                    ++n3;
                    this.computeSubSubStats(statsComputer, statsTypeCombination, by3, bl, bl2);
                }
            }
            if (n3 > 0 || !bl3) {
                this.computeSubSubStats(statsComputer, statsTypeCombination, (byte)10, bl, bl2);
                this.computeSubSubStats(statsComputer, statsTypeCombination, (byte)11, bl, bl2);
                this.computeSubSubStats(statsComputer, statsTypeCombination, (byte)40, bl, bl2);
            } else {
                this.computeSubSubStats(statsComputer, statsTypeCombination, (byte)10, bl, bl2);
                this.copyStats(statsTypeCombination, (byte)10, (byte)11, bl, bl2);
            }
        } else if (by == 127) {
            this.computeSubSubStats(statsComputer, statsTypeCombination, (byte)127, bl, bl2);
        } else {
            throw new Exception("Trying to compute stats for strange sample type: " + by);
        }
    }

    private void cleanStats(StatsTypeCombination statsTypeCombination, byte by, int n, boolean bl, boolean bl2) {
        if (by == 20) {
            this.remove(StatsTypeCombination.createKey((byte)1, (byte)10, OutOfSample.getOOSPart(n + 1)));
            this.remove(StatsTypeCombination.createKey((byte)1, (byte)20, OutOfSample.getOOSPart(n + 1)));
            this.remove(StatsTypeCombination.createKey((byte)1, (byte)30, OutOfSample.getOOSPart(n + 1)));
        } else if (by == 10) {
            this.remove(StatsTypeCombination.createKey((byte)1, (byte)10, OutOfSample.getISVPart(n + 1)));
            this.remove(StatsTypeCombination.createKey((byte)1, (byte)20, OutOfSample.getISVPart(n + 1)));
            this.remove(StatsTypeCombination.createKey((byte)1, (byte)30, OutOfSample.getISVPart(n + 1)));
        }
    }

    private void copyStats(StatsTypeCombination statsTypeCombination, byte by, byte by2, boolean bl, boolean bl2) {
        this.set(StatsTypeCombination.createKey((byte)1, (byte)10, by2), this.get(StatsTypeCombination.createKey((byte)1, (byte)10, by)));
        if (bl2) {
            this.set(StatsTypeCombination.createKey((byte)1, (byte)20, by2), this.get(StatsTypeCombination.createKey((byte)1, (byte)20, by)));
        }
        if (bl) {
            this.set(StatsTypeCombination.createKey((byte)1, (byte)30, by2), this.get(StatsTypeCombination.createKey((byte)1, (byte)30, by)));
        }
        this.set(StatsTypeCombination.createKey((byte)-1, (byte)10, by2), this.get(StatsTypeCombination.createKey((byte)-1, (byte)10, by)));
        if (bl2) {
            this.set(StatsTypeCombination.createKey((byte)-1, (byte)20, by2), this.get(StatsTypeCombination.createKey((byte)-1, (byte)20, by)));
        }
        if (bl) {
            this.set(StatsTypeCombination.createKey((byte)-1, (byte)30, by2), this.get(StatsTypeCombination.createKey((byte)-1, (byte)30, by)));
        }
        this.set(StatsTypeCombination.createKey((byte)0, (byte)10, by2), this.get(StatsTypeCombination.createKey((byte)0, (byte)10, by)));
        if (bl2) {
            this.set(StatsTypeCombination.createKey((byte)0, (byte)20, by2), this.get(StatsTypeCombination.createKey((byte)0, (byte)20, by)));
        }
        if (bl) {
            this.set(StatsTypeCombination.createKey((byte)0, (byte)30, by2), this.get(StatsTypeCombination.createKey((byte)0, (byte)30, by)));
        }
    }

    private void computeSubSubStats(StatsComputer statsComputer, StatsTypeCombination statsTypeCombination, byte by, boolean bl, boolean bl2) throws Exception {
        statsComputer.filterBy(this.resultKey, (byte)1, by);
        statsComputer.sortAndComputeOrderValues(this.settings, this.resultsGroup.symbols());
        this.computeComputeStats(statsComputer, statsTypeCombination.set((byte)1, (byte)10, by));
        if (bl2) {
            this.computeComputeStats(statsComputer, statsTypeCombination.set((byte)1, (byte)20, by));
        }
        if (bl) {
            this.computeComputeStats(statsComputer, statsTypeCombination.set((byte)1, (byte)30, by));
        }
        statsComputer.filterBy(this.resultKey, (byte)-1, by);
        statsComputer.sortAndComputeOrderValues(this.settings, this.resultsGroup.symbols());
        this.computeComputeStats(statsComputer, statsTypeCombination.set((byte)-1, (byte)10, by));
        if (bl2) {
            this.computeComputeStats(statsComputer, statsTypeCombination.set((byte)-1, (byte)20, by));
        }
        if (bl) {
            this.computeComputeStats(statsComputer, statsTypeCombination.set((byte)-1, (byte)30, by));
        }
        statsComputer.filterBy(this.resultKey, (byte)0, by);
        statsComputer.sortAndComputeOrderValues(this.settings, this.resultsGroup.symbols());
        this.computeComputeStats(statsComputer, statsTypeCombination.set((byte)0, (byte)10, by));
        if (bl2) {
            this.computeComputeStats(statsComputer, statsTypeCombination.set((byte)0, (byte)20, by));
        }
        if (bl) {
            this.computeComputeStats(statsComputer, statsTypeCombination.set((byte)0, (byte)30, by));
        }
    }

    private void computeComputeStats(StatsComputer statsComputer, StatsTypeCombination statsTypeCombination) throws Exception {
        SQStats sQStats = statsComputer.computeStats(this, statsTypeCombination, this.settings);
        int n = statsTypeCombination.getKey();
        this.set(n, sQStats);
    }

    /*
     * WARNING - Removed try catching itself - possible behaviour change.
     */
    public void addTradingChartsData(TradingSetup tradingSetup, OrdersList ordersList, boolean bl) throws Exception {
        this.chartsDataLock.lock();
        try {
            File file = this.getTempFile(bl);
            StockSaverOriginalFormat stockSaverOriginalFormat = new StockSaverOriginalFormat();
            Manifest manifest = new Manifest();
            manifest.getMainAttributes().put(Attributes.Name.MANIFEST_VERSION, "1.0");
            try (JarOutputStream jarOutputStream = new JarOutputStream((OutputStream)new FileOutputStream(file), manifest);){
                jarOutputStream.setLevel(0);
                stockSaverOriginalFormat.save(jarOutputStream, tradingSetup, ordersList, this.resultKey);
            }
            this.stockChartPath = file.getAbsolutePath();
            this.resultsGroup.specialValues().set("ContainsChart", (Object)true);
        }
        finally {
            this.chartsDataLock.unlock();
        }
    }

    private File getTempFile(boolean bl) throws IOException {
        String string = "/internal/tmp/";
        String string2 = MainApp.getDataPath() + string + (bl ? "algo" : "stock");
        SQUtils.ensureDirExists((String)string2);
        File file = File.createTempFile("sq4-stock-", ".jar", new File(string2));
        return file;
    }

    /*
     * WARNING - Removed try catching itself - possible behaviour change.
     */
    public void addTradingChartsData(LoadedPickerData loadedPickerData, Stockpicker stockpicker, OrdersList ordersList, boolean bl) throws Exception {
        this.chartsDataLock.lock();
        try {
            File file = this.getTempFile(bl);
            StockSaverForStockPicking stockSaverForStockPicking = new StockSaverForStockPicking();
            Manifest manifest = new Manifest();
            manifest.getMainAttributes().put(Attributes.Name.MANIFEST_VERSION, "1.0");
            try (JarOutputStream jarOutputStream = new JarOutputStream((OutputStream)new FileOutputStream(file), manifest);){
                jarOutputStream.setLevel(0);
                stockSaverForStockPicking.save(jarOutputStream, loadedPickerData, stockpicker, ordersList, this.resultKey);
            }
            this.stockChartPath = file.getAbsolutePath();
            this.resultsGroup.specialValues().set("ContainsChart", (Object)true);
        }
        finally {
            this.chartsDataLock.unlock();
        }
    }

    public void clear(boolean bl, boolean bl2) {
        String[] stringArray = this.getAllKeys();
        for (int i = 0; i < stringArray.length; ++i) {
            Object object;
            if (stringArray[i] == null) continue;
            if (stringArray[i].contains("RobustnessSimulation")) {
                if (stringArray[i].contains("Orders")) {
                    object = (OrdersList)this.get(stringArray[i]);
                    if (object != null) {
                        ((OrdersList)object).clear();
                    }
                    this.values.remove(this.getKeyHash(stringArray[i]));
                    continue;
                }
                if (!stringArray[i].contains("Results")) continue;
                this.values.remove(this.getKeyHash(stringArray[i]));
                continue;
            }
            if (!stringArray[i].startsWith("stats") || !((object = this.get(ValuesMap.getStatsIntKeyFromString((String)stringArray[i]))) instanceof SQStats)) continue;
            ((SQStats)object).clearData();
        }
        if (this.mcManipulationSimulations != null) {
            this.mcManipulationSimulations.clear();
        }
        if (this.mcRetestSimulations != null) {
            this.mcRetestSimulations.clear();
        }
        this.values.remove(this.getKeyHash("RobustnessOriginalResults"));
        this.fitnessCollection.clear();
        if (bl2) {
            this.removeStockChartTempFile();
        }
    }

    private void removeStockChartTempFile() {
        block5: {
            this.chartsDataLock.lock();
            try {
                if (this.stockChartPath == null) break block5;
                File file = new File(this.stockChartPath);
                try {
                    Files.deleteIfExists(file.toPath());
                }
                catch (IOException iOException) {
                    Log.error("Error while deleting chart file", (Throwable)iOException);
                }
                this.stockChartPath = null;
            }
            finally {
                this.chartsDataLock.unlock();
            }
        }
    }

    public void freeMemory2() {
        this.clear();
    }

    public void setStrategyProblems(int n) {
        this.resultsGroup.specialValues().set("StrategyProblems", (Object)n);
    }

    public int getStrategyProblems() {
        return this.resultsGroup.specialValues().getInt("StrategyProblems", 0);
    }

    public void copyStats(Result result) {
        String[] stringArray = result.getAllKeys();
        for (int i = 0; i < stringArray.length; ++i) {
            Object object = result.get(stringArray[i]);
            if (!(object instanceof SQStats)) continue;
            try {
                this.set(stringArray[i], ((SQStats)object).getClone());
                continue;
            }
            catch (Exception exception) {
                Log.error("Error while cloning Result's SQStats", (Throwable)exception);
            }
        }
    }

    public String getStockChartPath() {
        return this.stockChartPath;
    }

    public void setStockChartPath(String string) {
        this.stockChartPath = string;
    }

    public Long2FloatRBTreeMap getWorstDailyEquity() {
        this.dailyEquityLock.lock();
        try {
            Long2FloatRBTreeMap long2FloatRBTreeMap = this.worstDailyEquity;
            return long2FloatRBTreeMap;
        }
        finally {
            this.dailyEquityLock.unlock();
        }
    }

    public Long2FloatRBTreeMap getMaxDailyDD() {
        this.maxDailyDDLock.lock();
        try {
            Long2FloatRBTreeMap long2FloatRBTreeMap = this.maxDailyDD;
            return long2FloatRBTreeMap;
        }
        finally {
            this.maxDailyDDLock.unlock();
        }
    }

    public Long2FloatRBTreeMap getMaxDailyDDPct() {
        this.maxDailyDDPctLock.lock();
        try {
            Long2FloatRBTreeMap long2FloatRBTreeMap = this.maxDailyDDPct;
            return long2FloatRBTreeMap;
        }
        finally {
            this.maxDailyDDPctLock.unlock();
        }
    }

    public void setWorstDailyEquity(Long2FloatRBTreeMap long2FloatRBTreeMap) {
        this.dailyEquityLock.lock();
        try {
            this.worstDailyEquity = long2FloatRBTreeMap;
        }
        finally {
            this.dailyEquityLock.unlock();
        }
    }

    public void setMaxDailyDD(Long2FloatRBTreeMap long2FloatRBTreeMap) {
        this.maxDailyDDLock.lock();
        try {
            this.maxDailyDD = long2FloatRBTreeMap;
        }
        finally {
            this.maxDailyDDLock.unlock();
        }
    }

    public void setMaxDailyDDPct(Long2FloatRBTreeMap long2FloatRBTreeMap) {
        this.maxDailyDDPctLock.lock();
        try {
            this.maxDailyDDPct = long2FloatRBTreeMap;
        }
        finally {
            this.maxDailyDDPctLock.unlock();
        }
    }

    public boolean isSpecial() {
        return this.specialResult;
    }

    public void setSpecial(boolean bl) {
        this.specialResult = bl;
    }

    public void removeUnsavableSettings() {
        if (this.settings != null) {
            this.settings.removeUnsavableValues();
            this.settings.removeIgnoredKeys(ignoredSettings);
        }
    }

    public void addMCSimulation(String string, RobustnessResults robustnessResults) {
        MCSimulations mCSimulations = null;
        if (string.contains("Manipul")) {
            if (this.mcManipulationSimulations == null) {
                this.mcManipulationSimulations = new MCSimulations();
            }
            mCSimulations = this.mcManipulationSimulations;
        } else {
            if (this.mcRetestSimulations == null) {
                this.mcRetestSimulations = new MCSimulations();
            }
            mCSimulations = this.mcRetestSimulations;
        }
        mCSimulations.add(robustnessResults);
    }

    public RobustnessResults getMCSimulation(String string, int n) {
        MCSimulations mCSimulations = null;
        mCSimulations = string.contains("Manipul") ? this.mcManipulationSimulations : this.mcRetestSimulations;
        if (mCSimulations == null || n >= mCSimulations.size()) {
            return null;
        }
        return (RobustnessResults)mCSimulations.get(n);
    }

    public double getFitness(byte by) {
        return this.fitnessCollection.getFitness(by);
    }

    public void setFitness(byte by, double d) {
        this.fitnessCollection.setFitness(by, d);
    }

    public SequentialOptimizationResults getSequentialOptimizaionResults() {
        return this.sequentialOptimizationResults;
    }

    public void setSequentialOptimizationResults(SequentialOptimizationResults sequentialOptimizationResults) {
        this.sequentialOptimizationResults = sequentialOptimizationResults;
    }

    public ResultsGroup getResultsGroup() {
        return this.resultsGroup;
    }
}

