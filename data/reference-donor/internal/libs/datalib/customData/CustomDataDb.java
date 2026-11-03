/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  com.strategyquant.lib.db.DbBase
 */
package com.strategyquant.datalib.customData;

import com.strategyquant.lib.db.DbBase;

public abstract class CustomDataDb
extends DbBase {
    public CustomDataDb(String string) {
        super("CustomDataDb", "customdata.db", string);
        this.initDatabase();
    }

    public abstract void initDatabase();
}

