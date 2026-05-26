from sentence_transformers import SentenceTransformer

# Load the BERT model (downloads once, ~90MB, then cached)
# 'all-MiniLM-L6-v2' is small, fast, and highly accurate for text similarity
model = SentenceTransformer('all-MiniLM-L6-v2')

def get_embedding(text):
    """
    Takes any string and returns a 384-dimensional vector.
    Similar texts will have vectors close to each other.
    """
    embedding = model.encode(text, convert_to_tensor=True)
    return embedding


# --- TEST IT ---
if __name__ == "__main__":
    sample = "Machine learning engineer with Python and deep learning experience"
    vector = get_embedding(sample)
    
    print("Text:", sample)
    print("Embedding shape:", vector.shape)   # should print torch.Size([384])
    print("First 5 values:", vector[:5])      # just a peek at the numbers