/*
 * Decompiled with CFR 0.152.
 */
package com.strategyquant.strategyquant;

import com.strategyquant.strategyquant.SQApp;
import java.lang.reflect.Field;
import sun.misc.Unsafe;

public class SQConsoleStarter {
    public static void main(String[] stringArray) throws Exception {
        SQConsoleStarter.disableWarning();
        SQApp.main(stringArray, true);
    }

    public static void disableWarning() {
        try {
            Field field = Unsafe.class.getDeclaredField("theUnsafe");
            field.setAccessible(true);
            Unsafe unsafe = (Unsafe)field.get(null);
            Class<?> clazz = Class.forName("jdk.internal.module.IllegalAccessLogger");
            Field field2 = clazz.getDeclaredField("logger");
            unsafe.putObjectVolatile(clazz, unsafe.staticFieldOffset(field2), null);
        }
        catch (Exception exception) {
            // empty catch block
        }
    }
}

