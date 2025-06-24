import torch
import pickle
import os

# Define o modelo de rede neural usado em aprendizado federado
class FederatedNet(torch.nn.Module):
    def __init__(self):
        super().__init__()  # Inicializa o módulo base do PyTorch

        # Primeira camada convolucional: 3 canais de entrada (RGB), 20 filtros, kernel 7x7
        self.conv1 = torch.nn.Conv2d(3, 20, 7)

        # Segunda camada convolucional: 20 canais de entrada, 40 filtros, kernel 7x7
        self.conv2 = torch.nn.Conv2d(20, 40, 7)

        # Camada de max pooling: reduz as dimensões pela metade
        self.maxpool = torch.nn.MaxPool2d(2, 2)

        # Camada para achatar (flatten) os tensores para vetor 1D
        self.flatten = torch.nn.Flatten()

        # Camada totalmente conectada (linear): entrada 2560, saída 10 classes
        #self.linear = torch.nn.Linear(2560, 10)
        self.linear = torch.nn.Linear(4000, 10) # aceiando 4k

        # Função de ativação usada após cada camada convolucional
        self.non_linearity = torch.nn.functional.relu

        # Dicionário que guarda as camadas que serão acompanhadas (para pegar e aplicar os parâmetros)
        self.track_layers = {'conv1': self.conv1, 'conv2': self.conv2, 'linear': self.linear}

    # Define a passagem do dado pelo modelo
    def forward(self, x):
        x = self.non_linearity(self.conv1(x))  # Ativação após conv1
        x = self.non_linearity(self.conv2(x))  # Ativação após conv2
        x = self.maxpool(x)                    # Redução de dimensão
        x = self.flatten(x)                    # Achatar para o linear
        x = self.linear(x)                     # Classificação final
        return x

    # Função para obter os pesos e bias das camadas rastreadas
    def get_parameters(self):
        return {
            name: {
                'weight': layer.weight.data.clone(),  # Clona pesos
                'bias': layer.bias.data.clone()       # Clona bias
            } for name, layer in self.track_layers.items()
        }

    # Aplica novos parâmetros ao modelo
    def apply_parameters(self, parameters):
        with torch.no_grad():  # Desativa o autograd para não registrar essas operações
            for name in parameters:
                self.track_layers[name].weight.data.copy_(parameters[name]['weight'])  # Copia os pesos
                self.track_layers[name].bias.data.copy_(parameters[name]['bias'])      # Copia os bias


if __name__ == "__main__":
    print("🚀 Iniciando Servidor Federado...")
    
    # Número de rodadas e de clientes participantes
    rounds = 30
    num_clients = 3

    # Cria o modelo global inicial e obtém seus parâmetros
    global_net = FederatedNet()
    global_parameters = global_net.get_parameters()
    print("✅ Modelo global inicializado e parâmetros carregados.")

    # Loop de treinamento federado
    for round_num in range(rounds):
        print(f"\n🔁 Iniciando rodada {round_num + 1}")

        # Inicializa estrutura para acumular os novos parâmetros de todos os clientes
        new_parameters = {
            name: {
                'weight': torch.zeros_like(param['weight']),  # Zera os pesos
                'bias': torch.zeros_like(param['bias'])       # Zera os bias
            } for name, param in global_parameters.items()
        }

        # Para cada cliente, tenta carregar seus parâmetros salvos
        for client_id in range(num_clients):
            parameters_path = f"client_{client_id}_parameters.pkl"

            # Verifica se os parâmetros do cliente existem
            if os.path.exists(parameters_path):
                print(f"📥 Lendo parâmetros do cliente {client_id}...")

                with open(parameters_path, 'rb') as f:
                    client_parameters = pickle.load(f)

                # Soma os parâmetros, dividindo por número de clientes para fazer média (FedAvg)
                for name in client_parameters:
                    new_parameters[name]['weight'] += client_parameters[name]['weight'] / num_clients
                    new_parameters[name]['bias'] += client_parameters[name]['bias'] / num_clients

            else:
                print(f"⚠️ Aviso: {parameters_path} não encontrado. Ignorando cliente {client_id}")

        # Aplica a média dos parâmetros ao modelo global
        global_net.apply_parameters(new_parameters)
        global_parameters = new_parameters  # Atualiza o conjunto de parâmetros globais

        print(f"✅ Rodada {round_num + 1} finalizada.")

    # Ao fim de todas as rodadas, salva os parâmetros finais do modelo global
    with open("global_parameters.pkl", 'wb') as f:
        pickle.dump(global_parameters, f)

    print("\n🎉 Treinamento federado concluído!")
    print("📦 Parâmetros finais salvos em global_parameters.pkl")
