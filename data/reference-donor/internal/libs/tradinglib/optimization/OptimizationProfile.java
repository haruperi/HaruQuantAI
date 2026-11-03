/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  com.strategyquant.lib.L
 *  com.strategyquant.lib.SQUtils
 *  com.strategyquant.lib.XMLUtil
 *  com.strategyquant.lib.app.MainApp
 *  com.strategyquant.lib.settings.IXMLAble
 *  it.unimi.dsi.fastutil.doubles.DoubleArrayList
 *  it.unimi.dsi.fastutil.ints.IntOpenHashSet
 *  it.unimi.dsi.fastutil.objects.ObjectArrayList
 *  org.jdom2.Content
 *  org.jdom2.Element
 *  org.json.JSONArray
 *  org.json.JSONObject
 *  org.slf4j.Logger
 *  org.slf4j.LoggerFactory
 */
package com.strategyquant.tradinglib.optimization;

import com.strategyquant.lib.L;
import com.strategyquant.lib.SQUtils;
import com.strategyquant.lib.XMLUtil;
import com.strategyquant.lib.app.MainApp;
import com.strategyquant.lib.settings.IXMLAble;
import com.strategyquant.tradinglib.BarChart;
import com.strategyquant.tradinglib.ResultsGroup;
import com.strategyquant.tradinglib.SQStats;
import com.strategyquant.tradinglib.optimization.OptProfileChecksLevels;
import com.strategyquant.tradinglib.optimization.OptimizationTestResult;
import com.strategyquant.tradinglib.optimization.SysParamPermutationsCharts;
import com.strategyquant.tradinglib.optimization.SysParamPermutationsTable;
import it.unimi.dsi.fastutil.doubles.DoubleArrayList;
import it.unimi.dsi.fastutil.ints.IntOpenHashSet;
import it.unimi.dsi.fastutil.objects.ObjectArrayList;
import java.io.IOException;
import java.io.ObjectInput;
import java.io.ObjectOutput;
import java.util.List;
import org.jdom2.Content;
import org.jdom2.Element;
import org.json.JSONArray;
import org.json.JSONObject;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

public class OptimizationProfile
implements IXMLAble {
    public static final Logger Log = LoggerFactory.getLogger((String)"OptimizationResults");
    private ObjectArrayList<OptimizationTestResult> optimizations = new ObjectArrayList();
    private IntOpenHashSet optimizationKeys = new IntOpenHashSet();
    private boolean updated = false;
    public int countTotalOptimizations;
    public int countProfitableOptimizations;
    public int countLosingOptimizations;
    public int lastCount = 0;
    public int countZeroOptimizations;
    public double profitableOptPct;
    public double avgProfit;
    public int uniformDistrChanges;
    public double topProfit;
    public double stdev;
    private double stdevComputed;
    private OptimizationTestResult originalResult;
    private String dismissalMessage = null;
    private int dismissalReason;
    private static final int Passed = 1;
    private static final int Failed = 0;
    private static final int NotEvaluated = -1;
    private static final Object OPTPROF_FILE_FORMAT = null;
    public int profitableOptCheckResult;
    public int avgProfitCheckResult;
    public int uniformDistrCheckResult;
    public int topProfitCheckResult;
    private SysParamPermutationsCharts sysParamPermutationsCharts = null;
    private SysParamPermutationsTable sysParamPermutationsTable = null;
    private JSONArray availableParams = null;
    private JSONObject profitableOptimizationsJSON = null;
    private JSONObject performanceDistributionChart = null;
    private JSONObject checksObjJSON = null;
    private int checksLevelHash;

    /*
     * WARNING - Removed try catching itself - possible behaviour change.
     */
    public void addResult(ResultsGroup resultsGroup) throws Exception {
        String string = resultsGroup.specialValues().getString("OptimizationParameters");
        if (string == null) {
            throw new Exception(L.t((String)"No params set in the result!", (Object[])new Object[0]));
        }
        IntOpenHashSet intOpenHashSet = this.optimizationKeys;
        synchronized (intOpenHashSet) {
            if (!this.optimizationKeys.contains(string.hashCode())) {
                OptimizationTestResult optimizationTestResult = new OptimizationTestResult(resultsGroup, string, this);
                this.optimizations.add((Object)optimizationTestResult);
                this.optimizationKeys.add(string.hashCode());
                this.updated = true;
            }
        }
    }

    public void addOriginalResult(ResultsGroup resultsGroup) throws Exception {
        String string = resultsGroup.specialValues().getString("OptimizationParameters");
        if (string == null) {
            throw new Exception(L.t((String)"No params set in the result!", (Object[])new Object[0]));
        }
        this.originalResult = new OptimizationTestResult(resultsGroup, string, this);
        this.updated = true;
    }

    public OptimizationTestResult getOriginalResult() {
        return this.originalResult;
    }

    private void recomputeCounts() {
        if (this.lastCount == this.optimizations.size() || this.optimizations.size() == 0) {
            return;
        }
        if (this.profitableOptPct != 0.0 || this.avgProfit != 0.0 || this.countTotalOptimizations != 0) {
            // empty if block
        }
        this.lastCount = this.optimizations.size();
        this.countTotalOptimizations = this.optimizations.size();
        this.countProfitableOptimizations = 0;
        this.countLosingOptimizations = 0;
        this.countZeroOptimizations = 0;
        double d = 0.0;
        double d2 = Double.MIN_VALUE;
        this.profitableOptPct = 0.0;
        this.avgProfit = 0.0;
        this.uniformDistrChanges = 0;
        this.topProfit = -1.7976931348623157E308;
        DoubleArrayList doubleArrayList = new DoubleArrayList();
        for (int i = 0; i < this.optimizations.size(); ++i) {
            OptimizationTestResult optimizationTestResult = (OptimizationTestResult)this.optimizations.get(i);
            SQStats sQStats = optimizationTestResult.stats;
            double d3 = sQStats.getDouble("NetProfit");
            doubleArrayList.add(d3);
            d += d3;
            if (d3 > this.topProfit) {
                this.topProfit = d3;
            }
            if (d2 != Double.MIN_VALUE && (d2 < 0.0 && d3 > 0.0 || d2 > 0.0 && d3 < 0.0)) {
                ++this.uniformDistrChanges;
            }
            if (d3 >= 0.0) {
                ++this.countProfitableOptimizations;
            } else if (d3 == 0.0) {
                ++this.countZeroOptimizations;
            } else {
                ++this.countLosingOptimizations;
            }
            d2 = d3;
        }
        this.profitableOptPct = (double)this.countProfitableOptimizations / (double)this.optimizations.size() * 100.0;
        this.avgProfit = d / (double)this.optimizations.size();
        this.stdev = this.computeStdev(this.avgProfit, doubleArrayList);
    }

    public ObjectArrayList<OptimizationTestResult> getOptimizations() {
        return this.optimizations;
    }

    public int getDismissalReason() {
        return this.dismissalReason;
    }

    public String getDismissalMessage() {
        return this.dismissalMessage;
    }

    public boolean evaluateChecks(OptProfileChecksLevels optProfileChecksLevels) {
        this.dismissalMessage = null;
        this.dismissalReason = 0;
        this.profitableOptCheckResult = 1;
        this.avgProfitCheckResult = 1;
        this.uniformDistrCheckResult = 1;
        this.topProfitCheckResult = 1;
        this.recomputeCounts();
        if (optProfileChecksLevels.evalProfitOptCheck) {
            if (this.profitableOptPct <= (double)optProfileChecksLevels.profitableOptPct) {
                this.profitableOptCheckResult = 0;
                this.dismissalReason = 10008;
                this.dismissalMessage = L.t((String)"%% of Profitable Optimizations (%d %%) > %d %%", (Object[])new Object[]{SQUtils.round((double)this.profitableOptPct), optProfileChecksLevels.profitableOptPct});
            }
        } else {
            this.profitableOptCheckResult = -1;
        }
        if (optProfileChecksLevels.evalAvgProfitCheck) {
            if (this.avgProfit <= optProfileChecksLevels.avgProfit) {
                this.avgProfitCheckResult = 0;
                if (this.dismissalMessage == null) {
                    this.dismissalReason = 10009;
                    this.dismissalMessage = L.t((String)"Average profit ($ %s) > $ %s", (Object[])new Object[]{SQUtils.d2((double)this.avgProfit), SQUtils.d2((double)optProfileChecksLevels.avgProfit)});
                }
            }
        } else {
            this.avgProfitCheckResult = -1;
        }
        if (optProfileChecksLevels.evalUniformDistrCheck) {
            if (this.uniformDistrChanges >= optProfileChecksLevels.uniformDistrChanges) {
                this.uniformDistrCheckResult = 0;
                if (this.dismissalMessage == null) {
                    this.dismissalReason = 10010;
                    this.dismissalMessage = L.t((String)"Uniform distribution changes (%d) < %d", (Object[])new Object[]{this.uniformDistrChanges, optProfileChecksLevels.uniformDistrChanges});
                }
            }
        } else {
            this.uniformDistrCheckResult = -1;
        }
        this.stdevComputed = this.stdev * optProfileChecksLevels.stdevAvgProfit + this.avgProfit;
        if (optProfileChecksLevels.evalTopProfitCheck) {
            if (this.topProfit >= this.stdevComputed) {
                this.topProfitCheckResult = 0;
                if (this.dismissalMessage == null) {
                    this.dismissalReason = 10011;
                    this.dismissalMessage = L.t((String)"Best Optimization profit ($ %s) < $ %s", (Object[])new Object[]{SQUtils.d2((double)this.topProfit), SQUtils.d2((double)this.stdev)});
                }
            }
        } else {
            this.topProfitCheckResult = -1;
        }
        return this.dismissalMessage == null;
    }

    private double computeStdev(double d, DoubleArrayList doubleArrayList) {
        if (doubleArrayList.size() <= 0) {
            return 0.0;
        }
        double d2 = 0.0;
        for (int i = 0; i < doubleArrayList.size(); ++i) {
            double d3 = doubleArrayList.getDouble(i);
            d2 += Math.pow(1.0 * d3 - d, 2.0);
        }
        double d4 = Math.sqrt(d2 / (double)doubleArrayList.size());
        return d4;
    }

    public Element getXML() {
        Element element = new Element("OptimizationProfile");
        XMLUtil.trySetAttr((Element)element, (String)"version", (Object)"114");
        if (this.originalResult != null) {
            Element element2 = new Element("Original");
            element2.addContent((Content)this.originalResult.getXML());
            element.addContent((Content)element2);
        }
        for (int i = 0; i < this.optimizations.size(); ++i) {
            element.addContent((Content)((OptimizationTestResult)this.optimizations.get(i)).getXML());
        }
        return element;
    }

    public void setFromXML(Element element) throws Exception {
        Element element2 = element;
        List list = element2.getChildren();
        for (int i = 0; i < list.size(); ++i) {
            OptimizationTestResult optimizationTestResult;
            Element element3 = (Element)list.get(i);
            if (element3.getName().equals("Original")) {
                optimizationTestResult = new OptimizationTestResult();
                optimizationTestResult.setFromXML((Element)element3.getChildren().get(0));
                this.originalResult = optimizationTestResult;
                continue;
            }
            optimizationTestResult = new OptimizationTestResult();
            optimizationTestResult.setFromXML(element3);
            this.optimizations.add((Object)optimizationTestResult);
        }
    }

    public void clear() {
    }

    public void serialize(ObjectOutput objectOutput) throws IOException {
        objectOutput.writeInt(2);
        String string = MainApp.settings().get("dontStoreOP3DChartsData");
        boolean bl = string == null ? false : !Boolean.parseBoolean(string);
        objectOutput.writeBoolean(bl);
        if (bl) {
            if (this.originalResult != null) {
                objectOutput.writeBoolean(true);
                this.originalResult.serialize(objectOutput);
            } else {
                objectOutput.writeBoolean(false);
            }
            objectOutput.writeInt(this.optimizations.size());
            for (int i = 0; i < this.optimizations.size(); ++i) {
                ((OptimizationTestResult)this.optimizations.get(i)).serialize(objectOutput);
            }
        }
        this.getSysParamPermutationsTable().serialize(objectOutput);
        this.getSysParamPermutationsCharts().serialize(objectOutput);
        JSONArray jSONArray = this.getAvailableParams();
        objectOutput.writeUTF(jSONArray.toString());
        JSONObject jSONObject = this.printProfitableOptimizations();
        objectOutput.writeUTF(jSONObject.toString());
        objectOutput.writeInt(this.countTotalOptimizations);
        objectOutput.writeInt(this.countProfitableOptimizations);
        objectOutput.writeInt(this.countLosingOptimizations);
        objectOutput.writeInt(this.lastCount);
        objectOutput.writeInt(this.countZeroOptimizations);
        objectOutput.writeDouble(this.profitableOptPct);
        objectOutput.writeDouble(this.avgProfit);
        objectOutput.writeDouble(this.uniformDistrChanges);
        objectOutput.writeDouble(this.topProfit);
        objectOutput.writeDouble(this.stdev);
        objectOutput.writeDouble(this.stdevComputed);
        jSONObject = this.printPerformanceDistributionChart();
        objectOutput.writeUTF(jSONObject.toString());
        objectOutput.flush();
    }

    public void deserialize(ObjectInput objectInput) throws IOException {
        if (objectInput.available() > 0) {
            boolean bl;
            int n = objectInput.readInt();
            String string = MainApp.settings().get("dontStoreOP3DChartsData");
            boolean bl2 = string == null ? false : (bl = !Boolean.parseBoolean(string));
            if (n == 1) {
                this.readFormat1(objectInput);
                if (!bl) {
                    this.getSysParamPermutationsTable();
                    this.getSysParamPermutationsCharts();
                    this.getAvailableParams();
                    this.printProfitableOptimizations();
                    this.printPerformanceDistributionChart();
                }
            } else if (n == 2) {
                this.readFormat2(objectInput);
            } else {
                throw new IllegalArgumentException("Incorrect format " + n);
            }
            if (!bl) {
                this.optimizations.clear();
                this.optimizationKeys.clear();
            }
        }
    }

    private void readFormat2(ObjectInput objectInput) throws IOException {
        boolean bl = objectInput.readBoolean();
        if (bl) {
            this.readFormat1(objectInput);
        }
        this.sysParamPermutationsTable = new SysParamPermutationsTable(objectInput);
        this.sysParamPermutationsCharts = new SysParamPermutationsCharts(objectInput);
        this.availableParams = new JSONArray(objectInput.readUTF());
        this.profitableOptimizationsJSON = new JSONObject(objectInput.readUTF());
        this.countTotalOptimizations = objectInput.readInt();
        this.countProfitableOptimizations = objectInput.readInt();
        this.countLosingOptimizations = objectInput.readInt();
        this.lastCount = objectInput.readInt();
        this.countZeroOptimizations = objectInput.readInt();
        this.profitableOptPct = objectInput.readDouble();
        this.avgProfit = objectInput.readDouble();
        this.uniformDistrChanges = (int)objectInput.readDouble();
        this.topProfit = objectInput.readDouble();
        this.stdev = objectInput.readDouble();
        this.stdevComputed = objectInput.readDouble();
        this.performanceDistributionChart = new JSONObject(objectInput.readUTF());
    }

    private void readFormat1(ObjectInput objectInput) throws IOException {
        if (objectInput.readBoolean()) {
            OptimizationTestResult optimizationTestResult = new OptimizationTestResult();
            optimizationTestResult.deserialize(objectInput);
            this.originalResult = optimizationTestResult;
        }
        int n = objectInput.readInt();
        for (int i = 0; i < n; ++i) {
            OptimizationTestResult optimizationTestResult = new OptimizationTestResult();
            optimizationTestResult.deserialize(objectInput);
            this.optimizations.add((Object)optimizationTestResult);
        }
    }

    public SysParamPermutationsTable getSysParamPermutationsTable() {
        if (this.sysParamPermutationsTable == null) {
            this.sysParamPermutationsTable = new SysParamPermutationsTable(this);
        }
        return this.sysParamPermutationsTable;
    }

    public SysParamPermutationsCharts getSysParamPermutationsCharts() {
        if (this.sysParamPermutationsCharts == null) {
            this.sysParamPermutationsCharts = new SysParamPermutationsCharts(this);
        }
        return this.sysParamPermutationsCharts;
    }

    public JSONArray getAvailableParams() {
        if (this.availableParams == null) {
            if (this.optimizations.size() == 0) {
                return new JSONArray();
            }
            String string = ((OptimizationTestResult)this.optimizations.get((int)0)).params;
            this.availableParams = new JSONArray();
            String[] stringArray = string.split(",");
            for (int i = 0; i < stringArray.length; ++i) {
                if (!stringArray[i].contains("=")) continue;
                String[] stringArray2 = stringArray[i].split("=");
                String string2 = stringArray2[0].trim();
                this.availableParams.put((Object)string2);
            }
        }
        return this.availableParams;
    }

    public JSONObject printProfitableOptimizations() {
        if (this.profitableOptimizationsJSON == null) {
            JSONObject jSONObject = new JSONObject();
            this.recomputeCounts();
            double d = this.countTotalOptimizations;
            double d2 = this.countProfitableOptimizations;
            double d3 = this.countLosingOptimizations;
            double d4 = this.countZeroOptimizations;
            double d5 = SQUtils.round2((double)(d2 / d * 100.0));
            double d6 = SQUtils.round2((double)(d3 / d * 100.0));
            double d7 = SQUtils.round2((double)(d4 / d * 100.0));
            jSONObject.put("total", (Object)new JSONObject().put("count", d).put("pct", 100));
            jSONObject.put("profitable", (Object)new JSONObject().put("count", d2).put("pct", d5));
            jSONObject.put("losing", (Object)new JSONObject().put("count", d3).put("pct", d6));
            jSONObject.put("zero", (Object)new JSONObject().put("count", d4).put("pct", d7));
            this.profitableOptimizationsJSON = jSONObject;
        }
        return this.profitableOptimizationsJSON;
    }

    public JSONObject printChecksResults(OptProfileChecksLevels optProfileChecksLevels) {
        if (this.checksObjJSON == null) {
            JSONObject jSONObject = new JSONObject();
            jSONObject.put("profitableOptPct", SQUtils.round2((double)this.profitableOptPct));
            jSONObject.put("avgProfit", SQUtils.round2((double)this.avgProfit));
            jSONObject.put("uniformDistrChanges", this.uniformDistrChanges);
            jSONObject.put("topProfit", SQUtils.round2((double)this.topProfit));
            jSONObject.put("stdev", SQUtils.round2((double)this.stdev));
            this.checksObjJSON = jSONObject;
        }
        if (optProfileChecksLevels != null) {
            this.evaluateChecks(optProfileChecksLevels);
            this.checksObjJSON.put("profitableOptCheckResult", this.profitableOptCheckResult);
            this.checksObjJSON.put("avgProfitCheckResult", this.avgProfitCheckResult);
            this.checksObjJSON.put("uniformDistrCheckResult", this.uniformDistrCheckResult);
            this.checksObjJSON.put("topProfitCheckResult", this.topProfitCheckResult);
        }
        return this.checksObjJSON;
    }

    public JSONObject printPerformanceDistributionChart() {
        if (this.performanceDistributionChart == null) {
            this.performanceDistributionChart = new JSONObject();
            BarChart barChart = new BarChart();
            barChart.maxXTicksLimit = 10;
            barChart.yAxisTitle = L.t((String)"Net profit", (Object[])new Object[0]);
            barChart.xAxisTitle = L.t((String)"Optimization run", (Object[])new Object[0]);
            barChart.tooltips = false;
            barChart.displayXAxesLabels = false;
            barChart.disableEvents = true;
            ObjectArrayList<OptimizationTestResult> objectArrayList = this.getOptimizations();
            int[] nArray = new int[objectArrayList.size()];
            for (int i = 0; i < nArray.length; ++i) {
                OptimizationTestResult optimizationTestResult = (OptimizationTestResult)objectArrayList.get(i);
                nArray[i] = (int)optimizationTestResult.stats.getDouble("NetProfit");
            }
            nArray = this.optimalize(nArray, (int)this.avgProfit);
            JSONArray jSONArray = new JSONArray();
            for (int i = 0; i < nArray.length; ++i) {
                barChart.addValue("p", Integer.valueOf(i), nArray[i]);
                jSONArray.put((int)this.avgProfit);
            }
            JSONObject jSONObject = new JSONObject();
            jSONObject.put("type", (Object)"line");
            jSONObject.put("borderColor", (Object)"#E8383C");
            jSONObject.put("borderWidth", (Object)"2");
            jSONObject.put("fill", (Object)"false");
            jSONObject.put("data", (Object)jSONArray);
            this.performanceDistributionChart = barChart.toJSON();
            JSONArray jSONArray2 = this.performanceDistributionChart.getJSONObject("data").getJSONArray("datasets");
            if (jSONArray2.length() > 0) {
                JSONObject jSONObject2 = this.performanceDistributionChart.getJSONObject("data").getJSONArray("datasets").getJSONObject(0);
                this.performanceDistributionChart.getJSONObject("data").getJSONArray("datasets").put(0, (Object)jSONObject).put((Object)jSONObject2);
            }
        }
        return this.performanceDistributionChart;
    }

    private int[] optimalize(int[] nArray, int n) {
        int n2;
        int n3 = 500;
        if (nArray.length <= n3 * 2) {
            return nArray;
        }
        int[] nArray2 = new int[n3];
        int[] nArray3 = new int[n3];
        for (n2 = 0; n2 < n3; ++n2) {
            nArray2[n2] = Integer.MAX_VALUE;
            nArray3[n2] = Integer.MAX_VALUE;
        }
        n2 = nArray.length / n3;
        for (int i = 0; i < nArray.length; ++i) {
            int n4 = Math.round(i / n2);
            int n5 = nArray[i];
            if (n4 >= n3) {
                n4 = n3 - 1;
            }
            if (nArray2[n4] == Integer.MAX_VALUE || nArray2[n4] > n5) {
                nArray2[n4] = n5;
            }
            if (nArray3[n4] != Integer.MAX_VALUE && nArray3[n4] >= n5) continue;
            nArray3[n4] = n5;
        }
        int[] nArray4 = new int[n3 * 2];
        int n6 = 0;
        for (int i = 0; i < n3; ++i) {
            nArray4[n6++] = nArray2[i];
            nArray4[n6++] = nArray3[i];
        }
        return nArray4;
    }

    public void compute(boolean bl, boolean bl2) {
        String string = MainApp.settings().get("dontStoreOP3DChartsData");
        boolean bl3 = true;
        if (bl2) {
            if (this.optimizations == null || this.optimizations.size() == 0) {
                return;
            }
            this.recomputeCounts();
            this.sysParamPermutationsTable = null;
            this.getSysParamPermutationsTable();
            this.sysParamPermutationsCharts = null;
            this.getSysParamPermutationsCharts();
            this.getAvailableParams();
            this.profitableOptimizationsJSON = null;
            this.printProfitableOptimizations();
            this.performanceDistributionChart = null;
            this.printPerformanceDistributionChart();
            this.checksObjJSON = null;
            this.printChecksResults(null);
        }
    }

    public void reset() {
        this.lastCount = 0;
        this.profitableOptPct = 0.0;
        this.avgProfit = 0.0;
        this.countTotalOptimizations = 0;
        this.sysParamPermutationsTable = null;
        this.sysParamPermutationsCharts = null;
        this.availableParams = null;
        this.profitableOptimizationsJSON = null;
        this.performanceDistributionChart = null;
    }

    public void clearData() {
        boolean bl;
        String string = MainApp.settings().get("dontStoreOP3DChartsData");
        boolean bl2 = string == null ? false : (bl = !Boolean.parseBoolean(string));
        if (!bl) {
            if (this.optimizations == null || this.optimizations.size() == 0) {
                return;
            }
            this.getSysParamPermutationsTable();
            this.getSysParamPermutationsCharts();
            this.getAvailableParams();
            this.profitableOptimizationsJSON = null;
            this.printProfitableOptimizations();
            this.performanceDistributionChart = null;
            this.printPerformanceDistributionChart();
            this.checksObjJSON = null;
            this.printChecksResults(null);
            this.optimizations.clear();
            this.optimizationKeys.clear();
        }
    }
}

