/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  com.strategyquant.lib.SQUtils
 *  com.strategyquant.lib.snippets.CustomClasses
 *  com.strategyquant.lib.snippets.NonexistingCustomClassException
 *  org.jdom2.Content
 *  org.jdom2.Element
 */
package com.strategyquant.tradinglib.moneymanagement;

import com.strategyquant.lib.SQUtils;
import com.strategyquant.lib.snippets.CustomClasses;
import com.strategyquant.lib.snippets.NonexistingCustomClassException;
import com.strategyquant.tradinglib.BlockDefinitionException;
import com.strategyquant.tradinglib.MoneyManagementMethod;
import com.strategyquant.tradinglib.Parameter;
import com.strategyquant.tradinglib.blocks.AnnotationHandler;
import com.strategyquant.tradinglib.blocks.ParameterAnnotationGenerator;
import com.strategyquant.tradinglib.moneymanagement.MMComparatorByOrder;
import java.lang.reflect.Field;
import java.util.Collections;
import java.util.List;
import org.jdom2.Content;
import org.jdom2.Element;

public class MoneyManagementMethodsList
extends CustomClasses<MoneyManagementMethod> {
    private static MoneyManagementMethodsList instance;
    private MMComparatorByOrder comparatorByOrder;

    public static MoneyManagementMethodsList get() {
        if (instance == null) {
            instance = new MoneyManagementMethodsList();
        }
        return instance;
    }

    private MoneyManagementMethodsList() {
        this.setDirName("MoneyManagement");
        this.setExpectedClassType(MoneyManagementMethod.class);
        this.comparatorByOrder = new MMComparatorByOrder();
        this.loadAvailableClasses();
    }

    public static MoneyManagementMethod create(String string, Object ... objectArray) throws NonexistingCustomClassException {
        return MoneyManagementMethodsList.get()._create(string, objectArray);
    }

    private MoneyManagementMethod _create(String string, Object[] objectArray) throws NonexistingCustomClassException {
        for (MoneyManagementMethod moneyManagementMethod : this.getAvailableClasses()) {
            if (!moneyManagementMethod.getClass().getSimpleName().equals(string)) continue;
            try {
                return (MoneyManagementMethod)moneyManagementMethod.newInstance(objectArray);
            }
            catch (Exception exception) {
                Log.error("Cannot create new instance", (Throwable)exception);
            }
        }
        throw new NonexistingCustomClassException(string);
    }

    public static MoneyManagementMethod createFromXml(Element element) throws NonexistingCustomClassException {
        return MoneyManagementMethodsList.get()._createFromXml(element);
    }

    private MoneyManagementMethod _createFromXml(Element element) throws NonexistingCustomClassException {
        if (element == null) {
            return null;
        }
        String string = element.getAttributeValue("type");
        if (string == null || string.equals("MMNone")) {
            return null;
        }
        for (MoneyManagementMethod moneyManagementMethod : this.getAvailableClasses()) {
            if (!moneyManagementMethod.getClass().getSimpleName().equals(string)) continue;
            try {
                MoneyManagementMethod moneyManagementMethod2 = moneyManagementMethod.newInstance();
                moneyManagementMethod2.setMethodFromXML(element);
                return moneyManagementMethod2;
            }
            catch (Exception exception) {
                Log.error("Cannot create new instance", (Throwable)exception);
            }
        }
        throw new NonexistingCustomClassException(string);
    }

    public static void generateMethodsXml(Element element) throws BlockDefinitionException {
        MoneyManagementMethodsList.get()._generateMethodsXml(element);
    }

    private void _generateMethodsXml(Element element) throws BlockDefinitionException {
        for (MoneyManagementMethod moneyManagementMethod : this.getAvailableClasses()) {
            Element element2 = new Element("Item");
            Class<?> clazz = moneyManagementMethod.getClass();
            element2.setAttribute("key", clazz.getSimpleName());
            element2.setAttribute("name", moneyManagementMethod.getName());
            Element element3 = new Element("Description");
            element3.addContent(moneyManagementMethod.getNote());
            element2.addContent((Content)element3);
            Element element4 = new Element("Params");
            element2.addContent((Content)element4);
            for (Field field : clazz.getFields()) {
                Parameter parameter = field.getAnnotation(Parameter.class);
                if (parameter == null) continue;
                Element element5 = new Element("Param");
                element5.setAttribute("key", AnnotationHandler.decorateFieldName(field.getName()));
                element5.setAttribute("name", AnnotationHandler.getFieldName(parameter.name(), SQUtils.insertUppercaseSpaces((String)field.getName())));
                String string = field.getType().getName();
                if (!(string.equals("int") || string.equals("long") || string.equals("double") || string.equals("boolean") || string.equals("java.lang.String"))) {
                    throw new BlockDefinitionException("Parameter '" + field.getName() + "' has an unsupported type!");
                }
                ParameterAnnotationGenerator.wizardGenerateXml(parameter, field, null, null, clazz, false, 0, null, element5);
                element4.addContent((Content)element5);
            }
            element.addContent((Content)element2);
        }
    }

    public void loadAvailableClasses() {
        super.loadAvailableClasses();
        List list = super.getAvailableClasses();
        Collections.sort(list, this.comparatorByOrder);
    }

    public static MoneyManagementMethod loadMMMethodFromXML(Element element) throws Exception {
        try {
            Element element2 = element.getChild("Strategy").getChild("MoneyManagement");
            Element element3 = element2.getChild("Method");
            element3.setAttribute("type", element2.getAttributeValue("type"));
            MoneyManagementMethod moneyManagementMethod = MoneyManagementMethodsList.createFromXml(element3);
            if (moneyManagementMethod == null) {
                throw new Exception("Cannot create MM method from XML");
            }
            return moneyManagementMethod;
        }
        catch (Exception exception) {
            Log.error("Cannot get strategy MoneyManagement settings. Using FixedSize 0.1...");
            return MoneyManagementMethodsList.create("FixedSize", 0.1);
        }
    }
}

