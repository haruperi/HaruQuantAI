/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  com.strategyquant.datalib.InstrumentInfo
 *  com.strategyquant.lib.L
 *  com.strategyquant.lib.SQTime
 *  com.strategyquant.lib.SQUtils
 *  com.strategyquant.lib.SettingsMap
 *  com.strategyquant.lib.TimePeriods
 *  com.strategyquant.lib.XMLUtil
 *  com.strategyquant.lib.app.MainApp
 *  com.strategyquant.lib.settings.IXMLAble
 *  com.strategyquant.lib.utils.IUniqueNameChecker
 *  com.strategyquant.pluginlib.program.IProgram
 *  com.strategyquant.pluginlib.program.Program
 *  it.unimi.dsi.fastutil.longs.Long2FloatRBTreeMap
 *  it.unimi.dsi.fastutil.longs.Long2FloatSortedMap
 *  it.unimi.dsi.fastutil.longs.Long2ObjectOpenHashMap
 *  it.unimi.dsi.fastutil.longs.LongBidirectionalIterator
 *  it.unimi.dsi.fastutil.objects.ObjectArrayList
 *  org.jdom2.Content
 *  org.jdom2.Element
 *  org.slf4j.Logger
 *  org.slf4j.LoggerFactory
 */
package com.strategyquant.tradinglib;

import com.strategyquant.datalib.InstrumentInfo;
import com.strategyquant.lib.L;
import com.strategyquant.lib.SQTime;
import com.strategyquant.lib.SQUtils;
import com.strategyquant.lib.SettingsMap;
import com.strategyquant.lib.TimePeriods;
import com.strategyquant.lib.XMLUtil;
import com.strategyquant.lib.app.MainApp;
import com.strategyquant.lib.settings.IXMLAble;
import com.strategyquant.lib.utils.IUniqueNameChecker;
import com.strategyquant.pluginlib.program.IProgram;
import com.strategyquant.pluginlib.program.Program;
import com.strategyquant.tradinglib.ChartSetup;
import com.strategyquant.tradinglib.Databank;
import com.strategyquant.tradinglib.MoneyManagementMethod;
import com.strategyquant.tradinglib.Order;
import com.strategyquant.tradinglib.OrdersList;
import com.strategyquant.tradinglib.Result;
import com.strategyquant.tradinglib.StrategyBase;
import com.strategyquant.tradinglib.miniequitychart.MiniEquityChartComputer;
import com.strategyquant.tradinglib.optimization.OptimizationProfile;
import com.strategyquant.tradinglib.optimization.WalkForwardMatrixResult;
import com.strategyquant.tradinglib.project.SQProject;
import com.strategyquant.tradinglib.results.ResultsMap;
import com.strategyquant.tradinglib.results.SpecialValues;
import com.strategyquant.tradinglib.results.StrategyFingerprint;
import com.strategyquant.tradinglib.results.SymbolsMap;
import com.strategyquant.tradinglib.results.stats.comparator.OrderComparatorByCloseTime;
import com.strategyquant.tradinglib.results.stats.comparator.OrderComparatorByOpenTime;
import com.strategyquant.tradinglib.strategy.OutOfSample;
import it.unimi.dsi.fastutil.longs.Long2FloatRBTreeMap;
import it.unimi.dsi.fastutil.longs.Long2FloatSortedMap;
import it.unimi.dsi.fastutil.longs.Long2ObjectOpenHashMap;
import it.unimi.dsi.fastutil.longs.LongBidirectionalIterator;
import it.unimi.dsi.fastutil.objects.ObjectArrayList;
import java.io.Serializable;
import java.time.Instant;
import java.time.LocalDateTime;
import java.time.ZoneOffset;
import java.util.ArrayList;
import java.util.List;
import java.util.concurrent.TimeUnit;
import java.util.concurrent.locks.StampedLock;
import org.jdom2.Content;
import org.jdom2.Element;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

public class ResultsGroup
implements IXMLAble,
Serializable {
    public static final Logger Log = LoggerFactory.getLogger((String)"ResultsGroup");
    public static final String Portfolio = "Portfolio";
    public static final String MergedPortfolio = "Merged portfolio";
    public static final String WFResult = "WF:";
    public static final String AdditionalMarket = "AdditionalMarket";
    private String resultName;
    private ResultsMap resultsMap = new ResultsMap(this);
    private SymbolsMap symbolsMap = new SymbolsMap();
    private SettingsMap specialValues = new SettingsMap();
    private Databank databank;
    private String resultFileName = null;
    private OrdersList ordersList = null;
    private String lastSettingsXml = null;
    private StampedLock resultsGroupLock = new StampedLock();
    private volatile boolean destroyOnLockRelease = false;
    public boolean updated = true;
    private static boolean storeChartData = false;
    private OptimizationProfile optimizationProfile;
    private String lockingTaskInfo = null;
    private String bestWFResultKey = null;
    private OutOfSample oosSettings;
    private List<ResultsGroup> mergedResults = null;
    public TimePeriods correlationPeriods = null;

    public ResultsGroup(String string) {
        this.resultName = string = this.correctName(string);
        this.ordersList = new OrdersList(string);
    }

    public static void init() {
        storeChartData = Boolean.parseBoolean(MainApp.settings().get("storeChartData", "false"));
    }

    public String getName() {
        return this.resultName;
    }

    public void setName(String string) {
        this.resultName = this.correctName(string);
    }

    private String correctName(String string) {
        return string != null ? string.replace(",", ".") : null;
    }

    private void ensureResultsMap() throws Exception {
        if (this.resultsMap == null) {
            throw new Exception("ResultsMap is empty, this ResultsGroup was destroyed before! " + this + " - " + this.getName());
        }
    }

    public void addResultSymbol(String string, String string2) throws Exception {
    }

    public Result subResult(String string) throws Exception {
        this.ensureResultsMap();
        return this.resultsMap.get(string);
    }

    public String getMainResultKey() throws Exception {
        this.ensureResultsMap();
        return this.resultsMap.getMainResultKey();
    }

    public Result mainResult() throws Exception {
        this.ensureResultsMap();
        String string = this.resultsMap.getMainResultKey();
        return this.subResult(string);
    }

    public Result portfolio() throws Exception {
        this.ensureResultsMap();
        return this.resultsMap.get(null);
    }

    public void addSubresult(String string, SettingsMap settingsMap) throws Exception {
        this.ensureResultsMap();
        this.resultsMap.addResult(string, settingsMap);
    }

    public void addSubresult(String string, SettingsMap settingsMap, Result result) throws Exception {
        this.ensureResultsMap();
        this.resultsMap.addResult(string, settingsMap, result);
    }

    public void removeSubresult(String string, boolean bl) throws Exception {
        this.ensureResultsMap();
        this.resultsMap.removeResult(string, bl);
    }

    public List<String> getResultKeys() throws Exception {
        this.ensureResultsMap();
        return this.resultsMap.keys();
    }

    public List<String> additionalMarketKeys() throws Exception {
        this.ensureResultsMap();
        return this.resultsMap.additionalMarketKeys();
    }

    public boolean hasResult(String string) throws Exception {
        this.ensureResultsMap();
        return this.resultsMap.hasResult(string);
    }

    public SymbolsMap symbols() {
        return this.symbolsMap;
    }

    public void setDatabank(Databank databank) {
        this.databank = databank;
    }

    public void updateResults(ResultsGroup resultsGroup, boolean bl) throws Exception {
        this.resultsMap = resultsGroup.resultsMap;
        this.ordersList.clear();
        this.ordersList = resultsGroup.ordersList;
        this.lastSettingsXml = resultsGroup.lastSettingsXml;
        this.symbolsMap = resultsGroup.symbolsMap;
        String string = this.specialValues().getString(SpecialValues.Note, "");
        this.specialValues = resultsGroup.specialValues;
        this.specialValues().setString(SpecialValues.Note, string);
        this.optimizationProfile = resultsGroup.optimizationProfile;
        this.updated = true;
    }

    public OrdersList orders() throws Exception {
        return this.ordersList;
    }

    public String getFilePath() {
        if (this.databank != null) {
            return this.databank.getResultsFilePath(this);
        }
        return this.resultFileName;
    }

    public Databank getDatabank() {
        return this.databank;
    }

    public String generateUniqueResultKeyName(String string) throws Exception {
        String string2 = SQUtils.generateUniqueName((String)string, (IUniqueNameChecker)new IUniqueNameChecker(){

            public boolean checkNameExist(String string) throws Exception {
                return ResultsGroup.this.hasResult(string);
            }
        });
        return string2;
    }

    public static ResultsGroup merge(ArrayList<ResultsGroup> arrayList, String[] stringArray, SQProject sQProject) throws Exception {
        return ResultsGroup.merge(arrayList, stringArray, sQProject, null, null);
    }

    public static ResultsGroup merge(ArrayList<ResultsGroup> arrayList, String[] stringArray, SQProject sQProject, Long2ObjectOpenHashMap<String> long2ObjectOpenHashMap, ObjectArrayList<String> objectArrayList) throws Exception {
        ResultsGroup resultsGroup = new ResultsGroup(MergedPortfolio);
        int n = arrayList.size();
        for (int i = 0; i < n; ++i) {
            ResultsGroup resultsGroup2 = arrayList.get(i);
            resultsGroup.mergeWith(resultsGroup2, stringArray, long2ObjectOpenHashMap, objectArrayList);
            if (sQProject == null) continue;
            sQProject.getProgress().update("Create Portfolio", -1.0, null, L.t((String)String.format("Merging strategies %d / %d", i + 1, n), (Object[])new Object[]{true}));
        }
        return resultsGroup;
    }

    public static ResultsGroup mergeWF(ArrayList<ResultsGroup> arrayList, String[] stringArray, SQProject sQProject) throws Exception {
        ResultsGroup resultsGroup = new ResultsGroup(MergedPortfolio);
        int n = arrayList.size();
        for (int i = 0; i < n; ++i) {
            ResultsGroup resultsGroup2 = arrayList.get(i);
            resultsGroup.mergeWith(resultsGroup2, stringArray, true);
            if (sQProject == null) continue;
            sQProject.getProgress().update("Create Portfolio", -1.0, null, L.t((String)String.format("Merging strategies %d / %d", i + 1, n), (Object[])new Object[]{true}));
        }
        return resultsGroup;
    }

    public static ResultsGroup merge(ResultsGroup ... resultsGroupArray) throws Exception {
        ResultsGroup resultsGroup = new ResultsGroup(MergedPortfolio);
        for (int i = 0; i < resultsGroupArray.length; ++i) {
            ResultsGroup resultsGroup2 = resultsGroupArray[i];
            resultsGroup.mergeWith(resultsGroup2, null);
        }
        return resultsGroup;
    }

    public void mergeWith(ResultsGroup resultsGroup) throws Exception {
        this.mergeWith(resultsGroup, null);
    }

    public void mergeWith(ResultsGroup resultsGroup, String[] stringArray) throws Exception {
        this.mergeWith(resultsGroup, stringArray, false, null, null);
    }

    public void mergeWith(ResultsGroup resultsGroup, String[] stringArray, Long2ObjectOpenHashMap<String> long2ObjectOpenHashMap, ObjectArrayList<String> objectArrayList) throws Exception {
        this.mergeWith(resultsGroup, stringArray, false, long2ObjectOpenHashMap, objectArrayList);
    }

    public void mergeWith(ResultsGroup resultsGroup, String[] stringArray, boolean bl) throws Exception {
        this.mergeWith(resultsGroup, stringArray, bl, null, null);
    }

    public void mergeWith(ResultsGroup resultsGroup, String[] stringArray, boolean bl, Long2ObjectOpenHashMap<String> long2ObjectOpenHashMap, ObjectArrayList<String> objectArrayList) throws Exception {
        ChartSetup chartSetup;
        OrdersList ordersList = this.orders();
        Element element = null;
        int n = 0;
        ResultsGroup resultsGroup2 = null;
        ChartSetup chartSetup2 = null;
        double d = 0.0;
        n |= resultsGroup.specialValues().getInt("StrategyProblems", 0);
        if (this.getResultKeys().size() == 0) {
            resultsGroup2 = resultsGroup;
            chartSetup = (ChartSetup)resultsGroup2.portfolio().getSettings().get("BacktestChart");
            chartSetup2 = chartSetup == null ? null : chartSetup.getClone();
        } else {
            chartSetup2 = (ChartSetup)this.portfolio().getSettings().get("BacktestChart");
            if (chartSetup2 != null) {
                chartSetup = (ChartSetup)resultsGroup.portfolio().getSettings().get("BacktestChart");
            }
        }
        if (element == null && (element = resultsGroup.portfolio().getStrategyXml()) != null) {
            element = element.clone();
        }
        boolean bl2 = resultsGroup.isHodlStrategy();
        List<String> list = resultsGroup.getResultKeys();
        ArrayList<String> arrayList = this.getKeysToMerge(resultsGroup, list, bl, stringArray);
        for (String string : arrayList) {
            Object object;
            String string2;
            Result result = resultsGroup.subResult(string);
            String string3 = string.startsWith("Main:") ? string.replace("Main", resultsGroup.getName()) : string;
            if (bl && string.startsWith(WFResult)) {
                string3 = string3.replace(WFResult, "WF_");
            }
            if (resultsGroup.resultsMap != null && resultsGroup.resultsMap.size() == 1) {
                string2 = resultsGroup.getName();
                if (string2.equals("CrossCheck_SequentialOptimization")) {
                    string3 = "CrossCheck_SequentialOptimization";
                } else {
                    int n2 = string3.lastIndexOf(":");
                    object = null;
                    if (n2 > 0) {
                        object = string3.substring(n2 + 1);
                    }
                    if (string2 != null) {
                        string3 = string2;
                        if (object != null) {
                            string3 = string3 + ": " + (String)object;
                        }
                    }
                }
            }
            if (this.hasResult(string3)) {
                string3 = SQUtils.generateUniqueName((String)string, (IUniqueNameChecker)new IUniqueNameChecker(){

                    public boolean checkNameExist(String string) throws Exception {
                        return ResultsGroup.this.hasResult(string);
                    }
                });
            }
            string2 = result.getSettings().clone();
            Result result2 = new Result(string3, this, (SettingsMap)string2);
            result2.setString(SpecialValues.Symbol, resultsGroup.mainResult().getString(SpecialValues.Symbol));
            result2.setString(SpecialValues.Timeframe, resultsGroup.mainResult().getString(SpecialValues.Timeframe));
            this.addSubresult(string3, (SettingsMap)string2, result2);
            object = resultsGroup.orders().filterWithClone(string, (byte)0, (byte)127);
            for (int i = 0; i < ((OrdersList)object).size(); ++i) {
                Order order = ((OrdersList)object).get(i);
                if (string.hashCode() != string3.hashCode() && order.SetupName.equals(string) || resultsGroup.isStockpickerStrategy()) {
                    order.SetupName = string3;
                }
                if (bl && string.startsWith(WFResult)) {
                    order.SampleType = (byte)10;
                }
                if (long2ObjectOpenHashMap != null) {
                    long2ObjectOpenHashMap.put(order.OrderId, (Object)order.SetupName);
                }
                if (objectArrayList != null) {
                    objectArrayList.add((Object)order.SetupName);
                }
                ordersList.add(order);
            }
            this.symbols().add(resultsGroup.symbolsMap);
            result2.setStockChartPath(null);
            Long2FloatRBTreeMap long2FloatRBTreeMap = result.getWorstDailyEquity();
            if (long2FloatRBTreeMap != null) {
                result2.setWorstDailyEquity(long2FloatRBTreeMap.clone());
            }
            result2.copyStats(result);
        }
        d += resultsGroup.specialValues().getDouble(SpecialValues.BacktestDuration, 0.0);
        if (!this.specialValues().containsKey(SpecialValues.DateGenerated)) {
            this.specialValues().set(SpecialValues.DateGenerated, (Object)SQTime.getLocalCurrentTimeInMs());
        }
        this.specialValues().set(SpecialValues.DateLastModified, (Object)SQTime.getLocalCurrentTimeInMs());
        if (resultsGroup2 != null) {
            this.setLastSettings(resultsGroup2.getLastSettings());
            this.specialValues().setString(SpecialValues.Symbol, MergedPortfolio);
            this.specialValues().set(SpecialValues.HistoryFrom, (Object)resultsGroup2.specialValues().getLong(SpecialValues.HistoryFrom));
            this.specialValues().set(SpecialValues.HistoryTo, (Object)resultsGroup2.specialValues().getLong(SpecialValues.HistoryTo));
            this.specialValues().setString(SpecialValues.Timeframe, resultsGroup2.specialValues().getString(SpecialValues.Timeframe));
            this.specialValues().set("StrategyProblems", (Object)n);
            this.specialValues().set(SpecialValues.BacktestDuration, (Object)SQUtils.round((double)d, (int)2));
            this.specialValues().set(SpecialValues.LastModified, (Object)System.currentTimeMillis());
            this.specialValues().set(SpecialValues.Complexity, (Object)resultsGroup2.specialValues().getInt(SpecialValues.Complexity));
            this.specialValues().set(SpecialValues.ParametersStability, resultsGroup2.specialValues().get(SpecialValues.ParametersStability));
            if (element != null) {
                element.setAttribute("mergedResult", "false");
                this.portfolio().addStrategyXml(element);
            }
            long l = resultsGroup2.specialValues().getLong(SpecialValues.HistoryFrom, Long.MAX_VALUE);
            long l2 = resultsGroup2.specialValues().getLong(SpecialValues.HistoryTo, Long.MIN_VALUE);
            long l3 = this.specialValues().getLong(SpecialValues.PortfolioHistoryFrom, Long.MAX_VALUE);
            long l4 = this.specialValues().getLong(SpecialValues.PortfolioHistoryTo, Long.MIN_VALUE);
            if (l < l3) {
                this.specialValues().set(SpecialValues.PortfolioHistoryFrom, (Object)l);
            }
            if (l2 > l4) {
                this.specialValues().set(SpecialValues.PortfolioHistoryTo, (Object)l2);
            }
        }
        if (this.getOptimizationProfile() == null) {
            this.setOptimizationProfile(resultsGroup.getOptimizationProfile());
        }
        this.updated = true;
    }

    private ArrayList<String> getKeysToMerge(ResultsGroup resultsGroup, List<String> list, boolean bl, String[] stringArray) throws Exception {
        ArrayList<String> arrayList = new ArrayList<String>();
        if (bl) {
            for (String string : list) {
                if (!string.startsWith(WFResult)) continue;
                arrayList.add(string);
                break;
            }
            if (arrayList.size() > 0) {
                return arrayList;
            }
        }
        for (String string : list) {
            Result result;
            if (string.equals(Portfolio) || !bl && string.startsWith("WF")) continue;
            if (stringArray != null) {
                boolean bl2 = false;
                for (int i = 0; i < stringArray.length; ++i) {
                    if (!string.contains(stringArray[i])) continue;
                    bl2 = true;
                    break;
                }
                if (bl2) continue;
            }
            if ((result = resultsGroup.subResult(string)).isSpecial()) continue;
            arrayList.add(string);
        }
        return arrayList;
    }

    public boolean isPortfolio() throws Exception {
        this.ensureResultsMap();
        return this.resultsMap.isPortfolio();
    }

    public SettingsMap specialValues() {
        return this.specialValues;
    }

    public Element getXML() {
        Element element;
        Element element2 = new Element("ResultsGroup");
        XMLUtil.trySetAttr((Element)element2, (String)"ResultName", (Object)this.resultName);
        if (this.resultsMap != null) {
            element = this.resultsMap.getXML();
            element2.addContent((Content)element);
        }
        if (this.symbolsMap != null) {
            element = this.symbolsMap.getXML();
            element2.addContent((Content)element);
        }
        if (this.specialValues != null) {
            element = new Element("SpecialValuesMap");
            Element element3 = this.specialValues.getXML();
            element.addContent((Content)element3);
            element2.addContent((Content)element);
        }
        return element2;
    }

    public void setFromXML(Element element) throws Exception {
        Element element2;
        Element element3 = element.getChild("ResultsMap");
        Element element4 = element.getChild("SymbolsMap");
        if (element3 != null) {
            this.resultsMap = new ResultsMap(this);
            this.resultsMap.setFromXML(element3);
        }
        if (element4 != null) {
            this.symbolsMap = new SymbolsMap();
            this.symbolsMap.setFromXML(element4);
        }
        if ((element2 = element.getChild("SpecialValuesMap")) != null) {
            this.specialValues = new SettingsMap();
            Element element5 = element2.getChild("SettingsMap");
            List list = element5.getChildren();
            String string = this.getMainResultKey();
            string = MiniEquityChartComputer.correctResultKey(string);
            for (int i = 0; i < list.size(); ++i) {
                Element element6 = (Element)list.get(i);
                String string2 = SQUtils.decodeXmlKey((String)element6.getName());
                if (string2.startsWith("MEC_") && string2.endsWith(string)) {
                    string2 = string2.replace(string, "Main");
                }
                Object object = null;
                if (element6.getContentSize() > 0) {
                    object = XMLUtil.elementToValue((Element)element6);
                }
                this.specialValues.set(string2, object);
            }
        }
    }

    public void computeAllStats() throws Exception {
        this.ensureResultsMap();
        this.resultsMap.computeAllStats(this.specialValues(), this.getOOS());
        StrategyFingerprint strategyFingerprint = new StrategyFingerprint(this);
        this.specialValues().set(SpecialValues.Fingerprint, (Object)strategyFingerprint);
    }

    public ResultsGroup clone() {
        return this.clone(false);
    }

    public ResultsGroup clone(boolean bl) {
        ResultsGroup resultsGroup = new ResultsGroup(this.resultName);
        try {
            resultsGroup.symbolsMap = this.symbolsMap.getClone();
        }
        catch (Exception exception) {
            Log.error("Cannot clone SymbolsMap", (Throwable)exception);
        }
        resultsGroup.resultsMap = this.resultsMap.clone(resultsGroup);
        resultsGroup.specialValues = this.specialValues.clone();
        resultsGroup.databank = this.databank;
        resultsGroup.updated = true;
        resultsGroup.lastSettingsXml = this.lastSettingsXml;
        try {
            if (this.ordersList != null) {
                resultsGroup.ordersList = bl ? this.ordersList.cloneDeep() : this.ordersList.clone();
            }
        }
        catch (Exception exception) {
            Log.error("Exception when cloning ResultsGroup: ", (Throwable)exception);
        }
        resultsGroup.optimizationProfile = this.optimizationProfile;
        if (this.mergedResults != null) {
            resultsGroup.mergedResults = new ArrayList<ResultsGroup>();
            for (int i = 0; i < this.mergedResults.size(); ++i) {
                resultsGroup.mergedResults.add(this.mergedResults.get(i).clone());
            }
        }
        return resultsGroup;
    }

    public Element getStrategyXml() throws Exception {
        return this.portfolio().getStrategyXml();
    }

    public void setStrategyXml(Element element) throws Exception {
        this.portfolio().addStrategyXml(element);
    }

    public void setResultFileName(String string) {
        this.resultFileName = string;
    }

    public String getParams() {
        try {
            return (String)this.specialValues().get("OptimizationParameters");
        }
        catch (Exception exception) {
            Log.error("Error while obtaining opt params. Exc.", (Throwable)exception);
            return "N/A";
        }
    }

    public String getOriginalWFResultKey() throws Exception {
        for (String string : this.getResultKeys()) {
            if (string.startsWith(WFResult) || string.equals(Portfolio)) continue;
            return string;
        }
        return null;
    }

    public int getChartCount() {
        try {
            Element element = this.portfolio().getStrategyXml();
            Element element2 = element.getChild("Strategy").getChild("Datas");
            return element2.getChildren("data").size() - 1;
        }
        catch (Exception exception) {
            Log.error("Chart count of ResultsGroup '" + this.getName() + "' cannot be resolved. ", (Throwable)exception);
            return -1;
        }
    }

    public void setLastSettings(String string) throws Exception {
        this.lastSettingsXml = string;
    }

    public String getLastSettings() throws Exception {
        return this.lastSettingsXml;
    }

    public void createPortfolioResult() throws Exception {
        this.createPortfolioResult("single", null);
    }

    public void createPortfolioResult(String string, SQProject sQProject) throws Exception {
        Object object;
        Result result = null;
        String string2 = null;
        Long2FloatRBTreeMap long2FloatRBTreeMap = this.recomputeMergedDailyEquity();
        int n = 0;
        double d = 0.0;
        long l = Long.MAX_VALUE;
        long l2 = Long.MIN_VALUE;
        for (String object22 : this.getResultKeys()) {
            SettingsMap settingsMap;
            object = this.subResult(object22);
            if (object.isSpecial()) continue;
            ++n;
            if (string2 == null) {
                string2 = object.getString(SpecialValues.Timeframe, "N/A");
            } else if (!string2.equals(object.getString(SpecialValues.Timeframe, "N/A"))) {
                string2 = L.t((String)"multiple", (Object[])new Object[]{true});
            }
            if (result == null) {
                result = object;
            }
            if ((settingsMap = object.getSettings()) != null) {
                d += settingsMap.getDouble("MoneyManagement.InitialCapital", 10000.0);
            }
            long l3 = this.specialValues().getLong(SpecialValues.PortfolioHistoryFrom, Long.MAX_VALUE);
            long l4 = this.specialValues().getLong(SpecialValues.PortfolioHistoryTo, Long.MIN_VALUE);
            if (l3 < l) {
                l = l3;
            }
            if (l4 <= l2) continue;
            l2 = l4;
        }
        if (n <= 1) {
            throw new Exception("ResultGroup doesn't contain more Results, cannot create a portfolio!");
        }
        if (result == null) {
            throw new Exception("No Result in ResultGroup to create portfolio!");
        }
        SettingsMap settingsMap = result.getSettings();
        if (string.equals("sum")) {
            settingsMap = settingsMap.clone();
            settingsMap.set("MoneyManagement.InitialCapital", (Object)d);
        }
        settingsMap.set("PortfolioDataStart", (Object)l);
        settingsMap.set("PortfolioDataEnd", (Object)l2);
        Result result2 = new Result(Portfolio, this, settingsMap);
        this.removeSubresult(Portfolio, true);
        this.addSubresult(Portfolio, settingsMap, result2);
        this.specialValues().setString(SpecialValues.Symbol, Portfolio);
        this.specialValues().setString(SpecialValues.Timeframe, string2);
        object = this.orders();
        ((OrdersList)object).sort(new OrderComparatorByOpenTime());
        if (result != null && result.getStrategyXml() != null) {
            result2.addStrategyXml(result.getStrategyXml());
        }
        if (long2FloatRBTreeMap != null) {
            result2.setWorstDailyEquity(long2FloatRBTreeMap);
        }
        if (sQProject != null) {
            sQProject.getProgress().update("Create Portfolio", -1.0, null, L.t((String)"Computing stats of portfolio", (Object[])new Object[0]));
        }
        result2.computeAllStats(this.specialValues(), this.getOOS());
        this.updated = true;
    }

    public void createPortfolioResult(SQProject sQProject, float f, MoneyManagementMethod moneyManagementMethod) throws Exception {
        Object object;
        Result result = null;
        String string = null;
        Long2FloatRBTreeMap long2FloatRBTreeMap = this.recomputeMergedDailyEquity();
        int n = 0;
        long l = Long.MAX_VALUE;
        long l2 = Long.MIN_VALUE;
        for (String object22 : this.getResultKeys()) {
            object = this.subResult(object22);
            if (object.isSpecial()) continue;
            ++n;
            if (string == null) {
                string = object.getString(SpecialValues.Timeframe, "N/A");
            } else if (!string.equals(object.getString(SpecialValues.Timeframe, "N/A"))) {
                string = L.t((String)"multiple", (Object[])new Object[]{true});
            }
            if (result == null) {
                result = object;
            }
            long strategyBase = this.specialValues().getLong(SpecialValues.PortfolioHistoryFrom, Long.MAX_VALUE);
            long l3 = this.specialValues().getLong(SpecialValues.PortfolioHistoryTo, Long.MIN_VALUE);
            if (strategyBase < l) {
                l = strategyBase;
            }
            if (l3 <= l2) continue;
            l2 = l3;
        }
        if (n <= 1) {
            throw new Exception("ResultGroup doesn't contain more Results, cannot create a portfolio!");
        }
        if (result == null) {
            throw new Exception("No Result in ResultGroup to create portfolio!");
        }
        SettingsMap settingsMap = result.getSettings();
        settingsMap.set("MoneyManagement.InitialCapital", (Object)Float.valueOf(f));
        settingsMap.set("PortfolioDataStart", (Object)l);
        settingsMap.set("PortfolioDataEnd", (Object)l2);
        Result result2 = new Result(Portfolio, this, settingsMap);
        this.removeSubresult(Portfolio, true);
        this.addSubresult(Portfolio, settingsMap, result2);
        this.specialValues().setString(SpecialValues.Symbol, Portfolio);
        this.specialValues().setString(SpecialValues.Timeframe, string);
        object = this.orders();
        ((OrdersList)object).sort(new OrderComparatorByOpenTime());
        if (result != null && result.getStrategyXml() != null) {
            result2.addStrategyXml(result.getStrategyXml());
        }
        ((OrdersList)object).sort(new OrderComparatorByOpenTime());
        if (moneyManagementMethod != null) {
            StrategyBase strategyBase = StrategyBase.createXmlStrategy(result.getStrategyXml());
            this.calculateOrderValueSizeByMM((OrdersList)object, settingsMap, long2FloatRBTreeMap, strategyBase, f, moneyManagementMethod);
        }
        if (long2FloatRBTreeMap != null) {
            result2.setWorstDailyEquity(long2FloatRBTreeMap);
        }
        if (sQProject != null) {
            sQProject.getProgress().update("Create Portfolio", -1.0, null, L.t((String)"Computing stats of portfolio", (Object[])new Object[0]));
        }
        result2.computeAllStats(this.specialValues(), this.getOOS());
        this.updated = true;
    }

    private void calculateOrderValueSizeByMM(OrdersList ordersList, SettingsMap settingsMap, Long2FloatRBTreeMap long2FloatRBTreeMap, StrategyBase strategyBase, float f, MoneyManagementMethod moneyManagementMethod) throws Exception {
        float f2;
        float f3 = f2 = f;
        float f4 = 0.0f;
        float f5 = 1.0f;
        float f6 = 0.0f;
        float f7 = 0.0f;
        float f8 = 0.0f;
        for (int i = 0; i < ordersList.size(); ++i) {
            Order order = ordersList.get(i);
            try {
                float f9;
                List list = XMLUtil.stringToElement((String)this.getLastSettings()).getChild("Resources").getChild("Symbols").getChildren();
                Element element = ((Element)list.get(0)).getChild("InstrumentInfo");
                InstrumentInfo instrumentInfo = new InstrumentInfo();
                instrumentInfo.setFromXML(element);
                strategyBase.accountBalance = f2;
                strategyBase.accountEquity = f2;
                strategyBase.Symbol = order.Symbol;
                strategyBase.Instrument = instrumentInfo.instrument;
                float f10 = order.Size;
                if (f10 == 0.0f) {
                    f10 = 1.0f;
                }
                order.Ticket = i + 1;
                order.Size = (float)moneyManagementMethod.computeTradeSize(strategyBase, order.Symbol, order.Type, order.OpenPrice, order.StopLoss, instrumentInfo.tickSize, instrumentInfo.pointValue);
                order.PL = order.PipsPL * order.Size * (float)(instrumentInfo.pointValue * instrumentInfo.tickSize);
                float f11 = order.Size / f10;
                order.CommSwap *= f11;
                order.MAE *= f11;
                order.MFE *= f11;
                order.PL += order.CommSwap;
                order.PL -= order.SlippageInMoney;
                order.AccountBalance = f2 += order.PL;
                order.AccountBalanceTemp = f2;
                if (f2 > f3) {
                    f3 = f2;
                }
                if (f3 - f2 > f4) {
                    f4 = f3 - f2;
                }
                order.DD = f4;
                if (f2 != 0.0f) {
                    order.PctDD = Math.abs(f4 / f2);
                    order.PctPL = 100.0f * order.PL / f2;
                } else {
                    order.PctPL = 0.0f;
                }
                if (order.PL > 0.0f && order.PctPL < 0.0f) {
                    order.PctPL = -order.PctPL;
                }
                if (order.PL < 0.0f && order.PctPL > 0.0f) {
                    order.PctPL = -order.PctPL;
                }
                order.PctAccountBalance = f8 += order.PctPL;
                float f12 = 1.0f + order.PctPL / 100.0f;
                f5 = f9 = f12 * f5;
                f7 = (f9 - 1.0f) * 100.0f;
                order.PctPL_TWR = f7 - f6;
                f6 = f7;
                order.Size = (float)SQUtils.round2((double)order.Size);
                order.MAE = (float)SQUtils.round2((double)order.MAE);
                order.MFE = (float)SQUtils.round2((double)order.MFE);
                order.CommSwap = (float)SQUtils.round2((double)order.CommSwap);
                order.AccountBalance = (float)SQUtils.round2((double)order.AccountBalance);
                order.AccountBalanceTemp = (float)SQUtils.round2((double)order.AccountBalanceTemp);
                order.PL = (float)SQUtils.round2((double)order.PL);
                order.PctPL_TWR = (float)SQUtils.round2((double)order.PctPL_TWR);
                order.PipsPL = (float)SQUtils.round2((double)order.PipsPL);
                order.PctDD = (float)SQUtils.round2((double)order.PctDD);
                order.PctPL = (float)SQUtils.round2((double)order.PctPL);
                order.DD = (float)SQUtils.round2((double)order.DD);
                order.PctAccountBalance = (float)SQUtils.round2((double)order.PctAccountBalance);
                continue;
            }
            catch (Exception exception) {
                throw new Exception("Failed to calculate initial buy amount from MoneyManagement method - " + exception.getMessage(), exception);
            }
        }
        if (long2FloatRBTreeMap != null) {
            this.recalculateSubresultDailyEquity(this.portfolio());
        }
    }

    public Long2FloatRBTreeMap recomputeMergedDailyEquity() throws Exception {
        ArrayList<Long2FloatRBTreeMap> arrayList = null;
        for (String string : this.getResultKeys()) {
            Long2FloatRBTreeMap long2FloatRBTreeMap;
            Result result;
            if (string.contains(Portfolio) || (result = this.subResult(string)).isSpecial() || (long2FloatRBTreeMap = result.getWorstDailyEquity()) == null) continue;
            if (arrayList == null) {
                arrayList = new ArrayList<Long2FloatRBTreeMap>();
            }
            arrayList.add(long2FloatRBTreeMap);
        }
        if (arrayList == null) {
            return null;
        }
        if (arrayList.size() == 1) {
            return new Long2FloatRBTreeMap((Long2FloatSortedMap)arrayList.get(0));
        }
        return this.mergeDailyEquity((List<Long2FloatRBTreeMap>)arrayList);
    }

    private Long2FloatRBTreeMap mergeDailyEquity(List<Long2FloatRBTreeMap> list) {
        Long2FloatRBTreeMap long2FloatRBTreeMap = new Long2FloatRBTreeMap();
        for (Long2FloatRBTreeMap long2FloatRBTreeMap2 : list) {
            long2FloatRBTreeMap2.forEach((l, f) -> long2FloatRBTreeMap.put(l.longValue(), 0.0f));
        }
        Object object = new float[list.size()];
        for (int i = 0; i < ((Object)object).length; ++i) {
            object[i] = 0.0f;
        }
        LongBidirectionalIterator longBidirectionalIterator = long2FloatRBTreeMap.keySet().iterator();
        while (longBidirectionalIterator.hasNext()) {
            long l2 = (Long)longBidirectionalIterator.next();
            float f2 = 0.0f;
            for (int i = 0; i < list.size(); ++i) {
                Long2FloatRBTreeMap long2FloatRBTreeMap3 = list.get(i);
                float f3 = Float.MAX_VALUE;
                if (long2FloatRBTreeMap3.containsKey(l2)) {
                    f3 = long2FloatRBTreeMap3.get(l2);
                }
                if (f3 != Float.MAX_VALUE) {
                    object[i] = long2FloatRBTreeMap3.get(l2);
                }
                f2 += object[i];
            }
            long2FloatRBTreeMap.put(l2, f2);
        }
        return long2FloatRBTreeMap;
    }

    public void moveResultFrom(String string, ResultsGroup resultsGroup, boolean bl) throws Exception {
        Result result = resultsGroup.subResult(string);
        if (result == null) {
            throw new Exception("Result'" + string + "' doesn't exist in source ResultsGroup!");
        }
        if (this.hasResult(string)) {
            return;
        }
        this.moveOrdersFrom(string, resultsGroup);
        if (bl) {
            result.setSpecial(bl);
        }
        this.addSubresult(string, result.getSettings(), result);
        this.updated = true;
    }

    private void moveOrdersFrom(String string, ResultsGroup resultsGroup) throws Exception {
        if (!this.hasResult(string)) {
            OrdersList ordersList = resultsGroup.orders().filter(string, (byte)0, (byte)127);
            this.orders().addAll(ordersList);
        }
    }

    public void removeUnsavableSettings() {
        this.resultsMap.removeUnsavableSettings();
    }

    public double getFitness() {
        return this.getFitness((byte)10);
    }

    public double getFitness(byte by) {
        double d = 0.0;
        try {
            d = this.portfolio().getFitness(by);
        }
        catch (Exception exception) {
            Log.error("Error while getting fitness value of ResultsGroup '" + this.resultName + "'.", (Throwable)exception);
        }
        return d > 0.0 ? d : 0.0;
    }

    public StrategyFingerprint getFingerprint() {
        Object object = this.specialValues().get(SpecialValues.Fingerprint, null);
        if (object == null) {
            return null;
        }
        return (StrategyFingerprint)object;
    }

    public ResultsGroup lockRecord(String string) throws Exception {
        return this.lockRecord(15, string);
    }

    public ResultsGroup lockRecord(int n, String string) throws Exception {
        try {
            if (this.resultsGroupLock.tryWriteLock(n, TimeUnit.SECONDS) == 0L) {
                Log.error("Strategy result lock from {} not acquired, lock held by: {}!", (Object)string, (Object)this.lockingTaskInfo);
                throw new Exception("Lock not acquired ");
            }
            this.lockingTaskInfo = string;
            return this;
        }
        catch (Exception exception) {
            Log.error("[2] Strategy result lock from {} not acquired, lock held by: {}!", (Object)string, (Object)this.lockingTaskInfo);
            Log.error("Cannot lock orders", (Throwable)exception);
            throw exception;
        }
    }

    public void releaseLock(String string) {
        if (this.resultsGroupLock.tryUnlockWrite()) {
            this.lockingTaskInfo = null;
        } else {
            Log.debug("Nothing to unlock, record not locked, at: {}", (Object)string);
        }
    }

    public void clear() {
        this.resultsMap.clear(true, true);
        this.ordersList.clear();
        String string = this.specialValues().getString(SpecialValues.Note, "");
        boolean bl = this.specialValues().containsKey(SpecialValues.IsMergedPortfolio);
        long l = this.specialValues().getLong(SpecialValues.DateGenerated, -1L);
        this.specialValues().clear();
        this.specialValues().setString(SpecialValues.Note, string);
        if (bl) {
            this.specialValues().set(SpecialValues.IsMergedPortfolio, (Object)1);
        }
        this.specialValues().set(SpecialValues.DateGenerated, (Object)l);
        if (this.optimizationProfile != null) {
            this.optimizationProfile.clear();
            this.optimizationProfile = null;
        }
        this.updated = true;
    }

    public void clearTempData() {
        this.resultsMap.clearTempData();
        if (this.optimizationProfile != null) {
            this.optimizationProfile.clear();
            this.optimizationProfile = null;
        }
        this.updated = true;
    }

    public void destroy(boolean bl) {
        this.resultsMap.clear(false, bl);
        this.ordersList.clear();
        this.specialValues().clear();
        if (this.optimizationProfile != null) {
            this.optimizationProfile.clear();
            this.optimizationProfile = null;
        }
        if (this.mergedResults != null) {
            this.mergedResults.clear();
            this.mergedResults = null;
        }
        this.updated = true;
    }

    public boolean isFromAlgoWizard() {
        return this.specialValues().get("backtestID") != null;
    }

    public void trySaveToFile() {
        if (this.databank == null || !this.databank.isFileBased()) {
            return;
        }
        String string = this.databank.getResultsFilePath(this);
        try {
            IProgram iProgram = Program.get((String)"Saver");
            iProgram.call("saveFile", new Object[]{this, string});
            this.resultFileName = string;
        }
        catch (Exception exception) {
            Log.error("Saving ResultsGroup failed", (Throwable)exception);
        }
    }

    public boolean storesChartData() {
        return storeChartData;
    }

    public void setOptimizationProfile(OptimizationProfile optimizationProfile) {
        this.optimizationProfile = optimizationProfile;
    }

    public OptimizationProfile getOptimizationProfile() {
        return this.optimizationProfile;
    }

    public String getBestWFResultKey() {
        try {
            WalkForwardMatrixResult walkForwardMatrixResult = (WalkForwardMatrixResult)this.mainResult().get("WalkForwardResult");
            if (walkForwardMatrixResult != null && this.bestWFResultKey == null) {
                this.bestWFResultKey = walkForwardMatrixResult.computeBestWF(this);
            }
        }
        catch (Exception exception) {
            Log.error("Error while computing best WF result. Exc.", (Throwable)exception);
        }
        return this.bestWFResultKey;
    }

    public OutOfSample getOOS() {
        return this.oosSettings;
    }

    public void setOOSSettings(OutOfSample outOfSample) {
        this.oosSettings = outOfSample;
    }

    public List<ResultsGroup> getMergedResults() {
        return this.mergedResults;
    }

    public void setMergedResults(List<ResultsGroup> list) {
        if (this.mergedResults == null) {
            this.mergedResults = new ArrayList<ResultsGroup>();
        } else {
            this.mergedResults.clear();
        }
        for (int i = 0; i < list.size(); ++i) {
            ResultsGroup resultsGroup = list.get(i).clone();
            this.mergedResults.add(resultsGroup);
        }
        this.specialValues.set(SpecialValues.IsMergedPortfolio, (Object)1);
    }

    public boolean isStockpickerStrategy() {
        return this.specialValues().getBoolean(SpecialValues.StockpickerStrategy, false);
    }

    public void setNote(String string) {
        this.specialValues().setString(SpecialValues.Note, string);
        this.updated = true;
    }

    public String getNote() {
        return this.specialValues().getString(SpecialValues.Note, null);
    }

    public String getNote(String string) {
        String string2 = this.specialValues().getString(SpecialValues.Note, null);
        if (string2 == null) {
            return string;
        }
        return string2;
    }

    public boolean isHodlStrategy() {
        String string = this.specialValues().getString(SpecialValues.PortfolioComposerHodlSymbol);
        return string != null;
    }

    public void recalculateDailyEquity() throws Exception {
        for (String string : this.getResultKeys()) {
            Result result = this.subResult(string);
            if (result.isSpecial()) continue;
            this.recalculateSubresultDailyEquity(result);
        }
    }

    private void recalculateSubresultDailyEquity(Result result) throws Exception {
        float f;
        Long2FloatRBTreeMap long2FloatRBTreeMap = result.getWorstDailyEquity();
        if (long2FloatRBTreeMap == null) {
            return;
        }
        long2FloatRBTreeMap.clear();
        OrdersList ordersList = this.orders().filter(result.getResultKey(), (byte)0, (byte)127);
        ordersList.sort(new OrderComparatorByCloseTime());
        float f2 = 0.0f;
        float f3 = f = 0.0f;
        long l = 0L;
        long l2 = 0L;
        for (int i = 0; i < ordersList.size(); ++i) {
            Order order = ordersList.get(i);
            LocalDateTime localDateTime = LocalDateTime.ofInstant(Instant.ofEpochMilli(order.CloseTime), ZoneOffset.UTC);
            LocalDateTime localDateTime2 = localDateTime.toLocalDate().atStartOfDay().plusDays(1L);
            l = localDateTime2.toInstant(ZoneOffset.UTC).toEpochMilli();
            if (i > 0) {
                LocalDateTime localDateTime3 = LocalDateTime.ofInstant(Instant.ofEpochMilli(l2), ZoneOffset.UTC);
                while (localDateTime3.isBefore(localDateTime2)) {
                    localDateTime3 = localDateTime3.plusDays(1L);
                    long l3 = localDateTime3.toInstant(ZoneOffset.UTC).toEpochMilli();
                    long2FloatRBTreeMap.put(l3, f3);
                }
            }
            f2 = (f += order.PL) - order.MAE;
            if (!long2FloatRBTreeMap.containsKey(l) || f2 < long2FloatRBTreeMap.get(l)) {
                long2FloatRBTreeMap.put(l, f2);
            }
            f3 = f2;
            l2 = l;
        }
    }
}

