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
    
    /// Generate a single embedding
    pub fn generate_embedding(&self, text: &str) -> Result<Vec<f32>> {
        let embeddings = self.model.borrow_mut().embed(vec![text], None)?;
        
        // Return the first (and only) embedding
        embeddings.into_iter().next()
            .ok_or_else(|| anyhow::anyhow!("No embedding generated"))
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