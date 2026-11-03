/*
 * Decompiled with CFR 0.152.
 */
package com.strategyquant.strategyquant;

import com.strategyquant.lib.app.MainApp;
import com.strategyquant.strategyquant.MainWindow;
import com.strategyquant.strategyquant.SQApp;

public class SQInitializer {
    public SQInitializer() {
        MainApp.setMultiInstance(true);
        MainApp.addInstance(new SQApp(new MainWindow()));
        MainApp.settings().load();
        MainApp.start();
    }
}

