/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  com.strategyquant.datalib.customData.CustomDataInfo
 *  com.strategyquant.lib.IRandomGenerator
 *  com.strategyquant.lib.SQUtils
 *  org.jdom2.Attribute
 *  org.jdom2.Content
 *  org.jdom2.Element
 *  org.slf4j.Logger
 *  org.slf4j.LoggerFactory
 */
package com.strategyquant.tradinglib.blocks.random;

import com.strategyquant.datalib.customData.CustomDataInfo;
import com.strategyquant.lib.IRandomGenerator;
import com.strategyquant.lib.SQUtils;
import com.strategyquant.tradinglib.blocks.annotations.Value;
import com.strategyquant.tradinglib.blocks.random.BlockDefinition;
import com.strategyquant.tradinglib.blocks.random.BlockParameter;
import com.strategyquant.tradinglib.blocks.random.BlocksConfig;
import com.strategyquant.tradinglib.blocks.random.FormulaValue;
import com.strategyquant.tradinglib.blocks.random.ItemRandomValueRanges;
import com.strategyquant.tradinglib.blocks.random.ReplacementChartConfig;
import com.strategyquant.tradinglib.blocks.random.ReplacementConfig;
import com.strategyquant.tradinglib.blocks.random.ReplacementParameters;
import com.strategyquant.tradinglib.blocks.random.ReplacementsConfig;
import com.strategyquant.tradinglib.generator.BlockSettingsConverter;
import com.strategyquant.tradinglib.generator.GenerateException;
import java.util.ArrayList;
import org.jdom2.Attribute;
import org.jdom2.Content;
import org.jdom2.Element;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

public class ReplacementParameter {
    public static final Logger Log = LoggerFactory.getLogger((String)"ReplacementParameter");
    public static final byte Fixed = 1;
    public static final byte Random = 2;
    public static final byte Formula = 3;
    public static final double ATR_BASED_EXIT = -1.0;
    public static final double FIXED_PIPS_EXIT = 1.0;
    public BlockParameter blockParam;
    public byte generation;
    private BlockDefinition blockDef;
    private ReplacementConfig replacementConfig;
    private ReplacementsConfig replacementsConfig;
    private double formulaProbability;
    public String formulaDependentOn;
    private ArrayList<FormulaValue> formulaValues;
    private FormulaValue formulaNoneValue = null;
    private int formulaCummulativeWeight;
    private BlocksConfig blocksConfig;
    private int MinSLInPips;
    private int MaxSLInPips;
    private double MinSLInPercent;
    private double MaxSLInPercent;
    private double MinSLATRMultiple;
    private double MaxSLATRMultiple;
    private int MinSLATRPeriod;
    private int MaxSLATRPeriod;
    private int MinPTInPips;
    private int MaxPTInPips;
    private double MinPTInPercent;
    private double MaxPTInPercent;
    private double MinPTATRMultiple;
    private double MaxPTATRMultiple;
    private int MinPTATRPeriod;
    private int MaxPTATRPeriod;
    private boolean LimitSLPTRRR;
    private double LimitSLPTRRRFromCoef;
    private double LimitSLPTRRRToCoef;

    public ReplacementParameter(byte by, ReplacementsConfig replacementsConfig, BlockParameter blockParameter, BlocksConfig blocksConfig, BlockDefinition blockDefinition, ReplacementConfig replacementConfig) {
        this.blockParam = blockParameter.clone();
        this.replacementConfig = replacementConfig;
        this.replacementsConfig = replacementsConfig;
        this.blocksConfig = blocksConfig;
        this.blockDef = blockDefinition;
        this.generation = (byte)2;
        this.MinSLInPips = replacementConfig.buildSettings.getInt("MinSLInPips");
        this.MaxSLInPips = replacementConfig.buildSettings.getInt("MaxSLInPips");
        if (this.MaxSLInPips < this.MinSLInPips) {
            Log.error(String.format("=== ERROR - MAX is smaller than MIN, min: %d, max: %d", this.MinSLInPips, this.MaxSLInPips));
        }
        this.MinPTInPercent = replacementConfig.buildSettings.getDouble("MinPTInPercent");
        this.MaxPTInPercent = replacementConfig.buildSettings.getDouble("MaxPTInPercent");
        this.MinSLInPercent = replacementConfig.buildSettings.getDouble("MinSLInPercent");
        this.MaxSLInPercent = replacementConfig.buildSettings.getDouble("MaxSLInPercent");
        this.MinSLATRMultiple = replacementConfig.buildSettings.getDouble("MinSLATRMultiple");
        this.MaxSLATRMultiple = replacementConfig.buildSettings.getDouble("MaxSLATRMultiple");
        this.MinSLATRPeriod = replacementConfig.buildSettings.getInt("MinSLATRPeriod");
        this.MaxSLATRPeriod = replacementConfig.buildSettings.getInt("MaxSLATRPeriod");
        this.MinPTInPips = replacementConfig.buildSettings.getInt("MinPTInPips");
        this.MaxPTInPips = replacementConfig.buildSettings.getInt("MaxPTInPips");
        this.MinPTATRMultiple = replacementConfig.buildSettings.getDouble("MinPTATRMultiple");
        this.MaxPTATRMultiple = replacementConfig.buildSettings.getDouble("MaxPTATRMultiple");
        this.MinPTATRPeriod = replacementConfig.buildSettings.getInt("MinPTATRPeriod");
        this.MaxPTATRPeriod = replacementConfig.buildSettings.getInt("MaxPTATRPeriod");
        this.LimitSLPTRRR = replacementConfig.buildSettings.getBoolean("LimitSLPTRRR");
        if (this.LimitSLPTRRR) {
            double d = replacementConfig.buildSettings.getInt("LimitSLPTRRRFrom");
            double d2 = replacementConfig.buildSettings.getInt("LimitSLPTRRRTo");
            this.LimitSLPTRRRFromCoef = 1.0 / (d / 100.0);
            this.LimitSLPTRRRToCoef = 1.0 / (d2 / 100.0);
        }
    }

    ReplacementParameter() {
    }

    private double fixValue(double d, ReplacementChartConfig replacementChartConfig, boolean bl) {
        int n = (int)d;
        switch (n) {
            case -1000003: {
                return replacementChartConfig == null ? d : (double)replacementChartConfig.minPeriod;
            }
            case -1000004: {
                return replacementChartConfig == null ? d : (double)replacementChartConfig.maxPeriod;
            }
            case -1000001: {
                return replacementChartConfig == null ? d : (double)replacementChartConfig.minShift;
            }
            case -1000002: {
                return replacementChartConfig == null ? d : (double)replacementChartConfig.maxShift;
            }
            case -1000005: {
                return this.MinSLInPips;
            }
            case -1000006: {
                return this.MaxSLInPips;
            }
            case -1000019: {
                return this.MinSLInPercent;
            }
            case -1000020: {
                return this.MaxSLInPercent;
            }
            case -1000007: {
                return this.MinSLATRMultiple;
            }
            case -1000008: {
                return this.MaxSLATRMultiple;
            }
            case -1000009: {
                return this.MinSLATRPeriod;
            }
            case -1000010: {
                return this.MaxSLATRPeriod;
            }
            case -1000011: {
                return this.MinPTInPips;
            }
            case -1000012: {
                return this.MaxPTInPips;
            }
            case -1000017: {
                return this.MinPTInPercent;
            }
            case -1000018: {
                return this.MaxPTInPercent;
            }
            case -1000013: {
                return this.MinPTATRMultiple;
            }
            case -1000014: {
                return this.MaxPTATRMultiple;
            }
            case -1000015: {
                return this.MinPTATRPeriod;
            }
            case -1000016: {
                return this.MaxPTATRPeriod;
            }
        }
        return d;
    }

    private boolean isConstantValue(int n) {
        switch (n) {
            case -1000016: 
            case -1000015: 
            case -1000014: 
            case -1000013: 
            case -1000012: 
            case -1000011: 
            case -1000010: 
            case -1000009: 
            case -1000008: 
            case -1000007: 
            case -1000006: 
            case -1000005: 
            case -1000004: 
            case -1000003: 
            case -1000002: 
            case -1000001: {
                return true;
            }
        }
        return false;
    }

    public void initFromGeneratedParam(String string, Element element, Element element2) throws GenerateException {
        Object object;
        String string2 = element.getAttributeValue("generation");
        if (string2 == null) {
            String string3 = element.getParentElement().getParentElement().getAttributeValue("key");
            if (string3 == null) {
                string3 = "Unknown";
            }
            throw new GenerateException(String.format("Bad config - missing 'generation' attribute for parameter with key %s->%s!", string3, element.getAttributeValue("key")));
        }
        switch (string2) {
            case "fixed": {
                this.generation = 1;
                break;
            }
            case "random": {
                this.generation = (byte)2;
                break;
            }
            case "formula": {
                this.generation = (byte)3;
            }
        }
        boolean bl = false;
        Object object2 = element.getAttributes().iterator();
        while (object2.hasNext()) {
            object = (Attribute)object2.next();
            String string4 = object.getName();
            String string5 = object.getValue();
            if (string5.equals("undefined") || string5.equals("null") || string4.equals("key") || string4.equals("name") || string5.equals("")) continue;
            this.blockParam.setParamAttribute(string4, string5);
            bl = true;
        }
        if (this.generation == 1 && (object2 = element.getAttributeValue("type")) != null && (object = element.getText()) != null && !((String)object).equals("")) {
            try {
                if (((String)object2).equals("int")) {
                    int n;
                    this.blockParam.iDefaultValue = n = Integer.parseInt((String)object);
                } else if (((String)object2).equals("double")) {
                    double d;
                    this.blockParam.dDefaultValue = d = Double.parseDouble((String)object);
                }
            }
            catch (NumberFormatException numberFormatException) {
                // empty catch block
            }
        }
        if (bl) {
            this.blockParam.initializeRanges(this.generation == 2, this.blockDef.key);
            this.blockParam.recognizeDecimals();
        }
        if (this.generation == 3 && element2 != null) {
            this.initFormulas(element2);
        }
    }

    private void initFormulas(Element element) throws GenerateException {
        for (Element element2 : element.getChildren()) {
            if (!element2.getAttributeValue("key").equals(this.blockParam.key)) continue;
            this.formulaDependentOn = element2.getAttributeValue("dependentOn");
            this.formulaValues = new ArrayList();
            String string = element2.getAttributeValue("probability");
            this.formulaProbability = string == null ? 0.5 : (double)Integer.parseInt(string) / 100.0;
            this.formulaCummulativeWeight = 0;
            for (Element element3 : element2.getChildren()) {
                String string2;
                if (!element3.getName().contains("Value") || (string2 = element3.getAttributeValue("use")) != null && string2.equals("false")) continue;
                FormulaValue formulaValue = new FormulaValue(this.replacementsConfig, element3, this.blocksConfig, this.replacementConfig);
                if (formulaValue.isNoneValue) {
                    this.formulaNoneValue = formulaValue;
                    continue;
                }
                this.formulaCummulativeWeight += formulaValue.weight;
                this.formulaValues.add(formulaValue);
            }
        }
    }

    public void setDefaultValue(String string) {
        this.blockParam.setDefaultValue(string);
    }

    public void addIntParam(Element element, IRandomGenerator iRandomGenerator, ReplacementChartConfig replacementChartConfig, int n, ItemRandomValueRanges itemRandomValueRanges) throws GenerateException {
        Element element2 = new Element("Param");
        element2.setAttribute("key", this.blockParam.key);
        element2.setAttribute("controlType", this.blockParam.controlType);
        element2.setAttribute("type", this.blockParam.type);
        if (this.blockParam.exitMethod != null) {
            element2.setAttribute("exitMethod", this.blockParam.exitMethod);
        }
        if (this.blockParam.exitMethodType != null) {
            element2.setAttribute("exitMethodType", this.blockParam.exitMethodType);
        }
        try {
            if (this.generation == 1) {
                if (this.blockParam.couldBeVariable) {
                    if (this.replacementConfig.buildSettings.containsKey(this.blockParam.defaultValue)) {
                        element2.setAttribute("variable", "true");
                        element2.setAttribute("variableType", "INT");
                        if (n != -1) {
                            element2.addContent(Integer.toString(n));
                        } else {
                            element2.addContent(this.replacementConfig.buildSettings.getString(this.blockParam.defaultValue));
                        }
                    }
                } else {
                    int n2 = n != -1 ? n : this.blockParam.iDefaultValue;
                    element2.addContent(Integer.toString(n2));
                }
            } else {
                int n3 = n != -1 ? n : this.getIntParam(iRandomGenerator, replacementChartConfig, itemRandomValueRanges);
                element2.addContent(Integer.toString(n3));
            }
            element.addContent((Content)element2);
        }
        catch (IllegalArgumentException illegalArgumentException) {
            if (illegalArgumentException.getMessage().contains("n must be positive")) {
                Log.error("Exception generating parameter for {}.{}", (Object)element.getAttributeValue("key"), (Object)this.blockParam.key);
            }
            throw illegalArgumentException;
        }
    }

    public int getIntParam(IRandomGenerator iRandomGenerator, ReplacementChartConfig replacementChartConfig, ItemRandomValueRanges itemRandomValueRanges) throws GenerateException {
        int n;
        String string;
        boolean bl = false;
        if (this.blockParam.key.contains("ExitAfterBars") && (string = this.blockParam.getParamAttribute("probability")) != null && !string.equals("100") && iRandomGenerator.nextInt(2) == 0) {
            bl = true;
        }
        if (bl) {
            n = 0;
        } else if (this.blockParam.controlType.equals("combo")) {
            string = this.blockParam.values;
            String[] stringArray = string.split(",");
            int n2 = iRandomGenerator.nextInt(stringArray.length);
            String string2 = stringArray[n2];
            String[] stringArray2 = string2.split("=");
            n = Integer.parseInt(stringArray2[1]);
        } else {
            n = Integer.MAX_VALUE;
            if (itemRandomValueRanges != null) {
                n = (int)this.replacementConfig.generateValueFromRandomValue(this.blockParam.key, itemRandomValueRanges, iRandomGenerator, false);
            } else if (this.blockParam.rvConfig != null) {
                n = (int)this.blockParam.rvConfig.generateRandomValue(iRandomGenerator, false);
            }
            if (n == Integer.MAX_VALUE) {
                if (this.blockParam.controlType.equals("jspinnerVar") || this.blockParam.controlType.equals("jspinner")) {
                    if (this.blockParam.key.equals("#TimeFrom#") || this.blockParam.key.equals("#TimeTo#")) {
                        int n3 = Value.generateHH(iRandomGenerator, this.blockParam);
                        int n4 = Value.generateMM(iRandomGenerator, this.blockParam);
                        n = n3 * 100 + n4;
                    } else {
                        int n5;
                        int n6;
                        int n7 = (int)this.blockParam.minValue;
                        int n8 = (int)this.blockParam.maxValue;
                        int n9 = n7;
                        int n10 = n8;
                        if (replacementChartConfig != null) {
                            n9 = (int)this.fixValue(n7, replacementChartConfig, true);
                            n10 = (int)this.fixValue(n8, replacementChartConfig, false);
                        }
                        if ((n6 = (int)this.blockParam.step) <= 0) {
                            n6 = 1;
                        }
                        if (n10 < n9) {
                            n5 = n9;
                            n9 = n10;
                            n10 = n5;
                        }
                        if (n10 == n9) {
                            n = n10;
                        } else if (n6 == 0) {
                            n = n9;
                        } else {
                            n5 = (n10 - n9) / n6 + 1;
                            if (n5 <= 0) {
                                // empty if block
                            }
                            int n11 = iRandomGenerator.nextInt(n5);
                            n = n9 + n11 * n6;
                        }
                    }
                } else if (this.blockParam.controlType.equals("comboVar")) {
                    n = 0;
                } else {
                    throw new GenerateException("Unsupported control type '" + this.blockParam.controlType + "' when generating INT random parameter!");
                }
            }
        }
        return n;
    }

    public void addDoubleParam(Element element, IRandomGenerator iRandomGenerator, ItemRandomValueRanges itemRandomValueRanges) throws GenerateException {
        this._addDoubleParam(element, iRandomGenerator, -1.0, -1.0, itemRandomValueRanges);
    }

    private void _addDoubleParam(Element element, IRandomGenerator iRandomGenerator, double d, double d2, ItemRandomValueRanges itemRandomValueRanges) throws GenerateException {
        Element element2 = new Element("Param");
        element2.setAttribute("key", this.blockParam.key);
        element2.setAttribute("controlType", this.blockParam.controlType);
        element2.setAttribute("type", this.blockParam.type);
        if (this.blockParam.exitMethod != null) {
            element2.setAttribute("exitMethod", this.blockParam.exitMethod);
        }
        if (this.blockParam.exitMethodType != null) {
            element2.setAttribute("exitMethodType", this.blockParam.exitMethodType);
        }
        String string = this.getDoubleParam(iRandomGenerator, d, d2, itemRandomValueRanges);
        element2.addContent(string);
        element.addContent((Content)element2);
    }

    public String getDoubleParam(IRandomGenerator iRandomGenerator, double d, double d2, ItemRandomValueRanges itemRandomValueRanges) {
        String string;
        if (this.generation == 1) {
            double d3 = this.blockParam.dDefaultValue;
            int n = this.blockParam.decimals;
            n = this.replacementConfig.getDecimals(d3, n);
            string = SQUtils.d2String((double)d3, (int)n);
        } else if (this.blockParam.controlType.equals("combo")) {
            String string2 = this.blockParam.values;
            String[] stringArray = string2.split(",");
            int n = iRandomGenerator.nextInt(stringArray.length);
            String string3 = stringArray[n];
            String[] stringArray2 = string3.split("=");
            string = stringArray2[1];
        } else {
            double d4 = Double.MAX_VALUE;
            int n = this.blockParam.decimals;
            if (itemRandomValueRanges != null) {
                d4 = this.replacementConfig.generateValueFromRandomValue(this.blockParam.key, itemRandomValueRanges, iRandomGenerator, true);
                n = this.replacementConfig.getDecimals(this.blockParam.key, itemRandomValueRanges, n);
            } else if (this.blockParam.rvConfig != null) {
                d4 = this.blockParam.rvConfig.generateRandomValue(iRandomGenerator, true);
                n = this.blockParam.rvConfig.getDecimals(n);
            }
            if (d4 == Double.MAX_VALUE) {
                if (this.blockParam.controlType.equals("jspinnerVar") || this.blockParam.controlType.equals("jspinner")) {
                    double d5 = this.fixValue(this.blockParam.minValue, null, true);
                    double d6 = this.fixValue(this.blockParam.maxValue, null, false);
                    double d7 = this.blockParam.step;
                    if (d != -1.0 && d > d5) {
                        d5 = d < d6 ? d : d6;
                    }
                    if (d2 != -1.0 && d2 < d6) {
                        d6 = d2 > d5 ? d2 : d5;
                    }
                    if (d5 == d6) {
                        d4 = d6;
                    } else if (d7 == 0.0) {
                        d4 = d5;
                    } else {
                        int n2;
                        if (d5 < 0.0 && d6 < 0.0 && d7 > 0.0) {
                            d7 *= -1.0;
                        }
                        if ((n2 = (int)((d6 - d5) / d7) + 1) < 0) {
                            d5 = d5 < 0.0 ? -10000.0 : 0.0;
                            d6 = d6 > 0.0 ? 10000.0 : 0.0;
                            if (d7 < 1.0) {
                                d7 = 1.0;
                            }
                            n2 = (int)((d6 - d5) / d7) + 1;
                        }
                        int n3 = iRandomGenerator.nextInt(n2);
                        d4 = d5 + (double)n3 * d7;
                    }
                } else {
                    d4 = this.blockParam.dDefaultValue;
                }
            }
            string = SQUtils.d2String((double)d4, (int)n);
        }
        return string;
    }

    public void addBooleanParam(Element element, IRandomGenerator iRandomGenerator) throws GenerateException {
        boolean bl = false;
        if (this.generation == 1) {
            bl = this.blockParam.bDefaultValue;
        } else if (this.blockParam.controlType.equals("booleanVar")) {
            if (iRandomGenerator.nextInt(2) == 1) {
                bl = true;
            }
        } else {
            throw new GenerateException("Unsupported control type '" + this.blockParam.controlType + "' when generating BOOLEAN random parameter!");
        }
        Element element2 = new Element("Param");
        element2.setAttribute("key", this.blockParam.key);
        element2.setAttribute("controlType", this.blockParam.controlType);
        element2.setAttribute("type", this.blockParam.type);
        element2.addContent(Boolean.toString(bl));
        element.addContent((Content)element2);
    }

    public void addStringParam(Element element, IRandomGenerator iRandomGenerator) throws GenerateException {
        String string = "";
        if (this.generation == 1) {
            string = this.blockParam.defaultValue;
        } else if (!this.blockParam.controlType.equals("symbolVar") && !this.blockParam.controlType.equals("editbox")) {
            throw new GenerateException("Unsupported control type '" + this.blockParam.controlType + "' when generating STRING random parameter!");
        }
        Element element2 = new Element("Param");
        element2.setAttribute("key", this.blockParam.key);
        element2.setAttribute("controlType", this.blockParam.controlType);
        element2.setAttribute("type", this.blockParam.type);
        element2.addContent(string);
        element.addContent((Content)element2);
    }

    public void addDataParam(Element element, IRandomGenerator iRandomGenerator, ReplacementChartConfig replacementChartConfig) {
        Element element2 = new Element("Param");
        element2.setAttribute("key", this.blockParam.key);
        element2.setAttribute("controlType", this.blockParam.controlType);
        element2.setAttribute("type", this.blockParam.type);
        element2.addContent(Integer.toString(replacementChartConfig.chartIndex));
        element.addContent((Content)element2);
    }

    public void addFormulaParam(Element element, IRandomGenerator iRandomGenerator, ArrayList<ReplacementParameter> arrayList, ReplacementChartConfig replacementChartConfig, int n, double[] dArray, int n2) throws GenerateException {
        Element element2;
        Element element3 = new Element("Param");
        element3.setAttribute("key", this.blockParam.key);
        element3.setAttribute("controlType", this.blockParam.controlType);
        element3.setAttribute("type", this.blockParam.type);
        if (this.blockParam.exitMethod != null) {
            element3.setAttribute("exitMethod", this.blockParam.exitMethod);
        }
        if (this.blockParam.exitMethodType != null) {
            element3.setAttribute("exitMethodType", this.blockParam.exitMethodType);
        }
        if (this.formulaValues == null || this.formulaValues.size() == 0) {
            if (this.formulaNoneValue == null) {
                throw new GenerateException("No formula values specified for parameter '" + this.blockParam.key + "'");
            }
            element2 = new Element("Formula");
            element2.setAttribute("key", this.formulaNoneValue.key);
        } else {
            element2 = this.generateFormula(element, iRandomGenerator, arrayList, replacementChartConfig, n, dArray, n2);
        }
        element3.addContent((Content)element2);
        element.addContent((Content)element3);
    }

    private Element generateFormula(Element element, IRandomGenerator iRandomGenerator, ArrayList<ReplacementParameter> arrayList, ReplacementChartConfig replacementChartConfig, int n, double[] dArray, int n2) throws GenerateException {
        Object object;
        Element element2 = new Element("Formula");
        boolean bl = false;
        if (this.formulaDependentOn != null) {
            object = this.findDependentParam(element, this.formulaDependentOn);
            if (object == null) {
                throw new GenerateException("Dependent formula '" + this.formulaDependentOn + "' not found in for formula '" + this.blockParam.key + "'");
            }
            if (!this.dependentParamIsNone((Element)object, arrayList)) {
                bl = true;
            }
        } else {
            bl = this.formulaProbability < 1.0 ? iRandomGenerator.probability(this.formulaProbability) : true;
        }
        if (!bl) {
            if (this.formulaNoneValue == null) {
                throw new GenerateException("There is no valueNone specified for formula '" + this.blockParam.key + "'");
            }
            element2.setAttribute("key", this.formulaNoneValue.key);
            return element2;
        }
        object = this.generateFVRandomly(iRandomGenerator, dArray);
        String string = object.key;
        element2.setAttribute("key", string);
        this.generateFormulaParameters((FormulaValue)object, element2, iRandomGenerator, replacementChartConfig, n, dArray, n2);
        return element2;
    }

    private void generateFormulaParameters(FormulaValue formulaValue, Element element, IRandomGenerator iRandomGenerator, ReplacementChartConfig replacementChartConfig, int n, double[] dArray, int n2) throws GenerateException {
        if (formulaValue.parameters == null || formulaValue.parameters.size() == 0) {
            return;
        }
        ReplacementParameters replacementParameters = formulaValue.parameters.chooseRandomly(iRandomGenerator, replacementChartConfig, null);
        block16: for (ReplacementParameter replacementParameter : replacementParameters.parameters) {
            if (replacementParameter.generation == 3) continue;
            switch (replacementParameter.blockParam.type) {
                case "value": {
                    if (replacementParameter.blockParam.valueType != null && replacementParameter.blockParam.valueType.equals("price")) {
                        this.addFormulaPriceParam(replacementParameter, element, iRandomGenerator, n, 75, n2);
                        continue block16;
                    }
                    this.addFormulaPriceParam(replacementParameter, element, iRandomGenerator, n, 50, n2);
                    continue block16;
                }
                case "int": {
                    this.addIntParamSpecial(element, iRandomGenerator, replacementParameter, replacementChartConfig, formulaValue, dArray);
                    continue block16;
                }
                case "double": {
                    this.addDoubleParamSpecial(element, iRandomGenerator, replacementParameter, formulaValue, dArray);
                    continue block16;
                }
                case "string": {
                    replacementParameter.addStringParam(element, iRandomGenerator);
                    continue block16;
                }
                case "boolean": {
                    replacementParameter.addBooleanParam(element, iRandomGenerator);
                    continue block16;
                }
                case "data": {
                    replacementParameter.addDataParam(element, iRandomGenerator, replacementChartConfig);
                    continue block16;
                }
            }
            Log.error("Adding parameter of unknown type: " + replacementParameter.blockParam.type);
        }
    }

    public void addIntParamSpecial(Element element, IRandomGenerator iRandomGenerator, ReplacementParameter replacementParameter, ReplacementChartConfig replacementChartConfig, FormulaValue formulaValue, double[] dArray) throws GenerateException {
        if (dArray == null || formulaValue.exitBasedType != dArray[0]) {
            replacementParameter.addIntParam(element, iRandomGenerator, replacementChartConfig, -1, null);
            return;
        }
        if (this.LimitSLPTRRR && this.blockParam.key.contains("StopLoss")) {
            replacementParameter.addIntParam(element, iRandomGenerator, replacementChartConfig, (int)dArray[2], null);
        } else {
            replacementParameter.addIntParam(element, iRandomGenerator, replacementChartConfig, -1, null);
        }
    }

    private void addDoubleParamSpecial(Element element, IRandomGenerator iRandomGenerator, ReplacementParameter replacementParameter, FormulaValue formulaValue, double[] dArray) throws GenerateException {
        if (dArray == null || formulaValue.exitBasedType != dArray[0]) {
            replacementParameter.addDoubleParam(element, iRandomGenerator, null);
            return;
        }
        double d = -1.0;
        double d2 = -1.0;
        if (this.LimitSLPTRRR && this.blockParam.key.contains("StopLoss")) {
            d = SQUtils.round2((double)(dArray[1] * this.LimitSLPTRRRToCoef));
            d2 = SQUtils.round2((double)(dArray[1] * this.LimitSLPTRRRFromCoef));
        } else if (this.blockParam.key.contains("MoveSL2BE") || this.blockParam.key.contains("TrailingStop")) {
            d = -1.0;
            d2 = 0.75 * dArray[1];
        }
        replacementParameter._addDoubleParam(element, iRandomGenerator, d, d2, null);
    }

    private void addFormulaValueParam(ReplacementParameter replacementParameter, Element element, IRandomGenerator iRandomGenerator) throws GenerateException {
        throw new GenerateException("Not implemented yet - addFormulaValueParam for " + replacementParameter.blockDef.key + "." + replacementParameter.blockParam.key);
    }

    private void addFormulaPriceParam(ReplacementParameter replacementParameter, Element element, IRandomGenerator iRandomGenerator, int n, int n2, int n3) throws GenerateException {
        boolean bl;
        Element element2 = new Element("Block");
        element2.setAttribute("key", "#Value#");
        element2.setAttribute("name", "Value");
        element2.setAttribute("type", "value");
        element2.setAttribute("controlType", "value");
        element.addContent((Content)element2);
        boolean bl2 = false;
        Element element3 = this.replacementConfig.generateSpecialBlock(iRandomGenerator, 2, 0, n, n3, null);
        String string = element3.getAttributeValue("key");
        if (string.startsWith("CBlock") || !this.replacementConfig.checkPriceRangeBlockExists()) {
            bl = false;
        } else {
            boolean bl3 = bl = iRandomGenerator.nextInt(100) < n2;
            if (bl) {
                boolean bl4 = bl2 = iRandomGenerator.nextInt(3) == 0;
            }
        }
        if (bl) {
            Element element4 = new Element("Item");
            element4.setAttribute("key", bl2 ? "Minus" : "Plus");
            element4.setAttribute("returnType", "pricenumber");
            element4.setAttribute("categoryType", "other");
            element2.addContent((Content)element4);
            Element element5 = new Element("Block");
            element5.setAttribute("key", "#Left#");
            element4.addContent((Content)element5);
            Element element6 = element3;
            element5.addContent((Content)element6);
            Element element7 = new Element("Block");
            element7.setAttribute("key", "#Right#");
            element4.addContent((Content)element7);
            Element element8 = new Element("Item");
            element8.setAttribute("key", "Multiplication");
            element8.setAttribute("returnType", "pricenumber");
            element8.setAttribute("categoryType", "other");
            element7.addContent((Content)element8);
            Element element9 = new Element("Block");
            element9.setAttribute("key", "#Left#");
            element8.addContent((Content)element9);
            Element element10 = new Element("Item");
            element10.setAttribute("key", "Number");
            element10.setAttribute("returnType", "number");
            element10.setAttribute("categoryType", "other");
            element9.addContent((Content)element10);
            Element element11 = new Element("Param");
            element11.setAttribute("key", "#Number#");
            element11.addContent(this.generateAtrNumber(iRandomGenerator));
            element10.addContent((Content)element11);
            Element element12 = new Element("Block");
            element12.setAttribute("key", "#Right#");
            element8.addContent((Content)element12);
            Element element13 = this.replacementConfig.generateSpecialBlock(iRandomGenerator, 7, 0, n, n3, null);
            element12.addContent((Content)element13);
        } else {
            element2.addContent((Content)element3);
        }
    }

    private String generateAtrNumber(IRandomGenerator iRandomGenerator) {
        double d = 0.1;
        double d2 = 3.0;
        double d3 = 0.1;
        int n = (int)((d2 - d) / d3) + 1;
        int n2 = iRandomGenerator.nextInt(n);
        double d4 = d + (double)n2 * d3;
        return SQUtils.d2((double)d4);
    }

    private boolean dependentParamIsNone(Element element, ArrayList<ReplacementParameter> arrayList) throws GenerateException {
        String string = element.getAttributeValue("key");
        for (ReplacementParameter replacementParameter : arrayList) {
            if (!replacementParameter.blockParam.key.equals(string)) continue;
            String string2 = element.getChild("Formula").getAttributeValue("key");
            if (replacementParameter.formulaNoneValue == null) {
                throw new GenerateException("Dependent formula '" + string + "' doesn't have ValueNone set!");
            }
            if (!replacementParameter.formulaNoneValue.key.equals(string2)) continue;
            return true;
        }
        return false;
    }

    private Element findDependentParam(Element element, String string) {
        for (Element element2 : element.getChildren()) {
            if (!element2.getAttributeValue("key").equals(string)) continue;
            return element2;
        }
        return null;
    }

    private FormulaValue generateFVRandomly(IRandomGenerator iRandomGenerator, double[] dArray) throws GenerateException {
        int n;
        if (this.formulaValues.size() == 1) {
            return this.formulaValues.get(0);
        }
        if (dArray != null && this.LimitSLPTRRR) {
            for (n = 0; n < this.formulaValues.size(); ++n) {
                FormulaValue formulaValue = this.formulaValues.get(n);
                if (dArray[0] != formulaValue.exitBasedType) continue;
                return formulaValue;
            }
        }
        n = iRandomGenerator.nextInt(this.formulaCummulativeWeight);
        int n2 = 0;
        for (int i = 0; i < this.formulaValues.size(); ++i) {
            FormulaValue formulaValue = this.formulaValues.get(i);
            if (n >= (n2 += formulaValue.weight)) continue;
            return formulaValue;
        }
        throw new GenerateException("No Formula Value found for '" + this.blockParam.key + "', this shouldn't happen!");
    }

    public boolean formulaHasValues() {
        return this.formulaValues != null && this.formulaValues.size() != 0;
    }

    public static ReplacementParameter createCDataIndyShiftParam(BlockDefinition blockDefinition, ReplacementsConfig replacementsConfig, ReplacementConfig replacementConfig) {
        ReplacementParameter replacementParameter = new ReplacementParameter();
        replacementParameter.blockDef = blockDefinition;
        replacementParameter.generation = (byte)2;
        replacementParameter.replacementConfig = replacementConfig;
        replacementParameter.replacementsConfig = replacementsConfig;
        replacementParameter.blockParam = new BlockParameter(BlockSettingsConverter.createCDataShiftParamElement());
        return replacementParameter;
    }

    public static ReplacementParameter createCDataIndyValueParam(int n, BlockDefinition blockDefinition, ReplacementsConfig replacementsConfig, ReplacementConfig replacementConfig, CustomDataInfo customDataInfo) throws GenerateException {
        ReplacementParameter replacementParameter = new ReplacementParameter();
        replacementParameter.blockDef = blockDefinition;
        replacementParameter.generation = (byte)2;
        replacementParameter.replacementConfig = replacementConfig;
        replacementParameter.replacementsConfig = replacementsConfig;
        replacementParameter.blockParam = new BlockParameter(BlockSettingsConverter.createCDataValueParamElement(n, customDataInfo));
        return replacementParameter;
    }

    public boolean verifyParam(String string, Element element) throws GenerateException {
        String string2 = element.getAttributeValue("type");
        if (string2.equals("double")) {
            return this.verifyDoubleParam(string, element);
        }
        if (string2.equals("int")) {
            return this.verifyIntParam(string, element);
        }
        return true;
    }

    private boolean verifyIntParam(String string, Element element) throws GenerateException {
        int n;
        if (string.equals("#MagicNumber#")) {
            return true;
        }
        if (string.contains(".")) {
            return true;
        }
        String string2 = element.getText();
        if (string2 == null || string2.isEmpty()) {
            return true;
        }
        try {
            n = Integer.parseInt(string2);
        }
        catch (Exception exception) {
            Log.info("Cannot convert parameter '" + string + "' to int, value = '" + string2 + "'!");
            return true;
        }
        if (this.blockParam.key.contains("ExitAfterBars")) {
            return true;
        }
        if (this.generation == 1) {
            if (n == this.blockParam.iDefaultValue) {
                return true;
            }
            Log.info("Ver false 1 - {} - val: {} != {}", new Object[]{string, n, this.blockParam.iDefaultValue});
            return false;
        }
        if (this.blockParam.controlType.equals("combo")) {
            String string3 = this.blockParam.values;
            String[] stringArray = string3.split(",");
            return this.isInSubparts(n, stringArray);
        }
        if (this.blockParam.controlType.equals("jspinnerVar")) {
            if (this.blockParam.key.equals("#TimeFrom#") || this.blockParam.key.equals("#TimeTo#")) {
                return true;
            }
            int n2 = (int)this.blockParam.minValue;
            int n3 = (int)this.blockParam.maxValue;
            int n4 = n2;
            int n5 = n3;
            if (this.isConstantValue(n4)) {
                return true;
            }
            int n6 = (int)this.blockParam.step;
            if (n5 < n4) {
                int n7 = n4;
                n4 = n5;
                n5 = n7;
            }
            if (n5 == n4) {
                if (n == n5) {
                    return true;
                }
                Log.info("Ver false 2 - {} - val: {}, {} <> {}", new Object[]{string, n, n4, n5});
                return false;
            }
            if (n6 == 0) {
                if (n == n4) {
                    return true;
                }
                Log.info("Ver false 3 - {} - val: {}, {} <> {}", new Object[]{string, n, n4, n5});
                return false;
            }
            if (n >= n4 && n <= n5) {
                return true;
            }
            Log.info("Ver false 4 - {} - val: {}, {} <> {}", new Object[]{string, n, n4, n5});
            return false;
        }
        if (this.blockParam.controlType.equals("comboVar")) {
            return true;
        }
        throw new GenerateException("Unsupported control type '" + this.blockParam.controlType + "' when generating INT random parameter!");
    }

    private boolean isInSubparts(int n, String[] stringArray) {
        if (stringArray == null) {
            return true;
        }
        for (int i = 0; i < stringArray.length; ++i) {
            String[] stringArray2 = stringArray[i].split("=");
            int n2 = Integer.parseInt(stringArray2[1]);
            if (n != n2) continue;
            return true;
        }
        return false;
    }

    private boolean verifyDoubleParam(String string, Element element) {
        double d;
        if (string.contains(".")) {
            return true;
        }
        String string2 = element.getText();
        if (string2 == null || string2.isEmpty()) {
            return true;
        }
        try {
            d = Double.parseDouble(string2);
        }
        catch (Exception exception) {
            Log.info("Cannot convert parameter '" + string + "' to int, value = '" + string2 + "'!");
            return true;
        }
        if (this.generation == 1) {
            return d == (double)this.blockParam.iDefaultValue;
        }
        if (this.blockParam.controlType.equals("combo")) {
            String string3 = this.blockParam.values;
            String[] stringArray = string3.split(",");
            return this.isInSubparts((int)d, stringArray);
        }
        if (this.blockParam.controlType.equals("jspinnerVar") || this.blockParam.controlType.equals("jspinner")) {
            double d2 = this.fixValue(this.blockParam.minValue, null, true);
            double d3 = this.fixValue(this.blockParam.maxValue, null, false);
            double d4 = this.blockParam.step;
            if (d2 == d3) {
                return d == d3;
            }
            if (d4 == 0.0) {
                return d == d2;
            }
            return d >= d2 && d <= d3;
        }
        return d == this.blockParam.dDefaultValue;
    }
}

