/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  com.strategyquant.gridlib.client.GridClient
 *  com.strategyquant.gridlib.client.GridJob
 *  com.strategyquant.gridlib.client.GridMessage
 *  com.strategyquant.gridlib.client.IGridMessageListener
 *  com.strategyquant.gridlib.client.JobDetails
 *  com.strategyquant.gridlib.client.SQGrid
 *  com.strategyquant.lib.SQUtils
 *  it.unimi.dsi.fastutil.ints.Int2IntOpenHashMap
 *  it.unimi.dsi.fastutil.ints.Int2ObjectOpenHashMap
 *  it.unimi.dsi.fastutil.ints.IntOpenHashSet
 *  org.slf4j.Logger
 *  org.slf4j.LoggerFactory
 */
package com.strategyquant.tradinglib.gp;

import com.strategyquant.gridlib.client.GridClient;
import com.strategyquant.gridlib.client.GridJob;
import com.strategyquant.gridlib.client.GridMessage;
import com.strategyquant.gridlib.client.IGridMessageListener;
import com.strategyquant.gridlib.client.JobDetails;
import com.strategyquant.gridlib.client.SQGrid;
import com.strategyquant.lib.SQUtils;
import com.strategyquant.tradinglib.gp.GPEvaluationJob;
import com.strategyquant.tradinglib.gp.GPEvolutionMessage;
import com.strategyquant.tradinglib.gp.GPEvolutionPopulationMessage;
import com.strategyquant.tradinglib.gp.GPFitnessComparator;
import com.strategyquant.tradinglib.gp.GPFitnessEvolution;
import com.strategyquant.tradinglib.gp.GPFitnessEvolutionData;
import com.strategyquant.tradinglib.gp.GPIDs;
import com.strategyquant.tradinglib.gp.GPIslandJob;
import com.strategyquant.tradinglib.gp.GPSettings;
import com.strategyquant.tradinglib.gp.IGPNode;
import it.unimi.dsi.fastutil.ints.Int2IntOpenHashMap;
import it.unimi.dsi.fastutil.ints.Int2ObjectOpenHashMap;
import it.unimi.dsi.fastutil.ints.IntOpenHashSet;
import java.io.Serializable;
import java.util.ArrayList;
import java.util.Collections;
import java.util.HashMap;
import java.util.Iterator;
import java.util.List;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

public class GPGenerationalEngine<T extends IGPNode> {
    private static final Logger Log = LoggerFactory.getLogger((String)"GPGenerationalEngine");
    private static final int StatusRunning = 1;
    private static final int StatusPaused = 2;
    private static final int StatusStopped = 3;
    private GPSettings<T> gpSettings;
    private int islandIndex;
    private int currentGeneration;
    private GridClient gridClient;
    private String evaluationGroupID;
    private int runningStatus = 0;
    private ArrayList<T> initialPopulation = null;
    private ArrayList<T> population = new ArrayList();
    private ArrayList<T> candidatesInbox = new ArrayList();
    private Int2IntOpenHashMap similarStrategiesMap = new Int2IntOpenHashMap();
    private String gpGroupID;
    private GPFitnessComparator<T> gpComparator;
    private double thresholdFitness = 0.0;
    private int initialPopulationSize = 0;
    private Int2ObjectOpenHashMap<T> computedFitnessMap = new Int2ObjectOpenHashMap();
    private GPIslandJob<T> gpIslandJob;
    private GridJob parentGridJob;
    private String islandJobID;
    private int lastCheckedGeneration;
    private int restartReason;
    private int finishedJobs;
    private IntOpenHashSet uniqueTopStrategies = new IntOpenHashSet();
    private GPFitnessEvolution<T> gpFitnessEvolution;
    private String source;

    public GPGenerationalEngine(GPIslandJob<T> gPIslandJob, GPSettings<T> gPSettings, String string, String string2, String string3, int n, ArrayList<T> arrayList, GridJob gridJob) {
        this.gpIslandJob = gPIslandJob;
        this.gpSettings = gPSettings;
        this.islandIndex = n;
        this.gpGroupID = string;
        this.islandJobID = string2;
        this.parentGridJob = gridJob;
        this.source = string3;
        this.initialPopulation = arrayList;
        if (arrayList != null) {
            this.initialPopulationSize = arrayList.size();
        }
        this.gpFitnessEvolution = new GPFitnessEvolution<T>(n, gPSettings);
        this.evaluationGroupID = GPGenerationalEngine.getEvaluationGroupID(string, string2);
        this.gpComparator = new GPFitnessComparator(gPSettings.naturalFitness, 11);
        this.gridClient = SQGrid.getGridClient();
        this.gridClient.registerMessageListener(this.evaluationGroupID, new IGridMessageListener(){

            public void messageReceived(GridMessage gridMessage) {
                GPGenerationalEngine.this.processMessage(gridMessage);
            }
        });
    }

    public static String getEvaluationGroupID(String string, String string2) {
        return String.format("%s_%s", string, string2);
    }

    public void evolve() throws Exception {
        try {
            this.runningStatus = 1;
            do {
                Object object;
                this.gpEvolution();
                if (this.checkStopped()) {
                    break;
                }
                if (this.restartReason == 70) {
                    object = String.format("-- Evolution on island #%d restarted because of stagnation", this.islandIndex + 1);
                    Log.debug((String)object);
                    this.sendEvolutionStatusMessage(70, (String)object);
                    continue;
                }
                if (!this.gpSettings.restartOnFinish) {
                    break;
                }
                object = String.format("-- Evolution on island #%d ended, restarted again", this.islandIndex + 1);
                this.sendEvolutionStatusMessage(60, (String)object);
            } while (this.gpSettings.restartOnFinish || this.gpSettings.restartOnStagnation);
        }
        catch (Exception exception) {
            if (exception instanceof InterruptedException) {
            } else {
                Log.error("Error", (Throwable)exception);
                GridMessage gridMessage = new GridMessage(5, "GPException", (Serializable)((Object)SQUtils.getStackTrace((Throwable)exception)));
                this.gridClient.sendMessage(this.gpGroupID, null, gridMessage);
            }
        }
        finally {
            this.gridClient.stop(this.evaluationGroupID);
            this.gridClient.removeMessageListener(this.evaluationGroupID);
            GridMessage gridMessage = new GridMessage(1);
            this.gridClient.sendMessage(this.gpGroupID, null, gridMessage);
        }
    }

    private void gpEvolution() throws Exception {
        this.gpFitnessEvolution.reset();
        this.clearFromPreviousEvolution();
        this.generateInitialPopulation();
        this.sortEvaluatedPopulation();
        this.decimateInitialPopulation();
        this.addExistingInitialPopulation();
        this.sendLastPopulation();
        while (true) {
            this.gpFitnessEvolution.computeFitnessData(this.population, this.currentGeneration);
            this.sortEvaluatedPopulation();
            ++this.currentGeneration;
            if (this.currentGeneration > this.gpSettings.maxGenerations) break;
            this.checkPaused();
            if (this.checkStopped()) break;
            this.sendEvolutionStatusMessage(30, String.format("-- Evolving generation %d population for island #%d", this.currentGeneration, this.islandIndex + 1));
            this.nextEvolutionStep();
            if (this.gpFitnessEvolution.isStagnating()) {
                this.restartReason = 70;
                break;
            }
            this.sendLastPopulation();
        }
        this.clearFromPreviousEvolution();
        this.sendEvolutionStatusMessage(40, String.format("-- Evolution on island #%d finished", this.islandIndex + 1));
    }

    private void clearFromPreviousEvolution() {
        this.currentGeneration = 0;
        this.restartReason = 0;
        if (this.computedFitnessMap != null) {
            this.computedFitnessMap.clear();
        }
        this.clearPopulation();
        if (this.candidatesInbox != null) {
            this.candidatesInbox.clear();
        }
    }

    private void clearPopulation() {
        if (this.population != null) {
            for (int i = 0; i < this.population.size(); ++i) {
                IGPNode iGPNode = (IGPNode)this.population.get(i);
                iGPNode.destroy();
            }
            this.population.clear();
        }
    }

    private void nextEvolutionStep() throws Exception {
        this.receiveImmigrants();
        ArrayList<IGPNode> arrayList = new ArrayList<IGPNode>(this.gpSettings.elitismSize);
        Iterator<T> iterator = this.population.iterator();
        while (arrayList.size() < this.gpSettings.elitismSize && !this.checkStopped()) {
            if (!iterator.hasNext()) continue;
            arrayList.add((IGPNode)iterator.next());
        }
        List<Object> list = new ArrayList(this.population.size());
        list.addAll(this.gpSettings.selectionStrategy.select(this.population, this.gpSettings.naturalFitness, this.population.size() - this.gpSettings.elitismSize, this.gpSettings.rng, arrayList));
        ArrayList arrayList2 = new ArrayList(list);
        list = this.gpSettings.evolutionPipeline.apply(list, this.gpSettings.rng, this.gpSettings.factory, this.islandIndex, this.currentGeneration);
        list.addAll(arrayList);
        this.moveNewPopulationToGlobalPopulation(list);
        this.destroyUnusedCandidates(this.population, arrayList2);
        list.clear();
        this.evaluatePopulation(3);
        this.sortEvaluatedPopulation();
        this.processFreshBloodSettings();
        this.migrateIndividuals();
    }

    private void destroyUnusedCandidates(List<T> list, ArrayList<T> arrayList) {
        for (int i = 0; i < arrayList.size(); ++i) {
            IGPNode iGPNode = (IGPNode)arrayList.get(i);
            String string = iGPNode.getGPIDs().toShortString();
            if (this.existsInNewPopulation(iGPNode, list)) continue;
            iGPNode.destroy();
        }
    }

    private void processFreshBloodSettings() throws Exception {
        if (this.gpSettings.freshBloodReplaceSimilar) {
            this.removeTooSimilarStrategies();
        }
        if (this.gpSettings.freshBloodReplaceWeakest) {
            this.removeWeakestStrategies();
        }
        if (this.population.size() < this.gpSettings.populationSize) {
            this.generateAdditionalCandidates();
        }
    }

    private void removeTooSimilarStrategies() throws Exception {
        int n = 2;
        this.similarStrategiesMap.clear();
        Iterator<T> iterator = this.population.iterator();
        while (iterator.hasNext()) {
            IGPNode iGPNode = (IGPNode)iterator.next();
            if (iGPNode.getFitness((byte)11) == 0.0) {
                iGPNode.destroy();
                iterator.remove();
                continue;
            }
            int n2 = iGPNode.getFingerprint();
            if (!this.similarStrategiesMap.containsKey(n2)) {
                this.similarStrategiesMap.put(n2, 1);
                continue;
            }
            int n3 = this.similarStrategiesMap.get(n2);
            if (n3 < n) {
                this.similarStrategiesMap.put(n2, n3 + 1);
                continue;
            }
            iGPNode.destroy();
            iterator.remove();
        }
    }

    private void removeWeakestStrategies() throws Exception {
        int n;
        int n2;
        if (this.currentGeneration == 0 || this.currentGeneration % this.gpSettings.replaceWeakestGenerations != 0) {
            return;
        }
        double d = (double)Math.min(this.gpSettings.replaceWeakestPct, 50) / 100.0;
        int n3 = 0;
        if (d > 0.0) {
            n3 = (int)(d * (double)this.gpSettings.populationSize);
        }
        if (n3 == 0) {
            n3 = 1;
        }
        if ((n2 = n3 - (n = this.gpSettings.populationSize - this.population.size())) <= 0) {
            return;
        }
        for (int i = 0; i < n2; ++i) {
            if (this.population.size() <= 0) continue;
            int n4 = this.population.size() - 1;
            IGPNode iGPNode = (IGPNode)this.population.get(n4);
            iGPNode.destroy();
            this.population.remove(n4);
        }
    }

    private void generateAdditionalCandidates() throws Exception {
        this.sendEvolutionStatusMessage(80, String.format("-- Generating additional population for island #%d", this.islandIndex + 1));
        GPIDs gPIDs = new GPIDs();
        gPIDs.islandIndex = this.islandIndex;
        gPIDs.generationIndex = 0;
        gPIDs.generationType = "Initial";
        int n = this.gpSettings.populationSize;
        int n2 = this.population.size();
        ArrayList arrayList = new ArrayList();
        while (true) {
            Log.debug("Generating additional - current population: {}, required: {}", (Object)this.population.size(), (Object)n);
            if (this.population.size() >= n) {
                this.gpSettings.factory.generateRandomCandidate(this.gpSettings.rng);
                break;
            }
            this.checkPaused();
            if (this.checkStopped()) break;
            int n3 = n - this.population.size();
            if (n3 > this.gridClient.getUsedComputedThreads() * 2) {
                n3 = this.gridClient.getUsedComputedThreads() * 2;
            }
            arrayList.clear();
            for (int i = 0; i < n3; ++i) {
                Object t = this.gpSettings.factory.generateRandomCandidate(this.gpSettings.rng);
                gPIDs.nodeIndex = n2;
                t.setGPIDs(gPIDs);
                if (Log.isDebugEnabled()) {
                    Log.debug("Generated Candidate " + t.getAsString() + " - " + t.toString());
                }
                ++n2;
                arrayList.add(t);
            }
            this.sendEvolutionStatusMessage(90, null);
            this.evaluateGeneratedInitialPopulation(arrayList);
        }
        this.sendEvolutionStatusMessage(100, String.format("-- Additional population for island #%d generated", this.islandIndex + 1));
    }

    private void moveNewPopulationToGlobalPopulation(List<T> list) {
        for (int i = 0; i < this.population.size(); ++i) {
            IGPNode iGPNode = (IGPNode)this.population.get(i);
            if (this.existsInNewPopulation(iGPNode, list)) continue;
            iGPNode.destroy();
        }
        this.population.clear();
        this.population.addAll(list);
    }

    private boolean existsInNewPopulation(T t, List<T> list) {
        for (int i = 0; i < list.size(); ++i) {
            if (t != list.get(i)) continue;
            return true;
        }
        return false;
    }

    /*
     * WARNING - Removed try catching itself - possible behaviour change.
     */
    private void printPopulation(String string) {
        if (this.gpSettings.printPopulationToLog) {
            Logger logger = Log;
            synchronized (logger) {
                if (Log.isDebugEnabled()) {
                    Log.debug("---------------------------------------------------------");
                    Log.debug("--- Population for island : " + this.islandIndex + " generation: " + this.currentGeneration);
                    Log.debug("--- Text : " + string);
                    Log.debug("---------------------------------------------------------");
                    for (int i = 0; i < this.population.size(); ++i) {
                        IGPNode iGPNode = (IGPNode)this.population.get(i);
                        Log.debug("Candidate " + iGPNode.getAsString() + " - fitness: " + iGPNode.getFitness((byte)11) + " - " + iGPNode.toString());
                    }
                    Log.debug("---------------------------------------------------------");
                }
            }
        }
    }

    private void printPopulation2(String string, ArrayList<T> arrayList) {
        Log.info("---------------------------------------------------------");
        Log.info("--- Population for island : " + this.islandIndex + " generation: " + this.currentGeneration);
        Log.info("--- Text : " + string);
        Log.info("---------------------------------------------------------");
        for (int i = 0; i < arrayList.size(); ++i) {
            IGPNode iGPNode = (IGPNode)arrayList.get(i);
            Log.info("Candidate {} - fitness IST: {}, IS: {}, ISV: {}, OOS: {} - {}", new Object[]{iGPNode.getAsString(), iGPNode.getFitness((byte)11), iGPNode.getFitness((byte)10), iGPNode.getFitness((byte)40), iGPNode.getFitness((byte)20), iGPNode.toString()});
        }
        Log.info("---------------------------------------------------------");
    }

    private void migrateIndividuals() throws Exception {
        if (this.gpSettings.numberOfIslands == 1) {
            return;
        }
        if (this.gpSettings.migrationRate == 0.0) {
            return;
        }
        if (this.currentGeneration == 0 || this.currentGeneration % this.gpSettings.migrationGenerationsModulo != 0) {
            return;
        }
        int n = (int)((double)this.population.size() * this.gpSettings.migrationRate);
        if (this.gpSettings.migrationRate > 0.0 && n == 0) {
            n = 1;
        }
        ArrayList<IGPNode> arrayList = new ArrayList<IGPNode>();
        if (n > 0) {
            for (int i = 0; i < n; ++i) {
                IGPNode iGPNode = ((IGPNode)this.population.get(i)).cloneForMigration();
                arrayList.add(iGPNode);
            }
            this.sendMigrationCandidates(arrayList);
        }
    }

    private void decimateInitialPopulation() {
        int n = this.population.size() - this.gpSettings.populationSize + this.initialPopulationSize;
        for (int i = 0; i < n; ++i) {
            if (this.population.isEmpty()) {
                return;
            }
            int n2 = this.population.size() - 1;
            ((IGPNode)this.population.get(n2)).destroy();
            this.population.remove(n2);
        }
    }

    private void sortEvaluatedPopulation() {
        Collections.sort(this.population, this.gpComparator);
    }

    private void generateInitialPopulation() throws Exception {
        this.population.clear();
        this.candidatesInbox.clear();
        this.sendEvolutionStatusMessage(10, String.format("-- Generating initial population for island #%d", this.islandIndex + 1));
        if (this.gpSettings.decimationCoefficient <= 0) {
            this.gpSettings.decimationCoefficient = 1;
        }
        GPIDs gPIDs = new GPIDs();
        gPIDs.islandIndex = this.islandIndex;
        gPIDs.generationIndex = 0;
        gPIDs.generationType = "Initial";
        int n = (this.gpSettings.populationSize - this.initialPopulationSize) * this.gpSettings.decimationCoefficient;
        int n2 = this.population.size();
        ArrayList arrayList = new ArrayList();
        while (true) {
            Log.debug("Generating initial - current population: {}, required: {}", (Object)this.population.size(), (Object)n);
            if (this.population.size() >= n) {
                this.gpSettings.factory.generateRandomCandidate(this.gpSettings.rng);
                break;
            }
            this.checkPaused();
            if (this.checkStopped()) break;
            int n3 = n - this.population.size();
            if (n3 < 5) {
                n3 *= 2;
            } else if (n3 < 3) {
                n3 *= 4;
            }
            if (n3 > this.gridClient.getUsedComputedThreads() * 2) {
                n3 = this.gridClient.getUsedComputedThreads() * 2;
            }
            arrayList.clear();
            for (int i = 0; i < n3; ++i) {
                Object t = this.gpSettings.factory.generateRandomCandidate(this.gpSettings.rng);
                gPIDs.nodeIndex = n2;
                t.setGPIDs(gPIDs);
                if (Log.isDebugEnabled()) {
                    Log.debug("Generated Candidate " + t.getAsString() + " - " + t.toString());
                }
                ++n2;
                arrayList.add(t);
            }
            this.sendEvolutionStatusMessage(50, null);
            this.evaluateGeneratedInitialPopulation(arrayList);
        }
        this.sendEvolutionStatusMessage(20, String.format("-- Initial population for island #%d generated", this.islandIndex + 1));
    }

    private void addExistingInitialPopulation() throws Exception {
        if (this.initialPopulationSize == 0 || this.initialPopulation == null) {
            return;
        }
        GPIDs gPIDs = new GPIDs();
        gPIDs.islandIndex = this.islandIndex;
        gPIDs.generationIndex = 0;
        gPIDs.generationType = "Initial";
        int n = this.findBiggestExistingNodeIndexInPopulation();
        Collections.shuffle(this.initialPopulation);
        for (IGPNode iGPNode : this.initialPopulation) {
            if (this.population.size() >= this.gpSettings.populationSize) break;
            IGPNode iGPNode2 = iGPNode.clonePassed();
            gPIDs.nodeIndex = ++n;
            iGPNode2.setGPIDs(gPIDs);
            this.population.add(iGPNode2);
        }
        this.evaluatePopulation(2);
        this.sortEvaluatedPopulation();
    }

    private int findBiggestExistingNodeIndexInPopulation() {
        int n = 0;
        for (IGPNode iGPNode : this.population) {
            GPIDs gPIDs = iGPNode.getGPIDs();
            if (gPIDs.nodeIndex <= n) continue;
            n = gPIDs.nodeIndex;
        }
        return n;
    }

    private void evaluatePopulation(int n) throws Exception {
        int n2;
        IGPNode iGPNode;
        int n3;
        ArrayList<GPEvaluationJob<T>> arrayList = new ArrayList<GPEvaluationJob<T>>();
        for (n3 = 0; n3 < this.population.size(); ++n3) {
            iGPNode = (IGPNode)this.population.get(n3);
            n2 = iGPNode.getHash();
            if (!(iGPNode.getFitness((byte)11) >= 0.0) || this.computedFitnessMap.containsKey(n2)) continue;
            this.computedFitnessMap.put(n2, (Object)iGPNode);
        }
        for (n3 = 0; n3 < this.population.size(); ++n3) {
            Object object;
            iGPNode = (IGPNode)this.population.get(n3);
            if (!(iGPNode.getFitness((byte)11) < 0.0)) continue;
            n2 = iGPNode.getHash();
            if (this.computedFitnessMap.containsKey(n2)) {
                object = (IGPNode)this.computedFitnessMap.get(n2);
                iGPNode.setFitness((IGPNode)object);
                continue;
            }
            object = iGPNode.getGPIDs();
            String string = String.format("%s-Generation %d.%d.%d", this.gpIslandJob.getJobId(), ((GPIDs)object).islandIndex + 1, ((GPIDs)object).generationIndex, ((GPIDs)object).nodeIndex);
            HashMap<String, Serializable> hashMap = new HashMap<String, Serializable>();
            hashMap.put("evaluator", (Serializable)this.gpSettings.evaluator.getClone());
            hashMap.put("candidate", iGPNode);
            hashMap.put("populationType", Integer.valueOf(n));
            hashMap.put("sendLastPopulation", Boolean.valueOf(this.gpSettings.sendLastPopulation));
            GPEvaluationJob gPEvaluationJob = new GPEvaluationJob(string, hashMap);
            if (this.parentGridJob != null) {
                gPEvaluationJob.setPriority(this.parentGridJob.getPriority() + 1);
            }
            arrayList.add(gPEvaluationJob);
        }
        Log.debug("Created {} evaluation jobs in island {}", (Object)arrayList.size(), (Object)(this.islandIndex + 1));
        if (arrayList.size() == 0) {
            return;
        }
        this.removeUncomputedFitnessCandidates();
        if (this.gpSettings.singleThreaded) {
            this.executeInSingleThread(arrayList);
        } else {
            this.executeInGrid(arrayList);
        }
    }

    private void evaluateGeneratedInitialPopulation(ArrayList<T> arrayList) throws Exception {
        int n = 1;
        ArrayList<GPEvaluationJob<T>> arrayList2 = new ArrayList<GPEvaluationJob<T>>();
        for (int i = 0; i < arrayList.size(); ++i) {
            IGPNode iGPNode = (IGPNode)arrayList.get(i);
            GPIDs gPIDs = iGPNode.getGPIDs();
            String string = String.format("%s-Generation %d.%d.%d", this.gpIslandJob.getJobId(), gPIDs.islandIndex + 1, gPIDs.generationIndex, gPIDs.nodeIndex);
            HashMap<String, Serializable> hashMap = new HashMap<String, Serializable>();
            hashMap.put("evaluator", (Serializable)this.gpSettings.evaluator.getClone());
            hashMap.put("candidate", iGPNode);
            hashMap.put("populationType", Integer.valueOf(n));
            hashMap.put("sendLastPopulation", Boolean.valueOf(this.gpSettings.sendLastPopulation));
            GPEvaluationJob gPEvaluationJob = new GPEvaluationJob(string, hashMap);
            if (this.parentGridJob != null) {
                gPEvaluationJob.setPriority(this.parentGridJob.getPriority() + 1);
            }
            arrayList2.add(gPEvaluationJob);
        }
        if (arrayList2.size() == 0) {
            return;
        }
        if (this.gpSettings.singleThreaded) {
            this.executeInSingleThread(arrayList2);
        } else {
            this.executeInGrid(arrayList2);
        }
    }

    private void executeInSingleThread(ArrayList<GPEvaluationJob<T>> arrayList) {
        for (int i = 0; i < arrayList.size(); ++i) {
            GPEvaluationJob<T> gPEvaluationJob = arrayList.get(i);
            Object object = null;
            JobDetails jobDetails = new JobDetails(gPEvaluationJob.getJobId());
            try {
                long l = System.currentTimeMillis();
                object = gPEvaluationJob.call();
                long l2 = System.currentTimeMillis() - l;
                this.checkPaused();
                if (this.checkStopped()) break;
                jobDetails.setDuration(l2);
                this.addToPopulation(object, jobDetails);
                continue;
            }
            catch (Throwable throwable) {
                jobDetails.setException(SQUtils.getStackTrace((Throwable)throwable));
                this.addToPopulation(object, jobDetails);
                Log.error("Error while running task #{}", (Object)i, (Object)throwable);
            }
        }
    }

    private void executeInGrid(ArrayList<GPEvaluationJob<T>> arrayList) throws Exception {
        int n = arrayList.size();
        this.finishedJobs = 0;
        this.gridClient.executeOnGrid(this.evaluationGroupID, arrayList);
        this.gridClient.waitForFinish((Object)this, this.islandJobID, this.gpGroupID, this.evaluationGroupID);
        if (this.finishedJobs != n) {
            // empty if block
        }
        if (this.checkStopped()) {
            throw new InterruptedException();
        }
    }

    private void removeUncomputedFitnessCandidates() {
        Iterator<T> iterator = this.population.iterator();
        while (iterator.hasNext()) {
            IGPNode iGPNode = (IGPNode)iterator.next();
            if (!(iGPNode.getFitness((byte)11) < 0.0)) continue;
            iterator.remove();
        }
    }

    protected void processMessage(GridMessage gridMessage) {
        if (gridMessage.getMessageID() == 1) {
            this.messageJobFinished(gridMessage);
        } else if (gridMessage.getMessageID() == 5 && gridMessage.getCustomID().equals("GPThresholdFitness")) {
            this.messageThresholdFitness(gridMessage);
        }
    }

    private void messageThresholdFitness(GridMessage gridMessage) {
        double d = (Double)gridMessage.getData();
        if (this.gpSettings.naturalFitness) {
            if (d > this.thresholdFitness) {
                this.thresholdFitness = d;
            }
        } else if (d < this.thresholdFitness) {
            this.thresholdFitness = d;
        }
    }

    private void messageJobFinished(GridMessage gridMessage) {
        JobDetails jobDetails;
        IGPNode iGPNode = (IGPNode)gridMessage.getData();
        if (iGPNode == null) {
            try {
                jobDetails = new GridMessage(5, "GPException", (Serializable)((Object)"Evaluated candidate is null - exception?"));
                this.gridClient.sendMessage(this.gpGroupID, null, (GridMessage)jobDetails);
                this.gridClient.stop(this.evaluationGroupID);
                this.gridClient.removeMessageListener(this.evaluationGroupID);
                jobDetails = new GridMessage(1);
                this.gridClient.sendMessage(this.gpGroupID, null, (GridMessage)jobDetails);
            }
            catch (Exception exception) {
                Log.error("Exception in messageJobFinished", (Throwable)exception);
            }
        }
        if ((jobDetails = gridMessage.getJobDetails()) != null && jobDetails.getException() != null && !this.checkStopped() && jobDetails.getException().contains("OutOfMemoryError")) {
            try {
                this.gridClient.sendMessage(this.gpGroupID, null, gridMessage);
                this.gridClient.stop(this.gpGroupID);
                this.stop();
            }
            catch (Exception exception) {
                Log.error("Cannot send Error message to grid client", (Throwable)exception);
            }
        }
        if (this.checkStopped()) {
            if (Log.isDebugEnabled()) {
                Log.debug("Destroying, engine is stopped");
            }
            if (iGPNode != null) {
                iGPNode.destroy();
            }
        } else {
            ++this.finishedJobs;
            this.addToPopulation(iGPNode, gridMessage.getJobDetails());
        }
    }

    /*
     * WARNING - Removed try catching itself - possible behaviour change.
     */
    private void addToPopulation(T t, JobDetails jobDetails) {
        Object object;
        if (this.currentGeneration == 0 && t.getGPIDs().generationIndex == 0 && !t.passedEvaluation()) {
            object = t.getGPIDs().toString();
            if (t.getDismissalReason() == 10001) {
                Log.error("There was exception evaluating candidate, exception: " + t.getException() + ", error: " + t.getErrorMsg());
            }
            t.destroy();
        } else {
            object = this.population;
            synchronized (object) {
                this.population.add(t);
            }
        }
        try {
            this.sendToGPEngine(t, jobDetails);
        }
        catch (Exception exception) {
            Log.error("Cannot send candidate from Job to GPEngine", (Throwable)exception);
        }
    }

    private void sendToGPEngine(T t, JobDetails jobDetails) throws Exception {
        IGPNode iGPNode;
        GPIDs gPIDs;
        if (!this.gpSettings.sendEveryCandidateEvent || this.checkStopped()) {
            return;
        }
        if (t.passedEvaluation()) {
            gPIDs = t.getGPIDs();
            iGPNode = gPIDs.generationIndex == 0 ? t.cloneDismissed(10005) : (this.thresholdFitness == 0.0 || t.getFitness((byte)11) > this.thresholdFitness ? t.clonePassed() : t.cloneDismissed(10000));
        } else {
            iGPNode = t.cloneDismissed(t.getDismissalReason());
        }
        iGPNode.setJobDetails(jobDetails);
        gPIDs = new GridMessage(5, "GPEvaluatedCandidate", (Serializable)iGPNode);
        this.gridClient.sendMessage(this.gpGroupID, null, (GridMessage)gPIDs);
    }

    private void sendLastPopulation() throws Exception {
        if (this.islandIndex != 0 || !this.gpSettings.sendLastPopulation || this.checkStopped()) {
            return;
        }
        ArrayList<IGPNode> arrayList = new ArrayList<IGPNode>();
        for (int i = 0; i < this.population.size(); ++i) {
            arrayList.add(((IGPNode)this.population.get(i)).clonePassed());
        }
        GPEvolutionPopulationMessage gPEvolutionPopulationMessage = new GPEvolutionPopulationMessage(this.currentGeneration, this.islandIndex, arrayList);
        GridMessage gridMessage = new GridMessage(5, "GPLastPopulation", gPEvolutionPopulationMessage);
        this.gridClient.sendMessage(this.gpGroupID, null, gridMessage);
    }

    private void sendEvolutionStatusMessage(int n, String string) throws Exception {
        GPEvolutionMessage gPEvolutionMessage = new GPEvolutionMessage(n, this.currentGeneration, this.islandIndex, this.population.size(), string);
        gPEvolutionMessage.fitnessEvolutionData = this.gpFitnessEvolution.getData();
        this.updateEvolutionData(gPEvolutionMessage.fitnessEvolutionData);
        GridMessage gridMessage = new GridMessage(5, "GPEvolutionStatus", (Serializable)gPEvolutionMessage);
        this.gridClient.sendMessage(this.gpGroupID, null, gridMessage);
    }

    private void updateEvolutionData(GPFitnessEvolutionData gPFitnessEvolutionData) {
        gPFitnessEvolutionData.populationSize = this.population.size();
        gPFitnessEvolutionData.generation = this.currentGeneration;
    }

    public void pause() {
        if (this.runningStatus == 1) {
            this.runningStatus = 2;
        }
    }

    public void restart() {
        if (this.runningStatus == 2) {
            this.runningStatus = 1;
        }
    }

    public void stop() {
        if (this.runningStatus != 3) {
            this.runningStatus = 3;
            this.gridClient.stop(this.evaluationGroupID);
        }
    }

    private boolean checkStopped() {
        return this.runningStatus == 3;
    }

    private void checkPaused() throws InterruptedException {
        if (this.runningStatus != 2) {
            return;
        }
        while (this.runningStatus == 2) {
            Thread.sleep(100L);
        }
    }

    public void destroy() {
    }

    private void sendMigrationCandidates(ArrayList<IGPNode> arrayList) throws Exception {
        if (this.gpSettings.numberOfIslands == 1) {
            return;
        }
        int n = this.islandIndex + 1;
        if (n == this.gpSettings.numberOfIslands) {
            n = 0;
        }
        String string = GPIslandJob.createJobID(n, this.parentGridJob, this.source);
        GridMessage gridMessage = new GridMessage(5, "GBIslandExchange", arrayList);
        this.gridClient.sendMessage(this.gpGroupID, string, gridMessage);
    }

    /*
     * WARNING - Removed try catching itself - possible behaviour change.
     */
    private void receiveImmigrants() {
        if (this.currentGeneration < this.gpSettings.migrationGenerationsModulo) {
            return;
        }
        ArrayList<T> arrayList = this.candidatesInbox;
        synchronized (arrayList) {
            if (this.candidatesInbox.size() > 0) {
                int n = (int)(0.2 * (double)this.population.size());
                if (n == 0) {
                    n = 1;
                }
                n = this.candidatesInbox.size() < n ? this.candidatesInbox.size() : n;
                for (int i = 0; i < this.candidatesInbox.size(); ++i) {
                    if (i >= this.population.size() / 2) continue;
                    int n2 = this.population.size() - 1 - i;
                    ((IGPNode)this.population.get(n2)).destroy();
                    this.population.remove(n2);
                    this.population.add((IGPNode)this.candidatesInbox.get(i));
                }
                this.candidatesInbox.clear();
                this.sortEvaluatedPopulation();
            }
        }
    }

    /*
     * WARNING - Removed try catching itself - possible behaviour change.
     */
    public void addToInbox(List<T> list) {
        ArrayList<T> arrayList = this.candidatesInbox;
        synchronized (arrayList) {
            int n = (int)(0.2 * (double)this.gpSettings.populationSize);
            if (n == 0) {
                n = 1;
            }
            this.candidatesInbox.addAll(list);
            if (this.candidatesInbox.size() > n) {
                Collections.shuffle(this.candidatesInbox);
                this.shrinkTo(this.candidatesInbox, n);
            }
        }
    }

    private void shrinkTo(List list, int n) {
        int n2 = list.size();
        if (n >= n2) {
            return;
        }
        for (int i = n; i < n2; ++i) {
            list.remove(list.size() - 1);
        }
    }
}

