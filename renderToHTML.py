#!/usr/bin/env python3
"""Render psalter.xml to a plain HTML psalter.

Usage: python3 renderToHTML.py [--only VERSION] psalter.xml > psalter.html
Output is core semantic HTML only: no styles, no scripts. Each psalm
shows every version in sequence, with editorial notes at its foot;
--only restricts output to a single version (e.g. bcp1928 or modern).
"""
import argparse
import sys
import html
import xml.etree.ElementTree as ET

NOTE_SIGILS = ["†", "‡", "§", "‖", "¶"]  # † ‡ § ‖ ¶


def esc(s):
    return html.escape(s or "", quote=False)


def text_html(el):
    """Serialize a mixed-content text element. dn (tetragrammaton)
    renders per the traditional convention: LORD, all caps."""
    parts = [esc(el.text)]
    for child in el:
        inner = "".join(child.itertext())
        parts.append(esc(inner.upper() if child.tag == "dn" else inner))
        parts.append(esc(child.tail))
    return "".join(parts)


def render(path, only=None):
    tree = ET.parse(path)
    root = tree.getroot()
    meta = root.find("meta")
    title = meta.findtext("title", "The Psalter")
    versions = [
        (v.get("id"), v.findtext("name", v.get("id")))
        for v in meta.find("versions").findall("version")
    ]
    if only is not None:
        declared = ", ".join(vid for vid, _ in versions)
        versions = [(vid, name) for vid, name in versions if vid == only]
        if not versions:
            sys.exit(f"error: unknown version '{only}' (declared: {declared})")
    vids = [vid for vid, _ in versions]

    psalms_html = []
    nav_html = []
    for psalm in root.findall("psalm"):
        n = psalm.get("n")
        incipit = psalm.find("incipit")
        latin = incipit.get("latin") if incipit is not None else ""
        nav_html.append(f'<a href="#ps{n}">{n}</a>')

        verses_by_version = {vid: [] for vid in vids}
        notes = []

        for verse in psalm.iter("verse"):
            vn = verse.get("n")
            halves = verse.findall("half")
            vnotes = verse.findall("note")
            sigil_refs = ""
            for note in vnotes:
                nv = note.get("version")
                if nv and nv not in vids:
                    continue
                sig = NOTE_SIGILS[len(notes) % len(NOTE_SIGILS)]
                notes.append((sig, note.get("type", ""), note.text or ""))
                sigil_refs += f"<sup>{sig}</sup>"

            for vid in vids:
                parts = []
                for half in halves:
                    for t in half.findall("text"):
                        if t.get("version") == vid:
                            parts.append(text_html(t))
                joined = " * ".join(parts)
                verses_by_version[vid].append(
                    f"<p><sup>{vn}</sup> {joined}{sigil_refs}</p>"
                )

        body = []
        for vid, name in versions:
            if len(versions) > 1:
                body.append(f"<h3>{esc(name)}</h3>")
            body.extend(verses_by_version[vid])

        notes_html = ""
        if notes:
            items = "\n".join(
                f"<p><small>{sig} <i>{esc(t)}</i> {esc(txt)}</small></p>"
                for sig, t, txt in notes
            )
            notes_html = f"<footer>\n{items}\n</footer>\n"

        heading = f"Psalm {n}"
        if latin:
            heading += f" — <i>{esc(latin)}</i>"
        psalms_html.append(
            f'<section id="ps{n}">\n'
            f"<h2>{heading}</h2>\n"
            + "\n".join(body)
            + f"\n{notes_html}</section>"
        )

    subtitle = "pointed for chanting or reciting"
    if len(versions) == 1:
        subtitle = f"{esc(versions[0][1])} — {subtitle}"
    return HTML_TEMPLATE.format(
        title=esc(title),
        subtitle=subtitle,
        nav=" ".join(nav_html),
        psalms="\n".join(psalms_html),
    )


HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<title>{title}</title>
</head>
<body>
<h1>{title}</h1>
<p>{subtitle}</p>
<nav aria-label="Psalms">{nav}</nav>
{psalms}
</body>
</html>
"""

if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("source", nargs="?", default="psalter.xml",
                    help="psalter XML file (default: psalter.xml)")
    ap.add_argument("--only", metavar="VERSION",
                    help="render only this version id (e.g. bcp1928, modern)")
    args = ap.parse_args()
    sys.stdout.write(render(args.source, only=args.only))
