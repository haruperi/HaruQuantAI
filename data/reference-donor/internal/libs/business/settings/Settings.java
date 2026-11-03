/*
 * Decompiled with CFR 0.152.
 */
package com.strategyquant.wizard.desktop.settings;

import com.strategyquant.wizard.desktop.utils.FileUtils;
import java.io.File;
import java.io.FileReader;
import java.io.FileWriter;
import java.util.Properties;
import java.util.logging.Level;
import java.util.logging.Logger;

public class Settings {
    public static final String STRATEGY_FOLDER = "strategyFolder";
    public static final String INDICATOR_FOLDER = "indicatorFolder";
    public static final String RESULT_FOLDER = "resultFolder";
    private static final Logger logger = Logger.getLogger("");
    private static Settings instance = new Settings();
    private Properties properties = new Properties();

    public static Settings get() {
        return instance;
    }

    public void initialize() {
        File file = new File(FileUtils.getAppFolder(), "config.properties");
        try {
            FileReader fileReader = new FileReader(file);
            this.properties.load(fileReader);
            fileReader.close();
        }
        catch (Exception exception) {
            logger.log(Level.SEVERE, "Error while loading configuration");
        }
    }

    public String get(String string) {
        return this.properties.getProperty(string);
    }

    public void set(String string, String string2) {
        this.properties.setProperty(string, string2);
        this.save();
    }

    private void save() {
        File file = new File(FileUtils.getAppFolder(), "config.properties");
        try {
            FileWriter fileWriter = new FileWriter(file);
            this.properties.store(fileWriter, "");
            fileWriter.close();
        }
        catch (Exception exception) {
            logger.log(Level.SEVERE, "Error while loading configuration");
        }
    }
}

