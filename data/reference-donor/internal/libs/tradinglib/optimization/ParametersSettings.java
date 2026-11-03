/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  com.strategyquant.lib.L
 *  com.strategyquant.lib.SQTime
 *  com.strategyquant.lib.SQUtils
 *  com.strategyquant.lib.ValuesMap
 *  com.strategyquant.lib.XMLUtil
 *  org.jdom2.Element
 *  org.slf4j.Logger
 *  org.slf4j.LoggerFactory
 */
package com.strategyquant.tradinglib.optimization;

import com.strategyquant.lib.L;
import com.strategyquant.lib.SQTime;
import com.strategyquant.lib.SQUtils;
import com.strategyquant.lib.ValuesMap;
import com.strategyquant.lib.XMLUtil;
import com.strategyquant.tradinglib.StrategyBase;
import com.strategyquant.tradinglib.TradingOption;
import com.strategyquant.tradinglib.Variable;
import com.strategyquant.tradinglib.optimization.OptimizationParams;
import com.strategyquant.tradinglib.optimization.Parameter;
import com.strategyquant.tradinglib.project.ProjectConfigHelper;
import java.io.BufferedReader;
import java.io.File;
import java.io.FileReader;
import java.util.ArrayList;
import java.util.HashMap;
import org.jdom2.Element;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

public class ParametersSettings {
    public static final Logger Log = LoggerFactory.getLogger((String)"ParametersSettings");
    public static final ValuesMap AllParamTypes = new ValuesMap();
    private static final String OPTMETHOD_FALBACK = "<OptimizationMethod settings=\"automatic\" symmetricVariables=\"false\" symmetryDisabled=\"false\" method=\"brute-force\" maxSteps=\"20\" />";
    private static final String WHATTOPARAM_FALLBACK = "<WhatToParametrize type=\"0\">\n      <Recommended>true</Recommended>\n      <Periods>false</Periods>\n      <Shifts>false</Shifts>\n      <Constants>false</Constants>\n      <OtherParams>false</OtherParams>\n      <EntryParams>false</EntryParams>\n      <EntryLogic>false</EntryLogic>\n      <ExitParamsUsed>false</ExitParamsUsed>\n      <ExitParamsUnused>false</ExitParamsUnused>\n      <BooleanParams>false</BooleanParams>\n      <TradingOptions>false</TradingOptions>\n    </WhatToParametrize>";
    private static final String AUTOSETTINGS_FALLBACK = "<AutomaticSettings distributionUp=\"20\" distributionDown=\"20\" maxSteps=\"20\" ignoreMagicNumbers=\"undefined\" ignoreBoolean=\"undefined\" ignoreDouble=\"undefined\" distribution=\"20\" />";
    public OptimizationParams params = new OptimizationParams();
    public boolean manualMode;
    public boolean symmetry;
    public int method;
    public int distributionUp;
    public int distributionDown;
    public int maxSteps;
    public long combinationsCount;
    public ValuesMap paramTypes = new ValuesMap();

    public ParametersSettings() {
        AllParamTypes.set("ParamTypePeriod", (Object)true);
        AllParamTypes.set("ParamTypeShift", (Object)false);
        AllParamTypes.set("ParamTypeConstant", (Object)false);
        AllParamTypes.set("ParamTypeOtherParam", (Object)false);
        AllParamTypes.set("ParamTypeEntryLevel", (Object)true);
        AllParamTypes.set("ParamTypeEntryLogic", (Object)false);
        AllParamTypes.set("ParamTypeExitUsed", (Object)true);
        AllParamTypes.set("ParamTypeExitUnused", (Object)false);
        AllParamTypes.set("ParamTypeBoolean", (Object)false);
        AllParamTypes.set("ParamTypeTradingOptions", (Object)false);
    }

    public void setFromXML(Element element, Element element2) throws Exception {
        try {
            Object object;
            Element element3 = XMLUtil.getChildElem((Element)element, (String)"Optimization");
            Element element4 = XMLUtil.getChildElem((Element)element3, (String)"OptimizationMethod", (String)OPTMETHOD_FALBACK);
            Element element5 = XMLUtil.getChildElem((Element)element3, (String)"WhatToParametrize", (String)WHATTOPARAM_FALLBACK);
            int n = XMLUtil.getIntAttr((Element)element3, (String)"type", (int)1);
            boolean bl = false;
            try {
                bl = XMLUtil.getNodeValue((Element)element5, (String)"Recommended").equals("true");
            }
            catch (Exception exception) {
                // empty catch block
            }
            if (bl) {
                this.paramTypes.set("ParamTypeRecommended", (Object)true);
                this.symmetry = true;
            } else {
                this.paramTypes.set("ParamTypeRecommended", (Object)false);
                this.paramTypes.set("ParamTypePeriod", (Object)XMLUtil.getNodeValue((Element)element5, (String)"Periods").equals("true"));
                this.paramTypes.set("ParamTypeShift", (Object)XMLUtil.getNodeValue((Element)element5, (String)"Shifts").equals("true"));
                this.paramTypes.set("ParamTypeConstant", (Object)XMLUtil.getNodeValue((Element)element5, (String)"Constants").equals("true"));
                this.paramTypes.set("ParamTypeOtherParam", (Object)XMLUtil.getNodeValue((Element)element5, (String)"OtherParams").equals("true"));
                this.paramTypes.set("ParamTypeExitUsed", (Object)XMLUtil.getNodeValue((Element)element5, (String)"ExitParamsUsed").equals("true"));
                this.paramTypes.set("ParamTypeExitUnused", (Object)XMLUtil.getNodeValue((Element)element5, (String)"ExitParamsUnused").equals("true"));
                this.paramTypes.set("ParamTypeBoolean", (Object)XMLUtil.getNodeValue((Element)element5, (String)"BooleanParams").equals("true"));
                this.paramTypes.set("ParamTypeEntryLevel", (Object)XMLUtil.getNodeValue((Element)element5, (String)"EntryParams", (String)"false").equals("true"));
                this.paramTypes.set("ParamTypeEntryLogic", (Object)XMLUtil.getNodeValue((Element)element5, (String)"EntryLogic", (String)"false").equals("true"));
                this.symmetry = XMLUtil.elementIs((Element)element4, (String)"symmetricVariables");
            }
            this.paramTypes.set("ParamTypeTradingOptions", (Object)XMLUtil.getNodeValue((Element)element5, (String)"TradingOptions", (String)"false").equals("true"));
            this.manualMode = element4.getAttributeValue("settings").equals("manual");
            this.method = this.getMethod(element4.getAttributeValue("method"));
            this.params.clear();
            if (this.manualMode) {
                for (Object object2 : XMLUtil.getNestedElements((Element)element3, (String)"Param")) {
                    boolean bl2 = XMLUtil.tryGetBoolAttr((Element)object2, (String)"use");
                    object = object2.getAttributeValue("name");
                    String string = object2.getAttributeValue("type");
                    Object object3 = object2.getAttributeValue("value");
                    byte by = Parameter.getType(string);
                    double d = 0.0;
                    double d2 = 0.0;
                    double d3 = 0.0;
                    double d4 = 0.0;
                    boolean bl3 = XMLUtil.elementIs((Element)object2, (String)"calculateValues");
                    if (bl3) {
                        this.distributionUp = XMLUtil.getIntAttr((Element)object2, (String)"distributionUp", (int)20);
                        this.distributionDown = XMLUtil.getIntAttr((Element)object2, (String)"distributionDown", (int)20);
                        this.maxSteps = XMLUtil.getIntAttr((Element)object2, (String)"maxSteps", (int)10);
                        Parameter parameter = ParametersSettings.createParameter(new Variable((String)object, (String)object, string, (String)object3, false, false), this.distributionUp, this.distributionDown, this.maxSteps);
                        this.params.addParam(parameter);
                        object2.setAttribute("start", String.valueOf(parameter.start));
                        object2.setAttribute("stop", String.valueOf(parameter.stop));
                        object2.setAttribute("step", String.valueOf(parameter.step));
                        continue;
                    }
                    if (by == 4 || by == 1 || by == 5) {
                        d = Double.parseDouble(object2.getAttributeValue("start"));
                        d2 = Double.parseDouble(object2.getAttributeValue("stop"));
                        d3 = Double.parseDouble(object2.getAttributeValue("step"));
                        d4 = Double.parseDouble((String)object3);
                    } else {
                        d4 = object2.getAttributeValue("value").equals("true") ? 1.0 : 0.0;
                    }
                    this.params.addParam((String)object, by, bl2, d, d2, d3, d4);
                }
            } else {
                Object object2;
                Element element6 = XMLUtil.getChildElem((Element)element3, (String)"AutomaticSettings", (String)AUTOSETTINGS_FALLBACK);
                this.distributionUp = XMLUtil.getIntAttr((Element)element6, (String)"distributionUp", (int)20);
                this.distributionDown = XMLUtil.getIntAttr((Element)element6, (String)"distributionDown", (int)20);
                this.maxSteps = XMLUtil.tryGetIntAttr((Element)element6, (String)"maxSteps");
                object2 = StrategyBase.createXmlStrategy(element2);
                ((StrategyBase)object2).transformToVariables(this.symmetry, this.paramTypes);
                ArrayList arrayList = XMLUtil.getNestedElements((Element)element2, (String)"signal");
                object = null;
                try {
                    object = ProjectConfigHelper.getOptions(XMLUtil.getChildElem((Element)element, (String)"Options").getChild("BuildTradingOptions"));
                }
                catch (Exception exception) {
                    Log.error("Cannot load trading options from settings", (Throwable)exception);
                }
                for (Object object3 : ((StrategyBase)object2).variables()) {
                    String[] stringArray;
                    if (((Variable)object3).getName().startsWith("Magic") || this.isSignalVariable(((Variable)object3).getId(), arrayList)) continue;
                    if (object != null && ((Variable)object3).getParamType() == "ParamTypeTradingOptions" && (stringArray = ((Variable)object3).getId().split("\\.")).length == 2) {
                        String string = stringArray[0];
                        String string2 = stringArray[1];
                        for (int i = 0; i < ((ArrayList)object).size(); ++i) {
                            TradingOption tradingOption = (TradingOption)((ArrayList)object).get(i);
                            if (!tradingOption.getClass().getSimpleName().equals(string)) continue;
                            Object object4 = tradingOption.getParameterValue(string2);
                            ((Variable)object3).setFromString(object4.toString());
                        }
                    }
                    this.params.addParam(ParametersSettings.createParameter((Variable)object3, this.distributionUp, this.distributionDown, this.maxSteps));
                }
                if (Log.isDebugEnabled()) {
                    Log.debug("Variables count: {}", (Object)((StrategyBase)object2).variables().size());
                }
            }
            this.combinationsCount = 1L;
            for (Object object2 : this.params) {
                try {
                    this.combinationsCount = n == 4 ? Math.addExact(this.combinationsCount, (long)((Parameter)object2).getCombinationsCount()) : Math.multiplyExact(this.combinationsCount, ((Parameter)object2).getCombinationsCount());
                }
                catch (ArithmeticException arithmeticException) {
                    this.combinationsCount = -1L;
                }
                if (this.combinationsCount >= 0L) continue;
                break;
            }
            Log.debug("Total combinations: {}", (Object)this.combinationsCount);
        }
        catch (Exception exception) {
            throw new Exception("Cannot load Parameters settings. " + exception.getMessage(), exception);
        }
    }

    private boolean isSignalVariable(String string, ArrayList<Element> arrayList) {
        if (arrayList == null || arrayList.size() == 0) {
            return false;
        }
        for (int i = 0; i < arrayList.size(); ++i) {
            Element element = arrayList.get(i);
            String string2 = element.getAttributeValue("variable");
            if (string2 == null || !string2.equals(string)) continue;
            return true;
        }
        return false;
    }

    public static void checkParamValid(double d, double d2, double d3) throws Exception {
        if (d3 == 0.0 && (d != 0.0 || d2 != 0.0) && d != d2) {
            throw new Exception(L.t((String)"Zero step used", (Object[])new Object[0]));
        }
        if ((d2 - d) / d3 <= 0.0) {
            throw new Exception(L.t((String)"Invalid start/stop/step values", (Object[])new Object[0]));
        }
    }

    public static void checkTimeParamValid(int n, int n2, int n3) throws Exception {
        ParametersSettings.checkParamValid(n, n2, n3);
        ParametersSettings.checkTimeValue(n);
        ParametersSettings.checkTimeValue(n2);
        ParametersSettings.checkTimeValue(n3);
    }

    private static void checkTimeValue(int n) throws Exception {
        if (n < 0 || n > 86340) {
            throw new Exception(L.t((String)"Time must be in range 00:00 - 23:59", (Object[])new Object[0]));
        }
    }

    private int getMethod(String string) {
        if (string != null && string.equals("brute-force")) {
            return 1;
        }
        return 0;
    }

    public static Parameter createParameter(Variable variable, int n, int n2, int n3) {
        String string = variable.getName();
        byte by = variable.getInternalType();
        if (variable.getParamType() == null) {
            variable.setParamType("ParamTypeOtherParam");
        }
        double d = 0.0;
        double d2 = 0.0;
        double d3 = 0.0;
        double d4 = 0.0;
        String string2 = variable.getId();
        if (string2.contains("MinimumSL") || string2.contains("MaximumSL") || string2.contains("MinimumPT") || string2.contains("MaximumPT")) {
            d4 = variable.getValueAsDouble();
            d = 0.0;
            d2 = 500.0;
            d3 = ParametersSettings.findStep((int)d, (int)d2, n3);
        } else if (by == 4) {
            double d5 = variable.getValueAsDouble();
            double d6 = d5 / 100.0 * (double)n;
            double d7 = d5 / 100.0 * (double)n2;
            int n4 = 2;
            d4 = variable.getValueAsDouble();
            d = SQUtils.round((double)(d5 - d7), (int)n4);
            d2 = SQUtils.round((double)(d5 + d6), (int)n4);
            d3 = ParametersSettings.findStep(d, d2, n4, n3);
        } else if (by == 1) {
            int n5 = (int)variable.getMin();
            int n6 = (int)variable.getMax();
            if (n5 != Integer.MIN_VALUE && n6 != Integer.MIN_VALUE) {
                d = n5;
                d2 = n6;
            } else {
                double d8 = variable.getValueAsDouble();
                double d9 = d8 / 100.0 * (double)n;
                double d10 = d8 / 100.0 * (double)n2;
                d4 = variable.getValueAsDouble();
                d = (int)(d8 - d10);
                if (d8 <= 3.0 & (d2 = (double)((int)(d8 + d9))) <= 4.0) {
                    d2 = 6.0;
                }
            }
            if (variable.getParamType().equals("ParamTypePeriod")) {
                d = d > 2.0 ? d : 2.0;
            }
            d3 = ParametersSettings.findStep((int)d, (int)d2, n3);
        } else if (by == 5) {
            d4 = variable.getValueAsInt();
            double d11 = SQTime.HHMMToMinutes((int)((int)d4));
            int n7 = (int)(d11 / 100.0 * (double)n);
            int n8 = (int)(d11 / 100.0 * (double)n2);
            d = d11 - (double)n8;
            d = d < 0.0 ? 0.0 : d;
            d2 = d11 + (double)n7;
            d2 = d2 > 1439.0 ? 1439.0 : d2;
            d3 = ParametersSettings.findStep((int)d, (int)d2, n3);
            d = SQTime.minutesToHHMM((int)((int)d));
            d2 = SQTime.minutesToHHMM((int)((int)d2));
            d3 = SQTime.minutesToHHMM((int)((int)d3));
        } else if (by == 2) {
            boolean bl = variable.getValueAsBoolean();
            d = d4 = bl ? 1.0 : 0.0;
        }
        return new Parameter(string, by, true, d, d2, d3, d4);
    }

    private static int findStep(int n, int n2, int n3) {
        double d = ((double)n2 - (double)n) / (double)(n3 - 1);
        if (Math.abs(d - (double)((int)d)) < 0.001) {
            return (int)d;
        }
        d = n2 - n > 0 ? (d < 1.0 ? 1.0 : (double)((int)d)) : (d > -1.0 ? -1.0 : (double)((int)d));
        int n4 = ParametersSettings.getStepsCount(n, n2, d);
        while (n4 > n3 - 1) {
            n4 = ParametersSettings.getStepsCount(n, n2, d += d > 0.0 ? 1.0 : -1.0);
        }
        return (int)d;
    }

    private static double findStep(double d, double d2, int n, int n2) {
        double d3 = (d2 - d) / (double)(n2 - 1);
        double d4 = SQUtils.round((double)d3, (int)n);
        double d5 = 1.0 / Math.pow(10.0, n);
        if (d4 == d3) {
            return d4;
        }
        d3 = d4 > d3 ? (d3 > 0.0 ? d4 - d5 : d4) : (d3 > 0.0 ? d4 : d4 + d5);
        int n3 = ParametersSettings.getStepsCount(d, d2, d3);
        while (n3 > n2 - 1) {
            n3 = ParametersSettings.getStepsCount(d, d2, d3 += d3 >= 0.0 ? d5 : -d5);
        }
        return SQUtils.round((double)d3, (int)n);
    }

    private static int getStepsCount(double d, double d2, double d3) {
        return (int)((d2 - d) / d3);
    }

    public static HashMap<String, ParametersSettings> loadParamConfig(File file) throws Exception {
        HashMap<String, ParametersSettings> hashMap = new HashMap<String, ParametersSettings>();
        try (BufferedReader bufferedReader = new BufferedReader(new FileReader(file));){
            String string;
            int n = 0;
            while ((string = bufferedReader.readLine()) != null) {
                ++n;
                if (string.length() < 2) continue;
                String[] stringArray = string.split(";");
                if (stringArray.length == 0) {
                    throw new Exception("Bad format at line #" + n + ": " + string);
                }
                ParametersSettings parametersSettings = new ParametersSettings();
                parametersSettings.setFromXMLOptimConfig(stringArray, string, n);
                hashMap.put(stringArray[0], parametersSettings);
            }
        }
        return hashMap;
    }

    public void setFromXMLOptimConfig(String[] stringArray, String string, int n) throws Exception {
        try {
            this.manualMode = true;
            this.method = this.getMethod("brute-force");
            this.params.clear();
            for (int i = 1; i < stringArray.length; ++i) {
                Object object = stringArray[i].split(":");
                if (((String[])object).length != 6) {
                    throw new Exception("Cannot parse line #" + n + ": " + string);
                }
                String string2 = object[0];
                byte by = Parameter.getType(object[1]);
                double d = Double.parseDouble((String)object[2]);
                double d2 = Double.parseDouble((String)object[3]);
                double d3 = Double.parseDouble((String)object[4]);
                double d4 = Double.parseDouble((String)object[5]);
                this.params.addParam(string2, by, true, d2, d3, d4, d);
            }
            this.combinationsCount = 1L;
            for (Object object : this.params) {
                try {
                    this.combinationsCount = Math.multiplyExact(this.combinationsCount, ((Parameter)object).getCombinationsCount());
                }
                catch (ArithmeticException arithmeticException) {
                    this.combinationsCount = -1L;
                }
                if (this.combinationsCount >= 0L) continue;
                break;
            }
            Log.debug("Total combinations: {}", (Object)this.combinationsCount);
        }
        catch (Exception exception) {
            throw new Exception("Cannot load Parameters settings. " + exception.getMessage(), exception);
        }
    }
}

