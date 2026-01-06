#!/usr/bin/env python3
"""
LLM-based VB to C#/Java Conversion Script
Handles sequential file processing with retry logic and validation.
"""

import os
import sys
import argparse
import json
import re
from datetime import datetime
from pathlib import Path
from typing import Optional, Tuple

import openai
from tenacity import retry, stop_after_attempt, wait_exponential


class ConversionEngine:
    def __init__(self, api_key: str, endpoint: str, model: str, max_retries: int):
        self.api_key = api_key
        self.endpoint = endpoint
        self.model = model
        self.max_retries = max_retries
        openai.api_key = api_key
        if endpoint:
            openai.api_base = endpoint
    
    def load_prompt_template(self, prompt_type: str) -> str:
        """Load prompt template from prompts/ directory."""
        prompt_path = Path(f"prompts/{prompt_type}.txt")
        if not prompt_path.exists():
            raise FileNotFoundError(f"Prompt template not found: {prompt_path}")
        return prompt_path.read_text(encoding='utf-8')
    
    def load_source_code(self, source_path: str) -> str:
        """Load VB source code."""
        return Path(source_path).read_text(encoding='utf-8')
    
    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
    def call_llm(self, prompt: str) -> str:
        """Call LLM API with retry logic."""
        try:
            response = openai.ChatCompletion.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": self.load_prompt_template("system_prompt")},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.2,
                max_tokens=4000
            )
            return response.choices[0].message.content
        except Exception as e:
            print(f"LLM API Error: {e}", file=sys.stderr)
            raise
    
    def extract_code_block(self, llm_output: str) -> str:
        """Extract code from markdown code blocks."""
        pattern = r'```(?:csharp|java|cs)?\n(.*?)```'
        matches = re.findall(pattern, llm_output, re.DOTALL)
        if not matches:
            # Fallback: assume entire output is code
            return llm_output.strip()
        return matches[0].strip()
    
    def inject_governance_header(self, code: str, source_file: str, target_lang: str) -> str:
        """Inject traceability headers into generated code."""
        run_id = os.getenv('GITHUB_RUN_ID', 'local')
        timestamp = datetime.utcnow().isoformat()
        
        comment_style = "//" if target_lang == "CSHARP" else "//"
        header = f"""{comment_style} AUTO-GENERATED CODE
{comment_style} Pipeline Run ID: {run_id}
{comment_style} Source File: {source_file}
{comment_style} Model: {self.model}
{comment_style} Generated: {timestamp}
{comment_style} WARNING: Review required before production use

"""
        return header + code
    
    def convert_file(self, source_path: str, target_lang: str) -> Tuple[bool, str]:
        """
        Convert a single VB file to target language.
        Returns: (success, generated_code)
        """
        try:
            # Load source code
            vb_code = self.load_source_code(source_path)
            
            # Assemble prompt
            task_prompt = self.load_prompt_template("task_prompt")
            full_prompt = task_prompt.replace("{{TARGET_LANG}}", target_lang)
            full_prompt = full_prompt.replace("{{SOURCE_CODE}}", vb_code)
            
            # Call LLM
            print(f"Calling LLM for {source_path}...")
            raw_output = self.call_llm(full_prompt)
            
            # Extract and process code
            generated_code = self.extract_code_block(raw_output)
            generated_code = self.inject_governance_header(generated_code, source_path, target_lang)
            
            return True, generated_code
        
        except Exception as e:
            print(f"Conversion failed for {source_path}: {e}", file=sys.stderr)
            return False, ""
    
    def save_generated_code(self, source_path: str, code: str, target_lang: str):
        """Save generated code to appropriate location."""
        source_file = Path(source_path)
        extension = ".cs" if target_lang == "CSHARP" else ".java"
        
        output_path = Path("src/generated") / source_file.stem
        output_path = output_path.with_suffix(extension)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        output_path.write_text(code, encoding='utf-8')
        print(f"Generated: {output_path}")


def main():
    parser = argparse.ArgumentParser(description="Convert VB code to C#/Java using LLM")
    parser.add_argument("--source", required=True, help="Path to VB source file")
    parser.add_argument("--target-lang", required=True, choices=["CSHARP", "JAVA"])
    parser.add_argument("--model", default="gpt-4-turbo")
    parser.add_argument("--max-retries", type=int, default=3)
    
    args = parser.parse_args()
    
    # Get credentials from environment
    api_key = os.getenv("LLM_API_KEY")
    endpoint = os.getenv("LLM_ENDPOINT", "")
    
    if not api_key:
        print("ERROR: LLM_API_KEY not set", file=sys.stderr)
        sys.exit(1)
    
    # Initialize engine
    engine = ConversionEngine(api_key, endpoint, args.model, args.max_retries)
    
    # Convert file
    success, code = engine.convert_file(args.source, args.target_lang)
    
    if success:
        engine.save_generated_code(args.source, code, args.target_lang)
        sys.exit(0)
    else:
        # Log failure
        log_dir = Path("logs")
        log_dir.mkdir(exist_ok=True)
        log_file = log_dir / f"failed_{Path(args.source).stem}.log"
        log_file.write_text(f"Conversion failed for {args.source}\n")
        sys.exit(1)


if __name__ == "__main__":
    main()
