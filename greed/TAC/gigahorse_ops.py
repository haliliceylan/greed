import logging

from greed.TAC.base import TAC_Statement
from greed.solver.shortcuts import *
from greed.state import SymbolicEVMState
from greed.utils.exceptions import VMNoSuccessors

__all__ = ['TAC_Throw', 'TAC_Callprivate', 'TAC_Returnprivate', 'TAC_Phi', 'TAC_Const', 'TAC_Nop']

log = logging.getLogger(__name__)

"""
This module contains the TAC statements that are reserved by Gigahorse.
"""

class TAC_Throw(TAC_Statement):
    __internal_name__ = "THROW"

    @TAC_Statement.handler_with_side_effects
    def handle(self, state: SymbolicEVMState):
        state.halt = True
        return [state]


class TAC_Callprivate(TAC_Statement):
    __internal_name__ = "CALLPRIVATE"
    __aliases__ = {}

    @TAC_Statement.handler_with_side_effects
    def handle(self, state: SymbolicEVMState):
        # read target
        target_bb_id = hex(bv_unsigned_value(self.arg1_val))
        target_bb = state.project.factory.block(target_bb_id)

        try:
            saved_return_pc = state.get_fallthrough_pc()
        except VMNoSuccessors:
            fake_exit_bb = state.project.factory.block('fake_exit')
            saved_return_pc = fake_exit_bb.statements[0].id

        # read arg-alias map
        args = self.arg_vars[1:]
        args_alias = target_bb.function.arguments
        if len(args) != len(args_alias):
            # NOTE: if just the saved return pc is missing, we can handle that since we keep the callstack
            log.warning("Invalid CALLPRIVATE arguments")

        # NOTE: this assumes that the arguments are in the same order and cardinality, ignoring extra arguments
        # If the registers that remain unset are never used, the execution will succeed
        # Otherwise, the execution will fail with "uninitialized variable"
        alias_arg_map = dict(zip(args_alias, args))
        for alias, arg in alias_arg_map.items():
            state.registers[alias] = state.registers[arg]

        # read destination
        dest = target_bb.first_ins.id
        state.callstack.append((state.pc, saved_return_pc, self.res_vars))

        # jump to target
        state.pc = dest
        return [state]


class TAC_Returnprivate(TAC_Statement):
    __internal_name__ = "RETURNPRIVATE"
    __aliases__ = {}

    @TAC_Statement.handler_with_side_effects
    def handle(self, state: SymbolicEVMState):
        returnprivate_arg_names = self.arg_vars[1:]
        returnprivate_args = [state.registers[arg] for arg in returnprivate_arg_names]

        return self.return_values(state, returnprivate_args)

    @staticmethod
    def return_values(state: SymbolicEVMState, values: list):
        """
        Perform a function return, returning the values in the given list.

        This function is static so that it can be called from the symprocedures.
        """
        callprivate_pc, saved_return_pc, callprivate_return_vars = state.callstack.pop()

        for callprivate_return_var, value in zip(callprivate_return_vars, values):
            state.registers[callprivate_return_var] = value
        
        state.pc = saved_return_pc

        return [state]

class TAC_Phi(TAC_Statement):
    __internal_name__ = "PHI"
    __aliases__ = {}

    @TAC_Statement.handler_without_side_effects
    def handle(self, state: SymbolicEVMState):
        state.set_next_pc()
        return [state]


class TAC_Const(TAC_Statement):
    __internal_name__ = "CONST"
    __aliases__ = {}

    @TAC_Statement.handler_without_side_effects
    def handle(self, state: SymbolicEVMState):
        state.registers[self.res1_var] = self.res1_val
        state.set_next_pc()
        return [state]


class TAC_Nop(TAC_Statement):
    __internal_name__ = "NOP"

    # @TAC_Statement.handler_without_side_effects
    def handle(self, state: SymbolicEVMState):
        state.set_next_pc()
        return [state]


class TAC_Callprivateargs(TAC_Statement):
    __internal_name__ = "CALLPRIVATEARG"

    def handle(self, state: SymbolicEVMState):
        state.set_next_pc()
        return [state]
