/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  com.strategyquant.datalib.InstrumentInfo
 *  com.strategyquant.datalib.data.DataManager
 *  com.strategyquant.datalib.instrument.InstrumentManager
 *  com.strategyquant.lib.L
 *  com.strategyquant.tradinglib.yahoo.YahooHelper
 *  org.apache.http.HttpResponse
 *  org.apache.http.client.methods.HttpGet
 *  org.apache.http.client.methods.HttpUriRequest
 *  org.apache.http.impl.client.CloseableHttpClient
 *  org.apache.http.impl.client.HttpClientBuilder
 *  org.json.JSONArray
 *  org.json.JSONObject
 *  org.slf4j.Logger
 *  org.slf4j.LoggerFactory
 */
package com.strategyquant.plugin.DataSource.impl.Yahoo;

import com.strategyquant.datalib.InstrumentInfo;
import com.strategyquant.datalib.data.DataManager;
import com.strategyquant.datalib.instrument.InstrumentManager;
import com.strategyquant.lib.L;
import com.strategyquant.plugin.DataSource.impl.Yahoo.YahooSymbol;
import com.strategyquant.tradinglib.yahoo.YahooHelper;
import java.io.BufferedReader;
import java.io.InputStream;
import java.io.InputStreamReader;
import java.net.URLEncoder;
import java.nio.charset.StandardCharsets;
import org.apache.http.HttpResponse;
import org.apache.http.client.methods.HttpGet;
import org.apache.http.client.methods.HttpUriRequest;
import org.apache.http.impl.client.CloseableHttpClient;
import org.apache.http.impl.client.HttpClientBuilder;
import org.json.JSONArray;
import org.json.JSONObject;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

public class YahooDataManager {
    public static final Logger Log = LoggerFactory.getLogger(YahooDataManager.class);
    private static YahooDataManager instance;

    public static synchronized YahooDataManager get() {
        if (instance == null) {
            instance = new YahooDataManager();
        }
        return instance;
    }

    public String addData(String symbol, String postfix, byte dataType, String description, String exchange) throws Exception {
        double pointValue = 1.0;
        double tickSize = 0.01;
        double tickStep = 0.01;
        double defaultSpread = 0.0;
        double defaultSlippage = 0.0;
        String symbolName = symbol + postfix;
        String instrumentName = symbol;
        while (DataManager.checkDataExists((String)"History", (String)symbolName)) {
            symbolName = DataManager.generateName((String)symbolName);
        }
        if (!InstrumentManager.checkInstrumentExists((String)instrumentName)) {
            InstrumentManager.addInstrument((String)instrumentName, (String)"Yahoo instrument", (double)pointValue, (double)tickSize, (double)tickStep, (double)defaultSpread, (double)defaultSlippage, (String)"<Method type=\"None\" use=\"true\"><Params/></Method>", (byte)1, null, null, null, null, (double)1.0, (double)0.0);
        } else {
            InstrumentInfo instrument = InstrumentManager.getInstrumentInfo((String)instrumentName);
            if (instrument.tickSize != tickSize || instrument.tickStep != tickStep) {
                while (InstrumentManager.checkInstrumentExists((String)instrumentName)) {
                    instrumentName = DataManager.generateName((String)instrumentName);
                }
                InstrumentManager.addInstrument((String)instrumentName, (String)"Yahoo instrument", (double)pointValue, (double)tickSize, (double)tickStep, (double)defaultSpread, (double)defaultSlippage, (String)"<Method type=\"None\" use=\"true\"><Params/></Method>", (byte)1, null, null, null, null, (double)1.0, (double)0.0);
            }
        }
        DataManager.addData((String)"History", (String)symbolName, (String)instrumentName, (int)1, (int)3, (String)symbol, (String)(description + ", " + exchange));
        return symbolName;
    }

    private String getCookieCrumb() throws Exception {
        String crumb = null;
        Object cookieString = null;
        try {
            CloseableHttpClient client = HttpClientBuilder.create().build();
            HttpGet get = new HttpGet("https://finance.yahoo.com/quote/SPY");
            HttpResponse response = client.execute((HttpUriRequest)get);
            if (response.getStatusLine().getStatusCode() != 200) {
                throw new Exception(L.t((String)"HTML status code - %d", (Object[])new Object[]{response.getStatusLine().getStatusCode()}));
            }
            InputStream inStream = response.getEntity().getContent();
            InputStreamReader irdr = new InputStreamReader(inStream, StandardCharsets.UTF_8);
            BufferedReader rsv = new BufferedReader(irdr);
            String pattern = "\"crumb\":\"";
            String line = null;
            while ((line = rsv.readLine()) != null) {
                System.out.println(line);
                if (!line.contains(pattern)) continue;
                int indexStart = line.indexOf("\"crumb\":\"") + pattern.length();
                crumb = line.substring(indexStart, line.indexOf("\"", indexStart));
                break;
            }
            rsv.close();
        }
        catch (Error x) {
            throw new Exception(L.t((String)"Cannot get Yahoo cookie crumb.", (Object[])new Object[0]), x);
        }
        catch (Exception e) {
            throw new Exception(L.t((String)"Cannot get Yahoo cookie crumb.", (Object[])new Object[0]), e);
        }
        if (crumb == null) {
            throw new Exception(L.t((String)"Cannot get Yahoo cookies / crumb.", (Object[])new Object[0]));
        }
        return crumb;
    }

    public YahooSymbol downloadInfo(String name) throws Exception {
        String response;
        YahooSymbol symbol = new YahooSymbol();
        symbol.symbol = name;
        String url = "https://query1.finance.yahoo.com/v7/finance/quote?symbols=" + URLEncoder.encode(name);
        try {
            YahooHelper helper = new YahooHelper();
            response = helper.download(url);
        }
        catch (Exception e) {
            throw new Exception(L.t((String)"Symbol '%s' not found.", (Object[])new Object[]{name}));
        }
        try {
            JSONObject jsonObject = new JSONObject(response);
            JSONObject quoteResponse = jsonObject.getJSONObject("quoteResponse");
            JSONArray results = quoteResponse.getJSONArray("result");
            if (results.length() == 0) {
                throw new Exception(L.t((String)"Symbol '%s' not found.", (Object[])new Object[]{name}));
            }
            JSONObject result = results.getJSONObject(0);
            try {
                symbol.name = result.getString("shortName");
            }
            catch (Exception exception) {
                // empty catch block
            }
            symbol.exchange = result.getString("exchange");
            return symbol;
        }
        catch (Exception e) {
            Log.error("Cannot parse symbol '" + name + "' details from: " + response, (Throwable)e);
            throw new Exception(L.t((String)"Symbol '%s' not found.", (Object[])new Object[]{name}));
        }
    }
}

