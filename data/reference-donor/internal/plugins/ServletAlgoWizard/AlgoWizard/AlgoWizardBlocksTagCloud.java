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
 *  org.json.JSONObject
 *  org.slf4j.Logger
 *  org.slf4j.LoggerFactory
 */
package com.strategyquant.plugin.Servlet.impl.AlgoWizard;

import com.strategyquant.lib.SQUtils;
import com.strategyquant.lib.XMLUtil;
import com.strategyquant.lib.constants.SQPaths;
import java.io.File;
import java.util.HashMap;
import org.jdom2.Content;
import org.jdom2.Element;
import org.json.JSONArray;
import org.json.JSONObject;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

public class AlgoWizardBlocksTagCloud {
    private static final Logger Log = LoggerFactory.getLogger(AlgoWizardBlocksTagCloud.class);
    public static final String configFilePath = SQPaths.settingsDirPath + "/AlgoWizardBlocksTagCloud.xml";
    private static AlgoWizardBlocksTagCloud instance = null;
    private HashMap<String, Integer> loadedBlocks = new HashMap();

    private AlgoWizardBlocksTagCloud() {
        instance = this;
        try {
            this.load();
        }
        catch (Exception e) {
            Log.error("Cannot load AlgoWizard Blocks Tag Cloud", (Throwable)e);
        }
    }

    private void load() throws Exception {
        this.loadedBlocks.clear();
        File f = new File(configFilePath);
        if (!f.exists()) {
            Log.info("AlgoWizardBlocksTagCloud.xml doesn't exist yet");
            return;
        }
        Element elRecentFiles = XMLUtil.fileToXmlElement((File)f);
        for (Element elFile : elRecentFiles.getChildren("Block")) {
            try {
                this.loadedBlocks.put(elFile.getText(), Integer.parseInt(elFile.getAttributeValue("number")));
            }
            catch (Exception e) {
                Log.error("Cannot load block", (Throwable)e);
            }
        }
    }

    public static JSONArray listJSON() {
        JSONArray array = new JSONArray();
        for (String block : AlgoWizardBlocksTagCloud.get().loadedBlocks.keySet()) {
            JSONObject obj = new JSONObject();
            obj.put("block", (Object)block);
            obj.put("number", (Object)AlgoWizardBlocksTagCloud.get().loadedBlocks.get(block));
            array.put((Object)obj);
        }
        return array;
    }

    public static void save(String blockKey, String blockType, String blockParams) {
        AlgoWizardBlocksTagCloud.get()._save(blockKey, blockType, blockParams);
    }

    private static AlgoWizardBlocksTagCloud get() {
        if (instance == null) {
            instance = new AlgoWizardBlocksTagCloud();
        }
        return instance;
    }

    public void _save(String blockKey, String blockType, String blockParams) {
        String key = blockKey + "++" + blockType + "++" + blockParams;
        if (this.loadedBlocks.containsKey(key)) {
            this.loadedBlocks.put(key, this.loadedBlocks.get(key) + 1);
        } else {
            this.loadedBlocks.put(key, 1);
        }
        Element elBlocks = new Element("Blocks");
        for (String block : this.loadedBlocks.keySet()) {
            Element elBlock = new Element("Block");
            elBlock.setText(block);
            elBlock.setAttribute("number", this.loadedBlocks.get(block).toString());
            elBlocks.addContent((Content)elBlock);
        }
        SQUtils.stringToFile((File)new File(configFilePath), (String)XMLUtil.elementToString((Element)elBlocks));
    }
}

