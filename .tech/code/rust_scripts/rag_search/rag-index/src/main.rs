use anyhow::Result;
use chrono::NaiveDate;
use clap::Parser;
use gray_matter::Matter;
use gray_matter::engine::YAML;
use lancedb;
use arrow::array::{Int32Array, StringArray, FixedSizeListArray, Array};
use arrow::datatypes::{DataType, Field, Schema, Float32Type};
use arrow::record_batch::RecordBatch;
use arrow::record_batch::RecordBatchIterator;
use std::sync::Arc;
// use rand::Rng; // No longer needed for fake embeddings
use serde::Deserialize;
use std::fs;
use std::io::Write;
use std::path::{Path, PathBuf};
use walkdir::WalkDir;

mod template_filter;
use template_filter::TemplateFilter;
mod embeddings;
use embeddings::EmbeddingGenerator;

#[derive(Parser, Debug)]
#[command(author, version, about = "Index journal files for RAG search", long_about = None)]
struct Args {
    /// Journal directory to index
    #[arg(short, long, default_value = "journal")]
    journal_dir: PathBuf,

    /// LanceDB directory
    #[arg(short, long, default_value = ".tech/data/lancedb")]
    lance_dir: PathBuf,

    /// Force rebuild entire index
    #[arg(short, long)]
    rebuild: bool,

    /// Only index files modified since this date (YYYY-MM-DD)
    #[arg(short, long)]
    since: Option<String>,

    /// Verbose output
    #[arg(short, long)]
    verbose: bool,
}

#[derive(Debug, Deserialize)]
struct Frontmatter {
    date: String,
}

// Document struct is now only used for intermediate processing

// const EMBEDDING_DIM: usize = 384; // Now determined by the model

#[tokio::main]
async fn main() -> Result<()> {
    let args = Args::parse();
    
    println!("🔍 RAG Indexer");
    println!("📁 Scanning: {}", args.journal_dir.display());
    println!("💾 Index location: {}", args.lance_dir.display());
    
    // Scan documents
    let documents = scan_journal_directory(&args.journal_dir, args.since.as_deref(), args.verbose)?;
    println!("\n📊 Found {} documents to index", documents.len());
    
    if documents.is_empty() {
        println!("No documents to index!");
        return Ok(());
    }
    
    // Create or open LanceDB connection
    let lance_path = args.lance_dir.join("journal.lance");
    fs::create_dir_all(&args.lance_dir)?;
    
    let db = lancedb::connect(lance_path.to_str().unwrap())
        .execute()
        .await?;
    println!("📂 Connected to LanceDB at: {}", lance_path.display());
    
    // Create template filter
    let filter = TemplateFilter::new();
    
    // Create embedding generator
    let embedding_generator = EmbeddingGenerator::new()?;
    let embedding_dim = embedding_generator.embedding_dimension();
    
    // Create schema for our documents with chunk support
    let schema = Arc::new(Schema::new(vec![
        Field::new("path", DataType::Utf8, false),
        Field::new("date", DataType::Int32, false),
        Field::new("content", DataType::Utf8, false),
        Field::new("chunk_index", DataType::Int32, false),  // Which chunk in document
        Field::new("total_chunks", DataType::Int32, false), // Total chunks in document
        Field::new(
            "embedding",
            DataType::FixedSizeList(
                Arc::new(Field::new("item", DataType::Float32, true)),
                embedding_dim as i32,
            ),
            false,
        ),
    ]));
    
    // Prepare documents with embeddings
    println!("\n🧽 Cleaning template noise and chunking documents...");
    println!("🤖 Generating real embeddings with BGE-base-en-v1.5...");
    
    // Process documents into chunks
    let mut all_chunks = Vec::new();
    let mut chunk_paths = Vec::new();
    let mut chunk_dates = Vec::new();
    let mut chunk_indices = Vec::new();
    let mut total_chunks_vec = Vec::new();
    
    for doc in &documents {
        // Extract chunks for this document
        let chunks = filter.extract_chunks(&doc.content, 2000); // 2000 char max per chunk
        let num_chunks = chunks.len() as i32;
        
        // Add each chunk with metadata
        for (idx, chunk_content) in chunks.into_iter().enumerate() {
            all_chunks.push(chunk_content);
            chunk_paths.push(doc.path.clone());
            chunk_dates.push(doc.date);
            chunk_indices.push(idx as i32);
            total_chunks_vec.push(num_chunks);
        }
    }
    
    println!("  Extracted {} chunks from {} documents", all_chunks.len(), documents.len());
    
    // Generate embeddings in batches to avoid timeouts
    let mut embeddings = Vec::new();
    let batch_size = 100;
    
    for (i, chunk_batch) in all_chunks.chunks(batch_size).enumerate() {
        print!("  Generating embeddings batch {}/{}...\r", i + 1, (all_chunks.len() + batch_size - 1) / batch_size);
        std::io::stdout().flush()?;
        
        let batch_embeddings = embedding_generator.generate_embeddings(chunk_batch.to_vec())?;
        embeddings.extend(batch_embeddings);
    }
    
    println!("\n✅ Generated {} embeddings of dimension {}", embeddings.len(), embedding_dim);
    
    // Create Arrow arrays
    let path_array = Arc::new(StringArray::from(chunk_paths));
    let date_array = Arc::new(Int32Array::from(chunk_dates));
    let content_array = Arc::new(StringArray::from(all_chunks));
    let chunk_index_array = Arc::new(Int32Array::from(chunk_indices));
    let total_chunks_array = Arc::new(Int32Array::from(total_chunks_vec));
    let embedding_array = Arc::new(FixedSizeListArray::from_iter_primitive::<Float32Type, _, _>(
        embeddings.into_iter().map(|v| Some(v.into_iter().map(Some).collect::<Vec<_>>())),
        embedding_dim as i32,
    ));
    
    // Create RecordBatch - need to ensure all arrays are the same type
    let batch = RecordBatch::try_new(
        schema.clone(),
        vec![
            path_array as Arc<dyn Array>,
            date_array as Arc<dyn Array>,
            content_array as Arc<dyn Array>,
            chunk_index_array as Arc<dyn Array>,
            total_chunks_array as Arc<dyn Array>,
            embedding_array as Arc<dyn Array>,
        ],
    )?;
    
    // Create RecordBatchIterator
    let batches = RecordBatchIterator::new(
        vec![batch].into_iter().map(Ok),
        schema.clone(),
    );
    
    // Create or replace table
    let table_name = "documents";
    
    // Check if table exists
    let tables = db.table_names().execute().await?;
    
    if tables.contains(&table_name.to_string()) {
        if args.rebuild {
            println!("🗑️  Dropping existing table...");
            db.drop_table(table_name).await?;
        } else {
            println!("⚠️  Table already exists. Use --rebuild to overwrite.");
            return Ok(());
        }
    }
    
    let _ = table_name;  // Ensure table_name is used
    
    // Create new table from documents
    let table = db
        .create_table(table_name, batches)
        .execute()
        .await?;
    let count = table.count_rows(None).await?;
    
    println!("✅ Created table with {} chunks from {} documents", count, documents.len());
    println!("🧽 Removed template boilerplate from all entries");
    println!("\n✨ Indexing complete!");
    
    Ok(())
}

/// Get the date from a file's metadata (modification time)
fn get_file_date(path: &Path, verbose: bool) -> Result<NaiveDate> {
    use chrono::{DateTime, Utc};
    
    let metadata = fs::metadata(path)?;
    let modified = metadata.modified()?;
    
    // Convert SystemTime to DateTime<Utc>
    let datetime: DateTime<Utc> = modified.into();
    let date = datetime.naive_utc().date();
    
    if verbose {
        println!("    → File modified date: {}", date);
    }
    
    Ok(date)
}

fn scan_journal_directory(
    dir: &Path,
    since: Option<&str>,
    verbose: bool,
) -> Result<Vec<ScanDocument>> {
    let mut documents = Vec::new();
    let matter = Matter::<YAML>::new();
    
    // Parse since date if provided
    let since_date = since
        .map(|s| NaiveDate::parse_from_str(s, "%Y-%m-%d"))
        .transpose()?;
    
    for entry in WalkDir::new(dir)
        .follow_links(true)
        .into_iter()
        .filter_map(|e| e.ok())
    {
        let path = entry.path();
        
        // Skip if not a markdown file
        if path.extension().and_then(|s| s.to_str()) != Some("md") {
            continue;
        }
        
        // Skip template files
        if path.file_name()
            .and_then(|s| s.to_str())
            .map(|s| s.starts_with("template"))
            .unwrap_or(false)
        {
            continue;
        }
        
        if verbose {
            println!("  Checking: {}", path.display());
        }
        
        // Read file content
        let content = match fs::read_to_string(path) {
            Ok(c) => c,
            Err(e) => {
                eprintln!("  ⚠️  Error reading {}: {}", path.display(), e);
                continue;
            }
        };
        
        // Parse frontmatter
        let parsed = matter.parse(&content);
        
        // Extract date from frontmatter or use file modification time
        let date = if let Some(data) = &parsed.data {
            // Try to deserialize the frontmatter to get the date
            if let Ok(fm) = data.deserialize::<Frontmatter>() {
                match NaiveDate::parse_from_str(&fm.date, "%Y-%m-%d") {
                    Ok(date) => date,
                    Err(e) => {
                        eprintln!("  ⚠️  Invalid date in frontmatter for {}: {}, using file modification time", path.display(), e);
                        // Fall back to file modification time
                        get_file_date(path, verbose)?
                    }
                }
            } else {
                // Has frontmatter but couldn't parse it, use file modification time
                if verbose {
                    println!("  📅 Using file modification time for: {} (unparseable frontmatter)", path.display());
                }
                get_file_date(path, verbose)?
            }
        } else {
            // No frontmatter, use file modification time
            if verbose {
                println!("  📅 Using file modification time for: {} (no frontmatter)", path.display());
            }
            get_file_date(path, verbose)?
        };
        
        // Check if file is too old
        if let Some(since) = since_date {
            if date < since {
                if verbose {
                    println!("  ⏭️  Skipping {} (older than {})", path.display(), since);
                }
                continue;
            }
        }
        
        // Convert date to days since epoch for LanceDB
        let epoch = NaiveDate::from_ymd_opt(1970, 1, 1).unwrap();
        let days_since_epoch = (date - epoch).num_days() as i32;
        
        documents.push(ScanDocument {
            path: path.to_string_lossy().to_string(),
            date: days_since_epoch,
            content: parsed.content,
        });
    }
    
    // Sort by date
    documents.sort_by_key(|d| d.date);
    
    Ok(documents)
}

// Intermediate struct for scanning
struct ScanDocument {
    path: String,
    date: i32,
    content: String,
}

#[cfg(test)]
mod tests {
    use super::*;
    
    #[test]
    fn test_date_parsing() {
        let date = NaiveDate::parse_from_str("2025-07-21", "%Y-%m-%d").unwrap();
        assert_eq!(date.year(), 2025);
        assert_eq!(date.month(), 7);
        assert_eq!(date.day(), 21);
    }
}