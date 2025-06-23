#!/bin/bash

echo "🛠️ Iniciando instalação para SERVIDOR..."

# Verifica Python
if ! command -v python3 &> /dev/null; then
    echo "❌ Python3 não encontrado. Por favor, instale antes de continuar."
    exit 1
else
    echo "✅ Python3 OK."
fi

# Verifica pip
if ! command -v pip3 &> /dev/null; then
    echo "❌ pip3 não encontrado. Instalando..."
    sudo apt update
    sudo apt install -y python3-pip
fi

# Instala dependências do servidor
echo "📦 Instalando pacotes Python para servidor..."
pip3 install --upgrade pip
pip3 install torch torchvision paho-mqtt --quiet

# Cria pasta de logs
mkdir -p src/logs
echo "📁 Pasta de logs criada em src/logs"

# Instala Mosquitto (broker MQTT)
echo "📡 Verificando Mosquitto..."
if ! command -v mosquitto &> /dev/null; then
    echo "🔄 Instalando Mosquitto..."
    sudo apt update
    sudo apt install -y mosquitto mosquitto-clients
    sudo systemctl enable mosquitto
    sudo systemctl start mosquitto
else
    echo "✅ Mosquitto já está instalado."
fi

echo "✅ Instalação para SERVIDOR concluída!"
