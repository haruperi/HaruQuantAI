/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  com.strategyquant.datalib.data.DataException
 */
package com.strategyquant.tradinglib.task.settings;

import com.strategyquant.datalib.data.DataException;
import com.strategyquant.tradinglib.project.SQProject;
import java.text.ParseException;
import java.util.HashMap;

public interface IChangeSettings {
    public String applyChanges(HashMap<String, Object> var1, SQProject var2) throws DataException, ParseException, Exception;
}

