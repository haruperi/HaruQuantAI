/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  com.strategyquant.indicatorTester.IndicatorTesterConfig
 *  com.strategyquant.lib.L
 *  com.strategyquant.lib.SQUtils
 *  com.strategyquant.lib.XMLUtil
 *  com.strategyquant.lib.constants.SQPaths
 *  com.strategyquant.lib.utils.IProgressListener
 *  org.jdom2.Element
 */
package com.strategyquant.plugin.CodeEditor.impl.IndicatorTester;

import com.strategyquant.indicatorTester.IndicatorTesterConfig;
import com.strategyquant.lib.L;
import com.strategyquant.lib.SQUtils;
import com.strategyquant.lib.XMLUtil;
import com.strategyquant.lib.constants.SQPaths;
import com.strategyquant.lib.utils.IProgressListener;
import java.io.BufferedInputStream;
import java.io.BufferedOutputStream;
import java.io.File;
import java.io.FileOutputStream;
import java.io.FilterOutputStream;
import java.io.IOException;
import java.io.InputStream;
import java.net.HttpURLConnection;
import java.net.URL;
import java.util.Enumeration;
import java.util.zip.ZipEntry;
import java.util.zip.ZipFile;
import org.jdom2.Element;

public class IndicatorTestsDownloader {
    private static final String downloadURL = "http://autoupdate.strategyquant.com/indicator_data/indicator_tests.zip";
    private static final String targetFilePath = SQPaths.testsDirPath + "/tmp/indicator_tests.zip";
    private static Thread processingThread = null;

    public static void downloadTests(final IProgressListener listener) throws Exception {
        if (processingThread != null && processingThread.isAlive()) {
            throw new Exception("Download is already in progress");
        }
        processingThread = new Thread(){

            @Override
            public void run() {
                block2: {
                    try {
                        IndicatorTestsDownloader.downloadFile(listener);
                        IndicatorTestsDownloader.copyTestFiles(listener);
                        IndicatorTestsDownloader.updateTesterConfig(listener);
                    }
                    catch (Exception e) {
                        if (listener == null) break block2;
                        listener.onError(e.getMessage());
                    }
                }
            }
        };
        processingThread.start();
    }

    private static void downloadFile(IProgressListener listener) throws Exception {
        HttpURLConnection httpConnection = null;
        BufferedInputStream inputStream = null;
        FilterOutputStream outputStream = null;
        if (listener != null) {
            listener.setMessage(L.t((String)"Downloading tests...", (Object[])new Object[0]));
            listener.onProgress(0.0);
        }
        try {
            URL url = new URL(downloadURL);
            httpConnection = (HttpURLConnection)url.openConnection();
            long completeFileSize = httpConnection.getContentLength();
            inputStream = new BufferedInputStream(httpConnection.getInputStream());
            SQUtils.createFile((String)targetFilePath);
            FileOutputStream fos = new FileOutputStream(targetFilePath);
            outputStream = new BufferedOutputStream(fos, 1024);
            byte[] data = new byte[1024];
            long downloadedFileSize = 0L;
            int x = 0;
            while ((x = inputStream.read(data, 0, 1024)) >= 0) {
                double currentProgress = (double)(downloadedFileSize += (long)x) / (double)completeFileSize * 100.0;
                double d = currentProgress = currentProgress < 100.0 ? currentProgress : 99.0;
                if (listener != null) {
                    listener.onProgress(currentProgress);
                }
                ((BufferedOutputStream)outputStream).write(data, 0, x);
            }
            outputStream.close();
            inputStream.close();
        }
        catch (Exception e) {
            if (inputStream != null) {
                try {
                    inputStream.close();
                }
                catch (IOException completeFileSize) {
                    // empty catch block
                }
            }
            if (outputStream != null) {
                try {
                    outputStream.close();
                }
                catch (IOException completeFileSize) {
                    // empty catch block
                }
            }
            if (httpConnection != null) {
                httpConnection.disconnect();
            }
            new File(targetFilePath).delete();
            String reason = e.getMessage();
            throw new Exception("Download failed. Reason: " + reason != null ? reason : "NullPointer exception");
        }
    }

    private static void copyTestFiles(IProgressListener listener) throws Exception {
        if (listener != null) {
            listener.setMessage(L.t((String)"Copying test files...", (Object[])new Object[0]));
        }
        ZipFile zf = null;
        FileOutputStream fos = null;
        byte[] buffer = new byte[1024];
        try {
            File folder = new File(SQPaths.indicatorTestsPath);
            if (!folder.exists()) {
                folder.mkdirs();
            }
            zf = new ZipFile(targetFilePath);
            int entriesCount = zf.size();
            int entriesProcessed = 0;
            Enumeration<? extends ZipEntry> entries = zf.entries();
            while (entries.hasMoreElements()) {
                int len;
                double currentProgress;
                ZipEntry zipEntry = entries.nextElement();
                double d = currentProgress = (currentProgress = (double)(++entriesProcessed) / (double)entriesCount * 100.0) < 100.0 ? currentProgress : 99.0;
                if (listener != null) {
                    listener.onProgress(currentProgress);
                }
                if (zipEntry.isDirectory()) continue;
                String fileName = zipEntry.getName();
                File newFile = new File(SQPaths.indicatorTestsPath + File.separator + fileName);
                new File(newFile.getParent()).mkdirs();
                fos = new FileOutputStream(newFile);
                InputStream inputStream = zf.getInputStream(zipEntry);
                while ((len = inputStream.read(buffer)) > 0) {
                    fos.write(buffer, 0, len);
                }
                fos.close();
            }
            zf.close();
            new File(targetFilePath).delete();
        }
        catch (Exception e) {
            if (fos != null) {
                fos.close();
            }
            if (zf != null) {
                zf.close();
            }
            String reason = e.getMessage();
            throw new Exception("Copying test files failed. Reason: " + reason != null ? reason : "NullPointer exception");
        }
    }

    private static void updateTesterConfig(IProgressListener listener) throws Exception {
        if (listener != null) {
            listener.setMessage(L.t((String)"Updating tester config...", (Object[])new Object[0]));
            listener.onProgress(1.0);
        }
        String downloadedConfigPath = SQPaths.indicatorTestsPath + File.separator + "IndicatorTester.xml";
        try {
            Element downloadedConfig = XMLUtil.fileToXmlElement((File)new File(downloadedConfigPath));
            IndicatorTesterConfig.save((Element)downloadedConfig, (String)IndicatorTesterConfig.defaultConfigFilePath);
            if (listener != null) {
                listener.onProgress(100.0);
                listener.onFinish();
            }
            new File(downloadedConfigPath).delete();
        }
        catch (Exception e) {
            new File(downloadedConfigPath).delete();
            String reason = e.getMessage();
            throw new Exception("Updating Indicator Tester config failed. Reason: " + reason != null ? reason : "NullPointer exception");
        }
    }
}

