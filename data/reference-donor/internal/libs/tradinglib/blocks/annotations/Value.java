/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  com.strategyquant.lib.IRandomGenerator
 */
package com.strategyquant.tradinglib.blocks.annotations;

import com.strategyquant.lib.IRandomGenerator;
import com.strategyquant.tradinglib.blocks.random.BlockParameter;

public class Value {
    public static final String Null = "Null";
    public static final int MinShift = -1000001;
    public static final int MaxShift = -1000002;
    public static final int MinPeriod = -1000003;
    public static final int MaxPeriod = -1000004;
    public static final int MinSLInPips = -1000005;
    public static final int MaxSLInPips = -1000006;
    public static final int MinSLATRMultiple = -1000007;
    public static final int MaxSLATRMultiple = -1000008;
    public static final int MinSLATRPeriod = -1000009;
    public static final int MaxSLATRPeriod = -1000010;
    public static final int MinPTInPips = -1000011;
    public static final int MaxPTInPips = -1000012;
    public static final int MinPTATRMultiple = -1000013;
    public static final int MaxPTATRMultiple = -1000014;
    public static final int MinPTATRPeriod = -1000015;
    public static final int MaxPTATRPeriod = -1000016;
    public static final int MinPTInPercent = -1000017;
    public static final int MaxPTInPercent = -1000018;
    public static final int MinSLInPercent = -1000019;
    public static final int MaxSLInPercent = -1000020;

    public static boolean isPredefined(double d) {
        return d == -1000001.0 || d == -1000002.0 || d == -1000003.0 || d == -1000004.0 || d == -1000005.0 || d == -1000006.0 || d == -1000019.0 || d == -1000020.0 || d == -1000007.0 || d == -1000008.0 || d == -1000009.0 || d == -1000010.0 || d == -1000011.0 || d == -1000012.0 || d == -1000017.0 || d == -1000018.0 || d == -1000013.0 || d == -1000014.0 || d == -1000015.0 || d == -1000016.0;
    }

    public static int generateMM(IRandomGenerator iRandomGenerator, BlockParameter blockParameter) {
        int n;
        int n2;
        int n3;
        int n4 = (int)blockParameter.minValue % 100;
        int n5 = (int)blockParameter.maxValue % 100;
        int n6 = (int)blockParameter.step % 100;
        if (n6 == 0) {
            return 0;
        }
        if (n4 < 0) {
            n4 = 0;
        }
        if (n5 > 59) {
            n5 = 59;
        }
        if ((n3 = n4 + (n2 = iRandomGenerator.nextInt(n = n5 >= n4 ? (n5 - n4) / n6 + 1 : (n5 + n4) / n6 + 1)) * n6) > 60) {
            n3 -= 60;
        }
        if (n3 == 60) {
            return 0;
        }
        return n3;
    }

    public static int generateHH(IRandomGenerator iRandomGenerator, BlockParameter blockParameter) {
        int n = (int)blockParameter.minValue / 100;
        int n2 = (int)blockParameter.maxValue / 100;
        int n3 = (int)blockParameter.step / 100;
        if (n3 == 0) {
            n3 = 1;
        }
        if (n < 0) {
            n = 0;
        }
        if (n2 > 23) {
            n2 = 23;
        }
        int n4 = (n2 - n) / n3 + 1;
        int n5 = iRandomGenerator.nextInt(n4);
        int n6 = n + n5 * n3;
        return n6;
    }
}

