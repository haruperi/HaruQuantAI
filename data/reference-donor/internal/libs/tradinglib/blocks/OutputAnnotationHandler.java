/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  com.strategyquant.datalib.DataSeries
 *  com.strategyquant.lib.SQUtils
 *  org.jdom2.Content
 *  org.jdom2.Element
 */
package com.strategyquant.tradinglib.blocks;

import com.strategyquant.datalib.DataSeries;
import com.strategyquant.lib.SQUtils;
import com.strategyquant.tradinglib.BlockDefinitionException;
import com.strategyquant.tradinglib.Editors;
import com.strategyquant.tradinglib.IBlock;
import com.strategyquant.tradinglib.Output;
import com.strategyquant.tradinglib.blocks.AnnotationHandler;
import java.lang.annotation.Annotation;
import java.lang.reflect.Field;
import org.jdom2.Content;
import org.jdom2.Element;

public class OutputAnnotationHandler
extends AnnotationHandler {
    public static void wizardParseXml(Output output, IBlock iBlock, Field field, Element element) throws BlockDefinitionException {
        if (!element.getName().equals("Item")) {
            throw new BlockDefinitionException("@Output must be used on Item node!");
        }
        if (!field.getType().isAssignableFrom(DataSeries.class)) {
            throw new BlockDefinitionException("@Output parameter must have DataSeries type!");
        }
        Class<?> clazz = iBlock.getClass();
        int n = OutputAnnotationHandler.countOutputs(clazz);
        if (n > 1) {
            int n2 = (int)OutputAnnotationHandler.getParamNumberValue(iBlock, field, element.getChildren(), "#Line#");
            for (Field field2 : clazz.getFields()) {
                if (!field2.getName().equals("OutputIndex")) continue;
                OutputAnnotationHandler.setField(iBlock, field2, n2);
            }
        }
    }

    /*
     * WARNING - void declaration
     */
    public static void wizardGenerateXml(Class<?> clazz, Element element, IBlock iBlock, Class<?> clazz2, boolean bl) throws BlockDefinitionException {
        int n = 0;
        StringBuilder stringBuilder = new StringBuilder();
        block18: for (Field object : clazz.getFields()) {
            Annotation[] annotationArray = object.getAnnotations();
            int n2 = annotationArray.length;
            for (int i = 0; i < n2; ++i) {
                Annotation annotation = annotationArray[i];
                if (!(annotation instanceof Output)) continue;
                if (stringBuilder.length() != 0) {
                    stringBuilder.append(",");
                }
                stringBuilder.append(OutputAnnotationHandler.getFieldName(((Output)annotation).name(), object.getName()));
                stringBuilder.append("=");
                stringBuilder.append(n);
                ++n;
                continue block18;
            }
        }
        if (n <= 1) {
            return;
        }
        Element element2 = OutputAnnotationHandler.getOrCreateParamCategory(element, "Line", bl);
        Element element3 = new Element("Param");
        element3.setAttribute("key", "#Line#");
        element3.setAttribute("name", "Line");
        element3.setAttribute("type", "int");
        element3.setAttribute("controlType", Editors.convertToWizardConstant(40));
        if (!stringBuilder.toString().equals("Null")) {
            element3.setAttribute("values", stringBuilder.toString());
        }
        element3.setAttribute("defaultValue", "0");
        if (bl) {
            void var10_20;
            Field field = null;
            for (Field field2 : clazz.getFields()) {
                if (!field2.getName().equals("OutputIndex")) continue;
                field = field2;
            }
            if (field == null) {
                throw new BlockDefinitionException("There is no OutputIndex field in this block object!");
            }
            element3.removeAttribute("help");
            Object var10_14 = null;
            try {
                String string;
                switch (string = field.getType().getName()) {
                    case "int": {
                        String string2 = Integer.toString(field.getInt(iBlock));
                        break;
                    }
                    case "long": {
                        String string3 = Long.toString(field.getLong(iBlock));
                        break;
                    }
                    case "double": {
                        String string4 = SQUtils.doubleToString((double)field.getDouble(iBlock));
                        break;
                    }
                    case "boolean": {
                        String string5 = Boolean.toString(field.getBoolean(iBlock));
                        break;
                    }
                    case "java.lang.String": {
                        String string6 = (String)field.get(iBlock);
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
            if (var10_20 != null) {
                element3.addContent((String)var10_20);
            }
        }
        element2.addContent((Content)element3);
    }

    private static int countOutputs(Class<?> clazz) {
        int n = 0;
        for (Field field : clazz.getFields()) {
            for (Annotation annotation : field.getAnnotations()) {
                if (!(annotation instanceof Output)) continue;
                ++n;
            }
        }
        return n;
    }
}

