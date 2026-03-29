import torch
import torch.nn as nn
import numpy as np
from sklearn.preprocessing import MinMaxScaler

class RoadDamageLSTM(nn.Module):
    def __init__(self, input_size=1, hidden_size=32, num_layers=2, output_size=1):
        super(RoadDamageLSTM, self).__init__()
        self.hidden_size = hidden_size
        self.num_layers = num_layers
        self.lstm = nn.LSTM(input_size, hidden_size, num_layers, batch_first=True)
        self.fc = nn.Linear(hidden_size, output_size)

    def forward(self, x):
        h0 = torch.zeros(self.num_layers, x.size(0), self.hidden_size)
        c0 = torch.zeros(self.num_layers, x.size(0), self.hidden_size)
        out, _ = self.lstm(x, (h0, c0))
        out = self.fc(out[:, -1, :])
        return out


def train_lstm_model(sequence):
    scaler = MinMaxScaler(feature_range=(0, 1))
    scaled = scaler.fit_transform(np.array(sequence).reshape(-1, 1))
    x = []
    y = []
    window = 5
    for i in range(len(scaled) - window):
        x.append(scaled[i:i+window])
        y.append(scaled[i+window])
    x = torch.tensor(np.array(x), dtype=torch.float32)
    y = torch.tensor(np.array(y), dtype=torch.float32)

    model = RoadDamageLSTM()
    criterion = nn.MSELoss()
    optimizer = torch.optim.Adam(model.parameters(), lr=0.001)

    for epoch in range(20):
        model.train()
        pred = model(x)
        loss = criterion(pred, y)
        optimizer.zero_grad()
        loss.backward()
        optimizer.step()

    return model, scaler


def predict_lstm(trained_model, scaler, sequence):
    model = trained_model
    model.eval()
    seq = np.array(sequence[-5:]).reshape(-1,1)
    seq_scaled = scaler.transform(seq)
    t = torch.tensor(seq_scaled.reshape(1, 5, 1), dtype=torch.float32)
    with torch.no_grad():
        pred_scaled = model(t).numpy()
    return float(scaler.inverse_transform(pred_scaled)[0][0])
