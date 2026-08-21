from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Optional

from .common import Assertion, Choice, Expression, Parameter, VendorExtension
from .ports import DriveConstraint, LoadConstraint, Protocol, Qualifier, TimingConstraint
from .vlnv import VLNV, VLNVRef


class Presence(str, Enum):
    """ipxact:presence enumeration (abstractionDefinition.xsd presenceType)."""

    REQUIRED = "required"
    ILLEGAL = "illegal"
    OPTIONAL = "optional"


@dataclass
class PortConstraints:
    """abstractionDefPortConstraintsType - drive/load/timing constraints for a logical port."""

    timing_constraints: list[TimingConstraint] = field(default_factory=list)
    drive_constraint: Optional[DriveConstraint] = None
    load_constraint: Optional[LoadConstraint] = None


@dataclass
class RequiresDriver:
    """ipxact:requiresDriver - whether a wire port needs a driver connected, and of what kind."""

    value: bool = False
    driver_type: str = "any"  # clock/singleShot/any


@dataclass
class WireModeConstraints:
    """The wirePort group - direction/width/timing constraints for one mode of a logical wire port."""

    presence: Presence = Presence.OPTIONAL
    width: Optional[Expression] = None
    width_all_bits_required: bool = False
    direction: Optional[str] = None  # in/out/inout
    mode_constraints: Optional[PortConstraints] = None
    mirrored_mode_constraints: Optional[PortConstraints] = None


@dataclass
class WireSystemConstraints:
    """ipxact:onSystem (wire) - constraints for a logical port within one system group."""

    group: str
    constraints: WireModeConstraints


@dataclass
class WireAbstractionPort:
    """ipxact:wire - a logical port carrying simple bits, defined at the abstraction level."""

    qualifier: Optional[Qualifier] = None
    on_system: list[WireSystemConstraints] = field(default_factory=list)
    on_initiator: Optional[WireModeConstraints] = None
    on_target: Optional[WireModeConstraints] = None
    default_value: Optional[Expression] = None
    requires_driver: Optional[RequiresDriver] = None


@dataclass
class TransactionalModeConstraints:
    """The transactionalPort group - initiative/kind/protocol for one mode of a logical transactional port."""

    presence: Presence = Presence.OPTIONAL
    initiative: Optional[str] = None  # requires/provides/both
    kind: Optional[str] = None
    bus_width: Optional[Expression] = None
    protocol: Optional[Protocol] = None


@dataclass
class TransactionalSystemConstraints:
    """ipxact:onSystem (transactional) - constraints for a logical port within one system group."""

    group: str
    constraints: TransactionalModeConstraints


@dataclass
class TransactionalAbstractionPort:
    """ipxact:transactional - a logical port carrying TLM-style transactions, at the abstraction level."""

    qualifier: Optional[Qualifier] = None
    on_system: list[TransactionalSystemConstraints] = field(default_factory=list)
    on_initiator: Optional[TransactionalModeConstraints] = None
    on_target: Optional[TransactionalModeConstraints] = None


@dataclass
class AbstractionPort:
    """ipxact:port (within abstractionDefinition/ports) - one logical port of the bus.

    ``ipxact:packets`` (PSS packet framing) is out of scope, same rationale as elsewhere.
    """

    logical_name: str
    wire: Optional[WireAbstractionPort] = None
    transactional: Optional[TransactionalAbstractionPort] = None
    match: bool = False
    display_name: Optional[str] = None
    short_description: Optional[str] = None
    description: Optional[str] = None
    vendor_extensions: list[VendorExtension] = field(default_factory=list)


@dataclass
class AbstractionDefinition:
    """ipxact:abstractionDefinition - the signal-level refinement of a busDefinition for one level."""

    vlnv: VLNV
    bus_type: VLNVRef
    extends: Optional[VLNVRef] = None
    ports: list[AbstractionPort] = field(default_factory=list)
    choices: list[Choice] = field(default_factory=list)
    parameters: list[Parameter] = field(default_factory=list)
    assertions: list[Assertion] = field(default_factory=list)
    display_name: Optional[str] = None
    short_description: Optional[str] = None
    description: Optional[str] = None
    vendor_extensions: list[VendorExtension] = field(default_factory=list)
