/*
 * Decompiled with CFR 0.152.
 */
package com.strategyquant.gridlib;

public class ConsoleHelper {
    public void run(KeyHandler keyHandler) throws Exception {
        char c;
        while ((c = (char)System.in.read()) != 'q') {
            if (keyHandler == null) continue;
            keyHandler.handle(c);
        }
    }

    public static interface KeyHandler {
        public void handle(char var1) throws Exception;
    }
}

