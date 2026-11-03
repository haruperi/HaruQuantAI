/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  com.strategyquant.lib.db.DbBase
 *  org.slf4j.Logger
 *  org.slf4j.LoggerFactory
 */
package com.strategyquant.datalib.data;

import com.strategyquant.lib.db.DbBase;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

public abstract class DataDb
extends DbBase {
    public static final Logger Log = LoggerFactory.getLogger(DataDb.class);

    public DataDb(String string) {
        super("DataDb", "data.db", string);
        this.initDatabase();
    }

    public abstract void initDatabase();
}

