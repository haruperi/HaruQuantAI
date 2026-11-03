/*
 * Decompiled with CFR 0.152.
 */
package com.strategyquant.tradinglib.dukascopy;

import java.io.Serializable;

public class DownloadResultDto
implements Serializable {
    private static final long serialVersionUID = 1L;
    private String filename;
    private byte[] data;
    private int httpCode;
    private long duration;
    private boolean checksumFailed;
    private long downloadedSize;
    private String errorMessage;

    public static DownloadResultDto failed(int n) {
        DownloadResultDto downloadResultDto = new DownloadResultDto();
        downloadResultDto.httpCode = n;
        return downloadResultDto;
    }

    public static DownloadResultDto failed(int n, long l, long l2) {
        DownloadResultDto downloadResultDto = new DownloadResultDto();
        downloadResultDto.httpCode = n;
        downloadResultDto.duration = l2;
        downloadResultDto.downloadedSize = l;
        return downloadResultDto;
    }

    public static DownloadResultDto success(byte[] byArray, long l) {
        DownloadResultDto downloadResultDto = new DownloadResultDto();
        downloadResultDto.httpCode = 200;
        downloadResultDto.data = byArray;
        downloadResultDto.duration = l;
        downloadResultDto.downloadedSize = byArray == null ? 0L : (long)byArray.length;
        return downloadResultDto;
    }

    public static DownloadResultDto success(String string, long l, long l2) {
        DownloadResultDto downloadResultDto = new DownloadResultDto();
        downloadResultDto.httpCode = 200;
        downloadResultDto.duration = l2;
        downloadResultDto.filename = string;
        downloadResultDto.downloadedSize = l;
        return downloadResultDto;
    }

    public static DownloadResultDto checksumFailed() {
        DownloadResultDto downloadResultDto = new DownloadResultDto();
        downloadResultDto.checksumFailed = true;
        return downloadResultDto;
    }

    public long getDownloadedSize() {
        return this.downloadedSize;
    }

    public void setDownloadedBytes(long l) {
        this.downloadedSize = l;
    }

    public void setFilename(String string) {
        this.filename = string;
    }

    public String getFilename() {
        return this.filename;
    }

    public byte[] getData() {
        return this.data;
    }

    public void setData(byte[] byArray) {
        this.data = byArray;
    }

    public int getHttpCode() {
        return this.httpCode;
    }

    public void setHttpCode(int n) {
        this.httpCode = n;
    }

    public boolean isChecksumFailed() {
        return this.checksumFailed;
    }

    public void setChecksumFailed(boolean bl) {
        this.checksumFailed = bl;
    }

    public long getDuration() {
        return this.duration;
    }

    public void setDuration(long l) {
        this.duration = l;
    }

    public String getErrorMessage() {
        return this.errorMessage;
    }

    public void setErrorMessage(String string) {
        this.errorMessage = string;
    }
}

