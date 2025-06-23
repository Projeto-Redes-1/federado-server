#!/bin/bash

echo "🚀 Iniciando servidor federado..."

# Inicia o broker se não estiver rodando
if ! pgrep -x "mosquitto" > /dev/null; then
    echo "📡 Iniciando Mosquitto..."
    sudo systemctl start mosquitto
else
    echo "✅ Mosquitto já está rodando."
fi

# Ativa ambiente virtual se desejar (opcional)

# Roda o servidor MQTT (agregador)
echo "🧠 Iniciando script do servidor..."
python3 src/server_mqtt.py
