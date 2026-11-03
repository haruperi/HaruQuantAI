/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  org.jdom2.Element
 *  org.slf4j.Logger
 *  org.slf4j.LoggerFactory
 */
package com.strategyquant.tradinglib.blocks;

import com.strategyquant.tradinglib.BlockDefinitionException;
import com.strategyquant.tradinglib.ExitMethod;
import com.strategyquant.tradinglib.IBlock;
import com.strategyquant.tradinglib.Output;
import com.strategyquant.tradinglib.Parameter;
import com.strategyquant.tradinglib.blocks.OutputAnnotationHandler;
import com.strategyquant.tradinglib.blocks.ParameterAnnotationGenerator;
import com.strategyquant.tradinglib.blocks.ParameterAnnotationParser;
import java.lang.annotation.Annotation;
import java.lang.reflect.Field;
import org.jdom2.Element;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

public class AnnotationProcessor {
    public static final Logger Log = LoggerFactory.getLogger((String)"AnnotationProcessor");

    public static void wizardParseXml(IBlock iBlock, Field field, Element element) throws BlockDefinitionException {
        int n = 0;
        for (Annotation annotation : field.getAnnotations()) {
            if (annotation instanceof Parameter) {
                ParameterAnnotationParser.wizardParseXml((Parameter)annotation, iBlock, field, element);
            } else if (annotation instanceof Output) {
                OutputAnnotationHandler.wizardParseXml((Output)annotation, iBlock, field, element);
            }
            ++n;
        }
    }

    public static void wizardGenerateXml(Field field, Element element, IBlock iBlock, Class<?> clazz, boolean bl) throws BlockDefinitionException {
        if (field.getType().toString().equals("class [Lcom.strategyquant.tradinglib.ExitMethod;")) {
            try {
                ParameterAnnotationGenerator.wizardGenerateExitMethodParams(field, element, (ExitMethod[])field.get(iBlock), clazz, bl);
            }
            catch (IllegalAccessException | IllegalArgumentException exception) {
                Log.error("Parameter is not an ExitMethods array (2)!", (Throwable)exception);
                throw new BlockDefinitionException("Parameter is not an ExitMethods array (2)!");
            }
        } else {
            for (Annotation annotation : field.getAnnotations()) {
                if (!(annotation instanceof Parameter)) continue;
                ParameterAnnotationGenerator.wizardGenerateXml((Parameter)annotation, field, element, iBlock, clazz, bl, 0, null, null);
            }
        }
    }

    public static void wizardGenerateXmlForFormula(Field field, Element element, IBlock iBlock, Class<?> clazz, int n, String string) throws BlockDefinitionException {
        for (Annotation annotation : field.getAnnotations()) {
            if (!(annotation instanceof Parameter)) continue;
            ParameterAnnotationGenerator.wizardGenerateXml((Parameter)annotation, field, element, iBlock, clazz, false, n, string, null);
        }
    }

    public static void wizardParseExitTypesXml(IBlock iBlock, Field field, Element element) throws BlockDefinitionException {
        ParameterAnnotationParser.wizardParseXml(null, iBlock, field, element);
    }
}

