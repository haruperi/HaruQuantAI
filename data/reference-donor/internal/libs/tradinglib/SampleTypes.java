/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  com.strategyquant.lib.L
 */
package com.strategyquant.tradinglib;

import com.strategyquant.lib.L;

public class SampleTypes {
    public static final byte FullSample = 127;
    public static final byte InSample = 10;
    public static final byte InSampleTraining = 11;
    public static final byte InSampleValidation = 40;
    public static final byte InSampleValidation1 = 41;
    public static final byte InSampleValidation2 = 42;
    public static final byte InSampleValidation3 = 43;
    public static final byte InSampleValidation4 = 44;
    public static final byte InSampleValidation5 = 45;
    public static final byte InSampleValidation6 = 46;
    public static final byte InSampleValidation7 = 47;
    public static final byte InSampleValidation8 = 48;
    public static final byte InSampleValidation9 = 49;
    public static final byte InSampleValidation10 = 50;
    public static final byte OutOfSample = 20;
    public static final byte OutOfSample1 = 21;
    public static final byte OutOfSample2 = 22;
    public static final byte OutOfSample3 = 23;
    public static final byte OutOfSample4 = 24;
    public static final byte OutOfSample5 = 25;
    public static final byte OutOfSample6 = 26;
    public static final byte OutOfSample7 = 27;
    public static final byte OutOfSample8 = 28;
    public static final byte OutOfSample9 = 29;
    public static final byte OutOfSample10 = 30;
    public static final byte InSampleValidationEvery = 66;
    public static final byte OutOfSampleEvery = 77;
    public static final byte NoTrade = 99;

    public static byte[] types() {
        return new byte[]{127, 10, 20};
    }

    public static String typeToString(byte by) {
        switch (by) {
            case 10: {
                return L.tsq((String)"IS");
            }
            case 11: {
                return L.tsq((String)"IST");
            }
            case 40: {
                return L.tsq((String)"ISV");
            }
            case 66: {
                return L.tsq((String)"ISV-Every");
            }
            case 41: {
                return L.tsq((String)"ISV1");
            }
            case 42: {
                return L.tsq((String)"ISV2");
            }
            case 43: {
                return L.tsq((String)"ISV3");
            }
            case 44: {
                return L.tsq((String)"ISV4");
            }
            case 45: {
                return L.tsq((String)"ISV5");
            }
            case 46: {
                return L.tsq((String)"ISV6");
            }
            case 47: {
                return L.tsq((String)"ISV7");
            }
            case 48: {
                return L.tsq((String)"ISV8");
            }
            case 49: {
                return L.tsq((String)"ISV9");
            }
            case 50: {
                return L.tsq((String)"ISV10");
            }
            case 20: {
                return L.tsq((String)"OOS");
            }
            case 77: {
                return L.tsq((String)"OOS-Every");
            }
            case 21: {
                return L.tsq((String)"OOS1");
            }
            case 22: {
                return L.tsq((String)"OOS2");
            }
            case 23: {
                return L.tsq((String)"OOS3");
            }
            case 24: {
                return L.tsq((String)"OOS4");
            }
            case 25: {
                return L.tsq((String)"OOS5");
            }
            case 26: {
                return L.tsq((String)"OOS6");
            }
            case 27: {
                return L.tsq((String)"OOS7");
            }
            case 28: {
                return L.tsq((String)"OOS8");
            }
            case 29: {
                return L.tsq((String)"OOS9");
            }
            case 30: {
                return L.tsq((String)"OOS10");
            }
            case 99: {
                return L.tsq((String)"No trade");
            }
        }
        return L.tsq((String)"Full Sample");
    }

    public static boolean isOOS(byte by) {
        return by == 20 || by >= 21 && by <= 30;
    }

    public static boolean isISV(byte by) {
        return by == 40 || by >= 41 && by <= 50;
    }

    public static String typeToFullString(byte by) {
        switch (by) {
            case 10: {
                return L.tsq((String)"In Sample");
            }
            case 11: {
                return L.tsq((String)"In sample Training");
            }
            case 40: {
                return L.tsq((String)"In sample Validation");
            }
            case 41: {
                return L.tsq((String)"In sample Validation 1");
            }
            case 42: {
                return L.tsq((String)"In sample Validation 2");
            }
            case 43: {
                return L.tsq((String)"In sample Validation 3");
            }
            case 44: {
                return L.tsq((String)"In sample Validation 4");
            }
            case 45: {
                return L.tsq((String)"In sample Validation 5");
            }
            case 46: {
                return L.tsq((String)"In sample Validation 6");
            }
            case 47: {
                return L.tsq((String)"In sample Validation 7");
            }
            case 48: {
                return L.tsq((String)"In sample Validation 8");
            }
            case 49: {
                return L.tsq((String)"In sample Validation 9");
            }
            case 50: {
                return L.tsq((String)"In sample Validation 10");
            }
            case 20: {
                return L.tsq((String)"Out of sample");
            }
            case 21: {
                return L.tsq((String)"Out of sample 1");
            }
            case 22: {
                return L.tsq((String)"Out of sample 2");
            }
            case 23: {
                return L.tsq((String)"Out of sample 3");
            }
            case 24: {
                return L.tsq((String)"Out of sample 4");
            }
            case 25: {
                return L.tsq((String)"Out of sample 5");
            }
            case 26: {
                return L.tsq((String)"Out of sample 6");
            }
            case 27: {
                return L.tsq((String)"Out of sample 7");
            }
            case 28: {
                return L.tsq((String)"Out of sample 8");
            }
            case 29: {
                return L.tsq((String)"Out of sample 9");
            }
            case 30: {
                return L.tsq((String)"Out of sample 10");
            }
            case 99: {
                return L.tsq((String)"No trade");
            }
        }
        return L.tsq((String)"Full Sample");
    }

    public static byte[] list() {
        byte[] byArray = new byte[]{10, 11, 40, 41, 42, 43, 44, 45, 46, 47, 48, 49, 50, 20, 21, 22, 23, 24, 25, 26, 27, 28, 29, 30};
        return byArray;
    }
}

