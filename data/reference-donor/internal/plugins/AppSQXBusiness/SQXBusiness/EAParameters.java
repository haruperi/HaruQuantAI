/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  com.strategyquant.lib.L
 *  com.strategyquant.lib.ValuesMap
 *  com.strategyquant.lib.XMLUtil
 *  com.strategyquant.lib.sqxbusiness.MQLMarketConst
 *  com.strategyquant.pluginlib.program.IProgram
 *  com.strategyquant.pluginlib.program.Program
 *  com.strategyquant.tradinglib.ResultsGroup
 *  com.strategyquant.tradinglib.StrategyBase
 *  org.jdom2.Element
 */
package com.strategyquant.plugin.App.impl.SQXBusiness;

import com.strategyquant.lib.L;
import com.strategyquant.lib.ValuesMap;
import com.strategyquant.lib.XMLUtil;
import com.strategyquant.lib.sqxbusiness.MQLMarketConst;
import com.strategyquant.pluginlib.program.IProgram;
import com.strategyquant.pluginlib.program.Program;
import com.strategyquant.tradinglib.ResultsGroup;
import com.strategyquant.tradinglib.StrategyBase;
import org.jdom2.Element;

public class EAParameters {
    public static ResultsGroup getParametrizedResultsGroup(Element elProject) throws Exception {
        Element elSettings = XMLUtil.getChildElem((Element)elProject, (String)"Settings");
        Element elParameters = XMLUtil.getChildElem((Element)elSettings, (String)"Parameters");
        Element elVariableTypes = XMLUtil.getChildElem((Element)elParameters, (String)"VariableTypes");
        String parametrizationType = XMLUtil.getAttr((Element)elParameters, (String)"parametrizationType", (String)"recommended");
        boolean useRecommended = parametrizationType.equals("recommended");
        boolean symmetric = XMLUtil.getBooleanAttr((Element)elVariableTypes, (String)"symmetric", (boolean)true);
        if (parametrizationType.equals("none")) {
            return EAParameters.getStrategy(elProject);
        }
        ValuesMap paramTypes = new ValuesMap();
        if (useRecommended) {
            paramTypes.set("ParamTypeRecommended", (Object)true);
        } else {
            paramTypes.set("ParamTypePeriod", (Object)XMLUtil.getNodeValue((Element)elVariableTypes, (String)"Periods").equals("true"));
            paramTypes.set("ParamTypeShift", (Object)XMLUtil.getNodeValue((Element)elVariableTypes, (String)"Shifts").equals("true"));
            paramTypes.set("ParamTypeConstant", (Object)XMLUtil.getNodeValue((Element)elVariableTypes, (String)"Constants").equals("true"));
            paramTypes.set("ParamTypeOtherParam", (Object)XMLUtil.getNodeValue((Element)elVariableTypes, (String)"OtherParams").equals("true"));
            paramTypes.set("ParamTypeExitUsed", (Object)XMLUtil.getNodeValue((Element)elVariableTypes, (String)"ExitUsed").equals("true"));
            paramTypes.set("ParamTypeExitUnused", (Object)XMLUtil.getNodeValue((Element)elVariableTypes, (String)"ExitUnused").equals("true"));
            paramTypes.set("ParamTypeBoolean", (Object)XMLUtil.getNodeValue((Element)elVariableTypes, (String)"Boolean").equals("true"));
            paramTypes.set("ParamTypeTradingOptions", (Object)XMLUtil.getNodeValue((Element)elVariableTypes, (String)"TradingOptions", (String)"false").equals("true"));
            paramTypes.set("ParamTypeEntryLevel", (Object)XMLUtil.getNodeValue((Element)elVariableTypes, (String)"Entry", (String)"false").equals("true"));
            paramTypes.set("ParamTypeEntryLogic", (Object)XMLUtil.getNodeValue((Element)elVariableTypes, (String)"EntryLogic", (String)"false").equals("true"));
        }
        ResultsGroup resultsGroup = EAParameters.getStrategy(elProject);
        StrategyBase xmlS = StrategyBase.createXmlStrategy((Element)resultsGroup.getStrategyXml());
        xmlS.transformToVariables(symmetric && xmlS.isSymmetryEnabled(), paramTypes);
        return resultsGroup;
    }

    public static StrategyBase getStrategyBase(Element elProject) throws Exception {
        Element elSettings = XMLUtil.getChildElem((Element)elProject, (String)"Settings");
        Element elParameters = XMLUtil.getChildElem((Element)elSettings, (String)"Parameters");
        Element elVariableTypes = XMLUtil.getChildElem((Element)elParameters, (String)"VariableTypes");
        String parametrizationType = XMLUtil.getAttr((Element)elParameters, (String)"parametrizationType", (String)"recommended");
        boolean useRecommended = parametrizationType.equals("recommended");
        boolean symmetric = XMLUtil.getBooleanAttr((Element)elVariableTypes, (String)"symmetric", (boolean)true);
        if (parametrizationType.equals("none")) {
            return null;
        }
        ValuesMap paramTypes = new ValuesMap();
        if (useRecommended) {
            paramTypes.set("ParamTypeRecommended", (Object)true);
        } else {
            paramTypes.set("ParamTypePeriod", (Object)XMLUtil.getNodeValue((Element)elVariableTypes, (String)"Periods").equals("true"));
            paramTypes.set("ParamTypeShift", (Object)XMLUtil.getNodeValue((Element)elVariableTypes, (String)"Shifts").equals("true"));
            paramTypes.set("ParamTypeConstant", (Object)XMLUtil.getNodeValue((Element)elVariableTypes, (String)"Constants").equals("true"));
            paramTypes.set("ParamTypeOtherParam", (Object)XMLUtil.getNodeValue((Element)elVariableTypes, (String)"OtherParams").equals("true"));
            paramTypes.set("ParamTypeExitUsed", (Object)XMLUtil.getNodeValue((Element)elVariableTypes, (String)"ExitUsed").equals("true"));
            paramTypes.set("ParamTypeExitUnused", (Object)XMLUtil.getNodeValue((Element)elVariableTypes, (String)"ExitUnused").equals("true"));
            paramTypes.set("ParamTypeBoolean", (Object)XMLUtil.getNodeValue((Element)elVariableTypes, (String)"Boolean").equals("true"));
            paramTypes.set("ParamTypeTradingOptions", (Object)XMLUtil.getNodeValue((Element)elVariableTypes, (String)"TradingOptions", (String)"false").equals("true"));
            paramTypes.set("ParamTypeEntryLevel", (Object)XMLUtil.getNodeValue((Element)elVariableTypes, (String)"Entry", (String)"false").equals("true"));
            paramTypes.set("ParamTypeEntryLogic", (Object)XMLUtil.getNodeValue((Element)elVariableTypes, (String)"EntryLogic", (String)"false").equals("true"));
        }
        ResultsGroup resultsGroup = EAParameters.getStrategy(elProject);
        StrategyBase xmlS = StrategyBase.createXmlStrategy((Element)resultsGroup.getStrategyXml());
        xmlS.transformToVariables(symmetric && xmlS.isSymmetryEnabled(), paramTypes);
        return xmlS;
    }

    public static ResultsGroup getStrategy(Element elProject) throws Exception {
        Element elSettings = XMLUtil.getChildElem((Element)elProject, (String)"Settings");
        Element elGeneral = XMLUtil.getChildElem((Element)elSettings, (String)"General");
        String projectName = elGeneral.getAttributeValue("name");
        String strategyFileName = elGeneral.getAttributeValue("strategy");
        String projectFolder = MQLMarketConst.getProjectDirPath((String)projectName);
        String strategyFilePath = projectFolder + "/" + strategyFileName;
        if (strategyFileName == null || strategyFileName.isEmpty()) {
            throw new Exception(L.t((String)"Source strategy not found. Please set it in General settings", (Object[])new Object[0]));
        }
        IProgram loader = Program.get((String)"Loader");
        return (ResultsGroup)loader.call("loadFile", new Object[]{strategyFilePath});
    }
}

