/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  org.json.JSONArray
 *  org.json.JSONObject
 */
package com.strategyquant.plugin.Portfolio.impl.Composer;

import org.json.JSONArray;
import org.json.JSONObject;

public class PortfolioComposerChart {
    String labelTitle;
    String labelX;
    String labelY;
    String labelMinimumRiskPortfolio;
    String labelOptimalPortfolio;
    double[] x;
    double[] y;
    String[] weights;
    double bestX;
    double bestY;
    double MinimumRiskPortofolioX;
    double MinimumRiskPortofolioY;
    int decimals = 0;

    public PortfolioComposerChart(int nDataPoints) {
        this.x = new double[nDataPoints];
        this.y = new double[nDataPoints];
        this.weights = new String[nDataPoints];
    }

    public String toJsonString() {
        if (this.x == null) {
            return "Not initialized yet.";
        }
        JSONObject json = new JSONObject();
        json.put("labelTitle", (Object)this.labelTitle);
        json.put("labelX", (Object)this.labelX);
        json.put("labelY", (Object)this.labelY);
        json.put("labelMinimumRiskPortfolio", (Object)this.labelMinimumRiskPortfolio);
        json.put("labelOptimalPortfolio", (Object)this.labelOptimalPortfolio);
        json.put("x", (Object)new JSONArray((Object)this.x));
        json.put("y", (Object)new JSONArray((Object)this.y));
        json.put("weights", (Object)new JSONArray((Object)this.weights));
        json.put("bestX", this.bestX);
        json.put("bestY", this.bestY);
        json.put("MinRiskX", this.MinimumRiskPortofolioX);
        json.put("MinRiskY", this.MinimumRiskPortofolioY);
        json.put("decimals", this.decimals);
        return json.toString();
    }
}

