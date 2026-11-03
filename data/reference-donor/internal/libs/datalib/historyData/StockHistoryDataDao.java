/*
 * Decompiled with CFR 0.152.
 */
package com.strategyquant.datalib.historyData;

import com.strategyquant.datalib.historyData.AbstractHistoryDataDao;
import com.strategyquant.datalib.historyData.TickerRenameInfo;
import java.io.File;
import java.sql.Connection;
import java.sql.PreparedStatement;
import java.sql.ResultSet;
import java.util.Comparator;
import java.util.HashMap;
import java.util.LinkedList;
import java.util.List;
import java.util.Map;

public class StockHistoryDataDao
extends AbstractHistoryDataDao {
    public StockHistoryDataDao(String string) {
        super("sq", "hE8+-%:b&]^c#[b#j;+=*R[N~hrtbn$", string + File.separator + "data_stock");
    }

    public Map<String, List<TickerRenameInfo>> getTickerRenamed() {
        HashMap<String, List<TickerRenameInfo>> hashMap = new HashMap<String, List<TickerRenameInfo>>();
        try (Connection connection = this.getConnection();
             PreparedStatement preparedStatement = connection.prepareStatement("select ticker_from,ticker_to,change_date from ticker_renamed");){
            ResultSet resultSet = preparedStatement.executeQuery();
            while (resultSet.next()) {
                TickerRenameInfo tickerRenameInfo = new TickerRenameInfo();
                tickerRenameInfo.setDate(resultSet.getDate("change_date").getTime());
                tickerRenameInfo.setTickerFrom(resultSet.getString("ticker_from"));
                tickerRenameInfo.setTickerTo(resultSet.getString("ticker_to"));
                LinkedList<TickerRenameInfo> linkedList = (LinkedList<TickerRenameInfo>)hashMap.get(tickerRenameInfo.getTickerFrom());
                if (linkedList == null) {
                    linkedList = new LinkedList<TickerRenameInfo>();
                    hashMap.put(tickerRenameInfo.getTickerFrom(), linkedList);
                }
                linkedList.add(tickerRenameInfo);
            }
        }
        catch (Exception exception) {
            Log.error("Error while checking change_date value", (Throwable)exception);
        }
        hashMap.values().stream().forEach(list -> list.sort(new Comparator<TickerRenameInfo>(){

            @Override
            public int compare(TickerRenameInfo tickerRenameInfo, TickerRenameInfo tickerRenameInfo2) {
                return tickerRenameInfo.getDate().compareTo(tickerRenameInfo2.getDate());
            }
        }));
        return hashMap;
    }
}

