/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  com.strategyquant.gridlib.client.GridJob
 *  com.strategyquant.gridlib.client.GridMessage
 *  org.slf4j.Logger
 *  org.slf4j.LoggerFactory
 */
package com.strategyquant.tradinglib.gp;

import com.strategyquant.gridlib.client.GridJob;
import com.strategyquant.gridlib.client.GridMessage;
import com.strategyquant.tradinglib.gp.IFitnessEvaluator;
import com.strategyquant.tradinglib.gp.IGPNode;
import java.io.Serializable;
import java.util.Map;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

public class GPEvaluationJob<T extends IGPNode>
extends GridJob<T> {
    private static final Logger Log = LoggerFactory.getLogger((String)"GPEvaluationJob");
    private IFitnessEvaluator<? super T> evaluator;
    private T candidate;
    private int populationType;
    private boolean sendLastPopulation;

    public GPEvaluationJob(String string, Map<String, Serializable> map) {
        super(string, 1, map);
        this.evaluator = (IFitnessEvaluator)map.get("evaluator");
        this.candidate = (IGPNode)map.get("candidate");
        this.populationType = (Integer)map.get("populationType");
        this.sendLastPopulation = (Boolean)map.get("sendLastPopulation");
    }

    public T call() throws Exception {
        T t = this.evaluator.evaluateCandidate(this.candidate, this.populationType, this, this.sendLastPopulation);
        return t;
    }

    public void messageReceived(GridMessage gridMessage) {
        if (gridMessage.getMessageID() == 4) {
            this.evaluator.stop();
            this.destroy();
        }
    }

    public void destroy() {
        if (Log.isDebugEnabled()) {
            Log.debug("Job {} destroyed", (Object)this.getJobId());
        }
        if (this.evaluator != null) {
            if (Log.isDebugEnabled()) {
                Log.debug(" - Job {} evaluator destroyed", (Object)this.getJobId());
            }
            this.evaluator.destroy();
        }
    }
}

