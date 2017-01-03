import ast
import os
import signal
import sys
import time

import walk_ast


def get_expressions(file):
    with open(file, 'r') as myfile:
        source_code = myfile.read()
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
        self.input_field = None
        self.input_event = None
        self.user_inputs = None
        self.user_inputs_index = 0
        self.data = None
        self.variable_scope = None
        self.additional_lines_call_point = {}
        self.looking_for = []

    def communicate(self, fd_write, fd_read, file, input_field=None,
            input_event=None, user_inputs=None):
        self.fd_write = fd_write
        self.fd_read = fd_read
        self.input_field = input_field
        self.input_event = input_event
        self.user_inputs = user_inputs
        self.data, self.variable_scope = get_expressions(file)
        lineno = 0
        while lineno >= 0:
            output = os.read(self.fd_read, 1000)
            lineno = self.parse_line(output)
            if lineno in self.data:
                self.evaluate_line(self.data, lineno)
            if lineno == -2:
                lineno = 0
            self.executed_lines.append(lineno)
            os.write(self.fd_write, 's\n')
            if self.call > 1000:  # Terminate on long loops
                return

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
            if self.input_field is None:
                print "ERROR!!! BREAK"
                user_input = '10'
            else:
                if (len(self.user_inputs) > 0 and
                        self.user_inputs_index < len(self.user_inputs)):
                    user_input = self.user_inputs[self.user_inputs_index]
                    self.user_inputs_index += 1
                else:
                    self.input_event.wait()
                    user_input = self.input_field.get()
                    self.user_inputs.append(user_input)
                    self.input_field.delete(0, len(user_input))
                    self.user_inputs_index += 1
                    self.input_event.clear()
            os.write(self.fd_write, str(user_input) + '\n')
            while '--Return--' not in os.read(self.fd_read, 1000):
                os.write(self.fd_write, 's\n')
            result = str(user_input)
            self.setup_executed_code(lineno)
        else:
            result = self.evaluate_expressions(data, lineno)
        assigned = None
        for a in data[lineno]['assigned']:
            if assigned is None:
                assigned = a
            else:
                assigned += ',' + a
        if result is not None:
            # print assigned + '=' + result
            self.executed_code[self.call]['result'] = assigned + '=' + result
        self.executed_code[self.call]['assigned'] = True
        self.call += 1

    def evaluate_class(self, data, lineno):
        result = self.evaluate_expressions(data, lineno)
        self.executed_code[self.call]['result'] = result
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
            for func in data[lineno]['additional_lines']:
                if func in data['function_lines']:
                    # print '\t\t\tTEST: {0}:{1} from {2}'.format(lineno, data['function_lines'][func], func)
                    self.looking_for.append((lineno, data['function_lines'][func][:]))
        return final_expression

    def evaluate_and_store_expressions(self, data, lineno):
        self.add_call_point(lineno)
        result = ''
        if 'expressions' in data[lineno]:
            self.setup_executed_code(lineno)
            result = self.evaluate(data[lineno]['expressions'], True)
        print '\t\t{0}'.format(result)
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
            self.executed_code[self.call]['values'][item] = result
            if add_all:
                if '\n(Pdb) ' in result:
                    result = result.rstrip('\n(Pdb) ')
                if final_expression is None:
                    final_expression = result
                else:
                    final_expression += ',' + result
            else:
                final_expression = result
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


def main(file, input_field=None, input_event=None, user_inputs=None):
    communicator_read, communicator_write = os.pipe()
    debugger_read, debugger_write = os.pipe()
    pid = os.fork()
    if pid:  # Parent
        os.close(communicator_read)
        os.close(debugger_write)
        communicator = Communicator()
        communicator.communicate(communicator_write, debugger_read, file,
                                 input_field, input_event, user_inputs)
    else:  # Child
        os.close(debugger_read)
        os.close(communicator_write)
        launch_child(debugger_write, communicator_read, file)
    os.kill(pid, signal.SIGKILL)
    # print communicator.executed_lines
    # print communicator.executed_code
    for key, value in communicator.executed_code.iteritems():
        # print '{0}: Lineno: {1}'.format(key, value['lineno'])
        if 'result' in value:
            value['result'] = value['result'].rstrip('\n(Pdb) ')
            # print 'Result: {0}'.format(value['result'])
        # print 'Values:'
        for k, v in value['values'].iteritems():
            v = v.rstrip('\n(Pdb) ')
            value['values'][k] = v
            # print '\t{0}: {1}'.format(k, v)
    return communicator

if __name__ == '__main__':
    main('../test_code/code.py')
    # main('user_code.py')
    # main('../test_code/input_debug_test.py')
