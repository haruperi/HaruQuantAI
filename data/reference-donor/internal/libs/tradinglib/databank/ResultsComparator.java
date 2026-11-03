/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  com.strategyquant.lib.SQUtils
 *  com.strategyquant.lib.utils.StringComparator
 *  org.slf4j.Logger
 *  org.slf4j.LoggerFactory
 */
package com.strategyquant.tradinglib.databank;

import com.strategyquant.lib.SQUtils;
import com.strategyquant.lib.utils.StringComparator;
import com.strategyquant.tradinglib.Databank;
import com.strategyquant.tradinglib.ResultsGroup;
import com.strategyquant.tradinglib.databank.DatabankTableColumnEntry;
import com.strategyquant.tradinglib.databank.DatabankTableView;
import java.util.Comparator;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

public class ResultsComparator
implements Comparator<ResultsGroup> {
    private static final Logger Log = LoggerFactory.getLogger(ResultsComparator.class);
    private Databank databank;
    private StringComparator stringComparator = new StringComparator();
    private int column = 0;
    private String dataType;
    private boolean asc = true;

    public ResultsComparator(Databank databank) {
        this.databank = databank;
    }

    @Override
    public int compare(ResultsGroup resultsGroup, ResultsGroup resultsGroup2) {
        DatabankTableView databankTableView = this.databank.getView();
        if (databankTableView == null) {
            return 0;
        }
        this.dataType = "Text";
        String string = null;
        String string2 = null;
        boolean bl = this.databank.getProject().equals("Optimizer");
        int n = this.column - (bl ? 2 : 1);
        if (n >= 0 && n < databankTableView.columns.size()) {
            Object object = databankTableView.columns.get(n);
            this.dataType = ((DatabankTableColumnEntry)object).tableColumn.getType();
            string = ((DatabankTableColumnEntry)object).getValue(resultsGroup);
            string2 = ((DatabankTableColumnEntry)object).getValue(resultsGroup2);
        } else if (n == -1) {
            string = bl ? resultsGroup.getParams() : resultsGroup.getName();
            string2 = bl ? resultsGroup2.getParams() : resultsGroup2.getName();
        } else if (n == -2) {
            string = resultsGroup.getName();
            string2 = resultsGroup2.getName();
        } else {
            Log.error("Invalid databank sort column index : " + this.column);
            return 0;
        }
        try {
            switch (this.dataType) {
                case "Text": {
                    String string3 = SQUtils.removeHtmlTags((String)string);
                    String string4 = SQUtils.removeHtmlTags((String)string2);
                    int n2 = this.stringComparator.compare(string3, string4);
                    if (this.asc) {
                        return n2;
                    }
                    return -1 * n2;
                }
            }
            double d = Double.parseDouble(SQUtils.extractNumber((String)SQUtils.removeHtmlTags((String)string)));
            double d2 = Double.parseDouble(SQUtils.extractNumber((String)SQUtils.removeHtmlTags((String)string2)));
            if (d < d2) {
                if (this.asc) {
                    return -1;
                }
                return 1;
            }
            if (d > d2) {
                if (this.asc) {
                    return 1;
                }
                return -1;
            }
            return 0;
        }
        catch (Exception exception) {
            String string5 = SQUtils.removeHtmlTags((String)String.valueOf(string));
            String string6 = SQUtils.removeHtmlTags((String)String.valueOf(string2));
            int n3 = this.stringComparator.compare(string5, string6);
            if (this.asc) {
                return n3;
            }
            return -1 * n3;
        }
    }

    public int getColumn() {
        return this.column;
    }

    public void setColumn(int n) {
        this.column = n;
    }

    public boolean isAsc() {
        return this.asc;
    }

    public void setAsc(boolean bl) {
        this.asc = bl;
    }
}

