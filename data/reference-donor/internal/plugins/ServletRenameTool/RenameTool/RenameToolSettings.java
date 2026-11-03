/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  com.strategyquant.lib.XMLUtil
 *  com.strategyquant.lib.app.MainApp
 *  org.jdom2.Element
 *  org.slf4j.Logger
 *  org.slf4j.LoggerFactory
 */
package com.strategyquant.plugin.Servlet.impl.RenameTool;

import com.strategyquant.lib.XMLUtil;
import com.strategyquant.lib.app.MainApp;
import java.io.File;
import java.util.HashMap;
import java.util.LinkedHashMap;
import java.util.List;
import org.jdom2.Element;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

public class RenameToolSettings {
    private static final Logger Log = LoggerFactory.getLogger(RenameToolSettings.class);
    private static final String configFilePath = MainApp.getDataPath() + "user/settings/RenameToolConfig.xml";
    public static LinkedHashMap<String, String> SN_Markets = new LinkedHashMap();
    public static LinkedHashMap<String, String> SN_TimeFrames = new LinkedHashMap();
    public static LinkedHashMap<String, String> SN_OrderTypes = new LinkedHashMap();
    public static LinkedHashMap<String, String> SN_Indicators = new LinkedHashMap();
    public static LinkedHashMap<String, String> MN_Markets = new LinkedHashMap();
    public static LinkedHashMap<String, String> MN_TimeFrames = new LinkedHashMap();

    public static void load() {
        File configFile = new File(configFilePath);
        if (!configFile.exists()) {
            Log.error("Rename tool config file not found");
            return;
        }
        try {
            Element elConfig = XMLUtil.fileToXmlElement((File)configFile);
            Element elStrategyName = XMLUtil.getChildElem((Element)elConfig, (String)"StrategyName");
            RenameToolSettings.loadValues(elStrategyName, "Markets", SN_Markets);
            RenameToolSettings.loadValues(elStrategyName, "TimeFrames", SN_TimeFrames);
            RenameToolSettings.loadValues(elStrategyName, "OrderTypes", SN_OrderTypes);
            RenameToolSettings.loadValues(elStrategyName, "Indicators", SN_Indicators);
            Element elMagicNumber = XMLUtil.getChildElem((Element)elConfig, (String)"MagicNumber");
            RenameToolSettings.loadValues(elMagicNumber, "Markets", MN_Markets);
            RenameToolSettings.loadValues(elMagicNumber, "TimeFrames", MN_TimeFrames);
        }
        catch (Exception e) {
            Log.error("Loading config failed", (Throwable)e);
        }
    }

    private static void loadValues(Element elParent, String childName, HashMap<String, String> map) throws Exception {
        Element elChild = XMLUtil.getChildElem((Element)elParent, (String)childName);
        List valueElems = elChild.getChildren("Assign");
        for (int a = 0; a < valueElems.size(); ++a) {
            Element elAssign = (Element)valueElems.get(a);
            String originalValue = elAssign.getAttributeValue("value");
            String newValue = elAssign.getTextTrim();
            if (originalValue == null || newValue == null) continue;
            map.put(originalValue, newValue);
        }
    }
}

