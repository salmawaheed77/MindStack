import urllib.parse
import webbrowser

def open_website(payload):
    url = payload.get("url")
    if not isinstance(url, str):
        raise ValueError("A website URL is required.")
    parsed = urllib.parse.urlparse(url)
    if parsed.scheme not in ("http", "https") or not parsed.netloc:
        raise ValueError("Only valid http:// or https:// URLs are allowed.")
    opened = webbrowser.open(url)
    return {"success": bool(opened), "message": "Website opening requested." if opened else "Could not open the website."}

def google_search(payload):
    query = payload.get("query")
    if not isinstance(query, str) or not query.strip():
        raise ValueError("A search query is required.")
    url = "https://www.google.com/search?q=" + urllib.parse.quote_plus(query)
    opened = webbrowser.open(url)
    return {"success": bool(opened), "message": "Google search opened." if opened else "Could not open the browser."}
