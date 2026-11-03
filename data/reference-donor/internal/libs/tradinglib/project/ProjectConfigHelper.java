/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  com.strategyquant.datalib.consts.Precisions
 *  com.strategyquant.datalib.customData.CustomDataInfo
 *  com.strategyquant.datalib.customData.CustomDataManager
 *  com.strategyquant.datalib.data.DataException
 *  com.strategyquant.datalib.session.SessionManager
 *  com.strategyquant.lib.L
 *  com.strategyquant.lib.SQUtils
 *  com.strategyquant.lib.SettingsMap
 *  com.strategyquant.lib.XMLUtil
 *  com.strategyquant.lib.time.SQTimeOld
 *  com.strategyquant.lib.volumeProfile.VolumeProfileBlocks
 *  com.strategyquant.lib.volumeProfile.VolumeProfileSubscription
 *  com.strategyquant.pluginlib.SQPluginManager
 *  org.jdom2.Content
 *  org.jdom2.Element
 *  org.jdom2.JDOMException
 *  org.slf4j.Logger
 *  org.slf4j.LoggerFactory
 */
package com.strategyquant.tradinglib.project;

import com.strategyquant.datalib.consts.Precisions;
import com.strategyquant.datalib.customData.CustomDataInfo;
import com.strategyquant.datalib.customData.CustomDataManager;
import com.strategyquant.datalib.data.DataException;
import com.strategyquant.datalib.session.SessionManager;
import com.strategyquant.lib.L;
import com.strategyquant.lib.SQUtils;
import com.strategyquant.lib.SettingsMap;
import com.strategyquant.lib.XMLUtil;
import com.strategyquant.lib.time.SQTimeOld;
import com.strategyquant.lib.volumeProfile.VolumeProfileBlocks;
import com.strategyquant.lib.volumeProfile.VolumeProfileSubscription;
import com.strategyquant.pluginlib.SQPluginManager;
import com.strategyquant.tradinglib.BadStrategyException;
import com.strategyquant.tradinglib.ChartSetup;
import com.strategyquant.tradinglib.CommissionsMethod;
import com.strategyquant.tradinglib.Databank;
import com.strategyquant.tradinglib.DatabankColumn;
import com.strategyquant.tradinglib.MoneyManagementMethod;
import com.strategyquant.tradinglib.MonteCarloManipulation;
import com.strategyquant.tradinglib.MonteCarloRetest;
import com.strategyquant.tradinglib.ResultTypes;
import com.strategyquant.tradinglib.ResultsGroup;
import com.strategyquant.tradinglib.RiskManagementMethod;
import com.strategyquant.tradinglib.SwapMethod;
import com.strategyquant.tradinglib.WhatIf;
import com.strategyquant.tradinglib.commissions.CommissionsMethodsList;
import com.strategyquant.tradinglib.conditions.ColumnConditionValue;
import com.strategyquant.tradinglib.conditions.Condition;
import com.strategyquant.tradinglib.conditions.IConditionValue;
import com.strategyquant.tradinglib.conditions.NumericValue;
import com.strategyquant.tradinglib.crosscheck.CrossCheckConditionValue;
import com.strategyquant.tradinglib.crosscheck.ICrossCheck;
import com.strategyquant.tradinglib.databank.DatabankColumns;
import com.strategyquant.tradinglib.databank.IDatabankListener;
import com.strategyquant.tradinglib.databank.RecordNotFoundException;
import com.strategyquant.tradinglib.engine.ChartSetups;
import com.strategyquant.tradinglib.exception.StrategyProblem;
import com.strategyquant.tradinglib.fitnessfunction.IFitnessFunction;
import com.strategyquant.tradinglib.moneymanagement.MoneyManagementMethodsList;
import com.strategyquant.tradinglib.montecarlo.manipulation.MonteCarloManipulationList;
import com.strategyquant.tradinglib.montecarlo.retest.MonteCarloRetestList;
import com.strategyquant.tradinglib.optimization.OptimizationSettings;
import com.strategyquant.tradinglib.options.TradingOptions;
import com.strategyquant.tradinglib.options.TradingOptionsList;
import com.strategyquant.tradinglib.project.ProjectEngine;
import com.strategyquant.tradinglib.project.SQProject;
import com.strategyquant.tradinglib.riskmanagement.RiskManagementMethodsList;
import com.strategyquant.tradinglib.robustnesstests.RobustnessTestMethod;
import com.strategyquant.tradinglib.robustnesstests.RobustnessTestMethodsList;
import com.strategyquant.tradinglib.simulator.Engines;
import com.strategyquant.tradinglib.strategy.OutOfSample;
import com.strategyquant.tradinglib.taskImpl.AbstractTask;
import com.strategyquant.tradinglib.taskImpl.ISQTask;
import com.strategyquant.tradinglib.taskImpl.TaskException;
import com.strategyquant.tradinglib.whatif.WhatIfMethodsList;
import java.io.File;
import java.io.IOException;
import java.text.ParseException;
import java.util.ArrayList;
import java.util.ConcurrentModificationException;
import java.util.Iterator;
import java.util.List;
import org.jdom2.Content;
import org.jdom2.Element;
import org.jdom2.JDOMException;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

public class ProjectConfigHelper {
    private static final Logger Log = LoggerFactory.getLogger((String)"ProjectConfigHelper");

    public static ChartSetups getChartSetups(Element element) throws Exception {
        ChartSetups chartSetups = new ChartSetups();
        if (element == null) {
            return null;
        }
        Element element2 = element.getChild("Setups");
        List list = element2.getChildren("Setup");
        for (int i = 0; i < list.size(); ++i) {
            Element element3 = (Element)list.get(i);
            chartSetups.add(ProjectConfigHelper.getChartSetup(element3));
        }
        return chartSetups;
    }

    private static ChartSetup getChartSetup(Element element) throws Exception {
        List list = element.getChildren("Chart");
        Element element2 = (Element)list.get(0);
        String string = XMLUtil.removeXMLCharacters((String)element2.getAttributeValue("symbol"));
        String string2 = element2.getAttributeValue("timeframe");
        long l = SQTimeOld.parseDateToMilis((String)element.getAttributeValue("dateFrom"));
        long l2 = SQTimeOld.parseDateToMilis((String)element.getAttributeValue("dateTo"));
        double d = Double.parseDouble(element2.getAttributeValue("spread"));
        int n = Engines.getEngine(element.getAttributeValue("engine"));
        if (n == -1) {
            throw new Exception(L.t((String)"Trading engine not recognized %d", (Object[])new Object[]{n}));
        }
        if (Engines.isTradestationEngine(n)) {
            if (string2.equals("H1")) {
                string2 = "M60";
            } else if (string2.equals("H2")) {
                string2 = "M120";
            } else if (string2.equals("H4")) {
                string2 = "M240";
            }
        }
        String string3 = "No Session";
        if (Engines.isTradestationEngine(n) && SessionManager.getSession((String)(string3 = element.getAttributeValue("session"))) == null) {
            Log.debug("Session '{}' doesn't exist, using NoSession.", (Object)string3);
            string3 = "No Session";
        }
        ChartSetup chartSetup = null;
        try {
            chartSetup = new ChartSetup(string, string2, l, l2, d, string3);
            chartSetup.setTestPrecision(ProjectConfigHelper.getPrecision(element.getAttributeValue("testPrecision")));
            chartSetup.setCommissionsMethod(ProjectConfigHelper.getCommissionsMethod(element));
        }
        catch (DataException dataException) {
            Log.debug("No data for symbol '{}' found, using first available data", (Object)string);
            chartSetup = ChartSetup.createFirstAvailableData();
            chartSetup.setTestPrecision(ProjectConfigHelper.getPrecision(element.getAttributeValue("testPrecision")));
            chartSetup.setCommissionsMethod(ProjectConfigHelper.getCommissionsMethod(element));
        }
        chartSetup.setBacktestEngine(n);
        if (list.size() > 1) {
            for (int i = 1; i < list.size(); ++i) {
                Element element3 = (Element)list.get(i);
                String string4 = "History";
                String string5 = XMLUtil.removeXMLCharacters((String)element3.getAttributeValue("symbol"));
                String string6 = element3.getAttributeValue("timeframe");
                double d2 = Double.parseDouble(element3.getAttributeValue("spread"));
                string5 = string5.equals("Same as main chart") ? string : string5;
                chartSetup.addChart(string4, string5, string6, d2);
            }
        }
        return chartSetup;
    }

    public static ArrayList<String> getChartSetupValues(Element element, String string) throws Exception {
        ArrayList<String> arrayList = new ArrayList<String>();
        Element element2 = element.getChild("Setups");
        List list = element2.getChildren("Setup");
        for (int i = 0; i < list.size(); ++i) {
            Element element3 = (Element)list.get(i);
            arrayList.add(element3.getAttributeValue(string));
        }
        return arrayList;
    }

    public static ArrayList<CommissionsMethod> getChartSetupCommissions(Element element) throws Exception {
        ArrayList<CommissionsMethod> arrayList = new ArrayList<CommissionsMethod>();
        Element element2 = element.getChild("Setups");
        List list = element2.getChildren("Setup");
        for (int i = 0; i < list.size(); ++i) {
            Element element3 = (Element)list.get(i);
            arrayList.add(ProjectConfigHelper.getCommissionsMethod(element3));
        }
        return arrayList;
    }

    public static ArrayList<SwapMethod> getChartSetupSwaps(Element element) throws Exception {
        ArrayList<SwapMethod> arrayList = new ArrayList<SwapMethod>();
        Element element2 = element.getChild("Setups");
        List list = element2.getChildren("Setup");
        for (int i = 0; i < list.size(); ++i) {
            Element element3 = (Element)list.get(i);
            arrayList.add(ProjectConfigHelper.getSwapMethod(element3));
        }
        return arrayList;
    }

    public static ArrayList<String> getChartSetupMainTestValues(Element element, String string) throws Exception {
        ArrayList<String> arrayList = new ArrayList<String>();
        Element element2 = element.getChild("Setups");
        List list = element2.getChildren("Setup");
        for (int i = 0; i < list.size(); ++i) {
            Element element3 = (Element)list.get(i);
            arrayList.add(element3.getChild("MainTestValues").getAttributeValue(string));
        }
        return arrayList;
    }

    private static int getPrecision(String string) throws Exception {
        try {
            return Precisions.getPrecision((int)Integer.parseInt(string));
        }
        catch (Exception exception) {
            return Precisions.getPrecision((String)string);
        }
    }

    public static MoneyManagementMethod getMoneyManagement(Element element) throws Exception {
        for (Element element2 : element.getChildren("Method")) {
            if (!XMLUtil.elementIs((Element)element2, (String)"use")) continue;
            String string = element2.getAttributeValue("type");
            MoneyManagementMethod moneyManagementMethod = (MoneyManagementMethod)MoneyManagementMethodsList.get().createNew(string);
            if (moneyManagementMethod == null) {
                throw new Exception(L.t((String)"MoneyManagement method with name '%s' doesn't exist.", (Object[])new Object[]{string}));
            }
            moneyManagementMethod.setFromXML(element);
            return moneyManagementMethod;
        }
        throw new Exception(L.t((String)"MoneyManagement method not set.", (Object[])new Object[0]));
    }

    public static RiskManagementMethod getRiskManagement(Element element) throws Exception {
        for (Element element2 : element.getChildren("Method")) {
            if (!XMLUtil.elementIs((Element)element2, (String)"use")) continue;
            String string = element2.getAttributeValue("type");
            RiskManagementMethod riskManagementMethod = (RiskManagementMethod)RiskManagementMethodsList.get().createNew(string);
            if (riskManagementMethod == null) {
                throw new Exception(L.t((String)"RiskManagement method with name '%s' doesn't exist.", (Object[])new Object[]{string}));
            }
            riskManagementMethod.setFromXML(element);
            return riskManagementMethod;
        }
        throw new Exception(L.t((String)"RiskManagement method not set.", (Object[])new Object[0]));
    }

    public static ArrayList<MonteCarloManipulation> getMonteCarloManipulationMethods(Element element) throws Exception {
        ArrayList<MonteCarloManipulation> arrayList = new ArrayList<MonteCarloManipulation>();
        for (Element element2 : element.getChildren("Method")) {
            if (!XMLUtil.elementIs((Element)element2, (String)"use")) continue;
            String string = element2.getAttributeValue("type");
            try {
                MonteCarloManipulation monteCarloManipulation = (MonteCarloManipulation)MonteCarloManipulationList.get().createNew(string);
                monteCarloManipulation.setFromXML(element2);
                arrayList.add(monteCarloManipulation);
            }
            catch (Exception exception) {
                Log.error("Error while loading MonteCarloManipulation method '" + string + "'. " + exception.getMessage(), (Throwable)exception);
                throw new Exception(L.t((String)"Error while loading MonteCarloManipulation method '%s' - %s ", (Object[])new Object[]{string, exception.getMessage()}));
            }
        }
        if (arrayList.size() == 0) {
            throw new Exception(L.t((String)"MonteCarloManipulation method not set.", (Object[])new Object[0]));
        }
        return arrayList;
    }

    public static ArrayList<MonteCarloRetest> getMonteCarloRetestMethods(Element element) throws Exception {
        ArrayList<MonteCarloRetest> arrayList = new ArrayList<MonteCarloRetest>();
        for (Element element2 : element.getChildren("Method")) {
            if (!XMLUtil.elementIs((Element)element2, (String)"use")) continue;
            String string = element2.getAttributeValue("type");
            try {
                MonteCarloRetest monteCarloRetest = (MonteCarloRetest)MonteCarloRetestList.get().createNew(string);
                monteCarloRetest.setFromXML(element2);
                arrayList.add(monteCarloRetest);
            }
            catch (Exception exception) {
                Log.error("Error while loading MonteCarloRetest method '" + string + "'. " + exception.getMessage(), (Throwable)exception);
                throw new Exception(L.t((String)"Error while loading MonteCarloRetest method '%s' - %s.", (Object[])new Object[]{string, exception.getMessage()}));
            }
        }
        if (arrayList.size() == 0) {
            throw new Exception(L.t((String)"MonteCarloRetest method not set.", (Object[])new Object[0]));
        }
        return arrayList;
    }

    public static ArrayList<WhatIf> getWhatIfMethods(Element element) throws Exception {
        ArrayList<WhatIf> arrayList = new ArrayList<WhatIf>();
        for (Element element2 : element.getChildren("Method")) {
            if (!XMLUtil.elementIs((Element)element2, (String)"use")) continue;
            String string = element2.getAttributeValue("type");
            try {
                WhatIf whatIf = (WhatIf)WhatIfMethodsList.get().createNew(string);
                whatIf.setFromXML(element2);
                arrayList.add(whatIf);
            }
            catch (Exception exception) {
                Log.error("Error while loading WhatIf method '" + string + "'. " + exception.getMessage(), (Throwable)exception);
                throw new Exception(L.t((String)"Error while loading WhatIf method '%s' - %s.", (Object[])new Object[]{string, exception.getMessage()}));
            }
        }
        if (arrayList.size() == 0) {
            throw new Exception("WhatIf method not set.");
        }
        return arrayList;
    }

    public static ChartSetups cloneChartSetups(ChartSetups chartSetups) {
        if (chartSetups == null) {
            return null;
        }
        ChartSetups chartSetups2 = new ChartSetups();
        for (ChartSetup chartSetup : chartSetups) {
            chartSetups2.add(chartSetup.getClone());
        }
        return chartSetups2;
    }

    public static ArrayList<Condition> getConditions(Element element) throws Exception {
        ArrayList<Condition> arrayList = new ArrayList<Condition>();
        if (element == null) {
            return arrayList;
        }
        List list = element.getChildren("Condition");
        for (int i = 0; i < list.size(); ++i) {
            Element element2 = (Element)list.get(i);
            try {
                arrayList.add(ProjectConfigHelper.getCondition(element2));
                continue;
            }
            catch (Exception exception) {
                Log.error("Condition #" + i + " - " + exception.getMessage());
            }
        }
        return arrayList;
    }

    public static Condition getCondition(Element element) throws Exception {
        boolean bl = Boolean.parseBoolean(XMLUtil.getAttr((Element)element, (String)"use"));
        Element element2 = element.getChild("Left-Side");
        Element element3 = element.getChild("Right-Side");
        Element element4 = element.getChild("Comparator");
        IConditionValue iConditionValue = ProjectConfigHelper.loadConditionValue(element2);
        IConditionValue iConditionValue2 = ProjectConfigHelper.loadConditionValue(element3);
        String string = element4.getAttributeValue("value");
        return new Condition(bl, iConditionValue, iConditionValue2, string);
    }

    /*
     * Enabled force condition propagation
     * Lifted jumps to return sites
     */
    private static IConditionValue loadConditionValue(Element element) throws Exception {
        if (element == null) {
            return null;
        }
        String string = element.getAttributeValue("valueType");
        IConditionValue iConditionValue = null;
        if (string.equals("numeric")) {
            Element element2 = element.getChild("Numeric-Value");
            if (element2 == null) return null;
            String string2 = XMLUtil.getAttr((Element)element2, (String)"value");
            double d = 0.0;
            try {
                d = Double.parseDouble(string2);
                return new NumericValue(d);
            }
            catch (Exception exception) {
                throw new Exception("Incorrect value '" + string2 + "'");
            }
        }
        Element element3 = element.getChild("Column-Value");
        if (element3 != null) return ProjectConfigHelper.getConditionValue(element3);
        return null;
    }

    public static IConditionValue getConditionValue(Element element) throws Exception {
        try {
            String string = element.getAttributeValue("column");
            if (string == null) {
                string = element.getAttributeValue("class");
            }
            byte by = XMLUtil.getByteAttr((Element)element, (String)"direction", (byte)0);
            byte by2 = XMLUtil.getByteAttr((Element)element, (String)"sampleType", (byte)127);
            byte by3 = XMLUtil.getByteAttr((Element)element, (String)"plType", (byte)10);
            String string2 = XMLUtil.getAttr((Element)element, (String)"resultType", (String)"main");
            int n = 0;
            int n2 = XMLUtil.getIntAttr((Element)element, (String)"pctRatio", (int)0);
            if (n2 > 0) {
                n = n2;
            }
            if (ResultTypes.isCrossCheck(string2)) {
                return new CrossCheckConditionValue(string, string2, n, element);
            }
            DatabankColumn databankColumn = (DatabankColumn)DatabankColumns.get().findClassByName(string);
            return new ColumnConditionValue(databankColumn, string2, by, by3, by2, n);
        }
        catch (Exception exception) {
            Log.error("Error while parsing condition value. " + XMLUtil.elementToString((Element)element), (Throwable)exception);
            throw new Exception("Error while parsing condition value. " + exception.getMessage(), exception);
        }
    }

    public static TradingOptions getOptions(Element element) {
        return TradingOptionsList.getInstance().parseOptionsFromXml(element);
    }

    public static OutOfSample getOOS(Element element) throws ParseException {
        OutOfSample outOfSample = new OutOfSample();
        outOfSample.setFromXML(element);
        return outOfSample;
    }

    public static Databank getOutputDatabank(String string, Element element) throws Exception {
        Iterator iterator;
        Object object;
        Object object2;
        Element element2 = element.getChild("Databanks");
        if (element2 != null) {
            String string2;
            for (Element element3 : element2.getChildren("Databank")) {
                object2 = element3.getAttributeValue("name");
                if (!((String)object2).equals("Output")) continue;
                string2 = element3.getAttributeValue("value");
                object = (Databank)ProjectEngine.get(string).getDatabanks().get(string2);
                if (object == null) continue;
                return object;
            }
            iterator = element2.getChildren("Databank").iterator();
            while (iterator.hasNext()) {
                Element element3;
                element3 = (Element)iterator.next();
                object2 = element3.getAttributeValue("name");
                if (!((String)object2).equals("Target")) continue;
                string2 = element3.getAttributeValue("value");
                object = (Databank)ProjectEngine.get(string).getDatabanks().get(string2);
                if (object == null) continue;
                return object;
            }
        }
        if ((iterator = (Databank)ProjectEngine.get(string).getDatabanks().get("Results")) != null) {
            if (element2 == null) {
                element2 = new Element("Databanks");
                element.addContent((Content)element2);
            }
            boolean bl = false;
            for (String string2 : element2.getChildren("Databank")) {
                object = string2.getAttributeValue("name");
                if (!"Output".equals(object)) continue;
                bl = true;
                break;
            }
            if (!bl) {
                object2 = new Element("Databank");
                object2.setAttribute("label", "Output databank");
                object2.setAttribute("name", "Output");
                object2.setAttribute("value", "Results");
                element2.addContent((Content)object2);
                Log.info("Project '{}' - Missing <Databanks> element in task settings, created default Output=Results", (Object)string);
            }
            return iterator;
        }
        throw new Exception(L.t((String)"No output databank set.", (Object[])new Object[0]));
    }

    public static Databank getInputDatabank(String string, Element element) throws Exception {
        Databank databank;
        String string2;
        String string3;
        Element element2 = XMLUtil.getChildElem((Element)element, (String)"Databanks");
        for (Element element3 : element2.getChildren("Databank")) {
            string3 = element3.getAttributeValue("name");
            if (!string3.equals("Input")) continue;
            string2 = element3.getAttributeValue("value");
            databank = (Databank)ProjectEngine.get(string).getDatabanks().get(string2);
            if (databank == null) continue;
            return databank;
        }
        for (Element element3 : element2.getChildren("Databank")) {
            string3 = element3.getAttributeValue("name");
            if (!string3.equals("Source")) continue;
            string2 = element3.getAttributeValue("value");
            databank = (Databank)ProjectEngine.get(string).getDatabanks().get(string2);
            if (databank == null) continue;
            return databank;
        }
        throw new Exception(L.t((String)"No input databank set.", (Object[])new Object[0]));
    }

    public static Databank getDatabankByType(String string, String string2, Element element) throws Exception {
        Element element2 = XMLUtil.getChildElem((Element)element, (String)"Databanks");
        for (Element element3 : element2.getChildren("Databank")) {
            String string3 = element3.getAttributeValue("name");
            String string4 = element3.getAttributeValue("value");
            if (!string3.equals(string2)) continue;
            return (Databank)ProjectEngine.get(string).getDatabanks().get(string4);
        }
        throw new Exception(L.t((String)"Unknown databank type '%s'", (Object[])new Object[]{string2}));
    }

    public static ISQTask createTask(String string, String string2, String string3) throws Exception {
        for (ISQTask iSQTask : SQPluginManager.getPlugins(ISQTask.class)) {
            if (!iSQTask.getType().equals(string)) continue;
            ISQTask iSQTask2 = iSQTask.clone(string3, null);
            iSQTask2.setCustomName(string2);
            return iSQTask2;
        }
        throw new Exception(L.t((String)"Cannot create task '%s'", (Object[])new Object[]{string}));
    }

    public static Element createTaskElement(String string) throws Exception {
        return new Element("Task").setAttribute("type", string);
    }

    public static String[] getTaskSettings(String string) throws Exception {
        for (ISQTask iSQTask : SQPluginManager.getPlugins(ISQTask.class)) {
            if (!iSQTask.getType().equals(string)) continue;
            return iSQTask.getSettings();
        }
        throw new Exception(L.t((String)"Unknown task type '%s'", (Object[])new Object[]{string}));
    }

    public static ArrayList<RobustnessTestMethod> getRTMethods(Element element) throws Exception {
        ArrayList<RobustnessTestMethod> arrayList = new ArrayList<RobustnessTestMethod>();
        for (Element element2 : element.getChildren("Method")) {
            boolean bl = XMLUtil.elementIs((Element)element2, (String)"use");
            if (!bl) continue;
            String string = element2.getAttributeValue("type");
            RobustnessTestMethod robustnessTestMethod = (RobustnessTestMethod)RobustnessTestMethodsList.get().createNew(string);
            robustnessTestMethod.setFromXML(element2);
            arrayList.add(robustnessTestMethod);
        }
        return arrayList;
    }

    public static Element getTaskConfigByName(Element element, String string) throws Exception {
        Element element2 = element.getChild("Tasks");
        for (Element element3 : element2.getChildren("Task")) {
            String string2 = element3.getAttributeValue("name");
            if (!string2.equals(string)) continue;
            return element3;
        }
        throw new Exception(L.t((String)"Project config doesn't contain task with name '%s'.", (Object[])new Object[]{string}));
    }

    public static Element getTaskConfigByXMLFile(Element element, String string) throws Exception {
        Element element2 = element.getChild("Tasks");
        for (Element element3 : element2.getChildren("Task")) {
            String string2 = element3.getAttributeValue("taskXMLFile");
            if (!string2.equals(string)) continue;
            return element3;
        }
        throw new Exception(L.t((String)"Project config doesn't contain task with taskXMLFile '%s'.", (Object[])new Object[]{string}));
    }

    public static Databank getOutputDatabank(String string, String string2) throws Exception {
        SQProject sQProject = ProjectEngine.get(string);
        Element element = sQProject.getTaskSettingsByName(string2);
        return ProjectConfigHelper.getOutputDatabank(string, element);
    }

    public static void checkAdditionalChartsAndCIndysExpected(String string, Databank databank, ChartSetup chartSetup, ArrayList<String> arrayList) throws TaskException {
        if (databank == null) {
            throw new TaskException(L.t((String)"Additional charts check - Non-existing input Databank", (Object[])new Object[0]));
        }
        int n = 0;
        Iterator<ResultsGroup> iterator = databank.getRecords().iterator();
        try {
            while (iterator.hasNext()) {
                ResultsGroup resultsGroup = iterator.next();
                if (arrayList != null && !arrayList.contains(resultsGroup.getName())) continue;
                n = Math.max(resultsGroup.getChartCount(), n);
                ProjectConfigHelper.checkCustDataIndys(resultsGroup);
            }
        }
        catch (ConcurrentModificationException concurrentModificationException) {
            Log.info("Skipped because of ConcurrentModificationException - not necessary to check now");
        }
        if (n > chartSetup.getChartsCount() - 1) {
            throw new TaskException(9, AbstractTask.formatWSError("Data", null, L.t((String)"Not enough additional charts defined. Some strategies in databank expect at least %d additional chart(s).", (Object[])new Object[]{n})));
        }
    }

    public static void checkAdditionalChartsAndCIndysExpected(String string, ResultsGroup resultsGroup, ChartSetup chartSetup) throws TaskException {
        int n = 0;
        n = Math.max(resultsGroup.getChartCount(), n);
        ProjectConfigHelper.checkCustDataIndys(resultsGroup);
        if (n > chartSetup.getChartsCount() - 1) {
            throw new TaskException(9, AbstractTask.formatWSError("Data", null, L.t((String)"Not enough additional charts defined. Strategy expect at least %d additional chart(s).", (Object[])new Object[]{n})));
        }
    }

    public static void checkCustDataIndys(ResultsGroup resultsGroup) throws TaskException {
        try {
            Element element = resultsGroup.portfolio().getStrategyXml();
            if (element == null) {
                return;
            }
            ProjectConfigHelper.verifyCustDataIndyExists(resultsGroup.getName(), element);
        }
        catch (TaskException taskException) {
            throw taskException;
        }
        catch (Exception exception) {
            Log.error("checkCustDataIndys failes. ", (Throwable)exception);
        }
    }

    public static void checkVolumeProfileBlocksAllowed(Databank databank, ArrayList<String> arrayList) throws TaskException {
        if (databank == null) {
            return;
        }
        if (VolumeProfileSubscription.getInstance().isActive()) {
            return;
        }
        Iterator<ResultsGroup> iterator = databank.getRecords().iterator();
        try {
            while (iterator.hasNext()) {
                ResultsGroup resultsGroup = iterator.next();
                if (arrayList != null && !arrayList.contains(resultsGroup.getName())) continue;
                ProjectConfigHelper.checkVolumeProfileBlocksAllowed(resultsGroup);
            }
        }
        catch (ConcurrentModificationException concurrentModificationException) {
            Log.info("Skipped because of ConcurrentModificationException - not necessary to check now");
        }
    }

    public static void checkVolumeProfileBlocksAllowed(ResultsGroup resultsGroup) throws TaskException {
        if (resultsGroup == null) {
            return;
        }
        if (VolumeProfileSubscription.getInstance().isActive()) {
            return;
        }
        try {
            VolumeProfileBlocks.checkStrategyAllowed((Element)resultsGroup.getStrategyXml(), (String)resultsGroup.getName());
        }
        catch (TaskException taskException) {
            throw taskException;
        }
        catch (Exception exception) {
            throw new TaskException(9, AbstractTask.formatWSError("Data", null, exception.getMessage()));
        }
    }

    private static void verifyCustDataIndyExists(String string, Element element) throws TaskException {
        CustomDataInfo customDataInfo;
        String string2;
        Object object;
        if (element.getName().equals("Item") && (object = element.getAttributeValue("key")) != null && ((String)object).startsWith("CDataIndy") && (string2 = CustomDataManager.getCDataIndyId((String)object)) != null && (customDataInfo = CustomDataManager.getDataInfo((String)string2)) == null) {
            Log.error("Cannot load data info for {}", (Object)string2);
            throw new TaskException(9, AbstractTask.formatWSError("Data", null, "Strategy '" + string + "' uses custom data indicator '" + string2 + "', which doesn't exist in your StrategyQuant installation!"));
        }
        object = element.getChildren();
        if (object != null && object.size() > 0) {
            for (int i = 0; i < object.size(); ++i) {
                customDataInfo = (Element)object.get(i);
                ProjectConfigHelper.verifyCustDataIndyExists(string, (Element)customDataInfo);
            }
        }
    }

    /*
     * WARNING - Removed try catching itself - possible behaviour change.
     */
    public static void delete(final SQProject sQProject, Databank databank, String[] stringArray, String string) throws Exception {
        Object object;
        Object object2;
        Object object3;
        ArrayList<File> arrayList = ProjectConfigHelper.getOptimizationStrategies(sQProject, databank);
        final ArrayList<String> arrayList2 = new ArrayList<String>();
        boolean bl = stringArray.length == databank.size();
        for (int i = 0; i < stringArray.length; ++i) {
            object3 = stringArray[i];
            boolean bl2 = false;
            if (arrayList != null) {
                for (int j = 0; j < arrayList.size(); ++j) {
                    object2 = arrayList.get(j);
                    object = SQUtils.stripExtension((String)((File)object2).getName());
                    if (!((String)object3).equals(object)) continue;
                    bl2 = true;
                    break;
                }
            }
            if (bl2) continue;
            arrayList2.add((String)object3);
        }
        if (stringArray.length == 1 && arrayList2.size() == 0) {
            throw new Exception(L.t((String)"Cannot remove strategy that is selected to be optimized.", (Object[])new Object[0]));
        }
        sQProject.publisher.resetLastData("progress-channel");
        sQProject.getProgress().update("delete", 0.0, null);
        IDatabankListener iDatabankListener = null;
        try {
            iDatabankListener = new IDatabankListener(){
                double count = 0.0;

                @Override
                public void databankChanged(Databank databank) {
                    this.count += 1.0;
                    int n = (int)(this.count / (double)arrayList2.size() * 100.0);
                    sQProject.getProgress().update("delete", n, null);
                }
            };
            databank.addListener(iDatabankListener);
            object3 = new ArrayList();
            for (String string2 : arrayList2) {
                try {
                    databank.remove(string2, true, true, !bl, false, true, string);
                }
                catch (Exception exception) {
                    ((ArrayList)object3).add(string2);
                }
            }
            if (((ArrayList)object3).size() > 0) {
                Thread.sleep(200L);
                boolean bl3 = false;
                Iterator iterator = ((ArrayList)object3).iterator();
                while (iterator.hasNext()) {
                    object2 = (String)iterator.next();
                    if (databank.contains((String)object2)) {
                        try {
                            databank.remove((String)object2, true, !bl, !bl, false, true, string);
                        }
                        catch (RecordNotFoundException recordNotFoundException) {
                        }
                        catch (Exception exception) {
                            bl3 = true;
                        }
                        continue;
                    }
                    object = new File(databank.getDatabankFolder() + "/" + (String)object2 + ".sqx");
                    if (!((File)object).exists() || ((File)object).delete()) continue;
                    bl3 = true;
                }
                databank.updateBestResults();
                if (bl3) {
                    throw new Exception(L.t((String)"Some of the strategies couldn't be deleted.", (Object[])new Object[0]));
                }
            } else {
                databank.updateBestResults();
            }
            if (bl) {
                databank.notifyListeners("cleared");
            }
        }
        finally {
            databank.refreshGrid();
            if (iDatabankListener != null) {
                databank.removeListener(iDatabankListener);
                sQProject.getProgress().update("delete", 100.0, null);
            }
            if (stringArray.length > 1) {
                System.gc();
            }
        }
    }

    public static ArrayList<File> getOptimizationStrategies(SQProject sQProject, Databank databank) {
        ArrayList<File> arrayList = null;
        ArrayList<ISQTask> arrayList2 = sQProject.getTasks();
        for (int i = 0; i < arrayList2.size(); ++i) {
            ISQTask iSQTask = arrayList2.get(i);
            String string = iSQTask.getType();
            String string2 = iSQTask.getName();
            Element element = iSQTask.getConfig();
            if (element == null) {
                Log.warn("Warning! Task '" + string2 + "' from project '" + sQProject.getName() + "' doesn't contain Settings element in its config. ");
                continue;
            }
            Element element2 = element.getChild("Optimization");
            if (string == null || element == null || element2 == null || !string.equals("Optimize")) continue;
            Databank databank2 = null;
            try {
                databank2 = ProjectConfigHelper.getOutputDatabank(sQProject.getName(), element);
            }
            catch (Exception exception) {
                // empty catch block
            }
            if (databank2 == null || !databank2.getName().equals(databank.getName())) continue;
            OptimizationSettings optimizationSettings = new OptimizationSettings(sQProject.getName());
            try {
                optimizationSettings.setFromXML(element, element2);
            }
            catch (Exception exception) {
                continue;
            }
            if (!optimizationSettings.singleStrategy || optimizationSettings.strategyFile == null) continue;
            if (arrayList == null) {
                arrayList = new ArrayList<File>();
            }
            arrayList.add(optimizationSettings.strategyFile);
        }
        return arrayList;
    }

    public static double getChartValue(String string, Element element) {
        Element element2 = (Element)element.getChild("Setups").getChildren().get(0);
        return Double.parseDouble(element2.getAttributeValue(string));
    }

    public static SettingsMap getBuildSettings(Element element) {
        SettingsMap settingsMap = new SettingsMap();
        Element element2 = element.getChild("SLPTOptions");
        if (element2 == null) {
            return null;
        }
        for (Object object : element2.getChildren()) {
            String string = object.getValue();
            if (object.getName().endsWith("ValueType")) continue;
            if (string.equals("true") || string.equals("false")) {
                settingsMap.set(object.getName(), (Object)Boolean.parseBoolean(string));
                continue;
            }
            settingsMap.set(object.getName(), (Object)Double.parseDouble(string));
        }
        Element element3 = element.getChild("BuildTradingOptions");
        if (element3 == null) {
            return null;
        }
        for (String string : element3.getChildren()) {
            String string2 = string.getAttributeValue("key");
            String string3 = string.getValue();
            try {
                if (string3.equals("true") || string3.equals("false")) {
                    settingsMap.set(string2, (Object)Boolean.parseBoolean(string3));
                    continue;
                }
                if (string3.contains(".")) {
                    settingsMap.set(string2, (Object)Double.parseDouble(string3));
                    continue;
                }
                settingsMap.set(string2, (Object)Integer.parseInt(string3));
            }
            catch (NumberFormatException numberFormatException) {
                Log.error("Cannot parse Build Trading option key {}, value {}", (Object)string2, (Object)string3);
            }
        }
        return settingsMap;
    }

    public static int getDismissBadStrategiesSettings(Element element) {
        int n = 0;
        Element element2 = element.getChild("AutomaticDismissal");
        List list = null;
        if (element2 == null) {
            ArrayList<StrategyProblem> arrayList = BadStrategyException.listProblems();
            for (int i = 0; i < arrayList.size(); ++i) {
                n += arrayList.get((int)i).code;
            }
            return n;
        }
        list = element2.getChildren("Problem");
        for (int i = 0; i < list.size(); ++i) {
            Element element3 = (Element)list.get(i);
            if (!XMLUtil.elementIs((Element)element3, (String)"dismiss")) continue;
            String string = element3.getAttributeValue("code");
            int n2 = 0;
            try {
                n2 = Integer.parseInt(string);
            }
            catch (Exception exception) {
                Log.warn("Automatic dismissal settings error - no reason code");
                continue;
            }
            String string2 = BadStrategyException.getExplanation(n2);
            if (!string2.equals(BadStrategyException.ExplanationUnknown)) {
                if (n2 == 0) continue;
                n += n2;
                continue;
            }
            Log.warn("Automatic dismissal settings error - unknown reason code " + n2);
        }
        return n;
    }

    public static boolean getDismissBadStrategiesWarnings(Element element) {
        Element element2 = element.getChild("AutomaticDismissal");
        if (element2 == null) {
            return false;
        }
        String string = element2.getAttributeValue("warnings");
        return string != null && string.equals("true");
    }

    /*
     * WARNING - Removed try catching itself - possible behaviour change.
     */
    public static File getStrategyFile(Databank databank, String string, int n, String string2) {
        String string3;
        if (databank == null) {
            Log.error("Cannot get strategy file. Databank is null");
            return null;
        }
        if (string == null) {
            Log.error("Cannot get strategy file. Strategy name is null");
            return null;
        }
        ResultsGroup resultsGroup = null;
        try {
            resultsGroup = databank.getLocked(string, string2);
            string3 = resultsGroup.getFilePath();
        }
        catch (Exception exception) {
            File file = null;
            return file;
        }
        finally {
            if (resultsGroup != null) {
                resultsGroup.releaseLock(string2);
            }
        }
        File file = new File(string3);
        long l = file.length() / 1024L;
        if (l > (long)n) {
            Log.info("Strategy file not attached - too big (" + l + " kB)");
            return null;
        }
        return file;
    }

    public static CommissionsMethod getCommissionsMethod(Element element) throws Exception {
        Element element2 = element.getChild("Commissions");
        if (element2 != null) {
            List list = element2.getChildren("Method");
            for (int i = 0; i < list.size(); ++i) {
                Element element3 = (Element)list.get(i);
                if (element3.getChild("Params") == null) {
                    element3.addContent((Content)new Element("Params"));
                }
                if (list.size() > 1 && !XMLUtil.elementIs((Element)element3, (String)"use")) continue;
                String string = element3.getAttributeValue("type");
                if (!CommissionsMethodsList.get().checkClassExists(string)) continue;
                CommissionsMethod commissionsMethod = ((CommissionsMethod)CommissionsMethodsList.get().findClassByName(string)).getClone();
                commissionsMethod.setFromXML(element2);
                return commissionsMethod;
            }
            throw new Exception(L.t((String)"No commissions method set.", (Object[])new Object[0]));
        }
        try {
            String string = element.getAttributeValue("commission");
            return CommissionsMethodsList.create("SizeBased", Double.parseDouble(string));
        }
        catch (Exception exception) {
            throw new Exception(L.t((String)"Neither commissions method nor commission price set.", (Object[])new Object[0]));
        }
    }

    public static SwapMethod getSwapMethod(Element element) throws Exception {
        Element element2;
        SwapMethod swapMethod = new SwapMethod();
        if (element != null && (element2 = element.getChild("Swap")) != null) {
            swapMethod.setFromXML(element2);
        }
        return swapMethod;
    }

    public static ArrayList<ICrossCheck> cloneCrossChecks(ArrayList<ICrossCheck> arrayList) {
        if (arrayList == null) {
            return null;
        }
        ArrayList<ICrossCheck> arrayList2 = new ArrayList<ICrossCheck>();
        for (int i = 0; i < arrayList.size(); ++i) {
            arrayList2.add(arrayList.get(i).clone(null));
        }
        return arrayList2;
    }

    public static Element getElCommission(String string, boolean bl) throws IOException, JDOMException {
        String string2 = bl ? "<Setup><Commissions>\n                <Method type=\"PerTrade\" use=\"true\">\n                  <Params>\n                    <Param key=\"Commission\" className=\"PerTrade\">XXXXX</Param>\n                  </Params>\n                </Method>\n              </Commissions></Setup>" : "<Method type=\"PerTrade\" use=\"true\">\n                  <Params>\n                    <Param key=\"Commission\" className=\"PerTrade\">XXXXX</Param>\n                  </Params>\n                </Method>";
        String string3 = string2.replace("XXXXX", string);
        return XMLUtil.stringToElement((String)string3);
    }

    public static IFitnessFunction getFitnessFunction(Element element) throws Exception {
        Element element2 = XMLUtil.getChildElem((Element)element, (String)"FitnessCriteria");
        String string = element2.getAttributeValue("method");
        for (IFitnessFunction iFitnessFunction : SQPluginManager.getPlugins(IFitnessFunction.class)) {
            if (!iFitnessFunction.getFitnessKey().equals(string)) continue;
            iFitnessFunction = iFitnessFunction.clone();
            Element element3 = element2.getChild("Settings");
            if (element3 == null) {
                throw new Exception(L.t((String)"FitnessCriteria - No Settings found for method '%s'", (Object[])new Object[]{string}));
            }
            iFitnessFunction.initFitnessFromXml(element3);
            return iFitnessFunction;
        }
        throw new Exception(L.t((String)"No fitness function plugin of type '%s' found.", (Object[])new Object[]{string}));
    }

    private static void addGoalElement(Element element, String string, double d) {
        Element element2 = new Element("Goal");
        String string2 = ProjectConfigHelper.getElValueTypeForGoal(string);
        if (string2 == null) {
            return;
        }
        element2.setAttribute("use", "true");
        element2.setAttribute("type", string);
        element2.setAttribute("weight", Double.toString(d));
        element2.setAttribute("valueType", string2);
        element2.setAttribute("target", "0");
        element.addContent((Content)element2);
    }

    private static String getElValueTypeForGoal(String string) {
        for (DatabankColumn databankColumn : DatabankColumns.get().getAvailableClasses()) {
            if (!databankColumn.getClassName().equals(string)) continue;
            return Byte.toString(databankColumn.valueType);
        }
        return null;
    }

    public static String getEngineKey(Element element) {
        Object object;
        String string = null;
        try {
            Element element2;
            object = element.getChild("Data");
            if (object == null) {
                object = element.getChild("CustomData");
            }
            if (object != null && (element2 = object.getChild("Setups").getChild("Setup")) != null) {
                string = element2.getAttributeValue("engine");
            }
        }
        catch (Exception exception) {
            Log.error("Failed to parse engine.", (Throwable)exception);
        }
        object = Engines.getEngineKey(string);
        return object;
    }
}

