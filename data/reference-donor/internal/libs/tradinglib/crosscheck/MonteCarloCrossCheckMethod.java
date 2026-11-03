/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  com.strategyquant.lib.L
 *  com.strategyquant.lib.SQUtils
 *  com.strategyquant.lib.SettingsMap
 *  com.strategyquant.lib.XMLUtil
 *  org.jdom2.Content
 *  org.jdom2.Document
 *  org.jdom2.Element
 *  org.jdom2.output.Format
 *  org.jdom2.output.XMLOutputter
 *  org.slf4j.Logger
 *  org.slf4j.LoggerFactory
 */
package com.strategyquant.tradinglib.crosscheck;

import com.strategyquant.lib.L;
import com.strategyquant.lib.SQUtils;
import com.strategyquant.lib.SettingsMap;
import com.strategyquant.lib.XMLUtil;
import com.strategyquant.tradinglib.DatabankColumn;
import com.strategyquant.tradinglib.OrdersList;
import com.strategyquant.tradinglib.Result;
import com.strategyquant.tradinglib.ResultsGroup;
import com.strategyquant.tradinglib.SQStats;
import com.strategyquant.tradinglib.crosscheck.CrossCheckDataNotExistException;
import com.strategyquant.tradinglib.crosscheck.CrossCheckMethod;
import com.strategyquant.tradinglib.crosscheck.MCResultsComputer;
import com.strategyquant.tradinglib.databank.DatabankColumns;
import com.strategyquant.tradinglib.fitnessfunction.IFitnessFunction;
import com.strategyquant.tradinglib.results.SymbolsMap;
import com.strategyquant.tradinglib.robustnesstests.RobustnessOrdersValues;
import com.strategyquant.tradinglib.robustnesstests.RobustnessResultComparator;
import com.strategyquant.tradinglib.robustnesstests.RobustnessResults;
import java.io.BufferedWriter;
import java.io.InputStream;
import java.io.OutputStream;
import java.io.OutputStreamWriter;
import java.io.Writer;
import java.util.ArrayList;
import java.util.Collections;
import java.util.HashMap;
import java.util.List;
import java.util.jar.JarEntry;
import java.util.jar.JarFile;
import java.util.jar.JarOutputStream;
import java.util.zip.ZipEntry;
import org.jdom2.Content;
import org.jdom2.Document;
import org.jdom2.Element;
import org.jdom2.output.Format;
import org.jdom2.output.XMLOutputter;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

public abstract class MonteCarloCrossCheckMethod
extends CrossCheckMethod
implements IFitnessFunction {
    public static final Logger Log = LoggerFactory.getLogger((String)"MonteCarloCrossCheckMethod");
    public static int[] ConfidenceLevels = new int[]{50, 60, 70, 80, 90, 92, 95, 97, 98, 99, 100};
    public static double[] InitialCapitalVariants = new double[]{0.25, 0.5, 0.75, 1.0, 1.25, 1.5, 2.0, 3.0, 4.0, 6.0};
    private String fitnessDatabankColumnName = null;
    private int fitnessConfidenceLevel = 50;

    protected void computeConfidenceLevels(Result result, ArrayList<RobustnessResults> arrayList) {
        List list = DatabankColumns.get().getAvailableClasses();
        HashMap<Integer, SQStats> hashMap = this.createStatsForConfidenceLevels();
        for (DatabankColumn databankColumn : list) {
            byte by = databankColumn.getValueType();
            if (by == 3) {
                by = 1;
            }
            Collections.sort(arrayList, new RobustnessResultComparator(databankColumn));
            for (int n : hashMap.keySet()) {
                int n2 = this.getConfidenceLevelIndex(n, arrayList.size());
                if (n2 < 0) continue;
                RobustnessResults robustnessResults = arrayList.get(n2);
                hashMap.get(n).copyValueFrom(robustnessResults.getOriginalStats(), databankColumn.getStatsValueName());
            }
        }
        result.set(this.getSettingName() + "_ConfidenceLevelsStats", hashMap);
    }

    private int getConfidenceLevelIndex(int n, int n2) {
        int n3 = (int)Math.ceil((double)n2 * ((double)n / 100.0));
        return n3 - 1;
    }

    private HashMap<Integer, SQStats> createStatsForConfidenceLevels() {
        HashMap<Integer, SQStats> hashMap = new HashMap<Integer, SQStats>();
        hashMap.put(50, new SQStats());
        hashMap.put(60, new SQStats());
        hashMap.put(70, new SQStats());
        hashMap.put(80, new SQStats());
        hashMap.put(90, new SQStats());
        hashMap.put(92, new SQStats());
        hashMap.put(95, new SQStats());
        hashMap.put(97, new SQStats());
        hashMap.put(98, new SQStats());
        hashMap.put(99, new SQStats());
        hashMap.put(100, new SQStats());
        return hashMap;
    }

    private boolean isRuined(double d, RobustnessOrdersValues robustnessOrdersValues) {
        double d2 = d;
        int[] nArray = robustnessOrdersValues.arr();
        for (int i = 0; i < nArray.length; ++i) {
            if (!((d2 += (double)nArray[i] / 100.0) <= 0.0)) continue;
            return true;
        }
        return false;
    }

    protected void getOrCreateOriginalOrders(Result result, OrdersList ordersList, String string, SettingsMap settingsMap, SymbolsMap symbolsMap) throws Exception {
        result.set("RobustnessOriginalOrders", ordersList);
        RobustnessResults robustnessResults = MCResultsComputer.computeResults(ordersList, settingsMap, symbolsMap, null);
        result.set("RobustnessOriginalResults", robustnessResults);
    }

    @Override
    public void saveDataToFile(ResultsGroup resultsGroup, JarOutputStream jarOutputStream) throws Exception {
        JarEntry jarEntry;
        int n;
        Element element;
        Object object;
        Object object2;
        Object object3;
        String string = resultsGroup.getMainResultKey();
        Result result = resultsGroup.mainResult();
        int n2 = result.getInt(this.getSettingName() + "_NumberOfSimulations");
        if (n2 == 0) {
            return;
        }
        string = SQUtils.correctResultKeyToDirname((String)string);
        Element element2 = new Element("RobustnessResults");
        element2.addContent((Content)new Element("NumberOfSimulations").addContent("" + n2));
        String string2 = result.getString(this.getSettingName() + "_Symbol");
        if (string2 != null) {
            object3 = result.getString(this.getSettingName() + "_TimeFrame");
            object2 = result.getString(this.getSettingName() + "_DateRange");
            element2.addContent((Content)new Element("Symbol").addContent(string2));
            element2.addContent((Content)new Element("TimeFrame").addContent((String)object3));
            element2.addContent((Content)new Element("DateRange").addContent((String)object2));
            object = (String[])result.get(this.getSettingName() + "_Methods");
            element = new Element("Methods");
            for (n = 0; n < ((String[])object).length; ++n) {
                element.addContent((Content)new Element("Method").setText(object[n]));
            }
            element2.addContent((Content)element);
        }
        if ((object3 = (RobustnessResults)result.get("RobustnessOriginalResults")) != null) {
            object2 = ((RobustnessResults)object3).getXml("RobustnessOriginalResults");
            element2.addContent((Content)object2);
            try {
                jarEntry = new JarEntry("Results/" + string + "/RobustnessOriginalOrders.bin");
                jarOutputStream.putNextEntry(jarEntry);
                ((RobustnessResults)object3).saveOrderValuesToFile(jarOutputStream);
            }
            catch (Exception exception) {
                // empty catch block
            }
            for (int i = 0; i < n2; ++i) {
                object3 = result.getMCSimulation(this.getSettingName(), i);
                if (object3 == null) continue;
                jarEntry = new JarEntry("Results/" + string + "/" + String.format(this.getSettingName() + "_Simulation%dOrders", i) + ".bin");
                jarOutputStream.putNextEntry(jarEntry);
                ((RobustnessResults)object3).saveOrderValuesToFile(jarOutputStream);
            }
        }
        if ((object2 = (HashMap)result.get(this.getSettingName() + "_ConfidenceLevelsStats")) != null) {
            object = new Element("ConfidenceLevelStats");
            element = ((HashMap)object2).keySet().iterator();
            while (element.hasNext()) {
                n = (Integer)element.next();
                SQStats sQStats = (SQStats)((HashMap)object2).get(n);
                Element element3 = new Element("LevelStat");
                element3.setAttribute("level", "" + n);
                element3.addContent((Content)sQStats.getXML());
                object.addContent((Content)element3);
            }
            element2.addContent((Content)object);
        }
        if ((object = (HashMap)result.get(String.format(this.getSettingName() + "_RiskOfRuins%d", 90))) != null) {
            element = new Element("RiskOfRuins");
            for (int n3 : ConfidenceLevels) {
                Element element4 = new Element("ConfidenceLevelStats");
                element4.setAttribute("level", "" + n3);
                object = (HashMap)result.get(String.format(this.getSettingName() + "_RiskOfRuins%d", n3));
                for (double d : InitialCapitalVariants) {
                    Element element5 = new Element("InitialCapitalVariantStats");
                    element5.setAttribute("variant", "" + d);
                    element5.addContent((Content)((SQStats)((HashMap)object).get(d)).getXML());
                    element4.addContent((Content)element5);
                }
                element.addContent((Content)element4);
            }
            element2.addContent((Content)element);
        }
        jarEntry = new JarEntry("Results/" + string + "/" + this.getSettingName() + "_Results.xml");
        jarOutputStream.putNextEntry(jarEntry);
        element = new Document(element2);
        BufferedWriter bufferedWriter = new BufferedWriter(new OutputStreamWriter((OutputStream)jarOutputStream, "UTF8"));
        XMLOutputter xMLOutputter = new XMLOutputter(Format.getPrettyFormat());
        xMLOutputter.output((Document)element, (Writer)bufferedWriter);
    }

    @Override
    public void loadDataFromFile(ResultsGroup resultsGroup, JarFile jarFile) throws Exception {
        Object object;
        Object object2;
        int n;
        Object object3;
        Object object4;
        String string = resultsGroup.getMainResultKey();
        Result result = resultsGroup.mainResult();
        string = SQUtils.correctResultKeyToDirname((String)string);
        JarEntry jarEntry = jarFile.getJarEntry("Results/" + string + "/" + this.getSettingName() + "_Results.xml");
        if (jarEntry == null) {
            return;
        }
        Element element = XMLUtil.readXmlFile((InputStream)jarFile.getInputStream(jarEntry));
        Element element2 = element.getChild("NumberOfSimulations");
        int n2 = Integer.parseInt(element2.getValue());
        if (element.getChild("Symbol") != null) {
            result.set(this.getSettingName() + "_Symbol", element.getChild("Symbol").getText());
            result.set(this.getSettingName() + "_TimeFrame", element.getChild("TimeFrame").getText());
            result.set(this.getSettingName() + "_DateRange", element.getChild("DateRange").getText());
            object4 = element.getChild("Methods").getChildren("Method");
            object3 = new String[object4.size()];
            for (int i = 0; i < object4.size(); ++i) {
                object3[i] = ((Element)object4.get(i)).getText();
            }
            result.set(this.getSettingName() + "_Methods", object3);
        }
        if ((object4 = element.getChild("RobustnessOriginalResults")) != null) {
            object3 = new RobustnessResults(object4.getChild("SQStats"));
            result.set("RobustnessOriginalResults", object3);
            JarEntry jarEntry2 = jarFile.getJarEntry("Results/" + string + "/RobustnessOriginalOrders.bin");
            Object object5 = new RobustnessOrdersValues(jarFile.getInputStream(jarEntry2));
            ((RobustnessResults)object3).setOrdersValues((RobustnessOrdersValues)object5);
            for (n = 0; n < n2; ++n) {
                object2 = jarFile.getJarEntry("Results/" + string + "/" + String.format(this.getSettingName() + "_Simulation%dOrders", n) + ".bin");
                if (object2 == null) continue;
                object5 = new RobustnessOrdersValues(jarFile.getInputStream((ZipEntry)object2));
                object3 = new RobustnessResults();
                ((RobustnessResults)object3).setOrdersValues((RobustnessOrdersValues)object5);
                result.addMCSimulation(this.getSettingName(), (RobustnessResults)object3);
            }
        }
        object3 = new HashMap();
        for (Object object5 : element.getChild("ConfidenceLevelStats").getChildren("LevelStat")) {
            n = Integer.parseInt(object5.getAttributeValue("level"));
            object2 = object5.getChild("SQStats");
            object = new SQStats();
            ((SQStats)object).setFromXML((Element)object2);
            ((HashMap)object3).put(n, object);
        }
        result.set(this.getSettingName() + "_ConfidenceLevelsStats", object3);
        Element element3 = element.getChild("RiskOfRuins");
        if (element3 != null) {
            for (Element element4 : element3.getChildren("ConfidenceLevelStats")) {
                int n3 = Integer.parseInt(element4.getAttributeValue("level"));
                object = new HashMap();
                for (Element element5 : element4.getChildren("InitialCapitalVariantStats")) {
                    double d = Double.parseDouble(element5.getAttributeValue("variant"));
                    Element element6 = element5.getChild("SQStats");
                    SQStats sQStats = new SQStats();
                    sQStats.setFromXML(element6);
                    ((HashMap)object).put(d, sQStats);
                }
                result.set(String.format(this.getSettingName() + "_RiskOfRuins%d", n3), object);
            }
        }
    }

    @Override
    public double computeFitness(ResultsGroup resultsGroup, byte by, byte by2) throws Exception {
        return this.computeFitness(resultsGroup, by, by2, true);
    }

    @Override
    public double computeFitness(ResultsGroup resultsGroup, byte by, byte by2, boolean bl) throws Exception {
        double d;
        Result result = resultsGroup.mainResult();
        DatabankColumn databankColumn = (DatabankColumn)DatabankColumns.get().findClassByName(this.fitnessDatabankColumnName);
        HashMap hashMap = (HashMap)result.get(this.getSettingName() + "_ConfidenceLevelsStats");
        if (hashMap == null) {
            d = databankColumn.getNumericValue(resultsGroup, "Portfolio", by, (byte)10, by2);
        } else {
            SQStats sQStats = (SQStats)hashMap.get(this.fitnessConfidenceLevel);
            d = databankColumn.getNumericValue(sQStats);
        }
        double d2 = databankColumn.transformToFitnessRange(d, 0.0, (byte)0);
        if (d2 < 0.0) {
            d2 = 0.0;
        }
        if (d2 > 1.0) {
            d2 = 1.0;
        }
        return d2;
    }

    @Override
    public String getFitnessKey() {
        return this.getSettingName();
    }

    @Override
    public String getFitnessName() {
        return "Cross check - " + this.getName();
    }

    @Override
    public void initFitnessFromXml(Element element) {
        Element element2 = element.getChild("Ranking");
        this.fitnessDatabankColumnName = element2.getAttributeValue("type");
        if (this.fitnessDatabankColumnName.equals("Other")) {
            this.fitnessDatabankColumnName = element2.getAttributeValue("value");
        }
        this.fitnessConfidenceLevel = XMLUtil.getInt((Element)element, (String)"ConfidenceLevel", (int)50);
    }

    @Override
    public byte getFitnessType() throws Exception {
        if (this.fitnessDatabankColumnName.equals("Weighted")) {
            return 1;
        }
        return ((DatabankColumn)DatabankColumns.get().findClassByName((String)this.fitnessDatabankColumnName)).valueType;
    }

    @Override
    public String getFitnessDatabankColumnName() {
        return this.fitnessDatabankColumnName;
    }

    @Override
    public ArrayList<DatabankColumn> getUsedStatValues() throws Exception {
        throw new Exception(L.t((String)"This fitness method cannot be used in Walk-Forward!", (Object[])new Object[0]));
    }

    @Override
    public double getStatsValue(ResultsGroup resultsGroup, String string, Element element, Object ... objectArray) throws Exception {
        HashMap hashMap = (HashMap)resultsGroup.mainResult().get(this.getSettingName() + "_ConfidenceLevelsStats");
        if (hashMap == null) {
            throw new CrossCheckDataNotExistException(this.getName());
        }
        int n = XMLUtil.getIntAttr((Element)element, (String)"confidenceLevel", (int)60);
        SQStats sQStats = (SQStats)hashMap.get(n);
        DatabankColumn databankColumn = (DatabankColumn)DatabankColumns.get().findClassByName(string);
        return databankColumn.getNumericValue(sQStats);
    }

    @Override
    public boolean hasStatsValue(ResultsGroup resultsGroup, String string, Element element, Object ... objectArray) throws Exception {
        HashMap hashMap = (HashMap)resultsGroup.mainResult().get(this.getSettingName() + "_ConfidenceLevelsStats");
        return hashMap != null;
    }

    @Override
    public String printSpecialValue(ResultsGroup resultsGroup, String string, Element element, Object ... objectArray) throws Exception {
        HashMap hashMap = (HashMap)resultsGroup.mainResult().get(this.getSettingName() + "_ConfidenceLevelsStats");
        if (hashMap == null) {
            throw new CrossCheckDataNotExistException(this.getName());
        }
        DatabankColumn databankColumn = (DatabankColumn)DatabankColumns.get().findClassByName(string);
        return databankColumn.getValue(resultsGroup, resultsGroup.getMainResultKey(), (byte)0, (byte)10, (byte)127);
    }

    @Override
    public String getColumnTitle(String string, Element element, Object ... objectArray) {
        int n = XMLUtil.getIntAttr((Element)element, (String)"confidenceLevel", (int)60);
        String string2 = this.getColumnTitleTemplate();
        string2 = string2.replace("#columnName#", string);
        string2 = string2.replace("#confidenceLevel#", n + "");
        return string2;
    }

    @Override
    public String getColumnTitleTemplate() {
        return "#columnName# (" + this.getShortName() + ", Conf. level #confidenceLevel#%)";
    }

    @Override
    public boolean doesCreateSubjobs() {
        return false;
    }

    @Override
    public IFitnessFunction clone() {
        return this;
    }
}

