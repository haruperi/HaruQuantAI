/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  com.strategyquant.lib.XMLUtil
 *  com.strategyquant.lib.app.MainApp
 *  com.strategyquant.lib.constants.SQPaths
 *  org.jdom2.Content
 *  org.jdom2.Element
 *  org.slf4j.Logger
 *  org.slf4j.LoggerFactory
 */
package com.strategyquant.indicatorTester;

import com.strategyquant.indicatorTester.IndicatorInfo;
import com.strategyquant.indicatorTester.IndicatorsLoader;
import com.strategyquant.lib.XMLUtil;
import com.strategyquant.lib.app.MainApp;
import com.strategyquant.lib.constants.SQPaths;
import java.io.File;
import java.util.concurrent.locks.StampedLock;
import org.jdom2.Content;
import org.jdom2.Element;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

public class IndicatorTesterConfig {
    private static final Logger Log = LoggerFactory.getLogger(IndicatorTesterConfig.class);
    public static final String defaultConfigFileName = "IndicatorTester.xml";
    public static final String defaultConfigFilePath = SQPaths.settingsDirPath + "/IndicatorTesterConfigs/" + "IndicatorTester.xml";
    private static Element lastConfig;
    private static String lastConfigPath;
    private static StampedLock lock;

    public static Element getConfig() {
        long l = lock.readLock();
        try {
            Element element = lastConfig != null ? lastConfig : IndicatorTesterConfig.load(null);
            return element;
        }
        finally {
            lock.unlock(l);
        }
    }

    public static String getConfigPath() {
        return lastConfigPath;
    }

    public static void resetConfigPath() {
        long l = lock.writeLock();
        try {
            lastConfigPath = null;
        }
        finally {
            lock.unlock(l);
        }
    }

    /*
     * WARNING - Removed try catching itself - possible behaviour change.
     */
    public static Element load(String string) {
        if (string != null) {
            MainApp.settings().set("IndicatorTesterPath", string);
            MainApp.settings().save();
        } else {
            string = MainApp.settings().get("IndicatorTesterPath");
        }
        if (string == null) {
            string = defaultConfigFilePath;
        }
        lastConfigPath = string;
        File file = new File(string);
        if (file.exists()) {
            long l = lock.writeLock();
            try {
                Element element = lastConfig = XMLUtil.fileToXmlElement((File)file);
                return element;
            }
            catch (Exception exception) {
                Log.error("Error while reading indicator tester config. ", (Throwable)exception);
            }
            finally {
                lock.unlock(l);
            }
        }
        Element element = IndicatorTesterConfig.createDefaultConfig("MetaTrader4", "300");
        return element;
    }

    /*
     * WARNING - Removed try catching itself - possible behaviour change.
     */
    public static Element createDefaultConfig(String string, String string2) {
        Element element = new Element("IndicatorTester");
        Element element2 = new Element("Engine");
        element2.setText(string);
        Element element3 = new Element("BarsToReserve");
        element3.setText(string2);
        Element element4 = new Element("Tests");
        element.addContent((Content)element2);
        element.addContent((Content)element3);
        element.addContent((Content)element4);
        long l = lock.writeLock();
        try {
            lastConfig = element;
        }
        finally {
            lock.unlock(l);
        }
        lastConfigPath = null;
        return element;
    }

    /*
     * WARNING - Removed try catching itself - possible behaviour change.
     */
    public static void save(Element element, String string) {
        if (string != null) {
            MainApp.settings().set("IndicatorTesterPath", string);
            MainApp.settings().save();
            lastConfigPath = string;
        } else {
            string = lastConfigPath;
        }
        if (string == null) {
            return;
        }
        try {
            File file = new File(string);
            XMLUtil.xmlToFile((Element)(element != null ? element : IndicatorTesterConfig.getConfig()), (File)file);
        }
        catch (Exception exception) {
            Log.error("Exc.", (Throwable)exception);
        }
        if (element != null) {
            long l = lock.writeLock();
            try {
                lastConfig = element;
            }
            finally {
                lock.unlock(l);
            }
        }
    }

    /*
     * WARNING - Removed try catching itself - possible behaviour change.
     */
    public static Element createNewConfig(String[] element) throws Exception {
        long l = lock.writeLock();
        try {
            Element element2 = XMLUtil.getChildElem((Element)lastConfig, (String)"Tests");
            for (Element element3 : element) {
                IndicatorInfo indicatorInfo = IndicatorsLoader.getIndyByName((String)element3);
                element2.addContent((Content)indicatorInfo.getXML((String)element3));
            }
            Element element4 = lastConfig;
            return element4;
        }
        finally {
            lock.unlock(l);
        }
    }

    public static void updateConfig(Element element) {
        long l = lock.writeLock();
        try {
            lastConfig = element;
        }
        finally {
            lock.unlock(l);
        }
    }

    static {
        lock = new StampedLock();
    }
}

