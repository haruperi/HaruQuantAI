/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  com.strategyquant.datalib.TradingException
 *  com.strategyquant.lib.SettingsMap
 *  it.unimi.dsi.fastutil.ints.Int2IntOpenHashMap
 *  it.unimi.dsi.fastutil.ints.IntArraySet
 *  it.unimi.dsi.fastutil.ints.IntSet
 *  org.jdom2.Element
 */
package com.strategyquant.tradinglib.talib;

import com.strategyquant.datalib.TradingException;
import com.strategyquant.lib.SettingsMap;
import com.strategyquant.tradinglib.BlockDefinitionException;
import com.strategyquant.tradinglib.IBlock;
import com.strategyquant.tradinglib.ReturnTypes;
import com.strategyquant.tradinglib.StrategyBase;
import com.strategyquant.tradinglib.Variable;
import com.strategyquant.tradinglib.engine.stockpicker.backtester.BacktestData;
import com.strategyquant.tradinglib.talib.TALibBlocks;
import com.strategyquant.tradinglib.talib.TALibIndicators;
import it.unimi.dsi.fastutil.ints.Int2IntOpenHashMap;
import it.unimi.dsi.fastutil.ints.IntArraySet;
import it.unimi.dsi.fastutil.ints.IntSet;
import java.util.List;
import java.util.Map;
import org.jdom2.Element;

public class TALibIndicator
implements IBlock {
    public StrategyBase Strategy = null;
    private Int2IntOpenHashMap customData = null;
    private int returnType = 0;
    private String name;
    private SettingsMap params;
    private String[] paramsKeys;
    private IntSet periodParams;
    private int chartIndex;
    boolean paramsPrepared = false;
    private int paramShift = -1;
    private int paramLine = 0;
    private String paramLineName = null;
    private int paramLongestPeriod = -1;
    private int paramChartIndex = -1;
    private int paramComputedFrom = -1;

    @Override
    public double evaluateBlock() throws TradingException {
        float[][] fArray;
        int n;
        int n2;
        if (this.params == null) {
            throw new TradingException("First parseXml() must be called.");
        }
        if (!this.paramsPrepared) {
            this.prepareParams();
        }
        BacktestData backtestData = this.Strategy.Stockpicker.data;
        String string = backtestData.getSymbol(this.chartIndex);
        String string2 = backtestData.getChartTimeframe(this.paramChartIndex);
        double d = 0.0;
        int n3 = this.getCurrentIndex();
        if (this.paramLongestPeriod > 0 && (n2 = n3 - this.paramLongestPeriod) < (n = this.Strategy.Stockpicker.data.getChartSymbolData(this.paramChartIndex, string).getRealDataIndexStart(string2))) {
            throw new TradingException(String.format("Not enough data to calculate %s indicator value.", this.name), 55);
        }
        n = this.paramShift;
        if (this.Strategy.Stockpicker.strategyTriggeredAt() == 5 && n == 0 && (TALibIndicators.isHlcIndicator(this.name) || this.paramComputedFrom != -1 && this.paramComputedFrom != 1)) {
            n = 1;
            this.Strategy.setStrategyProblem(2048);
        }
        if ((fArray = this.Strategy.Stockpicker.TALibIndicators.calculate(string, this.name, this.params, this.Strategy, this.paramChartIndex, n, this.paramComputedFrom, this.paramLine, this.paramLineName)) != null) {
            n2 = n3 - n;
            d = fArray[this.paramLine][n2];
        }
        if (this.returnType == 3) {
            return d == 0.0 ? 0.0 : 1.0;
        }
        return d;
    }

    @Override
    public double evaluateBlock(int n) throws TradingException {
        float[][] fArray;
        int n2;
        int n3;
        if (this.params == null) {
            throw new TradingException("First parseXml() must be called.");
        }
        if (!this.paramsPrepared) {
            this.prepareParams();
        }
        BacktestData backtestData = this.Strategy.Stockpicker.data;
        String string = backtestData.getSymbol(this.chartIndex);
        String string2 = backtestData.getChartTimeframe(this.paramChartIndex);
        double d = 0.0;
        int n4 = this.getCurrentIndex();
        if (this.paramLongestPeriod > 0 && (n3 = n4 - n - this.paramLongestPeriod) < (n2 = this.Strategy.Stockpicker.data.getChartSymbolData(this.paramChartIndex, string).getRealDataIndexStart(string2))) {
            throw new TradingException(String.format("Not enough data to calculate %s indicator value.", this.name), 55);
        }
        n2 = this.paramShift;
        if (this.Strategy.Stockpicker.strategyTriggeredAt() == 5 && n2 == 0 && (TALibIndicators.isHlcIndicator(this.name) || this.paramComputedFrom != -1 && this.paramComputedFrom != 1)) {
            n2 = 1;
            this.Strategy.setStrategyProblem(2048);
        }
        if ((fArray = this.Strategy.Stockpicker.TALibIndicators.calculate(string, this.name, this.params, this.Strategy, this.paramChartIndex, n2, this.paramComputedFrom, this.paramLine, this.paramLineName)) != null) {
            n3 = n4 - n - n2;
            d = fArray[this.paramLine][n3];
        }
        if (this.returnType == 3) {
            return d == 0.0 ? 0.0 : 1.0;
        }
        return d;
    }

    private void prepareParams() throws TradingException {
        this.paramLine = this.params.getInt("Line");
        this.paramLineName = this.params.getString("LineName", "Value");
        this.paramShift = this.params.getInt("Shift");
        this.paramChartIndex = this.params.getInt("Chart");
        this.paramComputedFrom = this.params.getInt("ComputedFrom", -1);
        this.paramLongestPeriod = -1;
        for (int i = 0; i < this.paramsKeys.length; ++i) {
            int n;
            String string = this.paramsKeys[i];
            if (!this.periodParams.contains(string.hashCode()) || (n = this.params.getInt(string)) <= this.paramLongestPeriod) continue;
            this.paramLongestPeriod = n;
        }
        this.paramsPrepared = true;
    }

    private int getCurrentIndex() {
        return this.Strategy.Stockpicker.getCurrentBar(this.chartIndex);
    }

    @Override
    public IBlock newInstance(StrategyBase strategyBase, Element element) throws BlockDefinitionException {
        IBlock iBlock = this.clone(true, strategyBase);
        this.parseXml(element);
        return iBlock;
    }

    private void parseXml(Element element) throws BlockDefinitionException {
        if (!element.getName().equals("Item") && !element.getName().equals("Formula")) {
            throw new BlockDefinitionException("@Parameter must be used only on Item or Formula node!");
        }
        this.params = new SettingsMap();
        this.periodParams = new IntArraySet();
        this.name = element.getAttributeValue("key");
        this.name = this.name.replaceFirst("talib_", "");
        String string = element.getAttributeValue("returnType");
        this.returnType = ReturnTypes.translate(string);
        List list = element.getChildren();
        for (int i = 0; i < list.size(); ++i) {
            int n;
            Variable variable;
            Element element2 = (Element)list.get(i);
            String string2 = element2.getAttributeValue("type");
            String string3 = element2.getValue();
            String string4 = element2.getAttributeValue("key");
            string4 = string4.replace("#", "");
            String string5 = element2.getAttributeValue("variable");
            if (string5 != null && string5.equals("true") && (variable = this.Strategy.variables().getById(string3)) != null) {
                string3 = variable.getValue();
            }
            boolean bl = TALibIndicators.isPeriod(string4);
            if (string2.equals("int") || string2.equals("data") || string2.equals("period")) {
                n = Integer.parseInt(string3);
                if (bl && n < 2) {
                    n = 2;
                }
                this.params.set(string4, (Object)n);
            } else if (string2.equals("long")) {
                this.params.set(string4, (Object)Long.parseLong(string3));
            } else if (string2.equals("double")) {
                this.params.set(string4, (Object)Double.parseDouble(string3));
            } else if (string2.equals("boolean")) {
                this.params.set(string4, (Object)Boolean.parseBoolean(string3));
            } else if (string2.equals("java.lang.String")) {
                this.params.set(string4, (Object)string3);
            }
            if (bl || string4.equals("Shift")) {
                this.periodParams.add(string4.hashCode());
            }
            if (!string4.equals("Line")) continue;
            n = Integer.parseInt(string3);
            String string6 = element2.getAttributeValue("values");
            if (string6 == null) continue;
            String[] stringArray = string6.split(",");
            String string7 = stringArray[n].split("=")[0].trim();
            this.params.set("LineName", (Object)string7);
        }
        this.paramsKeys = this.params.getAllKeys();
        this.chartIndex = this.params.getInt("Chart");
    }

    @Override
    public StrategyBase getStrategy() {
        return this.Strategy;
    }

    @Override
    public IBlock clone(boolean bl, StrategyBase strategyBase) throws BlockDefinitionException {
        this.Strategy = strategyBase;
        return this;
    }

    @Override
    public void setCustomData(String string, int n) {
        if (this.customData == null) {
            this.customData = new Int2IntOpenHashMap();
        }
        this.customData.put(string.hashCode(), n);
    }

    @Override
    public int getCustomData(String string) {
        if (this.customData == null || !this.customData.containsKey(string.hashCode())) {
            return Integer.MIN_VALUE;
        }
        return this.customData.get(string.hashCode());
    }

    @Override
    public void copyCustomData(IBlock iBlock) {
        if (iBlock instanceof TALibIndicator) {
            TALibIndicator tALibIndicator = (TALibIndicator)iBlock;
            if (tALibIndicator.customData != null) {
                if (this.customData == null) {
                    this.customData = new Int2IntOpenHashMap();
                }
                this.customData.putAll((Map)tALibIndicator.customData);
            }
        }
    }

    @Override
    public int getReturnType() {
        return this.returnType;
    }

    @Override
    public void setReturnType(int n) {
        this.returnType = n;
    }

    @Override
    public Element getCustomBlockXml(int n) throws BlockDefinitionException {
        throw new BlockDefinitionException("Not implemented for this!");
    }

    public void copyFrom(TALibIndicator tALibIndicator) {
        this.name = tALibIndicator.name;
        this.returnType = tALibIndicator.returnType;
        this.params = tALibIndicator.params.clone();
        this.copyCustomData(tALibIndicator);
    }

    public Element getBlockXml() throws BlockDefinitionException {
        Element element = TALibBlocks.getBlock("talib_" + this.name);
        element = element.clone();
        List list = element.getChildren("Param");
        for (int i = 0; i < list.size(); ++i) {
            String string;
            Element element2 = (Element)list.get(i);
            String string2 = element2.getAttributeValue("type");
            String string3 = element2.getAttributeValue("key");
            if (!this.params.containsKey(string3 = string3.replace("#", ""))) {
                throw new BlockDefinitionException("Param '" + string3 + "' not found in block '" + this.name + "'");
            }
            if (string2.equals("int") || string2.equals("data") || string2.equals("period")) {
                string = Integer.toString(this.params.getInt(string3));
            } else if (string2.equals("long")) {
                string = Long.toString(this.params.getLong(string3));
            } else if (string2.equals("double")) {
                string = Double.toString(this.params.getDouble(string3));
            } else if (string2.equals("boolean")) {
                string = Boolean.toString(this.params.getBoolean(string3));
            } else if (string2.equals("java.lang.String")) {
                string = this.params.getString(string3);
            } else {
                throw new BlockDefinitionException("Param '" + string3 + "' in block '" + this.name + "' has unknown type: '" + string2 + "'");
            }
            element2.setText(string);
        }
        return element;
    }
}

