#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
SRC_DIR="$ROOT_DIR/scada-v6-master/scada-v6-master"
RUNTIME_DIR="$ROOT_DIR/scada-config/runtime/Instances/Default"

# Ensure base app directories exist
mkdir -p "$RUNTIME_DIR/ScadaServer"
mkdir -p "$RUNTIME_DIR/ScadaServer/Config"
mkdir -p "$RUNTIME_DIR/ScadaServer/Lang"
mkdir -p "$RUNTIME_DIR/ScadaServer/Log"
mkdir -p "$RUNTIME_DIR/ScadaServer/Mod"

mkdir -p "$RUNTIME_DIR/ScadaComm"
mkdir -p "$RUNTIME_DIR/ScadaComm/Config"
mkdir -p "$RUNTIME_DIR/ScadaComm/Lang"
mkdir -p "$RUNTIME_DIR/ScadaComm/Log"
mkdir -p "$RUNTIME_DIR/ScadaComm/Drv"

echo "Copying ScadaServer binaries..."
cp -r "$SRC_DIR/ScadaServer/ScadaServer/ScadaServerApp/bin/Release/net10.0/"* "$RUNTIME_DIR/ScadaServer/"
cp -r "$SRC_DIR/ScadaServer/ScadaServer/ScadaServerWkr/bin/Release/net10.0/Lang/"* "$RUNTIME_DIR/ScadaServer/Lang/"
cp "$SRC_DIR/ScadaCommon/ScadaCommon/Lang/"*.xml "$RUNTIME_DIR/ScadaServer/Lang/"

echo "Copying ScadaComm binaries..."
cp -r "$SRC_DIR/ScadaComm/ScadaComm/ScadaCommApp/bin/Release/net10.0/"* "$RUNTIME_DIR/ScadaComm/"
cp -r "$SRC_DIR/ScadaComm/ScadaComm/ScadaCommWkr/bin/Release/net10.0/Lang/"* "$RUNTIME_DIR/ScadaComm/Lang/"
cp "$SRC_DIR/ScadaCommon/ScadaCommon/Lang/"*.xml "$RUNTIME_DIR/ScadaComm/Lang/"

echo "Copying FileStorage..."
cp "$SRC_DIR/ScadaCommon/FileStorage/bin/Release/net10.0/FileStorage.dll" "$RUNTIME_DIR/ScadaServer/"
cp "$SRC_DIR/ScadaCommon/FileStorage/bin/Release/net10.0/FileStorage.dll" "$RUNTIME_DIR/ScadaComm/"

echo "Copying Server modules..."
cp "$SRC_DIR/ScadaServer/OpenModules/ModArcBasic.Logic/bin/Release/netstandard2.0/ModArcBasic.Logic.dll" "$RUNTIME_DIR/ScadaServer/Mod/"
cp "$SRC_DIR/ScadaServer/OpenModules/ModArcPostgreSql.Logic/bin/Release/net8.0/ModArcPostgreSql.Logic.dll" "$RUNTIME_DIR/ScadaServer/Mod/"
cp "$SRC_DIR/ScadaServer/OpenModules/ModArcPostgreSql.Logic/bin/Release/net8.0/Npgsql.dll" "$RUNTIME_DIR/ScadaServer/Mod/"
cp "$SRC_DIR/ScadaServer/OpenModules/ModArcPostgreSql.Logic/bin/Release/net8.0/Microsoft.Extensions.Logging.Abstractions.dll" "$RUNTIME_DIR/ScadaServer/"
cp "$SRC_DIR/ScadaServer/OpenModules/ModArcPostgreSql.Logic/bin/Release/net8.0/Microsoft.Extensions.DependencyInjection.Abstractions.dll" "$RUNTIME_DIR/ScadaServer/"

echo "Copying Communicator drivers..."
cp "$SRC_DIR/ScadaComm/OpenDrivers/DrvDsScadaServer.Logic/bin/Release/netstandard2.0/DrvDsScadaServer.Logic.dll" "$RUNTIME_DIR/ScadaComm/Drv/"
cp "$SRC_DIR/ScadaComm/OpenDrivers/DrvOpcUa.Logic/bin/Release/net8.0/DrvOpcUa.Logic.dll" "$RUNTIME_DIR/ScadaComm/Drv/"
cp "$SRC_DIR/ScadaComm/OpenDrivers/DrvOpcUa.Logic/bin/Release/net8.0/DrvOpcUa.Common.dll" "$RUNTIME_DIR/ScadaComm/Drv/"
cp "$SRC_DIR/ScadaComm/OpenDrivers/DrvOpcUa.Logic/bin/Release/net8.0/Opc.Ua.Client.dll" "$RUNTIME_DIR/ScadaComm/Drv/"
cp "$SRC_DIR/ScadaComm/OpenDrivers/DrvOpcUa.Logic/bin/Release/net8.0/Opc.Ua.Configuration.dll" "$RUNTIME_DIR/ScadaComm/Drv/"
cp "$SRC_DIR/ScadaComm/OpenDrivers/DrvOpcUa.Logic/bin/Release/net8.0/Opc.Ua.Core.dll" "$RUNTIME_DIR/ScadaComm/Drv/"
cp "$SRC_DIR/ScadaComm/OpenDrivers/DrvOpcUa.Logic/bin/Release/net8.0/Opc.Ua.Security.Certificates.dll" "$RUNTIME_DIR/ScadaComm/Drv/"
cp "$SRC_DIR/ScadaComm/OpenDrivers/DrvOpcUa.Logic/bin/Release/net8.0/Newtonsoft.Json.dll" "$RUNTIME_DIR/ScadaComm/Drv/"
cp "$SRC_DIR/ScadaComm/OpenDrivers/DrvOpcUa.Logic/bin/Release/net8.0/Microsoft.Extensions.Logging.Abstractions.dll" "$RUNTIME_DIR/ScadaComm/"
cp "$SRC_DIR/ScadaComm/OpenDrivers/DrvOpcUa.Logic/bin/Release/net8.0/Microsoft.Extensions.DependencyInjection.Abstractions.dll" "$RUNTIME_DIR/ScadaComm/"

echo "Runtime binaries copied to $RUNTIME_DIR"
