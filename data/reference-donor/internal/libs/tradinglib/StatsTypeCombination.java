/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  org.slf4j.Logger
 *  org.slf4j.LoggerFactory
 */
package com.strategyquant.tradinglib;

import com.strategyquant.tradinglib.Directions;
import com.strategyquant.tradinglib.PlTypes;
import com.strategyquant.tradinglib.SampleTypes;
import java.io.Serializable;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

public class StatsTypeCombination
implements Serializable {
    public static final Logger Log = LoggerFactory.getLogger((String)"StatsTypeCombination");
    private byte direction = 0;
    private byte plType = (byte)10;
    private byte sampleType = (byte)127;
    private int key;

    public StatsTypeCombination(byte by, byte by2, byte by3) {
        this.direction = by;
        this.plType = by2;
        this.sampleType = by3;
        this.key = StatsTypeCombination.createKey(by, by2, by3);
    }

    public StatsTypeCombination set(byte by, byte by2, byte by3) {
        this.direction = by;
        this.plType = by2;
        this.sampleType = by3;
        this.key = StatsTypeCombination.createKey(by, by2, by3);
        return this;
    }

    public static int createKey(byte by, byte by2, byte by3) {
        int n = by << 16 | by2 << 8 | by3;
        if (n < 0) {
            n *= -1;
        }
        return n;
    }

    public byte getDirection() {
        return this.direction;
    }

    public byte getPLType() {
        return this.plType;
    }

    public byte getSampleType() {
        return this.sampleType;
    }

    public int getKey() {
        return this.key;
    }

    public String getKeyAsStr() {
        return "Dir: " + Directions.typeToString(this.direction) + ", PL: " + PlTypes.typeToString(this.plType) + ", Sample: " + SampleTypes.typeToString(this.sampleType);
    }

    public String toString() {
        return Integer.toString(this.key);
    }

    public boolean isMainOne() {
        return this.direction == 0 && this.plType == 10 && this.sampleType == 127;
    }
}

