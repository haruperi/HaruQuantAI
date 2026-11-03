/*
 * Decompiled with CFR 0.152.
 */
package com.strategyquant.datalib.data.imports;

import com.strategyquant.datalib.data.io.columns.AskCol;
import com.strategyquant.datalib.data.io.columns.BidCol;
import com.strategyquant.datalib.data.io.columns.CloseCol;
import com.strategyquant.datalib.data.io.columns.CustomValue;
import com.strategyquant.datalib.data.io.columns.DateCol;
import com.strategyquant.datalib.data.io.columns.DateTimeCol;
import com.strategyquant.datalib.data.io.columns.DefaultCol;
import com.strategyquant.datalib.data.io.columns.HighCol;
import com.strategyquant.datalib.data.io.columns.LowCol;
import com.strategyquant.datalib.data.io.columns.OpenCol;
import com.strategyquant.datalib.data.io.columns.TimeCol;
import com.strategyquant.datalib.data.io.columns.UnusedCol;
import com.strategyquant.datalib.data.io.columns.VolumeCol;
import java.util.ArrayList;

public class DataColumns {
    private static DataColumns instance = new DataColumns();
    private ArrayList<DefaultCol> availableColTypes = new ArrayList();

    private DataColumns() {
        this.initAvailableColTypes();
    }

    public ArrayList<DefaultCol> getAvailableColTypes() {
        return this.availableColTypes;
    }

    public static DataColumns getInstance() {
        return instance;
    }

    private void initAvailableColTypes() {
        this.availableColTypes.add(new AskCol());
        this.availableColTypes.add(new BidCol());
        this.availableColTypes.add(new CloseCol());
        this.availableColTypes.add(new DateCol());
        this.availableColTypes.add(new TimeCol());
        this.availableColTypes.add(new DateTimeCol());
        this.availableColTypes.add(new HighCol());
        this.availableColTypes.add(new LowCol());
        this.availableColTypes.add(new OpenCol());
        this.availableColTypes.add(new UnusedCol());
        this.availableColTypes.add(new VolumeCol());
        for (int i = 1; i < 30; ++i) {
            this.availableColTypes.add(new CustomValue(i));
        }
    }

    public DefaultCol findColTypeByName(String string) {
        for (DefaultCol defaultCol : this.availableColTypes) {
            if (!defaultCol.getName().equalsIgnoreCase(string)) continue;
            return defaultCol;
        }
        return null;
    }
}

