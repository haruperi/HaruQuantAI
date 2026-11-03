/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  net.openhft.affinity.AffinityLock
 *  org.slf4j.Logger
 *  org.slf4j.LoggerFactory
 */
package com.strategyquant.gridlib.concurrent;

import java.util.LinkedList;
import java.util.List;
import java.util.Queue;
import java.util.logging.Level;
import net.openhft.affinity.AffinityLock;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

public class ThreadPool
implements AutoCloseable {
    private static final Logger LOGGER = LoggerFactory.getLogger(ThreadPool.class);
    private BlockingQueue<Runnable> queue;
    private List<Thread> threads = new LinkedList<Thread>();
    private boolean useAffinity;
    private volatile boolean shutdown;
    private int additonalCount = 0;

    public ThreadPool(int n, boolean bl) {
        this.queue = new BlockingQueue(n, false);
        this.useAffinity = bl;
        this.initializePool(n);
        if (bl) {
            this.setAffinityLibraryLoging();
        }
    }

    private void setAffinityLibraryLoging() {
        java.util.logging.Logger logger = java.util.logging.Logger.getLogger(AffinityLock.class.getName());
        logger.setLevel(Level.WARNING);
    }

    private void initializePool(int n) {
        LOGGER.info("Preparing thread executors: {}", (Object)n);
        for (int i = 0; i < n; ++i) {
            this.prepareThreadExecutor(i);
        }
    }

    private void prepareThreadExecutor(int n) {
        TaskExecutor taskExecutor = new TaskExecutor(this.queue);
        String string = "Blocking computeThread common ";
        string = string + "#" + n;
        Thread thread = new Thread(taskExecutor, string);
        this.threads.add(thread);
        thread.start();
        LOGGER.debug("Preparing common thread executor: #{}", (Object)n);
    }

    private void prepareThreadExecutor(int n, Runnable runnable) {
        TaskExecutor taskExecutor = new TaskExecutor(runnable);
        String string = "Blocking computeThread additional ";
        string = string + "#" + n;
        Thread thread = new Thread(taskExecutor, string);
        this.threads.add(thread);
        thread.start();
        LOGGER.debug("Preparing one time additional thread executor: #{}", (Object)n);
    }

    @Override
    public void close() {
        LOGGER.debug("Cleaning the pool");
        this.shutdown = true;
        this.queue.clear();
        for (Thread thread : this.threads) {
            thread.interrupt();
        }
    }

    public void waitForTermination(long l) {
        for (Thread thread : this.threads) {
            try {
                thread.join(l);
                LOGGER.debug("Thread: {} finished.", (Object)thread.getName());
            }
            catch (InterruptedException interruptedException) {
                interruptedException.printStackTrace();
            }
        }
        this.threads.clear();
    }

    /*
     * WARNING - Removed try catching itself - possible behaviour change.
     */
    public void execute(Runnable runnable, boolean bl) {
        if (this.shutdown) {
            return;
        }
        try {
            BlockingQueue<Runnable> blockingQueue = this.queue;
            synchronized (blockingQueue) {
                if (bl) {
                    this.prepareThreadExecutor(this.additonalCount++, runnable);
                } else {
                    this.queue.enqueue(runnable);
                }
            }
        }
        catch (InterruptedException interruptedException) {
            LOGGER.error("", (Throwable)interruptedException);
        }
    }

    private class BlockingQueue<T> {
        private Queue<T> queue = new LinkedList<T>();
        private int maxTasksInPool;
        private boolean limitMax;

        public BlockingQueue(int n, boolean bl) {
            this.maxTasksInPool = n;
            this.limitMax = bl;
        }

        public synchronized void remove(T t) {
            this.queue.remove(t);
        }

        public synchronized void clear() {
            this.queue.clear();
        }

        public synchronized boolean isEmpty() {
            return this.queue.isEmpty();
        }

        public synchronized void enqueue(T t) throws InterruptedException {
            while (this.limitMax && this.queue.size() == this.maxTasksInPool) {
                this.wait();
            }
            if (this.queue.isEmpty()) {
                this.notifyAll();
            }
            this.queue.offer(t);
        }

        public synchronized T dequeue() throws InterruptedException {
            while (this.queue.isEmpty()) {
                this.wait();
            }
            if (this.limitMax && this.queue.size() == this.maxTasksInPool) {
                this.notifyAll();
            }
            return this.queue.poll();
        }
    }

    private class TaskExecutor
    implements Runnable {
        private BlockingQueue<Runnable> queue;
        private boolean additionalExecutor;
        private Runnable task;

        public TaskExecutor(BlockingQueue<Runnable> blockingQueue) {
            this.queue = blockingQueue;
            this.additionalExecutor = false;
        }

        public TaskExecutor(Runnable runnable) {
            this.task = runnable;
            this.additionalExecutor = true;
        }

        @Override
        public void run() {
            if (this.additionalExecutor) {
                this.runAdditionalExecutor();
            } else {
                this.runCommonExecutor();
            }
        }

        private void runAdditionalExecutor() {
            if (!ThreadPool.this.shutdown) {
                try {
                    this.task.run();
                }
                catch (Throwable throwable) {
                    LOGGER.error("Error while performing task!", throwable);
                }
                LOGGER.debug("Removing executor from pool.");
                if (!ThreadPool.this.shutdown) {
                    ThreadPool.this.threads.remove(Thread.currentThread());
                }
            }
            LOGGER.debug("Shutting thread in pool");
        }

        private void runCommonExecutor() {
            AffinityLock affinityLock = null;
            if (ThreadPool.this.useAffinity) {
                LOGGER.debug("Binding cpu's core");
                affinityLock = this.acquireLock();
            }
            try {
                while (!ThreadPool.this.shutdown) {
                    try {
                        Runnable runnable = this.queue.dequeue();
                        runnable.run();
                    }
                    catch (InterruptedException interruptedException) {
                    }
                    catch (Throwable throwable) {
                        LOGGER.error("Error while performing task!", throwable);
                    }
                }
                LOGGER.debug("Shutting thread in pool");
            }
            finally {
                if (affinityLock != null) {
                    LOGGER.debug("Releasing lock");
                    affinityLock.release();
                }
            }
        }

        private AffinityLock acquireLock() {
            try {
                return AffinityLock.acquireLock();
            }
            catch (Throwable throwable) {
                LOGGER.error("Error while acquiring affinity lock", throwable);
                return null;
            }
        }
    }
}

