/*
 * Decompiled with CFR 0.152.
 */
package com.strategyquant.pluginlib;

import java.io.File;
import java.util.ArrayList;
import java.util.Collections;

public class DirManager {
    private static String originPath;

    public static void usePathsRelativeTo(String string) {
        originPath = string;
        originPath = originPath.replace("\\", "/");
        while (originPath.endsWith("/")) {
            originPath = originPath.substring(0, originPath.length() - 1);
        }
    }

    public static void useAbsolutePaths() {
        originPath = null;
    }

    public static ArrayList<String> listAllSubdirectoryPaths(String string) throws Exception {
        ArrayList<String> arrayList = new ArrayList<String>();
        ArrayList<String> arrayList2 = DirManager.getSubdirectoryNames(string);
        arrayList.addAll(arrayList2);
        ArrayList<String> arrayList3 = arrayList2;
        while (!(arrayList3 = DirManager.getSubdirectoriesNames(arrayList3)).isEmpty()) {
            arrayList.addAll(arrayList3);
        }
        return arrayList;
    }

    public static ArrayList<String> getSubdirectoryNames(String string) throws Exception {
        File[] fileArray;
        ArrayList<String> arrayList = new ArrayList<String>();
        File file = new File(string);
        if (!file.exists() || !file.isDirectory()) {
            return arrayList;
        }
        for (File file2 : fileArray = file.listFiles()) {
            String string2;
            if (!file2.isDirectory() || (string2 = file2.getAbsolutePath()).contains(".svn")) continue;
            arrayList.add(DirManager.formatPath(string2));
        }
        Collections.sort(arrayList);
        return arrayList;
    }

    private static ArrayList<String> getSubdirectoriesNames(ArrayList<String> arrayList) throws Exception {
        ArrayList<String> arrayList2 = new ArrayList<String>();
        for (String string : arrayList) {
            arrayList2.addAll(DirManager.getSubdirectoryNames(string));
        }
        return arrayList2;
    }

    public static ArrayList<String> listFileNamesInFolder(String string) {
        ArrayList<String> arrayList = new ArrayList<String>();
        File file = new File(string);
        if (file.exists()) {
            for (File file2 : file.listFiles()) {
                if (file2.isDirectory()) continue;
                String string2 = file2.getAbsolutePath();
                arrayList.add(DirManager.formatPath(string2));
            }
        }
        return arrayList;
    }

    private static String formatPath(String string) {
        string = string.replace("\\", "/");
        return string;
    }
}

