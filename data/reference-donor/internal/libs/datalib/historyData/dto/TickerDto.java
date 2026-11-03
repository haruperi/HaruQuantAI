/*
 * Decompiled with CFR 0.152.
 */
package com.strategyquant.datalib.historyData.dto;

import java.sql.Date;

public class TickerDto {
    private boolean eod;
    private Long id;
    private String name;
    private String ticker;
    private Long marketId;
    private String marketName;
    private Date dateFrom;
    private Date dateTo;
    private String type;
    private Long commodityId;
    private Long aliasTickerId;

    public Long getId() {
        return this.id;
    }

    public void setId(Long l) {
        this.id = l;
    }

    public String getName() {
        return this.name;
    }

    public void setName(String string) {
        this.name = string;
    }

    public String getTicker() {
        return this.ticker;
    }

    public void setTicker(String string) {
        this.ticker = string;
    }

    public Long getMarketId() {
        return this.marketId;
    }

    public void setMarketId(Long l) {
        this.marketId = l;
    }

    public String getMarketName() {
        return this.marketName;
    }

    public void setMarketName(String string) {
        this.marketName = string;
    }

    public boolean isEod() {
        return this.eod;
    }

    public void setEod(boolean bl) {
        this.eod = bl;
    }

    public Date getDateFrom() {
        return this.dateFrom;
    }

    public void setDateFrom(Date date) {
        this.dateFrom = date;
    }

    public Date getDateTo() {
        return this.dateTo;
    }

    public void setDateTo(Date date) {
        this.dateTo = date;
    }

    public String getType() {
        return this.type;
    }

    public void setType(String string) {
        this.type = string;
    }

    public Long getCommodityId() {
        return this.commodityId;
    }

    public void setCommodityId(Long l) {
        this.commodityId = l;
    }

    public Long getAliasTickerId() {
        return this.aliasTickerId;
    }

    public void setAliasTickerId(Long l) {
        this.aliasTickerId = l;
    }
}

