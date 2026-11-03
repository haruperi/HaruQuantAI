/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  com.strategyquant.lib.ElementComparatorByAttribute
 *  com.strategyquant.lib.XMLUtil
 *  org.jdom2.Element
 *  org.slf4j.Logger
 *  org.slf4j.LoggerFactory
 */
package com.strategyquant.tradinglib.project;

import com.strategyquant.lib.ElementComparatorByAttribute;
import com.strategyquant.lib.XMLUtil;
import java.util.ArrayList;
import java.util.List;
import org.jdom2.Element;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

public class ResourcesCustomBlocks {
    private static final Logger Log = LoggerFactory.getLogger(ResourcesCustomBlocks.class);

    public static boolean areIdentical(Element element, Element element2) throws Exception {
        try {
            Object object;
            Object object2;
            Element element3;
            Log.debug(String.format("Comparing two CB with keys '%s'/'%s', names '%s'/'%s'...", element.getAttributeValue("key"), element2.getAttributeValue("key"), XMLUtil.getAttr((Element)element, (String)"name", (String)"NA"), XMLUtil.getAttr((Element)element2, (String)"name", (String)"NA")));
            if (!(XMLUtil.getAttr((Element)element, (String)"key").equals(XMLUtil.getAttr((Element)element2, (String)"key")) && XMLUtil.getAttr((Element)element, (String)"oppositeBlockKey").equals(XMLUtil.getAttr((Element)element2, (String)"oppositeBlockKey")) && XMLUtil.getAttr((Element)element, (String)"returnType").equals(XMLUtil.getAttr((Element)element2, (String)"returnType")) && XMLUtil.getAttr((Element)element, (String)"type").equals(XMLUtil.getAttr((Element)element2, (String)"type")) && XMLUtil.getAttr((Element)element, (String)"strategyType", (String)"Standard").equals(XMLUtil.getAttr((Element)element2, (String)"strategyType", (String)"Standard")))) {
                Log.debug(String.format("CB has different attributes. Blocks:\n%s\n%s", XMLUtil.elementLineToString((Element)element), XMLUtil.elementLineToString((Element)element2)));
                return false;
            }
            String string = XMLUtil.getAttr((Element)element, (String)"key");
            Log.debug("CB attributes match, checking details ...");
            List list = element.getChildren("Param");
            List list2 = element2.getChildren("Param");
            if (list.size() != list2.size()) {
                Log.debug(String.format("CB %s has different Param count %d<>%d.", string, list.size(), list2.size()));
                return false;
            }
            for (int i = 0; i < list.size(); ++i) {
                element3 = (Element)list.get(i);
                object2 = (Element)list2.get(i);
                if (!XMLUtil.getAttr((Element)element3, (String)"key").equals(XMLUtil.getAttr((Element)object2, (String)"key"))) {
                    Log.debug(String.format("CB %s Param key mismatch '%s'<> '%s'.", string, XMLUtil.getAttr((Element)element3, (String)"key"), XMLUtil.getAttr((Element)object2, (String)"key")));
                    return false;
                }
                object = XMLUtil.getAttr((Element)element3, (String)"key");
                if (XMLUtil.getAttr((Element)element3, (String)"key").equals("#Chart1#") && XMLUtil.getAttr((Element)element3, (String)"defaultValue", (String)"missing").equals("missing")) {
                    XMLUtil.trySetAttr((Element)element3, (String)"defaultValue", (Object)"0");
                }
                if (XMLUtil.getAttr((Element)object2, (String)"key").equals("#Chart1#") && XMLUtil.getAttr((Element)object2, (String)"defaultValue", (String)"missing").equals("missing")) {
                    XMLUtil.trySetAttr((Element)object2, (String)"defaultValue", (Object)"0");
                }
                try {
                    if (XMLUtil.getAttr((Element)element3, (String)"name").equals(XMLUtil.getAttr((Element)object2, (String)"name")) && XMLUtil.getAttr((Element)element3, (String)"type").equals(XMLUtil.getAttr((Element)object2, (String)"type")) && XMLUtil.getAttr((Element)element3, (String)"controlType").equals(XMLUtil.getAttr((Element)object2, (String)"controlType")) && XMLUtil.getAttr((Element)element3, (String)"defaultValue").equals(XMLUtil.getAttr((Element)object2, (String)"defaultValue")) && XMLUtil.getAttr((Element)element3, (String)"minValue", (String)"NA").equals(XMLUtil.getAttr((Element)object2, (String)"minValue", (String)"NA")) && XMLUtil.getAttr((Element)element3, (String)"maxValue", (String)"NA").equals(XMLUtil.getAttr((Element)object2, (String)"maxValue", (String)"NA")) && XMLUtil.getAttr((Element)element3, (String)"step", (String)"NA").equals(XMLUtil.getAttr((Element)object2, (String)"step", (String)"NA"))) continue;
                    Log.debug(String.format("CB Param with key '%s/%s' has different attributes. Params:\n%s\n%s", string, object, XMLUtil.elementLineToString((Element)element3), XMLUtil.elementLineToString((Element)object2)));
                    return false;
                }
                catch (Exception exception) {
                    Log.debug(String.format("CB Error while comparing Param with key '%s/%s'. Err: %s", string, object, exception.getMessage()), (Throwable)exception);
                    return false;
                }
            }
            Element element4 = element.getChild("Contents");
            element3 = element2.getChild("Contents");
            object2 = element4.getChildren("Item");
            object = element3.getChildren("Item");
            if (object2.size() != object.size()) {
                Log.debug(String.format("CB has different Item count in Contents %d<>%d.", object2.size(), object.size()));
                return false;
            }
            ElementComparatorByAttribute elementComparatorByAttribute = new ElementComparatorByAttribute("key");
            object2.sort(elementComparatorByAttribute);
            object.sort(elementComparatorByAttribute);
            for (int i = 0; i < object2.size(); ++i) {
                Element element5;
                Element element6 = (Element)object2.get(i);
                if (!ResourcesCustomBlocks.itemIdentical(element6, element5 = (Element)object.get(i))) {
                    return false;
                }
                ArrayList arrayList = XMLUtil.getNestedElements((Element)element6, (String)"Item");
                ArrayList arrayList2 = XMLUtil.getNestedElements((Element)element5, (String)"Item");
                if (arrayList.size() != arrayList2.size()) {
                    Log.debug(String.format("Item with key '%s' has different nested Item count %d<>%d.", XMLUtil.getAttr((Element)element6, (String)"key"), arrayList.size(), arrayList2.size()));
                    return false;
                }
                for (int j = 0; j < arrayList.size(); ++j) {
                    Element element7;
                    Element element8 = (Element)arrayList.get(j);
                    if (ResourcesCustomBlocks.itemIdentical(element8, element7 = (Element)arrayList2.get(j))) continue;
                    return false;
                }
            }
            Log.debug("CB are itentical");
            return true;
        }
        catch (Exception exception) {
            Log.error("Error while comparing two CB..., Err. " + exception.getMessage(), (Throwable)exception);
            throw new Exception("Error while comparing two CB..., Err. " + exception.getMessage(), exception);
        }
    }

    private static boolean itemIdentical(Element element, Element element2) throws Exception {
        if (!(XMLUtil.getAttr((Element)element, (String)"key").equals(XMLUtil.getAttr((Element)element2, (String)"key")) && XMLUtil.getAttr((Element)element, (String)"name", (String)"NA").equals(XMLUtil.getAttr((Element)element2, (String)"name", (String)"NA")) && XMLUtil.getAttr((Element)element, (String)"returnType", (String)"NA").equals(XMLUtil.getAttr((Element)element2, (String)"returnType", (String)"NA")) && XMLUtil.getAttr((Element)element, (String)"categoryType", (String)"NA").equals(XMLUtil.getAttr((Element)element2, (String)"categoryType", (String)"NA")))) {
            Log.debug(String.format("Item with key '%s' has different attributes. Items:\n%s\n%s", XMLUtil.getAttr((Element)element, (String)"key"), XMLUtil.elementLineToString((Element)element), XMLUtil.elementLineToString((Element)element2)));
            return false;
        }
        List list = element.getChildren("Param");
        List list2 = element2.getChildren("Param");
        if (list.size() != list2.size()) {
            Log.debug(String.format("String.format(Item with key '%s' has different Param count %d<>%d.", XMLUtil.getAttr((Element)element, (String)"key"), list.size(), list2.size()));
            return false;
        }
        for (int i = 0; i < list.size(); ++i) {
            Element element3 = (Element)list.get(i);
            Element element4 = (Element)list2.get(i);
            if (XMLUtil.getAttr((Element)element3, (String)"key").equals(XMLUtil.getAttr((Element)element4, (String)"key")) && XMLUtil.getAttr((Element)element3, (String)"name").equals(XMLUtil.getAttr((Element)element4, (String)"name")) && XMLUtil.getAttr((Element)element3, (String)"type").equals(XMLUtil.getAttr((Element)element4, (String)"type")) && XMLUtil.getAttr((Element)element3, (String)"controlType").equals(XMLUtil.getAttr((Element)element4, (String)"controlType")) && XMLUtil.getAttr((Element)element3, (String)"defaultValue").equals(XMLUtil.getAttr((Element)element4, (String)"defaultValue")) && XMLUtil.getAttr((Element)element3, (String)"minValue", (String)"NA").equals(XMLUtil.getAttr((Element)element4, (String)"minValue", (String)"NA")) && XMLUtil.getAttr((Element)element3, (String)"maxValue", (String)"NA").equals(XMLUtil.getAttr((Element)element4, (String)"maxValue", (String)"NA")) && XMLUtil.getAttr((Element)element3, (String)"step", (String)"NA").equals(XMLUtil.getAttr((Element)element4, (String)"step", (String)"NA")) && XMLUtil.getAttr((Element)element3, (String)"builderStep", (String)"NA").equals(XMLUtil.getAttr((Element)element4, (String)"builderStep", (String)"NA")) && element3.getText().equals(element4.getText())) continue;
            Log.debug(String.format("Item/Param with key '%s/%s' has different attributes. Params:\n%s\n%s", XMLUtil.getAttr((Element)element, (String)"key"), XMLUtil.getAttr((Element)element3, (String)"key"), XMLUtil.elementLineToString((Element)element3), XMLUtil.elementLineToString((Element)element4)));
            return false;
        }
        return true;
    }
}

