/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  com.strategyquant.lib.L
 *  com.strategyquant.lib.SQUtils
 *  com.strategyquant.lib.app.MainApp
 *  com.strategyquant.lib.constants.SQPaths
 *  com.strategyquant.lib.plugins.compile.PluginCompiler
 *  com.strategyquant.lib.snippets.CustomClassesReg
 *  com.strategyquant.lib.snippets.ProtectedSnippets
 *  com.strategyquant.lib.snippets.SnippetsCompiler
 *  com.strategyquant.lib.snippets.SnippetsCompilerUtils
 *  com.strategyquant.lib.snippets.compile.AutoImport
 *  com.strategyquant.lib.snippets.compile.CompilationResult
 *  com.strategyquant.lib.snippets.compile.SQStructure
 *  com.strategyquant.lib.snippets.compile.inMemory.InMemoryJavaCompiler
 *  com.strategyquant.lib.snippets.compile.indicators.IndicatorsBuilder
 *  com.strategyquant.tradinglib.project.websocket.DataToSend
 *  com.strategyquant.tradinglib.project.websocket.SQWebSocketManager
 *  com.strategyquant.webguilib.servlet.HttpJSONServlet
 *  org.json.JSONArray
 *  org.json.JSONObject
 *  org.slf4j.Logger
 *  org.slf4j.LoggerFactory
 */
package com.strategyquant.plugin.Servlet.impl.CodeEditor;

import com.strategyquant.lib.L;
import com.strategyquant.lib.SQUtils;
import com.strategyquant.lib.app.MainApp;
import com.strategyquant.lib.constants.SQPaths;
import com.strategyquant.lib.plugins.compile.PluginCompiler;
import com.strategyquant.lib.snippets.CustomClassesReg;
import com.strategyquant.lib.snippets.ProtectedSnippets;
import com.strategyquant.lib.snippets.SnippetsCompiler;
import com.strategyquant.lib.snippets.SnippetsCompilerUtils;
import com.strategyquant.lib.snippets.compile.AutoImport;
import com.strategyquant.lib.snippets.compile.CompilationResult;
import com.strategyquant.lib.snippets.compile.SQStructure;
import com.strategyquant.lib.snippets.compile.inMemory.InMemoryJavaCompiler;
import com.strategyquant.lib.snippets.compile.indicators.IndicatorsBuilder;
import com.strategyquant.plugin.Servlet.impl.CodeEditor.CodeAutoCompleteManager;
import com.strategyquant.plugin.Servlet.impl.CodeEditor.CodeEditorInfoSender;
import com.strategyquant.plugin.Servlet.impl.CodeEditor.CodeEditorServletException;
import com.strategyquant.plugin.Servlet.impl.CodeEditor.FileMap;
import com.strategyquant.plugin.Servlet.impl.CodeEditor.searchInFiles.SearchInFiles;
import com.strategyquant.plugin.Servlet.impl.CodeEditor.searchInFiles.SearchInFilesResult;
import com.strategyquant.plugin.Servlet.impl.CodeEditor.templates.Template;
import com.strategyquant.plugin.Servlet.impl.CodeEditor.templates.Templates;
import com.strategyquant.tradinglib.project.websocket.DataToSend;
import com.strategyquant.tradinglib.project.websocket.SQWebSocketManager;
import com.strategyquant.webguilib.servlet.HttpJSONServlet;
import java.io.BufferedReader;
import java.io.BufferedWriter;
import java.io.File;
import java.io.FileInputStream;
import java.io.FileOutputStream;
import java.io.IOException;
import java.io.InputStream;
import java.io.InputStreamReader;
import java.io.OutputStream;
import java.io.OutputStreamWriter;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Paths;
import java.util.ArrayList;
import java.util.List;
import java.util.Map;
import java.util.regex.Matcher;
import java.util.regex.Pattern;
import org.json.JSONArray;
import org.json.JSONObject;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

public class CodeEditorServlet
extends HttpJSONServlet {
    private static final Logger Log = LoggerFactory.getLogger(CodeEditorServlet.class);
    private static CodeEditorInfoSender infoSender = null;
    private static FileMap fileMap = null;
    private static Templates templates = null;
    private PluginCompiler pc = new PluginCompiler();
    private static final String KEY_SUCCESS = "success";
    private static final String KEY_FILE = "file";
    private static final String KEY_FILES = "files";
    private static final String KEY_COMPILATION_RESULT = "compilationResult";
    private static final String KEY_INDICATORS = "indicators";
    private static final String KEY_TEMPLATE = "template";
    private static final String KEY_TEMPLATES = "templates";
    private static final String KEY_ID = "id";
    private static final String KEY_TEXT = "text";
    private static final String KEY_MATCHES = "matches";
    private static final String KEY_ITEM = "item";
    private static final String KEY_ITEMS = "items";
    private static final String KEY_NAME = "name";
    private static final String KEY_PROTECTED = "protected";
    private static final String KEY_TYPE = "type";
    private static final String KEY_DESCRIPTION = "description";
    private static final String KEY_DATA = "data";
    private static final String KEY_PLUGIN = "plugin";
    private static final String LAST_OPENED_SNIPPETS_FILE_PATH = SQPaths.settingsDirPath + "/lastOpenedSnippets.txt";

    private static synchronized CodeEditorInfoSender getInfoSenderInstance() {
        if (infoSender == null) {
            infoSender = new CodeEditorInfoSender();
        }
        return infoSender;
    }

    private static synchronized FileMap getFileMapInstance() {
        if (fileMap == null) {
            fileMap = new FileMap();
        }
        return fileMap;
    }

    private static synchronized Templates getTemplatesInstance() {
        if (templates == null) {
            templates = new Templates();
        }
        return templates;
    }

    protected String execute(String command, Map<String, String[]> parameterMap, String method) throws Exception {
        switch (command) {
            case "editorAutocomplete": {
                return this.onEditorAutocomplete();
            }
            case "listCodeTypes": {
                return this.onListCodeTypes();
            }
            case "list": {
                return this.onList(parameterMap);
            }
            case "getContent": {
                return this.onGetContent(parameterMap);
            }
            case "save": {
                return this.onSave(parameterMap);
            }
            case "saveAs": {
                return this.onSaveAs(parameterMap);
            }
            case "compile": {
                return this.onCompile(parameterMap);
            }
            case "compileAll": {
                return this.onCompileAll();
            }
            case "compilePlugin": {
                return this.onCompilePlugin(parameterMap);
            }
            case "stopCompilation": {
                return this.onStopCompilation();
            }
            case "listTemplates": {
                return this.onListTemplates(parameterMap);
            }
            case "listIndicators": {
                return this.onListIndicators();
            }
            case "createNew": {
                return this.onCreateNew(parameterMap);
            }
            case "createNewFile": {
                return this.onCreateNewFile(parameterMap);
            }
            case "createNewTemplate": {
                return this.onCreateNewTemplate(parameterMap);
            }
            case "createNewDir": {
                return this.onCreateNewDir(parameterMap);
            }
            case "rename": {
                return this.onRename(parameterMap);
            }
            case "delete": {
                return this.onDelete(parameterMap);
            }
            case "reload": {
                return this.onReload(parameterMap);
            }
            case "clone": {
                return this.onClone(parameterMap);
            }
            case "findInFiles": {
                return this.onFindInFiles(parameterMap);
            }
            case "getInfo": {
                return this.onGetInfo();
            }
            case "fixImports": {
                return this.onFixImports(parameterMap);
            }
            case "saveLastOpenedFiles": {
                return this.onSaveLastOpenedFiles(parameterMap);
            }
            case "loadLastOpenedFiles": {
                return this.onLoadLastOpenedFiles();
            }
            case "reloadApp": {
                return this.onReloadApp();
            }
        }
        throw new CodeEditorServletException(String.format("Unknown command '%s'.", command));
    }

    private void validateFileName(String name) throws CodeEditorServletException {
        if (!this.isNameValid(name)) {
            throw new CodeEditorServletException(L.t((String)"File name cannot contain spaces or special characters.", (Object[])new Object[0]));
        }
    }

    private void prvCheckParamExists(Map<String, String[]> params, String[] parameters) throws CodeEditorServletException {
        try {
            this.checkParamExists(params, parameters);
        }
        catch (Exception e) {
            throw new CodeEditorServletException(e.getMessage());
        }
    }

    private static void prvStringToFile(String path, String str) throws CodeEditorServletException {
        try {
            SQUtils.stringToFile((File)new File(path), (String)str);
        }
        catch (Exception e) {
            throw new CodeEditorServletException(e.getMessage());
        }
    }

    private static void prvStringToFile(File file, String str) throws CodeEditorServletException {
        try {
            SQUtils.stringToFile((File)file, (String)str);
        }
        catch (Exception e) {
            throw new CodeEditorServletException(e.getMessage());
        }
    }

    private static String prvFileToString(File file) throws CodeEditorServletException {
        try {
            return SQUtils.fileToString((File)file);
        }
        catch (Exception e) {
            throw new CodeEditorServletException(e.getMessage());
        }
    }

    private String onFindInFiles(Map<String, String[]> parameterMap) {
        String text = parameterMap.get(KEY_TEXT)[0];
        boolean caseSensitive = Boolean.parseBoolean(parameterMap.get("caseSensitive")[0]);
        boolean regex = Boolean.parseBoolean(parameterMap.get("regex")[0]);
        boolean wholeWord = Boolean.parseBoolean(parameterMap.get("wholeWord")[0]);
        JSONObject response = new JSONObject();
        SearchInFiles searchInFiles = new SearchInFiles();
        SearchInFilesResult searchResult = searchInFiles.search(SQStructure.getSnippetsSourceDirsAsMap(), text, caseSensitive, regex, wholeWord);
        response.put(KEY_ID, 0);
        response.put(KEY_ITEM, (Object)searchResult.getItems());
        response.put(KEY_TEXT, (Object)text);
        response.put(KEY_MATCHES, searchResult.getTotalMatchesCount());
        response.put(KEY_SUCCESS, (Object)"Search done.");
        return response.toString();
    }

    private String onReload(Map<String, String[]> parameterMap) throws CodeEditorServletException {
        File f = this.getFile(parameterMap);
        JSONObject response = new JSONObject();
        response.put(KEY_FILE, (Object)f.getAbsolutePath());
        response.put(KEY_SUCCESS, (Object)L.t((String)"File refreshed.", (Object[])new Object[0]));
        return response.toString();
    }

    private String onDelete(Map<String, String[]> parameterMap) throws Exception {
        String file = parameterMap.get(KEY_FILE)[0];
        JSONObject response = new JSONObject();
        File f = new File(file);
        if (ProtectedSnippets.getInstance().isProtected(f)) {
            throw new CodeEditorServletException(L.t((String)"Cannot delete a protected snippet.", (Object[])new Object[0]));
        }
        if (!f.exists()) {
            throw new CodeEditorServletException(L.t((String)"File '%s'doesn't exist.", (Object[])new Object[]{file}));
        }
        ArrayList<String> deletedFiles = new ArrayList<String>();
        this.deleteRecursive(f, deletedFiles);
        JSONArray array = new JSONArray();
        for (String path : deletedFiles) {
            array.put((Object)path);
        }
        response.put(KEY_FILES, (Object)array);
        response.put(KEY_SUCCESS, (Object)L.t((String)"Files deleted.", (Object[])new Object[0]));
        return response.toString();
    }

    public boolean deleteRecursive(File file, List<String> deletedFiles) throws Exception {
        if (!file.exists()) {
            return true;
        }
        boolean ret = true;
        if (file.isDirectory()) {
            File[] files = file.listFiles();
            if (files == null) {
                return true;
            }
            for (File f : files) {
                ret = ret && this.deleteRecursive(f, deletedFiles);
            }
        }
        String fileNameToDelete = file.getAbsolutePath();
        try {
            if (ret) {
                Files.delete(Paths.get(fileNameToDelete, new String[0]));
                deletedFiles.add(file.getAbsolutePath());
                return true;
            }
        }
        catch (IOException e) {
            throw new Exception(String.format("Error deleting file '%s'. Exc. %s", fileNameToDelete, e.toString()));
        }
        return false;
    }

    private String onRename(Map<String, String[]> parameterMap) throws CodeEditorServletException {
        String fPath;
        String name = parameterMap.get(KEY_NAME)[0];
        String file = parameterMap.get(KEY_FILE)[0];
        JSONObject response = new JSONObject();
        File fOrig = new File(file);
        if (fOrig.isDirectory()) {
            fPath = fOrig.getParentFile().getAbsolutePath() + '/' + name;
        } else {
            String extension = SQUtils.getExtension((String)fOrig.getName());
            fPath = fOrig.getParentFile().getAbsolutePath() + '/' + name + "." + extension;
        }
        File fNew = new File(fPath);
        if (ProtectedSnippets.getInstance().isProtected(fOrig)) {
            throw new CodeEditorServletException(L.t((String)"Cannot change a protected snippet.", (Object[])new Object[0]));
        }
        if (!fOrig.renameTo(fNew)) {
            throw new CodeEditorServletException(L.t((String)"Cannot rename file.\nPlease check  if this file is open in another program.", (Object[])new Object[0]));
        }
        response.put(KEY_FILE, (Object)fNew.getAbsolutePath());
        response.put(KEY_SUCCESS, (Object)L.t((String)"File renamed.", (Object[])new Object[0]));
        return response.toString();
    }

    private String onClone(Map<String, String[]> parameterMap) throws Exception {
        String name = parameterMap.get(KEY_NAME)[0];
        String file = parameterMap.get(KEY_FILE)[0];
        name = name.substring(0, 1).toUpperCase() + name.substring(1);
        this.validateFileName(name);
        JSONObject response = new JSONObject();
        File fOrig = new File(file);
        if (fOrig.isDirectory()) {
            throw new CodeEditorServletException(L.t((String)"Directory cannot be cloned.", (Object[])new Object[0]));
        }
        String origName = SQUtils.stripExtension((String)fOrig.getName());
        String extension = SQUtils.getExtension((String)fOrig.getName());
        String fPath = fOrig.getParentFile().getAbsolutePath() + '/' + name + "." + extension;
        File fNew = new File(fPath);
        String builtinDirPath = new File(SQStructure.getExtendBuiltinDirPath()).getAbsolutePath();
        String userDirPath = new File(SQStructure.getExtendUserDirPath()).getAbsolutePath();
        if (fNew.getPath().startsWith(builtinDirPath)) {
            fPath = fNew.getPath().replace(builtinDirPath, userDirPath);
            fNew = new File(fPath);
        }
        if (fNew.exists()) {
            throw new Exception("File with this name already exists.");
        }
        String content = SQUtils.fileToString((File)fOrig);
        if (extension.equalsIgnoreCase("java")) {
            content = content.replaceAll("(?<!double|int|long|String|char|boolean|float|byte|short) " + origName + " ", " " + name + " ");
            content = content.replaceAll(origName + ".class", name + ".class");
            content = content.replaceAll(" " + origName + "\\(", " " + name + "(");
            content = content.replaceAll("\"" + origName + "\"", "\"" + name + "\"");
        }
        CodeEditorServlet.prvStringToFile(fNew, content);
        response.put(KEY_FILE, (Object)fNew.getAbsolutePath());
        response.put(KEY_SUCCESS, (Object)L.t((String)"File cloned.", (Object[])new Object[0]));
        return response.toString();
    }

    private String onCreateNewDir(Map<String, String[]> parameterMap) throws CodeEditorServletException {
        String name = parameterMap.get(KEY_NAME)[0];
        String file = parameterMap.get(KEY_FILE)[0];
        JSONObject response = new JSONObject();
        File fDest = new File(file);
        String fPath = fDest.isDirectory() ? fDest.getAbsolutePath() + '/' + name : fDest.getParentFile().getAbsolutePath() + '/' + name;
        File f = new File(fPath);
        if (!f.mkdirs()) {
            throw new CodeEditorServletException(L.t((String)"The directory could not be created.", (Object[])new Object[0]));
        }
        response.put(KEY_FILE, (Object)f.getAbsolutePath());
        response.put(KEY_SUCCESS, (Object)"Directory created.");
        return response.toString();
    }

    private String onCreateNew(Map<String, String[]> parameterMap) throws CodeEditorServletException {
        JSONObject response = new JSONObject();
        String name = parameterMap.get(KEY_NAME)[0];
        String type = parameterMap.get(KEY_TYPE)[0];
        String indicator = parameterMap.containsKey("indicator") ? parameterMap.get("indicator")[0] : null;
        String orderActionType = parameterMap.containsKey("orderActionType") ? parameterMap.get("orderActionType")[0] : null;
        String mcType = parameterMap.containsKey("mcType") ? parameterMap.get("mcType")[0] : null;
        try {
            name = name.trim();
            if (name.isEmpty()) {
                throw new CodeEditorServletException(L.t((String)"File name cannot be blank.", (Object[])new Object[0]));
            }
            name = name.substring(0, 1).toUpperCase() + name.substring(1);
            this.validateFileName(name);
            if (type.equals("MonteCarlo")) {
                if (mcType.equals("Manipulation")) {
                    type = "MonteCarloManipulation";
                } else if (mcType.equals("Retest")) {
                    type = "MonteCarloRetest";
                }
            }
            Template template = CodeEditorServlet.getTemplatesInstance().findTemplateByFileName(type);
            String blockRelPath = SQUtils.trimFilePath((String)template.getTemplateFileDirectoryPath(), (String)Templates.TEMPLATES_PATH);
            String destPath = SQStructure.getSnippetsUserDirPath() + blockRelPath;
            switch (type) {
                case "BlocksIndicators": {
                    File fDest = new File(destPath + '/' + name);
                    if (!fDest.exists() && !fDest.mkdirs()) {
                        throw new CodeEditorServletException(L.t((String)"Unable to create directory '%s'.", (Object[])new Object[]{fDest.getAbsolutePath()}));
                    }
                    destPath = fDest.getAbsolutePath();
                    break;
                }
                case "BlocksSignal": {
                    if (indicator == null) {
                        throw new CodeEditorServletException("Indicator parameter is null");
                    }
                    boolean indyFound = false;
                    for (String srcDir : SQStructure.getSnippetsSourceDirs()) {
                        File fIndPath = new File(new File(srcDir, blockRelPath), indicator);
                        if (!fIndPath.exists()) continue;
                        indyFound = true;
                        break;
                    }
                    if (!indyFound) {
                        throw new CodeEditorServletException(L.t((String)"Cannnot create signal based on indicator '%s' because it doesn't exist.", (Object[])new Object[]{indicator}));
                    }
                    File fDest = new File(destPath, indicator);
                    destPath = fDest.getAbsolutePath();
                    break;
                }
                case "BlocksOrder": {
                    if (orderActionType == null) {
                        throw new CodeEditorServletException("OrderActionType parameter is null");
                    }
                    indicator = null;
                    File fDest = new File(destPath, orderActionType);
                    destPath = fDest.getAbsolutePath();
                    break;
                }
            }
            String newPath = template.createNewFile(name, destPath, indicator);
            response.put(KEY_FILE, (Object)newPath);
            response.put(KEY_SUCCESS, (Object)"Snippet created.");
            return response.toString();
        }
        catch (Exception e) {
            Log.error("Error creating new snippet. Exc.", (Throwable)e);
            throw new CodeEditorServletException(L.t((String)"Cannot create snippet.", (Object[])new Object[]{true}) + " " + e.getMessage());
        }
    }

    private String onCreateNewFile(Map<String, String[]> parameterMap) throws Exception {
        String newPath;
        String name = parameterMap.get(KEY_NAME)[0];
        String path = parameterMap.get(KEY_FILE)[0];
        String fileTemplate = parameterMap.get(KEY_TEMPLATE)[0];
        String ext = parameterMap.get("ext")[0];
        boolean createCodeFile = Boolean.parseBoolean(parameterMap.get("createCodeFile")[0]);
        if ((name = name.trim()).isEmpty()) {
            throw new CodeEditorServletException(L.t((String)"File name cannot be blank.", (Object[])new Object[0]));
        }
        name = name.substring(0, 1).toUpperCase() + name.substring(1);
        this.validateFileName(name);
        JSONObject response = new JSONObject();
        File fDest = new File(path);
        if (fDest.isDirectory()) {
            String absPath = fDest.getAbsolutePath().replace("\\", "/");
            if (absPath.endsWith("SQ/Blocks/Indicators")) {
                if (!(fDest = new File(fDest.getAbsolutePath() + '/' + name)).exists() && !fDest.mkdirs()) {
                    throw new CodeEditorServletException(L.t((String)"Unable to create directory '%s'.", (Object[])new Object[]{fDest.getAbsolutePath()}));
                }
                path = fDest.getAbsolutePath();
            }
            newPath = fDest.getAbsolutePath() + '/' + name + "." + ext;
        } else {
            newPath = fDest.getParentFile().getAbsolutePath() + '/' + name + "." + ext;
        }
        if (createCodeFile) {
            if (fileTemplate.equals("CodeBlocksFile")) {
                newPath = this.createCodeBlocksTemplate(newPath);
            } else {
                File f = new File(newPath);
                if (!f.createNewFile()) {
                    throw new CodeEditorServletException(L.t((String)"The file could not be created.", (Object[])new Object[0]));
                }
                newPath = f.getAbsolutePath();
            }
        } else if (fileTemplate.equals("EmptyFile")) {
            newPath = this.createEmptyFileTemplate(newPath);
        } else {
            Template template = CodeEditorServlet.getTemplatesInstance().findTemplateByPath(fileTemplate);
            newPath = template.createNewFile(name, path, null);
        }
        response.put(KEY_FILE, (Object)newPath);
        response.put(KEY_SUCCESS, (Object)L.t((String)"File created.", (Object[])new Object[0]));
        return response.toString();
    }

    private String createEmptyFileTemplate(String path) throws Exception {
        File f = new File(path);
        String content = SQUtils.fileToString((String)Templates.EMPTY_FILE_PATH);
        String packageT = SQUtils.trimFilePath((String)f.getParentFile().getAbsolutePath(), (String)SQStructure.SNIPPETS_DIR_PATH_WITHOUT_PACKAGE);
        packageT = packageT.replace("/", ".").replace(".java", "");
        content = content.replace("[package]", packageT);
        String snippetName = SQUtils.stripExtension((String)f.getName());
        content = content.replace("[class_name]", snippetName);
        CodeEditorServlet.prvStringToFile(f, content);
        return f.getAbsolutePath();
    }

    private String createCodeBlocksTemplate(String path) throws Exception {
        File f = new File(path);
        String snippetName = SQUtils.stripExtension((String)f.getName());
        String content = path.contains(new File(SQStructure.getIndyCodeBuiltinDirPath() + "PseudoCode").getAbsolutePath()) ? SQUtils.fileToString((String)Templates.PSEUDO_CODE_BLOCKS_TPL_PATH) : SQUtils.fileToString((String)Templates.CODE_BLOCKS_TPL_PATH);
        content = content.replace("SNIPPET_NAME", snippetName);
        CodeEditorServlet.prvStringToFile(f, content);
        return f.getAbsolutePath();
    }

    private String onCreateNewTemplate(Map<String, String[]> parameterMap) throws Exception {
        String path = parameterMap.get(KEY_FILE)[0];
        try {
            String successText;
            JSONObject response = new JSONObject();
            StringBuilder newPath = new StringBuilder();
            if (path.contains(",")) {
                String[] paths;
                for (String s : paths = path.split(",")) {
                    newPath.append(this.createCodeBlocksTemplate(s.trim())).append(",");
                }
                newPath = new StringBuilder(newPath.substring(0, newPath.length() - 1));
                successText = L.t((String)"Templates created.", (Object[])new Object[0]);
            } else {
                newPath = new StringBuilder(this.createCodeBlocksTemplate(path));
                successText = L.t((String)"Template created.", (Object[])new Object[0]);
            }
            response.put(KEY_FILE, (Object)newPath.toString());
            response.put(KEY_SUCCESS, (Object)successText);
            return response.toString();
        }
        catch (Exception e) {
            Log.error("The template could not be created.", (Throwable)e);
            throw new CodeEditorServletException("The template could not be created.");
        }
    }

    private boolean isNameValid(String name) {
        Pattern p = Pattern.compile("[A-Z][a-zA-Z0-9]*");
        Matcher m = p.matcher(name);
        return m.matches();
    }

    private String onListIndicators() {
        JSONObject response = new JSONObject();
        JSONArray indicators = new JSONArray();
        this.listIndicators(SQStructure.getSnippetsBuiltinDirPath(), indicators);
        this.listIndicators(SQStructure.getSnippetsUserDirPath(), indicators);
        response.put(KEY_INDICATORS, (Object)indicators);
        response.put(KEY_SUCCESS, (Object)"Indicators listed.");
        return response.toString();
    }

    private void listIndicators(String dirPath, JSONArray indicators) {
        File fDir = new File(dirPath + "/SQ/Blocks/Indicators");
        File[] children = fDir.listFiles();
        if (children != null) {
            for (File f : children) {
                if (!f.isDirectory()) continue;
                indicators.put((Object)f.getName());
            }
        }
    }

    private String onListTemplates(Map<String, String[]> parameterMap) {
        String file = parameterMap.get(KEY_FILE)[0];
        File f = new File(file);
        if (!f.isDirectory()) {
            file = f.getParentFile().getAbsolutePath();
        }
        file = SQUtils.trimFilePath((String)file, (String)SQStructure.SNIPPETS_DIR_PATH_WITHOUT_PACKAGE);
        JSONObject response = new JSONObject();
        JSONArray templatesArray = new JSONArray();
        for (Template template : CodeEditorServlet.getTemplatesInstance().getAvailableTemplates()) {
            JSONObject templateObject = new JSONObject();
            String templateFile = SQUtils.trimFilePath((String)template.getTemplateFileDirectoryPath(), (String)Templates.TEMPLATES_PATH);
            if (!file.contains(templateFile)) continue;
            templateObject.put(KEY_FILE, (Object)template.getTemplateFileAbsolutePath());
            templateObject.put(KEY_NAME, (Object)template.getName());
            templateObject.put(KEY_DESCRIPTION, (Object)template.getDescription());
            templatesArray.put((Object)templateObject);
        }
        response.put(KEY_TEMPLATES, (Object)templatesArray);
        response.put(KEY_SUCCESS, (Object)"Templates listed.");
        return response.toString();
    }

    private String onEditorAutocomplete() throws ClassNotFoundException, IOException {
        return new CodeAutoCompleteManager().getData();
    }

    private String onListCodeTypes() throws CodeEditorServletException {
        JSONObject response = new JSONObject();
        JSONArray items = new JSONArray();
        CodeEditorServlet.getFileMapInstance().searchForMissingTemplateFiles();
        for (String blockType : CodeEditorServlet.getFileMapInstance().getCodeBlocksTypes()) {
            items.put((Object)blockType);
        }
        response.put(KEY_ITEMS, (Object)items);
        response.put(KEY_SUCCESS, (Object)"Code types listed.");
        return response.toString();
    }

    private String onList(Map<String, String[]> parameterMap) throws Exception {
        String filter = parameterMap.get("filter")[0];
        String[] dirs = this.getParam(parameterMap, "dirs", "Builtin,User").split(",");
        JSONObject response = new JSONObject();
        CodeEditorServlet.getFileMapInstance().searchForMissingTemplateFiles();
        Map sourceDirs = SQStructure.getExtendsSourceDirsAsMap((String[])dirs);
        int index = 0;
        response.put(KEY_ID, index++);
        JSONArray itemArray = CodeEditorServlet.getFileMapInstance().generateTree(sourceDirs, filter, index);
        response.put(KEY_ITEM, (Object)itemArray);
        response.put(KEY_SUCCESS, (Object)"Sources listed.");
        return response.toString();
    }

    private String onGetContent(Map<String, String[]> parameterMap) throws Exception {
        File f = this.getFile(parameterMap);
        String text = SQUtils.fileToString((File)f);
        JSONObject response = new JSONObject();
        response.put(KEY_NAME, (Object)f.getName());
        response.put(KEY_TEXT, (Object)text);
        response.put(KEY_PROTECTED, ProtectedSnippets.getInstance().isProtected(f));
        response.put(KEY_SUCCESS, (Object)"ok");
        return response.toString();
    }

    private File getFile(Map<String, String[]> parameterMap) throws CodeEditorServletException {
        this.prvCheckParamExists(parameterMap, new String[]{KEY_FILE});
        String file = parameterMap.get(KEY_FILE)[0];
        File f = new File(file);
        if (!f.exists()) {
            throw new CodeEditorServletException(String.format("File '%s' doesn't exist.", file));
        }
        return f;
    }

    private String onSave(Map<String, String[]> parameterMap) throws CodeEditorServletException {
        File f = this.getFile(parameterMap);
        String data = parameterMap.get(KEY_DATA)[0];
        JSONObject response = new JSONObject();
        CodeEditorServlet.prvStringToFile(f, data);
        response.put(KEY_SUCCESS, (Object)L.t((String)"File saved.", (Object[])new Object[0]));
        return response.toString();
    }

    private String onSaveAs(Map<String, String[]> parameterMap) throws CodeEditorServletException {
        this.prvCheckParamExists(parameterMap, new String[]{KEY_FILE});
        String file = parameterMap.get(KEY_FILE)[0];
        String data = parameterMap.get(KEY_DATA)[0];
        JSONObject response = new JSONObject();
        CodeEditorServlet.prvStringToFile(file, data);
        response.put(KEY_SUCCESS, (Object)L.t((String)"File saved.", (Object[])new Object[0]));
        return response.toString();
    }

    private String onCompile(Map<String, String[]> parameterMap) throws CodeEditorServletException {
        File f = this.getFile(parameterMap);
        if (ProtectedSnippets.getInstance().isProtected(f)) {
            throw new CodeEditorServletException(L.t((String)"Protected snippet doesn't need to be compiled.", (Object[])new Object[0]));
        }
        String data = parameterMap.get(KEY_DATA)[0];
        JSONObject response = new JSONObject();
        CodeEditorServlet.prvStringToFile(f, data);
        new Thread(() -> {
            CompilationResult result;
            ArrayList<File> files = new ArrayList<File>();
            files.add(f);
            if (data.contains("IndicatorBlock")) {
                files.add(new File(SQStructure.SNIPPETS_DIR_PATH + "Internal/Indicators.java"));
                try {
                    Log.info("Generating Indicators.java");
                    IndicatorsBuilder indicatorsBuilder = new IndicatorsBuilder();
                    indicatorsBuilder.run(f);
                }
                catch (Exception e) {
                    Log.error("Generating Indicators.java failed. Exc.", (Throwable)e);
                }
            }
            if (f.getAbsolutePath().toLowerCase().endsWith(".tpl")) {
                result = new CompilationResult();
                result.success = true;
                result.addCompilationMessage(0, "<html><font color=\"green\"><b>" + L.t((String)"Nothing to compile, template file changes are automatically applied after save. Please refresh the Source code to see the difference.", (Object[])new Object[0]) + "</b></font>");
            } else {
                SnippetsCompiler compiler = SnippetsCompiler.getInstance();
                result = compiler.run(files, true);
            }
            JSONObject data1 = new JSONObject();
            JSONObject r = result.toJSON();
            r.put(KEY_FILE, (Object)f.getAbsolutePath());
            data1.put(KEY_COMPILATION_RESULT, (Object)r);
            CodeEditorServlet.getInfoSenderInstance().sendData(data1);
        }).start();
        response.put(KEY_SUCCESS, (Object)"Started.");
        return response.toString();
    }

    private String onCompileAll() {
        JSONObject response = new JSONObject();
        new Thread(() -> {
            try {
                Log.info("Generating Indicators.java");
                IndicatorsBuilder indicatorsBuilder = new IndicatorsBuilder();
                indicatorsBuilder.run();
            }
            catch (Exception e) {
                Log.error("Generating Indicators.java failed. Exc.", (Throwable)e);
            }
            SnippetsCompiler compiler = SnippetsCompiler.getInstance();
            CompilationResult result = compiler.run(true);
            if (result.success) {
                File cachedFile = new File(MainApp.getDataPath() + "/internal/autocomplete", "cache.json");
                String fileNameToDelete = cachedFile.getAbsolutePath();
                try {
                    Files.delete(Paths.get(fileNameToDelete, new String[0]));
                }
                catch (IOException e) {
                    Log.warn(String.format("Error deleting autocomplete file '%s'. Exc. %s", fileNameToDelete, e.toString()));
                }
            }
            JSONObject data = new JSONObject();
            data.put(KEY_COMPILATION_RESULT, (Object)result.toJSON());
            CodeEditorServlet.getInfoSenderInstance().sendData(data);
        }).start();
        response.put(KEY_SUCCESS, (Object)"Started.");
        return response.toString();
    }

    private String onStopCompilation() {
        JSONObject response = new JSONObject();
        response.put(KEY_SUCCESS, (Object)"Stopped.");
        return response.toString();
    }

    private String onCompilePlugin(Map<String, String[]> parameterMap) throws CodeEditorServletException {
        File f = this.getFile(parameterMap);
        if (!f.isDirectory()) {
            throw new CodeEditorServletException(L.t((String)"File is not a folder.", (Object[])new Object[0]));
        }
        JSONObject response = new JSONObject();
        new Thread(() -> {
            CompilationResult cr = this.pc.compile(f.getAbsolutePath());
            JSONObject data1 = new JSONObject();
            JSONObject r = cr.toJSON();
            r.put(KEY_PLUGIN, true);
            r.put(KEY_FILE, (Object)f.getAbsolutePath());
            data1.put(KEY_COMPILATION_RESULT, (Object)r);
            CodeEditorServlet.getInfoSenderInstance().sendData(data1);
        }).start();
        response.put(KEY_SUCCESS, (Object)"Started.");
        return response.toString();
    }

    private String onFixImports(Map<String, String[]> parameterMap) throws Exception {
        File f = this.getFile(parameterMap);
        if (ProtectedSnippets.getInstance().isProtected(f)) {
            throw new CodeEditorServletException(L.t((String)"Protected snippet doesn't need to be fixed.", (Object[])new Object[0]));
        }
        String data = parameterMap.get(KEY_DATA)[0];
        JSONObject response = new JSONObject();
        CodeEditorServlet.prvStringToFile(f, data);
        if (this.fixImports(f)) {
            response.put(KEY_TEXT, (Object)SQUtils.fileToString((File)f));
            response.put(KEY_SUCCESS, (Object)L.t((String)"New imports added.", (Object[])new Object[0]));
        } else {
            response.put(KEY_SUCCESS, (Object)L.t((String)"No new imports added.", (Object[])new Object[0]));
        }
        return response.toString();
    }

    private boolean fixImports(File f) {
        ArrayList<File> files = new ArrayList<File>();
        files.add(f);
        List dependencies = SnippetsCompilerUtils.loadDependencies();
        InMemoryJavaCompiler inMemoryCompiler = new InMemoryJavaCompiler();
        CompilationResult result = inMemoryCompiler.compile(files, dependencies);
        if (!result.success) {
            AutoImport autoImport = new AutoImport();
            return autoImport.fixImports(result, f);
        }
        return false;
    }

    private String onGetInfo() {
        JSONObject response = new JSONObject();
        new Thread(() -> {
            try {
                CompilationResult result = SnippetsCompiler.getInstance().getLastCompilationResult();
                if (result == null || result.success) {
                    return;
                }
                DataToSend toSend = new DataToSend("codeEditor", new JSONObject().put(KEY_COMPILATION_RESULT, (Object)result.toJSON()));
                SQWebSocketManager.addToDataQueue((DataToSend)toSend, (String[])new String[]{"SQEDITOR"});
            }
            catch (Exception e) {
                Log.error("Error while checking snippets. Exc.", (Throwable)e);
            }
        }).start();
        response.put(KEY_SUCCESS, (Object)"Notified");
        return response.toString();
    }

    private String onSaveLastOpenedFiles(Map<String, String[]> parameterMap) {
        JSONObject response = new JSONObject();
        String files = parameterMap.get(KEY_FILES)[0];
        try (BufferedWriter writer = new BufferedWriter(new OutputStreamWriter((OutputStream)new FileOutputStream(LAST_OPENED_SNIPPETS_FILE_PATH, false), StandardCharsets.UTF_8));){
            String[] array = files.split(",", -1);
            ArrayList<String> list = new ArrayList<String>();
            for (String s : array) {
                String line = s.trim();
                if (line.isEmpty() || list.contains(line)) continue;
                writer.write(line + "\n");
                list.add(line);
            }
        }
        catch (Exception e) {
            Log.error("Exc.", (Throwable)e);
        }
        response.put(KEY_SUCCESS, (Object)"Saved");
        return response.toString();
    }

    private String onReloadApp() {
        JSONObject response = new JSONObject();
        Log.info("Reloading registered custom classes...");
        CustomClassesReg.reloadAll();
        response.put(KEY_SUCCESS, (Object)L.t((String)"App reloaded.", (Object[])new Object[0]));
        return response.toString();
    }

    /*
     * Enabled aggressive block sorting
     * Enabled unnecessary exception pruning
     * Enabled aggressive exception aggregation
     */
    private String onLoadLastOpenedFiles() {
        JSONObject response = new JSONObject();
        JSONArray files = new JSONArray();
        ArrayList<String> list = new ArrayList<String>();
        File f = new File(LAST_OPENED_SNIPPETS_FILE_PATH);
        if (f.exists()) {
            try (FileInputStream fis = new FileInputStream(f);
                 InputStreamReader isr = new InputStreamReader((InputStream)fis, StandardCharsets.UTF_8);
                 BufferedReader reader = new BufferedReader(isr);){
                String line;
                while ((line = reader.readLine()) != null) {
                    try {
                        f = new File(line);
                        if (!f.exists() || list.contains(f.getAbsolutePath())) continue;
                        String content = CodeEditorServlet.prvFileToString(f);
                        files.put((Object)new JSONObject().put(KEY_NAME, (Object)f.getName()).put(KEY_FILE, (Object)f.getAbsolutePath()).put(KEY_PROTECTED, ProtectedSnippets.getInstance().isProtected(f)).put(KEY_TEXT, (Object)content));
                        list.add(f.getAbsolutePath());
                    }
                    catch (CodeEditorServletException codeEditorServletException) {}
                }
            }
            catch (IOException e) {
                Log.warn("Error reading last opened snippets file. Exc.", (Throwable)e);
            }
        }
        response.put(KEY_FILES, (Object)files);
        response.put(KEY_SUCCESS, (Object)"Loaded");
        return response.toString();
    }
}

