/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  org.apache.commons.codec.digest.DigestUtils
 *  org.slf4j.Logger
 *  org.slf4j.LoggerFactory
 */
package com.strategyquant.gridlib;

import java.io.File;
import java.io.FileInputStream;
import java.io.FileOutputStream;
import java.io.IOException;
import java.io.InputStream;
import java.util.LinkedList;
import java.util.List;
import java.util.zip.ZipEntry;
import java.util.zip.ZipInputStream;
import java.util.zip.ZipOutputStream;
import org.apache.commons.codec.digest.DigestUtils;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

public class FileHelper {
    private static final Logger LOGGER = LoggerFactory.getLogger(FileHelper.class);
    private static final int BUFFER_SIZE = 10240;

    private static void generateFileList(String string, File file, List<String> list) {
        if (file.isFile()) {
            list.add(FileHelper.generateZipEntry(string, file.toString()));
        }
        if (file.isDirectory()) {
            String[] stringArray;
            for (String string2 : stringArray = file.list()) {
                FileHelper.generateFileList(string, new File(file, string2), list);
            }
        }
    }

    private static String generateZipEntry(String string, String string2) {
        return string2.substring(string.length() + 1, string2.length());
    }

    public static String countHash(String string) throws IOException {
        StringBuilder stringBuilder = new StringBuilder();
        List<String> list = FileHelper.getPaths(string);
        int n = string.length();
        for (String string2 : list) {
            String string3 = string2.substring(n + 1);
            if (stringBuilder.length() > 0) {
                stringBuilder.append("\n");
            }
            stringBuilder.append(FileHelper.countHash(new File(string2)) + " " + string3);
        }
        return stringBuilder.toString();
    }

    private static List<String> getPaths(String string) {
        LinkedList<String> linkedList = new LinkedList<String>();
        FileHelper.fillPaths(linkedList, string);
        return linkedList;
    }

    private static void fillPaths(List<String> list, String string) {
        File file = new File(string);
        File[] fileArray = file.listFiles();
        if (fileArray != null) {
            for (File file2 : fileArray) {
                if (file2.isDirectory()) {
                    FileHelper.fillPaths(list, file2.getAbsolutePath());
                    continue;
                }
                list.add(file2.getAbsolutePath());
            }
        }
    }

    public static String countHash(File file) throws IOException {
        FileInputStream fileInputStream = new FileInputStream(file);
        String string = DigestUtils.md5Hex((InputStream)fileInputStream);
        fileInputStream.close();
        return string;
    }

    public static File zip(String string) throws IOException {
        LinkedList<String> linkedList = new LinkedList<String>();
        FileHelper.generateFileList(string, new File(string), linkedList);
        return FileHelper.zip(string, linkedList);
    }

    public static File zip(String string, List<String> list) throws IOException {
        LOGGER.debug("Zipping files in folder:" + string);
        byte[] byArray = new byte[10240];
        File file = File.createTempFile("strategyquant_", ".zip");
        FileOutputStream fileOutputStream = new FileOutputStream(file);
        try (ZipOutputStream zipOutputStream = new ZipOutputStream(fileOutputStream);){
            for (String string2 : list) {
                string2 = string2.trim();
                LOGGER.debug("Adding file: " + string2 + "...");
                ZipEntry zipEntry = new ZipEntry(string2);
                zipOutputStream.putNextEntry(zipEntry);
                try (FileInputStream fileInputStream = new FileInputStream(new File(string, string2));){
                    int n;
                    while ((n = fileInputStream.read(byArray)) > 0) {
                        zipOutputStream.write(byArray, 0, n);
                    }
                }
            }
            zipOutputStream.closeEntry();
            LOGGER.debug("Files successfully compressed");
        }
        return file;
    }

    public static void unzip(String string, File file) {
        byte[] byArray = new byte[10240];
        try {
            File file2 = new File(string);
            if (!file2.exists()) {
                file2.mkdir();
            }
            try (ZipInputStream zipInputStream = new ZipInputStream(new FileInputStream(file));){
                ZipEntry zipEntry = zipInputStream.getNextEntry();
                while (zipEntry != null) {
                    String string2 = zipEntry.getName();
                    File file3 = new File(string, string2);
                    LOGGER.debug("file unzip : " + file3.getAbsoluteFile());
                    new File(file3.getParent()).mkdirs();
                    try (FileOutputStream fileOutputStream = new FileOutputStream(file3);){
                        int n;
                        while ((n = zipInputStream.read(byArray)) > 0) {
                            fileOutputStream.write(byArray, 0, n);
                        }
                    }
                    zipEntry = zipInputStream.getNextEntry();
                }
                zipInputStream.closeEntry();
            }
            LOGGER.debug("UnZip done");
        }
        catch (IOException iOException) {
            iOException.printStackTrace();
        }
    }
}

