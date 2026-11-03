/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  com.strategyquant.datalib.DataSeries
 *  com.strategyquant.datalib.dataseries.TimeDataSeries
 *  com.strategyquant.lib.SQUtils
 *  org.jdom2.Content
 *  org.jdom2.Element
 *  org.slf4j.Logger
 *  org.slf4j.LoggerFactory
 */
package com.strategyquant.tradinglib.blocks;

import com.strategyquant.datalib.DataSeries;
import com.strategyquant.datalib.dataseries.TimeDataSeries;
import com.strategyquant.lib.SQUtils;
import com.strategyquant.tradinglib.BlockDefinitionException;
import com.strategyquant.tradinglib.Blocks;
import com.strategyquant.tradinglib.ChartData;
import com.strategyquant.tradinglib.Editor;
import com.strategyquant.tradinglib.Editors;
import com.strategyquant.tradinglib.ExitMethod;
import com.strategyquant.tradinglib.ForEngine;
import com.strategyquant.tradinglib.Formula;
import com.strategyquant.tradinglib.Help;
import com.strategyquant.tradinglib.IBlock;
import com.strategyquant.tradinglib.NoShift;
import com.strategyquant.tradinglib.Parameter;
import com.strategyquant.tradinglib.Required;
import com.strategyquant.tradinglib.SLPTValue;
import com.strategyquant.tradinglib.Variable;
import com.strategyquant.tradinglib.blocks.AnnotationHandler;
import com.strategyquant.tradinglib.blocks.annotations.DataSeriesChoice;
import com.strategyquant.tradinglib.exit.ExitMethodsList;
import java.lang.reflect.Field;
import java.util.List;
import org.jdom2.Content;
import org.jdom2.Element;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

public class ParameterAnnotationGenerator
extends AnnotationHandler {
    public static final Logger Log = LoggerFactory.getLogger((String)"ParameterAnnotationGenerator");

    public static void wizardGenerateXml(Parameter parameter, Field field, Element element, IBlock iBlock, Class<?> clazz, boolean bl, int n, String string, Element element2) throws BlockDefinitionException {
        String string2 = field.getType().getName();
        if (string2.equals("int") || string2.equals("long") || string2.equals("double") || string2.equals("boolean") || string2.equals("java.lang.String") || string2.equals("java.lang.Object") || string2.equals("com.strategyquant.tradinglib.Variable")) {
            ParameterAnnotationGenerator.wizardGeneratePrimitiveTypeXml(parameter, field, element, iBlock, clazz, string2, bl, n, element2);
        } else if (string2.equals("com.strategyquant.tradinglib.IFormula")) {
            ParameterAnnotationGenerator.wizardGenerateFormulaXml(parameter, field, element, iBlock, clazz, string2, bl, n, string, null);
        } else if (string2.equals("com.strategyquant.tradinglib.IBlock")) {
            ParameterAnnotationGenerator.wizardGenerateBlock(parameter, field, element, iBlock, clazz, string2, bl);
        } else if (string2.equals("[Lcom.strategyquant.tradinglib.IBlock;")) {
            ParameterAnnotationGenerator.wizardGenerateBlocks(parameter, field, element, iBlock, clazz, string2, bl);
        } else if (field.getType().isAssignableFrom(ChartData.class)) {
            ParameterAnnotationGenerator.wizardGenerateChartDataXml(parameter, field, element, iBlock, clazz, bl);
        } else if (field.getType().isAssignableFrom(DataSeries.class)) {
            ParameterAnnotationGenerator.wizardGenerateChartDataXml(parameter, field, element, iBlock, clazz, bl);
            ParameterAnnotationGenerator.wizardGenerateComputeFromXml(parameter, field, element, iBlock, clazz, bl);
        } else if (!field.getType().isAssignableFrom(TimeDataSeries.class)) {
            if (field.getType().toString().equals("class [Lcom.strategyquant.tradinglib.ExitMethod;")) {
                try {
                    ParameterAnnotationGenerator.wizardGenerateExitMethodParams(field, element, (ExitMethod[])field.get(iBlock), clazz, bl);
                }
                catch (IllegalAccessException | IllegalArgumentException exception) {
                    Log.error("Parameter is not an ExitMethods array!", (Throwable)exception);
                    throw new BlockDefinitionException("Parameter is not an ExitMethods array!");
                }
            } else {
                throw new BlockDefinitionException("Unsupported parameter type " + field.getType() + " in block '" + iBlock.getClass().getSimpleName() + "'!");
            }
        }
    }

    private static void wizardGenerateBlocks(Parameter parameter, Field field, Element element, IBlock iBlock, Class<?> clazz, String string, boolean bl) throws BlockDefinitionException {
        if (bl) {
            IBlock[] iBlockArray;
            try {
                iBlockArray = (IBlock[])field.get(iBlock);
            }
            catch (IllegalAccessException | IllegalArgumentException exception) {
                throw new BlockDefinitionException("Error getting blocks", exception);
            }
            for (IBlock iBlock2 : iBlockArray) {
                Element element2 = new Element("Block");
                element2.addContent((Content)Blocks.generateBlockTreeXml(iBlock2));
                element.addContent((Content)element2);
            }
        }
    }

    private static void wizardGenerateBlock(Parameter parameter, Field field, Element element, IBlock iBlock, Class<?> clazz, String string, boolean bl) throws BlockDefinitionException {
        if (bl) {
            IBlock iBlock2;
            try {
                iBlock2 = (IBlock)field.get(iBlock);
            }
            catch (IllegalAccessException | IllegalArgumentException exception) {
                throw new BlockDefinitionException("Error getting block", exception);
            }
            Element element2 = new Element("Block");
            element2.setAttribute("key", ParameterAnnotationGenerator.decorateFieldName(field.getName()));
            element2.addContent((Content)Blocks.generateBlockTreeXml(iBlock2));
            element.addContent((Content)element2);
        } else {
            Element element3 = ParameterAnnotationGenerator.getOrCreateParamCategory(element, parameter.category(), bl);
            Element element4 = new Element("Param");
            element4.setAttribute("key", ParameterAnnotationGenerator.decorateFieldName(field.getName()));
            element4.setAttribute("name", ParameterAnnotationGenerator.getFieldName(parameter.name(), SQUtils.insertUppercaseSpaces((String)field.getName())));
            element4.setAttribute("type", "value");
            if (ParameterAnnotationGenerator.isPriceFormula(iBlock)) {
                element4.setAttribute("valueType", "price");
            }
            element4.setAttribute("controlType", "value");
            if (!parameter.postfix().equals("Null")) {
                element4.setAttribute("postfix", parameter.postfix());
            }
            if (!parameter.standsFor().equals("Null")) {
                element4.setAttribute("standsFor", parameter.standsFor());
            }
            element3.addContent((Content)element4);
        }
    }

    static void wizardGenerateExitMethodParams(Field field, Element element, ExitMethod[] exitMethodArray, Class<?> clazz, boolean bl) throws BlockDefinitionException {
        Element element2 = ParameterAnnotationGenerator.getOrCreateParamCategory(element, "Exit methods", bl);
        for (ExitMethod exitMethod : ExitMethodsList.get().getAvailableClasses()) {
            exitMethod.generateXmlParams(element2, field, element, exitMethodArray, bl);
        }
    }

    private static boolean isPriceFormula(IBlock iBlock) {
        Formula formula = iBlock.getClass().getAnnotation(Formula.class);
        return formula != null && formula.priceLevel();
    }

    public static void wizardGenerateFormulaXml(Parameter parameter, Field field, Element element, IBlock iBlock, Class<?> clazz, String string, boolean bl, int n, String string2, Element element2) throws BlockDefinitionException {
        Required required;
        Editor editor;
        Element element3 = null;
        Element element4 = element2;
        if (element2 == null) {
            element3 = ParameterAnnotationGenerator.getOrCreateParamCategory(element, parameter.category(), bl);
            element4 = new Element("Param");
            element4.setAttribute("key", ParameterAnnotationGenerator.decorateFieldName(field.getName()));
            element4.setAttribute("name", ParameterAnnotationGenerator.getFieldName(parameter.name(), SQUtils.insertUppercaseSpaces((String)field.getName())));
        }
        element4.setAttribute("type", "double");
        element4.setAttribute("isFormula", "true");
        if (!parameter.defaultValue().equals("Null")) {
            element4.setAttribute("defaultValue", parameter.defaultValue());
        }
        if (!parameter.showIfDefault()) {
            element4.setAttribute("displayOnDefault", "false");
        }
        if ((editor = field.getAnnotation(Editor.class)) == null) {
            throw new BlockDefinitionException("Formula type field must have the editor defined!");
        }
        if (editor.type() == 200) {
            element4.setAttribute("controlType", editor.formulaName());
        } else {
            element4.setAttribute("controlType", Editors.convertToWizardConstant(editor.type()));
        }
        String string3 = ParameterAnnotationGenerator.getHelpValue(field);
        if (!string3.equals("Null")) {
            element4.setAttribute("help", string3);
        }
        if ((required = field.getAnnotation(Required.class)) != null) {
            element4.setAttribute("required", "true");
        }
        if (n != 0) {
            element4.setAttribute("exitMethod", "true");
            if (string2 != null) {
                element4.setAttribute("dependentOn", string2);
            }
            if (n == 2) {
                element4.setAttribute("exitMethodType", "SL");
            } else if (n == 3) {
                element4.setAttribute("exitMethodType", "PT");
            }
        }
        ParameterAnnotationGenerator.addForEngineAttribute(element4, field);
        if (element2 == null) {
            element3.addContent((Content)element4);
        }
        if (bl) {
            element4.addContent((Content)ParameterAnnotationGenerator.generateFormulaForParam(parameter, field, element, iBlock, clazz, string));
        }
    }

    private static Element generateFormulaForParam(Parameter parameter, Field field, Element element, IBlock iBlock, Class<?> clazz, String string) throws BlockDefinitionException {
        Element element2 = new Element("Formula");
        try {
            Object object = field.get(iBlock);
            if (object == null) {
                throw new BlockDefinitionException(String.format("Parameter '%s' in exit method/block '%s' is null!", field.getName(), iBlock.getClass().getSimpleName()));
            }
            element2.setAttribute("key", object.getClass().getCanonicalName());
            Element element3 = Blocks.generateBlockTreeXml((IBlock)object);
            if (element3 != null) {
                List list = element3.getChildren();
                int n = list.size();
                for (int i = 0; i < n; ++i) {
                    element2.addContent((Content)((Element)list.get(0)).detach());
                }
            }
        }
        catch (IllegalAccessException | IllegalArgumentException exception) {
            throw new BlockDefinitionException("Exception generating XML for formula!", exception);
        }
        return element2;
    }

    private static String getHelpValue(Field field) {
        Help help = field.getAnnotation(Help.class);
        if (help != null) {
            return help.value();
        }
        return "Null";
    }

    private static void wizardGenerateComputeFromXml(Parameter parameter, Field field, Element element, IBlock iBlock, Class<?> clazz, boolean bl) {
        String string = "ComputedFrom";
        String string2 = "Computed From";
        int n = 0;
        String string3 = "Default";
        String string4 = null;
        DataSeriesChoice dataSeriesChoice = field.getAnnotation(DataSeriesChoice.class);
        if (dataSeriesChoice != null) {
            string = dataSeriesChoice.key();
            string2 = dataSeriesChoice.name();
            n = parameter.defaultSeries();
            string3 = dataSeriesChoice.category();
            string4 = dataSeriesChoice.help();
        }
        Element element2 = ParameterAnnotationGenerator.getOrCreateParamCategory(element, string3, bl);
        Element element3 = new Element("Param");
        element3.setAttribute("key", ParameterAnnotationGenerator.decorateFieldName(string));
        element3.setAttribute("name", string2);
        element3.setAttribute("type", "int");
        element3.setAttribute("controlType", "combo");
        element3.setAttribute("values", "Close=0,Open=1,High=2,Low=3,Median=4,Typical=5,Weighted=6");
        element3.setAttribute("defaultValue", String.valueOf(n));
        if (string4 != null) {
            element3.setAttribute("help", string4);
        }
        if (bl) {
            int n2 = iBlock.getCustomData(field.getName() + "ComputedFrom");
            element3.addContent(Integer.toString(n2));
        }
        element2.addContent((Content)element3);
    }

    private static void wizardGenerateChartDataXml(Parameter parameter, Field field, Element element, IBlock iBlock, Class<?> clazz, boolean bl) {
        Element element2 = ParameterAnnotationGenerator.getOrCreateParamCategory(element, parameter.category(), bl);
        Element element3 = new Element("Param");
        element3.setAttribute("key", ParameterAnnotationGenerator.decorateFieldName("Chart"));
        element3.setAttribute("name", !parameter.name().equals("Null") ? parameter.name() : "Chart");
        element3.setAttribute("type", "data");
        element3.setAttribute("controlType", "dataVar");
        element3.setAttribute("defaultValue", String.valueOf(parameter.defaultChartIndex()));
        String string = ParameterAnnotationGenerator.getHelpValue(field);
        if (!string.equals("Null")) {
            element3.setAttribute("help", string);
        }
        if (bl) {
            Variable variable;
            int n = iBlock.getCustomData(field.getName() + "ChartIndex");
            element3.addContent(Integer.toString(n));
            if (iBlock.getStrategy() != null && (variable = iBlock.getStrategy().variables().getByField(iBlock, field.getName())) != null) {
                element3.setAttribute("variable", "true");
                element3.setAttribute("variableType", variable.translateType(variable.getInternalType()));
                element3.setText(variable.getId());
            }
        }
        element2.addContent((Content)element3);
    }

    private static void wizardGeneratePrimitiveTypeXml(Parameter parameter, Field field, Element element, IBlock iBlock, Class<?> clazz, String string, boolean bl, int n, Element element2) throws BlockDefinitionException {
        SLPTValue sLPTValue;
        Required required;
        Object object;
        Element element3 = null;
        Element element4 = element2;
        if (element2 == null) {
            element3 = ParameterAnnotationGenerator.getOrCreateParamCategory(element, parameter.category(), bl);
            element4 = new Element("Param");
            element4.setAttribute("key", ParameterAnnotationGenerator.decorateFieldName(field.getName()));
            element4.setAttribute("name", ParameterAnnotationGenerator.getFieldName(parameter.name(), SQUtils.insertUppercaseSpaces((String)field.getName())));
        }
        if (field.getName().equals("Shift") && (object = clazz.getAnnotation(NoShift.class)) != null) {
            return;
        }
        if (string.equals("java.lang.String")) {
            element4.setAttribute("type", "string");
        } else if (string.equals("java.lang.Object") || string.equals("com.strategyquant.tradinglib.Variable")) {
            element4.setAttribute("type", "none");
        } else {
            element4.setAttribute("type", string);
        }
        object = ParameterAnnotationGenerator.getDefaultValue(field, parameter.defaultValue());
        if (((String)object).endsWith(".0")) {
            object = ((String)object).substring(0, ((String)object).length() - 2);
        }
        if (!(string.equals("java.lang.Object") || string.equals("com.strategyquant.tradinglib.Variable") || ((String)object).equals("Null"))) {
            element4.setAttribute("defaultValue", (String)object);
        }
        if (!parameter.showIfDefault()) {
            element4.setAttribute("displayOnDefault", "false");
        }
        ParameterAnnotationGenerator.wizardGenerateEditorAttributes(element4, parameter, field, string);
        String string2 = ParameterAnnotationGenerator.getHelpValue(field);
        if (!string2.equals("Null")) {
            element4.setAttribute("help", string2);
        }
        if (!parameter.postfix().equals("Null")) {
            element4.setAttribute("postfix", parameter.postfix());
        }
        if ((required = field.getAnnotation(Required.class)) != null) {
            element4.setAttribute("required", "true");
        }
        if (n > 0) {
            element4.setAttribute("exitMethod", "true");
        }
        if ((sLPTValue = ParameterAnnotationGenerator.getSLPTAnnotation(field)) != null) {
            if (n == 2) {
                if (sLPTValue.value() == -1000) {
                    element4.setAttribute("genMinValue", Integer.toString(-1000005));
                    element4.setAttribute("genMaxValue", Integer.toString(-1000006));
                } else if (sLPTValue.value() == -2000) {
                    element4.setAttribute("genMinValue", Integer.toString(-1000007));
                    element4.setAttribute("genMaxValue", Integer.toString(-1000008));
                } else if (sLPTValue.value() == -3000) {
                    element4.setAttribute("genMinValue", Integer.toString(-1000009));
                    element4.setAttribute("genMaxValue", Integer.toString(-1000010));
                } else if (sLPTValue.value() == -4000) {
                    element4.setAttribute("genMinValue", Integer.toString(-1000019));
                    element4.setAttribute("genMaxValue", Integer.toString(-1000020));
                }
            }
            if (n == 3) {
                if (sLPTValue.value() == -1000) {
                    element4.setAttribute("genMinValue", Integer.toString(-1000011));
                    element4.setAttribute("genMaxValue", Integer.toString(-1000012));
                } else if (sLPTValue.value() == -2000) {
                    element4.setAttribute("genMinValue", Integer.toString(-1000013));
                    element4.setAttribute("genMaxValue", Integer.toString(-1000014));
                } else if (sLPTValue.value() == -3000) {
                    element4.setAttribute("genMinValue", Integer.toString(-1000015));
                    element4.setAttribute("genMaxValue", Integer.toString(-1000016));
                } else if (sLPTValue.value() == -4000) {
                    element4.setAttribute("genMinValue", Integer.toString(-1000017));
                    element4.setAttribute("genMaxValue", Integer.toString(-1000018));
                }
            }
        }
        if (parameter.builderMinValue() != -9999999.0) {
            element4.setAttribute("builderMinValue", SQUtils.doubleToString((double)parameter.builderMinValue()));
        }
        if (parameter.builderMaxValue() != -9999999.0) {
            element4.setAttribute("builderMaxValue", SQUtils.doubleToString((double)parameter.builderMaxValue()));
        }
        if (parameter.builderStep() != -9999999.0) {
            element4.setAttribute("builderStep", SQUtils.doubleToString((double)parameter.builderStep()));
        } else {
            element4.setAttribute("builderStep", SQUtils.doubleToString((double)parameter.step()));
        }
        ParameterAnnotationGenerator.addForEngineAttribute(element4, field);
        if (!parameter.standsFor().equals("Null")) {
            element4.setAttribute("standsFor", parameter.standsFor());
        }
        if (bl) {
            Object object2;
            element4.removeAttribute("help");
            boolean bl2 = false;
            if (iBlock.getStrategy() != null && (object2 = iBlock.getStrategy().variables().getByField(iBlock, field.getName())) != null) {
                element4.setAttribute("variable", "true");
                element4.setAttribute("variableType", ((Variable)object2).translateType(((Variable)object2).getInternalType()));
                element4.addContent(((Variable)object2).getId());
                bl2 = true;
            }
            if (!bl2) {
                object = null;
                try {
                    switch (string) {
                        case "int": {
                            object = Integer.toString(field.getInt(iBlock));
                            break;
                        }
                        case "long": {
                            object = Long.toString(field.getLong(iBlock));
                            break;
                        }
                        case "double": {
                            object = SQUtils.doubleToString((double)field.getDouble(iBlock));
                            break;
                        }
                        case "boolean": {
                            object = Boolean.toString(field.getBoolean(iBlock));
                            break;
                        }
                        case "java.lang.String": {
                            object = (String)field.get(iBlock);
                            break;
                        }
                        case "java.lang.Object": {
                            throw new BlockDefinitionException("Cannot set value of type Object!");
                        }
                    }
                }
                catch (IllegalAccessException | IllegalArgumentException exception) {
                    throw new BlockDefinitionException("Exception", exception);
                }
                if (object != null) {
                    element4.addContent((String)object);
                }
            }
        }
        if (element2 == null) {
            element3.addContent((Content)element4);
        }
    }

    private static void addForEngineAttribute(Element element, Field field) {
        ForEngine forEngine = field.getAnnotation(ForEngine.class);
        if (forEngine != null && !forEngine.value().equals("Null")) {
            String string = forEngine.value();
            element.setAttribute("forEngine", string);
        }
    }

    private static SLPTValue getSLPTAnnotation(Field field) {
        return field.getAnnotation(SLPTValue.class);
    }

    private static String getDefaultValue(Field field, String string) {
        if (!string.equals("Null")) {
            return string;
        }
        if (field.getName().equals("Shift")) {
            return "1";
        }
        if (field.getType().getName().equals("java.lang.String")) {
            return "";
        }
        return "10";
    }

    private static void wizardGenerateEditorAttributes(Element element, Parameter parameter, Field field, String string) throws BlockDefinitionException {
        int n;
        String string2 = field.getName();
        boolean bl = true;
        String string3 = null;
        if (string.equals("int") && string2.contains("Shift")) {
            element.setAttribute("controlType", "jspinnerVar");
            element.setAttribute("minValue", "0");
            element.setAttribute("maxValue", "1000");
            element.setAttribute("genMinValue", SQUtils.doubleToString((double)-1000001.0));
            element.setAttribute("genMaxValue", SQUtils.doubleToString((double)-1000002.0));
            element.setAttribute("paramType", "shift");
            element.setAttribute("step", "1");
            if (element.getAttribute("defaultValue") == null) {
                element.setAttribute("defaultValue", "1");
            }
            return;
        }
        if (string.equals("int") && (string2.contains("Period") || parameter.isPeriod())) {
            element.setAttribute("genMinValue", SQUtils.doubleToString((double)-1000003.0));
            element.setAttribute("genMaxValue", SQUtils.doubleToString((double)-1000004.0));
            element.setAttribute("paramType", "period");
        }
        if (string.equals("java.lang.String") && string2.equalsIgnoreCase("Symbol")) {
            if (parameter.allowAny()) {
                element.setAttribute("controlType", "symbolVarWithAny");
                element.setAttribute("defaultValue", "Current");
            } else {
                element.setAttribute("controlType", "symbolVar");
                element.setAttribute("defaultValue", "Current");
            }
            element.setAttribute("paramType", "symbol");
            return;
        }
        Editor editor = field.getAnnotation(Editor.class);
        if (editor != null && editor.type() != 0) {
            n = string.equals("java.lang.String") ? (editor.type() == 20 ? 30 : editor.type()) : (editor.type() == 30 ? 20 : editor.type());
            bl = editor.allowVariables();
            string3 = editor.values();
        } else if (string.equals("java.lang.String")) {
            n = 30;
            bl = false;
        } else if (string.equals("boolean")) {
            n = 100;
            bl = false;
        } else {
            n = 20;
            bl = true;
        }
        element.setAttribute("controlType", Editors.convertToWizardConstant(n));
        if (!(string.equals("java.lang.String") || n != 10 && n != 20)) {
            element.setAttribute("minValue", SQUtils.doubleToString((double)parameter.minValue()));
            element.setAttribute("maxValue", SQUtils.doubleToString((double)parameter.maxValue()));
            element.setAttribute("step", SQUtils.doubleToString((double)parameter.step()));
        }
        if (string3 != null && !string3.equals("Null")) {
            element.setAttribute("values", string3);
        }
    }
}

