/*
 * Decompiled with CFR 0.152.
 */
package com.strategyquant.tradinglib.project;

import java.util.concurrent.locks.Lock;
import java.util.concurrent.locks.ReentrantLock;

public class ProjectLog {
    private final Lock lock = new ReentrantLock();
    private String[] buffer = new String[1000];
    private String lastOutput = "";
    private int lastIndex = 0;
    private int totalWritten = 0;
    private boolean changed = true;

    /*
     * WARNING - Removed try catching itself - possible behaviour change.
     */
    public void add(String string) {
        try {
            int n;
            this.lock.lock();
            if (string == null) {
                return;
            }
            int n2 = this.buffer.length - this.lastIndex;
            String[] stringArray = string.split("\n");
            if (n2 < stringArray.length) {
                n = stringArray.length - n2;
                this.shiftBuffer(n);
                this.lastIndex = this.lastIndex > n ? this.lastIndex - n : 0;
            }
            for (n = stringArray.length - 1; n >= 0 && this.lastIndex < this.buffer.length; --n) {
                this.buffer[this.lastIndex++] = stringArray[n];
            }
            this.changed = true;
            this.totalWritten += stringArray.length;
        }
        finally {
            this.lock.unlock();
        }
    }

    public String getNext() {
        try {
            CharSequence charSequence;
            this.lock.lock();
            if (this.lastIndex == 0) {
                String string = null;
                return string;
            }
            if (this.changed) {
                charSequence = new StringBuilder();
                for (int i = this.lastIndex - 1; i >= 0; --i) {
                    ((StringBuilder)charSequence).append(this.buffer[i]);
                    ((StringBuilder)charSequence).append("\n");
                }
                if (this.totalWritten > this.buffer.length) {
                    ((StringBuilder)charSequence).append("\n(log shortened to save memory, see the complete log in the log file)\n...");
                }
                this.lastOutput = ((StringBuilder)charSequence).toString();
                this.changed = false;
            }
            charSequence = this.lastOutput;
            return charSequence;
        }
        finally {
            this.lock.unlock();
        }
    }

    public void clear() {
        try {
            this.lock.lock();
            this.lastIndex = 0;
            this.changed = false;
            this.totalWritten = 0;
        }
        finally {
            this.lock.unlock();
        }
    }

    public void resetLastData() {
        this.changed = true;
    }

    private void shiftBuffer(int n) {
        for (int i = 0; i < this.buffer.length && i + n != this.lastIndex; ++i) {
            this.buffer[i] = this.buffer[i + n];
        }
    }
}

