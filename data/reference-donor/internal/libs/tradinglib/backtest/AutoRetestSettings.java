/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  com.strategyquant.datalib.consts.Precisions
 *  com.strategyquant.datalib.data.DataManager
 *  com.strategyquant.lib.L
 *  com.strategyquant.lib.SQTime
 *  com.strategyquant.lib.XMLUtil
 *  org.jdom2.Element
 */
package com.strategyquant.tradinglib.backtest;

import com.strategyquant.datalib.consts.Precisions;
import com.strategyquant.datalib.data.DataManager;
import com.strategyquant.lib.L;
import com.strategyquant.lib.SQTime;
import com.strategyquant.lib.XMLUtil;
import com.strategyquant.tradinglib.CommissionsMethod;
import com.strategyquant.tradinglib.SwapMethod;
import com.strategyquant.tradinglib.project.ProjectConfigHelper;
import com.strategyquant.tradinglib.simulator.Engines;
import java.io.Serializable;
import java.util.ArrayList;
import java.util.List;
import org.jdom2.Element;

public class AutoRetestSettings
implements Serializable {
    private boolean useCustomEngine = false;
    private boolean useCustomSymbol = false;
    private boolean useCustomTimeframe = false;
    private boolean useCustomDates = false;
    private boolean useCustomSubCharts = false;
    private boolean useCustomPrecision = false;
    private boolean useCustomMinDistance = false;
    private boolean useCustomSpread = false;
    private boolean useCustomSwap = false;
    private boolean useCustomSlippage = false;
    private boolean useCustomCommissions = false;
    private boolean useCustomMoneyManagement = false;
    private boolean useCustomTradingOptions = false;
    private String engine;
    private String symbol;
    private String timeframe;
    private String dateFrom;
    private String dateTo;
    private int precision = 0;
    private double spread = 0.0;
    private double slippage = 0.0;
    private double minDistance = 0.0;
    private CommissionsMethod commissions = null;
    private SwapMethod swap = null;
    private ArrayList<Subchart> subcharts = new ArrayList();

    public void init(Element element) throws Exception {
        Element element2;
        Element element3;
        Element element4 = XMLUtil.getChildElem((Element)element, (String)"CustomData");
        Element element5 = XMLUtil.getChildElem((Element)element4, (String)"Setups");
        Element element6 = XMLUtil.getChildElem((Element)element5, (String)"Setup");
        List list = element6.getChildren("Chart");
        Element element7 = (Element)list.get(0);
        Element element8 = XMLUtil.getChildElem((Element)element6, (String)"MainTestValues");
        this.useCustomEngine = !XMLUtil.getBooleanAttr((Element)element8, (String)"engine", (boolean)true);
        this.useCustomSymbol = !XMLUtil.getBooleanAttr((Element)element8, (String)"symbol", (boolean)true);
        this.useCustomTimeframe = !XMLUtil.getBooleanAttr((Element)element8, (String)"timeframe", (boolean)true);
        this.useCustomDates = !XMLUtil.getBooleanAttr((Element)element8, (String)"dates", (boolean)true);
        this.useCustomSubCharts = !XMLUtil.getBooleanAttr((Element)element8, (String)"subcharts", (boolean)true);
        this.useCustomPrecision = !XMLUtil.getBooleanAttr((Element)element8, (String)"precision", (boolean)true);
        String string = XMLUtil.getStringAttr((Element)element8, (String)"spread", (String)"strategy");
        String string2 = XMLUtil.getStringAttr((Element)element8, (String)"distance", (String)"strategy");
        String string3 = XMLUtil.getStringAttr((Element)element8, (String)"commissions", (String)"strategy");
        String string4 = XMLUtil.getStringAttr((Element)element8, (String)"slippage", (String)"strategy");
        String string5 = XMLUtil.getStringAttr((Element)element8, (String)"swap", (String)"strategy");
        this.useCustomSpread = string.equals("false") || string.equals("custom") || string.equals("instrument");
        this.useCustomMinDistance = string2.equals("false") || string2.equals("custom") || string2.equals("instrument");
        this.useCustomCommissions = string3.equals("false") || string3.equals("custom") || string3.equals("instrument");
        this.useCustomSlippage = string4.equals("false") || string4.equals("custom") || string4.equals("instrument");
        boolean bl = this.useCustomSwap = string5.equals("false") || string5.equals("custom") || string5.equals("instrument");
        if (this.useCustomSymbol) {
            try {
                this.symbol = element7.getAttributeValue("symbol");
                if (this.symbol == null) {
                    throw new Exception(L.t((String)"Main chart symbol not set", (Object[])new Object[0]));
                }
            }
            catch (Exception exception) {
                throw new Exception(L.t((String)"Cannot load main chart settings - %s", (Object[])new Object[]{exception.getMessage()}));
            }
        }
        for (int i = 1; i < list.size(); ++i) {
            element3 = (Element)list.get(i);
            try {
                String string6 = element3.getAttributeValue("symbol");
                if (string6 == null) {
                    throw new Exception(L.t((String)"Subchart #%d symbol not set", (Object[])new Object[]{i}));
                }
                DataManager.getDataInfo((String)"History", (String)string6);
                String string7 = element3.getAttributeValue("timeframe");
                if (string7 == null) {
                    throw new Exception(L.t((String)"Subchart #%d timeframe not set", (Object[])new Object[]{i}));
                }
                this.subcharts.add(new Subchart(string6, string7));
                continue;
            }
            catch (Exception exception) {
                throw new Exception(L.t((String)"Cannot load subchart settings - %s", (Object[])new Object[]{exception.getMessage()}));
            }
        }
        if (this.useCustomEngine) {
            try {
                this.engine = element6.getAttributeValue("engine");
                Engines.getEngine(this.engine);
            }
            catch (Exception exception) {
                throw new Exception(L.t((String)"Cannot get engine - %s", (Object[])new Object[]{exception.getMessage()}));
            }
        }
        if (this.useCustomTimeframe) {
            try {
                this.timeframe = element7.getAttributeValue("timeframe");
            }
            catch (Exception exception) {
                throw new Exception(L.t((String)"Cannot get timeframe - %s", (Object[])new Object[]{exception.getMessage()}));
            }
        }
        if (this.useCustomDates) {
            this.dateFrom = element6.getAttributeValue("dateFrom", "");
            this.dateTo = element6.getAttributeValue("dateTo", "");
            if (this.dateFrom.isEmpty() || this.dateTo.isEmpty()) {
                throw new Exception(L.t((String)"Backtest dates not set", (Object[])new Object[0]));
            }
            try {
                SQTime.parseDateToMilis((String)this.dateFrom);
                SQTime.parseDateToMilis((String)this.dateTo);
            }
            catch (Exception exception) {
                throw new Exception(L.t((String)"Cannot parse backtest dates - %s", (Object[])new Object[]{exception.getMessage()}));
            }
        }
        if (this.useCustomPrecision) {
            try {
                this.precision = Precisions.getPrecision((int)Integer.parseInt(element6.getAttributeValue("testPrecision", "-1")));
            }
            catch (Exception exception) {
                throw new Exception(L.t((String)"Cannot get test precision - %s", (Object[])new Object[]{exception.getMessage()}));
            }
        }
        if (this.useCustomMinDistance) {
            try {
                this.minDistance = Double.parseDouble(element6.getAttributeValue("minDist", "-1"));
                if (this.minDistance < 0.0) {
                    throw new Exception("Min. distance not set");
                }
            }
            catch (Exception exception) {
                throw new Exception(L.t((String)"Cannot get min. distance - %s", (Object[])new Object[]{exception.getMessage()}));
            }
        }
        if (this.useCustomSpread) {
            try {
                this.spread = Double.parseDouble(element7.getAttributeValue("spread", "-1"));
                if (this.spread < 0.0) {
                    throw new Exception(L.t((String)"Spread not set", (Object[])new Object[0]));
                }
            }
            catch (Exception exception) {
                throw new Exception(L.t((String)"Cannot get spread - %s", (Object[])new Object[]{exception.getMessage()}));
            }
        }
        if (this.useCustomSlippage) {
            try {
                this.slippage = Double.parseDouble(element6.getAttributeValue("slippage", "-1"));
                if (this.slippage < 0.0) {
                    throw new Exception(L.t((String)"Slippage not set", (Object[])new Object[0]));
                }
            }
            catch (Exception exception) {
                throw new Exception(L.t((String)"Cannot get slippage - %s", (Object[])new Object[]{exception.getMessage()}));
            }
        }
        if (this.useCustomCommissions) {
            try {
                this.commissions = ProjectConfigHelper.getCommissionsMethod(element6);
            }
            catch (Exception exception) {
                throw new Exception(L.t((String)"Cannot get commissions settings - %s", (Object[])new Object[]{exception.getMessage()}));
            }
        }
        if (this.useCustomSwap) {
            try {
                this.swap = ProjectConfigHelper.getSwapMethod(element6);
            }
            catch (Exception exception) {
                throw new Exception(L.t((String)"Cannot get swap settings - %s", (Object[])new Object[]{exception.getMessage()}));
            }
        }
        this.useCustomMoneyManagement = (element2 = element.getChild("RiskMoneyManagement")) == null ? false : XMLUtil.getBooleanAttr((Element)element2, (String)"customSettings", (boolean)false);
        element3 = element.getChild("Options");
        this.useCustomTradingOptions = element3 == null ? false : XMLUtil.getBooleanAttr((Element)element3, (String)"customSettings", (boolean)false);
    }

    public boolean useCustomEngine() {
        return this.useCustomEngine;
    }

    public boolean useCustomSymbol() {
        return this.useCustomSymbol;
    }

    public boolean useCustomTimeframe() {
        return this.useCustomTimeframe;
    }

    public boolean useCustomDates() {
        return this.useCustomDates;
    }

    public boolean useCustomSubCharts() {
        return this.useCustomSubCharts;
    }

    public boolean useCustomPrecision() {
        return this.useCustomPrecision;
    }

    public boolean useCustomMinDistance() {
        return this.useCustomMinDistance;
    }

    public boolean useCustomSwap() {
        return this.useCustomSwap;
    }

    public boolean useCustomSpread() {
        return this.useCustomSpread;
    }

    public boolean useCustomSlippage() {
        return this.useCustomSlippage;
    }

    public boolean useCustomCommissions() {
        return this.useCustomCommissions;
    }

    public String getEngine() {
        return this.engine;
    }

    public String getSymbol() {
        return this.symbol;
    }

    public String getTimeframe() {
        return this.timeframe;
    }

    public String getDateFrom() {
        return this.dateFrom;
    }

    public String getDateTo() {
        return this.dateTo;
    }

    public int getPrecision() {
        return this.precision;
    }

    public double getSpread() {
        return this.spread;
    }

    public double getSlippage() {
        return this.slippage;
    }

    public double getMinDistance() {
        return this.minDistance;
    }

    public CommissionsMethod getCommissions() {
        return this.commissions;
    }

    public SwapMethod getSwap() {
        return this.swap;
    }

    public boolean useCustomMoneyManagement() {
        return this.useCustomMoneyManagement;
    }

    public boolean useCustomTradingOptions() {
        return this.useCustomTradingOptions;
    }

    public ArrayList<Subchart> getSubcharts() {
        return this.subcharts;
    }

    public class Subchart {
        public String symbol;
        public String timeframe;

        public Subchart(String string, String string2) {
            this.symbol = string;
            this.timeframe = string2;
        }
    }
}

