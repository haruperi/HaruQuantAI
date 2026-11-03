/*
 * Decompiled with CFR 0.152.
 */
package com.strategyquant.wizard.desktop.loader;

import com.strategyquant.wizard.desktop.utils.FileUtils;
import com.strategyquant.wizard.desktop.utils.JsonUtils;
import java.io.File;
import java.io.FileWriter;
import java.io.IOException;
import java.nio.file.Files;

public class RecentFilesLoader {
    private static final String RECENT_FILE_NAME = "recentFiles.json";
    private static final String DEFAULT_RECENT = "{\"result\":\"success\",\"files\":[]}";
    private boolean netFailed;

    public String loadRecentFiles(String string) {
        Object var2_2 = null;
        File file = new File(FileUtils.getAppFolder() + "//" + RECENT_FILE_NAME);
        if (!file.exists()) {
            return DEFAULT_RECENT;
        }
        try {
            String string2 = new String(Files.readAllBytes(file.toPath()));
            string2 = string2.replace("\\\\", "\\").replace("\\", "\\\\");
            return string2;
        }
        catch (IOException iOException) {
            return DEFAULT_RECENT;
        }
    }

    public String saveRecentFiles(String string, String string2, String string3) {
        this.saveToCloud(string, string3);
        try {
            File file = new File(FileUtils.getAppFolder() + "//" + RECENT_FILE_NAME);
            FileWriter fileWriter = new FileWriter(file);
            fileWriter.write(string2);
            fileWriter.close();
            return "{\"result\":\"success\"}";
        }
        catch (IOException iOException) {
            return JsonUtils.getErrorResonse(iOException.getMessage());
        }
    }

    private String loadFromCloud(String string) {
        this.netFailed = false;
        String string2 = "http://wizard.strategyquant.com/backend/getrecent?&s=" + string;
        try {
            String string3 = JsonUtils.doGet(string2);
            return string3;
        }
        catch (IOException iOException) {
            this.netFailed = true;
            return JsonUtils.getErrorResonse(iOException.getMessage());
        }
    }

    private String saveToCloud(String string, String string2) {
        this.netFailed = false;
        String string3 = "http://wizard.strategyquant.com/backend/saverecent?&s=" + string2;
        String string4 = string;
        try {
            String string5 = JsonUtils.doPost(string3, string4);
            return string5;
        }
        catch (IOException iOException) {
            this.netFailed = true;
            return JsonUtils.getErrorResonse(iOException.getMessage());
        }
    }
}

