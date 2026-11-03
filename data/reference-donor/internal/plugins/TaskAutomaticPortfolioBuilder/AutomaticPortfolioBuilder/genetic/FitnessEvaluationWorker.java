/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  org.uncommons.util.concurrent.ConfigurableThreadFactory
 *  org.uncommons.util.id.IDSource
 *  org.uncommons.util.id.IntSequenceIDSource
 *  org.uncommons.util.id.StringPrefixIDSource
 *  org.uncommons.watchmaker.framework.EvaluatedCandidate
 */
package com.strategyquant.plugin.Task.impl.AutomaticPortfolioBuilder.genetic;

import com.strategyquant.plugin.Task.impl.AutomaticPortfolioBuilder.genetic.FitnessEvalutationTask;
import java.util.concurrent.Future;
import java.util.concurrent.LinkedBlockingQueue;
import java.util.concurrent.ThreadFactory;
import java.util.concurrent.ThreadPoolExecutor;
import java.util.concurrent.TimeUnit;
import org.uncommons.util.concurrent.ConfigurableThreadFactory;
import org.uncommons.util.id.IDSource;
import org.uncommons.util.id.IntSequenceIDSource;
import org.uncommons.util.id.StringPrefixIDSource;
import org.uncommons.watchmaker.framework.EvaluatedCandidate;

public class FitnessEvaluationWorker {
    private static final IDSource<String> WORKER_ID_SOURCE = new StringPrefixIDSource("FitnessEvaluationWorker", (IDSource)new IntSequenceIDSource());
    private final LinkedBlockingQueue<Runnable> workQueue = new LinkedBlockingQueue();
    private final ThreadPoolExecutor executor;

    FitnessEvaluationWorker() {
        this(true);
    }

    private FitnessEvaluationWorker(boolean daemonWorkerThreads) {
        ConfigurableThreadFactory threadFactory = new ConfigurableThreadFactory((String)((Object)WORKER_ID_SOURCE.nextID()), 5, daemonWorkerThreads);
        this.executor = new ThreadPoolExecutor(Runtime.getRuntime().availableProcessors(), Runtime.getRuntime().availableProcessors(), 60L, TimeUnit.SECONDS, this.workQueue, (ThreadFactory)threadFactory);
        this.executor.prestartAllCoreThreads();
    }

    public <T> Future<EvaluatedCandidate<T>> submit(FitnessEvalutationTask<T> task) {
        return this.executor.submit(task);
    }

    public static void main(String[] args) {
        new FitnessEvaluationWorker(false);
    }

    protected void finalize() throws Throwable {
        this.executor.shutdown();
        super.finalize();
    }
}

