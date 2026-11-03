/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  com.strategyquant.datalib.customData.CustomDataManager
 *  com.strategyquant.gridlib.client.GridClient
 *  com.strategyquant.gridlib.client.SQGrid
 *  com.strategyquant.lib.XMLUtil
 *  com.strategyquant.lib.sqxbusiness.EAOption
 *  com.strategyquant.lib.sqxbusiness.MQLMarketBuildSettings
 *  com.strategyquant.lib.sqxbusiness.MQLMarketConst
 *  com.strategyquant.tradinglib.ResultsGroup
 *  com.strategyquant.tradinglib.blocks.CustomBlocks
 *  com.strategyquant.tradinglib.project.StrategyXMLModifier
 *  com.strategyquant.tradinglib.strategy.SizingMetadata
 *  org.jdom2.Content
 *  org.jdom2.Element
 */
package com.strategyquant.plugin.App.impl.SQXBusiness;

import com.strategyquant.datalib.customData.CustomDataManager;
import com.strategyquant.gridlib.client.GridClient;
import com.strategyquant.gridlib.client.SQGrid;
import com.strategyquant.lib.XMLUtil;
import com.strategyquant.lib.sqxbusiness.EAOption;
import com.strategyquant.lib.sqxbusiness.MQLMarketBuildSettings;
import com.strategyquant.lib.sqxbusiness.MQLMarketConst;
import com.strategyquant.plugin.App.impl.SQXBusiness.EAParameter;
import com.strategyquant.plugin.App.impl.SQXBusiness.EAParameters;
import com.strategyquant.plugin.App.impl.SQXBusiness.MQLMarketBuildJob;
import com.strategyquant.plugin.App.impl.SQXBusiness.SQXBusinessBuildReporter;
import com.strategyquant.tradinglib.ResultsGroup;
import com.strategyquant.tradinglib.blocks.CustomBlocks;
import com.strategyquant.tradinglib.project.StrategyXMLModifier;
import com.strategyquant.tradinglib.strategy.SizingMetadata;
import java.io.Serializable;
import java.util.ArrayList;
import java.util.Comparator;
import java.util.HashMap;
import java.util.List;
import java.util.UUID;
import org.jdom2.Content;
import org.jdom2.Element;

public class MQLMarketBuildExecutor {
    private static final Comparator<Element> variablesComparator = new Comparator<Element>(){

        @Override
        public int compare(Element o1, Element o2) {
            int pos1 = XMLUtil.getIntAttr((Element)o1, (String)"position", (int)0);
            int pos2 = XMLUtil.getIntAttr((Element)o2, (String)"position", (int)0);
            return pos1 - pos2;
        }
    };
    private static GridClient gridClient;
    private static String jobGroupID;

    public static void init() {
        gridClient = SQGrid.getGridClient();
    }

    public static void execute(String projectName, Element elProject, String type, String platform) throws Exception {
        jobGroupID = UUID.randomUUID().toString();
        List<MQLMarketBuildJob> jobs = MQLMarketBuildExecutor.prepareJobs(projectName, elProject, type, platform);
        SQXBusinessBuildReporter.registerMessageListener(jobGroupID);
        gridClient.executeOnGrid(jobGroupID, jobs);
    }

    private static List<MQLMarketBuildJob> prepareJobs(String projectName, Element elProject, String type, String platform) throws Exception {
        boolean buildAll;
        ArrayList<MQLMarketBuildJob> jobs = new ArrayList<MQLMarketBuildJob>();
        ResultsGroup rg = EAParameters.getParametrizedResultsGroup(elProject);
        SizingMetadata sizing = SizingMetadata.resolve((ResultsGroup)rg, (String)projectName);
        Element strategyXML = MQLMarketBuildExecutor.getStrategyXML(elProject, rg);
        CustomDataManager.addCDataIndySourceCodes((Element)strategyXML);
        CustomBlocks.addCBlockSourceCodes((Element)strategyXML);
        Element elSettings = XMLUtil.getChildElem((Element)elProject, (String)"Settings");
        Element elGeneral = XMLUtil.getChildElem((Element)elSettings, (String)"General");
        Element elBuild = XMLUtil.getChildElem((Element)elSettings, (String)"Build");
        Element elEAOptions = elSettings.getChild("EAOptions");
        String outputName = elBuild.getAttributeValue("outputName");
        MQLMarketBuildSettings settings = new MQLMarketBuildSettings();
        settings.projectName = projectName;
        settings.strategyXML = strategyXML;
        settings.orderSizeMultiplier = sizing.orderSizeMultiplier;
        settings.orderSizeStep = sizing.orderSizeStep;
        settings.copyright = elGeneral.getAttributeValue("copyright");
        settings.link = elGeneral.getAttributeValue("link");
        settings.version = elGeneral.getAttributeValue("version");
        settings.comment = elGeneral.getAttributeValue("comment");
        settings.description = elGeneral.getAttributeValue("description");
        settings.eaOptions = new ArrayList();
        if (elEAOptions != null) {
            List options = elEAOptions.getChildren("Option");
            for (int a = 0; a < options.size(); ++a) {
                Element elOption = (Element)options.get(a);
                String name = XMLUtil.getAttr((Element)elOption, (String)"name", (String)"xx");
                String optionType = XMLUtil.getAttr((Element)elOption, (String)"type", (String)"string");
                String value = XMLUtil.getAttr((Element)elOption, (String)"value", (String)"");
                boolean enabled = XMLUtil.getBooleanAttr((Element)elOption, (String)"enabled", (boolean)true);
                settings.eaOptions.add(new EAOption(name, optionType, value, enabled));
            }
        }
        if ((buildAll = type.equals("all")) || type.equals("unlocked")) {
            Element elUnlockedEA = XMLUtil.getChildElem((Element)elBuild, (String)"UnlockedEA");
            if (!buildAll || XMLUtil.getBooleanAttr((Element)elUnlockedEA, (String)"use", (boolean)false)) {
                settings.account = -1;
                settings.demoOnly = false;
                settings.expirationDate = null;
                settings.fixedSize = -1.0;
                MQLMarketBuildExecutor.tryAddJobs(jobs, projectName, outputName, elUnlockedEA, settings, platform);
            }
        }
        if (buildAll || type.equals("lockedToDemo")) {
            Element elLockedToDemo = XMLUtil.getChildElem((Element)elBuild, (String)"LockedToDemo");
            if (!buildAll || XMLUtil.getBooleanAttr((Element)elLockedToDemo, (String)"use", (boolean)false)) {
                settings.account = -1;
                settings.demoOnly = true;
                settings.expirationDate = null;
                settings.fixedSize = -1.0;
                MQLMarketBuildExecutor.tryAddJobs(jobs, projectName, outputName, elLockedToDemo, settings, platform);
            }
        }
        if (buildAll || type.equals("fixedSize")) {
            Element elLockedToFixedSize = XMLUtil.getChildElem((Element)elBuild, (String)"LockedToFixedSize");
            if (!buildAll || XMLUtil.getBooleanAttr((Element)elLockedToFixedSize, (String)"use", (boolean)false)) {
                settings.account = -1;
                settings.demoOnly = false;
                settings.expirationDate = null;
                settings.fixedSize = XMLUtil.getDoubleAttr((Element)elLockedToFixedSize, (String)"lots", (double)0.01);
                MQLMarketBuildExecutor.tryAddJobs(jobs, projectName, outputName, elLockedToFixedSize, settings, platform);
            }
        }
        if (buildAll || type.equals("lockedByDate")) {
            Element elLockedByDate = XMLUtil.getChildElem((Element)elBuild, (String)"LockedByDate");
            if (!buildAll || XMLUtil.getBooleanAttr((Element)elLockedByDate, (String)"use", (boolean)false)) {
                settings.account = -1;
                settings.demoOnly = false;
                settings.expirationDate = elLockedByDate.getAttributeValue("date");
                settings.fixedSize = -1.0;
                MQLMarketBuildExecutor.tryAddJobs(jobs, projectName, outputName, elLockedByDate, settings, platform);
            }
        }
        if (buildAll || type.equals("demoLockedByDate")) {
            Element elLockedByDateDemo = XMLUtil.getChildElem((Element)elBuild, (String)"LockedByDateDemo");
            if (!buildAll || XMLUtil.getBooleanAttr((Element)elLockedByDateDemo, (String)"use", (boolean)false)) {
                settings.account = -1;
                settings.demoOnly = true;
                settings.expirationDate = elLockedByDateDemo.getAttributeValue("date");
                settings.fixedSize = -1.0;
                MQLMarketBuildExecutor.tryAddJobs(jobs, projectName, outputName, elLockedByDateDemo, settings, platform);
            }
        }
        if (buildAll || type.equals("lockedByAccount")) {
            Element elLockedByAccount = XMLUtil.getChildElem((Element)elBuild, (String)"LockedByAccount");
            if (!buildAll || XMLUtil.getBooleanAttr((Element)elLockedByAccount, (String)"use", (boolean)false)) {
                Element elAccounts = XMLUtil.getChildElem((Element)elLockedByAccount, (String)"Accounts");
                List accountElems = elAccounts.getChildren("Account");
                for (int a = 0; a < accountElems.size(); ++a) {
                    Element elAccount = (Element)accountElems.get(a);
                    if (!XMLUtil.getBooleanAttr((Element)elAccount, (String)"use", (boolean)false)) continue;
                    settings.account = XMLUtil.getIntAttr((Element)elAccount, (String)"number", (int)0);
                    settings.demoOnly = XMLUtil.getBooleanAttr((Element)elAccount, (String)"demoOnly", (boolean)false);
                    settings.expirationDate = elAccount.getAttributeValue("validUntil");
                    settings.fixedSize = -1.0;
                    MQLMarketBuildExecutor.tryAddJobs(jobs, projectName, outputName, elAccount, settings, platform);
                }
            }
        }
        return jobs;
    }

    private static void tryAddJobs(List<MQLMarketBuildJob> jobs, String projectName, String baseName, Element settingsElem, MQLMarketBuildSettings settings, String platform) throws Exception {
        String jobID;
        HashMap<String, Serializable> params;
        MQLMarketBuildSettings settingsCloned;
        String outputName = baseName + settingsElem.getAttributeValue("name");
        if (platform.equals("mql4") || platform.equals("mql45")) {
            settingsCloned = settings.clone();
            settingsCloned.platform = "mql4";
            settingsCloned.outputName = outputName;
            params = new HashMap<String, Serializable>();
            params.put("settings", (Serializable)settingsCloned);
            jobID = MQLMarketConst.getBuildJobID((String)projectName, (String)outputName, (boolean)false);
            jobs.add(new MQLMarketBuildJob(jobID, 1, params));
            SQXBusinessBuildReporter.addNewBuildData(projectName, jobGroupID, jobID, outputName, false);
        }
        if (platform.equals("mql5") || platform.equals("mql45")) {
            settingsCloned = settings.clone();
            settingsCloned.platform = "mql5";
            settingsCloned.outputName = outputName;
            params = new HashMap();
            params.put("settings", (Serializable)settingsCloned);
            jobID = MQLMarketConst.getBuildJobID((String)projectName, (String)outputName, (boolean)true);
            jobs.add(new MQLMarketBuildJob(jobID, 1, params));
            SQXBusinessBuildReporter.addNewBuildData(projectName, jobGroupID, jobID, outputName, true);
        }
    }

    private static Element getStrategyXML(Element elProject, ResultsGroup rg) throws Exception {
        Element elStrategyFile = StrategyXMLModifier.getUpdatedStrategyXML((ResultsGroup)rg);
        HashMap<String, EAParameter> eaParams = MQLMarketBuildExecutor.getEAParameters(elProject);
        ArrayList<Element> externalVariables = new ArrayList<Element>();
        Element elStrategy = XMLUtil.getChildElem((Element)elStrategyFile, (String)"Strategy");
        Element elVariables = XMLUtil.getChildElem((Element)elStrategy, (String)"Variables");
        List variableElems = elVariables.getChildren("variable");
        for (int a = variableElems.size() - 1; a >= 0; --a) {
            Element elVariable = (Element)variableElems.get(a);
            String name = elVariable.getChildText("name");
            if (name.equals("MagicNumber")) continue;
            if (eaParams.containsKey(name)) {
                Element elVariableCloned = elVariable.clone();
                EAParameter eaParam = eaParams.get(name);
                XMLUtil.getChildElem((Element)elVariableCloned, (String)"name").setText(eaParam.newName);
                XMLUtil.getChildElem((Element)elVariableCloned, (String)"value").setText(eaParam.value);
                XMLUtil.getChildElem((Element)elVariableCloned, (String)"makeExternal").setText("true");
                elVariableCloned.setAttribute("position", "" + eaParam.position);
                externalVariables.add(elVariableCloned);
                elVariables.removeContent((Content)elVariable);
                continue;
            }
            Element elMakeExternal = XMLUtil.getChildElem((Element)elVariable, (String)"makeExternal");
            elMakeExternal.setText("false");
        }
        int i = 1;
        for (String variableName : eaParams.keySet()) {
            EAParameter eaParam = eaParams.get(variableName);
            if (!eaParam.isCategory) continue;
            Element elVariable = new Element("variable");
            Element elID = new Element("id");
            elID.setText("");
            elVariable.addContent((Content)elID);
            Element elName = new Element("name");
            elName.setText("cat" + i++);
            elVariable.addContent((Content)elName);
            Element elType = new Element("type");
            elType.setText("string");
            elVariable.addContent((Content)elType);
            Element elValue = new Element("value");
            elValue.setText(eaParam.newName);
            elVariable.addContent((Content)elValue);
            Element elMakeExternal = new Element("makeExternal");
            elMakeExternal.setText("true");
            elVariable.addContent((Content)elMakeExternal);
            elVariable.setAttribute("position", "" + eaParam.position);
            externalVariables.add(elVariable);
        }
        externalVariables.sort(variablesComparator);
        for (int a = 0; a < externalVariables.size(); ++a) {
            Element elVariable = (Element)externalVariables.get(a);
            elVariables.addContent((Content)elVariable);
        }
        return elStrategyFile;
    }

    private static HashMap<String, EAParameter> getEAParameters(Element elProject) throws Exception {
        HashMap<String, EAParameter> params = new HashMap<String, EAParameter>();
        Element elSettings = XMLUtil.getChildElem((Element)elProject, (String)"Settings");
        Element elParameters = XMLUtil.getChildElem((Element)elSettings, (String)"Parameters");
        Element elParams = XMLUtil.getChildElem((Element)elParameters, (String)"Params");
        List paramElems = elParams.getChildren("Param");
        for (int a = 0; a < paramElems.size(); ++a) {
            Element elParam = (Element)paramElems.get(a);
            if (!XMLUtil.getBooleanAttr((Element)elParam, (String)"external", (boolean)false)) continue;
            EAParameter param = new EAParameter(elParam);
            params.put(param.originalName, param);
        }
        return params;
    }
}

