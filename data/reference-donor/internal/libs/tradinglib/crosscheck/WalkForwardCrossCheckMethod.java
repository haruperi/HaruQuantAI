/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  com.strategyquant.gridlib.client.GridJob
 *  com.strategyquant.lib.SettingsMap
 *  com.strategyquant.lib.ValuesMap
 *  com.strategyquant.lib.XMLUtil
 *  org.jdom2.Element
 */
package com.strategyquant.tradinglib.crosscheck;

import com.strategyquant.gridlib.client.GridJob;
import com.strategyquant.lib.SettingsMap;
import com.strategyquant.lib.ValuesMap;
import com.strategyquant.lib.XMLUtil;
import com.strategyquant.tradinglib.DatabankColumn;
import com.strategyquant.tradinglib.Order;
import com.strategyquant.tradinglib.OrdersList;
import com.strategyquant.tradinglib.Result;
import com.strategyquant.tradinglib.ResultsGroup;
import com.strategyquant.tradinglib.SQStats;
import com.strategyquant.tradinglib.StrategyBase;
import com.strategyquant.tradinglib.Variable;
import com.strategyquant.tradinglib.WalkForwardColumn;
import com.strategyquant.tradinglib.WalkForwardResult;
import com.strategyquant.tradinglib.crosscheck.CrossCheckDataNotExistException;
import com.strategyquant.tradinglib.crosscheck.CrossCheckMethod;
import com.strategyquant.tradinglib.crosscheck.ICrossCheck;
import com.strategyquant.tradinglib.databank.DatabankColumnTypes;
import com.strategyquant.tradinglib.databank.DatabankColumns;
import com.strategyquant.tradinglib.optimization.BadOptimizationParamsException;
import com.strategyquant.tradinglib.optimization.INewResultListener;
import com.strategyquant.tradinglib.optimization.IStepsListener;
import com.strategyquant.tradinglib.optimization.OptimizationEngine;
import com.strategyquant.tradinglib.optimization.OptimizationParams;
import com.strategyquant.tradinglib.optimization.OptimizationSettings;
import com.strategyquant.tradinglib.optimization.Parameter;
import com.strategyquant.tradinglib.optimization.ParametersSettings;
import com.strategyquant.tradinglib.optimization.WalkForwardColumns;
import com.strategyquant.tradinglib.optimization.WalkForwardMatrixResult;
import com.strategyquant.tradinglib.optimization.WalkForwardParametersStability;
import com.strategyquant.tradinglib.project.ILastEventListener;
import java.util.List;
import org.jdom2.Element;

public abstract class WalkForwardCrossCheckMethod
extends CrossCheckMethod {
    protected static final String SeqOpt_CROSSCHECK = "SequentialOptimization_CrossCheck";
    protected static final String WFO_CROSSCHECK = "WalkForwardOptimization_CrossCheck";
    protected static final String WFM_CROSSCHECK = "WalkForwardMatrix_CrossCheck";
    protected OptimizationSettings optimizationSettings;
    protected ValuesMap paramTypes = new ValuesMap();
    protected boolean paramSymmetry = true;
    protected Element elRankings;
    private String taskName;

    public WalkForwardCrossCheckMethod(String string) {
        this.taskName = string;
        this.optimizationSettings = new OptimizationSettings(string);
        this.paramTypes.set("ParamTypeRecommended", (Object)true);
    }

    @Override
    public String getSettingName() {
        return this.getClass().getSimpleName();
    }

    @Override
    public int getType() {
        return 2;
    }

    @Override
    public int getNumberOfSimulations() {
        return 0;
    }

    @Override
    public boolean doesRetest() {
        return true;
    }

    @Override
    public boolean doesForEverySetup() {
        return false;
    }

    @Override
    public boolean runTest(final ResultsGroup resultsGroup, int n, double d, GridJob gridJob, boolean bl, ILastEventListener iLastEventListener, String string) throws Exception {
        String string2 = resultsGroup.getMainResultKey();
        Result result = resultsGroup.subResult(string2);
        SettingsMap settingsMap = result.getSettings();
        Element element = result.getStrategyXml();
        SettingsMap settingsMap2 = this.prepareSettings(resultsGroup.getName(), settingsMap, element, bl);
        OptimizationEngine optimizationEngine = new OptimizationEngine(this.taskName, this.stopPauseEngine, gridJob, "WFCC", iLastEventListener, null);
        optimizationEngine.initialize(settingsMap2);
        optimizationEngine.setNewResultListener(new INewResultListener(){
            final /* synthetic */ WalkForwardCrossCheckMethod this$0;
            {
                this.this$0 = walkForwardCrossCheckMethod;
            }

            @Override
            public void newResult(ResultsGroup resultsGroup2) throws Exception {
                this.this$0.processResult(resultsGroup, resultsGroup2);
            }
        });
        optimizationEngine.setStepsListener(new IStepsListener(){

            @Override
            public void step(int n) {
                WalkForwardCrossCheckMethod.this.backtestProgressListener.increaseProgressStep();
            }
        });
        try {
            optimizationEngine.optimize();
        }
        catch (BadOptimizationParamsException badOptimizationParamsException) {
            if (badOptimizationParamsException.getMessage().equals("Misconfiguration - no parameter was chosen to be optimized")) {
                Log.debug("CrossCheck Optimization exception", (Throwable)badOptimizationParamsException);
                return true;
            }
            throw badOptimizationParamsException;
        }
        return this.checkConditions(resultsGroup, n);
    }

    protected void processResult(ResultsGroup resultsGroup, ResultsGroup resultsGroup2) {
        try {
            Object object;
            int n;
            Result result = resultsGroup2.mainResult();
            Result result2 = resultsGroup.mainResult();
            WalkForwardMatrixResult walkForwardMatrixResult = (WalkForwardMatrixResult)result.get("WalkForwardResult");
            if (walkForwardMatrixResult != null) {
                result2.set("WalkForwardResult", walkForwardMatrixResult);
                resultsGroup.specialValues().set("WalkForwardConditions", resultsGroup2.specialValues().get("WalkForwardConditions"));
            }
            List<String> list = resultsGroup2.getResultKeys();
            OrdersList ordersList = resultsGroup2.orders();
            for (n = 0; n < ordersList.size(); ++n) {
                object = ordersList.get(n);
                ((Order)object).IsInPortfolio = 0;
            }
            for (n = 0; n < list.size(); ++n) {
                object = list.get(n);
                if (!((String)object).startsWith("WF:")) continue;
                resultsGroup.moveResultFrom((String)object, resultsGroup2, true);
            }
            resultsGroup2.orders().clear();
            WalkForwardParametersStability.compute(resultsGroup, this.optimizationSettings.parameters);
        }
        catch (Exception exception) {
            Log.info("Error processing WF Optimization result", (Throwable)exception);
        }
    }

    protected OptimizationParams initializeParams(StrategyBase strategyBase, int n, int n2, int n3) {
        Parameter parameter;
        Object object2;
        OptimizationParams optimizationParams = new OptimizationParams();
        for (Object object2 : strategyBase.variables()) {
            if (((Variable)object2).getName().startsWith("Magic") || ((Variable)object2).getName().contains("EntrySignal") || ((Variable)object2).getName().contains("ExitSignal") || ((Variable)object2).getName().contains("ReplaceExistingOrders") || ((Variable)object2).getInternalType() == 3) continue;
            optimizationParams.addParam(ParametersSettings.createParameter((Variable)object2, n, n2, n3));
        }
        if (Log.isDebugEnabled()) {
            Log.debug("Variables count: {}", (Object)strategyBase.variables().size());
        }
        int n4 = 1;
        object2 = optimizationParams.iterator();
        while (object2.hasNext() && (n4 *= (parameter = (Parameter)object2.next()).getCombinationsCount()) != 0) {
        }
        Log.debug("Total combinations: {}", (Object)n4);
        return optimizationParams;
    }

    @Override
    protected boolean checkConditions(ResultsGroup resultsGroup, int n) {
        try {
            WalkForwardMatrixResult walkForwardMatrixResult = (WalkForwardMatrixResult)resultsGroup.mainResult().get("WalkForwardResult");
            if (walkForwardMatrixResult != null && !walkForwardMatrixResult.passed) {
                this.dismissalReason = 300000 + n * 1000;
                this.dismissalMessage = String.format("Cross Check filter in '%s': %s", this.getName(), walkForwardMatrixResult.dismissalMessage);
                return false;
            }
        }
        catch (Exception exception) {
            Log.error("Error while evaluating WF conditions. Exc.", (Throwable)exception);
        }
        return true;
    }

    @Override
    public double getStatsValue(ResultsGroup resultsGroup, String string, Element element, Object ... objectArray) throws Exception {
        WalkForwardResult walkForwardResult = null;
        if (objectArray.length > 1 && objectArray[1] instanceof WalkForwardResult) {
            walkForwardResult = (WalkForwardResult)objectArray[1];
        } else {
            WalkForwardMatrixResult walkForwardMatrixResult = (WalkForwardMatrixResult)resultsGroup.mainResult().get("WalkForwardResult");
            if (walkForwardMatrixResult == null) {
                throw new CrossCheckDataNotExistException(this.getName());
            }
            walkForwardResult = walkForwardMatrixResult.getWFResult(resultsGroup.getBestWFResultKey(), true);
            if (walkForwardResult == null) {
                walkForwardResult = walkForwardMatrixResult.getResultList().get(0);
            }
        }
        int n = XMLUtil.getByteAttr((Element)element, (String)"subresult", (byte)30);
        byte by = XMLUtil.getByteAttr((Element)element, (String)"direction", (byte)0);
        byte by2 = XMLUtil.getByteAttr((Element)element, (String)"sampleType", (byte)127);
        byte by3 = XMLUtil.getByteAttr((Element)element, (String)"plType", (byte)10);
        if (WalkForwardColumns.get().checkClassExists(string)) {
            n = 33;
        }
        switch (n) {
            case 30: {
                DatabankColumn databankColumn = (DatabankColumn)DatabankColumns.get().findClassByName(string);
                SQStats sQStats = resultsGroup.subResult(walkForwardResult.resultName).stats(by, by3, by2);
                return databankColumn.getNumericValue(sQStats);
            }
            case 32: {
                DatabankColumn databankColumn = (DatabankColumn)DatabankColumns.get().findClassByName(string);
                return databankColumn.getNumericValue(walkForwardResult.statsScore);
            }
            case 31: {
                DatabankColumn databankColumn = (DatabankColumn)DatabankColumns.get().findClassByName(string);
                return databankColumn.getNumericValue(walkForwardResult.statsStability);
            }
            case 33: {
                WalkForwardColumn walkForwardColumn = (WalkForwardColumn)WalkForwardColumns.get().findClassByName(string);
                return walkForwardColumn.getNumericValue(walkForwardResult.statsSpecial);
            }
        }
        return 0.0;
    }

    @Override
    public boolean hasStatsValue(ResultsGroup resultsGroup, String string, Element element, Object ... objectArray) throws Exception {
        if (objectArray.length > 1 && objectArray[1] instanceof WalkForwardResult) {
            return true;
        }
        WalkForwardMatrixResult walkForwardMatrixResult = (WalkForwardMatrixResult)resultsGroup.mainResult().get("WalkForwardResult");
        return walkForwardMatrixResult != null;
    }

    @Override
    public String printSpecialValue(ResultsGroup resultsGroup, String string, Element element, Object ... objectArray) throws Exception {
        WalkForwardMatrixResult walkForwardMatrixResult = (WalkForwardMatrixResult)resultsGroup.mainResult().get("WalkForwardResult");
        if (walkForwardMatrixResult == null) {
            throw new CrossCheckDataNotExistException(this.getName());
        }
        DatabankColumn databankColumn = (DatabankColumn)DatabankColumns.get().findClassByName(string);
        return databankColumn.getValue(resultsGroup, resultsGroup.getMainResultKey(), (byte)0, (byte)10, (byte)127);
    }

    @Override
    public String getColumnTitle(String string, Element element, Object ... objectArray) {
        byte by = XMLUtil.getByteAttr((Element)element, (String)"subresult", (byte)30);
        String string2 = this.getColumnTitleTemplate();
        if (string2 != null && string != null) {
            string2 = string2.replace("#columnName#", string);
            string2 = string2.replace("#subresult#", DatabankColumnTypes.typeToString(by));
        }
        return string2;
    }

    @Override
    public String getColumnTitleTemplate() {
        return "#subresult# #columnName#";
    }

    @Override
    public boolean doesCreateSubjobs() {
        return true;
    }

    protected void readWhatToParametrize(Element element) {
        boolean bl = true;
        try {
            bl = XMLUtil.getNodeValue((Element)element, (String)"Recommended", (String)"true").equals("true");
        }
        catch (Exception exception) {
            // empty catch block
        }
        if (bl) {
            this.paramTypes.set("ParamTypeRecommended", (Object)true);
            this.paramSymmetry = true;
        } else {
            this.paramTypes.set("ParamTypeRecommended", (Object)false);
            this.paramTypes.set("ParamTypePeriod", (Object)XMLUtil.getNodeValue((Element)element, (String)"Periods", (String)"false").equals("true"));
            this.paramTypes.set("ParamTypeShift", (Object)XMLUtil.getNodeValue((Element)element, (String)"Shifts", (String)"false").equals("true"));
            this.paramTypes.set("ParamTypeConstant", (Object)XMLUtil.getNodeValue((Element)element, (String)"Constants", (String)"false").equals("true"));
            this.paramTypes.set("ParamTypeOtherParam", (Object)XMLUtil.getNodeValue((Element)element, (String)"OtherParams", (String)"false").equals("true"));
            this.paramTypes.set("ParamTypeExitUsed", (Object)XMLUtil.getNodeValue((Element)element, (String)"ExitParamsUsed", (String)"false").equals("true"));
            this.paramTypes.set("ParamTypeExitUnused", (Object)XMLUtil.getNodeValue((Element)element, (String)"ExitParamsUnused", (String)"false").equals("true"));
            this.paramTypes.set("ParamTypeBoolean", (Object)XMLUtil.getNodeValue((Element)element, (String)"BooleanParams", (String)"false").equals("true"));
            this.paramTypes.set("ParamTypeTradingOptions", (Object)XMLUtil.getNodeValue((Element)element, (String)"TradingOptions", (String)"false").equals("true"));
            this.paramTypes.set("ParamTypeEntryLevel", (Object)XMLUtil.getNodeValue((Element)element, (String)"EntryParams", (String)"false").equals("true"));
            this.paramTypes.set("ParamTypeEntryLogic", (Object)XMLUtil.getNodeValue((Element)element, (String)"EntryLogic", (String)"false").equals("true"));
            this.paramSymmetry = XMLUtil.elementIs((Element)element, (String)"symmetricVariables");
        }
    }

    @Override
    public abstract ICrossCheck clone(SettingsMap var1);

    protected abstract SettingsMap prepareSettings(String var1, SettingsMap var2, Element var3, boolean var4) throws Exception;
}

