"""Print an Armenian sub-law (government or prime-minister decision, ministerial order), or one file of it, as it
stood on a date.

    python tools/in_force_on.py 2024-06-01 government/NNNN          # every file of a government decision on that day
    python tools/in_force_on.py 2024-06-01 government/NNNN title    # its title.md: title, preamble and enacting words
    python tools/in_force_on.py 2024-06-01 government/NNNN 3        # point 3 (or article 3 of an act with articles)
    python tools/in_force_on.py 2024-06-01 government/NNNN annex-1  # its first appendix

Reads the `In-force:` trailers (the real dates; commit dates before 1970 are clamped), so it is right for any day,
in any time zone. Only `main` is read: texts that apply after the build day are on the `future` branch.
Standard library only.
"""
import subprocess
import sys


def git(*args: str) -> str:
    return subprocess.run(['git', '-c', 'core.quotepath=off', *args], capture_output=True, text=True, encoding='utf-8',
                          check=True).stdout


def commit_on(day: str, path: str) -> str | None:
    """The last commit on or before `day` that touched `path`."""
    fmt = '%H%x1f%(trailers:key=In-force,valueonly,separator=)%x1f%(trailers:key=Consolidated,valueonly,separator=)'
    best = None
    for line in git('log', '--first-parent', f'--format={fmt}', 'main', '--', path).splitlines():
        h, inforce, consolidated = (line.split('\x1f') + ['', ''])[:3]
        d = (inforce or consolidated).strip()
        if d and d <= day:
            best = h
            break
    return best


def main() -> None:
    if len(sys.argv) < 3:
        sys.exit(__doc__)
    day, law = sys.argv[1], sys.argv[2].strip('/')
    unit = sys.argv[3] if len(sys.argv) > 3 else None
    path = f'{law}/{unit}.md' if unit else law
    h = commit_on(day, path)
    if not h:
        sys.exit(f'{path}: no text on or before {day} (the law was not yet in force, or the file did not exist then)')
    if unit:
        if not git('ls-tree', '--name-only', h, path).strip():
            sys.exit(f'{path}: not in the text in force on {day} (removed by the commit {h[:10]})')
        sys.stdout.write(git('show', f'{h}:{path}'))
        return
    names = git('ls-tree', '--name-only', h, f'{law}/').split()
    def order(n: str):
        stem = n.rsplit('/', 1)[-1][:-3]
        parts = [int(x) if x.isdigit() else 0 for x in stem.split('~')[0].split('.')] if stem[:1].isdigit() else []
        return (stem != 'title', not stem[:1].isdigit(), parts, stem)
    for n in sorted(names, key=order):
        sys.stdout.write(git('show', f'{h}:{n}') + '\n')


if __name__ == '__main__':
    main()
