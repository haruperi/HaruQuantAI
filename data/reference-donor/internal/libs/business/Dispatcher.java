/*
 * Decompiled with CFR 0.152.
 */
package com.strategyquant.wizard.desktop;

import com.strategyquant.wizard.desktop.loader.CustomIndicatorLoader;
import com.strategyquant.wizard.desktop.loader.ErrorReportSender;
import com.strategyquant.wizard.desktop.loader.FavoriteItemsLoader;
import com.strategyquant.wizard.desktop.loader.LicenceLoader;
import com.strategyquant.wizard.desktop.loader.RecentFilesLoader;
import com.strategyquant.wizard.desktop.loader.ShareLoader;
import com.strategyquant.wizard.desktop.loader.StrategyLoader;
import com.strategyquant.wizard.desktop.loader.TransformEngineLoader;
import com.strategyquant.wizard.desktop.utils.FileUtils;
import com.strategyquant.wizard.desktop.utils.JsonUtils;
import java.awt.Toolkit;
import java.awt.datatransfer.Clipboard;
import java.awt.datatransfer.DataFlavor;
import java.awt.datatransfer.StringSelection;
import java.awt.datatransfer.Transferable;
import java.awt.datatransfer.UnsupportedFlavorException;
import java.io.File;
import java.io.IOException;
import java.io.UnsupportedEncodingException;
import java.nio.file.Files;

public class Dispatcher {
    public static final String SEPARATOR_PATTERN = "#;#";
    private TransformEngineLoader transformEngineLoader = new TransformEngineLoader(null);
    private RecentFilesLoader recentFilesLoader = new RecentFilesLoader();
    private StrategyLoader strategyLoader = new StrategyLoader(null);
    private LicenceLoader licenceLoader = new LicenceLoader();
    private CustomIndicatorLoader customIndicatorLoader = new CustomIndicatorLoader(null);
    private FavoriteItemsLoader favoriteItemsLoader = new FavoriteItemsLoader();
    private ErrorReportSender errorReportSender = new ErrorReportSender(null);
    private ShareLoader shareLoader = new ShareLoader();
    private Runnable initializedRunnable;

    public void setInitializedRunnable(Runnable runnable) {
        this.initializedRunnable = runnable;
    }

    public void dispose() {
        this.transformEngineLoader.dispose();
        this.strategyLoader.dispose();
        this.customIndicatorLoader.dispose();
        this.errorReportSender.dispose();
    }

    public String share(String string, String string2, String string3, String string4) {
        return this.shareLoader.share(string, string2, string3, string4);
    }

    public String execute(String string) throws UnsupportedEncodingException, IOException, UnsupportedFlavorException {
        String[] stringArray = string.split(SEPARATOR_PATTERN);
        String string2 = stringArray[0];
        if (string2.equalsIgnoreCase("getAppVersion")) {
            return this.getVersion();
        }
        if (string2.equalsIgnoreCase("verifyShare")) {
            return this.verifyShare(stringArray[1]);
        }
        if (string2.equalsIgnoreCase("notifyShare")) {
            return this.notifyShare(stringArray[1], stringArray[2]);
        }
        if (string2.equalsIgnoreCase("loadShared")) {
            return this.loadShared(stringArray[1], stringArray[2]);
        }
        if (string2.equalsIgnoreCase("saveShared")) {
            return this.saveShared(stringArray[1], stringArray[2], stringArray[3]);
        }
        if (string2.equalsIgnoreCase("transformCode")) {
            return this.transformCode(stringArray[1], stringArray[2]);
        }
        if (string2.equalsIgnoreCase("loadTransformEngines")) {
            return this.loadTransformEngines();
        }
        if (string2.equalsIgnoreCase("saveTransformedCode")) {
            this.saveTransformedCode(stringArray[1], stringArray[2], stringArray[3]);
            return "";
        }
        if (string2.equalsIgnoreCase("loadFavorites")) {
            return this.loadFavorites();
        }
        if (string2.equalsIgnoreCase("saveRecentFiles")) {
            return this.saveRecentFiles(stringArray[1], stringArray[2], stringArray[3]);
        }
        if (string2.equalsIgnoreCase("loadRecentFiles")) {
            return this.loadRecentFiles(stringArray[1]);
        }
        if (string2.equalsIgnoreCase("errorReport")) {
            return String.valueOf(this.errorReport(stringArray[1], stringArray[2]));
        }
        if (string2.equalsIgnoreCase("exit")) {
            this.exit();
            return "";
        }
        if (string2.equalsIgnoreCase("loadLicense")) {
            return this.loadLicense(stringArray[1]);
        }
        if (string2.equalsIgnoreCase("loadFile")) {
            return this.loadFile(stringArray[1]);
        }
        if (string2.equalsIgnoreCase("showDialogAndLoadFile")) {
            return this.showDialogAndLoadFile();
        }
        if (string2.equalsIgnoreCase("saveFile")) {
            return this.saveFile(stringArray[1], stringArray[2], Boolean.parseBoolean(stringArray[3]));
        }
        if (string2.equalsIgnoreCase("loadCloudFileList")) {
            return this.loadCloudFileList(stringArray[1], stringArray[2]);
        }
        if (string2.equalsIgnoreCase("createFolder")) {
            return this.createFolder(stringArray[1], stringArray[2]);
        }
        if (string2.equalsIgnoreCase("loadCloudFileContent")) {
            return this.loadCloudFileContent(stringArray[1], stringArray[2]);
        }
        if (string2.equalsIgnoreCase("saveCloudFileContent")) {
            return this.saveCloudFileContent(stringArray[1], stringArray[2], stringArray[3]);
        }
        if (string2.equalsIgnoreCase("importCustomIndicator")) {
            return this.importCustomIndicator();
        }
        if (string2.equalsIgnoreCase("loadCustomIndicators")) {
            return this.importCustomIndicator(stringArray[1]);
        }
        if (string2.equalsIgnoreCase("copyToClipboard")) {
            this.copyToClipboard(stringArray[1]);
            return "";
        }
        if (string2.equalsIgnoreCase("paste")) {
            return this.paste(stringArray[1]);
        }
        if (string2.equalsIgnoreCase("initializationOver")) {
            this.initializationOver();
            return "";
        }
        return null;
    }

    public String verifyShare(String string) {
        return this.shareLoader.verifyShare(string);
    }

    public String notifyShare(String string, String string2) {
        return this.shareLoader.notifyShare(string, string2);
    }

    public String loadShared(String string, String string2) {
        return this.shareLoader.loadShared(string, string2);
    }

    public String saveShared(String string, String string2, String string3) {
        return this.shareLoader.saveShared(string, string2, string3);
    }

    public String transformCode(String string, String string2) {
        String string3 = this.transformEngineLoader.transformCode(string, string2);
        return string3;
    }

    public void initializationOver() {
        if (this.initializedRunnable != null) {
            this.initializedRunnable.run();
        }
    }

    public String loadTransformEngines() {
        return this.transformEngineLoader.load();
    }

    public void saveTransformedCode(String string, String string2, String string3) {
        this.transformEngineLoader.save(string, string2, string3);
    }

    public String loadFavorites() {
        return this.favoriteItemsLoader.getFavoriteItems();
    }

    public String saveRecentFiles(String string, String string2, String string3) {
        return this.recentFilesLoader.saveRecentFiles(string, string2, string3);
    }

    public String loadRecentFiles(String string) {
        return this.recentFilesLoader.loadRecentFiles(string);
    }

    public boolean errorReport(String string, String string2) {
        return this.errorReportSender.send(string, string2);
    }

    public String loadLicense(String string) {
        return this.licenceLoader.loadLicense(string);
    }

    public void exit() {
        this.dispose();
    }

    public String loadFile(String string) {
        return this.strategyLoader.loadFile(string);
    }

    public String showDialogAndLoadFile() {
        return this.strategyLoader.loadFileWithName();
    }

    public String saveFile(String string, String string2, boolean bl) {
        try {
            return this.strategyLoader.saveFile(string, string2, bl);
        }
        catch (IOException iOException) {
            return JsonUtils.getErrorResonse(iOException.getMessage());
        }
    }

    public String loadCloudFileList(String string, String string2) {
        return this.strategyLoader.loadCloudFileList(string, string2);
    }

    public String createFolder(String string, String string2) {
        return this.strategyLoader.createCloudFolder(string, string2);
    }

    public String loadCloudFileContent(String string, String string2) {
        return this.strategyLoader.loadCloudFile(string, string2);
    }

    public String saveCloudFileContent(String string, String string2, String string3) {
        return this.strategyLoader.saveCloudFile(string, string2, string3);
    }

    public String importCustomIndicator() {
        return this.customIndicatorLoader.loadFile();
    }

    public String importCustomIndicator(String string) {
        return this.customIndicatorLoader.loadFile(string);
    }

    public void copyToClipboard(String string) {
        Clipboard clipboard = Toolkit.getDefaultToolkit().getSystemClipboard();
        clipboard.setContents(new StringSelection(string), null);
    }

    public String paste(String string) throws UnsupportedFlavorException, IOException {
        Transferable transferable = Toolkit.getDefaultToolkit().getSystemClipboard().getContents(this);
        if (transferable != null && transferable.isDataFlavorSupported(DataFlavor.stringFlavor)) {
            String string2 = (String)transferable.getTransferData(DataFlavor.stringFlavor);
            if (string2 != null) {
                string2 = string2.replace("\n", "").replace("\r", "").replace("\t", "");
            }
            return "{\"result\":\"success\",\"content\":\"" + string2 + "\"}";
        }
        return null;
    }

    public String getVersion() {
        File file = new File(FileUtils.getAppFolder() + "version");
        try {
            return new String(Files.readAllBytes(file.toPath()));
        }
        catch (IOException iOException) {
            return "{\"version\":\"unknown\"}";
        }
    }
}

