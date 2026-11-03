/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  org.apache.http.HttpResponse
 *  org.apache.http.client.HttpClient
 *  org.apache.http.client.methods.HttpGet
 *  org.apache.http.client.methods.HttpUriRequest
 *  org.slf4j.Logger
 *  org.slf4j.LoggerFactory
 */
package com.strategyquant.tradinglib.dukascopy.job;

import com.strategyquant.tradinglib.dukascopy.DownloadResultDto;
import com.strategyquant.tradinglib.dukascopy.job.DownloadRateCorrector;
import com.strategyquant.tradinglib.jobs.SimpleDownloadJob;
import java.io.Serializable;
import java.net.UnknownHostException;
import java.util.Map;
import org.apache.http.HttpResponse;
import org.apache.http.client.HttpClient;
import org.apache.http.client.methods.HttpGet;
import org.apache.http.client.methods.HttpUriRequest;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

public class DownloadWithFlexibileSpeedJob
extends SimpleDownloadJob {
    private static final long serialVersionUID = 1L;
    public static final Logger Log = LoggerFactory.getLogger(DownloadWithFlexibileSpeedJob.class);
    private static final int TRY_COUNT = 5;
    private static final int TRY_COUNT_503 = 20;
    private DownloadRateCorrector corrector;

    public DownloadWithFlexibileSpeedJob(String string, int n, Map<String, Serializable> map, DownloadRateCorrector downloadRateCorrector) {
        super(string, n, map);
        this.corrector = downloadRateCorrector;
    }

    /*
     * WARNING - Removed try catching itself - possible behaviour change.
     */
    @Override
    protected DownloadResultDto doDownload(HttpClient httpClient, HttpGet httpGet) throws Exception {
        Object object;
        int n = -1;
        HttpResponse httpResponse = null;
        int n2 = 0;
        int n3 = 0;
        int n4 = 1;
        String string = null;
        boolean bl = false;
        long l = System.nanoTime();
        while (n2 < 5 && n3 < 20) {
            try {
                object = this.corrector;
                synchronized (object) {
                    this.corrector.waitBeforeNextDownload();
                    httpResponse = httpClient.execute((HttpUriRequest)httpGet);
                    n = httpResponse.getStatusLine().getStatusCode();
                    if (n == 503 || n == 500 || n == 504) {
                        this.corrector.downloadFailed();
                        ++n3;
                    } else if (n == 200) {
                        this.corrector.downloadSuccess();
                    } else {
                        ++n2;
                    }
                }
                if (n != 200) continue;
                long l2 = System.nanoTime() - l;
                DownloadResultDto downloadResultDto = this.handleSuccessDownload(httpResponse, l2);
                return downloadResultDto;
            }
            catch (InterruptedException interruptedException) {
                bl = true;
                break;
            }
            catch (UnknownHostException unknownHostException) {
                Log.error("Unknown host: " + httpGet.getURI() + ". Try " + n4, (Throwable)unknownHostException);
                string = "The server address could not be resolved. This may be due to a DNS or network issue.";
                ++n2;
            }
            catch (Exception exception) {
                Log.error("Error while downloading:" + httpGet.getURI() + ". Try " + n4, (Throwable)exception);
                ++n2;
            }
            finally {
                httpGet.releaseConnection();
                ++n4;
            }
        }
        if (!bl) {
            Log.error("Download failed:" + httpGet.getURI());
        }
        object = DownloadResultDto.failed(n);
        ((DownloadResultDto)object).setErrorMessage(string);
        return object;
    }
}

