# Simpson Thacher — homepage redesign concept

An unofficial, self-contained concept redesign of the stblaw.com homepage. Open
`index.html` in any browser; there is no build step and no dependencies.

## Direction

The current site follows the standard large-firm template: navy chrome, stock
architectural photography, and content buried under hover menus. This concept
inverts that — the firm's work is the design.

- **Stone paper, blue-black ink, single cobalt accent.** No navy-and-gold, no
  gradients, no drop shadows. Hairline rules do all the separating, so the page
  reads as a printed record rather than a stack of cards.
- **Bodoni Moda / Archivo / IBM Plex Mono.** A high-contrast didone for gravitas,
  a modern grotesque for reading, and a monospace for the things a deals firm
  actually publishes — values, roles, closing dates, timestamps.
- **The hero is a matters ticker.** Deals are the product, so representative
  matters sit beside the headline and rotate, rather than sitting three clicks
  deep under "Experience".
- **A filterable matters table** using real tombstone conventions (role, value,
  status, date) instead of a press-release feed.
- **Practice index as a typographic list** with lawyer counts, so depth is
  visible without opening anything.
- **Live local clocks per office**, which is the one thing a client in another
  timezone actually wants from a contact page.
- Full light/dark support driven by CSS tokens, plus a manual toggle;
  responsive to ~390px; respects `prefers-reduced-motion`.

## Content notice

This is a design concept and is not affiliated with or endorsed by the firm.
Every matter, figure, headcount, ranking and date on the page is placeholder
content written to demonstrate layout — nothing here reports a real engagement.
Practice groups and office cities follow the firm's publicly known structure.

## Note on sourcing

The live site could not be loaded from the environment this was built in
(outbound access to stblaw.com is blocked by the network egress policy), so the
information architecture is reconstructed from the firm's publicly known
practice and office structure rather than copied from the current site.
