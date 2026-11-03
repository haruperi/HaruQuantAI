/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  org.jdom2.Element
 *  org.slf4j.Logger
 *  org.slf4j.LoggerFactory
 */
package com.strategyquant.tradinglib.blocks.random;

import com.strategyquant.tradinglib.blocks.annotations.Value;
import com.strategyquant.tradinglib.blocks.random.RandomValueConfig;
import java.io.Serializable;
import java.math.BigDecimal;
import org.jdom2.Element;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

public class BlockParameter
implements Serializable {
    public static final Logger Log = LoggerFactory.getLogger((String)"BlockParameter");
    public String key;
    public String defaultValue;
    public String type;
    public String controlType;
    private Element elParam;
    public double minValue;
    public double maxValue;
    public int decimals;
    public double step;
    public String values;
    public int iDefaultValue;
    public double dDefaultValue;
    public boolean bDefaultValue;
    boolean couldBeVariable = false;
    public String valueType = null;
    public String exitMethod = null;
    public String exitMethodType = null;
    public boolean customRangesSet;
    public RandomValueConfig rvConfig = null;
    public String paramType = null;

    public BlockParameter(Element element) {
        this.elParam = element;
        this.key = element.getAttributeValue("key");
        this.type = element.getAttributeValue("type");
        this.controlType = element.getAttributeValue("controlType");
        this.valueType = element.getAttributeValue("valueType");
        this.paramType = element.getAttributeValue("paramType");
        this.initializeRanges(false, null);
        this.recognizeDecimals();
        this.exitMethod = element.getAttributeValue("exitMethod");
        this.exitMethodType = element.getAttributeValue("exitMethodType");
        this.values = this.getStringAttribute("values", null);
        this.setDefaultValue(element.getAttributeValue("defaultValue"));
    }

    public void initializeRanges(boolean bl, String string) {
        String string2;
        this.minValue = this.getDoubleAttribute("minValue", -1.0);
        this.maxValue = this.getDoubleAttribute("maxValue", -1.0);
        this.step = this.getDoubleAttribute("step", -1.0);
        if (string == null || !string.contains("SQ.Formulas.SLPT")) {
            double d;
            double d2;
            if (!bl || Value.isPredefined(this.minValue)) {
                d2 = this.getDoubleAttribute("builderMinValue", -9999999.0);
                if (d2 != -9999999.0 && d2 > this.minValue) {
                    this.minValue = d2;
                }
                if ((d = this.getDoubleAttribute("genMinValue", -9999999.0)) != -9999999.0 && (d > this.minValue || Value.isPredefined(d))) {
                    this.minValue = d;
                }
            }
            if (!bl || Value.isPredefined(this.maxValue)) {
                d2 = this.getDoubleAttribute("builderMaxValue", -9999999.0);
                if (d2 != -9999999.0 && d2 < this.maxValue) {
                    this.maxValue = d2;
                }
                if ((d = this.getDoubleAttribute("genMaxValue", -9999999.0)) != -9999999.0 && (d < this.maxValue || Value.isPredefined(d))) {
                    this.maxValue = d;
                }
            }
            if (!bl || Value.isPredefined(this.minValue) && Value.isPredefined(this.maxValue)) {
                this.step = d2 = this.getDoubleAttribute("builderStep", -9999999.0);
                d = this.getDoubleAttribute("genStep", -9999999.0);
                if (d != -9999999.0) {
                    this.step = d;
                }
            }
        }
        if ((string2 = this.elParam.getAttributeValue("randomValue")) != null && !string2.equals("") && !string2.equals("default")) {
            this.rvConfig = RandomValueConfig.parseRandomValue(string2, false);
        }
        this.customRangesSet = false;
        if (this.key.startsWith("#Period") && (this.minValue != -1000003.0 || this.maxValue != -1000004.0)) {
            this.customRangesSet = true;
        }
    }

    public void recognizeDecimals() {
        if (this.minValue == 0.0) {
            this.decimals = 2;
        }
        double d = Math.min(this.minValue, this.step);
        BigDecimal bigDecimal = BigDecimal.valueOf(d);
        this.decimals = bigDecimal.scale();
        if (this.decimals > 6) {
            this.decimals = 6;
        }
    }

    private double getDoubleAttribute(String string, double d) {
        String string2 = this.elParam.getAttributeValue(string);
        if (string2 == null || string2.isBlank()) {
            return d;
        }
        return Double.parseDouble(string2);
    }

    private String getStringAttribute(String string, String string2) {
        String string3 = this.elParam.getAttributeValue(string);
        if (string3 == null) {
            return string2;
        }
        return string3;
    }

    public boolean isValueParameter() {
        return this.type.equals("value");
    }

    public BlockParameter clone() {
        BlockParameter blockParameter = new BlockParameter(this.elParam.clone());
        return blockParameter;
    }

    public void setDefaultValue(String string) {
        this.defaultValue = string;
        if (this.defaultValue != null) {
            try {
                switch (this.type) {
                    case "int": {
                        this.iDefaultValue = Integer.parseInt(this.defaultValue);
                        break;
                    }
                    case "double": {
                        this.dDefaultValue = Double.parseDouble(this.defaultValue);
                        break;
                    }
                    case "boolean": {
                        this.bDefaultValue = Boolean.parseBoolean(this.defaultValue);
                    }
                }
            }
            catch (NumberFormatException numberFormatException) {
                this.couldBeVariable = true;
            }
        }
    }

    public void setParamAttribute(String string, String string2) {
        this.elParam.setAttribute(string, string2);
        switch (string) {
            case "type": {
                this.type = this.elParam.getAttributeValue("type");
                break;
            }
            case "controlType": {
                this.controlType = this.elParam.getAttributeValue("controlType");
                break;
            }
            case "minValue": {
                this.minValue = this.getDoubleAttribute("minValue", -1.0);
                break;
            }
            case "maxValue": {
                this.maxValue = this.getDoubleAttribute("maxValue", -1.0);
                break;
            }
            case "step": {
                this.step = this.getDoubleAttribute("step", -1.0);
                break;
            }
            case "builderMinValue": {
                double d = this.getDoubleAttribute("builderMinValue", -9999999.0);
                if (d == -9999999.0 || !(d > this.minValue) || !this.notPreset(this.minValue)) break;
                this.minValue = d;
                break;
            }
            case "builderMaxValue": {
                double d = this.getDoubleAttribute("builderMaxValue", -9999999.0);
                if (d == -9999999.0 || !(d < this.maxValue) || !this.notPreset(this.minValue)) break;
                this.maxValue = d;
                break;
            }
            case "builderStep": {
                double d = this.getDoubleAttribute("builderStep", -9999999.0);
                if (d == -9999999.0) break;
                this.step = d;
                break;
            }
            case "values": {
                this.values = this.getStringAttribute("values", null);
                break;
            }
            case "defaultValue": {
                this.setDefaultValue(this.elParam.getAttributeValue("defaultValue"));
            }
        }
    }

    private boolean notPreset(double d) {
        return d <= -1000001.0 && d >= 1000056.0;
    }

    public String getParamAttribute(String string) {
        return this.elParam.getAttributeValue(string);
    }

    public Element getParamElement() {
        return this.elParam.clone();
    }
}

