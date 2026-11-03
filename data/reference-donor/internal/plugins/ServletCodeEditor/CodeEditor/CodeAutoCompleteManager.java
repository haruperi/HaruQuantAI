/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  com.strategyquant.lib.SQUtils
 *  com.strategyquant.lib.app.MainApp
 *  com.strategyquant.lib.classInfo.ClassHelper
 *  com.strategyquant.lib.classInfo.ClazzInfo
 *  com.strategyquant.lib.classInfo.CodeInfo
 *  com.strategyquant.lib.utils.JsonCreator
 *  org.slf4j.Logger
 *  org.slf4j.LoggerFactory
 */
package com.strategyquant.plugin.Servlet.impl.CodeEditor;

import com.strategyquant.lib.SQUtils;
import com.strategyquant.lib.app.MainApp;
import com.strategyquant.lib.classInfo.ClassHelper;
import com.strategyquant.lib.classInfo.ClazzInfo;
import com.strategyquant.lib.classInfo.CodeInfo;
import com.strategyquant.lib.utils.JsonCreator;
import java.io.File;
import java.io.IOException;
import java.net.URL;
import java.net.URLClassLoader;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.OpenOption;
import java.util.ArrayList;
import java.util.Enumeration;
import java.util.HashSet;
import java.util.LinkedList;
import java.util.jar.JarEntry;
import java.util.jar.JarFile;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

public class CodeAutoCompleteManager {
    private static final Logger Log = LoggerFactory.getLogger(CodeAutoCompleteManager.class);

    public String getData() throws IOException, ClassNotFoundException {
        String autocompleteData = this.getSqAutoCompleteData();
        String customJarCompleteData = this.getCustomJarsCompleteData();
        String javaDocs = this.getJavaDocs();
        JsonCreator jc = new JsonCreator();
        jc.beginObject();
        jc.put("success", (Object)"Code types listed.", true);
        jc.putBeginObject("data");
        jc.putRaw("autocompleteData", (Object)autocompleteData, true);
        jc.putRaw("customJarsAutoCompleteData", (Object)customJarCompleteData, true);
        jc.putRaw("javaDocs", (Object)javaDocs, false);
        jc.endObject(false);
        jc.endObject(false);
        String result = jc.toJson();
        Log.debug(javaDocs);
        return result;
    }

    private File[] getCustomJarFiles() {
        File folder = new File(MainApp.getDataPath(), "user" + File.separator + "libs");
        return folder.listFiles((arg0, arg1) -> {
            File file = new File(arg0, arg1);
            return file.isFile() && arg1.endsWith(".jar");
        });
    }

    private File getCustomJarCacheFile(File f) {
        File cachedFile = new File(MainApp.getDataPath() + "/internal/autocomplete", "cache_custom_" + f.getName().replace(".jar", ".json"));
        return cachedFile;
    }

    private String getCachedCustomJarData(File cachedFile) {
        String json = null;
        if (cachedFile.exists()) {
            try {
                byte[] encoded = Files.readAllBytes(cachedFile.toPath());
                json = new String(encoded, StandardCharsets.UTF_8);
            }
            catch (Exception e) {
                Log.error("Error while loading cache.json file", (Throwable)e);
            }
        }
        return json;
    }

    private CodeInfo performLoadCustomJarInfo(File file) throws IOException {
        CodeInfo codeInfo = new CodeInfo();
        codeInfo.setImports(new HashSet());
        codeInfo.setClasses(new LinkedList());
        JarFile jarFile = new JarFile(file);
        Enumeration<JarEntry> e = jarFile.entries();
        URL[] urls = new URL[]{new URL("jar:" + SQUtils.toFileUrl((String)file.getAbsolutePath()) + "!/")};
        URLClassLoader cl = URLClassLoader.newInstance(urls);
        while (e.hasMoreElements()) {
            JarEntry je = e.nextElement();
            if (je.isDirectory() || !je.getName().endsWith(".class")) continue;
            Log.debug(String.format("Analysing class: %s", je.getName()));
            String className = je.getName().substring(0, je.getName().length() - 6);
            className = className.replace('/', '.');
            try {
                Class<?> c = cl.loadClass(className);
                ClazzInfo info = ClassHelper.getClazzInfo(c);
                if (info == null) continue;
                codeInfo.getClasses().add(info);
                codeInfo.getImports().add(c.getPackage().getName());
            }
            catch (Throwable e1) {
                Log.error("Error while analyzing class", e1);
            }
        }
        return codeInfo;
    }

    private String getCustomJarsCompleteData() throws IOException {
        File[] files = this.getCustomJarFiles();
        JsonCreator jc = new JsonCreator();
        jc.beginObject();
        if (files != null) {
            for (int i = 0; i < files.length; ++i) {
                File file = files[i];
                Log.debug(String.format("Analysing jar: %s", file.getName()));
                File cachedFile = this.getCustomJarCacheFile(file);
                String json = this.getCachedCustomJarData(cachedFile);
                if (json == null) {
                    json = this.performLoadCustomJarInfo(file).toJSON();
                    Files.write(cachedFile.toPath(), json.getBytes(), new OpenOption[0]);
                }
                jc.putRaw(file.getName(), (Object)json, i < files.length - 1);
            }
        }
        jc.endObject(false);
        return jc.toJson();
    }

    private String getSqAutoCompleteData() throws ClassNotFoundException, IOException {
        File cachedFile = new File(MainApp.getDataPath() + "/internal/autocomplete", "cache_v2.json");
        String json = null;
        if (cachedFile.exists()) {
            try {
                byte[] encoded = Files.readAllBytes(cachedFile.toPath());
                json = new String(encoded, StandardCharsets.UTF_8);
            }
            catch (Exception e) {
                Log.error("Error while loading cache.json file", (Throwable)e);
            }
        }
        if (json == null) {
            File packageFile = new File(MainApp.getDataPath() + "/internal/autocomplete", "packages.txt");
            ArrayList<String> packages = new ArrayList<String>();
            if (packageFile.exists()) {
                packages.addAll(Files.readAllLines(packageFile.toPath()));
            } else {
                Log.warn("Autocomplete package list not found: " + packageFile.getAbsolutePath());
            }
            packages.removeIf(s -> s.trim().isEmpty());
            json = ClassHelper.getClassesJson((String[])packages.toArray(new String[0]));
            cachedFile.getParentFile().mkdirs();
            Files.write(cachedFile.toPath(), json.getBytes(), new OpenOption[0]);
        }
        return json;
    }

    private String getJavaDocs() {
        File javadocsFile = new File(MainApp.getDataPath() + "/internal/autocomplete", "docs.json");
        String javaDocs = null;
        if (javadocsFile.exists()) {
            try {
                byte[] encoded = Files.readAllBytes(javadocsFile.toPath());
                javaDocs = new String(encoded, StandardCharsets.UTF_8).replaceAll("\\s+", " ").replaceAll("\\{@code\\s(.*?)\\}", "**$1**").replace("\\n ", "\\n");
            }
            catch (Exception e) {
                Log.error("Error while loading docs.json file", (Throwable)e);
            }
        }
        if (javaDocs == null) {
            javaDocs = "{}";
        }
        return javaDocs;
    }
}

