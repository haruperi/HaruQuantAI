/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  com.strategyquant.datalib.customData.CustomDataManager
 *  com.strategyquant.lib.XMLUtil
 *  org.jdom2.Content
 *  org.jdom2.Element
 *  org.json.JSONObject
 *  org.slf4j.Logger
 *  org.slf4j.LoggerFactory
 */
package com.strategyquant.tradinglib.project;

import com.strategyquant.datalib.customData.CustomDataManager;
import com.strategyquant.lib.XMLUtil;
import com.strategyquant.tradinglib.Blocks;
import com.strategyquant.tradinglib.blocks.CustomBlocks;
import com.strategyquant.tradinglib.project.RandomGroups;
import com.strategyquant.tradinglib.project.ResourcesCustomBlocks;
import com.strategyquant.tradinglib.project.ResourcesRandomGroups;
import com.strategyquant.tradinglib.project.websocket.DataToSend;
import com.strategyquant.tradinglib.project.websocket.SQWebSocketManager;
import java.util.ArrayList;
import java.util.List;
import org.jdom2.Content;
import org.jdom2.Element;
import org.json.JSONObject;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

public class ProjectCustomResources {
    private static final Logger Log = LoggerFactory.getLogger(ProjectCustomResources.class);
    private static final String ResourcesElementName = "Resources";
    private static final String CustomSnippetsElementName = "CustomSnippets";
    private static final String CustomIndicatorsElementName = "CustomIndicators";
    private static final String CustomBlocksElementName = "CustomBlocks";
    private static final String RandomGroupsElementName = "RandomGroups";

    public static void addProjectResources(String string, Element element) throws Exception {
        try {
            Element element2;
            int n;
            ArrayList arrayList;
            if (string == null) {
                string = XMLUtil.elementToString((Element)element);
            }
            Element element3 = XMLUtil.getOrCreateChild((Element)element, (String)ResourcesElementName);
            ArrayList<String> arrayList2 = new ArrayList<String>();
            try {
                arrayList = XMLUtil.getNestedElements((Element)element, (String)"CustomData");
                for (n = 0; n < arrayList.size(); ++n) {
                    element2 = (Element)arrayList.get(n);
                    List list = element2.getChildren("Data");
                    for (int i = 0; i < list.size(); ++i) {
                        String string2;
                        Element element4 = (Element)list.get(i);
                        if (!XMLUtil.getBooleanAttr((Element)element4, (String)"use", (boolean)false) || arrayList2.contains(string2 = element4.getAttributeValue("name"))) continue;
                        arrayList2.add(string2);
                    }
                }
            }
            catch (Exception exception) {
                Log.error("No custom data added to custom resources", (Throwable)exception);
            }
            arrayList = XMLUtil.getOrCreateChild((Element)element3, (String)CustomIndicatorsElementName);
            arrayList.removeContent();
            for (n = 0; n < arrayList2.size(); ++n) {
                element2 = new Element("CustomIndicator");
                element2.setText((String)arrayList2.get(n));
                arrayList.addContent((Content)element2);
            }
        }
        catch (Exception exception) {
            Log.error("Cannot add custom resources into XML config", (Throwable)exception);
            throw exception;
        }
    }

    private static void loadCustomBlocks(ArrayList<String> arrayList, String string, String string2, String string3) {
        int n = string.indexOf(string2, 0);
        while (n > 0) {
            try {
                int n2 = string.indexOf(string3, n);
                int n3 = string.indexOf("<Contents>", n);
                if (n3 > 0 && n3 < n2) {
                    int n4 = string.indexOf("</Contents>", n);
                    n2 = string.indexOf(string3, n4);
                }
                if (n2 > 0) {
                    String string4 = string.substring(n, n2 + string3.length());
                    Element element = XMLUtil.stringToElement((String)string4);
                    String string5 = element.getAttributeValue("key");
                    boolean bl = XMLUtil.getBooleanAttr((Element)element, (String)"use", (boolean)true);
                    if (!arrayList.contains(string5) && bl) {
                        arrayList.add(string5);
                    }
                }
            }
            catch (Exception exception) {
                Log.error("Checking custom block resource failed", (Throwable)exception);
            }
            n = string.indexOf(string2, n + 1);
        }
    }

    public static Element checkProjectResources(ArrayList<Element> arrayList) throws Exception {
        Element element = new Element(ResourcesElementName);
        Element element2 = XMLUtil.getOrCreateChild((Element)element, (String)CustomIndicatorsElementName);
        Element element3 = XMLUtil.getOrCreateChild((Element)element, (String)CustomSnippetsElementName);
        Element element4 = XMLUtil.getOrCreateChild((Element)element, (String)CustomBlocksElementName);
        for (int i = 0; i < arrayList.size(); ++i) {
            Element element5 = arrayList.get(i);
            Element element6 = XMLUtil.getOrCreateChild((Element)element5, (String)ResourcesElementName);
            try {
                Object object;
                Element element7;
                int n;
                Object object2;
                String string;
                Object object3;
                Element element8 = XMLUtil.getOrCreateChild((Element)element6, (String)CustomIndicatorsElementName);
                List list = element8.getChildren("CustomIndicator");
                for (int j = list.size() - 1; j >= 0; --j) {
                    object3 = (Element)list.get(j);
                    string = object3.getText();
                    if (CustomDataManager.checkDataExists((String)string)) {
                        element8.removeContent((Content)object3);
                        continue;
                    }
                    object3.setAttribute("status", "0");
                    element2.addContent((Content)object3.clone());
                }
                ArrayList<Element> arrayList2 = new ArrayList<Element>();
                object3 = XMLUtil.getNestedElements((Element)element5, (String)"Block");
                for (int j = 0; j < ((ArrayList)object3).size(); ++j) {
                    Element element9;
                    object2 = (Element)((ArrayList)object3).get(j);
                    n = XMLUtil.getBooleanAttr((Element)object2, (String)"use", (boolean)false);
                    if (n == 0 || ProjectCustomResources.keyIsIgnored((String)(element9 = (element7 = object2.getAttributeValue("key").split("\\."))[((String[])element7).length - 1])) || element9 == null || element9.startsWith("CBlock") || element9.startsWith("talib_") || Blocks.exists((String)element9) || arrayList2.contains(element9)) continue;
                    arrayList2.add(element9);
                    object = new Element("CustomSnippet");
                    object.setText((String)element9);
                    element3.addContent((Content)object.clone());
                }
                string = element6.getChild(CustomBlocksElementName);
                if (string == null) continue;
                object2 = string.getChildren("Item");
                for (n = 0; n < object2.size(); ++n) {
                    element7 = (Element)object2.get(n);
                    int n2 = -1;
                    object = null;
                    String string2 = element7.getAttributeValue("key");
                    Element element10 = CustomBlocks.findByKey(string2);
                    if (element10 == null) {
                        Log.debug(String.format("CB '%s' / '%s' is missing", string2, XMLUtil.getAttr((Element)element7, (String)"name", (String)"NA")));
                        n2 = 0;
                    } else {
                        boolean bl = ResourcesCustomBlocks.areIdentical(element7, element10);
                        if (bl) {
                            if (!XMLUtil.getAttr((Element)element7, (String)"name").equals(XMLUtil.getAttr((Element)element10, (String)"name"))) {
                                n2 = 3;
                                object = XMLUtil.getAttr((Element)element10, (String)"name");
                            }
                        } else {
                            n2 = 1;
                        }
                    }
                    if (n2 == -1) continue;
                    Element element11 = element7.clone();
                    element11.setAttribute("status", n2 + "");
                    if (object != null) {
                        element11.setAttribute("differentName", (String)object);
                    }
                    element4.addContent((Content)element11);
                }
                continue;
            }
            catch (Exception exception) {
                Log.error("Cannot check custom resources from XML config", (Throwable)exception);
                throw new Exception("Cannot check XML config custom resources - " + exception.getMessage());
            }
        }
        return element;
    }

    private static boolean keyIsIgnored(String string) {
        switch (string) {
            case "ExitAfterBars": 
            case "MoveSL2BE": 
            case "SL2BEAddPips": 
            case "StopLoss": 
            case "ProfitTarget": 
            case "TrailingStop": 
            case "TrailingActivation": 
            case "_ExitRule_": 
            case "_ExitEOD_": {
                return true;
            }
        }
        return false;
    }

    public static Element checkStrategyResources(Element element) throws Exception {
        Element element2;
        List list;
        List list2;
        Element element3 = new Element(ResourcesElementName);
        Element element4 = XMLUtil.getOrCreateChild((Element)element3, (String)CustomBlocksElementName);
        Element element5 = XMLUtil.getOrCreateChild((Element)element3, (String)RandomGroupsElementName);
        int n = -1;
        String string = null;
        Element element6 = element.getChild(CustomBlocksElementName);
        if (element6 != null) {
            list2 = element6.getChildren("Item");
            for (int i = 0; i < list2.size(); ++i) {
                n = -1;
                string = null;
                list = (Element)list2.get(i);
                String string2 = list.getAttributeValue("key");
                element2 = CustomBlocks.findByKey(string2);
                if (element2 == null) {
                    Log.debug(String.format("CB '%s' / '%s' is missing", string2, XMLUtil.getAttr((Element)list, (String)"name", (String)"NA")));
                    n = 0;
                } else {
                    boolean bl = ResourcesCustomBlocks.areIdentical((Element)list, element2);
                    if (bl) {
                        if (!XMLUtil.getAttr((Element)list, (String)"name").equals(XMLUtil.getAttr((Element)element2, (String)"name"))) {
                            n = 3;
                            string = XMLUtil.getAttr((Element)element2, (String)"name");
                        }
                    } else {
                        n = 1;
                    }
                }
                if (n == -1) continue;
                Element element7 = list.clone();
                element7.setAttribute("status", n + "");
                if (string != null) {
                    element7.setAttribute("differentName", string);
                }
                element4.addContent((Content)element7);
            }
        }
        if ((list2 = element.getChild(RandomGroupsElementName)) != null) {
            List<Element> list3 = RandomGroups.listGroups();
            list = list2.getChildren("Group");
            for (int i = 0; i < list.size(); ++i) {
                n = -1;
                string = null;
                element2 = (Element)list.get(i);
                String string3 = XMLUtil.getAttr((Element)element2, (String)"id");
                Element element8 = RandomGroups.findByID(string3, list3);
                if (element8 == null) {
                    Log.debug(String.format("RG '%s' / '%s' is missing", string3, XMLUtil.getAttr((Element)element2, (String)"name", (String)"NA")));
                    n = 0;
                } else {
                    boolean bl = ResourcesRandomGroups.areIdentical(element2, element8);
                    if (bl) {
                        if (!XMLUtil.getAttr((Element)element2, (String)"name").equals(XMLUtil.getAttr((Element)element8, (String)"name"))) {
                            n = 3;
                            string = XMLUtil.getAttr((Element)element8, (String)"name");
                        }
                    } else {
                        n = 1;
                    }
                }
                if (n == -1) continue;
                Element element9 = element2.clone();
                element9.setAttribute("status", n + "");
                if (string != null) {
                    element9.setAttribute("differentName", string);
                }
                element5.addContent((Content)element9);
            }
        }
        return element3;
    }

    public static Element resolveStrategyResources(Element element, Element element2) throws Exception {
        Object object;
        Object object2;
        String string;
        Object object3;
        Object object4;
        Object object5;
        Object object6;
        Object object7;
        Element element3;
        if (element == null) {
            return element2;
        }
        boolean bl = false;
        Element element4 = null;
        Element element5 = element.getChild(CustomBlocksElementName);
        if (element5 != null) {
            element4 = CustomBlocks.get();
            List list = element5.getChildren("Item");
            for (int i = 0; i < list.size(); ++i) {
                element3 = (Element)list.get(i);
                object7 = XMLUtil.getAttr((Element)element3, (String)"action");
                object6 = XMLUtil.getAttr((Element)element3, (String)"name");
                String string2 = XMLUtil.getAttr((Element)element3, (String)"key");
                object5 = XMLUtil.getAttr((Element)element3, (String)"differentName", null);
                try {
                    if (object5 != null) {
                        if (element2 == null) continue;
                        ProjectCustomResources.useCustomBlockFromSQ(string2, element2);
                        continue;
                    }
                    if (((String)object7).equals("ignore")) continue;
                    if (((String)object7).equals("add") || ((String)object7).equals("useFromConfig")) {
                        object4 = element4.getChildren("Item");
                        for (int j = 0; j < object4.size(); ++j) {
                            object3 = (Element)object4.get(j);
                            String string3 = object3.getAttributeValue("key");
                            if (string3 == null || !string3.equals(string2)) continue;
                            element4.removeContent((Content)object3);
                            break;
                        }
                        string = element3.clone();
                        try {
                            Element element6;
                            int n;
                            object3 = object6;
                            int n2 = 1;
                            while (CustomBlocks.findByName((String)object3, element4) != null) {
                                object3 = (String)object6 + " (" + ++n2 + ")";
                            }
                            if (!((String)object3).equals(object6)) {
                                string.setAttribute("name", (String)object3);
                            }
                            object2 = string.getChildren("Param");
                            object = string.getChild("Contents");
                            List list2 = object.getChildren("Param");
                            ArrayList arrayList = XMLUtil.getNestedElements((Element)string.getChild("Contents"), (String)"Param");
                            for (n = list2.size() - 1; n >= 0; --n) {
                                element6 = (Element)list2.get(n);
                                if (!element6.getAttributeValue("name").equals("Chart")) continue;
                                object.removeContent((Content)element6);
                            }
                            for (n = 0; n < arrayList.size(); ++n) {
                                element6 = (Element)arrayList.get(n);
                                if (!element6.getAttributeValue("customParam", "false").equals("true")) continue;
                                String string4 = element6.getText();
                                if (!string4.startsWith("#") && (string4 = element6.getAttributeValue("value", "null")).startsWith("#")) {
                                    element6.setText(string4);
                                }
                                boolean bl2 = false;
                                for (int j = 0; j < object2.size(); ++j) {
                                    Element element7 = (Element)object2.get(j);
                                    if (!element7.getAttributeValue("key", "").equals(string4)) continue;
                                    bl2 = true;
                                    break;
                                }
                                if (bl2) continue;
                                element6.setText(element6.getAttributeValue("defaultValue", "0"));
                                element6.removeAttribute("customParam");
                            }
                        }
                        catch (Exception exception) {
                            Log.error(String.format("Error fixing missing CB with key %s.", string2), (Throwable)exception);
                        }
                        element4.addContent((Content)string);
                        bl = true;
                        continue;
                    }
                    if (!((String)object7).equals("useFromSQ") || element2 == null) continue;
                    ProjectCustomResources.useCustomBlockFromSQ(string2, element2);
                    continue;
                }
                catch (Exception exception) {
                    Log.error("Resolving custom block '" + (String)object6 + "' failed", (Throwable)exception);
                }
            }
        }
        boolean bl3 = false;
        Element element8 = null;
        element3 = element.getChild(RandomGroupsElementName);
        if (element3 != null) {
            element8 = RandomGroups.getXml();
            object7 = element8.getChildren("Group");
            object6 = element3.getChildren("Group");
            for (int i = 0; i < object6.size(); ++i) {
                object5 = (Element)object6.get(i);
                object4 = XMLUtil.getAttr((Element)object5, (String)"action");
                string = XMLUtil.getAttr((Element)object5, (String)"name");
                object3 = XMLUtil.getAttr((Element)object5, (String)"id");
                String string5 = XMLUtil.getAttr((Element)object5, (String)"differentName", null);
                try {
                    if (string5 != null || ((String)object4).equals("ignore")) continue;
                    if (((String)object4).equals("add") || ((String)object4).equals("useFromConfig")) {
                        for (int j = 0; j < object7.size(); ++j) {
                            object = (Element)object7.get(j);
                            String string6 = object.getAttributeValue("id");
                            if (string6 == null || !string6.equals(object3)) continue;
                            element8.removeContent((Content)object);
                            break;
                        }
                        object2 = object5.clone();
                        try {
                            object = string;
                            int n = 1;
                            while (RandomGroups.findByName((String)object, element8) != null) {
                                object = string + " (" + ++n + ")";
                            }
                            if (!((String)object).equals(string)) {
                                object2.setAttribute("name", (String)object);
                            }
                        }
                        catch (Exception exception) {
                            Log.error(String.format("Error fixing missing RG with id %s.", object3), (Throwable)exception);
                        }
                        element8.addContent((Content)object2);
                        bl3 = true;
                        continue;
                    }
                    if (!((String)object4).equals("useFromSQ") || element2 == null) continue;
                    object2 = RandomGroups.findByID((String)object3, (List<Element>)object7);
                    object = XMLUtil.findFirst((Element)element2, (String)RandomGroupsElementName);
                    XMLUtil.replaceElementsWithAttribute((Element)object, (String)"id", (String)object3, (Element)object2.clone(), null);
                    continue;
                }
                catch (Exception exception) {
                    Log.error("Resolving random group '" + string + "' failed", (Throwable)exception);
                }
            }
        }
        if (bl3) {
            RandomGroups.save(element8);
            SQWebSocketManager.addToDataQueue(new DataToSend("randomGroups", new JSONObject().put("blockGroupsXML", (Object)XMLUtil.elementToString((Element)RandomGroups.getXml()))), "SQUANT", "AlgoWizard");
        }
        if (bl) {
            CustomBlocks.save(element4);
            SQWebSocketManager.addToDataQueue(new DataToSend("customBlocks", new JSONObject().put("customBlocksXML", (Object)XMLUtil.elementToString((Element)CustomBlocks.get()))), "SQUANT", "AlgoWizard");
        }
        return element2;
    }

    private static void useCustomBlockFromSQ(String string, Element element) throws Exception {
        Element element2 = CustomBlocks.findByKey(string);
        if (element2 == null) {
            throw new Exception(String.format("Custom block with key '%s' doesn't exist.", string));
        }
        Element element3 = XMLUtil.findFirst((Element)element, (String)CustomBlocksElementName);
        if (element3 != null) {
            XMLUtil.replaceElementsWithAttribute((Element)element3, (String)"key", (String)string, (Element)element2, null);
        }
        Element element4 = element2.clone();
        element4.removeContent((Content)element4.getChild("Contents"));
        List list = element4.getChildren("Param");
        for (int i = 0; i < list.size(); ++i) {
            Element element5 = (Element)list.get(i);
            element5.setText(element5.getAttributeValue("defaultValue", "0"));
        }
        XMLUtil.replaceElementsWithAttribute((Element)element, (String)"key", (String)string, (Element)element4, (String)CustomBlocksElementName);
    }
}

