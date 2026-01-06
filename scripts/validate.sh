#!/bin/bash
# Pre-commit validation script for generated code
# Performs basic syntax and structural checks

set -e

GENERATED_DIR="src/generated"
EXIT_CODE=0

echo "=== Starting Validation ==="

# Check if generated directory exists
if [ ! -d "$GENERATED_DIR" ]; then
    echo "No generated code found. Skipping validation."
    exit 0
fi

# Validate C# files
if ls $GENERATED_DIR/*.cs 1> /dev/null 2>&1; then
    echo "Validating C# files..."
    for file in $GENERATED_DIR/*.cs; do
        echo "Checking: $file"
        
        # Check for balanced braces
        OPEN=$(grep -o '{' "$file" | wc -l)
        CLOSE=$(grep -o '}' "$file" | wc -l)
        
        if [ "$OPEN" -ne "$CLOSE" ]; then
            echo "ERROR: Unbalanced braces in $file"
            EXIT_CODE=1
        fi
        
        # Check for class declaration
        if ! grep -q "class " "$file"; then
            echo "WARNING: No class declaration found in $file"
        fi
        
        # Check for governance header
        if ! grep -q "AUTO-GENERATED CODE" "$file"; then
            echo "ERROR: Missing governance header in $file"
            EXIT_CODE=1
        fi
    done
fi

# Validate Java files
if ls $GENERATED_DIR/*.java 1> /dev/null 2>&1; then
    echo "Validating Java files..."
    for file in $GENERATED_DIR/*.java; do
        echo "Checking: $file"
        
        # Check for balanced braces
        OPEN=$(grep -o '{' "$file" | wc -l)
        CLOSE=$(grep -o '}' "$file" | wc -l)
        
        if [ "$OPEN" -ne "$CLOSE" ]; then
            echo "ERROR: Unbalanced braces in $file"
            EXIT_CODE=1
        fi
        
        # Check for class declaration
        if ! grep -q "class " "$file"; then
            echo "WARNING: No class declaration found in $file"
        fi
        
        # Check for governance header
        if ! grep -q "AUTO-GENERATED CODE" "$file"; then
            echo "ERROR: Missing governance header in $file"
            EXIT_CODE=1
        fi
    done
fi

if [ $EXIT_CODE -eq 0 ]; then
    echo "=== Validation Passed ==="
else
    echo "=== Validation Failed ==="
fi

exit $EXIT_CODE
