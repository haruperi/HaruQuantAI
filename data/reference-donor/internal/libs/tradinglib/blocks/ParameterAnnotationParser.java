/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  com.strategyquant.datalib.DataSeries
 *  com.strategyquant.datalib.dataseries.DataSeriesTypes
 *  org.jdom2.Element
 *  org.slf4j.Logger
 *  org.slf4j.LoggerFactory
 */
package com.strategyquant.tradinglib.blocks;

import com.strategyquant.datalib.DataSeries;
import com.strategyquant.datalib.dataseries.DataSeriesTypes;
import com.strategyquant.tradinglib.BlockDefinitionException;
import com.strategyquant.tradinglib.Blocks;
import com.strategyquant.tradinglib.ChartData;
import com.strategyquant.tradinglib.ExitMethod;
import com.strategyquant.tradinglib.IBlock;
import com.strategyquant.tradinglib.IFormula;
import com.strategyquant.tradinglib.Parameter;
import com.strategyquant.tradinglib.StrategyBase;
import com.strategyquant.tradinglib.Variable;
import com.strategyquant.tradinglib.blocks.AnnotationHandler;
import com.strategyquant.tradinglib.blocks.annotations.DataSeriesChoice;
import com.strategyquant.tradinglib.exit.ExitMethodsList;
import com.strategyquant.tradinglib.formulas.Formulas;
import java.lang.reflect.Field;
import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import org.jdom2.Element;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

class ParameterAnnotationParser
extends AnnotationHandler {
    private static final Logger Log = LoggerFactory.getLogger(ParameterAnnotationParser.class);

    ParameterAnnotationParser() {
    }

    public static void wizardParseXml(Parameter parameter, IBlock iBlock, Field field, Element element) throws BlockDefinitionException {
        if (!element.getName().equals("Item") && !element.getName().equals("Formula")) {
            throw new BlockDefinitionException("@Parameter must be used only on Item or Formula node!");
        }
        String string = field.getType().getName();
        String string2 = ParameterAnnotationParser.decorateFieldName(field.getName());
        List list = element.getChildren();
        if (string.equals("int") || string.equals("long") || string.equals("double") || string.equals("boolean") || string.equals("java.lang.String")) {
            ParameterAnnotationParser.wizardParsePrimitiveType(iBlock, field, list, string2, string);
        } else if (field.getType().isAssignableFrom(Variable.class)) {
            ParameterAnnotationParser.wizardParseVariable(iBlock, field, list, string2);
        } else if (field.getType().isAssignableFrom(DataSeries.class)) {
            ParameterAnnotationParser.wizardParseDataSeries(iBlock, field, list, string2);
        } else if (field.getType().isAssignableFrom(ChartData.class)) {
            ParameterAnnotationParser.wizardParseChartData(iBlock, field, list, string2);
        } else if (string.equals("com.strategyquant.tradinglib.IFormula")) {
            ParameterAnnotationParser.wizardParseFormula(iBlock, field, list, string2, element);
        } else if (string.equals("com.strategyquant.tradinglib.IBlock")) {
            ParameterAnnotationParser.wizardParseBlock(iBlock, field, list, string2);
        } else if (string.equals("[Lcom.strategyquant.tradinglib.IBlock;")) {
            ParameterAnnotationParser.wizardParseBlocks(iBlock, field, list, string2);
        } else if (field.getType().toString().equals("class [Lcom.strategyquant.tradinglib.ExitMethod;")) {
            ParameterAnnotationParser.wizardParseExitMethods(iBlock, field, list, string2);
        } else {
            throw new BlockDefinitionException("Param with name '" + string2 + "' has an unknown type '" + string + "' in block " + iBlock + "!");
        }
    }

    private static void wizardParseVariable(IBlock iBlock, Field field, List<Element> list, String string) throws BlockDefinitionException {
        Element element = ParameterAnnotationParser.getParameter(iBlock, list, string);
        String string2 = element.getAttributeValue("variable");
        if (string2 == null || !string2.equals("true")) {
            throw new BlockDefinitionException("Field is not a variable!");
        }
        String string3 = element.getValue();
        if (iBlock.getStrategy() == null) {
            throw new BlockDefinitionException("Strategy cannot be null when using Variable!");
        }
        Variable variable = iBlock.getStrategy().variables().getById(string3);
        ParameterAnnotationParser.setField(iBlock, field, variable);
    }

    /*
     * WARNING - void declaration
     */
    private static void wizardParseExitMethods(IBlock iBlock, Field field, List<Element> list, String string) throws BlockDefinitionException {
        void var7_14;
        Object object;
        String[] stringArray;
        String string2;
        if (!field.getType().isAssignableFrom(ExitMethod[].class)) {
            Class<?> clazz = iBlock.getClass();
            throw new BlockDefinitionException("Field " + clazz.getSimpleName() + "." + field.getName() + " must have ExitMethod[] type!");
        }
        HashMap hashMap = new HashMap();
        for (Element object22 : list) {
            String string3 = object22.getAttributeValue("exitMethod");
            if (string3 == null || !string3.equals("true")) continue;
            string2 = object22.getAttributeValue("key");
            stringArray = (string2 = string2.replace("#", "")).split("\\.");
            if (stringArray.length != 2) {
                throw new BlockDefinitionException(String.format("Key for exit method has incorrect format '%s'", string2));
            }
            object = stringArray[0];
            if (!hashMap.containsKey(object)) {
                hashMap.put(object, new ArrayList());
            }
            ArrayList arrayList = (ArrayList)hashMap.get(object);
            arrayList.add(object22);
        }
        if (hashMap.isEmpty()) {
            return;
        }
        ArrayList arrayList = new ArrayList();
        for (Map.Entry entry : hashMap.entrySet()) {
            string2 = (String)entry.getKey();
            stringArray = (String[])entry.getValue();
            object = ExitMethodsList.getExitMethodObject(string2, iBlock.getStrategy(), (ArrayList<Element>)stringArray);
            arrayList.add(object);
        }
        ExitMethod[] exitMethodArray = new ExitMethod[arrayList.size()];
        boolean bl = false;
        while (var7_14 < arrayList.size()) {
            exitMethodArray[var7_14] = (ExitMethod)arrayList.get((int)var7_14);
            ++var7_14;
        }
        ParameterAnnotationParser.setField(iBlock, field, exitMethodArray);
    }

    private static void wizardParseBlocks(IBlock iBlock, Field field, List<Element> list, String string) throws BlockDefinitionException {
        if (!field.getType().isAssignableFrom(IBlock[].class)) {
            Class<?> clazz = iBlock.getClass();
            throw new BlockDefinitionException("Field " + clazz.getSimpleName() + "." + field.getName() + " must have Block type!");
        }
        ArrayList<IBlock> arrayList = new ArrayList<IBlock>();
        for (int i = 0; i < list.size(); ++i) {
            Element element = list.get(i);
            if (element.getName().equals("Block")) {
                arrayList.add(ParameterAnnotationParser.parseSubBlock(iBlock.getStrategy(), element.getChild("Item")));
                continue;
            }
            if (!element.getName().equals("Item")) continue;
            arrayList.add(ParameterAnnotationParser.parseSubBlock(iBlock.getStrategy(), element));
        }
        IBlock[] iBlockArray = new IBlock[arrayList.size()];
        for (int i = 0; i < arrayList.size(); ++i) {
            iBlockArray[i] = (IBlock)arrayList.get(i);
        }
        ParameterAnnotationParser.setField(iBlock, field, iBlockArray);
    }

    public static IBlock parseSubBlock(StrategyBase strategyBase, Element element) throws BlockDefinitionException {
        if (element == null) {
            throw new BlockDefinitionException("Block doesn't contain item 1");
        }
        IBlock iBlock = Blocks.getBlockObject(element.getAttributeValue("key"), strategyBase, element);
        return iBlock;
    }

    private static void wizardParseBlock(IBlock iBlock, Field field, List<Element> list, String string) throws BlockDefinitionException {
        if (!field.getType().isAssignableFrom(IBlock.class)) {
            Class<?> clazz = iBlock.getClass();
            throw new BlockDefinitionException("Field " + clazz.getSimpleName() + "." + field.getName() + " must have Block type!");
        }
        String string2 = ParameterAnnotationParser.decorateFieldName(field.getName());
        for (int i = 0; i < list.size(); ++i) {
            Element element = list.get(i);
            if (!ParameterAnnotationParser.isBlock(iBlock, element)) continue;
            String string3 = element.getAttributeValue("key");
            if (string3 == null) {
                throw new BlockDefinitionException("Block doesn't have 'key' attribute!");
            }
            if (!string3.equalsIgnoreCase(string2)) continue;
            Element element2 = element.getChild("Item");
            ParameterAnnotationParser.setField(iBlock, field, ParameterAnnotationParser.parseSubBlock(iBlock.getStrategy(), element2));
        }
    }

    private static boolean isBlock(IBlock iBlock, Element element) {
        if (element.getName().equals("Block")) {
            return true;
        }
        if (element.getName().equals("Param")) {
            String string = element.getAttributeValue("key");
            if (string == null) {
                return false;
            }
            Class<?> clazz = iBlock.getClass().getSuperclass();
            if (clazz == null) {
                return false;
            }
            String string2 = clazz.getSimpleName();
            if (string2 == null || !string2.equals("LeftRightComparisonBlockAbstract")) {
                return false;
            }
            if (string.equals("#Left#") || string.equals("#Right#")) {
                return true;
            }
        }
        return false;
    }

    private static void wizardParsePrimitiveType(IBlock iBlock, Field field, List<Element> list, String string, String string2) throws BlockDefinitionException {
        Element element = ParameterAnnotationParser.getParameter(iBlock, list, string);
        if (element == null) {
            return;
        }
        String string3 = null;
        String string4 = element.getAttributeValue("variable");
        String string5 = element.getAttributeValue("customParam");
        if (!(string4 != null && string4.equals("true") || string5 != null && string5.equals("true"))) {
            string3 = element.getValue();
        } else {
            String string6 = element.getValue();
            if (iBlock.getStrategy() != null) {
                String string7;
                Variable variable = null;
                if (string4 != null && string4.equals("true")) {
                    variable = iBlock.getStrategy().variables().getById(string6);
                } else if (string5 != null) {
                    string7 = element.getText();
                    variable = new Variable(string7, string7, "customParam", "0", true, false);
                    iBlock.getStrategy().variables().add(variable);
                }
                if (variable == null) {
                    string7 = element.getAttributeValue("key");
                    if (string7.contains("MagicNumber") && (variable = iBlock.getStrategy().variables().get("MagicNumber")) != null) {
                        element.setText(variable.getId());
                    }
                    if (variable == null) {
                        throw new BlockDefinitionException(String.format("No Variable with ID '%s' defined!", string6));
                    }
                }
                variable.registerAttachedField(iBlock, field);
                string3 = variable.getValue();
            }
        }
        if (string3 != null) {
            try {
                ParameterAnnotationParser.parseValue(string2, iBlock, field, string3);
            }
            catch (NumberFormatException numberFormatException) {
                if (string3.contains("--")) {
                    string3 = string3.replace("--", "-");
                    ParameterAnnotationParser.parseValue(string2, iBlock, field, string3);
                }
                throw numberFormatException;
            }
        }
    }

    private static void parseValue(String string, IBlock iBlock, Field field, String string2) throws BlockDefinitionException {
        try {
            if (string.equals("int")) {
                if (string2.equalsIgnoreCase("Any")) {
                    ParameterAnnotationParser.setField(iBlock, field, 0);
                } else if (string2.contains(":")) {
                    String[] stringArray = string2.split(":");
                    ParameterAnnotationParser.setField(iBlock, field, Integer.parseInt(stringArray[0]) * 100 + Integer.parseInt(stringArray[1]));
                } else {
                    ParameterAnnotationParser.setField(iBlock, field, (int)Double.parseDouble(string2));
                }
            } else if (string.equals("long")) {
                ParameterAnnotationParser.setField(iBlock, field, Long.parseLong(string2));
            } else if (string.equals("double")) {
                ParameterAnnotationParser.setField(iBlock, field, Double.parseDouble(string2));
            } else if (string.equals("boolean")) {
                ParameterAnnotationParser.setField(iBlock, field, Boolean.parseBoolean(string2));
            } else if (string.equals("java.lang.String")) {
                ParameterAnnotationParser.setField(iBlock, field, string2);
            }
        }
        catch (Exception exception) {
            Log.error(String.format("Failed to set param '%s/%s', value '%s'.", iBlock.getClass().getSimpleName(), field.getName(), string2));
            throw new BlockDefinitionException(String.format("Failed to set param '%s/%s', value '%s'.", iBlock.getClass().getSimpleName(), field.getName(), string2), exception);
        }
    }

    private static void wizardParseFormula(IBlock iBlock, Field field, List<Element> list, String string, Element element) throws BlockDefinitionException {
        if (!field.getType().isAssignableFrom(IFormula.class)) {
            Class<?> clazz = iBlock.getClass();
            throw new BlockDefinitionException("Field " + clazz.getSimpleName() + "." + field.getName() + " must have Formula type!");
        }
        for (int i = 0; i < list.size(); ++i) {
            Element element2;
            Element element3 = list.get(i);
            boolean bl = false;
            if (!element3.getName().equals("Param")) continue;
            String string2 = element3.getAttributeValue("key");
            if (string2 == null) {
                throw new BlockDefinitionException("Param doesn't have 'key' attribute!");
            }
            String string3 = ParameterAnnotationParser.decorateFieldName(field.getName());
            if (string2.equalsIgnoreCase(string3)) {
                bl = true;
            } else if (string2.contains(".")) {
                element2 = string2.split("\\.");
                if (((Element)element2).length != 2) {
                    throw new BlockDefinitionException(String.format("Key for exit method has incorrect format '%s'", string2));
                }
                string2 = (String)element2[0] + "#";
                if (string2.equalsIgnoreCase(string3)) {
                    bl = true;
                }
            }
            if (!bl) continue;
            element2 = element3.getChild("Formula");
            if (element2 == null) {
                throw new BlockDefinitionException("Formula parameter '" + field.getName() + "' doesn't have Formula child!");
            }
            String string4 = element2.getAttributeValue("key");
            if (string4 == null) {
                throw new BlockDefinitionException("CompositeValue doesn't have 'key' attribute!");
            }
            IFormula iFormula = Formulas.get(string4);
            iFormula = iFormula.newFormulaInstance(iBlock.getStrategy(), element2);
            ParameterAnnotationParser.setField(iBlock, field, iFormula);
            return;
        }
        if (!field.getType().isAssignableFrom(IFormula.class)) {
            Class<?> clazz = iBlock.getClass();
            throw new BlockDefinitionException("Field " + clazz.getSimpleName() + "." + field.getName() + " must have Formula type!");
        }
        throw new BlockDefinitionException("Error parsing formula!");
    }

    private static void wizardParseDataSeries(IBlock iBlock, Field field, List<Element> list, String string) throws BlockDefinitionException {
        if (string.equals("#Input#")) {
            string = "#Chart#";
        }
        int n = (int)ParameterAnnotationParser.getParamNumberValue(iBlock, field, list, string);
        int n2 = (int)ParameterAnnotationParser.getParamChartTFValue(iBlock, field, list, string);
        String string2 = "ComputedFrom";
        DataSeriesChoice dataSeriesChoice = field.getAnnotation(DataSeriesChoice.class);
        if (dataSeriesChoice != null) {
            string2 = dataSeriesChoice.key();
        }
        int n3 = (int)ParameterAnnotationParser.getParamNumberValue(iBlock, field, list, ParameterAnnotationParser.decorateFieldName(string2));
        try {
            iBlock.setCustomData(field.getName() + "ChartIndex", n);
            iBlock.setCustomData(field.getName() + "ComputedFrom", n3);
            iBlock.setCustomData(field.getName() + "ChartTF", n2);
            if (iBlock.getStrategy() != null && iBlock.getStrategy().MarketData != null) {
                ParameterAnnotationParser.setField(iBlock, field, iBlock.getStrategy().MarketData.Chart(n).getSeries(n3, n2));
            }
        }
        catch (Exception exception) {
            throw new BlockDefinitionException("Exception in getting DataSeries for chart: " + n + ", and series: " + DataSeriesTypes.toString((int)n3));
        }
    }

    private static void wizardParseChartData(IBlock iBlock, Field field, List<Element> list, String string) throws BlockDefinitionException {
        if (string.equals("#Input#")) {
            string = "#Chart#";
        }
        int n = (int)ParameterAnnotationParser.getParamNumberValue(iBlock, field, list, string);
        int n2 = (int)ParameterAnnotationParser.getParamChartTFValue(iBlock, field, list, string);
        try {
            iBlock.setCustomData("StockpickerChartIndex", n);
            iBlock.setCustomData(field.getName() + "ChartIndex", n);
            iBlock.setCustomData(field.getName() + "ChartTF", n2);
            if (iBlock.getStrategy() != null && iBlock.getStrategy().MarketData != null) {
                ChartData chartData = iBlock.getStrategy().MarketData.Chart(n);
                if (n2 != 0) {
                    chartData = chartData.cloneOnlyTF(n2);
                }
                ParameterAnnotationParser.setField(iBlock, field, chartData);
            }
        }
        catch (Exception exception) {
            iBlock.setCustomData(field.getName() + "ChartIndex", n);
            if (iBlock.getStrategy() != null && iBlock.getStrategy().MarketData != null) {
                ChartData chartData = iBlock.getStrategy().MarketData.Chart(n);
                if (n2 != 0) {
                    chartData = chartData.cloneForTF(n2);
                }
                ParameterAnnotationParser.setField(iBlock, field, chartData);
            }
            throw new BlockDefinitionException("Exception in getting DataSeries for chart: " + n);
        }
    }
}

