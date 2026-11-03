/*
 * Decompiled with CFR 0.152.
 */
package com.strategyquant.tradinglib.project;

import com.strategyquant.tradinglib.project.SQProject;
import java.util.Comparator;

public class ProjectNameComparator
implements Comparator<SQProject> {
    @Override
    public int compare(SQProject sQProject, SQProject sQProject2) {
        return sQProject.getName().compareToIgnoreCase(sQProject2.getName());
    }
}

