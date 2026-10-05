"""
gru_model.py

PyTorch implementation of the GRU (Gated Recurrent Unit) workload predictor.
Comparable recurrent architecture alternative to LSTM.
"""

import time
import copy
from typing import Dict, Any, Tuple, Optional
import numpy as np
import torch
import torch.nn as nn
from torch.utils.data import TensorDataset, DataLoader


class GRUWorkloadPredictor(nn.Module):
    def __init__(
        self,
        input_dim: int = 1,
        hidden_dim: int = 64,
        num_layers: int = 1,
        dropout: float = 0.2,
    ):
        super().__init__()
        self.hidden_dim = hidden_dim
        self.num_layers = num_layers

        # GRU layer
        self.gru = nn.GRU(
            input_size=input_dim,
            hidden_size=hidden_dim,
            num_layers=num_layers,
            batch_first=True,
            dropout=dropout if num_layers > 1 else 0.0,
        )
        self.dropout = nn.Dropout(dropout)
        self.fc = nn.Linear(hidden_dim, 1)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        # x shape: (batch_size, seq_len, input_dim)
        gru_out, _ = self.gru(x)
        # Take the output at the last time step
        last_step_out = self.dropout(gru_out[:, -1, :])
        out = self.fc(last_step_out)
        return out.squeeze(-1)


def train_gru(
    X_train: np.ndarray,
    y_train: np.ndarray,
    X_val: np.ndarray,
    y_val: np.ndarray,
    hidden_dim: int = 64,
    dropout: float = 0.2,
    epochs: int = 100,
    batch_size: int = 64,
    lr: float = 0.001,
    patience: int = 15,
    device: Optional[torch.device] = None,
) -> Tuple[GRUWorkloadPredictor, Dict[str, Any]]:
    """
    Train the GRU model with early stopping on validation loss.

    Returns:
        best_model: Model loaded with the best validation state.
        history: Dictionary containing training and validation losses, best epoch, and training time.
    """
    if device is None:
        device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

    # Reshape (N, lookback) -> (N, lookback, 1)
    X_tr_t = torch.tensor(X_train[..., np.newaxis], dtype=torch.float32)
    y_tr_t = torch.tensor(y_train, dtype=torch.float32)
    X_val_t = torch.tensor(X_val[..., np.newaxis], dtype=torch.float32).to(device)
    y_val_t = torch.tensor(y_val, dtype=torch.float32).to(device)

    train_dataset = TensorDataset(X_tr_t, y_tr_t)
    train_loader = DataLoader(train_dataset, batch_size=batch_size, shuffle=False)

    model = GRUWorkloadPredictor(
        input_dim=1,
        hidden_dim=hidden_dim,
        num_layers=1,
        dropout=dropout,
    ).to(device)

    criterion = nn.MSELoss()
    optimizer = torch.optim.Adam(model.parameters(), lr=lr)

    best_val_loss = float("inf")
    best_weights = None
    best_epoch = 0
    patience_counter = 0

    train_losses = []
    val_losses = []

    start_time = time.perf_counter()

    for epoch in range(1, epochs + 1):
        model.train()
        running_train_loss = 0.0
        for batch_X, batch_y in train_loader:
            batch_X, batch_y = batch_X.to(device), batch_y.to(device)
            optimizer.zero_grad()
            preds = model(batch_X)
            loss = criterion(preds, batch_y)
            loss.backward()
            optimizer.step()
            running_train_loss += loss.item() * len(batch_y)

        epoch_train_loss = running_train_loss / len(train_dataset)
        train_losses.append(epoch_train_loss)

        # Validation phase
        model.eval()
        with torch.no_grad():
            val_preds = model(X_val_t)
            epoch_val_loss = criterion(val_preds, y_val_t).item()
            val_losses.append(epoch_val_loss)

        if epoch_val_loss < best_val_loss:
            best_val_loss = epoch_val_loss
            best_epoch = epoch
            best_weights = copy.deepcopy(model.state_dict())
            patience_counter = 0
        else:
            patience_counter += 1

        if patience_counter >= patience:
            break

    total_train_time = time.perf_counter() - start_time

    # Restore best weights
    if best_weights is not None:
        model.load_state_dict(best_weights)

    history = {
        "train_losses": train_losses,
        "val_losses": val_losses,
        "best_epoch": best_epoch,
        "best_val_loss": best_val_loss,
        "total_epochs": len(train_losses),
        "train_time_sec": total_train_time,
    }

    return model, history


def predict_gru(
    model: GRUWorkloadPredictor,
    X: np.ndarray,
    device: Optional[torch.device] = None,
) -> np.ndarray:
    """Generate predictions from GRU model."""
    if device is None:
        device = next(model.parameters()).device

    model.eval()
    X_t = torch.tensor(X[..., np.newaxis], dtype=torch.float32).to(device)
    with torch.no_grad():
        preds = model(X_t).cpu().numpy()
    return preds.flatten()
