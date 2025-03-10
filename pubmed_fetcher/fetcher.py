import requests
import csv
import re
from typing import List, Dict
from xml.etree import ElementTree as ET

class PubMedFetcher:
    def __init__(self, email: str):
        self.email = email
        self.base_url_search = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi"
        self.base_url_fetch = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi"

    def search(self, query: str, debug: bool = False) -> List[str]:
        """Fetch PubMed IDs based on query."""
        params = {
            "db": "pubmed",
            "term": query,
            "retmode": "json",
            "email": self.email,
            "retmax": 20,
        }
        response = requests.get(self.base_url_search, params=params)
        data = response.json()
        return data.get("esearchresult", {}).get("idlist", [])

    def fetch_details(self, pubmed_ids: List[str], debug: bool = False) -> List[Dict]:
        """Fetch paper details including title, date, affiliations, and emails."""
        if not pubmed_ids:
            return []

        params = {
            "db": "pubmed",
            "id": ",".join(pubmed_ids),
            "retmode": "xml",
            "email": self.email,
        }
        response = requests.get(self.base_url_fetch, params=params)
        if debug:
            print(response.text)

        root = ET.fromstring(response.text)
        papers = []
        
        for article in root.findall(".//PubmedArticle"):
            pmid = article.find(".//PMID").text
            title = article.find(".//ArticleTitle").text
            
            # Extract publication date
            pub_date_element = article.find(".//PubDate")
            if pub_date_element is not None:
                pub_date = " ".join([e.text for e in pub_date_element if e is not None])
            else:
                pub_date = "TBD"
            
            non_academic_authors = []
            company_affiliations = []
            corresponding_email = "TBD"

            # Extract author info
            for author in article.findall(".//Author"):
                last_name_element = author.find("LastName")
                last_name = last_name_element.text if last_name_element is not None else "Unknown"

                affiliation = author.find(".//Affiliation")
                if affiliation is not None:
                    aff_text = affiliation.text
                    if any(word in aff_text.lower() for word in ["pharma", "biotech", "inc", "ltd", "corporation"]):
                        company_affiliations.append(aff_text)
                        non_academic_authors.append(last_name)
                    
                    # Extract email using regex
                    email_match = re.search(r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}", aff_text)
                    if email_match:
                        corresponding_email = email_match.group(0)

            papers.append({
                "PubmedID": pmid,
                "Title": title,
                "Publication Date": pub_date,
                "Non-academic Author(s)": "; ".join(non_academic_authors) if non_academic_authors else "TBD",
                "Company Affiliation(s)": "; ".join(company_affiliations) if company_affiliations else "TBD",
                "Corresponding Author Email": corresponding_email,
            })

        return papers

    def save_to_csv(self, papers: List[Dict], filename: str):
        """Save paper details to a CSV file."""
        fieldnames = ["PubmedID", "Title", "Publication Date", "Non-academic Author(s)", "Company Affiliation(s)", "Corresponding Author Email"]
        with open(filename, mode="w", newline="", encoding="utf-8") as file:
            writer = csv.DictWriter(file, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(papers)
