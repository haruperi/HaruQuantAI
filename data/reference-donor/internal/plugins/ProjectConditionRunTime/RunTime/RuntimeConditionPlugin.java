/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  com.strategyquant.lib.L
 *  com.strategyquant.lib.SQTime
 *  com.strategyquant.pluginlib.annotations.Category
 *  com.strategyquant.pluginlib.annotations.License
 *  com.strategyquant.pluginlib.annotations.Name
 *  com.strategyquant.pluginlib.annotations.ShortDesc
 *  com.strategyquant.tradinglib.conditions.Condition
 *  com.strategyquant.tradinglib.project.IProjectCondition
 *  com.strategyquant.tradinglib.project.ProjectConditionField
 *  com.strategyquant.tradinglib.project.SQProject
 *  com.strategyquant.tradinglib.taskImpl.ISQTask
 *  net.xeoh.plugins.base.annotations.PluginImplementation
 *  net.xeoh.plugins.base.annotations.meta.Author
 *  org.jdom2.Element
 *  org.slf4j.Logger
 *  org.slf4j.LoggerFactory
 */
package com.strategyquant.plugin.ProjectCondition.impl.RunTime;

import com.strategyquant.lib.L;
import com.strategyquant.lib.SQTime;
import com.strategyquant.pluginlib.annotations.Category;
import com.strategyquant.pluginlib.annotations.License;
import com.strategyquant.pluginlib.annotations.Name;
import com.strategyquant.pluginlib.annotations.ShortDesc;
import com.strategyquant.tradinglib.conditions.Condition;
import com.strategyquant.tradinglib.project.IProjectCondition;
import com.strategyquant.tradinglib.project.ProjectConditionField;
import com.strategyquant.tradinglib.project.SQProject;
import com.strategyquant.tradinglib.taskImpl.ISQTask;
import java.util.List;
import net.xeoh.plugins.base.annotations.PluginImplementation;
import net.xeoh.plugins.base.annotations.meta.Author;
import org.jdom2.Element;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

@Author(name="Tomas Brynda")
@Name(name="RunTime Condition plugin")
@Category(name="Project Condition")
@License(text="")
@ShortDesc(text="Short description")
@PluginImplementation
public class RuntimeConditionPlugin
implements IProjectCondition {
    public static final Logger Log = LoggerFactory.getLogger((String)"DurationConditionPlugin");
    private static final ProjectConditionField[] fields = new ProjectConditionField[]{new ProjectConditionField("comparator", "Comparator", "<"), new ProjectConditionField("duration", "Run time", "120")};
    private String comparator;
    private long minutes;
    private String lastCheckedValue = null;

    public String getName() {
        return "RunTime";
    }

    public String getTitle() {
        return L.tsq((String)"Project run time");
    }

    public String getDescription() {
        return String.format(this.getDescriptionFormat(), this.comparator, SQTime.formatDateTime((long)(this.minutes * 60L)));
    }

    public String getDescriptionFormat() {
        return L.t((String)"Project run time %s %s", (Object[])new Object[0]);
    }

    public String getLastCheckedValue() {
        return this.lastCheckedValue;
    }

    public ProjectConditionField[] getFields() {
        return fields;
    }

    public void readSettings(Element elSettings) throws Exception {
        List fieldElems = elSettings.getChildren("Field");
        block8: for (int a = 0; a < fieldElems.size(); ++a) {
            Element elField = (Element)fieldElems.get(a);
            String type = elField.getAttributeValue("type");
            if (type == null) continue;
            switch (type) {
                case "comparator": {
                    this.comparator = elField.getText();
                    continue block8;
                }
                case "duration": {
                    this.minutes = Integer.parseInt(elField.getText());
                }
            }
        }
    }

    public boolean isMet(SQProject project, ISQTask task) throws Exception {
        long runTimeMs = project.getProjectRunningTime();
        long intervalMs = this.minutes * 60000L;
        this.lastCheckedValue = SQTime.formatDateTime((long)(runTimeMs / 1000L));
        return Condition.validate((double)(runTimeMs - intervalMs), (String)this.comparator);
    }

    public String getProduct() {
        return "SQUANT";
    }

    public int getPreferredPosition() {
        return 0;
    }

    public void initPlugin() throws Exception {
    }

    public IProjectCondition clone() {
        RuntimeConditionPlugin newInstance = new RuntimeConditionPlugin();
        newInstance.comparator = this.comparator;
        newInstance.minutes = this.minutes;
        return newInstance;
    }
}

