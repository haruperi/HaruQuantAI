/*
 * Decompiled with CFR 0.152.
 */
package com.strategyquant.gridlib.compute.common;

import java.util.Iterator;
import java.util.NoSuchElementException;

public class RingBuffer<T>
implements Iterable<T> {
    private T[] data;
    private int size;
    private int writePos = 0;
    private int oldest = 0;

    public RingBuffer(int n) {
        this.size = n;
        this.data = new Object[n];
    }

    public int getSize() {
        return this.size;
    }

    public void add(T t) {
        if (this.data[this.writePos] != null) {
            ++this.oldest;
            if (this.oldest == this.size) {
                this.oldest = 0;
            }
        }
        this.data[this.writePos] = t;
        ++this.writePos;
        if (this.writePos == this.size) {
            this.writePos = 0;
        }
    }

    public void clear() {
        for (int i = 0; i < this.size; ++i) {
            this.data[i] = null;
        }
        this.oldest = 0;
        this.writePos = 0;
    }

    @Override
    public Iterator<T> iterator() {
        return new IteratorImpl(this.oldest);
    }

    private class IteratorImpl
    implements Iterator<T> {
        private int current;
        private int returned = 0;

        public IteratorImpl(int n) {
            this.current = n;
        }

        @Override
        public boolean hasNext() {
            return RingBuffer.this.data[this.current] != null && this.returned != RingBuffer.this.data.length;
        }

        @Override
        public T next() {
            if (!this.hasNext()) {
                throw new NoSuchElementException();
            }
            Object object = RingBuffer.this.data[this.current];
            ++this.current;
            if (this.current == RingBuffer.this.data.length) {
                this.current = 0;
            }
            ++this.returned;
            return object;
        }
    }
}

