from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional

from .common import Assertion, Choice, Expression, Parameter, VendorExtension
from .vlnv import VLNV, VLNVRef


@dataclass
class BusDefinition:
    """ipxact:busDefinition - the topology rules of a bus protocol, independent of abstraction level."""

    vlnv: VLNV
    direct_connection: bool
    is_addressable: bool
    broadcast: Optional[bool] = None
    extends: Optional[VLNVRef] = None
    max_initiators: Optional[Expression] = None
    max_targets: Optional[Expression] = None
    system_group_names: list[str] = field(default_factory=list)
    choices: list[Choice] = field(default_factory=list)
    parameters: list[Parameter] = field(default_factory=list)
    assertions: list[Assertion] = field(default_factory=list)
    display_name: Optional[str] = None
    short_description: Optional[str] = None
    description: Optional[str] = None
    vendor_extensions: list[VendorExtension] = field(default_factory=list)
