/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  org.jdom2.Element
 *  org.slf4j.Logger
 *  org.slf4j.LoggerFactory
 */
package com.strategyquant.tradinglib.blocks.random;

import com.strategyquant.tradinglib.generator.GenerateException;
import org.jdom2.Element;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

public class ReplacementChartConfig {
    public static final Logger Log = LoggerFactory.getLogger((String)"ReplacementChartConfig");
    public int minConditions;
    public int maxConditions;
    public int minExitConditions;
    public int maxExitConditions;
    public int minExitTypes;
    public int maxExitTypes;
    public int minShift;
    public int maxShift;
    public int minPeriod;
    public int maxPeriod;
    public int chartIndex;
    private int conditionsToGenerate;
    private int exitConditionsToGenerate;

    public ReplacementChartConfig(int n, Element element, double d) throws GenerateException {
        this.chartIndex = this.loadIntAttribute(element, "chartIndex", n);
        this.minConditions = this.loadIntAttribute(element, "minConditions", 0);
        this.maxConditions = this.loadIntAttribute(element, "maxConditions", 0);
        if (this.minConditions != 0 && this.maxConditions != 0 && this.minConditions > this.maxConditions) {
            this.maxConditions = this.minConditions;
        }
        this.minExitConditions = this.loadIntAttribute(element, "minExitConditions", 0);
        this.maxExitConditions = this.loadIntAttribute(element, "maxExitConditions", 0);
        if (this.minExitConditions != 0 && this.maxExitConditions != 0 && this.minExitConditions > this.maxExitConditions) {
            this.maxExitConditions = this.minExitConditions;
        }
        if (this.minExitConditions == 0 && d == 1.0 && this.minExitConditions > 0 && this.maxExitConditions == 0) {
            this.maxExitConditions = 1;
        }
        this.minShift = this.loadIntAttribute(element, "minShift", -1);
        this.maxShift = this.loadIntAttribute(element, "maxShift", -1);
        if (this.minShift >= 0 && this.maxShift >= 0 && this.minShift > this.maxShift) {
            this.minShift = this.maxShift;
        }
        this.minPeriod = this.loadIntAttribute(element, "minPeriod", -1);
        this.maxPeriod = this.loadIntAttribute(element, "maxPeriod", -1);
        if (this.minPeriod >= 0 && this.maxPeriod >= 0 && this.minPeriod > this.maxPeriod) {
            this.maxPeriod = this.minPeriod;
        }
        this.minExitTypes = this.loadIntAttribute(element, "minExitTypes", 1);
        this.maxExitTypes = this.loadIntAttribute(element, "maxExitTypes", 5);
        if (this.minExitTypes != 0 && this.maxExitTypes != 0 && this.minExitTypes > this.maxExitTypes) {
            this.maxExitTypes = this.minExitTypes;
        }
    }

    private int loadIntAttribute(Element element, String string, int n) throws GenerateException {
        String string2 = element.getAttributeValue(string);
        if (n < 0 && string2 == null) {
            throw new GenerateException("Attribute '" + string + "' must be set!");
        }
        return string2 != null ? Integer.parseInt(string2) : n;
    }

    public void setConditionsToGenerate(int n, int n2) {
        if (n == 2) {
            this.exitConditionsToGenerate = n2;
            if (this.exitConditionsToGenerate < this.minExitConditions) {
                this.exitConditionsToGenerate = this.minExitConditions;
            }
            if (this.exitConditionsToGenerate > this.maxExitConditions) {
                this.exitConditionsToGenerate = this.maxExitConditions;
            }
        } else {
            this.conditionsToGenerate = n2;
            if (this.conditionsToGenerate < this.minConditions) {
                this.conditionsToGenerate = this.minConditions;
            }
            if (this.conditionsToGenerate > this.maxConditions) {
                this.conditionsToGenerate = this.maxConditions;
            }
        }
    }

    public int getConditionsToGenerate(int n) {
        if (n == 2) {
            return this.exitConditionsToGenerate;
        }
        return this.conditionsToGenerate;
    }

    public void decreaseConditionsToGenerate(int n) {
        if (n == 2) {
            --this.exitConditionsToGenerate;
        } else {
            --this.conditionsToGenerate;
        }
    }
}

