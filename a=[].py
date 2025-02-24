import pandas as pd
import torch
import numpy as np
import faiss
from transformers import DistilBertTokenizer, DistilBertModel
import os

os.environ["KMP_DUPLICATE_LIB_OK"] = "TRUE"

# Load dataset
df = pd.read_csv("Zomato Chennai Listing 2020.csv")

# Data Cleaning
df["Top Dishes"] = df["Top Dishes"].replace("Invalid", "No popular dish found")
df["Dining Rating"] = df["Dining Rating"].fillna(0)

# Combine text fields for context
df["combined_text"] = df["Name of Restaurant"] + " " + df["Location"] + " " + df["Cuisine"] + " " + df["Top Dishes"]

# Load DistilBERT (on CPU)
device = "cpu"
tokenizer = DistilBertTokenizer.from_pretrained("distilbert-base-uncased")
model = DistilBertModel.from_pretrained("distilbert-base-uncased").to(device)

# Tokenize text
# tokens = tokenizer(df["combined_text"].tolist(), padding=True, truncation=True, return_tensors="pt")

# # Generate embeddings
# with torch.no_grad():
#     embeddings = model(**tokens).last_hidden_state[:, 0, :].numpy()  # CLS token representation

# Normalize embeddings for cosine similarity
def normalize(vecs):
    return vecs / np.linalg.norm(vecs, axis=1, keepdims=True)

# embeddings_np = normalize(embeddings)
# np.save("embeddings.npy", embeddings_np)  # Save embeddings
# df.to_csv("processed_data.csv", index=False)  # Save processed dataset

# # Create FAISS index using cosine similarity
# d = embeddings_np.shape[1]  # Embedding dimension
# index = faiss.IndexFlatIP(d)
# index.add(embeddings_np)

# # Save index to disk
# faiss.write_index(index, "faiss_index.bin")
# print("FAISS index dimensions:", embeddings_np.shape[1])  # Should match embedding dimension

# print("✅ Embeddings and FAISS index generated and saved without numeric features!")

# Load dataset and FAISS index
df = pd.read_csv("processed_data.csv")
index = faiss.read_index("faiss_index.bin")

def recommend(query, top_k=1):
    query_lower = query.lower()
    
    # If query contains a specific dish, search in 'Top Dishes' column
    dish_matches = df[df["Best Dish"].str.contains(query, case=False, na=False)]
    dish_matches = dish_matches[dish_matches["Best Dish"] != "No popular dish found"]
    
    if not dish_matches.empty:
        results = dish_matches.head(top_k)
    else:
        # Encode query with DistilBERT
        query_embedding = tokenizer(query, padding=True, truncation=True, return_tensors="pt")
        
        with torch.no_grad():
            query_vector = model(**query_embedding).last_hidden_state[:, 0, :].numpy()
        
        # Convert query embedding to float32 and normalize
        query_vector = normalize(np.asarray(query_vector, dtype=np.float32))
        
        # Search in FAISS
        distances, indices = index.search(query_vector, top_k)
        results = df.iloc[indices[0]].copy()
        results["Distance"] = distances[0]
    
    
    # Print results
    for i, row in results.iterrows():
        print(f"🔹 {row['Name of Restaurant']} ({row['Location']})")
        print(f"   - Cuisine: {row['Cuisine']}")
        print(f"   - Best Dish: {row['Top Dishes']}")
        print(f"   - Price for Two: ₹{row['Price for 2']} | Rating: {row['Dining Rating']}/5")
        print(f"   - Reason: Matches your query based on cuisine, rating, and price.\n")

# Test recommendation
recommend("ya moideen")
