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

public class ResourcesRandomGroups {
    private static final Logger Log = LoggerFactory.getLogger(ResourcesRandomGroups.class);

    public static boolean areIdentical(Element element, Element element2) throws Exception {
        try {
            Log.debug(String.format("Comparing two RG with ids '%s'/'%s', names '%s'/'%s'...", XMLUtil.getAttr((Element)element, (String)"id"), XMLUtil.getAttr((Element)element2, (String)"id"), XMLUtil.getAttr((Element)element, (String)"name", (String)"NA"), XMLUtil.getAttr((Element)element2, (String)"name", (String)"NA")));
            if (!XMLUtil.getAttr((Element)element, (String)"id").equals(XMLUtil.getAttr((Element)element2, (String)"id")) || !XMLUtil.getAttr((Element)element, (String)"type").equals(XMLUtil.getAttr((Element)element2, (String)"type"))) {
                Log.debug(String.format("RG has different attributes. Groups:\n%s\n%s", XMLUtil.elementLineToString((Element)element), XMLUtil.elementLineToString((Element)element2)));
                return false;
            }
            Log.debug("RG attributes match, checking details ...");
            List list = element.getChildren("Item");
            List list2 = element2.getChildren("Item");
            if (list.size() != list2.size()) {
                Log.debug("RG has different Item count.");
                return false;
            }
            ElementComparatorByAttribute elementComparatorByAttribute = new ElementComparatorByAttribute("key");
            list.sort(elementComparatorByAttribute);
            list2.sort(elementComparatorByAttribute);
            for (int i = 0; i < list.size(); ++i) {
                Element element3;
                Element element4 = (Element)list.get(i);
                if (!ResourcesRandomGroups.itemIdentical(element4, element3 = (Element)list2.get(i))) {
                    return false;
                }
                ArrayList arrayList = XMLUtil.getNestedElements((Element)element4, (String)"Item");
                ArrayList arrayList2 = XMLUtil.getNestedElements((Element)element3, (String)"Item");
                if (arrayList.size() != arrayList2.size()) {
                    Log.debug(String.format("Item with key '%s' has different nested Item count %d<>%d.", XMLUtil.getAttr((Element)element4, (String)"key"), arrayList.size(), arrayList2.size()));
                    return false;
                }
                for (int j = 0; j < arrayList.size(); ++j) {
                    Element element5;
                    Element element6 = (Element)arrayList.get(j);
                    if (ResourcesRandomGroups.itemIdentical(element6, element5 = (Element)arrayList2.get(j))) continue;
                    return false;
                }
            }
            Log.debug("RG are itentical");
            return true;
        }
        catch (Exception exception) {
            Log.error("Error while comparing two RG..., Err. " + exception.getMessage(), (Throwable)exception);
            throw new Exception("Error while comparing two RG..., Err. " + exception.getMessage(), exception);
        }
    }

    private static boolean itemIdentical(Element element, Element element2) throws Exception {
        if (!(XMLUtil.getAttr((Element)element, (String)"key").equals(XMLUtil.getAttr((Element)element2, (String)"key")) && XMLUtil.getAttr((Element)element, (String)"name", (String)"NA").equals(XMLUtil.getAttr((Element)element2, (String)"name", (String)"NA")) && XMLUtil.getAttr((Element)element, (String)"returnType", (String)"NA").equals(XMLUtil.getAttr((Element)element2, (String)"returnType", (String)"NA")) && XMLUtil.getAttr((Element)element, (String)"categoryType", (String)"NA").equals(XMLUtil.getAttr((Element)element2, (String)"categoryType", (String)"NA")))) {
            Log.debug(String.format("Item with key '%s' has different attributes. Items:\n%s\n%s", XMLUtil.getAttr((Element)element, (String)"key"), XMLUtil.elementLineToString((Element)element), XMLUtil.elementLineToString((Element)element2)));
            return false;
        }
        String string = XMLUtil.getAttr((Element)element, (String)"key");
        List list = element.getChildren("Param");
        List list2 = element2.getChildren("Param");
        if (list.size() != list2.size()) {
            Log.debug(String.format("RG Item with key '%s' has different Param count %d<>%d.", string, list.size(), list2.size()));
            return false;
        }
        for (int i = 0; i < list.size(); ++i) {
            Element element3 = (Element)list.get(i);
            Element element4 = (Element)list2.get(i);
            if (!XMLUtil.getAttr((Element)element3, (String)"key").equals(XMLUtil.getAttr((Element)element4, (String)"key"))) {
                Log.debug(String.format("RG %s Param key mismatch '%s'<> '%s'.", string, XMLUtil.getAttr((Element)element3, (String)"key"), XMLUtil.getAttr((Element)element4, (String)"key")));
                return false;
            }
            String string2 = XMLUtil.getAttr((Element)element3, (String)"key");
            try {
                if (XMLUtil.getAttr((Element)element3, (String)"name").equals(XMLUtil.getAttr((Element)element4, (String)"name")) && XMLUtil.getAttr((Element)element3, (String)"type").equals(XMLUtil.getAttr((Element)element4, (String)"type")) && XMLUtil.getAttr((Element)element3, (String)"controlType").equals(XMLUtil.getAttr((Element)element4, (String)"controlType")) && XMLUtil.getAttr((Element)element3, (String)"defaultValue").equals(XMLUtil.getAttr((Element)element4, (String)"defaultValue")) && XMLUtil.getAttr((Element)element3, (String)"minValue", (String)"NA").equals(XMLUtil.getAttr((Element)element4, (String)"minValue", (String)"NA")) && XMLUtil.getAttr((Element)element3, (String)"maxValue", (String)"NA").equals(XMLUtil.getAttr((Element)element4, (String)"maxValue", (String)"NA")) && XMLUtil.getAttr((Element)element3, (String)"step", (String)"NA").equals(XMLUtil.getAttr((Element)element4, (String)"step", (String)"NA")) && XMLUtil.getAttr((Element)element3, (String)"generate", (String)"NA").equals(XMLUtil.getAttr((Element)element4, (String)"generate", (String)"NA")) && XMLUtil.getAttr((Element)element3, (String)"randomValue", (String)"NA").equals(XMLUtil.getAttr((Element)element4, (String)"randomValue", (String)"NA")) && XMLUtil.getAttr((Element)element3, (String)"builderStep", (String)"NA").equals(XMLUtil.getAttr((Element)element4, (String)"builderStep", (String)"NA")) && element3.getText().equals(element4.getText())) continue;
                Log.debug(String.format("RG Item/Param with key '%s/%s' has different attributes. Params:\n%s\n%s", string, XMLUtil.getAttr((Element)element3, (String)"key"), XMLUtil.elementLineToString((Element)element3), XMLUtil.elementLineToString((Element)element4)));
                return false;
            }
            catch (Exception exception) {
                Log.error(String.format("RG Error comparing Param with key '%s/%s'..., Err: %s", string, string2, exception.getMessage()), (Throwable)exception);
                return false;
            }
        }
        return true;
    }
}

