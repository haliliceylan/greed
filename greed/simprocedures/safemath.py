"""
Simprocedure stubs for SAFEMATH functions:
safe_add, safe_sub, safe_mul, safe_div

These stubs produce constraints that are more friendly to
the solver than their original implementations.
"""

import typing

from greed.solver.shortcuts import *
from greed.TAC.gigahorse_ops import TAC_Returnprivate

from .base import BaseSimProcedure

if typing.TYPE_CHECKING:
    from greed.function import TAC_Function
    from greed.state import SymbolicEVMState


class SimProcedureSafeMul(BaseSimProcedure):

    def __init__(self, original_function: "TAC_Function"):
        super().__init__("SIMPROCEDURE_SAFEMUL", original_function)

    def handle(self, state: "SymbolicEVMState", _arg_names, arg_vals):
        assert len(arg_vals) == 2, f"Expected 2 arguments, got {len(arg_vals)}"

        # get the arguments to SAFE_MUL
        a, b = arg_vals

        # Is anything concrete? If so we can just return the result.
        a_concrete = state.solver.is_concrete(a)
        b_concrete = state.solver.is_concrete(b)
        if a_concrete:
            a_val = state.solver.eval(a)
        if b_concrete:
            b_val = state.solver.eval(b)

        if a_concrete and b_concrete:
            result_i = a_val * b_val
            # if result fits within 1 word, use it as return value
            if result_i < 2**256:
                result = BVV(a_val * b_val, 256)
            else:
                # no non-revert states
                return []
        # if one of the arguments is concrete, we can do some simplification
        elif a_concrete or b_concrete:
            conc_val, sym = (a_val, b) if a_concrete else (b_val, a)

            if conc_val == 0:
                # if either is zero, the result is zero
                result = BVV(0, 256)
            if conc_val == 1:
                # if either is one, the result is the other
                result = sym
            else:
                # we can simply constrain the sym value to be such that (conc_val * sym) < 2**256
                limit = 2**256 // conc_val
                new_constraint = BV_ULT(sym, BVV(limit, 256))
                setattr(new_constraint, "safemath", True)
                state.solver.add_path_constraint(new_constraint)
                result = BV_Mul(a, b)
        else:
            # do the multiplication
            a_extended = BV_Zero_Extend(a, 256)
            b_extended = BV_Zero_Extend(b, 256)
            result_extended = BV_Mul(a_extended, b_extended)

            # assert no overflow
            limit = BVV((1 << 256), 256 * 2)
            new_constraint = BV_ULT(result_extended, limit)
            setattr(new_constraint, "safemath", True)
            state.solver.add_path_constraint(new_constraint)

            # extract the result
            result = BV_Mul(a, b)

        # do a sym return
        return TAC_Returnprivate.return_values(state, [result])


class SimProcedureSafeDiv(BaseSimProcedure):

    def __init__(self, original_function: "TAC_Function"):
        super().__init__("SIMPROCEDURE_SAFEDIV", original_function)

    def handle(self, state: SymbolicEVMState, _arg_names, _arg_vals):
        assert len(_arg_vals) == 2, f"Expected 2 arguments, got {len(_arg_vals)}"

        # get the arguments to SAFE_DIV
        a, b = _arg_vals

        # do the division
        result = BV_UDiv(a, b)

        # assert no divide by zero
        new_constraint = NotEqual(b, BVV(0, 256))
        setattr(new_constraint, "safemath", True)
        state.solver.add_path_constraint(new_constraint)

        # do a sym return
        return TAC_Returnprivate.return_values(state, [result])


class SimProcedureSafeAdd(BaseSimProcedure):

    def __init__(self, original_function: "TAC_Function"):
        super().__init__("SIMPROCEDURE_SAFEADD", original_function)

    def handle(self, state: SymbolicEVMState, _arg_names, _arg_vals):
        assert len(_arg_vals) == 2, f"Expected 2 arguments, got {len(_arg_vals)}"

        # get the arguments to SAFE_ADD
        a, b = _arg_vals

        a_concrete = state.solver.is_concrete(a)
        b_concrete = state.solver.is_concrete(b)
        if a_concrete:
            a_val = state.solver.eval(a)
        if b_concrete:
            b_val = state.solver.eval(b)

        if a_concrete and b_concrete:
            result_i = a_val + b_val
            # if result fits within 1 word, use it as return value
            if result_i < 2**256:
                result = BVV(a_val + b_val, 256)
            else:
                # no non-revert states
                return []
        # if one of the arguments is concrete, we can do some simplification
        elif a_concrete or b_concrete:
            conc_val, sym = (a_val, b) if a_concrete else (b_val, a)

            # if the concrete value is zero, the result is the other
            if conc_val == 0:
                result = sym
            else:
                # we can simply constrain the sym value to be such that (conc_val + sym) < 2**256
                assert conc_val > 0, f"Expected positive concrete value, got {conc_val}"
                limit = 2**256 - conc_val
                new_constraint = BV_ULT(sym, BVV(limit, 256))
                setattr(new_constraint, "safemath", True)
                state.solver.add_path_constraint(new_constraint)
                result = BV_Add(a, b)
        else:
            # extend by 1 bit (the carry)
            a_extended = BV_Zero_Extend(a, 1)
            b_extended = BV_Zero_Extend(b, 1)

            result_extended = BV_Add(a_extended, b_extended)
            limit = BVV((1 << 256), 257)
            new_constraint = BV_ULT(result_extended, limit)
            setattr(new_constraint, "safemath", True)
            state.solver.add_path_constraint(new_constraint)

            # do the addition
            result = BV_Add(a, b)

        # do a sym return
        return TAC_Returnprivate.return_values(state, [result])


class SimProcedureSafeSub(BaseSimProcedure):

    def __init__(self, original_function: "TAC_Function"):
        super().__init__("SIMPROCEDURE_SAFESUB", original_function)

    def handle(self, state: SymbolicEVMState, _arg_names, _arg_vals):
        assert len(_arg_vals) == 2, f"Expected 2 arguments, got {len(_arg_vals)}"

        # get the arguments to SAFE_SUB
        a, b = _arg_vals

        a_concrete = state.solver.is_concrete(a)
        b_concrete = state.solver.is_concrete(b)
        if a_concrete:
            a_val = state.solver.eval(a)
        if b_concrete:
            b_val = state.solver.eval(b)

        if a_concrete and b_concrete:
            result_i = a_val - b_val
            # if result does not underflow (i.e., is positive), use it as return value
            if result_i >= 0:
                result = BVV(a_val - b_val, 256)
            else:
                # no non-revert states
                return []
        else:
            # do the subtraction
            result = BV_Sub(a, b)

            # assert no underflow
            new_constraint = BV_UGE(a, b)
            setattr(new_constraint, "safemath", True)
            state.solver.add_path_constraint(new_constraint)

        # do a sym return
        return TAC_Returnprivate.return_values(state, [result])
