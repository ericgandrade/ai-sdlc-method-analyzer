# Licences

Handle each reference by its licence as recorded in `references/registry.yaml`: cite paths, describe mechanisms in our own words, and never paste text from a share-alike source. In addition, our own scorecards and analyses of public methods are our work and ship under the repository licence. They describe mechanisms in our own words.

**CC BY-SA scan.** `engine leakcheck --ccbysa` runs over `baseline/`, `docs/` and every shipped report, in CI and in the pre-push hook. It has two detectors:
- **Shingle detector.** A run of 12 or more consecutive words identical to any Agile V file is a hit. The 12-word threshold is the smallest that does not fire on common technical phrasing in the fixtures.
- **Quoted-span detector.** Any quoted span (`"…"`, `“…”`, or a Markdown blockquote) of **5 words or more**, inside a string or paragraph that cites `cache:agile-v/`, is a hit. Shorter verbatim fragments attributed to Agile V cannot pass silently.
