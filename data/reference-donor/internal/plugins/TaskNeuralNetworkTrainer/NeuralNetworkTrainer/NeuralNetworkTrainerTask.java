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
 *  com.strategyquant.tradinglib.project.ProgressEngine
 *  com.strategyquant.tradinglib.taskImpl.AbstractTask
 *  com.strategyquant.tradinglib.taskImpl.ISQTask
 *  net.xeoh.plugins.base.annotations.PluginImplementation
 *  net.xeoh.plugins.base.annotations.meta.Author
 */
package com.strategyquant.plugin.Task.impl.NeuralNetworkTrainer;

import com.strategyquant.lib.L;
import com.strategyquant.pluginlib.annotations.Category;
import com.strategyquant.pluginlib.annotations.License;
import com.strategyquant.pluginlib.annotations.Name;
import com.strategyquant.pluginlib.annotations.ShortDesc;
import com.strategyquant.tradinglib.Databank;
import com.strategyquant.tradinglib.project.ProgressEngine;
import com.strategyquant.tradinglib.taskImpl.AbstractTask;
import com.strategyquant.tradinglib.taskImpl.ISQTask;
import net.xeoh.plugins.base.annotations.PluginImplementation;
import net.xeoh.plugins.base.annotations.meta.Author;

@Author(name="Tamas Takacs")
@Name(name="Neural network trainer plugin")
@Category(name="Task")
@License(text="")
@ShortDesc(text="Short description")
@PluginImplementation
public class NeuralNetworkTrainerTask
extends AbstractTask {
    public NeuralNetworkTrainerTask() throws Exception {
        super(null, null);
    }

    public NeuralNetworkTrainerTask(String projectName, ProgressEngine progressEngine) throws Exception {
        super(projectName, progressEngine);
    }

    public String getType() {
        return "NeuralNetworkTrainer";
    }

    public String getName() {
        return L.tsq((String)"Neural Network Trainer");
    }

    public ISQTask clone(String projectName, ProgressEngine progressEngine) throws Exception {
        NeuralNetworkTrainerTask task = new NeuralNetworkTrainerTask(projectName, progressEngine);
        task.settingTabPlugins = this.settingTabPlugins;
        return task;
    }

    public void start() throws Exception {
    }

    protected int getRunningStatus() {
        return 0;
    }

    public String getPluginFolderName() {
        return "TaskNeuralNetworkTrainer";
    }

    public int getPreferredPosition() {
        return 5;
    }

    public String[] getSettings() {
        return new String[]{"Data", "Options", "Rankings", "Notes"};
    }

    protected Databank[] getUsedDatabanks() {
        return null;
    }

    protected Databank getOutputDatabank() {
        return null;
    }

    public String getProduct() {
        return "SQUANT";
    }
}

