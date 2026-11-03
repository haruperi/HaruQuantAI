/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  com.strategyquant.model.IdName
 *  org.h2.jdbcx.JdbcConnectionPool
 *  org.slf4j.Logger
 *  org.slf4j.LoggerFactory
 */
package com.strategyquant.datalib.historyData;

import com.strategyquant.datalib.historyData.TickerFilterDto;
import com.strategyquant.datalib.historyData.dto.AliasDto;
import com.strategyquant.datalib.historyData.dto.TickerDto;
import com.strategyquant.model.IdName;
import java.sql.Connection;
import java.sql.Date;
import java.sql.PreparedStatement;
import java.sql.ResultSet;
import java.sql.SQLException;
import java.sql.Statement;
import java.util.Arrays;
import java.util.Collection;
import java.util.HashMap;
import java.util.LinkedList;
import java.util.List;
import java.util.Map;
import java.util.Set;
import org.h2.jdbcx.JdbcConnectionPool;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

public abstract class AbstractHistoryDataDao {
    public static final Logger Log = LoggerFactory.getLogger(AbstractHistoryDataDao.class);
    private static final String SQL_GET_ALL_MARKETS = "select id, code from market order by code";
    private static final String SQL_GET_ALL_TICKERS = "select t.timeframe,t.id,t.ticker,t.name,t.market_id,m.code,t.date_from,t.date_to,t.date_from,t.date_to,t.name,commodity_id tickerName,type.name typeName,alias_ticker_id from ticker as t left outer join market as m on m.id=t.market_id left outer join ticker_type as type on type.id=t.type_id";
    private JdbcConnectionPool pool;
    private Map<String, String> tickersExchnageMap = null;

    public AbstractHistoryDataDao(String string, String string2, String string3) {
        this.pool = JdbcConnectionPool.create((String)("jdbc:h2:file:" + string3), (String)string, (String)string2);
    }

    public void createIndexes() throws SQLException {
        this.createIndex("CREATE INDEX IDX_MARKET_CODE ON MARKET (code)");
        this.createIndex("CREATE INDEX IDX_TICKER_TICKER ON TICKER (TICKER)");
        this.createIndex("CREATE INDEX IDX_TICKER_NAME ON TICKER (NAME)");
        this.createIndex("CREATE INDEX IDX_TICKER_MARKET_ID ON TICKER (MARKET_ID)");
        this.createIndex("CREATE INDEX IDX_TICKER_MARKET_TICKER_ID ON TICKER_MARKET (TICKER_ID)");
        this.createIndex("CREATE INDEX IDX_TICKER_MARKET_MARKET_ID ON TICKER_MARKET (MARKET_ID)");
        this.createIndex("CREATE INDEX IDX_ALIAS_ALIAS ON ALIAS(ALIAS)");
        this.createForeignKey("ALTER TABLE TICKER ADD FOREIGN KEY (TYPE_ID) REFERENCES TICKER_TYPE(ID)");
        this.createForeignKey("ALTER TABLE TICKER_PROPERTIES ADD FOREIGN KEY (TICKER_ID) REFERENCES TICKER(ID)");
        this.createForeignKey("ALTER TABLE TICKER_MARKET ADD FOREIGN KEY (MARKET_ID) REFERENCES MARKET(ID)");
        this.createForeignKey("ALTER TABLE TICKER_MARKET ADD FOREIGN KEY (TICKER_ID) REFERENCES TICKER(ID)");
    }

    public List<AliasDto> getAliasesForAlias(Collection<String> collection) throws SQLException {
        try (Connection connection = this.getConnection();){
            Object object;
            block13: {
                Statement statement = connection.createStatement();
                try {
                    String string = this.getInStatement("upper(alias)", collection, false);
                    String string2 = "select original, alias from alias where " + string;
                    ResultSet resultSet = statement.executeQuery(string2);
                    LinkedList<AliasDto> linkedList = new LinkedList<AliasDto>();
                    while (resultSet.next()) {
                        object = resultSet.getString("original");
                        String string3 = resultSet.getString("alias");
                        AliasDto aliasDto = new AliasDto();
                        linkedList.add(aliasDto);
                        aliasDto.setAlias(string3);
                        aliasDto.setOriginal((String)object);
                    }
                    object = linkedList;
                    if (statement == null) break block13;
                }
                catch (Throwable throwable) {
                    if (statement != null) {
                        try {
                            statement.close();
                        }
                        catch (Throwable throwable2) {
                            throwable.addSuppressed(throwable2);
                        }
                    }
                    throw throwable;
                }
                statement.close();
            }
            return object;
        }
    }

    public Map<String, String> getAliasesMapForAlias(Collection<String> collection) throws SQLException {
        try {
            List<AliasDto> list = this.getAliasesForAlias(collection);
            HashMap<String, String> hashMap = new HashMap<String, String>();
            for (AliasDto aliasDto : list) {
                hashMap.put(aliasDto.getOriginal(), aliasDto.getAlias());
            }
            return hashMap;
        }
        catch (Exception exception) {
            Log.error("Error while loading aliases", (Throwable)exception);
            return new HashMap<String, String>();
        }
    }

    /*
     * Enabled aggressive block sorting
     * Enabled unnecessary exception pruning
     * Enabled aggressive exception aggregation
     */
    public Date getChangeDate(String string) {
        try (Connection connection = this.getConnection();
             PreparedStatement preparedStatement = connection.prepareStatement("select change_date from ticker where ticker=?");){
            preparedStatement.setString(1, string);
            ResultSet resultSet = preparedStatement.executeQuery();
            if (!resultSet.next()) return null;
            Date date = resultSet.getDate("change_date");
            return date;
        }
        catch (Exception exception) {
            Log.error("Error while checking change_date value", (Throwable)exception);
        }
        return null;
    }

    public Map<String, Date> getChangeDate() {
        HashMap<String, Date> hashMap = new HashMap<String, Date>();
        try (Connection connection = this.getConnection();
             PreparedStatement preparedStatement = connection.prepareStatement("select ticker, change_date from ticker");){
            ResultSet resultSet = preparedStatement.executeQuery();
            while (resultSet.next()) {
                hashMap.put(resultSet.getString("ticker"), resultSet.getDate("change_date"));
            }
        }
        catch (Exception exception) {
            Log.error("Error while checking change_date value", (Throwable)exception);
        }
        return hashMap;
    }

    public void dispose() {
        this.pool.dispose();
    }

    protected void createForeignKey(String string) throws SQLException {
        this.sqlCommand(string);
    }

    protected void createIndex(String string) throws SQLException {
        this.sqlCommand(string);
    }

    private void sqlCommand(String string) throws SQLException {
        try (Connection connection = this.getConnection();
             Statement statement = connection.createStatement();){
            statement.executeUpdate(string);
        }
    }

    protected Connection getConnection() throws SQLException {
        return this.pool.getConnection();
    }

    public List<IdName> getAllMarkets() throws SQLException {
        try (Connection connection = this.getConnection();){
            LinkedList<IdName> linkedList;
            block13: {
                PreparedStatement preparedStatement = connection.prepareStatement(SQL_GET_ALL_MARKETS);
                try {
                    ResultSet resultSet = preparedStatement.executeQuery();
                    LinkedList<IdName> linkedList2 = new LinkedList<IdName>();
                    while (resultSet.next()) {
                        linkedList = resultSet.getLong("id");
                        String string = resultSet.getString("code");
                        linkedList2.add(new IdName(linkedList, string));
                    }
                    linkedList = linkedList2;
                    if (preparedStatement == null) break block13;
                }
                catch (Throwable throwable) {
                    if (preparedStatement != null) {
                        try {
                            preparedStatement.close();
                        }
                        catch (Throwable throwable2) {
                            throwable.addSuppressed(throwable2);
                        }
                    }
                    throw throwable;
                }
                preparedStatement.close();
            }
            return linkedList;
        }
    }

    protected String getTickerSql(String string, TickerFilterDto tickerFilterDto, Set<String> set) throws SQLException {
        boolean bl;
        StringBuilder stringBuilder = new StringBuilder(string);
        boolean bl2 = false;
        if (tickerFilterDto.getMarketId() != null && !tickerFilterDto.getMarketId().equals(0L)) {
            stringBuilder.append(" where t.market_id=" + tickerFilterDto.getMarketId());
            bl2 = true;
        }
        boolean bl3 = bl = tickerFilterDto.getNames() != null && tickerFilterDto.getNames().length > 0;
        if (bl) {
            stringBuilder.append(bl2 ? " and " : " where ");
            stringBuilder.append("(");
            if (tickerFilterDto.isExactMatch()) {
                stringBuilder.append("t.ticker in(");
                for (int i = 0; i < tickerFilterDto.getNames().length; ++i) {
                    stringBuilder.append("'" + tickerFilterDto.getNames()[i].trim() + "'");
                    if (i == tickerFilterDto.getNames().length - 1) continue;
                    stringBuilder.append(",");
                }
                stringBuilder.append(")");
            } else {
                if (tickerFilterDto.isSearchInTicker()) {
                    String[] stringArray = tickerFilterDto.getNames();
                    if (!set.isEmpty()) {
                        LinkedList<String> linkedList = new LinkedList<String>(Arrays.asList(stringArray));
                        linkedList.addAll(set);
                        stringArray = linkedList.toArray(new String[0]);
                    }
                    stringBuilder.append(this.getInStatement("upper(t.ticker)", stringArray, true));
                }
                if (tickerFilterDto.isSearchInName() && tickerFilterDto.isSearchInTicker()) {
                    stringBuilder.append(" OR ");
                }
                if (tickerFilterDto.isSearchInName()) {
                    stringBuilder.append(this.getInStatement("upper(t.name)", tickerFilterDto.getNames(), true));
                }
            }
            stringBuilder.append(")");
        }
        if (!bl2 && !bl) {
            stringBuilder.append(" where 1=1 ");
        }
        this.appendTickersSql(stringBuilder, tickerFilterDto);
        stringBuilder.append(" order by t.ticker");
        String string2 = stringBuilder.toString();
        return string2;
    }

    protected void appendTickersSql(StringBuilder stringBuilder, TickerFilterDto tickerFilterDto) {
    }

    protected String getInStatement(String string, String[] stringArray, boolean bl) {
        StringBuilder stringBuilder = new StringBuilder();
        stringBuilder.append("(");
        for (int i = 0; i < stringArray.length; ++i) {
            if (stringBuilder.length() > 1) {
                stringBuilder.append(" OR ");
            }
            if (bl) {
                stringBuilder.append(string + " like '%" + stringArray[i].toUpperCase().trim() + "%'");
                continue;
            }
            stringBuilder.append(string + " = '" + stringArray[i].toUpperCase().trim() + "'");
        }
        stringBuilder.append(")");
        return stringBuilder.toString();
    }

    protected String getInStatement(String string, Collection<String> collection, boolean bl) {
        StringBuilder stringBuilder = new StringBuilder();
        stringBuilder.append("(");
        for (String string2 : collection) {
            if (stringBuilder.length() > 1) {
                stringBuilder.append(" OR ");
            }
            if (bl) {
                stringBuilder.append(string + " like '%" + string2.toUpperCase().trim() + "%'");
                continue;
            }
            stringBuilder.append(string + " = '" + string2.toUpperCase().trim() + "'");
        }
        stringBuilder.append(")");
        return stringBuilder.toString();
    }

    private TickerDto getTicker(ResultSet resultSet) throws SQLException {
        TickerDto tickerDto = new TickerDto();
        tickerDto.setId(resultSet.getLong("id"));
        tickerDto.setTicker(resultSet.getString("ticker"));
        tickerDto.setName(resultSet.getString("name"));
        tickerDto.setMarketId(resultSet.getLong("market_id"));
        tickerDto.setMarketName(resultSet.getString("code"));
        tickerDto.setDateFrom(resultSet.getDate("date_from"));
        tickerDto.setDateTo(resultSet.getDate("date_to"));
        tickerDto.setType(resultSet.getString("typeName"));
        tickerDto.setCommodityId(resultSet.getLong("commodity_id"));
        String string = resultSet.getString("timeframe");
        tickerDto.setEod(string.equals("D"));
        if (resultSet.wasNull()) {
            tickerDto.setCommodityId(null);
        }
        tickerDto.setAliasTickerId(resultSet.getLong("alias_ticker_id"));
        if (resultSet.wasNull()) {
            tickerDto.setAliasTickerId(null);
        }
        return tickerDto;
    }

    public TickerDto getTicker(String string, String string2) throws SQLException {
        try (Connection connection = this.getConnection();){
            TickerDto tickerDto;
            block16: {
                PreparedStatement preparedStatement;
                block14: {
                    TickerDto tickerDto2;
                    block15: {
                        preparedStatement = connection.prepareStatement(string + " where t.ticker=?");
                        try {
                            preparedStatement.setString(1, string2);
                            ResultSet resultSet = preparedStatement.executeQuery();
                            if (!resultSet.next()) break block14;
                            tickerDto2 = this.getTicker(resultSet);
                            if (preparedStatement == null) break block15;
                        }
                        catch (Throwable throwable) {
                            if (preparedStatement != null) {
                                try {
                                    preparedStatement.close();
                                }
                                catch (Throwable throwable2) {
                                    throwable.addSuppressed(throwable2);
                                }
                            }
                            throw throwable;
                        }
                        preparedStatement.close();
                    }
                    return tickerDto2;
                }
                tickerDto = null;
                if (preparedStatement == null) break block16;
                preparedStatement.close();
            }
            return tickerDto;
        }
    }

    public TickerDto getTicker(String string) throws SQLException {
        return this.getTicker(SQL_GET_ALL_TICKERS, string);
    }

    public TickerDto getTicker(String string, Long l) throws SQLException {
        try (Connection connection = this.getConnection();){
            TickerDto tickerDto;
            block16: {
                PreparedStatement preparedStatement;
                block14: {
                    TickerDto tickerDto2;
                    block15: {
                        preparedStatement = connection.prepareStatement(string + " where t.id=?");
                        try {
                            preparedStatement.setLong(1, l);
                            ResultSet resultSet = preparedStatement.executeQuery();
                            if (!resultSet.next()) break block14;
                            tickerDto2 = this.getTicker(resultSet);
                            if (preparedStatement == null) break block15;
                        }
                        catch (Throwable throwable) {
                            if (preparedStatement != null) {
                                try {
                                    preparedStatement.close();
                                }
                                catch (Throwable throwable2) {
                                    throwable.addSuppressed(throwable2);
                                }
                            }
                            throw throwable;
                        }
                        preparedStatement.close();
                    }
                    return tickerDto2;
                }
                tickerDto = null;
                if (preparedStatement == null) break block16;
                preparedStatement.close();
            }
            return tickerDto;
        }
    }

    public TickerDto getTicker(Long l) throws SQLException {
        return this.getTicker(SQL_GET_ALL_TICKERS, l);
    }

    public final List<TickerDto> getTickers(String string, TickerFilterDto tickerFilterDto) throws SQLException {
        String[] stringArray = tickerFilterDto.getNames();
        if (stringArray == null) {
            stringArray = new String[]{};
        }
        try (Connection connection = this.getConnection();){
            Object object;
            block15: {
                Statement statement = connection.createStatement();
                try {
                    boolean bl = !tickerFilterDto.isExactMatch() && tickerFilterDto.isSearchInTicker();
                    HashMap<String, String> hashMap = bl && stringArray.length > 0 ? this.getAliasesMapForAlias(Arrays.asList(stringArray)) : new HashMap<String, String>();
                    String string2 = this.getTickerSql(string, tickerFilterDto, hashMap.keySet());
                    if (tickerFilterDto.getNames() != null && tickerFilterDto.getNames().length == 1 && tickerFilterDto.getNames()[0].equals("EVERYTHING")) {
                        string2 = string;
                    }
                    ResultSet resultSet = statement.executeQuery(string2);
                    LinkedList<TickerDto> linkedList = new LinkedList<TickerDto>();
                    while (resultSet.next()) {
                        object = this.getTicker(resultSet);
                        linkedList.add((TickerDto)object);
                    }
                    this.modifyTickers(linkedList, hashMap);
                    object = linkedList;
                    if (statement == null) break block15;
                }
                catch (Throwable throwable) {
                    if (statement != null) {
                        try {
                            statement.close();
                        }
                        catch (Throwable throwable2) {
                            throwable.addSuppressed(throwable2);
                        }
                    }
                    throw throwable;
                }
                statement.close();
            }
            return object;
        }
    }

    public List<TickerDto> getTickers(TickerFilterDto tickerFilterDto) throws SQLException {
        return this.getTickers(SQL_GET_ALL_TICKERS, tickerFilterDto);
    }

    protected void updateNameByTimeframe(TickerDto tickerDto) {
        if (tickerDto.isEod()) {
            tickerDto.setName(tickerDto.getName() + " - [Daily]");
        }
    }

    protected void modifyTickers(List<TickerDto> list, Map<String, String> map) throws SQLException {
        for (TickerDto tickerDto : list) {
            this.updateNameByTimeframe(tickerDto);
            String string = map.get(tickerDto.getTicker());
            if (string == null) continue;
            tickerDto.setName(tickerDto.getName() + " (" + string + ")");
        }
    }

    public synchronized String getExchangeForTicker(String string) throws SQLException {
        if (this.tickersExchnageMap == null) {
            this.tickersExchnageMap = new HashMap<String, String>();
            List<TickerDto> list = this.getTickers(new TickerFilterDto());
            list.stream().forEach(tickerDto -> this.tickersExchnageMap.put(tickerDto.getTicker(), tickerDto.getMarketName()));
        }
        if (string == null) {
            return null;
        }
        return this.tickersExchnageMap.get(string);
    }
}

