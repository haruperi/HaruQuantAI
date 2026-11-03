/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  com.strategyquant.pluginlib.SQPluginManager
 *  org.jdom2.Element
 *  org.json.JSONArray
 *  org.json.JSONObject
 */
package com.strategyquant.tradinglib.project;

import com.strategyquant.pluginlib.SQPluginManager;
import com.strategyquant.tradinglib.project.IProjectCondition;
import com.strategyquant.tradinglib.project.ProjectConditionField;
import java.util.ArrayList;
import java.util.List;
import org.jdom2.Element;
import org.json.JSONArray;
import org.json.JSONObject;

public class ProjectConditions {
    private static ArrayList<IProjectCondition> conditionPlugins;

    public static ArrayList<IProjectCondition> list() {
        if (conditionPlugins == null) {
            conditionPlugins = SQPluginManager.getPlugins(IProjectCondition.class);
        }
        return conditionPlugins;
    }

    public static JSONArray toJSON() {
        JSONArray jSONArray = new JSONArray();
        ArrayList<IProjectCondition> arrayList = ProjectConditions.list();
        for (int i = 0; i < arrayList.size(); ++i) {
            IProjectCondition iProjectCondition = arrayList.get(i);
            JSONObject jSONObject = new JSONObject();
            jSONObject.put("type", (Object)iProjectCondition.getName());
            jSONObject.put("title", (Object)iProjectCondition.getTitle());
            jSONObject.put("descriptionFormat", (Object)iProjectCondition.getDescriptionFormat());
            JSONArray jSONArray2 = new JSONArray();
            ProjectConditionField[] projectConditionFieldArray = iProjectCondition.getFields();
            for (int j = 0; j < projectConditionFieldArray.length; ++j) {
                ProjectConditionField projectConditionField = projectConditionFieldArray[j];
                JSONObject jSONObject2 = new JSONObject();
                jSONObject2.put("name", (Object)projectConditionField.getName());
                jSONObject2.put("type", (Object)projectConditionField.getType());
                jSONObject2.put("value", (Object)projectConditionField.getDefaultValue());
                jSONObject2.put("defaultValue", (Object)projectConditionField.getDefaultValue());
                jSONArray2.put((Object)jSONObject2);
            }
            jSONObject.put("fields", (Object)jSONArray2);
            jSONArray.put((Object)jSONObject);
        }
        return jSONArray;
    }

    public static ArrayList<IProjectCondition> loadFromConfig(Element element) throws Exception {
        ArrayList<IProjectCondition> arrayList = ProjectConditions.list();
        ArrayList<IProjectCondition> arrayList2 = new ArrayList<IProjectCondition>();
        List list = element.getChildren("Condition");
        for (int i = 0; i < list.size(); ++i) {
            Element element2 = (Element)list.get(i);
            String string = element2.getAttributeValue("type");
            if (string == null) continue;
            for (int j = 0; j < arrayList.size(); ++j) {
                IProjectCondition iProjectCondition = arrayList.get(j);
                if (!string.equals(iProjectCondition.getName())) continue;
                IProjectCondition iProjectCondition2 = iProjectCondition.clone();
                iProjectCondition2.readSettings(element2);
                arrayList2.add(iProjectCondition2);
            }
        }
        return arrayList2;
    }
}

