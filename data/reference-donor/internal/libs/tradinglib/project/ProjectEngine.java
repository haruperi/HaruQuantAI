/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  com.strategyquant.lib.L
 *  com.strategyquant.lib.SQUtils
 *  com.strategyquant.lib.constants.SQPaths
 *  com.strategyquant.pluginlib.SQPluginManager
 *  org.jdom2.Element
 *  org.json.JSONObject
 *  org.slf4j.Logger
 *  org.slf4j.LoggerFactory
 */
package com.strategyquant.tradinglib.project;

import com.strategyquant.lib.L;
import com.strategyquant.lib.SQUtils;
import com.strategyquant.lib.constants.SQPaths;
import com.strategyquant.pluginlib.SQPluginManager;
import com.strategyquant.tradinglib.file.SQFileManager;
import com.strategyquant.tradinglib.plugindef.app.IAppPlugin;
import com.strategyquant.tradinglib.project.SQProject;
import com.strategyquant.tradinglib.project.websocket.DataToSend;
import com.strategyquant.tradinglib.project.websocket.SQWebSocketManager;
import java.io.File;
import java.nio.file.CopyOption;
import java.nio.file.Files;
import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;
import java.util.concurrent.locks.ReentrantLock;
import org.jdom2.Element;
import org.json.JSONObject;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

public class ProjectEngine {
    private static final Logger Log = LoggerFactory.getLogger(ProjectEngine.class);
    private static ProjectEngine instance = null;
    private HashMap<String, SQProject> projects = new HashMap();
    private static ReentrantLock lock = new ReentrantLock();
    public static boolean loading = true;

    public static List<SQProject> list() {
        return new ArrayList<SQProject>(ProjectEngine.getInstance().projects.values());
    }

    public static List<SQProject> listCustomProjects() {
        ArrayList<SQProject> arrayList = new ArrayList<SQProject>();
        ArrayList<SQProject> arrayList2 = new ArrayList<SQProject>(ProjectEngine.getInstance().projects.values());
        for (int i = 0; i < arrayList2.size(); ++i) {
            SQProject sQProject = (SQProject)arrayList2.get(i);
            if (sQProject.isAppProject()) continue;
            arrayList.add(sQProject);
        }
        return arrayList;
    }

    public static synchronized ProjectEngine getInstance() {
        if (instance == null) {
            instance = new ProjectEngine();
            ProjectEngine.initTasks();
            loading = false;
        }
        return instance;
    }

    private ProjectEngine() {
        this.loadAvailableProjects();
    }

    private void loadAvailableProjects() {
        File file = new File(SQPaths.projectsDirPath);
        if (!file.exists()) {
            file.mkdirs();
        } else {
            for (File file2 : file.listFiles()) {
                if (!file2.isDirectory()) continue;
                this.loadProject(file2.getName());
            }
        }
        this.checkDefaultProjects();
    }

    private static void initTasks() {
        for (String string : ProjectEngine.instance.projects.keySet()) {
            try {
                ProjectEngine.instance.projects.get(string).initTasksFromConfig();
            }
            catch (Exception exception) {
                Log.error("Initialization of project '" + string + "' failed", (Throwable)exception);
            }
        }
    }

    private void checkDefaultProjects() {
        for (IAppPlugin iAppPlugin : SQPluginManager.getPlugins(IAppPlugin.class)) {
            String string = iAppPlugin.getProject();
            if (string == null || this.projects.containsKey(string)) continue;
            this.loadProject(string);
        }
    }

    private void loadProject(String string) {
        Log.debug("Loading project '" + string + "'.");
        try {
            SQProject sQProject = new SQProject(string);
            this.projects.put(string, sQProject);
        }
        catch (Exception exception) {
            Log.error("Cannot load project " + string + ". Exc.", (Throwable)exception);
        }
    }

    public static SQProject get(String string) throws Exception {
        SQProject sQProject = ProjectEngine.getInstance().projects.get(string);
        if (sQProject == null) {
            throw new Exception("Project '" + string + "' does not exist.");
        }
        return sQProject;
    }

    public static SQProject add(String string) throws Exception {
        string = ProjectEngine.generateProjectName(string);
        SQProject sQProject = new SQProject(string);
        ProjectEngine.getInstance().projects.put(string, sQProject);
        sQProject.initTasksFromConfig();
        return sQProject;
    }

    public static SQProject add(String string, File file, Element element, HashMap<String, Element> hashMap) throws Exception {
        string = ProjectEngine.generateProjectName(string);
        element.setAttribute("name", string);
        File file2 = new File(SQPaths.projectsDirPath + "/" + string + "/" + "project.cfx");
        SQUtils.ensureDirExists((String)file2.getParent());
        if (hashMap != null) {
            SQFileManager.createProjectFile(file2, element, hashMap);
        } else {
            Files.copy(file.toPath(), file2.toPath(), new CopyOption[0]);
            SQFileManager.updateProjectConfig(file2, element);
        }
        SQProject sQProject = new SQProject(string);
        ProjectEngine.getInstance().projects.put(string, sQProject);
        sQProject.initTasksFromConfig();
        return sQProject;
    }

    public static void remove(String string) throws Exception {
        SQProject sQProject = ProjectEngine.get(string);
        if (sQProject.isAppProject()) {
            throw new Exception(String.format("Predefined project %s cannot be removed.", string));
        }
        sQProject.getDatabanks().clear(false, String.format("Remove project %s", string));
        ProjectEngine.getInstance().projects.remove(string);
        SQUtils.deleteRecursive((File)new File(sQProject.getProjectFolder()));
    }

    public static void rename(String string, String string2) throws Exception {
        if (string.equals(string2)) {
            return;
        }
        if (ProjectEngine.projectExists(string2)) {
            throw new Exception(L.t((String)"Project with the same name already exists.", (Object[])new Object[0]));
        }
        SQProject sQProject = ProjectEngine.get(string);
        sQProject.setProjectName(string2);
        ProjectEngine.getInstance().projects.remove(string);
        ProjectEngine.getInstance().projects.put(string2, sQProject);
    }

    public static boolean projectExists(String string) {
        return ProjectEngine.getInstance().projects.containsKey(string);
    }

    public static String generateProjectName(String string) {
        String string2 = string;
        if (!ProjectEngine.projectExists(string2)) {
            return string2;
        }
        for (int i = 2; i < 1000 && ProjectEngine.projectExists(string2 = string + "(" + i + ")"); ++i) {
        }
        return string2;
    }

    public static boolean isDefaulProject(String string) {
        return string != null && (string.equals("Builder") || string.equals("Optimizer") || string.equals("Retester") || string.equals("PortfolioMaster"));
    }

    public static void loadStrategies() {
        Log.info("Loading strategies from files ...");
        for (SQProject sQProject : ProjectEngine.list()) {
            try {
                sQProject.getDatabanks().loadStrategies();
            }
            catch (Exception exception) {
                Log.error("Project '" + sQProject.getName() + "', loading strategies failed - " + exception.getMessage(), (Throwable)exception);
            }
        }
    }

    public static void stopAll() {
        for (SQProject sQProject : ProjectEngine.list()) {
            try {
                Log.debug("Stop running project '" + sQProject.getName() + "'.");
                sQProject.stop();
            }
            catch (Exception exception) {
                Log.error("Project '" + sQProject.getName() + "' - The project couldn't be stopped.");
            }
        }
    }

    public static boolean isInitialized() {
        return instance != null;
    }

    public static void projectFinished(String string) {
        try {
            Object object;
            JSONObject jSONObject = new JSONObject();
            jSONObject.put("productCode", (Object)SQWebSocketManager.getProductCode(string));
            if (!ProjectEngine.isDefaulProject(string)) {
                object = new ArrayList<SQProject>(ProjectEngine.getInstance().projects.values());
                for (int i = 0; i < object.size(); ++i) {
                    SQProject sQProject = (SQProject)object.get(i);
                    if (ProjectEngine.isDefaulProject(sQProject.getName()) || !sQProject.isRunning()) continue;
                    return;
                }
            }
            jSONObject.put("finished", true);
            object = new DataToSend("appStatusChanged", jSONObject);
            SQWebSocketManager.addToDataQueue((DataToSend)object, "SQUANT");
        }
        catch (Exception exception) {
            Log.error("Exc.", (Throwable)exception);
        }
    }
}

