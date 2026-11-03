/*
 * Decompiled with CFR 0.152.
 */
package com.strategyquant.tradinglib.backtest;

public class BacktestDataType {
    public static final int File = 0;
    public static final int Offheap = 1;
    public static final int Array = 2;

    public static String toString(int n) {
        switch (n) {
            case 0: {
                return "File";
            }
            case 1: {
                return "Offheap";
            }
            case 2: {
                return "Array";
            }
        }
        return "Unknown";
    }
}

