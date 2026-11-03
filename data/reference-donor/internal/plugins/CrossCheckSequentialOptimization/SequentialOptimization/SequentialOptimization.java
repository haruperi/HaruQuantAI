/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  com.strategyquant.gridlib.client.GridJob
 *  com.strategyquant.lib.L
 *  com.strategyquant.lib.SQUtils
 *  com.strategyquant.lib.SettingsMap
 *  com.strategyquant.lib.XMLUtil
 *  com.strategyquant.tradinglib.ChartSetup
 *  com.strategyquant.tradinglib.DatabankColumn
 *  com.strategyquant.tradinglib.Result
 *  com.strategyquant.tradinglib.ResultsGroup
 *  com.strategyquant.tradinglib.StrategyBase
 *  com.strategyquant.tradinglib.crosscheck.CrossCheckDataNotExistException
 *  com.strategyquant.tradinglib.crosscheck.CrossCheckMethod
 *  com.strategyquant.tradinglib.crosscheck.ICrossCheck
 *  com.strategyquant.tradinglib.crosscheck.WalkForwardCrossCheckMethod
 *  com.strategyquant.tradinglib.databank.DatabankColumns
 *  com.strategyquant.tradinglib.engine.ChartSetups
 *  com.strategyquant.tradinglib.fitnessfunction.IFitnessFunction
 *  com.strategyquant.tradinglib.optimization.ISequentialOptimizationCompleteListener
 *  com.strategyquant.tradinglib.optimization.SequentialOptimizationEngine
 *  com.strategyquant.tradinglib.optimization.SequentialOptimizationSettings
 *  com.strategyquant.tradinglib.project.ILastEventListener
 *  com.strategyquant.tradinglib.project.ProjectConfigHelper
 *  com.strategyquant.tradinglib.results.SpecialValues
 *  com.strategyquant.tradinglib.robustnesstests.SequentialOptimizationResults
 *  com.strategyquant.tradinglib.task.settings.TaskSettingsData
 *  net.xeoh.plugins.base.annotations.PluginImplementation
 *  org.jdom2.Document
 *  org.jdom2.Element
 *  org.jdom2.output.Format
 *  org.jdom2.output.XMLOutputter
 */
package com.strategyquant.plugin.CrossCheck.impl.SequentialOptimization;

import com.strategyquant.gridlib.client.GridJob;
import com.strategyquant.lib.L;
import com.strategyquant.lib.SQUtils;
import com.strategyquant.lib.SettingsMap;
import com.strategyquant.lib.XMLUtil;
import com.strategyquant.tradinglib.ChartSetup;
import com.strategyquant.tradinglib.DatabankColumn;
import com.strategyquant.tradinglib.Result;
import com.strategyquant.tradinglib.ResultsGroup;
import com.strategyquant.tradinglib.StrategyBase;
import com.strategyquant.tradinglib.crosscheck.CrossCheckDataNotExistException;
import com.strategyquant.tradinglib.crosscheck.CrossCheckMethod;
import com.strategyquant.tradinglib.crosscheck.ICrossCheck;
import com.strategyquant.tradinglib.crosscheck.WalkForwardCrossCheckMethod;
import com.strategyquant.tradinglib.databank.DatabankColumns;
import com.strategyquant.tradinglib.engine.ChartSetups;
import com.strategyquant.tradinglib.fitnessfunction.IFitnessFunction;
import com.strategyquant.tradinglib.optimization.ISequentialOptimizationCompleteListener;
import com.strategyquant.tradinglib.optimization.SequentialOptimizationEngine;
import com.strategyquant.tradinglib.optimization.SequentialOptimizationSettings;
import com.strategyquant.tradinglib.project.ILastEventListener;
import com.strategyquant.tradinglib.project.ProjectConfigHelper;
import com.strategyquant.tradinglib.results.SpecialValues;
import com.strategyquant.tradinglib.robustnesstests.SequentialOptimizationResults;
import com.strategyquant.tradinglib.task.settings.TaskSettingsData;
import java.io.BufferedWriter;
import java.io.InputStream;
import java.io.OutputStream;
import java.io.OutputStreamWriter;
import java.io.Writer;
import java.util.jar.JarEntry;
import java.util.jar.JarFile;
import java.util.jar.JarOutputStream;
import net.xeoh.plugins.base.annotations.PluginImplementation;
import org.jdom2.Document;
import org.jdom2.Element;
import org.jdom2.output.Format;
import org.jdom2.output.XMLOutputter;

@PluginImplementation
public class SequentialOptimization
extends WalkForwardCrossCheckMethod
implements ILastEventListener {
    private IFitnessFunction fitnessFunction;
    private ChartSetups chartSetups;
    private SequentialOptimizationSettings seqOptSettings = new SequentialOptimizationSettings();

    public SequentialOptimization() {
        super("SequentialOptimization_CrossCheck");
    }

    public String getName() {
        return NameSequentialOptimization;
    }

    public String getShortName() {
        return L.tsq((String)"Sequential Optimization");
    }

    public String getDescription() {
        return L.tsq((String)"This cross check performs sequential optimization of the strategy and finds stable parameters.");
    }

    public String getSettingName() {
        return ((Object)((Object)this)).getClass().getSimpleName();
    }

    public int getType() {
        return 1;
    }

    public int getPreferredPosition() {
        return 300;
    }

    public int getNumberOfSimulations() {
        return 0;
    }

    public boolean doesRetest() {
        return true;
    }

    public boolean doesForEverySetup() {
        return false;
    }

    public void fixSettings(Element elSettings) {
        super.fixSettings(elSettings);
        Element elMethodSettings = XMLUtil.tryAddElement((Element)elSettings, (String)"Settings");
        Element elParameterSettings = XMLUtil.tryAddElement((Element)elMethodSettings, (String)"ParameterSettings");
        XMLUtil.tryAddIntNode((Element)elParameterSettings, (String)"DistributionUp", (int)50);
        XMLUtil.tryAddIntNode((Element)elParameterSettings, (String)"DistributionDown", (int)50);
        XMLUtil.tryAddIntNode((Element)elParameterSettings, (String)"Steps", (int)50);
        XMLUtil.tryAddBooleanNode((Element)elParameterSettings, (String)"ApplyToStrategy", (boolean)false);
        Element elAcceptanceSettings = XMLUtil.tryAddElement((Element)elSettings, (String)"AcceptanceSettings");
        XMLUtil.tryAddIntNode((Element)elAcceptanceSettings, (String)"PctToPass", (int)80);
        XMLUtil.tryAddIntNode((Element)elAcceptanceSettings, (String)"ResultsCount", (int)5);
        XMLUtil.tryAddIntNode((Element)elAcceptanceSettings, (String)"StabilityRange", (int)30);
    }

    public void readSettings(Element elSettings, TaskSettingsData data) throws Exception {
        this.fixSettings(elSettings);
        Element elTaskSettings = elSettings.getParentElement().getParentElement();
        Element elRankings = elTaskSettings.getChild("Rankings");
        this.fitnessFunction = ProjectConfigHelper.getFitnessFunction((Element)elRankings);
        Element elData = elTaskSettings.getChild("Data");
        this.chartSetups = ProjectConfigHelper.getChartSetups((Element)elData);
        Element elMethodSettings = XMLUtil.getChildElem((Element)elSettings, (String)"Settings");
        Element whatToParametrizeElem = elMethodSettings.getChild("WhatToParametrize");
        this.readWhatToParametrize(whatToParametrizeElem);
        Element elParameterSettings = XMLUtil.getChildElem((Element)elMethodSettings, (String)"ParameterSettings");
        this.seqOptSettings.distributionUp = XMLUtil.getNodeIntValue((Element)elParameterSettings, (String)"DistributionUp");
        this.seqOptSettings.distributionDown = XMLUtil.getNodeIntValue((Element)elParameterSettings, (String)"DistributionDown");
        this.seqOptSettings.steps = XMLUtil.getNodeIntValue((Element)elParameterSettings, (String)"Steps");
        this.seqOptSettings.applyToStrategy = XMLUtil.getNodeBooleanValue((Element)elParameterSettings, (String)"ApplyToStrategy", (boolean)false);
        Element elAcceptanceSettings = XMLUtil.getChildElem((Element)elSettings, (String)"AcceptanceSettings");
        this.seqOptSettings.pctToPass = XMLUtil.getNodeIntValue((Element)elAcceptanceSettings, (String)"PctToPass");
        this.seqOptSettings.stableAreaCount = XMLUtil.getNodeIntValue((Element)elAcceptanceSettings, (String)"ResultsCount");
        this.seqOptSettings.stabilityRangePct = XMLUtil.getNodeIntValue((Element)elAcceptanceSettings, (String)"StabilityRange");
        this.seqOptSettings.paramTypes = this.paramTypes;
        this.seqOptSettings.symmetry = this.paramSymmetry;
    }

    public boolean runTest(final ResultsGroup rg, int index, double globalATR, GridJob parentGridJob, boolean singleThreaded, ILastEventListener lastEventListener, String strategyName) throws Exception {
        this.checkSpecialTrialLimitation();
        SequentialOptimizationEngine engine = new SequentialOptimizationEngine(this.seqOptSettings, this.stopPauseEngine, lastEventListener, null);
        String mainResultKey = rg.getMainResultKey();
        Result result = rg.subResult(mainResultKey);
        final double mainResultFitness = result.getFitness((byte)127);
        if (lastEventListener != null) {
            String event = L.t((String)"Running sequential optimization for %s", (Object[])new Object[]{strategyName});
            lastEventListener.setLastEvent(event);
        }
        SettingsMap rgSettings = result.getSettings().clone();
        ChartSetups tmpChartSetups = this.chartSetups;
        if (tmpChartSetups == null) {
            tmpChartSetups = new ChartSetups((ChartSetup)rgSettings.get("BacktestChart"));
        }
        rgSettings.set("ChartSetups", (Object)tmpChartSetups);
        rgSettings.set("FitnessFunction", (Object)this.fitnessFunction);
        engine.initialize(rg.getName(), rg.getStrategyXml().clone(), rgSettings);
        boolean success = engine.optimize(false, singleThreaded, parentGridJob, new ISequentialOptimizationCompleteListener(){
            final /* synthetic */ SequentialOptimization this$0;
            {
                this.this$0 = this$0;
            }

            public void onFinish(boolean success, StrategyBase optimizedStrategy, SequentialOptimizationResults results, ResultsGroup optimizedRG) {
                try {
                    if (success) {
                        if (((SequentialOptimization)this.this$0).seqOptSettings.applyToStrategy) {
                            rg.mainResult().addStrategy(optimizedStrategy);
                            rg.mainResult().addStrategyXml(optimizedStrategy.getStrategyXml());
                        }
                        if (optimizedRG != null) {
                            String newResultKey = "CrossCheck_SequentialOptimization";
                            optimizedRG.setName(newResultKey);
                            rg.mergeWith(optimizedRG);
                            rg.createPortfolioResult();
                            rg.portfolio().setFitness((byte)127, mainResultFitness);
                            rg.portfolio().setFitness((byte)10, mainResultFitness);
                            rg.portfolio().setFitness((byte)20, mainResultFitness);
                            rg.portfolio().setFitness((byte)11, mainResultFitness);
                            rg.portfolio().setFitness((byte)40, mainResultFitness);
                        }
                    }
                    rg.mainResult().setSequentialOptimizationResults(results);
                }
                catch (Exception e) {
                    CrossCheckMethod.Log.error("Updating sequential optimized strategy failed", (Throwable)e);
                }
            }
        });
        if (!success) {
            this.dismissalMessage = engine.getDismissalMessage();
            this.dismissalReason = 10039;
            rg.specialValues().setString(SpecialValues.FiltersResultFailedReason, this.dismissalMessage);
        }
        return success;
    }

    protected boolean checkConditions(ResultsGroup strategy, int index) {
        return true;
    }

    public String getColumnTitleTemplate() {
        return "#columnName# (" + this.getShortName() + ", #sampleType#, #direction#, #plType#)";
    }

    public double getStatsValue(ResultsGroup rg, String columnName, Element elColumn, Object ... params) throws Exception {
        if (!rg.hasResult("CrossCheck_SequentialOptimization")) {
            throw new CrossCheckDataNotExistException(this.getName());
        }
        byte direction = XMLUtil.getByteAttr((Element)elColumn, (String)"direction", (byte)0);
        byte sampleType = this.getSampleType(elColumn, params);
        byte plType = XMLUtil.getByteAttr((Element)elColumn, (String)"plType", (byte)10);
        DatabankColumn column = (DatabankColumn)DatabankColumns.get().findClassByName(columnName);
        return column.getNumericValue(rg, "CrossCheck_SequentialOptimization", direction, plType, sampleType);
    }

    public boolean hasStatsValue(ResultsGroup rg, String columnName, Element elColumn, Object ... params) throws Exception {
        return rg.hasResult("CrossCheck_SequentialOptimization");
    }

    public ChartSetups getChartSetups(ChartSetup mainChartSetup) {
        ChartSetups list = new ChartSetups(mainChartSetup);
        return list;
    }

    public ICrossCheck clone(SettingsMap settings) {
        SequentialOptimization crossCheck = new SequentialOptimization();
        crossCheck.seqOptSettings = this.seqOptSettings != null ? this.seqOptSettings.clone() : null;
        crossCheck.fitnessFunction = this.fitnessFunction;
        crossCheck.chartSetups = this.chartSetups != null ? this.chartSetups.getClone() : null;
        return crossCheck;
    }

    public String printSettings(Element elMethod) throws Exception {
        if (elMethod == null) {
            throw new NullPointerException();
        }
        if (!XMLUtil.elementIs((Element)elMethod, (String)"use")) {
            return "Not used";
        }
        Element settingsEl = elMethod.getChild("Settings");
        Element elParameterSettings = XMLUtil.getChildElem((Element)settingsEl, (String)"ParameterSettings");
        int distUp = XMLUtil.getNodeIntValue((Element)elParameterSettings, (String)"DistributionUp");
        int distDown = XMLUtil.getNodeIntValue((Element)elParameterSettings, (String)"DistributionDown");
        int distSteps = XMLUtil.getNodeIntValue((Element)elParameterSettings, (String)"Steps");
        boolean apply = XMLUtil.getNodeBooleanValue((Element)elParameterSettings, (String)"ApplyToStrategy", (boolean)true);
        String settings = L.t((String)"Distribution: Up: %d%%, Down: %d%%, Steps: %d, Apply to Strategy: %s", (Object[])new Object[]{distUp, distDown, distSteps, apply});
        Element elAcceptanceSettings = XMLUtil.getChildElem((Element)elMethod, (String)"AcceptanceSettings");
        int pctToPass = XMLUtil.getNodeIntValue((Element)elAcceptanceSettings, (String)"PctToPass");
        int stableAreaCount = XMLUtil.getNodeIntValue((Element)elAcceptanceSettings, (String)"ResultsCount");
        int stabilityRangePct = XMLUtil.getNodeIntValue((Element)elAcceptanceSettings, (String)"StabilityRange");
        settings = settings + "\n" + L.t((String)"Filtering: Parameters to pass: %d%%, Stable area results: %d, Stability range: %d%%", (Object[])new Object[]{pctToPass, stableAreaCount, stabilityRangePct});
        return settings;
    }

    public void saveDataToFile(ResultsGroup rg, JarOutputStream jarOutStream) throws Exception {
        String resultKey = rg.getMainResultKey();
        Result result = rg.mainResult();
        resultKey = SQUtils.correctResultKeyToDirname((String)resultKey);
        SequentialOptimizationResults results = result.getSequentialOptimizaionResults();
        if (results == null) {
            return;
        }
        Element elChainOptimization = results.toXML();
        JarEntry entry = new JarEntry("Results/" + resultKey + "/" + this.getSettingName() + "_Results.xml");
        jarOutStream.putNextEntry(entry);
        Document myDocument = new Document(elChainOptimization);
        BufferedWriter outputStream = new BufferedWriter(new OutputStreamWriter((OutputStream)jarOutStream, "UTF8"));
        XMLOutputter outputter = new XMLOutputter(Format.getPrettyFormat());
        outputter.output(myDocument, (Writer)outputStream);
    }

    public void loadDataFromFile(ResultsGroup rg, JarFile jarFile) throws Exception {
        String resultKey = rg.getMainResultKey();
        Result result = rg.mainResult();
        resultKey = SQUtils.correctResultKeyToDirname((String)resultKey);
        JarEntry globalXml = jarFile.getJarEntry("Results/" + resultKey + "/" + this.getSettingName() + "_Results.xml");
        if (globalXml == null) {
            return;
        }
        Element element = XMLUtil.readXmlFile((InputStream)jarFile.getInputStream(globalXml));
        SequentialOptimizationResults results = new SequentialOptimizationResults().fromXML(element);
        result.setSequentialOptimizationResults(results);
    }

    public int getBadStrategyReason() {
        return 10039;
    }

    public boolean doesCreateSubjobs() {
        return true;
    }

    public void setLastEvent(String message) {
    }

    protected SettingsMap prepareSettings(String name, SettingsMap mainSettings, Element strategyXml, boolean singleThreaded) throws Exception {
        return null;
    }

    public boolean disabledForSpecialTrial() {
        return true;
    }
}

