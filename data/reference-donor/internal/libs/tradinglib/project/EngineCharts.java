/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  org.json.JSONArray
 *  org.json.JSONObject
 */
package com.strategyquant.tradinglib.project;

import com.strategyquant.tradinglib.EngineChart;
import com.strategyquant.tradinglib.enginecharts.EngineChartsList;
import com.strategyquant.tradinglib.project.FitnessEvolution;
import com.strategyquant.tradinglib.project.SQProject;
import java.util.ArrayList;
import java.util.List;
import org.json.JSONArray;
import org.json.JSONObject;

public class EngineCharts {
    private ArrayList<EngineChart> list = new ArrayList();
    private ArrayList<EngineChart> global;
    public FitnessEvolution fitnessEvolution;
    private SQProject project;

    public EngineCharts(SQProject sQProject) {
        this.global = EngineChartsList.getInstance().globalCharts;
        this.fitnessEvolution = null;
        this.project = sQProject;
        this.init(sQProject);
    }

    private void init(SQProject sQProject) {
        this.fitnessEvolution = new FitnessEvolution(sQProject);
        List list = EngineChartsList.getInstance().getAvailableClasses();
        for (int i = 0; i < list.size(); ++i) {
            EngineChart engineChart = (EngineChart)list.get(i);
            if (engineChart.getType() != 50) continue;
            EngineChart engineChart2 = (EngineChart)EngineChartsList.getInstance().createNew(engineChart.getClassName());
            engineChart2.setProject(sQProject);
            this.list.add(engineChart2);
        }
    }

    public JSONObject print() {
        JSONObject jSONObject = new JSONObject();
        JSONArray jSONArray = new JSONArray();
        this.printCharts(this.list, jSONArray);
        this.printCharts(this.global, jSONArray);
        jSONObject.put("charts", (Object)jSONArray);
        if (this.project.getName().equals("Builder")) {
            jSONObject.put("fitnessEvolution", (Object)this.fitnessEvolution.print());
        }
        return jSONObject;
    }

    private void printCharts(ArrayList<EngineChart> arrayList, JSONArray jSONArray) {
        for (int i = 0; i < arrayList.size(); ++i) {
            EngineChart engineChart = arrayList.get(i);
            JSONObject jSONObject = new JSONObject();
            JSONObject jSONObject2 = engineChart.print();
            if (jSONObject2 == null) continue;
            jSONObject.put("type", (Object)engineChart.getClassName());
            jSONObject.put("data", (Object)jSONObject2);
            jSONArray.put((Object)jSONObject);
        }
    }

    public void generate() {
        for (int i = 0; i < this.list.size(); ++i) {
            EngineChart engineChart = this.list.get(i);
            engineChart.addNextValue();
        }
        this.fitnessEvolution.addNextValue();
    }
}

