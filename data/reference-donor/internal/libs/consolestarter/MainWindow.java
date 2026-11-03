/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  org.slf4j.Logger
 *  org.slf4j.LoggerFactory
 */
package com.strategyquant.strategyquant;

import com.strategyquant.lib.app.IMainWindow;
import com.strategyquant.lib.app.MainApp;
import com.strategyquant.strategyquant.SQWebServer;
import com.strategyquant.webguilib.BrowserGUI;
import com.strategyquant.webguilib.WebServer;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

public class MainWindow
implements IMainWindow {
    public static final Logger Log = LoggerFactory.getLogger(MainWindow.class);
    private BrowserGUI frame = null;
    private WebServer webServer;

    @Override
    public void initialize() {
        Log.info("Initializing Browser ...");
        this.frame = new BrowserGUI("sq_ico.png");
    }

    @Override
    public void initWebServer() {
        this.waitUntilFrameReady();
        try {
            this.webServer = new SQWebServer();
            this.webServer.start();
        }
        catch (Exception exception) {
            Log.error("Cannot start web server", (Throwable)exception);
            BrowserGUI.showErrorDialog("Application error", "Cannot start internal webserver on port " + this.webServer.getUsedPort() + ". Please check your firewall settings.");
            MainApp.exitApp();
        }
        this.frame.init(this.webServer.getWebAppManager().getAppName());
    }

    private void waitUntilFrameReady() {
        Thread thread = new Thread(){

            @Override
            public void run() {
                while (MainWindow.this.frame == null) {
                    try {
                        Thread.sleep(100L);
                    }
                    catch (InterruptedException interruptedException) {}
                }
            }
        };
        thread.start();
        try {
            thread.join();
        }
        catch (Exception exception) {
            // empty catch block
        }
    }

    @Override
    public void setTitle() {
        this.waitUntilFrameReady();
        this.frame.setTitle(MainApp.getFrameTitle());
    }

    @Override
    public void destroy() {
        BrowserGUI.getInstance().destroy();
    }

    public WebServer getWebServer() {
        return this.webServer;
    }
}

