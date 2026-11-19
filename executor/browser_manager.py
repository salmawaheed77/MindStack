"""Safe browser-opening helpers; no shell is involved."""

import urllib.parse
import webbrowser


def open_website(payload: dict) -> dict:
    url = payload.get("url")
    if not isinstance(url, str) or not url.strip():
        raise ValueError("A website URL is required.")
    if any(ord(char) < 32 for char in url) or any(char.isspace() for char in url):
        raise ValueError("The URL cannot contain whitespace or control characters.")
    parsed = urllib.parse.urlsplit(url.strip())
    if parsed.scheme.casefold() not in ("http", "https") or not parsed.hostname:
        raise ValueError("Only valid http:// or https:// URLs are allowed.")
    if parsed.username is not None or parsed.password is not None:
        raise ValueError("URLs containing embedded usernames or passwords are not allowed.")
    opened = webbrowser.open(url.strip(), new=2)
    return {"success": bool(opened), "message": "Website opening requested." if opened else "Could not open the website."}


def google_search(payload: dict) -> dict:
    query = payload.get("query")
    if not isinstance(query, str) or not query.strip():
        raise ValueError("A search query is required.")
    url = "https://www.google.com/search?" + urllib.parse.urlencode({"q": query.strip()})
    opened = webbrowser.open(url, new=2)
    return {"success": bool(opened), "message": "Google search opened." if opened else "Could not open the browser."}
