/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  org.apache.commons.codec.binary.Hex
 *  org.slf4j.Logger
 *  org.slf4j.LoggerFactory
 */
package com.strategyquant.datalib.metatrader4;

import java.io.File;
import java.io.FilenameFilter;
import java.io.IOException;
import java.nio.file.Files;
import java.security.MessageDigest;
import java.util.HashSet;
import java.util.LinkedList;
import java.util.Set;
import org.apache.commons.codec.binary.Hex;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

public class MT4Utils {
    private static final Logger Log = LoggerFactory.getLogger((String)"MT4Utils");
    private static final Set<String> IGNORE_FOLDER_SET = new HashSet<String>();

    public static final MetaTraderLocation getDataFolder(String string) {
        string = string.toLowerCase().trim();
        File file = new File(string);
        File file2 = MT4Utils.getDataFolderFile();
        File[] fileArray = file2.listFiles();
        if (fileArray == null) {
            return null;
        }
        String string2 = MT4Utils.getTerminalHash(string);
        String string3 = file2.getAbsolutePath() + "\\" + string2;
        if (new File(string3).exists()) {
            String[] stringArray = MT4Utils.getServerNames(string3);
            return new MetaTraderLocation(string3, stringArray);
        }
        return null;
    }

    public static String getTerminalHash(String string) {
        try {
            string = string.toUpperCase().replace("/", "\\");
            if (string.endsWith("\\")) {
                string = string.substring(0, string.length() - 1);
            }
            return Hex.encodeHexString((byte[])MessageDigest.getInstance("MD5").digest(string.toUpperCase().getBytes("UTF-16LE"))).toUpperCase();
        }
        catch (Exception exception) {
            Log.error("Cannot get terminal folder hash", (Throwable)exception);
            return null;
        }
    }

    public static File getDataFolderFile() {
        String string = System.getProperty("user.home");
        String string2 = string + "\\AppData\\Roaming\\MetaQuotes\\Terminal";
        return new File(string2);
    }

    public static String[] getServerNames(String string) {
        File[] fileArray = new File(string, "history").listFiles();
        LinkedList<String> linkedList = new LinkedList<String>();
        if (fileArray != null) {
            for (File file : fileArray) {
                String[] stringArray;
                if (file.isFile() || IGNORE_FOLDER_SET.contains(file.getName()) || (stringArray = file.list(new FilenameFilter(){

                    @Override
                    public boolean accept(File file, String string) {
                        return string.endsWith("hst");
                    }
                })) == null || stringArray.length <= 0) continue;
                linkedList.add(file.getName());
            }
        }
        return linkedList.toArray(new String[0]);
    }

    private static String readOriginFile(File file) {
        File file2 = new File(file, "origin.txt");
        if (!file2.exists()) {
            return null;
        }
        try {
            String string = new String(Files.readAllBytes(file2.toPath()), "UTF-16LE");
            if (string.length() > 0) {
                string = string.substring(1);
            }
            return string;
        }
        catch (IOException iOException) {
            return null;
        }
    }

    public static void main(String[] stringArray) {
        MetaTraderLocation metaTraderLocation = MT4Utils.getDataFolder("C:\\Program Files (x86)\\MetaTrader 4");
        System.out.println(metaTraderLocation.getDataFolder() + " " + metaTraderLocation.getServerNames());
    }

    static {
        IGNORE_FOLDER_SET.add("default");
        IGNORE_FOLDER_SET.add("downloads");
        IGNORE_FOLDER_SET.add("deleted");
    }

    public static class MetaTraderLocation {
        private String dataFolder;
        private String[] serverNames;

        public MetaTraderLocation(String string, String[] stringArray) {
            this.dataFolder = string;
            this.serverNames = stringArray;
        }

        public String getDataFolder() {
            return this.dataFolder;
        }

        public String[] getServerNames() {
            return this.serverNames;
        }
    }
}

