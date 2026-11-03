/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  org.apache.commons.io.FileUtils
 *  org.jdom2.Element
 *  org.slf4j.Logger
 *  org.slf4j.LoggerFactory
 */
package com.strategyquant.strategyquant;

import com.strategyquant.lib.L;
import com.strategyquant.lib.SQUtils;
import com.strategyquant.lib.XMLUtil;
import com.strategyquant.lib.app.MainApp;
import com.strategyquant.lib.snippets.compile.SQStructure;
import java.io.File;
import org.apache.commons.io.FileUtils;
import org.jdom2.Element;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

public class SQInstaller {
    private static final Logger Log = LoggerFactory.getLogger(SQInstaller.class);
    private static final String ConfigUrl = "https://1859438673.rsc.cdn77.org/ninstall/sqxinstaller/updates.xml";
    private static final String VersionPath = SQStructure.INTERNAL_DIR_PATH + "SQI.dat";

    public void checkForUpdatesAsync() {
        new Thread(new Runnable(){

            @Override
            public void run() {
                SQInstaller.this.checkForUpdates();
            }
        }).start();
    }

    public void checkForUpdates() {
        try {
            Log.debug("Checking for new SQX Installer");
            String string = SQUtils.httpGet(ConfigUrl);
            Element element = XMLUtil.stringToElement(string);
            int n = XMLUtil.getIntAttr(element, "version", 0);
            String string2 = element.getAttributeValue("url");
            String string3 = element.getAttributeValue("checksum");
            int n2 = this.getCurrentVersion();
            Log.debug("Installed version: " + n2);
            Log.debug("Available version: " + n);
            if (n > n2) {
                Log.debug("Downloading new version of StrategyQuantX.exe");
                byte[] byArray = SQUtils.loadDataFromServer(string2);
                if (!string3.equals(SQUtils.md5CheckSum(byArray))) {
                    throw new Exception(L.t("Checksum doesn't match.", new Object[0]));
                }
                FileUtils.writeByteArrayToFile((File)new File(MainApp.getDataPath() + "StrategyQuantX.exe"), (byte[])byArray);
                SQUtils.stringToFile(VersionPath, n + "");
            }
        }
        catch (Exception exception) {
            Log.error("Error while checking for updates. Exc.", (Throwable)exception);
        }
    }

    private int getCurrentVersion() {
        int n = 1;
        File file = new File(VersionPath);
        if (file.exists()) {
            try {
                String string = SQUtils.fileToString(file);
                n = Integer.valueOf(string);
            }
            catch (Exception exception) {
                // empty catch block
            }
        }
        return n;
    }
}

