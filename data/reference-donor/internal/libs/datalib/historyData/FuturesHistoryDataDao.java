/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  com.strategyquant.lib.app.MainApp
 *  com.strategyquant.model.IdName
 */
package com.strategyquant.datalib.historyData;

import com.strategyquant.datalib.historyData.AbstractHistoryDataDao;
import com.strategyquant.datalib.historyData.TickerFilterDto;
import com.strategyquant.datalib.historyData.dto.CommodityDto;
import com.strategyquant.datalib.historyData.dto.TickerDto;
import com.strategyquant.lib.app.MainApp;
import com.strategyquant.model.IdName;
import java.io.File;
import java.sql.Connection;
import java.sql.PreparedStatement;
import java.sql.ResultSet;
import java.sql.SQLException;
import java.sql.Statement;
import java.util.HashMap;
import java.util.HashSet;
import java.util.LinkedList;
import java.util.List;
import java.util.Map;
import java.util.Set;
import java.util.stream.Collectors;

public class FuturesHistoryDataDao
extends AbstractHistoryDataDao {
    public static final Long BMF_ID = 100000L;
    private static final String SQL_GET_ALL_BR_TICKERS = "select t.timeframe,t.id,t.ticker,t.name,100000 as market_id,'BMF' as code,t.date_from,t.date_to,t.date_from,t.date_to,t.name,commodity_id tickerName,type.name typeName,alias_ticker_id from br_ticker as t left outer join ticker_type as type on type.id=t.type_id ";
    private static final Map<String, String> MONTH_LETTERS = new HashMap<String, String>();
    private static final Set<String> BR_SYMBOLS = new HashSet<String>();

    public FuturesHistoryDataDao(String string) {
        super("sq", "hE8+-%:b&]^c#[b#j;+=*R[N~hrtbn$", string + File.separator + "data_futures");
    }

    @Override
    public List<IdName> getAllMarkets() throws SQLException {
        List<IdName> list = super.getAllMarkets();
        if (MainApp.isBrazilianEdition()) {
            list.add(0, new IdName(BMF_ID, "BMF"));
        }
        return list;
    }

    @Override
    public void createIndexes() throws SQLException {
        super.createIndexes();
        this.createIndex("CREATE INDEX IDX_COMMODITY_CODE ON COMMODITY (code)");
        this.createForeignKey("ALTER TABLE TICKER ADD FOREIGN KEY (COMMODITY_ID) REFERENCES COMMODITY(ID)");
        if (MainApp.isBrazilianEdition()) {
            this.createForeignKey("ALTER TABLE BR_TICKER ADD FOREIGN KEY (COMMODITY_ID) REFERENCES COMMODITY(ID)");
        }
    }

    public CommodityDto getCommodity(Long l) throws SQLException {
        try (Connection connection = this.getConnection();){
            CommodityDto commodityDto;
            block16: {
                PreparedStatement preparedStatement;
                block14: {
                    CommodityDto commodityDto2;
                    block15: {
                        preparedStatement = connection.prepareStatement("select id,name,code,point_value,tick_step,tick_Size,order_size_multi,order_size_step from commodity where id=?");
                        try {
                            preparedStatement.setLong(1, l);
                            ResultSet resultSet = preparedStatement.executeQuery();
                            if (!resultSet.next()) break block14;
                            CommodityDto commodityDto3 = new CommodityDto();
                            commodityDto3.setId(resultSet.getLong("id"));
                            commodityDto3.setName(resultSet.getString("name"));
                            commodityDto3.setCode(resultSet.getString("code"));
                            commodityDto3.setPointValue(resultSet.getBigDecimal("point_value"));
                            commodityDto3.setTickStep(resultSet.getBigDecimal("tick_step"));
                            commodityDto3.setTickSize(resultSet.getBigDecimal("tick_size"));
                            commodityDto3.setOrderSizeMulti(resultSet.getBigDecimal("order_size_multi"));
                            commodityDto3.setOrderSizeStep(resultSet.getBigDecimal("order_size_step"));
                            commodityDto2 = commodityDto3;
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
                    return commodityDto2;
                }
                commodityDto = null;
                if (preparedStatement == null) break block16;
                preparedStatement.close();
            }
            return commodityDto;
        }
    }

    @Override
    public List<TickerDto> getTickers(TickerFilterDto tickerFilterDto) throws SQLException {
        List<TickerDto> list = super.getTickers(tickerFilterDto);
        boolean bl = BMF_ID.equals(tickerFilterDto.getMarketId());
        if (MainApp.isBrazilianEdition() && (tickerFilterDto.getMarketId() == null || tickerFilterDto.getMarketId().equals(0L) || bl)) {
            tickerFilterDto.setMarketId(null);
            tickerFilterDto.setOnlyContFutures(false);
            List<TickerDto> list2 = this.getTickers(SQL_GET_ALL_BR_TICKERS, tickerFilterDto);
            if (bl) {
                return list2;
            }
            list2.addAll(list);
            return list2;
        }
        return list;
    }

    private List<TickerDto> filterMainBr(List<TickerDto> list) {
        LinkedList<TickerDto> linkedList = new LinkedList<TickerDto>();
        for (TickerDto tickerDto : list) {
            String string = tickerDto.getTicker();
            if (string.startsWith("@@")) {
                string = string.substring(2);
            } else if (string.startsWith("@")) {
                string = string.substring(1);
            }
            if (string.endsWith(".D")) {
                string = string.substring(0, string.length() - 2);
            }
            if (!BR_SYMBOLS.contains(string)) continue;
            linkedList.add(tickerDto);
        }
        return linkedList;
    }

    @Override
    public TickerDto getTicker(Long l) throws SQLException {
        TickerDto tickerDto;
        if (MainApp.isBrazilianEdition() && (tickerDto = this.getTicker(SQL_GET_ALL_BR_TICKERS, l)) != null) {
            return tickerDto;
        }
        return super.getTicker(l);
    }

    @Override
    public TickerDto getTicker(String string) throws SQLException {
        TickerDto tickerDto;
        if (MainApp.isBrazilianEdition() && (tickerDto = this.getTicker(SQL_GET_ALL_BR_TICKERS, string)) != null) {
            return tickerDto;
        }
        return super.getTicker(string);
    }

    @Override
    protected void modifyTickers(List<TickerDto> list, Map<String, String> map) throws SQLException {
        if (list.isEmpty()) {
            return;
        }
        Set<Long> set = list.stream().map(TickerDto::getCommodityId).collect(Collectors.toSet());
        List<CommodityDto> list2 = this.getCommodities(set);
        Map<Long, String> map2 = list2.stream().collect(Collectors.toMap(CommodityDto::getId, CommodityDto::getCode));
        Map<Long, String> map3 = list2.stream().collect(Collectors.toMap(CommodityDto::getId, CommodityDto::getName));
        for (TickerDto tickerDto : list) {
            String string;
            if (tickerDto.getName() == null && tickerDto.getCommodityId() != null) {
                string = map3.get(tickerDto.getCommodityId());
                tickerDto.setName(string);
            }
            if (MainApp.isBrazilianEdition()) {
                string = tickerDto.getName();
                String string2 = tickerDto.getTicker();
                string = string2.endsWith("_D1") ? string + " - Diario" : string + " - 1 Minuto";
                tickerDto.setName(string);
                continue;
            }
            this.updateFundamentalName(tickerDto);
            this.updateNameByTimeframe(tickerDto);
            this.updateAliases(tickerDto, map, map2);
        }
    }

    private void updateAliases(TickerDto tickerDto, Map<String, String> map, Map<Long, String> map2) {
        String string = map2.get(tickerDto.getCommodityId());
        String string2 = map.get(string);
        if (string2 != null) {
            tickerDto.setName(tickerDto.getName() + " (" + string2 + ")");
        }
    }

    @Override
    protected void appendTickersSql(StringBuilder stringBuilder, TickerFilterDto tickerFilterDto) {
        super.appendTickersSql(stringBuilder, tickerFilterDto);
        if (tickerFilterDto.isOnlyContFutures()) {
            stringBuilder.append("AND t.ticker like '@%' ");
        }
    }

    private void updateFundamentalName(TickerDto tickerDto) {
        if (tickerDto.getTicker().startsWith("@")) {
            return;
        }
        int n = tickerDto.getTicker().length();
        String string = tickerDto.isEod() ? Character.toString(tickerDto.getTicker().charAt(n - 5)) : Character.toString(tickerDto.getTicker().charAt(n - 3));
        String string2 = MONTH_LETTERS.get(string);
        if (string2 != null && tickerDto.getName() != null) {
            try {
                String string3 = tickerDto.isEod() ? tickerDto.getTicker().substring(n - 4, n - 2) : tickerDto.getTicker().substring(n - 2, n);
                String string4 = tickerDto.getName() + " [" + string2 + string3 + "]";
                tickerDto.setName(string4);
            }
            catch (Exception exception) {
                // empty catch block
            }
        }
    }

    public CommodityDto getCommodityForFuture(String string) throws SQLException {
        try (Connection connection = this.getConnection();){
            CommodityDto commodityDto;
            block16: {
                PreparedStatement preparedStatement;
                block14: {
                    CommodityDto commodityDto2;
                    block15: {
                        preparedStatement = connection.prepareStatement("select c.id,c.name,c.code,c.point_value,c.tick_step,c.tick_Size,c.order_size_multi from ticker t join commodity c on c.id=t.commodity_id where t.ticker=?");
                        try {
                            preparedStatement.setString(1, string);
                            ResultSet resultSet = preparedStatement.executeQuery();
                            if (!resultSet.next()) break block14;
                            commodityDto2 = this.getCommodity(resultSet);
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
                    return commodityDto2;
                }
                commodityDto = null;
                if (preparedStatement == null) break block16;
                preparedStatement.close();
            }
            return commodityDto;
        }
    }

    private CommodityDto getCommodity(ResultSet resultSet) throws SQLException {
        CommodityDto commodityDto = new CommodityDto();
        commodityDto.setId(resultSet.getLong("id"));
        commodityDto.setName(resultSet.getString("name"));
        commodityDto.setCode(resultSet.getString("code"));
        commodityDto.setPointValue(resultSet.getBigDecimal("point_value"));
        commodityDto.setTickStep(resultSet.getBigDecimal("tick_step"));
        commodityDto.setTickSize(resultSet.getBigDecimal("tick_size"));
        commodityDto.setOrderSizeMulti(resultSet.getBigDecimal("order_size_multi"));
        commodityDto.setOrderSizeStep(resultSet.getBigDecimal("order_size_step"));
        return commodityDto;
    }

    public List<CommodityDto> getCommoditiesForFutures(String[] stringArray) throws SQLException {
        LinkedList<CommodityDto> linkedList;
        block22: {
            linkedList = new LinkedList<CommodityDto>();
            if (stringArray.length == 0) {
                return linkedList;
            }
            try (Connection connection = this.getConnection();){
                ResultSet resultSet;
                String string;
                try (Statement statement = connection.createStatement();){
                    string = this.getCommodityStatement("ticker", stringArray);
                    resultSet = statement.executeQuery(string);
                    while (resultSet.next()) {
                        linkedList.add(this.getCommodity(resultSet));
                    }
                }
                if (!MainApp.isBrazilianEdition()) break block22;
                statement = connection.createStatement();
                try {
                    string = this.getCommodityStatement("br_ticker", stringArray);
                    resultSet = statement.executeQuery(string);
                    while (resultSet.next()) {
                        linkedList.add(this.getCommodity(resultSet));
                    }
                }
                finally {
                    if (statement != null) {
                        statement.close();
                    }
                }
            }
        }
        return linkedList;
    }

    public List<CommodityDto> getCommodities(Set<Long> set) throws SQLException {
        LinkedList<CommodityDto> linkedList = new LinkedList<CommodityDto>();
        if (set.isEmpty()) {
            return linkedList;
        }
        try (Connection connection = this.getConnection();){
            LinkedList<CommodityDto> linkedList2;
            block14: {
                Statement statement = connection.createStatement();
                try {
                    String string = this.getCommodityStatement(set);
                    ResultSet resultSet = statement.executeQuery(string);
                    while (resultSet.next()) {
                        linkedList.add(this.getCommodity(resultSet));
                    }
                    linkedList2 = linkedList;
                    if (statement == null) break block14;
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
            return linkedList2;
        }
    }

    private String getCommodityStatement(Set<Long> set) throws SQLException {
        StringBuilder stringBuilder = new StringBuilder();
        stringBuilder.append("select c.id,c.name,c.code,c.point_value,c.tick_step,c.tick_Size,c.order_size_multi,c.order_size_step from commodity c where c.id in (");
        int n = 0;
        for (Long l : set) {
            stringBuilder.append("'" + l + "'");
            if (n != set.size() - 1) {
                stringBuilder.append(",");
            }
            ++n;
        }
        stringBuilder.append(")");
        return stringBuilder.toString();
    }

    private String getCommodityStatement(String string, String[] stringArray) throws SQLException {
        StringBuilder stringBuilder = new StringBuilder();
        stringBuilder.append("select c.id,c.name,c.code,c.point_value,c.tick_step,c.tick_Size,c.order_size_multi,c.order_size_step from commodity c where c.id in (select t.commodity_id from " + string + " t where commodity_id is not null and t.ticker in (");
        for (int i = 0; i < stringArray.length; ++i) {
            stringBuilder.append("'" + stringArray[i] + "'");
            if (i == stringArray.length - 1) continue;
            stringBuilder.append(",");
        }
        stringBuilder.append("))");
        return stringBuilder.toString();
    }

    static {
        MONTH_LETTERS.put("F", "Jan");
        MONTH_LETTERS.put("G", "Feb");
        MONTH_LETTERS.put("H", "Mar");
        MONTH_LETTERS.put("J", "Apr");
        MONTH_LETTERS.put("K", "May");
        MONTH_LETTERS.put("M", "Jun");
        MONTH_LETTERS.put("N", "Jul");
        MONTH_LETTERS.put("Q", "Aug");
        MONTH_LETTERS.put("U", "Sep");
        MONTH_LETTERS.put("V", "Oct");
        MONTH_LETTERS.put("X", "Nov");
        MONTH_LETTERS.put("Z", "Dec");
        BR_SYMBOLS.add("WDO");
        BR_SYMBOLS.add("WIN");
        BR_SYMBOLS.add("DOL");
        BR_SYMBOLS.add("IND");
        BR_SYMBOLS.add("DI1");
        BR_SYMBOLS.add("CCM");
        BR_SYMBOLS.add("BGI");
    }
}

