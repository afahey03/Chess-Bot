import torch
import torch.optim as optim
import torch.nn as nn
from model import ChessNet
from data_processor import parse_database

# --- Hyperparameters ---
LEARNING_RATE = 0.001
BATCH_SIZE = 256
EPOCHS = 10
DATABASE_PATH = "database.pgn.zst"
MAX_GAMES_TO_PROCESS = 50000
MODEL_SAVE_PATH = "chess_net.pth"

def train():
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print(f"Using device: {device}")

    model = ChessNet().to(device)
    optimizer = optim.Adam(model.parameters(), lr=LEARNING_RATE)
    criterion = nn.MSELoss()

    print("Starting training...")
    for epoch in range(EPOCHS):
        running_loss = 0.0
        position_count = 0
        
        data_generator = parse_database(DATABASE_PATH, max_games=MAX_GAMES_TO_PROCESS)
        
        batch_tensors = []
        batch_labels = []

        for tensor, label in data_generator:
            batch_tensors.append(tensor)
            batch_labels.append(label)
            
            if len(batch_tensors) >= BATCH_SIZE:
                tensors = torch.stack(batch_tensors).to(device)
                labels = torch.tensor(batch_labels, dtype=torch.float32).unsqueeze(1).to(device)
                
                optimizer.zero_grad()
                
                outputs = model(tensors)
                loss = criterion(outputs, labels)
                
                loss.backward()
                optimizer.step()
                
                running_loss += loss.item()
                position_count += BATCH_SIZE

                batch_tensors, batch_labels = [], []

                if position_count % (100 * BATCH_SIZE) == 0:
                    print(f"Epoch {epoch+1}, Positions {position_count}: Loss = {running_loss / (position_count / BATCH_SIZE):.6f}")

        print(f"Epoch {epoch+1} finished. Average Loss: {running_loss / (position_count / BATCH_SIZE):.6f}")

        torch.save(model.state_dict(), MODEL_SAVE_PATH)
        print(f"Model saved to {MODEL_SAVE_PATH}")

if __name__ == "__main__":
    train()