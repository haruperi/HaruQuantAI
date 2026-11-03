/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  com.strategyquant.lib.L
 *  com.strategyquant.lib.SQUtils
 *  com.strategyquant.lib.XMLUtil
 *  com.strategyquant.lib.constants.SQPaths
 *  org.jdom2.Content
 *  org.jdom2.Element
 *  org.json.JSONArray
 *  org.json.JSONObject
 *  org.slf4j.Logger
 *  org.slf4j.LoggerFactory
 */
package com.strategyquant.tradinglib.blocks;

import com.strategyquant.lib.L;
import com.strategyquant.lib.SQUtils;
import com.strategyquant.lib.XMLUtil;
import com.strategyquant.lib.constants.SQPaths;
import com.strategyquant.tradinglib.blocks.random.BlockDefinition;
import com.strategyquant.tradinglib.project.websocket.DataToSend;
import com.strategyquant.tradinglib.project.websocket.SQWebSocketManager;
import java.io.File;
import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;
import org.jdom2.Content;
import org.jdom2.Element;
import org.json.JSONArray;
import org.json.JSONObject;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

public class CustomBlocks {
    private static final Logger Log = LoggerFactory.getLogger(CustomBlocks.class);
    private static Element config;
    private static final DataToSend refreshMessage;
    private static HashMap<String, BlockDefinition> cbDefinitionsMap;
    private static HashMap<String, Element> cbElementsMap;

    public static void load() {
        block6: {
            try {
                File file = new File(SQPaths.algoWizardCustomBlocksPath);
                if (file.exists()) {
                    try {
                        Element element = XMLUtil.fileToXmlElement((File)file);
                        if (CustomBlocks.setConfig(element)) {
                            XMLUtil.xmlToFile((Element)element, (File)file);
                        }
                        break block6;
                    }
                    catch (Exception exception) {
                        Log.error("Loading custom blocks failed", (Throwable)exception);
                        CustomBlocks.setConfig(new Element("CustomBlocks"));
                    }
                    break block6;
                }
                CustomBlocks.setConfig(new Element("CustomBlocks"));
            }
            catch (Exception exception) {
                Log.error("Error while loading CustomBlocks - " + exception.getMessage(), (Throwable)exception);
            }
        }
    }

    public static void save(Element element) throws Exception {
        CustomBlocks.setConfig(element);
        String string = XMLUtil.elementToString((Element)element);
        SQUtils.createAndHandleBackupFiles((String)SQPaths.algoWizardCustomBlocksPath, (String)string, (int)50);
        SQUtils.stringToFile((String)SQPaths.algoWizardCustomBlocksPath, (String)string);
        SQWebSocketManager.addToDataQueue(refreshMessage, "BUILDER", "TASKMANAGER");
    }

    public static Element get() {
        return config;
    }

    public static JSONArray getAsBuildingBlocks() {
        JSONArray jSONArray = new JSONArray();
        if (config != null) {
            List list = config.getChildren("Item");
            for (int i = 0; i < list.size(); ++i) {
                try {
                    Element element = (Element)list.get(i);
                    Element element2 = element.getChild("Contents");
                    JSONObject jSONObject = new JSONObject();
                    jSONObject.put("name", (Object)element.getAttributeValue("name"));
                    jSONObject.put("key", (Object)element.getAttributeValue("key"));
                    jSONObject.put("weight", 1);
                    jSONObject.put("originalWeight", 1);
                    jSONObject.put("empty", element2 == null || element2.getChildren().size() == 0);
                    String string = element.getAttributeValue("type");
                    String string2 = element.getAttributeValue("category");
                    jSONObject.put("returnType", (Object)CustomBlocks.getReturnType(string));
                    jSONObject.put("strategyType", (Object)element.getAttributeValue("strategyType", "Standard"));
                    jSONObject.put("groupKey", (Object)CustomBlocks.getGroupName(string, null));
                    jSONObject.put("group", (Object)CustomBlocks.getGroupName(string, string2));
                    JSONArray jSONArray2 = new JSONArray();
                    List list2 = element.getChildren("Param");
                    for (int j = 0; j < list2.size(); ++j) {
                        Element element3 = (Element)list2.get(j);
                        String string3 = element3.getAttributeValue("key");
                        String string4 = element3.getAttributeValue("name");
                        String string5 = element3.getAttributeValue("type");
                        String string6 = element3.getAttributeValue("paramType");
                        String string7 = element3.getAttributeValue("defaultValue");
                        String string8 = element3.getAttributeValue("minValue");
                        String string9 = element3.getAttributeValue("maxValue");
                        String string10 = element3.getAttributeValue("genMinValue");
                        String string11 = element3.getAttributeValue("genMaxValue");
                        String string12 = element3.getAttributeValue("step");
                        if (string3.equals("#Chart#")) {
                            jSONArray2.put((Object)new JSONObject().put("generation", (Object)"random").put("defaultValue", (Object)"0").put("name", (Object)string4).put("weight", 1).put("originalWeight", 1).put("type", (Object)"data").put("paramType", (Object)string6).put("allCharts", true).put("key", (Object)"#Chart#"));
                            continue;
                        }
                        if (string3.equals("#ComputedFrom#")) {
                            jSONArray2.put((Object)new JSONObject().put("generation", (Object)"random").put("defaultValue", (Object)CustomBlocks.getComputedFromDefaultValue(string7)).put("values", (Object)"Close=0,Open=1,High=2,Low=3,Median=4,Typical=5,Weighted=6,Volume=7").put("name", (Object)string4).put("weight", 1).put("originalWeight", 1).put("type", (Object)"int").put("paramType", (Object)string6).put("key", (Object)"#ComputedFrom#"));
                            continue;
                        }
                        string5 = string5.equals("bool") ? "boolean" : string5;
                        JSONObject jSONObject2 = new JSONObject();
                        jSONObject2.put("generation", (Object)"random");
                        jSONObject2.put("key", (Object)string3);
                        jSONObject2.put("name", (Object)string4);
                        jSONObject2.put("type", (Object)string5);
                        jSONObject2.put("paramType", (Object)string6);
                        if (string5.equals("int") || string5.equals("double")) {
                            jSONObject2.put("originalMaxValue", (Object)string9);
                            jSONObject2.put("genMaxValue", (Object)string11);
                            jSONObject2.put("maxValue", (Object)string9);
                            jSONObject2.put("originalMinValue", (Object)string8);
                            jSONObject2.put("genMinValue", (Object)string10);
                            jSONObject2.put("minValue", (Object)string8);
                            jSONObject2.put("step", (Object)string12);
                        } else if (string5.equals("data")) {
                            jSONObject2.put("paramType", (Object)"data");
                            jSONObject2.put("allCharts", true);
                        }
                        if (string6 != null && "0".equals(string12) && "0".equals(string8) && "0".equals(string9)) {
                            if (string6.equals("period")) {
                                jSONObject2.put("minValue", -1000003);
                                jSONObject2.put("maxValue", -1000004);
                                jSONObject2.put("step", 1);
                            } else if (string6.equals("shift")) {
                                jSONObject2.put("minValue", -1000001);
                                jSONObject2.put("maxValue", -1000002);
                                jSONObject2.put("step", 1);
                            }
                        }
                        jSONObject2.put("defaultValue", (Object)string7);
                        jSONObject2.put("weight", 1);
                        jSONObject2.put("originalWeight", 1);
                        jSONArray2.put((Object)jSONObject2);
                    }
                    jSONObject.put("params", (Object)jSONArray2);
                    jSONArray.put((Object)jSONObject);
                    continue;
                }
                catch (Exception exception) {
                    Log.error("Converting custom blocks to building blocks failed", (Throwable)exception);
                }
            }
        }
        return jSONArray;
    }

    private static String getReturnType(String string) {
        if (string == null) {
            return "number";
        }
        switch (string) {
            case "Condition": {
                return "boolean";
            }
            case "Price level": {
                return "price";
            }
        }
        return "number";
    }

    private static String getComputedFromDefaultValue(String string) {
        if (string == null) {
            return "0";
        }
        switch (string) {
            case "Open": {
                return "1";
            }
            case "High": {
                return "2";
            }
            case "Low": {
                return "3";
            }
            case "Median": {
                return "4";
            }
            case "Typical": {
                return "5";
            }
            case "Weighted": {
                return "6";
            }
        }
        return "0";
    }

    private static String getGroupName(String string, String string2) {
        if (string == null) {
            return "Custom values";
        }
        switch (string) {
            case "Condition": {
                if (string2 == null || string2.equals("No category")) {
                    return "Custom conditions";
                }
                return string2;
            }
            case "Price level": {
                return "Custom price levels";
            }
        }
        return "Custom values";
    }

    /*
     * WARNING - Removed try catching itself - possible behaviour change.
     */
    public static BlockDefinition getBlock(String string) {
        HashMap<String, BlockDefinition> hashMap = cbDefinitionsMap;
        synchronized (hashMap) {
            return cbDefinitionsMap.get(string);
        }
    }

    /*
     * WARNING - Removed try catching itself - possible behaviour change.
     */
    private static boolean setConfig(Element element) {
        boolean bl = CustomBlocks.fixConfig(element);
        config = element;
        HashMap<String, BlockDefinition> hashMap = cbDefinitionsMap;
        synchronized (hashMap) {
            cbDefinitionsMap.clear();
            cbElementsMap.clear();
            if (config != null) {
                List list = config.getChildren("Item");
                for (int i = 0; i < list.size(); ++i) {
                    try {
                        Element element2 = (Element)list.get(i);
                        Element element3 = new Element("TempCategory");
                        element3.addContent((Content)element2.clone());
                        String string = element2.getAttributeValue("type");
                        CustomBlocks.fixReturnType(element2, string);
                        BlockDefinition blockDefinition = new BlockDefinition(element2, element3, string);
                        cbDefinitionsMap.put(blockDefinition.key, blockDefinition);
                        cbElementsMap.put(blockDefinition.key, element2.clone());
                        continue;
                    }
                    catch (Exception exception) {
                        Log.error("Converting custom blocks to building blocks failed", (Throwable)exception);
                    }
                }
            }
        }
        return bl;
    }

    private static boolean fixConfig(Element element) {
        if (element == null) {
            return false;
        }
        boolean bl = false;
        try {
            String string;
            Element element2;
            int n;
            ArrayList<String> arrayList = new ArrayList<String>();
            List list = element.getChildren("Item");
            for (n = 0; n < list.size(); ++n) {
                element2 = (Element)list.get(n);
                string = XMLUtil.getAttr((Element)element2, (String)"key");
                if (arrayList.contains(string)) continue;
                arrayList.add(string);
            }
            for (n = 0; n < list.size(); ++n) {
                element2 = (Element)list.get(n);
                string = XMLUtil.getAttr((Element)element2, (String)"key");
                String string2 = XMLUtil.getAttr((Element)element2, (String)"name");
                String string3 = XMLUtil.getAttr((Element)element2, (String)"oppositeBlockKey", null);
                if (string3 == null || string3.equals("") || string3.equals("CBlock_null") || string3.equals("null") || string3.equals("CBlock_") || arrayList.contains(string3)) continue;
                element2.setAttribute("oppositeBlockKey", "CBlock_null");
                bl = true;
                Log.info(String.format("Fixed CustomBlock with key/name %s/%s - Opposite block with key %s doesn't exist, changed to 'CBlock_null'", string, string2, string3));
            }
        }
        catch (Exception exception) {
            Log.error("Error while fixing CustomBlocks xml - " + exception.getMessage(), (Throwable)exception);
        }
        return bl;
    }

    private static void fixReturnType(Element element, String string) throws Exception {
        switch (string) {
            case "Condition": {
                element.setAttribute("returnType", "boolean");
                return;
            }
            case "Price level": {
                element.setAttribute("returnType", "price");
                return;
            }
            case "Action": {
                element.setAttribute("returnType", "order");
                return;
            }
            case "Value": {
                element.setAttribute("returnType", "number");
                return;
            }
        }
        throw new Exception(L.t((String)"Custom block has unknown block type: %s", (Object[])new Object[]{string}));
    }

    /*
     * WARNING - Removed try catching itself - possible behaviour change.
     */
    public static Element getElement(String string) {
        HashMap<String, BlockDefinition> hashMap = cbDefinitionsMap;
        synchronized (hashMap) {
            return cbElementsMap.get(string);
        }
    }

    /*
     * WARNING - Removed try catching itself - possible behaviour change.
     */
    public static HashMap<String, Element> getAllElements() {
        HashMap<String, BlockDefinition> hashMap = cbDefinitionsMap;
        synchronized (hashMap) {
            return cbElementsMap;
        }
    }

    public static void addCBlockSourceCodes(Element element) {
        Element element2 = element.getChild("Strategy").getChild("CustomBlocks");
        if (element2 == null) {
            return;
        }
        try {
            CustomBlocks._addCBlockSourceCodesToItems(element, element2);
        }
        catch (Exception exception) {
            exception.printStackTrace();
        }
    }

    private static void _addCBlockSourceCodesToItems(Element element, Element element2) {
        String string;
        Object object;
        if (element.getName().equals("RandomGroups")) {
            return;
        }
        if (element.getName().equals("Item") && (object = element.getAttributeValue("key")) != null && ((String)object).startsWith("CBlock") && (string = CustomBlocks.getCBlockId((String)object)) != null) {
            CustomBlocks._addCBlockSourceCodesToItem(element, (String)object, element2);
        }
        if ((object = element.getChildren()) != null && object.size() > 0) {
            for (int i = 0; i < object.size(); ++i) {
                Element element3 = (Element)object.get(i);
                CustomBlocks._addCBlockSourceCodesToItems(element3, element2);
            }
        }
    }

    private static void _addCBlockSourceCodesToItem(Element element, String string, Element element2) {
        String string2;
        Element element3 = null;
        List list = element2.getChildren();
        for (int i = 0; i < list.size(); ++i) {
            Element element4 = (Element)list.get(i);
            string2 = element4.getAttributeValue("key");
            if (string2 == null || !string2.equals(string)) continue;
            element3 = element4;
            break;
        }
        if (element3 == null) {
            Log.error("No Custom Blocks definition found for block '" + string + "'");
        }
        Element element5 = element3.getChild("Contents").clone();
        if (!CustomBlocks.hasContentsElement(element)) {
            element.addContent((Content)element5);
        }
        list = element.getChildren("Param");
        for (int i = 0; i < list.size(); ++i) {
            string2 = (Element)list.get(i);
            CustomBlocks._fixCBlockParametersForSourceCodes((Element)string2, element5);
        }
    }

    private static boolean hasContentsElement(Element element) {
        Element element2 = element.getChild("Contents");
        return element2 != null && element2.getChildren().size() != 0;
    }

    private static void _fixCBlockParametersForSourceCodes(Element element, Element element2) {
        Object object;
        String string = element.getAttributeValue("key");
        if (element2.getName().equals("Param") && (object = element2.getText()) != null && ((String)object).equals(string)) {
            element2.setText(element.getText());
            String string2 = element.getAttributeValue("variable");
            if (string2 != null) {
                element2.setAttribute("variable", string2);
            }
        }
        if ((object = element2.getChildren()) != null && object.size() > 0) {
            for (int i = 0; i < object.size(); ++i) {
                Element element3 = (Element)object.get(i);
                CustomBlocks._fixCBlockParametersForSourceCodes(element, element3);
            }
        }
    }

    public static String getCBlockId(String string) {
        if (string.length() <= 7) {
            return null;
        }
        return string.substring(7);
    }

    public static Element findByKey(String string) {
        HashMap<String, Element> hashMap = CustomBlocks.getAllElements();
        for (String string2 : hashMap.keySet()) {
            Element element = hashMap.get(string2);
            if (!element.getAttributeValue("key").equals(string)) continue;
            return element;
        }
        return null;
    }

    public static Element findByName(String string, Element element) {
        if (element == null) {
            return null;
        }
        List list = element.getChildren("Item");
        for (Element element2 : list) {
            if (!element2.getAttributeValue("name").equals(string)) continue;
            return element2;
        }
        return null;
    }

    public static JSONArray listBackupFiles() {
        return SQUtils.listBackupFiles((String)SQPaths.algoWizardCustomBlocksPath);
    }

    static {
        refreshMessage = new DataToSend("customBlocksChanged", new JSONObject().put("customBlocksChanged", true));
        cbDefinitionsMap = new HashMap();
        cbElementsMap = new HashMap();
    }
}

