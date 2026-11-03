/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  com.strategyquant.lib.L
 *  com.strategyquant.lib.SQUtils
 *  com.strategyquant.lib.XMLUtil
 *  com.strategyquant.lib.snippets.compile.SQStructure
 *  com.strategyquant.lib.sqxbusiness.MQLMarketConst
 *  org.jdom2.Element
 *  org.slf4j.Logger
 *  org.slf4j.LoggerFactory
 */
package com.strategyquant.plugin.App.impl.SQXBusiness;

import com.strategyquant.lib.L;
import com.strategyquant.lib.SQUtils;
import com.strategyquant.lib.XMLUtil;
import com.strategyquant.lib.snippets.compile.SQStructure;
import com.strategyquant.lib.sqxbusiness.MQLMarketConst;
import java.io.File;
import java.util.LinkedHashMap;
import org.jdom2.Element;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

public class MQLMarketProjects {
    public static final Logger Log = LoggerFactory.getLogger(MQLMarketProjects.class);
    private static final String sampleProjectPath = SQStructure.INTERNAL_DIR_PATH + "web/SQXBUSINESS/Sample Project";
    private static MQLMarketProjects instance;
    private LinkedHashMap<String, Element> projects;

    private MQLMarketProjects() {
        this.loadProjects();
    }

    private static MQLMarketProjects get() {
        if (instance == null) {
            instance = new MQLMarketProjects();
        }
        return instance;
    }

    public static LinkedHashMap<String, Element> list() {
        return MQLMarketProjects.get().projects;
    }

    public static void add(String name, Element config) throws Exception {
        File projectDir = new File(MQLMarketConst.getProjectDirPath((String)name));
        if (projectDir.exists()) {
            throw new Exception(L.t((String)"Cannot create project with name '%s' - Folder already exists", (Object[])new Object[]{name}));
        }
        projectDir.mkdirs();
        SQUtils.stringToFile((String)(projectDir + "/" + "config.xml"), (String)XMLUtil.elementToString((Element)config));
        MQLMarketProjects.get().projects.put(name, config);
    }

    public static void update(String name, Element config, String oldName) throws Exception {
        File projectDir = new File(MQLMarketConst.getProjectDirPath((String)name));
        if (oldName != null) {
            if (projectDir.exists()) {
                throw new Exception(L.t((String)"Cannot rename project - Folder '%s' already exists", (Object[])new Object[]{name}));
            }
            File oldProjectDir = new File(MQLMarketConst.getProjectDirPath((String)oldName));
            if (!oldProjectDir.exists()) {
                throw new Exception(L.t((String)"Cannot rename project - Folder '%s' doesn't exist", (Object[])new Object[]{oldName}));
            }
            oldProjectDir.renameTo(projectDir);
        }
        SQUtils.stringToFile((String)(projectDir + "/" + "config.xml"), (String)XMLUtil.elementToString((Element)config));
        MQLMarketProjects.get().projects.put(name, config);
    }

    public static void remove(String name) {
        SQUtils.deleteDirectory((String)MQLMarketConst.getProjectDirPath((String)name));
        MQLMarketProjects.get().projects.remove(name);
    }

    private void loadProjects() {
        try {
            File projectsDir;
            this.projects = new LinkedHashMap();
            File sampleProjectDir = new File(sampleProjectPath);
            if (sampleProjectDir.exists()) {
                try {
                    String projectName = sampleProjectDir.getName();
                    File configFile = new File(sampleProjectDir.getAbsolutePath() + "/" + "config.xml");
                    Element projectConfig = XMLUtil.fileToXmlElement((File)configFile);
                    projectConfig.setAttribute("sample", "true");
                    this.projects.put(projectName, projectConfig);
                }
                catch (Exception e) {
                    Log.error("Cannot load SQX Business sample project", (Throwable)e);
                }
            }
            if ((projectsDir = new File(MQLMarketConst.projectsPath)).exists()) {
                File[] subFolders = projectsDir.listFiles();
                for (int a = 0; a < subFolders.length; ++a) {
                    File configFile;
                    File subFolder = subFolders[a];
                    if (!subFolder.isDirectory() || !(configFile = new File(subFolder.getAbsolutePath() + "/" + "config.xml")).exists()) continue;
                    try {
                        String projectName = subFolder.getName();
                        Element projectConfig = XMLUtil.fileToXmlElement((File)configFile);
                        this.projects.put(projectName, projectConfig);
                        continue;
                    }
                    catch (Exception e) {
                        Log.error("Cannot load SQX Business project '" + subFolder.getName() + "'", (Throwable)e);
                    }
                }
            }
        }
        catch (Exception e) {
            Log.error("Loading SQX Business projects failed", (Throwable)e);
        }
    }
}

