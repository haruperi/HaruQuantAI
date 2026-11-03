/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  org.jdom2.Content
 *  org.jdom2.Element
 *  org.slf4j.Logger
 *  org.slf4j.LoggerFactory
 */
package com.strategyquant.tradinglib.blocks;

import com.strategyquant.tradinglib.BlockDefinitionException;
import com.strategyquant.tradinglib.IBlock;
import com.strategyquant.tradinglib.Variable;
import java.lang.reflect.Field;
import java.util.List;
import org.jdom2.Content;
import org.jdom2.Element;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

public abstract class AnnotationHandler {
    private static final Logger Log = LoggerFactory.getLogger(AnnotationHandler.class);

    public static String decorateFieldName(String string) {
        StringBuilder stringBuilder = new StringBuilder();
        stringBuilder.append("#");
        stringBuilder.append(string);
        stringBuilder.append("#");
        return stringBuilder.toString();
    }

    protected static double getParamNumberValue(IBlock iBlock, Field field, List<Element> list, String string) throws BlockDefinitionException {
        Element element = AnnotationHandler.getParameter(iBlock, list, string);
        String string2 = element.getAttributeValue("variable");
        String string3 = element.getAttributeValue("customParam");
        if (!(string2 != null && string2.equals("true") || string3 != null && string3.equals("true"))) {
            return Double.parseDouble(element.getValue());
        }
        String string4 = element.getValue();
        if (iBlock.getStrategy() != null) {
            Variable variable = null;
            if (string2 != null && string2.equals("true")) {
                variable = iBlock.getStrategy().variables().getById(string4);
            }
            if (string3 != null) {
                String string5 = element.getText();
                variable = new Variable(string5, string5, "customParam", "0", true, false);
                iBlock.getStrategy().variables().add(variable);
            }
            try {
                variable.registerAttachedField(iBlock, field);
            }
            catch (NullPointerException nullPointerException) {
                Log.error("AnnotationHandler exception", (Throwable)nullPointerException);
            }
            return Double.parseDouble(variable.getValue());
        }
        throw new BlockDefinitionException("Strategy is null for block!");
    }

    protected static double getParamChartTFValue(IBlock iBlock, Field field, List<Element> list, String string) throws BlockDefinitionException {
        Element element = AnnotationHandler.getParameter(iBlock, list, string);
        String string2 = element.getAttributeValue("chartTF");
        if (string2 == null || string2.equals("")) {
            return 0.0;
        }
        switch (string2) {
            case "D1": {
                return 1.0;
            }
            case "W1": {
                return 2.0;
            }
            case "M1": {
                return 3.0;
            }
        }
        return 0.0;
    }

    protected static Element getParameter(IBlock iBlock, List<Element> list, String string) throws BlockDefinitionException {
        for (Element element : list) {
            String string2;
            if (element.getName().equals("Param")) {
                string2 = element.getAttributeValue("key");
                if (string2 == null) {
                    throw new BlockDefinitionException("Block '" + iBlock.getClass().getSimpleName() + "' - Param doesn't have 'key' attribute!");
                }
                if (!string2.equalsIgnoreCase(string)) continue;
                return element;
            }
            if (element.getName().equals("Block")) {
                string2 = element.getAttributeValue("key");
                if (string2 == null) {
                    throw new BlockDefinitionException("Block '" + iBlock.getClass().getSimpleName() + "' - Block doesn't have 'key' attribute!");
                }
                if (!string2.equalsIgnoreCase(string)) continue;
                throw new BlockDefinitionException("getParameter() shouldn't be used for <Block> parameter!");
            }
            throw new BlockDefinitionException("Block '" + iBlock.getClass().getSimpleName() + "' - Item parameter should have name <Param> or <Block>, it is <" + element.getName() + "> instead!");
        }
        return null;
    }

    protected static void setField(IBlock iBlock, Field field, Object object) {
        try {
            field.set(iBlock, object);
        }
        catch (IllegalArgumentException illegalArgumentException) {
            Log.error(String.format("Failed to set field '%s' to value '%s'.", field.getName(), object == null ? "null" : object.toString()));
        }
        catch (IllegalAccessException illegalAccessException) {
            Log.error(String.format("Failed to set field '%s' to value '%s'.", field.getName(), object == null ? "null" : object.toString()));
        }
    }

    public static String getFieldName(String string, String string2) {
        if (!string.equals("Null")) {
            return string;
        }
        return string2;
    }

    protected static Element getOrCreateParamCategory(Element element, String string, boolean bl) {
        if (bl) {
            return element;
        }
        for (Element element2 : element.getChildren("paramCategory")) {
            if (!element2.getAttributeValue("name").equals(string)) continue;
            return element2;
        }
        Element element3 = new Element("paramCategory");
        element3.setAttribute("name", string);
        element3.setAttribute("expanded", "true");
        element.addContent((Content)element3);
        return element3;
    }
}

