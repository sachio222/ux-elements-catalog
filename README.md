# UX elements catalog

Plan every page of a website or mobile app before you design it, then hand that plan to your design or coding tool to make the designs.

This is a skill for AI coding agents such as Claude Code. You point it at your app's code or at a product plan. It writes down, page by page, what a visitor wants to do there and every element that helps them: buttons, form fields, sections of text, error messages and ways back out. Each page gets one primary button. From that list it works out every component your UI kit needs (a UI kit is the shared set of buttons, fields, menus and other parts every page is built from). You read it all on one web page, then give it to whatever makes your designs.

## Install

You need Python 3 (no packages) and an AI coding agent that can read skills.

**Claude Code, for all your projects:**

```
git clone https://github.com/sachio222/ux-elements-catalog ~/.claude/skills/ux-elements-catalog
```

**Claude Code, for one project only:** run this from the project folder.

```
git clone https://github.com/sachio222/ux-elements-catalog .claude/skills/ux-elements-catalog
```

**Another agent:** clone it into that agent's skills folder. If your agent has no skills folder, clone it anywhere and start your request with "Read SKILL.md in that folder and follow it."

To update later, run `git pull` inside the folder.

## Make a catalog

Open your agent in your project and ask in plain words. For an app you already have:

> Make a UX elements catalog for this repo.

For something not built yet:

> Make a UX elements catalog for the app described in docs/plan.md.

For a mobile app, the same request works; each screen counts as a page.

The agent finds your pages or screens (it reads Next.js, Expo, React Navigation, React Router, SvelteKit, Flutter, SwiftUI, Jetpack Compose and more), catalogs each one and builds the reading page. It asks you only about real decisions, such as prices, names or promises to customers. Everything else gets a sensible default, listed on the page under "Defaults applied, change if wrong".

You get a folder with three files:

| File | Use it for |
|---|---|
| `UX-ELEMENTS-CATALOG.html` | Reading. Open it in any browser; it works offline. |
| `UX-ELEMENTS-CATALOG.md` | Handing to your design or coding tool. |
| `elements.json` | The data. To change the catalog, ask your agent to edit this file and rebuild. |

## Check it before you design

Open the HTML page and check:

1. **Each page's main story and primary button.** When the agent catalogs existing code, it drafts these, because code cannot say what a visitor wants. Fix any that are wrong.
2. **Defaults applied.** Change any you disagree with.
3. **Gaps found in the app** (for an existing app) and the ways-out grid. Each one is a place a person can get stuck today, such as a form with no error message or a screen with no way back. Decide which to fix in the new design.

Tell your agent what to change, for example "HOME's primary button should be Book a demo", and it updates the catalog.

## Get designs out of it

The catalog says what every page holds and does. It holds no visual design: colors, fonts, spacing and layout come from your design tool or your designer. Work in this order.

### Step 1: build the UI kit

The "Component inventory" section lists every part the product needs (buttons, fields, cards, menus, error messages), with how often each is used, which states it needs and its longest label. Give it to your tool first, so every page is built from the same parts:

> Build a UI kit from the Component inventory in UX-ELEMENTS-CATALOG.md. Make one component for each kit part, with every state the inventory lists for it (default, error, disabled, loading, empty). Show each one at its longest label. Use these design tokens: [your colors, fonts and spacing, or "propose a set and show me first"].

### Step 2: design one page at a time

Each page in `UX-ELEMENTS-CATALOG.md` has its own section. Give your tool one page per request:

> Design the Sign up page from UX-ELEMENTS-CATALOG.md, using our UI kit. Place its elements in the listed order with the exact labels. The element marked primary is the one primary button on the page. Include every element under "When things go wrong", each error state with the way out it names. Use the parts listed under "Kit parts on this page". Leave out anything the page does not list.

For a mobile app, say "screen" and name the platform, for example "Design the Visit screen for iOS".

### Step 3: check each page against its table

> Check the Sign up page you built against its element table in UX-ELEMENTS-CATALOG.md. List any element that is missing, out of order or labeled differently, and any error state without its way out.

### Which file to give which tool

| You design with | Give it |
|---|---|
| A coding agent in your repo (Claude Code, Cursor and others) | The path to `UX-ELEMENTS-CATALOG.md`; the prompts above work as written. |
| A chat-based app builder (v0, Lovable, Bolt and others) | Paste one page's section from `UX-ELEMENTS-CATALOG.md` with the Step 2 prompt; paste the Component inventory for Step 1. |
| A designer, or Figma by hand | The HTML page. Each page's element table is the content list for one frame, top to bottom. |

## What is in a catalog

- A sitemap of every page or screen.
- For each page: what visitors want there, as user stories ("As a new visitor, I want to create an account quickly"); the needs behind each story; and every element in reading order, with its label, what it does and the analytics event it sends.
- What happens when things go wrong: validation errors, failed payments, offline, permission denied, and the way out of each.
- A ways-out grid: can a person go back, cancel, undo, get help, and leave without losing their work, on every page.
- A component inventory, product-wide and per page.
- Open decisions, each with a recommended answer, and the defaults that were applied.

## What is in this folder

| Path | What it is |
|---|---|
| `SKILL.md` | The instructions your agent follows. |
| `scripts/build.py` | Builds the HTML and Markdown from `elements.json`, and refuses a planned catalog with gaps. |
| `scripts/routes.py` | Lists the pages and screens of an existing app. |
| `templates/starter.elements.json` | A small example catalog, for its shape. |
| `assets/fonts/` | Geist and Geist Mono, embedded in the HTML page. |

## License

MIT, see `LICENSE`. The fonts in `assets/fonts/` keep their own SIL Open Font License.
