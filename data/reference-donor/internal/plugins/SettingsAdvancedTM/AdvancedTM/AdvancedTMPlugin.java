/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  com.strategyquant.lib.L
 *  com.strategyquant.lib.XMLUtil
 *  com.strategyquant.pluginlib.annotations.Category
 *  com.strategyquant.pluginlib.annotations.License
 *  com.strategyquant.pluginlib.annotations.Name
 *  com.strategyquant.pluginlib.annotations.ShortDesc
 *  com.strategyquant.tradinglib.ATM
 *  com.strategyquant.tradinglib.ATMExit
 *  com.strategyquant.tradinglib.atm.ATMConfigVerifier
 *  com.strategyquant.tradinglib.atm.ATMGenerateConfig
 *  com.strategyquant.tradinglib.servlet.IServletPlugin
 *  com.strategyquant.tradinglib.task.settings.ISettingTabPlugin
 *  com.strategyquant.tradinglib.task.settings.TaskSettingsData
 *  com.strategyquant.tradinglib.taskImpl.ISQTask
 *  jakarta.servlet.Servlet
 *  net.xeoh.plugins.base.annotations.PluginImplementation
 *  net.xeoh.plugins.base.annotations.meta.Author
 *  org.eclipse.jetty.server.Handler
 *  org.eclipse.jetty.servlet.ServletContextHandler
 *  org.eclipse.jetty.servlet.ServletHolder
 *  org.jdom2.Element
 *  org.json.JSONArray
 *  org.json.JSONObject
 */
package com.strategyquant.plugin.Settings.impl.AdvancedTM;

import com.strategyquant.lib.L;
import com.strategyquant.lib.XMLUtil;
import com.strategyquant.plugin.Settings.impl.AdvancedTM.AdvancedTMServlet;
import com.strategyquant.pluginlib.annotations.Category;
import com.strategyquant.pluginlib.annotations.License;
import com.strategyquant.pluginlib.annotations.Name;
import com.strategyquant.pluginlib.annotations.ShortDesc;
import com.strategyquant.tradinglib.ATM;
import com.strategyquant.tradinglib.ATMExit;
import com.strategyquant.tradinglib.atm.ATMConfigVerifier;
import com.strategyquant.tradinglib.atm.ATMGenerateConfig;
import com.strategyquant.tradinglib.servlet.IServletPlugin;
import com.strategyquant.tradinglib.task.settings.ISettingTabPlugin;
import com.strategyquant.tradinglib.task.settings.TaskSettingsData;
import com.strategyquant.tradinglib.taskImpl.ISQTask;
import jakarta.servlet.Servlet;
import java.io.Serializable;
import net.xeoh.plugins.base.annotations.PluginImplementation;
import net.xeoh.plugins.base.annotations.meta.Author;
import org.eclipse.jetty.server.Handler;
import org.eclipse.jetty.servlet.ServletContextHandler;
import org.eclipse.jetty.servlet.ServletHolder;
import org.jdom2.Element;
import org.json.JSONArray;
import org.json.JSONObject;

@Author(name="Tomas Brynda")
@Name(name="Settings AdvancedTM plugin")
@Category(name="Settings")
@License(text="")
@ShortDesc(text="Short description")
@PluginImplementation
public class AdvancedTMPlugin
implements ISettingTabPlugin,
IServletPlugin {
    private ServletContextHandler dataContext;
    private AdvancedTMServlet servlet;

    public String getProduct() {
        return "SQUANT";
    }

    public int getPreferredPosition() {
        return 50;
    }

    public void initPlugin() throws Exception {
    }

    public Handler getHandler() {
        if (this.dataContext == null) {
            this.servlet = new AdvancedTMServlet();
            this.dataContext = new ServletContextHandler(1);
            this.dataContext.setContextPath("/advancedtm/");
            this.dataContext.addServlet(new ServletHolder((Servlet)this.servlet), "/*");
        }
        return this.dataContext;
    }

    public void readSettings(String projectName, ISQTask task, Element elSettings, TaskSettingsData data) {
        try {
            Element elAdvancedTM = elSettings.getChild(this.getSettingName());
            ATMConfigVerifier.verifyConfig((Element)elSettings, (TaskSettingsData)data);
            if (elAdvancedTM == null) {
                data.addParam("ATM", null);
            } else {
                ATM atm = new ATM(elAdvancedTM);
                if (atm.getType() == 3) {
                    ATMGenerateConfig atmGenConfig = atm.getGenerateConfig();
                    atmGenConfig.verifyConfig(data);
                    data.addParam("ATMGenerateConfig", (Serializable)atmGenConfig);
                    atm.changeToStrategy();
                } else {
                    data.addParam("ATMGenerateConfig", null);
                }
                data.addParam("ATM", (Serializable)atm);
            }
        }
        catch (Exception e) {
            data.addError(this.getSettingName(), null, e.getMessage());
            return;
        }
    }

    public void getStrategyConfigSettings(Element elSettings, JSONArray settingsArray) throws Exception {
        Element elATMs = XMLUtil.tryAddElement((Element)elSettings, (String)this.getSettingName());
        try {
            ATM atm = new ATM(elATMs);
            int type = atm.getType();
            switch (type) {
                case 0: {
                    settingsArray.put((Object)new JSONObject().put("key", (Object)"ATM").put("value", (Object)"Don't use"));
                    return;
                }
                case 1: {
                    settingsArray.put((Object)new JSONObject().put("key", (Object)"ATM").put("value", (Object)"Use from strategy"));
                    settingsArray.put((Object)new JSONObject().put("key", (Object)"Size decimals").put("value", atm.getSizeDecimals()));
                    settingsArray.put((Object)new JSONObject().put("key", (Object)"Minimum size").put("value", atm.getMinimalSize()));
                    return;
                }
                case 2: {
                    settingsArray.put((Object)new JSONObject().put("key", (Object)"ATM").put("value", (Object)"From config"));
                    settingsArray.put((Object)new JSONObject().put("key", (Object)"Size decimals").put("value", atm.getSizeDecimals()));
                    settingsArray.put((Object)new JSONObject().put("key", (Object)"Minimum size").put("value", atm.getMinimalSize()));
                    for (int i = 0; i < atm.getExitsCount(); ++i) {
                        ATMExit atmExit = atm.getExit(i);
                        settingsArray.put((Object)new JSONObject().put("key", (Object)String.format("Exit #%d", i + 1)).put("value", (Object)atmExit.toString()));
                    }
                    break;
                }
            }
        }
        catch (Exception e) {
            settingsArray.put((Object)new JSONObject().put("key", (Object)"ATM").put("value", (Object)"Don't use"));
        }
    }

    public String getSettingName() {
        return "ATMs";
    }

    public String getName() {
        return L.tsq((String)"Advanced Trading Management");
    }

    public JSONObject getInitializationData() throws Exception {
        JSONObject data = new JSONObject();
        return data;
    }
}

