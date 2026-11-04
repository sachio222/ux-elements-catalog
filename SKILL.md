---
name: ux-elements-catalog
description: Use before any UI design, wireframe, UI kit or build of a website, landing pages or app. Produces a UX elements catalog: a sitemap, then for each page the user stories ("As a [role], I want to..."), needs chains ("In order to [see my options / understand that / decide], I need..."), and every element those needs call for (content and actions) in reading order, with one primary call to action per page, secondary and tertiary CTAs, component-level parts (each pricing tier, login, logout), unhappy paths with error states and ways out, a ways-out grid, analytics events, build state, and open questions with defaults. The catalog also gives a UI kit its component inventory and the states each component needs. Outputs a self-contained HTML reading page and a Markdown record from one JSON file. Trigger on "UX elements catalog", "UI elements catalog", "design elements catalog", "elements catalog", "actions catalog", "sitemap and elements", "what goes on each page", "catalog the pages", "what components do we need", "catalog this repo", "discover the UI", "audit the screens", or any request to plan or audit a site's or mobile app's pages or screens before design.
---

# UX elements catalog

A method for planning pages before anyone designs them. Start with a sitemap. For each page, write what the visitor wants to do there, then list every element that helps them do it: buttons, inputs, calculators, sections of text, error messages. Mark one primary call to action per page. The catalog fixes what each page must do, for whom, and why each element exists, so wireframes, a UI kit and visual design all start from an agreed list. It makes no visual decisions.

It works the same for a website and a mobile app. On mobile, each screen is a page: its `path` is the route or screen name, and tab bars, navigation headers and drawers are shared shells.

Two ways in:

- **Plan** (`meta.mode: "plan"`, the default): no app yet, or a redesign. Start from the product plan and follow the method below. The build refuses a catalog with gaps, so the plan has none.
- **Discover** (`meta.mode: "discover"`): an app already exists. Point the skill at its repo. The catalog records what the app does today; the build still runs when the app breaks a rule and lists each break under "Gaps found in the app". See "Discover from an existing app".

Starter: `templates/starter.elements.json` (two pages, every field shown, passes every check). Copy it for its shape; replace all of its content.

## Before you start

| Step | Action |
|---|---|
| 0.1 | If the user has a house style guide for copy, load it before writing labels, and check the finished labels against it. |
| 0.2 | Collect sources: the product plan, audience and offer decisions, pricing, research (conversion, buyer jobs, voice of customer), legal notes, and the existing app's code if one exists. Never open or print `.env` files. Never copy personal data or secrets from code or fixtures into the catalog (names, phone numbers, emails, keys); write "[sample phone number]" instead. |
| 0.3 | Give each source a short key (for example `PLAN`, `AUD`, `APP`). Every story, element and default cites its key and section (for code, `APP file:line`). |
| 0.4 | Make a folder for the catalog: beside the project's planning docs, or in `docs/ux-catalog/` of the repo, or anywhere the user names when the repo must stay untouched. Write `elements.json` there. |

## Discover from an existing app

Code shows what exists and what it does. It cannot show what a visitor wants. So discovery fills in pages, elements, labels, events and failure states from the code, and drafts the stories and primary CTAs for the user to confirm.

| Step | Action |
|---|---|
| D.1 | Run `python3 <skill-folder>/scripts/routes.py <repo>` (add `--json` for the data). It lists, per app in the repo: pages or screens with path, group and file:line; layouts and navigators (header, tab bar, drawer, stack); error, not-found and loading screens; screen files no navigator registers; component folders; and analytics event names called in code. It covers Next.js, Expo Router, React Navigation, React Router, Remix, SvelteKit, Nuxt, Astro, Flutter, SwiftUI, Jetpack Compose, Rails and Django. When it finds nothing, read the app's entry file and navigation code by hand. Set `meta.mode` to `"discover"`. |
| D.2 | Sitemap from the list: each page or screen becomes a page entry, route groups (`(marketing)`, `(tabs)`, a navigator) become sitemap groups, `state: exists`. Leave out API routes, and dev or test pages unless the user wants them. An unregistered or empty screen file goes in the sitemap only, with `page: null`, `state: later` and a note. |
| D.3 | Shared shells from layouts and navigators: header, footer, sidebar, tab bar, navigation header, drawer. Catalog their parts once as `GLB-` elements in a named global group, and list the group names in each page's `shells`. |
| D.4 | Elements from each page's file and the components it renders, in render order: headings, text blocks, buttons, links, inputs, forms, toggles, lists, modals, sheets and alerts. See "Labels, kit names and events" for what goes in each field. Leave out UI the code never renders, and say so in the page's `notes`. |
| D.5 | Unhappy paths from failure-handling code: error and not-found screens, error boundaries, validation messages and schemas, toasts, empty and loading states, catch blocks, offline handling, permission prompts. Each becomes a row with `path: unhappy` and its trigger in plain words. A failure the app does not handle (it fails silently, or the error offers no way forward) is still cataloged: an `error` row with `state: missing` and no `wayout`. The build lists it as a gap. |
| D.6 | Optional: run the app (browser for web, simulator or Expo web for mobile) and walk each route. This catches text built at runtime, signed-in-only parts and conditional states that reading code misses. |
| D.7 | Draft one main story and primary CTA per page from what the page does (usually its most prominent action). Record the drafts together as one `open_questions` entry with `status: "default"`. In the final report, ask the user once to confirm them; do not ask about each. |
| D.8 | Build. Report the "Gaps found in the app" first, then the "no" answers in the ways-out grid; each is a way a person can get stuck today. If a planned catalog exists for the same product, compare the two: pages planned but missing, pages shipped but never planned, labels that differ. Compare paths without the host (`app.example.com/login` and `/login` are the same page). |

## The method, in order

### 1. Sitemap
List every page with its URL path, grouped (public marketing pages, free tools, lead magnet pages, legal and email pages, account and app pages, system pages such as 404 and error), each with its audience, its job in one line, its build state and target date. Show it as an indented tree: `depth` is how far in a person goes to reach the page (on mobile, how many screens they push through). Pages without an element table can be listed too, with `page: null`.

### 2. User stories per page
Each page opens with what its visitors want there, as user stories, split by role where roles differ:

> As a [role], I want to [goal].

Exactly one story per page is the **main story** (`main: true`). The page's primary call to action must serve it. Story IDs: `<PAGE>-G1`, `-G2`...

### 3. Needs chains
Under each story, a chain of needs that ends in elements:

> In order to [step], I need [thing] → element IDs

Pick the verb that fits the step: "in order to understand that", "to see my options", "to figure that out", "to trust that", "to compare", "to decide", "to pay". Avoid a fixed "do that". Keep going until every line names a concrete element. A step can nest under another (`d` is its depth).

### 4. Elements, content included
Break the needs into the page's full element list, in top-to-bottom reading order: the sample download button, the pricing link, the hero image, the title, and each section named by what it tells.

- **One primary CTA per page.** A repeat of the same button lower on the page is the same CTA (mark it with `rep`).
- **Secondary and tertiary CTAs**, then navigation, inputs (one per field, with units), calculators, results, forms, links.
- **Component level:** pricing tier 1, 2, 3 each with its button; billing toggle; recommended badge; sign in; sign out; account menu; each footer link; consent lines.
- **Content blocks:** title, subtitle, hero image or hero object, each section named by what it tells ("Section: what a lender checks"), proof, each FAQ item, terms beside the button.
- **Shared elements** (header signed out and signed in, footer, account menu, shared error and recovery parts) are cataloged once as `GLB-` elements in named global groups. Each page lists the groups it uses in `shells`.
- Labels come from the sources; new labels are marked `proposed`; labels already in the app are marked `app`.

Common cases:

| Case | How to catalog it |
|---|---|
| A toggle whose label changes | One element, label "Start recording / Stop recording". |
| A list | One element for the list, one for the row template (`sub: "list row"`), not one per row. |
| An empty list or empty screen | `content` with `path: unhappy`, trigger "no items yet", and the action that fills it. |
| A native alert or confirm dialog | `component` with `sub: "alert dialog"`; its buttons are elements of their own when they do different things. |
| A modal or bottom sheet | `component` with `sub: "sheet"`, then its contents as elements. |
| Data the app loses (not saved, wiped on close) | Not an element. Answer "no" under "keep" in the ways-out grid, with the reason in its note. |
| A failure the app does not show | `error` with `state: missing`, label "[nothing shown]", and the trigger. |
| Any other `component` | Give it a `sub` or a `kit` name ("date picker", "map"), so the inventory does not pile unrelated parts into one row called "Component". |

### 5. Unhappy paths and ways out
After the happy path, catalog what happens when things go wrong, so no visitor gets stuck with nowhere to go. Write unhappy stories with chains the same way ("As a buyer whose card was declined, I want to fix it without losing my seat..."). Cover, where the page has them:

- Field validation with the fix in plain words; entries kept on error.
- Calculator inputs blank, out of range or impossible, and what the result shows then.
- Network or server failure with retry; 404 and error pages that lead somewhere.
- Payment: declined card, bank check failure, double click, abandoned checkout, lost receipt, sold out, refunds and automatic refunds.
- Sign-up and sign-in: existing account, wrong password, lockout, expired link, missing invite.
- Email and lists: typo, confirmation not arriving, signing up twice, leaving a list, expired download link.
- Account and billing: cancel, pause, downgrade, export everything before leaving, delete account and data, failed renewal with grace period, a discount ending.
- App work: unsaved changes, autosave and resume, undo delete, blocked export with the reason and fix, session timeout that keeps the work.
- Back and cancel on every multi-step flow; contact help from any error; "email me a link to finish later" on phones.
- Mobile apps: offline and slow network, permission denied (camera, location, notifications, photos), app sent to the background mid-task and reopened, update required, a deep link or push notification that opens deleted or private content, the keyboard covering a field, sign-in expired while the app was closed.
- Fake doors (buttons for features not built yet): the click tells the truth and offers a real next step, never a dead end.
- No dark patterns: no confirmshaming, hidden costs, pre-checked extras, fake urgency or hard-to-cancel flows (FTC staff report "Bringing Dark Patterns to Light", 2022; the US Restore Online Shoppers' Confidence Act, ROSCA).

Unhappy elements carry `path: unhappy` and a `trigger`. An error state lists in `wayout` the elements that get the person moving again (a retry button, the field to fix, a help link).

### 6. Ways-out grid
Every page answers five questions with yes, no or n/a, naming the elements: Can they go back? Cancel? Undo? Get help? Leave and keep their work? Close cheap "no" answers; flag the rest for a decision. On mobile, "back" includes the swipe-back gesture on iOS and the system back button on Android, and "cancel" includes dismissing a sheet, modal or alert; name the element that offers it.

### 7. Cross-page index
All stories grouped by intent (learn, calculate or use, sign up, pay, get help, manage account, recover when something goes wrong), with the pages they appear on.

### 8. Open questions with defaults
List every place the sources disagree or are silent. Apply a sensible default to each (`status: "default"`, with `default` and a one-line `reason`); the page shows these under "Defaults applied, change if wrong". Bring the user only real decisions (money, legal entity, promises to customers, addresses, names), each with a `recommended` answer (`status: "open"`); ask them with your agent's question tool (AskUserQuestion in Claude Code), or in one batched message. When the user answers, set `status: "decided"` and write the answer in `answer`. Set `meta.owner` to whoever makes these decisions; the page heads the open list "Needs [owner]".

## Where the catalog fits with a UI kit

A UI kit is the set of reusable parts a product is built from: design tokens (color, type, spacing, radius, motion) and components (buttons, fields, cards, menus) with all their states. The catalog comes first. It says which parts the product needs and what each one must say and do; the kit decides how they look.

Order of work: sitemap and catalog, then component inventory from the catalog, then the UI kit, then wireframes and visual design built from kit parts.

| In the catalog | What the kit gets from it |
|---|---|
| `primary`, `secondary`, `tertiary` | Three button emphasis levels. One primary per page means the loudest style appears once per screen. |
| `navigation`, `link`, `GLB-` shells | Nav bar, tab bar, links, account menu, and layout shells for signed out and signed in. |
| `input` (one per field, with units) | Text, number-with-unit, select and checkbox fields, each with label, help text and error text. |
| `form` | Form layout, submit behavior, inline validation. |
| `calculator`, `result` | Composite components with an empty, invalid and filled result. |
| `component` | Named composites: pricing tier card, billing toggle, recommended badge, account menu, sheet, alert dialog. |
| `content` and its `sub` (title, subtitle, hero, section, proof, FAQ item, terms) | Type scale and content blocks. |
| `error` | Inline field error, form banner, full-page error (404, server error). |
| `wayout` | Back, cancel, undo notice, "save and finish later", contact help. |
| `state: fakedoor` | A "not built yet" pattern that still offers a next step. |
| Unhappy rows and their `trigger` | Each component's non-default states: error, disabled, loading, empty, expired, sold out. |
| `label` | Real copy for the kit's demos, so each component is tested at real text lengths. |
| `event` | Analytics names the components pass through when clicked or submitted. |

The build turns this into two inventories:

- **Component inventory** (product-wide): one row per kit part with its uses (repeats apart), the pages it appears on, build state counts, unhappy uses, the error states whose way out is this part (a field there needs an error look; a button or link there is a recovery step), and its longest label with a character count, so the part is tested at real text length. Rows run in type order, most used first.
- **By page** (per screen): a grid of every page against every kit part with counts, plus the shared shells each page uses. Each page card also ends with "Kit parts on this page", listing the element IDs behind each count. For an app, catalog each screen as a page; the grid is then a per-screen inventory.

The catalog never supplies tokens, visual style or responsive layout; those come from the design work.

## Labels, kit names and events

| Field | Rule |
|---|---|
| `label` | The visible text. For an icon-only control, use its accessibility label; when it has none, describe it in brackets ("[plus icon]"), keep `lab: app`, and note the missing accessible name in the page's `notes`. Bracketed labels are left out of the longest-label test. |
| `kit` | The UI kit part the element is built from ("Button/primary", "Text field", "Icon button", "Sheet"). Elements with the same `kit` name count as one part. When the app's code builds it by hand from platform primitives (a pressable view, a plain text input, a styled div) instead of a shared component (the app's own `Button`, or a library's or the platform's, such as a native alert), add " (raw)", so the inventory shows parts built by hand. Without `kit`, the part is named after the type and subtype ("Content: FAQ item"). |
| `event` | The analytics event name the element sends. `none` for content that takes no action; `not set` for an interactive element that sends no event (in discovery, when the app has no analytics, every interactive element is `not set`). Names not listed in `source_events` show as proposed. |

## Element fields

| Field | Meaning |
|---|---|
| `id` | `<PAGE>-NN`, unique across the catalog, in reading order. Gaps in the numbering are fine, so inserting a row needs no renumbering (`HOME-07a` works too). |
| `el` / `label` / `lab` | element name / visible label / label source (`source`, `proposed`, `app`) |
| `type` | `primary`, `secondary`, `tertiary`, `navigation`, `input`, `calculator`, `result`, `component`, `form`, `link`, `content`, `error`, `wayout` |
| `sub` | subtype: title, subtitle, hero image, section, proof, FAQ item, terms, list row, sheet, alert dialog |
| `does` / `then` | what the person does / what happens (destination, result, what a fake door says) |
| `event` | see "Labels, kit names and events" |
| `state` | `exists` (in the app now), `missing` (the app should have it and lacks it; discovery), `build` (planned, to build), `fakedoor`, `later`, `outside` (lives outside this product, such as an email) |
| `src` | source key and section |
| `path` / `trigger` / `wayout` | `happy` or `unhappy` (on an element, `path` is the path through the page, not a URL) / what causes it / the way-out element IDs |
| `rep` | ID of the element this repeats |
| `kit` | optional: see "Labels, kit names and events" |

Required: element `id`, `el`, `type`; page `id`, `name`, `primary`, `ways_out`; story `id`, `story`; chain step `to`, `need`. Everything else has a default. The starter shows every field in use.

| Object | Fields |
|---|---|
| `meta` | `product`, `title`, `file` (record path), `updated`, `status` (one line on where the catalog stands), `purpose`, `main_message`, `reading` (how to read it), `tracking_note` (one line on analytics, shown with Global elements), plus the options below |
| page | `id`, `name`, `path` (URL or screen name), `group`, `audience`, `job`, `state`, `when`, `primary`, `shells` (global group names), `stories`, `elements`, `notes`, `ways_out` |
| story | `id`, `story`, `main` (true on one per page), `path` (`unhappy` for an unhappy story), `src`, `chain` |
| chain step | `d` (depth), `to`, `need`, `els` (element IDs; empty means no element meets it yet), `why` (optional, when `els` is empty) |
| `ways_out` | five keys `back`, `cancel`, `undo`, `help`, `keep`, each `{v: "yes" \| "no" \| "n/a", els: [...], note}` |
| `sitemap` | groups `{group, pages: [{path, name, page (page id, or null when it has no table), depth, audience, job, state, when, note}]}` |
| `global` | `groups` (`{name, ids}`), `elements`, `stories` |
| `index` | `{intent, goals: [{text, stories: [...]}]}` |
| `open_questions` | `id`, `topic`, `q`, `status` (`open`, `default` or `decided`), `recommended`, `default`, `reason`, `answer`, `src`, `pages` (page ids, or `GLOBAL`) |
| top level | also `terms` (`[term, definition]` pairs), `sources` (`[key, description]` pairs), `source_events` (event names the sources define) |

A page that has an element table takes its audience, job, state and date from its page entry; the sitemap entry repeats them for the tree.

`meta` options:

| Option | Default | Effect |
|---|---|---|
| `mode` | `"plan"` | `"discover"` builds even when the app breaks a rule, and lists each break under "Gaps found in the app". |
| `owner` | `"the product owner"` | Who makes the open decisions; names that section. |
| `top_terms` | first six terms | Terms defined at the top of the page, before they are used. |
| `no_dashes` | `false` | When `true`, the build refuses em and en dashes in the data. |

## Build and checks

```
python3 <skill-folder>/scripts/build.py <catalog-folder>
```

Python 3 only, no packages. It reads `<catalog-folder>/elements.json` and writes `UX-ELEMENTS-CATALOG.md` (the record) and `UX-ELEMENTS-CATALOG.html` (the reading page: sticky page index, sitemap tree, stories and chains linked to element rows, filters by type, state and path, primary CTA highlighted, ways-out grid, component inventory with a per-page grid, kit parts on each page card, light and dark mode, fonts embedded, no network requests). Edit `elements.json` and build again; never edit the outputs.

It names every missing required field by ID, and always refuses to build when:

- an element or story ID is used twice;
- a chain or a ways-out grid names a missing element, or a way out names one that does not exist;
- a page has other than exactly one primary CTA, or other than one main story, or the primary is not in the main story's chain;
- an unhappy element has no trigger;
- a page lacks a ways-out grid or one of its five answers, or a "yes" in it names no element;
- a type, state, path, label source, ways-out answer, status or shell name is not one of the allowed values;
- a global group, index entry, sitemap entry or open question names an element, story or page that does not exist;
- `no_dashes` is on and the data holds an em or en dash.

These rules refuse the build in plan mode and are listed as gaps in discover mode:

- an error state has no way out;
- a page with an input, form or calculator has no error state, or no way out (a `wayout` element, or an error state that names one).

Each page also lists elements no story reaches (cut them or name their goal) and needs no element meets yet.

## Finish

| Step | Action |
|---|---|
| 9.1 | Look at the catalog page at desktop and phone width, light and dark. With Chrome (on macOS, `<chrome>` is `/Applications/Google Chrome.app/Contents/MacOS/Google Chrome`): `"<chrome>" --headless=new --window-size=1440,1400 --screenshot=desk.png file:///<folder>/UX-ELEMENTS-CATALOG.html`, and for phone width wrap the page in a 390 px iframe (Chrome's window has a minimum width): `<iframe src="file:///<folder>/UX-ELEMENTS-CATALOG.html" style="width:390px;height:1400px;border:0">` in a small HTML file, screenshotted the same way with `--allow-file-access-from-files`. Add `--force-dark-mode` for dark. Check: no overlap, no page-level sideways scroll (wide tables scroll inside their card). |
| 9.2 | Open the HTML for the user. Keep the `.md` as the record; the user reads the HTML. |
| 9.3 | Report: page count, elements per page with each primary CTA, unhappy counts, gaps found (discover), ways-out gaps, defaults applied, and the decisions that need the user. |
| 9.4 | No visual design in the catalog: name what each block says and does, not how it looks. Wireframes, the UI kit and design come after the catalog is agreed. |
| 9.5 | When the user is ready to build, hand `UX-ELEMENTS-CATALOG.md` to whatever builds the UI, one page or screen at a time, with: "Build the [page] page from UX-ELEMENTS-CATALOG.md. Use its elements in the listed order with the exact labels. The element marked primary is the page's one primary button. Include every unhappy-path element, each error state with the way out it names. Use the kit parts listed under Kit parts on this page, and send the events in the Event column." Build the kit parts from the component inventory first. |
