# Agent traversal

How a reasoning agent works the vault over MCP, once the
[Semantic Vault MCP](https://community.obsidian.md/plugins/semantic-vault-mcp)
plugin is exposing it.

## The MCP surface

The plugin provides (action names may vary by version):

- `vault` / **search** — full-text and TF-IDF over note content; operators
  `content:`, `tag:`, `file:`, `path:`, plus `OR`/`AND`, `"phrases"`, `/regex/`.
- `vault` / **read**, `view` / **file** — a note's frontmatter and body.
- `graph` / **neighbors** — a node's immediate links.
- `graph` / **traverse** — breadth-first expansion to depth *N*.
- `graph` / **search-traverse** — follow links and score each node against a query;
  returns connected snippets. Lower `scoreThreshold` if it prunes too early.
- `graph` / **path** — shortest route between two nodes.
- `graph` / **statistics**, **tag-traverse**, **tag-analysis** — counts and
  tag-scoped walks.

## Four ways in

A parameter sits in four independent groupings. Each is a separate entry point, and
the agent crosses between them:

1. **By meaning** — `vault.search` resolves intent and terminology to the board's
   actual labels (a query for `impedance` finds the ODT family; `Precision Boost
   Overdrive` finds the PBO controls).
2. **By menu** — `graph.neighbors` on a form node returns the cluster of settings
   that menu controls.
3. **By variable** — the `var` node lists every parameter writing one NVRAM
   variable, ordered by offset.
4. **By domain** — the `#domain/*` tags (and the per-domain index notes) group
   settings by subject across modules.

A single search operator can miss. Exact-phrase `content:"Memory Context Restore"`
returns nothing on this vault; the ranked search for `Context Restore` returns the
parameter in four modules. Use more than one mode, and fall back to structural
traversal when search is empty.

## Scale

A full vault is ~5,000 notes — too many to read file by file. Traversal loads only
the nodes on the path being reasoned about, and the edges carry the relationships
(menu, variable, sibling) that matter. Search to a node, expand its neighbors, read
the one or two notes that answer the question.

## Operational notes

- Let first-time indexing finish before querying. A partial index looks like a graph
  full of orphans and returns empty searches.
- Keep Obsidian's **global graph view closed** while an agent queries. The MCP
  server runs inside Obsidian; a several-thousand-node force render starves it. Local
  graphs and search do not.
- The agent locates and explains. A proposed NVRAM write is a hypothesis to review,
  apply, and verify on the operator's own machine.

See the [walkthroughs](walkthroughs.md) for worked traversals.
