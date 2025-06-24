import os
import pickle
import time
from datetime import datetime
import paho.mqtt.client as mqtt
import torch
from server import FederatedNet  # Seu modelo
from logger_utils import setup_logger

NUM_CLIENTS = 2  # Número total de clientes que devem enviar parâmetros
RECEIVED = {}   # Dicionário para armazenar parâmetros recebidos dos clientes
MODEL_PATH = "global_parameters.pkl"  # Arquivo onde o modelo global é salvo
BROKER = "localhost"  # IP do broker MQTT
PORT = 1883  # Porta padrão MQTT

# Configura logger para o servidor
logger = setup_logger("server", "logs/server.log")

def fed_avg(param_list):
    """
    Faz a média dos parâmetros dos modelos recebidos dos clientes.
    param_list: lista de dicionários, cada um com parâmetros de um cliente.
    Retorna o dicionário com parâmetros médios.
    """
    avg_params = {}
    for name in param_list[0]:
        avg_params[name] = {
            'weight': sum(p[name]['weight'] for p in param_list) / len(param_list),
            'bias': sum(p[name]['bias'] for p in param_list) / len(param_list),
        }
    return avg_params

def create_initial_model():
    """
    Cria um modelo inicial com pesos padrão e salva em disco.
    Retorna os parâmetros formatados para o formato federado.
    """
    logger.info("1. Criando modelo global inicial (default)...")
    print("[INFO] 1. Criando modelo global inicial (default)...")

    model = FederatedNet()  # Instancia o modelo
    state_dict = model.state_dict()  # Pega o dicionário dos pesos

    # Converte o state_dict em formato {layer: {'weight': tensor, 'bias': tensor}}
    parameters = {}
    for name in state_dict:
        if 'weight' in name:
            base = name.replace('.weight', '')
            if base not in parameters:
                parameters[base] = {}
            parameters[base]['weight'] = state_dict[name]
        elif 'bias' in name:
            base = name.replace('.bias', '')
            if base not in parameters:
                parameters[base] = {}
            parameters[base]['bias'] = state_dict[name]

    # Salva os parâmetros no arquivo do modelo global
    with open(MODEL_PATH, "wb") as f:
        pickle.dump(parameters, f)
    logger.info("2. Modelo inicial salvo como 'global_parameters.pkl'")
    print("[INFO] 2. Modelo inicial salvo como 'global_parameters.pkl'")

    return parameters

def on_message(client, userdata, msg):
    """
    Callback chamado quando uma mensagem MQTT é recebida.
    Processa os parâmetros enviados por um cliente.
    """
    try:
        start_recv = time.time()  # Marca início do recebimento

        # Extrai o ID do cliente a partir do tópico, ex: fed/client/0/params -> 0
        client_id = int(msg.topic.split("/")[2])

        # Desserializa os parâmetros enviados (pickle)
        data = pickle.loads(msg.payload)

        duration_recv = time.time() - start_recv  # Tempo gasto recebendo e desserializando

        # Armazena os parâmetros recebidos no dicionário global
        RECEIVED[client_id] = data

        logger.info(f"3. [{datetime.now()}] Cliente {client_id} enviou {len(msg.payload)} bytes em {duration_recv:.2f}s.")
        print(f"[INFO] 3. [{datetime.now()}] Cliente {client_id} enviou {len(msg.payload)} bytes em {duration_recv:.2f}s.")

        # Quando todos os clientes enviaram seus parâmetros
        if len(RECEIVED) == NUM_CLIENTS:
            logger.info("4. Todos os clientes enviaram. Iniciando FedAvg...")
            print("[INFO] 4. Todos os clientes enviaram. Iniciando FedAvg...")

            start_agg = time.time()  # Marca início da agregação
            aggregated = fed_avg(list(RECEIVED.values()))  # Calcula média dos parâmetros
            duration_agg = time.time() - start_agg

            # Salva o novo modelo agregado no disco
            with open(MODEL_PATH, "wb") as f:
                pickle.dump(aggregated, f)
            logger.info("5. Novo modelo global salvo.")
            print("[INFO] 5. Novo modelo global salvo.")

            # Serializa para publicar no tópico global
            payload = pickle.dumps(aggregated)
            client.publish("fed/global/params", payload)
            logger.info(f"6. Modelo global atualizado publicado ({len(payload)} bytes).")
            print(f"[INFO] 6. Modelo global atualizado publicado ({len(payload)} bytes).")

            # Limpa os parâmetros recebidos para próxima rodada
            RECEIVED.clear()
    except Exception as e:
        logger.error(f"7. Erro no processamento da mensagem: {e}")
        print(f"[ERROR] 7. Erro no processamento da mensagem: {e}")

# Configuração do cliente MQTT do servidor
client = mqtt.Client()
client.on_message = on_message

print(f"[INFO] Conectando ao broker MQTT em {BROKER}:{PORT}...")
client.connect(BROKER, PORT, 60)
logger.info(f"Conectado ao broker MQTT em {BROKER}:{PORT}")
print("[INFO] Conectado ao broker MQTT.")

# Se inscreve nos tópicos para receber parâmetros de cada cliente
for cid in range(NUM_CLIENTS):
    topic = f"fed/client/{cid}/params"
    client.subscribe(topic)
    logger.info(f"8. Subscrito em {topic}")
    print(f"[INFO] 8. Subscrito em {topic}")

# Se o modelo global inicial não existir, cria ele
if not os.path.exists(MODEL_PATH):
    initial_params = create_initial_model()
else:
    with open(MODEL_PATH, "rb") as f:
        initial_params = pickle.load(f)
    logger.info("9. Modelo global existente carregado.")
    print("[INFO] 9. Modelo global existente carregado.")

# Publica o modelo global inicial para os clientes começarem
payload = pickle.dumps(initial_params)
client.publish("fed/global/params", payload)
logger.info(f"10. Modelo global inicial publicado ({len(payload)} bytes).")
print(f"[INFO] 10. Modelo global inicial publicado ({len(payload)} bytes).")

logger.info(f"11. Servidor pronto às {datetime.now()}, aguardando atualizações...")
print(f"[INFO] 11. Servidor pronto às {datetime.now()}, aguardando atualizações...")

# Inicia loop infinito para processar mensagens MQTT conforme chegam
client.loop_forever()
