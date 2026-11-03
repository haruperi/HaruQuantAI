/*
 * Decompiled with CFR 0.152.
 */
package com.strategyquant.wizard.desktop.loader;

import com.strategyquant.wizard.desktop.utils.JsonUtils;
import java.io.IOException;

public class ShareLoader {
    public String share(String string, String string2, String string3, String string4) {
        String string5 = "http://wizard.strategyquant.com/backend/share";
        String string6 = "s=" + string3 + "&filename=" + string + "&type=" + string2 + string4;
        try {
            String string7 = JsonUtils.doPost(string5, string6);
            return string7;
        }
        catch (IOException iOException) {
            return JsonUtils.getErrorResonse(iOException.getMessage());
        }
    }

    public String verifyShare(String string) {
        String string2 = "http://wizard.strategyquant.com/backend/verifyusers?" + string;
        try {
            String string3 = JsonUtils.doGet(string2);
            return string3;
        }
        catch (IOException iOException) {
            return JsonUtils.getErrorResonse(iOException.getMessage());
        }
    }

    public String notifyShare(String string, String string2) {
        String string3 = "http://wizard.strategyquant.com/backend/notifyshare?id=" + string + "&s=" + string2;
        try {
            String string4 = JsonUtils.doGet(string3);
            return string4;
        }
        catch (IOException iOException) {
            return JsonUtils.getErrorResonse(iOException.getMessage());
        }
    }

    public String loadShared(String string, String string2) {
        String string3 = "http://wizard.strategyquant.com/backend/loadshared?id=" + string + "&s=" + string2;
        try {
            String string4 = JsonUtils.doGet(string3);
            return string4;
        }
        catch (IOException iOException) {
            return JsonUtils.getErrorResonse(iOException.getMessage());
        }
    }

    public String saveShared(String string, String string2, String string3) {
        String string4 = "http://wizard.strategyquant.com/backend/saveshared";
        String string5 = "content=" + string2 + "&id=" + string + "&s=" + string3;
        try {
            String string6 = JsonUtils.doPost(string4, string5);
            return string6;
        }
        catch (IOException iOException) {
            return JsonUtils.getErrorResonse(iOException.getMessage());
        }
    }
}

