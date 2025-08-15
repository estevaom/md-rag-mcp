use anyhow::{Context, Result};
use chrono::NaiveDate;
use clap::Parser;
use regex::Regex;
use serde::Serialize;
use serde_json::json;
use std::collections::HashMap;
use std::fs;
use std::path::{Path, PathBuf};
use walkdir::WalkDir;

#[derive(Parser, Debug)]
#[command(author, version, about, long_about = None)]
struct Args {
    /// Directory to search for journal files
    #[arg(short, long, default_value = "journal")]
    path: PathBuf,

    /// Fields to extract from frontmatter
    #[arg(short, long, num_args = 1.., default_values_t = vec!["mood".to_string(), "anxiety".to_string(), "weight_kg".to_string()])]
    fields: Vec<String>,

    /// Start date filter (YYYY-MM-DD)
    #[arg(short = 's', long)]
    start_date: Option<String>,

    /// End date filter (YYYY-MM-DD)
    #[arg(short = 'e', long)]
    end_date: Option<String>,

    /// Calculate statistics for numeric fields
    #[arg(long)]
    stats: bool,

    /// Output format
    #[arg(short = 'o', long, value_enum, default_value = "json")]
    format: OutputFormat,

    /// Include file paths in output
    #[arg(long)]
    include_files: bool,
}

#[derive(Debug, Clone, clap::ValueEnum)]
enum OutputFormat {
    Json,
    Csv,
    Table,
}

#[derive(Debug)]
struct JournalEntry {
    file_path: PathBuf,
    date: NaiveDate,
    frontmatter: HashMap<String, serde_yaml::Value>,
}

#[derive(Debug, Serialize)]
struct QueryResult {
    date: String,
    #[serde(skip_serializing_if = "Option::is_none")]
    file: Option<String>,
    #[serde(flatten)]
    fields: HashMap<String, Option<serde_json::Value>>,
}

#[derive(Debug, Serialize)]
struct FieldStats {
    count: usize,
    min: f64,
    max: f64,
    avg: f64,
    #[serde(skip_serializing_if = "Option::is_none")]
    skipped_count: Option<usize>,
}

fn extract_frontmatter(content: &str) -> Result<HashMap<String, serde_yaml::Value>> {
    let re = Regex::new(r"(?s)^---\n(.*?)\n---")?;
    
    if let Some(captures) = re.captures(content) {
        let yaml_content = captures.get(1).unwrap().as_str();
        let frontmatter: HashMap<String, serde_yaml::Value> = serde_yaml::from_str(yaml_content)
            .context("Failed to parse YAML frontmatter")?;
        Ok(frontmatter)
    } else {
        Err(anyhow::anyhow!("No frontmatter found"))
    }
}

fn parse_date_from_frontmatter(frontmatter: &HashMap<String, serde_yaml::Value>) -> Result<NaiveDate> {
    let date_value = frontmatter.get("date")
        .ok_or_else(|| anyhow::anyhow!("No date field in frontmatter"))?;
    
    match date_value {
        serde_yaml::Value::String(s) => {
            NaiveDate::parse_from_str(s, "%Y-%m-%d")
                .context("Failed to parse date string")
        }
        _ => Err(anyhow::anyhow!("Date field is not a string")),
    }
}

fn find_journal_files(
    base_dir: &Path,
    start_date: Option<NaiveDate>,
    end_date: Option<NaiveDate>,
) -> Result<Vec<JournalEntry>> {
    let mut entries = Vec::new();
    
    for entry in WalkDir::new(base_dir) {
        let entry = entry?;
        let path = entry.path();
        
        if path.extension().and_then(|s| s.to_str()) == Some("md") {
            let content = match fs::read_to_string(path) {
                Ok(content) => content,
                Err(_) => continue, // Skip files we can't read
            };
            
            let frontmatter = match extract_frontmatter(&content) {
                Ok(fm) => fm,
                Err(_) => continue, // Skip files without valid frontmatter
            };
            
            let date = match parse_date_from_frontmatter(&frontmatter) {
                Ok(date) => date,
                Err(_) => continue, // Skip files without valid date
            };
            
            // Apply date filters
            if let Some(start) = start_date {
                if date < start {
                    continue;
                }
            }
            if let Some(end) = end_date {
                if date > end {
                    continue;
                }
            }
            
            entries.push(JournalEntry {
                file_path: path.to_path_buf(),
                date,
                frontmatter,
            });
        }
    }
    
    // Sort by date
    entries.sort_by_key(|e| e.date);
    
    Ok(entries)
}

fn yaml_to_json_value(yaml_val: &serde_yaml::Value) -> serde_json::Value {
    match yaml_val {
        serde_yaml::Value::Null => serde_json::Value::Null,
        serde_yaml::Value::Bool(b) => serde_json::Value::Bool(*b),
        serde_yaml::Value::Number(n) => {
            if let Some(i) = n.as_i64() {
                serde_json::Value::Number(i.into())
            } else if let Some(f) = n.as_f64() {
                serde_json::Value::Number(serde_json::Number::from_f64(f).unwrap_or(0.into()))
            } else {
                serde_json::Value::Null
            }
        }
        serde_yaml::Value::String(s) => {
            // Clean up values by removing comments
            let cleaned = if let Some(pos) = s.find('#') {
                s[..pos].trim().to_string()
            } else {
                s.clone()
            };
            serde_json::Value::String(cleaned)
        }
        serde_yaml::Value::Sequence(seq) => {
            serde_json::Value::Array(seq.iter().map(yaml_to_json_value).collect())
        }
        serde_yaml::Value::Mapping(map) => {
            let obj: serde_json::Map<String, serde_json::Value> = map
                .iter()
                .filter_map(|(k, v)| {
                    k.as_str().map(|key| (key.to_string(), yaml_to_json_value(v)))
                })
                .collect();
            serde_json::Value::Object(obj)
        }
        _ => serde_json::Value::Null,
    }
}

fn query_fields(entries: &[JournalEntry], fields: &[String], include_files: bool) -> Vec<QueryResult> {
    entries.iter().map(|entry| {
        let mut field_values = HashMap::new();
        
        for field in fields {
            let value = entry.frontmatter.get(field)
                .map(|v| yaml_to_json_value(v))
                .filter(|v| !matches!(v, serde_json::Value::Null));
            
            field_values.insert(field.clone(), value);
        }
        
        QueryResult {
            date: entry.date.format("%Y-%m-%d").to_string(),
            file: if include_files {
                Some(entry.file_path.display().to_string())
            } else {
                None
            },
            fields: field_values,
        }
    }).collect()
}

fn parse_numeric_value(value: &serde_json::Value) -> Option<f64> {
    match value {
        serde_json::Value::Number(n) => n.as_f64(),
        serde_json::Value::String(s) => {
            // Handle range values like "3-4"
            if let Some(dash_pos) = s.find('-') {
                let (start, end) = s.split_at(dash_pos);
                let end = &end[1..]; // Skip the dash
                
                if let (Ok(start_val), Ok(end_val)) = (start.trim().parse::<f64>(), end.trim().parse::<f64>()) {
                    return Some((start_val + end_val) / 2.0);
                }
            }
            
            // Try direct parse
            s.parse::<f64>().ok()
        }
        _ => None,
    }
}

fn calculate_stats(results: &[QueryResult], field: &str) -> Option<FieldStats> {
    let mut values = Vec::new();
    let mut skipped = 0;
    
    for result in results {
        if let Some(Some(value)) = result.fields.get(field) {
            if let Some(num) = parse_numeric_value(value) {
                values.push(num);
            } else {
                skipped += 1;
            }
        }
    }
    
    if values.is_empty() {
        return None;
    }
    
    let count = values.len();
    let min = values.iter().cloned().fold(f64::INFINITY, f64::min);
    let max = values.iter().cloned().fold(f64::NEG_INFINITY, f64::max);
    let sum: f64 = values.iter().sum();
    let avg = sum / count as f64;
    
    Some(FieldStats {
        count,
        min,
        max,
        avg,
        skipped_count: if skipped > 0 { Some(skipped) } else { None },
    })
}

fn output_json(results: &[QueryResult], stats: Option<HashMap<String, FieldStats>>) {
    if let Some(stats) = stats {
        let output = json!({
            "results": results,
            "stats": stats,
        });
        println!("{}", serde_json::to_string_pretty(&output).unwrap());
    } else {
        println!("{}", serde_json::to_string_pretty(&results).unwrap());
    }
}

fn output_csv(results: &[QueryResult], fields: &[String], include_files: bool) {
    // Header
    print!("date");
    if include_files {
        print!(",file");
    }
    for field in fields {
        print!(",{}", field);
    }
    println!();
    
    // Data
    for result in results {
        print!("{}", result.date);
        if include_files {
            if let Some(ref file) = result.file {
                print!(",{}", file);
            }
        }
        for field in fields {
            print!(",");
            if let Some(Some(value)) = result.fields.get(field) {
                match value {
                    serde_json::Value::String(s) => print!("{}", s),
                    _ => print!("{}", value),
                }
            }
        }
        println!();
    }
}

fn output_table(results: &[QueryResult], fields: &[String]) {
    // Header
    print!("date\t");
    for field in fields {
        print!("{}\t", field);
    }
    println!();
    
    // Data
    for result in results {
        print!("{}\t", result.date);
        for field in fields {
            if let Some(Some(value)) = result.fields.get(field) {
                match value {
                    serde_json::Value::String(s) => print!("{}\t", s),
                    _ => print!("{}\t", value),
                }
            } else {
                print!("\t");
            }
        }
        println!();
    }
}

fn main() -> Result<()> {
    let args = Args::parse();
    
    // Parse dates if provided
    let start_date = args.start_date
        .as_ref()
        .map(|s| NaiveDate::parse_from_str(s, "%Y-%m-%d"))
        .transpose()
        .context("Invalid start date format")?;
    
    let end_date = args.end_date
        .as_ref()
        .map(|s| NaiveDate::parse_from_str(s, "%Y-%m-%d"))
        .transpose()
        .context("Invalid end date format")?;
    
    // Find and process journal files
    let entries = find_journal_files(&args.path, start_date, end_date)?;
    let results = query_fields(&entries, &args.fields, args.include_files);
    
    // Calculate statistics if requested
    let stats = if args.stats {
        let mut field_stats = HashMap::new();
        for field in &args.fields {
            if let Some(stats) = calculate_stats(&results, field) {
                field_stats.insert(field.clone(), stats);
            }
        }
        Some(field_stats)
    } else {
        None
    };
    
    // Output results
    match args.format {
        OutputFormat::Json => output_json(&results, stats),
        OutputFormat::Csv => output_csv(&results, &args.fields, args.include_files),
        OutputFormat::Table => output_table(&results, &args.fields),
    }
    
    Ok(())
}