# PyHX Framework Documentation

PyHX is an independent, lightweight Python web framework. It provides a declarative way to build web applications using [FastAPI](https://fastapi.tiangolo.com/) and [htpy](https://htpy.dev/) (a Pythonic HTML templating library) and [HTMX](https://htmx.org/).

The goal of PyHX is to enable developers to develop professional, enterprise-grade web applications with the ease of Streamlit apps.

## Quick Example

```python
# src/app/_02_webapp/main.py
import pyhx.app as hx

hx.set_app_title("My Application")
hx.set_layout("shell")

home = hx.add_page(source="home", title="Home", path="/")
about = hx.add_page(source="about", title="About", path="/about")

hx.add_nav_items("Main")[home, about]
```

```python
# src/app/_02_webapp/pages/home.py
import pyhx.page as hx
from htpy import h1, p

hx.html(
    h1["Welcome to My Application"],
    p["This is the home page."]
)
```

```python
# main.py
from pyhx as hx
app = hx.init()
```

Start the app with `fastapi dev main.py`.