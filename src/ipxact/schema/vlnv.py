from __future__ import annotations

from dataclasses import dataclass, field


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
        vendor, library, name, version = value.split(":")
        return cls(vendor, library, name, version)


@dataclass(frozen=True)
class VLNVRef:
    """A reference to another IP-XACT document by VLNV, e.g. busType, abstractionRef, componentRef.

    config_element_values holds raw expression strings keyed by the referenced document's
    parameterId (ipxact:configurableElementValues), left unresolved for now.
    """

    vendor: str
    library: str
    name: str
    version: str
    config_element_values: dict[str, str] = field(default_factory=dict)

    def __str__(self) -> str:
        return f"{self.vendor}:{self.library}:{self.name}:{self.version}"

    @property
    def vlnv(self) -> VLNV:
        return VLNV(self.vendor, self.library, self.name, self.version)
