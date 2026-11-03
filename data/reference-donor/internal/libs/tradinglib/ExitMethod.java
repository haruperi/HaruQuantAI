/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  com.strategyquant.datalib.TradingException
 *  com.strategyquant.lib.SQUtils
 *  com.strategyquant.lib.SettingsMap
 *  it.unimi.dsi.fastutil.ints.Int2IntOpenHashMap
 *  org.jdom2.Content
 *  org.jdom2.Element
 *  org.slf4j.Logger
 *  org.slf4j.LoggerFactory
 */
package com.strategyquant.tradinglib;

import com.strategyquant.datalib.TradingException;
import com.strategyquant.lib.SQUtils;
import com.strategyquant.lib.SettingsMap;
import com.strategyquant.tradinglib.BlockDefinitionException;
import com.strategyquant.tradinglib.Editor;
import com.strategyquant.tradinglib.ExitType;
import com.strategyquant.tradinglib.ForEngine;
import com.strategyquant.tradinglib.IBlock;
import com.strategyquant.tradinglib.ILiveOrder;
import com.strategyquant.tradinglib.Parameter;
import com.strategyquant.tradinglib.StrategyBase;
import com.strategyquant.tradinglib.blocks.AnnotationHandler;
import com.strategyquant.tradinglib.blocks.AnnotationProcessor;
import com.strategyquant.tradinglib.blocks.ParameterAnnotationGenerator;
import com.strategyquant.tradinglib.debug.Debugger;
import com.strategyquant.tradinglib.exit.ExitMethodsList;
import com.strategyquant.tradinglib.formulas.Formulas;
import it.unimi.dsi.fastutil.ints.Int2IntOpenHashMap;
import java.lang.annotation.Annotation;
import java.lang.reflect.Constructor;
import java.lang.reflect.Field;
import java.util.ArrayList;
import java.util.Map;
import org.jdom2.Content;
import org.jdom2.Element;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

public abstract class ExitMethod
extends Debugger
implements IBlock {
    private static final int UseInitialSLPTHash = "UseInitialSLPT".hashCode();
    public static final Logger Log = LoggerFactory.getLogger((String)"ExitMethod");
    public StrategyBase Strategy;
    private StrategyBase nonXmlStrategy = null;
    private Int2IntOpenHashMap customData = null;
    private int exitType = 0;
    private int returnType = 0;
    private int minSLPips = -1;
    private int maxSLPips = -1;
    private int minPTPips = -1;
    private int maxPTPips = -1;

    public abstract double computeValue(byte var1, StrategyBase var2, String var3, double var4) throws TradingException;

    public abstract void setForOrder(ILiveOrder var1, StrategyBase var2) throws TradingException;

    public ExitMethod newInstance(StrategyBase strategyBase, ArrayList<Element> arrayList) throws BlockDefinitionException {
        try {
            Constructor<?> constructor = this.getClass().getConstructor(new Class[0]);
            ExitMethod exitMethod = (ExitMethod)SQUtils.invokeUnchecked(constructor, (Object[])new Object[0]);
            exitMethod.initialize(strategyBase, arrayList);
            return exitMethod;
        }
        catch (NoSuchMethodException | SecurityException exception) {
            exception.printStackTrace();
            throw new BlockDefinitionException("Cannot create ExitMethod", exception);
        }
    }

    private void initialize(StrategyBase strategyBase, ArrayList<Element> arrayList) throws BlockDefinitionException {
        this.Strategy = strategyBase;
        if (arrayList != null) {
            this.parseXml(arrayList);
        }
    }

    private void parseXml(ArrayList<Element> arrayList) throws BlockDefinitionException {
        Class<?> clazz = this.getClass();
        Element element = new Element("Item");
        for (Element element2 : arrayList) {
            Element element3 = element2.clone();
            this.fixKey(element3);
            element.addContent((Content)element3);
        }
        for (Field field : clazz.getFields()) {
            AnnotationProcessor.wizardParseXml(this, field, element);
            int n = this.getFieldExitType(field);
            if (n == 0) continue;
            this.exitType = n;
        }
    }

    private int getFieldExitType(Field field) {
        for (Annotation annotation : field.getAnnotations()) {
            if (!(annotation instanceof ExitType)) continue;
            return ((ExitType)annotation).value();
        }
        return 0;
    }

    private void fixKey(Element element) {
        String string = element.getAttributeValue("key");
        String[] stringArray = string.split("\\.");
        StringBuilder stringBuilder = new StringBuilder("#");
        stringBuilder.append(stringArray[1]);
        element.setAttribute("key", stringBuilder.toString());
    }

    public void generateXmlParams(Element element, Field field, Element element2, ExitMethod[] exitMethodArray, boolean bl) throws BlockDefinitionException {
        Class<?> clazz = this.getClass();
        String string = clazz.getSimpleName();
        String string2 = null;
        for (Field field2 : clazz.getFields()) {
            ExitMethod exitMethod;
            Parameter parameter = field2.getAnnotation(Parameter.class);
            if (parameter == null) continue;
            Element element3 = new Element("Param");
            String string3 = field2.getName();
            String string4 = String.format("%s.%s", string, string3);
            String string5 = field2.getType().getName();
            element3.setAttribute("key", AnnotationHandler.decorateFieldName(string4));
            element3.setAttribute("name", AnnotationHandler.getFieldName(parameter.name(), SQUtils.insertUppercaseSpaces((String)field2.getName())));
            if (string5.equals("java.lang.String")) {
                element3.setAttribute("type", "string");
            } else if (string5.equals("java.lang.Object")) {
                element3.setAttribute("type", "none");
            } else {
                element3.setAttribute("type", string5);
            }
            int n = 1;
            ExitType exitType = field2.getAnnotation(ExitType.class);
            if (exitType != null) {
                n = exitType.value();
            }
            if (string5.equals("int") || string5.equals("long") || string5.equals("double") || string5.equals("boolean") || string5.equals("java.lang.String") || string5.equals("java.lang.Object")) {
                exitMethod = this.findThisExitMethod(bl, exitMethodArray);
                if (exitMethod != null) {
                    ParameterAnnotationGenerator.wizardGenerateXml(parameter, field2, element2, exitMethod, clazz, bl, n, string2, element3);
                }
            } else if (string5.equals("com.strategyquant.tradinglib.IFormula")) {
                element3.setAttribute("type", "formula");
                exitMethod = this.findThisExitMethod(bl, exitMethodArray);
                if (exitMethod != null) {
                    ParameterAnnotationGenerator.wizardGenerateFormulaXml(parameter, field2, element2, exitMethod, clazz, string5, bl, n, string2, element3);
                }
            }
            element.addContent((Content)element3);
            string2 = string4;
        }
    }

    private ExitMethod findThisExitMethod(boolean bl, ExitMethod[] exitMethodArray) {
        if (exitMethodArray != null) {
            for (int i = 0; i < exitMethodArray.length; ++i) {
                if (this.getClass().getCanonicalName().hashCode() != exitMethodArray[i].getClass().getCanonicalName().hashCode()) continue;
                return exitMethodArray[i];
            }
        }
        if (!bl && exitMethodArray == null) {
            for (ExitMethod exitMethod : ExitMethodsList.get().getAvailableClasses()) {
                if (this.getClass().getCanonicalName().hashCode() != exitMethod.getClass().getCanonicalName().hashCode()) continue;
                return exitMethod;
            }
        }
        return null;
    }

    public void createExitMethodXml(Element element) throws BlockDefinitionException {
        Class<?> clazz = this.getClass();
        String string = clazz.getSimpleName();
        String string2 = null;
        for (Field field : clazz.getFields()) {
            Annotation annotation;
            Parameter parameter = field.getAnnotation(Parameter.class);
            if (parameter == null) continue;
            Element element2 = new Element("ExitRule");
            String string3 = field.getName();
            String string4 = String.format("%s.%s", string, string3);
            element2.setAttribute("key", string4);
            element2.setAttribute("name", SQUtils.insertUppercaseSpaces((String)string3));
            element2.setAttribute("probability", "50");
            if (string2 != null) {
                element2.setAttribute("dependentOn", string2);
            }
            String string5 = field.getType().getName();
            int n = 1;
            ExitType exitType = field.getAnnotation(ExitType.class);
            if (exitType != null) {
                n = exitType.value();
            }
            if (string5.equals("int") || string5.equals("long") || string5.equals("double") || string5.equals("boolean") || string5.equals("java.lang.String") || string5.equals("java.lang.Object")) {
                element2.setAttribute("type", string5);
                ParameterAnnotationGenerator.wizardGenerateXml(parameter, field, element2, null, clazz, false, n, string2, null);
            } else if (string5.equals("com.strategyquant.tradinglib.IFormula")) {
                element2.setAttribute("type", "formula");
                annotation = field.getAnnotation(Editor.class);
                if (annotation == null) {
                    throw new BlockDefinitionException("Parameter '" + string3 + "' has type formula, but doesn't have Formula editor specified!");
                }
                Formulas.generateFormulaParameters(annotation.formulaName(), element2, n, string2);
            }
            annotation = clazz.getAnnotation(ForEngine.class);
            if (annotation != null && !annotation.value().equals("Null")) {
                String string6 = annotation.value();
                element2.setAttribute("forEngine", string6);
            }
            element.addContent((Content)element2);
            string2 = string4;
        }
    }

    @Override
    public double evaluateBlock() throws TradingException {
        throw new TradingException("Not used here!");
    }

    @Override
    public double evaluateBlock(int n) throws TradingException {
        throw new TradingException("Not used here!");
    }

    @Override
    public IBlock newInstance(StrategyBase strategyBase, Element element) throws BlockDefinitionException {
        throw new BlockDefinitionException("Not used here!");
    }

    @Override
    public StrategyBase getStrategy() {
        return this.Strategy != null ? this.Strategy : this.nonXmlStrategy;
    }

    @Override
    public IBlock clone(boolean bl, StrategyBase strategyBase) throws BlockDefinitionException {
        throw new BlockDefinitionException("Not used here!");
    }

    @Override
    public void setCustomData(String string, int n) {
        if (this.customData == null) {
            this.customData = new Int2IntOpenHashMap();
        }
        this.customData.put(string.hashCode(), n);
    }

    @Override
    public int getCustomData(String string) {
        if (this.customData == null || !this.customData.containsKey(string.hashCode())) {
            return Integer.MIN_VALUE;
        }
        return this.customData.get(string.hashCode());
    }

    @Override
    public void copyCustomData(IBlock iBlock) {
        if (iBlock instanceof ExitMethod) {
            ExitMethod exitMethod = (ExitMethod)iBlock;
            if (exitMethod.customData != null) {
                if (this.customData == null) {
                    this.customData = new Int2IntOpenHashMap();
                }
                this.customData.putAll((Map)exitMethod.customData);
            }
        }
    }

    public int getExitType() {
        return this.exitType;
    }

    @Override
    public int getReturnType() {
        return this.returnType;
    }

    @Override
    public void setReturnType(int n) {
        this.returnType = n;
    }

    public double correctSLPT(ILiveOrder iLiveOrder, double d, boolean bl) {
        return this.correctSLPT(iLiveOrder.getOpenPrice(), d, iLiveOrder.getDirection(), iLiveOrder.getInstrumentInfo().tickSize, bl);
    }

    public double correctSLPT(double d, double d2, int n, double d3, boolean bl) {
        int n2;
        SettingsMap settingsMap;
        if (this.minSLPips < 0) {
            settingsMap = this.Strategy.getSettings();
            this.minSLPips = settingsMap.getInt("MinMaxSLPT.MinimumSL", 0);
            this.maxSLPips = settingsMap.getInt("MinMaxSLPT.MaximumSL", 0);
        }
        if (this.minPTPips < 0) {
            settingsMap = this.Strategy.getSettings();
            this.minPTPips = settingsMap.getInt("MinMaxSLPT.MinimumPT", 0);
            this.maxPTPips = settingsMap.getInt("MinMaxSLPT.MaximumPT", 0);
        }
        int n3 = n2 = n > 0 && !bl || n < 0 && bl ? 1 : -1;
        if (bl) {
            double d4;
            if (this.minSLPips > 0) {
                d4 = d + (double)(n2 * this.minSLPips) * d3;
                double d5 = d2 = n2 > 0 ? Math.max(d4, d2) : Math.min(d4, d2);
            }
            if (this.maxSLPips > 0) {
                d4 = d + (double)(n2 * this.maxSLPips) * d3;
                d2 = n2 > 0 ? Math.min(d4, d2) : Math.max(d4, d2);
            }
        } else {
            double d6;
            if (this.minPTPips > 0) {
                d6 = d + (double)(n2 * this.minPTPips) * d3;
                double d7 = d2 = n2 > 0 ? Math.max(d6, d2) : Math.min(d6, d2);
            }
            if (this.maxPTPips > 0) {
                d6 = d + (double)(n2 * this.maxPTPips) * d3;
                d2 = n2 > 0 ? Math.min(d6, d2) : Math.max(d6, d2);
            }
        }
        return d2;
    }

    public boolean setExit(ILiveOrder iLiveOrder, StrategyBase strategyBase) throws TradingException {
        return false;
    }

    @Override
    public Element getCustomBlockXml(int n) throws BlockDefinitionException {
        throw new BlockDefinitionException("Not implemented for this!");
    }

    protected boolean isInitialSLPTApplied(StrategyBase strategyBase) {
        SettingsMap settingsMap = strategyBase.getSettings();
        boolean bl = settingsMap.containsKey(UseInitialSLPTHash) && (Boolean)settingsMap.get(UseInitialSLPTHash) != false;
        return bl;
    }

    protected boolean shouldApplySLPTToOrder(ILiveOrder iLiveOrder, StrategyBase strategyBase) throws TradingException {
        boolean bl;
        boolean bl2 = bl = strategyBase.getEngine() == 56756755 || strategyBase.getEngine() == 938213070;
        if (bl) {
            return this.isInitialSLPTApplied(strategyBase) || strategyBase.Time() >= iLiveOrder.getOpenTime();
        }
        return true;
    }
}

