/*
 * Decompiled with CFR 0.152.
 */
package com.strategyquant.datalib.historyData.dto;

import java.math.BigDecimal;

public class CommodityDto {
    private Long id;
    private String code;
    private String name;
    private BigDecimal commision;
    private BigDecimal defaultSpread;
    private BigDecimal pointValue;
    private BigDecimal tickStep;
    private BigDecimal tickSize;
    private BigDecimal orderSizeMulti;
    private BigDecimal orderSizeStep;

    public Long getId() {
        return this.id;
    }

    public void setId(Long l) {
        this.id = l;
    }

    public String getCode() {
        return this.code;
    }

    public void setCode(String string) {
        this.code = string;
    }

    public BigDecimal getCommision() {
        return this.commision;
    }

    public void setCommision(BigDecimal bigDecimal) {
        this.commision = bigDecimal;
    }

    public BigDecimal getDefaultSpread() {
        return this.defaultSpread;
    }

    public void setDefaultSpread(BigDecimal bigDecimal) {
        this.defaultSpread = bigDecimal;
    }

    public BigDecimal getPointValue() {
        return this.pointValue;
    }

    public void setPointValue(BigDecimal bigDecimal) {
        this.pointValue = bigDecimal;
    }

    public BigDecimal getTickStep() {
        return this.tickStep;
    }

    public void setTickStep(BigDecimal bigDecimal) {
        this.tickStep = bigDecimal;
    }

    public BigDecimal getTickSize() {
        return this.tickSize;
    }

    public void setTickSize(BigDecimal bigDecimal) {
        this.tickSize = bigDecimal;
    }

    public String getName() {
        return this.name;
    }

    public void setName(String string) {
        this.name = string;
    }

    public BigDecimal getOrderSizeMulti() {
        return this.orderSizeMulti;
    }

    public void setOrderSizeMulti(BigDecimal bigDecimal) {
        this.orderSizeMulti = bigDecimal;
    }

    public BigDecimal getOrderSizeStep() {
        return this.orderSizeStep;
    }

    public void setOrderSizeStep(BigDecimal bigDecimal) {
        this.orderSizeStep = bigDecimal;
    }
}

