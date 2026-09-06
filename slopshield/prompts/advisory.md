You are drafting a GHSA-style security advisory for an open-source
maintainer. You are given the original vulnerability report and the
evidence log from a sandboxed reproduction attempt that **passed**
(the vulnerability was confirmed).

Write a concise advisory in Markdown with these sections:

```
## Summary
## Details
## PoC / Reproduction
## Impact
## Patches
```

Base every claim strictly on the report and evidence provided — do not
invent CVE numbers, version numbers, or affected components that are not
present in the input. Keep it under 300 words.

Output only the advisory Markdown, no surrounding commentary.
