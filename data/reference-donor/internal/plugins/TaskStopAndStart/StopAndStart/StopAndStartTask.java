/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  com.strategyquant.lib.L
 *  com.strategyquant.pluginlib.annotations.Category
 *  com.strategyquant.pluginlib.annotations.License
 *  com.strategyquant.pluginlib.annotations.Name
 *  com.strategyquant.pluginlib.annotations.ShortDesc
 *  com.strategyquant.tradinglib.Databank
 *  com.strategyquant.tradinglib.project.IProjectCondition
 *  com.strategyquant.tradinglib.project.ProgressEngine
 *  com.strategyquant.tradinglib.project.ProjectEngine
 *  com.strategyquant.tradinglib.project.ProjectGlobalLog
 *  com.strategyquant.tradinglib.project.ProjectNameComparator
 *  com.strategyquant.tradinglib.project.SQProject
 *  com.strategyquant.tradinglib.taskImpl.AbstractTask
 *  com.strategyquant.tradinglib.taskImpl.ISQTask
 *  net.xeoh.plugins.base.annotations.PluginImplementation
 *  net.xeoh.plugins.base.annotations.meta.Author
 */
package com.strategyquant.plugin.Task.impl.StopAndStart;

import com.strategyquant.lib.L;
import com.strategyquant.pluginlib.annotations.Category;
import com.strategyquant.pluginlib.annotations.License;
import com.strategyquant.pluginlib.annotations.Name;
import com.strategyquant.pluginlib.annotations.ShortDesc;
import com.strategyquant.tradinglib.Databank;
import com.strategyquant.tradinglib.project.IProjectCondition;
import com.strategyquant.tradinglib.project.ProgressEngine;
import com.strategyquant.tradinglib.project.ProjectEngine;
import com.strategyquant.tradinglib.project.ProjectGlobalLog;
import com.strategyquant.tradinglib.project.ProjectNameComparator;
import com.strategyquant.tradinglib.project.SQProject;
import com.strategyquant.tradinglib.taskImpl.AbstractTask;
import com.strategyquant.tradinglib.taskImpl.ISQTask;
import java.util.ArrayList;
import java.util.List;
import net.xeoh.plugins.base.annotations.PluginImplementation;
import net.xeoh.plugins.base.annotations.meta.Author;

@Author(name="Tomas Brynda")
@Name(name="Stop & Start task plugin")
@Category(name="Task")
@License(text="")
@ShortDesc(text="Short description")
@PluginImplementation
public class StopAndStartTask
extends AbstractTask {
    private ArrayList<IProjectCondition> conditions;
    private boolean skipToFirstProject = false;
    private String logMessage;
    private ProjectNameComparator projectNameComparator = new ProjectNameComparator();

    public StopAndStartTask() throws Exception {
        super(null, null);
    }

    public StopAndStartTask(String projectName, ProgressEngine progressEngine) throws Exception {
        super(projectName, progressEngine);
    }

    public String getType() {
        return "StopAndStart";
    }

    public String getName() {
        return L.tsq((String)"Stop & Start");
    }

    public ISQTask clone(String projectName, ProgressEngine progressEngine) throws Exception {
        StopAndStartTask task = new StopAndStartTask(projectName, progressEngine);
        task.settingTabPlugins = this.settingTabPlugins;
        return task;
    }

    public void start() throws Exception {
        this.project = ProjectEngine.get((String)this.projectName);
        this.progressEngine.setLogPrefix(this.taskLogPrefix);
        this.progressEngine.printToLog(L.t((String)"Starting Stop & Start evaluation...", (Object[])new Object[0]));
        this.progressEngine.start();
        this.conditions = (ArrayList)this.settingsData.getParams().get("ProjectConditions");
        this.skipToFirstProject = (Boolean)this.settingsData.getParams().get("SkipToFirstProject");
        this.logMessage = null;
        boolean conditionsMet = true;
        for (int a = 0; a < this.conditions.size(); ++a) {
            IProjectCondition condition = this.conditions.get(a);
            if (condition.isMet(this.project, (ISQTask)this)) continue;
            conditionsMet = false;
            this.logMessage = L.t((String)"Condition '%s' (%s) not met", (Object[])new Object[]{condition.getDescription(), condition.getLastCheckedValue()});
            this.progressEngine.printToLog(this.logMessage);
            break;
        }
        if (conditionsMet) {
            this.logMessage = L.t((String)"All conditions met, stopping project...", (Object[])new Object[0]);
            this.progressEngine.printToLog(this.logMessage);
            this.progressEngine.stop();
            String projectToStart = (String)this.settingsData.getParams().get("ProjectToStart");
            if (projectToStart != null) {
                try {
                    if (projectToStart.equals("next-project")) {
                        projectToStart = this.getNextProjectName();
                    }
                    if (projectToStart != null) {
                        String message = L.t((String)"Starting project '%s'...", (Object[])new Object[]{projectToStart});
                        this.logMessage = this.logMessage + "\n" + message;
                        this.progressEngine.printToLog(message);
                        SQProject nextProject = ProjectEngine.get((String)projectToStart);
                        nextProject.setRunSpecification(0);
                        nextProject.initTasksFromConfig();
                        nextProject.beforeStart();
                        nextProject.start();
                    }
                }
                catch (Exception e) {
                    String message = L.t((String)"Cannot start project '%s'", (Object[])new Object[]{e.getMessage()});
                    this.logMessage = this.logMessage + "\n" + message;
                    this.progressEngine.printToLog(message);
                }
            }
        } else {
            this.progressEngine.finish();
        }
    }

    private String getNextProjectName() {
        String nextProjectName = null;
        List projects = ProjectEngine.listCustomProjects();
        projects.sort(this.projectNameComparator);
        for (int i = 0; i < projects.size(); ++i) {
            SQProject project = (SQProject)projects.get(i);
            if (!project.getName().equals(this.projectName)) continue;
            if (i < projects.size() - 1) {
                nextProjectName = ((SQProject)projects.get(i + 1)).getName();
                break;
            }
            if (!this.skipToFirstProject) break;
            nextProjectName = ((SQProject)projects.get(0)).getName();
            break;
        }
        return nextProjectName;
    }

    protected int getRunningStatus() {
        return 0;
    }

    public String getPluginFolderName() {
        return "TaskStopAndStart";
    }

    public int getPreferredPosition() {
        return 3;
    }

    public String[] getSettings() {
        return new String[]{"StopAndStart"};
    }

    protected Databank[] getUsedDatabanks() {
        return null;
    }

    protected Databank getOutputDatabank() {
        return null;
    }

    public void logTaskFinished(ProjectGlobalLog log) {
        super.logTaskFinished(log);
        log.print(this.logMessage);
    }
}

