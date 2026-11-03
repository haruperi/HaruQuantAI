/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  org.joda.time.DateTime
 *  org.joda.time.DateTimeZone
 */
package com.strategyquant.datalib.data;

import com.strategyquant.datalib.data.io.VersatileData;
import com.strategyquant.datalib.timezone.Timezone;
import org.joda.time.DateTime;
import org.joda.time.DateTimeZone;

public class DateShifter {
    private final DateTimeZone sourceTz;
    private final DateTimeZone targetTz;
    private int shiftHours = 0;

    public DateShifter(String string, String string2) {
        if (string != null) {
            if (string.equals("EETUS")) {
                string = "America/New_York";
                this.shiftHours = -7;
            }
            this.sourceTz = DateTimeZone.forID((String)Timezone.parseId(string));
        } else {
            this.sourceTz = null;
        }
        if (string2 != null && !string2.equals("")) {
            if (string2.equals("EETUS")) {
                string2 = "America/New_York";
                this.shiftHours = 7;
            }
            this.targetTz = DateTimeZone.forID((String)Timezone.parseId(string2));
        } else {
            this.targetTz = null;
        }
    }

    public void transformToTimeZone(VersatileData versatileData) {
        if (this.sourceTz != null && this.targetTz != null) {
            DateTime dateTime = new DateTime(versatileData.time).withZoneRetainFields(this.sourceTz);
            DateTime dateTime2 = dateTime.withZone(this.targetTz).toLocalDateTime().toDateTime();
            if (this.shiftHours != 0) {
                dateTime2 = dateTime2.plusHours(this.shiftHours);
            }
            versatileData.time = dateTime2.getMillis();
        }
    }
}

