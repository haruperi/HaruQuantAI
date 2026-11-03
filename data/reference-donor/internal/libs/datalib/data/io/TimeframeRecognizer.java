/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  org.slf4j.Logger
 *  org.slf4j.LoggerFactory
 */
package com.strategyquant.datalib.data.io;

import com.strategyquant.datalib.TimeframeManager;
import java.util.HashMap;
import java.util.Map;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

public class TimeframeRecognizer {
    public static final Logger Log = LoggerFactory.getLogger((String)"TimeframeRecognizer");
    private long previousTime;
    private HashMap<Long, Integer> gapCounts = new HashMap();

    public void reset() {
        this.previousTime = 0L;
        this.gapCounts.clear();
    }

    public void processTime(long l) {
        if (this.previousTime != 0L) {
            Long l2 = Math.abs(l - this.previousTime);
            if (l2 > 80000000L && l2 < 92000000L) {
                l2 = new Long(86400000L);
            }
            if (l2 > 160000000L && l2 < 184000000L) {
                l2 = new Long(172800000L);
            }
            if (this.gapCounts.containsKey(l2)) {
                this.gapCounts.put(l2, new Integer(this.gapCounts.get(l2) + 1));
            } else {
                this.gapCounts.put(l2, new Integer(1));
            }
        }
        this.previousTime = l;
    }

    public String getTimeframe() {
        int n = (int)(this.getAverageGapBetweenLines() / 60000L);
        return TimeframeManager.getTFName(n * 60000);
    }

    private long getAverageGapBetweenLines() {
        if (this.gapCounts.size() == 0) {
            return -1L;
        }
        long l = 0L;
        long l2 = 0L;
        int n = 0;
        int n2 = 0;
        for (Map.Entry<Long, Integer> entry : this.gapCounts.entrySet()) {
            long l3 = entry.getKey();
            int n3 = entry.getValue();
            ++n;
            n2 += n3;
            Log.debug("Gap: {} , Count: {}", (Object)l3, (Object)n3);
            if ((long)n3 <= l) continue;
            l = n3;
            l2 = l3;
        }
        Log.info("Total gaps: {}, most frequent gap: {} - in {} cases", new Object[]{n, l2, l});
        if (l > (long)(n / 2)) {
            Log.info("Gap {} is in more than 50% of data, it is probably the one", (Object)l2);
            return l2;
        }
        if (n > 200) {
            return -60000L;
        }
        if (n > 8 * (n2 /= 100)) {
            return -60000L;
        }
        return l2;
    }
}

