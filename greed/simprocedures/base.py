import typing
import logging
from abc import abstractmethod
from greed.TAC import TAC_Statement, TAC_Returnprivate
from greed.function import TAC_Function

if typing.TYPE_CHECKING:
    from greed.state import SymbolicEVMState
    from greed.solver import Term

log = logging.getLogger(__name__)


class BaseSimProcedure:
    """
    Base class for all symbolic procedures.

    This is intended to be inserted as the first statement in the body
    of an internal function call. It will handle the logic of
    retrieving function args, calling the underlying symbolic procedure,
    placing the return value in the correct register(s), and
    returning execution to the approprate instruction.
    """

    _internal_name: str
    _original_function: TAC_Function

    def __init__(self, internal_name: str, original_function: TAC_Function):
        """
        Args:
            internal_name: The internal name of the procedure (mostly for debugging).
            original_function: The original function that this procedure is replacing.
        """
        self._internal_name = internal_name
        self._original_function = original_function

    def as_tac_statement(self) -> typing.Type[TAC_Statement]:
        """
        Return the TAC_Statement subclass that will handle this
        procedure.
        """
        myself = self  # store self in closure

        class SimProcedureStatement(TAC_Statement):
            __internal_name__ = self._internal_name
            __aliases__ = {}

            @TAC_Statement.handler_with_side_effects
            def handle(
                self, state: "SymbolicEVMState"
            ) -> typing.List["SymbolicEVMState"]:
                arg_names = myself._original_function.arguments
                arg_vals = [state.registers[arg_name] for arg_name in arg_names]

                return myself.handle(state, arg_names, arg_vals)

        return SimProcedureStatement

    @abstractmethod
    def handle(
        self,
        state: "SymbolicEVMState",
        arg_names: typing.List[str],
        arg_vals: typing.List[typing.Any],
    ) -> typing.List["SymbolicEVMState"]:
        """
        Handle the logic of the symbolic procedure.
        """
        raise NotImplementedError("Must implement handle method")
