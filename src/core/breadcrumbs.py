def make_breadcrumbs(*parts):
    """Build breadcrumbs. Each part is (title, url); empty url = current page."""
    items = [{'title': 'Головна', 'url': '/'}]
    for title, url in parts:
        items.append({'title': title, 'url': url or ''})
    return items
