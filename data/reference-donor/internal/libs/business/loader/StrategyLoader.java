/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  com.strategyquant.lib.L
 *  com.strategyquant.lib.utils.SQFileChooserFactory
 */
package com.strategyquant.wizard.desktop.loader;

import com.strategyquant.lib.L;
import com.strategyquant.lib.utils.SQFileChooserFactory;
import com.strategyquant.wizard.desktop.settings.Settings;
import com.strategyquant.wizard.desktop.utils.JsonUtils;
import java.awt.Component;
import java.io.ByteArrayInputStream;
import java.io.ByteArrayOutputStream;
import java.io.EOFException;
import java.io.File;
import java.io.FileWriter;
import java.io.IOException;
import java.io.InputStream;
import java.nio.file.Files;
import java.nio.file.OpenOption;
import java.nio.file.Paths;
import java.util.Enumeration;
import java.util.zip.ZipEntry;
import java.util.zip.ZipFile;
import java.util.zip.ZipInputStream;
import java.util.zip.ZipOutputStream;
import javax.swing.JFileChooser;
import javax.swing.filechooser.FileNameExtensionFilter;

public class StrategyLoader {
    private static final String STRATEGY_IN_ZIP = "strategy_Portfolio.xml";
    private Component parent;

    public StrategyLoader(Component component) {
        this.parent = component;
    }

    public String loadFileWithName() {
        String string = Settings.get().get("strategyFolder");
        JFileChooser jFileChooser = SQFileChooserFactory.createPersistingJFileChooser(string == null || string.isEmpty() ? null : string).getJFileChooser();
        jFileChooser.addChoosableFileFilter(new FileNameExtensionFilter("SQW files", "sqw"));
        jFileChooser.addChoosableFileFilter(new FileNameExtensionFilter("SQX files", "sqx"));
        jFileChooser.addChoosableFileFilter(new FileNameExtensionFilter("SQ4 files", "sq4"));
        jFileChooser.addChoosableFileFilter(new FileNameExtensionFilter("STR files", "str"));
        int n = jFileChooser.showOpenDialog(this.parent);
        if (n == 0) {
            File file = jFileChooser.getSelectedFile();
            Settings.get().set("strategyFolder", file.getParent());
            return this.loadFile(file.getAbsolutePath());
        }
        return null;
    }

    public String loadFile(String string) {
        File file = new File(string);
        StringBuilder stringBuilder = new StringBuilder();
        stringBuilder.append("{");
        if (!file.exists()) {
            stringBuilder.append("\"result\":\"error\",\"errors\":{\"message\":\"File: " + string.replace("\\", "\\\\") + " not found.\"}");
        } else {
            try {
                byte[] byArray = Files.readAllBytes(file.toPath());
                String string2 = new String(byArray);
                if (this.isZip(string2)) {
                    string2 = this.getUnzippedStrategy(byArray);
                }
                return string + "#;#" + string2;
            }
            catch (EOFException eOFException) {
                stringBuilder.append("\"result\":\"error\",\"errors\":{\"message\":\"Zip file is corrupted\"}");
            }
            catch (Throwable throwable) {
                throwable.printStackTrace();
                stringBuilder.append("\"result\":\"error\",\"errors\":{\"message\":\"" + throwable.getMessage().replace("\\", "\\\\").replace("\n", "").replace("\r", "") + "\"}");
            }
        }
        stringBuilder.append("}");
        String string3 = stringBuilder.toString();
        return string3;
    }

    /*
     * WARNING - Removed try catching itself - possible behaviour change.
     */
    private String getUnzippedStrategy(byte[] byArray) throws IOException {
        try (ZipInputStream zipInputStream = new ZipInputStream(new ByteArrayInputStream(byArray));){
            ZipEntry zipEntry = null;
            while ((zipEntry = zipInputStream.getNextEntry()) != null) {
                if (!zipEntry.getName().equals(STRATEGY_IN_ZIP)) continue;
                byte[] byArray2 = new byte[8192];
                try (ByteArrayOutputStream byteArrayOutputStream = new ByteArrayOutputStream();){
                    int n;
                    while ((n = zipInputStream.read(byArray2)) != -1) {
                        byteArrayOutputStream.write(byArray2, 0, n);
                    }
                }
                String string = new String(byteArrayOutputStream.toByteArray());
                return string;
            }
        }
        throw new RuntimeException(L.t((String)"Strategy was not found in zip file", (Object[])new Object[0]));
    }

    private boolean isZip(String string) {
        return string.startsWith("PK");
    }

    private boolean hasExtension(String string) {
        int n = string.lastIndexOf(".");
        if (n == -1) {
            return false;
        }
        int n2 = string.lastIndexOf(File.separator);
        return n2 < n;
    }

    public String saveFile(String string, String string2, boolean bl) throws IOException {
        boolean bl2;
        File file;
        File file2 = file = string2 == null || string2.isEmpty() ? null : new File(string2);
        if (bl || file2 == null) {
            String string3 = Settings.get().get("strategyFolder");
            JFileChooser jFileChooser = SQFileChooserFactory.createPersistingJFileChooser((String)(string3.isEmpty() ? null : string3)).getJFileChooser();
            jFileChooser.addChoosableFileFilter(new FileNameExtensionFilter("SQW files", "sqw"));
            jFileChooser.addChoosableFileFilter(new FileNameExtensionFilter("SQX files", "sqx"));
            jFileChooser.addChoosableFileFilter(new FileNameExtensionFilter("SQ4 files", "sq4"));
            int n = jFileChooser.showSaveDialog(this.parent);
            if (n != 0) {
                return null;
            }
            file2 = jFileChooser.getSelectedFile();
            Settings.get().set("strategyFolder", file2.getParent());
            if (!this.hasExtension(file2.getAbsolutePath())) {
                file2 = new File(file2.getAbsoluteFile() + ".sqx");
            }
        }
        if (bl2 = file2.getAbsolutePath().endsWith("sqw")) {
            this.saveFile(string, file2);
        } else if (file != null && file.exists() && this.isZip(file)) {
            this.saveToZip(file, file2, string);
        } else {
            this.saveToZip(file2, string);
        }
        return file2.getAbsolutePath();
    }

    private void saveToZip(File file, File file2, String string) throws IOException {
        ByteArrayOutputStream byteArrayOutputStream = new ByteArrayOutputStream();
        try (Object object = new ZipFile(file);){
            ZipOutputStream zipOutputStream = new ZipOutputStream(byteArrayOutputStream);
            Enumeration<? extends ZipEntry> enumeration = ((ZipFile)object).entries();
            while (enumeration.hasMoreElements()) {
                ZipEntry zipEntry = enumeration.nextElement();
                if (!zipEntry.getName().equalsIgnoreCase(STRATEGY_IN_ZIP)) {
                    int n;
                    zipOutputStream.putNextEntry(zipEntry);
                    InputStream inputStream = ((ZipFile)object).getInputStream(zipEntry);
                    byte[] byArray = new byte[1024];
                    while ((n = inputStream.read(byArray)) > 0) {
                        zipOutputStream.write(byArray, 0, n);
                    }
                } else {
                    zipOutputStream.putNextEntry(new ZipEntry(STRATEGY_IN_ZIP));
                    zipOutputStream.write(string.getBytes());
                }
                zipOutputStream.closeEntry();
            }
            zipOutputStream.close();
        }
        object = byteArrayOutputStream.toByteArray();
        Files.write(Paths.get(file2.getAbsolutePath(), new String[0]), (byte[])object, new OpenOption[0]);
    }

    private void saveToZip(File file, String string) throws IOException {
        ByteArrayOutputStream byteArrayOutputStream = new ByteArrayOutputStream();
        ZipOutputStream zipOutputStream = new ZipOutputStream(byteArrayOutputStream);
        zipOutputStream.putNextEntry(new ZipEntry(STRATEGY_IN_ZIP));
        zipOutputStream.write(string.getBytes());
        zipOutputStream.closeEntry();
        zipOutputStream.close();
        byte[] byArray = byteArrayOutputStream.toByteArray();
        Files.write(Paths.get(file.getAbsolutePath(), new String[0]), byArray, new OpenOption[0]);
    }

    private boolean isZip(File file) {
        try {
            byte[] byArray = Files.readAllBytes(file.toPath());
            String string = new String(byArray);
            return this.isZip(string);
        }
        catch (Exception exception) {
            exception.printStackTrace();
            return false;
        }
    }

    private void saveFile(String string, File file) throws IOException {
        FileWriter fileWriter = null;
        fileWriter = new FileWriter(file);
        fileWriter.write(string);
        fileWriter.close();
    }

    public String loadCloudFileList(String string, String string2) {
        return "{\"files\":[],\"result\":\"success\"}";
    }

    public String loadCloudFile(String string, String string2) {
        String string3 = "http://wizard.strategyquant.com/backend/get?filename=" + string + "&s=" + string2;
        try {
            String string4 = JsonUtils.doGet(string3);
            return string4;
        }
        catch (IOException iOException) {
            return JsonUtils.getErrorResonse(iOException.getMessage());
        }
    }

    public String saveCloudFile(String string, String string2, String string3) {
        String string4 = "http://wizard.strategyquant.com/backend/save?s=" + string3 + "&filename=" + string;
        String string5 = "content=" + string2;
        try {
            String string6 = JsonUtils.doPost(string4, string5);
            return string6;
        }
        catch (IOException iOException) {
            return JsonUtils.getErrorResonse(iOException.getMessage());
        }
    }

    public String createCloudFolder(String string, String string2) {
        String string3 = "http://wizard.strategyquant.com/backend/createdir?s=" + string2 + "&filename=" + string;
        try {
            String string4 = JsonUtils.doGet(string3);
            return string4;
        }
        catch (IOException iOException) {
            return JsonUtils.getErrorResonse(iOException.getMessage());
        }
    }

    public void dispose() {
        this.parent = null;
    }
}

