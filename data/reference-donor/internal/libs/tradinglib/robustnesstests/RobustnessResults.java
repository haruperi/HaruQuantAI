/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  org.jdom2.Content
 *  org.jdom2.Element
 */
package com.strategyquant.tradinglib.robustnesstests;

import com.strategyquant.tradinglib.SQStats;
import com.strategyquant.tradinglib.robustnesstests.RobustnessOrdersValues;
import java.io.IOException;
import java.util.jar.JarOutputStream;
import org.jdom2.Content;
import org.jdom2.Element;

public class RobustnessResults {
    private RobustnessOrdersValues ordersValues;
    private SQStats stats;

    public RobustnessResults() {
    }

    public RobustnessResults(Element element) {
        this.stats = new SQStats();
        this.stats.setFromXML(element);
    }

    public RobustnessOrdersValues getOrdersValues() {
        return this.ordersValues;
    }

    public void setOrdersValues(RobustnessOrdersValues robustnessOrdersValues) {
        this.ordersValues = robustnessOrdersValues;
    }

    public void setOriginalStats(SQStats sQStats) {
        this.stats = sQStats;
    }

    public SQStats getOriginalStats() {
        return this.stats;
    }

    public Element getXml(String string) {
        Element element = new Element(string);
        element.addContent((Content)this.stats.getXML());
        return element;
    }

    public void saveOrderValuesToFile(JarOutputStream jarOutputStream) throws IOException {
        this.ordersValues.saveOrderValuesToFile(jarOutputStream);
    }

    public RobustnessResults getClone() throws Exception {
        RobustnessResults robustnessResults = new RobustnessResults();
        if (this.ordersValues != null) {
            robustnessResults.ordersValues = this.ordersValues.clone();
        }
        if (this.stats != null) {
            robustnessResults.stats = this.stats.getClone();
        }
        return robustnessResults;
    }
}

