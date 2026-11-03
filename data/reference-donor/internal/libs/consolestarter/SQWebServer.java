/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  org.apache.http.HttpResponse
 *  org.apache.http.client.methods.HttpGet
 *  org.apache.http.client.methods.HttpUriRequest
 *  org.apache.http.impl.client.CloseableHttpClient
 *  org.apache.http.impl.client.HttpClientBuilder
 *  org.slf4j.Logger
 *  org.slf4j.LoggerFactory
 */
package com.strategyquant.strategyquant;

import com.strategyquant.lib.app.MainApp;
import com.strategyquant.pluginlib.SQPluginManager;
import com.strategyquant.tradinglib.backtest.SQBacktester;
import com.strategyquant.tradinglib.plugindef.app.IAppPlugin;
import com.strategyquant.tradinglib.results.DatabankResultsGroupProvider;
import com.strategyquant.webguilib.BrowserGUI;
import com.strategyquant.webguilib.WebAppManager;
import com.strategyquant.webguilib.WebServer;
import com.strategyquant.webguilib.init.AutoCompiler;
import com.strategyquant.webguilib.server.AbstractUIWebServer;
import com.strategyquant.webguilib.server.JettyServer;
import com.strategyquant.webguilib.websocket.SQWebSocketServlet;
import java.util.ArrayList;
import org.apache.http.HttpResponse;
import org.apache.http.client.methods.HttpGet;
import org.apache.http.client.methods.HttpUriRequest;
import org.apache.http.impl.client.CloseableHttpClient;
import org.apache.http.impl.client.HttpClientBuilder;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

public class SQWebServer
implements WebServer {
    private static final Logger Log = LoggerFactory.getLogger(SQWebServer.class);
    private static int portFrom;
    private static int portTo;
    private static String pluginsPath;
    private static String webPath;
    private WebAppManager webAppManager;

    @Override
    public void start() throws Exception {
        SQWebServer.checkVariables();
        this.webAppManager = new WebAppManager(this);
        if (AutoCompiler.checkFilesChanged(this)) {
            this.regenerateFiles();
        }
        new JettyServer(this, new DatabankResultsGroupProvider(), SQBacktester.get(), new SQWebSocketServlet());
        JettyServer.getInstance().start();
        this.jettyFailover();
    }

    private void jettyFailover() {
        new Thread(){

            @Override
            public void run() {
                boolean bl = false;
                StringBuilder stringBuilder = new StringBuilder().append("http://localhost:");
                JettyServer.getInstance();
                String string = stringBuilder.append(AbstractUIWebServer.port).append("/main/alive").toString();
                HttpGet httpGet = new HttpGet(string);
                httpGet.setHeader("browserToken", JettyServer.getBrowserToken() + "");
                int n = 0;
                while (true) {
                    try {
                        Thread.sleep(60000L);
                    }
                    catch (InterruptedException interruptedException) {
                        // empty catch block
                    }
                    try {
                        int n2 = -1;
                        try {
                            CloseableHttpClient closeableHttpClient = HttpClientBuilder.create().build();
                            HttpResponse httpResponse = closeableHttpClient.execute((HttpUriRequest)httpGet);
                            n2 = httpResponse.getStatusLine().getStatusCode();
                        }
                        catch (Exception exception) {
                            Log.error("Cannot get response /main/alive. Exc.", (Throwable)exception);
                        }
                        if (bl && n2 != 200) {
                            if (++n == 5) {
                                Log.error("Jetty server failed! /main/alive response status: " + n2);
                                Log.info("Restart Jetty server.");
                                JettyServer.getInstance().restartServer();
                                n = 0;
                            }
                        } else {
                            n = 0;
                        }
                        if (n2 != 200) continue;
                        bl = true;
                        continue;
                    }
                    catch (Exception exception) {
                        Log.error("Cannot restart Jetty server. Exc.", (Throwable)exception);
                        continue;
                    }
                    break;
                }
            }
        }.start();
    }

    private static void checkVariables() {
        if (portFrom == 0) {
            portFrom = 8080;
            portTo = 8085;
        }
        if (pluginsPath == null) {
            pluginsPath = MainApp.getDataPath() + "internal/plugins";
        }
        if (webPath == null) {
            webPath = MainApp.getDataPath() + "internal/web";
        }
        Log.debug("Port range: " + portFrom + " - " + portTo);
        Log.debug("Plugins folder path: " + pluginsPath);
        Log.debug("Web folder path: " + webPath);
    }

    @Override
    public void showErrorDialog(String string, String string2) {
        BrowserGUI.showErrorDialog(string, string2);
    }

    public void setPortRange(int n, int n2) {
        portFrom = n;
        portTo = n2;
    }

    public void setPluginsFolderPath(String string) {
        pluginsPath = string;
    }

    @Override
    public String getPluginsPath() {
        return pluginsPath;
    }

    @Override
    public String getWebPath() {
        return webPath;
    }

    @Override
    public int getPortFrom() {
        return portFrom;
    }

    @Override
    public int getPortTo() {
        return portTo;
    }

    @Override
    public int getUsedPort() {
        return JettyServer.port;
    }

    @Override
    public void regenerateFiles() throws Exception {
        Log.debug("Starting to regenerate files.");
        long l = System.currentTimeMillis();
        AutoCompiler.compileBatchFiles(this);
        ArrayList<IAppPlugin> arrayList = SQPluginManager.getPlugins(IAppPlugin.class);
        for (IAppPlugin iAppPlugin : arrayList) {
            if (iAppPlugin.getAppCode().equals("SQWIZARD") || iAppPlugin.getAppCode().equals("SQXBUSINESS")) continue;
            AutoCompiler.compileLayoutFiles(this, iAppPlugin.getAppCode());
        }
        long l2 = System.currentTimeMillis() - l;
        Log.debug("Files regenerated - regeneration took " + l2 + "ms");
        Log.debug("Clearing browser cache...");
        BrowserGUI.clearCache();
    }

    @Override
    public WebAppManager getWebAppManager() {
        return this.webAppManager;
    }

    @Override
    public String getBaseURL() {
        return (JettyServer.useHttps ? "https" : "http") + "://localhost:" + JettyServer.port;
    }
}

