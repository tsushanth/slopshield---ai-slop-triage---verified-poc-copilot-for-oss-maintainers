# Reflected XSS in /greet endpoint

**Component:** `app.py`, `greet()` view function
**Endpoint:** `GET /greet?name=`

## Summary

The `name` query parameter is interpolated directly into the HTML response
via an f-string, with no escaping:

```python
@app.route("/greet")
def greet():
    name = request.args.get("name", "world")
    return f"<h1>Hello {name}</h1>"
```

Because the value isn't passed through `markupsafe.escape` or a Jinja
autoescaped template, any HTML/JS in `name` is reflected verbatim in the
response body.

## Steps to reproduce

```
curl -G "http://TARGET_HOST/greet" --data-urlencode 'name=<script>alert(1)</script>'
```

Expected (safe): the payload appears HTML-escaped in the response
(`&lt;script&gt;...`).

Actual (vulnerable): the response body contains the raw, unescaped
`<script>alert(1)</script>` tag, confirming reflected XSS.

## Impact

An attacker who can get a victim to click a crafted link to this endpoint
can execute arbitrary JavaScript in the victim's browser session.

## Suggested fix

Escape `name` before interpolating it into the response, e.g. via
`markupsafe.escape(name)`, or render through an autoescaping Jinja
template instead of an f-string.
