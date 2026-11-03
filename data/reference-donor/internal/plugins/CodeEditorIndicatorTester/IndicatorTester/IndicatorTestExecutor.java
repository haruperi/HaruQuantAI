/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  com.strategyquant.indicatorTester.IndicatorParameters
 *  com.strategyquant.indicatorTester.IndicatorTestException
 *  com.strategyquant.indicatorTester.IndicatorTester
 *  com.strategyquant.indicatorTester.IndicatorTesterConfig
 *  com.strategyquant.indicatorTester.IndicatorsLoader
 *  com.strategyquant.lib.XMLUtil
 *  com.strategyquant.tradinglib.project.websocket.DataToSend
 *  com.strategyquant.tradinglib.project.websocket.SQWebSocketManager
 *  com.strategyquant.tradinglib.project.websocket.SynchronizedWebSocketPublisher
 *  com.strategyquant.tradinglib.project.websocket.WebSocketPublisher
 *  org.jdom2.Content
 *  org.jdom2.Element
 *  org.json.JSONObject
 *  org.slf4j.Logger
 *  org.slf4j.LoggerFactory
 */
package com.strategyquant.plugin.CodeEditor.impl.IndicatorTester;

import com.strategyquant.indicatorTester.IndicatorParameters;
import com.strategyquant.indicatorTester.IndicatorTestException;
import com.strategyquant.indicatorTester.IndicatorTester;
import com.strategyquant.indicatorTester.IndicatorTesterConfig;
import com.strategyquant.indicatorTester.IndicatorsLoader;
import com.strategyquant.lib.XMLUtil;
import com.strategyquant.tradinglib.project.websocket.DataToSend;
import com.strategyquant.tradinglib.project.websocket.SQWebSocketManager;
import com.strategyquant.tradinglib.project.websocket.SynchronizedWebSocketPublisher;
import com.strategyquant.tradinglib.project.websocket.WebSocketPublisher;
import java.util.ArrayList;
import java.util.List;
import java.util.concurrent.locks.ReentrantLock;
import org.jdom2.Content;
import org.jdom2.Element;
import org.json.JSONObject;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

public class IndicatorTestExecutor
extends SynchronizedWebSocketPublisher {
    private static final Logger Log = LoggerFactory.getLogger(IndicatorTestExecutor.class);
    private List<Element> testConfigs = new ArrayList<Element>();
    private IndicatorTester tester;
    private int testIndex = 0;
    private int runningStatus = 0;
    private boolean shouldStop = false;
    private boolean newUpdate = false;
    private DataToSend info = new DataToSend("IndicatorTesterStatus");
    private JSONObject status = new JSONObject();
    private ReentrantLock lock = new ReentrantLock();
    private static IndicatorTestExecutor instance;

    private IndicatorTestExecutor() {
        instance = this;
        this.info.setDataObject(this.status);
        SQWebSocketManager.getInstance().addAppPublisher("SQEDITOR", (WebSocketPublisher)this);
    }

    public static IndicatorTestExecutor get() {
        return instance == null ? new IndicatorTestExecutor() : instance;
    }

    public void start() throws Exception {
        if (this.tester == null) {
            this.tester = new IndicatorTester();
        }
        if (this.getRunningStatus() == 1) {
            throw new Exception("Tests are already running");
        }
        this.loadTestsConfig();
        new Thread(){

            @Override
            public void run() {
                IndicatorTestExecutor.this.shouldStop = false;
                IndicatorTestExecutor.this.setTestIndex(0);
                IndicatorTestExecutor.this.setRunningStatus(1);
                while (IndicatorTestExecutor.this.getTestIndex() < IndicatorTestExecutor.this.testConfigs.size() && !IndicatorTestExecutor.this.shouldStop) {
                    IndicatorTestExecutor.this.setNewUpdate();
                    IndicatorTestExecutor.this.runNextTest();
                    IndicatorTestExecutor.this.incrementTestIndex();
                }
                IndicatorTestExecutor.this.setRunningStatus(IndicatorTestExecutor.this.shouldStop ? 4 : 3);
                IndicatorTestExecutor.this.setNewUpdate();
            }
        }.start();
    }

    public void stop() {
        this.shouldStop = true;
    }

    private void loadTestsConfig() throws Exception {
        try {
            Element config = IndicatorTesterConfig.getConfig();
            Element elTests = XMLUtil.getChildElem((Element)config, (String)"Tests");
            this.testConfigs.clear();
            for (Element elTest : elTests.getChildren("Test")) {
                if (!XMLUtil.elementIs((Element)elTest, (String)"use")) continue;
                this.testConfigs.add(elTest);
            }
            String engine = config.getChild("Engine").getText();
            String barsToReserve = config.getChild("BarsToReserve").getText();
            this.tester.init(engine);
            this.tester.setStartCompareIndex(Integer.parseInt(barsToReserve));
        }
        catch (Exception e) {
            throw new Exception("Invalid tests config. ", e);
        }
    }

    private void runNextTest() {
        try {
            this.performTest();
            this.testConfigs.get(this.getTestIndex()).setAttribute("result", "Passed");
            this.testConfigs.get(this.getTestIndex()).removeContent();
        }
        catch (IndicatorTestException e) {
            String message = this.getResultMessage(e);
            Log.error("Indicator test failed. " + message, (Throwable)e);
            this.testConfigs.get(this.getTestIndex()).setAttribute("result", message);
            this.addErrors(this.testConfigs.get(this.getTestIndex()));
        }
        IndicatorTesterConfig.save(null, null);
    }

    private void addErrors(Element elTest) {
        Element elErrors = XMLUtil.tryAddElement((Element)elTest, (String)"Errors");
        elErrors.removeContent();
        elErrors.setAttribute("showGrid", String.valueOf(this.tester.shouldShowGrid()));
        ArrayList errors = this.tester.getDataErrors();
        for (int i = 0; i < errors.size(); ++i) {
            Element elError = new Element("Error");
            elError.setText((String)errors.get(i));
            elErrors.addContent((Content)elError);
        }
    }

    private String getResultMessage(IndicatorTestException e) {
        switch (e.getCode()) {
            case 0: {
                return "Skipped - File not found.";
            }
            case 2: {
                return "Skipped - Invalid config.";
            }
            case 1: {
                return "Skipped - " + this.tester.getErrorMsg();
            }
            case 3: 
            case 4: {
                return "Failed - " + this.tester.getErrorMsg();
            }
            case 5: {
                return "Skipped - Empty file.";
            }
        }
        return "";
    }

    private void performTest() throws IndicatorTestException {
        try {
            this.tester.reset();
            Element testConfig = this.testConfigs.get(this.getTestIndex());
            String indicatorName = testConfig.getAttributeValue("indicator");
            String fileName = testConfig.getAttributeValue("fileName");
            int decimals = Integer.parseInt(testConfig.getAttributeValue("decimals"));
            int shift = Integer.parseInt(testConfig.getAttributeValue("shift"));
            if (!this.tester.checkFileExists(fileName)) {
                testConfig.setAttribute("exists", "no");
                String filePath = this.tester.getFilePath(fileName);
                throw new IndicatorTestException(0, new Exception(filePath));
            }
            testConfig.setAttribute("exists", "yes");
            String paramsStr = testConfig.getAttributeValue("parameters");
            String[] parameters = paramsStr.isEmpty() ? null : paramsStr.split(",");
            IndicatorParameters ip = new IndicatorParameters(this.tester);
            Object[] convertedParams = ip.convertParams(indicatorName, parameters);
            this.tester.runTest(fileName, ip.getDataSource(), IndicatorsLoader.correctIndyName((String)indicatorName), IndicatorsLoader.getBufferName((String)indicatorName), convertedParams, decimals, shift);
        }
        catch (IndicatorTestException e) {
            throw e;
        }
        catch (Exception e) {
            throw new IndicatorTestException(2, e);
        }
    }

    /*
     * WARNING - Removed try catching itself - possible behaviour change.
     */
    public DataToSend getData() {
        this.lock.lock();
        try {
            if (!this.newUpdate) {
                DataToSend dataToSend = null;
                return dataToSend;
            }
            double percent = (double)this.testIndex / (double)this.testConfigs.size() * 100.0;
            this.status.put("percent", percent);
            this.status.put("status", this.runningStatus);
            this.status.put("xmlConfig", (Object)XMLUtil.xmlToString((Element)IndicatorTesterConfig.getConfig()));
            DataToSend dataToSend = this.info;
            return dataToSend;
        }
        finally {
            this.newUpdate = false;
            this.lock.unlock();
        }
    }

    public void resetLastData() {
    }

    private int getTestIndex() {
        this.lock.lock();
        try {
            int n = this.testIndex;
            return n;
        }
        finally {
            this.lock.unlock();
        }
    }

    private void setTestIndex(int value) {
        this.lock.lock();
        this.testIndex = value;
        this.lock.unlock();
    }

    private void incrementTestIndex() {
        this.lock.lock();
        ++this.testIndex;
        this.lock.unlock();
    }

    public int getRunningStatus() {
        this.lock.lock();
        try {
            int n = this.runningStatus;
            return n;
        }
        finally {
            this.lock.unlock();
        }
    }

    private void setRunningStatus(int status) {
        this.lock.lock();
        this.runningStatus = status;
        this.lock.unlock();
    }

    private void setNewUpdate() {
        this.lock.lock();
        this.newUpdate = true;
        this.lock.unlock();
    }
}

