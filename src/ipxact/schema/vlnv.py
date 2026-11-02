from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional

from .common import Expression


@dataclass(frozen=True)
class VLNV:
    """Vendor-library-name-version identity of an IP-XACT document (IEEE 1685-2022 1.4.3)."""

    vendor: str
    library: str
    name: str
    version: str

    def __str__(self) -> str:
        return f"{self.vendor}:{self.library}:{self.name}:{self.version}"

    @classmethod
    def parse(cls, value: str) -> "VLNV":
        parts = value.split(":")
        if len(parts) != 4:
            raise ValueError(f"expected a 'vendor:library:name:version' string, got: {value!r}")
        vendor, library, name, version = parts
        return cls(vendor, library, name, version)


@dataclass(frozen=True)
class VLNVRef:
    """A reference to another IP-XACT document by VLNV, e.g. busType, abstractionRef, componentRef.

    config_element_values holds the ipxact:configurableElementValues expressions keyed by the
    referenced document's parameterId (their referenceId), left unresolved.
    """

    vendor: str
    library: str
    name: str
    version: str
    config_element_values: dict[str, Expression] = field(default_factory=dict)
    xml_id: Optional[str] = None

    def __str__(self) -> str:
        return f"{self.vendor}:{self.library}:{self.name}:{self.version}"

    @property
    def vlnv(self) -> VLNV:
        return VLNV(self.vendor, self.library, self.name, self.version)
