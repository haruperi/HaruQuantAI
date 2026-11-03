/*
 * Decompiled with CFR 0.152.
 */
package com.strategyquant.gridlib.client;

public class RunningStatus {
    public static final int BeforeStart = 0;
    public static final int Running = 1;
    public static final int Paused = 2;
    public static final int Finished = 3;
    public static final int Stopped = 4;
    public static final int Pausing = 5;
    public static final int Stopping = 6;
    public static final int Error = 50;
    public static final int Loading = 100;

    public static String printStatus(int n) {
        switch (n) {
            case 0: {
                return "BeforeStart";
            }
            case 1: {
                return "Running";
            }
            case 3: {
                return "Finished";
            }
            case 2: {
                return "Paused";
            }
            case 4: {
                return "Stopped";
            }
            case 5: {
                return "Pausing";
            }
            case 6: {
                return "Stopping";
            }
            case 50: {
                return "Error";
            }
            case 100: {
                return "Loading";
            }
        }
        return "? status: " + n;
    }

    public static boolean canBeStarted(int n) {
        return n == 0 || n == 4 || n == 50 || n == 3;
    }
}

