/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  org.slf4j.Logger
 *  org.slf4j.LoggerFactory
 */
package com.strategyquant.tradinglib.task.settings;

import com.strategyquant.tradinglib.task.settings.SettingError;
import java.io.Serializable;
import java.util.ArrayList;
import java.util.HashMap;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

public class TaskSettingsData {
    public static final Logger Log = LoggerFactory.getLogger((String)"TaskSettingsData");
    private HashMap<String, Serializable> params = new HashMap();
    private ArrayList<SettingError> errors = new ArrayList();

    public void clear() {
        this.params.clear();
        this.errors.clear();
    }

    public void addError(SettingError settingError) {
        this.errors.add(settingError);
    }

    public void addError(String string, String string2, String string3) {
        this.addError(new SettingError(string, string2, string3));
    }

    public void addParam(String string, Serializable serializable) throws Exception {
        if (this.params.containsKey(string)) {
            Log.debug("Duplicate key '" + string + "'");
        }
        this.params.put(string, serializable);
    }

    public void addParamUnchecked(String string, Serializable serializable) {
        this.params.put(string, serializable);
    }

    public boolean hasErrors() {
        return !this.errors.isEmpty();
    }

    public HashMap<String, Serializable> getParams() {
        return this.params;
    }

    public ArrayList<SettingError> getErrors() {
        return this.errors;
    }
}

