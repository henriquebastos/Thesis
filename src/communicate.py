import ast
import os
import signal
import sys
import time

import walk_ast


def get_expressions(file):
    with open(file, 'r') as myfile:
        source_code = myfile.read()
        myfile.close()
    tree = ast.parse(source_code)
    # print ast.dump(tree)
    walker = walk_ast.WalkAST()
    walker.visit(tree)
    walker.print_map()
    walker.remove_empty_expressions()
    return walker.data, walker.variable_scope


def has_user_input_call(data, lineno):
    for expr in data[lineno]['expressions']:
        if 'input(' in expr or 'raw_input(' in expr:
            return True
    return False


class Communicator(object):
    def __init__(self):
        self.call = 0
        self.should_execute_previous = False
        self.executed_code = {}
        self.executed_lines = []
        self.fd_write = None
        self.fd_read = None
        self.stop_event = None
        self.input_event = None
        self.user_inputs = None
        self.user_inputs_index = 0
        self.data = None
        self.variable_scope = None
        self.variable_values = {}
        self.additional_lines_call_point = {}
        self.looking_for = []

    def communicate(self, fd_write, fd_read, fd_write_2, fd_read_2, file, stop_event=None,
                    input_event=None, user_inputs=None, pid=None, pid2=None):
        self.fd_write = fd_write
        self.fd_read = fd_read
        self.fd_write_2 = fd_write_2
        self.fd_read_2 = fd_read_2
        self.stop_event = stop_event
        self.input_event = input_event
        self.user_inputs = user_inputs
        self.data, self.variable_scope = get_expressions(file)
        lineno = 0

        while lineno >= 0:
            output = os.read(self.fd_read, 1000)
            output2 = os.read(fd_read_2, 1000)
            lineno = self.parse_line(output)
            self.evaluate_variable_values(lineno)
            if lineno in self.data:
                self.evaluate_line(self.data, lineno)
            if lineno == -2:
                lineno = 0
            self.executed_lines.append(lineno)
            os.write(self.fd_write, 's\n')
            os.write(fd_write_2, 's\n')
            # Terminate on long loops
            if self.call > 1000 or self.stop_event.isSet():
                os.kill(pid, signal.SIGUSR1)
                os.kill(pid2, signal.SIGUSR1)
                return
        os.kill(pid, signal.SIGUSR1)
        os.kill(pid2, signal.SIGUSR1)

    def in_correct_scope(self, scope, lineno):
        if scope == 'global' and 'function_lines' in self.data:
            for func,lines in self.data['function_lines'].iteritems():
                if lineno in lines:
                    return False
            return True
        return ('function_lines' in self.data and
            scope in self.data['function_lines'] and
            lineno in self.data['function_lines'][scope])

    def evaluate_variable_values(self, lineno):
        for scope, variables in self.variable_scope.iteritems():
            if self.in_correct_scope(scope, lineno):
                for variable in variables:
                    os.write(self.fd_write_2, 'p {0}\n'.format(variable))
                    result = os.read(self.fd_read_2, 1000)
                    result = result.rstrip('\n(Pdb) ')
                    if self.call > 0 and '*** NameError' not in result and '<built-in method' not in result:
                        if self.call-1 not in self.variable_values:
                            self.variable_values[self.call-1] = {}
                        if scope not in self.variable_values[self.call-1]:
                            self.variable_values[self.call-1][scope] = {}
                        self.variable_values[self.call-1][scope][variable] = result

    def parse_line(self, line):
        lineno = -1
        marked = False
        try:
            if '--Return--' in line:
                marked = True
            lineno = line.split('.py(')[1].split(')')[0]
        except:
            lineno = -1
        if marked and lineno >= 0:
            lineno = -2
        return int(lineno)

    def evaluate_line(self, data, lineno):
        if ('type' in data[lineno] and data[lineno]['type'] == 'func' and
                'declared' not in data[lineno]):
            data[lineno]['declared'] = True
        else:
            if self.should_execute_previous:
                previous_lineno = self.executed_lines[
                    len(self.executed_lines)-1]
                if previous_lineno in data:
                    if data[previous_lineno]['type'] == 'loop':
                        self.evaluate_loop_after(data, previous_lineno)
                    else:
                        self.should_execute_previous = False
                        self.call += 1
                        self.evaluate_expressions(data, previous_lineno)
            if 'type' in data[lineno]:
                if data[lineno]['type'] == 'assign':
                    self.evaluate_assign(data, lineno)
                elif data[lineno]['type'] == 'class':
                    self.evaluate_class(data, lineno)
                elif data[lineno]['type'] == 'conditional':
                    self.evaluate_cond(data, lineno)
                elif data[lineno]['type'] == 'delete':
                    self.evaluate_delete(data, lineno)
                elif data[lineno]['type'] == 'func':
                    self.evaluate_func(data, lineno)
                elif data[lineno]['type'] == 'list_assign':
                    self.evaluate_list_assign(data, lineno)
                elif data[lineno]['type'] == 'loop':
                    self.evaluate_loop(data, lineno)
                elif data[lineno]['type'] == 'print':
                    self.evaluate_print(data, lineno)
                elif data[lineno]['type'] == 'return':
                    self.evaluate_return(data, lineno)
            else:
                result = self.evaluate_expressions(data, lineno)
                self.executed_code[self.call]['result'] = result
                self.call += 1

    def evaluate_assign(self, data, lineno):
        if has_user_input_call(data, lineno):
            os.write(self.fd_write, 's\n')
            os.write(self.fd_write_2, 's\n')
            if (len(self.user_inputs) > 0 and
                    self.user_inputs_index < len(self.user_inputs)):
                user_input = self.user_inputs[self.user_inputs_index]
                self.user_inputs_index += 1
            else:
                self.input_event.wait()
                self.user_inputs_index = len(self.user_inputs) - 1  # Maybe Delete
                user_input = self.user_inputs[self.user_inputs_index]
                self.user_inputs_index += 1
                self.input_event.clear()
            if self.stop_event.isSet():
                return
            os.write(self.fd_write, str(user_input) + '\n')
            while '--Return--' not in os.read(self.fd_read, 1000):
                os.write(self.fd_write, 's\n')
            os.write(self.fd_write_2, str(user_input) + '\n')
            while '--Return--' not in os.read(self.fd_read_2, 1000):
                os.write(self.fd_write_2, 's\n')
            result = str(user_input)
            self.setup_executed_code(lineno)
        else:
            result = self.evaluate_expressions(data, lineno)
            self.evaluate_assigned_expressions(data, lineno)
        assigned = None
        for a in data[lineno]['assigned']:
            if assigned is None:
                assigned = a
            else:
                assigned += ',' + a
        if result is not None:
            self.executed_code[self.call]['result'] = assigned + '=' + result
        self.executed_code[self.call]['assigned'] = True
        self.call += 1

    def evaluate_class(self, data, lineno):
        result = self.evaluate_expressions(data, lineno)
        # self.executed_code[self.call]['result'] = result
        self.call += 1

    def evaluate_cond(self, data, lineno):
        result = self.evaluate_expressions(data, lineno)
        self.executed_code[self.call]['result'] = result
        self.call += 1

    def evaluate_delete(self, data, lineno):
        print 'TODO'

    def evaluate_func(self, data, lineno):
        result = self.evaluate_expressions(data, lineno)
        self.call += 1

    def evaluate_list_assign(self, data, lineno):
        result = self.evaluate_and_store_expressions(data, lineno)
        assigned = None
        for a in data[lineno]['assigned']:
            if assigned is None:
                assigned = a
            else:
                assigned += ',' + a
        if result is not None:
            self.executed_code[self.call]['result'] = assigned + '=' + result
        self.executed_code[self.call]['assigned'] = True
        self.call += 1

    def evaluate_loop(self, data, lineno):
        result = self.evaluate_expressions(data, lineno)
        self.executed_code[self.call]['result'] = result
        self.should_execute_previous = True
        self.previous_type = 'loop'

    def evaluate_loop_after(self, data, lineno):
        result = self.evaluate_targets(data, lineno)
        if result is not None:
            self.executed_code[self.call]['result'] = result
        self.should_execute_previous = False
        self.call += 1

    def evaluate_print(self, data, lineno):
        result = self.evaluate_expressions(data, lineno)
        self.executed_code[self.call]['result'] = result
        self.executed_code[self.call]['print'] = True
        self.call += 1

    def evaluate_return(self, data, lineno):
        result = self.evaluate_expressions(data, lineno)
        self.executed_code[self.call]['result'] = result
        self.call += 1

    def setup_executed_code(self, lineno):
        if self.call not in self.executed_code:
            self.executed_code[self.call] = {}
            self.executed_code[self.call]['lineno'] = lineno
            self.executed_code[self.call]['values'] = {}

    def evaluate_expressions(self, data, lineno):
        self.add_call_point(lineno)
        final_expression = None
        if 'expressions' in data[lineno]:
            self.setup_executed_code(lineno)
            final_expression = self.evaluate(data[lineno]['expressions'],
                                             False)
        if 'additional_lines' in data[lineno]:
            self.additional_lines_call_point[lineno] = {}
            for name in data[lineno]['additional_lines']:
                if '.' in name:
                    name = name.split('.')[-1]
                if 'function_lines' in data and name in data['function_lines']:
                    self.looking_for.append(
                        (lineno, data['function_lines'][name][:]))
                elif ('classes' in data and name in data['classes'] and 
                        '__init__' in data['classes'][name]['functions']):
                    self.looking_for.append(
                        (lineno, data['classes'][name]['functions']['__init__'][:]))
        return final_expression

    def evaluate_assigned_expressions(self, data, lineno):
        if 'assigned_expressions' in data[lineno]:
            for assigned,expressions in data[lineno]['assigned_expressions'].iteritems():
                for expression in expressions:
                    if assigned != expression:
                        os.write(self.fd_write, 'p {0}\n'.format(expression))
                        result = os.read(self.fd_read, 1000)
                        if 'assigned_values' not in self.executed_code[self.call]:
                            self.executed_code[self.call]['assigned_values'] = {}
                        self.executed_code[self.call]['assigned_values'][expression] = result

    def evaluate_and_store_expressions(self, data, lineno):
        self.add_call_point(lineno)
        result = ''
        if 'expressions' in data[lineno]:
            self.setup_executed_code(lineno)
            result = self.evaluate(data[lineno]['expressions'], True)
        if result == '\'[]\'' or result == '[]':
            return '[]'
        return '[' + result + ']'

    def evaluate_targets(self, data, lineno):
        if 'targets' in data[lineno]:
            self.setup_executed_code(lineno)
            self.evaluate(data[lineno]['targets'], True)

    def evaluate(self, items, add_all):
        final_expression = None
        for item in items:
            os.write(self.fd_write, 'p {0}\n'.format(item))
            result = os.read(self.fd_read, 1000)
            result = result.rstrip('\n(Pdb) ')
            self.executed_code[self.call]['values'][item] = result
            if add_all:
                if '\n(Pdb) ' in result:
                    result = result.rstrip('\n(Pdb) ')
                    result = result[1:-1]
                if final_expression is None:
                    final_expression = result
                else:
                    final_expression += ',' + result
            else:
                final_expression = result
            if '\n(Pdb) ' in final_expression:
                final_expression = final_expression.rstrip('\n(Pdb) ')[1:-1]
        return final_expression

    def add_call_point(self, lineno):
        for t in self.looking_for:
            if lineno in t[1]:
                self.additional_lines_call_point[t[0]][lineno] = self.call
                t[1].remove(lineno)


def launch_child(fd_write, fd_read, file):
    os.dup2(fd_read, sys.stdin.fileno())
    os.dup2(fd_write, sys.stdout.fileno())
    os.execlp('python', 'Debugger', 'pdb.py', file)


def main(file, stop_event=None, input_event=None, user_inputs=None):
    communicator_read, communicator_write = os.pipe()
    debugger_read, debugger_write = os.pipe()
    pid = os.fork()
    if pid:  # Parent
        os.close(communicator_read)
        os.close(debugger_write)

        communicator_read_2, communicator_write_2 = os.pipe()
        debugger_read_2, debugger_write_2 = os.pipe()
        pid2 = os.fork()
        if pid2:
            os.close(communicator_read_2)
            os.close(debugger_write_2)

            communicator = Communicator()
            communicator.communicate(communicator_write, debugger_read, communicator_write_2, debugger_read_2, file,
                                     stop_event, input_event, user_inputs, pid, pid2)
        else:
            os.close(debugger_read)
            os.close(communicator_write)
            os.close(debugger_read_2)
            os.close(communicator_write_2)
            launch_child(debugger_write_2, communicator_read_2, file)
        os.close(communicator_write_2)
        os.close(debugger_read_2)
        os.kill(pid2, signal.SIGKILL)
    else:  # Child
        os.close(debugger_read)
        os.close(communicator_write)
        launch_child(debugger_write, communicator_read, file)
    os.close(communicator_write)
    os.close(debugger_read)
    os.kill(pid, signal.SIGKILL)

    # TODO remove this and make it part of os.read()
    # May already be done.
    for key, value in communicator.executed_code.iteritems():
        if 'result' in value:
            value['result'] = value['result'].rstrip('\n(Pdb) ')
        for k, v in value['values'].iteritems():
            v = v.rstrip('\n(Pdb) ')
            value['values'][k] = v
    return communicator

if __name__ == '__main__':
    # main('../test_code/node_class.py')
    # main('../test_code/code.py')
    main('user_code.py')
    # main('../test_code/input_debug_test.py')
