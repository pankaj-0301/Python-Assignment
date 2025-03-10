import typer
from pubmed_fetcher.fetcher import PubMedFetcher

app = typer.Typer()

@app.command()
def fetch_papers(query: str, email: str, file: str = "output.csv", debug: bool = False):
    """
    Fetch research papers from PubMed and save to CSV.
    """
    fetcher = PubMedFetcher(email)
    pubmed_ids = fetcher.search(query, debug)
    papers = fetcher.fetch_details(pubmed_ids, debug)
    fetcher.save_to_csv(papers, file)
    typer.echo(f"Results saved to {file}")

if __name__ == "__main__":
    app()
