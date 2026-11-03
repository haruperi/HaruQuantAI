/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  com.strategyquant.lib.L
 */
package com.strategyquant.datalib.timezone;

import com.strategyquant.datalib.timezone.Timezones;
import com.strategyquant.lib.L;
import java.util.TimeZone;

public class Timezone {
    public static final String DEFAULT = "Etc/UCT";
    private String name;
    private String id;
    public boolean dst = false;

    public Timezone(String string, String string2) {
        this.name = string;
        this.id = string2;
        if (string2.equals("EETUS")) {
            string2 = "America/New_York";
        }
        TimeZone timeZone = TimeZone.getTimeZone(string2);
        this.dst = timeZone.useDaylightTime();
    }

    public String toString() {
        return this.name + ", DST: " + (this.dst ? "Yes" : "No");
    }

    public String getId() {
        return this.id;
    }

    public String getName() {
        return this.toString();
    }

    public static String print(String string, int n, boolean bl) {
        if (!(n != 5 && n != 6 || string != null && !string.isBlank())) {
            return L.t((String)"Exchange", (Object[])new Object[0]);
        }
        if (string == null) {
            return null;
        }
        String string2 = "";
        String[] stringArray = string.split("\\|");
        String string3 = stringArray[0];
        Timezone timezone = Timezones.findByKey(string3);
        if (timezone == null) {
            return string3;
        }
        string2 = timezone.getName();
        if (bl) {
            string2 = string2.substring(0, string2.lastIndexOf(")") + 1);
            string2 = string2.replaceAll("\\(", "");
            string2 = string2.replaceAll("\\)", "");
        }
        if (stringArray.length > 1) {
            for (int i = 1; i < stringArray.length; ++i) {
                int n2 = Integer.parseInt(stringArray[i]);
                string2 = string2 + " " + (n2 > 0 ? "+" + stringArray[i] : stringArray[i]);
            }
        }
        return string2;
    }

    public String printShortName() {
        return this.name.substring(0, this.name.indexOf(")") + 1);
    }

    public static String shiftHours(String string, int n) {
        return n == 0 ? string : string + "|" + n;
    }

    public static String parseId(String string) {
        return string.split("\\|")[0];
    }
}

