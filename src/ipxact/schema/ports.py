from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Optional

from .businterface import FieldReference
from .common import Expression, ModeRef, Parameter, PartSelect, SubPortReference, VendorExtension, Vector


class Direction(str, Enum):
    """ipxact:direction on a wire port (port.xsd componentPortDirectionType)."""

    IN = "in"
    OUT = "out"
    INOUT = "inout"
    PHANTOM = "phantom"


class Initiative(str, Enum):
    """ipxact:initiative on a transactional port (port.xsd initiativeType)."""

    REQUIRES = "requires"
    PROVIDES = "provides"
    BOTH = "both"
    PHANTOM = "phantom"


@dataclass
class LevelFlag:
    """A boolean qualifier that also carries an active-level attribute (isReset, isClockEn, isPowerEn)."""

    value: bool
    level: Optional[str] = None  # "low" | "high"
    power_domain_ref: Optional[str] = None


@dataclass
class FlowControlFlag:
    """ipxact:isFlowControl - value plus the controlled-flow type it qualifies."""

    value: bool
    flow_type: Optional[str] = None  # credit-return/ready/busy/user
    user: Optional[str] = None


@dataclass
class UserFlag:
    """ipxact:isUser - value plus a user-defined behavior tag."""

    value: bool
    user: Optional[str] = None


@dataclass
class Qualifier:
    """ipxact:qualifier - semantic role(s) carried by a port (commonStructures qualifierType)."""

    is_address: Optional[bool] = None
    is_data: Optional[bool] = None
    is_clock: Optional[bool] = None
    is_reset: Optional[LevelFlag] = None
    is_valid: Optional[bool] = None
    is_interrupt: Optional[bool] = None
    is_clock_en: Optional[LevelFlag] = None
    is_power_en: Optional[LevelFlag] = None
    is_opcode: Optional[bool] = None
    is_protection: Optional[bool] = None
    is_flow_control: Optional[FlowControlFlag] = None
    is_user: Optional[UserFlag] = None
    is_request: Optional[bool] = None
    is_response: Optional[bool] = None


@dataclass
class CellSpecification:
    """ipxact:cellSpecification - a technology-library cell described independent of the library."""

    cell_function: Optional[str] = None
    cell_class: Optional[str] = None  # combinational/sequential
    cell_strength: Optional[str] = None  # low/median/high


@dataclass
class DriveConstraint:
    """ipxact:driveConstraint - how an input port is to be driven."""

    cell: CellSpecification


@dataclass
class LoadConstraint:
    """ipxact:loadConstraint - the load presented on an output port."""

    cell: CellSpecification
    count: Expression = "3"


@dataclass
class TimingConstraint:
    """ipxact:timingConstraint - a timing constraint relative to a named clock."""

    value: Expression  # percentage of the clock period, 0..100
    clock_name: str
    clock_edge: Optional[str] = None  # rise/fall
    delay_type: Optional[str] = None  # min/max


@dataclass
class ConstraintSet:
    """ipxact:constraintSet - a named group of drive/load/timing constraints for a port."""

    name: Optional[str] = None
    vector_left: Optional[Expression] = None
    vector_right: Optional[Expression] = None
    drive_constraint: Optional[DriveConstraint] = None
    load_constraint: Optional[LoadConstraint] = None
    timing_constraints: list[TimingConstraint] = field(default_factory=list)
    constraint_set_id: str = "default"


@dataclass
class ClockDriver:
    """ipxact:clockDriver - a simulated clock waveform driven onto a wire port."""

    clock_period: Expression
    clock_pulse_offset: Expression
    clock_pulse_value: Expression
    clock_pulse_duration: Expression
    clock_name: Optional[str] = None
    period_units: str = "ns"
    offset_units: str = "ns"
    duration_units: str = "ns"


@dataclass
class SingleShotDriver:
    """ipxact:singleShotDriver - a simulated one-shot waveform driven onto a wire port."""

    single_shot_offset: Expression
    single_shot_value: Expression
    single_shot_duration: Expression
    offset_units: str = "ns"
    duration_units: str = "ns"


@dataclass
class Driver:
    """ipxact:driver - a simulation stimulus driven onto a wire port (or a bit range of it)."""

    default_value: Optional[Expression] = None
    clock_driver: Optional[ClockDriver] = None
    single_shot_driver: Optional[SingleShotDriver] = None
    range_left: Optional[Expression] = None
    range_right: Optional[Expression] = None
    view_refs: list[str] = field(default_factory=list)


@dataclass
class WirePort:
    """ipxact:wire - a port whose type resolves to simple bits (port.xsd portWireType).

    HDL type-binding metadata (wireTypeDefs/domainTypeDefs/signalTypeDefs, which bind the
    port to a language-specific type like VHDL std_logic_vector) is out of scope for v1:
    direction and vectors are enough to generate SystemVerilog RTL without a type system.
    """

    direction: Direction
    qualifier: Optional[Qualifier] = None
    vectors: list[Vector] = field(default_factory=list)
    drivers: list[Driver] = field(default_factory=list)
    constraint_sets: list[ConstraintSet] = field(default_factory=list)
    all_logical_directions_allowed: bool = False


@dataclass
class Payload:
    """ipxact:payload - the structure of data transported by a transactional port."""

    type: str  # generic/specific
    name: Optional[str] = None
    extension: Optional[str] = None
    extension_mandatory: bool = False


@dataclass
class Protocol:
    """ipxact:protocol - the transaction protocol used by a transactional port."""

    protocol_type: str  # tlm/custom
    custom_type_name: Optional[str] = None
    payload: Optional[Payload] = None


@dataclass
class TransactionalPort:
    """ipxact:transactional - a SystemC/TLM service port (port.xsd portTransactionalType).

    SystemC type-binding metadata (transTypeDefs, typeParameters) is out of scope for v1,
    same rationale as WirePort's wireTypeDefs.
    """

    initiative: Initiative
    kind: Optional[str] = None  # tlm_port/tlm_socket/simple_socket/multi_socket/custom
    bus_width: Optional[Expression] = None
    qualifier: Optional[Qualifier] = None
    protocol: Optional[Protocol] = None
    max_connections: Optional[Expression] = None
    min_connections: Optional[Expression] = None
    all_logical_initiatives_allowed: bool = False


@dataclass
class SubPort:
    """ipxact:subPort - one member of a structured port, itself a wire or nested structured port."""

    name: str
    wire: Optional[WirePort] = None
    structured: Optional["StructuredPort"] = None
    display_name: Optional[str] = None
    description: Optional[str] = None
    is_io: Optional[bool] = None


@dataclass
class StructuredPort:
    """ipxact:structured - a struct/union/interface-typed port made of subPorts (port.xsd portStructuredType).

    structPortTypeDefs (language-specific struct/interface type bindings) is out of scope,
    same rationale as WirePort's wireTypeDefs.
    """

    struct_type: str  # struct/union/interface
    vectors: list[Vector] = field(default_factory=list)
    sub_ports: list[SubPort] = field(default_factory=list)
    packed: bool = True
    role: Optional[str] = None  # only meaningful when struct_type == "interface"


@dataclass
class FieldMap:
    """ipxact:fieldMap - maps a slice of this port to a component register field slice."""

    field_slice: FieldReference
    sub_port_refs: list[SubPortReference] = field(default_factory=list)
    part_select: Optional[PartSelect] = None
    mode_refs: list[ModeRef] = field(default_factory=list)


@dataclass
class Port:
    """ipxact:port - a physical signal of the component model (port.xsd portType).

    Exactly one of wire/transactional/structured is set, mirroring the schema's port-style
    choice. portPackets (PSS packet framing) is out of scope.
    """

    name: str
    wire: Optional[WirePort] = None
    transactional: Optional[TransactionalPort] = None
    structured: Optional[StructuredPort] = None
    field_maps: list[FieldMap] = field(default_factory=list)
    display_name: Optional[str] = None
    description: Optional[str] = None
    parameters: list[Parameter] = field(default_factory=list)
    vendor_extensions: list[VendorExtension] = field(default_factory=list)
