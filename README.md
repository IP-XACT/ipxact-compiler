# ipxact-compiler

A Python library that parses [IEEE 1685-2022](https://standards.ieee.org/ieee/1685/10307/) IP-XACT
XML documents into a Python object model.

It is a standalone, general-purpose parsing library, not tied to any specific downstream tool or
flow. `ipxact-compiler` reads IP-XACT and hands you back Python objects; it does not resolve
cross-file references, elaborate a design, validate semantic consistency, or generate any output.
That is the job of tools built on top of it.

## What it supports

Five IP-XACT top-level document types are supported for now:

- `component`
- `design`
- `designConfiguration`
- `busDefinition`
- `abstractionDefinition`

The object model aims for full fidelity with the IEEE 1685-2022 XSD schema for these document types:
every element and attribute the schema defines is represented.

A few things are intentionally represented in a simplified form rather than being modeled in full
depth:

- **Expressions are raw strings.** Fields typed as an IP-XACT `expression` (parameter values, array
  bounds, and similar) are kept as unevaluated strings, not parsed or evaluated as arithmetic.
- **`vendorExtensions` is opaque.** It is parsed generically, not modeled per-vendor.

## Installation

```bash
pip install ipxact-compiler
```

Or, for local development:

```bash
git clone <this repo>
cd ipxact-compiler
pip install -e ".[dev]"
```

Requires Python >= 3.9. The only runtime dependency is [`lxml`](https://lxml.de/).

## Usage

```python
import ipxact

component = ipxact.parse_file("path/to/some_component.xml")

component.vlnv            # VLNV
component.bus_interfaces  # list[BusInterface]
component.memory_maps     # list[MemoryMap]
component.model           # Model | None
```

`ipxact.parse_file(path)` reads a file, figures out its document type from the root element, and
returns the matching dataclass (`Component`, `Design`, `DesignConfiguration`, `BusDefinition`, or
`AbstractionDefinition`).

Every schema class (`Component`, `VLNV`, `BusInterface`, `Register`, `Field`, and so on) is
re-exported at the top level, so `ipxact.<ClassName>` works without reaching into submodules.

## Design principles

- **Single-file parsing only.** `ipxact-compiler` never opens a second file on its own. Resolving
  VLNV references across a library of files (for example, finding the `Component` that a `Design`'s
  instance refers to) is left to the caller.
- **Input files are assumed to be valid.** `ipxact-compiler` does not perform validation; it assumes
  the IP-XACT documents you give it are already well-formed and conform to the standard. This is why
  the parser currently favors defaulting over raising on missing or malformed data. This may change
  (see "Known limitations").
- **Hand-written, not XSD auto-generated.** The object model is a set of hand-written Python
  dataclasses following the schema but not automatically generated from the XSD. This keeps the API
  stable, at the cost of needing to keep it manually in sync with the standard.

## Known limitations / ideas for later

These are open items, not commitments. None of them are currently planned to start imminently.

- **No XSD schema validation.** Malformed IP-XACT (missing required elements, wrong types, invalid
  structure) is not rejected at parse time; the parser will generally just default missing fields
  rather than erroring. A validation path using the bundled IEEE 1685-2022 XSDs and
  `lxml.etree.XMLSchema` could be considered, but it means packaging the full IEEE 1685-2022 XSD
  schema with this repository, for a benefit that only matters if you're feeding it genuinely
  invalid files.
- **No deliberate error-handling philosophy yet.** Right now, malformed input either silently
  produces a default value or raises whatever low-level Python exception happens to occur (a
  `ValueError`, an `AttributeError`, etc.) rather than a clear, intentional error type. Deciding on
  and implementing a consistent policy (raise vs. warn vs. silently default, and what exception
  types/messages to use) is still open.
- **No Semantic Consistency Rule (SCR) checking**, per IEEE 1685-2022 Annex B. These are the
  standard's own rules for validity that XSD alone can't express (VLNV resolution correctness,
  bus/abstraction interface compatibility, and so on). Each rule is tagged with two independent
  flags: whether it is checkable on a single document alone, and whether it applies
  post-configuration (after linking). In our case, only the subset that is single-document-checkable
  and not post-config could live in `ipxact-compiler`.
- **No dedicated documentation yet.** This README covers the basics, but a proper documentation site
  (full API reference, more usage examples) is planned for the future.

## License

LGPL-3.0. See [`LICENSE`](LICENSE).
