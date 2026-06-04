import requests
from bs4 import BeautifulSoup

MAX_LENGTH = 8000


def web_fetch(params:dict):
    url = params.get("url")

    if not url:
        return "Error : no url is provided"
    

    try:
        
        # make actual request

        response = requests.get(url,timeout=10,headers={"User-Agent":"Mozilla/5.0"})

        # check if site is rechable
        if response.status_code !=200:
            return "Error : site is not reachable!!"

        # pass the response to beautifull soup

        soup = BeautifulSoup(response.text,"html.parser")

        # instead of soup.text
        for tag in soup(["script", "style", "nav", "footer", "header"]):
            tag.decompose()  # remove these entirely

        text = soup.get_text(separator="\n", strip=True)


        if len(text) > MAX_LENGTH:
            return text[:MAX_LENGTH] + f"\n\n[truncated — full page is {len(text)} chars]"
        return text


    except Exception as e:
        return f"Error fetchign web : '{str(e)}"
    
