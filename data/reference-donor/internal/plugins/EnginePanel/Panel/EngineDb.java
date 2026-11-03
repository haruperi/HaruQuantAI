/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  com.strategyquant.lib.db.DbBase
 */
package com.strategyquant.plugin.Engine.impl.Panel;

import com.strategyquant.lib.db.DbBase;
import java.sql.Connection;
import java.sql.ResultSet;
import java.sql.Statement;

public class EngineDb
extends DbBase {
    private static EngineDb instance = null;

    public static void init(String directoryPath) {
        if (instance != null) {
            return;
        }
        instance = new EngineDb(directoryPath);
    }

    private EngineDb(String directoryPath) {
        super("EngineDb", "EnginePanel.db", directoryPath);
        this.initDatabase();
    }

    private static EngineDb get() {
        return instance;
    }

    protected void initDatabase() {
        if (this.isDbExist()) {
            return;
        }
        try {
            String query = "CREATE TABLE SETTINGS (KEY VARCHAR(256) PRIMARY KEY, VALUE VARCHAR(256) DEFAULT '')";
            this.sqlCommand(query);
            Log.debug("Engine settings table created successfully");
        }
        catch (Exception e) {
            Log.error("DB error:", (Throwable)e);
        }
    }

    public static void setSetting(String key, String value) {
        EngineDb.get()._setSetting(key, value);
    }

    public static String getSetting(String key, String defaultValue) {
        String value = EngineDb.get()._getSetting(key);
        return value == null ? defaultValue : value;
    }

    private void _setSetting(String key, String value) {
        try {
            if (this._getSetting(key) == null) {
                String query = "INSERT INTO SETTINGS (KEY, VALUE) VALUES ('" + key + "','" + value + "')";
                this.sqlCommand(query);
            } else {
                String query = "UPDATE SETTINGS SET VALUE='" + value + "' WHERE KEY='" + key + "'";
                this.sqlCommand(query);
            }
        }
        catch (Exception e) {
            Log.error("DB Exception", (Throwable)e);
        }
    }

    /*
     * WARNING - Removed try catching itself - possible behaviour change.
     * Enabled aggressive block sorting
     * Enabled unnecessary exception pruning
     * Enabled aggressive exception aggregation
     */
    private String _getSetting(String key) {
        ResultSet rs;
        Statement stat;
        Connection conn;
        block7: {
            String string;
            block6: {
                conn = null;
                stat = null;
                rs = null;
                try {
                    conn = this.getConnection();
                    stat = conn.createStatement();
                    rs = stat.executeQuery("SELECT * FROM SETTINGS WHERE KEY='" + key + "'");
                    if (rs.next()) {
                        string = rs.getString("VALUE");
                        this.close(rs);
                        break block6;
                    }
                    this.close(rs);
                    break block7;
                }
                catch (Exception e) {
                    Log.error("DB Exception", (Throwable)e);
                    return null;
                }
            }
            this.close(stat);
            this.close(conn);
            return string;
        }
        this.close(stat);
        this.close(conn);
        return null;
        finally {
            this.close(rs);
            this.close(stat);
            this.close(conn);
        }
    }
}

