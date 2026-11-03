/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  com.strategyquant.lib.app.MainApp
 */
package com.strategyquant.wizard.desktop.loader;

import com.strategyquant.lib.app.MainApp;
import com.strategyquant.wizard.desktop.utils.JsonUtils;
import java.awt.Component;
import java.io.IOException;

public class ErrorReportSender {
    private Component parent;

    public ErrorReportSender(Component component) {
        this.parent = component;
    }

    public boolean send(String string, String string2) {
        String string3 = "http://wizard.strategyquant.com/backend/errorReport";
        String string4 = "email=" + string + "&strategy=" + string2;
        try {
            JsonUtils.doPost(string3, string4);
            return true;
        }
        catch (IOException iOException) {
            MainApp.showErrorDialog((String)"Cannot connect to internet");
            return false;
        }
    }

    public void dispose() {
        this.parent = null;
    }
}

