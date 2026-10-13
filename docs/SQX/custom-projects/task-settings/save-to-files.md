# `SaveToFiles` task

Exports strategies / databank / trades / source code to disk. Section: `SaveToFiles`.

```xml
<Settings>
  <SaveToFiles>
    <OverwriteFiles>true</OverwriteFiles>
    <SaveInSqxFormat>true</SaveInSqxFormat><DestDirectorySqx>C:/out/sqx</DestDirectorySqx>
    <SaveInStrFormat>false</SaveInStrFormat><DestDirectoryStr />
    <ExportDatabank>false</ExportDatabank><DestDirectoryDatabank />
    <ExportTrades>false</ExportTrades><DestDirectoryTrades />
    <SaveInHtmlFormat>false</SaveInHtmlFormat><DestDirectoryHtml />
    <SaveInPdfFormat>false</SaveInPdfFormat><DestDirectoryPdf />
    <SaveSourceCode type="…" format="…" /><DestDirectorySC />
    <MNActive>false</MNActive><MNValue>12345</MNValue>
    <Data>all</Data><Format>xlsx</Format><UseComma>false</UseComma>
    <SetNoteActive>false</SetNoteActive><SetNoteType>timeframe</SetNoteType><SetNoteCustom />
  </SaveToFiles>
</Settings>
```

- Every `DestDirectory*` element must EXIST as an element (even empty); when its flag is `true`,
  the directory itself must exist on disk.

Default template: `internal/plugins/TaskSaveToFiles/task.xml`.
