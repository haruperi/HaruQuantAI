/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  com.strategyquant.gridlib.client.JobDetails
 *  com.strategyquant.lib.XMLUtil
 *  org.jdom2.Content
 *  org.jdom2.Element
 *  org.slf4j.Logger
 *  org.slf4j.LoggerFactory
 */
package com.strategyquant.tradinglib.gp.strategies;

import com.strategyquant.gridlib.client.JobDetails;
import com.strategyquant.lib.XMLUtil;
import com.strategyquant.tradinglib.ResultsGroup;
import com.strategyquant.tradinglib.SQStats;
import com.strategyquant.tradinglib.backtestrunner.DurationStats;
import com.strategyquant.tradinglib.gp.GPIDs;
import com.strategyquant.tradinglib.gp.IGPNode;
import com.strategyquant.tradinglib.gp.strategies.GeneratedObjectsMap;
import java.util.List;
import org.jdom2.Content;
import org.jdom2.Element;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

public class Node
implements IGPNode {
    private static final Logger Log = LoggerFactory.getLogger((String)"Node");
    private final GPIDs gpIDs = new GPIDs();
    private double fitnessIS = -1.0;
    private double fitnessIST = -1.0;
    private double fitnessISV = -1.0;
    private double fitnessOOS = -1.0;
    private Element elStrategy;
    private int dismissalReason = 0;
    private String errorMsg = null;
    private Exception exception;
    private GeneratedObjectsMap genObjMap = null;
    private ResultsGroup resultsGroup = null;
    private JobDetails jobDetails;
    private DurationStats durationStats;
    private boolean modified = false;
    private int strategyHash = -1;

    public Node(Element element) {
        this.elStrategy = element;
    }

    public Node clone() {
        Node node = new Node(this.elStrategy.clone());
        node.fitnessIS = this.fitnessIS;
        node.fitnessIST = this.fitnessIST;
        node.fitnessISV = this.fitnessISV;
        node.fitnessOOS = this.fitnessOOS;
        node.errorMsg = this.errorMsg;
        node.exception = this.exception;
        node.gpIDs.set(this.gpIDs);
        node.durationStats = this.durationStats;
        node.resultsGroup = this.resultsGroup;
        node.modified = this.modified;
        return node;
    }

    @Override
    public IGPNode clonePassed() {
        Node node = new Node(this.elStrategy.clone());
        node.fitnessIS = this.fitnessIS;
        node.fitnessIST = this.fitnessIST;
        node.fitnessISV = this.fitnessISV;
        node.fitnessOOS = this.fitnessOOS;
        node.errorMsg = this.errorMsg;
        node.exception = this.exception;
        node.gpIDs.set(this.gpIDs);
        node.durationStats = this.durationStats;
        node.modified = this.modified;
        if (this.resultsGroup != null) {
            node.resultsGroup = this.resultsGroup.clone();
        }
        return node;
    }

    @Override
    public IGPNode cloneFull() {
        Node node = new Node(this.elStrategy.clone());
        node.fitnessIS = this.fitnessIS;
        node.fitnessIST = this.fitnessIST;
        node.fitnessISV = this.fitnessISV;
        node.fitnessOOS = this.fitnessOOS;
        node.errorMsg = this.errorMsg;
        node.exception = this.exception;
        node.gpIDs.set(this.gpIDs);
        node.durationStats = this.durationStats;
        node.modified = this.modified;
        if (this.resultsGroup != null) {
            node.resultsGroup = this.resultsGroup.clone();
            this.resultsGroup.clearTempData();
        }
        return node;
    }

    @Override
    public IGPNode cloneDismissed(int n) {
        Node node = new Node(null);
        node.fitnessIS = this.fitnessIS;
        node.fitnessIST = this.fitnessIST;
        node.fitnessISV = this.fitnessISV;
        node.fitnessOOS = this.fitnessOOS;
        node.errorMsg = this.errorMsg;
        node.exception = this.exception;
        node.gpIDs.set(this.gpIDs);
        node.dismissalReason = n;
        node.durationStats = this.durationStats;
        node.resultsGroup = this.resultsGroup;
        node.modified = this.modified;
        return node;
    }

    @Override
    public IGPNode cloneForMigration() {
        Node node = new Node(this.elStrategy.clone());
        node.fitnessIS = this.fitnessIS;
        node.fitnessIST = this.fitnessIST;
        node.fitnessISV = this.fitnessISV;
        node.fitnessOOS = this.fitnessOOS;
        node.errorMsg = this.errorMsg;
        node.exception = this.exception;
        node.gpIDs.set(this.gpIDs);
        node.durationStats = this.durationStats;
        node.modified = this.modified;
        node.resultsGroup = null;
        return node;
    }

    @Override
    public void destroy() {
        String string = this.gpIDs.toShortString();
        if (this.resultsGroup != null) {
            this.resultsGroup.clear();
            this.resultsGroup = null;
        }
    }

    @Override
    public void setFitness(double d, byte by) {
        switch (by) {
            case 10: {
                this.fitnessIS = d;
                break;
            }
            case 11: {
                this.fitnessIST = d;
                break;
            }
            case 40: {
                this.fitnessISV = d;
                break;
            }
            case 20: {
                this.fitnessOOS = d;
            }
        }
    }

    @Override
    public void setFitness(IGPNode iGPNode) {
        Node node = (Node)iGPNode;
        this.fitnessIS = node.getFitness((byte)10);
        this.fitnessIST = node.getFitness((byte)11);
        this.fitnessISV = node.getFitness((byte)40);
        this.fitnessOOS = node.getFitness((byte)20);
        this.resultsGroup = node.getResultGroup();
    }

    @Override
    public double getFitness(byte by) {
        switch (by) {
            case 10: {
                return this.fitnessIS;
            }
            case 11: {
                return this.fitnessIST;
            }
            case 40: {
                return this.fitnessISV;
            }
            case 20: {
                return this.fitnessOOS;
            }
        }
        return -1.0;
    }

    @Override
    public void setGPIDs(GPIDs gPIDs) {
        this.gpIDs.set(gPIDs);
    }

    @Override
    public GPIDs getGPIDs() {
        return this.gpIDs;
    }

    public Element getStrategy() {
        return this.elStrategy;
    }

    public void setError(int n, String string, Exception exception) {
        this.fitnessIS = 0.0;
        this.fitnessIST = 0.0;
        this.fitnessISV = 0.0;
        this.fitnessOOS = 0.0;
        this.dismissalReason = n;
        this.errorMsg = string;
        this.exception = exception;
    }

    public GeneratedObjectsMap getGeneratedObjectsMap() {
        if (this.genObjMap == null) {
            this.createGeneratedObjectsMap();
        }
        return this.genObjMap;
    }

    private void createGeneratedObjectsMap() {
        this.genObjMap = new GeneratedObjectsMap();
        Element element = this.elStrategy.getChild("Strategy").getChild("Rules").getChild("Events");
        this.goThroughXML(element);
    }

    public void clearGeneratedObjectsMap() {
        if (this.genObjMap != null) {
            this.genObjMap.clear();
            this.genObjMap = null;
        }
    }

    private void goThroughXML(Element element) {
        List list = element.getChildren();
        for (int i = 0; i < list.size(); ++i) {
            Element element2 = (Element)list.get(i);
            String string = element2.getAttributeValue("generated");
            if (string != null && string.equals("random")) {
                String string2 = element2.getName();
                if (string2.equals("Item")) {
                    this.genObjMap.addItem(element2);
                } else if (string2.equals("Param")) {
                    this.genObjMap.addParam(element2);
                }
            }
            this.goThroughXML(element2);
        }
    }

    public void replaceObjectById(int n, Element element) {
        Element element2 = this.elStrategy.getChild("Strategy").getChild("Rules").getChild("Events");
        String string = Integer.toString(n);
        this.goThroughXMLAndReplace(element2, string, element);
    }

    private void goThroughXMLAndReplace(Element element, String string, Element element2) {
        List list = element.getChildren();
        for (int i = 0; i < list.size(); ++i) {
            Element element3 = (Element)list.get(i);
            String string2 = element3.getAttributeValue("gid");
            if (string2 != null && string2.equals(string)) {
                Element element4 = element2.clone();
                String string3 = element3.getAttributeValue("generated");
                String string4 = element3.getAttributeValue("randomId");
                if (string3 != null) {
                    element4.setAttribute("generated", string3);
                }
                if (string4 != null) {
                    element4.setAttribute("randomId", string4);
                }
                element.setContent(i, (Content)element4);
                return;
            }
            this.goThroughXMLAndReplace(element3, string, element2);
        }
    }

    public String getStrategyName(String string) {
        if (string != null) {
            return String.format("%s%d.%d.%d", string, this.gpIDs.islandIndex + 1, this.gpIDs.generationIndex, this.gpIDs.nodeIndex);
        }
        return String.format("Strategy %d.%d.%d", this.gpIDs.islandIndex + 1, this.gpIDs.generationIndex, this.gpIDs.nodeIndex);
    }

    public void setResultsGroup(ResultsGroup resultsGroup) {
        this.resultsGroup = resultsGroup;
    }

    public ResultsGroup getResultGroup() {
        return this.resultsGroup;
    }

    @Override
    public boolean passedEvaluation() {
        return this.errorMsg == null;
    }

    @Override
    public String getErrorMsg() {
        return this.errorMsg;
    }

    @Override
    public int getDismissalReason() {
        return this.dismissalReason;
    }

    @Override
    public void setJobDetails(JobDetails jobDetails) {
        this.jobDetails = jobDetails;
    }

    @Override
    public JobDetails getJobDetails() {
        return this.jobDetails;
    }

    @Override
    public Exception getException() {
        return this.exception;
    }

    @Override
    public String getAsString() {
        return this.gpIDs.toString();
    }

    public DurationStats getDurationStats() {
        return this.durationStats;
    }

    public void setDurationStats(DurationStats durationStats) {
        this.durationStats = durationStats;
    }

    public void setModified() {
        this.modified = true;
    }

    public boolean isModified() {
        return this.modified;
    }

    @Override
    public int getHash() {
        if (this.elStrategy == null) {
            return 0;
        }
        if (this.strategyHash == -1) {
            this.strategyHash = XMLUtil.xmlToStringRaw((Element)this.elStrategy).hashCode();
        }
        return this.strategyHash;
    }

    @Override
    public int getFingerprint() {
        if (this.resultsGroup == null) {
            return -1;
        }
        double d = this.resultsGroup.getFitness();
        try {
            SQStats sQStats = this.resultsGroup.portfolio().stats((byte)0, (byte)10, (byte)127);
            if (sQStats != null) {
                int n = sQStats.getInt("NumberOfTrades");
                double d2 = sQStats.getDouble("NetProfit");
                String string = String.format("%.2f__%d", d2, n);
                int n2 = string.hashCode();
                return n2;
            }
        }
        catch (Exception exception) {
            Log.error("Cannot compute strategy fingerprint in Gen Evo", (Throwable)exception);
        }
        return -2;
    }
}

