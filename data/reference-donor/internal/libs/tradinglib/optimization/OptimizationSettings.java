/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  com.strategyquant.lib.XMLUtil
 *  org.jdom2.Element
 *  org.slf4j.Logger
 *  org.slf4j.LoggerFactory
 */
package com.strategyquant.tradinglib.optimization;

import com.strategyquant.lib.XMLUtil;
import com.strategyquant.tradinglib.Databank;
import com.strategyquant.tradinglib.conditions.Condition;
import com.strategyquant.tradinglib.optimization.BadOptimizationParamsException;
import com.strategyquant.tradinglib.optimization.OptimizationParams;
import com.strategyquant.tradinglib.optimization.Parameter;
import com.strategyquant.tradinglib.optimization.ParametersSettings;
import com.strategyquant.tradinglib.project.ProjectConfigHelper;
import com.strategyquant.tradinglib.project.ProjectEngine;
import java.io.File;
import java.io.Serializable;
import java.util.ArrayList;
import java.util.HashMap;
import org.jdom2.Element;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

public class OptimizationSettings
implements Serializable {
    public static final Logger Log = LoggerFactory.getLogger((String)"OptimizationSettings");
    private static final String SOURCE_FALLBACK = "<Source type=\"2\" relativePath=\"false\" />";
    private static final String WALKFORWARD_FALLBACK = "<WalkForward type=\"0\" period=\"30\" optimization=\"15\">\n      <Param1 value=\"20\" />\n      <Param2 value=\"10\" />\n    </WalkForward>";
    private String projectName;
    public int type;
    public boolean singleStrategy;
    public boolean storeAll;
    public boolean floating;
    public int periodType;
    public int optimizationType;
    public int param1Start;
    public int param1Stop;
    public int param1Step;
    public int param2Start;
    public int param2Stop;
    public int param2Step;
    public File strategyFile;
    public OptimizationParams parameters = new OptimizationParams();
    public int optimizationMethod;
    public Databank inputDatabank = null;
    public Databank outputDatabank = null;
    public int maxOptimizationBacktests = 0;
    public Element elConditions;
    public ArrayList<Condition> conditions;
    public int thresholdPct;
    public int robCombRows;
    public int robCombCols;
    public int robMinComb;
    public boolean singleThreaded = false;
    public boolean deleteFailedStr = false;
    public boolean dontSaveOriginalStr = false;
    public int stableAreaCount;
    public int stabilityRangePct;
    public int pctToPass;
    private String taskName = null;
    private HashMap<String, ParametersSettings> configParamSettings;
    private String projectLogMessage = "";
    public String debugWFFitnessPath = null;

    public OptimizationSettings(String string) {
        this.projectName = string;
    }

    public void setFromXML(Element element, Element element2) throws Exception {
        String string;
        block14: {
            this.type = XMLUtil.tryGetIntAttr((Element)element2, (String)"type");
            this.maxOptimizationBacktests = XMLUtil.getIntAttr((Element)element2, (String)"maxOptimizations", (int)100);
            this.taskName = this.recognizeTaskName(element);
            Element element3 = XMLUtil.getChildElem((Element)element2, (String)"Source", (String)SOURCE_FALLBACK);
            boolean bl = this.singleStrategy = XMLUtil.tryGetIntAttr((Element)element3, (String)"type") == 1;
            if (this.singleStrategy) {
                this.inputDatabank = (Databank)ProjectEngine.get(this.projectName).getDatabanks().get("Results");
                try {
                    string = element3.getTextTrim();
                    this.strategyFile = new File(string);
                    if (!this.strategyFile.exists()) {
                        throw new Exception(String.format("Selected strategy file '%s' doesn't exist.", string));
                    }
                    break block14;
                }
                catch (Exception exception) {
                    throw new Exception("Cannot get input strategy. " + exception.getMessage(), exception);
                }
            }
            this.inputDatabank = this.projectName.equals("Optimizer") ? (Databank)ProjectEngine.get(this.projectName).getDatabanks().get("Strategies to optimize") : ProjectConfigHelper.getInputDatabank(this.projectName, element2.getParentElement());
        }
        if (this.projectName.equals("Optimizer")) {
            this.outputDatabank = (Databank)ProjectEngine.get(this.projectName).getDatabanks().get("Results");
        } else {
            try {
                this.outputDatabank = ProjectConfigHelper.getOutputDatabank(this.projectName, element2.getParentElement());
            }
            catch (Exception exception) {
                this.outputDatabank = (Databank)ProjectEngine.get(this.projectName).getDatabanks().get("Results");
            }
        }
        string = XMLUtil.getChildElem((Element)element, (String)"Rankings");
        Element element4 = string.getChild("WalkForward");
        if (element4 == null) {
            throw new Exception("Walk-Forward Optimization is missing Robustness settings");
        }
        this.dontSaveOriginalStr = XMLUtil.getBoolean((Element)element4, (String)"DontSaveOriginalStr", (boolean)false);
        switch (this.type) {
            case 1: 
            case 4: {
                this.loadSimpleSettings(element2);
                break;
            }
            case 2: {
                this.loadWalkForwardSettings(element2);
                break;
            }
            case 3: {
                this.loadWalkForwardSettings(element2);
                break;
            }
            default: {
                throw new Exception("Unknown optimization type '" + this.type + "'. ");
            }
        }
    }

    private String recognizeTaskName(Element element) {
        if (element == null) {
            return null;
        }
        Element element2 = element.getParentElement();
        if (element2 == null) {
            return null;
        }
        return element2.getAttributeValue("type");
    }

    private void loadSimpleSettings(Element element) throws Exception {
        Element element2 = XMLUtil.getChildElem((Element)element, (String)"SimpleOptimization");
        this.storeAll = XMLUtil.tryGetIntAttr((Element)element2, (String)"type") == 5;
        this.stableAreaCount = XMLUtil.tryGetIntAttr((Element)element2, (String)"resultsCount");
        this.stabilityRangePct = XMLUtil.tryGetIntAttr((Element)element2, (String)"stabilityRange");
        this.pctToPass = XMLUtil.tryGetIntAttr((Element)element2, (String)"pctToPass");
    }

    private void loadWalkForwardSettings(Element element) throws Exception {
        Element element2 = XMLUtil.getChildElem((Element)element, (String)"WalkForward", (String)WALKFORWARD_FALLBACK);
        this.optimizationType = XMLUtil.tryGetIntAttr((Element)element2, (String)"type");
        if (this.optimizationType < 0) {
            this.optimizationType = 0;
        }
        this.periodType = XMLUtil.tryGetIntAttr((Element)element2, (String)"period");
        if (this.periodType < 0) {
            this.periodType = 20;
        }
        this.floating = XMLUtil.tryGetIntAttr((Element)element2, (String)"optimization") == 15;
        Element element3 = XMLUtil.getChildElem((Element)element2, (String)"Param1");
        Element element4 = XMLUtil.getChildElem((Element)element2, (String)"Param2");
        if (this.type == 2) {
            this.param1Stop = this.param1Start = XMLUtil.tryGetIntAttr((Element)element3, (String)"value");
            this.param1Step = 0;
            this.param2Stop = this.param2Start = XMLUtil.tryGetIntAttr((Element)element4, (String)"value");
            this.param2Step = 0;
        } else {
            this.param1Start = XMLUtil.tryGetIntAttr((Element)element3, (String)"start");
            this.param1Stop = XMLUtil.tryGetIntAttr((Element)element3, (String)"stop");
            this.param1Step = XMLUtil.tryGetIntAttr((Element)element3, (String)"step");
            this.param2Start = XMLUtil.tryGetIntAttr((Element)element4, (String)"start");
            this.param2Stop = XMLUtil.tryGetIntAttr((Element)element4, (String)"stop");
            this.param2Step = XMLUtil.tryGetIntAttr((Element)element4, (String)"step");
        }
    }

    public void verify() throws BadOptimizationParamsException {
        if (this.isOptimizationConfigurable()) {
            this.verifyStandard();
        } else {
            this.verifyStandard();
        }
    }

    public void verifyStandard() throws BadOptimizationParamsException {
        if (this.type == 1 || this.type == 4) {
            return;
        }
        String string = "";
        if (this.type == 3) {
            string = "start";
        }
        if (this.periodType == 10) {
            this.checkInRange(this.param1Start, 1, 95, String.format("Misconfiguration of Walk-Forward - OOS period %% %s ", string));
            this.checkInRange(this.param2Start, 1, 95, String.format("Misconfiguration of Walk-Forward - runs %s ", string));
        } else if (this.periodType == 20) {
            this.checkInRange(this.param1Start, 5, 100000, String.format("Misconfiguration of Walk-Forward - In Sample days  %s ", string));
            this.checkInRange(this.param2Start, 5, 100000, String.format("Misconfiguration of Walk-Forward - Out Of Sample days %s ", string));
        } else {
            this.checkInRange(this.param1Start, 5, 500000, String.format("Misconfiguration of Walk-Forward - In Sample bars  %s ", string));
            this.checkInRange(this.param2Start, 5, 500000, String.format("Misconfiguration of Walk-Forward - Out Of Sample bars %s ", string));
        }
        if (this.type != 3) {
            return;
        }
        if (this.periodType == 10) {
            this.checkInRange(this.param1Stop, 1, 95, "Misconfiguration of Walk-Forward - OOS period % stop");
            this.checkInRange(this.param2Stop, 1, 95, "Misconfiguration of Walk-Forward - runs stop");
        } else if (this.periodType == 20) {
            this.checkInRange(this.param1Stop, 5, 100000, "Misconfiguration of Walk-Forward - In Sample days stop");
            this.checkInRange(this.param2Stop, 5, 100000, "Misconfiguration of Walk-Forward - Out Of Sample days stop");
        } else {
            this.checkInRange(this.param1Stop, 5, 500000, "Misconfiguration of Walk-Forward - In Sample bars stop");
            this.checkInRange(this.param2Stop, 5, 500000, "Misconfiguration of Walk-Forward - Out Of Sample bars stop");
        }
        if (this.periodType == 10) {
            this.checkInRange(this.param1Step, 1, 95, "Misconfiguration of Walk-Forward - OOS period % step");
            this.checkInRange(this.param2Step, 1, 95, "Misconfiguration of Walk-Forward - runs step");
        } else if (this.periodType == 20) {
            this.checkInRange(this.param1Step, 5, 5000, "Misconfiguration of Walk-Forward - In Sample days step");
            this.checkInRange(this.param2Step, 5, 5000, "Misconfiguration of Walk-Forward - Out Of Sample days step");
        } else {
            this.checkInRange(this.param1Step, 5, 50000, "Misconfiguration of Walk-Forward - In Sample bars step");
            this.checkInRange(this.param2Step, 5, 50000, "Misconfiguration of Walk-Forward - Out Of Sample bars step");
        }
        int n = Math.abs((this.param1Stop - this.param1Start) / this.param1Step + 1);
        string = this.periodType == 10 ? "OOS period %" : (this.periodType == 20 ? "In Sample days" : "In Sample bars");
        this.checkInRange(n, 1, 100, String.format("Misconfiguration of Walk-Forward - too many steps for %s", string));
        n = Math.abs((this.param2Stop - this.param2Start) / this.param2Step + 1);
        string = this.periodType == 10 ? "runs" : (this.periodType == 20 ? "Out Of Sample days" : "Out Of Sample bars");
        this.checkInRange(n, 1, 100, String.format("Misconfiguration of Walk-Forward - too many steps for %s", string));
    }

    private void checkInRange(int n, int n2, int n3, String string) throws BadOptimizationParamsException {
        if (n < n2) {
            throw new BadOptimizationParamsException(String.format("%s must be bigger than %d !", string, n2));
        }
        if (n > n3) {
            throw new BadOptimizationParamsException(String.format("%s must be smaller than %d !", string, n3));
        }
    }

    public short[] transformToFullIndexes(short[] sArray) {
        short[] sArray2 = new short[this.parameters.size()];
        int n = 0;
        for (int i = 0; i < this.parameters.size(); ++i) {
            Parameter parameter = (Parameter)this.parameters.get(i);
            if (!parameter.isUsed()) {
                sArray2[i] = 0;
                continue;
            }
            sArray2[i] = sArray[n];
            ++n;
        }
        return sArray2;
    }

    public OptimizationSettings clone() {
        OptimizationSettings optimizationSettings = new OptimizationSettings(this.projectName);
        optimizationSettings.type = this.type;
        optimizationSettings.singleStrategy = this.singleStrategy;
        optimizationSettings.storeAll = this.storeAll;
        optimizationSettings.optimizationType = this.optimizationType;
        optimizationSettings.periodType = this.periodType;
        optimizationSettings.floating = this.floating;
        optimizationSettings.param1Start = this.param1Start;
        optimizationSettings.param1Stop = this.param1Stop;
        optimizationSettings.param1Step = this.param1Step;
        optimizationSettings.param2Start = this.param2Start;
        optimizationSettings.param2Stop = this.param2Stop;
        optimizationSettings.param2Step = this.param2Step;
        optimizationSettings.strategyFile = this.strategyFile;
        optimizationSettings.parameters = this.parameters.clone();
        optimizationSettings.optimizationMethod = this.optimizationMethod;
        optimizationSettings.inputDatabank = this.inputDatabank;
        optimizationSettings.outputDatabank = this.outputDatabank;
        optimizationSettings.maxOptimizationBacktests = this.maxOptimizationBacktests;
        optimizationSettings.elConditions = this.elConditions;
        optimizationSettings.conditions = this.conditions;
        optimizationSettings.thresholdPct = this.thresholdPct;
        optimizationSettings.robCombRows = this.robCombRows;
        optimizationSettings.robCombCols = this.robCombCols;
        optimizationSettings.robMinComb = this.robMinComb;
        optimizationSettings.singleThreaded = this.singleThreaded;
        optimizationSettings.deleteFailedStr = this.deleteFailedStr;
        optimizationSettings.dontSaveOriginalStr = this.dontSaveOriginalStr;
        optimizationSettings.debugWFFitnessPath = this.debugWFFitnessPath;
        return optimizationSettings;
    }

    public boolean isOptimizationConfigurable() {
        return this.taskName != null && this.taskName.equals("OptimizeConfigurable");
    }

    public String getProjectLogMessage() {
        return this.projectLogMessage;
    }
}

