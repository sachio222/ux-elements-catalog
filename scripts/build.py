#!/usr/bin/env python3
"""Build a UX elements catalog from elements.json (ux-elements-catalog skill).

Writes UX-ELEMENTS-CATALOG.md (the record) and UX-ELEMENTS-CATALOG.html (the
reading page, self-contained, fonts embedded) into the folder that holds
elements.json:

    python3 <skill-folder>/scripts/build.py <catalog-folder>

The folder defaults to the current directory. Start from
templates/starter.elements.json.

meta options: product (header, title, frontmatter), file (record path in
frontmatter), owner (who makes the open decisions, default "the product
owner"), mode ("plan" refuses a catalog with gaps; "discover" builds and
lists them as gaps found in the app), top_terms (terms shown at the top,
default the first six), no_dashes (refuse em and en dashes in the data,
default false).

Data keys per element: id, el (element), label, lab (source | proposed | app),
type, sub (content subtype), does, then (what happens), event, state
(exists | missing | build | fakedoor | later | outside), src, rep (repeat of
another element), kit (UI kit part), path (happy | unhappy), trigger,
wayout (way-out element IDs). Pages may list shells (global group names).
Stories carry a needs chain: steps {d (depth), to, need, els, why}.
The Serves column is computed from the chains. Missing optional keys take
defaults; missing required keys are reported by ID before anything is built.
"""
import base64
import html
import json
import re
import sys
from collections import Counter, OrderedDict
from datetime import date
from pathlib import Path

HERE = Path(sys.argv[1]).resolve() if len(sys.argv) > 1 else Path.cwd()
FONTS = Path(__file__).resolve().parent.parent / "assets" / "fonts"
SOURCE_FILE = HERE / "elements.json"
if not SOURCE_FILE.exists():
    print(f"No elements.json in {HERE}. Copy templates/starter.elements.json there to begin.")
    sys.exit(1)
DATA = json.loads(SOURCE_FILE.read_text())

TYPE_ORDER = ["primary", "secondary", "tertiary", "navigation", "input", "calculator",
              "result", "component", "form", "link", "content", "error", "wayout"]
TYPE_LABEL = {"primary": "Primary CTA", "secondary": "Secondary CTA", "tertiary": "Tertiary CTA",
              "navigation": "Navigation", "input": "Input", "calculator": "Calculator",
              "result": "Result", "component": "Component", "form": "Form", "link": "Link",
              "content": "Content", "error": "Error state", "wayout": "Way out"}
STATE_ORDER = ["exists", "missing", "build", "fakedoor", "later"]
STATE_LABEL = {"exists": "Exists in app", "missing": "Missing in app", "build": "To build", "fakedoor": "Fake door",
               "later": "Later", "outside": "Outside this site"}
ACTION_TYPES = {"primary", "secondary", "tertiary", "form", "link", "calculator", "input", "wayout"}
PATH_LABEL = {"happy": "Happy", "unhappy": "Unhappy"}
WAYS = [("back", "Can they go back?"), ("cancel", "Can they cancel?"), ("undo", "Can they undo?"),
        ("help", "Can they get help?"), ("keep", "Can they leave and keep their work?")]
INPUT_TYPES = {"input", "form", "calculator"}


def path_of(e):
    return e.get("path", "happy")


# ---------------------------------------------------------------- defaults
def need(obj, keys, where, out):
    for k in keys:
        if k not in obj:
            out.append(f"{where}: missing '{k}'")


def fill(obj, defaults):
    for k, v in defaults.items():
        obj.setdefault(k, v)


def check_story(s, where, out):
    need(s, ("id", "story"), where, out)
    fill(s, {"src": "", "chain": []})
    for i, st in enumerate(s["chain"]):
        need(st, ("to", "need"), f"{s.get('id', where)} step {i + 1}", out)
        st.setdefault("els", [])


def check_element(e, where, out):
    eid = e.get("id", where)
    need(e, ("id", "el", "type"), eid, out)
    fill(e, {"label": e.get("el", ""), "lab": "source", "does": "", "then": "", "event": "none",
             "state": "build", "src": ""})
    if e["lab"] not in ("source", "proposed", "app"):
        out.append(f"{eid}: lab '{e['lab']}' is not source, proposed or app")
    if e.get("type") and e["type"] not in TYPE_LABEL:
        out.append(f"{eid}: type '{e['type']}' is not one of {', '.join(TYPE_ORDER)}")
    if e["state"] not in STATE_LABEL:
        out.append(f"{eid}: state '{e['state']}' is not one of {', '.join(STATE_LABEL)}")
    if path_of(e) not in PATH_LABEL:
        out.append(f"{eid}: path '{path_of(e)}' is not happy or unhappy")


def normalize(d):
    """Fill optional keys with defaults; return missing required keys by ID."""
    out = []
    m = d.setdefault("meta", {})
    fill(m, {"product": "Product", "file": "UX-ELEMENTS-CATALOG", "updated": date.today().isoformat(),
             "status": "", "purpose": "", "main_message": "", "reading": "", "tracking_note": "",
             "owner": "the product owner", "mode": "plan", "top_terms": None, "no_dashes": False})
    if m["mode"] not in ("plan", "discover"):
        out.append(f"meta.mode '{m['mode']}' is not plan or discover")
    m.setdefault("title", f"{m['product']} UX elements catalog")
    for k in ("terms", "sources", "source_events", "sitemap", "index", "open_questions", "pages"):
        d.setdefault(k, [])
    g = d.setdefault("global", {})
    fill(g, {"groups": [], "elements": [], "stories": []})
    if not d["pages"]:
        out.append("pages: none listed; a catalog needs at least one page")
    for e in g["elements"]:
        check_element(e, "global element", out)
    for s in g["stories"]:
        check_story(s, "global story", out)
    for gr in g["groups"]:
        need(gr, ("name", "ids"), "global group", out)
    for i, p in enumerate(d["pages"]):
        where = p.get("id", f"page {i + 1}")
        need(p, ("id", "name", "primary"), where, out)
        fill(p, {"path": "", "group": "Pages", "audience": "", "job": "", "state": "build", "when": "",
                 "stories": [], "elements": [], "notes": "", "shells": []})
        for sh in p["shells"]:
            if sh not in [gr.get("name") for gr in g["groups"]]:
                out.append(f"{where}: shell '{sh}' is not a global group name")
        for s in p["stories"]:
            check_story(s, f"{where} story", out)
        for e in p["elements"]:
            check_element(e, f"{where} element", out)
        for k, _ in WAYS:
            if "ways_out" in p:
                if k not in p["ways_out"]:
                    out.append(f"{where}: ways_out missing '{k}'")
                else:
                    need(p["ways_out"][k], ("v",), f"{where} ways_out {k}", out)
                    fill(p["ways_out"][k], {"els": [], "note": ""})
                    if p["ways_out"][k].get("v") not in ("yes", "no", "n/a"):
                        out.append(f"{where}: ways_out {k} is '{p['ways_out'][k].get('v')}', not yes, no or n/a")
    for gr in d["sitemap"]:
        need(gr, ("group",), "sitemap group", out)
        gr.setdefault("pages", [])
        for pg in gr["pages"]:
            need(pg, ("name",), f"sitemap {gr.get('group', '')}", out)
            fill(pg, {"path": "", "page": None, "depth": 0, "audience": "", "job": "", "state": "build", "when": "", "note": ""})
            if pg["state"] not in STATE_LABEL:
                out.append(f"sitemap {pg.get('name', '')}: state '{pg['state']}' is not one of {', '.join(STATE_LABEL)}")
            if pg["page"] is not None and pg["page"] not in [p.get("id") for p in d["pages"]]:
                out.append(f"sitemap {pg.get('name', '')}: page '{pg['page']}' is not a page id (use null for a page without a table)")
    for gr in d["index"]:
        need(gr, ("intent",), "index", out)
        gr.setdefault("goals", [])
        for gg in gr["goals"]:
            need(gg, ("text",), f"index {gr.get('intent', '')}", out)
            gg.setdefault("stories", [])
    for i, q in enumerate(d["open_questions"]):
        fill(q, {"id": f"Q{i + 1}", "topic": "", "q": "", "status": "open", "recommended": "",
                 "default": "", "reason": "", "answer": "", "src": "", "pages": []})
        if q["status"] not in ("open", "default", "decided"):
            out.append(f"{q['id']}: status '{q['status']}' is not open, default or decided")
        for pid in q["pages"]:
            if pid != "GLOBAL" and pid not in [p.get("id") for p in d["pages"]]:
                out.append(f"{q['id']}: page '{pid}' is not a page id or GLOBAL")
    return out


missing = normalize(DATA)
if missing:
    print("Data problems:\n  " + "\n  ".join(missing))
    sys.exit(1)
PRODUCT = DATA["meta"]["product"]
RECORD = DATA["meta"]["file"]
OWNER = DATA["meta"]["owner"]
SOURCE_EVENTS = set(DATA["source_events"])

esc = html.escape


# ---------------------------------------------------------------- checks
DUPES = []


def all_elements():
    out = OrderedDict()
    pairs = [("GLOBAL", e) for e in DATA["global"]["elements"]] + [(p["id"], e) for p in DATA["pages"] for e in p["elements"]]
    for pid, e in pairs:
        if e["id"] in out:
            DUPES.append(f"{e['id']}: element ID used twice")
        out[e["id"]] = (pid, e)
    return out


ELEMS = all_elements()
STORIES = OrderedDict()
for pid, s in [("GLOBAL", s) for s in DATA["global"]["stories"]] + [(p["id"], s) for p in DATA["pages"] for s in p["stories"]]:
    if s["id"] in STORIES:
        DUPES.append(f"{s['id']}: story ID used twice")
    STORIES[s["id"]] = (pid, s)

SERVES = {k: [] for k in ELEMS}
for sid, (_, s) in STORIES.items():
    for st in s["chain"]:
        for eid in st["els"]:
            if sid not in SERVES.setdefault(eid, []):
                SERVES[eid].append(sid)

DISCOVER = DATA["meta"]["mode"] == "discover"
problems = list(DUPES)
GAPS = []  # rule breaks that, when cataloging an existing app, are gaps in the app itself


def page_label(e):
    pid = ELEMS[e["id"]][0]
    return "global" if pid == "GLOBAL" else next(p["name"] for p in DATA["pages"] if p["id"] == pid)


def gap(msg):
    (GAPS if DISCOVER else problems).append(msg)


for sid, (_, s) in STORIES.items():
    for st in s["chain"]:
        for eid in st["els"]:
            if eid not in ELEMS:
                problems.append(f"{sid} names missing element {eid}")
for gr in DATA["global"]["groups"]:
    for i in gr["ids"]:
        if i not in ELEMS:
            problems.append(f"global group '{gr['name']}' names missing element {i}")
for gr in DATA["index"]:
    for gg in gr["goals"]:
        for sid in gg["stories"]:
            if sid not in STORIES:
                problems.append(f"index '{gg['text']}' names missing story {sid}")
for p in DATA["pages"]:
    prim = [e["id"] for e in p["elements"] if e["type"] == "primary" and not e.get("rep")]
    if prim != [p["primary"]]:
        problems.append(f"{p['id']}: primary CTAs {prim}, declared {p['primary']}")
    main = [s for s in p["stories"] if s.get("main")]
    if len(main) != 1:
        problems.append(f"{p['id']}: {len(main)} main stories")
    elif p["primary"] not in [x for st in main[0]["chain"] for x in st["els"]]:
        problems.append(f"{p['id']}: primary {p['primary']} not in main story chain")
for e in [x for _, x in ELEMS.values()]:
    if e["type"] == "error":
        if not e.get("wayout"):
            gap(f"{e['id']} ({e['el']}, {page_label(e)}): error state with no way out")
        for w in e.get("wayout", []):
            if w not in ELEMS:
                problems.append(f"{e['id']}: way out {w} does not exist")
    if path_of(e) == "unhappy" and not e.get("trigger"):
        problems.append(f"{e['id']}: unhappy element with no trigger")
for p in DATA["pages"]:
    types = {e["type"] for e in p["elements"]}
    if types & INPUT_TYPES:
        if "error" not in types:
            gap(f"{p['id']} ({p['name']}): has an input, form or calculator but no error state")
        if "wayout" not in types and not any(e["type"] == "error" and e.get("wayout") for e in p["elements"]):
            gap(f"{p['id']} ({p['name']}): has an input, form or calculator but no way out (a wayout element, or an error state that names one)")
    if "ways_out" not in p:
        problems.append(f"{p['id']}: no ways-out grid")
    else:
        for k, _ in WAYS:
            c = p["ways_out"][k]
            if c["v"] == "yes" and not c["els"]:
                problems.append(f"{p['id']}: ways-out {k} is yes with no element")
            for w in c["els"]:
                if w not in ELEMS:
                    problems.append(f"{p['id']}: ways-out {k} names missing {w}")
if DATA["meta"]["no_dashes"] and re.search("[\u2014\u2013]", SOURCE_FILE.read_text()):
    problems.append("elements.json contains an em or en dash (meta.no_dashes is on)")
if problems:
    print("Data problems:\n  " + "\n  ".join(problems))
    if not DISCOVER and any("no error state" in x or "no way out" in x for x in problems):
        print("Cataloging an app that already exists? Set meta.mode to \"discover\" to list these as gaps in the app instead.")
    sys.exit(1)


# ---------------------------------------------------------------- helpers
def type_text(e):
    t = TYPE_LABEL[e["type"]]
    if e.get("sub"):
        t += f": {e['sub']}"
    return t


def event_flag(ev):
    if ev in ("none", "not set") or ev.startswith("("):
        return ev, False
    return ev, ev not in SOURCE_EVENTS


def short(s, n=46):
    s = s.strip()
    return s if len(s) <= n else s[: n - 1].rstrip() + "\u2026"


def page_name(pid):
    if pid == "GLOBAL":
        return "Global elements"
    return next(p["name"] for p in DATA["pages"] if p["id"] == pid)


def no_story(elements):
    return [e for e in elements if not SERVES.get(e["id"])]


def open_needs(stories):
    out = []
    for s in stories:
        for st in s["chain"]:
            if not st["els"]:
                out.append((s, st))
    return out


# ---------------------------------------------------------------- component inventory
def is_pointer(e):
    """A page row that only points to shared GLB- elements (header, footer)."""
    return e["label"].startswith("See GLB")


def kit_name(e):
    return e.get("kit") or type_text(e)


ERRORS_ON = {}
for _eid, (_, _e) in ELEMS.items():
    if _e["type"] == "error":
        for _w in _e.get("wayout", []):
            ERRORS_ON.setdefault(_w, []).append(_eid)


def inventory(pairs):
    """Kit parts from (page id, element) pairs: uses, repeats, pages, build states, unhappy uses,
    error states that send people to the part, and the longest label to test text length."""
    parts = OrderedDict()
    for pid, e in pairs:
        if is_pointer(e):
            continue
        k = kit_name(e)
        p = parts.setdefault(k, {"name": k, "type": e["type"], "els": [], "reps": [], "pages": [],
                                 "states": Counter(), "unhappy": 0, "errors": [], "longest": "", "first": len(parts)})
        (p["reps"] if e.get("rep") else p["els"]).append(e["id"])
        if pid not in p["pages"]:
            p["pages"].append(pid)
        p["states"][e["state"]] += 1
        p["unhappy"] += path_of(e) == "unhappy"
        p["errors"] += [x for x in ERRORS_ON.get(e["id"], []) if x not in p["errors"]]
        if e["state"] != "missing" and not e["label"].startswith("[") and len(e["label"]) > len(p["longest"]):
            p["longest"] = e["label"]
    return sorted(parts.values(), key=lambda p: (TYPE_ORDER.index(p["type"]), -len(p["els"]) - len(p["reps"]), p["first"]))


def page_pairs(p):
    return [(p["id"], e) for e in p["elements"]]


def shells(p):
    return list(p["shells"]) + [e["el"] for e in p["elements"] if is_pointer(e) and e["el"] not in p["shells"]]


KIT = inventory([("GLOBAL", e) for e in DATA["global"]["elements"]] + [x for p in DATA["pages"] for x in page_pairs(p)])


def states_text(c):
    return ", ".join(f"{STATE_LABEL[s]} {c[s]}" for s in STATE_LABEL if c[s])


def uses_text(p):
    return str(len(p["els"])) + (f" + {len(p['reps'])} repeats" if p["reps"] else "")


TODAY = DATA["meta"]["updated"]
total_elements = sum(len(p["elements"]) for p in DATA["pages"])


# ---------------------------------------------------------------- markdown
def md_cell(s):
    return str(s).replace("|", "\\|").replace("\n", " ")


def md_chain_line(st):
    refs = ", ".join(f"{eid} \"{short(ELEMS[eid][1]['label'], 40)}\"" for eid in st["els"])
    tail = f" ({refs})" if refs else " (no element yet" + (f": {st['why']}" if st.get("why") else "") + ")"
    return "  " * (st.get("d", 0) + 1) + f"- In order to {st['to']}, I need {st['need']}{tail}."


def md_stories(stories):
    out = []
    for s in stories:
        tag = " (main)" if s.get("main") else ""
        out.append(f"- **{s['id']}{tag}.** {s['story']} _Source: {s['src']}._")
        for st in s["chain"]:
            out.append(md_chain_line(st))
    return out


def md_table(elements):
    rows = ["| ID | Element | Label | Type | Path | Trigger | Person does | What happens | Event | State | Source | Serves |",
            "|---|---|---|---|---|---|---|---|---|---|---|---|"]
    for e in elements:
        ev, prop = event_flag(e["event"])
        label = e["label"] + (" (proposed)" if e["lab"] == "proposed" else "")
        idt = f"**{e['id']}**" if e["type"] == "primary" and not e.get("rep") else e["id"]
        typ = type_text(e) + (f" (repeat of {e['rep']})" if e.get("rep") else "")
        rows.append("| " + " | ".join(md_cell(x) for x in [
            idt, e["el"], label, typ, PATH_LABEL[path_of(e)], e.get("trigger", ""), e["does"],
            sentence(e["then"]) + (f" Way out: {', '.join(e['wayout'])}." if e.get("wayout") else ""), ev + (" (proposed)" if prop else ""),
            STATE_LABEL[e["state"]], e["src"], ", ".join(SERVES.get(e["id"], [])) or "none"]) + " |")
    return rows


def md_flags(elements, stories):
    out = []
    ns = no_story(elements)
    out.append("**Elements with no user story:** " + ("; ".join(f"{e['id']} {e['el']}" for e in ns) if ns else "none."))
    on = open_needs(stories)
    out.append("")
    out.append("**Needs with no element yet:** " + ("; ".join(
        f"{s['id']}: in order to {st['to']}, I need {st['need']}" + (f" ({st['why']})" if st.get("why") else "")
        for s, st in on) if on else "none."))
    return out


def sentence(s):
    s = s.rstrip()
    return s if not s or s[-1] in ".!?:)" else s + "."


def wo_text(c):
    t = {"yes": "Yes", "no": "No (gap)", "n/a": "Not needed"}[c["v"]]
    if c["els"]:
        t += " (" + ", ".join(c["els"]) + ")"
    if c.get("note"):
        t += f": {c['note'].rstrip('.')}"
    return t


def wo_gaps():
    return [(p, k, q, p["ways_out"][k]) for p in DATA["pages"] for k, q in WAYS if p["ways_out"][k]["v"] == "no"]


def build_md():
    m = DATA["meta"]
    L = [f"---", f'product: "{PRODUCT}"', f'file: "{RECORD}"',
         f'updated: "{m["updated"]}"', f'status: "{m["status"]}"',
         'built_from: "elements.json by build.py; edit the JSON, then run python3 build.py"', "---", "",
         f"# {m['title']}", "", f"**Purpose.** {m['purpose']}", "", f"**Main message.** {m['main_message']}", "",
         f"**How to read it.** {m['reading']}", ""]
    if GAPS:
        L += ["## Gaps found in the app", "", "Places where the app breaks a catalog rule today. Each is a way a person can get stuck.", ""]
        L += [f"- {g}" for g in GAPS] + [""]
    L += ["## Terms", ""]
    for t, dfn in DATA["terms"]:
        L.append(f"- **{t}:** {dfn}")
    L += ["", "## Sources", "", "| Key | Source |", "|---|---|"]
    for k, v in DATA["sources"]:
        L.append(f"| {k} | {md_cell(v)} |")
    L += ["", "## Sitemap", ""]
    for g in DATA["sitemap"]:
        L.append(f"- **{g['group']}**")
        for pg in g["pages"]:
            ind = "  " * (pg["depth"] + 1)
            L.append(f"{ind}- `{pg['path']}` {pg['name']}. {pg['audience']}. {pg['job']}. _{STATE_LABEL[pg['state']]}, {pg['when']}._")
    L += ["", "## Primary call to action by page", "", "| Page | Path | Primary CTA | Elements |", "|---|---|---|---|"]
    for p in DATA["pages"]:
        pe = ELEMS[p["primary"]][1]
        L.append(f"| {p['name']} | `{p['path']}` | {p['primary']} \"{md_cell(pe['label'])}\" | {len(p['elements'])} |")
    L += ["", f"Pages with element tables: {len(DATA['pages'])}. Elements on those pages: {total_elements}. Global elements: {len(DATA['global']['elements'])}.", ""]
    L += ["## Global elements", "", "Shared parts, cataloged once. Each page lists the shells it uses.", "", DATA["meta"]["tracking_note"], ""]
    L += md_stories(DATA["global"]["stories"]) + [""]
    for g in DATA["global"]["groups"]:
        L.append(f"### {g['name']}")
        L.append("")
        L += md_table([ELEMS[i][1] for i in g["ids"]])
        L.append("")
    L += md_flags(DATA["global"]["elements"], DATA["global"]["stories"]) + [""]
    for p in DATA["pages"]:
        L += [f"## {p['name']} (`{p['path']}`)", "",
              f"**Job:** {p['job']} **Audience:** {p['audience']}. **State:** {STATE_LABEL[p['state']]}, {p['when']}.", "",
              f"**Primary CTA:** {p['primary']} \"{ELEMS[p['primary']][1]['label']}\".", "", "### User stories and needs", ""]
        hs = [x for x in p["stories"] if x.get("path") != "unhappy"]
        us = [x for x in p["stories"] if x.get("path") == "unhappy"]
        he = [x for x in p["elements"] if path_of(x) == "happy"]
        ue = [x for x in p["elements"] if path_of(x) == "unhappy"]
        L += md_stories(hs) + ["", "### Elements, top to bottom", ""]
        L += md_table(he) + [""]
        if us or ue:
            L += ["### When things go wrong", "", "#### Stories and needs", ""] + md_stories(us) + ["", "#### Elements", ""]
            L += md_table(ue) + [""]
        L += md_flags(p["elements"], p["stories"]) + [""]
        L += ["**Ways out:** " + "; ".join(f"{q} {wo_text(p['ways_out'][k])}" for k, q in WAYS) + ".", ""]
        L += [md_page_kit(p), ""]
        if p.get("notes"):
            L += [f"_Note:_ {p['notes']}", ""]
    L += ["## Ways out", "", "Every page against five questions. A no is a gap: a place a person can get stuck.", "",
          "| Page | " + " | ".join(q for _, q in WAYS) + " |", "|---|" + "---|" * len(WAYS)]
    for p in DATA["pages"]:
        L.append(f"| {p['name']} | " + " | ".join(md_cell(wo_text(p["ways_out"][k])) for k, _ in WAYS) + " |")
    L += ["", "**Gaps:** " + ("; ".join(f"{p['name']}, {q.lower()} {c['note'].rstrip('.')}" for p, k, q, c in wo_gaps()) + "." if wo_gaps() else "none."), ""]
    L += ["## Cross-page index", "", "Grouped by intent, then by what the person wants, then the actions that serve it.", ""]
    for g in DATA["index"]:
        L.append(f"### {g['intent']}")
        L.append("")
        for gg in g["goals"]:
            L.append(f"- **{gg['text']}.** Stories: " + ", ".join(f"{s} ({page_name(STORIES[s][0])})" for s in gg["stories"]))
            for eid, pid in index_actions(gg):
                e = ELEMS[eid][1]
                L.append(f"  - {e['label']} ({eid}, {page_name(pid)})")
        L.append("")
    L += md_inventory()
    L += [f"## Needs {OWNER}", "", f"Decisions only {OWNER} can make. Each carries a recommendation where the sources support one.", ""]
    for q in [q for q in DATA["open_questions"] if q["status"] == "open"]:
        rec = f" **Recommended:** {q['recommended']}" if q["recommended"] else ""
        L.append(f"- **{q['id']} {q['topic']}.** {q['q']}{rec} _Sources: {q['src']}. Pages: {', '.join(q['pages'])}._")
    L += ["", "## Defaults applied, change if wrong", "", "Open points from the sources where a default was taken so the build can start.", ""]
    for q in [q for q in DATA["open_questions"] if q["status"] == "default"]:
        L.append(f"- **{q['id']} {q['topic']}.** {q['q']} **Default:** {q['default']} _Reason: {q['reason']} Sources: {q['src']}._")
    dec = [q for q in DATA["open_questions"] if q["status"] == "decided"]
    if dec:
        L += ["", "## Decided", ""]
        for q in dec:
            L.append(f"- **{q['id']} {q['topic']}.** {q['q']} **Decided:** {q['answer']} _Sources: {q['src']}._")
    L.append("")
    return "\n".join(L)


def md_page_kit(p):
    parts = "; ".join(f"{k['name']} {uses_text(k)} ({', '.join(k['els'] + k['reps'])})" for k in inventory(page_pairs(p)))
    sh = shells(p)
    return f"**Kit parts on this page:** {parts or 'none'}." + (f" **Shared shells:** {', '.join(sh)}." if sh else "")


def md_inventory():
    L = ["## Component inventory", "",
         "Every part a UI kit needs, from the element tables. Uses counts elements, with repeats of the same element apart. "
         "Reached from errors lists the error states whose way out is this part: a field there needs an error look, a button or link there is a recovery step. "
         "Longest label sets the text length to test.", "",
         "| Kit part | Uses | Pages | Build state | Unhappy uses | Reached from errors | Longest label |",
         "|---|---|---|---|---|---|---|"]
    for k in KIT:
        L.append("| " + " | ".join(md_cell(x) for x in [
            k["name"], uses_text(k), len(k["pages"]), states_text(k["states"]), k["unhappy"],
            ", ".join(k["errors"]) or "none", f"{k['longest']} ({len(k['longest'])} characters)" if k["longest"] else "nothing visible"]) + " |")
    L += ["", "### By page", "", "| Page | Kit parts | Shared shells |", "|---|---|---|"]
    for p in DATA["pages"]:
        parts = ", ".join(f"{k['name']} {len(k['els']) + len(k['reps'])}" for k in inventory(page_pairs(p)))
        L.append(f"| {md_cell(p['name'])} | {md_cell(parts)} | {md_cell(', '.join(shells(p)) or 'none')} |")
    L.append("")
    return L


def index_actions(gg):
    seen = []
    for sid in gg["stories"]:
        _, s = STORIES[sid]
        for st in s["chain"]:
            for eid in st["els"]:
                pid, e = ELEMS[eid]
                if e["type"] in ACTION_TYPES and not e["label"].startswith("See GLB") and eid not in [x for x, _ in seen]:
                    seen.append((eid, pid))
    return seen


# ---------------------------------------------------------------- html
def font_face(name, file, weight="100 900"):
    b = base64.b64encode((FONTS / file).read_bytes()).decode()
    return (f"@font-face{{font-family:'{name}';src:url(data:font/ttf;base64,{b}) format('truetype');"
            f"font-weight:{weight};font-style:normal;font-display:swap}}")


def h_ref(eid):
    e = ELEMS[eid][1]
    return (f'<a class="ref" href="#row-{eid}"><span class="mono">{eid}</span> '
            f'<span class="reflabel">\u201c{esc(short(e["label"], 44))}\u201d</span></a>')


def h_stories(stories):
    out = ['<div class="stories">']
    for s in stories:
        main = s.get("main")
        out.append(f'<div class="story{" main" if main else ""}" id="story-{s["id"]}">')
        out.append(f'<p class="story-head"><span class="mono sid">{s["id"]}</span>'
                   + ('<span class="badge main-b">Main story</span>' if main else "")
                   + f' {esc(s["story"])}</p>')
        out.append('<ul class="chain">')
        for st in s["chain"]:
            d = st.get("d", 0)
            refs = ", ".join(h_ref(x) for x in st["els"])
            if not st["els"]:
                refs = '<span class="gap">no element yet' + (f": {esc(st['why'])}" if st.get("why") else "") + "</span>"
            out.append(f'<li class="d{d}">In order to {esc(st["to"])}, I need {esc(st["need"])} ({refs}).</li>')
        out.append("</ul>")
        out.append(f'<p class="src">Source: {esc(s["src"])}</p></div>')
    out.append("</div>")
    return "\n".join(out)


def h_table(elements, primary=None):
    out = ['<div class="tablewrap"><table><colgroup><col class="c-id"><col class="c-el"><col class="c-lab"><col class="c-ty"><col class="c-pa"><col class="c-tr"><col class="c-do"><col class="c-th"><col class="c-ev"><col class="c-st"><col class="c-src"><col class="c-sv"></colgroup><thead><tr><th>ID</th><th>Element</th><th>Label</th><th>Type</th>'
           '<th>Path</th><th>Trigger</th><th>Person does</th><th>What happens</th><th>Event</th><th>State</th><th>Source</th><th>Serves</th></tr></thead><tbody>']
    for e in elements:
        ev, prop = event_flag(e["event"])
        is_primary = e["type"] == "primary"
        cls = ("primary-row " if is_primary else "") + ("err-row" if e["type"] == "error" else ("way-row" if e["type"] == "wayout" else ""))
        wo = ""
        if e.get("wayout"):
            wo = '<span class="wo">Way out: ' + ", ".join(f'<a class="mono" href="#row-{w}">{w}</a>' for w in e["wayout"]) + "</span>"
        lab = esc(e["label"])
        if e["lab"] == "proposed":
            lab += ' <span class="tag prop">proposed</span>'
        elif e["lab"] == "app":
            lab += ' <span class="tag app">app label</span>'
        typ = esc(type_text(e))
        if e.get("rep"):
            typ += f' <span class="tag">repeat of {e["rep"]}</span>'
        evh = f'<span class="mono">{esc(ev)}</span>' + (' <span class="tag prop">proposed</span>' if prop else "")
        serves = SERVES.get(e["id"], [])
        sv = ", ".join(f'<a href="#story-{s}" class="mono">{s}</a>' for s in serves) or '<span class="gap">none</span>'
        out.append(f'<tr id="row-{e["id"]}" class="{cls}" data-type="{e["type"]}" data-state="{e["state"]}" data-path="{path_of(e)}">'
                   f'<td class="mono idc">{e["id"]}</td><td>{esc(e["el"])}</td><td>{lab}</td><td>{typ}</td>'
                   f'<td><span class="pa pa-{path_of(e)}">{PATH_LABEL[path_of(e)]}</span></td><td class="trc">{esc(e.get("trigger", ""))}</td>'
                   f'<td>{esc(e["does"])}</td><td>{esc(e["then"])} {wo}</td><td>{evh}</td>'
                   f'<td><span class="st st-{e["state"]}">{STATE_LABEL[e["state"]]}</span></td>'
                   f'<td class="srcc">{esc(e["src"])}</td><td>{sv}</td></tr>')
    out.append("</tbody></table></div>")
    return "\n".join(out)


def h_flags(elements, stories):
    ns = no_story(elements)
    on = open_needs(stories)
    a = "".join(f'<li>{h_ref(e["id"])} {esc(e["el"])}</li>' for e in ns) or "<li>None.</li>"
    b = "".join(f'<li><a class="mono" href="#story-{s["id"]}">{s["id"]}</a> In order to {esc(st["to"])}, I need {esc(st["need"])}'
                + (f'. {esc(st["why"])}' if st.get("why") else "") + "</li>" for s, st in on) or "<li>None.</li>"
    return (f'<div class="flags"><div><h4>Elements with no user story</h4><ul>{a}</ul></div>'
            f'<div><h4>Needs with no element yet</h4><ul>{b}</ul></div></div>')


def h_unhappy(p):
    us = [x for x in p["stories"] if x.get("path") == "unhappy"]
    ue = [x for x in p["elements"] if path_of(x) == "unhappy"]
    if not (us or ue):
        return ""
    return ('<div class="unhappy"><h3 class="wrong">When things go wrong</h3><h4 class="sub4">Stories and needs</h4>' + h_stories(us)
            + '<h4 class="sub4">Elements</h4>' + h_table(ue) + "</div>")


def wo_cell(c):
    cls = {"yes": "wo-yes", "no": "wo-no", "n/a": "wo-na"}[c["v"]]
    t = {"yes": "Yes", "no": "No", "n/a": "Not needed"}[c["v"]]
    els = " ".join(f'<a class="mono" href="#row-{w}">{w}</a>' for w in c["els"])
    note = f'<span class="won">{esc(c["note"])}</span>' if c.get("note") else ""
    return f'<td class="{cls}"><b>{t}</b> {els}{note}</td>'


def h_wo_page(p):
    return ('<div class="wopage"><h4>Ways out on this page</h4><div class="tablewrap wo"><table class="wot"><thead><tr>'
            + "".join(f"<th>{esc(q)}</th>" for _, q in WAYS) + "</tr></thead><tbody><tr>"
            + "".join(wo_cell(p["ways_out"][k]) for k, _ in WAYS) + "</tr></tbody></table></div></div>")


def h_ids(ids):
    return " ".join(f'<a class="mono" href="#row-{i}">{i}</a>' for i in ids)


def h_page_link(pid):
    if pid == "GLOBAL":
        return '<a href="#global">Global elements</a>'
    return f'<a href="#page-{pid}">{esc(page_name(pid))}</a>'


def h_kit_page(p):
    rows = "".join(f'<tr><td>{esc(k["name"])}</td><td class="num">{len(k["els"]) + len(k["reps"])}</td>'
                   f'<td>{h_ids(k["els"] + k["reps"])}</td><td class="num">{k["unhappy"] or ""}</td></tr>'
                   for k in inventory(page_pairs(p)))
    sh = shells(p)
    shl = f'<p class="note">Shared shells on this page: {esc(", ".join(sh))}. Their parts are in <a href="#global">Global elements</a>.</p>' if sh else ""
    return ('<div class="kitpage"><h4>Kit parts on this page</h4><div class="tablewrap kit"><table><thead><tr>'
            '<th>Kit part</th><th class="num">Count</th><th>Elements</th><th class="num">Unhappy</th></tr></thead>'
            f'<tbody>{rows}</tbody></table></div>{shl}</div>')


def h_errs(ids):
    if not ids:
        return '<span class="gap0">none</span>'
    if len(ids) <= 6:
        return h_ids(ids)
    return f'<details><summary>{len(ids)} error states</summary>{h_ids(ids)}</details>'


def h_inventory():
    rows = []
    for k in KIT:
        pages = ", ".join(h_page_link(x) for x in k["pages"])
        rows.append(f'<tr><td class="kn">{esc(k["name"])}</td><td class="num">{esc(uses_text(k))}</td>'
                    f'<td><details><summary>{len(k["pages"])} {"page" if len(k["pages"]) == 1 else "pages"}</summary>{pages}</details></td>'
                    f'<td>{esc(states_text(k["states"]))}</td><td class="num">{k["unhappy"] or ""}</td>'
                    f'<td>{h_errs(k["errors"])}</td>'
                    + (f'<td>{esc(k["longest"])} <span class="tag">{len(k["longest"])} characters</span></td></tr>' if k["longest"] else '<td><span class="gap0">nothing visible</span></td></tr>'))
    names = [k["name"] for k in KIT]
    head = "".join(f'<th class="rot"><span>{esc(n)}</span></th>' for n in names)
    mat = []
    for p in DATA["pages"]:
        c = {k["name"]: len(k["els"]) + len(k["reps"]) for k in inventory(page_pairs(p))}
        mat.append(f'<tr><td class="pn">{h_page_link(p["id"])}</td>'
                   + "".join(f'<td class="num{" z" if not c.get(n) else ""}">{c.get(n, "")}</td>' for n in names)
                   + f'<td class="sh">{esc(", ".join(shells(p)))}</td></tr>')
    return ('<section id="inventory" class="card"><h2>Component inventory</h2>'
            '<p>Every part a UI kit needs, from the element tables above. Uses counts elements, with repeats of the same element apart. '
            'Reached from errors lists the error states whose way out is this part: a field there needs an error look, a button or link there is a recovery step. '
            'Longest label sets the text length to test the part at.</p>'
            '<div class="tablewrap kit"><table><thead><tr><th>Kit part</th><th class="num">Uses</th><th>Pages</th><th>Build state</th>'
            '<th class="num">Unhappy uses</th><th>Reached from errors</th><th>Longest label</th></tr></thead><tbody>'
            + "".join(rows) + '</tbody></table></div>'
            '<h3>By page</h3><p>Each page or screen against every kit part. A number is how many times the part appears there.</p>'
            f'<div class="tablewrap kit mat"><table><thead><tr><th>Page</th>{head}<th>Shared shells</th></tr></thead><tbody>'
            + "".join(mat) + "</tbody></table></div></section>")


def type_counts(elements):
    c = Counter(e["type"] for e in elements if not e.get("rep"))
    reps = sum(1 for e in elements if e.get("rep"))
    unh = sum(1 for e in elements if path_of(e) == "unhappy")
    return " ".join(f'<span class="cnt" data-t="{t}">{TYPE_LABEL[t]} <b>{c[t]}</b></span>' for t in TYPE_ORDER if c[t]) + (f' <span class="cnt">repeats <b>{reps}</b></span>' if reps else "") + (f' <span class="cnt unh">unhappy path <b>{unh}</b></span>' if unh else "")


def build_html():
    m = DATA["meta"]
    css_fonts = font_face("Geist", "Geist[wght].ttf") + font_face("Geist Mono", "GeistMono[wght].ttf")
    nav = ['<a href="#overview">Overview</a>'] + (['<a href="#gaps">Gaps found</a>'] if GAPS else []) + ['<a href="#sitemap">Sitemap</a>', '<a href="#global">Global elements</a>']
    groups = OrderedDict()
    for p in DATA["pages"]:
        groups.setdefault(p["group"], []).append(p)
    navp = []
    for g, ps in groups.items():
        navp.append(f'<p class="navg">{esc(g)}</p>')
        for p in ps:
            navp.append(f'<a href="#page-{p["id"]}" data-page="{p["id"]}">{esc(p["name"])} <span class="navc" id="navc-{p["id"]}">{len(p["elements"])}</span></a>')
    nav_tail = ['<a href="#waysout">Ways out</a>', '<a href="#index">Cross-page index</a>', '<a href="#inventory">Component inventory</a>', f'<a href="#decisions">Needs {esc(OWNER)}</a>', '<a href="#questions">Defaults applied</a>', '<a href="#terms">Terms and sources</a>']

    # sitemap tree
    sm = ['<div class="tree">']
    for g in DATA["sitemap"]:
        sm.append(f'<div class="tgroup"><p class="tg">{esc(g["group"])}</p><ul>')
        for pg in g["pages"]:
            link = f'<a href="#page-{pg["page"]}">{esc(pg["name"])}</a>' if pg["page"] else esc(pg["name"])
            sm.append(f'<li class="t{pg["depth"]}"><span class="mono path">{esc(pg["path"])}</span> {link} '
                      f'<span class="st st-{pg["state"]}">{STATE_LABEL[pg["state"]]}</span>'
                      f'<span class="when">{esc(pg["when"])}</span>'
                      f'<span class="tline">{esc(pg["audience"])}. {esc(pg["job"])}.{(" " + esc(pg["note"])) if pg["note"] else ""}</span></li>')
        sm.append("</ul></div>")
    sm.append("</div>")

    prim_rows = "".join(
        f'<tr><td><a href="#page-{p["id"]}">{esc(p["name"])}</a></td><td class="mono">{esc(p["path"])}</td>'
        f'<td><a href="#row-{p["primary"]}" class="mono">{p["primary"]}</a> {esc(ELEMS[p["primary"]][1]["label"])}</td>'
        f'<td class="num">{len(p["elements"])}</td></tr>' for p in DATA["pages"])

    filt_t = "".join(f'<button type="button" class="chip on" data-ft="{t}" aria-pressed="true">{TYPE_LABEL[t]}</button>' for t in TYPE_ORDER)
    filt_p = "".join(f'<button type="button" class="chip on" data-fp="{k}" aria-pressed="true">{v}</button>' for k, v in PATH_LABEL.items())
    filt_s = "".join(f'<button type="button" class="chip on" data-fs="{s}" aria-pressed="true">{STATE_LABEL[s]}</button>' for s in STATE_ORDER)

    gsec = [f'<section id="global" class="card"><h2>Global elements</h2>'
            '<p>Shared parts, cataloged once. Each page card names the shells it uses under "Kit parts on this page".</p>',
            f'<p class="note">{esc(DATA["meta"]["tracking_note"])}</p>', "<h3>User stories and needs</h3>", h_stories([x for x in DATA["global"]["stories"] if x.get("path") != "unhappy"]),
            '<h3 class="wrong">When things go wrong: stories and needs</h3>', h_stories([x for x in DATA["global"]["stories"] if x.get("path") == "unhappy"])]
    for g in DATA["global"]["groups"]:
        gsec.append(f"<h3>{esc(g['name'])}</h3>")
        gsec.append(h_table([ELEMS[i][1] for i in g["ids"]]))
    gsec.append(h_flags(DATA["global"]["elements"], DATA["global"]["stories"]))
    gsec.append("</section>")

    psec = []
    for p in DATA["pages"]:
        pe = ELEMS[p["primary"]][1]
        psec.append(f'<section id="page-{p["id"]}" class="card page" data-page="{p["id"]}">'
                    f'<div class="phead"><h2>{esc(p["name"])}</h2><span class="mono path">{esc(p["path"])}</span>'
                    f'<span class="st st-{p["state"]}">{STATE_LABEL[p["state"]]}</span><span class="when">{esc(p["when"])}</span></div>'
                    f'<p class="job"><b>Job:</b> {esc(p["job"])} <b>Audience:</b> {esc(p["audience"])}.</p>'
                    f'<div class="primary-call"><span class="pc-k">Primary CTA</span> <a class="mono" href="#row-{p["primary"]}">{p["primary"]}</a> '
                    f'<span class="pc-l">{esc(pe["label"])}</span><span class="pc-d">{esc(pe["then"])}</span></div>'
                    f'<p class="counts"><span class="shown" id="shown-{p["id"]}">{len(p["elements"])} of {len(p["elements"])} elements shown</span> {type_counts(p["elements"])}</p>'
                    "<h3>User stories and needs</h3>" + h_stories([x for x in p["stories"] if x.get("path") != "unhappy"]) +
                    "<h3>Elements, top to bottom</h3>" + h_table([x for x in p["elements"] if path_of(x) == "happy"]) +
                    h_unhappy(p) + h_flags(p["elements"], p["stories"]) + h_wo_page(p) + h_kit_page(p) +
                    (f'<p class="note">{esc(p["notes"])}</p>' if p.get("notes") else "") + "</section>")

    gaps = wo_gaps()
    wsec = ['<section id="waysout" class="card"><h2>Ways out</h2><p>Every page against five questions, so a person never gets stuck. A no is a gap.</p>'
            '<div class="tablewrap wo"><table class="wot grid"><thead><tr><th>Page</th>' + "".join(f"<th>{esc(q)}</th>" for _, q in WAYS) + "</tr></thead><tbody>"]
    for p in DATA["pages"]:
        wsec.append(f'<tr><td><a href="#page-{p["id"]}">{esc(p["name"])}</a></td>' + "".join(wo_cell(p["ways_out"][k]) for k, _ in WAYS) + "</tr>")
    wsec.append('</tbody></table></div><h3>Gaps</h3><ul class="gaps">' + ("".join(
        f'<li><a href="#page-{p["id"]}">{esc(p["name"])}</a>: {esc(q)} {esc(c["note"])}</li>' for p, k, q, c in gaps) or "<li>None.</li>") + "</ul></section>")
    isec = ['<section id="index" class="card"><h2>Cross-page index</h2>'
            '<p>Grouped by intent, then by what the person wants, then the actions that serve it and the pages they sit on.</p>']
    for g in DATA["index"]:
        isec.append(f'<h3>{esc(g["intent"])}</h3><ul class="idx">')
        for gg in g["goals"]:
            st = ", ".join(f'<a class="mono" href="#story-{s}">{s}</a>' for s in gg["stories"])
            acts = "".join(f'<li><a href="#row-{eid}" class="mono">{eid}</a> {esc(ELEMS[eid][1]["label"])} '
                           f'<span class="pg">{esc(page_name(pid))}</span></li>' for eid, pid in index_actions(gg))
            isec.append(f'<li><p class="ig">{esc(gg["text"])}</p><p class="is">Stories: {st}</p><ul class="acts">{acts}</ul></li>')
        isec.append("</ul>")
    isec.append("</section>")

    def qpages(q):
        return ", ".join(f'<a href="#{"global" if x == "GLOBAL" else "page-" + x}">{esc(page_name(x))}</a>' for x in q["pages"])
    qsec = [f'<section id="decisions" class="card needs"><h2>Needs {esc(OWNER)}</h2>'
            f"<p>Decisions only {esc(OWNER)} can make. Each carries a recommendation where the sources support one.</p><ol class=\"qs\">"]
    for q in [q for q in DATA["open_questions"] if q["status"] == "open"]:
        rec = f'<p class="rec"><b>Recommended:</b> {esc(q["recommended"])}</p>' if q["recommended"] else ""
        qsec.append(f'<li id="{q["id"]}"><p><span class="mono">{q["id"]}</span> <b>{esc(q["topic"])}.</b> {esc(q["q"])}</p>{rec}'
                    f'<p class="src">Sources: {esc(q["src"])}. Pages: {qpages(q)}.</p></li>')
    qsec.append('</ol></section><section id="questions" class="card"><h2>Defaults applied, change if wrong</h2>'
                "<p>Open points from the sources where a default was taken so the build can start.</p><ol class=\"qs\">")
    for q in [q for q in DATA["open_questions"] if q["status"] == "default"]:
        qsec.append(f'<li id="{q["id"]}"><p><span class="mono">{q["id"]}</span> <b>{esc(q["topic"])}.</b> {esc(q["q"])}</p>'
                    f'<p class="rec"><b>Default:</b> {esc(q["default"])}</p>'
                    f'<p class="src">Reason: {esc(q["reason"])} Sources: {esc(q["src"])}. Pages: {qpages(q)}.</p></li>')
    qsec.append("</ol></section>")
    dec = [q for q in DATA["open_questions"] if q["status"] == "decided"]
    if dec:
        qsec.append('<section id="decided" class="card"><h2>Decided</h2><ol class="qs">')
        for q in dec:
            qsec.append(f'<li id="{q["id"]}"><p><span class="mono">{q["id"]}</span> <b>{esc(q["topic"])}.</b> {esc(q["q"])}</p>'
                        f'<p class="rec"><b>Decided:</b> {esc(q["answer"])}</p><p class="src">Sources: {esc(q["src"])}. Pages: {qpages(q)}.</p></li>')
        qsec.append("</ol></section>")
    gsec_gaps = ""
    if GAPS:
        gsec_gaps = ('<section id="gaps" class="card needs"><h2>Gaps found in the app</h2>'
                     '<p>Places where the app breaks a catalog rule today. Each is a way a person can get stuck.</p><ul class="gaps">'
                     + "".join(f"<li>{esc(g)}</li>" for g in GAPS) + "</ul></section>")

    tsec = ['<section id="terms" class="card"><h2>Terms and sources</h2><dl class="terms">']
    for t, dfn in DATA["terms"]:
        tsec.append(f"<dt>{esc(t)}</dt><dd>{esc(dfn)}</dd>")
    tsec.append('</dl><h3>Source keys</h3><dl class="terms">')
    for k, v in DATA["sources"]:
        tsec.append(f'<dt class="mono">{esc(k)}</dt><dd>{esc(v)}</dd>')
    tsec.append("</dl></section>")

    # short terms at the top (common ground before use)
    top_terms = DATA["meta"]["top_terms"]
    if top_terms is None:
        top_terms = [t for t, _ in DATA["terms"][:6]]
    tt = "".join(f"<dt>{esc(t)}</dt><dd>{esc(d)}</dd>" for t, d in DATA["terms"] if t in top_terms)
    tt = f'<h3>Terms used on this page</h3><dl class="terms">{tt}</dl>' if tt else ""

    state_c = Counter(e["state"] for p in DATA["pages"] for e in p["elements"])
    stats = "".join(f'<div class="stat"><b>{v}</b><span>{l}</span></div>' for v, l in [
        (len(DATA["pages"]), "pages with tables"), (total_elements, "page elements"),
        (len(DATA["global"]["elements"]), "global elements"), (state_c["exists"], "exist in app"),
        (state_c["build"] + state_c["fakedoor"], "to build or fake door"), (sum(1 for p in DATA["pages"] for e in p["elements"] if path_of(e) == "unhappy"), "unhappy-path elements"),
        (len(wo_gaps()), "ways-out gaps"), (sum(1 for q in DATA["open_questions"] if q["status"] == "open"), f"decisions for {OWNER}")])

    return f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>{html.escape(PRODUCT)} UX Elements Catalog</title>
<meta name="description" content="{esc(m['purpose'])}">
<style>
{css_fonts}
:root{{--bg:#FCFBF9;--card:#FFFFFF;--ink:#111111;--body:#4F4A45;--muted:#7A736C;--line:rgba(17,17,17,.12);--soft:rgba(17,17,17,.05);
--accent:#D93A1E;--accent-bg:rgba(217,58,30,.08);--pass:#2E6B4E;--pass-bg:rgba(46,107,78,.1);--warn:#8A5A00;--warn-bg:rgba(200,140,0,.13);
--blue:#2B5A8A;--blue-bg:rgba(43,90,138,.1);--grey-bg:rgba(17,17,17,.07)}}
@media (prefers-color-scheme: dark){{:root:not([data-theme="light"]){{--bg:#121110;--card:#1B1A18;--ink:#F2EFEA;--body:#CFC9C1;--muted:#9A938B;
--line:rgba(242,239,234,.14);--soft:rgba(242,239,234,.05);--accent:#F06A44;--accent-bg:rgba(240,106,68,.13);--pass:#6FC296;--pass-bg:rgba(111,194,150,.13);
--warn:#E2B347;--warn-bg:rgba(226,179,71,.14);--blue:#86B4E6;--blue-bg:rgba(134,180,230,.13);--grey-bg:rgba(242,239,234,.09)}}}}
*{{box-sizing:border-box}}
html{{scroll-behavior:smooth;scroll-padding-top:120px}}
body{{margin:0;background:var(--bg);color:var(--body);font:15px/1.55 'Geist',system-ui,sans-serif;-webkit-font-smoothing:antialiased}}
a{{color:var(--ink);text-decoration-color:var(--line);text-underline-offset:2px}}
a:hover{{text-decoration-color:var(--accent)}}
h1,h2,h3,h4{{color:var(--ink);font-weight:600;line-height:1.25;margin:0}}
h1{{font-size:30px;letter-spacing:-.01em}} h2{{font-size:22px}} h3{{font-size:15px;margin:22px 0 10px;text-transform:uppercase;letter-spacing:.06em;color:var(--muted)}}
h4{{font-size:13px;margin-bottom:6px}}
.mono{{font-family:'Geist Mono',ui-monospace,monospace;font-size:.92em}}
.layout{{display:grid;grid-template-columns:260px minmax(0,1fr);max-width:1600px;margin:0 auto}}
aside{{position:sticky;top:0;height:100vh;overflow:auto;border-right:1px solid var(--line);padding:22px 14px 40px 20px}}
aside .brand{{font-family:'Geist Mono',monospace;letter-spacing:.12em;color:var(--ink);font-weight:600;font-size:13px;margin:0 0 14px}}
aside a{{display:flex;justify-content:space-between;gap:8px;padding:4px 8px;border-radius:4px;text-decoration:none;color:var(--body);font-size:13.5px}}
aside a:hover,aside a.cur{{background:var(--soft);color:var(--ink)}}
.navg{{font-size:11px;text-transform:uppercase;letter-spacing:.07em;color:var(--muted);margin:14px 8px 4px}}
.navc{{font-family:'Geist Mono',monospace;color:var(--muted);font-size:12px}}
main{{padding:28px 32px 80px;min-width:0}}
.card{{background:var(--card);border:1px solid var(--line);border-radius:6px;padding:24px 26px;margin:0 0 22px;min-width:0}}
.lede p{{max-width:880px}} .lede .main-msg{{color:var(--ink);font-size:16.5px}}
.stats{{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:10px;margin:18px 0 6px}}
.stat{{border:1px solid var(--line);border-radius:5px;padding:10px 12px}} .stat b{{display:block;font:600 22px 'Geist Mono',monospace;color:var(--ink)}} .stat span{{font-size:12.5px;color:var(--muted)}}
dl.terms{{display:grid;grid-template-columns:200px minmax(0,1fr);gap:6px 18px;margin:12px 0 0}} dl.terms dt{{color:var(--ink);font-weight:600}} dl.terms dd{{margin:0}}
.filters{{position:sticky;top:0;z-index:5;background:var(--bg);padding:10px 0 10px;margin:0 0 18px;border-bottom:1px solid var(--line)}}
.frow{{display:flex;flex-wrap:wrap;gap:6px;align-items:center;margin:4px 0}} .frow .fl{{font-size:12px;color:var(--muted);width:44px}}
.chip{{font:12.5px 'Geist',sans-serif;border:1px solid var(--line);background:var(--card);color:var(--muted);padding:4px 10px;border-radius:20px;cursor:pointer;min-height:28px}}
.chip.on{{color:var(--ink);border-color:var(--ink)}} .chip.reset{{border-style:dashed}}
.tree ul{{list-style:none;margin:0;padding:0}} .tgroup{{margin:0 0 14px}} .tg{{font-weight:600;color:var(--ink);margin:0 0 6px}}
.tree li{{padding:5px 0 5px 10px;border-left:1px solid var(--line);margin-left:6px}}
.tree li.t1{{margin-left:30px}} .tree li.t2{{margin-left:54px}}
.tree .path{{color:var(--ink);margin-right:6px;word-break:break-all}} .tline{{display:block;color:var(--muted);font-size:13px}}
.when{{color:var(--muted);font-size:12.5px;margin-left:6px}}
.st{{display:inline-block;font-size:11.5px;padding:1px 7px;border-radius:3px;margin-left:6px;white-space:nowrap}}
.st-exists{{background:var(--pass-bg);color:var(--pass)}} .st-build{{background:var(--blue-bg);color:var(--blue)}}
.st-fakedoor{{background:var(--warn-bg);color:var(--warn)}} .st-missing{{background:var(--accent-bg);color:var(--accent)}} .st-later,.st-outside{{background:var(--grey-bg);color:var(--muted)}}
table.pt,.tablewrap table{{border-collapse:collapse;width:100%}}
.tablewrap{{overflow-x:auto;border:1px solid var(--line);border-radius:5px;margin:8px 0 12px}}
.tablewrap table{{min-width:1240px;font-size:12.5px;table-layout:fixed}}
.tablewrap col.c-id{{width:74px}} .tablewrap col.c-el{{width:10%}} .tablewrap col.c-lab{{width:13%}} .tablewrap col.c-ty{{width:8%}} .tablewrap col.c-pa{{width:72px}} .tablewrap col.c-tr{{width:11%}} .tablewrap col.c-do{{width:8%}} .tablewrap col.c-th{{width:15%}} .tablewrap col.c-ev{{width:9%}} .tablewrap col.c-st{{width:7%}} .tablewrap col.c-src{{width:9%}} .tablewrap col.c-sv{{width:6%}}
.pa{{font-size:11px;padding:1px 6px;border-radius:3px;white-space:nowrap}} .pa-happy{{background:var(--pass-bg);color:var(--pass)}} .pa-unhappy{{background:var(--warn-bg);color:var(--warn)}}
td.trc{{color:var(--body);font-size:12px}} .wo{{display:block;margin-top:4px;font-size:12px;color:var(--muted)}}
tr.err-row td.idc{{box-shadow:inset 3px 0 0 var(--warn)}} tr.way-row td.idc{{box-shadow:inset 3px 0 0 var(--pass)}}
h3.wrong{{color:var(--warn)}} .unhappy{{border-top:1px dashed var(--line);margin-top:18px;padding-top:4px}} h4.sub4{{margin:14px 0 8px;color:var(--muted);font-size:12px;text-transform:uppercase;letter-spacing:.06em}}
.wopage h4{{margin:16px 0 6px}} .tablewrap.wo table{{min-width:760px;table-layout:auto}} .tablewrap.wo table.grid{{min-width:980px}}
td.wo-yes b{{color:var(--pass)}} td.wo-no{{background:var(--accent-bg)}} td.wo-no b{{color:var(--accent)}} td.wo-na b{{color:var(--muted);font-weight:500}}
.won{{display:block;font-size:12px;color:var(--muted)}} ul.gaps{{padding-left:18px}}
td{{overflow-wrap:anywhere}}
th{{text-align:left;font-weight:600;color:var(--ink);background:var(--soft);padding:8px 9px;border-bottom:1px solid var(--line);white-space:nowrap}}
td{{padding:8px 9px;border-bottom:1px solid var(--line);vertical-align:top}}
tr:last-child td{{border-bottom:0}}
td.idc{{white-space:nowrap;color:var(--ink)}} td.srcc{{color:var(--muted);font-size:12px}}
tr.primary-row td{{background:var(--accent-bg)}} tr.primary-row td.idc{{box-shadow:inset 3px 0 0 var(--accent);font-weight:600}}
tr.hide{{display:none}} tr:target td{{outline:2px solid var(--accent);outline-offset:-2px}}
.tag{{display:inline-block;font-size:10.5px;padding:0 5px;border:1px solid var(--line);border-radius:3px;color:var(--muted);margin-left:3px;white-space:nowrap}}
.tag.prop{{color:var(--warn);border-color:var(--warn)}} .tag.app{{color:var(--pass);border-color:var(--pass)}}
.phead{{display:flex;flex-wrap:wrap;align-items:baseline;gap:6px 10px}} .phead .path{{color:var(--muted)}}
.job{{margin:8px 0 12px}}
.primary-call{{border:1px solid var(--accent);background:var(--accent-bg);border-radius:5px;padding:10px 14px;display:flex;flex-wrap:wrap;gap:4px 10px;align-items:baseline}}
.pc-k{{font-size:11px;text-transform:uppercase;letter-spacing:.08em;color:var(--accent);font-weight:600}} .pc-l{{color:var(--ink);font-weight:600}} .pc-d{{flex-basis:100%;font-size:13px}}
.counts{{font-size:12.5px;color:var(--muted);margin:12px 0 0;display:flex;flex-wrap:wrap;gap:6px 12px}} .counts b{{color:var(--ink);font-family:'Geist Mono',monospace}}
.shown{{color:var(--ink)}}
.story{{border-left:2px solid var(--line);padding:2px 0 2px 14px;margin:0 0 14px}} .story.main{{border-left-color:var(--accent)}}
.story-head{{margin:0 0 6px;color:var(--ink)}} .sid{{margin-right:8px;color:var(--muted)}}
.badge{{font-size:10.5px;text-transform:uppercase;letter-spacing:.06em;padding:1px 6px;border-radius:3px;margin-right:6px}} .main-b{{background:var(--accent-bg);color:var(--accent)}}
ul.chain{{list-style:none;margin:0;padding:0}} ul.chain li{{padding:3px 0 3px 16px;position:relative;font-size:14px}}
ul.chain li::before{{content:'';position:absolute;left:3px;top:12px;width:7px;height:1px;background:var(--muted)}}
ul.chain li.d1{{margin-left:22px}} ul.chain li.d2{{margin-left:44px}}
a.ref{{text-decoration:none;white-space:normal}} a.ref .mono{{color:var(--ink);border-bottom:1px solid var(--line)}} .reflabel{{color:var(--muted)}}
.gap{{color:var(--warn)}}
p.src{{font-size:12px;color:var(--muted);margin:4px 0 0}}
.flags{{display:grid;grid-template-columns:1fr 1fr;gap:16px;margin-top:6px}} .flags ul{{margin:0;padding-left:18px;font-size:13.5px}}
.note{{font-size:13px;color:var(--muted);margin:12px 0 0}} .rec{{color:var(--ink)}} .needs{{border-color:var(--accent)}}
.pt td,.pt th{{font-size:13.5px}} .num{{font-family:'Geist Mono',monospace;text-align:right}}
ul.idx{{list-style:none;padding:0;margin:0}} ul.idx>li{{border-top:1px solid var(--line);padding:10px 0}}
.ig{{color:var(--ink);font-weight:600;margin:0}} .is{{font-size:12.5px;color:var(--muted);margin:2px 0 6px}}
ul.acts{{margin:0;padding-left:18px;font-size:13.5px;columns:2;column-gap:28px}} ul.acts li{{break-inside:avoid}} .pg{{color:var(--muted);font-size:12px}}
ol.qs{{padding-left:0;list-style:none}} ol.qs li{{border-top:1px solid var(--line);padding:10px 0}} ol.qs p{{margin:0}}
.tablewrap.kit table{{min-width:760px;table-layout:auto;font-size:12.5px}} .kitpage h4{{margin:16px 0 6px}}
.kitpage .tablewrap.kit table{{min-width:520px}} td.kn{{color:var(--ink);font-weight:600;white-space:nowrap}} .tablewrap.kit td{{overflow-wrap:normal}} .tablewrap.kit td.num,.tablewrap.kit th.num{{white-space:nowrap}} .gap0{{color:var(--muted)}}
.tablewrap.kit details summary{{cursor:pointer;color:var(--ink)}} .tablewrap.kit details a{{display:inline-block;margin:2px 8px 0 0}}
.mat table{{min-width:0}} .mat th.rot{{vertical-align:bottom;white-space:nowrap;padding:8px 4px}} .mat th.rot span{{writing-mode:vertical-rl;transform:rotate(180deg)}}
.mat td.num{{text-align:center;padding:6px 4px;min-width:26px}} .mat td.z{{background:var(--soft)}} .mat td.pn{{white-space:nowrap;position:sticky;left:0;background:var(--card)}}
.mat td.sh{{font-size:12px;color:var(--muted);min-width:180px}}
.mobnav{{display:none}}
footer.ver{{font-size:12px;color:var(--muted);margin-top:30px}}
@media (max-width:900px){{
 .layout{{display:block}} aside{{display:none}}
 main{{padding:16px 16px 60px}}
 .mobnav{{display:block;background:var(--card);border:1px solid var(--line);border-radius:6px;margin:0 0 14px}}
 .mobnav summary{{padding:12px 14px;color:var(--ink);font-weight:600;cursor:pointer;min-height:44px}}
 .mobnav nav{{padding:0 8px 10px}} .mobnav a{{display:flex;justify-content:space-between;padding:8px;text-decoration:none;color:var(--body);font-size:14px;min-height:36px}}
 .card{{padding:18px 16px}} h1{{font-size:24px}}
 .stats{{grid-template-columns:repeat(2,minmax(0,1fr))}}
 dl.terms{{grid-template-columns:1fr}} dl.terms dd{{margin-bottom:8px}}
 .flags{{grid-template-columns:1fr}} ul.acts{{columns:1}}
 .tree li.t1{{margin-left:18px}} .tree li.t2{{margin-left:30px}}
 .filters{{position:static}} html{{scroll-padding-top:12px}}
 .ptwrap{{overflow-x:auto}} .ptwrap table{{min-width:560px}}
}}
</style></head>
<body>
<div class="layout">
<aside aria-label="Pages"><p class="brand">{html.escape(PRODUCT)}</p><nav>{''.join(nav)}{''.join(navp)}{''.join(nav_tail)}</nav></aside>
<main>
<details class="mobnav"><summary>Pages and sections</summary><nav>{''.join(nav)}{''.join(navp)}{''.join(nav_tail)}</nav></details>
<section id="overview" class="card lede">
<h1>{esc(m['title'])}</h1>
<p>{esc(m['purpose'])}</p>
<p class="main-msg">{esc(m['main_message'])}</p>
<div class="stats">{stats}</div>
<p>{esc(m['reading'])}</p>
{tt}
<p class="src">More terms and every source key are at the end, under <a href="#terms">Terms and sources</a>. {esc(m['status'])}</p>
</section>
{gsec_gaps}
<section id="sitemap" class="card"><h2>Sitemap</h2><p>Every page with its path, audience and job. Pages with a link have an element table below.</p>{''.join(sm)}
<h3>Primary call to action by page</h3><div class="ptwrap"><table class="pt"><thead><tr><th>Page</th><th>Path</th><th>Primary CTA</th><th class="num">Elements</th></tr></thead><tbody>{prim_rows}</tbody></table></div></section>
<div class="filters" role="group" aria-label="Filter element rows">
<div class="frow"><span class="fl">Type</span>{filt_t}</div>
<div class="frow"><span class="fl">Path</span>{filt_p}</div>
<div class="frow"><span class="fl">State</span>{filt_s}<button type="button" class="chip reset" id="reset">Show all</button></div>
</div>
{''.join(gsec)}
{''.join(psec)}
{''.join(wsec)}
{''.join(isec)}
{h_inventory()}
{''.join(qsec)}
{''.join(tsec)}
<footer class="ver">Built from elements.json by build.py, data dated {esc(TODAY)}, page built {date.today().isoformat()}. Elements: {total_elements} on {len(DATA['pages'])} pages plus {len(DATA['global']['elements'])} global.</footer>
</main></div>
<script>
(function(){{
 var ft=new Set({json.dumps(TYPE_ORDER)}), fs=new Set({json.dumps(STATE_ORDER)}), fp=new Set(["happy","unhappy"]);
 function apply(){{
  document.querySelectorAll('tr[data-type]').forEach(function(r){{
   r.classList.toggle('hide', !(ft.has(r.dataset.type) && fs.has(r.dataset.state) && fp.has(r.dataset.path)));
  }});
  document.querySelectorAll('section.page').forEach(function(s){{
   var rows=s.querySelectorAll('tr[data-type]'), n=0;
   rows.forEach(function(r){{ if(!r.classList.contains('hide')) n++; }});
   var el=document.getElementById('shown-'+s.dataset.page); if(el) el.textContent=n+' of '+rows.length+' elements shown';
   document.querySelectorAll('#navc-'+s.dataset.page).forEach(function(c){{ c.textContent = n===rows.length ? rows.length : n+'/'+rows.length; }});
  }});
 }}
 function wire(attr,set){{
  document.querySelectorAll('[data-'+attr+']').forEach(function(b){{
   b.addEventListener('click',function(){{
    var v=b.getAttribute('data-'+attr);
    if(set.has(v)) set.delete(v); else set.add(v);
    b.classList.toggle('on', set.has(v)); b.setAttribute('aria-pressed', set.has(v));
    apply();
   }});
  }});
 }}
 wire('ft',ft); wire('fs',fs); wire('fp',fp);
 document.getElementById('reset').addEventListener('click',function(){{
  {json.dumps(TYPE_ORDER)}.forEach(function(t){{ft.add(t)}}); {json.dumps(STATE_ORDER)}.forEach(function(s){{fs.add(s)}}); fp.add('happy'); fp.add('unhappy');
  document.querySelectorAll('.chip[data-ft],.chip[data-fs],.chip[data-fp]').forEach(function(b){{b.classList.add('on');b.setAttribute('aria-pressed','true')}});
  apply();
 }});
 document.querySelectorAll('.mobnav a').forEach(function(a){{a.addEventListener('click',function(){{a.closest('details').open=false;}});}});
 var links=document.querySelectorAll('aside a[href^="#"]');
 if('IntersectionObserver' in window){{
  var io=new IntersectionObserver(function(es){{es.forEach(function(e){{ if(e.isIntersecting){{
   links.forEach(function(l){{ l.classList.toggle('cur', l.getAttribute('href')==='#'+e.target.id); }}); }} }});}},{{rootMargin:'-10% 0px -80% 0px'}});
  document.querySelectorAll('main section[id]').forEach(function(s){{io.observe(s)}});
 }}
}})();
</script>
</body></html>
"""


if __name__ == "__main__":
    md = build_md()
    (HERE / "UX-ELEMENTS-CATALOG.md").write_text(md)
    page = build_html()
    (HERE / "UX-ELEMENTS-CATALOG.html").write_text(page)
    for name, text in (("md", md), ("html", page)):
        bad = re.findall("[\u2014\u2013]", text)
        if bad and DATA["meta"]["no_dashes"]:
            print(f"warning: {len(bad)} em or en dashes in {name}")
    if GAPS:
        print(f"gaps found in the app ({len(GAPS)}):\n  " + "\n  ".join(GAPS))
    print(f"pages {len(DATA['pages'])}, page elements {total_elements}, global {len(DATA['global']['elements'])}, "
          f"html {len(page)//1024} KB")
    for p in DATA["pages"]:
        print(f"  {p['id']:5} {len(p['elements']):3}  primary {p['primary']} {ELEMS[p['primary']][1]['label']}")
