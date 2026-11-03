/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  com.strategyquant.datalib.TradingException
 *  com.strategyquant.datalib.basket.BasketDto
 *  com.strategyquant.datalib.basket.BasketOfStocksManager
 *  com.strategyquant.datalib.basket.StockDto
 *  com.strategyquant.gridlib.client.GridClient
 *  com.strategyquant.gridlib.client.JobDetails
 *  com.strategyquant.lib.L
 *  com.strategyquant.lib.SQTime
 *  com.strategyquant.lib.TaskStoppedException
 *  it.unimi.dsi.fastutil.longs.Long2IntMap
 *  it.unimi.dsi.fastutil.longs.Long2IntOpenHashMap
 *  it.unimi.dsi.fastutil.longs.LongAVLTreeSet
 *  org.slf4j.Logger
 *  org.slf4j.LoggerFactory
 */
package com.strategyquant.tradinglib.engine.stockpicker.data.timeline;

import com.strategyquant.datalib.TradingException;
import com.strategyquant.datalib.basket.BasketDto;
import com.strategyquant.datalib.basket.BasketOfStocksManager;
import com.strategyquant.datalib.basket.StockDto;
import com.strategyquant.gridlib.client.GridClient;
import com.strategyquant.gridlib.client.JobDetails;
import com.strategyquant.lib.L;
import com.strategyquant.lib.SQTime;
import com.strategyquant.lib.TaskStoppedException;
import com.strategyquant.tradinglib.engine.stockpicker.data.timeline.TimelineCalcJob;
import com.strategyquant.tradinglib.project.StopPauseEngine;
import com.strategyquant.tradinglib.simplegrid.SimpleGridEngine;
import it.unimi.dsi.fastutil.longs.Long2IntMap;
import it.unimi.dsi.fastutil.longs.Long2IntOpenHashMap;
import it.unimi.dsi.fastutil.longs.LongAVLTreeSet;
import java.util.ArrayList;
import java.util.Collections;
import java.util.List;
import java.util.Set;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

public class PickerDataTimeline {
    public static final Logger Log = LoggerFactory.getLogger(PickerDataTimeline.class);
    private int SizeD;
    private int SizeW;
    private int SizeM;
    private long[] TimeD;
    private long[] TimeW;
    private long[] TimeM;
    private BasketDto dto;
    private long dateFrom = -1L;
    private long dateTo = -1L;
    private Long2IntOpenHashMap TimeIndexD = new Long2IntOpenHashMap();
    private Long2IntOpenHashMap TimeIndexW = new Long2IntOpenHashMap();
    private Long2IntOpenHashMap TimeIndexM = new Long2IntOpenHashMap();
    Set<Long> tl = Collections.synchronizedSet(new LongAVLTreeSet());
    private int lastIndex;
    private double total;
    private double processed = 0.0;

    public void init(BasketDto basketDto, StopPauseEngine stopPauseEngine) throws Exception {
        this.dto = basketDto;
        try {
            long l2;
            this.runOnGrid(basketDto, stopPauseEngine);
            this.SizeD = this.tl.size();
            this.TimeD = new long[this.SizeD];
            int n = 0;
            for (long l2 : this.tl) {
                this.TimeIndexD.put(l2, n);
                this.TimeD[n] = l2;
                if (this.dateFrom < 0L) {
                    this.dateFrom = l2;
                }
                this.dateTo = l2;
                ++n;
            }
            if (this.dateFrom < 0L || this.dateTo < 0L) {
                throw new Exception(L.t((String)"No data found for stock group %s. Please updade data and try it again ...", (Object[])new Object[]{basketDto.getName()}));
            }
            this.SizeW = SQTime.getWeeksBetween((long)this.dateFrom, (long)this.dateTo) + 10;
            this.TimeW = new long[this.SizeW];
            l2 = SQTime.setFirstDayOfWeek((long)this.dateFrom);
            l2 = SQTime.getDateInMs((long)l2);
            n = 0;
            do {
                this.TimeIndexW.put(l2, n);
                this.TimeW[n] = l2;
                l2 = SQTime.addWeeks((long)l2, (int)1);
                ++n;
            } while (l2 <= this.dateTo);
            this.TimeIndexW.put(l2, n);
            this.TimeW[n] = l2;
            this.SizeM = SQTime.getMonthsBetween((long)this.dateFrom, (long)this.dateTo) + 10;
            this.TimeM = new long[this.SizeM];
            l2 = SQTime.setDayOfMonth((long)this.dateFrom, (int)1);
            l2 = SQTime.getDateInMs((long)l2);
            n = 0;
            do {
                this.TimeIndexM.put(l2, n);
                this.TimeM[n] = l2;
                l2 = SQTime.addMonths((long)l2, (int)1);
                ++n;
            } while (l2 <= this.dateTo);
            this.TimeIndexM.put(l2, n);
            this.TimeM[n] = l2;
            this.tl.clear();
            this.tl = null;
            Log.info("Created timeline for stockgroup {} from {} to {}, size {}", new Object[]{basketDto.getName(), SQTime.toDateString((long)this.dateFrom), SQTime.toDateString((long)this.dateTo), this.SizeD});
        }
        catch (Exception exception) {
            throw new Exception(L.t((String)"Error while generating picker timeline - %s", (Object[])new Object[]{exception.getMessage()}), exception);
        }
    }

    private void runOnGrid(BasketDto basketDto, final StopPauseEngine stopPauseEngine) throws Exception {
        this.lastIndex = 0;
        this.processed = 0.0;
        final List list = BasketOfStocksManager.getInstance().getStocks(basketDto.getId().intValue());
        this.total = list.size();
        SimpleGridEngine<TimelineCalcJob, String> simpleGridEngine = new SimpleGridEngine<TimelineCalcJob, String>(this, stopPauseEngine, null, false){
            final /* synthetic */ PickerDataTimeline this$0;
            {
                this.this$0 = pickerDataTimeline;
                super(stopPauseEngine3, gridJob, bl);
            }

            @Override
            protected ArrayList<TimelineCalcJob> createJobsBatch(int n, GridClient gridClient) throws Exception {
                return this.this$0.createBatch(n, list, stopPauseEngine);
            }

            @Override
            protected void processResult(String string, JobDetails jobDetails) throws Exception {
                PickerDataTimeline.access$008(this.this$0);
                Log.debug("Loaded symbols {}/{}", (Object)this.this$0.processed, (Object)this.this$0.total);
            }

            @Override
            protected void onError(String string, Exception exception) {
                Log.error("Timeline calc Error {}, Exception ", (Object)string, (Object)exception);
            }
        };
        simpleGridEngine.start();
        simpleGridEngine.unregisterListeners();
    }

    protected ArrayList<TimelineCalcJob> createBatch(int n, List<StockDto> list, StopPauseEngine stopPauseEngine) throws Exception {
        ArrayList<TimelineCalcJob> arrayList = new ArrayList<TimelineCalcJob>();
        int n2 = 0;
        for (int i = this.lastIndex; i < this.lastIndex + n && !((double)i >= this.total); ++i) {
            if (stopPauseEngine.isStopped()) {
                throw new TaskStoppedException();
            }
            StockDto stockDto = list.get(i);
            TimelineCalcJob timelineCalcJob = new TimelineCalcJob(stockDto.getTicker(), stockDto.getTicker() + i, this.tl, stopPauseEngine);
            arrayList.add(timelineCalcJob);
            ++n2;
        }
        this.lastIndex += n2;
        if (arrayList.size() == 0) {
            return null;
        }
        return arrayList;
    }

    public boolean containsTimeD(long l) throws TradingException {
        return this.TimeIndexD.containsKey(l);
    }

    public boolean containsTimeW(long l) throws TradingException {
        return this.TimeIndexW.containsKey(l);
    }

    public boolean containsTimeM(long l) throws TradingException {
        return this.TimeIndexM.containsKey(l);
    }

    public int timeToIndexD(long l) throws TradingException {
        if (!this.TimeIndexD.containsKey(l)) {
            throw new TradingException(String.format("Picker timeline->timeToIndexD() - Time not found %s.", SQTime.toFullDateTimeString((long)l)));
        }
        return this.TimeIndexD.get(l);
    }

    public int timeToIndexW(long l) throws TradingException {
        if (!this.TimeIndexW.containsKey(l)) {
            throw new TradingException(String.format("Picker timeline->timeToIndexW() - Time not found %s.", SQTime.toFullDateTimeString((long)l)));
        }
        return this.TimeIndexW.get(l);
    }

    public int timeToIndexM(long l) throws TradingException {
        if (!this.TimeIndexM.containsKey(l)) {
            throw new TradingException(String.format("Picker timeline->timeToIndexM() - Time not found %s.", SQTime.toFullDateTimeString((long)l)));
        }
        return this.TimeIndexM.get(l);
    }

    public long indexToTimeD(int n) throws TradingException {
        if (n < 0 || n >= this.TimeD.length) {
            return 0L;
        }
        return this.TimeD[n];
    }

    public long indexToTimeW(int n) throws TradingException {
        if (n < 0 || n >= this.TimeW.length) {
            return 0L;
        }
        return this.TimeW[n];
    }

    public long indexToTimeM(int n) throws TradingException {
        if (n < 0 || n >= this.TimeM.length) {
            return 0L;
        }
        return this.TimeM[n];
    }

    public int SizeD() {
        return this.SizeD;
    }

    public int SizeW() {
        return this.SizeW;
    }

    public int SizeM() {
        return this.SizeM;
    }

    public int searchIndexByTimeD(long l, boolean bl) throws TradingException {
        l = SQTime.getDateInMs((long)l);
        do {
            if (this.TimeIndexD.containsKey(l)) {
                return this.TimeIndexD.get(l);
            }
            l = SQTime.addDays((long)l, (int)(bl ? 1 : -1));
        } while ((bl || l >= this.dateFrom) && (!bl || l <= this.dateTo));
        throw new TradingException(String.format("Picker timeline->searchIndexByTimeD() - Time not found %s.", SQTime.toFullDateTimeString((long)l)));
    }

    public long dateFrom() {
        return this.dateFrom;
    }

    public long dateTo() {
        return this.dateTo;
    }

    public String toString() {
        return String.format("Timeline %s, date from %s to %s", this.dto.getName(), SQTime.toDateString((long)this.dateFrom), SQTime.toDateString((long)this.dateTo));
    }

    public PickerDataTimeline clone() {
        PickerDataTimeline pickerDataTimeline = new PickerDataTimeline();
        pickerDataTimeline.TimeD = this.TimeD != null ? (long[])this.TimeD.clone() : null;
        pickerDataTimeline.TimeW = this.TimeW != null ? (long[])this.TimeW.clone() : null;
        pickerDataTimeline.TimeM = this.TimeM != null ? (long[])this.TimeM.clone() : null;
        pickerDataTimeline.TimeIndexD = new Long2IntOpenHashMap((Long2IntMap)this.TimeIndexD);
        pickerDataTimeline.TimeIndexW = new Long2IntOpenHashMap((Long2IntMap)this.TimeIndexW);
        pickerDataTimeline.TimeIndexM = new Long2IntOpenHashMap((Long2IntMap)this.TimeIndexM);
        return pickerDataTimeline;
    }

    public void clear() {
    }

    static /* synthetic */ double access$008(PickerDataTimeline pickerDataTimeline) {
        double d = pickerDataTimeline.processed;
        pickerDataTimeline.processed = d + 1.0;
        return d;
    }
}

