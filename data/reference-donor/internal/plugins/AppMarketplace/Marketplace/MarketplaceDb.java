/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  com.strategyquant.lib.constants.SQPaths
 *  com.strategyquant.lib.db.DbBase
 *  org.json.JSONArray
 *  org.json.JSONObject
 */
package com.strategyquant.plugin.App.impl.Marketplace;

import com.strategyquant.lib.constants.SQPaths;
import com.strategyquant.lib.db.DbBase;
import java.sql.Connection;
import java.sql.PreparedStatement;
import java.sql.ResultSet;
import org.json.JSONArray;
import org.json.JSONObject;

public class MarketplaceDb
extends DbBase {
    private static MarketplaceDb instance = null;

    public static synchronized MarketplaceDb get() {
        if (instance == null) {
            instance = new MarketplaceDb(SQPaths.settingsDirPath);
        }
        return instance;
    }

    private MarketplaceDb(String directoryPath) {
        super("MarketplaceDb", "marketplace.db", directoryPath);
        this.initDatabase();
    }

    protected void initDatabase() {
        this.isDbExist();
        try {
            Class.forName("org.sqlite.JDBC");
            String query = "CREATE TABLE IF NOT EXISTS INSTALLED_PRODUCTS (SLUG VARCHAR(255) PRIMARY KEY NOT NULL, TITLE VARCHAR(512), VERSION VARCHAR(64), FILE_NAME VARCHAR(512), SHA256 VARCHAR(64), INSTALLED_AT INTEGER NOT NULL, FILES TEXT)";
            this.sqlCommand(query);
            Log.debug("Marketplace database created successfully");
        }
        catch (Exception e) {
            Log.error("DB error:", (Throwable)e);
        }
    }

    /*
     * WARNING - Removed try catching itself - possible behaviour change.
     */
    public void recordInstall(String slug, String title, String version, String fileName, String sha256, JSONArray installedFiles) throws Exception {
        Connection conn = null;
        PreparedStatement stat = null;
        try {
            conn = this.getConnection();
            stat = conn.prepareStatement("INSERT OR REPLACE INTO INSTALLED_PRODUCTS (SLUG, TITLE, VERSION, FILE_NAME, SHA256, INSTALLED_AT, FILES) VALUES (?,?,?,?,?,?,?)");
            stat.setString(1, slug);
            stat.setString(2, title);
            stat.setString(3, version);
            stat.setString(4, fileName);
            stat.setString(5, sha256);
            stat.setLong(6, System.currentTimeMillis());
            stat.setString(7, installedFiles != null ? installedFiles.toString() : null);
            stat.executeUpdate();
        }
        catch (Throwable throwable) {
            this.close(stat);
            this.close(conn);
            throw throwable;
        }
        this.close(stat);
        this.close(conn);
    }

    /*
     * WARNING - Removed try catching itself - possible behaviour change.
     * Enabled aggressive block sorting
     * Enabled unnecessary exception pruning
     * Enabled aggressive exception aggregation
     */
    public JSONArray getInstalledFiles(String slug) {
        ResultSet rs;
        PreparedStatement stat;
        Connection conn;
        block7: {
            JSONArray jSONArray;
            block6: {
                conn = null;
                stat = null;
                rs = null;
                try {
                    String files;
                    conn = this.getConnection();
                    stat = conn.prepareStatement("SELECT FILES FROM INSTALLED_PRODUCTS WHERE SLUG=?");
                    stat.setString(1, slug);
                    rs = stat.executeQuery();
                    if (rs.next() && (files = rs.getString("FILES")) != null && !files.trim().isEmpty()) {
                        jSONArray = new JSONArray(files);
                        this.close(rs);
                        break block6;
                    }
                    this.close(rs);
                    break block7;
                }
                catch (Exception e) {
                    Log.error("DB Exception", (Throwable)e);
                    return new JSONArray();
                }
            }
            this.close(stat);
            this.close(conn);
            return jSONArray;
        }
        this.close(stat);
        this.close(conn);
        return new JSONArray();
        finally {
            this.close(rs);
            this.close(stat);
            this.close(conn);
        }
    }

    /*
     * WARNING - Removed try catching itself - possible behaviour change.
     */
    public void deleteInstall(String slug) throws Exception {
        Connection conn = null;
        PreparedStatement stat = null;
        try {
            conn = this.getConnection();
            stat = conn.prepareStatement("DELETE FROM INSTALLED_PRODUCTS WHERE SLUG=?");
            stat.setString(1, slug);
            stat.executeUpdate();
        }
        catch (Throwable throwable) {
            this.close(stat);
            this.close(conn);
            throw throwable;
        }
        this.close(stat);
        this.close(conn);
    }

    /*
     * WARNING - Removed try catching itself - possible behaviour change.
     */
    public JSONArray listInstalled() {
        JSONArray result = new JSONArray();
        Connection conn = null;
        PreparedStatement stat = null;
        ResultSet rs = null;
        try {
            conn = this.getConnection();
            stat = conn.prepareStatement("SELECT SLUG, VERSION FROM INSTALLED_PRODUCTS ORDER BY SLUG");
            rs = stat.executeQuery();
            while (rs.next()) {
                JSONObject item = new JSONObject();
                item.put("slug", (Object)rs.getString("SLUG"));
                String version = rs.getString("VERSION");
                if (version != null && !version.isEmpty()) {
                    item.put("version", (Object)version);
                }
                result.put((Object)item);
            }
        }
        catch (Exception e) {
            try {
                Log.error("DB Exception", (Throwable)e);
            }
            catch (Throwable throwable) {
                this.close(rs);
                this.close(stat);
                this.close(conn);
                throw throwable;
            }
            this.close(rs);
            this.close(stat);
            this.close(conn);
        }
        this.close(rs);
        this.close(stat);
        this.close(conn);
        return result;
    }
}

