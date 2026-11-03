/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  com.strategyquant.lib.app.MainApp
 *  org.apache.commons.io.IOUtils
 *  org.apache.http.client.ClientProtocolException
 *  org.apache.http.client.HttpClient
 *  org.apache.http.client.config.RequestConfig
 *  org.apache.http.client.methods.CloseableHttpResponse
 *  org.apache.http.client.methods.HttpGet
 *  org.apache.http.client.methods.HttpUriRequest
 *  org.apache.http.conn.socket.LayeredConnectionSocketFactory
 *  org.apache.http.conn.ssl.NoopHostnameVerifier
 *  org.apache.http.conn.ssl.SSLConnectionSocketFactory
 *  org.apache.http.impl.client.CloseableHttpClient
 *  org.apache.http.impl.client.HttpClientBuilder
 *  org.apache.http.impl.client.HttpClients
 *  org.apache.http.ssl.SSLContextBuilder
 *  org.slf4j.Logger
 *  org.slf4j.LoggerFactory
 */
package com.strategyquant.tradinglib.historyData;

import com.strategyquant.lib.app.MainApp;
import java.io.File;
import java.io.IOException;
import java.io.InputStream;
import java.security.KeyManagementException;
import java.security.KeyStoreException;
import java.security.NoSuchAlgorithmException;
import javax.net.ssl.HostnameVerifier;
import org.apache.commons.io.IOUtils;
import org.apache.http.client.ClientProtocolException;
import org.apache.http.client.HttpClient;
import org.apache.http.client.config.RequestConfig;
import org.apache.http.client.methods.CloseableHttpResponse;
import org.apache.http.client.methods.HttpGet;
import org.apache.http.client.methods.HttpUriRequest;
import org.apache.http.conn.socket.LayeredConnectionSocketFactory;
import org.apache.http.conn.ssl.NoopHostnameVerifier;
import org.apache.http.conn.ssl.SSLConnectionSocketFactory;
import org.apache.http.impl.client.CloseableHttpClient;
import org.apache.http.impl.client.HttpClientBuilder;
import org.apache.http.impl.client.HttpClients;
import org.apache.http.ssl.SSLContextBuilder;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

public class HttpApacheManager {
    private static final Logger Log = LoggerFactory.getLogger(HttpApacheManager.class);
    private static HttpApacheManager INSTANCE = new HttpApacheManager();
    private boolean ignoreSSL = false;

    public static HttpApacheManager getInstance() {
        return INSTANCE;
    }

    private HttpApacheManager() {
        File file = new File(MainApp.getDataPath() + "/ignoressl.txt");
        Log.debug("Checking file in location: {}" + file.getAbsolutePath());
        this.ignoreSSL = file.exists();
        Log.debug("Initializing http manager with strict mode: " + !this.ignoreSSL);
    }

    public HttpClient getClient() throws KeyManagementException, NoSuchAlgorithmException, KeyStoreException {
        return this.getClient(null);
    }

    public HttpClient getClient(Integer n) {
        try {
            SSLContextBuilder sSLContextBuilder;
            HttpClientBuilder httpClientBuilder = HttpClientBuilder.create();
            if (this.ignoreSSL) {
                sSLContextBuilder = new SSLContextBuilder();
                sSLContextBuilder.loadTrustMaterial(null, (x509CertificateArray, string) -> true);
                SSLConnectionSocketFactory sSLConnectionSocketFactory = new SSLConnectionSocketFactory(sSLContextBuilder.build(), (HostnameVerifier)NoopHostnameVerifier.INSTANCE);
                httpClientBuilder = HttpClients.custom().setSSLSocketFactory((LayeredConnectionSocketFactory)sSLConnectionSocketFactory);
            }
            if (n == null) {
                n = 40;
            }
            sSLContextBuilder = RequestConfig.custom().setConnectTimeout(n * 1000).setConnectionRequestTimeout(n * 1000).setSocketTimeout(4 * n * 1000).build();
            httpClientBuilder.setDefaultRequestConfig((RequestConfig)sSLContextBuilder);
            return httpClientBuilder.build();
        }
        catch (Exception exception) {
            throw new RuntimeException("Error while creating http client", exception);
        }
    }

    public byte[] getData(String string) throws ClientProtocolException, IOException {
        return this.getData(string, null);
    }

    public byte[] getData(String string, Integer n) throws ClientProtocolException, IOException {
        try (CloseableHttpClient closeableHttpClient = (CloseableHttpClient)this.getClient(n);){
            byte[] byArray;
            block13: {
                CloseableHttpResponse closeableHttpResponse = closeableHttpClient.execute((HttpUriRequest)new HttpGet(string));
                InputStream inputStream = closeableHttpResponse.getEntity().getContent();
                try {
                    int n2 = closeableHttpResponse.getStatusLine().getStatusCode();
                    byte[] byArray2 = IOUtils.toByteArray((InputStream)inputStream);
                    if (n2 >= 400) {
                        throw new HttpException("Request error: GET, " + string + " - status code:" + n2, string, n2, byArray2);
                    }
                    byArray = byArray2;
                    if (inputStream == null) break block13;
                }
                catch (Throwable throwable) {
                    if (inputStream != null) {
                        try {
                            inputStream.close();
                        }
                        catch (Throwable throwable2) {
                            throwable.addSuppressed(throwable2);
                        }
                    }
                    throw throwable;
                }
                inputStream.close();
            }
            return byArray;
        }
    }

    public static class HttpException
    extends RuntimeException {
        private static final long serialVersionUID = 1L;
        private int code;
        private byte[] resultBytes;
        private String url;

        public HttpException(String string, String string2, int n, byte[] byArray) {
            super(string);
            this.url = string2;
            this.code = n;
            this.resultBytes = byArray;
        }

        public String getUrl() {
            return this.url;
        }

        public int getCode() {
            return this.code;
        }

        public byte[] getResultBytes() {
            return this.resultBytes;
        }
    }
}

