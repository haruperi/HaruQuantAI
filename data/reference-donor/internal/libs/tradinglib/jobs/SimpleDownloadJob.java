/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  com.strategyquant.gridlib.client.GridJob
 *  org.apache.commons.io.IOUtils
 *  org.apache.http.HttpEntity
 *  org.apache.http.HttpResponse
 *  org.apache.http.client.HttpClient
 *  org.apache.http.client.config.RequestConfig
 *  org.apache.http.client.methods.HttpGet
 *  org.apache.http.client.methods.HttpUriRequest
 *  org.apache.http.impl.client.CloseableHttpClient
 *  org.apache.http.impl.client.HttpClientBuilder
 *  org.slf4j.Logger
 *  org.slf4j.LoggerFactory
 */
package com.strategyquant.tradinglib.jobs;

import com.strategyquant.gridlib.client.GridJob;
import com.strategyquant.tradinglib.dukascopy.DownloadResultDto;
import java.io.IOException;
import java.io.InputStream;
import java.io.Serializable;
import java.util.Map;
import org.apache.commons.io.IOUtils;
import org.apache.http.HttpEntity;
import org.apache.http.HttpResponse;
import org.apache.http.client.HttpClient;
import org.apache.http.client.config.RequestConfig;
import org.apache.http.client.methods.HttpGet;
import org.apache.http.client.methods.HttpUriRequest;
import org.apache.http.impl.client.CloseableHttpClient;
import org.apache.http.impl.client.HttpClientBuilder;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

public class SimpleDownloadJob
extends GridJob<DownloadResultDto> {
    private static final long serialVersionUID = 1L;
    public static final Logger Log = LoggerFactory.getLogger(SimpleDownloadJob.class);
    private static final int TIMEOUT = 30;
    public static final String URL_PARAM = "url";

    public SimpleDownloadJob(String string, int n, Map<String, Serializable> map) {
        super(string, n, map);
    }

    public DownloadResultDto call() throws Exception {
        String string = (String)this.getParameters().get(URL_PARAM);
        RequestConfig requestConfig = RequestConfig.custom().setConnectTimeout(30000).setConnectionRequestTimeout(30000).setSocketTimeout(120000).build();
        CloseableHttpClient closeableHttpClient = HttpClientBuilder.create().setDefaultRequestConfig(requestConfig).build();
        HttpGet httpGet = new HttpGet(string);
        return this.doDownload((HttpClient)closeableHttpClient, httpGet);
    }

    /*
     * WARNING - Removed try catching itself - possible behaviour change.
     */
    protected DownloadResultDto doDownload(HttpClient httpClient, HttpGet httpGet) throws Exception {
        int n = -1;
        try {
            long l = System.nanoTime();
            HttpResponse httpResponse = httpClient.execute((HttpUriRequest)httpGet);
            n = httpResponse.getStatusLine().getStatusCode();
            if (n == 200) {
                long l2 = System.nanoTime() - l;
                DownloadResultDto downloadResultDto = this.handleSuccessDownload(httpResponse, l2);
                return downloadResultDto;
            }
        }
        catch (Exception exception) {
            Log.error("Error while downloading:" + httpGet.getURI(), (Throwable)exception);
        }
        finally {
            httpGet.releaseConnection();
        }
        return DownloadResultDto.failed(n);
    }

    protected byte[] getResponseData(HttpResponse httpResponse) throws IllegalStateException, IOException {
        HttpEntity httpEntity = httpResponse.getEntity();
        InputStream inputStream = httpEntity.getContent();
        byte[] byArray = IOUtils.toByteArray((InputStream)inputStream);
        return byArray;
    }

    protected DownloadResultDto handleSuccessDownload(HttpResponse httpResponse, long l) throws IllegalStateException, IOException {
        byte[] byArray = this.getResponseData(httpResponse);
        return DownloadResultDto.success(byArray, l);
    }
}

