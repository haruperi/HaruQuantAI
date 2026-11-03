/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  com.strategyquant.pluginlib.annotations.Category
 *  com.strategyquant.pluginlib.annotations.License
 *  com.strategyquant.pluginlib.annotations.Name
 *  com.strategyquant.pluginlib.annotations.ShortDesc
 *  com.strategyquant.tradinglib.plugindef.app.IAppPlugin
 *  net.xeoh.plugins.base.annotations.PluginImplementation
 *  net.xeoh.plugins.base.annotations.meta.Author
 *  org.slf4j.Logger
 *  org.slf4j.LoggerFactory
 */
package com.strategyquant.plugin.App.impl.TaskManager;

import com.strategyquant.plugin.App.impl.TaskManager.TaskManagerProgressPublisher;
import com.strategyquant.pluginlib.annotations.Category;
import com.strategyquant.pluginlib.annotations.License;
import com.strategyquant.pluginlib.annotations.Name;
import com.strategyquant.pluginlib.annotations.ShortDesc;
import com.strategyquant.tradinglib.plugindef.app.IAppPlugin;
import net.xeoh.plugins.base.annotations.PluginImplementation;
import net.xeoh.plugins.base.annotations.meta.Author;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

@Author(name="Tamas Takacs")
@Name(name="Project Manager")
@Category(name="App")
@License(text="")
@ShortDesc(text="Short description")
@PluginImplementation
public class TaskManagerAppPlugin
implements IAppPlugin {
    public static final Logger Log = LoggerFactory.getLogger(TaskManagerAppPlugin.class);

    public String getName() {
        return "Project Manager";
    }

    public String getProduct() {
        return "SQUANT";
    }

    public int getPreferredPosition() {
        return 0;
    }

    public void initPlugin() throws Exception {
        new TaskManagerProgressPublisher();
    }

    public String getContextPath() {
        return "/taskmanager";
    }

    public String getAppCode() {
        return "TASKMANAGER";
    }

    public String getTooltip() {
        return "Project Manager";
    }

    public String getProject() {
        return null;
    }

    public String getDefaultTaskType() {
        return null;
    }

    public String getDefaultTaskName() {
        return null;
    }
}

