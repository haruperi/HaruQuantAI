/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  com.strategyquant.pluginlib.ISQPlugin
 *  org.jdom2.Element
 */
package com.strategyquant.tradinglib.project;

import com.strategyquant.pluginlib.ISQPlugin;
import com.strategyquant.tradinglib.project.ProjectConditionField;
import com.strategyquant.tradinglib.project.SQProject;
import com.strategyquant.tradinglib.taskImpl.ISQTask;
import org.jdom2.Element;

public interface IProjectCondition
extends ISQPlugin {
    public String getName();

    public String getTitle();

    public ProjectConditionField[] getFields();

    public void readSettings(Element var1) throws Exception;

    public boolean isMet(SQProject var1, ISQTask var2) throws Exception;

    public IProjectCondition clone();

    public String getDescription();

    public String getDescriptionFormat();

    public String getLastCheckedValue();
}

