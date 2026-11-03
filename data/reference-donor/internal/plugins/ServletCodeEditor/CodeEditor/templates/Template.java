/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  com.strategyquant.lib.SQUtils
 *  com.strategyquant.lib.snippets.compile.SQStructure
 */
package com.strategyquant.plugin.Servlet.impl.CodeEditor.templates;

import com.strategyquant.lib.SQUtils;
import com.strategyquant.lib.snippets.compile.SQStructure;
import com.strategyquant.plugin.Servlet.impl.CodeEditor.templates.TemplateException;
import java.io.File;
import java.util.regex.Matcher;
import java.util.regex.Pattern;

public class Template {
    private final File fileTemplate;
    private String name;
    private String description;
    private String fileExt = "java";

    public Template(File f) throws TemplateException {
        this.fileTemplate = f;
        this.parse();
    }

    public String getDescription() {
        return this.description;
    }

    public String getName() {
        return this.name;
    }

    public String getExtension() {
        return this.fileExt;
    }

    public String getTemplateFileAbsolutePath() {
        return this.fileTemplate.getAbsolutePath();
    }

    public String getTemplateFileDirectoryPath() {
        return this.fileTemplate.getParentFile().getAbsolutePath();
    }

    public String getTemplateFileName() {
        return this.fileTemplate.getName();
    }

    private void parse() throws TemplateException {
        String content;
        try {
            content = SQUtils.fileToString((File)this.fileTemplate);
        }
        catch (Exception e) {
            throw new TemplateException("Unable to read template file");
        }
        int index = content.indexOf("</definition>");
        if (index == -1) {
            throw new TemplateException("Missing tag <definition></definition>");
        }
        content = content.substring(0, index);
        this.name = this.parseTextBetweenTags("name", content);
        this.description = this.parseTextBetweenTags("description", content);
        this.fileExt = this.parseTextBetweenTags("extension", content);
    }

    private String parseTextBetweenTags(String tag, String content) throws TemplateException {
        Pattern pattern = Pattern.compile("<" + tag + ">.*</" + tag + ">");
        Matcher matcher = pattern.matcher(content);
        if (matcher.find()) {
            String text = matcher.group().trim();
            text = text.replaceAll("<" + tag + ">", "");
            text = text.replaceAll("</" + tag + ">", "");
            return text;
        }
        throw new TemplateException("Missing tag <" + tag + "></" + tag + ">");
    }

    public String createNewFile(String fileName, String destPath, String indicatorName) throws TemplateException {
        File fDest = new File(destPath);
        if (!fDest.exists() && !fDest.mkdirs()) {
            throw new TemplateException("Unable to create directory path");
        }
        String fPath = fDest.isDirectory() ? fDest.getAbsolutePath() + '/' + fileName + "." + this.fileExt : fDest.getParentFile().getAbsolutePath() + '/' + fileName + "." + this.fileExt;
        File f = new File(fPath);
        if (f.exists()) {
            throw new TemplateException("File with this name already exists.");
        }
        String content = this.generateContent(fileName, f, indicatorName);
        try {
            SQUtils.stringToFile((File)f, (String)content);
        }
        catch (Exception e) {
            throw new TemplateException(String.format("Unable to write file '%s'. Exc. %s", f.getPath(), e.toString()), e);
        }
        return f.getAbsolutePath();
    }

    private String generateContent(String className, File targetFile, String indicatorName) throws TemplateException {
        String content;
        try {
            content = SQUtils.fileToString((File)this.fileTemplate);
        }
        catch (Exception e) {
            throw new TemplateException(String.format("Unable to read template file '%s'. Exc. %s", targetFile.getPath(), e.toString()), e);
        }
        content = Template.removeDefinition(content);
        content = content.replace("[class_name]", className);
        if (indicatorName != null) {
            content = content.replace("[indicator_name]", indicatorName);
        }
        String packageT = SQUtils.trimFilePath((String)targetFile.getParentFile().getAbsolutePath(), (String)SQStructure.getSnippetsUserDirPath());
        packageT = packageT.replace("/", ".").replace(".java", "");
        content = content.replace("[package]", packageT);
        return content;
    }

    private static String removeDefinition(String content) {
        String endTag = "</definition>";
        int index = content.indexOf(endTag);
        if (index != -1) {
            content = content.substring(index + endTag.length());
        }
        return content.trim();
    }
}

