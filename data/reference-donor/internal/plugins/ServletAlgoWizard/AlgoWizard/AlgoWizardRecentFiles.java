/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  com.strategyquant.lib.SQUtils
 *  com.strategyquant.lib.XMLUtil
 *  com.strategyquant.lib.constants.SQPaths
 *  org.jdom2.Content
 *  org.jdom2.Element
 *  org.json.JSONArray
 *  org.slf4j.Logger
 *  org.slf4j.LoggerFactory
 */
package com.strategyquant.plugin.Servlet.impl.AlgoWizard;

import com.strategyquant.lib.SQUtils;
import com.strategyquant.lib.XMLUtil;
import com.strategyquant.lib.constants.SQPaths;
import java.io.File;
import java.util.ArrayList;
import org.jdom2.Content;
import org.jdom2.Element;
import org.json.JSONArray;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

public class AlgoWizardRecentFiles {
    private static final Logger Log = LoggerFactory.getLogger(AlgoWizardRecentFiles.class);
    public static final String configFilePath = SQPaths.settingsDirPath + "/AlgoWizardRecentFiles.xml";
    private static final int maxRecentFiles = 0;
    private static AlgoWizardRecentFiles instance = null;
    private ArrayList<String> recentFiles = new ArrayList();

    private AlgoWizardRecentFiles() {
        instance = this;
        try {
            this.load();
        }
        catch (Exception e) {
            Log.error("Cannot load AlgoWizard recent files", (Throwable)e);
        }
    }

    private void load() throws Exception {
        this.recentFiles.clear();
        File f = new File(configFilePath);
        if (!f.exists()) {
            Log.info("AlgoWizardRecentFiles.xml doesn't exist yet");
            return;
        }
        Element elRecentFiles = XMLUtil.fileToXmlElement((File)f);
        int index = 0;
        for (Element elFile : elRecentFiles.getChildren("File")) {
            this.recentFiles.add(elFile.getText());
            ++index;
        }
    }

    public static ArrayList<String> list() {
        return AlgoWizardRecentFiles.get().recentFiles;
    }

    public static JSONArray listJSON() {
        JSONArray array = new JSONArray();
        for (String file : AlgoWizardRecentFiles.get().recentFiles) {
            array.put((Object)file);
        }
        return array;
    }

    public static void save(String recentFile) {
        AlgoWizardRecentFiles.get()._save(recentFile);
    }

    private static AlgoWizardRecentFiles get() {
        if (instance == null) {
            instance = new AlgoWizardRecentFiles();
        }
        return instance;
    }

    public void _save(String recentFile) {
        if (this.recentFiles.contains(recentFile)) {
            this.recentFiles.remove(recentFile);
        }
        this.recentFiles.add(0, recentFile);
        Element elRecentFiles = new Element("RecentFiles");
        for (String file : this.recentFiles) {
            Element elFile = new Element("File");
            elFile.setText(file);
            elRecentFiles.addContent((Content)elFile);
        }
        SQUtils.stringToFile((File)new File(configFilePath), (String)XMLUtil.elementToString((Element)elRecentFiles));
    }
}

