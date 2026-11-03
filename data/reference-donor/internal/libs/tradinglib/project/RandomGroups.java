/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  com.strategyquant.lib.SQUtils
 *  com.strategyquant.lib.XMLUtil
 *  com.strategyquant.lib.constants.SQPaths
 *  org.jdom2.Element
 *  org.json.JSONArray
 *  org.slf4j.Logger
 *  org.slf4j.LoggerFactory
 */
package com.strategyquant.tradinglib.project;

import com.strategyquant.lib.SQUtils;
import com.strategyquant.lib.XMLUtil;
import com.strategyquant.lib.constants.SQPaths;
import java.io.File;
import java.util.List;
import org.jdom2.Element;
import org.json.JSONArray;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

public class RandomGroups {
    private static final Logger Log = LoggerFactory.getLogger(RandomGroups.class);

    public static Element getXml() {
        Element element = new Element("Groups");
        try {
            File file = new File(SQPaths.algoWizardBlockGroupsPath);
            if (file.exists()) {
                Element element2 = XMLUtil.stringToElement((String)SQUtils.fileToString((File)file));
                if ("RandomGroups".equals(element2.getName())) {
                    element2.setName("Groups");
                }
                return element2;
            }
        }
        catch (Exception exception) {
            Log.error("Error while loading Block groups.", (Throwable)exception);
        }
        return element;
    }

    public static List<Element> listGroups() {
        Element element = RandomGroups.getXml();
        return element.getChildren("Group");
    }

    public static Element findByID(String string, List<Element> list) {
        if (list == null) {
            return null;
        }
        for (int i = 0; i < list.size(); ++i) {
            Element element = list.get(i);
            if (!string.equals(element.getAttributeValue("id"))) continue;
            return element;
        }
        return null;
    }

    public static Element findByName(String string, Element element) {
        if (element == null) {
            return null;
        }
        List list = element.getChildren("Group");
        for (Element element2 : list) {
            if (!string.equals(element2.getAttributeValue("name"))) continue;
            return element2;
        }
        return null;
    }

    public static void save(String string) throws Exception {
        Element element;
        if (string == null) {
            throw new Exception("Groups XML cannot be null.");
        }
        try {
            element = XMLUtil.stringToElement((String)string);
        }
        catch (Exception exception) {
            throw new Exception("Invalid XML. " + exception.getMessage(), exception);
        }
        RandomGroups.save(element);
    }

    public static void save(Element element) throws Exception {
        if (element == null) {
            throw new Exception("Groups XML cannot be null.");
        }
        String string = XMLUtil.xmlToString((Element)element);
        SQUtils.createAndHandleBackupFiles((String)SQPaths.algoWizardBlockGroupsPath, (String)string, (int)50);
        SQUtils.stringToFile((String)SQPaths.algoWizardBlockGroupsPath, (String)string);
    }

    public static JSONArray listBackupFiles() {
        return SQUtils.listBackupFiles((String)SQPaths.algoWizardBlockGroupsPath);
    }
}

