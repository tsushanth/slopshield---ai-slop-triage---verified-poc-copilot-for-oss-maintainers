# Path traversal in /read endpoint allows reading files outside data/

**Component:** `app.py`, `read()` view function
**Endpoint:** `GET /read?file=`

## Summary

`read()` joins the user-controlled `file` parameter onto `DATA_DIR` with
`os.path.join` and opens the result, without checking that the resolved
path stays inside `DATA_DIR`:

```python
@app.route("/read")
def read():
    filename = request.args.get("file", "public.txt")
    path = os.path.join(DATA_DIR, filename)
    with open(path, "r") as f:
        return f.read()
```

`os.path.join(DATA_DIR, "../secret_admin.txt")` resolves to a path one
directory above `DATA_DIR`, so a `../` sequence in `file` escapes the
intended directory.

## Steps to reproduce

```
curl -G "http://TARGET_HOST/read" --data-urlencode 'file=../secret_admin.txt'
```

Expected (safe): 403/404, or the request is rejected because it resolves
outside `data/`.

Actual (vulnerable): the response body contains the contents of
`secret_admin.txt` from the app's install directory, one level above
`data/`.

## Impact

Any file readable by the app's process (config files, credentials,
source code) can potentially be exfiltrated via crafted `file` values.

## Suggested fix

Resolve the joined path with `os.path.realpath` and verify it is still
inside `DATA_DIR` before opening it (or use
`werkzeug.utils.safe_join`/`secure_filename`).
