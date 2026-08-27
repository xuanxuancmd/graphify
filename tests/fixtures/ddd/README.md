# DDD Fixtures

This directory contains DDD-style markdown documents used by
`tests/test_ddd_extractor.py`. Each file exercises one branch of the
DDD extractor whitelist:

- `context-map.md` — BC table + business-relationship table + glossary table
- `technical-constraints.md` — TC headings + code-anchor prefixes + scope prefixes
- `order-business-flow.md` — tagged table (`business-flow` keyword)
- `order-invariants.md` — tagged table (`invariants` keyword)
- `order-contracts.md` — tagged table (`contracts` keyword)
- `order-domain-events.md` — tagged table (`domain-events` keyword)
- `order-domain-model.md` — tagged table (`domain-model` keyword)
- `README.md` — non-whitelist file, should fall back to default `extract_markdown`

This README itself is a non-whitelist `.md` file: its filename contains none
of the DDD keywords, so the DDD extractor returns `None` and the default
markdown extractor produces `page` + `heading` nodes only.
