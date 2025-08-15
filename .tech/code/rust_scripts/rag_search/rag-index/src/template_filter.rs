use std::collections::HashSet;

/// Identifies and filters out template boilerplate from journal entries
pub struct TemplateFilter {
    boilerplate_headers: HashSet<String>,
    empty_section_patterns: Vec<&'static str>,
}

impl TemplateFilter {
    pub fn new() -> Self {
        let mut boilerplate_headers = HashSet::new();
        
        // Level 2 headers that are pure template
        boilerplate_headers.insert("## I. Work Responsibilities & Goals (Mon-Fri)".to_string());
        boilerplate_headers.insert("## II. Primary Focus Activities: [Declared Primary Focus from above]".to_string());
        boilerplate_headers.insert("## III. Nice-to-Haves / Other Minor Tasks".to_string());
        boilerplate_headers.insert("## IV. Progress Toward Broader Goals".to_string());
        boilerplate_headers.insert("## V. End-of-Day Reflection".to_string());
        
        // Level 3 headers that are pure template
        boilerplate_headers.insert("### A. If AI Study:".to_string());
        boilerplate_headers.insert("### B. If Rust Study:".to_string());
        boilerplate_headers.insert("### C. If Other Focused Activity (e.g., NixOS Rice, Specific Project):".to_string());
        boilerplate_headers.insert("### C. If Other Focused Activity:".to_string());
        
        // Common empty patterns that indicate unfilled template sections
        let empty_section_patterns = vec![
            "- Main Work Goal(s) for Today:\n  -\n",
            "- Key Work Tasks:\n  - [ ]\n  - [ ]\n  - [ ]\n",
            "- Learning Objective(s) (Review `journal/topics/ai_study_backlog.md` with Cline if needed):\n  -\n",
            "- Project Task(s) (if any):\n  - [ ]\n",
            "- Key Questions for AI / Discussion Points:\n  -\n",
            "- Time Allotted:\n",
            "- Goal for this session:\n  -\n",
            "- Specific Learning Focus:\n  -\n",
            "- Key Tasks:\n  - [ ]\n",
            "- [ ]\n- [ ]\n",
            "- Time Allotted:\n- Reflection/Notes:\n",
            "- Goal for this session:\n  -\n- Key Tasks:\n  - [ ]\n- Time Allotted:\n- Reflection/Notes:\n",
            "- What went well today (Work, Primary Focus, Personal)?\n",
            "- Challenges faced & how they were handled?\n",
            "- Key learnings (Technical, Rust, Personal, etc.)?\n",
            "- How did the overall balance feel today (Work/Focus/Relaxation/Other Activities)?\n",
            "- Adjustments or intentions for tomorrow?\n",
            "- Gratitude Moment:\n",
        ];
        
        Self {
            boilerplate_headers,
            empty_section_patterns,
        }
    }
    
    /// Process content and return cleaned version with template noise removed
    pub fn clean_content(&self, content: &str) -> String {
        let mut cleaned = String::new();
        let mut current_section = String::new();
        let mut in_boilerplate_section = false;
        let mut _section_header = String::new();
        
        for line in content.lines() {
            // Check if this is a header
            if line.starts_with("##") {
                // Process the previous section
                if !in_boilerplate_section && !self.is_empty_section(&current_section) {
                    cleaned.push_str(&current_section);
                }
                
                // Reset for new section
                current_section.clear();
                _section_header = line.to_string();
                
                // Check if this header is boilerplate
                in_boilerplate_section = self.boilerplate_headers.contains(line);
                
                // Add the header to current section
                current_section.push_str(line);
                current_section.push('\n');
            } else {
                // Add line to current section
                current_section.push_str(line);
                current_section.push('\n');
            }
        }
        
        // Don't forget the last section
        if !in_boilerplate_section && !self.is_empty_section(&current_section) {
            cleaned.push_str(&current_section);
        }
        
        // Remove consecutive empty lines
        self.remove_excessive_whitespace(&cleaned)
    }
    
    /// Check if a section contains only template boilerplate
    fn is_empty_section(&self, section: &str) -> bool {
        // Skip if section is too short to have content
        if section.trim().lines().count() < 3 {
            return true;
        }
        
        // Check for empty bullet patterns
        for pattern in &self.empty_section_patterns {
            if section.contains(pattern) {
                // Count how many non-template lines exist
                let meaningful_lines = section
                    .lines()
                    .filter(|line| {
                        let trimmed = line.trim();
                        !trimmed.is_empty() 
                            && !trimmed.starts_with('#')
                            && !trimmed.starts_with("- [ ]")
                            && !trimmed.starts_with("  -")
                            && trimmed != "-"
                    })
                    .count();
                
                if meaningful_lines < 2 {
                    return true;
                }
            }
        }
        
        false
    }
    
    /// Remove excessive whitespace while preserving paragraph structure
    fn remove_excessive_whitespace(&self, content: &str) -> String {
        let mut result = String::new();
        let mut consecutive_empty = 0;
        
        for line in content.lines() {
            if line.trim().is_empty() {
                consecutive_empty += 1;
                if consecutive_empty <= 2 {
                    result.push('\n');
                }
            } else {
                consecutive_empty = 0;
                result.push_str(line);
                result.push('\n');
            }
        }
        
        result.trim().to_string()
    }
    
    /// Extract chunks by meaningful sections, skipping template noise
    pub fn extract_chunks(&self, content: &str, max_chunk_size: usize) -> Vec<String> {
        let cleaned = self.clean_content(content);
        let mut chunks = Vec::new();
        let mut current_chunk = String::new();
        
        for line in cleaned.lines() {
            // Start new chunk on headers
            if line.starts_with('#') && !current_chunk.is_empty() {
                if current_chunk.len() > 100 {  // Minimum chunk size
                    chunks.push(current_chunk.trim().to_string());
                }
                current_chunk.clear();
            }
            
            current_chunk.push_str(line);
            current_chunk.push('\n');
            
            // Split if chunk gets too large
            if current_chunk.len() > max_chunk_size {
                chunks.push(current_chunk.trim().to_string());
                current_chunk.clear();
            }
        }
        
        // Don't forget the last chunk
        if current_chunk.len() > 100 {
            chunks.push(current_chunk.trim().to_string());
        }
        
        chunks
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    
    #[test]
    fn test_removes_empty_work_section() {
        let filter = TemplateFilter::new();
        let content = r#"
# Daily Reflection

## Morning Check-in
Had a great morning!

## I. Work Responsibilities & Goals (Mon-Fri)
- Main Work Goal(s) for Today:
  -
- Key Work Tasks:
  - [ ]
  - [ ]
  - [ ]

## Real Content
This section has actual content worth indexing.
"#;
        
        let cleaned = filter.clean_content(content);
        assert!(!cleaned.contains("Work Responsibilities"));
        assert!(cleaned.contains("Had a great morning"));
        assert!(cleaned.contains("Real Content"));
    }
}