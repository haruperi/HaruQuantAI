/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  com.strategyquant.lib.app.MainApp
 *  com.strategyquant.lib.historyData.HistoryDataSubscription
 *  com.strategyquant.lib.license.LicenseInfo
 *  com.strategyquant.lib.license.LicenseStore
 *  com.strategyquant.lib.volumeProfile.VolumeProfileSubscription
 *  com.strategyquant.webguilib.BrowserGUI
 *  com.strategyquant.webguilib.servlet.HttpJSONServlet
 *  org.json.JSONObject
 *  org.slf4j.Logger
 *  org.slf4j.LoggerFactory
 */
package com.strategyquant.plugin.Home.impl.About;

import com.strategyquant.lib.app.MainApp;
import com.strategyquant.lib.historyData.HistoryDataSubscription;
import com.strategyquant.lib.license.LicenseInfo;
import com.strategyquant.lib.license.LicenseStore;
import com.strategyquant.lib.volumeProfile.VolumeProfileSubscription;
import com.strategyquant.webguilib.BrowserGUI;
import com.strategyquant.webguilib.servlet.HttpJSONServlet;
import java.util.Map;
import org.json.JSONObject;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

public class AboutServlet
extends HttpJSONServlet {
    private static final Logger Log = LoggerFactory.getLogger(AboutServlet.class);

    protected String execute(String command, Map<String, String[]> parameterMap, String method) throws Exception {
        switch (command) {
            case "license": {
                return this.onLicense();
            }
            case "updateLicense": {
                return this.onUpdateLicense(parameterMap);
            }
        }
        throw new Exception("Unknown command '" + command + "'.");
    }

    private String onUpdateLicense(Map<String, String[]> args) throws Exception {
        this.checkParamExists(args, new String[]{"code"});
        String code = args.get("code")[0];
        JSONObject response = new JSONObject();
        try {
            MainApp.setLicenseCode((String)code);
            LicenseInfo lc = MainApp.getLicenseInfo();
            LicenseInfo.reasonVerifFailed = null;
            response.put("updateResult", (Object)"License OK");
            response.put("updateSuccess", true);
            if (MainApp.checkProduct((String)"QDM")) {
                LicenseStore.setStoredLicenseCode((String)lc.getCode());
            }
            HistoryDataSubscription.getInstance().update();
            VolumeProfileSubscription.getInstance().update();
            BrowserGUI.notifyUILicenseChanged((Boolean)false);
        }
        catch (Exception e) {
            Log.error("Exc.", (Throwable)e);
            LicenseInfo.reasonVerifFailed = e.getMessage();
            response.put("updateResult", (Object)e.getMessage());
            response.put("updateSuccess", false);
        }
        this.getLicenseInfo(response);
        return response.toString();
    }

    private String onLicense() {
        JSONObject response = new JSONObject();
        this.getLicenseInfo(response);
        return response.toString();
    }

    private JSONObject getLicenseInfo(JSONObject response) {
        LicenseInfo licenseInfo = MainApp.getLicenseInfo();
        if (MainApp.checkProduct((String)"QDM")) {
            response.put("product", (Object)"QuantDataManager");
            response.put("version", (Object)(licenseInfo.isFull() ? " Pro version" : " Free version"));
            response.put("hardwareid", (Object)licenseInfo.getHardwareID());
            response.put("code", (Object)licenseInfo.getCode());
            response.put("owner", (Object)licenseInfo.getOwnerName());
            response.put("type", (Object)licenseInfo.printType(licenseInfo.getCode()));
        } else {
            response.put("product", (Object)"StrategyQuant");
            response.put("version", (Object)MainApp.printAppVersion((String)licenseInfo.printEdition(), (boolean)true));
            response.put("hardwareid", (Object)licenseInfo.getHardwareID());
            response.put("code", (Object)licenseInfo.getCode());
            response.put("email", (Object)licenseInfo.getOwnerEmail());
            String owner = licenseInfo.getOwnerName();
            if (licenseInfo.isPersonalized()) {
                owner = owner + " - " + licenseInfo.getOwnerEmail();
            }
            response.put("owner", (Object)owner);
            response.put("type", (Object)licenseInfo.printType(licenseInfo.getCode()));
        }
        response.put("volumeProfile", (Object)VolumeProfileSubscription.toJSON());
        response.put("success", (Object)"ok");
        return response;
    }
}

