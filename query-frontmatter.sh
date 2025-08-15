#!/bin/bash
# Query journal frontmatter with the Rust tool

# Get the directory where this script is located (project root)
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"

# Run from project root so journal directory is found
cd "$SCRIPT_DIR" && .tech/code/rust_scripts/frontmatter_query/target/release/frontmatter-query "$@"