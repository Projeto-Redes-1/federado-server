#!/bin/bash
echo "🚀 Iniciando servidor federado..."

# Ativa ambiente virtual
source venv/bin/activate

# Inicia o Mosquitto se não estiver rodando
if ! pgrep -x "mosquitto" > /dev/null; then
    echo "📡 Iniciando Mosquitto..."
    sudo systemctl start mosquitto
else
    echo "✅ Mosquitto já está rodando."
fi

# Inicia o script de agregação no ambiente virtual
echo "🧠 Iniciando script do servidor MQTT..."
python3 server_mqtt.py
