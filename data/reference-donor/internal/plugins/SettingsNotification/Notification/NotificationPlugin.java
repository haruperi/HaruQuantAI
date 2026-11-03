/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  com.strategyquant.lib.L
 *  com.strategyquant.lib.XMLUtil
 *  com.strategyquant.lib.app.MainApp
 *  com.strategyquant.lib.utils.EmailSender
 *  com.strategyquant.pluginlib.annotations.Category
 *  com.strategyquant.pluginlib.annotations.License
 *  com.strategyquant.pluginlib.annotations.Name
 *  com.strategyquant.pluginlib.annotations.ShortDesc
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
package com.strategyquant.plugin.Settings.impl.Notification;

import com.strategyquant.lib.L;
import com.strategyquant.lib.XMLUtil;
import com.strategyquant.lib.app.MainApp;
import com.strategyquant.lib.utils.EmailSender;
import com.strategyquant.plugin.Settings.impl.Notification.NotificationServlet;
import com.strategyquant.pluginlib.annotations.Category;
import com.strategyquant.pluginlib.annotations.License;
import com.strategyquant.pluginlib.annotations.Name;
import com.strategyquant.pluginlib.annotations.ShortDesc;
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
@Name(name="Settings Notification plugin")
@Category(name="Settings")
@License(text="")
@ShortDesc(text="Short description")
@PluginImplementation
public class NotificationPlugin
implements ISettingTabPlugin,
IServletPlugin {
    private ServletContextHandler dataContext;
    private NotificationServlet servlet;

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
            this.servlet = new NotificationServlet();
            this.dataContext = new ServletContextHandler(1);
            this.dataContext.setContextPath("/notification/");
            this.dataContext.addServlet(new ServletHolder((Servlet)this.servlet), "/*");
        }
        return this.dataContext;
    }

    public void readSettings(String projectName, ISQTask task, Element elSettings, TaskSettingsData data) {
        Element elNotification = null;
        try {
            elNotification = XMLUtil.getChildElem((Element)elSettings, (String)this.getSettingName());
        }
        catch (Exception e) {
            data.addError(this.getSettingName(), null, e.getMessage());
            return;
        }
        try {
            data.addParam("Type", (Serializable)((Object)XMLUtil.getChildElem((Element)elNotification, (String)"Type").getText()));
            data.addParam("Email", (Serializable)((Object)XMLUtil.getChildElem((Element)elNotification, (String)"Email").getText()));
            data.addParam("PauseProject", (Serializable)Boolean.valueOf(Boolean.parseBoolean(XMLUtil.getChildElem((Element)elNotification, (String)"Wait").getText())));
            String type = (String)data.getParams().get("Type");
            String email = (String)data.getParams().get("Email");
            if (type.toLowerCase().equals("email")) {
                if (EmailSender.isValidEmailAddress((String)email)) {
                    data.addParam("SMTPServer", (Serializable)((Object)MainApp.settings().get("SMTPServer", "")));
                    data.addParam("SMTPPort", (Serializable)Integer.valueOf(Integer.parseInt(MainApp.settings().get("SMTPPort", "25"))));
                    data.addParam("SMTPUsername", (Serializable)((Object)MainApp.settings().get("SMTPUsername", "")));
                    data.addParam("SMTPPassword", (Serializable)((Object)MainApp.settings().get("SMTPPassword", "")));
                    data.addParam("SMTPEmailFrom", (Serializable)((Object)MainApp.settings().get("SMTPEmailFrom", "")));
                    data.addParam("SMTPUseSSL", (Serializable)Boolean.valueOf(Boolean.parseBoolean(MainApp.settings().get("SMTPUseSSL", "false"))));
                    String host = (String)data.getParams().get("SMTPServer");
                    if (host.trim().isEmpty()) {
                        data.addError(this.getSettingName(), "smtp", L.t((String)"To enable email notifications, you need to configure email server on Global setting -> SMTP server panel.", (Object[])new Object[0]));
                    }
                } else {
                    data.addError(this.getSettingName(), "email", L.t((String)"Email is not valid.", (Object[])new Object[0]));
                }
            }
        }
        catch (Exception e) {
            data.addError(this.getSettingName(), null, "Cannot load Notification settings. " + e.getMessage());
        }
    }

    public void getStrategyConfigSettings(Element elSettings, JSONArray settingsArray) throws Exception {
    }

    public String getSettingName() {
        return "Notification";
    }

    public String getName() {
        return L.tsq((String)"Notification");
    }

    public JSONObject getInitializationData() throws Exception {
        JSONObject data = new JSONObject();
        data.put("types", (Object)this.servlet.getTypes());
        return data;
    }
}

