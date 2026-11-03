/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  com.strategyquant.lib.app.MainApp
 *  org.slf4j.Logger
 *  org.slf4j.LoggerFactory
 */
package com.strategyquant.tradinglib.python;

import com.strategyquant.lib.app.MainApp;
import java.io.BufferedReader;
import java.io.File;
import java.io.FileNotFoundException;
import java.io.IOException;
import java.io.InputStreamReader;
import java.util.ArrayList;
import java.util.Arrays;
import java.util.List;
import java.util.UUID;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

public class PythonRunner {
    public static final Logger Log = LoggerFactory.getLogger(PythonRunner.class);
    private String pythonExePath;
    private File scriptFolder;
    private File tmpFolder;
    private Process process;
    private Object lock = new Object();
    private volatile boolean stopped;

    public PythonRunner() {
        File file = new File(MainApp.getDataPath(), "internal");
        File file2 = new File(file, "python");
        File file3 = new File(file2, "runtime");
        this.pythonExePath = new File(file3, "python.exe").getAbsolutePath();
        this.scriptFolder = new File(file2, "scripts");
        this.tmpFolder = new File(file, "tmp");
    }

    public File getTmpFile(String string, String string2) {
        String string3;
        File file;
        while ((file = new File(this.tmpFolder, string3 = string + UUID.randomUUID().toString().replace("-", "") + string2)).exists()) {
        }
        return file;
    }

    private Process createPythonProcess(List<String> list) throws IOException {
        this.stopped = false;
        ProcessBuilder processBuilder = new ProcessBuilder(list);
        processBuilder.environment().remove("PYTHONPATH");
        processBuilder.environment().put("PYTHONNOUSERSITE", "1");
        processBuilder.redirectErrorStream(true);
        return processBuilder.start();
    }

    private List<String> getPythonCommands(File file, String ... stringArray) {
        ArrayList<String> arrayList = new ArrayList<String>();
        arrayList.add(this.pythonExePath);
        arrayList.add(file.getAbsolutePath());
        arrayList.addAll(Arrays.asList(stringArray));
        Log.info("Running {} {}", (Object)file.getName(), (Object)String.join((CharSequence)" ", stringArray));
        return arrayList;
    }

    private String readOutput(Process process) throws IOException {
        StringBuilder stringBuilder = new StringBuilder();
        try (BufferedReader bufferedReader = new BufferedReader(new InputStreamReader(process.getInputStream()));){
            String string;
            while ((string = bufferedReader.readLine()) != null) {
                stringBuilder.append(string).append("\n");
            }
        }
        return stringBuilder.toString();
    }

    /*
     * WARNING - Removed try catching itself - possible behaviour change.
     */
    public String run(String string, ProgressCallback progressCallback, String ... stringArray) throws IOException, InterruptedException {
        File file = new File(this.scriptFolder, string);
        List<String> list = this.getPythonCommands(file, stringArray);
        this.process = this.createPythonProcess(list);
        String string2 = this.listenPythonOutput(progressCallback, this.process);
        int n = this.process.waitFor();
        Object object = this.lock;
        synchronized (object) {
            this.process = null;
        }
        if (this.stopped) {
            return null;
        }
        switch (n) {
            case 0: {
                return string2;
            }
            case 1: {
                Log.error("Error while running script: " + string2);
                throw new RuntimeException("Error while running script: " + string2);
            }
            case 2: {
                throw new FileNotFoundException("Script not found: " + file.getAbsolutePath());
            }
        }
        throw new RuntimeException("Unexpected error (exit code " + n + "):\n" + string2);
    }

    private String listenPythonOutput(ProgressCallback progressCallback, Process process) throws InterruptedException {
        StringBuilder stringBuilder = new StringBuilder();
        Thread thread = new Thread(() -> {
            try (BufferedReader bufferedReader = new BufferedReader(new InputStreamReader(process.getInputStream()));){
                String string;
                while ((string = bufferedReader.readLine()) != null) {
                    stringBuilder.append(string);
                    if (progressCallback != null) {
                        this.callCallback(progressCallback, string);
                        continue;
                    }
                    Log.debug(string);
                }
            }
            catch (IOException iOException) {
                Log.error("Error reading output", (Throwable)iOException);
            }
        });
        thread.start();
        thread.join();
        return stringBuilder.toString();
    }

    private void callCallback(ProgressCallback progressCallback, String string) {
        if ((string = string.trim()).startsWith("SQERROR:")) {
            progressCallback.onError(string.substring(8).trim());
        } else if (string.startsWith("SQRESULT:")) {
            progressCallback.onResult(string.substring(9).trim());
        } else if (string.startsWith("SQMESSAGE:")) {
            progressCallback.onMessage(string.substring(10).trim());
        } else if (string.startsWith("SQPROGRESS:")) {
            String string2 = string.substring(11).trim();
            try {
                double d = Double.valueOf(string2);
                progressCallback.onProgress(d);
            }
            catch (Exception exception) {
                Log.error("Error while parsing progress response: " + string2, (Throwable)exception);
            }
        } else {
            Log.debug(string);
        }
    }

    /*
     * WARNING - Removed try catching itself - possible behaviour change.
     */
    public void cancel() {
        Object object = this.lock;
        synchronized (object) {
            if (this.process != null) {
                this.stopped = true;
                this.process.destroyForcibly();
            }
        }
    }

    public static interface ProgressCallback {
        public void onResult(String var1);

        public void onProgress(double var1);

        public void onError(String var1);

        public void onMessage(String var1);
    }

    public static class ProgressCallbackAdapter
    implements ProgressCallback {
        @Override
        public void onResult(String string) {
        }

        @Override
        public void onProgress(double d) {
        }

        @Override
        public void onError(String string) {
        }

        @Override
        public void onMessage(String string) {
        }
    }
}

