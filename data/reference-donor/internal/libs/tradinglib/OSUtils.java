/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  com.sun.jna.Library
 *  com.sun.jna.Native
 *  com.sun.jna.win32.W32APIOptions
 */
package com.strategyquant.tradinglib;

import com.sun.jna.Library;
import com.sun.jna.Native;
import com.sun.jna.win32.W32APIOptions;
import java.util.Map;

public class OSUtils {
    public static void hideConsole() {
        System.out.println("Hiding console...");
        try {
            int n = Kernel32.INSTANCE.GetConsoleWindow();
            if (n != 0) {
                User32.INSTANCE.ShowWindow(n, 0);
                System.out.println("Console window hidden.");
            } else {
                System.err.println("No console window found.");
            }
        }
        catch (Error | Exception throwable) {
            System.err.println("Error while hiding console: " + throwable.getMessage());
        }
    }

    public static interface Kernel32
    extends Library {
        public static final Kernel32 INSTANCE = (Kernel32)Native.load((String)"kernel32", Kernel32.class);

        public int GetConsoleWindow();
    }

    public static interface User32
    extends Library {
        public static final User32 INSTANCE = (User32)Native.load((String)"user32", User32.class, (Map)W32APIOptions.DEFAULT_OPTIONS);

        public boolean ShowWindow(int var1, int var2);
    }
}

