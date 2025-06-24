
import torch
import pickle
import os

class FederatedNet(torch.nn.Module):
    def __init__(self):
        super().__init__()
        self.conv1 = torch.nn.Conv2d(3, 20, 7)
        self.conv2 = torch.nn.Conv2d(20, 40, 7)
        self.maxpool = torch.nn.MaxPool2d(2, 2)
        self.flatten = torch.nn.Flatten()
        self.linear = torch.nn.Linear(2560, 10)
        self.non_linearity = torch.nn.functional.relu
        self.track_layers = {'conv1': self.conv1, 'conv2': self.conv2, 'linear': self.linear}

    def forward(self, x):
        x = self.non_linearity(self.conv1(x))
        x = self.non_linearity(self.conv2(x))
        x = self.maxpool(x)
        x = self.flatten(x)
        x = self.linear(x)
        return x

    def get_parameters(self):
        return {name: {'weight': layer.weight.data.clone(), 'bias': layer.bias.data.clone()} for name, layer in self.track_layers.items()}

    def apply_parameters(self, parameters):
        with torch.no_grad():
            for name in parameters:
                self.track_layers[name].weight.data.copy_(parameters[name]['weight'])
                self.track_layers[name].bias.data.copy_(parameters[name]['bias'])


if __name__ == "__main__":
    # Number of communication rounds and clients
    rounds = 30
    num_clients = 3

    # Initialize the global model and get its parameters
    global_net = FederatedNet()
    global_parameters = global_net.get_parameters()

    # Federated training loop
    for round_num in range(rounds):
        print(f"Starting round {round_num + 1}")

        # Create a parameter accumulator to aggregate client updates
        new_parameters = {name: {'weight': torch.zeros_like(param['weight']), 'bias': torch.zeros_like(param['bias'])} for name, param in global_parameters.items()}

        # Iterate over each client
        for client_id in range(num_clients):
            parameters_path = f"client_{client_id}_parameters.pkl"
            
            # Check if the client has provided its parameters
            if os.path.exists(parameters_path):
                with open(parameters_path, 'rb') as f:
                    client_parameters = pickle.load(f)

                # Accumulate parameters from the client
                for name in client_parameters:
                    new_parameters[name]['weight'] += client_parameters[name]['weight'] / num_clients
                    new_parameters[name]['bias'] += client_parameters[name]['bias'] / num_clients
            else:
                print(f"Warning: {parameters_path} not found. Skipping client {client_id}")

        # Update global model with averaged parameters
        global_net.apply_parameters(new_parameters)
        global_parameters = new_parameters

        print(f"Round {round_num + 1} completed")

    # Save the final global model parameters
    with open("global_parameters.pkl", 'wb') as f:
        pickle.dump(global_parameters, f)

    print("Global training completed. Parameters saved to global_parameters.pkl")

