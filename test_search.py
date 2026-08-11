import requests
from bs4 import BeautifulSoup

def web_search(query):

    url = "https://html.duckduckgo.com/html/"

    headers = {
        "User-Agent": "Mozilla/5.0"
    }

    data = {
        "q": query
    }

    try:
        response = requests.post(
            url,
            headers=headers,
            data=data,
            timeout=10
        )

        soup = BeautifulSoup(response.text, "html.parser")

        results = []

        for item in soup.select(".result")[:5]:

            title = item.select_one(".result__title")
            snippet = item.select_one(".result__snippet")
            link = item.select_one(".result__url")

            results.append(
                f"Title: {title.get_text(' ', strip=True) if title else 'No title'}\n"
                f"Body: {snippet.get_text(' ', strip=True) if snippet else 'No description'}\n"
                f"URL: {link.get_text(' ', strip=True) if link else 'No URL'}"
            )

        return "\n\n".join(results)

    except Exception as e:
        return f"Search Error: {e}"

print(web_search("Latest AI news"))