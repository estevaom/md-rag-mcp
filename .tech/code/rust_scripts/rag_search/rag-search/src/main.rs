use anyhow::Result;
use chrono::NaiveDate;
use clap::Parser;
use serde::Serialize;
use std::path::PathBuf;
use lancedb;
use lancedb::query::{QueryBase, ExecutableQuery};
use arrow::array::{Int32Array, StringArray};
use futures::TryStreamExt;

mod embeddings;
use embeddings::EmbeddingGenerator;

#[derive(Parser, Debug)]
#[command(author, version, about = "Search indexed journal files", long_about = None)]
struct Args {
    /// Search query
    query: String,

    /// Filter results after this date (YYYY-MM-DD)
    #[arg(long)]
    after: Option<String>,

    /// Filter results before this date (YYYY-MM-DD)
    #[arg(long)]
    before: Option<String>,

    /// Number of results to return
    #[arg(short, long, default_value = "10")]
    num_results: usize,

    /// Return only file paths
    #[arg(long)]
    files_only: bool,

    /// Show debug information (scores, metadata)
    #[arg(long)]
    debug: bool,

    /// Output format
    #[arg(short, long, default_value = "text", value_enum)]
    format: OutputFormat,
}

#[derive(Debug, Clone, clap::ValueEnum)]
enum OutputFormat {
    Text,
    Json,
}

#[derive(Debug, Serialize)]
struct SearchResult {
    path: PathBuf,
    date: NaiveDate,
    score: f32,
    snippet: String,
    #[serde(skip_serializing_if = "Option::is_none")]
    metadata: Option<serde_json::Value>,
}

#[tokio::main]
async fn main() -> Result<()> {
    let args = Args::parse();
    
    // Parse date filters
    let after_date = args.after
        .as_deref()
        .map(|s| NaiveDate::parse_from_str(s, "%Y-%m-%d"))
        .transpose()?;
    
    let before_date = args.before
        .as_deref()
        .map(|s| NaiveDate::parse_from_str(s, "%Y-%m-%d"))
        .transpose()?;
    
    if args.debug {
        eprintln!("🔍 Query: '{}'", args.query);
        if let Some(after) = after_date {
            eprintln!("📅 After: {}", after);
        }
        if let Some(before) = before_date {
            eprintln!("📅 Before: {}", before);
        }
    }
    
    // Connect to LanceDB
    let lance_path = ".tech/data/lancedb/journal.lance";
    let results = match search_index(
        &lance_path,
        &args.query,
        after_date,
        before_date,
        args.num_results,
    ).await {
        Ok(results) => results,
        Err(e) => {
            eprintln!("Error searching index: {}", e);
            eprintln!("Falling back to stub results");
            search_stub(&args.query, after_date, before_date, args.num_results)
        }
    };
    
    // Output results
    match args.format {
        OutputFormat::Text => {
            if args.files_only {
                for result in &results {
                    println!("{}", result.path.display());
                }
            } else {
                for (i, result) in results.iter().enumerate() {
                    println!("\n{} {} | {} | Score: {:.3}", 
                        i + 1,
                        result.date,
                        result.path.display(),
                        result.score
                    );
                    println!("  {}", result.snippet);
                    
                    if args.debug {
                        if let Some(meta) = &result.metadata {
                            println!("  Debug: {}", serde_json::to_string_pretty(meta)?);
                        }
                    }
                }
            }
        }
        OutputFormat::Json => {
            let output = serde_json::to_string_pretty(&results)?;
            println!("{}", output);
        }
    }
    
    Ok(())
}

async fn search_index(
    lance_path: &str,
    query: &str,
    after: Option<NaiveDate>,
    before: Option<NaiveDate>,
    limit: usize,
) -> Result<Vec<SearchResult>> {
    // Connect to database
    let db = lancedb::connect(lance_path)
        .execute()
        .await?;
    
    // Open table
    let table = db.open_table("documents")
        .execute()
        .await?;
    
    // Generate embedding for the query
    let embedding_generator = EmbeddingGenerator::new()?;
    let query_embedding = embedding_generator.generate_embedding(query)?;
    
    // Build vector query
    let mut vector_query = table.vector_search(query_embedding)?
        .column("embedding")
        .limit(limit);
    
    // Build filter conditions
    let mut conditions = Vec::new();
    
    if let Some(after_date) = after {
        let days_since_epoch = (after_date - NaiveDate::from_ymd_opt(1970, 1, 1).unwrap()).num_days() as i32;
        conditions.push(format!("date >= {}", days_since_epoch));
    }
    
    if let Some(before_date) = before {
        let days_since_epoch = (before_date - NaiveDate::from_ymd_opt(1970, 1, 1).unwrap()).num_days() as i32;
        conditions.push(format!("date <= {}", days_since_epoch));
    }
    
    // Apply combined filter if we have conditions
    if !conditions.is_empty() {
        vector_query = vector_query.only_if(conditions.join(" AND "));
    }
    
    // Execute vector search
    let stream = vector_query.execute().await?;
    let batches: Vec<_> = stream.try_collect().await?;
    
    let mut results = Vec::new();
    
    // Process results
    for batch in batches {
        let path_array = batch.column_by_name("path")
            .ok_or(anyhow::anyhow!("Missing path column"))?
            .as_any()
            .downcast_ref::<StringArray>()
            .ok_or(anyhow::anyhow!("Failed to cast path column"))?;
        
        let date_array = batch.column_by_name("date")
            .ok_or(anyhow::anyhow!("Missing date column"))?
            .as_any()
            .downcast_ref::<Int32Array>()
            .ok_or(anyhow::anyhow!("Failed to cast date column"))?;
        
        let content_array = batch.column_by_name("content")
            .ok_or(anyhow::anyhow!("Missing content column"))?
            .as_any()
            .downcast_ref::<StringArray>()
            .ok_or(anyhow::anyhow!("Failed to cast content column"))?;
        
        // Get distance scores if available
        let distance_array = batch.column_by_name("_distance")
            .map(|col| col.as_any()
                .downcast_ref::<arrow::array::Float32Array>());
        
        for i in 0..batch.num_rows() {
            let path = path_array.value(i);
            let days_since_epoch = date_array.value(i);
            let content = content_array.value(i);
            
            // Convert days since epoch back to NaiveDate
            let date = NaiveDate::from_ymd_opt(1970, 1, 1).unwrap() + chrono::Duration::days(days_since_epoch as i64);
            
            // Get distance/score (lower is better for L2 distance)
            let score = if let Some(Some(distances)) = distance_array {
                // Convert L2 distance to similarity score (0-1, higher is better)
                let distance = distances.value(i);
                1.0 / (1.0 + distance)
            } else {
                0.5 // Default score if distance not available
            };
            
            // Extract snippet - prioritize content around query terms if present
            let snippet = extract_snippet(content, query, 500);
            
            results.push(SearchResult {
                path: PathBuf::from(path),
                date,
                score,
                snippet,
                metadata: None,
            });
        }
    }
    
    Ok(results)
}

fn extract_snippet(content: &str, query: &str, context_chars: usize) -> String {
    let lower_content = content.to_lowercase();
    let lower_query = query.to_lowercase();
    
    if let Some(pos) = lower_content.find(&lower_query) {
        // Find the byte position in the original content
        let byte_pos = pos;
        
        // Calculate approximate start and end positions
        let start_byte = byte_pos.saturating_sub(context_chars);
        let end_byte = (byte_pos + query.len() + context_chars).min(content.len());
        
        // Find valid UTF-8 boundaries
        let start = if start_byte == 0 {
            0
        } else {
            // Move backward to find a valid char boundary
            let mut valid_start = start_byte;
            while valid_start > 0 && !content.is_char_boundary(valid_start) {
                valid_start -= 1;
            }
            valid_start
        };
        
        let end = if end_byte >= content.len() {
            content.len()
        } else {
            // Move forward to find a valid char boundary
            let mut valid_end = end_byte;
            while valid_end < content.len() && !content.is_char_boundary(valid_end) {
                valid_end += 1;
            }
            valid_end
        };
        
        let snippet = &content[start..end];
        let snippet = snippet.trim();
        
        if start > 0 {
            format!("...{}", snippet)
        } else {
            snippet.to_string()
        }
    } else {
        content.chars().take(context_chars * 2).collect()
    }
}

// Temporary stub function for Phase 1
fn search_stub(
    query: &str,
    after: Option<NaiveDate>,
    before: Option<NaiveDate>,
    limit: usize,
) -> Vec<SearchResult> {
    // Return fake results for testing
    vec![
        SearchResult {
            path: PathBuf::from("journal/2025/07/21.md"),
            date: NaiveDate::from_ymd_opt(2025, 7, 21).unwrap(),
            score: 0.95,
            snippet: format!("Found '{}' in context: discussing Rust RAG implementation...", query),
            metadata: None,
        },
        SearchResult {
            path: PathBuf::from("journal/2025/07/20.md"),
            date: NaiveDate::from_ymd_opt(2025, 7, 20).unwrap(),
            score: 0.87,
            snippet: format!("Another match for '{}': working on performance optimization...", query),
            metadata: None,
        },
    ]
    .into_iter()
    .filter(|r| {
        // Apply date filters
        if let Some(after) = after {
            if r.date < after {
                return false;
            }
        }
        if let Some(before) = before {
            if r.date > before {
                return false;
            }
        }
        true
    })
    .take(limit)
    .collect()
}

#[cfg(test)]
mod tests {
    use super::*;
    
    #[test]
    fn test_date_filtering() {
        let results = search_stub(
            "test",
            Some(NaiveDate::from_ymd_opt(2025, 7, 21).unwrap()),
            None,
            10
        );
        assert_eq!(results.len(), 1);
        assert_eq!(results[0].date.day(), 21);
    }
}