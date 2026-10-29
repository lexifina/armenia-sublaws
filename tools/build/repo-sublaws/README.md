# Armenian sub-laws, change by change

The normative sub-laws of the Republic of Armenia as a git repository: {{GOVERNMENT}} government decisions, {{PRIME_MINISTER}} prime-minister decisions and {{MINISTERIAL}} ministerial orders from [ARLIS](https://www.arlis.am), the official legal information system of the Republic of Armenia. Each act is a folder, with one file per article, appendix and opening text, and one paragraph per line. Every change is a commit credited to the act that made it and dated the day the changed text took effect, at noon Yerevan time. The text is the Armenian original, which is the authoritative text.

This is the companion of [lexifina/armenia-law](https://github.com/lexifina/armenia-law), which holds the Constitution, the codes and the laws, built the same way by the same scripts.

On `main`, the record runs from {{FIRST}} to {{LAST}} in {{COMMITS}} commits, built from {{TEXTS}} texts: each act's original text plus every consolidated text ARLIS made of it. A further {{FUTURE_COMMITS}} commits apply after the build day and sit on the `future` branch.

## A lawyer's questions as git commands

| Question | Command |
| --- | --- |
| What did a government decision say on 1 June 2020? | `python tools/in_force_on.py 2020-06-01 government/{{EXAMPLE_ID}}` |
| Which act last changed each paragraph? | `git blame government/{{EXAMPLE_ID}}/title.md` |
| Every change to a decision, with the act behind it | `git log -p -- government/{{EXAMPLE_ID}}` |
| The words that changed, not whole paragraphs | `git log -p --word-diff -- government/{{EXAMPLE_ID}}` |
| Everything one act changed, across every sub-law | `git log --author='N 1530-Ն' --stat` |
| Every act that changed a decision, in order | `git log --format='%(trailers:key=In-force,valueonly,separator=) %an' -- government/{{EXAMPLE_ID}}` |
| What takes effect after today | `git log main..future` |
| The list of acts, with their ARLIS links | [`laws.csv`](laws.csv) |

Use `tools/in_force_on.py` for "on this date" questions rather than `git log --before`. It picks the text by the `In-force:` trailer, so it is right in any time zone and for dates before 1970. If you use raw git, write the time out in full: `git rev-list -1 --before="2020-06-01T23:59:59+04:00" main`.

Folders are `government/` (decisions of the Government, including the Council of Ministers before 1995), `prime-minister/` (decisions of the Prime Minister) and `ministerial/` (orders of a minister, alone or jointly with another minister or head of a state body). Each act's folder is named after its ARLIS number, the `N` in `arlis.am/hy/acts/N`. Most sub-laws are not divided into articles: a decision is a list of numbered points, often approving a procedure or a list in an appendix. The shared parser splits a text at articles, and at appendices once an article has begun. So an act without articles, which is most of them, is one file, `title.md`: title, preamble, points and appendices. An act with articles has one file per article (`4.md`), one per appendix (`annex-1.md`), and `title.md` for the text before the first article. Each line is one paragraph or one table row, so `git blame` still names the act behind each point. Each point's own history note, such as `(1-ին կետը փոփ. 12.03.15 N 245-Ն)`, is kept as a line, exactly as ARLIS prints it.

## Which acts

A sub-law is here when ARLIS types it as a decision, an order or a joint order, its number carries the suffix `-Ն`, and its issuer is the Government, the Prime Minister or a minister. The `-Ն` suffix is how Armenian law marks a normative act (Law on Normative Legal Acts, ՀՕ-180-Ն). Individual acts (`-Ա`, appointments, grants, property transfers) are left out, and so are acts that only amend others; those are the authors of commits here. Normative acts of other bodies (the Central Bank, regulators and commissions, regional and local bodies) and presidential decrees are not in this build. Acts older than the `-Ն` numbering have no marker of normative force on ARLIS, so they are not here either.

## The dates, and which one we use

ARLIS keeps every consolidated text it made of an act and gives each one its period of application, for example `Գործում է (01.09.2026-01.11.2026)`. **Commits are dated by the first day of that period.** That date decides which text governs a case, and it is the day the changes in that text took effect. The amending act's adoption date is in the `Enacted:` trailer. In {{RETROACTIVE}} commits, the text applies from a day before the act was adopted (retroactive effect). Those commits keep the in-force date and show the adoption date.

The first commit of each act is its original text (`Kind: original`), dated the day the act took effect. Where ARLIS never made a text for some amendment, the next commit can carry several amendments at once (see "what author means").

**Git cannot store dates before 1970.** None of these acts is that old, but the builder would commit any such act on 1970-01-01 with its real date in the `In-force:` trailer, as in lexifina/armenia-law.

**Texts that apply after the build day** are on the branch `future`, which starts at the tip of `main` and is never merged into it, so `main` never shows text that is not yet law. After a rebuild, run `git fetch --force origin future`.

## What "author" means

The author of a commit is the act that made the change, at an address that cannot exist, for example `N 1530-Ն (22.10.2026) <n-1530-n-20261022@arlis.invalid>`. The number is the act's official number and the date is its adoption date. So `git blame` names, for each paragraph, the act that last wrote it. One commit holds everything one act changed on one day, across every sub-law it touched.

ARLIS pairs every consolidated text with the one amending act it was made for, and that act is credited (`Evidence: edition`). Where the changed file's own history note newly names that act, the evidence is `note`. Where the note instead newly names another amending act of the same sub-law, one that has no consolidated text of its own, the change goes to the latest such act (`Evidence: note (no text of its own)`). Amending acts that ARLIS lists but never made a text for ({{NOT_INCORPORATED}}) are in [`data/not-incorporated.csv`](data/not-incorporated.csv). Their changes reach this record only through the next text that was made.

Evidence counts by changed file: note {{EVIDENCE_NOTE}}, edition {{EVIDENCE_EDITION}}, note with no text of its own {{EVIDENCE_CAUGHT_UP}}. In all there are {{ORIGINAL}} original acts and {{AMENDMENT}} amendment commits by {{AMENDING_ACTS}} amending acts.

Blame credits whole paragraphs. A paragraph changed by two acts names only the later one, so use `git log -p --word-diff` to see each act's words.

## What it does not show

- Laws, codes and the Constitution: see lexifina/armenia-law.
- The bodies and acts listed under "which acts" as not in this build.
- Texts ARLIS has not consolidated (see above), and texts it could not serve or we could not read ({{UNREADABLE}}, in [`data/unreadable.csv`](data/unreadable.csv)).
- Points and appendices of acts without articles are not files of their own; they are lines of `title.md`, because the parser (the same as lexifina/armenia-law's) splits texts at articles.
- ARLIS's links to case law, its tables of contents, and its translations.

ARLIS's consolidated texts are marked official or unofficial. This repository is a research aid and is not an official publication. For the authoritative text, see the official publication cited at the `Source:` link.

## How it is checked

- `scripts/global-law/check_corpus.py` passes: in-force order, ISO dates, `corpus.json`, `REPRODUCE.md`.
- An independent check, `tools/build/check_words.py`, compares a sample of texts letter by letter (letters and digits only) between ARLIS's raw page and the files in git, read without the parser.
- `tools/in_force_on.py` is compared with ARLIS's own text for several acts and dates.
- `main` has no merge commits, its commit dates never go backwards, and none of them is after the build day.
- Two builds from the same cache give the same commit hashes.

The sha256 of every downloaded text is in [`data/texts-sha256.tsv`](data/texts-sha256.tsv). See [`REPRODUCE.md`](REPRODUCE.md).

## How it is built

`tools/build/fetch.py --set sublaws` finds the sub-laws through ARLIS's search, leaving out acts that only amend others. It then reads each act's change history, which pairs amending acts with consolidated texts, and downloads the print view of the original act and of every consolidated text. `parse_text.py` splits each text into articles, appendices and paragraphs. `build.py` compares each act's texts in date order and credits each change as above. It writes the whole history with one `git fast-import`. These are the same scripts, with the same parser version, that build lexifina/armenia-law. No AI model reads or writes any text, either in the build or in the checks.

## Licence

Source: ARLIS, the legal information system of the Republic of Armenia (www.arlis.am). Under article 4(1)(c) of the Law of the Republic of Armenia on Copyright and Related Rights (ՀՕ-142-Ն, 2006), official documents, including legal acts and their official translations, are not objects of copyright. The texts here were split into files and arranged as commits; their wording was not changed. Lexifina's own contributions (the tools, the arrangement and the commit messages) are CC0. See [`LICENSE`](LICENSE).
