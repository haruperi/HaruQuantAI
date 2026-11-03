/*
 * Decompiled with CFR 0.152.
 */
package com.strategyquant.tradinglib.databank;

import com.strategyquant.tradinglib.Databank;
import com.strategyquant.tradinglib.ResultsGroup;
import java.util.ArrayList;
import java.util.Comparator;

public abstract class DatabankButton {
    private String name = "No Name";
    public static Comparator<DatabankButton> PositionComparator = new Comparator<DatabankButton>(){

        @Override
        public int compare(DatabankButton databankButton, DatabankButton databankButton2) {
            int n;
            int n2 = databankButton.getPreferredPosition();
            return n2 > (n = databankButton2.getPreferredPosition()) ? 1 : (n2 < n ? -1 : 0);
        }
    };

    public void setName(String string) {
        this.name = string;
    }

    public String getName() {
        return this.name;
    }

    public String[] parseName() {
        String[] stringArray = this.name.split(":");
        return stringArray;
    }

    public abstract void execute(Databank var1, ArrayList<ResultsGroup> var2) throws Exception;

    public String getProduct() {
        return "*";
    }

    public int getPreferredPosition() {
        return 100;
    }
}

