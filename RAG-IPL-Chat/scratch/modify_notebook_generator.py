import os

path = '/Users/rahulshinde/.gemini/antigravity-ide/brain/83e7608c-89cc-41c4-bde5-d25ad235e78c/scratch/create_notebook.py'
with open(path) as f:
    content = f.read()

target = '            "# Test chunking function on the opening match of IPL 2008 (335982.json)\\n",\n            "sample_file = \\"ipl-2008-2026/335982.json\\"\\n",\n            "sample_id = filepath_to_id[sample_file]\\n",'

replacement = '            "# Test chunking function on a sample match\\n",\n            "import os\\n",\n            "sample_file = f\\"{dataset_dir}/335982.json\\"\\n",\n            "if not os.path.exists(sample_file):\\n",\n            "    # Fallback to the first available match file\\n",\n            "    import glob\\n",\n            "    available_files = glob.glob(f\'{dataset_dir}/*.json\')\\n",\n            "    sample_file = available_files[0] if available_files else None\\n",\n            "\\n",\n            "sample_id = filepath_to_id[sample_file]\\n",'

if target in content:
    with open(path, 'w') as f:
        f.write(content.replace(target, replacement))
    print("Replaced successfully")
else:
    print("Target not found - might have already been replaced")
