/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  com.strategyquant.lib.app.MainApp
 *  org.slf4j.Logger
 *  org.slf4j.LoggerFactory
 */
package com.strategyquant.datalib.basket;

import com.strategyquant.lib.app.MainApp;
import java.io.File;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

public class BasketBrokerDev {
    private static final Logger Log = LoggerFactory.getLogger(BasketBrokerDev.class);
    private boolean dev;
    private static BasketBrokerDev instance = new BasketBrokerDev();

    public static BasketBrokerDev getInstance() {
        return instance;
    }

    private BasketBrokerDev() {
        File file = new File(MainApp.getDataPath() + "/datadev.txt");
        Log.debug("Checking file in location: {}", (Object)file.getAbsolutePath());
        this.dev = file.exists();
        Log.debug("Dev mode: {}", (Object)this.dev);
    }

    public boolean isDev() {
        return this.dev;
    }
}

