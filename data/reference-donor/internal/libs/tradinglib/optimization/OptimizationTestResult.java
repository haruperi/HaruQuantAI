/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  com.strategyquant.lib.SQUtils
 *  com.strategyquant.lib.XMLUtil
 *  com.strategyquant.lib.settings.IXMLAble
 *  it.unimi.dsi.fastutil.ints.Int2DoubleOpenHashMap
 *  org.jdom2.Content
 *  org.jdom2.Element
 *  org.slf4j.Logger
 *  org.slf4j.LoggerFactory
 */
package com.strategyquant.tradinglib.optimization;

import com.strategyquant.lib.SQUtils;
import com.strategyquant.lib.XMLUtil;
import com.strategyquant.lib.settings.IXMLAble;
import com.strategyquant.tradinglib.ResultsGroup;
import com.strategyquant.tradinglib.SQStats;
import com.strategyquant.tradinglib.optimization.OptimizationProfile;
import it.unimi.dsi.fastutil.ints.Int2DoubleOpenHashMap;
import java.io.IOException;
import java.io.ObjectInput;
import java.io.ObjectOutput;
import org.jdom2.Content;
import org.jdom2.Element;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

public class OptimizationTestResult
implements IXMLAble {
    public static final Logger Log = LoggerFactory.getLogger((String)"OptimizationTestResult");
    public String params;
    public SQStats stats;
    private Int2DoubleOpenHashMap parsedParams = null;

    public OptimizationTestResult(ResultsGroup resultsGroup, String string, OptimizationProfile optimizationProfile) throws Exception {
        this.params = string;
        this.stats = resultsGroup.mainResult().stats((byte)0, (byte)10, (byte)127).getClone();
        double d = resultsGroup.getFitness();
        double d2 = this.stats.getDouble("Fitness");
        if (d > 0.0 && d2 == 0.0) {
            this.stats.set("Fitness", d);
        }
        resultsGroup.setOptimizationProfile(optimizationProfile);
    }

    public OptimizationTestResult() {
    }

    public Element getXML() {
        Element element = new Element("Optimization");
        XMLUtil.trySetAttr((Element)element, (String)"params", (Object)this.params);
        element.addContent((Content)this.stats.getXML());
        return element;
    }

    public void setFromXML(Element element) throws Exception {
        this.params = element.getAttributeValue("params");
        this.stats = new SQStats();
        this.stats.setFromXML(element.getChild("SQStats"));
    }

    public Int2DoubleOpenHashMap parseParams() {
        if (this.parsedParams == null) {
            this.parsedParams = new Int2DoubleOpenHashMap();
        }
        String[] stringArray = this.params.split(",");
        for (int i = 0; i < stringArray.length; ++i) {
            double d;
            if (!stringArray[i].contains("=")) continue;
            String[] stringArray2 = stringArray[i].split("=");
            try {
                d = Double.parseDouble(stringArray2[1].trim());
            }
            catch (Exception exception) {
                if (stringArray2[1].trim().equalsIgnoreCase("true")) {
                    d = 1.0;
                }
                if (!stringArray2[1].trim().equalsIgnoreCase("false")) continue;
                d = 0.0;
            }
            this.parsedParams.put(stringArray2[0].trim().hashCode(), d);
        }
        return this.parsedParams;
    }

    public void serialize(ObjectOutput objectOutput) throws IOException {
        objectOutput.writeInt(1);
        SQUtils.writeUTF((ObjectOutput)objectOutput, (String)this.params);
        this.stats.serialize(objectOutput);
    }

    public void deserialize(ObjectInput objectInput) throws IOException {
        int n = objectInput.readInt();
        if (n != 1) {
            throw new IllegalArgumentException("Incorrect format " + n);
        }
        this.params = SQUtils.readUTF((ObjectInput)objectInput);
        this.stats = new SQStats();
        this.stats.deserialize(objectInput);
    }
}

