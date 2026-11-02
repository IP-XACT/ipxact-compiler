# ipxact-compiler

A Python library that parses [IEEE 1685-2022](https://standards.ieee.org/ieee/1685/10307/) IP-XACT
XML documents into a Python object model.

It is a standalone, general-purpose parsing library, not tied to any specific downstream tool or
flow. `ipxact-compiler` reads IP-XACT and hands you back Python objects; it does not resolve
cross-file references, link a design, validate semantic consistency, or generate any output.
That is the job of tools built on top of it.

## What it supports

Five IP-XACT top-level document types are supported for now:

- `component`
- `design`
- `designConfiguration`
- `busDefinition`
- `abstractionDefinition`

The object model covers the IEEE 1685-2022 XSD schema for these document types: every element and
attribute the schema allows in them has a place in the object model and is read by the parser. This
is checked against the official Accellera XSD files, with XML documents generated from the schema
itself.

### How values are represented

- **Expressions are `Expression` objects.** Fields typed as an IP-XACT expression (parameter values,
  addresses, sizes, vector and array bounds, and similar) hold an `Expression` with the raw `value`
  text and its optional `minimum`/`maximum` bounds. Expressions are not evaluated: `"DATA_W-1"` stays
  `"DATA_W-1"`. [XactFlow](https://github.com/IP-XACT/XactFlow) provides an evaluator
  (`xactflow.evaluate`).
- **`xml:id` attributes** are kept as `xml_id` fields. Plain text elements that can carry an `xml:id`
  (`viewRef`, `group`, `dependency`, ...) are `TextValue` objects (`value` and `xml_id`).
- **Attributes from other namespaces**, where the schema allows them, are kept in `other_attributes`
  dictionaries, keyed by `{namespace}name`.
- **`vendorExtensions` is opaque.** Each extension is kept as a raw XML string, not modeled
  per-vendor.
- **References are kept as references.** VLNV references (`busType`, `componentRef`, ...) and the
  `*DefinitionRef` elements that point into a `typeDefinitions` document are stored as they are
  written; resolving them is left to the caller.

### What is not kept

- XML comments and processing instructions.
- `xsi:` attributes, such as `xsi:schemaLocation` on the root element. On elements that have
  `other_attributes`, they are kept there like any other foreign attribute.
- The relative order of sibling elements that the schema lets you mix but that end up in separate
  lists: `interconnection` and `monitorInterconnection`, and the different kinds of instantiations.
  Order within each list is kept.
- Whether an optional element or attribute with a schema default was written out or omitted: both give
  the default value.
- The `invert` attribute of a `portMap` is not typed in the XSD; it is read as a boolean.

Other IP-XACT document types (`typeDefinitions`, `catalog`, `abstractor`, `generatorChain`) are not
parsed.

## Installation

```bash
pip install ipxact-compiler
```

Or, for local development:

```bash
git clone https://github.com/IP-XACT/ipxact-compiler.git
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

register = component.memory_maps[0].items[0].registers[0]
register.size             # Expression(value="32", minimum=None, maximum=None, ...)
register.size.value       # "32"
```

`ipxact.parse_file(path)` reads a file, figures out its document type from the root element, and
returns the matching dataclass (`Component`, `Design`, `DesignConfiguration`, `BusDefinition`, or
`AbstractionDefinition`).

Every schema class (`Component`, `VLNV`, `BusInterface`, `Register`, `Field`, `Expression`, and so
on) is re-exported at the top level, so `ipxact.<ClassName>` works without reaching into submodules.

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

These are open items, not commitments.

- **No XSD schema validation.** Malformed IP-XACT (missing required elements, wrong types, invalid
  structure) is not rejected at parse time; the parser will generally just default missing fields
  rather than erroring. A validation path using the IEEE 1685-2022 XSDs and `lxml.etree.XMLSchema`
  is being considered. Shipping the XSD files with this library would also let tools built on it
  validate their own output.
- **No deliberate error-handling philosophy yet.** Right now, malformed input either silently
  produces a default value or raises whatever low-level Python exception happens to occur (a
  `ValueError`, an `AttributeError`, etc.) rather than a clear, intentional error type. Deciding on
  and implementing a consistent policy (raise vs. warn vs. silently default, and what exception
  types/messages to use) is still open.
- **No Semantic Consistency Rule (SCR) checking.** This rules are out of scope for this library.
  They are handled by [XactFlow](https://github.com/IP-XACT/XactFlow), including the rules that
  can be checked on a single document.
- **No dedicated documentation yet.** This README covers the basics, but a proper documentation site
  (full API reference, more usage examples) is planned for the future.

## License

LGPL-3.0. See [`LICENSE`](LICENSE).
