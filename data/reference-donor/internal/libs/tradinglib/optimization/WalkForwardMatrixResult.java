/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  com.strategyquant.lib.XMLUtil
 *  com.strategyquant.lib.settings.IXMLAble
 *  com.strategyquant.lib.time.SQTimeOld
 *  org.jdom2.Content
 *  org.jdom2.Element
 */
package com.strategyquant.tradinglib.optimization;

import com.strategyquant.lib.XMLUtil;
import com.strategyquant.lib.settings.IXMLAble;
import com.strategyquant.lib.time.SQTimeOld;
import com.strategyquant.tradinglib.ResultsGroup;
import com.strategyquant.tradinglib.WalkForwardPeriod;
import com.strategyquant.tradinglib.WalkForwardResult;
import com.strategyquant.tradinglib.conditions.Condition;
import com.strategyquant.tradinglib.project.ProjectConfigHelper;
import java.util.ArrayList;
import org.jdom2.Content;
import org.jdom2.Element;

public class WalkForwardMatrixResult
implements IXMLAble {
    private ArrayList<WalkForwardResult> results = new ArrayList();
    public int start1;
    public int stop1;
    public int increment1;
    public int start2;
    public int stop2;
    public int increment2;
    public int activeParam1;
    public int activeParam2;
    public int periodType;
    public ArrayList<Condition> conditions = null;
    public Element conditionsElem;
    public int thresholdPct = -1;
    public int rows = -1;
    public int cols = -1;
    public int comb = -1;
    public boolean passed = false;
    public String dismissalMessage = null;
    public int combinationsTotal = 0;
    public int combinationsPassed = 0;
    public int condPassedInBestGroup = 0;
    public String bestGroupArroundCell = "N/A";
    public String recommendedCombination = "N/A";
    public WalkForwardResult bestGroupArroundWFCell = null;
    public int numberOfPassedCombinationInBestGroup = -1;

    public void addWFResult(int n, int n2, WalkForwardResult walkForwardResult) {
        walkForwardResult.param1 = n;
        walkForwardResult.param2 = n2;
        this.results.add(walkForwardResult);
    }

    public WalkForwardResult getWFResult(int n, int n2) throws Exception {
        for (int i = 0; i < this.results.size(); ++i) {
            WalkForwardResult walkForwardResult = this.results.get(i);
            if (walkForwardResult.param1 != n || walkForwardResult.param2 != n2) continue;
            return walkForwardResult;
        }
        throw new Exception("No WalkForwardResult exists for " + n + " / " + n2);
    }

    public WalkForwardResult getWFResult(String string, boolean bl) throws Exception {
        if (string == null) {
            return null;
        }
        for (int i = 0; i < this.results.size(); ++i) {
            WalkForwardResult walkForwardResult = this.results.get(i);
            if (!walkForwardResult.resultName.equals(string)) continue;
            return walkForwardResult;
        }
        if (bl) {
            return null;
        }
        if (this.getResultList().size() > 1) {
            return this.getWFResult(this.start1, this.start2);
        }
        return this.getResultList().get(0);
    }

    public ArrayList<WalkForwardResult> getResultList() {
        return this.results;
    }

    public boolean isMatrix() {
        return this.getResultList().size() > 1;
    }

    public Element getXML() {
        Element element = new Element("MatrixResult");
        XMLUtil.trySetAttr((Element)element, (String)"start1", (Object)this.start1);
        XMLUtil.trySetAttr((Element)element, (String)"stop1", (Object)this.stop1);
        XMLUtil.trySetAttr((Element)element, (String)"increment1", (Object)this.increment1);
        XMLUtil.trySetAttr((Element)element, (String)"start2", (Object)this.start2);
        XMLUtil.trySetAttr((Element)element, (String)"stop2", (Object)this.stop2);
        XMLUtil.trySetAttr((Element)element, (String)"increment2", (Object)this.increment2);
        XMLUtil.trySetAttr((Element)element, (String)"activeParam1", (Object)this.activeParam1);
        XMLUtil.trySetAttr((Element)element, (String)"activeParam2", (Object)this.activeParam2);
        XMLUtil.trySetAttr((Element)element, (String)"periodType", (Object)this.periodType);
        for (int i = 0; i < this.results.size(); ++i) {
            Element element2 = this.results.get(i).getXML();
            element.addContent((Content)element2);
        }
        return element;
    }

    public void setFromXML(Element element) throws Exception {
        this.start1 = XMLUtil.tryGetIntAttr((Element)element, (String)"start1");
        this.stop1 = XMLUtil.tryGetIntAttr((Element)element, (String)"stop1");
        this.increment1 = XMLUtil.tryGetIntAttr((Element)element, (String)"increment1");
        this.start2 = XMLUtil.tryGetIntAttr((Element)element, (String)"start2");
        this.stop2 = XMLUtil.tryGetIntAttr((Element)element, (String)"stop2");
        this.increment2 = XMLUtil.tryGetIntAttr((Element)element, (String)"increment2");
        this.activeParam1 = XMLUtil.tryGetIntAttr((Element)element, (String)"activeParam1");
        this.activeParam2 = XMLUtil.tryGetIntAttr((Element)element, (String)"activeParam2");
        this.periodType = XMLUtil.getIntAttr((Element)element, (String)"periodType", (int)10);
        this.results.clear();
        for (Element element2 : element.getChildren()) {
            WalkForwardResult walkForwardResult = new WalkForwardResult();
            walkForwardResult.setFromXML(element2);
            this.results.add(walkForwardResult);
        }
    }

    private WalkForwardResult[][] createMatrix() throws Exception {
        int n;
        int n2 = 0;
        int n3 = 0;
        for (n = this.start2; n <= this.stop2; n += this.increment2) {
            ++n2;
        }
        for (n = this.start1; n <= this.stop1; n += this.increment1) {
            ++n3;
        }
        WalkForwardResult[][] walkForwardResultArray = new WalkForwardResult[n2][n3];
        int n4 = 0;
        int n5 = 0;
        for (int i = this.start2; i <= this.stop2; i += this.increment2) {
            for (int j = this.start1; j <= this.stop1; j += this.increment1) {
                WalkForwardResult walkForwardResult;
                walkForwardResultArray[n5][n4] = walkForwardResult = this.getWFResult(j, i);
                ++n4;
            }
            ++n5;
            n4 = 0;
        }
        return walkForwardResultArray;
    }

    public String computeBestWF(ResultsGroup resultsGroup) throws Exception {
        String string = null;
        if (this.isMatrix()) {
            Element element = (Element)resultsGroup.specialValues().get("WalkForwardConditions");
            ArrayList<Condition> arrayList = ProjectConfigHelper.getConditions(element);
            int n = XMLUtil.getIntAttr((Element)element, (String)"thresholdPct", (int)80);
            int n2 = XMLUtil.getIntAttr((Element)element, (String)"robCombRows", (int)3);
            int n3 = XMLUtil.getIntAttr((Element)element, (String)"robCombCols", (int)3);
            int n4 = XMLUtil.getIntAttr((Element)element, (String)"robMinComb", (int)7);
            this.computeRobustnessResults(resultsGroup, element, arrayList, n, n2, n3, n4);
            string = this.bestGroupArroundWFCell.getResultKeyName();
        } else {
            WalkForwardResult walkForwardResult = this.getResultList().get(0);
            walkForwardResult.computeStats(resultsGroup);
            string = walkForwardResult.getResultKeyName();
        }
        return string;
    }

    public void computeRobustnessResults(ResultsGroup resultsGroup, Element element, ArrayList<Condition> arrayList, int n, int n2, int n3, int n4) throws Exception {
        this.conditionsElem = element;
        this.conditions = arrayList;
        this.thresholdPct = n;
        this.rows = n2;
        this.cols = n3;
        this.comb = n4;
        this.combinationsTotal = 0;
        this.combinationsPassed = 0;
        this.dismissalMessage = null;
        WalkForwardResult walkForwardResult = null;
        if (this.results.size() > 1) {
            for (int i = this.start2; i <= this.stop2; i += this.increment2) {
                for (int j = this.start1; j <= this.stop1; j += this.increment1) {
                    ++this.combinationsTotal;
                    walkForwardResult = this.getWFResult(j, i);
                    walkForwardResult.computeRobustnessScore(resultsGroup, arrayList, n, this.periodType);
                    if (!walkForwardResult.passed) continue;
                    ++this.combinationsPassed;
                }
            }
            this.passed = this.findBestGroupOfPassedCombinations(n2, n3, n4);
            if (!this.passed) {
                this.dismissalMessage = "Robustness score didn't pass.";
            }
            this.condPassedInBestGroup = this.numberOfPassedCombinationInBestGroup;
            this.bestGroupArroundCell = this.bestGroupArroundWFCell.toString(this.periodType);
            WalkForwardPeriod walkForwardPeriod = this.bestGroupArroundWFCell.wfPeriods.get(0);
            this.recommendedCombination = String.format("Recommended combination: %s, which means:<br/><b>reoptimizing every %d days on history of %d days</b>", this.bestGroupArroundWFCell.toString(this.periodType), SQTimeOld.getDaysBetween((long)walkForwardPeriod.runFrom, (long)walkForwardPeriod.runTo), SQTimeOld.getDaysBetween((long)walkForwardPeriod.optimizeFrom, (long)walkForwardPeriod.optimizeTo));
        } else {
            walkForwardResult = this.results.get(0);
            int n5 = walkForwardResult.computeRobustnessScore(resultsGroup, arrayList, n, this.periodType);
            this.passed = walkForwardResult.passed;
            if (!this.passed) {
                this.dismissalMessage = String.format("Robustness score %d%% didn't pass %d%%.", n5, n);
            }
        }
    }

    private boolean findBestGroupOfPassedCombinations(int n, int n2, int n3) throws Exception {
        this.bestGroupArroundWFCell = null;
        this.numberOfPassedCombinationInBestGroup = -1;
        WalkForwardResult[][] walkForwardResultArray = this.createMatrix();
        int n4 = 0;
        int n5 = 0;
        int n6 = 0;
        int n7 = 0;
        int n8 = walkForwardResultArray.length;
        int n9 = walkForwardResultArray[0].length;
        int n10 = 0;
        if (n > n8 || n2 > n9) {
            for (WalkForwardResult walkForwardResult : this.results) {
                if (this.bestGroupArroundWFCell != null && this.bestGroupArroundWFCell.scorePerc >= walkForwardResult.scorePerc) continue;
                this.bestGroupArroundWFCell = walkForwardResult;
                this.numberOfPassedCombinationInBestGroup = 1;
            }
        } else {
            for (n4 = 0; n4 < n8 && n4 + (n - 1) < n8; ++n4) {
                for (n5 = 0; n5 < n9 && n5 + (n2 - 1) < n9; ++n5) {
                    WalkForwardResult walkForwardResult;
                    n10 = 0;
                    for (n6 = n4; n6 < n4 + n && n6 < n8; ++n6) {
                        for (n7 = n5; n7 < n5 + n2 && n7 < n9; ++n7) {
                            walkForwardResult = walkForwardResultArray[n6][n7];
                            if (!walkForwardResult.passed) continue;
                            ++n10;
                        }
                    }
                    walkForwardResult = walkForwardResultArray[n4 + (n - 1) / 2][n5 + (n2 - 1) / 2];
                    if (this.numberOfPassedCombinationInBestGroup >= n10) continue;
                    this.numberOfPassedCombinationInBestGroup = n10;
                    this.bestGroupArroundWFCell = walkForwardResult;
                }
            }
        }
        return this.numberOfPassedCombinationInBestGroup >= n3;
    }
}

