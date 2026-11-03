/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  com.strategyquant.datalib.ChartDef
 *  com.strategyquant.datalib.TimeframeManager
 *  com.strategyquant.lib.L
 *  com.strategyquant.lib.SQUtils
 *  com.strategyquant.lib.SettingsMap
 *  com.strategyquant.lib.XMLUtil
 *  com.strategyquant.lib.app.MainApp
 *  com.strategyquant.pluginlib.program.IProgram
 *  com.strategyquant.pluginlib.program.Program
 *  org.jdom2.Content
 *  org.jdom2.Element
 *  org.slf4j.Logger
 *  org.slf4j.LoggerFactory
 */
package com.strategyquant.tradinglib.strategy;

import com.strategyquant.datalib.ChartDef;
import com.strategyquant.datalib.TimeframeManager;
import com.strategyquant.lib.L;
import com.strategyquant.lib.SQUtils;
import com.strategyquant.lib.SettingsMap;
import com.strategyquant.lib.XMLUtil;
import com.strategyquant.lib.app.MainApp;
import com.strategyquant.pluginlib.program.IProgram;
import com.strategyquant.pluginlib.program.Program;
import com.strategyquant.tradinglib.ChartSetup;
import com.strategyquant.tradinglib.MoneyManagementMethod;
import com.strategyquant.tradinglib.ResultsGroup;
import com.strategyquant.tradinglib.StrategyBase;
import com.strategyquant.tradinglib.blocks.CustomBlocks;
import com.strategyquant.tradinglib.engine.ChartSetups;
import com.strategyquant.tradinglib.project.ProjectConfigHelper;
import com.strategyquant.tradinglib.project.SQProject;
import com.strategyquant.tradinglib.project.StrategyXMLModifier;
import java.io.BufferedOutputStream;
import java.io.File;
import java.io.FileOutputStream;
import java.io.InputStream;
import java.io.OutputStream;
import java.util.ArrayList;
import java.util.Arrays;
import java.util.Enumeration;
import java.util.HashMap;
import java.util.List;
import java.util.UUID;
import java.util.jar.JarEntry;
import java.util.jar.JarFile;
import java.util.zip.ZipFile;
import org.jdom2.Content;
import org.jdom2.Element;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

public class StrategyMerger {
    private static final Logger Log = LoggerFactory.getLogger(StrategyMerger.class);
    public static final String PortfolioPartsDir = "PortfolioParts";
    public static final String TempPath = MainApp.getDataPath() + "/internal/tmp/";
    public static final int TempBufferSize = 1024;

    public static ResultsGroup createSimulatedResult(SQProject sQProject, ArrayList<ResultsGroup> arrayList, String string, String string2) throws Exception {
        Element element;
        ResultsGroup resultsGroup = ResultsGroup.merge(arrayList, new String[]{"AdditionalMarket", "CrossCheck_"}, sQProject);
        resultsGroup.setName(string);
        if (sQProject != null) {
            sQProject.getProgress().update("Create Portfolio", -1.0, null, L.t((String)"Creating portfolio result", (Object[])new Object[0]));
        }
        if (arrayList.size() > 0) {
            resultsGroup.createPortfolioResult(string2, sQProject);
        }
        if ((element = resultsGroup.portfolio().getStrategyXml()) != null) {
            element.setAttribute("mergedResult", "true");
        }
        resultsGroup.setLastSettings(arrayList.get(0).getLastSettings());
        StrategyMerger.addStrategyConfigs(resultsGroup, arrayList);
        return resultsGroup;
    }

    public static ResultsGroup createSimulatedResult(SQProject sQProject, ArrayList<ResultsGroup> arrayList, String string, float f, MoneyManagementMethod moneyManagementMethod) throws Exception {
        Element element;
        ResultsGroup resultsGroup = ResultsGroup.merge(arrayList, new String[]{"AdditionalMarket", "CrossCheck_"}, sQProject);
        resultsGroup.setName(string);
        if (sQProject != null) {
            sQProject.getProgress().update("Create Portfolio", -1.0, null, L.t((String)"Creating portfolio result", (Object[])new Object[0]));
        }
        if (arrayList.size() > 0) {
            resultsGroup.createPortfolioResult(sQProject, f, moneyManagementMethod);
        }
        if ((element = resultsGroup.portfolio().getStrategyXml()) != null) {
            element.setAttribute("mergedResult", "true");
        }
        resultsGroup.setLastSettings(arrayList.get(0).getLastSettings());
        StrategyMerger.addStrategyConfigs(resultsGroup, arrayList);
        return resultsGroup;
    }

    public static ResultsGroup createMergedResult(SQProject sQProject, ArrayList<ResultsGroup> arrayList, String string) throws Exception {
        Object object;
        Object object2;
        List list;
        Object object3;
        String string2;
        Object object5;
        Object object6;
        Object object7;
        int n;
        ResultsGroup resultsGroup = new ResultsGroup(string);
        resultsGroup.addSubresult("MergedToOne", new SettingsMap());
        Object object8 = null;
        Element element = null;
        Element element2 = null;
        Element element3 = null;
        Element element4 = null;
        Element element5 = new Element("CustomBlocks");
        int n2 = 11111;
        ArrayList<Integer> arrayList2 = new ArrayList<Integer>();
        ArrayList<String> arrayList3 = new ArrayList<String>();
        ArrayList<String> arrayList4 = new ArrayList<String>();
        ArrayList<String> arrayList5 = new ArrayList<String>();
        String string3 = "";
        for (n = 0; n < arrayList.size(); ++n) {
            String string4;
            ChartDef chartDef;
            Object object4;
            List<ChartSetup> list2;
            object7 = StrategyXMLModifier.getUpdatedStrategyXML(arrayList.get(n)).clone();
            object6 = StrategyBase.createXmlStrategy(object7);
            ((StrategyBase)object6).transformToNumbers();
            object5 = StrategyMerger.generateUniqueVariableIDs(object7);
            string2 = XMLUtil.elementToString((Element)object7);
            for (String string5 : ((HashMap)object5).keySet()) {
                string2 = string2.replace(">" + string5 + "<", ">" + (String)((HashMap)object5).get(string5) + "<").replace("variable=\"" + string5 + "\"", "variable=\"" + (String)((HashMap)object5).get(string5) + "\"");
                string2 = string2.replace("<name>" + (String)((HashMap)object5).get(string5) + "</name>", "<name>" + string5 + "</name>");
            }
            object7 = XMLUtil.stringToElement((String)string2);
            object3 = null;
            try {
                String string6 = arrayList.get(n).getLastSettings();
                Element element6 = XMLUtil.stringToElement((String)string6);
                Element element7 = element6.getChild("Data").getChild("Setups").getChild("Setup");
                list = element7.getChildren("Chart");
                object2 = ((Element)list.get(0)).clone();
                object2.setAttribute("timeframe", "0");
                object2.setAttribute("spread", "0");
                list.add(0, object2);
                object = (Element)list.get(1);
                object.setAttribute("symbol", "Same as main chart");
                if (n == 0) {
                    string3 = XMLUtil.elementToString((Element)element6);
                }
                list2 = ProjectConfigHelper.getChartSetups(element6.getChild("Data"));
                object4 = ((ChartSetups)list2).getMainSetup();
                chartDef = ((ChartSetup)object4).getMainChart();
                object3 = chartDef.getSymbol() + "/" + TimeframeManager.translateToMTConstant((String)chartDef.getTimeframe());
                if (element4 == null) {
                    try {
                        element4 = element6.getChild("Options").getChild("BuildTradingOptions").clone();
                        element4.setName("TradingOptions");
                    }
                    catch (Exception exception) {}
                }
            }
            catch (Exception exception) {
                throw new Exception("Cannot parse strategies last settings. Please make sure all of the selected strategies are backtested");
            }
            HashMap<Integer, Integer> object42 = StrategyMerger.generateUniqueCharts(object7, (String)object3, arrayList4, arrayList5);
            int n3 = string2.indexOf("key=\"#Chart#\"", 0);
            while (n3 > 0) {
                int n4 = string2.indexOf(">", n3) + 1;
                int n5 = string2.indexOf("<", n4);
                int n6 = 0;
                try {
                    n6 = Integer.parseInt(string2.substring(n4, n5));
                }
                catch (Exception exception) {
                    // empty catch block
                }
                string2 = string2.substring(0, n4) + object42.get(n6) + string2.substring(n5);
                n3 = string2.indexOf("key=\"#Chart#\"", n5);
            }
            int n7 = object42.get(0);
            n3 = string2.indexOf("key=\"#Symbol#\"", 0);
            while (n3 > 0) {
                int n8 = string2.indexOf(">", n3) + 1;
                int n9 = string2.indexOf("<", n3);
                string2 = string2.substring(0, n8) + "Subchart" + n7 + "Symbol" + string2.substring(n9);
                n3 = string2.indexOf("key=\"#Symbol#\"", n9);
            }
            object7 = XMLUtil.stringToElement((String)string2);
            if (n == 0) {
                object8 = object7;
                element = StrategyMerger.getOBUElement(object8);
                element2 = object8.getChild("Strategy").getChild("Variables");
                element3 = object8.getChild("Strategy").getChild("Datas");
                list = StrategyMerger.processCustomComments(arrayList.get(n), object7, n);
                element2.addContent((Content)list);
            } else {
                list = StrategyMerger.processCustomComments(arrayList.get(n), object7, n);
                element2.addContent((Content)list);
                object2 = StrategyMerger.getOBUElement(object7);
                object = object2.getChildren("Rule");
                for (int i = 0; i < object.size(); ++i) {
                    object4 = ((Element)object.get(i)).clone();
                    object4.setAttribute("name", object4.getAttributeValue("name") + (n + 1));
                    element.addContent((Content)object4);
                }
            }
            list = object7.getChild("Strategy").getChild("Variables");
            object2 = list.getChildren("variable");
            for (int i = 0; i < object2.size(); ++i) {
                list2 = ((Element)object2.get(i)).clone();
                object4 = list2.getChildText("name");
                if (((String)object4).equals("MagicNumber")) {
                    int n10 = -1;
                    try {
                        n10 = Integer.parseInt(list2.getChild("value").getText());
                    }
                    catch (Exception exception) {
                        // empty catch block
                    }
                    if (arrayList2.contains(n10) || n10 <= 0) {
                        n10 = n2;
                    }
                    if (n10 == n2) {
                        ++n2;
                    }
                    list2.getChild("value").setText("" + n10);
                    arrayList2.add(n10);
                } else if (((String)object4).startsWith("CustomComment") && (chartDef = list2.getChild("value")) != null && (string4 = chartDef.getText()) != null && string4.length() > 30) {
                    chartDef.setText(string4.substring(0, 30));
                }
                if (n <= 0) continue;
                list2.getChild("name").setText(list2.getChildText("name") + (n + 1));
                element2.addContent(list2);
            }
            object = object7.getChild("Strategy").getChild("CustomBlocks");
            if (object == null) continue;
            list2 = object.getChildren("Item");
            for (int i = 0; i < list2.size(); ++i) {
                chartDef = (Element)list2.get(i);
                string4 = chartDef.getAttributeValue("key");
                if (string4 == null || arrayList3.contains(string4)) continue;
                element5.addContent((Content)chartDef.clone());
                arrayList3.add(string4);
            }
        }
        element3.removeContent();
        for (n = -1; n < arrayList4.size(); ++n) {
            object7 = "" + (n + 1);
            object6 = "Main chart";
            object5 = "NULL";
            string2 = "0";
            object3 = "1.0E-4";
            if (n >= 0) {
                String string7 = (String)arrayList4.get(n);
                int n11 = string7.lastIndexOf("/");
                object6 = "SubChart " + (n + 1);
                object5 = string7.substring(0, n11);
                string2 = string7.substring(n11 + 1);
                object3 = (String)arrayList5.get(n);
            }
            Element element8 = new Element("data");
            Element element9 = new Element("id");
            element9.setText((String)object7);
            Element element10 = new Element("chart");
            element10.setText((String)object6);
            list = new Element("symbol");
            list.setText((String)object5);
            object2 = new Element("timeFrame");
            object2.setText(string2);
            object = new Element("ticksize");
            object.setText((String)object3);
            element8.addContent((Content)element9);
            element8.addContent((Content)element10);
            element8.addContent((Content)list);
            element8.addContent((Content)object2);
            element8.addContent((Content)object);
            element3.addContent((Content)element8);
        }
        if (element4 != null) {
            object8.removeChild("TradingOptions");
            object8.addContent(element4);
        }
        Element element10 = object8.getChild("Strategy");
        element10.removeChild("CustomBlocks");
        element10.addContent((Content)element5);
        CustomBlocks.addCBlockSourceCodes(object8);
        resultsGroup.portfolio().addStrategyXml((Element)object8);
        resultsGroup.setLastSettings(string3);
        StrategyMerger.addStrategyConfigs(resultsGroup, arrayList);
        return resultsGroup;
    }

    private static Element getOBUElement(Element element) {
        Element element2 = element.getChild("Strategy").getChild("Rules").getChild("Events");
        List list = element2.getChildren("Event");
        for (int i = 0; i < list.size(); ++i) {
            if (!((Element)list.get(i)).getAttributeValue("key").equals("OnBarUpdate")) continue;
            return (Element)list.get(i);
        }
        return null;
    }

    private static HashMap<String, String> generateUniqueVariableIDs(Element element) {
        HashMap<String, String> hashMap = new HashMap<String, String>();
        Element element2 = element.getChild("Strategy").getChild("Variables");
        List list = element2.getChildren("variable");
        for (int i = 0; i < list.size(); ++i) {
            Element element3 = (Element)list.get(i);
            hashMap.put(element3.getChildText("id"), UUID.randomUUID().toString());
        }
        return hashMap;
    }

    private static HashMap<Integer, Integer> generateUniqueCharts(Element element, String string, ArrayList<String> arrayList, ArrayList<String> arrayList2) {
        HashMap<Integer, Integer> hashMap = new HashMap<Integer, Integer>();
        Element element2 = element.getChild("Strategy").getChild("Datas");
        List list = element2.getChildren("data");
        for (int i = 0; i < list.size(); ++i) {
            Element element3 = (Element)list.get(i);
            String string2 = element3.getChildText("symbol");
            String string3 = element3.getChildText("timeFrame");
            String string4 = element3.getChildText("ticksize");
            String string5 = i == 0 ? string : string2 + "/" + string3;
            int n = -1;
            for (int j = 0; j < arrayList.size(); ++j) {
                if (!arrayList.get(j).equals(string5)) continue;
                n = j;
                break;
            }
            if (n < 0) {
                n = arrayList.size();
                arrayList.add(string5);
                arrayList2.add(string4);
            }
            hashMap.put(i, n + 1);
        }
        return hashMap;
    }

    public static ResultsGroup createFuzzyResult(SQProject sQProject, ArrayList<ResultsGroup> arrayList, String string, int n, String string2) throws Exception {
        Element element;
        List list;
        Object object;
        Object object2;
        Element element2;
        Object object3;
        Element element3;
        String string3;
        ResultsGroup resultsGroup = new ResultsGroup(string);
        resultsGroup.addSubresult("EnsembleStrategy", new SettingsMap());
        ResultsGroup resultsGroup2 = null;
        Element element4 = null;
        for (int i = 0; i < arrayList.size(); ++i) {
            if (!arrayList.get(i).getName().equals(string2)) continue;
            resultsGroup2 = arrayList.get(i);
            element4 = arrayList.get(i).getStrategyXml().clone();
            try {
                string3 = resultsGroup2.getLastSettings();
                if (string3 == null) {
                    Log.info("Signal strategy doesn't contain last settings - trading options not set");
                    break;
                }
                element3 = XMLUtil.stringToElement((String)string3).getChild("Options").getChild("BuildTradingOptions").clone();
                element3.setName("TradingOptions");
                element4.removeChild("TradingOptions");
                element4.addContent((Content)element3);
            }
            catch (Exception exception) {
                Log.error("Unable to set trading options into XML", (Throwable)exception);
            }
            break;
        }
        if (element4 == null) {
            throw new Exception(L.tsq((String)"Selected signals strategy not found"));
        }
        Element element5 = StrategyMerger.getOBUElement(element4);
        string3 = null;
        element3 = null;
        Element element6 = null;
        Element element7 = null;
        Element element8 = new Element("CustomBlocks");
        ArrayList<String> arrayList2 = new ArrayList<String>();
        List list2 = element5.getChildren("Rule");
        ArrayList<String> arrayList3 = new ArrayList<String>(Arrays.asList("Long entry", "Short entry", "Long exit", "Short exit"));
        for (int i = 0; i < list2.size(); ++i) {
            Element element9 = (Element)list2.get(i);
            object3 = element9.getAttributeValue("name");
            if (((String)object3).equals("Trading signals")) {
                element9.setAttribute("type", "SignalFuzzy");
                element2 = element9.getChild("signals");
                object2 = element2.getChildren("signal");
                for (int j = 0; j < object2.size(); ++j) {
                    Element element10 = (Element)object2.get(j);
                    object = element10.getAttributeValue("variable");
                    element10.setAttribute("minTrue", "" + n);
                    if (((String)object).equals("33333333-1111-1111-3333-333333333333")) {
                        string3 = element10;
                        continue;
                    }
                    if (((String)object).equals("33333333-2222-1111-3333-333333333333")) {
                        element3 = element10;
                        continue;
                    }
                    if (((String)object).equals("33333333-1111-2222-3333-333333333333")) {
                        element6 = element10;
                        continue;
                    }
                    if (!((String)object).equals("33333333-2222-2222-3333-333333333333")) continue;
                    element7 = element10;
                }
                continue;
            }
            if (!arrayList3.contains(object3)) continue;
            arrayList3.remove(object3);
        }
        if (arrayList3.size() != 0) {
            throw new Exception("Signals strategy doesn't contain all expected rules (Long entry, Short entry, Long exit, Short exit)");
        }
        ArrayList<String> arrayList4 = new ArrayList<String>();
        for (int i = 0; i < arrayList.size(); ++i) {
            try {
                object3 = arrayList.get(i).getStrategyXml().clone();
                element2 = object3.getChild("Strategy").getChild("CustomBlocks");
                if (element2 != null) {
                    object2 = element2.getChildren("Item");
                    for (int j = 0; j < object2.size(); ++j) {
                        Element element11 = (Element)object2.get(j);
                        object = element11.getAttributeValue("key");
                        if (object == null || arrayList2.contains(object)) continue;
                        element8.addContent((Content)element11.clone());
                        arrayList2.add((String)object);
                    }
                }
                if (arrayList.get(i).getName().equals(string2)) continue;
                object2 = StrategyMerger.getOBUElement((Element)object3);
                List list3 = object2.getChild("Rule").getChild("signals").getChildren("signal");
                for (int j = 0; j < list3.size(); ++j) {
                    object = (Element)list3.get(j);
                    String string4 = object.getAttributeValue("variable");
                    list = object.getChildren();
                    if (list.size() == 0) continue;
                    StrategyMerger.processElement((Element)object.getChildren().get(0), arrayList4, i);
                    if (string4.equals("33333333-1111-1111-3333-333333333333")) {
                        if (string3 == null) continue;
                        string3.addContent((Content)((Element)object.getChildren().get(0)).clone());
                        continue;
                    }
                    if (string4.equals("33333333-2222-1111-3333-333333333333")) {
                        if (element3 == null) continue;
                        element3.addContent((Content)((Element)object.getChildren().get(0)).clone());
                        continue;
                    }
                    if (string4.equals("33333333-1111-2222-3333-333333333333")) {
                        if (element6 == null) continue;
                        element6.addContent((Content)((Element)object.getChildren().get(0)).clone());
                        continue;
                    }
                    if (!string4.equals("33333333-2222-2222-3333-333333333333") || element7 == null) continue;
                    element7.addContent((Content)((Element)object.getChildren().get(0)).clone());
                }
                continue;
            }
            catch (Exception exception) {
                throw new Exception("Cannot find signals definition of strategy '" + arrayList.get(i).getName() + "'");
            }
        }
        Element element12 = element4.getChild("Strategy").getChild("Variables");
        object3 = element12.getChildren();
        element2 = new Element("Variables");
        object2 = object3.iterator();
        while (object2.hasNext()) {
            Element element13 = (Element)object2.next();
            element2.addContent((Content)element13.clone());
        }
        try {
            for (int i = 0; i < arrayList.size(); ++i) {
                Element element14 = arrayList.get(i).getStrategyXml().clone();
                if (arrayList.get(i).getName().equals(string2)) continue;
                Element element15 = element14.getChild("Strategy").getChild("Variables");
                object = element15.getChildren("variable");
                for (int j = 0; j < object.size(); ++j) {
                    String string5;
                    list = ((Element)object.get(j)).clone();
                    String string6 = list.getChildText("id");
                    if (!arrayList4.contains(string6 + "St" + String.valueOf(i))) continue;
                    Element element16 = list.getChild("id");
                    if (element16 != null) {
                        element16.removeAttribute("variable");
                        string5 = list.getChildText("id") + "St" + String.valueOf(i);
                        element16.setText(string5);
                    } else {
                        element16 = new Element("id");
                        element16.removeAttribute("variable");
                        element16.setText(list.getChildText("id") + "St" + String.valueOf(i));
                        list.addContent((Content)element16);
                    }
                    string5 = list.getChild("name");
                    if (string5 != null) {
                        string5.removeAttribute("variable");
                        String string7 = list.getChildText("name") + "St" + String.valueOf(i);
                        string5.setText(string7);
                    } else {
                        string5 = new Element("id");
                        string5.removeAttribute("variable");
                        string5.setText(list.getChildText("name") + "St" + String.valueOf(i));
                        list.addContent((Content)string5);
                    }
                    XMLUtil.xmlToFile((Element)list, (File)new File(MainApp.getDataPath() + "tests/tmp/elVariable.xml"));
                    element2.addContent((Content)list);
                }
            }
            element = element12.getParentElement();
            int n2 = element.indexOf((Content)element12);
            element.setContent(n2, (Content)element2);
        }
        catch (Exception exception) {
            throw new Exception("Cannot find variables of a strategy");
        }
        element = element4.getChild("Strategy");
        element.removeChild("CustomBlocks");
        element.addContent((Content)element8);
        CustomBlocks.addCBlockSourceCodes(element4);
        resultsGroup.portfolio().addStrategyXml(element4);
        resultsGroup.setLastSettings(resultsGroup2.getLastSettings());
        StrategyMerger.addStrategyConfigs(resultsGroup, arrayList);
        return resultsGroup;
    }

    private static void processElement(Element element, List<String> list, int n) {
        Object object;
        Object object2;
        if ("Param".equals(element.getName()) && (object2 = element.getAttributeValue("variable")) != null && ((String)object2).equals("true") && (object = element.getText() + "St" + String.valueOf(n)) != null) {
            element.setText((String)object);
            list.add((String)object);
        }
        object2 = element.getChildren();
        object = object2.iterator();
        while (object.hasNext()) {
            Element element2 = (Element)object.next();
            StrategyMerger.processElement(element2, list, n);
        }
    }

    public static List<ResultsGroup> getSplitResults(ResultsGroup resultsGroup) {
        List<ResultsGroup> list = resultsGroup.getMergedResults();
        if (list == null) {
            list = StrategyMerger.loadSplitResultsFromSource(resultsGroup.getFilePath());
        }
        return list;
    }

    /*
     * WARNING - Removed try catching itself - possible behaviour change.
     */
    public static List<ResultsGroup> loadSplitResultsFromSource(String string) {
        ArrayList<ResultsGroup> arrayList;
        block31: {
            arrayList = new ArrayList<ResultsGroup>();
            ZipFile zipFile = null;
            IProgram iProgram = null;
            try {
                iProgram = Program.get((String)"Loader");
                File file = new File(string);
                if (!file.exists()) break block31;
                zipFile = new JarFile(file);
                Enumeration<JarEntry> enumeration = ((JarFile)zipFile).entries();
                while (enumeration.hasMoreElements()) {
                    String string2;
                    JarEntry jarEntry = enumeration.nextElement();
                    if (jarEntry.isDirectory() || !(string2 = jarEntry.getName()).startsWith(PortfolioPartsDir)) continue;
                    File file2 = new File(TempPath + UUID.randomUUID() + ".sqx");
                    String string3 = SQUtils.stripExtension((String)new File(string2).getName());
                    try {
                        Object object;
                        InputStream inputStream = null;
                        OutputStream outputStream = null;
                        try {
                            int n;
                            inputStream = ((JarFile)zipFile).getInputStream(jarEntry);
                            if (!file2.exists() && file2.getParentFile() != null) {
                                file2.getParentFile().mkdirs();
                            }
                            outputStream = new BufferedOutputStream(new FileOutputStream(file2));
                            object = new byte[1024];
                            while ((n = inputStream.read((byte[])object)) != -1) {
                                outputStream.write((byte[])object, 0, n);
                            }
                        }
                        finally {
                            if (inputStream != null) {
                                inputStream.close();
                            }
                            if (outputStream != null) {
                                outputStream.close();
                            }
                        }
                        object = (ResultsGroup)iProgram.call("loadFile", new Object[]{file2.getAbsolutePath()});
                        ((ResultsGroup)object).setName(string3);
                        arrayList.add((ResultsGroup)object);
                    }
                    catch (Exception exception) {
                        Log.error("Loading split strategy '" + string3 + "' from portfolio failed", (Throwable)exception);
                    }
                    finally {
                        try {
                            file2.delete();
                        }
                        catch (Exception exception) {
                            Log.error("Error while deleting temp file", (Throwable)exception);
                        }
                    }
                }
            }
            catch (Exception exception) {
                Log.error("Can't get merged results from portfolio", (Throwable)exception);
            }
            finally {
                if (zipFile != null) {
                    try {
                        zipFile.close();
                    }
                    catch (Exception exception) {
                        Log.error("Unable to close jarFile", (Throwable)exception);
                    }
                }
            }
        }
        return arrayList;
    }

    private static void addStrategyConfigs(ResultsGroup resultsGroup, ArrayList<ResultsGroup> arrayList) throws Exception {
        resultsGroup.setMergedResults(arrayList);
    }

    private static Element processCustomComments(ResultsGroup resultsGroup, Element element, int n) throws Exception {
        Element element2;
        ArrayList arrayList = XMLUtil.getNestedElements((Element)element, (String)"Param", (String)"key", (String)"#Comment#");
        String string = "CustomComment" + (n > 0 ? Integer.valueOf(n + 1) : "");
        for (int i = 0; i < arrayList.size(); ++i) {
            element2 = (Element)arrayList.get(i);
            if (!XMLUtil.elementIsNot((Element)element2, (String)"variable")) continue;
            element2.setAttribute("variable", "true");
            element2.setAttribute("variableType", "STRING");
            element2.setText(string);
        }
        Element element3 = new Element("variable");
        element2 = new Element("id");
        element2.setText(string);
        element3.addContent((Content)element2);
        Element element4 = new Element("name");
        element4.setText(string);
        element3.addContent((Content)element4);
        Element element5 = new Element("type");
        element5.setText("string");
        element3.addContent((Content)element5);
        String string2 = resultsGroup.getName().replace("Optimized", "Opt.").replace("Optimization", "Opt.");
        string2 = string2.length() > 30 ? string2.substring(0, 30) : string2;
        Element element6 = new Element("value");
        element6.setText(string2);
        element3.addContent((Content)element6);
        Element element7 = new Element("makeExternal");
        element7.setText("true");
        element3.addContent((Content)element7);
        return element3;
    }

    public static ResultsGroup createSimulatedWFResult(SQProject sQProject, ArrayList<ResultsGroup> arrayList, String string) throws Exception {
        Element element;
        ResultsGroup resultsGroup = ResultsGroup.mergeWF(arrayList, new String[]{"AdditionalMarket"}, sQProject);
        resultsGroup.setName(string);
        sQProject.getProgress().update("Create Portfolio", -1.0, null, L.t((String)"Creating portfolio result", (Object[])new Object[0]));
        if (arrayList.size() > 0) {
            resultsGroup.createPortfolioResult("sum", sQProject);
        }
        if ((element = resultsGroup.portfolio().getStrategyXml()) != null) {
            element.setAttribute("mergedResult", "true");
        }
        resultsGroup.setLastSettings(arrayList.get(0).getLastSettings());
        StrategyMerger.addStrategyConfigs(resultsGroup, arrayList);
        return resultsGroup;
    }
}

