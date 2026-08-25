# Build reproduzível do FORTE MPC V2

## Objetivo

Este documento registra a receita validada para compilar o FORTE utilizado com
`MPC_MOVE_BLOCKED_NMPC_V2`.

A configuração foi validada em 15/08/2026 e produziu:

```text
FORTE SHA256
49BB157D27BD0545AC96E50305529C255791BBF5257A14A2563D0FB5F6F13173

open62541.dll SHA256
452DD9B74FFBFCD08AE1A268D6DE58B552F8CB9D111972265CDFD8989C4F4318
```

O build é local. Ele não inicia o FORTE, não acessa PLC/gateway e não realiza
deploy ou atuação física.

## Componentes

### Código-fonte do FORTE

```text
C:\Users\guilh\4diac\4diac-forte
```

Commit observado no build validado:

```text
7c8b6296227fa292c13d71d2958a404c6db03e53
```

O working tree local do FORTE possuía um overlay/modificação já utilizado pelo
workflow V1. Portanto, o commit sozinho não descreve integralmente aquele
estado local; a árvore usada no build deve ser preservada.

### open62541

```text
include/build root:
C:\Users\guilh\4diac\open62541\build

DLL:
C:\Users\guilh\4diac\open62541\build\bin\Debug\open62541.dll
```

### Módulo externo MPC V2

```text
C:\Projetos\forte-external-modules-mpc-v2-build\MPC_V2
```

Conteúdo esperado:

```text
CMakeLists.txt
MPC_MEDIAN_FILTER_9.cpp
MPC_MEDIAN_FILTER_9.h
MPC_MOVE_BLOCKED_NMPC_V2.cpp
MPC_MOVE_BLOCKED_NMPC_V2.h
SAFE_DAC_RATE_LIMITER.cpp
SAFE_DAC_RATE_LIMITER.h
```

O `CMakeLists.txt` usa o mesmo padrão genérico validado no V1:

```cmake
forte_add_directory_module()
forte_add_all_sourcefiles()
```

### Controller V2 exportado do 4diac

Hashes validados:

```text
MPC_MOVE_BLOCKED_NMPC_V2.cpp
77E1CE99CB7AB3A24C57EFCBBF02C5A1CF0F9C6CBCF0B1724918357B4E0764E1

MPC_MOVE_BLOCKED_NMPC_V2.h
D2E6573E8AF6414EA01CED947BE8310BFC6047E16B27E1B961BEA4D17A73A394
```

Os auxiliares `MPC_MEDIAN_FILTER_9` e `SAFE_DAC_RATE_LIMITER` são cópias
bit-a-bit dos auxiliares já validados no runtime MPC V1.

## Configuração CMake validada

Generator:

```text
Visual Studio 18 2026
x64
```

Arquitetura:

```text
FORTE_ARCHITECTURE=Win32
```

Build:

```text
FORTE_BUILD_EXECUTABLE=ON
FORTE_BUILD_SHARED_LIBRARY=ON
FORTE_BUILD_STATIC_LIBRARY=OFF
```

Comunicação:

```text
FORTE_COM_ETH=ON
FORTE_COM_FBDK=ON
FORTE_COM_LOCAL=ON
FORTE_COM_RAW=ON

FORTE_COM_OPC_UA=ON
FORTE_COM_OPC_UA_ENCRYPTION=OFF
FORTE_COM_OPC_UA_INCLUDE_DIR=C:/Users/guilh/4diac/open62541/build
FORTE_COM_OPC_UA_LIB=open62541.dll
FORTE_COM_OPC_UA_LIB_DIR=C:/Users/guilh/4diac/open62541/build/bin/Debug
FORTE_COM_OPC_UA_MULTICAST=OFF
FORTE_COM_OPC_UA_CLIENT_PUB_INTERVAL=100.0
FORTE_COM_OPC_UA_SERVER_PUB_INTERVAL=100.0
```

Módulos:

```text
FORTE_MODULE_EXTERNAL_MPC_V2=ON
FORTE_MODULE_CONVERT=ON
FORTE_MODULE_IEC61131=ON
FORTE_MODULE_UTILS=ON
```

Suporte:

```text
FORTE_SUPPORT_ARRAYS=ON
FORTE_SUPPORT_BOOT_FILE=ON
FORTE_SUPPORT_CUSTOM_SERIALIZABLE_DATATYPES=ON
FORTE_SUPPORT_MONITORING=ON
FORTE_SUPPORT_QUERY_CMD=ON

FORTE_USE_64BIT_DATATYPES=ON
FORTE_USE_REAL_DATATYPE=ON
FORTE_USE_WSTRING_DATATYPE=ON
```

## Por que os quatro módulos de comunicação são importantes

Uma tentativa anterior habilitou OPC UA e os módulos IEC necessários, mas
omitiu:

```text
FORTE_COM_ETH
FORTE_COM_FBDK
FORTE_COM_LOCAL
FORTE_COM_RAW
```

Os três FBs customizados chegaram a compilar, porém o link de `forte.exe`
falhou com símbolos não resolvidos de:

```text
CWin32SocketInterface
CFDSelectHandler
```

Ao reproduzir o conjunto completo de comunicação já validado no build MPC V1,
foram gerados `win32socketinterf.cpp` e `fdselecthand.cpp` e o link passou.

## Build manual

A forma recomendada é usar:

```powershell
cd C:\Projetos\master-thesis-level-control

powershell.exe `
    -NoProfile `
    -ExecutionPolicy Bypass `
    -File ".\scripts\build_forte_mpc_v2.ps1" `
    -Clean
```

O script:

1. valida o módulo externo e os hashes do controller;
2. valida o `open62541.dll`;
3. exige que nenhum FORTE esteja em execução;
4. opcionalmente remove somente `build-mpc-v2`;
5. configura com a receita acima;
6. compila em Debug;
7. verifica os três FBs customizados;
8. verifica `forte.exe`;
9. copia `forte.exe` e `open62541.dll` para o runtime de validação;
10. não inicia o runtime.

## Saídas

Build:

```text
C:\Users\guilh\4diac\4diac-forte\build-mpc-v2
```

Executável:

```text
C:\Users\guilh\4diac\4diac-forte\build-mpc-v2\src\Debug\forte.exe
```

Runtime externo de validação:

```text
C:\Projetos\forte-mpc-v2-validation
```

Runtime preservado no repositório:

```text
forte/preserved-v2/runtimes/mpc-v2
```

## Critérios de sucesso

```text
CMAKE CONFIGURE: PASSED
FORTE MPC V2 LINK/BUILD: PASSED

MPC_MEDIAN_FILTER_9 COMPILED: YES
MPC_MOVE_BLOCKED_NMPC_V2 COMPILED: YES
SAFE_DAC_RATE_LIMITER COMPILED: YES

FORTE V2 STARTED: NO
PLC/GATEWAY ACCESSED: NO
DEPLOYMENT PERFORMED: NO
```

## Limite de autorização

Um build bem-sucedido prova disponibilidade de compilação/link, não valida
controle real.

```text
REAL MPC FULL OPERATION AUTHORIZED: NO
```

Antes de qualquer retorno à planta, o runtime deve passar pelo smoke test
offline de disponibilidade dos tipos e depois pelo procedimento protegido de
zero output.
