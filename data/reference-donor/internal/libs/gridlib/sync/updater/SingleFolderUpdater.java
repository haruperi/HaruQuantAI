/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  javax.jms.JMSException
 */
package com.strategyquant.gridlib.sync.updater;

import com.strategyquant.gridlib.FileHelper;
import com.strategyquant.gridlib.message.JmsConnectionInfo;
import com.strategyquant.gridlib.sync.updater.AbstractFolderUpdater;
import com.strategyquant.gridlib.sync.updater.HandleHashResult;
import java.io.File;
import java.io.IOException;
import java.util.HashMap;
import java.util.LinkedList;
import java.util.List;
import java.util.Map;
import java.util.Set;
import javax.jms.JMSException;

public class SingleFolderUpdater
extends AbstractFolderUpdater {
    private FileStructures hashFileStructure;

    public SingleFolderUpdater(String string, String string2, JmsConnectionInfo jmsConnectionInfo) throws IOException, JMSException {
        super(string, string2, jmsConnectionInfo);
    }

    @Override
    public void updateHash() throws IOException {
        this.hash = FileHelper.countHash(this.getFolder());
        this.hashFileStructure = new FileStructures(this.hash);
    }

    @Override
    public HandleHashResult hashChanged(String string) {
        FileStructures fileStructures = new FileStructures(string);
        FileStructureCompareResult fileStructureCompareResult = new FileStructureComparator().compare(this.hashFileStructure, fileStructures);
        this.removeUnecessaryFiles(fileStructureCompareResult.removedFiles);
        if (fileStructureCompareResult.newOrChangedFiles.isEmpty()) {
            return new HandleHashResult(false, null);
        }
        return new HandleHashResult(true, (LinkedList)fileStructureCompareResult.newOrChangedFiles);
    }

    private void removeUnecessaryFiles(List<String> list) {
        for (String string : list) {
            new File(this.getFolder(), string).delete();
        }
    }

    private static class FileStructures {
        private Map<String, String> structure = new HashMap<String, String>();

        public FileStructures(String string) {
            this.parse(string);
        }

        private void parse(String string) {
            String[] stringArray;
            for (String string2 : stringArray = string.split("\n")) {
                if (string2.isEmpty()) continue;
                int n = string2.indexOf(32);
                String string3 = string2.substring(0, n - 1);
                String string4 = string2.substring(n + 1);
                this.structure.put(string4, string3);
            }
        }

        public boolean equalsHash(String string, String string2) {
            String string3 = this.structure.get(string);
            return string2.equals(string3);
        }

        public boolean hasFile(String string) {
            return this.structure.containsKey(string);
        }

        public Set<String> getFileNames() {
            return this.structure.keySet();
        }

        public String getHash(String string) {
            return this.structure.get(string);
        }
    }

    private static class FileStructureComparator {
        private FileStructureComparator() {
        }

        public FileStructureCompareResult compare(FileStructures fileStructures, FileStructures fileStructures2) {
            FileStructureCompareResult fileStructureCompareResult = new FileStructureCompareResult();
            this.evalRemovedOrChangedFiles(fileStructureCompareResult, fileStructures, fileStructures2);
            this.evalAddedFiles(fileStructureCompareResult, fileStructures, fileStructures2);
            return fileStructureCompareResult;
        }

        private void evalRemovedOrChangedFiles(FileStructureCompareResult fileStructureCompareResult, FileStructures fileStructures, FileStructures fileStructures2) {
            for (String string : fileStructures.getFileNames()) {
                if (!fileStructures2.hasFile(string = string.trim())) {
                    fileStructureCompareResult.removedFiles.add(string);
                    continue;
                }
                if (fileStructures2.equalsHash(string, fileStructures.getHash(string))) continue;
                fileStructureCompareResult.newOrChangedFiles.add(string);
            }
        }

        private void evalAddedFiles(FileStructureCompareResult fileStructureCompareResult, FileStructures fileStructures, FileStructures fileStructures2) {
            for (String string : fileStructures2.getFileNames()) {
                if (fileStructures.hasFile(string = string.trim())) continue;
                fileStructureCompareResult.newOrChangedFiles.add(string);
            }
        }
    }

    private static class FileStructureCompareResult {
        private List<String> removedFiles = new LinkedList<String>();
        private List<String> newOrChangedFiles = new LinkedList<String>();

        private FileStructureCompareResult() {
        }
    }
}

