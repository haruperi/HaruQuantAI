/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  com.strategyquant.lib.IRandomGenerator
 *  com.strategyquant.lib.XMLUtil
 *  org.jdom2.Content
 *  org.jdom2.Element
 */
package com.strategyquant.tradinglib.atm;

import com.strategyquant.lib.IRandomGenerator;
import com.strategyquant.lib.XMLUtil;
import com.strategyquant.tradinglib.atm.exits.FixedProfit;
import com.strategyquant.tradinglib.atm.exits.MultipleOfOriginalPT;
import com.strategyquant.tradinglib.atm.exits.MultipleOfOriginalSL;
import com.strategyquant.tradinglib.atm.exits.None;
import com.strategyquant.tradinglib.atm.exits.TrailingStop;
import com.strategyquant.tradinglib.generator.GenerateException;
import com.strategyquant.tradinglib.task.settings.TaskSettingsData;
import java.io.Serializable;
import org.jdom2.Content;
import org.jdom2.Element;

public class ATMGenerateConfig
implements Serializable {
    private static final int Scenario2exits_5050 = 100;
    private static final int Scenario2exits_3366 = 101;
    private static final int Scenario2exits_6633 = 102;
    private static final int Scenario3exits_333333 = 200;
    private static final int Scenario3exits_502525 = 201;
    private static final int Scenario3exits_255025 = 202;
    private static final int Scenario3exits_252550 = 203;
    public boolean useSLMultiple;
    public double slMultipleMin = 1.0;
    public double slMultipleMax = 1.0;
    public boolean usePTMultiple;
    public double ptMultipleMin = 1.0;
    public double ptMultipleMax = 1.0;
    public boolean useFixedProfit;
    public boolean useFixedProfitFixedPips;
    public int fixedProfitFixedPipsMin = 30;
    public int fixedProfitFixedPipsMax = 80;
    public boolean useFixedProfitATR;
    public double fixedProfitATRMutliplierMin = 1.0;
    public double fixedProfitATRMutliplierMax = 1.0;
    public int fixedProfitATRPeriodMin = 20;
    public int fixedProfitATRPeriodMax = 20;
    public boolean useTS;
    public boolean useTSFixedPips;
    public int tsFixedPipsMin = 30;
    public int tsFixedPipsMax = 80;
    public boolean useTSATR;
    public double tsATRMutliplierMin = 1.0;
    public double tsATRMutliplierMax = 1.0;
    public int tsATRPeriodMin = 30;
    public int tsATRPeriodMax = 80;
    public boolean useNone;
    public boolean useNoneLimit;
    public int noneMinBars = 50;
    public int noneMaxBars = 50;
    public boolean scenario_2exits_5050 = false;
    public boolean scenario_2exits_3366 = false;
    public boolean scenario_2exits_6633 = false;
    public boolean scenario_3exits_333333 = false;
    public boolean scenario_3exits_502525 = false;
    public boolean scenario_3exits_255025 = false;
    public boolean scenario_3exits_252550 = false;
    private int configHash;
    private int sizeDecimals;
    private double minimalSize;
    private int totalEnabledScenarios;
    private Element elMoveSL2BE;
    private int totalEnabledExits;

    public void init(Element element, int n, double d) throws Exception {
        if (element == null) {
            return;
        }
        this.sizeDecimals = n;
        this.minimalSize = d;
        String string = XMLUtil.xmlToStringRaw((Element)element);
        this.configHash = string.hashCode() + Integer.hashCode(n) + Double.hashCode(d);
        Element element2 = XMLUtil.getChildElem((Element)element, (String)"Types");
        Element element3 = XMLUtil.getChildElem((Element)element2, (String)"SLMultiple");
        this.useSLMultiple = XMLUtil.getBooleanAttr((Element)element3, (String)"use", (boolean)false);
        this.slMultipleMin = XMLUtil.getDoubleAttr((Element)element3, (String)"minMultiplier", (double)1.0);
        this.slMultipleMax = XMLUtil.getDoubleAttr((Element)element3, (String)"maxMultiplier", (double)1.0);
        Element element4 = XMLUtil.getChildElem((Element)element2, (String)"PTMultiple");
        this.usePTMultiple = XMLUtil.getBooleanAttr((Element)element4, (String)"use", (boolean)false);
        this.ptMultipleMin = XMLUtil.getDoubleAttr((Element)element4, (String)"minMultiplier", (double)1.0);
        this.ptMultipleMax = XMLUtil.getDoubleAttr((Element)element4, (String)"maxMultiplier", (double)1.0);
        Element element5 = XMLUtil.getChildElem((Element)element2, (String)"FixedProfit");
        this.useFixedProfit = XMLUtil.getBooleanAttr((Element)element5, (String)"use", (boolean)false);
        this.useFixedProfitFixedPips = XMLUtil.getBooleanAttr((Element)element5, (String)"useFixedPips", (boolean)false);
        this.fixedProfitFixedPipsMin = XMLUtil.getIntAttr((Element)element5, (String)"minPips", (int)30);
        this.fixedProfitFixedPipsMax = XMLUtil.getIntAttr((Element)element5, (String)"maxPips", (int)80);
        this.useFixedProfitATR = XMLUtil.getBooleanAttr((Element)element5, (String)"useATR", (boolean)false);
        this.fixedProfitATRMutliplierMin = XMLUtil.getDoubleAttr((Element)element5, (String)"minMultiplier", (double)1.5);
        this.fixedProfitATRMutliplierMax = XMLUtil.getDoubleAttr((Element)element5, (String)"maxMultiplier", (double)1.5);
        this.fixedProfitATRPeriodMin = XMLUtil.getIntAttr((Element)element5, (String)"minATRPeriod", (int)20);
        this.fixedProfitATRPeriodMax = XMLUtil.getIntAttr((Element)element5, (String)"maxATRPeriod", (int)20);
        Element element6 = XMLUtil.getChildElem((Element)element2, (String)"TrailingStop");
        this.useTS = XMLUtil.getBooleanAttr((Element)element6, (String)"use", (boolean)false);
        this.useTSFixedPips = XMLUtil.getBooleanAttr((Element)element6, (String)"useFixedPips", (boolean)false);
        this.tsFixedPipsMin = XMLUtil.getIntAttr((Element)element6, (String)"minPips", (int)30);
        this.tsFixedPipsMax = XMLUtil.getIntAttr((Element)element6, (String)"maxPips", (int)80);
        this.useTSATR = XMLUtil.getBooleanAttr((Element)element6, (String)"useATR", (boolean)false);
        this.tsATRMutliplierMin = XMLUtil.getDoubleAttr((Element)element6, (String)"minMultiplier", (double)1.5);
        this.tsATRMutliplierMax = XMLUtil.getDoubleAttr((Element)element6, (String)"maxMultiplier", (double)1.5);
        this.tsATRPeriodMin = XMLUtil.getIntAttr((Element)element6, (String)"minATRPeriod", (int)20);
        this.tsATRPeriodMax = XMLUtil.getIntAttr((Element)element6, (String)"maxATRPeriod", (int)20);
        Element element7 = XMLUtil.getChildElem((Element)element2, (String)"None");
        this.useNoneLimit = XMLUtil.getBooleanAttr((Element)element7, (String)"useLimit", (boolean)false);
        this.noneMinBars = XMLUtil.getIntAttr((Element)element7, (String)"minBars", (int)50);
        this.noneMaxBars = XMLUtil.getIntAttr((Element)element7, (String)"maxBars", (int)50);
        Element element8 = XMLUtil.getChildElem((Element)element, (String)"Scenarios");
        Element element9 = XMLUtil.getChildElem((Element)element8, (String)"TwoExits");
        this.scenario_2exits_5050 = XMLUtil.getBooleanAttr((Element)element9, (String)"exit5050", (boolean)false);
        this.scenario_2exits_3366 = XMLUtil.getBooleanAttr((Element)element9, (String)"exit3366", (boolean)false);
        this.scenario_2exits_6633 = XMLUtil.getBooleanAttr((Element)element9, (String)"exit6633", (boolean)false);
        Element element10 = XMLUtil.getChildElem((Element)element8, (String)"ThreeExits");
        this.scenario_3exits_333333 = XMLUtil.getBooleanAttr((Element)element10, (String)"exit333333", (boolean)false);
        this.scenario_3exits_502525 = XMLUtil.getBooleanAttr((Element)element10, (String)"exit502525", (boolean)false);
        this.scenario_3exits_255025 = XMLUtil.getBooleanAttr((Element)element10, (String)"exit255025", (boolean)false);
        this.scenario_3exits_252550 = XMLUtil.getBooleanAttr((Element)element10, (String)"exit252550", (boolean)false);
        this.totalEnabledExits = this.countEnabledExits();
        this.totalEnabledScenarios = this.countEnabledScenarios();
        this.elMoveSL2BE = this.generateConstantMoveSL2BE();
    }

    private int countEnabledExits() {
        int n = 0;
        if (this.useSLMultiple) {
            ++n;
        }
        if (this.usePTMultiple) {
            ++n;
        }
        if (this.useFixedProfit) {
            ++n;
        }
        if (this.useTS) {
            ++n;
        }
        if (this.useNoneLimit) {
            ++n;
        }
        return n;
    }

    private Element generateConstantMoveSL2BE() {
        Element element = new Element("MoveSL2BE");
        XMLUtil.setItemBoolParam((Element)element, (String)"MoveSL2BE", (boolean)false);
        XMLUtil.setItemBoolParam((Element)element, (String)"MoveSL2BEAddPips", (boolean)false);
        XMLUtil.setItemIntParam((Element)element, (String)"Type", (int)1);
        XMLUtil.setItemIntParam((Element)element, (String)"AddPipsValue", (int)10);
        return element;
    }

    private int countEnabledScenarios() {
        int n = 0;
        if (this.scenario_2exits_5050) {
            ++n;
        }
        if (this.scenario_2exits_3366) {
            ++n;
        }
        if (this.scenario_2exits_6633) {
            ++n;
        }
        if (this.scenario_3exits_333333) {
            ++n;
        }
        if (this.scenario_3exits_502525) {
            ++n;
        }
        if (this.scenario_3exits_255025) {
            ++n;
        }
        if (this.scenario_3exits_252550) {
            ++n;
        }
        return n;
    }

    public int getHash() {
        return this.configHash;
    }

    public Element generate(IRandomGenerator iRandomGenerator) throws GenerateException {
        Element element = new Element("ATMs");
        element.setAttribute("enable", "true");
        element.setAttribute("source", "config");
        element.setAttribute("generated", "true");
        element.setAttribute("sizeDecimals", Integer.toString(this.sizeDecimals));
        element.setAttribute("minSize", Double.toString(this.minimalSize));
        Element element2 = new Element("ATM");
        element.addContent((Content)element2);
        element2.setAttribute("id", "global");
        element2.setAttribute("sizeDecimals", Integer.toString(this.sizeDecimals));
        element2.setAttribute("minimalSize", Double.toString(this.minimalSize));
        Element element3 = new Element("Exits");
        element2.addContent((Content)element3);
        int n = this.chooseScenario(iRandomGenerator);
        for (int i = 0; i < this.getScenarioExitCount(n); ++i) {
            Element element4 = this.generateScenarioExit(i, n, iRandomGenerator);
            element3.addContent((Content)element4);
        }
        return element;
    }

    private Element generateScenarioExit(int n, int n2, IRandomGenerator iRandomGenerator) throws GenerateException {
        Element element = new Element("Exit");
        Element element2 = this.generateExitPositionSize(n, n2, iRandomGenerator);
        element.addContent((Content)element2);
        Element element3 = this.generateExitExitLevel(n, n2, iRandomGenerator);
        element.addContent((Content)element3);
        Element element4 = this.generateExitMoveSL2BE(n, n2, iRandomGenerator);
        element.addContent((Content)element4);
        return element;
    }

    private Element generateExitExitLevel(int n, int n2, IRandomGenerator iRandomGenerator) throws GenerateException {
        Element element = new Element("ExitLevels");
        String string = this.chooseExitLevel(n2, iRandomGenerator);
        Element element2 = this.generateExitLevelParams(string, iRandomGenerator);
        element.addContent((Content)element2);
        return element;
    }

    private Element generateExitLevelParams(String string, IRandomGenerator iRandomGenerator) throws GenerateException {
        switch (string) {
            case "MultipleOfOriginalSL": {
                return MultipleOfOriginalSL.generate(iRandomGenerator, this);
            }
            case "MultipleOfOriginalPT": {
                return MultipleOfOriginalPT.generate(iRandomGenerator, this);
            }
            case "FixedProfit": {
                return FixedProfit.generate(iRandomGenerator, this);
            }
            case "TrailingStop": {
                return TrailingStop.generate(iRandomGenerator, this);
            }
            case "None": {
                return None.generate(iRandomGenerator, this);
            }
        }
        throw new GenerateException("Unknown exit level type '" + string + "'");
    }

    private String chooseExitLevel(int n, IRandomGenerator iRandomGenerator) throws GenerateException {
        if (this.totalEnabledExits == 0) {
            throw new GenerateException("No ATM exit chosen!");
        }
        int n2 = 0;
        if (this.totalEnabledScenarios > 1) {
            n2 = iRandomGenerator.nextInt(this.totalEnabledExits);
        }
        int n3 = 0;
        if (this.useSLMultiple) {
            if (n2 == n3) {
                return "MultipleOfOriginalSL";
            }
            ++n3;
        }
        if (this.usePTMultiple) {
            if (n2 == n3) {
                return "MultipleOfOriginalPT";
            }
            ++n3;
        }
        if (this.useFixedProfit) {
            if (n2 == n3) {
                return "FixedProfit";
            }
            ++n3;
        }
        if (this.useTS) {
            if (n2 == n3) {
                return "TrailingStop";
            }
            ++n3;
        }
        if (this.useNoneLimit) {
            if (n2 == n3) {
                return "None";
            }
            ++n3;
        }
        throw new GenerateException("Non-existing ATM exit level chosen!");
    }

    private Element generateExitPositionSize(int n, int n2, IRandomGenerator iRandomGenerator) throws GenerateException {
        int n3;
        Element element = new Element("PositionSizes");
        Element element2 = new Element("PositionSize");
        element.addContent((Content)element2);
        element2.setAttribute("key", "SizePercents");
        element2.setAttribute("use", "true");
        switch (n2) {
            case 100: {
                n3 = 50;
                break;
            }
            case 101: {
                n3 = n == 0 ? 33 : 66;
                break;
            }
            case 102: {
                n3 = n == 0 ? 66 : 33;
                break;
            }
            case 200: {
                n3 = 33;
                break;
            }
            case 201: {
                n3 = n == 0 ? 50 : 25;
                break;
            }
            case 202: {
                n3 = n == 1 ? 50 : 25;
                break;
            }
            case 203: {
                n3 = n == 2 ? 50 : 25;
                break;
            }
            default: {
                throw new GenerateException("Cannot generate position size for non-existing ATM scenario: " + n2 + "!");
            }
        }
        XMLUtil.setItemIntParam((Element)element2, (String)"Percents", (int)n3);
        return element;
    }

    private Element generateExitMoveSL2BE(int n, int n2, IRandomGenerator iRandomGenerator) {
        return this.elMoveSL2BE.clone();
    }

    private int getScenarioExitCount(int n) throws GenerateException {
        switch (n) {
            case 100: 
            case 101: 
            case 102: {
                return 2;
            }
            case 200: 
            case 201: 
            case 202: 
            case 203: {
                return 3;
            }
        }
        throw new GenerateException("Non'existing ATM scenario chosen: " + n + "!");
    }

    private int chooseScenario(IRandomGenerator iRandomGenerator) throws GenerateException {
        if (this.totalEnabledScenarios == 0) {
            throw new GenerateException("No ATM scenario chosen!");
        }
        int n = 0;
        if (this.totalEnabledScenarios > 1) {
            n = iRandomGenerator.nextInt(this.totalEnabledScenarios);
        }
        int n2 = 0;
        if (this.scenario_2exits_5050) {
            if (n == n2) {
                return 100;
            }
            ++n2;
        }
        if (this.scenario_2exits_3366) {
            if (n == n2) {
                return 101;
            }
            ++n2;
        }
        if (this.scenario_2exits_6633) {
            if (n == n2) {
                return 102;
            }
            ++n2;
        }
        if (this.scenario_3exits_333333) {
            if (n == n2) {
                return 200;
            }
            ++n2;
        }
        if (this.scenario_3exits_502525) {
            if (n == n2) {
                return 201;
            }
            ++n2;
        }
        if (this.scenario_3exits_255025) {
            if (n == n2) {
                return 202;
            }
            ++n2;
        }
        if (this.scenario_3exits_252550) {
            if (n == n2) {
                return 203;
            }
            ++n2;
        }
        throw new GenerateException("Non-existing ATM scenario chosen!");
    }

    public void verifyConfig(TaskSettingsData taskSettingsData) {
        if (this.totalEnabledExits == 0) {
            taskSettingsData.addError("ATM settings", null, "You have no exits enabled for ATR generation!");
        }
        if (this.totalEnabledScenarios == 0) {
            taskSettingsData.addError("ATM settings", null, "You have no scenarios enabled for ATR generation!");
        }
        if (this.useFixedProfit && !this.useFixedProfitFixedPips && !this.useFixedProfitATR) {
            taskSettingsData.addError("ATM settings", null, "You have enabled Use fixed profit but none of its option in ATM generation (fixed or ATR)!");
        }
        if (this.useTS && !this.useTSFixedPips && !this.useTSATR) {
            taskSettingsData.addError("ATM settings", null, "You have enabled Use fixed profit but none of its option in ATM generation (fixed or ATR)!");
        }
    }
}

