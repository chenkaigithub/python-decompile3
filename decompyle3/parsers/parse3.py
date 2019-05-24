#  Copyright (c) 2015-2019 Rocky Bernstein
#  Copyright (c) 2005 by Dan Pascu <dan@windowmaker.org>
#  Copyright (c) 2000-2002 by hartmut Goebel <h.goebel@crazy-compilers.com>
#  Copyright (c) 1999 John Aycock
#
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
"""
A spark grammar for Python 3.x.

However instead of terminal symbols being the usual ASCII text,
e.g. 5, myvariable, "for", etc.  they are CPython Bytecode tokens,
e.g. "LOAD_CONST 5", "STORE NAME myvariable", "SETUP_LOOP", etc.

If we succeed in creating a parse tree, then we have a Python program
that a later phase can turn into a sequence of ASCII text.
"""

from decompyle3.scanners.tok import Token
from decompyle3.parser import PythonParser, PythonParserSingle, nop_func
from decompyle3.parsers.treenode import SyntaxTree
from spark_parser import DEFAULT_DEBUG as PARSER_DEFAULT_DEBUG

class Python3Parser(PythonParser):

    def __init__(self, debug_parser=PARSER_DEFAULT_DEBUG):
        self.added_rules = set()
        super(Python3Parser, self).__init__(SyntaxTree, 'stmts', debug=debug_parser)
        self.new_rules = set()

    def p_comprehension3(self, args):
        """
        # Python3 scanner adds LOAD_LISTCOMP. Python3 does list comprehension like
        # other comprehensions (set, dictionary).

        # Our "continue" heuristic -  in two successive JUMP_BACKS, the first
        # one may be a continue - sometimes classifies a JUMP_BACK
        # as a CONTINUE. The two are kind of the same in a comprehension.

        comp_for ::= expr for_iter store comp_iter CONTINUE
        comp_for ::= expr for_iter store comp_iter JUMP_BACK

        list_comp ::= BUILD_LIST_0 list_iter
        lc_body   ::= expr LIST_APPEND
        list_for ::= expr FOR_ITER store list_iter jb_or_c

        # This is seen in PyPy, but possibly it appears on other Python 3?
        list_if     ::= expr jmp_false list_iter COME_FROM
        list_if_not ::= expr jmp_true list_iter COME_FROM

        jb_or_c ::= JUMP_BACK
        jb_or_c ::= CONTINUE

        stmt ::= set_comp_func

        set_comp_func ::= BUILD_SET_0 LOAD_FAST FOR_ITER store comp_iter
                          JUMP_BACK RETURN_VALUE RETURN_LAST

        set_comp_func ::= BUILD_SET_0 LOAD_FAST FOR_ITER store comp_iter
                          COME_FROM JUMP_BACK RETURN_VALUE RETURN_LAST

        comp_body ::= dict_comp_body
        comp_body ::= set_comp_body
        dict_comp_body ::= expr expr MAP_ADD
        set_comp_body ::= expr SET_ADD

        # See also common Python p_list_comprehension
        """

    def p_dict_comp3(self, args):
        """"
        expr ::= dict_comp
        stmt ::= dict_comp_func
        dict_comp_func ::= BUILD_MAP_0 LOAD_FAST FOR_ITER store
                           comp_iter JUMP_BACK RETURN_VALUE RETURN_LAST

        comp_iter     ::= comp_if
        comp_iter     ::= comp_if_not
        comp_if_not   ::= expr jmp_true comp_iter
        comp_iter     ::= comp_body
        """

    def p_grammar(self, args):
        '''
        sstmt ::= stmt
        sstmt ::= ifelsestmtr
        sstmt ::= return RETURN_LAST

        return_if_stmts ::= return_if_stmt come_from_opt
        return_if_stmts ::= _stmts return_if_stmt _come_froms
        return_if_stmt  ::= ret_expr RETURN_END_IF
        returns         ::= _stmts return_if_stmt

        stmt      ::= break
        break     ::= BREAK_LOOP

        stmt      ::= continue
        continue  ::= CONTINUE
        continues ::= _stmts lastl_stmt continue
        continues ::= lastl_stmt continue
        continues ::= continue


        kwarg      ::= LOAD_CONST expr
        kwargs     ::= kwarg+


        classdef ::= build_class store

        # FIXME: we need to add these because don't detect this properly
        # in custom rules. Specifically if one of the exprs is CALL_FUNCTION
        # then we'll mistake that for the final CALL_FUNCTION.
        # We can fix by triggering on the CALL_FUNCTION op
        # Python3 introduced LOAD_BUILD_CLASS
        # Other definitions are in a custom rule
        build_class ::= LOAD_BUILD_CLASS mkfunc expr call CALL_FUNCTION_3
        build_class ::= LOAD_BUILD_CLASS mkfunc expr call expr CALL_FUNCTION_4

        stmt ::= classdefdeco
        classdefdeco ::= classdefdeco1 store

        expr   ::= LOAD_ASSERT
        assert ::= assert_expr jmp_true LOAD_ASSERT RAISE_VARARGS_1 COME_FROM

        assert_expr ::= expr
        assert_expr ::= assert_expr_or
        assert_expr ::= assert_expr_and
        assert_expr_or ::= assert_expr jmp_true expr
        assert_expr_and ::= assert_expr jmp_false expr

        ifstmt ::= testexpr _ifstmts_jump

        testexpr ::= testfalse
        testexpr ::= testtrue
        testfalse ::= expr jmp_false
        testtrue ::= expr jmp_true

        _ifstmts_jump ::= return_if_stmts
        _ifstmts_jump ::= c_stmts_opt COME_FROM

        iflaststmt ::= testexpr c_stmts_opt JUMP_ABSOLUTE

        iflaststmtl ::= testexpr c_stmts_opt JUMP_BACK
        iflaststmtl ::= testexpr c_stmts_opt JUMP_BACK COME_FROM_LOOP
        iflaststmtl ::= testexpr c_stmts_opt JUMP_BACK POP_BLOCK

        # These are used to keep parse tree indices the same
        jump_forward_else  ::= JUMP_FORWARD ELSE
        jump_absolute_else ::= JUMP_ABSOLUTE ELSE

        # Note: in if/else kinds of statements, we err on the side
        # of missing "else" clauses. Therefore we include grammar
        # rules with and without ELSE.

        ifelsestmt ::= testexpr c_stmts_opt JUMP_FORWARD
                       else_suite opt_come_from_except
        ifelsestmt ::= testexpr c_stmts_opt jump_forward_else
                       else_suite _come_froms

        # ifelsestmt ::= testexpr c_stmts_opt jump_forward_else
        #                pass  _come_froms

        ifelsestmtc ::= testexpr c_stmts_opt JUMP_ABSOLUTE else_suitec
        ifelsestmtc ::= testexpr c_stmts_opt jump_absolute_else else_suitec

        ifelsestmtr ::= testexpr return_if_stmts returns

        ifelsestmtl ::= testexpr c_stmts_opt JUMP_BACK else_suitel
        ifelsestmtl ::= testexpr c_stmts_opt cf_jump_back else_suitel

        cf_jump_back ::= COME_FROM JUMP_BACK

        # FIXME: this feels like a hack. Is it just 1 or two
        # COME_FROMs?  the parsed tree for this and even with just the
        # one COME_FROM for Python 2.7 seems to associate the
        # COME_FROM targets from the wrong places

        # this is nested inside a try_except
        tryfinallystmt ::= SETUP_FINALLY suite_stmts_opt
                           POP_BLOCK LOAD_CONST
                           COME_FROM_FINALLY suite_stmts_opt END_FINALLY

        except_handler ::= jmp_abs COME_FROM except_stmts
                           END_FINALLY
        except_handler ::= jmp_abs COME_FROM_EXCEPT except_stmts
                           END_FINALLY

        # FIXME: remove this
        except_handler ::= JUMP_FORWARD COME_FROM except_stmts
                           END_FINALLY COME_FROM

        except_handler ::= JUMP_FORWARD COME_FROM except_stmts
                           END_FINALLY COME_FROM_EXCEPT

        except_stmts ::= except_stmts except_stmt
        except_stmts ::= except_stmt

        except_stmt ::= except_cond1 except_suite
        except_stmt ::= except_cond2 except_suite
        except_stmt ::= except_cond2 except_suite_finalize
        except_stmt ::= except

        ## FIXME: what's except_pop_except?
        except_stmt ::= except_pop_except

        # Python3 introduced POP_EXCEPT
        except_suite ::= c_stmts_opt POP_EXCEPT jump_except
        jump_except ::= JUMP_ABSOLUTE
        jump_except ::= JUMP_BACK
        jump_except ::= JUMP_FORWARD
        jump_except ::= CONTINUE

        # This is used in Python 3 in
        # "except ... as e" to remove 'e' after the c_stmts_opt finishes
        except_suite_finalize ::= SETUP_FINALLY c_stmts_opt except_var_finalize
                                  END_FINALLY _jump

        except_var_finalize ::= POP_BLOCK POP_EXCEPT LOAD_CONST COME_FROM_FINALLY
                                LOAD_CONST store del_stmt

        except_suite ::= returns

        except_cond1 ::= DUP_TOP expr COMPARE_OP
                         jmp_false POP_TOP POP_TOP POP_TOP

        except_cond2 ::= DUP_TOP expr COMPARE_OP
                         jmp_false POP_TOP store POP_TOP

        except  ::=  POP_TOP POP_TOP POP_TOP c_stmts_opt POP_EXCEPT _jump
        except  ::=  POP_TOP POP_TOP POP_TOP returns

        jmp_abs ::= JUMP_ABSOLUTE
        jmp_abs ::= JUMP_BACK

        ## FIXME: Right now we have erroneous jump targets
        ## This below is probably not correct when the COME_FROM is put in the right place
        and ::= expr jmp_false expr COME_FROM
        or  ::= expr jmp_true  expr COME_FROM

        # # something like the below is needed when the jump targets are fixed
        ## or  ::= expr JUMP_IF_TRUE_OR_POP COME_FROM expr
        ## and ::= expr JUMP_IF_FALSE_OR_POP COME_FROM expr
        '''

    def p_misc3(self, args):
        """
        except_handler ::= JUMP_FORWARD COME_FROM_EXCEPT except_stmts
                            END_FINALLY COME_FROM_EXCEPT_CLAUSE

        for_block ::= l_stmts_opt COME_FROM_LOOP JUMP_BACK
        for_block ::= l_stmts
        iflaststmtl ::= testexpr c_stmts_opt
        """

    def p_def_annotations3(self, args):
        """
        # Annotated functions
        stmt                  ::= function_def_annotate
        function_def_annotate ::= mkfunc_annotate store

        mkfuncdeco0 ::= mkfunc_annotate

        # This has the annotation value.
        # LOAD_NAME is used in an annotation type like
        # int, float, str
        annotate_arg    ::= LOAD_NAME
        # LOAD_CONST is used in an annotation string
        annotate_arg    ::= expr

        # This stores the tuple of parameter names
        # that have been annotated
        annotate_tuple    ::= LOAD_CONST
        """

    def p_come_from3(self, args):
        """
        opt_come_from_except ::= COME_FROM_EXCEPT
        opt_come_from_except ::= _come_froms
        opt_come_from_except ::= come_from_except_clauses

        come_from_except_clauses ::= COME_FROM_EXCEPT_CLAUSE+
        """

    def p_jump3(self, args):
        """
        jmp_false ::= POP_JUMP_IF_FALSE
        jmp_true  ::= POP_JUMP_IF_TRUE

        # FIXME: Common with 2.7
        ret_and  ::= expr JUMP_IF_FALSE_OR_POP ret_expr_or_cond COME_FROM
        ret_or   ::= expr JUMP_IF_TRUE_OR_POP ret_expr_or_cond COME_FROM
        ret_cond ::= expr POP_JUMP_IF_FALSE expr RETURN_END_IF COME_FROM ret_expr_or_cond

        or   ::= expr JUMP_IF_TRUE_OR_POP expr COME_FROM
        and  ::= expr JUMP_IF_FALSE_OR_POP expr COME_FROM

        # compare_chained1 is used exclusively in chained_compare
        compare_chained1 ::= expr DUP_TOP ROT_THREE COMPARE_OP JUMP_IF_FALSE_OR_POP
                             compare_chained1 COME_FROM
        compare_chained1 ::= expr DUP_TOP ROT_THREE COMPARE_OP JUMP_IF_FALSE_OR_POP
                             compare_chained2 COME_FROM
        """

    def p_stmt3(self, args):
        """
        stmt               ::= if_expr_lambda
        stmt               ::= conditional_not_lambda
        if_expr_lambda     ::= expr jmp_false expr return_if_lambda
                               return_stmt_lambda LAMBDA_MARKER
        conditional_not_lambda
                           ::= expr jmp_true expr return_if_lambda
                               return_stmt_lambda LAMBDA_MARKER

        return_stmt_lambda ::= ret_expr RETURN_VALUE_LAMBDA
        return_if_lambda   ::= RETURN_END_IF_LAMBDA

        stmt ::= return_closure
        return_closure ::= LOAD_CLOSURE RETURN_VALUE RETURN_LAST

        stmt ::= whileTruestmt
        ifelsestmt ::= testexpr c_stmts_opt JUMP_FORWARD else_suite _come_froms
        """

    def p_loop_stmt3(self, args):
        """
        for               ::= SETUP_LOOP expr for_iter store for_block POP_BLOCK
                              COME_FROM_LOOP

        forelsestmt       ::= SETUP_LOOP expr for_iter store for_block POP_BLOCK else_suite
                              COME_FROM_LOOP

        forelselaststmt   ::= SETUP_LOOP expr for_iter store for_block POP_BLOCK else_suitec
                              COME_FROM_LOOP

        forelselaststmtl  ::= SETUP_LOOP expr for_iter store for_block POP_BLOCK else_suitel
                              COME_FROM_LOOP

        whilestmt         ::= SETUP_LOOP testexpr l_stmts_opt COME_FROM JUMP_BACK POP_BLOCK
                              COME_FROM_LOOP

        whilestmt         ::= SETUP_LOOP testexpr l_stmts_opt JUMP_BACK POP_BLOCK
                              COME_FROM_LOOP

        whilestmt         ::= SETUP_LOOP testexpr returns          POP_BLOCK
                              COME_FROM_LOOP

        while1elsestmt    ::= SETUP_LOOP          l_stmts     JUMP_BACK
                              else_suitel

        whileelsestmt     ::= SETUP_LOOP testexpr l_stmts_opt JUMP_BACK POP_BLOCK
                              else_suitel COME_FROM_LOOP

        whileTruestmt     ::= SETUP_LOOP l_stmts_opt          JUMP_BACK POP_BLOCK
                              COME_FROM_LOOP

        # FIXME: Python 3.? starts adding branch optimization? Put this starting there.

        while1stmt        ::= SETUP_LOOP l_stmts COME_FROM_LOOP
        while1stmt        ::= SETUP_LOOP l_stmts COME_FROM JUMP_BACK COME_FROM_LOOP

        while1elsestmt    ::= SETUP_LOOP l_stmts JUMP_BACK
                              else_suite COME_FROM_LOOP

        # FIXME: investigate - can code really produce a NOP?
        for               ::= SETUP_LOOP expr for_iter store for_block POP_BLOCK NOP
                              COME_FROM_LOOP
        """

    def p_generator_exp3(self, args):
        '''
        load_genexpr ::= LOAD_GENEXPR
        load_genexpr ::= BUILD_TUPLE_1 LOAD_GENEXPR LOAD_CONST
        '''

    def p_expr3(self, args):
        """
        expr           ::= conditionalnot
        conditionalnot ::= expr jmp_true  expr jump_forward_else expr COME_FROM

        # a JUMP_FORWARD to another JUMP_FORWARD can get turned into
        # a JUMP_ABSOLUTE with no COME_FROM
        conditional    ::= expr jmp_false expr jump_absolute_else expr

        # if_expr_true are for conditions which always evaluate true
        # There is dead or non-optional remnants of the condition code though,
        # and we use that to match on to reconstruct the source more accurately
        expr           ::= if_expr_true
        if_expr_true   ::= expr JUMP_FORWARD expr COME_FROM
        """

    @staticmethod
    def call_fn_name(token):
        """Customize CALL_FUNCTION to add the number of positional arguments"""
        if token.attr is not None:
            return '%s_%i' % (token.kind, token.attr)
        else:
            return '%s_0' % (token.kind)

    def custom_build_class_rule(self, opname, i, token, tokens, customize):
        '''
        # Should the first rule be somehow folded into the 2nd one?
        build_class ::= LOAD_BUILD_CLASS mkfunc
                        LOAD_CLASSNAME {expr}^n-1 CALL_FUNCTION_n
                        LOAD_CONST CALL_FUNCTION_n
        build_class ::= LOAD_BUILD_CLASS mkfunc
                        expr
                        call
                        CALL_FUNCTION_3
         '''
        # FIXME: I bet this can be simplified
        # look for next MAKE_FUNCTION
        for i in range(i+1, len(tokens)):
            if tokens[i].kind.startswith('MAKE_FUNCTION'):
                break
            elif tokens[i].kind.startswith('MAKE_CLOSURE'):
                break
            pass
        assert i < len(tokens), "build_class needs to find MAKE_FUNCTION or MAKE_CLOSURE"
        assert tokens[i+1].kind == 'LOAD_CONST', \
          "build_class expecting CONST after MAKE_FUNCTION/MAKE_CLOSURE"
        call_fn_tok = None
        for i in range(i, len(tokens)):
            if tokens[i].kind.startswith('CALL_FUNCTION'):
                call_fn_tok = tokens[i]
                break
        if not call_fn_tok:
            raise RuntimeError("build_class custom rule for %s needs to find CALL_FUNCTION"
                               % opname)


        # customize build_class rule
        # FIXME: What's the deal with the two rules? Different Python versions?
        # Different situations? Note that the above rule is based on the CALL_FUNCTION
        # token found, while this one doesn't.
        if self.version < 3.6:
            call_function = self.call_fn_name(call_fn_tok)
            args_pos, args_kw = self.get_pos_kw(call_fn_tok)
            rule = ("build_class ::= LOAD_BUILD_CLASS mkfunc %s"
                        "%s" % (('expr ' * (args_pos - 1) + ('kwarg ' * args_kw)),
                                    call_function))
        else:
            # 3.6+ handling
            call_function = call_fn_tok.kind
            if call_function.startswith("CALL_FUNCTION_KW"):
                self.addRule("classdef ::= build_class_kw store", nop_func)
                rule = ("build_class_kw ::= LOAD_BUILD_CLASS mkfunc %sLOAD_CONST %s"
                        % ('expr ' * (call_fn_tok.attr - 1), call_function))
            else:
                call_function = self.call_fn_name(call_fn_tok)
                rule = ("build_class ::= LOAD_BUILD_CLASS mkfunc %s%s"
                         % ('expr ' * (call_fn_tok.attr - 1), call_function))
        self.addRule(rule, nop_func)
        return

    def custom_classfunc_rule(self, opname, token, customize, next_token):
        """
        call ::= expr {expr}^n CALL_FUNCTION_n
        call ::= expr {expr}^n CALL_FUNCTION_VAR_n
        call ::= expr {expr}^n CALL_FUNCTION_VAR_KW_n
        call ::= expr {expr}^n CALL_FUNCTION_KW_n

        classdefdeco2 ::= LOAD_BUILD_CLASS mkfunc {expr}^n-1 CALL_FUNCTION_n
        """
        args_pos, args_kw = self.get_pos_kw(token)

        # Additional exprs for * and ** args:
        #  0 if neither
        #  1 for CALL_FUNCTION_VAR or CALL_FUNCTION_KW
        #  2 for * and ** args (CALL_FUNCTION_VAR_KW).
        # Yes, this computation based on instruction name is a little bit hoaky.
        nak = ( len(opname)-len('CALL_FUNCTION') ) // 3

        token.kind = self.call_fn_name(token)
        uniq_param = args_kw + args_pos

        # Note: 3.5+ have subclassed this method; so we don't handle
        # 'CALL_FUNCTION_VAR' or 'CALL_FUNCTION_EX' here.
        rule = ('call ::= expr ' +
                    ('pos_arg ' * args_pos) +
                    ('kwarg ' * args_kw) +
                    'expr ' * nak + token.kind)

        self.add_unique_rule(rule, token.kind, uniq_param, customize)

        if 'LOAD_BUILD_CLASS' in self.seen_ops:
            if (next_token == 'CALL_FUNCTION' and next_token.attr == 1
                and args_pos > 1):
                rule = ('classdefdeco2 ::= LOAD_BUILD_CLASS mkfunc %s%s_%d'
                        %  (('expr ' * (args_pos-1)), opname, args_pos))
                self.add_unique_rule(rule, token.kind, uniq_param, customize)

    def add_make_function_rule(self, rule, opname, attr, customize):
        """Python 3.3 added a an addtional LOAD_CONST before MAKE_FUNCTION and
        this has an effect on many rules.
        """
        if self.version >= 3.3:
            new_rule = rule % (('LOAD_CONST ') * 1)
        else:
            new_rule = rule % (('LOAD_CONST ') * 0)
        self.add_unique_rule(new_rule, opname, attr, customize)

    def customize_grammar_rules(self, tokens, customize):
        """The base grammar we start out for a Python version even with the
        subclassing is, well, is pretty base.  And we want it that way: lean and
        mean so that parsing will go faster.

        Here, we add additional grammar rules based on specific instructions
        that are in the instruction/token stream. In classes that
        inherit from from here and other versions, grammar rules may
        also be removed.

        For example if we see a pretty rare DELETE_DEREF instruction we'll
        add the grammar for that.

        More importantly, here we add grammar rules for instructions
        that may access a variable number of stack items. CALL_FUNCTION,
        BUILD_LIST and so on are like this.

        Without custom rules, there can be an super-exponential number of
        derivations. See the deparsing paper for an elaboration of
        this.

        """

        is_pypy               = False

        # For a rough break out on the first word. This may
        # include instructions that don't need customization,
        # but we'll do a finer check after the rough breakout.
        customize_instruction_basenames = frozenset(
            ('BUILD', 'CALL',   'CONTINUE',    'DELETE', 'GET',
             'JUMP',  'LOAD',   'LOOKUP',      'MAKE',
             'RETURN', 'RAISE', 'SETUP',
             'UNPACK'))

        # Opcode names in the custom_ops_processed set have rules that get added
        # unconditionally and the rules are constant. So they need to be done
        # only once and if we see the opcode a second we don't have to consider
        # adding more rules.
        #
        # Note: BUILD_TUPLE_UNPACK_WITH_CALL gets considered by
        # default because it starts with BUILD. So we'll set to ignore it from
        # the start.
        custom_ops_processed = set(('BUILD_TUPLE_UNPACK_WITH_CALL',))

        # A set of instruction operation names that exist in the token stream.
        # We use this customize the grammar that we create.
        # 2.6-compatible set comprehensions
        self.seen_ops = frozenset([t.kind for t in tokens])
        self.seen_op_basenames = frozenset([opname[:opname.rfind('_')] for opname in self.seen_ops])

        # Loop over instructions adding custom grammar rules based on
        # a specific instruction seen.

        if 'PyPy' in customize:
            is_pypy = True
            self.addRule("""
              stmt ::= assign3_pypy
              stmt ::= assign2_pypy
              assign3_pypy       ::= expr expr expr store store store
              assign2_pypy       ::= expr expr store store
              stmt               ::= if_expr_lambda
              stmt               ::= conditional_not_lambda
              if_expr_lambda     ::= expr jmp_false expr return_if_lambda
                                     return_lambda LAMBDA_MARKER
              conditional_not_lambda
                                 ::= expr jmp_true expr return_if_lambda
                                     return_lambda LAMBDA_MARKER
              """, nop_func)

        n = len(tokens)

        # Determine if we have an iteration CALL_FUNCTION_1.
        has_get_iter_call_function1 = False
        max_branches = 0
        for i, token in enumerate(tokens):
            if token == 'GET_ITER' and i < n-2 and self.call_fn_name(tokens[i+1]) == 'CALL_FUNCTION_1':
                has_get_iter_call_function1 = True
                max_branches += 1
            elif (token == 'GET_AWAITABLE' and i < n-3
                  and tokens[i+1] == 'LOAD_CONST' and tokens[i+2] == 'YIELD_FROM'):
                max_branches += 1
            if max_branches > 2:
                break

        for i, token in enumerate(tokens):
            opname = token.kind

            # Do a quick breakout before testing potentially
            # each of the dozen or so instruction in if elif.
            if (opname[:opname.find('_')] not in customize_instruction_basenames
                    or opname in custom_ops_processed):
                continue

            opname_base = opname[:opname.rfind('_')]
            # The order of opname listed is roughly sorted below
            if opname_base == 'BUILD_CONST_KEY_MAP':
                # This is in 3.6+
                kvlist_n = 'expr ' * (token.attr)
                rule = "dict ::= %sLOAD_CONST %s" % (kvlist_n, opname)
                self.addRule(rule, nop_func)
            elif opname.startswith('BUILD_LIST_UNPACK'):
                v = token.attr
                rule = 'build_list_unpack ::= %s%s' % ('expr ' * v, opname)
                self.addRule(rule, nop_func)
                rule = 'expr ::= build_list_unpack'
                self.addRule(rule, nop_func)
            elif opname_base in ('BUILD_MAP', 'BUILD_MAP_UNPACK'):
                kvlist_n = "kvlist_%s" % token.attr
                if opname == 'BUILD_MAP_n':
                    # PyPy sometimes has no count. Sigh.
                    rule = ('dict_comp_func ::= BUILD_MAP_n LOAD_FAST FOR_ITER store '
                            'comp_iter JUMP_BACK RETURN_VALUE RETURN_LAST')
                    self.add_unique_rule(rule, 'dict_comp_func', 1, customize)

                    kvlist_n = 'kvlist_n'
                    rule = 'kvlist_n ::=  kvlist_n kv3'
                    self.add_unique_rule(rule, 'kvlist_n', 0, customize)
                    rule = 'kvlist_n ::='
                    self.add_unique_rule(rule, 'kvlist_n', 1, customize)
                    rule = "dict ::=  BUILD_MAP_n kvlist_n"

                if not opname.startswith('BUILD_MAP_WITH_CALL'):
                    # FIXME: Use the attr
                    # so this doesn't run into exponential parsing time.
                    if opname.startswith('BUILD_MAP_UNPACK'):
                        # FIXME: start here. The LHS should be unmap_dict, not dict.
                        # FIXME: really we need a combination of dict_entry-like things.
                        # It just so happens the most common case is not to mix
                        # dictionary comphensions with dictionary, elements
                        if 'LOAD_DICTCOMP' in self.seen_ops:
                            rule = 'dict ::= %s%s' % ('dict_comp ' * token.attr, opname)
                            self.addRule(rule, nop_func)
                        rule = """
                         expr       ::= unmap_dict
                         unmap_dict ::= %s%s
                         """ % ('expr ' * token.attr, opname)
                    else:
                        rule = "%s ::= %s %s" % (kvlist_n, 'expr ' * (token.attr*2), opname)
                        self.add_unique_rule(rule, opname, token.attr, customize)
                        rule = "dict ::=  %s" % kvlist_n
                self.add_unique_rule(rule, opname, token.attr, customize)
            elif opname.startswith('BUILD_MAP_UNPACK_WITH_CALL'):
                v = token.attr
                rule = 'build_map_unpack_with_call ::= %s%s' % ('expr ' * v, opname)
                self.addRule(rule, nop_func)
            elif opname.startswith('BUILD_TUPLE_UNPACK_WITH_CALL'):
                v = token.attr
                rule = ('starred ::= %s %s' % ('expr ' * v, opname))
                self.addRule(rule, nop_func)

            elif opname_base in ('BUILD_LIST', 'BUILD_SET', 'BUILD_TUPLE',
                                 'BUILD_TUPLE_UNPACK'):
                v = token.attr

                is_LOAD_CLOSURE = False
                if opname_base == 'BUILD_TUPLE':
                    # If is part of a "load_closure", then it is not part of a
                    # "list".
                    is_LOAD_CLOSURE = True
                    for j in range(v):
                        if tokens[i-j-1].kind != 'LOAD_CLOSURE':
                            is_LOAD_CLOSURE = False
                            break
                    if is_LOAD_CLOSURE:
                        rule = ('load_closure ::= %s%s' % (('LOAD_CLOSURE ' * v), opname))
                        self.add_unique_rule(rule, opname, token.attr, customize)
                if not is_LOAD_CLOSURE or v == 0:
                    # We do this complicated test to speed up parsing of
                    # pathelogically long literals, especially those over 1024.
                    build_count = token.attr
                    thousands = (build_count//1024)
                    thirty32s = ((build_count//32) % 32)
                    if thirty32s > 0:
                        rule = "expr32 ::=%s" % (' expr' * 32)
                        self.add_unique_rule(rule, opname_base, build_count, customize)
                        pass
                    if thousands > 0:
                        self.add_unique_rule("expr1024 ::=%s" % (' expr32' * 32),
                                             opname_base, build_count, customize)
                        pass
                    collection = opname_base[opname_base.find('_')+1:].lower()
                    rule = (('%s ::= ' % collection) + 'expr1024 '*thousands +
                            'expr32 '*thirty32s + 'expr '*(build_count % 32) + opname)
                    self.add_unique_rules([
                        "expr ::= %s" % collection,
                        rule], customize)
                    continue
                continue
            elif opname_base == 'BUILD_SLICE':
                if token.attr == 2:
                     self.add_unique_rules([
                        'expr ::= build_slice2',
                        'build_slice2 ::= expr expr BUILD_SLICE_2'
                        ], customize)
                else:
                    assert token.attr == 3, "BUILD_SLICE value must be 2 or 3; is %s" % v
                    self.add_unique_rules([
                        'expr ::= build_slice3',
                        'build_slice3 ::= expr expr expr BUILD_SLICE_3',
                        ], customize)
            elif (opname in frozenset(('CALL_FUNCTION',
                                       'CALL_FUNCTION_EX',
                                       'CALL_FUNCTION_EX_KW',
                                       'CALL_FUNCTION_VAR',
                                       'CALL_FUNCTION_VAR_KW'))
                  or opname.startswith('CALL_FUNCTION_KW')):

                if opname == 'CALL_FUNCTION' and token.attr == 1:
                    rule = """
                     dict_comp    ::= LOAD_DICTCOMP LOAD_CONST MAKE_FUNCTION_0 expr
                                      GET_ITER CALL_FUNCTION_1
                    classdefdeco1 ::= expr classdefdeco2 CALL_FUNCTION_1
                    """
                    if self.version < 3.5:
                        rule += """
                        classdefdeco1 ::= expr classdefdeco1 CALL_FUNCTION_1
                        """
                    self.addRule(rule, nop_func)

                self.custom_classfunc_rule(opname, token, customize, tokens[i+1])
                # Note: don't add to custom_ops_processed.

            elif opname_base == 'CALL_METHOD':
                # PyPy only - DRY with parse2

                args_pos, args_kw = self.get_pos_kw(token)

                # number of apply equiv arguments:
                nak = ( len(opname_base)-len('CALL_METHOD') ) // 3
                rule = ('call ::= expr ' +
                        ('pos_arg ' * args_pos) +
                        ('kwarg ' * args_kw) +
                        'expr ' * nak + opname)
                self.add_unique_rule(rule, opname, token.attr, customize)
            elif opname == 'CONTINUE':
                self.addRule('continue ::= CONTINUE', nop_func)
                custom_ops_processed.add(opname)
            elif opname == 'CONTINUE_LOOP':
                self.addRule('continue ::= CONTINUE_LOOP', nop_func)
                custom_ops_processed.add(opname)
            elif opname == 'DELETE_ATTR':
                self.addRule('del_stmt ::= expr DELETE_ATTR', nop_func)
                custom_ops_processed.add(opname)
            elif opname == 'DELETE_DEREF':
                self.addRule("""
                   stmt           ::= del_deref_stmt
                   del_deref_stmt ::= DELETE_DEREF
                   """, nop_func)
                custom_ops_processed.add(opname)
            elif opname == 'DELETE_SUBSCR':
                self.addRule("""
                    del_stmt ::= delete_subscript
                    delete_subscript ::= expr expr DELETE_SUBSCR
                   """, nop_func)
                custom_ops_processed.add(opname)
            elif opname == 'GET_ITER':
                self.addRule("""
                    expr      ::= get_iter
                    attribute ::= expr GET_ITER
                    """, nop_func)
                custom_ops_processed.add(opname)
            elif opname == 'JUMP_IF_NOT_DEBUG':
                v = token.attr
                self.addRule("""
                    stmt        ::= assert_pypy
                    stmt        ::= assert2_pypy", nop_func)
                    assert_pypy ::=  JUMP_IF_NOT_DEBUG assert_expr jmp_true
                                     LOAD_ASSERT RAISE_VARARGS_1 COME_FROM
                    assert2_pypy ::= JUMP_IF_NOT_DEBUG assert_expr jmp_true
                                     LOAD_ASSERT expr CALL_FUNCTION_1
                                     RAISE_VARARGS_1 COME_FROM
                    assert2_pypy ::= JUMP_IF_NOT_DEBUG assert_expr jmp_true
                                     LOAD_ASSERT expr CALL_FUNCTION_1
                                     RAISE_VARARGS_1 COME_FROM,
                    """, nop_func)
                custom_ops_processed.add(opname)
            elif opname == 'LOAD_BUILD_CLASS':
                self.custom_build_class_rule(opname, i, token, tokens, customize)
                # Note: don't add to custom_ops_processed.
            elif opname == 'LOAD_CLASSDEREF':
                # Python 3.4+
                self.addRule("expr ::= LOAD_CLASSDEREF", nop_func)
                custom_ops_processed.add(opname)
            elif opname == 'LOAD_CLASSNAME':
                self.addRule("expr ::= LOAD_CLASSNAME", nop_func)
                custom_ops_processed.add(opname)
            elif opname == 'LOAD_DICTCOMP':
                if has_get_iter_call_function1:
                    rule_pat = ("dict_comp ::= LOAD_DICTCOMP %sMAKE_FUNCTION_0 expr "
                                "GET_ITER CALL_FUNCTION_1")
                    self.add_make_function_rule(rule_pat, opname, token.attr, customize)
                    pass
                custom_ops_processed.add(opname)
            elif opname == 'LOAD_ATTR':
                self.addRule("""
                  expr      ::= attribute
                  attribute ::= expr LOAD_ATTR
                  """, nop_func)
                custom_ops_processed.add(opname)
            elif opname == 'LOAD_LISTCOMP':
                self.add_unique_rule("expr ::= listcomp", opname, token.attr, customize)
                custom_ops_processed.add(opname)
            elif opname == 'LOAD_SETCOMP':
                # Should this be generalized and put under MAKE_FUNCTION?
                if has_get_iter_call_function1:
                    self.addRule("expr ::= set_comp", nop_func)
                    rule_pat = ("set_comp ::= LOAD_SETCOMP %sMAKE_FUNCTION_0 expr "
                                "GET_ITER CALL_FUNCTION_1")
                    self.add_make_function_rule(rule_pat, opname, token.attr, customize)
                    pass
                custom_ops_processed.add(opname)
            elif opname == 'LOOKUP_METHOD':
                # A PyPy speciality - DRY with parse3
                self.addRule("""
                             expr      ::= attribute
                             attribute ::= expr LOOKUP_METHOD
                             """,
                             nop_func)
                custom_ops_processed.add(opname)
            elif opname.startswith('MAKE_CLOSURE'):
                # DRY with MAKE_FUNCTION
                # Note: this probably doesn't handle kwargs proprerly

                if opname == 'MAKE_CLOSURE_0' and 'LOAD_DICTCOMP' in self.seen_ops:
                    # Is there something general going on here?
                    # Note that 3.6+ doesn't do this, but we'll remove
                    # this rule in parse36.py
                    rule = """
                        dict_comp ::= load_closure LOAD_DICTCOMP LOAD_CONST
                                      MAKE_CLOSURE_0 expr
                                      GET_ITER CALL_FUNCTION_1
                    """
                    self.addRule(rule, nop_func)

                args_pos, args_kw, annotate_args  = token.attr

                # FIXME: Fold test  into add_make_function_rule
                if self.version < 3.3:
                    j = 1
                else:
                    j = 2
                if is_pypy or (i >= j and tokens[i-j] == 'LOAD_LAMBDA'):
                    rule_pat = ('mklambda ::= %sload_closure LOAD_LAMBDA %%s%s' %
                                ('pos_arg ' * args_pos, opname))
                    self.add_make_function_rule(rule_pat, opname, token.attr, customize)

                if has_get_iter_call_function1:
                    rule_pat = ("generator_exp ::= %sload_closure load_genexpr %%s%s expr "
                                "GET_ITER CALL_FUNCTION_1" % ('pos_arg ' * args_pos, opname))
                    self.add_make_function_rule(rule_pat, opname, token.attr, customize)

                    if has_get_iter_call_function1:
                        if (is_pypy or (i >= j and tokens[i-j] == 'LOAD_LISTCOMP')):
                            # In the tokens we saw:
                            #   LOAD_LISTCOMP LOAD_CONST MAKE_FUNCTION (>= 3.3) or
                            #   LOAD_LISTCOMP MAKE_FUNCTION (< 3.3) or
                            #   and have GET_ITER CALL_FUNCTION_1
                            # Todo: For Pypy we need to modify this slightly
                            rule_pat = ('listcomp ::= %sload_closure LOAD_LISTCOMP %%s%s expr '
                                        'GET_ITER CALL_FUNCTION_1' % ('pos_arg ' * args_pos, opname))
                            self.add_make_function_rule(rule_pat, opname, token.attr, customize)
                        if (is_pypy or (i >= j and tokens[i-j] == 'LOAD_SETCOMP')):
                            rule_pat = ('set_comp ::= %sload_closure LOAD_SETCOMP %%s%s expr '
                                        'GET_ITER CALL_FUNCTION_1' % ('pos_arg ' * args_pos, opname))
                            self.add_make_function_rule(rule_pat, opname, token.attr, customize)
                        if (is_pypy or (i >= j and tokens[i-j] == 'LOAD_DICTCOMP')):
                            self.add_unique_rule('dict_comp ::= %sload_closure LOAD_DICTCOMP %s '
                                                 'expr GET_ITER CALL_FUNCTION_1' %
                                                 ('pos_arg ' * args_pos, opname),
                                                 opname, token.attr, customize)

                if args_kw > 0:
                    kwargs_str = 'kwargs '
                else:
                    kwargs_str = ''

                # Note order of kwargs and pos args changed between 3.3-3.4
                if self.version <= 3.2:
                    rule = ('mkfunc ::= %s%sload_closure LOAD_CONST %s'
                            % (kwargs_str, 'expr ' * args_pos, opname))
                elif self.version == 3.3:
                    rule = ('mkfunc ::= %s%sload_closure LOAD_CONST LOAD_CONST %s'
                            % (kwargs_str, 'expr ' * args_pos, opname))
                elif self.version >= 3.4:
                    rule = ('mkfunc ::= %s%s load_closure LOAD_CONST LOAD_CONST %s'
                            % ('expr ' * args_pos, kwargs_str, opname))

                self.add_unique_rule(rule, opname, token.attr, customize)

                if args_kw == 0:
                    rule = ('mkfunc ::= %sload_closure load_genexpr %s'
                                % ('pos_arg ' * args_pos, opname))
                    self.add_unique_rule(rule, opname, token.attr, customize)

                if self.version < 3.4:
                    rule = ('mkfunc ::= %sload_closure LOAD_CONST %s'
                            % ('expr ' * args_pos, opname))
                    self.add_unique_rule(rule, opname, token.attr, customize)

                pass
            elif opname_base.startswith('MAKE_FUNCTION'):
                # DRY with MAKE_CLOSURE
                if self.version >= 3.6:
                    # The semantics of MAKE_FUNCTION in 3.6 are totally different from
                    # before.
                    args_pos, args_kw, annotate_args, closure  = token.attr
                    stack_count = args_pos + args_kw + annotate_args
                    if closure:
                        if args_pos:
                            rule = ('mklambda ::= %s%s%s%s' %
                                        ('expr ' * stack_count,
                                         'load_closure ' * closure,
                                         'BUILD_TUPLE_1 LOAD_LAMBDA LOAD_CONST ',
                                        opname))
                        else:
                            rule = ('mklambda ::= %s%s%s' %
                                        ('load_closure ' * closure,
                                         'LOAD_LAMBDA LOAD_CONST ',
                                        opname))
                        self.add_unique_rule(rule, opname, token.attr, customize)

                    else:
                        rule = ('mklambda ::= %sLOAD_LAMBDA LOAD_CONST %s' %
                                (('expr ' * stack_count), opname))
                        self.add_unique_rule(rule, opname, token.attr, customize)


                    rule = ('mkfunc ::= %s%s%s%s' %
                            ('expr ' * stack_count,
                             'load_closure ' * closure,
                             'LOAD_CONST ' * 2,
                             opname))
                    self.add_unique_rule(rule, opname, token.attr, customize)

                    if has_get_iter_call_function1:
                        rule_pat = ("generator_exp ::= %sload_genexpr %%s%s expr "
                                "GET_ITER CALL_FUNCTION_1" % ('pos_arg ' * args_pos, opname))
                        self.add_make_function_rule(rule_pat, opname, token.attr, customize)
                        rule_pat = ("generator_exp ::= %sload_closure load_genexpr %%s%s expr "
                                   "GET_ITER CALL_FUNCTION_1" % ('pos_arg ' * args_pos, opname))
                        self.add_make_function_rule(rule_pat, opname, token.attr, customize)
                        if is_pypy or (i >= 2 and tokens[i-2] == 'LOAD_LISTCOMP'):
                            if self.version >= 3.6:
                                # 3.6+ sometimes bundles all of the
                                # 'exprs' in the rule above into a
                                # tuple.
                                rule_pat = ("listcomp ::= load_closure LOAD_LISTCOMP %%s%s "
                                        "expr GET_ITER CALL_FUNCTION_1" % (opname,))
                                self.add_make_function_rule(rule_pat, opname, token.attr, customize)
                            rule_pat = ("listcomp ::= %sLOAD_LISTCOMP %%s%s expr "
                                        "GET_ITER CALL_FUNCTION_1" % ('expr ' * args_pos, opname))
                            self.add_make_function_rule(rule_pat, opname, token.attr, customize)

                    if is_pypy or (i >= 2 and tokens[i-2] == 'LOAD_LAMBDA'):
                        rule_pat = ('mklambda ::= %s%sLOAD_LAMBDA %%s%s' %
                                    (('pos_arg ' * args_pos),
                                     ('kwarg ' * args_kw),
                                     opname))
                        self.add_make_function_rule(rule_pat, opname, token.attr, customize)
                    continue

                if self.version < 3.6:
                    args_pos, args_kw, annotate_args  = token.attr
                else:
                    args_pos, args_kw, annotate_args, closure  = token.attr

                if self.version < 3.3:
                    j = 1
                else:
                    j = 2

                if has_get_iter_call_function1:
                    rule_pat = ("generator_exp ::= %sload_genexpr %%s%s expr "
                                "GET_ITER CALL_FUNCTION_1" % ('pos_arg ' * args_pos, opname))
                    self.add_make_function_rule(rule_pat, opname, token.attr, customize)

                    if is_pypy or (i >= j and tokens[i-j] == 'LOAD_LISTCOMP'):
                        # In the tokens we saw:
                        #   LOAD_LISTCOMP LOAD_CONST MAKE_FUNCTION (>= 3.3) or
                        #   LOAD_LISTCOMP MAKE_FUNCTION (< 3.3) or
                        #   and have GET_ITER CALL_FUNCTION_1
                        # Todo: For Pypy we need to modify this slightly
                        rule_pat  = ("listcomp ::= %sLOAD_LISTCOMP %%s%s expr "
                                     "GET_ITER CALL_FUNCTION_1" % ('expr ' * args_pos, opname))
                        self.add_make_function_rule(rule_pat, opname, token.attr, customize)

                # FIXME: Fold test  into add_make_function_rule
                if is_pypy or (i >= j and tokens[i-j] == 'LOAD_LAMBDA'):
                    rule_pat = ('mklambda ::= %s%sLOAD_LAMBDA %%s%s' %
                                (('pos_arg ' * args_pos),
                                ('kwarg ' * args_kw),
                                opname))
                    self.add_make_function_rule(rule_pat, opname, token.attr, customize)

                if args_kw == 0:
                    kwargs = 'no_kwargs'
                    self.add_unique_rule("no_kwargs ::=", opname, token.attr, customize)
                else:
                    kwargs = 'kwargs'

                if self.version < 3.3:
                    # positional args after keyword args
                    rule = ('mkfunc ::= %s %s%s%s' %
                            (kwargs, 'pos_arg ' * args_pos, 'LOAD_CONST ',
                             opname))
                    self.add_unique_rule(rule, opname, token.attr, customize)
                    rule = ('mkfunc ::= %s%s%s' %
                            ('pos_arg ' * args_pos, 'LOAD_CONST ',
                             opname))
                elif self.version == 3.3:
                    # positional args after keyword args
                    rule = ('mkfunc ::= %s %s%s%s' %
                            (kwargs, 'pos_arg ' * args_pos, 'LOAD_CONST '*2,
                             opname))
                elif self.version > 3.5:
                    # positional args before keyword args
                    rule = ('mkfunc ::= %s%s %s%s' %
                            ('pos_arg ' * args_pos, kwargs, 'LOAD_CONST '*2,
                             opname))
                elif self.version > 3.3:
                    # positional args before keyword args
                    rule = ('mkfunc ::= %s%s %s%s' %
                            ('pos_arg ' * args_pos, kwargs, 'LOAD_CONST '*2,
                             opname))
                else:
                    rule = ('mkfunc ::= %s%sexpr %s' %
                            (kwargs, 'pos_arg ' * args_pos, opname))
                self.add_unique_rule(rule, opname, token.attr, customize)

                if opname.startswith('MAKE_FUNCTION_A'):
                    if self.version >= 3.6:
                        rule = ('mkfunc_annotate ::= %s%sannotate_tuple LOAD_CONST LOAD_CONST %s' %
                                (('pos_arg ' * (args_pos)),
                                 ('call ' * (annotate_args-1)), opname))
                        self.add_unique_rule(rule, opname, token.attr, customize)
                        rule = ('mkfunc_annotate ::= %s%sannotate_tuple LOAD_CONST LOAD_CONST %s' %
                                (('pos_arg ' * (args_pos)),
                                 ('annotate_arg ' * (annotate_args-1)), opname))
                    if self.version >= 3.3:
                        # Normally we remove EXTENDED_ARG from the opcodes, but in the case of
                        # annotated functions can use the EXTENDED_ARG tuple to signal we have an annotated function.
                        # Yes this is a little hacky
                        rule = ('mkfunc_annotate ::= %s%sannotate_tuple LOAD_CONST LOAD_CONST EXTENDED_ARG %s' %
                                (('pos_arg ' * (args_pos)),
                                 ('call ' * (annotate_args-1)), opname))
                        self.add_unique_rule(rule, opname, token.attr, customize)
                        rule = ('mkfunc_annotate ::= %s%sannotate_tuple LOAD_CONST LOAD_CONST EXTENDED_ARG %s' %
                                (('pos_arg ' * (args_pos)),
                                 ('annotate_arg ' * (annotate_args-1)), opname))
                    else:
                        # See above comment about use of EXTENDED_ARG
                        rule = ('mkfunc_annotate ::= %s%sannotate_tuple LOAD_CONST EXTENDED_ARG %s' %
                                (('pos_arg ' * (args_pos)),
                                 ('annotate_arg ' * (annotate_args-1)), opname))
                        self.add_unique_rule(rule, opname, token.attr, customize)
                        rule = ('mkfunc_annotate ::= %s%sannotate_tuple LOAD_CONST EXTENDED_ARG %s' %
                                (('pos_arg ' * (args_pos)),
                                 ('call ' * (annotate_args-1)), opname))
                    self.addRule(rule, nop_func)
            elif opname == 'RETURN_VALUE_LAMBDA':
                self.addRule("""
                    return_lambda ::= ret_expr RETURN_VALUE_LAMBDA
                    """, nop_func)
                custom_ops_processed.add(opname)
            elif opname == 'RAISE_VARARGS_0':
                self.addRule("""
                    stmt        ::= raise_stmt0
                    raise_stmt0 ::= RAISE_VARARGS_0
                    """, nop_func)
                custom_ops_processed.add(opname)
            elif opname == 'RAISE_VARARGS_1':
                self.addRule("""
                    stmt        ::= raise_stmt1
                    raise_stmt1 ::= expr RAISE_VARARGS_1
                    """, nop_func)
                custom_ops_processed.add(opname)
            elif opname == 'RAISE_VARARGS_2':
                self.addRule("""
                    stmt        ::= raise_stmt2
                    raise_stmt2 ::= expr expr RAISE_VARARGS_2
                    """, nop_func)
                custom_ops_processed.add(opname)
            elif opname == 'SETUP_EXCEPT':
                self.addRule("""
                    try_except     ::= SETUP_EXCEPT suite_stmts_opt POP_BLOCK
                                       except_handler opt_come_from_except

                    tryelsestmt    ::= SETUP_EXCEPT suite_stmts_opt POP_BLOCK
                                       except_handler else_suite come_from_except_clauses

                    tryelsestmt    ::= SETUP_EXCEPT suite_stmts_opt POP_BLOCK
                                       except_handler else_suite come_froms

                    tryelsestmtl   ::= SETUP_EXCEPT suite_stmts_opt POP_BLOCK
                                       except_handler else_suitel come_from_except_clauses

                    stmt             ::= tryelsestmtl3
                    tryelsestmtl3    ::= SETUP_EXCEPT suite_stmts_opt POP_BLOCK
                                         except_handler COME_FROM else_suitel
                                         opt_come_from_except
                    """, nop_func)
                custom_ops_processed.add(opname)
            elif opname_base in ('UNPACK_EX',):
                before_count, after_count = token.attr
                rule = 'unpack ::= ' + opname + ' store' * (before_count + after_count + 1)
                self.addRule(rule, nop_func)
            elif opname_base in ('UNPACK_TUPLE', 'UNPACK_SEQUENCE'):
                rule = 'unpack ::= ' + opname + ' store' * token.attr
                self.addRule(rule, nop_func)
            elif opname_base == 'UNPACK_LIST':
                rule = 'unpack_list ::= ' + opname + ' store' * token.attr
                self.addRule(rule, nop_func)
                custom_ops_processed.add(opname)
                pass
            pass

        self.check_reduce['aug_assign1'] = 'AST'
        self.check_reduce['aug_assign2'] = 'AST'
        self.check_reduce['while1stmt'] = 'noAST'
        self.check_reduce['while1elsestmt'] = 'noAST'
        self.check_reduce['ifelsestmt'] = 'AST'
        self.check_reduce['annotate_tuple'] = 'noAST'
        self.check_reduce['kwarg'] = 'noAST'
        if self.version < 3.6:
            # 3.6+ can remove a JUMP_FORWARD which messes up our testing here
            self.check_reduce['try_except'] = 'AST'

        # FIXME: remove parser errors caused by the below
        # self.check_reduce['while1elsestmt'] = 'noAST'
        return

    def reduce_is_invalid(self, rule, ast, tokens, first, last):
        lhs = rule[0]
        if lhs in ('aug_assign1', 'aug_assign2') and ast[0][0] == 'and':
            return True
        elif lhs == 'annotate_tuple':
            return not isinstance(tokens[first].attr, tuple)
        elif lhs == 'kwarg':
            arg = tokens[first].attr
            return not isinstance(arg, str)
        elif lhs == 'while1elsestmt':

            n  = len(tokens)
            if last == n:
                # Adjust for fuzziness in parsing
                last -= 1

            if tokens[last] == 'COME_FROM_LOOP':
                last -= 1
            elif tokens[last-1] == 'COME_FROM_LOOP':
                last -= 2
            if tokens[last] in ('JUMP_BACK', 'CONTINUE'):
                # These indicate inside a loop, but token[last]
                # should not be in a loop.
                # FIXME: Not quite right: refine by using target
                return True

            # if SETUP_LOOP target spans the else part, then this is
            # not while1else. Also do for whileTrue?
            last += 1
            while last < n and isinstance(tokens[last].offset, str):
                last += 1
            if last == n:
                return False
            # 3.8+ Doesn't have SETUP_LOOP
            return self.version < 3.8 and tokens[first].attr > tokens[last].offset

        elif rule == ('try_except',
                      ('SETUP_EXCEPT', 'suite_stmts_opt', 'POP_BLOCK',
                       'except_handler', 'opt_come_from_except')):
            come_from_except = ast[-1]
            if come_from_except[0] == 'COME_FROM':
                # There should be at last two COME_FROMs, one from an
                # exception handler and one from the try. Otherwise
                # we have a try/else.
                return True
            pass
        elif lhs == 'while1stmt':

            # If there is a fall through to the COME_FROM_LOOP, then this is
            # not a while 1. So the instruction before should either be a
            # JUMP_BACK or the instruction before should not be the target of a
            # jump. (Well that last clause i not quite right; that target could be
            # from dead code. Ugh. We need a more uniform control flow analysis.)
            if last == len(tokens) or tokens[last-1] == 'COME_FROM_LOOP':
                cfl = last-1
            else:
                cfl = last
            assert tokens[cfl] == 'COME_FROM_LOOP'

            for i in range(cfl-1, first, -1):
                if tokens[i] != 'POP_BLOCK':
                    break
            if tokens[i].kind not in ('JUMP_BACK', 'RETURN_VALUE'):
                if not tokens[i].kind.startswith('COME_FROM'):
                    return True

            # Check that the SETUP_LOOP jumps to the offset after the
            # COME_FROM_LOOP
            if (0 <= last < len(tokens)
                and tokens[last] in ('COME_FROM_LOOP', 'JUMP_BACK')):
                # jump_back should be right before COME_FROM_LOOP?
                last += 1
            while last < len(tokens) and isinstance(tokens[last].offset, str):
                last += 1
            if last < len(tokens):
                offset = tokens[last].offset
                assert tokens[first] == 'SETUP_LOOP'
                if offset != tokens[first].attr:
                    return True
            return False
        elif rule == ('ifelsestmt',
                      ('testexpr', 'c_stmts_opt', 'jump_forward_else', 'else_suite', '_come_froms')):
            # Make sure the highest/smallest "come from" offset comes inside the "if".
            come_froms = ast[-1]
            if not isinstance(come_froms, Token):
                return tokens[first].offset > come_froms[-1].attr
            return False

        return False

class Python30Parser(Python3Parser):

    def p_30(self, args):
        """
        jmp_true ::= JUMP_IF_TRUE_OR_POP POP_TOP
        _ifstmts_jump ::= c_stmts_opt JUMP_FORWARD POP_TOP COME_FROM
        """

class Python3ParserSingle(Python3Parser, PythonParserSingle):
    pass

def info(args):
    # Check grammar
    p = Python3Parser()
    if len(args) > 0:
        arg = args[0]
        if arg == '3.5':
            from decompyle3.parser.parse35 import Python35Parser
            p = Python35Parser()
        elif arg == '3.3':
            from decompyle3.parser.parse33 import Python33Parser
            p = Python33Parser()
        elif arg == '3.2':
            from decompyle3.parser.parse32 import Python32Parser
            p = Python32Parser()
        elif arg == '3.0':
            p = Python30Parser()
    p.check_grammar()
    if len(sys.argv) > 1 and sys.argv[1] == 'dump':
        print('-' * 50)
        p.dump_grammar()

if __name__ == '__main__':
    import sys
    info(sys.argv)