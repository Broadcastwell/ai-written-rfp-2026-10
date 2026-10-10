# The AI Written RFP

Prepared by the Broadcastwell team

Team review: in progress. Zero criteria are analyst verified.

The study records requirements stated before a named vendor in the frozen September answers, then links explicit vendor associations and dated public page comparisons. The published data covers fourteen categories, 2,093 included source answers, 2,003 category criteria, 10,547 supporting answer spans, 2,417 explicit vendor association passages and 10,015 page comparisons.

Answers captured under method v1.1 on 22 to 23 Sep 2026 for the Absence Index release 2026-09 (DOI 10.5281/zenodo.22907695).

Study DOI: [10.5281/zenodo.23271935](https://doi.org/10.5281/zenodo.23271935). [All versions](https://doi.org/10.5281/zenodo.23271934).

This metadata update adds the minted study DOI to the report, citation and joined data. The original deposit remains the dated release of record. Every observation table and research figure is unchanged.

## Read the findings

[Complete report](Study7_The_AI_Written_RFP.pdf) and [accessible report text](Study7_The_AI_Written_RFP.md).

The report shows ten frequent criteria per category and every mapped vendor page summary. The complete observation tables accompany it. A statement not found on a dated page is not a missing product feature; unsuitable or partial scope remains unknown.

## Complete data

| File | Contents |
|---|---|
| [Joined data](data/study7-index.json) | All tables, provenance, methods, review state and medians in schema study7-index-2 |
| [Source records](data/records.csv) | Every scheduled category record, actual capture attribution, inclusion status, boundary and answer hash |
| [Criteria](data/criteria.csv) | Every canonical criterion, exact count and base, Wilson interval, repeated runs, source references and vendor associations |
| [Evidence](data/evidence.csv) | Every supporting answer span with engine, question, run, date, exact character offsets and hashes |
| [Vendor associations](data/adjacency.csv) | Explicit associations in the same complete source answer, with precise evidence pointers |
| [Dated page comparisons](data/vendor_pages.csv) | Every scoped vendor and criterion comparison, page URL, date, snapshot hash and quoted evidence where stated |
| [Vendor summaries](data/vendor_summaries.csv) | Page state figures with count and base, interval and category median |

## Reproduce and review

The [original source deposit](https://doi.org/10.5281/zenodo.22907695) contains the actual frozen answers and Index release. The public verifier recomputes counts, intervals and medians from the released data and supports exact answer hash and offset checks against that deposited source. Record identifiers are derived from the original category, question, engine and run fields. Offsets count Unicode characters, while hashes use UTF8 text.

No Perplexity answer quotation text is redistributed here. Its source pointers and exact hashes remain in the data, so the original deposited answer can be checked without a rewritten quote or an invented sharing link. Research completion hashes are recorded in [research provenance](research-provenance.json). Every criterion retains Team review: in progress until authentic analyst decisions are validated against its evidence fingerprint.

Run the independent check with Python 3:

```text
python verify_publication.py data/study7-index.json
```

For exact source verification, download [the deposited answers](https://zenodo.org/api/records/22907695/files/answers-2026-09.jsonl/content) and [the deposited Index release](https://zenodo.org/api/records/22907695/files/release-2026-09.json/content), then supply their local file names:

```text
python verify_publication.py data/study7-index.json --answers-source answers-2026-09.jsonl --release-source release-2026-09.json
```

The integrity manifest lists the byte length and SHA256 of every release file except the manifest itself. Git line ending conversion is disabled so the repository archive preserves these bytes.

## Product and corrections

Checklist Audit $490. [Every figure comes from the published method, v1.1.](https://broadcastwell.com/methodology)

Any named company may request one no-cost re-run at index@broadcastwell.com; both results are published.

CC BY 4.0. Source material remains attributable to its original source.
