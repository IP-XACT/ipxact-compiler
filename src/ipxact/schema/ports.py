from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Optional

from .common import (
    AccessHandle,
    ArrayBound,
    Expression,
    FieldReference,
    ModeRef,
    ModuleParameter,
    Parameter,
    PartSelect,
    Range,
    SubPortReference,
    TextValue,
    VendorExtension,
    Vector,
)


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
    xml_id: Optional[str] = None


@dataclass
class CellSpecification:
    """ipxact:cellSpecification - a technology-library cell described independent of the library.

    ``cell_function_other`` names the cell when ``cell_function`` is "other".
    """

    cell_function: Optional[str] = None
    cell_function_other: Optional[str] = None
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
    count: Expression = field(default_factory=lambda: Expression("3"))


@dataclass
class TimingConstraint:
    """ipxact:timingConstraint - a timing constraint relative to a named clock."""

    value: str  # percentage of the clock period, 0..100
    clock_name: str
    clock_edge: Optional[str] = None  # rise/fall
    delay_type: Optional[str] = None  # min/max
    xml_id: Optional[str] = None


@dataclass
class ConstraintSet:
    """ipxact:constraintSet - a named group of drive/load/timing constraints for a port."""

    name: Optional[str] = None
    vector: Optional[Vector] = None
    drive_constraint: Optional[DriveConstraint] = None
    load_constraint: Optional[LoadConstraint] = None
    timing_constraints: list[TimingConstraint] = field(default_factory=list)
    constraint_set_id: str = "default"
    display_name: Optional[str] = None
    short_description: Optional[str] = None
    description: Optional[str] = None
    xml_id: Optional[str] = None


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
    xml_id: Optional[str] = None


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
    range: Optional[Range] = None
    view_refs: list[TextValue] = field(default_factory=list)
    xml_id: Optional[str] = None


@dataclass
class WireTypeDef:
    """ipxact:wireTypeDef - the HDL type of a wire port for some views (e.g. std_logic_vector).

    ``type_name_constrained`` lists the parts of the type the vectors constrain.
    """

    type_name: Optional[str] = None
    type_name_constrained: list[str] = field(default_factory=list)
    type_definitions: list[TextValue] = field(default_factory=list)
    view_refs: list[TextValue] = field(default_factory=list)
    xml_id: Optional[str] = None


@dataclass
class DomainTypeDef:
    """ipxact:domainTypeDef - the HDL domain type of a wire port for some views (e.g. AMS nature)."""

    type_name: Optional[TextValue] = None
    type_definitions: list[TextValue] = field(default_factory=list)
    view_refs: list[TextValue] = field(default_factory=list)
    xml_id: Optional[str] = None


@dataclass
class SignalTypeDef:
    """ipxact:signalTypeDef - the signal type of a wire port for some views (e.g. digital)."""

    signal_type: str  # continuous-conservative/continuous-non-conservative/discrete/digital
    view_refs: list[TextValue] = field(default_factory=list)
    xml_id: Optional[str] = None


@dataclass
class ServiceTypeDef:
    """ipxact:serviceTypeDef - a service type (and its parameters) used by a transactional type."""

    type_name: str
    type_name_implicit: bool = False
    type_definitions: list[TextValue] = field(default_factory=list)
    type_parameters: list[ModuleParameter] = field(default_factory=list)
    service_type_defs: list["ServiceTypeDef"] = field(default_factory=list)
    xml_id: Optional[str] = None


@dataclass
class TransTypeDef:
    """ipxact:transTypeDef - the HDL type of a transactional port for some views (e.g. a SystemC socket)."""

    type_name: Optional[str] = None
    type_name_exact: bool = True
    type_definitions: list[TextValue] = field(default_factory=list)
    type_parameters: list[ModuleParameter] = field(default_factory=list)
    service_type_defs: list[ServiceTypeDef] = field(default_factory=list)
    view_refs: list[TextValue] = field(default_factory=list)
    xml_id: Optional[str] = None


@dataclass
class PowerConstraint:
    """ipxact:powerConstraint - the power domain a port (or a bit range of a wire port) belongs to."""

    power_domain_ref: str
    range: Optional[Range] = None
    xml_id: Optional[str] = None
    vendor_extensions: list[VendorExtension] = field(default_factory=list)


@dataclass
class WirePort:
    """ipxact:wire - a port whose type resolves to simple bits (port.xsd portWireType)."""

    direction: Direction
    qualifier: Optional[Qualifier] = None
    vectors: list[Vector] = field(default_factory=list)
    wire_type_defs: list[WireTypeDef] = field(default_factory=list)
    domain_type_defs: list[DomainTypeDef] = field(default_factory=list)
    signal_type_defs: list[SignalTypeDef] = field(default_factory=list)
    drivers: list[Driver] = field(default_factory=list)
    constraint_sets: list[ConstraintSet] = field(default_factory=list)
    power_constraints: list[PowerConstraint] = field(default_factory=list)
    all_logical_directions_allowed: bool = False


@dataclass
class Payload:
    """ipxact:payload - the structure of data transported by a transactional port."""

    type: str  # generic/specific
    name: Optional[str] = None
    extension: Optional[str] = None
    extension_mandatory: bool = False
    vendor_extensions: list[VendorExtension] = field(default_factory=list)


@dataclass
class Protocol:
    """ipxact:protocol - the transaction protocol used by a transactional port."""

    protocol_type: str  # tlm/custom
    custom_type_name: Optional[str] = None
    payload: Optional[Payload] = None


@dataclass
class TransactionalPort:
    """ipxact:transactional - a SystemC/TLM service port (port.xsd portTransactionalType).

    ``kind_custom`` names the kind when ``kind`` is "custom".
    """

    initiative: Initiative
    kind: Optional[str] = None  # tlm_port/tlm_socket/simple_socket/multi_socket/custom
    kind_custom: Optional[str] = None
    bus_width: Optional[Expression] = None
    qualifier: Optional[Qualifier] = None
    protocol: Optional[Protocol] = None
    trans_type_defs: list[TransTypeDef] = field(default_factory=list)
    max_connections: Optional[Expression] = None
    min_connections: Optional[Expression] = None
    power_constraints: list[PowerConstraint] = field(default_factory=list)
    all_logical_initiatives_allowed: bool = False


@dataclass
class PortAccess:
    """ipxact:access - how a port is accessed (by reference or pointer) and its HDL access paths."""

    port_access_type: Optional[str] = None  # ref/ptr
    access_handles: list[AccessHandle] = field(default_factory=list)


@dataclass
class SubPort:
    """ipxact:subPort - one member of a structured port, itself a wire or nested structured port."""

    name: str
    wire: Optional[WirePort] = None
    structured: Optional["StructuredPort"] = None
    arrays: list[ArrayBound] = field(default_factory=list)
    access: Optional[PortAccess] = None
    display_name: Optional[str] = None
    short_description: Optional[str] = None
    description: Optional[str] = None
    is_io: Optional[bool] = None
    xml_id: Optional[str] = None
    vendor_extensions: list[VendorExtension] = field(default_factory=list)


@dataclass
class StructPortTypeDef:
    """ipxact:structPortTypeDef - one language-specific type binding for a structured port."""

    type_name: str
    constrained: list[str] = field(default_factory=list)
    type_definitions: list[TextValue] = field(default_factory=list)
    type_parameters: list[ModuleParameter] = field(default_factory=list)
    role: Optional[str] = None  # only valid when struct_type == "interface" (the SV modport)
    view_refs: list[TextValue] = field(default_factory=list)
    xml_id: Optional[str] = None


@dataclass
class StructuredPort:
    """ipxact:structured - a struct/union/interface-typed port made of subPorts (port.xsd portStructuredType)."""

    struct_type: str  # struct/union/interface
    vectors: list[Vector] = field(default_factory=list)
    sub_ports: list[SubPort] = field(default_factory=list)
    packed: bool = True
    direction: Optional[Direction] = None  # only meaningful when struct_type is struct/union
    phantom: Optional[bool] = None  # only meaningful when struct_type == "interface"
    struct_port_type_defs: list[StructPortTypeDef] = field(default_factory=list)


@dataclass
class FieldMap:
    """ipxact:fieldMap - maps a slice of this port to a component register field slice."""

    field_slice: FieldReference
    sub_port_refs: list[SubPortReference] = field(default_factory=list)
    part_select: Optional[PartSelect] = None
    mode_refs: list[ModeRef] = field(default_factory=list)
    xml_id: Optional[str] = None


@dataclass
class Port:
    """ipxact:port - a physical signal of the component model (port.xsd portType).

    Exactly one of wire/transactional/structured is set, mirroring the schema's port-style
    choice.
    """

    name: str
    wire: Optional[WirePort] = None
    transactional: Optional[TransactionalPort] = None
    structured: Optional[StructuredPort] = None
    field_maps: list[FieldMap] = field(default_factory=list)
    arrays: list[ArrayBound] = field(default_factory=list)
    access: Optional[PortAccess] = None
    display_name: Optional[str] = None
    short_description: Optional[str] = None
    description: Optional[str] = None
    parameters: list[Parameter] = field(default_factory=list)
    xml_id: Optional[str] = None
    vendor_extensions: list[VendorExtension] = field(default_factory=list)
