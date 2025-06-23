import os
import pickle
import time
import paho.mqtt.client as mqtt
import torch
from server import FederatedNet  # seu código existente
from logger_utils import setup_logger

NUM_CLIENTS = 2
RECEIVED = {}

logger = setup_logger("server", "logs/server.log")

def fed_avg(param_list):
    avg_params = {}
    for name in param_list[0]:
        avg_params[name] = {
            'weight': sum(p[name]['weight'] for p in param_list) / len(param_list),
            'bias': sum(p[name]['bias'] for p in param_list) / len(param_list),
        }
    return avg_params

def on_message(client, userdata, msg):
    client_id = int(msg.topic.split("/")[2])
    data = pickle.loads(msg.payload)
    RECEIVED[client_id] = data
    logger.info(f"📥 Recebido de cliente {client_id}: {len(msg.payload)} bytes.")

    if len(RECEIVED) == NUM_CLIENTS:
        logger.info("🧮 Iniciando agregação FedAvg...")
        start_time = time.time()
        aggregated = fed_avg(list(RECEIVED.values()))
        duration = time.time() - start_time
        logger.info(f"✅ Agregação concluída em {duration:.2f} segundos.")
        payload = pickle.dumps(aggregated)
        client.publish("fed/global/params", payload)
        logger.info(f"📤 Modelo global publicado: {len(payload)} bytes.")
        RECEIVED.clear()

client = mqtt.Client()
client.on_message = on_message
client.connect("localhost", 1883, 60)

for cid in range(NUM_CLIENTS):
    client.subscribe(f"fed/client/{cid}/params")

logger.info("🚀 Servidor iniciado e aguardando atualizações dos clientes...")
client.loop_forever()
