#!/usr/bin/env python3
"""List the pages and screens of an existing app (ux-elements-catalog skill).

    python3 <skill-folder>/scripts/routes.py <repo> [--json]

Finds every app in the repo (monorepos included) and prints, per app:
pages or screens with their path, group and file:line; layouts and
navigators (shared shells such as a header, tab bar or drawer); error,
not-found and loading screens; component folders (the UI kit in use); and
analytics event names called in code.

Web: Next.js (app and pages routers), Expo Router, SvelteKit, Remix and
React Router file routes, Nuxt, Astro, React Router in code, Rails, Django.
Mobile: Expo Router, React Navigation, Flutter (GoRouter and route maps),
SwiftUI, Jetpack Compose.

It reads file names and a few patterns only. It does not read component
trees; the agent reads each listed file for elements. It never opens
.env files.
"""
import json
import os
import re
import sys
from pathlib import Path

SKIP_DIRS = {"node_modules", ".git", ".next", ".expo", ".svelte-kit", ".nuxt", ".output", "dist", "build",
             "out", "coverage", "Pods", "DerivedData", ".gradle", ".dart_tool", "vendor", "__pycache__",
             ".venv", "venv", ".turbo", ".vercel", "android/app/build"}
CODE_EXT = {".tsx", ".ts", ".jsx", ".js", ".mjs", ".vue", ".svelte", ".astro", ".dart", ".swift", ".kt", ".py", ".rb"}
JS_EXT = (".tsx", ".ts", ".jsx", ".js")
KIT_DIR_NAMES = {"ui", "components", "design-system", "primitives", "widgets", "elements"}
EVENT_RE = re.compile(r"""(?:\btrack|\bcapture|\blogEvent|\.track|\.capture|\.logEvent|gtag\(\s*['"]event['"]\s*,)\s*\(?\s*['"]([A-Za-z][\w.:\- ]{1,60})['"]""")


def walk(root):
    for d, dirs, files in os.walk(root):
        dirs[:] = [x for x in dirs if x not in SKIP_DIRS and not x.startswith(".")]
        for f in files:
            if f.startswith(".env"):
                continue
            yield Path(d) / f


def read(p):
    try:
        return p.read_text(errors="ignore")
    except OSError:
        return ""


def line_of(text, pos):
    return text.count("\n", 0, pos) + 1


def deps_of(pkg):
    try:
        j = json.loads(pkg.read_text())
    except (OSError, ValueError):
        return set()
    return set(j.get("dependencies", {})) | set(j.get("devDependencies", {}))


def rel(p, root):
    return str(p.relative_to(root))


def row(fw, kind, path, group, f, root, line=1, note=""):
    return {"framework": fw, "kind": kind, "path": path, "group": group, "file": f"{rel(f, root)}:{line}", "note": note}


# ---------------------------------------------------------------- file-based routers
def segs_to_path(parts):
    out, group = [], ""
    for s in parts:
        if s.startswith("(") and s.endswith(")"):
            group = s[1:-1]
            continue
        if s in ("index", "_index"):
            continue
        out.append(s)
    return "/" + "/".join(out), group


def next_app(app, root):
    kinds = {"page": "page", "layout": "layout", "template": "layout", "error": "error", "global-error": "error",
             "not-found": "not-found", "loading": "loading", "route": "api"}
    rows = []
    for f in walk(app):
        if f.suffix not in (".tsx", ".jsx", ".ts", ".js", ".mdx") or f.stem not in kinds:
            continue
        parts = list(f.relative_to(app).parent.parts)
        if any(p.startswith("_") for p in parts):
            continue
        slot = next((p for p in parts if p.startswith("@")), "")
        parts = [p for p in parts if not p.startswith("@")]
        path, group = segs_to_path(parts)
        rows.append(row("Next.js app router", kinds[f.stem], path, group or (parts[0] if parts else ""), f, root,
                        note=f"parallel slot {slot}" if slot else ""))
    return rows


def next_pages(pages, root):
    rows = []
    for f in walk(pages):
        if f.suffix not in JS_EXT + (".mdx",):
            continue
        parts = list(f.relative_to(pages).with_suffix("").parts)
        if parts[0] == "api":
            continue
        if parts[-1] in ("_app", "_document"):
            rows.append(row("Next.js pages router", "layout", "/", "", f, root))
            continue
        kind = {"404": "not-found", "500": "error", "_error": "error"}.get(parts[-1], "page")
        path, group = segs_to_path(parts)
        rows.append(row("Next.js pages router", kind, path, group or (parts[0] if len(parts) > 1 else ""), f, root))
    return rows


def expo_router(app, root):
    rows = []
    for f in walk(app):
        if f.suffix not in JS_EXT:
            continue
        stem = f.stem
        parts = list(f.relative_to(app).parent.parts) + [stem]
        if stem in ("+html", "+native-intent") or stem.endswith("+api"):
            continue
        if stem == "_layout":
            src = read(f)
            nav = next((n for n, pat in (("tab bar", r"<Tabs\b"), ("drawer", r"<Drawer\b"), ("stack", r"<Stack\b"),
                                         ("slot", r"<Slot\b")) if re.search(pat, src)), "layout")
            wrap = re.search(r"<([A-Z]\w*)\b[^>]*>\s*<Slot\b", src)
            if nav == "slot" and wrap:
                nav = f"custom shell {wrap.group(1)}"
            path, group = segs_to_path(parts[:-1])
            rows.append(row("Expo Router", "navigator", path, group, f, root, note=nav))
            continue
        kind = "not-found" if stem == "+not-found" else "screen"
        path, group = segs_to_path(parts if kind == "screen" else parts[:-1])
        modal = re.search(r"presentation\s*:\s*['\"](modal|formSheet|transparentModal)", read(f))
        rows.append(row("Expo Router", kind, path, group, f, root, note=f"presented as {modal.group(1)}" if modal else ""))
    return rows


def sveltekit(routes, root):
    kinds = {"+page": "page", "+layout": "layout", "+error": "error"}
    rows = []
    for f in walk(routes):
        if f.stem not in kinds or f.suffix != ".svelte":
            continue
        path, group = segs_to_path(list(f.relative_to(routes).parent.parts))
        rows.append(row("SvelteKit", kinds[f.stem], path, group, f, root))
    return rows


def flat_routes(routes, root, fw):
    rows = []
    for f in walk(routes):
        if f.suffix not in JS_EXT:
            continue
        name = f.stem if f.parent == routes else f.parent.name
        if f.parent != routes and f.stem != "route":
            continue
        parts = [p for p in name.split(".") if p]
        segs = []
        for p in parts:
            if p in ("_index", "index"):
                continue
            if p.startswith("_"):
                continue
            segs.append(":" + p[1:] if p.startswith("$") else p)
        rows.append(row(fw, "page", "/" + "/".join(segs), parts[0] if parts else "", f, root))
    return rows


def dir_pages(pages, root, fw, exts):
    rows = []
    for f in walk(pages):
        if f.suffix not in exts:
            continue
        parts = list(f.relative_to(pages).with_suffix("").parts)
        kind = "not-found" if parts[-1] in ("404", "[...slug]") and fw == "Astro" and parts[-1] == "404" else "page"
        path, group = segs_to_path(parts)
        rows.append(row(fw, kind, path, group or (parts[0] if len(parts) > 1 else ""), f, root))
    return rows


# ---------------------------------------------------------------- code-defined routers
def code_routes(app_root, root):
    rows = []
    for f in walk(app_root):
        if f.suffix not in CODE_EXT:
            continue
        src = read(f)
        if f.suffix in JS_EXT:
            if re.search(r"create\w*Navigator\s*(?:<[^>]*>)?\s*\(", src):
                navs = dict(re.findall(r"(?:const|let|var)\s+(\w+)\s*=\s*create(\w*?)Navigator\s*(?:<[^>]*>)?\s*\(", src))
                for m in re.finditer(r"<(\w+)\.Screen\b(.*?)/?>", src, re.S):
                    name = re.search(r"""\bname\s*=\s*\{?\s*['"]([^'"]+)['"]""", m.group(2))
                    comp = re.search(r"component\s*=\s*\{\s*(\w+)", m.group(2))
                    if name:
                        kind = navs.get(m.group(1), "")
                        rows.append(row("React Navigation", "screen", name.group(1), f"{kind} navigator".strip(), f, root,
                                        line_of(src, m.start()), f"component {comp.group(1)}" if comp else ""))
                for var, kind in navs.items():
                    pos = re.search(rf"\b{var}\s*=\s*create", src).start()
                    shell = {"BottomTab": "tab bar", "MaterialBottomTab": "tab bar", "MaterialTopTab": "top tabs",
                             "Drawer": "drawer"}.get(kind, "stack")
                    rows.append(row("React Navigation", "navigator", var, kind, f, root, line_of(src, pos), shell))
            if re.search(r"createBrowserRouter|createHashRouter|createRoutesFromElements|<Routes\b|RouterProvider", src):
                for m in re.finditer(r"""<Route\b[^>]*?\bpath\s*=\s*\{?\s*['"]([^'"]+)['"]""", src):
                    rows.append(row("React Router", "page", m.group(1), "", f, root, line_of(src, m.start())))
                if "createBrowserRouter" in src or "createHashRouter" in src:
                    for m in re.finditer(r"""\bpath\s*:\s*['"]([^'"]+)['"]""", src):
                        rows.append(row("React Router", "page", m.group(1), "", f, root, line_of(src, m.start())))
        elif f.suffix == ".dart":
            for m in re.finditer(r"""GoRoute\s*\(\s*(?:name\s*:\s*['"][^'"]*['"]\s*,\s*)?path\s*:\s*['"]([^'"]+)['"]""", src):
                rows.append(row("Flutter GoRouter", "screen", m.group(1), "", f, root, line_of(src, m.start())))
            if re.search(r"\broutes\s*:\s*\{", src):
                for m in re.finditer(r"""['"](/[^'"]*)['"]\s*:\s*\(\s*\w*\s*\)\s*=>""", src):
                    rows.append(row("Flutter route map", "screen", m.group(1), "", f, root, line_of(src, m.start())))
            if re.search(r"\b(BottomNavigationBar|NavigationBar|TabBar|Drawer)\s*\(", src):
                rows.append(row("Flutter", "navigator", f.stem, "", f, root, 1, "tab bar or drawer"))
        elif f.suffix == ".swift":
            for m in re.finditer(r"struct\s+(\w+)\s*:\s*(?:some\s+)?View\b", src):
                name = m.group(1)
                body = src[m.start():]
                nxt = re.search(r"\n(?:struct|class|enum|extension)\s", body[1:])
                body = body[: nxt.start() + 1] if nxt else body
                shell = next((n for n, pat in (("tab bar", r"\bTabView\b"), ("stack", r"\bNavigationStack\b|\bNavigationView\b"),
                                               ("split view", r"\bNavigationSplitView\b")) if re.search(pat, body)), "")
                pres = sorted(set(re.findall(r"\.(sheet|fullScreenCover|popover|alert|confirmationDialog)\s*\(", body)))
                if shell:
                    rows.append(row("SwiftUI", "navigator", name, "", f, root, line_of(src, m.start()), shell))
                elif re.search(r"(Screen|View|Page)$", name) and name not in ("ContentView",) or name == "ContentView":
                    rows.append(row("SwiftUI", "screen", name, "", f, root, line_of(src, m.start()),
                                    "presents " + ", ".join(pres) if pres else ""))
        elif f.suffix == ".kt":
            for m in re.finditer(r"""composable\s*\(\s*(?:route\s*=\s*)?['"]([^'"]+)['"]""", src):
                rows.append(row("Jetpack Compose", "screen", m.group(1), "", f, root, line_of(src, m.start())))
            for m in re.finditer(r"composable<(\w+)>", src):
                rows.append(row("Jetpack Compose", "screen", m.group(1), "", f, root, line_of(src, m.start())))
            if re.search(r"\b(NavigationBar|BottomNavigation|ModalNavigationDrawer|NavigationRail)\s*\(", src):
                rows.append(row("Jetpack Compose", "navigator", f.stem, "", f, root, 1, "tab bar, rail or drawer"))
        elif f.name == "routes.rb":
            for m in re.finditer(r"""^\s*(get|post|patch|put|delete|resources?|root)\b\s*[:'"]?([\w/:\-]*)""", src, re.M):
                rows.append(row("Rails", "page", (m.group(1) + " " + m.group(2)).strip(), "", f, root, line_of(src, m.start())))
        elif f.name == "urls.py":
            for m in re.finditer(r"""\b(?:re_)?path\s*\(\s*r?['"]([^'"]*)['"]""", src):
                rows.append(row("Django", "page", "/" + m.group(1), "", f, root, line_of(src, m.start())))
    return rows


# ---------------------------------------------------------------- per app
def first_dir(base, *names):
    for n in names:
        if (base / n).is_dir():
            return base / n
    return None


def app_roots(root):
    roots = []
    for f in walk(root):
        if f.name in ("package.json", "pubspec.yaml", "Package.swift", "build.gradle", "build.gradle.kts", "Gemfile", "manage.py") \
                or f.suffix == ".xcodeproj":
            roots.append(f.parent)
    for d, dirs, _ in os.walk(root):
        dirs[:] = [x for x in dirs if x not in SKIP_DIRS and not x.startswith(".")]
        if any(x.endswith(".xcodeproj") for x in os.listdir(d)):
            roots.append(Path(d))
    out = []
    for r in sorted(set(roots), key=lambda p: len(p.parts)):
        out.append(r)
    return out or [root]


def scan_app(base, root):
    rows, fws = [], []
    deps = deps_of(base / "package.json") if (base / "package.json").exists() else set()
    if "expo-router" in deps and (d := first_dir(base, "app", "src/app")):
        fws.append("Expo Router")
        rows += expo_router(d, root)
    elif "next" in deps:
        if d := first_dir(base, "app", "src/app"):
            fws.append("Next.js app router")
            rows += next_app(d, root)
        if d := first_dir(base, "pages", "src/pages"):
            fws.append("Next.js pages router")
            rows += next_pages(d, root)
    if "@sveltejs/kit" in deps and (d := first_dir(base, "src/routes")):
        fws.append("SvelteKit")
        rows += sveltekit(d, root)
    if ({"@remix-run/react", "@react-router/dev"} & deps) and (d := first_dir(base, "app/routes")):
        fws.append("Remix / React Router file routes")
        rows += flat_routes(d, root, "Remix / React Router")
    if "nuxt" in deps and (d := first_dir(base, "pages", "app/pages")):
        fws.append("Nuxt")
        rows += dir_pages(d, root, "Nuxt", {".vue"})
    if "astro" in deps and (d := first_dir(base, "src/pages")):
        fws.append("Astro")
        rows += dir_pages(d, root, "Astro", {".astro", ".md", ".mdx"})
    code = code_routes(base, root)
    fws += sorted({r["framework"] for r in code} - set(fws))
    rows += code
    used = {m.group(1) for r in code if (m := re.match(r"component (\w+)", r["note"]))}
    if used:
        for f in walk(base):
            if f.suffix in JS_EXT and f.parent.name.lower() in ("screens", "pages", "views") and f.stem not in used:
                rows.append(row("React Navigation", "unregistered", f.stem, "", f, root, 1,
                                "screen file not registered in any navigator"))
    return fws, rows


def kit_folders(base, root):
    """Top-most folders named like a component library, with code files counted recursively."""
    out = []
    for d, dirs, _ in os.walk(base):
        dirs[:] = [x for x in dirs if x not in SKIP_DIRS and not x.startswith(".")]
        p = Path(d)
        if p.name.lower() in KIT_DIR_NAMES and not any(Path(o["path"]) in p.parents for o in out):
            n = sum(1 for f in walk(p) if f.suffix in CODE_EXT)
            if n >= 3:
                out.append({"folder": rel(p, root), "files": n, "path": str(p)})
    return [{"folder": o["folder"], "files": o["files"]} for o in out]


def events(base, root):
    found = {}
    for f in walk(base):
        if f.suffix in CODE_EXT:
            src = read(f)
            for m in EVENT_RE.finditer(src):
                found.setdefault(m.group(1), f"{rel(f, root)}:{line_of(src, m.start())}")
    return found


def main():
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    root = Path(args[0] if args else ".").resolve()
    seen, report = set(), []
    for base in app_roots(root):
        fws, rows = scan_app(base, root)
        rows = [r for r in rows if (r["framework"], r["kind"], r["path"], r["file"]) not in seen]
        seen |= {(r["framework"], r["kind"], r["path"], r["file"]) for r in rows}
        if not rows:
            continue
        report.append({"app": rel(base, root) if base != root else root.name, "frameworks": fws, "routes": rows,
                       "kit_folders": kit_folders(base, root), "events": events(base, root)})
    if "--json" in sys.argv:
        print(json.dumps(report, indent=1))
        return
    if not report:
        print("No pages or screens found. Read the app's entry file and navigation code by hand.")
        return
    order = ["navigator", "layout", "page", "screen", "error", "not-found", "loading", "unregistered", "api"]
    for a in report:
        print(f"## {a['app']}  ({', '.join(a['frameworks'])})")
        for kind in order:
            rs = [r for r in a["routes"] if r["kind"] == kind]
            if not rs:
                continue
            print(f"\n{kind} ({len(rs)})")
            for r in sorted(rs, key=lambda r: (r["group"], r["path"])):
                g = f"  [{r['group']}]" if r["group"] else ""
                n = f"  {r['note']}" if r["note"] else ""
                print(f"  {r['path']:<40}{g}  {r['file']}{n}")
        if a["kit_folders"]:
            print("\ncomponent folders")
            for k in a["kit_folders"]:
                print(f"  {k['folder']}  ({k['files']} files)")
        if a["events"]:
            print(f"\nanalytics events in code ({len(a['events'])})")
            for e, where in sorted(a["events"].items()):
                print(f"  {e:<40}{where}")
        else:
            print("\nanalytics events in code: none found (no track, capture, logEvent or gtag calls with a literal name)")
        print()


if __name__ == "__main__":
    main()
