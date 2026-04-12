from scraper import fetch_website_links, fetch_website_contents
import os
import json
from dotenv import load_dotenv
from IPython.display import display, Markdown
from openai import OpenAI


MODEL="gpt-4o-mini"


link_system_prompt = """
You are provided with a list of links found on a webpage.
You are able to decide which of the links would be most relevant to include in a brochure about the company,
such as links to an About page, or a Company page, or Careers/Jobs pages.
You should respond in JSON as in this example:

{
    "links": [
        {"type": "about page", "url": "https://full.url/goes/here/about"},
        {"type": "careers page", "url": "https://another.full.url/careers"}
    ]
}
"""


def get_links_user_prompt(url):
    user_prompt = f"""
Here is the list of links on the website {url} -
Please decide which of these are relevant web links for a brochure about the company, 
respond with the full https URL in JSON format.
Do not include Terms of Service, Privacy, email links.

Links (some might be relative links):

"""
    links = fetch_website_links(url)
    user_prompt += "\n".join(links)
    return user_prompt


def get_brochure_user_prompt(company_name, url):
    user_prompt = f"""
You are looking at a company called: {company_name}
Here are the contents of its landing page and other relevant pages;
use this information to build a short brochure of the company in markdown without code blocks.\n\n
"""
    user_prompt += fetch_page_and_all_relevant_links(url)
    user_prompt = user_prompt[:5_000] # Truncate if more than 5,000 characters
    return user_prompt


brochure_system_prompt = """
You are an assistant that analyzes the contents of several relevant pages from a company website
and creates a short brochure about the company for prospective customers, investors and recruits.
Respond in markdown without code blocks.
Include details of company culture, customers and careers/jobs if you have the information.
"""


def select_relevant_links(url):
    print(f"Selecting relevant links for {url} by calling Model {MODEL}...")
    openai_client = OpenAI()
    response = openai_client.chat.completions.create(
        model=MODEL,
        messages=[
            {"role": "system", "content": link_system_prompt},
            {"role": "user", "content": get_links_user_prompt(url)}
        ],
        response_format={"type": "json_object"}
    )
    result = response.choices[0].message.content
    links = json.loads(result)
    print(f"Selected {len(links['links'])} relevant links")
    return links

def fetch_page_and_all_relevant_links(url):
    print(f"Fetching brochure content for {url} by calling Model {MODEL}...")
    content = fetch_website_contents(url)
    links = select_relevant_links(url)
    result = f"## Landing page content\n\n{content}\n\n## Relevant links\n\n{links}"
    for link in links['links']:
        result += f"\n\n## {link['type']}\n\n{fetch_website_contents(link['url'])}"
    return result
   
def createBrochure(company_name, url):
    response = OpenAI().chat.completions.create(
        model=MODEL,
        messages=[
            {"role": "system", "content": brochure_system_prompt},
            {"role": "user", "content": get_brochure_user_prompt(company_name, url)}
        ],
    )
    brochure = response.choices[0].message.content
    print(brochure)
    
    file_name = f"{company_name.replace(' ', '_').lower()}_brochure.md"
    with open(file_name, "w") as f:
        f.write(brochure)
    print(f"\nBrochure saved to {file_name}")



   

def main():
    load_dotenv(override=True)
    print("Hello from website-brochure-app!")

    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise ValueError("OPENAI_API_KEY not found in environment variables")
    elif not api_key.startswith("sk-"):
        raise ValueError("OPENAI_API_KEY is not valid")
    else:
        print("OPENAI_API_KEY is valid")

    

   

    # links = fetch_website_links("https://www.google.com")
    # print(links)  

    # print(get_links_user_prompt("https://edwarddonner.com"))

    # json = select_relevant_links("https://edwarddonner.com")

    # print(json)

    # print(fetch_page_and_all_relevant_links("https://edwarddonner.com"))

    # print(get_brochure_user_prompt("HuggingFace", "https://huggingface.co"))


    createBrochure("spitertech", "https://www.spitertech.com")


    
    
    
    


if __name__ == "__main__":
    main()
