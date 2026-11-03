/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  com.strategyquant.lib.L
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
package com.strategyquant.plugin.ProjectCondition.impl.CyclesCount;

import com.strategyquant.lib.L;
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
@Name(name="CyclesCount Condition plugin")
@Category(name="Project Condition")
@License(text="")
@ShortDesc(text="Short description")
@PluginImplementation
public class CyclesCountConditionPlugin
implements IProjectCondition {
    public static final Logger Log = LoggerFactory.getLogger((String)"CyclesCountConditionPlugin");
    private static final ProjectConditionField[] fields = new ProjectConditionField[]{new ProjectConditionField("comparator", "Comparator", "<"), new ProjectConditionField("number", "Value", "100")};
    private String comparator;
    private int value;
    private String lastCheckedValue = null;

    public String getName() {
        return "CyclesCount";
    }

    public String getTitle() {
        return L.tsq((String)"Number of cycles (Project)");
    }

    public String getDescription() {
        return String.format(this.getDescriptionFormat(), this.comparator, this.value);
    }

    public String getDescriptionFormat() {
        return L.t((String)"Number of cycles (Project) %s %d", (Object[])new Object[0]);
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
                case "number": {
                    this.value = Integer.parseInt(elField.getText());
                }
            }
        }
    }

    public boolean isMet(SQProject project, ISQTask task) throws Exception {
        int cycles = project.getRunCycles();
        this.lastCheckedValue = cycles + "";
        return Condition.validate((double)(cycles - this.value), (String)this.comparator);
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
        CyclesCountConditionPlugin newInstance = new CyclesCountConditionPlugin();
        newInstance.comparator = this.comparator;
        newInstance.value = this.value;
        return newInstance;
    }
}

