/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  com.strategyquant.gridlib.client.GridJob
 *  com.strategyquant.gridlib.client.GridMessage
 *  com.strategyquant.lib.SQUtils
 *  com.strategyquant.lib.XMLUtil
 *  org.jdom2.Element
 *  org.slf4j.Logger
 *  org.slf4j.LoggerFactory
 */
package com.strategyquant.tradinglib.backtest;

import com.strategyquant.gridlib.client.GridJob;
import com.strategyquant.gridlib.client.GridMessage;
import com.strategyquant.lib.SQUtils;
import com.strategyquant.lib.XMLUtil;
import com.strategyquant.tradinglib.ResultsGroup;
import com.strategyquant.tradinglib.backtest.AWProgressEngine;
import com.strategyquant.tradinglib.backtest.BacktestDataInitializer;
import com.strategyquant.tradinglib.backtest.LoadDataProgressEngine;
import com.strategyquant.tradinglib.backtestrunner.BacktestResult;
import com.strategyquant.tradinglib.backtestrunner.BacktestRunner;
import com.strategyquant.tradinglib.backtestrunner.BacktestSettings;
import com.strategyquant.tradinglib.project.ILastEventListener;
import com.strategyquant.tradinglib.results.SpecialValues;
import java.io.Serializable;
import java.util.ArrayList;
import java.util.Map;
import org.jdom2.Element;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

public class SQBacktesterJob
extends GridJob<BacktestResult> {
    public static final Logger Log = LoggerFactory.getLogger((String)"SQBacktesterJob");
    private BacktestRunner backtestRunner;
    private AWProgressEngine progressEngine;
    private BacktestDataInitializer bdi;
    private String strategyName;
    private Element settingsXML;
    private ILastEventListener lastEventListener;

    public SQBacktesterJob(String string, Map<String, Serializable> map, ILastEventListener iLastEventListener) throws Exception {
        super(string, 1, map);
        this.lastEventListener = iLastEventListener;
        if (this.lastEventListener == null) {
            this.lastEventListener = new ILastEventListener(){

                @Override
                public void setLastEvent(String string) {
                }
            };
        }
        this.progressEngine = new AWProgressEngine();
        this.bdi = new BacktestDataInitializer(new LoadDataProgressEngine(this.progressEngine), (ArrayList)map.get("ChartSetups"), false, null, iLastEventListener);
        this.backtestRunner = new BacktestRunner(new BacktestSettings(map), this.progressEngine, this, false, this.lastEventListener, null);
        this.strategyName = (String)((Object)map.get("StrategyName"));
        this.settingsXML = (Element)map.get("StrategyLastSettings");
    }

    public BacktestResult call() throws Exception {
        try {
            this.progressEngine.start();
            long l = this.bdi.prepareData();
            BacktestResult backtestResult = this.backtestRunner.execute();
            ResultsGroup resultsGroup = backtestResult.getResult();
            if (resultsGroup != null) {
                resultsGroup.setLastSettings(XMLUtil.elementToString((Element)this.settingsXML));
                resultsGroup.specialValues().set(SpecialValues.LoadDataDuration, (Object)SQUtils.round((double)((double)l / 1000.0), (int)2));
            }
            return backtestResult;
        }
        catch (Exception exception) {
            Log.error("Backtesting strategy '" + this.strategyName + "' failed");
            throw exception;
        }
    }

    public void messageReceived(GridMessage gridMessage) {
        if (gridMessage.getMessageID() == 5 && gridMessage.getCustomID() != null && gridMessage.getCustomID().equals("StopBacktest")) {
            this.progressEngine.stop();
            this.backtestRunner.stop();
        }
    }
}

