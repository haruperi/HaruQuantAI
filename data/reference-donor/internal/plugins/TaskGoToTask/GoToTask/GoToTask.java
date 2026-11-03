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
 *  com.strategyquant.tradinglib.project.GoToTaskException
 *  com.strategyquant.tradinglib.project.IProjectCondition
 *  com.strategyquant.tradinglib.project.ProgressEngine
 *  com.strategyquant.tradinglib.project.ProjectEngine
 *  com.strategyquant.tradinglib.project.ProjectGlobalLog
 *  com.strategyquant.tradinglib.taskImpl.AbstractTask
 *  com.strategyquant.tradinglib.taskImpl.ISQTask
 *  net.xeoh.plugins.base.annotations.PluginImplementation
 *  net.xeoh.plugins.base.annotations.meta.Author
 */
package com.strategyquant.plugin.Task.impl.GoToTask;

import com.strategyquant.lib.L;
import com.strategyquant.pluginlib.annotations.Category;
import com.strategyquant.pluginlib.annotations.License;
import com.strategyquant.pluginlib.annotations.Name;
import com.strategyquant.pluginlib.annotations.ShortDesc;
import com.strategyquant.tradinglib.Databank;
import com.strategyquant.tradinglib.project.GoToTaskException;
import com.strategyquant.tradinglib.project.IProjectCondition;
import com.strategyquant.tradinglib.project.ProgressEngine;
import com.strategyquant.tradinglib.project.ProjectEngine;
import com.strategyquant.tradinglib.project.ProjectGlobalLog;
import com.strategyquant.tradinglib.taskImpl.AbstractTask;
import com.strategyquant.tradinglib.taskImpl.ISQTask;
import java.util.ArrayList;
import net.xeoh.plugins.base.annotations.PluginImplementation;
import net.xeoh.plugins.base.annotations.meta.Author;

@Author(name="Tamas Takacs")
@Name(name="Go To Task plugin")
@Category(name="Task")
@License(text="")
@ShortDesc(text="Short description")
@PluginImplementation
public class GoToTask
extends AbstractTask {
    private String targetTaskName;
    private boolean resetEvaluatedCycles;
    private boolean resetActivatedCycles;
    private ArrayList<IProjectCondition> conditions;
    private String logMessage;
    private int evaluatedCycles;
    private int activatedCycles;

    public GoToTask() throws Exception {
        super(null, null);
    }

    public GoToTask(String projectName, ProgressEngine progressEngine) throws Exception {
        super(projectName, progressEngine);
        this.evaluatedCycles = 0;
        this.activatedCycles = 0;
    }

    public void start() throws Exception {
        this.targetTaskName = (String)this.settingsData.getParams().get("GoToTaskName");
        this.resetEvaluatedCycles = (Boolean)this.settingsData.getParams().get("GoToTaskResetEvaluatedCycles");
        this.resetActivatedCycles = (Boolean)this.settingsData.getParams().get("GoToTaskResetActivatedCycles");
        this.conditions = (ArrayList)this.settingsData.getParams().get("ProjectConditions");
        this.project = ProjectEngine.get((String)this.projectName);
        this.progressEngine.setLogPrefix(this.taskLogPrefix);
        this.logMessage = "";
        if (this.targetTaskName.trim().isEmpty()) {
            return;
        }
        ++this.evaluatedCycles;
        boolean conditionsMet = true;
        for (int a = 0; a < this.conditions.size(); ++a) {
            IProjectCondition condition = this.conditions.get(a);
            boolean metResult = condition.isMet(this.project, (ISQTask)this);
            this.logMessage = this.logMessage + "- " + L.t((String)"Condition '%s' (%s) - %s.", (Object[])new Object[]{condition.getDescription(), condition.getLastCheckedValue(), metResult ? L.t((String)"passed", (Object[])new Object[0]) : L.t((String)"failed", (Object[])new Object[0])}) + "\n";
            if (metResult) continue;
            conditionsMet = false;
            this.logMessage = this.logMessage + "  - " + L.t((String)"Condition '%s' (%s) failed, going to following task.", (Object[])new Object[]{condition.getDescription(), condition.getLastCheckedValue()});
            this.progressEngine.printToLog(this.logMessage);
            break;
        }
        if (!conditionsMet) {
            if (this.taskIndex < this.project.getTasksCount()) {
                ISQTask nextTask = this.project.getTask(this.taskIndex);
                String string = this.targetTaskName = nextTask == null ? "lastTaskBreakcmd" : nextTask.getCustomName();
                if (this.resetActivatedCycles) {
                    this.logMessage = this.logMessage + "- " + L.t((String)"Number of ACTIVATED cycles has been reset.\n", (Object[])new Object[0]);
                    this.activatedCycles = 0;
                }
                if (nextTask == null) {
                    this.progressEngine.setRunningStatus(4);
                }
                this.logTaskFinished(this.project.getGlobalLog());
                throw new GoToTaskException(this.targetTaskName);
            }
            this.progressEngine.setRunningStatus(4);
            this.logTaskFinished(this.project.getGlobalLog());
            throw new GoToTaskException("lastTaskBreakcmd");
        }
        if (conditionsMet) {
            ++this.activatedCycles;
            ISQTask task = this.project.getTaskByName(this.targetTaskName);
            int targetTaskIndex = task == null ? 0 : task.getIndex();
            String taskTitle = task == null ? this.targetTaskName : task.getTitle();
            this.logMessage = this.logMessage + L.t((String)"- %s. Skipping to task #%d %s\n", (Object[])new Object[]{this.conditions.isEmpty() ? L.t((String)"No conditions", (Object[])new Object[0]) : L.t((String)"All conditions passed", (Object[])new Object[0]), targetTaskIndex, taskTitle});
            if (this.resetEvaluatedCycles) {
                this.logMessage = this.logMessage + "- " + L.t((String)"Number of EVALUATED cycles has been reset.\n", (Object[])new Object[0]);
                this.evaluatedCycles = 0;
            }
            this.progressEngine.printToLog(this.logMessage);
            this.logTaskFinished(this.project.getGlobalLog());
            throw new GoToTaskException(this.targetTaskName);
        }
    }

    protected int getRunningStatus() {
        return 0;
    }

    public String getPluginFolderName() {
        return "TaskGoToTask";
    }

    public int getPreferredPosition() {
        return 4;
    }

    public String getType() {
        return "GoToTask";
    }

    public String getName() {
        return L.tsq((String)"Go To Task");
    }

    public ISQTask clone(String projectName, ProgressEngine progressEngine) throws Exception {
        GoToTask task = new GoToTask(projectName, progressEngine);
        task.settingTabPlugins = this.settingTabPlugins;
        return task;
    }

    public String[] getSettings() {
        return new String[]{"GoToTask"};
    }

    protected Databank[] getUsedDatabanks() {
        return null;
    }

    protected Databank getOutputDatabank() {
        return null;
    }

    public void logTaskFinished(ProjectGlobalLog log) {
        log.print(this.logMessage);
        super.logTaskFinished(log);
    }

    public double getCustomValue(String key) {
        if (key.equals("evaluatedCycles")) {
            return this.evaluatedCycles;
        }
        if (key.equals("activatedCycles")) {
            return this.activatedCycles;
        }
        return 0.0;
    }
}

