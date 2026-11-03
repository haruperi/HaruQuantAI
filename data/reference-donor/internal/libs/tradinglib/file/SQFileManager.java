/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  com.strategyquant.lib.L
 *  com.strategyquant.lib.SQUtils
 *  com.strategyquant.lib.XMLUtil
 *  com.strategyquant.lib.app.MainApp
 *  org.jdom2.Content
 *  org.jdom2.Element
 *  org.slf4j.Logger
 *  org.slf4j.LoggerFactory
 */
package com.strategyquant.tradinglib.file;

import com.strategyquant.lib.L;
import com.strategyquant.lib.SQUtils;
import com.strategyquant.lib.XMLUtil;
import com.strategyquant.lib.app.MainApp;
import com.strategyquant.tradinglib.project.DefaultProjectConfig;
import com.strategyquant.tradinglib.project.ProjectResources;
import com.strategyquant.tradinglib.project.SQProject;
import com.strategyquant.tradinglib.project.StrategySaver;
import com.strategyquant.tradinglib.taskImpl.ISQTask;
import java.io.File;
import java.io.FileInputStream;
import java.io.FileOutputStream;
import java.io.IOException;
import java.io.InputStream;
import java.io.OutputStream;
import java.net.URI;
import java.nio.charset.StandardCharsets;
import java.nio.file.FileSystem;
import java.nio.file.FileSystems;
import java.nio.file.Files;
import java.nio.file.OpenOption;
import java.nio.file.Path;
import java.nio.file.StandardCopyOption;
import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.zip.ZipEntry;
import java.util.zip.ZipFile;
import java.util.zip.ZipInputStream;
import java.util.zip.ZipOutputStream;
import org.jdom2.Content;
import org.jdom2.Element;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

public class SQFileManager {
    private static final Logger Log = LoggerFactory.getLogger(SQFileManager.class);
    public static final String CFX_SUFFIX = "cfx";
    public static final String SQB_SUFFIX = "sqb";
    public static final String PLA_SUFFIX = "pla";
    private static final String CONFIG_FILE = "config.xml";
    public static final String TASK_XML_FILE_ATTR = "taskXMLFile";
    private static Map<String, String> ZipFileSystemConfig = null;

    public static File saveFile(String string, String string2) throws Exception {
        return SQFileManager.saveFile(string, string2, null);
    }

    public static File createV136ProjectFile(SQProject sQProject) throws Exception {
        return SQFileManager.createV136ProjectFile(sQProject.getProjectConfigFile(), sQProject.getConfig());
    }

    public static File createV136ProjectFile(File file, Element element) throws Exception {
        File file2 = SQFileManager.tryCreateProjectBackupFile(file);
        File file3 = SQFileManager.ensureDirExists(file.getAbsolutePath());
        HashMap<String, Element> hashMap = SQFileManager.convertOldProjectConfig(element);
        try (ZipOutputStream zipOutputStream = new ZipOutputStream((OutputStream)new FileOutputStream(file3), StandardCharsets.UTF_8);){
            for (String object : hashMap.keySet()) {
                try {
                    Element exception = hashMap.get(object);
                    ZipEntry zipEntry = new ZipEntry(object);
                    zipOutputStream.putNextEntry(zipEntry);
                    byte[] byArray = XMLUtil.elementToString((Element)exception, (boolean)true).getBytes(StandardCharsets.UTF_8);
                    zipOutputStream.write(byArray, 0, byArray.length);
                    zipOutputStream.closeEntry();
                }
                catch (Exception exception) {
                    throw new Exception(L.t((String)"Couldn't save task file '%s'.", (Object[])new Object[]{object}), exception);
                }
            }
            try {
                ZipEntry zipEntry = new ZipEntry(CONFIG_FILE);
                zipOutputStream.putNextEntry(zipEntry);
                byte[] byArray = SQFileManager.tryCorrectVersion(XMLUtil.elementToString((Element)element, (boolean)true)).getBytes(StandardCharsets.UTF_8);
                zipOutputStream.write(byArray, 0, byArray.length);
                zipOutputStream.closeEntry();
            }
            catch (Exception exception) {
                throw new Exception(L.t((String)"Couldn't save config.xml file.", (Object[])new Object[0]), exception);
            }
        }
        catch (Exception exception) {
            throw new Exception(L.t((String)"Failed to save project file - %s", (Object[])new Object[]{exception.getMessage()}), exception);
        }
        if (file2 != null) {
            Files.delete(file2.toPath());
        }
        return file3;
    }

    public static HashMap<String, Element> convertOldProjectConfig(Element element) throws Exception {
        Element element2 = XMLUtil.getChildElem((Element)element, (String)"Tasks");
        List list = element2.getChildren("Task");
        HashMap<String, Element> hashMap = new HashMap<String, Element>();
        for (int i = 0; i < list.size(); ++i) {
            Element element3 = (Element)list.get(i);
            try {
                Element element4 = XMLUtil.getChildElem((Element)element3, (String)"Settings");
                String string = XMLUtil.getStringAttr((Element)element3, (String)"type", (String)"Unknown");
                String string2 = string + "-Task" + (i + 1) + ".xml";
                element3.setAttribute(TASK_XML_FILE_ATTR, string2);
                element3.removeContent();
                hashMap.put(string2, element4.clone());
                continue;
            }
            catch (Exception exception) {
                throw new Exception(L.t((String)"Unable to convert old task '%s' to new project format", (Object[])new Object[]{element3 != null ? element3.getAttributeValue("name") : "null"}), exception);
            }
        }
        element.setAttribute("version", MainApp.getAppVersion());
        return hashMap;
    }

    public static File createV136ProjectFile(File file, DefaultProjectConfig defaultProjectConfig) throws Exception {
        File file2 = SQFileManager.tryCreateProjectBackupFile(file);
        File file3 = SQFileManager.ensureDirExists(file.getAbsolutePath());
        try (ZipOutputStream zipOutputStream = new ZipOutputStream((OutputStream)new FileOutputStream(file3), StandardCharsets.UTF_8);){
            Object object;
            Object object2;
            if (defaultProjectConfig.taskConfig != null) {
                object2 = defaultProjectConfig.taskXMLFileName;
                try {
                    object = new ZipEntry(defaultProjectConfig.taskXMLFileName);
                    zipOutputStream.putNextEntry((ZipEntry)object);
                    byte[] byArray = XMLUtil.elementToString((Element)defaultProjectConfig.taskConfig, (boolean)true).getBytes(StandardCharsets.UTF_8);
                    zipOutputStream.write(byArray, 0, byArray.length);
                    zipOutputStream.closeEntry();
                }
                catch (Exception exception) {
                    throw new Exception(L.t((String)"Couldn't save task file '%s'.", (Object[])new Object[]{object2}), exception);
                }
            }
            try {
                object2 = new ZipEntry(CONFIG_FILE);
                zipOutputStream.putNextEntry((ZipEntry)object2);
                object = SQFileManager.tryCorrectVersion(XMLUtil.elementToString((Element)defaultProjectConfig.projectConfig, (boolean)true)).getBytes(StandardCharsets.UTF_8);
                zipOutputStream.write((byte[])object, 0, ((Object)object).length);
                zipOutputStream.closeEntry();
            }
            catch (Exception exception) {
                throw new Exception(L.t((String)"Couldn't save config.xml file.", (Object[])new Object[0]), exception);
            }
        }
        catch (Exception exception) {
            throw new Exception(L.t((String)"Failed to save project file - %s", (Object[])new Object[]{exception.getMessage()}), exception);
        }
        if (file2 != null) {
            Files.delete(file2.toPath());
        }
        return file3;
    }

    private static File tryCreateProjectBackupFile(File file) throws Exception {
        if (!file.exists()) {
            return null;
        }
        File file2 = new File(SQUtils.stripExtension((String)file.getAbsolutePath()) + "_backup." + SQUtils.getExtension((String)file.getAbsolutePath()));
        Files.copy(file.toPath(), file2.toPath(), StandardCopyOption.REPLACE_EXISTING);
        return file2;
    }

    public static Element loadProjectConfig(File file) throws Exception {
        String string = SQFileManager.getZipContent(file.getAbsolutePath(), CONFIG_FILE);
        return XMLUtil.stringToElement((String)string);
    }

    public static void updateProjectConfig(SQProject sQProject) throws Exception {
        SQFileManager.updateProjectConfig(sQProject.getProjectConfigFile(), sQProject.getConfig());
    }

    public static void updateProjectConfig(File file, Element element) throws Exception {
        SQFileManager.updateZipContent(file, CONFIG_FILE, XMLUtil.elementToString((Element)element, (boolean)true));
    }

    public static HashMap<String, Element> loadTaskConfigs(File file) throws Exception {
        Object object;
        HashMap<String, Element> hashMap = new HashMap<String, Element>();
        if (file == null) {
            throw new Exception(L.t((String)"Project file is null", (Object[])new Object[0]));
        }
        if (!file.exists()) {
            throw new Exception(L.t((String)"Project file '%s' doesn't exist", (Object[])new Object[]{file.getAbsolutePath()}));
        }
        ZipFile zipFile = new ZipFile(file);
        try {
            object = zipFile.entries();
            while (object.hasMoreElements()) {
                ZipEntry zipEntry = object.nextElement();
                String string = zipEntry.getName();
                try {
                    if (string.equals(CONFIG_FILE)) continue;
                    String string2 = SQUtils.inputStreamToString((InputStream)zipFile.getInputStream(zipEntry));
                    if (string2.trim().isEmpty()) {
                        throw new Exception(L.t((String)"Empty file.", (Object[])new Object[0]));
                    }
                    hashMap.put(string, XMLUtil.stringToElement((String)string2));
                }
                catch (Exception exception) {
                    throw new Exception(L.t((String)"Couldn't load task file '%s'", (Object[])new Object[]{string}), exception);
                }
            }
            object = hashMap;
        }
        catch (Throwable throwable) {
            try {
                try {
                    zipFile.close();
                }
                catch (Throwable throwable2) {
                    throwable.addSuppressed(throwable2);
                }
                throw throwable;
            }
            catch (Exception exception) {
                throw new Exception(L.t((String)"Failed to load task configs - %s", (Object[])new Object[]{exception.getMessage()}), exception);
            }
        }
        zipFile.close();
        return object;
    }

    public static Element loadTaskConfig(File file, String string) throws Exception {
        try {
            String string2 = SQFileManager.getZipContent(file.getAbsolutePath(), string);
            return XMLUtil.stringToElement((String)string2);
        }
        catch (Exception exception) {
            throw new Exception(L.t((String)"Error while loading task xml %s", (Object[])new Object[]{string}));
        }
    }

    public static void updateTaskConfig(File file, String string, Element element) throws Exception {
        SQFileManager.updateZipContent(file, string, XMLUtil.elementToString((Element)element, (boolean)true));
    }

    public static void updateTaskConfig(FileSystem fileSystem, String string, String string2, Element element) throws Exception {
        SQFileManager.updateZipContent(fileSystem, string, string2, XMLUtil.elementToString((Element)element, (boolean)true));
    }

    public static void updateWholeProjectConfig(SQProject sQProject) throws Exception {
        File file = sQProject.getProjectConfigFile();
        File file2 = SQFileManager.tryCreateProjectBackupFile(file);
        SQFileManager.saveProjectFile(sQProject, sQProject.getProjectConfigFile());
        Files.delete(file2.toPath());
    }

    public static void saveProjectFile(SQProject sQProject, File file) throws Exception {
        SQFileManager.ensureDirExists(file.getAbsolutePath());
        ProjectResources.addResources(sQProject);
        try (ZipOutputStream zipOutputStream = new ZipOutputStream((OutputStream)new FileOutputStream(file), StandardCharsets.UTF_8);){
            byte[] byArray = null;
            Element element = sQProject.getConfig();
            Element element2 = element.getChild("Tasks");
            List list = element2.getChildren("Task");
            ArrayList<ISQTask> arrayList = sQProject.getTasks();
            if (list.size() != arrayList.size()) {
                throw new Exception("Project integrity failed.");
            }
            try {
                zipOutputStream.putNextEntry(new ZipEntry(CONFIG_FILE));
                byArray = XMLUtil.elementToString((Element)element, (boolean)true).getBytes(StandardCharsets.UTF_8);
                zipOutputStream.write(byArray, 0, byArray.length);
            }
            catch (Exception exception) {
                throw new Exception("Couldn't save config.xml file.", exception);
            }
            for (int i = 0; i < arrayList.size(); ++i) {
                ISQTask iSQTask = (ISQTask)arrayList.get(i);
                String string = iSQTask.getTaskXMLFileName();
                try {
                    zipOutputStream.putNextEntry(new ZipEntry(string));
                    byArray = XMLUtil.elementToString((Element)iSQTask.getConfig(), (boolean)true).getBytes(StandardCharsets.UTF_8);
                    zipOutputStream.write(byArray, 0, byArray.length);
                    continue;
                }
                catch (Exception exception) {
                    throw new Exception(String.format("Couldn't save task file '%s'.", string), exception);
                }
            }
        }
        catch (Exception exception) {
            throw new Exception(L.t((String)"Failed to save project file - %s", (Object[])new Object[]{exception.getMessage()}), exception);
        }
    }

    /*
     * Enabled force condition propagation
     * Lifted jumps to return sites
     */
    public static void createProjectFile(File file, Element element, HashMap<String, Element> hashMap) throws Exception {
        SQFileManager.ensureDirExists(file.getAbsolutePath());
        try (ZipOutputStream zipOutputStream = new ZipOutputStream((OutputStream)new FileOutputStream(file), StandardCharsets.UTF_8);){
            byte[] byArray = null;
            try {
                zipOutputStream.putNextEntry(new ZipEntry(CONFIG_FILE));
                byArray = XMLUtil.elementToString((Element)element, (boolean)true).getBytes(StandardCharsets.UTF_8);
                zipOutputStream.write(byArray, 0, byArray.length);
            }
            catch (Exception exception) {
                throw new Exception(L.t((String)"Couldn't save config.xml file.", (Object[])new Object[0]), exception);
            }
            for (String string : hashMap.keySet()) {
                Element element2 = hashMap.get(string);
                try {
                    zipOutputStream.putNextEntry(new ZipEntry(string));
                    byArray = XMLUtil.elementToString((Element)element2, (boolean)true).getBytes(StandardCharsets.UTF_8);
                    zipOutputStream.write(byArray, 0, byArray.length);
                }
                catch (Exception exception) {
                    throw new Exception(L.t((String)"Couldn't save task file %s.", (Object[])new Object[]{string}), exception);
                    return;
                }
            }
        }
        catch (Exception exception) {
            throw new Exception(L.t((String)"Failed to save project file - %s", (Object[])new Object[]{exception.getMessage()}), exception);
        }
    }

    private static synchronized void updateZipContent(File file, String string, String string2) throws Exception {
        if (ZipFileSystemConfig == null) {
            ZipFileSystemConfig = new HashMap<String, String>();
            ZipFileSystemConfig.put("create", "true");
            ZipFileSystemConfig.put("compressionMethod", "DEFLATED");
        }
        String string3 = ("jar:file:/" + file.getAbsolutePath()).replace("\\", "/").replace("%", "%25").replace("//", "/").replace(" ", "%20").replace("[", "%5B").replace("]", "%5D");
        URI uRI = URI.create(string3);
        try (FileSystem fileSystem = FileSystems.newFileSystem(uRI, ZipFileSystemConfig);){
            Path path = fileSystem.getPath("/" + string, new String[0]);
            Files.writeString(path, (CharSequence)string2, new OpenOption[0]);
        }
        catch (Exception exception) {
            throw new Exception(L.t((String)"Failed to update zip content - '%s'", (Object[])new Object[]{string3}), exception);
        }
    }

    public static synchronized void updateZipContent(FileSystem fileSystem, String string, String string2, String string3) throws Exception {
        try {
            Path path = fileSystem.getPath("/" + string2, new String[0]);
            Files.writeString(path, (CharSequence)string3, new OpenOption[0]);
        }
        catch (Exception exception) {
            throw new Exception(L.t((String)"Failed to update zip content - '%s'", (Object[])new Object[]{string}), exception);
        }
    }

    public static FileSystem createFileSystem(File file) throws IOException {
        if (ZipFileSystemConfig == null) {
            ZipFileSystemConfig = new HashMap<String, String>();
            ZipFileSystemConfig.put("create", "true");
            ZipFileSystemConfig.put("compressionMethod", "DEFLATED");
        }
        String string = ("jar:file:/" + file.getAbsolutePath()).replace("\\", "/").replace("%", "%25").replace("//", "/").replace(" ", "%20").replace("[", "%5B").replace("]", "%5D");
        URI uRI = URI.create(string);
        FileSystem fileSystem = FileSystems.newFileSystem(uRI, ZipFileSystemConfig);
        return fileSystem;
    }

    public static File saveFile(String string, String string2, Element element) throws Exception {
        if (string.endsWith(CFX_SUFFIX)) {
            return SQFileManager.createZipFile(string, string2);
        }
        if (string.endsWith(SQB_SUFFIX)) {
            Element element2;
            if (element == null) {
                element = XMLUtil.stringToElement((String)string2);
            }
            if ((element2 = XMLUtil.findFirst((Element)element, (String)"Blocks")) == null) {
                throw new Exception(L.t((String)"Blocks element not found in XML config", (Object[])new Object[0]));
            }
            return SQFileManager.createZipFile(string, string2);
        }
        File file = SQUtils.createFile((String)string);
        if (string.endsWith(PLA_SUFFIX)) {
            string2 = StrategySaver.getPLAContent(SQUtils.stripExtension((String)file.getName()), string2);
        }
        SQUtils.stringToFile((File)file, (String)string2);
        return file;
    }

    public static String loadFile(String string) throws Exception {
        if (string.endsWith(CFX_SUFFIX)) {
            return SQFileManager.getZipContent(string, CONFIG_FILE);
        }
        if (string.endsWith(SQB_SUFFIX)) {
            Element element = XMLUtil.stringToElement((String)SQFileManager.getZipContent(string, null));
            Element element2 = XMLUtil.findFirst((Element)element, (String)"Blocks");
            if (element2 == null) {
                throw new Exception(L.t((String)"Blocks element not found in XML config", (Object[])new Object[0]));
            }
            return XMLUtil.elementToString((Element)element2);
        }
        return SQUtils.fileToString((String)string);
    }

    public static void xmlToCfx(File file, boolean bl) throws Exception {
        String string = SQUtils.fileToString((File)file);
        String string2 = file.getAbsolutePath().substring(0, file.getAbsolutePath().length() - 3) + CFX_SUFFIX;
        SQFileManager.saveFile(string2, string);
        if (bl) {
            file.delete();
        }
    }

    /*
     * WARNING - Removed try catching itself - possible behaviour change.
     */
    private static String getZipContent(String string, String string2) throws Exception {
        try (ZipInputStream zipInputStream = null;){
            Object object;
            zipInputStream = new ZipInputStream((InputStream)new FileInputStream(string), StandardCharsets.UTF_8);
            if (string2 != null) {
                while (zipInputStream.available() > 0 && !((ZipEntry)(object = zipInputStream.getNextEntry())).getName().equals(string2)) {
                }
            } else {
                zipInputStream.getNextEntry();
            }
            object = SQUtils.inputStreamToString((InputStream)zipInputStream);
            String string3 = SQFileManager.checkXml((String)object);
            return string3;
        }
    }

    /*
     * WARNING - Removed try catching itself - possible behaviour change.
     */
    private static File createZipFile(String string, String string2) throws Exception {
        File file = SQFileManager.ensureDirExists(string);
        string2 = SQFileManager.tryCorrectVersion(string2);
        try (ZipOutputStream zipOutputStream = null;){
            zipOutputStream = new ZipOutputStream((OutputStream)new FileOutputStream(file), StandardCharsets.UTF_8);
            ZipEntry zipEntry = new ZipEntry(CONFIG_FILE);
            zipOutputStream.putNextEntry(zipEntry);
            byte[] byArray = string2.getBytes(StandardCharsets.UTF_8);
            zipOutputStream.write(byArray, 0, byArray.length);
            zipOutputStream.closeEntry();
            File file2 = file;
            return file2;
        }
    }

    private static File ensureDirExists(String string) {
        File file = new File(string);
        if (!file.exists() && file.getParentFile() != null) {
            file.getParentFile().mkdirs();
        }
        return file;
    }

    public static String tryCorrectVersion(String string) {
        int n = string.indexOf(">");
        if (n < 0) {
            return string;
        }
        String string2 = " version=\"" + MainApp.getAppVersion() + "\"";
        String string3 = string.substring(0, n);
        int n2 = string3.indexOf(" version");
        string3 = n2 < 0 ? string3 + string2 : string3.replaceAll("\\s+(?:version)\\s*=\\s*\"[^\"]*\"", string2);
        return string3 + string.substring(n);
    }

    private static String checkXml(String string) {
        try {
            Element element = XMLUtil.stringToXmlElement((String)string);
            if (SQFileManager.checkXmlElement(element)) {
                string = XMLUtil.elementToString((Element)element);
            }
        }
        catch (Exception exception) {
            Log.error("Exc.", (Throwable)exception);
        }
        return string;
    }

    private static boolean checkXmlElement(Element element) {
        boolean bl = false;
        if (element.getAttributeValue("version") == null) {
            if (element.getName().equals("Project")) {
                List list = element.getChild("Tasks").getChildren("Task");
                for (int i = 0; i < list.size(); ++i) {
                    if (!SQFileManager.checkTask((Element)list.get(i))) continue;
                    bl = true;
                }
            } else if (element.getName().equals("Task")) {
                bl = SQFileManager.checkTask(element);
            }
        }
        return bl;
    }

    private static boolean checkTask(Element element) {
        boolean bl = false;
        Element element2 = element.getChild("Settings");
        try {
            if (SQFileManager.checkConditions(element2.getChild("Rankings").getChild("Conditions"))) {
                bl = true;
            }
        }
        catch (Exception exception) {
            // empty catch block
        }
        try {
            List list = element2.getChild("CrossChecks").getChildren();
            for (int i = 0; i < list.size(); ++i) {
                Element element3 = ((Element)list.get(i)).getChild("AcceptanceSettings").getChild("Conditions");
                if (!SQFileManager.checkConditions(element3)) continue;
                bl = true;
            }
        }
        catch (Exception exception) {
            // empty catch block
        }
        return bl;
    }

    private static boolean checkConditions(Element element) {
        boolean bl = false;
        List list = element.getChildren("Condition");
        for (int i = 0; i < list.size(); ++i) {
            try {
                if (SQFileManager.checkConditionColumnValue(((Element)list.get(i)).getChild("Left-Side").getChild("Column-Value"))) {
                    bl = true;
                }
            }
            catch (Exception exception) {
                // empty catch block
            }
            try {
                if (!SQFileManager.checkConditionColumnValue(((Element)list.get(i)).getChild("Right-Side").getChild("Column-Value"))) continue;
                bl = true;
                continue;
            }
            catch (Exception exception) {
                // empty catch block
            }
        }
        return bl;
    }

    private static boolean checkConditionColumnValue(Element element) {
        boolean bl = false;
        if (element.getAttributeValue("resultType").equals("RetestWithHigherPrecision") || element.getAttributeValue("resultType").equals("RetestOnAdditionalMarkets") || element.getAttributeValue("resultType").equals("WhatIf")) {
            element.setAttribute("direction", "0");
            element.setAttribute("sampleType", "127");
            element.setAttribute("plType", "10");
            bl = true;
        }
        return bl;
    }

    /*
     * WARNING - Removed try catching itself - possible behaviour change.
     */
    public static void updateTaskConfigurations(SQProject sQProject, HashMap<String, Element> hashMap) throws Exception {
        String string = sQProject.getProjectConfigFile().getAbsolutePath();
        try (FileSystem fileSystem = SQFileManager.createFileSystem(new File(string));){
            for (String string2 : hashMap.keySet()) {
                Element element = hashMap.get(string2);
                ISQTask iSQTask = sQProject.getTaskByXMLFile(string2);
                Element element2 = iSQTask.getConfig();
                element2.removeContent();
                for (Content content : element.getContent()) {
                    element2.addContent(content.clone());
                }
                SQFileManager.updateTaskConfig(fileSystem, string, string2, element);
            }
        }
        catch (Exception exception) {
            throw new Exception("Unable to update task configurations in the project file '" + string + "' - " + exception.getMessage(), exception);
        }
    }
}

