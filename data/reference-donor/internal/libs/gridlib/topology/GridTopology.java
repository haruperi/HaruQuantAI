/*
 * Decompiled with CFR 0.152.
 */
package com.strategyquant.gridlib.topology;

import com.strategyquant.gridlib.topology.NodeInfo;
import java.io.Serializable;
import java.util.LinkedList;
import java.util.List;

public class GridTopology
implements Serializable {
    private static final long serialVersionUID = 1L;
    private List<NodeInfo> nodes = new LinkedList<NodeInfo>();
    private int totalCores;

    /*
     * WARNING - Removed try catching itself - possible behaviour change.
     */
    public int getRunningThreads() {
        GridTopology gridTopology = this;
        synchronized (gridTopology) {
            int n = 0;
            for (NodeInfo nodeInfo : this.nodes) {
                n += nodeInfo.getRunningThreads();
            }
            return n;
        }
    }

    /*
     * WARNING - Removed try catching itself - possible behaviour change.
     */
    public List<NodeInfo> getNodes() {
        GridTopology gridTopology = this;
        synchronized (gridTopology) {
            return this.nodes;
        }
    }

    /*
     * WARNING - Removed try catching itself - possible behaviour change.
     */
    public void setNodes(List<NodeInfo> list) {
        GridTopology gridTopology = this;
        synchronized (gridTopology) {
            this.nodes = list;
        }
    }

    public int getTotalCores() {
        return this.totalCores;
    }

    public void setTotalCores(int n) {
        this.totalCores = n;
    }
}

