/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  com.strategyquant.lib.SQUtils
 *  com.strategyquant.lib.snippets.compile.SQStructure
 *  org.slf4j.Logger
 *  org.slf4j.LoggerFactory
 */
package com.strategyquant.datalib.timezone;

import com.strategyquant.datalib.timezone.Timezone;
import com.strategyquant.lib.SQUtils;
import com.strategyquant.lib.snippets.compile.SQStructure;
import java.io.File;
import java.util.ArrayList;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

public class Timezones {
    public static final Logger Log = LoggerFactory.getLogger(Timezones.class);
    private static final String path = SQStructure.INTERNAL_DIR_PATH + "/web/SQMANAGER/timezones.csv";
    private static Timezones instance;
    private ArrayList<Timezone> timezones = new ArrayList();

    private Timezones() {
        this.loadTimezones();
    }

    private static Timezones get() {
        if (instance == null) {
            instance = new Timezones();
        }
        return instance;
    }

    public static ArrayList<Timezone> getTimezones() {
        return Timezones.get().timezones;
    }

    private void loadTimezones() {
        try {
            String[] stringArray;
            String string = SQUtils.fileToString((File)new File(path));
            for (String string2 : stringArray = string.split("\n")) {
                String[] stringArray2 = string2.split(";");
                Timezone timezone = new Timezone(stringArray2[0].trim(), stringArray2[1].trim());
                this.timezones.add(timezone);
            }
        }
        catch (Exception exception) {
            Log.error("Cannot load timezones", (Throwable)exception);
        }
    }

    public static Timezone findByKey(String string) {
        for (Timezone timezone : Timezones.getTimezones()) {
            if (!timezone.getId().equals(string)) continue;
            return timezone;
        }
        return null;
    }
}

