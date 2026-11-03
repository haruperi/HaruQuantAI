/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  com.strategyquant.lib.constants.SQPaths
 */
package com.strategyquant.datalib.session;

import com.strategyquant.datalib.data.DataDb;
import com.strategyquant.datalib.session.Session;
import com.strategyquant.datalib.session.SessionComparator;
import com.strategyquant.datalib.session.SessionElement;
import com.strategyquant.datalib.session.SessionException;
import com.strategyquant.datalib.session.SessionNoSession;
import com.strategyquant.lib.constants.SQPaths;
import java.io.File;
import java.sql.Connection;
import java.sql.ResultSet;
import java.sql.SQLException;
import java.sql.Statement;
import java.util.ArrayList;
import java.util.HashMap;

public class SessionManager
extends DataDb {
    private static SessionManager instance = null;
    private HashMap<String, Session> sessionCache = new HashMap();
    private ArrayList<Session> sessionList = new ArrayList();
    private boolean cacheEmpty = true;
    private Session sessionNoSession = new SessionNoSession();
    private SessionComparator sessionComparator = new SessionComparator();

    public static void init(String string) throws Exception {
        if (instance != null) {
            throw new Exception("SessionManager.init() called more than once!");
        }
        instance = new SessionManager(string);
    }

    private SessionManager(String string) {
        super(string);
        this.addInitialRecords();
    }

    private static SessionManager get() {
        return instance;
    }

    @Override
    public void initDatabase() {
        try {
            String string;
            if (!this.tableExists("SESSIONS")) {
                string = "CREATE TABLE SESSIONS (SESSION \tVARCHAR(50) PRIMARY KEY NOT NULL)";
                this.sqlCommand(string);
                Log.debug("Sessions table created successfully");
            }
            if (!this.tableExists("ELEMENTS")) {
                string = "CREATE TABLE ELEMENTS (ID\tINTEGER PRIMARY KEY AUTOINCREMENT,SESSION VARCHAR(50) NOT NULL,DAYFROM INTEGER NOT NULL,TIMEFROM INTEGER NOT NULL,DAYTO INTEGER NOT NULL,TIMETO INTEGER NOT NULL,EOD BOOLEAN NOT NULL)";
                this.sqlCommand(string);
                Log.info("Elements table created successfully");
            }
            if (!this.columnExists("SESSIONS", "BROKER_ID")) {
                string = "ALTER TABLE SESSIONS ADD BROKER_ID INT DEFAULT -1";
                this.sqlCommand(string);
            }
        }
        catch (Exception exception) {
            Log.error("DB error: Cannot create Sessions table.", (Throwable)exception);
        }
    }

    private void addInitialRecords() {
        try {
            ArrayList<SessionElement> arrayList = new ArrayList<SessionElement>();
            arrayList.add(new SessionElement(1, 0, 1, 0, true));
            arrayList.add(new SessionElement(2, 0, 2, 0, true));
            arrayList.add(new SessionElement(3, 0, 3, 0, true));
            arrayList.add(new SessionElement(4, 0, 4, 0, true));
            arrayList.add(new SessionElement(5, 0, 5, 0, true));
            Session session = new Session("Forex_245", arrayList);
            if (!this._checkSessionExists("Forex_245")) {
                this._addSession(session);
            }
            arrayList.add(new SessionElement(6, 0, 6, 0, true));
            arrayList.add(new SessionElement(7, 0, 7, 0, true));
            session = new Session("Forex_247", arrayList);
            if (!this._checkSessionExists("Forex_247")) {
                this._addSession(session);
            }
            arrayList = new ArrayList();
            arrayList.add(new SessionElement(1, SessionElement.getTimeInt("08:30"), 1, SessionElement.getTimeInt("15:00"), true));
            arrayList.add(new SessionElement(2, SessionElement.getTimeInt("08:30"), 2, SessionElement.getTimeInt("15:00"), true));
            arrayList.add(new SessionElement(3, SessionElement.getTimeInt("08:30"), 3, SessionElement.getTimeInt("15:00"), true));
            arrayList.add(new SessionElement(4, SessionElement.getTimeInt("08:30"), 4, SessionElement.getTimeInt("15:00"), true));
            arrayList.add(new SessionElement(5, SessionElement.getTimeInt("08:30"), 5, SessionElement.getTimeInt("15:00"), true));
            session = new Session("US_Index_Futures", arrayList);
            if (!this._checkSessionExists("US_Index_Futures")) {
                this._addSession(session);
            }
            arrayList = new ArrayList();
            arrayList.add(new SessionElement(1, SessionElement.getTimeInt("09:30"), 1, SessionElement.getTimeInt("16:00"), true));
            arrayList.add(new SessionElement(2, SessionElement.getTimeInt("09:30"), 2, SessionElement.getTimeInt("16:00"), true));
            arrayList.add(new SessionElement(3, SessionElement.getTimeInt("09:30"), 3, SessionElement.getTimeInt("16:00"), true));
            arrayList.add(new SessionElement(4, SessionElement.getTimeInt("09:30"), 4, SessionElement.getTimeInt("16:00"), true));
            arrayList.add(new SessionElement(5, SessionElement.getTimeInt("09:30"), 5, SessionElement.getTimeInt("16:00"), true));
            session = new Session("US_Stocks", arrayList);
            if (!this._checkSessionExists("US_Stocks")) {
                this._addSession(session);
            }
        }
        catch (Exception exception) {
            Log.error("Cannot add sessions.", (Throwable)exception);
        }
    }

    public static synchronized ArrayList<Session> getSessions() {
        return SessionManager.get()._getSessions();
    }

    public static void addSession(Session session) throws SessionException {
        SessionManager.get()._addSession(session);
        SessionManager.get()._clearCache();
    }

    public static Session getSession(String string) {
        return SessionManager.get()._getSession(string);
    }

    public static boolean checkSessionExists(String string) {
        return SessionManager.get()._checkSessionExists(string);
    }

    public static void removeSession(String string) throws SessionException {
        SessionManager.get()._removeSession(string);
        SessionManager.deleteOldDataFiles(string, new File(SQPaths.dataDirPath));
    }

    public static void updateSession(Session session) throws SessionException {
        SessionManager.updateSession(session.getSessionName(), session.getElements());
    }

    public static void updateSession(String string, ArrayList<SessionElement> arrayList) throws SessionException {
        SessionManager.get()._updateSession(string, arrayList);
        SessionManager.deleteOldDataFiles(string, new File(SQPaths.dataDirPath));
    }

    private static void deleteOldDataFiles(String string, File file) {
        if (!file.exists()) {
            return;
        }
        if (file.isDirectory()) {
            File[] fileArray = file.listFiles();
            for (int i = 0; i < fileArray.length; ++i) {
                SessionManager.deleteOldDataFiles(string, fileArray[i]);
            }
        } else {
            SessionManager.tryDeleteFile(file, string);
        }
    }

    private static void tryDeleteFile(File file, String string) {
        try {
            if (file.getName().endsWith("_" + string + ".dat") && !file.delete()) {
                Log.error("File '" + file.getAbsolutePath() + "' was not deleted");
            }
        }
        catch (Exception exception) {
            Log.error("Cannot delete file '" + file.getAbsolutePath() + "'", (Throwable)exception);
        }
    }

    /*
     * WARNING - Removed try catching itself - possible behaviour change.
     */
    private ArrayList<Session> _getSessions() {
        block9: {
            if (!this.cacheEmpty) {
                return this.sessionList;
            }
            this._clearCache();
            Connection connection = null;
            Statement statement = null;
            Statement statement2 = null;
            ResultSet resultSet = null;
            ResultSet resultSet2 = null;
            try {
                int n;
                String string;
                connection = this.getConnection();
                statement2 = connection.createStatement();
                resultSet2 = statement2.executeQuery("SELECT * FROM ELEMENTS");
                HashMap hashMap = new HashMap();
                while (resultSet2.next()) {
                    string = resultSet2.getString(2);
                    n = resultSet2.getInt(3);
                    int n2 = resultSet2.getInt(4);
                    int n3 = resultSet2.getInt(5);
                    int n4 = resultSet2.getInt(6);
                    boolean bl = resultSet2.getBoolean(7);
                    if (!hashMap.containsKey(string)) {
                        hashMap.put(string, new ArrayList());
                    }
                    ((ArrayList)hashMap.get(string)).add(new SessionElement(n, n2, n3, n4, bl));
                }
                statement = connection.createStatement();
                resultSet = statement.executeQuery("SELECT SESSION,BROKER_ID FROM SESSIONS");
                while (resultSet.next()) {
                    string = resultSet.getString(1);
                    n = resultSet.getInt(2);
                    ArrayList arrayList = hashMap.containsKey(string) ? (ArrayList)hashMap.get(string) : new ArrayList();
                    Session session = new Session(string, arrayList);
                    session.setBroker(n);
                    this.sessionCache.put(string, session);
                    this.sessionList.add(session);
                }
                this.cacheEmpty = false;
                this.close(resultSet);
            }
            catch (Exception exception) {
                Log.error("DB Exception", (Throwable)exception);
                break block9;
            }
            finally {
                this.close(resultSet);
                this.close(statement);
                this.close(connection);
            }
            this.close(statement);
            this.close(connection);
        }
        this.sessionList.sort(this.sessionComparator);
        return this.sessionList;
    }

    private void _addSession(Session session) throws SessionException {
        Connection connection = null;
        Statement statement = null;
        ResultSet resultSet = null;
        try {
            connection = this.getConnection();
            if (this._checkSessionExists(connection, session.getSessionName())) {
                throw new SessionException("Session '" + session.getSessionName() + "' already exists!");
            }
            statement = connection.createStatement();
            String string = "INSERT INTO SESSIONS (SESSION, BROKER_ID) VALUES ('" + session.getSessionName() + "'," + session.getBroker() + ")";
            statement.executeUpdate(string);
            this.createElements(session.getSessionName(), session.getElements(), statement);
        }
        catch (Exception exception) {
            try {
                throw new SessionException(exception.getMessage());
            }
            catch (Throwable throwable) {
                this.close(resultSet);
                this.close(statement);
                this.close(connection);
                throw throwable;
            }
        }
        this.close(resultSet);
        this.close(statement);
        this.close(connection);
    }

    private void createElements(String string, ArrayList<SessionElement> arrayList, Statement statement) throws SQLException {
        for (SessionElement sessionElement : arrayList) {
            String string2 = "INSERT INTO ELEMENTS(SESSION, DAYFROM, TIMEFROM, DAYTO, TIMETO, EOD) VALUES ('" + string + "'," + sessionElement.getDayFrom() + "," + sessionElement.getTimeFrom() + "," + sessionElement.getDayTo() + "," + sessionElement.getTimeTo() + "," + (sessionElement.isEOD() ? "1" : "0") + ")";
            Log.debug(string2);
            statement.executeUpdate(string2);
        }
        this._clearCache();
    }

    /*
     * WARNING - Removed try catching itself - possible behaviour change.
     */
    private boolean _checkSessionExists(String string) {
        if (string.equals("No Session")) {
            return true;
        }
        Connection connection = null;
        try {
            connection = this.getConnection();
            boolean bl = this._checkSessionExists(connection, string);
            return bl;
        }
        catch (Exception exception) {
            Log.error("DB Exception", (Throwable)exception);
            boolean bl = false;
            return bl;
        }
        finally {
            this.close(connection);
        }
    }

    private boolean _checkSessionExists(Connection connection, String string) {
        if (string.equals("No Session")) {
            return true;
        }
        if (this.sessionCache.containsKey(string)) {
            return true;
        }
        return this.sqlCheckRecordExists(connection, "SELECT * FROM SESSIONS WHERE SESSION='" + string + "'");
    }

    /*
     * WARNING - Removed try catching itself - possible behaviour change.
     */
    private Session _getSession(String string) {
        if (string.equals("No Session")) {
            return this.sessionNoSession;
        }
        if (this.sessionCache.containsKey(string)) {
            return this.sessionCache.get(string);
        }
        Connection connection = null;
        try {
            connection = this.getConnection();
            if (!this._checkSessionExists(connection, string)) {
                Session session = null;
                return session;
            }
            ArrayList<SessionElement> arrayList = this._getSessionElements(connection, string);
            Session session = new Session(string, arrayList);
            return session;
        }
        catch (Exception exception) {
            Log.error("DB Exception", (Throwable)exception);
        }
        finally {
            this.close(connection);
        }
        return null;
    }

    private ArrayList<SessionElement> _getSessionElements(Connection connection, String string) throws SessionException {
        ArrayList<SessionElement> arrayList;
        Statement statement = null;
        ResultSet resultSet = null;
        try {
            statement = connection.createStatement();
            resultSet = statement.executeQuery("SELECT * FROM ELEMENTS WHERE SESSION='" + string + "'");
            ArrayList<SessionElement> arrayList2 = new ArrayList<SessionElement>();
            while (resultSet.next()) {
                arrayList2.add(new SessionElement(resultSet.getInt("DAYFROM"), resultSet.getInt("TIMEFROM"), resultSet.getInt("DAYTO"), resultSet.getInt("TIMETO"), resultSet.getBoolean("EOD")));
            }
            arrayList = arrayList2;
        }
        catch (Exception exception) {
            try {
                Log.error("DB Exception", (Throwable)exception);
                throw new SessionException("Error getting elements for session '" + string + "' !");
            }
            catch (Throwable throwable) {
                this.close(resultSet);
                this.close(statement);
                throw throwable;
            }
        }
        this.close(resultSet);
        this.close(statement);
        return arrayList;
    }

    private void _clearCache() {
        this.sessionCache.clear();
        this.sessionList.clear();
        this.sessionList.add(this.sessionNoSession);
        this.cacheEmpty = true;
    }

    private void _removeSession(String string) throws SessionException {
        Statement statement = null;
        try {
            Connection connection = this.getConnection();
            statement = connection.createStatement();
            statement.executeUpdate("DELETE FROM SESSIONS WHERE SESSION='" + string + "'");
            statement.executeUpdate("DELETE FROM ELEMENTS WHERE SESSION='" + string + "'");
            this._clearCache();
        }
        catch (Exception exception) {
            try {
                Log.error("DB Exception", (Throwable)exception);
                throw new SessionException("Error while removing session '" + string + "'.");
            }
            catch (Throwable throwable) {
                this.close(statement);
                throw throwable;
            }
        }
        this.close(statement);
    }

    private void _updateSession(String string, ArrayList<SessionElement> arrayList) throws SessionException {
        Statement statement = null;
        try {
            Connection connection = this.getConnection();
            statement = connection.createStatement();
            statement.executeUpdate("DELETE FROM ELEMENTS WHERE SESSION='" + string + "'");
            this.createElements(string, arrayList, statement);
        }
        catch (Exception exception) {
            try {
                Log.error("DB Exception", (Throwable)exception);
                throw new SessionException("Error while removing session '" + string + "'.");
            }
            catch (Throwable throwable) {
                this.close(statement);
                throw throwable;
            }
        }
        this.close(statement);
    }
}

