#!/usr/bin/env python3
"""
Template Compiler for CO2 Monitor
Compiles .tpl files to _tpl.py files using utemplate
"""
import sys
from pathlib import Path
from utemplate.source import Compiler


def compile_template(tpl_path):
    """Compile a single template file"""
    try:
        # Determine output path
        output_path = tpl_path.with_name(tpl_path.stem + "_tpl.py")
        
        print(f"Compiling {tpl_path.name} -> {output_path.name}")
        
        # Compile template
        with open(tpl_path, 'r') as f_in, open(output_path, 'w') as f_out:
            compiler = Compiler(f_in, f_out)
            compiler.compile()
        
        return True
    except Exception as e:
        print(f"ERROR compiling {tpl_path.name}: {e}")
        return False


def main():
    """Compile all .tpl files in templates/ directory"""
    templates_dir = Path("templates")
    
    if not templates_dir.exists():
        print(f"ERROR: {templates_dir} directory not found")
        sys.exit(1)
    
    # Find all .tpl files
    tpl_files = list(templates_dir.glob("*.tpl"))
    
    if not tpl_files:
        print("No .tpl files found in templates/ directory")
        return
    
    print(f"Found {len(tpl_files)} template files to compile:")
    
    success_count = 0
    for tpl_file in sorted(tpl_files):
        if compile_template(tpl_file):
            success_count += 1
    
    print(f"\nCompilation complete: {success_count}/{len(tpl_files)} templates compiled successfully")
    
    if success_count != len(tpl_files):
        sys.exit(1)


if __name__ == "__main__":
    main()