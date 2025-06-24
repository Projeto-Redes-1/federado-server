#!/bin/bash
echo "🛠️ Instalando dependências do SERVIDOR..."

# Verifica Python 3
if ! command -v python3 >/dev/null; then
    echo "❌ Python3 não encontrado."
    exit 1
else
    echo "✅ Python3 encontrado: $(python3 --version)"
fi

# Verifica pip
if ! command -v pip3 >/dev/null; then
    echo "❌ pip3 não encontrado. Instalando..."
    sudo apt update && sudo apt install -y python3-pip python3-venv
fi

# Instala python3.11-venv para garantir criação do ambiente virtual (caso precise)
if ! dpkg -s python3.11-venv >/dev/null 2>&1; then
    echo "📦 Instalando python3.11-venv..."
    sudo apt update
    sudo apt install -y python3.11-venv
else
    echo "✅ python3.11-venv já instalado."
fi

# Cria ambiente virtual se não existir
if [ ! -d "venv" ]; then
    echo "🛠️ Criando ambiente virtual..."
    python3 -m venv venv
else
    echo "✅ Ambiente virtual já existe."
fi

# Ativa ambiente virtual
source venv/bin/activate

# Atualiza pip e instala pacotes Python no ambiente virtual
echo "📦 Instalando pacotes Python no ambiente virtual..."
pip install --upgrade pip
#pip install torch torchvision paho-mqtt
pip3 install torch --break-system-packages
pip3 install torchvision --break-system-packages
pip3 install paho-mqtt --break-system-packages

# Instala Mosquitto (broker MQTT)
if ! command -v mosquitto >/dev/null; then
    echo "📡 Instalando Mosquitto..."
    sudo apt install -y mosquitto mosquitto-clients
    sudo systemctl enable mosquitto
    sudo systemctl start mosquitto
else
    echo "✅ Mosquitto já está instalado."
fi

# Cria pasta de logs (na raiz do fed-server)
mkdir -p logs
echo "📁 Pasta 'logs/' criada."

echo "✅ SERVIDOR pronto para uso."
