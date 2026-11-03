/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  com.strategyquant.lib.app.MainApp
 *  org.jdom2.Content
 *  org.jdom2.Element
 *  org.slf4j.Logger
 *  org.slf4j.LoggerFactory
 */
package com.strategyquant.tradinglib.util;

import com.strategyquant.lib.app.MainApp;
import com.strategyquant.tradinglib.SQStats;
import java.lang.reflect.Method;
import java.net.URLClassLoader;
import org.jdom2.Content;
import org.jdom2.Element;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

public class TradingLibUtil {
    private static final Logger Log = LoggerFactory.getLogger(TradingLibUtil.class);

    public static Object elementToValue(Element element) {
        Content content = element.getContent(0);
        String string = element.getAttributeValue("type");
        Object object = null;
        if (string == null) {
            return null;
        }
        switch (string) {
            case "String": {
                object = content.getValue().intern();
                break;
            }
            case "Byte": {
                object = Byte.parseByte(content.getValue());
                break;
            }
            case "Short": {
                object = Short.parseShort(content.getValue());
                break;
            }
            case "Integer": {
                object = Integer.parseInt(content.getValue());
                break;
            }
            case "Long": {
                object = Long.parseLong(content.getValue());
                break;
            }
            case "Float": {
                object = Float.valueOf(Float.parseFloat(content.getValue()));
                break;
            }
            case "Double": {
                object = Double.parseDouble(content.getValue());
                break;
            }
            case "Element": {
                object = (Element)element.getChildren().get(0);
                break;
            }
            default: {
                Throwable throwable = null;
                try {
                    return TradingLibUtil.createInstance(string, (Element)element.getChildren().get(0));
                }
                catch (Exception exception) {
                    throwable = null;
                    try {
                        return TradingLibUtil.createInstance(string, element);
                    }
                    catch (Exception exception2) {
                        Log.error("Error while instantiating object of type using child: '" + string + "'. Exc.", throwable);
                        Log.error("Error while instantiating object of type using element: '" + string + "'. Exc.", (Throwable)exception2);
                    }
                }
            }
        }
        return object;
    }

    private static Object createInstance(String string, Element element) throws Exception {
        URLClassLoader uRLClassLoader;
        Class<?> clazz = null;
        if (!string.startsWith("SQ.")) {
            if (string.endsWith("SQStats")) {
                SQStats sQStats = new SQStats();
                sQStats.setFromXML(element);
                return sQStats;
            }
            if (string.contains("com.strategyquant.lib.trading.")) {
                string = string.replace("com.strategyquant.lib.trading.", "com.strategyquant.tradinglib.");
            } else if (string.contains("com.strategyquant.lib.optimization.")) {
                string = string.replace("com.strategyquant.lib.optimization.", "com.strategyquant.tradinglib.optimization.");
            }
            clazz = Class.forName(string);
        } else {
            uRLClassLoader = MainApp.getSnippetsClassLoader();
            clazz = uRLClassLoader.loadClass(string);
        }
        if (clazz != null) {
            uRLClassLoader = clazz.newInstance();
            Method method = clazz.getMethod("setFromXML", Element.class);
            method.invoke((Object)uRLClassLoader, element);
            return uRLClassLoader;
        }
        return null;
    }
}

