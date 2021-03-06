#  Copyright (c) 2020 Rocky Bernstein
#  This program is free software: you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation, either version 3 of the License, or
#  (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this program.  If not, see <http://www.gnu.org/licenses/>.

from decompyle3.scanners.tok import Token

IFELSE_STMT_RULES = frozenset(
    [
        (
            "ifelsestmt",
            (
                "testexpr",
                "stmts_opt",
                "jump_forward_else",
                "else_suite",
                "_come_froms",
            ),
        ),
        ("ifelsestmtc", ("testexpr", "c_stmts_opt", "jb_cf", "else_suitec"),),
        ("ifelsestmtc", ("testexpr", "c_stmts_opt", "jb_cfs", "else_suitec"),),
        (
            "ifelsestmtc",
            (
                "testexpr", "c_stmts", "come_froms", "else_suite")
        ),
        (
            "ifelsestmt",
            (
                "testexpr",
                "stmts_opt",
                "jump_forward_else",
                "else_suite",
                "\\e__come_froms",
            ),
        ),
        (
            "ifelsestmtc",
            (
                "testexpr",
                "c_stmts_opt",
                "jump_forward_else",
                "else_suitec",
                "opt_come_from_except",
            ),
        ),
        (
            "ifelsestmtc",
            (
                "testexpr",
                "c_stmts_opt",
                "jump_forward_else",
                "else_suitec",
                "\\e_opt_come_from_except",
            ),
        ),
        (
            "ifelsestmt",
            (
                "testexpr",
                "stmts_opt",
                "jf_cfs",
                "else_suite",
                "\\e_opt_come_from_except",
            ),
        ),
        (
            "ifelsestmt",
            ("testexpr", "stmts", "come_froms", "else_suite", "come_froms",),
        ),
        (
            "ifelsestmt",
            ("testexpr", "stmts_opt", "jf_cfs", "else_suite", "opt_come_from_except",),
        ),
        (
            "ifelsestmt",
            (
                "testexpr",
                "stmts_opt",
                "jump_forward_else",
                "else_suite",
                "\\e__come_froms",
            ),
        ),
    ]
)


def ifelsestmt(
    self, lhs: str, n: int, rule, ast, tokens: list, first: int, last: int
) -> bool:

    if (last + 1) < n and tokens[last + 1] == "COME_FROM_LOOP":
        # ifelsestmt jumped outside of loop. No good.
        return True
    # print("XXX", first, last, rule)
    # if (first, last) == (6, 23):
    #     for t in range(first, last): print(tokens[t])
    #     print("="*40)
    #     from trepan.api import debug; debug()

    # if lhs == "ifelsestmtc":
    #     print("XXX", first, last, rule)
    #     for t in range(first, last):
    #         print(tokens[t])
    #     print("=" * 40)
    #     if (first, last) == (4, 47):
    #         from trepan.api import debug; debug()

    if rule not in IFELSE_STMT_RULES:
        return False

    # Make sure all the offsets from the "come froms" at the
    # end of the "if" come from somewhere inside the "if".
    # Since the come_froms are ordered so that lowest
    # offset COME_FROM is last, it is sufficient to test
    # just the last one.
    if len(ast) == 5:
        end_come_froms = ast[-1]
        if end_come_froms == "opt_come_from_except" and len(end_come_froms) > 0:
            end_come_froms = end_come_froms[0]
        if not isinstance(end_come_froms, Token):
            if len(end_come_froms) and tokens[first].offset > end_come_froms[-1].attr:
                return True
        elif tokens[first].offset > end_come_froms.attr:
            return True

    testexpr = ast[0]

    # Check that the condition portion of the "if"
    # jumps to the "else" part.
    if testexpr[0] in ("testtrue", "testfalse"):
        if_condition = testexpr[0]

        else_suite = ast[3]
        assert else_suite in ("else_suite", "else_suitec")

        if else_suite == "else_suitec" and ast[2] in ("jb_elsec", "jb_cfs", "jump_forward_else"):
            stmts = ast[1]
            jb_else = ast[2]
            come_from = jb_else[-1]
            if come_from in ("come_froms", "_come_froms") and len(come_from):
                come_from = come_from[-1]
            if come_from == "COME_FROM":
                if come_from.attr > stmts.first_child().off2int():
                    return True
                pass
            pass

        if len(if_condition) > 1 and if_condition[1].kind.startswith("POP_JUMP_IF_"):
            if last == n:
                last -= 1

            jmp = if_condition[1]
            jump_target = jmp.attr

            # Below we check that jump_target is jumping to a feasible
            # location. It should be to the transition after the "then"
            # block and to the beginning of the "else" block.
            # However the "if/else" is inside a loop the false test can be
            # back to the loop.

            # FIXME: the below logic for jf_cfs could probably be
            # simplified.
            jump_else_end = ast[2]
            if jump_else_end == "jf_cf_pop":
                jump_else_end = jump_else_end[0]

            jump_to_jump = False
            if jump_else_end == "JUMP_FORWARD":
                jump_to_jump = True
                endif_target = int(jump_else_end.pattr)
                last_offset = tokens[last].off2int()
                if endif_target != last_offset:
                    return True
            last_offset = tokens[last].off2int(prefer_last=False)
            if jump_target == last_offset:
                # jump_target should be jumping to the end of the if/then/else
                # but is it jumping to the beginning of the "else"
                return True
            if (
                jump_else_end in ("jf_cfs", "jump_forward_else")
                and jump_else_end[0] == "JUMP_FORWARD"
            ):
                # If the "else" jump jumps before the end of the the "if .. else end", then this
                # is not this kind of "ifelsestmt".
                jump_else_forward = jump_else_end[0]
                jump_else_forward_target = jump_else_forward.attr
                if jump_else_forward_target < last_offset:
                    return True
                pass
            if (
                jump_else_end in ("jb_elsec", "jf_cfs", "jb_cfs")
                and jump_else_end[-1] == "COME_FROM"
            ):
                if jump_else_end[-1].off2int() != jump_target:
                    return True

            if tokens[first].off2int() > jump_target:
                return True

            return (jump_target > last_offset) and tokens[last] != "JUMP_FORWARD"

    return False
