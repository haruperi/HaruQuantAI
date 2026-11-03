/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  com.strategyquant.lib.L
 *  com.strategyquant.lib.SQUtils
 *  com.strategyquant.lib.XMLUtil
 *  com.strategyquant.lib.settings.IXMLAble
 *  org.jdom2.Content
 *  org.jdom2.Element
 *  org.slf4j.Logger
 *  org.slf4j.LoggerFactory
 */
package com.strategyquant.tradinglib;

import com.strategyquant.lib.L;
import com.strategyquant.lib.SQUtils;
import com.strategyquant.lib.XMLUtil;
import com.strategyquant.lib.settings.IXMLAble;
import com.strategyquant.tradinglib.DatabankColumn;
import com.strategyquant.tradinglib.ResultsGroup;
import com.strategyquant.tradinglib.SQStats;
import com.strategyquant.tradinglib.WalkForwardColumn;
import com.strategyquant.tradinglib.WalkForwardPeriod;
import com.strategyquant.tradinglib.conditions.Condition;
import com.strategyquant.tradinglib.databank.DatabankColumns;
import com.strategyquant.tradinglib.optimization.OptimizationConst;
import com.strategyquant.tradinglib.optimization.WalkForwardColumns;
import com.strategyquant.tradinglib.optimization.WalkForwardScore;
import com.strategyquant.tradinglib.optimization.WalkForwardStability;
import com.strategyquant.tradinglib.table.TableColumn;
import java.util.ArrayList;
import org.jdom2.Content;
import org.jdom2.Element;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

public class WalkForwardResult
implements IXMLAble {
    public static final Logger Log = LoggerFactory.getLogger(WalkForwardResult.class);
    public ArrayList<WalkForwardPeriod> wfPeriods = null;
    public String resultName = null;
    public int param1;
    public int param2;
    public String testParams;
    public SQStats stats = null;
    public SQStats statsOOS = null;
    public SQStats statsStability = null;
    public SQStats statsScore = null;
    public SQStats statsSpecial = null;
    public int testedConditions = 0;
    public int passedConditions = 0;
    public int scorePerc = 0;
    public boolean passed = false;

    public Element getXML() {
        Element element = new Element("RunResult");
        XMLUtil.trySetAttr((Element)element, (String)"param1", (Object)this.param1);
        XMLUtil.trySetAttr((Element)element, (String)"param2", (Object)this.param2);
        XMLUtil.trySetAttr((Element)element, (String)"testParams", (Object)this.testParams);
        XMLUtil.trySetAttr((Element)element, (String)"resultName", (Object)this.resultName);
        Element element2 = XMLUtil.valueToElement((String)"stats", (Object)this.stats);
        if (element2 != null) {
            element.addContent((Content)element2);
        }
        XMLUtil.trySetAttr((Element)element, (String)"stats", (Object)this.stats);
        element2 = XMLUtil.valueToElement((String)"statsOOS", (Object)this.statsOOS);
        if (element2 != null) {
            element.addContent((Content)element2);
        }
        XMLUtil.trySetAttr((Element)element, (String)"statsOOS", (Object)this.statsOOS);
        Element element3 = new Element("Periods");
        element.addContent((Content)element3);
        for (int i = 0; i < this.wfPeriods.size(); ++i) {
            Element element4 = this.wfPeriods.get(i).getXML();
            element3.addContent((Content)element4);
        }
        return element;
    }

    public void setFromXML(Element element) throws Exception {
        this.param1 = XMLUtil.tryGetIntAttr((Element)element, (String)"param1");
        this.param2 = XMLUtil.tryGetIntAttr((Element)element, (String)"param2");
        this.testParams = element.getAttributeValue("testParams");
        this.resultName = element.getAttributeValue("resultName");
        Element element2 = element.getChild("stats").getChild("SQStats");
        if (this.stats == null) {
            this.stats = new SQStats();
        }
        this.stats.setFromXML(element2);
        if (this.statsOOS == null) {
            this.statsOOS = new SQStats();
        }
        if ((element2 = element.getChild("statsOOS")) != null) {
            element2 = element2.getChild("SQStats");
            this.statsOOS.setFromXML(element2);
        }
        if (this.wfPeriods == null) {
            this.wfPeriods = new ArrayList();
        } else {
            this.wfPeriods.clear();
        }
        Element element3 = element.getChild("Periods");
        for (Element element4 : element3.getChildren()) {
            WalkForwardPeriod walkForwardPeriod = new WalkForwardPeriod();
            walkForwardPeriod.setFromXML(element4);
            this.wfPeriods.add(walkForwardPeriod);
        }
    }

    public String toString(int n) {
        return OptimizationConst.printWFByPeriodType(n, this.param2, this.param1);
    }

    public String getResultKeyName() {
        return this.resultName;
    }

    public int computeRobustnessScore(ResultsGroup resultsGroup, ArrayList<Condition> arrayList, int n, int n2) throws Exception {
        this.testedConditions = 0;
        this.passedConditions = 0;
        this.scorePerc = 100;
        this.passed = true;
        this.computeStats(resultsGroup);
        try {
            if (arrayList == null) {
                return this.scorePerc;
            }
            for (int i = 0; i < arrayList.size(); ++i) {
                Condition condition = arrayList.get(i);
                if (!condition.isUsed()) continue;
                try {
                    boolean bl = condition.isMet(resultsGroup, this);
                    ++this.testedConditions;
                    if (!bl) continue;
                    ++this.passedConditions;
                    continue;
                }
                catch (Exception exception) {
                    Log.error(String.format("Cannot evaluate condition %s. Exc.", condition.toString()), (Throwable)exception);
                }
            }
            if (this.testedConditions > 0) {
                this.scorePerc = SQUtils.round((double)(SQUtils.safeDivide((double)this.passedConditions, (double)this.testedConditions) * 100.0));
                this.passed = this.scorePerc >= n;
            }
        }
        catch (Exception exception) {
            throw new Exception(L.t((String)"Error while computing Robustness Result of combination '%s'.", (Object[])new Object[]{this.toString(n2)}), exception);
        }
        this.statsSpecial.set("WFScore", (double)this.scorePerc);
        return this.scorePerc;
    }

    public void computeStats(ResultsGroup resultsGroup) {
        if (this.statsStability != null) {
            return;
        }
        this.statsStability = new SQStats();
        this.statsScore = new SQStats();
        this.statsSpecial = new SQStats();
        for (TableColumn tableColumn : DatabankColumns.get().getAvailableClasses()) {
            WalkForwardStability.compute((DatabankColumn)tableColumn, this.statsStability, this);
            WalkForwardScore.compute((DatabankColumn)tableColumn, resultsGroup, this.statsScore, this);
        }
        for (TableColumn tableColumn : WalkForwardColumns.get().getAvailableClasses()) {
            ((WalkForwardColumn)tableColumn).compute(this, this.statsSpecial);
        }
    }
}

