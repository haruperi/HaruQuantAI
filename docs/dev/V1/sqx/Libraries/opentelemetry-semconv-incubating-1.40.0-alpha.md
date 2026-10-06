# opentelemetry-semconv-incubating-1.40.0-alpha.jar

[Group index](README.md) | [All archives](../README.md)

## Scope and provenance

- **Donor:** `SQX_145_REFERENCE_ROOT/internal/libs/opentelemetry-semconv-incubating-1.40.0-alpha.jar`.
- **SHA-256:** `b73e725e970e3120670d3e64b8ff058fba495b0e8040b259b50dd38e030380e4`; accessed 2026-10-06; captured `2026-10-06T18:54:51.906614+00:00`.
- **Classes:** 227 raw entries; 227 unique entry names. Duplicate occurrence indices are zero-based.
- **Inspection:** read-only ZIP hashing and class-file structural parsing; signatures/descriptors, modifiers, hierarchy and references only. Bytecode bodies are hashed, not published.
- **Allocation:** proposed `FEAT-HOST-OPENTELEMETRY-SEMCONV-INCUBATING`, P01; [roadmap](../../sqx-full-application-roadmap.md). Domain README registration remains required.
- **Repository:** `01067f00031428613c6394064ca1bcadc1ba00ee`; review state unreviewed. Download label 145-dev1; installed build/activation and runtime equivalence unverified.
- **Limit:** every class/member is inventoried; declaration coverage does not establish consumed calls, defaults, formulas, failure semantics or algorithm parity.
- **Archive/resource index:** [095.json](../../../evidence/sqx145/archives/145/095.json).

## Complete member declarations

Member shards contain exact JVM names/descriptors, access flags, generic signatures, throws types, declared fields/methods, superclass/interfaces and referenced class names. All classes, nested/synthetic members and overloads are retained. Code length/hash is structural evidence, not a normalized algorithm comparison.

- [001.json](../../../evidence/sqx145/members/095/001.json) — SHA-256 `989d43c671dfad610ad492d54876943b9f670e656cd8cabf8e4ada8addb234f6`.
- [002.json](../../../evidence/sqx145/members/095/002.json) — SHA-256 `dfad3ab58a1c0f3c5918c57e77e121e0e1f28c0de0954ee4c79bcb3e969bdecc`.
- [003.json](../../../evidence/sqx145/members/095/003.json) — SHA-256 `556fcf876ace1cd619cbecd92111ce656600f9f1204369591f8f7cacc6f62a93`.

## Focused structural diagram

Up to twelve non-nested classes; arrows show declared inheritance/interfaces only. External type names are not evidence of an available body or an executed dependency.

```mermaid
classDiagram
    class C0["AndroidIncubatingAttributes"]
    class C1["AppIncubatingAttributes"]
    class C2["ArtifactIncubatingAttributes"]
    class C3["AwsIncubatingAttributes"]
    class C4["AzIncubatingAttributes"]
    class C5["AzureIncubatingAttributes"]
    class C6["BrowserIncubatingAttributes"]
    class C7["CassandraIncubatingAttributes"]
    class C8["CicdIncubatingAttributes"]
    class C9["ClientIncubatingAttributes"]
    class C10["CloudIncubatingAttributes"]
    class C11["CloudeventsIncubatingAttributes"]
```

## Class inventory

| Archive entry | Occurrence | Class SHA-256 | Fields | Methods |
| --- | ---: | --- | ---: | ---: |
| `io/opentelemetry/semconv/incubating/AndroidIncubatingAttributes$AndroidAppStateIncubatingValues.class` | 0 | `5aea7cbab180cf5a8fab9fec125afbb5d3e1009951a1a95502dd7f494afead44` | 3 | 1 |
| `io/opentelemetry/semconv/incubating/AndroidIncubatingAttributes$AndroidStateIncubatingValues.class` | 0 | `26795527b209d386245b337fd01b7222122484155c097b4995800169935646e4` | 3 | 1 |
| `io/opentelemetry/semconv/incubating/AndroidIncubatingAttributes.class` | 0 | `65e6a9752963f8496b877906ad6a522e42a62d6db0898ca7f13e5bf1689efa19` | 3 | 2 |
| `io/opentelemetry/semconv/incubating/AppIncubatingAttributes.class` | 0 | `59e040e6774058989ca5ebe28c0efb6a7af903c3ef2983f4ab093566848edee9` | 11 | 2 |
| `io/opentelemetry/semconv/incubating/ArtifactIncubatingAttributes.class` | 0 | `4b0adcece9adac264c4e04247a4bef66276fa72071dd0beffec1a62f307e7bb4` | 7 | 2 |
| `io/opentelemetry/semconv/incubating/AwsIncubatingAttributes$AwsEcsLaunchtypeIncubatingValues.class` | 0 | `77428f5206a95a7560dcd6767d88c5bd3401038972445400406ee02553ee9a15` | 2 | 1 |
| `io/opentelemetry/semconv/incubating/AwsIncubatingAttributes.class` | 0 | `1a0d981d1bbea69f2e48b5ae148c3bcec01293646792ee71ffbfb731f9acdfe4` | 52 | 2 |
| `io/opentelemetry/semconv/incubating/AzIncubatingAttributes.class` | 0 | `aa42b802d669fe61e039403fc893a32c2d07a3d1a2bf90c5e0b2ccd72113bb42` | 2 | 2 |
| `io/opentelemetry/semconv/incubating/AzureIncubatingAttributes$AzureCosmosdbConnectionModeIncubatingValues.class` | 0 | `b5749d6db2f67d67ea1447ff15c6f5ff556a305b88745c8dea5db87554b48cdb` | 2 | 1 |
| `io/opentelemetry/semconv/incubating/AzureIncubatingAttributes$AzureCosmosdbConsistencyLevelIncubatingValues.class` | 0 | `85f3ad80ef338ec44b0e4af5279693ff64c7f5da08a4413188a064bb779c642e` | 5 | 1 |
| `io/opentelemetry/semconv/incubating/AzureIncubatingAttributes.class` | 0 | `22d56096933cb2136a3a44f2080e51c3f563546c8014a999601d7be2615cfac7` | 9 | 2 |
| `io/opentelemetry/semconv/incubating/BrowserIncubatingAttributes.class` | 0 | `b6fd2cc69ab0764120efbff2daf95c74776c25dbad8f3c9cd6e7018224f6811c` | 4 | 2 |
| `io/opentelemetry/semconv/incubating/CassandraIncubatingAttributes$CassandraConsistencyLevelIncubatingValues.class` | 0 | `94d1bbcd65529282bdeba91bd1657af06b4f6c24691a437385de91c6770b360d` | 11 | 1 |
| `io/opentelemetry/semconv/incubating/CassandraIncubatingAttributes.class` | 0 | `3aed3e1400e77577f4272ef375edcd2373d190be2b7aa55320053c2b6fdc028b` | 6 | 2 |
| `io/opentelemetry/semconv/incubating/CicdIncubatingAttributes$CicdPipelineActionNameIncubatingValues.class` | 0 | `8635ba93d7ec22317c8194c611d363b810c8df7e80acdd31b74a58d10be883da` | 3 | 1 |
| `io/opentelemetry/semconv/incubating/CicdIncubatingAttributes$CicdPipelineResultIncubatingValues.class` | 0 | `ee0e21a98c608e7752d3da4259f2801d03cacfae33b16e0f5143d4f40eb4b557` | 6 | 1 |
| `io/opentelemetry/semconv/incubating/CicdIncubatingAttributes$CicdPipelineRunStateIncubatingValues.class` | 0 | `6ff762aa47767fa9aeb2ec3e98fce15808284662fac6ef00c85995389538ca14` | 3 | 1 |
| `io/opentelemetry/semconv/incubating/CicdIncubatingAttributes$CicdPipelineTaskRunResultIncubatingValues.class` | 0 | `a73c4e32b6efbc7e4f2305a4ef16b9583a2d510f7e51fe6b21493ac8af5e7e14` | 6 | 1 |
| `io/opentelemetry/semconv/incubating/CicdIncubatingAttributes$CicdPipelineTaskTypeIncubatingValues.class` | 0 | `2a10ecbf5c02e36d50ca564ef9975ae0ec39c19c2604bd3f344fa8904ab0c2ac` | 3 | 1 |
| `io/opentelemetry/semconv/incubating/CicdIncubatingAttributes$CicdWorkerStateIncubatingValues.class` | 0 | `d26e4a01ab8b6eb56bb1e310ca4eae7e8bf512ce5c9c7462e6452f75bb353046` | 3 | 1 |
| `io/opentelemetry/semconv/incubating/CicdIncubatingAttributes.class` | 0 | `50787ae36714166b6eb8199541223eeff15fc2c456b880fbd6b3981d71e7f186` | 16 | 2 |
| `io/opentelemetry/semconv/incubating/ClientIncubatingAttributes.class` | 0 | `534a825fb8979c6297a329ebe6aa85c23058fdf5f6a278f5b24704c1efbf91ed` | 2 | 2 |
| `io/opentelemetry/semconv/incubating/CloudIncubatingAttributes$CloudPlatformIncubatingValues.class` | 0 | `4d12b17dfed66bfc9d29300c25b05412d91b425596c04dca58a39888b3564557` | 34 | 1 |
| `io/opentelemetry/semconv/incubating/CloudIncubatingAttributes$CloudProviderIncubatingValues.class` | 0 | `6f6e92f47a034abc038d64ce3fd1ba8e2b858b814cc2cfad95f6d4e99367762b` | 11 | 1 |
| `io/opentelemetry/semconv/incubating/CloudIncubatingAttributes.class` | 0 | `16183ea806746d1f87b37b13c51e37a62ae1518572328a123fe82774aaa24069` | 6 | 2 |
| `io/opentelemetry/semconv/incubating/CloudeventsIncubatingAttributes.class` | 0 | `b6e518c463acf9d942f9d8ccaf6d2a36da832f6b817e4f227eb0d7cdc1b0c7c4` | 5 | 2 |
| `io/opentelemetry/semconv/incubating/CloudfoundryIncubatingAttributes.class` | 0 | `317b79c09ad929aff4c368aab9a728dee82373dadb95a325220de7275bef0bad` | 11 | 2 |
| `io/opentelemetry/semconv/incubating/CodeIncubatingAttributes.class` | 0 | `e40cb79b69943a6a22b8a76327b8a6c54f6ef1bcd881cf5f97ed8e9aa3124560` | 10 | 2 |
| `io/opentelemetry/semconv/incubating/ContainerIncubatingAttributes$ContainerCpuStateIncubatingValues.class` | 0 | `642d1570e162415f8d6a77eff1740de1ec1240f9fccc752a039c8328afe83a97` | 3 | 1 |
| `io/opentelemetry/semconv/incubating/ContainerIncubatingAttributes.class` | 0 | `e390143e5ec7687d0dcad0704d1f34a6946be157a380904e3243a25e518b4f3e` | 18 | 2 |
| `io/opentelemetry/semconv/incubating/CpuIncubatingAttributes$CpuModeIncubatingValues.class` | 0 | `116d5575b5a87173390c68b8ed35da1dd68e04311c539aa5a8bc6588d60143a9` | 8 | 1 |
| `io/opentelemetry/semconv/incubating/CpuIncubatingAttributes.class` | 0 | `354e0a13937598463902b3169175390e75de7e5c9c7a4f2129908c91d2142c1f` | 2 | 2 |
| `io/opentelemetry/semconv/incubating/CpythonIncubatingAttributes$CpythonGcGenerationIncubatingValues.class` | 0 | `601df6dbeeeddf171d4167b75969af318c01e68045cdf5cecfc897230050a40f` | 3 | 1 |
| `io/opentelemetry/semconv/incubating/CpythonIncubatingAttributes.class` | 0 | `652b8f822ce344ea8ca2b699db3e18528ddb55ce9687c11235130681a8e12c41` | 1 | 2 |
| `io/opentelemetry/semconv/incubating/DbIncubatingAttributes$DbCassandraConsistencyLevelIncubatingValues.class` | 0 | `b59dd39230e3f6d58c14c50ac64d8bd8354a18a8a891ae2550b2e5097d0e0ffd` | 11 | 1 |
| `io/opentelemetry/semconv/incubating/DbIncubatingAttributes$DbClientConnectionStateIncubatingValues.class` | 0 | `567e830ef9825c22b772808b8b849c3b49ccb2c7d0985328cbd90713f0df073c` | 2 | 1 |
| `io/opentelemetry/semconv/incubating/DbIncubatingAttributes$DbClientConnectionsStateIncubatingValues.class` | 0 | `c171eb0edc8a58287ba1c1a7429ae6781d408a28e1a09d9f0b27edb0309c7898` | 2 | 1 |
| `io/opentelemetry/semconv/incubating/DbIncubatingAttributes$DbCosmosdbConnectionModeIncubatingValues.class` | 0 | `8df27586572c33e4689ac991828bb3d8ae602b84866405bc666f3791e750ce8b` | 2 | 1 |
| `io/opentelemetry/semconv/incubating/DbIncubatingAttributes$DbCosmosdbConsistencyLevelIncubatingValues.class` | 0 | `f904354f28ca01fc2e7e39661871a0ad1ca7ad0082901873dbf429c0f48ff953` | 5 | 1 |
| `io/opentelemetry/semconv/incubating/DbIncubatingAttributes$DbCosmosdbOperationTypeIncubatingValues.class` | 0 | `944d3dc1276136a0b0956529eca855f3451660559ff7ef66ab45eb7f97fe3417` | 15 | 1 |
| `io/opentelemetry/semconv/incubating/DbIncubatingAttributes$DbSystemIncubatingValues.class` | 0 | `d364281593cc8bbc85de20d8e61886b5c0511c99d09216e00142af7fd8b75fc8` | 54 | 1 |
| `io/opentelemetry/semconv/incubating/DbIncubatingAttributes$DbSystemNameIncubatingValues.class` | 0 | `eafe7941c0e4f5ed66eb9c06a46b6ccc701680bfba30ba5b2f6e43e3f8093546` | 41 | 1 |
| `io/opentelemetry/semconv/incubating/DbIncubatingAttributes.class` | 0 | `b8cc64e0186585a9b0056d11f220602c26e071b8b863717c168a467411b1201b` | 48 | 2 |
| `io/opentelemetry/semconv/incubating/DeploymentIncubatingAttributes$DeploymentStatusIncubatingValues.class` | 0 | `189c4c1827e3dbbb9c298d803a2522c8457151ab33ff139a89cc043cd65bdccf` | 2 | 1 |
| `io/opentelemetry/semconv/incubating/DeploymentIncubatingAttributes.class` | 0 | `a051ae4fd0764409c5adb2afa237360398244eb68866f497a4b81921c9d66df6` | 5 | 2 |
| `io/opentelemetry/semconv/incubating/DestinationIncubatingAttributes.class` | 0 | `85e0124ade5b9f056b594c2220c1cfbe32e0ec5669d672ef2f6c1c8fa8cd9ad9` | 2 | 2 |
| `io/opentelemetry/semconv/incubating/DeviceIncubatingAttributes.class` | 0 | `4eb69e5e2d15d03ec0c04ffed5eaaa4ff4b7c5a2b4c4b95bcc03ed0d41db8385` | 4 | 2 |
| `io/opentelemetry/semconv/incubating/DiskIncubatingAttributes$DiskIoDirectionIncubatingValues.class` | 0 | `14fd12d7fd82f20c6a619066fbfde527c71ea61694a25c4de5c2ad93c9b67959` | 2 | 1 |
| `io/opentelemetry/semconv/incubating/DiskIncubatingAttributes.class` | 0 | `f32d236fb336233360952abed8c9d513af287f2ebcfbe91257c22ed478f1c5d9` | 1 | 2 |
| `io/opentelemetry/semconv/incubating/DnsIncubatingAttributes.class` | 0 | `ed63cb580ab1e099f7c081c0dfc20dfdc3d5d49285e8df830970e040aca91298` | 2 | 2 |
| `io/opentelemetry/semconv/incubating/ElasticsearchIncubatingAttributes.class` | 0 | `5c4a4dec2b34a087e27ebb6bf2b37ea225e4228ddcb3b94de955ce0d14a06bb7` | 1 | 2 |
| `io/opentelemetry/semconv/incubating/EnduserIncubatingAttributes.class` | 0 | `85675b0a4b85ce94d307504a71b41f9e378225d2e4cccbd3911877a6e043794e` | 4 | 2 |
| `io/opentelemetry/semconv/incubating/ErrorIncubatingAttributes$ErrorTypeIncubatingValues.class` | 0 | `b576d5e0460da8fc28964e8822b0fd2187036b3f8681fc01d6a14de2d7807fb2` | 1 | 1 |
| `io/opentelemetry/semconv/incubating/ErrorIncubatingAttributes.class` | 0 | `fd253fbb4ba63b81536072dd0ffe894ba00b4927aca1b31b8a241a602046f63a` | 2 | 2 |
| `io/opentelemetry/semconv/incubating/EventIncubatingAttributes.class` | 0 | `a91309cda8518344bd42734eebfd87e6d132fb9c08cb7d3efb1eabf84b19efb5` | 1 | 2 |
| `io/opentelemetry/semconv/incubating/ExceptionIncubatingAttributes.class` | 0 | `643b22c3eb9d328f5c593cd01ac095a79d4435c5b1f668fc2730137ed72611de` | 3 | 2 |
| `io/opentelemetry/semconv/incubating/FaasIncubatingAttributes$FaasDocumentOperationIncubatingValues.class` | 0 | `7c489b0b8ebfb9cfc42b340eb52d0e3b6f99c6782206495b77f41f516dbfde94` | 3 | 1 |
| `io/opentelemetry/semconv/incubating/FaasIncubatingAttributes$FaasInvokedProviderIncubatingValues.class` | 0 | `31f5f4343a99f3ef5f495013325385abcd2d372c05bee08a5409f70753f8f408` | 5 | 1 |
| `io/opentelemetry/semconv/incubating/FaasIncubatingAttributes$FaasTriggerIncubatingValues.class` | 0 | `c76e428e2742ba1091354e7e6898d1877e82449fa2f5fd42db5b8717556fd41c` | 5 | 1 |
| `io/opentelemetry/semconv/incubating/FaasIncubatingAttributes.class` | 0 | `31c41bd3e3ef8a8e6e2df81bb6d6cbafde9abbae8deff8bd86a8196d7f725808` | 16 | 2 |
| `io/opentelemetry/semconv/incubating/FeatureFlagIncubatingAttributes$FeatureFlagEvaluationReasonIncubatingValues.class` | 0 | `e019ff806f5a0b5718d1793569f511c659c95603eea67f608573033e43827b99` | 9 | 1 |
| `io/opentelemetry/semconv/incubating/FeatureFlagIncubatingAttributes$FeatureFlagResultReasonIncubatingValues.class` | 0 | `e2476f46c85270ef6461709eb2a7e15aa3ca685c1368aa826fb058cb7a9adcfb` | 9 | 1 |
| `io/opentelemetry/semconv/incubating/FeatureFlagIncubatingAttributes.class` | 0 | `8b6b1b1bfd1e3507a28083e46116567ea14b901ffd5037f0c5c890157ccfe686` | 11 | 2 |
| `io/opentelemetry/semconv/incubating/FileIncubatingAttributes.class` | 0 | `9f64546bc6704a16b58fb47f5b446b0b7e4a9df4d3054befdba69784f7675283` | 18 | 2 |
| `io/opentelemetry/semconv/incubating/GcpIncubatingAttributes$GcpApphubDestinationServiceCriticalityTypeIncubatingValues.class` | 0 | `ea12b71dd23a97156b17ca3df82c3a9d3abf64d1c39cfa0fd3ca25536670d345` | 4 | 1 |
| `io/opentelemetry/semconv/incubating/GcpIncubatingAttributes$GcpApphubDestinationServiceEnvironmentTypeIncubatingValues.class` | 0 | `081c0f12fab93146547db23972e4adf003c7f0aaba0cc3aa285b78f2e88a05f5` | 4 | 1 |
| `io/opentelemetry/semconv/incubating/GcpIncubatingAttributes$GcpApphubDestinationWorkloadCriticalityTypeIncubatingValues.class` | 0 | `3df3dac71d989b0bfe291d48585440c0179f14d55e35e98910a4b47b96b26972` | 4 | 1 |
| `io/opentelemetry/semconv/incubating/GcpIncubatingAttributes$GcpApphubDestinationWorkloadEnvironmentTypeIncubatingValues.class` | 0 | `9c25a3e920533969a242084d1f0f7b0f369a1ff7c7daa5578c51a1b6c31a9bee` | 4 | 1 |
| `io/opentelemetry/semconv/incubating/GcpIncubatingAttributes$GcpApphubServiceCriticalityTypeIncubatingValues.class` | 0 | `70dc332db56f66e8dde6b18a76ee3d74e52df4e74d0f677909bdd1ba37326de7` | 4 | 1 |
| `io/opentelemetry/semconv/incubating/GcpIncubatingAttributes$GcpApphubServiceEnvironmentTypeIncubatingValues.class` | 0 | `6ee3663cf15be06911030698d453f0468de74973df216c53c2751b35789202e9` | 4 | 1 |
| `io/opentelemetry/semconv/incubating/GcpIncubatingAttributes$GcpApphubWorkloadCriticalityTypeIncubatingValues.class` | 0 | `a58e96f8f32ef06e298e001b4cdf0735cbd6f5908ce7551ba9cbeb9f78274424` | 4 | 1 |
| `io/opentelemetry/semconv/incubating/GcpIncubatingAttributes$GcpApphubWorkloadEnvironmentTypeIncubatingValues.class` | 0 | `c0a034fff31d4d04019501908e881ec9a9d0a926100e4d51970c2799edb82328` | 4 | 1 |
| `io/opentelemetry/semconv/incubating/GcpIncubatingAttributes.class` | 0 | `945f231900b796a5eced508c2d6103e7a7a06d459aac5ad267ea0284a57624cc` | 26 | 2 |
| `io/opentelemetry/semconv/incubating/GenAiIncubatingAttributes$GenAiOpenaiRequestResponseFormatIncubatingValues.class` | 0 | `feb2d496985584925529b34e3b7246357518b1be4b988d5cc2432e9de26ce693` | 3 | 1 |
| `io/opentelemetry/semconv/incubating/GenAiIncubatingAttributes$GenAiOpenaiRequestServiceTierIncubatingValues.class` | 0 | `7be7b0abbd62154cd96c9e7c7f4b024faacca7c0d4850d5dc9229e0d58bf65c0` | 2 | 1 |
| `io/opentelemetry/semconv/incubating/GenAiIncubatingAttributes$GenAiOperationNameIncubatingValues.class` | 0 | `eb6bc16eaec7525d51bf09d2f42cf3f82a489dd56d1bb0bbe29602459781ecf3` | 8 | 1 |
| `io/opentelemetry/semconv/incubating/GenAiIncubatingAttributes$GenAiOutputTypeIncubatingValues.class` | 0 | `693d4ea8105582d845c958f18f3258a75d6c9e9bad087520dbc5b9b5ff9144f2` | 4 | 1 |
| `io/opentelemetry/semconv/incubating/GenAiIncubatingAttributes$GenAiProviderNameIncubatingValues.class` | 0 | `139d0e577e01307b9f863336a4f9c5c4f78e9bc1dcce4052dc8df546cdff0f7b` | 15 | 1 |
| `io/opentelemetry/semconv/incubating/GenAiIncubatingAttributes$GenAiSystemIncubatingValues.class` | 0 | `6da84724ddb59268207ed87b90b65497f10c6a93b61b51bca3adf64e2de5829b` | 19 | 1 |
| `io/opentelemetry/semconv/incubating/GenAiIncubatingAttributes$GenAiTokenTypeIncubatingValues.class` | 0 | `cb68be02927e651d520b828d3b769971c96b6880f9f31ccfb397ddc241c5044e` | 3 | 1 |
| `io/opentelemetry/semconv/incubating/GenAiIncubatingAttributes.class` | 0 | `dcaaaa3f23de7f638946352be9d8c806ef969d3c5222c47ee21ee58db7affdb2` | 49 | 2 |
| `io/opentelemetry/semconv/incubating/GeoIncubatingAttributes$GeoContinentCodeIncubatingValues.class` | 0 | `43303f4292934cfa8540b26560d6f723b028fbde828e2972a01bf3427ec304a6` | 7 | 1 |
| `io/opentelemetry/semconv/incubating/GeoIncubatingAttributes.class` | 0 | `31dc326c7739dae6449561e5e7714fbad28cf60b91a7a4528d84711fc8f5ead2` | 7 | 2 |
| `io/opentelemetry/semconv/incubating/GoIncubatingAttributes$GoMemoryTypeIncubatingValues.class` | 0 | `43fb618df126a9511519170b30fe590e59fa17a5a98505262ef500da75051875` | 2 | 1 |
| `io/opentelemetry/semconv/incubating/GoIncubatingAttributes.class` | 0 | `82965b42f9ab3298b9f9eaa3534984040f55d2b940345acd03838726167e2101` | 1 | 2 |
| `io/opentelemetry/semconv/incubating/GraphqlIncubatingAttributes$GraphqlOperationTypeIncubatingValues.class` | 0 | `2a798057d0982d78b0ab27fd28505b7b20004c0f102385404118aa65c9a0ea40` | 3 | 1 |
| `io/opentelemetry/semconv/incubating/GraphqlIncubatingAttributes.class` | 0 | `09212f47eb67fdca409684d53a1e9bb1be7816a1e2fda0ee1501613dfc7540ad` | 3 | 2 |
| `io/opentelemetry/semconv/incubating/HerokuIncubatingAttributes.class` | 0 | `f4626eac28f145f17e7855e2c7aa3fd8d3e33ee70f8e85f18267fe99ccf67cf0` | 3 | 2 |
| `io/opentelemetry/semconv/incubating/HostIncubatingAttributes$HostArchIncubatingValues.class` | 0 | `b84c2c35720cb97ad7f15b8ee2cae48f4f5d0bc5a1d1103aa27794f7000b58ef` | 8 | 1 |
| `io/opentelemetry/semconv/incubating/HostIncubatingAttributes.class` | 0 | `f5aba391563092271cbf5713d48911cace9c05c29057dbea411fe8046b039b49` | 15 | 2 |
| `io/opentelemetry/semconv/incubating/HttpIncubatingAttributes$HttpConnectionStateIncubatingValues.class` | 0 | `df7b3158c1199cb3244d53b482807d4555a7fadadb8fef3f3ef09ffc8ae5ae49` | 2 | 1 |
| `io/opentelemetry/semconv/incubating/HttpIncubatingAttributes$HttpFlavorIncubatingValues.class` | 0 | `27edd2fe21ab57f1975418dce28a86957813cde197a3f56b99ccee2e232cf078` | 6 | 1 |
| `io/opentelemetry/semconv/incubating/HttpIncubatingAttributes$HttpRequestMethodIncubatingValues.class` | 0 | `7f4455590c8749dfeb9310927f0494facde419a0e4fd75969cf4812021bdb5ff` | 11 | 1 |
| `io/opentelemetry/semconv/incubating/HttpIncubatingAttributes.class` | 0 | `7637af146746e19574aa62652110a36b722ff29d91a2c8e6f5495a16dc054af4` | 26 | 2 |
| `io/opentelemetry/semconv/incubating/HwIncubatingAttributes$HwBatteryStateIncubatingValues.class` | 0 | `db858be460069b17b82dcd69be83e81d209e8e339d75cedc90767ee44bfec907` | 2 | 1 |
| `io/opentelemetry/semconv/incubating/HwIncubatingAttributes$HwGpuTaskIncubatingValues.class` | 0 | `eacc0a3b6f6c2aaebfd7e8e2588dbe14a8f30c8d253882c3a32e74648075db7d` | 3 | 1 |
| `io/opentelemetry/semconv/incubating/HwIncubatingAttributes$HwLimitTypeIncubatingValues.class` | 0 | `bf3065959a8e9e4be3d86b0fc3000a87b72ccef393ad91ad4eb8ff6fcf6b8802` | 9 | 1 |
| `io/opentelemetry/semconv/incubating/HwIncubatingAttributes$HwLogicalDiskStateIncubatingValues.class` | 0 | `1655cf4f49208a5adf0856c4a7222b178a1af7ca72e5282a4713d149d790933a` | 2 | 1 |
| `io/opentelemetry/semconv/incubating/HwIncubatingAttributes$HwPhysicalDiskStateIncubatingValues.class` | 0 | `c5db84900a45a4506311d1aec3d25b28c685c550926cf2aeaac7f1553bfb0aa0` | 1 | 1 |
| `io/opentelemetry/semconv/incubating/HwIncubatingAttributes$HwStateIncubatingValues.class` | 0 | `c4f59eba1e09c39d46a98e57ca3b2d3afea489cca7bdb55a348964bb89a9faa8` | 5 | 1 |
| `io/opentelemetry/semconv/incubating/HwIncubatingAttributes$HwTapeDriveOperationTypeIncubatingValues.class` | 0 | `b6986caff408503f6a50175084513b1a60c249edd9c071f8ff76f8cee584f27a` | 3 | 1 |
| `io/opentelemetry/semconv/incubating/HwIncubatingAttributes$HwTypeIncubatingValues.class` | 0 | `b5d9d560379843ca9303e410a3cfb5c0b4352b3274f2573faee021f306665cfa` | 14 | 1 |
| `io/opentelemetry/semconv/incubating/HwIncubatingAttributes.class` | 0 | `73436992736ac86963b7cd36b42202b198f2d75bdad555231dcb5da08ab9ba9d` | 27 | 2 |
| `io/opentelemetry/semconv/incubating/JsonrpcIncubatingAttributes.class` | 0 | `6857042e80406792bfa556c692b840704ec29b9422f38aaefd4bc66a85a9b4c3` | 2 | 2 |
| `io/opentelemetry/semconv/incubating/JvmIncubatingAttributes$JvmMemoryTypeIncubatingValues.class` | 0 | `3d02453f4d764908a9d279901aae0fa2f4dda7a51a71625a5ba571b5dbbfa59e` | 2 | 1 |
| `io/opentelemetry/semconv/incubating/JvmIncubatingAttributes$JvmThreadStateIncubatingValues.class` | 0 | `97f94bc70320e4f5c9e7c43b5649ba0ccfe063b39a524bbe1f2ab46966764425` | 6 | 1 |
| `io/opentelemetry/semconv/incubating/JvmIncubatingAttributes.class` | 0 | `cee577a1a69d20cde08fbe434bafa529590ef466b3738e3cf6e8e211bcc5e38d` | 8 | 2 |
| `io/opentelemetry/semconv/incubating/K8sIncubatingAttributes$K8sContainerStatusReasonIncubatingValues.class` | 0 | `4938af2adddb7d62f79544b7a5d56dab29cca39e0dfb8b8681d1767b8b0b5d05` | 9 | 1 |
| `io/opentelemetry/semconv/incubating/K8sIncubatingAttributes$K8sContainerStatusStateIncubatingValues.class` | 0 | `1a14a25b6e83e70bdd65e159d8f1a19b7a8a8eead56ae72cd16e58911447efbb` | 3 | 1 |
| `io/opentelemetry/semconv/incubating/K8sIncubatingAttributes$K8sNamespacePhaseIncubatingValues.class` | 0 | `4ba220cc269ee761ccc54fd524b2e85d24601f96e1a9841d4bd5fe7306b97689` | 2 | 1 |
| `io/opentelemetry/semconv/incubating/K8sIncubatingAttributes$K8sNodeConditionStatusIncubatingValues.class` | 0 | `20ca9e7735a9ecd506617e7ac375dbeed74ba7290502e038b9e8375d237090fb` | 3 | 1 |
| `io/opentelemetry/semconv/incubating/K8sIncubatingAttributes$K8sNodeConditionTypeIncubatingValues.class` | 0 | `3bf6776d2b7965b99f17bfd0ca8f2718bb4466e08f7c5176dd056e37399809c5` | 5 | 1 |
| `io/opentelemetry/semconv/incubating/K8sIncubatingAttributes$K8sPodStatusPhaseIncubatingValues.class` | 0 | `28befd0c1c96e9a4fecfc65be0e5082cde4df625a22609e66a5fc076f6d161a1` | 5 | 1 |
| `io/opentelemetry/semconv/incubating/K8sIncubatingAttributes$K8sPodStatusReasonIncubatingValues.class` | 0 | `54414e8cd1a58e8ff0fb6006f07791864f54023e8c60ebdcab747efca8228514` | 5 | 1 |
| `io/opentelemetry/semconv/incubating/K8sIncubatingAttributes$K8sServiceEndpointAddressTypeIncubatingValues.class` | 0 | `23198d0cdf5e4a32a393ff197338e4c9daa7c3eb5388753e1ca3e4cb31ea4da7` | 3 | 1 |
| `io/opentelemetry/semconv/incubating/K8sIncubatingAttributes$K8sServiceEndpointConditionIncubatingValues.class` | 0 | `d0c91e904473077275918a8b1e9b67681dfdf6dbef0ee60a89738b125dbe3cc1` | 3 | 1 |
| `io/opentelemetry/semconv/incubating/K8sIncubatingAttributes$K8sServiceTypeIncubatingValues.class` | 0 | `70884c508fbc1219c5f4f148dae620c05030f4836e34b9de33de653401798464` | 4 | 1 |
| `io/opentelemetry/semconv/incubating/K8sIncubatingAttributes$K8sVolumeTypeIncubatingValues.class` | 0 | `9fb063a0e69fe796aa62f0a6c499f2df15c853bc7ddd93b0d8402f0fd0ad964d` | 6 | 1 |
| `io/opentelemetry/semconv/incubating/K8sIncubatingAttributes.class` | 0 | `e78781af4f4c6d56d8b67fbaacb7ea407a5d127289ca4f3fd830f74fc871c8aa` | 77 | 2 |
| `io/opentelemetry/semconv/incubating/LinuxIncubatingAttributes$LinuxMemorySlabStateIncubatingValues.class` | 0 | `f067c64a06581ac92960a2e788b3120158c15952af035f9f525c68cba1c031c8` | 2 | 1 |
| `io/opentelemetry/semconv/incubating/LinuxIncubatingAttributes.class` | 0 | `7a1d1a9be665b12a9c7a648d0a84c1cf4a3ac923fe5b4f922d24ca0af6d92bcb` | 1 | 2 |
| `io/opentelemetry/semconv/incubating/LogIncubatingAttributes$LogIostreamIncubatingValues.class` | 0 | `dbb225dca7e9a26ca4bddc9613cf700183b6e3e5396cbb9148d80d1a69ae9d24` | 2 | 1 |
| `io/opentelemetry/semconv/incubating/LogIncubatingAttributes.class` | 0 | `a67fa6e8451e4e6d3a0ad8eefee2cdafe35ebca161844c640aabde919ca28c09` | 7 | 2 |
| `io/opentelemetry/semconv/incubating/MainframeIncubatingAttributes.class` | 0 | `f04eb68bcd9637ac2dbe28e2129c66afa3b2e6978f5cac2a90bf34f2ee1d1110` | 1 | 2 |
| `io/opentelemetry/semconv/incubating/McpIncubatingAttributes$McpMethodNameIncubatingValues.class` | 0 | `62b85de2846def08e29c52ca30f02f15eff5b882e1f0fb77ae92810d8d4114d7` | 25 | 1 |
| `io/opentelemetry/semconv/incubating/McpIncubatingAttributes.class` | 0 | `a842070d06f171d27217f1fb4ff1e928635cbe43348f9c99fbebba88545c05a1` | 4 | 2 |
| `io/opentelemetry/semconv/incubating/MessageIncubatingAttributes$MessageTypeIncubatingValues.class` | 0 | `3917fbb15a0074f11263b702080862f85a70d049ff9391faeeb1e76391a5d6c1` | 2 | 1 |
| `io/opentelemetry/semconv/incubating/MessageIncubatingAttributes.class` | 0 | `8d1a949a879573d09a32d2003c1af7b1d671d638afd253d618069748b56cb37b` | 4 | 2 |
| `io/opentelemetry/semconv/incubating/MessagingIncubatingAttributes$MessagingOperationTypeIncubatingValues.class` | 0 | `afe43f1f646a5ca6dba0b21e007749d2ef43c08f0ab96eb655457c666ad91ff8` | 7 | 1 |
| `io/opentelemetry/semconv/incubating/MessagingIncubatingAttributes$MessagingRocketmqConsumptionModelIncubatingValues.class` | 0 | `58cdea5702ed15035b6cf3c2d2d4e18e49b524ddc4b9d241eae83ba8d4298443` | 2 | 1 |
| `io/opentelemetry/semconv/incubating/MessagingIncubatingAttributes$MessagingRocketmqMessageTypeIncubatingValues.class` | 0 | `16e6d1d509443028763e582c95843f54f9e63a77d1a4be1efa919c68169278b8` | 4 | 1 |
| `io/opentelemetry/semconv/incubating/MessagingIncubatingAttributes$MessagingServicebusDispositionStatusIncubatingValues.class` | 0 | `6df5557cd0d212f2636c23575fa2a2efe7b615e851e8778db97b1c6d05bf1ce4` | 4 | 1 |
| `io/opentelemetry/semconv/incubating/MessagingIncubatingAttributes$MessagingSystemIncubatingValues.class` | 0 | `a863698dc1abbe55184b555a0b4b2478d894aacf33b3206270df0fd662843731` | 12 | 1 |
| `io/opentelemetry/semconv/incubating/MessagingIncubatingAttributes.class` | 0 | `3e1ab3711574498e540d43e248fe0c4cd259eee5f971c6159c893e54781e2704` | 46 | 2 |
| `io/opentelemetry/semconv/incubating/NetIncubatingAttributes$NetSockFamilyIncubatingValues.class` | 0 | `676af408943107e0530b0816b8db6e2333e166dafe8a5e15557747a2c65f5c9f` | 3 | 1 |
| `io/opentelemetry/semconv/incubating/NetIncubatingAttributes$NetTransportIncubatingValues.class` | 0 | `240ecc4d3efc788396311340d373989b17afc656323d5eba30c074935a5d1461` | 5 | 1 |
| `io/opentelemetry/semconv/incubating/NetIncubatingAttributes.class` | 0 | `5273f64141fe3d73491fe7e91f610da54c58256b904990bae943459919f67104` | 15 | 2 |
| `io/opentelemetry/semconv/incubating/NetworkIncubatingAttributes$NetworkConnectionStateIncubatingValues.class` | 0 | `7177691df490029789990d60d0cf940d772107e2ffcce5b0e99d62863043f937` | 11 | 1 |
| `io/opentelemetry/semconv/incubating/NetworkIncubatingAttributes$NetworkConnectionSubtypeIncubatingValues.class` | 0 | `18069739818aec9100955db7c85d9c18be87d5aead753eeea079c3fb4a87e36e` | 21 | 1 |
| `io/opentelemetry/semconv/incubating/NetworkIncubatingAttributes$NetworkConnectionTypeIncubatingValues.class` | 0 | `93fc326eba79e5cc07865626f018dd5b2057de296f623f8b3295936c7a88114a` | 5 | 1 |
| `io/opentelemetry/semconv/incubating/NetworkIncubatingAttributes$NetworkIoDirectionIncubatingValues.class` | 0 | `3f4e9554d0587a053d8d90128f9704d1336f9f2cec51fdc71733f6c253b60520` | 2 | 1 |
| `io/opentelemetry/semconv/incubating/NetworkIncubatingAttributes$NetworkTransportIncubatingValues.class` | 0 | `519d55f7a571f58827151d5e8011456ff439c7b81950eab653c30fa349b78835` | 5 | 1 |
| `io/opentelemetry/semconv/incubating/NetworkIncubatingAttributes$NetworkTypeIncubatingValues.class` | 0 | `56660fee7c89f00858096c89d4f259c857bc71eb2244716a6c5aba5d2d07722c` | 2 | 1 |
| `io/opentelemetry/semconv/incubating/NetworkIncubatingAttributes.class` | 0 | `54fc684a789196a47865e9b7198e963ca377b70539140dfa11ce2f41f373f4c0` | 17 | 2 |
| `io/opentelemetry/semconv/incubating/NfsIncubatingAttributes.class` | 0 | `941df96be19131ac3f8049ef48f5028b22a1dc138debbe3ff87f96892923f6a7` | 2 | 2 |
| `io/opentelemetry/semconv/incubating/NodejsIncubatingAttributes$NodejsEventloopStateIncubatingValues.class` | 0 | `8106c50d1e725a2b2c2a57b7129f365139c7f2f879096b800ae76ddf4046c782` | 2 | 1 |
| `io/opentelemetry/semconv/incubating/NodejsIncubatingAttributes.class` | 0 | `a17d59b29d3888e3c38e63efbccc663f9d4bd873a082cec523e9835ed6be0006` | 1 | 2 |
| `io/opentelemetry/semconv/incubating/OciIncubatingAttributes.class` | 0 | `1b8bb6a13d2868daa24281b1e80d931e990d680b1b5b42082aed3fbf2a5debec` | 1 | 2 |
| `io/opentelemetry/semconv/incubating/OncRpcIncubatingAttributes.class` | 0 | `fcedf10823c004b1827d4cea2f1d88b59846fc7d650351792f876cf14f4d77e7` | 4 | 2 |
| `io/opentelemetry/semconv/incubating/OpenaiIncubatingAttributes$OpenaiApiTypeIncubatingValues.class` | 0 | `75006e09ce65ba94a9d0baa9157de3959fa6b0ea1e584d96047bc3fb0147a7ba` | 2 | 1 |
| `io/opentelemetry/semconv/incubating/OpenaiIncubatingAttributes$OpenaiRequestServiceTierIncubatingValues.class` | 0 | `3d18fd3ed43000b240b409f52f1642168b3c38d34e777c9d635c94bc4d368804` | 2 | 1 |
| `io/opentelemetry/semconv/incubating/OpenaiIncubatingAttributes.class` | 0 | `9aff9956ec531b9856f24322e455b33aac8d5ddae65325cabe56957623a69a20` | 4 | 2 |
| `io/opentelemetry/semconv/incubating/OpenshiftIncubatingAttributes.class` | 0 | `ba8077b72ca5dea6f72b590bc8771ececaa58e7fdfb529bffb71703eea91e105` | 2 | 2 |
| `io/opentelemetry/semconv/incubating/OpentracingIncubatingAttributes$OpentracingRefTypeIncubatingValues.class` | 0 | `3df6b6e23665b7c2902f749bc883183c15338d490b43353c7e01d75f0b7cc13d` | 2 | 1 |
| `io/opentelemetry/semconv/incubating/OpentracingIncubatingAttributes.class` | 0 | `520f1875c116cdd571ad216f7121f37519ea26b2cfde4ffbf1d9548a32489a74` | 1 | 2 |
| `io/opentelemetry/semconv/incubating/OracleCloudIncubatingAttributes.class` | 0 | `7205f36be422289a80dab34355a08b0032d8c853d36860c6a31ad21024420e5f` | 1 | 2 |
| `io/opentelemetry/semconv/incubating/OracleIncubatingAttributes.class` | 0 | `86eb29b77194be51c19e9116ce25f1b5fde8b06547eb75399b486b2c4d7bfb82` | 5 | 2 |
| `io/opentelemetry/semconv/incubating/OsIncubatingAttributes$OsTypeIncubatingValues.class` | 0 | `0a1ed5ee588687ecfb3681f0e156f0da259849899913dd48b6c2ba53a9071058` | 12 | 1 |
| `io/opentelemetry/semconv/incubating/OsIncubatingAttributes.class` | 0 | `59815195a4a00da75525509af92b56e15d0e1a7d18d1853179de3111055d0905` | 5 | 2 |
| `io/opentelemetry/semconv/incubating/OtelIncubatingAttributes$OtelComponentTypeIncubatingValues.class` | 0 | `26bcd737c214c7dbf51f0c13656ace5ee18782ca36769a58bfe344afa483f41c` | 16 | 1 |
| `io/opentelemetry/semconv/incubating/OtelIncubatingAttributes$OtelSpanParentOriginIncubatingValues.class` | 0 | `64e0ceae4bb8199e4742a6c1ecb0ab5ad21a20899325e69a975211e71654c0b9` | 3 | 1 |
| `io/opentelemetry/semconv/incubating/OtelIncubatingAttributes$OtelSpanSamplingResultIncubatingValues.class` | 0 | `a3e42f6b6a2f687512c81e8da2e32bbadfe718f92a1edd031dc19c15f7d75c8c` | 3 | 1 |
| `io/opentelemetry/semconv/incubating/OtelIncubatingAttributes$OtelStatusCodeIncubatingValues.class` | 0 | `abc819ff3ded7784dec57e3363e2d04c3941a67ef4413cbb3aa05c1a4942f762` | 2 | 1 |
| `io/opentelemetry/semconv/incubating/OtelIncubatingAttributes.class` | 0 | `e0d3c468cdfcd4d0a63904d5a574b3dfb2feabbea3bd539b2f5491dc9388b79b` | 12 | 2 |
| `io/opentelemetry/semconv/incubating/OtherIncubatingAttributes$StateIncubatingValues.class` | 0 | `3cafa19e25dbac5f2d81228c52cf3b8c9c58de4b820be3e10e4a22a0f6f0f31b` | 2 | 1 |
| `io/opentelemetry/semconv/incubating/OtherIncubatingAttributes.class` | 0 | `981ab6d418dc0dfc0cf3eed9f0fd086b8192e4a683fb27d91cb7113650b62bc8` | 1 | 2 |
| `io/opentelemetry/semconv/incubating/PeerIncubatingAttributes.class` | 0 | `f94ced5273c4d3ab5bfa96c420ac613e73a129d5c80cf39260f354c76da75fd6` | 1 | 2 |
| `io/opentelemetry/semconv/incubating/PoolIncubatingAttributes.class` | 0 | `4d418c0830824612ced82f7961038d87b5a332e6e384e7c42ac1cb4228c19676` | 1 | 2 |
| `io/opentelemetry/semconv/incubating/PprofIncubatingAttributes.class` | 0 | `9d566eb5abe20046c00a646cdc58dc92970adc4c63669fcf2b5c61eb1c919449` | 11 | 2 |
| `io/opentelemetry/semconv/incubating/ProcessIncubatingAttributes$ProcessContextSwitchTypeIncubatingValues.class` | 0 | `eefbde6f7e22f5c5bfa8ba134eea4c1b5bf0eab476d3a2592039c8edc28cc899` | 2 | 1 |
| `io/opentelemetry/semconv/incubating/ProcessIncubatingAttributes$ProcessCpuStateIncubatingValues.class` | 0 | `173a5e6b3fbb0725e92dfde0eb65a90418b97502009ebef886fae4b0ee94b219` | 3 | 1 |
| `io/opentelemetry/semconv/incubating/ProcessIncubatingAttributes$ProcessPagingFaultTypeIncubatingValues.class` | 0 | `7548695dc906c903edd6939d24b3fc6006a8b92dec9adba9aaba456f04ad9612` | 2 | 1 |
| `io/opentelemetry/semconv/incubating/ProcessIncubatingAttributes$ProcessStateIncubatingValues.class` | 0 | `3c2fd5e49e2d9d609906c2bcb959c6e41e579bb1144a88e17450e94599657cb2` | 4 | 1 |
| `io/opentelemetry/semconv/incubating/ProcessIncubatingAttributes.class` | 0 | `5a309c8fd3c7ba12bb4d071ec838f9d3272a1592dd14fd44bc80bfe23148f5e5` | 37 | 2 |
| `io/opentelemetry/semconv/incubating/ProfileIncubatingAttributes$ProfileFrameTypeIncubatingValues.class` | 0 | `0236f8a5ee747039c4ff9da3a644fb4cdebe330ec4c1a114f17ab62cffebab40` | 12 | 1 |
| `io/opentelemetry/semconv/incubating/ProfileIncubatingAttributes.class` | 0 | `0673e52eea8d9876bec6f2542cbb01d2e8ae5384085c13a4bb75aaab35f51289` | 1 | 2 |
| `io/opentelemetry/semconv/incubating/RpcIncubatingAttributes$RpcConnectRpcErrorCodeIncubatingValues.class` | 0 | `6b5a3224dc04932d7556636ef5743557b221a43a4e219e5e759f01542efdfc0a` | 16 | 1 |
| `io/opentelemetry/semconv/incubating/RpcIncubatingAttributes$RpcGrpcStatusCodeIncubatingValues.class` | 0 | `3288a14c3bc9a54d3d28adb6b33bb2ebc9cd127c8710630e9d8cb213fe7d629a` | 17 | 1 |
| `io/opentelemetry/semconv/incubating/RpcIncubatingAttributes$RpcMessageTypeIncubatingValues.class` | 0 | `815f34ba36feb96d2d6c64d268019ed767cfcea37278028bdff76eb8b8a5de06` | 2 | 1 |
| `io/opentelemetry/semconv/incubating/RpcIncubatingAttributes$RpcSystemIncubatingValues.class` | 0 | `3ba71ff7aee413132651bd85bab450398f4522b751d5bf10d22b8986fb4f3901` | 7 | 1 |
| `io/opentelemetry/semconv/incubating/RpcIncubatingAttributes$RpcSystemNameIncubatingValues.class` | 0 | `fa8140de9d43119eba510ed52231f563f5cfc9a9f5eddbf84d2755fcc654048c` | 4 | 1 |
| `io/opentelemetry/semconv/incubating/RpcIncubatingAttributes.class` | 0 | `80c4b3361c5dc461f25094d9949915670b53be492ca4c5f83e7fe78b1195a85e` | 22 | 2 |
| `io/opentelemetry/semconv/incubating/SecurityRuleIncubatingAttributes.class` | 0 | `8886cdc1cf587fbb1e162f87879e5ae8bb361347eb55f0863ed82df63074903b` | 8 | 2 |
| `io/opentelemetry/semconv/incubating/ServerIncubatingAttributes.class` | 0 | `9f1c73960edd0bccf87c7cb42c8f2b1e0007446757398a7ebea511e764d3b8ad` | 2 | 2 |
| `io/opentelemetry/semconv/incubating/ServiceIncubatingAttributes$ServiceCriticalityIncubatingValues.class` | 0 | `bc24d96b6dfce6bca5d1132b665a55bece0589fc35e8203f39ca3a91b362a4d4` | 4 | 1 |
| `io/opentelemetry/semconv/incubating/ServiceIncubatingAttributes.class` | 0 | `b6696601fba88cd8ba723d296d88f52799aec749ef1485431a30f0befcc7ecad` | 7 | 2 |
| `io/opentelemetry/semconv/incubating/SessionIncubatingAttributes.class` | 0 | `97f2ddb6097212aadb998821eff717a1da533650e0d554041ec2d3f2b944b7f8` | 2 | 2 |
| `io/opentelemetry/semconv/incubating/SourceIncubatingAttributes.class` | 0 | `df99029cb820044a1e6f1d35ae730a946f5fb2cc6737a8e8df64074633692f13` | 2 | 2 |
| `io/opentelemetry/semconv/incubating/SystemIncubatingAttributes$SystemCpuStateIncubatingValues.class` | 0 | `ff09ffd188e2c6fe7f202e40b23d022c6fac7d7c881754a6b258a2a6d91fd28b` | 7 | 1 |
| `io/opentelemetry/semconv/incubating/SystemIncubatingAttributes$SystemFilesystemStateIncubatingValues.class` | 0 | `d7998935ea038a6df355bf7fb1b2e8da384611175f356a9abdc7a2d4b76c6fb8` | 3 | 1 |
| `io/opentelemetry/semconv/incubating/SystemIncubatingAttributes$SystemFilesystemTypeIncubatingValues.class` | 0 | `935c82b2fb2e13ab4e21a11e44258aa757782138634cc07787c0acb5556465f3` | 6 | 1 |
| `io/opentelemetry/semconv/incubating/SystemIncubatingAttributes$SystemMemoryLinuxSlabStateIncubatingValues.class` | 0 | `e995be2736ce4694867d0c7b0351f029aff9b5408340448eae82bad45a3e2ece` | 2 | 1 |
| `io/opentelemetry/semconv/incubating/SystemIncubatingAttributes$SystemMemoryStateIncubatingValues.class` | 0 | `84829fd8a12d5b16c5b5ca3bf3b92909e7b92007843dfc4828309b257a0f5753` | 5 | 1 |
| `io/opentelemetry/semconv/incubating/SystemIncubatingAttributes$SystemNetworkStateIncubatingValues.class` | 0 | `b91eba7fa6822bae8c967191ccfea35b323a1714e2cf3e54583924331c1e93ca` | 12 | 1 |
| `io/opentelemetry/semconv/incubating/SystemIncubatingAttributes$SystemPagingDirectionIncubatingValues.class` | 0 | `66ad48acbdb5a402446ddad96e5ab7ed0b455635ec7dfa48c324f8222eb12faf` | 2 | 1 |
| `io/opentelemetry/semconv/incubating/SystemIncubatingAttributes$SystemPagingFaultTypeIncubatingValues.class` | 0 | `8d320455e4e6809ba9e114e48fdd1d21fb8bdd9871c00e63d1ce05c6e9868505` | 2 | 1 |
| `io/opentelemetry/semconv/incubating/SystemIncubatingAttributes$SystemPagingStateIncubatingValues.class` | 0 | `42c77ba5d3f9186662cb3a4a2cba6638446a08e80039137143b635f373e9c76e` | 2 | 1 |
| `io/opentelemetry/semconv/incubating/SystemIncubatingAttributes$SystemPagingTypeIncubatingValues.class` | 0 | `5fb58114be5a4463309b15905bf46056c11a2aeb73ec6ad7d04e0e5c307e1588` | 2 | 1 |
| `io/opentelemetry/semconv/incubating/SystemIncubatingAttributes$SystemProcessStatusIncubatingValues.class` | 0 | `21564765bdc22b6f774a846680eee1035bdf736254e6a05606a517fed6146680` | 4 | 1 |
| `io/opentelemetry/semconv/incubating/SystemIncubatingAttributes$SystemProcessesStatusIncubatingValues.class` | 0 | `ec13050bae2fd4359aa5c7f84211f380ef6eab557c41a910afbd4e285e55d84e` | 4 | 1 |
| `io/opentelemetry/semconv/incubating/SystemIncubatingAttributes.class` | 0 | `0cc35e046a2dd69e260d46b00680d9bb37a8f17e6f3b231ac29eb2dba7aa71c0` | 16 | 2 |
| `io/opentelemetry/semconv/incubating/TelemetryIncubatingAttributes$TelemetrySdkLanguageIncubatingValues.class` | 0 | `75be917780e23d2aa950cea9cab1edce00d97b4e327ef273095f3db940f499ee` | 12 | 1 |
| `io/opentelemetry/semconv/incubating/TelemetryIncubatingAttributes.class` | 0 | `d4b4c02be9a862c0290668c11d747a9112a36f4a089fe16f097b497602b87304` | 5 | 2 |
| `io/opentelemetry/semconv/incubating/TestIncubatingAttributes$TestCaseResultStatusIncubatingValues.class` | 0 | `30f6411e3406df067f061209f33fefbc255041e987a9fe0293f29632700095f3` | 2 | 1 |
| `io/opentelemetry/semconv/incubating/TestIncubatingAttributes$TestSuiteRunStatusIncubatingValues.class` | 0 | `a7952982879649d46375ea7387d9be06aab5802ac04463cafdafd312b4f6089c` | 6 | 1 |
| `io/opentelemetry/semconv/incubating/TestIncubatingAttributes.class` | 0 | `01b27ddf7c68b08f15c4435b4ddc3b600c5eeb0547f49bbd7e9006a034129448` | 4 | 2 |
| `io/opentelemetry/semconv/incubating/ThreadIncubatingAttributes.class` | 0 | `da60e5d78201b932c6446a4f48c33c856fac0d36ce0fbc63b1dfdc96ec49942c` | 2 | 2 |
| `io/opentelemetry/semconv/incubating/TlsIncubatingAttributes$TlsProtocolNameIncubatingValues.class` | 0 | `af1a18ba8e4284140e82085289033f019347559c7c5f3e7a62c7a692bebce851` | 2 | 1 |
| `io/opentelemetry/semconv/incubating/TlsIncubatingAttributes.class` | 0 | `b1da450fd56d18038b67e1bd9c04c26e172aa1e15c541bc2d2878e3c20764bef` | 29 | 2 |
| `io/opentelemetry/semconv/incubating/UrlIncubatingAttributes.class` | 0 | `2cd7f08e601d6a55e959314300a4120cad271ba0f143b4a0f1ebc72dc8635fb4` | 13 | 2 |
| `io/opentelemetry/semconv/incubating/UserAgentIncubatingAttributes$UserAgentSyntheticTypeIncubatingValues.class` | 0 | `646fc7c628731540a492b8292069831fd4550feeff2cb93bdc42ddeaef10cfd5` | 2 | 1 |
| `io/opentelemetry/semconv/incubating/UserAgentIncubatingAttributes.class` | 0 | `605f4b1472e71cdc2fb1d012b5f303998a07a9585872bf1de5388c32cf23ba09` | 6 | 2 |
| `io/opentelemetry/semconv/incubating/UserIncubatingAttributes.class` | 0 | `1e47156fc71466fda6541f3a51f83ee5cb59b7a72210b36383a8d450381a92c8` | 6 | 2 |
| `io/opentelemetry/semconv/incubating/V8jsIncubatingAttributes$V8jsGcTypeIncubatingValues.class` | 0 | `d60880821665a21a98f002fcec5a84d444da3077c8f5aaf96d59417b826a2184` | 4 | 1 |
| `io/opentelemetry/semconv/incubating/V8jsIncubatingAttributes$V8jsHeapSpaceNameIncubatingValues.class` | 0 | `dd628658b8ed0e50047e8fd848f7ba9888e2a238efefc8719f815516b5f9bb9c` | 5 | 1 |
| `io/opentelemetry/semconv/incubating/V8jsIncubatingAttributes.class` | 0 | `efd3ecde466f1248991704d4cf03836dcd6e9a34df7c5c2723f4e820c3f92077` | 2 | 2 |
| `io/opentelemetry/semconv/incubating/VcsIncubatingAttributes$VcsChangeStateIncubatingValues.class` | 0 | `2ff099c4194f1895bdc4d6ac3770221981d16742d9c94266eb6db483aece7ce1` | 4 | 1 |
| `io/opentelemetry/semconv/incubating/VcsIncubatingAttributes$VcsLineChangeTypeIncubatingValues.class` | 0 | `e39338fc1f1a4d2de95123610e8c37f6f150a83792ce56733f958bbb0da40000` | 2 | 1 |
| `io/opentelemetry/semconv/incubating/VcsIncubatingAttributes$VcsProviderNameIncubatingValues.class` | 0 | `9033b711b9d5e40103b0687570f8b2d6a8d8f305f9a345923f43b91f749c4741` | 5 | 1 |
| `io/opentelemetry/semconv/incubating/VcsIncubatingAttributes$VcsRefBaseTypeIncubatingValues.class` | 0 | `c401e3ebcb2a8a67b2481e00677ad09c1dd90aff4885870c0003b26debdf7201` | 2 | 1 |
| `io/opentelemetry/semconv/incubating/VcsIncubatingAttributes$VcsRefHeadTypeIncubatingValues.class` | 0 | `3850aaecc9bd5b99975279b6abdedc6a60e6bfb3c4ca2d0b28c3644db6693d7e` | 2 | 1 |
| `io/opentelemetry/semconv/incubating/VcsIncubatingAttributes$VcsRefTypeIncubatingValues.class` | 0 | `3fbc17f7696a316c41b5229cb01ee54ff396e0ec6adafc0dc62cad8f1a3621e9` | 2 | 1 |
| `io/opentelemetry/semconv/incubating/VcsIncubatingAttributes$VcsRepositoryRefTypeIncubatingValues.class` | 0 | `70b15154d81f92b0713126e5a5ef4c27c53059cb3ef45e855407082a3f59f446` | 2 | 1 |
| `io/opentelemetry/semconv/incubating/VcsIncubatingAttributes$VcsRevisionDeltaDirectionIncubatingValues.class` | 0 | `5e59b8a14f21e366d60011c46b150bb227b93a100dbe66c80cf2444bb3dc6812` | 2 | 1 |
| `io/opentelemetry/semconv/incubating/VcsIncubatingAttributes.class` | 0 | `5a23a7bc3d99143739d414fb4ce5fbf69376abe0b8909f3063cfb4c03e6b98d0` | 21 | 2 |
| `io/opentelemetry/semconv/incubating/WebengineIncubatingAttributes.class` | 0 | `beceba9fd2a73c68ee1a9290e0a19a3896650390af5e85380957fcac2d396b36` | 3 | 2 |
| `io/opentelemetry/semconv/incubating/ZosIncubatingAttributes.class` | 0 | `9e924bf915f4c6eaebda3a605396a0a31bdfb2969ce5d86a6c890bec9d766a6d` | 2 | 2 |
