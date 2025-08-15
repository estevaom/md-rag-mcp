use anyhow::Result;
use fastembed::{TextEmbedding, InitOptions, EmbeddingModel};
use std::cell::RefCell;

/// Manages text embeddings for the RAG system
pub struct EmbeddingGenerator {
    model: RefCell<TextEmbedding>,
}

impl EmbeddingGenerator {
    /// Create a new embedding generator with BGE-base-en-v1.5 model
    pub fn new() -> Result<Self> {
        println!("🤖 Loading embedding model (BGE-base-en-v1.5)...");
        
        // Use BGEBaseENV15 which produces 768-dimensional embeddings
        // This is a high-quality English-focused model
        let model = TextEmbedding::try_new(
            InitOptions::new(EmbeddingModel::BGEBaseENV15)
        )?;
        
        println!("✅ Embedding model loaded successfully!");
        
        Ok(Self { model: RefCell::new(model) })
    }
    
    /// Generate embeddings for a batch of texts
    pub fn generate_embeddings(&self, texts: Vec<String>) -> Result<Vec<Vec<f32>>> {
        // fastembed expects &str, so we need to convert
        let text_refs: Vec<&str> = texts.iter().map(|s| s.as_str()).collect();
        
        // Generate embeddings
        let embeddings = self.model.borrow_mut().embed(text_refs, None)?;
        
        // Convert to Vec<Vec<f32>>
        Ok(embeddings)
    }
    
    
    /// Get the dimension of embeddings produced by this model
    pub fn embedding_dimension(&self) -> usize {
        768 // BGE-base-en-v1.5 produces 768-dimensional vectors
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    
    #[test]
    fn test_embedding_dimension() {
        let generator = EmbeddingGenerator::new().unwrap();
        assert_eq!(generator.embedding_dimension(), 768);
    }
    
    #[test]
    fn test_single_embedding() {
        let generator = EmbeddingGenerator::new().unwrap();
        let embedding = generator.generate_embedding("Hello, world!").unwrap();
        assert_eq!(embedding.len(), 768);
    }
}