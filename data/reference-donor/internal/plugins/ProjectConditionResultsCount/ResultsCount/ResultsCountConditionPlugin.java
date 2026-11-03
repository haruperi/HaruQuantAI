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
package com.strategyquant.plugin.ProjectCondition.impl.ResultsCount;

import com.strategyquant.lib.L;
import com.strategyquant.pluginlib.annotations.Category;
import com.strategyquant.pluginlib.annotations.License;
import com.strategyquant.pluginlib.annotations.Name;
import com.strategyquant.pluginlib.annotations.ShortDesc;
import com.strategyquant.tradinglib.Databank;
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
@Name(name="ResultsCount Condition plugin")
@Category(name="Project Condition")
@License(text="")
@ShortDesc(text="Short description")
@PluginImplementation
public class ResultsCountConditionPlugin
implements IProjectCondition {
    public static final Logger Log = LoggerFactory.getLogger((String)"ResultsCountConditionPlugin");
    private static final ProjectConditionField[] fields = new ProjectConditionField[]{new ProjectConditionField("databank", "Databank", "Results"), new ProjectConditionField("comparator", "Comparator", "<"), new ProjectConditionField("number", "Value", "100")};
    private String databankName;
    private String comparator;
    private int value;
    private String lastCheckedValue = null;

    public String getName() {
        return "ResultsCount";
    }

    public String getTitle() {
        return L.tsq((String)"Number of results in databank");
    }

    public String getDescription() {
        return String.format(this.getDescriptionFormat(), this.databankName, this.comparator, this.value);
    }

    public String getDescriptionFormat() {
        return L.t((String)"Number of results in databank %s %s %d", (Object[])new Object[0]);
    }

    public String getLastCheckedValue() {
        return this.lastCheckedValue;
    }

    public ProjectConditionField[] getFields() {
        return fields;
    }

    public void readSettings(Element elSettings) throws Exception {
        List fieldElems = elSettings.getChildren("Field");
        block10: for (int a = 0; a < fieldElems.size(); ++a) {
            Element elField = (Element)fieldElems.get(a);
            String type = elField.getAttributeValue("type");
            if (type == null) continue;
            switch (type) {
                case "databank": {
                    this.databankName = elField.getText();
                    continue block10;
                }
                case "comparator": {
                    this.comparator = elField.getText();
                    continue block10;
                }
                case "number": {
                    this.value = Integer.parseInt(elField.getText());
                }
            }
        }
    }

    public boolean isMet(SQProject project, ISQTask task) throws Exception {
        Databank databank = (Databank)project.getDatabanks().get((Object)this.databankName);
        if (databank == null) {
            throw new Exception(L.t((String)"Databank %s doesn't exist", (Object[])new Object[]{this.databankName}));
        }
        int resultsCount = databank.getRecords().size();
        this.lastCheckedValue = resultsCount + "";
        return Condition.validate((double)(resultsCount - this.value), (String)this.comparator);
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
        ResultsCountConditionPlugin newInstance = new ResultsCountConditionPlugin();
        newInstance.databankName = this.databankName;
        newInstance.comparator = this.comparator;
        newInstance.value = this.value;
        return newInstance;
    }
}

