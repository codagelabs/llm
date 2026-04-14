# Website Brochure App

An AI-powered tool that automatically generates a professional markdown brochure for a company by scraping its website and intelligently extracting relevant information.

## Overview

The Website Brochure App visits a company's URL, extracts the landing page content, and uses an LLM (OpenAI's `gpt-4o-mini`) to dynamically identify additional relevant links (like "About Us", "Careers", "Culture", etc.). It then fetches the content from all of these pages and synthesizes a comprehensive, easy-to-read markdown brochure document.

## Features

- **Intelligent Link Selection:** Uses AI to determine which sub-pages are most relevant for a company brochure.
- **Deep Scraping:** Fetches content from the landing page and all selected sub-pages.
- **Dynamic Content Generation:** Synthesizes the scraped data to produce a coherent summary outlining the company's culture, offerings, and open positions.
- **Markdown Export:** Automatically outputs and saves the generated brochure as a local `.md` file (e.g. `companyname_brochure.md`).

## Requirements

The project uses `uv` for dependency management. 

- Python 3.12+
- `uv` package manager

## Setup and Installation

1. **Clone the repository and enter the directory**:
   ```bash
   cd website-brochure-app
   ```

2. **Configure your Environment**:
   Create a `.env` file in the root directory and add your OpenAI API Key:
   ```env
   OPENAI_API_KEY=sk-your-openai-api-key-here
   ```

3. **Install Dependencies and Run**:
   You can easily execute the app directly, and `uv` will handle injecting the dependencies:
   ```bash
   uv run main.py
   ```

## Usage

By default, the script is configured to run against a specific company in `main.py`. You can change the target by editing the `createBrochure(company_name, url)` call at the bottom of `main.py`:

```python
# In main.py
createBrochure("Company Name", "https://example-company-url.com")
```

When you run the script, you'll see console output of exactly which links are being targeted, and upon completion, a new file (e.g., `company_name_brochure.md`) will appear in your project working directory.
