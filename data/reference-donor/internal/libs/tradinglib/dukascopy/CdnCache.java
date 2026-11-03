/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  com.strategyquant.datalib.data.DataManager
 *  com.strategyquant.lib.SQTime
 *  com.strategyquant.lib.app.MainApp
 *  com.strategyquant.lib.tempfiles.TempFilesManager
 *  org.apache.commons.io.IOUtils
 *  org.apache.http.HttpEntity
 *  org.apache.http.HttpResponse
 *  org.apache.http.client.HttpClient
 *  org.apache.http.client.methods.HttpGet
 *  org.apache.http.client.methods.HttpUriRequest
 *  org.apache.http.conn.ConnectTimeoutException
 *  org.slf4j.Logger
 *  org.slf4j.LoggerFactory
 */
package com.strategyquant.tradinglib.dukascopy;

import com.strategyquant.datalib.data.DataManager;
import com.strategyquant.lib.SQTime;
import com.strategyquant.lib.app.MainApp;
import com.strategyquant.lib.tempfiles.TempFilesManager;
import com.strategyquant.tradinglib.data.download.SpeedEvaluator;
import com.strategyquant.tradinglib.dukascopy.DownloadResultDto;
import com.strategyquant.tradinglib.dukascopy.DukascopyUtils;
import com.strategyquant.tradinglib.historyData.DownloadMessageHandler;
import com.strategyquant.tradinglib.historyData.HttpApacheManager;
import java.io.BufferedOutputStream;
import java.io.ByteArrayInputStream;
import java.io.File;
import java.io.FileOutputStream;
import java.io.IOException;
import java.io.InputStream;
import java.net.SocketTimeoutException;
import java.security.KeyManagementException;
import java.security.KeyStoreException;
import java.security.NoSuchAlgorithmException;
import java.util.HashSet;
import java.util.Set;
import java.util.concurrent.ExecutorService;
import java.util.concurrent.Executors;
import java.util.concurrent.TimeUnit;
import java.util.zip.ZipEntry;
import java.util.zip.ZipInputStream;
import javax.net.ssl.SSLProtocolException;
import org.apache.commons.io.IOUtils;
import org.apache.http.HttpEntity;
import org.apache.http.HttpResponse;
import org.apache.http.client.HttpClient;
import org.apache.http.client.methods.HttpGet;
import org.apache.http.client.methods.HttpUriRequest;
import org.apache.http.conn.ConnectTimeoutException;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

public class CdnCache {
    public static final Logger Log = LoggerFactory.getLogger(CdnCache.class);
    private static final int BUFFER_SIZE = 49152;
    private static final int TIMEOUT = 40;
    private static final int RETRY_COUNT = 5;
    private static final int RETRY_DELAY = 30;
    private Set<String> cachedFiles = new HashSet<String>();
    private Set<String> downloadedUrls = new HashSet<String>();
    private String dukasSymbol;
    private String cdnBaseUrl;
    private String tmpFolder;
    private String rootFolderPath;
    private long lastDurationNano;
    private long lastDownloadedBytes;
    private File rootFolder;
    private String fromDateStr;
    private boolean loadMonthPackage;
    private volatile boolean stopped = false;
    private Thread downloadThread;
    private SpeedEvaluator speedEvaluator = new SpeedEvaluator();

    public CdnCache(String string, String string2, String string3, Set<String> set, long l) {
        this.cdnBaseUrl = string2;
        this.dukasSymbol = string3;
        this.tmpFolder = DataManager.fixFilename((String)(string + "_" + System.currentTimeMillis()));
        File file = new File(MainApp.getDataPath() + "/internal/tmp", this.tmpFolder);
        file.mkdirs();
        this.rootFolderPath = file.getAbsolutePath();
        this.rootFolder = new File(this.rootFolderPath);
        this.rootFolder.mkdirs();
        this.fromDateStr = SQTime.toString((long)l, (String)"yyyy_MM_dd") + ".dat";
        String string4 = SQTime.toString((long)l, (String)"yyyy_MM") + ".zip";
        this.loadMonthPackage = set.contains(string4);
    }

    public String getDataFile(int n, int n2, int n3) {
        String string = this.getFileName(n, n2, n3);
        if (!this.cachedFiles.contains(string)) {
            return null;
        }
        return this.rootFolderPath + File.separator + string;
    }

    private String getFileName(int n, int n2, int n3) {
        String string = String.format("%04d_%02d_%02d", n, n2, n3);
        return string + ".dat";
    }

    private String getUrl(int n, int n2) {
        String string = this.loadMonthPackage ? DukascopyUtils.generateCdnMonthUrl(this.cdnBaseUrl, n, n2, this.dukasSymbol) : DukascopyUtils.generateCdnYearUrl(this.cdnBaseUrl, n, this.dukasSymbol);
        return string;
    }

    private void sendMessage(DownloadMessageHandler downloadMessageHandler, String string, String string2) {
        if (downloadMessageHandler != null) {
            downloadMessageHandler.onDownloadMessage(string, string2);
        }
    }

    /*
     * WARNING - Removed try catching itself - possible behaviour change.
     */
    public void preload(long l, long l2, final DownloadMessageHandler downloadMessageHandler) {
        ExecutorService executorService = Executors.newFixedThreadPool(3);
        HashSet<String> hashSet = new HashSet<String>();
        try {
            long l3 = l;
            Log.debug("Preloading data");
            while (l3 <= l2 && !this.stopped) {
                if (this.stopped) {
                    return;
                }
                final int n = SQTime.getFullYear((long)l3);
                int n2 = SQTime.getMonth((long)l3) + 1;
                final String string = this.getUrl(n, n2);
                HashSet<String> hashSet2 = hashSet;
                synchronized (hashSet2) {
                    if (!hashSet.contains(string)) {
                        hashSet.add(string);
                        Log.debug("Registering downloading year: {}", (Object)n);
                        executorService.submit(new Runnable(){
                            final /* synthetic */ CdnCache this$0;
                            {
                                this.this$0 = cdnCache;
                            }

                            @Override
                            public void run() {
                                if (this.this$0.stopped) {
                                    return;
                                }
                                Log.debug("Downloading year: {}", (Object)n);
                                this.this$0.sendMessage(downloadMessageHandler, "Downloading year:" + n, null);
                                SpeedEvaluator speedEvaluator = this.this$0.doDownload(string, downloadMessageHandler);
                                if (!this.this$0.stopped) {
                                    this.this$0.sendMessage(downloadMessageHandler, "Downloaded year:" + n, speedEvaluator == null ? null : speedEvaluator.getSpeed());
                                }
                                Log.debug("Downloaded year: {}", (Object)n);
                            }
                        });
                    }
                }
                l3 = SQTime.addMonths((long)l3, (int)1);
            }
        }
        finally {
            try {
                Log.debug("Waiting for all to download");
                executorService.shutdown();
                executorService.awaitTermination(Long.MAX_VALUE, TimeUnit.SECONDS);
            }
            catch (InterruptedException interruptedException) {}
            executorService.shutdownNow();
        }
        Log.debug("Preload finished");
    }

    /*
     * WARNING - Removed try catching itself - possible behaviour change.
     */
    private SpeedEvaluator doDownload(String string, DownloadMessageHandler downloadMessageHandler) {
        HttpClient httpClient = this.getClient();
        SpeedEvaluator speedEvaluator = new SpeedEvaluator();
        int n = -1;
        for (int i = 1; i <= 5 && !this.stopped; ++i) {
            HttpGet httpGet = new HttpGet(string);
            Log.debug("Downloading data from url: {}", (Object)string);
            try {
                long l = System.nanoTime();
                HttpResponse httpResponse = httpClient.execute((HttpUriRequest)httpGet);
                this.downloadedUrls.add(string);
                n = httpResponse.getStatusLine().getStatusCode();
                if (n >= 200 && n < 300) {
                    byte[] byArray = this.getResponseData(httpResponse);
                    CdnCache cdnCache = this;
                    synchronized (cdnCache) {
                        this.lastDownloadedBytes = byArray.length;
                        this.lastDurationNano = System.nanoTime() - l;
                        try {
                            this.unzip(byArray);
                        }
                        catch (Exception exception) {
                            Log.error("Error while unziping data for url: " + string, (Throwable)exception);
                        }
                        speedEvaluator.evalSpeed(DownloadResultDto.success(null, this.lastDownloadedBytes, this.lastDurationNano));
                        return speedEvaluator;
                    }
                }
                if (n == -1) {
                    this.sendMessage(downloadMessageHandler, "Error while downloding file. Unknown communication error. Please check your internet connection.", null);
                } else {
                    this.sendMessage(downloadMessageHandler, "Error while downloding file. Http code: " + n, null);
                }
                Log.error("Http result: " + n + " for url: " + string);
                continue;
            }
            catch (SocketTimeoutException | SSLProtocolException iOException) {
                Log.error("Download timeout", (Throwable)iOException);
                long l = 40000L;
                Log.debug("Used timeout timeout: {}ms", (Object)l);
                if (iOException instanceof ConnectTimeoutException) {
                    Log.debug("Host: {}", (Object)((ConnectTimeoutException)iOException).getHost());
                }
                this.sendMessage(downloadMessageHandler, "Download timeout. Waiting for: 30sec", null);
                if (this.stopped) break;
                try {
                    this.downloadThread = Thread.currentThread();
                    Thread.sleep(30000L);
                }
                catch (InterruptedException interruptedException) {
                    return null;
                }
                this.sendMessage(downloadMessageHandler, "Trying download again.", null);
                continue;
            }
            catch (Exception exception) {
                Log.error("Error while downloading url: " + string, (Throwable)exception);
            }
        }
        return null;
    }

    private HttpClient getClient() {
        return HttpApacheManager.getInstance().getClient(40);
    }

    public synchronized DownloadResultDto performLoad(int n, int n2, int n3, DownloadMessageHandler downloadMessageHandler) throws KeyManagementException, NoSuchAlgorithmException, KeyStoreException {
        String string = this.getUrl(n, n2);
        if (this.downloadedUrls.contains(string)) {
            String string2 = this.getDataFile(n, n2, n3);
            return string2 == null ? DownloadResultDto.failed(-1) : DownloadResultDto.success(string2, this.lastDownloadedBytes, this.lastDurationNano);
        }
        HttpClient httpClient = this.getClient();
        int n4 = -1;
        for (int i = 1; i <= 5 && !this.stopped; ++i) {
            HttpGet httpGet = new HttpGet(string);
            try {
                long l = System.nanoTime();
                HttpResponse httpResponse = httpClient.execute((HttpUriRequest)httpGet);
                this.downloadedUrls.add(string);
                n4 = httpResponse.getStatusLine().getStatusCode();
                if (n4 == 200) {
                    byte[] byArray = this.getResponseData(httpResponse);
                    this.lastDownloadedBytes = byArray.length;
                    this.lastDurationNano = System.nanoTime() - l;
                    this.unzip(byArray);
                    String string3 = this.getDataFile(n, n2, n3);
                    return string3 == null ? DownloadResultDto.failed(-1, this.lastDownloadedBytes, this.lastDurationNano) : DownloadResultDto.success(string3, this.lastDownloadedBytes, this.lastDurationNano);
                }
                Log.error("Http result: " + n4 + " for url: " + string);
                this.sendMessage(downloadMessageHandler, "Error while downloding file. Http code: " + n4, null);
                continue;
            }
            catch (SocketTimeoutException | SSLProtocolException iOException) {
                Log.error("Download timeout", (Throwable)iOException);
                long l = 40000L;
                Log.debug("Used timeout timeout: {}ms", (Object)l);
                if (iOException instanceof ConnectTimeoutException) {
                    Log.debug("Host: {}", (Object)((ConnectTimeoutException)iOException).getHost());
                }
                this.sendMessage(downloadMessageHandler, "Download timeout. Waiting for: 30sec", null);
                try {
                    this.downloadThread = Thread.currentThread();
                    Thread.sleep(30000L);
                }
                catch (InterruptedException interruptedException) {
                    return DownloadResultDto.failed(n4);
                }
                this.sendMessage(downloadMessageHandler, "Trying download again.", null);
                continue;
            }
            catch (Exception exception) {
                Log.error("Error while downloading url: " + string, (Throwable)exception);
            }
        }
        return DownloadResultDto.failed(n4);
    }

    private byte[] getResponseData(HttpResponse httpResponse) throws IllegalStateException, IOException {
        HttpEntity httpEntity = httpResponse.getEntity();
        InputStream inputStream = httpEntity.getContent();
        byte[] byArray = IOUtils.toByteArray((InputStream)inputStream);
        return byArray;
    }

    public void clean() {
        TempFilesManager.get().cleanSubFolder(this.tmpFolder);
    }

    /*
     * WARNING - Removed try catching itself - possible behaviour change.
     */
    private void unzip(byte[] byArray) throws IOException {
        byte[] byArray2 = new byte[49152];
        ZipInputStream zipInputStream = new ZipInputStream(new ByteArrayInputStream(byArray));
        try {
            ZipEntry zipEntry = zipInputStream.getNextEntry();
            while (zipEntry != null) {
                if (this.stopped) {
                    break;
                }
                String string = zipEntry.getName();
                int n = string.compareTo(this.fromDateStr);
                if (n >= 0) {
                    this.cachedFiles.add(string);
                    File file = new File(this.rootFolder, string);
                    try (BufferedOutputStream bufferedOutputStream = new BufferedOutputStream(new FileOutputStream(file));){
                        int n2;
                        while ((n2 = zipInputStream.read(byArray2)) > 0) {
                            bufferedOutputStream.write(byArray2, 0, n2);
                        }
                    }
                }
                zipEntry = zipInputStream.getNextEntry();
            }
        }
        finally {
            zipInputStream.closeEntry();
            zipInputStream.close();
        }
    }

    public void stop() {
        this.stopped = true;
        if (this.downloadThread != null) {
            this.downloadThread.interrupt();
        }
    }
}

