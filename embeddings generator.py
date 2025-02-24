import numpy as np
from pymongo import MongoClient
from transformers import AutoTokenizer, AutoModel
import torch
import faiss

# Step 1: Connect to MongoDB and load data
client = MongoClient("mongodb+srv://harissh:Xboxones07@cluster0.dm6mvwq.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0")
db = client["music"]
collection = db["top50"]

# Fetch all documents
documents = list(collection.find({}))

# Step 2: Extract text data (for example, Track.Name and Artist.Name)
texts = [f"{doc['Track.Name']} {doc['Artist.Name']}" for doc in documents]

# Step 3: Load the embedding model
tokenizer = AutoTokenizer.from_pretrained("meta-llama/Llama-2-7b")
model = AutoModel.from_pretrained("meta-llama/Llama-2-7b")
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
model.to(device)

def generate_embeddings(texts):
    embeddings = []
    for text in texts:
        inputs = tokenizer(text, return_tensors="pt", truncation=True, padding=True)
        inputs = {key: value.to(device) for key, value in inputs.items()}
        with torch.no_grad():
            outputs = model(**inputs)
        last_hidden_states = outputs.last_hidden_state
        embedding = last_hidden_states.mean(dim=1).cpu().numpy()
        embeddings.append(embedding)
    return embeddings

embeddings = generate_embeddings(texts)

# Convert list of embeddings to a NumPy array
embeddings_array = np.vstack(embeddings)

# Step 4: Store the embeddings in a Faiss index
d = embeddings_array.shape[1]  # Dimensionality of embeddings
index = faiss.IndexFlatL2(d)
index.add(embeddings_array)

# You can save the index to disk if needed
faiss.write_index(index, "vector_index.faiss")

print("Embeddings generated and stored in Faiss index.")

# Verify by querying the index (optional)
D, I = index.search(embeddings_array[:1], 5)  # Search for the 5 nearest neighbors of the first embedding
print("Nearest neighbors of the first embedding:", I)

for doc in collection.find():
    doc_string = create_document_string(doc)
    embedding = model.encode(doc_string).tolist()  
    collection.update_one({'_id': doc['_id']}, {'$set': {'track_embedding': embedding}})
    print(embedding)
print("Embeddings added to all documents.")