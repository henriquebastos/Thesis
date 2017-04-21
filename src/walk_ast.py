import ast

import utils


def walk_ast(node, current_scope):
    walker = WalkAST(current_scope)
    walker.visit(node)
    return walker


def walk_ast_for_names(node, current_scope):
    walker = WalkAST(current_scope)
    walker.get_names = True
    walker.visit(node)
    return walker


def walk_ast_for_expr(node, current_scope):
    walker = WalkAST(current_scope)
    walker.is_bin_op = True
    walker.visit(node)
    return walker


class WalkAST(ast.NodeVisitor):

    def __init__(self, current_scope=None):
        self.data = {}
        self.variable_scope = {'global': []}
        self.current_scope = 'global'
        if current_scope is not None:
            self.current_scope = current_scope
        self.line = ''
        self.is_bin_op = False
        self.get_names = False
        self.lineno = None
        self.function_name = None

    def print_map(self):
        self.remove_empty_expressions()
        # print
        # print 'Line Expressions:'
        # print '-----------------'
        # for line_num, line in self.data.iteritems():
        #     print '{0}: {1}'.format(line_num, line)

    def remove_empty_expressions(self):
        for lineno in self.data.keys():
            utils.remove_empty_string(self.data, lineno)

    #
    # mod
    #

    # Module(stmt* body)
    def visit_Module(self, node):
        # print 'Module'
        for stmt in node.body:
            walker = walk_ast(stmt, self.current_scope)
            utils.add_string_to_data(stmt.lineno, walker.data,
                                     walker.line)
            utils.combine_all_data(self.data, walker.data)
            utils.combine_variable_scopes(self.variable_scope,
                                          walker.variable_scope)
        # self.generic_visit(node)

    # Interactive(stmt* body)
    def visit_Interactive(self, node):
        # print 'Module Interactive'
        self.generic_visit(node)

    # Expression(expr body)
    def visit_Expression(self, node):
        # print 'Module Expr'
        self.generic_visit(node)

    # Suite(stmt* body)
    def visit_Suite(self, node):
        # print 'Module Suite'
        self.generic_visit(self, node)

    def visit_Import(self, node):
        utils.set_type(self.data, node.lineno, 'import')
        self.lineno = node.lineno
        for name in node.names:
            walker = WalkAST()
            walker.lineno = node.lineno
            walker.visit(name)
            utils.combine_all_data(self.data, walker.data)

    #
    # stmt
    #

    # FunctionDef(identifier name, arguments args,
    #             stmt* body, expr* decorator_list)
    def visit_FunctionDef(self, node):
        # print '{0}: FunctionDef - def {1}():'.format(node.lineno, node.name)
        utils.set_type(self.data, node.lineno, 'func')
        utils.set_name(self.data, node.lineno, node.name)
        utils.add_function_def(self.data, node.name, node.lineno)
        self.variable_scope[node.name] = []
        arg_walker = WalkAST(node.name)
        arg_walker.lineno = node.lineno
        arg_walker.visit(node.args)
        utils.combine_data(node.lineno, self.data, arg_walker.data)
        utils.combine_variable_scopes(self.variable_scope,
                                      arg_walker.variable_scope)
        for stmts in [node.body, node.decorator_list]:
            for stmt in stmts:
                walker = walk_ast(stmt, node.name)
                utils.add_string_to_data(stmt.lineno, walker.data,
                                         walker.line)
                utils.add_function_line(self.data, node.name, stmt.lineno)
                # utils.combine_data(stmt.lineno, self.data, walker.data)
                utils.combine_all_data(self.data, walker.data)
                utils.combine_variable_scopes(self.variable_scope,
                                              walker.variable_scope)
        # self.generic_visit(node)

    # ClassDef(identifier name, expr* bases, stmt* body, expr* decorator_list)
    def visit_ClassDef(self, node):
        # print '{0}: ClassDef Name: {1}'.format(node.lineno, node.name)
        utils.set_type(self.data, node.lineno, 'class')
        utils.set_name(self.data, node.lineno, node.name)
        utils.add_class(self.data, node.name)
        # Add class functions
        # Add class variables (only self.* variables)
        # self.generic_visit(node)
        for stmts in [node.bases, node.body, node.decorator_list]:
            for stmt in stmts:
                walker = walk_ast(stmt, self.current_scope)  # possibly switch scope to Class
                utils.add_string_to_data(stmt.lineno, walker.data,
                                         walker.line)
                # utils.add_function_line(self.data, node.name, stmt.lineno)
                utils.combine_all_data(self.data, walker.data)
                utils.combine_variable_scopes(self.variable_scope,
                                              walker.variable_scope)
                utils.add_function_to_class(self.data, walker.data, node.name)
                utils.add_variables_to_class(self.data, walker.variable_scope,
                                             node.name)

    # Return(expr? value)
    def visit_Return(self, node):
        # print '{0}: self.line +='.format(node.lineno)
        utils.set_type(self.data, node.lineno, 'return')
        if node.value is not None:
            walker = walk_ast_for_expr(node.value, self.current_scope)
            # print walker.data
            # print self.data
            # print walker.line
            utils.combine_data(node.lineno, self.data, walker.data)
            utils.add_string_to_data(node.lineno, self.data, walker.line)
            utils.combine_variable_scopes(self.variable_scope,
                                          walker.variable_scope)

    # Delete(expr* targets)
    def visit_Delete(self, node):
        # print '{0}: Delete'.format(node.lineno)
        self.generic_visit(node)
        utils.set_type(self.data, node.lineno, 'delete')

    # Assign(expr* targets, expr value)
    def visit_Assign(self, node):
        # print '{0}: Assign'.format(node.lineno)
        self.line = ''
        utils.set_type(self.data, node.lineno, 'assign')
        for target in node.targets:
            target_walker = walk_ast_for_names(target, self.current_scope)
            utils.set_assign(self.data, node.lineno, target_walker.line)
            utils.set_assigned_expressions(
                self.data, node.lineno, target_walker.line,
                target_walker.data[node.lineno]['expressions'])
            utils.combine_variable_scopes(self.variable_scope,
                                          target_walker.variable_scope)
            # utils.combine_data(node.lineno, self.data, target_walker.data)
        value_walker = walk_ast_for_expr(node.value, self.current_scope)
        utils.add_string_to_data(node.lineno, value_walker.data,
                                 value_walker.line)
        utils.combine_data(node.lineno, self.data, value_walker.data)
        # TODO
        utils.combine_variable_scopes(self.variable_scope,
                                      value_walker.variable_scope)
        # self.generic_visit(node)

    # AugAssign(expr target, operator op, expr value)
    def visit_AugAssign(self, node):
        # print '{0}: AugAssign'.format(node.lineno)
        target_walker = walk_ast_for_names(node.target, self.current_scope)
        utils.add_string_to_data(node.lineno, target_walker.data,
                                 target_walker.line)
        utils.combine_data(node.lineno, self.data, target_walker.data)
        utils.combine_variable_scopes(self.variable_scope,
                                      target_walker.variable_scope)
        op_walker = walk_ast_for_expr(node.op, self.current_scope)
        utils.combine_variable_scopes(self.variable_scope,
                                      op_walker.variable_scope)
        value_walker = walk_ast_for_expr(node.value, self.current_scope)
        utils.combine_variable_scopes(self.variable_scope,
                                      value_walker.variable_scope)
        utils.add_string_to_data(node.lineno, value_walker.data,
                                 value_walker.line)
        utils.combine_data(node.lineno, self.data, value_walker.data)
        self.line = '{0}{1}{2}'.format(target_walker.line, op_walker.line,
                                       value_walker.line)
        utils.add_string_to_data(node.lineno, self.data, self.line)
        utils.set_type(self.data, node.lineno, 'assign')
        utils.set_assign(self.data, node.lineno, target_walker.line)
        # self.generic_visit(node)

    # Print(expr? dest, expr* values, bool nl)
    def visit_Print(self, node):
        # print '{0}: Print'.format(node.lineno)
        # print 'Has New Line: {0}'.format(node.nl)
        utils.set_type(self.data, node.lineno, 'print')
        for value in node.values:
            # walker = walk_ast_for_names(value)
            walker = walk_ast_for_expr(value, self.current_scope)
            utils.add_string_to_data(node.lineno, walker.data, walker.line)
            utils.combine_data(node.lineno, self.data, walker.data)
            utils.combine_variable_scopes(self.variable_scope,
                                          walker.variable_scope)
        self.generic_visit(node)

    # For(expr target, expr iter, stmt* body, stmt* orelse)
    def visit_For(self, node):
        # print '{0}: For'.format(node.lineno)
        utils.add_loop_def(self.data, node.lineno)
        target_walker = walk_ast_for_names(node.target, self.current_scope)
        utils.add_string_to_data(node.lineno, target_walker.data,
                                 target_walker.line)
        utils.add_targets_to_data(node.lineno, self.data, target_walker.data)
        utils.combine_variable_scopes(self.variable_scope,
                                      target_walker.variable_scope)
        expr_walker = walk_ast_for_names(node.iter, self.current_scope)
        utils.add_string_to_data(node.lineno, expr_walker.data,
                                 expr_walker.line)
        utils.combine_data(node.lineno, self.data, expr_walker.data)
        utils.combine_variable_scopes(self.variable_scope,
                                      expr_walker.variable_scope)
        for stmts in [node.body, node.orelse]:
            for stmt in stmts:
                utils.add_loop_line(self.data, node.lineno, stmt.lineno)
                walker = walk_ast(stmt, self.current_scope)
                utils.add_string_to_data(stmt.lineno, walker.data,
                                         walker.line)
                # utils.combine_data(stmt.lineno, self.data, walker.data)
                utils.combine_all_data(self.data, walker.data)
                utils.combine_variable_scopes(self.variable_scope,
                                              walker.variable_scope)
        utils.set_type(self.data, node.lineno, 'loop')

    # While(expr test, stmt* body, stmt* orelse)
    def visit_While(self, node):
        # print '{0}: While'.format(node.lineno)
        utils.add_loop_def(self.data, node.lineno)
        test_walker = WalkAST(self.current_scope)
        test_walker.get_names = True
        test_walker.visit(node.test)
        utils.add_string_to_data(node.lineno, test_walker.data,
                                 test_walker.line)
        utils.combine_data(node.lineno, self.data, test_walker.data)
        utils.combine_variable_scopes(self.variable_scope,
                                      test_walker.variable_scope)
        for stmts in [node.body, node.orelse]:
            for stmt in stmts:
                utils.add_loop_line(self.data, node.lineno, stmt.lineno)
                walker = walk_ast(stmt, self.current_scope)
                utils.add_string_to_data(stmt.lineno, walker.data,
                                         walker.line)
                # utils.combine_data(stmt.lineno, self.data, walker.data)
                utils.combine_all_data(self.data, walker.data)
                utils.combine_variable_scopes(self.variable_scope,
                                              walker.variable_scope)
        utils.set_type(self.data, node.lineno, 'loop')

    # If(expr test, stmt* body, stmt* orelse)
    def visit_If(self, node):
        # print '{0}: Stmt If'.format(node.lineno)
        self.line = ''
        test_walker = walk_ast_for_expr(node.test, self.current_scope)
        utils.add_string_to_data(node.lineno, test_walker.data,
                                 test_walker.line)
        utils.combine_data(node.lineno, self.data, test_walker.data)
        utils.combine_variable_scopes(self.variable_scope,
                                      test_walker.variable_scope)
        for stmts in [node.body, node.orelse]:
            for stmt in stmts:
                walker = walk_ast(stmt, self.current_scope)
                utils.add_string_to_data(stmt.lineno, walker.data, walker.line)
                utils.combine_data(stmt.lineno, self.data, walker.data)
                utils.combine_variable_scopes(self.variable_scope,
                                              walker.variable_scope)
                utils.remove_empty_string(self.data, stmt.lineno)
        utils.set_type(self.data, node.lineno, 'conditional')
        # self.generic_visit(node)

    # With(expr context_expr, expr? optional_vars, stmt* body)
    def visit_With(self, node):
        # print '{0}: With'.format(node.lineno)
        context_expr = walk_ast_for_expr(node.context_expr, self.current_scope)
        utils.add_string_to_data(node.lineno, context_expr.data,
                                 context_expr.line)
        utils.combine_data(node.lineno, self.data, context_expr.data)
        utils.combine_variable_scopes(self.variable_scope,
                                      context_expr.variable_scope)
        if node.optional_vars is not None:
            optional_vars_walker = walk_ast_for_names(node.optional_vars,
                                                      self.current_scope)
            utils.set_type(self.data, node.lineno, 'assign')
            utils.set_assign(self.data, node.lineno, optional_vars_walker.line)
            utils.combine_variable_scopes(self.variable_scope,
                                          optional_vars_walker.variable_scope)
        for stmt in node.body:
                walker = walk_ast(stmt, self.current_scope)
                utils.add_string_to_data(stmt.lineno, walker.data, walker.line)
                utils.combine_data(stmt.lineno, self.data, walker.data)
                utils.combine_variable_scopes(self.variable_scope,
                                              walker.variable_scope)
                utils.remove_empty_string(self.data, stmt.lineno)
        # self.generic_visit(node)

    # Raise(expr? type, expr? inst, expr? tback)
    def visit_Raise(self, node):
        # print '{0}: Raise'.format(node.lineno)
        self.generic_visit(node)

    # TryExcept(stmt* body, excepthandler* handlers, stmt* orelse)
    def visit_TryExcept(self, node):
        # print '{0}: TryExcept'.format(node.lineno)
        self.generic_visit(node)

    # TryFinally(stmt* body, stmt* finalbody)
    def visit_TryFinally(self, node):
        # print '{0}: TryFinally'.format(node.lineno)
        self.generic_visit(node)

    # Exec(expr body, expr? globals, expr? locals)
    def visit_Exec(self, node):
        # print '{0}: Exec'.format(node.lineno)
        self.generic_visit(node)

    # Global(identifier* names)
    def visit_Global(self, node):
        # print '{0}: Globals'.format(node.lineno)
        self.generic_visit(node)

    # Expr(expr value)
    def visit_Expr(self, node):
        # print '{0}: Expression'.format(node.lineno)
        self.generic_visit(node)

    def visit_Pass(self, node):
        # print '{0}: Pass'.format(node.lineno)
        self.generic_visit(node)

    def visit_Break(self, node):
        # print '{0}: Break'.format(node.lineno)
        self.generic_visit(node)

    def visit_Continue(self, node):
        # print '{0}: Continue'.format(node.lineno)
        self.generic_visit(node)

    #
    # expr
    #

    # BoolOp(boolop op, expr* values)
    def visit_BoolOp(self, node):
        # print '{0} BOOL_OP:'.format(node.lineno)
        op_walker = walk_ast_for_expr(node.op, self.current_scope)
        utils.combine_variable_scopes(self.variable_scope,
                                      op_walker.variable_scope)
        first_node = True
        for n in node.values:
            walker = walk_ast_for_expr(n, self.current_scope)
            utils.add_string_to_data(node.lineno, walker.data, walker.line)
            utils.combine_data(node.lineno, self.data, walker.data)
            utils.combine_variable_scopes(self.variable_scope,
                                          walker.variable_scope)
            if first_node:
                first_node = False
                self.line += walker.line
            else:
                self.line = '(' + self.line + ' ' + op_walker.line + ' ' + \
                            walker.line + ')'
            utils.add_string_to_data(node.lineno, self.data, self.line)

    # BinOp(expr left, operator op, expr right)
    def visit_BinOp(self, node):
        walker = WalkAST(self.current_scope)
        walker.is_bin_op = True
        walker.visit(node.left)
        walker.visit(node.op)
        walker.visit(node.right)
        walker.line = '(' + walker.line + ')'
        utils.add_string_to_data(node.lineno, walker.data, walker.line)
        utils.combine_data(node.lineno, self.data, walker.data)
        utils.combine_variable_scopes(self.variable_scope,
                                      walker.variable_scope)
        self.line += walker.line
        utils.add_string_to_data(node.lineno, self.data, self.line)

    # UnaryOp(unaryop op, expr operand)
    def visit_UnaryOp(self, node):
        # print '{0}:'.format(node.lineno)
        op_walker = walk_ast(node.op, self.current_scope)
        utils.combine_variable_scopes(self.variable_scope,
                                      op_walker.variable_scope)
        expr_walker = walk_ast_for_expr(node.operand, self.current_scope)
        utils.combine_variable_scopes(self.variable_scope,
                                      expr_walker.variable_scope)
        # print '\t' + op_walker.line + ' ' + expr_walker.line
        utils.add_string_to_data(node.lineno, expr_walker.data,
                                 expr_walker.line)
        utils.combine_data(node.lineno, self.data, expr_walker.data)
        self.line += op_walker.line + ' ' + expr_walker.line
        utils.add_string_to_data(node.lineno, self.data, self.line)

    # Lambda(arguments args, expr body)
    def visit_Lambda(self, node):
        # print '{0}:'.format(node.lineno)
        self.generic_visit(node)

    # IfExp(expr test, expr body, expr orelse)
    def visit_IfExp(self, node):
        # print '{0}: If'.format(node.lineno)
        self.generic_visit(node)

    # Dict(expr* keys, expr* values)
    def visit_Dict(self, node):
        # print '{0}: Dict'.format(node.lineno)
        for value in node.values:
            walker = walk_ast_for_expr(value, self.current_scope)
            utils.add_string_to_data(node.lineno, walker.data, walker.line)
            utils.combine_data(node.lineno, self.data, walker.data)
            utils.combine_variable_scopes(self.variable_scope,
                                          walker.variable_scope)

        # self.generic_visit(node)

    # Set(expr* elts)
    def visit_Set(self, node):
        # print '{0}: Set'.format(node.lineno)
        self.generic_visit(node)

    # ListComp(expr elt, comprehension* generators)
    def visit_ListComp(self, node):
        # print '{0}: List Comp'.format(node.lineno)
        self.generic_visit(node)

    # SetComp(expr elt, comprehension* generators)
    def visit_SetComp(self, node):
        # print '{0}: Set Comp'.format(node.lineno)
        self.generic_visit(node)

    # DictComp(expr key, expr value, comprehension* generators)
    def visit_DictComp(self, node):
        # print '{0}: Dict Comp'.format(node.lineno)
        self.generic_visit(node)

    # GeneratorExp(expr elt, comprehension* generators)
    def visit_GeneratorExp(self, node):
        # print '{0}: Generator Expression'.format(node.lineno)
        self.generic_visit(node)

    # Yield(expr? value)
    def visit_Yield(self, node):
        # print '{0}: Yield'.format(node.lineno)
        self.generic_visit(node)

    # Compare(expr left, cmpop* ops, expr* comparators)
    def visit_Compare(self, node):
        # print '{0}: Compare'.format(node.lineno)
        left_walker = walk_ast_for_names(node.left, self.current_scope)
        utils.add_string_to_data(node.lineno, left_walker.data,
                                 left_walker.line)
        utils.combine_data(node.lineno, self.data, left_walker.data)
        utils.combine_variable_scopes(self.variable_scope,
                                      left_walker.variable_scope)
        self.line = left_walker.line
        for op, comparator in zip(node.ops, node.comparators):
            op_walker = walk_ast_for_expr(op, self.current_scope)
            utils.combine_variable_scopes(self.variable_scope,
                                          op_walker.variable_scope)
            comparator_walker = walk_ast_for_expr(comparator,
                                                  self.current_scope)
            utils.add_string_to_data(node.lineno, comparator_walker.data,
                                     comparator_walker.line)
            utils.combine_data(node.lineno, self.data, comparator_walker.data)
            utils.combine_variable_scopes(self.variable_scope,
                                          comparator_walker.variable_scope)
            self.line += op_walker.line + comparator_walker.line

    # Call(expr func, expr* args, keyword* keywords,
    #      expr? starargs, expr? kwargs)
    def visit_Call(self, node):
        # print '{0}: Call'.format(node.lineno)
        func_walker = walk_ast_for_names(node.func, self.current_scope)
        if not isinstance(node.func, ast.Name):
            utils.combine_data(node.lineno, self.data, func_walker.data)
            utils.combine_variable_scopes(self.variable_scope,
                                          func_walker.variable_scope)
        self.line += func_walker.line + '('
        first_arg = True
        for arg in node.args:
            arg_walker = walk_ast_for_expr(arg, self.current_scope)
            utils.add_string_to_data(node.lineno, arg_walker.data,
                                     arg_walker.line)
            utils.combine_data(node.lineno, self.data, arg_walker.data)
            utils.combine_variable_scopes(self.variable_scope,
                                          arg_walker.variable_scope)
            if not first_arg:
                self.line += ','
            first_arg = False
            self.line += arg_walker.line
        self.line += ')'
        utils.add_additional_lines(self.data, node.lineno, func_walker.line)
        utils.add_string_to_data(node.lineno, self.data, self.line)

    # Repr(expr value)
    def visit_Repr(self, node):
        # print '{0}: Repr'.format(node.lineno)
        self.generic_visit(node)

    # Num(object n) -- a number as a PyObject.
    def visit_Num(self, node):
        # print '{0}: Num: {1}'.format(node.lineno, node.n)
        if self.is_bin_op:
            self.line += str(node.n)

    # Str(string s) -- need to specify raw, unicode, etc?
    def visit_Str(self, node):
        # print '{0}: String: {1}'.format(node.lineno, node.s)
        self.line += '\'' + node.s + '\''

    # Attribute(expr value, identifier attr, expr_context ctx)
    def visit_Attribute(self, node):
        # print '{0}: Attribute attr: {1}'.format(node.lineno, node.attr)
        walker = walk_ast_for_expr(node.value, self.current_scope)
        utils.combine_data(node.lineno, self.data, walker.data)
        utils.combine_variable_scopes(self.variable_scope,
                                      walker.variable_scope)
        self.line += walker.line + '.' + node.attr
        if self.line not in self.variable_scope[self.current_scope]:
            self.variable_scope[self.current_scope].append(self.line)
        utils.add_string_to_data(node.lineno, self.data, walker.line)

    # Subscript(expr value, slice slice, expr_context ctx)
    def visit_Subscript(self, node):
        # print '{0}: Subscript'.format(node.lineno)
        value_walker = walk_ast_for_names(node.value, self.current_scope)
        utils.add_string_to_data(node.lineno, value_walker.data,
                                 value_walker.line)
        utils.combine_data(node.lineno, self.data, value_walker.data)
        utils.combine_variable_scopes(self.variable_scope,
                                      value_walker.variable_scope)
        slice_walker = WalkAST(self.current_scope)
        slice_walker.lineno = node.lineno
        slice_walker.visit(node.slice)
        utils.add_string_to_data(node.lineno, slice_walker.data,
                                 slice_walker.line)
        utils.combine_data(node.lineno, self.data, slice_walker.data)
        utils.combine_variable_scopes(self.variable_scope,
                                      slice_walker.variable_scope)
        self.line = '{0}[{1}]'.format(value_walker.line, slice_walker.line)
        utils.add_string_to_data(node.lineno, self.data, self.line)

    # Name(identifier id, expr_context ctx)
    def visit_Name(self, node):
        # print '{0}: Name id: {1}'.format(node.lineno, node.id)
        if (self.is_bin_op and isinstance(node.ctx, ast.Load)) or \
                self.get_names:
            utils.add_string_to_data(node.lineno, self.data, node.id)
            self.line += node.id
        if self.current_scope not in self.variable_scope:
            self.variable_scope[self.current_scope] = []
        if (node.id not in self.variable_scope[self.current_scope] and
                node.id != 'self' and node.id != 'None'):
            self.variable_scope[self.current_scope].append(node.id)
        self.generic_visit(node)

    # List(expr* elts, expr_context ctx)
    def visit_List(self, node):
        # print '{0}: List'.format(node.lineno)
        if len(node.elts) == 0:
            utils.setup_expressions(self.data, node.lineno)
            self.line += '[]'
            utils.add_string_to_data(node.lineno, self.data, '[]')
        else:
            for e in node.elts:
                # walker = walk_ast_for_names(e)
                walker = walk_ast_for_expr(e, self.current_scope)
                utils.add_string_to_data(node.lineno, walker.data, walker.line)
                utils.combine_data(node.lineno, self.data, walker.data)
                utils.combine_variable_scopes(self.variable_scope,
                                              walker.variable_scope)
                # utils.add_string_to_data(node.lineno, self.data, self.line)
        self.generic_visit(node.ctx)
        # print self.data[node.lineno]['expressions']
        self.data[node.lineno]['type'] = 'list_assign'
        utils.remove_empty_string(self.data, node.lineno)
        # self.generic_visit(node)

    # Tuple(expr* elts, expr_context ctx)
    def visit_Tuple(self, node):
        # print '{0}: Tuple'.format(node.lineno)
        for elt in node.elts:
            walker = walk_ast_for_names(elt, self.current_scope)
            utils.add_string_to_data(node.lineno, walker.data, walker.line)
            utils.combine_data(node.lineno, self.data, walker.data)
            utils.combine_variable_scopes(self.variable_scope,
                                          walker.variable_scope)
        # self.generic_visit(node)

    #
    # expr_context
    #
    def visit_Load(self, node):
        # print 'Load'
        self.line += ''

    def visit_Store(self, node):
        # print 'Store'
        self.line += ''

    def visit_Del(self, node):
        # print 'Del'
        self.line += ''

    def visit_AugLoad(self, node):
        # print 'AugLoad'
        self.line += ''

    def visit_AugStore(self, node):
        # print 'AugStore'
        self.line += ''

    def visit_Param(self, node):
        # print 'Param'
        self.line += ''

    #
    # slice
    #

    # Ellipsis
    def visit_Ellipsis(self, node):
        pass
        # print 'Ellipsis'

    # Slice(expr? lower, expr? upper, expr? step)
    def visit_Slice(self, node):
        # print 'Slice'
        self.generic_visit(node)

    # ExtSlice(slice* dims)
    def visit_ExtSlice(self, node):
        # print 'ExtSlice'
        self.generic_visit(node)

    # Index(expr value)
    def visit_Index(self, node):
        # print 'Index'
        walker = walk_ast_for_expr(node.value, self.current_scope)
        self.line = walker.line
        utils.add_string_to_data(self.lineno, walker.data, walker.line)
        utils.combine_data(self.lineno, self.data, walker.data)
        utils.combine_variable_scopes(self.variable_scope,
                                      walker.variable_scope)

    #
    # boolop
    #
    def visit_And(self, node):
        # print 'and'
        self.line += 'and'

    def visit_Or(self, node):
        # print 'or'
        self.line += 'or'

    #
    # operator
    #
    def visit_Add(self, node):
        # print '+'
        self.line += '+'

    def visit_Sub(self, node):
        # print '-'
        self.line += '-'

    def visit_Mult(self, node):
        # print '*'
        self.line += '*'

    def visit_Div(self, node):
        # print '/'
        self.line += '/'

    def visit_Mod(self, node):
        # print '%'
        self.line += '%'

    def visit_Pow(self, node):
        # print '**'
        self.line += '**'

    def visit_LShift(self, node):
        # print '<<'
        self.line += '<<'

    def visit_RShift(self, node):
        # print '>>'
        self.line += '>>'

    def visit_BitOr(self, node):
        # print '|'
        self.line += '|'

    def visit_BitXor(self, node):
        # print '^'
        self.line += '^'

    def visit_BitAnd(self, node):
        # print '&'
        self.line += '&'

    def visit_FloorDiv(self, node):
        pass
        # print 'FLOOR DIV'

    #
    # unaryop
    #
    def visit_Invert(self, node):
        # print '~'
        self.line += '~'

    def visit_Not(self, node):
        # print 'not'
        self.line += 'not'

    def visit_UAdd(self, node):
        # print '+'
        self.line += '+'

    def visit_USub(self, node):
        # print '-'
        self.line += '-'

    #
    # cmpop
    #
    def visit_Eq(self, node):
        # print '=='
        self.line += '=='

    def visit_NotEq(self, node):
        # print '!='
        self.line += '!='

    def visit_Lt(self, node):
        # print '<'
        self.line += '<'

    def visit_LtE(self, node):
        # print '<='
        self.line += '<='

    def visit_Gt(self, node):
        # print '>'
        self.line += '>'

    def visit_GtE(self, node):
        # print '>='
        self.line += '>='

    def visit_Is(self, node):
        # print 'is'
        self.line += 'is'

    def visit_IsNot(self, node):
        # print 'is not'
        self.line += 'is not'

    def visit_In(self, node):
        # print 'in'
        self.line += 'in'

    def visit_NotIn(self, node):
        # print 'not in'
        self.line += 'not in'

    # comprehension = (expr target, expr iter, expr* ifs)
    def visit_comprehension(self, node):
        # print 'Comprehension'
        self.generic_visit(node)

    # excepthandler = ExceptHandler(expr? type, expr? name, stmt* body)
    #                           attributes (int lineno, int col_offset)
    def visit_ExceptHandler(self, node):
        # print 'ExceptHandler'
        self.generic_visit(node)

    # arguments = (expr* args, identifier? vararg,
    #              identifier? kwarg, expr* defaults)
    def visit_arguments(self, node):
        # print '{0}: Arguments'.format(self.lineno)
        if len(node.args) == 0:
            utils.setup_expressions(self.data, self.lineno)
        else:
            for arg in node.args:
                arg_walker = walk_ast_for_names(arg, self.current_scope)
                if arg_walker.line == 'self':
                    # TODO: Decide if this removal is right
                    arg_walker.data[self.lineno]['expressions'].remove('self')
                else:
                    utils.add_string_to_data(self.lineno, arg_walker.data,
                                             arg_walker.line)
                utils.combine_data(self.lineno, self.data, arg_walker.data)
                utils.combine_variable_scopes(self.variable_scope,
                                              arg_walker.variable_scope)
        # self.generic_visit(node)

    # keyword = (identifier arg, expr value)
    def visit_keyword(self, node):
        # print 'KEY_WORD'
        self.generic_visit(node)

    # alias = (identifier name, identifier? asname)
    def visit_alias(self, node):
        # print 'ALIAS'
        utils.add_string_to_data(self.lineno, self.data, node.name)
        if node.asname is not None:
            utils.add_string_to_data(self.lineno, self.data, node.asname)
        # self.generic_visit(node)


if __name__ == '__main__':
    # file = '../test_code/node_class.py'
    # file = '../test_code/test_code.py'
    file = 'user_code.py'
    # file = '../test_code/input_debug_test.py'
    with open(file, 'r') as myfile:
        source_code = myfile.read()
        myfile.close()
    tree = ast.parse(source_code)
    print ast.dump(tree)
    walker = WalkAST()
    walker.visit(tree)
    walker.print_map()
    print '\nDATA:'
    for key, value in walker.data.items():
        print '\t{0}: {1}'.format(key, value)
    print '\nVARIABLE SCOPE:'
    for key, value in walker.variable_scope.items():
        print '\t{0}: {1}'.format(key, value)
