<#assign MAMethodInt>
    <@printParam block "#MAMethod#" />
</#assign>
<#assign TypeInt>
    <@printParam block "#Type#" />
</#assign>

<#-- GEN-31 (plán 090): ak MA blok nemá ani #MAMethod# ani #Type# param, MAMethod by ostal
     nepriradený -> ${MAMethod} na riadku nižšie crashne ("null or missing"). Default MODE_SMA
     zrkadlí printMAMethod `<#else> MODE_SMA`; bloky s metódou ho nižšie prepíšu. -->
<#assign MAMethod = "MODE_SMA">
<#if MAMethodInt?? && MAMethodInt?has_content>
    <#assign MAMethod>
        <@printMAMethod><@printParam block "#MAMethod#" /></@printMAMethod>
    </#assign>
</#if>

<#if TypeInt?? && TypeInt?has_content>
    <#assign MAMethod>
        <@printMAMethod><@printParam block "#Type#" /></@printMAMethod>
    </#assign>
</#if>

iMA(<@printInput block />, <@printParam block "#Period#" />, 0, ${MAMethod}, <@printComputedFromParam block />)