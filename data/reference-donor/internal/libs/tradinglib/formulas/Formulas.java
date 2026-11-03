/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  com.strategyquant.lib.snippets.CustomClassesLoader
 *  com.strategyquant.lib.snippets.CustomClassesReg
 *  com.strategyquant.lib.snippets.ICustomClasses
 *  org.jdom2.Content
 *  org.jdom2.Element
 *  org.slf4j.Logger
 *  org.slf4j.LoggerFactory
 */
package com.strategyquant.tradinglib.formulas;

import com.strategyquant.lib.snippets.CustomClassesLoader;
import com.strategyquant.lib.snippets.CustomClassesReg;
import com.strategyquant.lib.snippets.ICustomClasses;
import com.strategyquant.tradinglib.BlockDefinitionException;
import com.strategyquant.tradinglib.Formula;
import com.strategyquant.tradinglib.IBlock;
import com.strategyquant.tradinglib.IFormula;
import com.strategyquant.tradinglib.IgnoreInBuilder;
import com.strategyquant.tradinglib.blocks.AnnotationProcessor;
import com.strategyquant.tradinglib.formulas.FormulaComparatorByOrder;
import java.lang.reflect.Field;
import java.util.ArrayList;
import java.util.Collections;
import java.util.Comparator;
import java.util.HashMap;
import org.jdom2.Content;
import org.jdom2.Element;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

public class Formulas
implements ICustomClasses {
    public static final Logger Log = LoggerFactory.getLogger((String)"Formulas");
    private static Formulas instance;
    private HashMap<String, ArrayList<IBlock>> mapClasses = new HashMap();
    private Comparator<IBlock> comparatorByOrder;

    public Formulas() {
        CustomClassesReg.add((ICustomClasses)this);
        this.comparatorByOrder = new FormulaComparatorByOrder();
        this.initClassesMap("Formulas");
    }

    public static void init() throws Exception {
        if (instance != null) {
            throw new Exception("Formulas.init() called more than once!");
        }
        instance = new Formulas();
    }

    public static IFormula get(String string) throws BlockDefinitionException {
        if (instance == null) {
            throw new BlockDefinitionException("You have to call Formulas.init() on program startup!");
        }
        return instance._get(string);
    }

    private IFormula _get(String string) throws BlockDefinitionException {
        for (String string2 : this.mapClasses.keySet()) {
            ArrayList<IBlock> arrayList = this.mapClasses.get(string2);
            for (int i = 0; i < arrayList.size(); ++i) {
                IBlock iBlock = arrayList.get(i);
                if (!iBlock.getClass().getName().equals(string)) continue;
                return (IFormula)((Object)iBlock);
            }
        }
        throw new BlockDefinitionException("Cannot find formula '" + string + "'");
    }

    private void initClassesMap(String string) {
        try {
            this.mapClasses.clear();
            CustomClassesLoader customClassesLoader = new CustomClassesLoader(string);
            while (customClassesLoader.hasNext()) {
                String string2 = customClassesLoader.getNext();
                Object object = customClassesLoader.createInstance(string2);
                if (object instanceof IFormula && object instanceof IBlock) {
                    IBlock iBlock = (IBlock)object;
                    Class<?> clazz = iBlock.getClass();
                    Formula formula = clazz.getAnnotation(Formula.class);
                    if (formula == null) {
                        Log.error("Class " + clazz.getName() + " doesn't have @Formula annotation, it will be ignored!");
                        continue;
                    }
                    String string3 = formula.formula();
                    if (string3.equals("Null")) {
                        Log.error("Class " + clazz.getName() + " - @Formula annotation is missing formula definition!");
                        continue;
                    }
                    if (!this.mapClasses.containsKey(string3)) {
                        this.mapClasses.put(string3, new ArrayList());
                    }
                    ArrayList<IBlock> arrayList = this.mapClasses.get(string3);
                    arrayList.add(iBlock);
                    continue;
                }
                if (!Log.isDebugEnabled()) continue;
                Log.debug("Class: " + string2 + " is not an instance of block");
            }
            this.sortClasses();
        }
        catch (Exception exception) {
            Log.error("An error occured while loading custom classes.", (Throwable)exception);
        }
    }

    private void sortClasses() {
        for (String string : this.mapClasses.keySet()) {
            ArrayList<IBlock> arrayList = this.mapClasses.get(string);
            Collections.sort(arrayList, this.comparatorByOrder);
        }
    }

    public static void generateFormulasXml(Element element) throws BlockDefinitionException {
        if (instance == null) {
            throw new BlockDefinitionException("You have to call Blocks.init() on program startup!");
        }
        instance._generateFormulasXml(element);
    }

    private void _generateFormulasXml(Element element) throws BlockDefinitionException {
        for (String string : this.mapClasses.keySet()) {
            Element element2 = new Element("Formula");
            element2.setAttribute("key", string);
            for (IBlock iBlock : this.mapClasses.get(string)) {
                Element element3 = this.getFormulaItem(iBlock, 0, null);
                element2.addContent((Content)element3);
            }
            element.addContent((Content)element2);
        }
    }

    private Element getFormulaItem(IBlock iBlock, int n, String string) throws BlockDefinitionException {
        IgnoreInBuilder ignoreInBuilder;
        Element element = new Element("Item");
        Class<?> clazz = iBlock.getClass();
        Formula formula = clazz.getAnnotation(Formula.class);
        if (formula == null) {
            throw new BlockDefinitionException("This shouldn't happen!!!");
        }
        element.setAttribute("key", clazz.getName());
        element.setAttribute("name", formula.name().equals("Null") ? clazz.getSimpleName() : formula.name());
        if (formula.noneValue()) {
            element.setAttribute("noneValue", "true");
        }
        if ((ignoreInBuilder = clazz.getAnnotation(IgnoreInBuilder.class)) != null) {
            element.setAttribute("ignoreInBuilder", "true");
        }
        this.addFormulaParameters(iBlock, clazz, element, n, string);
        return element;
    }

    private void addFormulaParameters(IBlock iBlock, Class<?> clazz, Element element, int n, String string) throws BlockDefinitionException {
        for (Field field : clazz.getFields()) {
            AnnotationProcessor.wizardGenerateXmlForFormula(field, element, iBlock, clazz, n, string);
        }
    }

    public static void generateFormulaParameters(String string, Element element, int n, String string2) throws BlockDefinitionException {
        if (instance == null) {
            throw new BlockDefinitionException("You have to call Formulas.init() on program startup!");
        }
        instance._generateFormulaParameters(string, element, n, string2);
    }

    private void _generateFormulaParameters(String string, Element element, int n, String string2) throws BlockDefinitionException {
        for (IBlock iBlock : this.mapClasses.get(string)) {
            String string3;
            Element element2 = this.getFormulaItem(iBlock, n, string2);
            String string4 = element2.getAttributeValue("ignoreInBuilder");
            if (string4 != null && string4.equals("true") || (string3 = element2.getAttributeValue("noneValue")) != null && string3.equals("true")) continue;
            element.addContent((Content)element2);
        }
    }

    public void reload() throws Exception {
        this.initClassesMap("Formulas");
    }
}

