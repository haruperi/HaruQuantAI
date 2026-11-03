/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  com.strategyquant.lib.L
 *  com.strategyquant.lib.SQUtils
 *  it.unimi.dsi.fastutil.ints.Int2DoubleOpenHashMap
 *  org.slf4j.Logger
 *  org.slf4j.LoggerFactory
 */
package com.strategyquant.tradinglib.databank;

import com.strategyquant.lib.L;
import com.strategyquant.lib.SQUtils;
import com.strategyquant.tradinglib.Databank;
import com.strategyquant.tradinglib.ResultsGroup;
import com.strategyquant.tradinglib.databank.DefaultDatabankFilter;
import com.strategyquant.tradinglib.databank.IDatabankFilter;
import com.strategyquant.tradinglib.databank.IProgressListener;
import it.unimi.dsi.fastutil.ints.Int2DoubleOpenHashMap;
import java.util.ArrayList;
import java.util.concurrent.locks.ReentrantReadWriteLock;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

public abstract class AbstractDatabankFilter
implements IDatabankFilter {
    public static final Logger Log = LoggerFactory.getLogger(DefaultDatabankFilter.class);
    protected Databank databank;
    protected int maxRecords = 1000;
    private Int2DoubleOpenHashMap rankValues = new Int2DoubleOpenHashMap();
    private ArrayList<String> strategiesSorted = new ArrayList();
    private Thread maxRecordsThread;
    private ReentrantReadWriteLock lock = new ReentrantReadWriteLock();

    public AbstractDatabankFilter(int n) {
        this.maxRecords = n;
    }

    @Override
    public void init(Databank databank) throws Exception {
        this.init(databank, null);
    }

    @Override
    public void init(Databank databank, IProgressListener iProgressListener) throws Exception {
        this.databank = databank;
        this.calculateRankValues();
        this.removeOverabundantResults(iProgressListener);
    }

    /*
     * WARNING - Removed try catching itself - possible behaviour change.
     */
    protected void calculateRankValues() {
        this.lock.writeLock().lock();
        try {
            this.rankValues.clear();
            this.strategiesSorted.clear();
            ArrayList<ResultsGroup> arrayList = this.databank.getRecords();
            for (int i = 0; i < arrayList.size(); ++i) {
                String string = arrayList.get(i).getName();
                int n = SQUtils.betterHashCode((String)string);
                double d = this.getRankValue(arrayList.get(i));
                this.insert(null, n, string, d);
            }
        }
        catch (Exception exception) {
            Log.error("Error while calculating rank values", (Throwable)exception);
        }
        finally {
            this.lock.writeLock().unlock();
        }
    }

    protected void removeWorseStrategy(String string) {
        this.lock.writeLock().lock();
        try {
            int n = SQUtils.betterHashCode((String)string);
            this.rankValues.remove(n);
            this.strategiesSorted.remove(string);
        }
        finally {
            this.lock.writeLock().unlock();
        }
    }

    public double getRankValue(ResultsGroup resultsGroup) {
        try {
            return resultsGroup.getFitness((byte)10);
        }
        catch (Exception exception) {
            Log.error("Cannot calculate rank value of strategy '" + resultsGroup.getName() + "'", (Throwable)exception);
            return 0.0;
        }
    }

    @Override
    public int getMaxStrategies() {
        return this.maxRecords;
    }

    @Override
    public void destroy() {
        this.lock.writeLock().lock();
        try {
            this.strategiesSorted.clear();
            this.rankValues.clear();
        }
        finally {
            this.lock.writeLock().unlock();
        }
    }

    @Override
    public boolean changeMaxRecords(int n, IProgressListener iProgressListener) throws Exception {
        if (this.databank.noActionRunning() && (this.maxRecordsThread == null || !this.maxRecordsThread.isAlive())) {
            this.maxRecords = n;
            if (this.databank.getRecords().size() > n) {
                this.removeOverabundantResults(iProgressListener);
                return true;
            }
        } else {
            throw new Exception(L.t((String)"Another databank action is already in progress.", (Object[])new Object[0]));
        }
        return false;
    }

    private void removeOverabundantResults(final IProgressListener iProgressListener) {
        this.maxRecordsThread = new Thread(this){
            final /* synthetic */ AbstractDatabankFilter this$0;
            {
                this.this$0 = abstractDatabankFilter;
            }

            /*
             * WARNING - Removed try catching itself - possible behaviour change.
             */
            @Override
            public void run() {
                this.this$0.lock.writeLock().lock();
                double d = 0.0;
                try {
                    int n = this.this$0.strategiesSorted.size() - this.this$0.maxRecords;
                    if (n <= 0) {
                        return;
                    }
                    for (int i = 0; i < n; ++i) {
                        String string = (String)this.this$0.strategiesSorted.remove(this.this$0.strategiesSorted.size() - 1);
                        this.this$0.rankValues.remove(SQUtils.betterHashCode((String)string));
                        this.this$0.databank.removeNoLock(string, true, false, true, "removeOverabundantResults");
                        d = ((double)i + 1.0) / (double)n * 100.0;
                        if (iProgressListener == null) continue;
                        iProgressListener.onProgress(d);
                    }
                    this.this$0.databank.refreshGrid();
                    if (iProgressListener != null) {
                        iProgressListener.onDone();
                    }
                }
                catch (Exception exception) {
                    Log.error("Error while removing overabundant results", (Throwable)exception);
                    if (iProgressListener != null) {
                        iProgressListener.onError(d, "Removing result failed. " + exception.getMessage());
                    }
                }
                finally {
                    this.this$0.lock.writeLock().unlock();
                }
            }
        };
        this.maxRecordsThread.start();
    }

    @Override
    public double getWorstFitness() {
        this.lock.readLock().lock();
        try {
            double d = this.getWorstRankValue();
            return d;
        }
        finally {
            this.lock.readLock().unlock();
        }
    }

    /*
     * WARNING - Removed try catching itself - possible behaviour change.
     */
    public double getWorstRankValue() {
        this.lock.readLock().lock();
        String string = null;
        try {
            if (this.strategiesSorted == null) {
                Log.error("Strategies sorted is null");
                double d = 0.0;
                return d;
            }
            if (this.strategiesSorted.size() == 0) {
                double d = 0.0;
                return d;
            }
            int n = this.strategiesSorted.size() - 1;
            string = this.strategiesSorted.get(n);
            double d = this.rankValues.get(SQUtils.betterHashCode((String)string));
            return d;
        }
        finally {
            this.lock.readLock().unlock();
        }
    }

    public String getWorstStrategy() {
        this.lock.readLock().lock();
        try {
            String string = this.strategiesSorted.size() > 0 ? this.strategiesSorted.get(this.strategiesSorted.size() - 1) : null;
            return string;
        }
        finally {
            this.lock.readLock().unlock();
        }
    }

    /*
     * WARNING - Removed try catching itself - possible behaviour change.
     */
    protected double getWorstRankValue(String string) {
        this.lock.readLock().lock();
        try {
            if (this.rankValues == null) {
                Log.error("rankValues is null");
                double d = 0.0;
                return d;
            }
            double d = this.rankValues.get(SQUtils.betterHashCode((String)string));
            return d;
        }
        finally {
            this.lock.readLock().unlock();
        }
    }

    /*
     * WARNING - Removed try catching itself - possible behaviour change.
     */
    protected boolean hasWorseRankValue(ArrayList<String> arrayList, double d) {
        this.lock.readLock().lock();
        try {
            int n;
            if (this.rankValues == null) {
                Log.error("rankValues is null");
                boolean bl = true;
                return bl;
            }
            for (n = 0; n < arrayList.size(); ++n) {
                double d2;
                String string = arrayList.get(n);
                int n2 = SQUtils.betterHashCode((String)string);
                if (!this.rankValues.containsKey(n2) || !((d2 = this.rankValues.get(n2)) < d)) continue;
                boolean bl = true;
                return bl;
            }
            n = 0;
            return n != 0;
        }
        finally {
            this.lock.readLock().unlock();
        }
    }

    /*
     * WARNING - Removed try catching itself - possible behaviour change.
     */
    protected String getStrategyWithWorseRank(ArrayList<String> arrayList, double d) {
        this.lock.readLock().lock();
        try {
            if (this.rankValues == null) {
                Log.error("rankValues is null");
                String string = null;
                return string;
            }
            for (int i = 0; i < arrayList.size(); ++i) {
                double d2;
                String string = arrayList.get(i);
                int n = SQUtils.betterHashCode((String)string);
                if (!this.rankValues.containsKey(n) || !((d2 = this.rankValues.get(n)) < d)) continue;
                String string2 = string;
                return string2;
            }
            String string = null;
            return string;
        }
        finally {
            this.lock.readLock().unlock();
        }
    }

    /*
     * WARNING - Removed try catching itself - possible behaviour change.
     */
    protected String getWorstStrategy(ArrayList<String> arrayList) {
        this.lock.readLock().lock();
        try {
            for (int i = this.strategiesSorted.size() - 1; i >= 0; --i) {
                String string = this.strategiesSorted.get(i);
                if (!arrayList.contains(string)) continue;
                String string2 = string;
                return string2;
            }
            String string = null;
            return string;
        }
        finally {
            this.lock.readLock().unlock();
        }
    }

    @Override
    public void onRemove(String string) {
        this.lock.writeLock().lock();
        try {
            this.rankValues.remove(SQUtils.betterHashCode((String)string));
            this.strategiesSorted.remove(string);
        }
        finally {
            this.lock.writeLock().unlock();
        }
    }

    /*
     * WARNING - Removed try catching itself - possible behaviour change.
     */
    @Override
    public boolean onAdd(ResultsGroup resultsGroup) {
        double d = this.getRankValue(resultsGroup);
        String string = resultsGroup.getName();
        this.lock.writeLock().lock();
        try {
            if (this.addStrategy(resultsGroup, d)) {
                int n = SQUtils.betterHashCode((String)string);
                this.insert(resultsGroup, n, string, d);
                boolean bl = true;
                return bl;
            }
            boolean bl = false;
            return bl;
        }
        catch (Exception exception) {
            Log.error("Error while adding strategy", (Throwable)exception);
            boolean bl = false;
            return bl;
        }
        finally {
            this.lock.writeLock().unlock();
        }
    }

    @Override
    public boolean checkShouldAdd(ResultsGroup resultsGroup) {
        double d = this.getRankValue(resultsGroup);
        return this.shouldAddStrategy(resultsGroup, d);
    }

    /*
     * WARNING - Removed try catching itself - possible behaviour change.
     */
    @Override
    public void onUpdate(ResultsGroup resultsGroup) {
        this.lock.writeLock().lock();
        try {
            String string = resultsGroup.getName();
            double d = this.getRankValue(resultsGroup);
            int n = SQUtils.betterHashCode((String)string);
            if (this.strategiesSorted.size() > 1) {
                this.strategiesSorted.remove(string);
                this.insert(resultsGroup, n, string, d);
            } else {
                this.rankValues.put(n, d);
            }
        }
        catch (Exception exception) {
            Log.error("Error while updating strategy", (Throwable)exception);
        }
        finally {
            this.lock.writeLock().unlock();
        }
    }

    protected void insert(ResultsGroup resultsGroup, int n, String string, double d) {
        boolean bl = false;
        for (int i = 0; i < this.strategiesSorted.size(); ++i) {
            String string2 = this.strategiesSorted.get(i);
            double d2 = this.rankValues.get(SQUtils.betterHashCode((String)string2));
            if (!(d2 < d)) continue;
            this.strategiesSorted.add(i, string);
            bl = true;
            break;
        }
        if (!bl) {
            this.strategiesSorted.add(string);
        }
        this.rankValues.put(n, d);
        this.actionOnInsert(resultsGroup);
    }

    protected void actionOnInsert(ResultsGroup resultsGroup) {
    }

    protected abstract boolean shouldAddStrategy(ResultsGroup var1, double var2);

    protected abstract boolean addStrategy(ResultsGroup var1, double var2) throws Exception;
}

