/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  com.strategyquant.lib.L
 *  com.strategyquant.lib.SettingsMap
 *  com.strategyquant.lib.XMLUtil
 *  com.strategyquant.lib.app.MainApp
 *  org.jdom2.Element
 *  org.slf4j.Logger
 *  org.slf4j.LoggerFactory
 */
package com.strategyquant.tradinglib.crosscheck;

import com.strategyquant.lib.L;
import com.strategyquant.lib.SettingsMap;
import com.strategyquant.lib.XMLUtil;
import com.strategyquant.lib.app.MainApp;
import com.strategyquant.tradinglib.ChartSetup;
import com.strategyquant.tradinglib.ResultsGroup;
import com.strategyquant.tradinglib.StatsTypeCombination;
import com.strategyquant.tradinglib.StrategyBase;
import com.strategyquant.tradinglib.backtestrunner.IBacktestProgressListener;
import com.strategyquant.tradinglib.conditions.Condition;
import com.strategyquant.tradinglib.conditions.ConditionsChecker;
import com.strategyquant.tradinglib.crosscheck.CrossCheckDataNotExistException;
import com.strategyquant.tradinglib.crosscheck.ICrossCheck;
import com.strategyquant.tradinglib.options.TradingOptions;
import com.strategyquant.tradinglib.project.ProjectConfigHelper;
import com.strategyquant.tradinglib.project.StopPauseEngine;
import java.util.ArrayList;
import java.util.HashMap;
import java.util.jar.JarFile;
import java.util.jar.JarOutputStream;
import org.jdom2.Element;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

public abstract class CrossCheckMethod
implements ICrossCheck {
    public static final String RetestOnAdditionalMarkets = "RetestOnAdditionalMarkets";
    public static final String OptProfileSysParamPermutation = "OptProfileSysParamPermutation";
    public static final String WhatIf = "WhatIf";
    public static final String RetestWithHigherPrecision = "RetestWithHigherPrecision";
    public static final String NameMCManipulation = L.tsq((String)"Monte Carlo trades manipulation");
    public static final String NameMCRetest = L.tsq((String)"Monte Carlo retest methods");
    public static final String NameOptProfileSPP = L.tsq((String)"Opt. Profile / Sys. Param. Permutation");
    public static final String NameAddMarkets = L.tsq((String)"Backtests on additional markets");
    public static final String NameWFMatrix = L.tsq((String)"Walk-Forward Matrix");
    public static final String NameWFOptimization = L.tsq((String)"Walk-Forward Optimization");
    public static final String NameHigherBacktestPrecis = L.tsq((String)"Higher backtest precision");
    public static final String NameWhatIf = L.tsq((String)"What If simulations");
    public static final String NameSequentialOptimization = L.tsq((String)"Sequential Optimization");
    public static final Logger Log = LoggerFactory.getLogger((String)"CrossCheckMethod");
    protected SettingsMap settings = new SettingsMap();
    public static int[] ConfidenceLevels = new int[]{50, 60, 70, 80, 90, 92, 95, 97, 98, 99, 100};
    public static double[] InitialCapitalVariants = new double[]{0.25, 0.5, 0.75, 1.0, 1.25, 1.5, 2.0, 3.0, 4.0, 6.0};
    protected static final StatsTypeCombination combination = new StatsTypeCombination(0, 10, 127);
    protected int dismissalReason = 0;
    protected String dismissalMessage = "";
    protected IBacktestProgressListener backtestProgressListener;
    protected StopPauseEngine stopPauseEngine;
    protected ConditionsChecker conditionsChecker = new ConditionsChecker();

    public String getProduct() {
        return "SQUANTBACKTESTNODE";
    }

    public abstract int getPreferredPosition();

    public void initPlugin() throws Exception {
    }

    @Override
    public String getDescription() {
        return null;
    }

    @Override
    public SettingsMap getSettings() {
        return this.settings;
    }

    @Override
    public void fixSettings(Element element) {
        XMLUtil.tryAddElement((Element)element, (String)"Settings");
        Element element2 = XMLUtil.tryAddElement((Element)element, (String)"AcceptanceSettings");
        XMLUtil.tryAddElement((Element)element2, (String)"Conditions");
        if (!MainApp.v571hfnsHw().gDmtOfRJBr()) {
            element.setAttribute("use", "false");
        }
    }

    @Override
    public int getDismissalReason() {
        return this.dismissalReason;
    }

    @Override
    public String getDismissalMessage() {
        return this.dismissalMessage;
    }

    protected void readConditions(Element element) throws Exception {
        Element element2 = XMLUtil.tryAddElement((Element)element, (String)"AcceptanceSettings");
        try {
            Element element3 = XMLUtil.tryAddElement((Element)element2, (String)"Conditions");
            this.settings.set("Conditions", ProjectConfigHelper.getConditions(element3));
        }
        catch (Exception exception) {
            throw new Exception(L.t((String)"Cannot read conditions of Crosscheck method '%s'", (Object[])new Object[]{this.getName()}), exception);
        }
    }

    private String getPluginName() {
        return this.getClass().getSimpleName();
    }

    protected boolean checkConditions(ResultsGroup resultsGroup, int n) {
        ArrayList arrayList = (ArrayList)this.settings.get("Conditions");
        if (arrayList != null && arrayList.size() > 0) {
            for (int i = 0; i < arrayList.size(); ++i) {
                Condition condition = (Condition)arrayList.get(i);
                if (!condition.isUsed()) continue;
                try {
                    boolean bl = this.conditionsChecker.check(resultsGroup, condition);
                    if (bl) continue;
                    this.dismissalReason = 300000 + i + n * 1000;
                    this.dismissalMessage = String.format("Cross Check filter in '%s': %s", this.getName(), this.conditionsChecker.dismissalMessage);
                    return false;
                }
                catch (CrossCheckDataNotExistException crossCheckDataNotExistException) {
                    continue;
                }
                catch (Exception exception) {
                    Log.error("Error while checking condition", (Throwable)exception);
                    this.dismissalReason = 10003;
                    this.dismissalMessage = String.format("Cross Check filter in '%s': Error evaluating conditions: %s", this.getName(), exception.getMessage());
                    return false;
                }
            }
        }
        return true;
    }

    protected SettingsMap cloneSettings(SettingsMap settingsMap) throws CloneNotSupportedException {
        SettingsMap settingsMap2 = new SettingsMap();
        String[] stringArray = settingsMap.getAllKeys();
        for (int i = 0; i < stringArray.length; ++i) {
            Object object = this.cloneValue(stringArray[i], settingsMap.get(stringArray[i]));
            settingsMap2.set(stringArray[i], object);
        }
        settingsMap2.set("StrategyCheckDate", (Object)-1L);
        return settingsMap2;
    }

    private Object cloneValue(String string, Object object) throws CloneNotSupportedException {
        if (string.equals("TradingOptions")) {
            return ((TradingOptions)object).getClone();
        }
        if (string.equals("StoreChartData")) {
            return false;
        }
        if (object instanceof StrategyBase) {
            return ((StrategyBase)object).clone();
        }
        if (string.equals("BacktestChart")) {
            return ((ChartSetup)object).getClone();
        }
        return object;
    }

    protected void setJobProgress(int n) {
        if (this.backtestProgressListener != null) {
            this.backtestProgressListener.setProgress(n);
        }
    }

    @Override
    public void registerProgressListener(IBacktestProgressListener iBacktestProgressListener) {
        this.backtestProgressListener = iBacktestProgressListener;
    }

    @Override
    public void setStopPauseEngine(StopPauseEngine stopPauseEngine) {
        this.stopPauseEngine = stopPauseEngine;
    }

    @Override
    public void saveDataToFile(ResultsGroup resultsGroup, JarOutputStream jarOutputStream) throws Exception {
    }

    @Override
    public void loadDataFromFile(ResultsGroup resultsGroup, JarFile jarFile) throws Exception {
    }

    protected byte getSampleType(Element element, Object ... objectArray) {
        HashMap hashMap;
        byte by = XMLUtil.getByteAttr((Element)element, (String)"sampleType", (byte)127);
        if ((by == 66 || by == 77) && objectArray.length > 1 && objectArray[1] instanceof HashMap && (hashMap = (HashMap)objectArray[1]).containsKey("SampleType")) {
            by = (Byte)hashMap.get("SampleType");
        }
        return by;
    }

    public boolean disabledForSpecialTrial() {
        return false;
    }

    protected void checkSpecialTrialLimitation() throws Exception {
        if (MainApp.v571hfnsHw().bDm88fRJA3()) {
            throw new Exception(L.t((String)"Crosscheck '%s' is available only in the full version.", (Object[])new Object[]{this.getName()}));
        }
    }
}

