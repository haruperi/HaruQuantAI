/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  org.apache.commons.io.IOUtils
 *  org.apache.http.Header
 *  org.apache.http.HttpEntity
 *  org.apache.http.client.ClientProtocolException
 *  org.apache.http.client.methods.CloseableHttpResponse
 *  org.apache.http.client.methods.HttpGet
 *  org.apache.http.client.methods.HttpUriRequest
 *  org.apache.http.impl.client.CloseableHttpClient
 *  org.apache.http.impl.client.HttpClientBuilder
 *  org.slf4j.Logger
 *  org.slf4j.LoggerFactory
 */
package com.strategyquant.tradinglib.yahoo;

import java.io.IOException;
import java.io.InputStream;
import java.util.Random;
import org.apache.commons.io.IOUtils;
import org.apache.http.Header;
import org.apache.http.HttpEntity;
import org.apache.http.client.ClientProtocolException;
import org.apache.http.client.methods.CloseableHttpResponse;
import org.apache.http.client.methods.HttpGet;
import org.apache.http.client.methods.HttpUriRequest;
import org.apache.http.impl.client.CloseableHttpClient;
import org.apache.http.impl.client.HttpClientBuilder;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

public class YahooHelper {
    private static final String CRUMB_URL = "https://query2.finance.yahoo.com/v1/test/getcrumb";
    public static final Logger Log = LoggerFactory.getLogger(YahooHelper.class);
    private Random random = new Random();
    private String[] AGENTS = new String[]{"Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36", "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/138.0.0.0 Safari/537.36", "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/138.0.0.0 Safari/537.36 Edg/138.0.0.0"};

    public String getCrumb(String string, String string2) throws ClientProtocolException, IOException {
        return this.doDownloadWithCookies(CRUMB_URL, string, string2);
    }

    public String download(String string) throws Exception {
        int n = this.random.nextInt(this.AGENTS.length);
        String string2 = this.AGENTS[n];
        String string3 = this.getCookies(string2, n);
        String string4 = this.getCrumb(string2, string3);
        string = string + "&crumb=" + string4;
        return this.doDownloadWithCookies(string, string2, string3);
    }

    /*
     * Enabled aggressive block sorting
     * Enabled unnecessary exception pruning
     * Enabled aggressive exception aggregation
     */
    private String getCookies(String string, int n) throws Exception {
        try (CloseableHttpClient closeableHttpClient = HttpClientBuilder.create().build();){
            Header header;
            block11: {
                HttpGet httpGet = new HttpGet("https://fc.yahoo.com");
                httpGet.addHeader("User-Agent", string);
                CloseableHttpResponse closeableHttpResponse = closeableHttpClient.execute((HttpUriRequest)httpGet);
                Header[] headerArray = closeableHttpResponse.getAllHeaders();
                int n2 = headerArray.length;
                int n3 = 0;
                while (n3 < n2) {
                    header = headerArray[n3];
                    if (!header.getName().equalsIgnoreCase("Set-Cookie")) {
                        ++n3;
                        continue;
                    }
                    break block11;
                }
                throw new Exception("Error while getting cookie");
            }
            String string2 = header.getValue();
            String[] stringArray = string2.split(";");
            String string3 = stringArray[0];
            return string3;
        }
        catch (Exception exception) {
            Log.error("Error while getting cookie", (Throwable)exception);
            throw new Exception("Error while getting cookie");
        }
    }

    private String doDownloadWithCookies(String string, String string2, String string3) throws IOException, ClientProtocolException {
        try (CloseableHttpClient closeableHttpClient = HttpClientBuilder.create().build();){
            HttpGet httpGet = new HttpGet(string);
            httpGet.addHeader("Cookie", string3);
            httpGet.addHeader("User-Agent", string2);
            CloseableHttpResponse closeableHttpResponse = closeableHttpClient.execute((HttpUriRequest)httpGet);
            HttpEntity httpEntity = closeableHttpResponse.getEntity();
            int n = closeableHttpResponse.getStatusLine().getStatusCode();
            if (n != 200) {
                Log.error("Error while downloading: " + string + ". Error code:" + n);
            }
            InputStream inputStream = httpEntity.getContent();
            byte[] byArray = IOUtils.toByteArray((InputStream)inputStream);
            String string4 = new String(byArray);
            return string4;
        }
    }
}

