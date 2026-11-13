# Reproducing this repository

Everything in this history comes from ARLIS (www.arlis.am) and can be rebuilt from it. The same downloaded texts give the same commit hashes.

## What this build used

- Retrieved on 2026-10-29: 13162 sub-laws (9760 government decisions, 136 prime-minister decisions, 3266 ministerial orders) and 36012 texts (original acts plus consolidated texts).
- Requests: the search pages (5 act types × 6 orderings, 10 results a page), 13162 act pages and 36012 print views.
- 31586 commits on `main`: 13146 original acts, 18439 amendments and this documentation commit. A further 19 are on `future`.
- The sha256 of every downloaded text (gzip of the HTML as served) is in `data/texts-sha256.tsv`; the sha256 of that list is d784e9e53fdf010722f57143c6ea8f1fa5620cbeab462a784de281ea105d3f46.
- Build scripts, copied to `tools/build/`, with their sha256:
  - `corpus_set.py` a9111e573022e2576ad722e7d23554fb14d71df05ddd0c27f5bb3ec284619f16
  - `fetch.py` 21f9fbe0f73d677cd08b3c3585c4032ade4671d487ed94df0725e8ad032de40d
  - `parse_text.py` 33b4679fd442b0209dd94fe39b4d95fa75afb08241efbf85323abcc6fad14e55
  - `build.py` a70fd4feb11e70998fc9cf1f78f62a156d25a9e0fe468434eb50cc48acfdbe1f
  - `docs.py` 6ee814ae12a0dc267f41525c55eef69eea7d9fdc553e0ca77a8dcfd26e928823
  - `check_words.py` 5a7b4f92c256b82d3b2db29679c3dec64dc3a5a236e71df1d18c2c6ed19d62c3
- Tools: Python 3.12.10 with lxml 6.1.3; git version 2.46.0.windows.1; curl 8.21.0 (Windows) libcurl/8.21.0 Schannel zlib/1.3.2 WinIDN WinLDAP.

## Fetch rate


## Steps

```sh
cd tools/build
python fetch.py catalogue --set sublaws   # .cache-sublaws/catalogue.json: search for types 8, 11, 31, 44, 47, number `Ն`
python fetch.py laws --set sublaws        # .cache-sublaws/laws/<id>.json: each act's change history
python fetch.py texts --set sublaws       # .cache-sublaws/text/<id>.html.gz: print view of every original and consolidated text
python build.py ../../../armenia-sublaws-rebuilt --set sublaws --today 2026-10-29
python check_words.py ../../../armenia-sublaws-rebuilt --set sublaws --sample 2000
```

Without `--set sublaws` the same scripts build lexifina/armenia-law.

`--today` is the cache's retrieval day. It is required: it dates the documentation commit and divides `main` from `future`, so a rebuild never depends on the day it is run. The builder refuses to build into a directory that holds anything except an earlier build. On a rebuild it keeps the `origin` remote.

ARLIS adds texts as acts change, so a later fetch gives a longer history. To rebuild this exact history, use texts whose sha256 match `data/texts-sha256.tsv`.

## Decisions

- **Which acts:** ARLIS search, act types 8 (decision), 11 (order), 31 (joint order), 44 and 47 (joint order-decision), with "exclude changing acts" and the number field `Ն`. Of the results, an act is kept when its number ends in `Ն` (normative) and its title names the Government (or the Council of Ministers), the Prime Minister, or a minister issuing an order. Everything the searches returned is kept in the cache as `search-all.json`. ARLIS's paging is not stable when sort keys tie, so six orderings are paged and their results combined.
- **Which texts:** the act's original text (`/hy/acts/<id>`), plus every text on the "Ինկորպորացիա" side of its change history.
- **Dates:** a consolidated text's in-force date is the start of the period in its status line. The original act's is its "Ուժի մեջ մտնելու ամսաթիվ" (date of entry into force). Commits are dated noon at +0400. Texts dated after `--today` go on `future`.
- **Units:** parser version 5: lexifina/armenia-law's parser (version 4, unchanged), plus `split_points` for sub-laws. An article starts at "Հոդված N.". In an act without articles (most decisions and orders), `title.md` runs to the enacting words ("... որոշում է.", "Հրամայում եմ."); then each line starting `N.` that continues the sequence 1, 2, 3 ... before the signature row starts point file `N.md`, and each line starting "Հավելված" (optionally `N 1`) starts an appendix file `annex-N.md`. Without enacting words, the points start at the first `1.`. Each <P> is one line. ARLIS's ⚖ case-law links are dropped.
- **Normalised away:** whitespace (a text that differs only in whitespace is not a change), curly quotes and soft hyphens.
- **Language guard:** a text that is less than half Armenian letters is skipped and listed in `data/unreadable.csv`.
- **Crediting:** see the README. Notes cite sub-laws by bare number (`12.03.15 N 245-Ն`), so numbers are compared without their `N` or `թիվ` prefix. Changes no act explains would be `Kind: unexplained`. ARLIS pairs every text with an act, so there are 0 of them.
- **Order:** by in-force date. On one date, original acts come first, then amendments by ARLIS act id.

## What AI did

This repository was built by Claude Code with Claude Opus 5.5 (`claude-opus-5-5`), which wrote the scripts and this documentation. No AI model reads, writes, summarises or classifies any legal text, either at data-build time or at git-build time. Commit messages are generated by code from ARLIS's metadata.
