/*
 * Decompiled with CFR 0.152.
 */
package com.strategyquant.wizard.desktop.utils;

import java.io.File;

public class FileUtils {
    public static String getAppFolder() {
        return FileUtils.getRootFolder() + "\\internal\\web\\SQWIZARD\\";
    }

    public static String getRootFolder() {
        File file = new File("");
        return file.getAbsolutePath();
    }

    public static String getCodeFolder() {
        return FileUtils.getRootFolder() + "\\extend\\code\\";
    }
}

