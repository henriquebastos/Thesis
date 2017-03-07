from Tkinter import *
from tkinter import ttk
from tkMessageBox import showinfo
import tkFileDialog
import os
import ScrolledText as ST
import threading
import time

from pygments import lex
from pygments.lexers import PythonLexer

import communicate as Communicate
import generic_object as GenericObject
import treeview
from treeview_wrappers import TreeWrapper, TreeViewer

# RENAME to Environment

name = 'Live Programming Environment'
root = Tk(screenName=name, baseName=name, className=name)
user_code = ''
user_inputs = []
FILE_NAME = 'user_code.py'
INPUT_FILE_NAME = 'user_input.txt'
scale_size = 0
prev_scale_setting = 0
prev_start_scale_setting = 0
executed_code = None
data = None
variable_scope = None
variable_values = {}
variable_values_per_line = {}
communicationThread = None
input_event = threading.Event()
rerun_event = threading.Event()
exit_event = threading.Event()
additional_lines_call_point = None
successful_exit = True
scroll_position = None

generic_objects = {}
current_object_lines = []
current_generic_object = None
current_function = None
selected_object = StringVar()
root_objects = None

DO_NOT_RUN = False
display_map = {}


def get_function_call_lineno(call, lineno):
    for line, values in additional_lines_call_point.iteritems():
        for additional_line, additional_calls in values.iteritems():
            if lineno == additional_line and call in additional_calls:
                return line


def variable_declared_in_scope(variable, function, function_lines):
    if function == 'global':
        return True
    else:
        for line in function_lines:
            if ('type' in data[line] and ('func' == data[line]['type'] or
                    ('assign' == data[line]['type'] and
                    variable in data[line]['assigned']))):
                return True
    return False


def get_function_call_points(lineno):
    call_points = {}
    for line, func_calls in additional_lines_call_point.iteritems():
        if lineno in func_calls:
            call_points[line] = additional_lines_call_point[line][lineno]
    return call_points


def get_loop_iteration_calls(lineno, lines):
    calls = []
    count = 0
    for call, info in executed_code.iteritems():
        if info['lineno'] in lines:
            calls.append(call)
        if info['lineno'] == lineno:
            count += 1
    return calls, count


def display_variables(variable_box, call_num):
    global variable_scope
    global variable_values

    # print '\n\n\n\nVariable Values: '
    # for k,v in variable_values.items():
    #     print '\t{0}: {1}'.format(k,v)
    # print 'Variable Scope:'
    # for k,v in variable_scope.items():
    #     print '\t{0}: {1}'.format(k,v)
    # print 'Executed Code:'
    # for k,v in executed_code.items():
    #     print '\t{0}: {1}'.format(k,v)
    # print 'DATA: '
    # for k,v in data.items():
    #     print '\t{0}: {1}'.format(k,v)
    # print 'Generic Objects:'
    # for k,v in generic_objects.items():
    #     print '\t{0}: {1}'.format(k,v)
    # print 'Variable Values Per Line:'
    # for k,v in variable_values_per_line.items():
    #     print '\t{0}: {1}'.format(k,v)
    # print 'Additional Lines Call Point:'
    # for k,v in additional_lines_call_point.items():
    #     print '\t{0}: {1}'.format(k,v)
    variable_box.config(state=NORMAL)
    variable_box.delete(0.0, END)
    for func, variables in variable_scope.items():
        func_lines = None
        if 'function_lines' in data and func in data['function_lines']:
            func_lines = data['function_lines'][func]
        variables_line = ''
        for variable in variables:
            if variable_declared_in_scope(variable, func, func_lines):
                if (call_num in variable_values_per_line and
                        func in variable_values_per_line[call_num] and
                        variable in variable_values_per_line[call_num][func] and
                        variable_values_per_line[call_num][func][variable] is not None):
                    result = variable_values_per_line[call_num][func][variable]
                    if 'instance' in result and '.' in result:
                        variables_line += '{0}={1}\n'.format(
                            variable, variable_values[func][variable])
                    else:
                        variables_line += '{0}={1}\n'.format(
                            variable, result)
                        if func not in variable_values:
                            variable_values[func] = {}
                        variable_values[func][variable] = result
                elif (func in variable_values and 
                        variable in variable_values[func]):
                    variables_line += '{0}={1}\n'.format(
                        variable, variable_values[func][variable])
        if variables_line != '':
            variable_box.insert(INSERT, '{0}:\n'.format(func), 'BOLD')
            variable_box.insert(INSERT, variables_line)
            variable_box.insert(INSERT, '\n')
    variable_box.config(state=DISABLED)


def get_scope(lineno):
    global data
    if 'function_lines' in data and 'name' in data[lineno]:
        return data[lineno]['name']
        # for func, lines in data['function_lines'].items():
        #     for line in lines:
        #         if lineno == line:
        #             return func
    return 'global'


def set_variable_value(scope, variable, result, call_num):
    global variable_values
    if scope not in variable_values:
        variable_values[scope] = {}
    if 'instance' in result and '.' in result:
        class_name = result.split(' instance')[0].split('.')[1]
        instance_id = result.split(' instance at ')[1].split('>')[0]
        obj = get_object(instance_id)
        variable_values[scope][variable] = '{0}_{1}'.format(class_name, obj.simple_id)
    else:
        variable_values[scope][variable] = result


def get_object(instance_id):
    if instance_id in generic_objects:
        return generic_objects[instance_id]
    return None


def remove_object_name(name):
    for k,v in generic_objects.iteritems():
        if name in v.name:
            v.name.remove(name) 


def check_for_new_object(scope, variable, result):
    global current_generic_object
    global current_object_lines
    if 'instance' in result and '.' in result:
        class_name = result.split(' instance')[0].split('.')[1]
        instance_id = result.split(' instance at ')[1].split('>')[0]
        obj = get_object(instance_id)
        remove_object_name(variable)
        if obj is not None:
            remove_object_name(variable)
            obj.name.append(variable)
        elif class_name in data['classes']:
            generic_object = GenericObject.GenericObject(class_name, variable,
                                                         instance_id, len(generic_objects))
            if 'functions' in data['classes'][class_name] and \
                    '__init__' in data['classes'][class_name]['functions']:
                current_generic_object = generic_object
                current_object_lines = data['classes'][class_name]['functions']['__init__']
            generic_objects[instance_id] = generic_object
            return True
    return False


def check_add_to_object(scope, variable, result, lineno):
    global current_object_lines
    global current_generic_object
    global current_function

    if lineno in current_object_lines:
        if 'self.' in variable:
            if 'instance at' in result and '.' in result:
                class_name = result.split('=')[1].split(' instance')[0].split('.')[1]
                instance_id = result.split(' instance at ')[1].split('>')[0]
                obj = get_object(instance_id)
                simple_id = obj.simple_id
                current_generic_object.add_variable(variable, result, class_name, simple_id)
            else:
                current_generic_object.add_variable(variable, result)
        elif current_function is not None:
            current_generic_object.add_function_variable(current_function, variable, result)
    else:
        current_generic_object = None
        current_function = None
        current_object_lines = []
        if '.' in variable:
            name = variable.split('.')[0]
            for v in variable.split('.')[1:-1]:
                name += '.' + v
            obj = get_object_from_name(name)
            if obj is not None:
                if 'instance at' in result and '.' in result:
                    class_name = result.split('=')[1].split(' instance')[0].split('.')[1]
                    instance_id = result.split(' instance at ')[1].split('>')[0]
                    added_obj = get_object(instance_id)
                    simple_id = added_obj.simple_id
                    obj.add_variable(variable, result, class_name, simple_id)
                else:
                    obj.add_variable(variable, result)


def get_object_from_name(name):
    for k,v in generic_objects.iteritems():
        if name in v.name:
            return v
    return None


def check_modify_object(variable, result, lineno):
    if '.' in variable:
        main_object = get_object_from_name(variable.split('.')[0])
        if main_object is not None:
            for v in variable.split('.')[1:-1]:
                instance_id = main_object.get_variable(v)
                if 'instance' in instance_id and '.' in instance_id:
                    instance_id = instance_id.split(' instance at ')[1].split('>')[0]
                    main_object = get_object(instance_id)
            
            new_variable = variable.split('.')[-1]
            if 'instance at' in result and '.' in result:
                class_name = result.split('=')[1].split(' instance')[0].split('.')[1]
                instance_id = result.split(' instance at ')[1].split('>')[0]
                obj = get_object(instance_id)
                simple_id = obj.simple_id
                main_object.add_variable(new_variable, result, class_name, simple_id)
            else:
                main_object.add_variable(new_variable, result)


def check_function_variables_arguments(lineno, values):
    if lineno in current_object_lines:
        for k,v in values.iteritems():
            if current_generic_object is not None and current_function is not None:
                current_generic_object.add_function_variable(current_function, k, v)


def handle_assignment_in_executed_code(value, call_num):
    scope = get_scope(value['lineno'])
    # print 'HANDLE ASSIGNMENT: {0}'.format(scope)
    variable = value['result'].split('=')[0]
    if '=' in value['result']:
        result = value['result'].split('=')[1]
    else:
        result = ''
    if not check_for_new_object(scope, variable, result):
        check_add_to_object(scope, variable, value['result'],
                            value['lineno'])
    else:
        check_modify_object(variable, value['result'], value['lineno'])
    set_variable_value(scope, variable, result, call_num)


def handle_additional_lines_in_executed_code(value):
    global current_generic_object
    global current_object_lines
    global current_function
    additional_lines = data[value['lineno']]['additional_lines']
    #  check if it is an object call with a .
    for additional_line in additional_lines:
        if '.' in additional_line:
            split_value = additional_line.split('.')
            seeking_variable = ''
            for v in split_value[:-1]:
                seeking_variable += v + '.'
            seeking_variable = seeking_variable.rstrip('.')
            seeking_function = split_value[-1]
            # GET LATEST OBJECT FROM VALUES 
            # Objects instance ID
            obj = value['values'][seeking_variable]
            if 'instance' in obj and '.' in obj:
                seeking_object_instance_id = obj.split(' instance at ')[1].split('>')[0]
                if seeking_object_instance_id in generic_objects:
                    obj = generic_objects[seeking_object_instance_id]
                    if seeking_function in data['function_lines']:
                        obj.add_function(seeking_function)
                        current_generic_object = obj
                        current_object_lines = data['function_lines'][seeking_function]
                        current_function = seeking_function


def get_display_line_in_executed_code(value):
    result = ''
    if 'instance at' in value['result'] and '.' in value['result']:
        try:
            variable = value['result'].split('=')[0]
            result = value['result'].split('=')[1]
            class_name = result.split(' instance')[0].split('.')[1]
            instance_id = result.split(' instance at ')[1].split('>')[0]
            obj = get_object(instance_id)
            return '{1}_{2}'.format(variable, class_name, obj.simple_id)
        except:
            if '=' in value['result']:
                result = value['result'].split('=')[1]
            else:
                result = value['result']
    else:
        if '=' in value['result']:
            result = value['result'].split('=')[1]
        else:
            result = value['result']
    return result


def handle_functions_in_executed_code(value, call_num):
    display_line = ''
    no_comma = True
    scope = get_scope(value['lineno'])
    for k, v in value['values'].iteritems():
        if no_comma:
            no_comma = False
        else:
            display_line += ', '
        display_line += '{0}={1}'.format(k, v)
        set_variable_value(scope, k, v, call_num)
    check_function_variables_arguments(value['lineno'], value['values'])
    return display_line


def display_executed_code(executed_code, code_box,
                          variable_box, output_box, start, total):
    global display_map
    display_map = {}
    for key, value in executed_code.iteritems():
        display_line = ''
        if total >= 0 and start <= 0:
            if 'result' in value:
                if 'assigned' in value:
                    handle_assignment_in_executed_code(value, key)
                if 'print' in value:
                    output_box.config(state=NORMAL)
                    output_box.insert(INSERT, value['result'] + '\n')
                    output_box.config(state=DISABLED)
                if (value['lineno'] in data and
                        'additional_lines' in data[value['lineno']]):
                    handle_additional_lines_in_executed_code(value)
                display_line += get_display_line_in_executed_code(value)
            else:
                display_line = handle_functions_in_executed_code(value, key)
            display_variables(variable_box, key)
            display_map[key] = display_line
        total -= 1
        start -= 1


def get_classes():
    classes = []
    if data is not None and 'classes' in data:
        classes = data['classes'].keys()
    return classes


def get_functions():
    functions = []
    if data is not None and 'function_lines' in data:
        functions = data['function_lines'].keys()
    return functions


def display_tree(event, combobox, tree_viewer):
    for obj in root_objects:
        if selected_object.get() in obj.generic_object.name:
            tree_viewer.clearTree()
            obj.view()
    combobox.selection_clear()


def display_objects(tree_wrapper, tree_viewer, combobox):
    global root_objects
    tree_wrapper.generic_objects = generic_objects
    tree_wrapper.classes = get_classes()
    trees = []
    root_objects_names = []
    root_objects = []

    for obj in generic_objects.values():
        tree = treeview.GenericTree(tree_viewer, obj)
        trees.append(tree)
        name = obj.get_name()
        if name is not None:
            root_objects.append(tree)
            root_objects_names.append(name)
    combobox['values'] = tuple(root_objects_names)


def reset_boxes(variable_box, output_box):
    global variable_values
    variable_box.config(state=NORMAL)
    variable_box.delete(0.0, END)
    variable_box.config(state=DISABLED)
    output_box.config(state=NORMAL)
    output_box.delete(0.0, END)
    output_box.config(state=DISABLED)
    variable_values = {}


def reset_objects():
    global generic_objects
    global current_object_lines
    global current_generic_object
    global current_function
    generic_objects = {}
    current_object_lines = []
    current_generic_object = None
    current_function = None


def highlight_code(code_box):
    code_box.mark_set('range_start', '1.0')
    data = code_box.get('1.0', 'end-1c')
    is_def = False
    for token, content in lex(data, PythonLexer()):
        if content == 'def' and str(token) == 'Token.Keyword':
            is_def = True
        elif content == ')' and str(token) == 'Token.Punctuation':
            is_def = False
                
        code_box.mark_set('range_end', 'range_start + %dc' % len(content))
        if content == 'None':
            # purple
            code_box.tag_remove('Token.Literal.Number.Integer', 'range_start', 'range_end')
            code_box.tag_add('Token.Literal.Number.Integer', 'range_start', 'range_end')
        elif ((content == '__init__' and str(token) == 'Token.Name.Function') or
                (content in get_classes() and str(token) == 'Token.Name') or
                ((content == 'class' or content == 'def') and str(token) == 'Token.Keyword')):
            # blue
            code_box.tag_remove('Token.Name.Builtin', 'range_start', 'range_end')
            code_box.tag_add('Token.Name.Builtin', 'range_start', 'range_end')
        elif is_def and str(token) == 'Token.Name':
            # orange
            code_box.tag_remove('Token.Name.Builtin.Pseudo', 'range_start', 'range_end')
            code_box.tag_add('Token.Name.Builtin.Pseudo', 'range_start', 'range_end')
        elif str(token) == 'Token.Name' and (content in get_classes() or
                content in get_functions()):
            code_box.tag_remove('Token.Name.Builtin', 'range_start', 'range_end')
            code_box.tag_add('Token.Name.Builtin', 'range_start', 'range_end')
        elif str(token) == 'Token.Operator' and content == '.':
            pass
        else:
            code_box.tag_remove(str(token), 'range_start', 'range_end')
            code_box.tag_add(str(token), 'range_start', 'range_end')
        code_box.mark_set('range_start', 'range_end')


def tag_add_highlight(widget, line, call, start, length):
    global DO_NOT_RUN
    if communicationThread is None:
        DO_NOT_RUN = True
        widget.tag_remove('HIGHLIGHT', '{0}.{1}'.format(line, start),
                          '{0}.{1}'.format(line, length))
        widget.tag_add('HIGHLIGHT', '{0}.{1}'.format(line, start),
                       '{0}.{1}'.format(line, length))
        if call in display_map:
            widget.insert('{0}.{1}'.format(line, length), '     {0}'.format(display_map[call].lstrip(' ')))


def tag_remove_highlight(widget, line, call, start, length):
    global DO_NOT_RUN
    if communicationThread is None:
        widget.config(state=NORMAL)
        widget.tag_remove('HIGHLIGHT', '{0}.{1}'.format(line, start),
                          '{0}.{1}'.format(line, length))
        widget.delete('{0}.{1}'.format(line, length), '{0}.end'.format(line))
        DO_NOT_RUN = False


def optional_add_highlights(widget, lineno, call, line_start, line_length,
                            lines=None):
    if lines is not None:
        for line in lines:
            end = len(user_code.split('\n')[line-1])
            call += 1
            tag_add_highlight(widget, line, call, 0, end)

def optional_remove_highlights(widget, lineno, call, line_start, line_length,
                               lines=None):
    if lines is not None:
        for line in lines:
            end = len(user_code.split('\n')[line-1])
            tag_remove_highlight(widget, line, call, 0, end)


def add_highlight(event, widget, lineno, call, line_start, line_length,
                  lines=None):
    tag_add_highlight(widget, lineno, call, line_start, line_length)
    if lines is not None:
        optional_add_highlights(widget, lineno, call, line_start, line_length,
                                lines)
        widget.config(state=DISABLED)
    else:
        widget.config(state=DISABLED)


def remove_highlight(event, widget, lineno, call, line_start, line_length,
                     lines=None):
    tag_remove_highlight(widget, lineno, call, line_start, line_length)
    if lines is not None:
        optional_remove_highlights(widget, lineno, call, line_start, line_length,
                                   lines)


def display_func_output(event, executed_box, func_lineno, func_lines, selected_call):
    executed_box.config(state=NORMAL)
    executed_box.delete(0.0, END)
    selected_line = selected_call.get()
    if 'Call: ' in selected_line:
        selected_line = selected_line.lstrip('Call: ')
        index = int(selected_line.split(' @ ')[0]) - 1
        calling_lineno = selected_line.split(' @ ')[1].lstrip('Line: ')

    else:
        index = 0
        calling_lineno = selected_line.lstrip('Line: ')
    if ',' in calling_lineno:
        calling_lineno = calling_lineno.split(',')[0]
    calling_lineno = int(calling_lineno)
    # Get the code for those lines
    executed_output = ''
    for line in func_lines:
        # Get executed_code
        call_no = additional_lines_call_point[calling_lineno][line][index]
        executed_line = None
        if 'result' in executed_code[call_no]:
            if 'instance' in executed_code[call_no]['result'] and '.' in executed_code[call_no]['result']:
                variable = executed_code[call_no]['result'].split('=')[0]
                value = executed_code[call_no]['result'].split('=')[1]
                class_name = value.split(' instance')[0].split('.')[1]
                instance_id = value.split(' instance at ')[1].split('>')[0]
                obj = get_object(instance_id)
                value = '{0}_{1}'.format(class_name, obj.simple_id)
                executed_line = '{0}={1}'.format(variable, value)
            else:
                executed_line = executed_code[call_no]['result']
        else:
            for variable, value in executed_code[call_no]['values'].iteritems():
                if 'instance' in value and '.' in value:
                    class_name = value.split(' instance')[0].split('.')[1]
                    instance_id = value.split(' instance at ')[1].split('>')[0]
                    obj = get_object(instance_id)
                    value = '{0}_{1}'.format(class_name, obj.simple_id)
                if executed_line is None:
                    executed_line = '{0}={1}'.format(variable, value)
                else:
                    executed_line += ',{0}={1}'.format(variable, value)
        executed_output += '{0}\n'.format(executed_line)
    executed_box.insert(INSERT, executed_output)
    executed_box.config(state=DISABLED)


# TODO
def set_var_to_type(v):
    if v == 'None':
        return None
    elif v == 'True':
        return True
    elif v == 'False':
        return False
    elif '[' in v and ']' in v:
        r = []
        v = v[1:-1]
        for t in v.split(','):
            r.append(set_var_to_type(t))
        return r
    else:
        try:
            return int(v)
        except:
            return v


def test_class_call(toplevel, executed_box, code, class_lineno, class_lines,
                    labels, entries):
    executed_box.config(state=NORMAL)
    executed_box.delete(0.0, END)
    variables = []
    bad_input = False
    offset = 0
    index = 0
    line_length = len(code.split('\n'))
    used_labels = []
    for (l, e) in zip(labels, entries):
        l_text = l.cget('text').rstrip(':')
        if e.get() == '':
            bad_input = True
            executed_box.insert(INSERT, 'Variable {0}: Invalid Input.\n'.format(l_text))
        elif e.get() != '__NULL__':
            e_text = set_var_to_type(e.get())
            code += '{0} = {1}\n'.format(l_text, e_text)
            used_labels.append(l_text)
            offset += 1
        else:
            break
        index += 1
    code += '_test_obj_={0}('.format(data[class_lineno]['name'])
    for l in used_labels:
        code += '{0},'.format(l.rstrip(':'))
    code = code.rstrip(',')
    code += ')\n'
    offset += 1
    
    while index < len(labels):
        used_labels = []
        func_name = labels[index].cget('text').rstrip(':')
        index += 1
        for (l, e) in zip(labels[index:], entries[index:]):
            l_text = l.cget('text').rstrip(':')
            if e.get() == '':
                bad_input = True
                executed_box.insert(INSERT, 'Variable {0}: Invalid Input.\n'.format(l_text))
            elif e.get() != '__NULL__':
                e_text = set_var_to_type(e.get())
                code += '{0} = {1}\n'.format(l_text, e_text)
                used_labels.append(l_text)
                offset += 1
            else:
                break
            index += 1
        code += '_test_obj_.{0}('.format(func_name)
        for l in used_labels:
            code += '{0},'.format(l.rstrip(':'))
        code = code.rstrip(',')
        code += ')\n'
    offset += 1
    if bad_input:
        executed_box.insert(INSERT, '\nIf you meant to put a string, use quotes\nsuch as: \'INPUT\'\nor\nFor an empty string use: \'\'\n')
    else:
        with open('temp_user_code.py', "w") as code_file:
            code_file.write(code)
            code_file.close()
        functionThread = TestFunctionThread('temp_user_code.py')
        functionThread.start()
        while not functionThread.complete and functionThread.isAlive():
            time.sleep(0.25)
            pass
        functionThread.stop()
        if functionThread.success:
            for l in range(line_length):
                executed_box.insert(INSERT, '\n')
            executed_output = ''
            tabs = -1
            prev_scope = None
            simple_id = 0
            for call_no, values in functionThread.executed_code.iteritems():
                if int(values['lineno']) < line_length and int(values['lineno']) != 1:
                    # Get executed_code
                    executed_line = None
                    if 'result' in functionThread.executed_code[call_no]:
                        if 'instance' in functionThread.executed_code[call_no]['result'] and '.' in functionThread.executed_code[call_no]['result']:
                            variable = ''
                            if '=' in functionThread.executed_code[call_no]['result']:
                                variable = functionThread.executed_code[call_no]['result'].split('=')[0]
                                value = functionThread.executed_code[call_no]['result'].split('=')[1]
                            else:
                                value = functionThread.executed_code[call_no]['result']
                            class_name = value.split(' instance')[0].split('.')[1]
                            value = '{0}_{1}'.format(class_name, simple_id)
                            simple_id += 1
                            if variable != '':
                                executed_line = '{0}={1}'.format(variable, value)
                            else:
                                executed_line = value
                        else:
                            executed_line = functionThread.executed_code[call_no]['result']
                    else:
                        for variable, value in functionThread.executed_code[call_no]['values'].iteritems():
                            if 'instance' in value and '.' in value:
                                class_name = value.split(' instance')[0].split('.')[1]
                                value = '{0}_{1}'.format(class_name, simple_id)
                                simple_id += 1
                            if executed_line is None:
                                executed_line = '{0}={1}'.format(variable, value)
                            else:
                                executed_line += ',{0}={1}'.format(variable, value)
                    scope = functionThread.get_scope(values['lineno'])
                    if scope != prev_scope:
                        prev_scope = scope
                        tabs += 1
                    executed_line = '{0}{1}'.format(tabs * '  ', executed_line)
                    executed_box.insert('{0}.end'.format(values['lineno']), '{0}    '.format(executed_line))
        else:
            executed_box.insert(INSERT, 'There was an error with your code. Please try again or modify your input\n')
    executed_box.config(state=DISABLED)


class TestFunctionThread(threading.Thread):
    def __init__(self, filename):
        self.executed_code = None
        self.variable_values_per_line = None
        threading.Thread.__init__(self)
        self.filename = filename
        self.stop_event = threading.Event()
        self.complete = False
        self.success = False

    def run(self):
        try:
            communicator = Communicate.main(self.filename, self.stop_event,
                                            input_event, user_inputs)
            if not self.stop_event.isSet():
                self.data = communicator.data
                self.executed_code = communicator.executed_code
                self.variable_values_per_line = communicator.variable_values
                self.correct_mangled_variables()
                self.success = True
        except Exception as e:
            self.stop()
            self.success = False
        self.complete = True

    def get_scope(self, lineno):
        if 'function_lines' in self.data and 'name' in self.data[lineno]:
            return self.data[lineno]['name']
        return 'global'


    def correct_mangled_variables(self):
        for call, evaluated in self.executed_code.iteritems():
            scope = self.get_scope(evaluated['lineno'])
            for key, value in evaluated['values'].iteritems():
                try:
                    correct_value = self.variable_values_per_line[call-1][scope][key]
                    correct_result = self.variable_values_per_line[call][scope][key]
                    if value != correct_value:
                        self.executed_code[call]['values'][key] = correct_value
                        if value == evaluated['result']:
                            self.executed_code[call]['result'] = correct_result
                        elif evaluated['result'] == '{0}={1}'.format(key, value):
                            self.executed_code[call]['result'] = '{0}={1}'.format(key, correct_result)
                except KeyError:
                    pass

    def stop(self):
        self.stop_event.set()


def test_function_call(toplevel, executed_box, code, func_lineno, func_name,
                       func_lines, labels, entries):
    executed_box.config(state=NORMAL)
    executed_box.delete(0.0, END)
    variables = []
    bad_input = False
    offset = 0
    for (l, e) in zip(labels, entries):
        l_text = l.cget('text').rstrip(':')
        if e.get() == '':
            bad_input = True
            executed_box.insert(INSERT, 'Variable {0}: Invalid Input.\n'.format(l_text))
        e_text = set_var_to_type(e.get())
        code += '{0} = {1}\n'.format(l_text, e_text)
        offset += 1
    code += '{0}('.format(func_name)
    for l in labels:
        code += '{0},'.format(l.cget('text').rstrip(':'))
    code = code.rstrip(',')
    code += ')\n'
    offset += 1
    if bad_input:
        executed_box.insert(INSERT, '\nIf you meant to put a string, use quotes\nsuch as: \'INPUT\'\nor\nFor an empty string use: \'\'\n')
    else:
        with open('temp_user_code.py', "w") as code_file:
            code_file.write(code)
            code_file.close()
        functionThread = TestFunctionThread('temp_user_code.py')
        functionThread.start()
        while not functionThread.complete and functionThread.isAlive():
            time.sleep(0.25)
            pass
        functionThread.stop()
        if functionThread.success:
            executed_output = ''
            call_no = offset
            simple_id = 0
            for line in func_lines:
                # Get executed_code
                executed_line = None
                if 'result' in functionThread.executed_code[call_no]:
                    if 'instance' in functionThread.executed_code[call_no]['result'] and '.' in functionThread.executed_code[call_no]['result']:
                        variable = ''
                        if '=' in functionThread.executed_code[call_no]['result']:
                            variable = functionThread.executed_code[call_no]['result'].split('=')[0]
                            value = functionThread.executed_code[call_no]['result'].split('=')[1]
                        else:
                            value = functionThread.executed_code[call_no]['result']
                        class_name = value.split(' instance')[0].split('.')[1]
                        value = '{0}_{1}'.format(class_name, simple_id)
                        simple_id += 1
                        if variable != '':
                            executed_line = '{0}={1}'.format(variable, value)
                        else:
                            executed_line = value
                    else:
                        executed_line = functionThread.executed_code[call_no]['result']
                else:
                    for variable, value in functionThread.executed_code[call_no]['values'].iteritems():
                        if 'instance' in value and '.' in value:
                            class_name = value.split(' instance')[0].split('.')[1]
                            value = '{0}_{1}'.format(class_name, simple_id)
                            simple_id += 1
                        if executed_line is None:
                            executed_line = '{0}={1}'.format(variable, value)
                        else:
                            executed_line += ',{0}={1}'.format(variable, value)
                executed_output += '{0}\n'.format(executed_line)
                call_no += 1
            executed_box.insert(INSERT, executed_output)
        else:
            executed_box.insert(INSERT, 'There was an error with your code. Please try again or modify your input\n')
    executed_box.config(state=DISABLED)


def add_class_function(event, widget, code_box, executed_box, label, combobox,
                       selected, labels, entries, r):
    print selected.get()
    labels.append(Label(widget, text='{0}:'.format(selected.get())))
    entries.append(Entry(widget))
    entries[-1].insert(INSERT, '__NULL__')
    new_labels = []
    new_entries = []
    if 'function_lines' in data and selected.get() in data['function_lines']:
        func_line = data['function_lines'][selected.get()][0]
        for expr in data[func_line]['expressions']:
            new_labels.append(Label(widget, text='{0}:'.format(expr)))
            new_entries.append(Entry(widget))
    labels[-1].grid(row=r, column=0)
    r += 1
    c = 0
    for l, e in zip(new_labels, new_entries):
        l.grid(row=r, column=c, sticky='E')
        e.grid(row=r, column=c+1, sticky='W')
        c += 2
        if c >= 4:
            r += 1
            c = 0
    r += 1
    label.grid(row=r, column=2)
    combobox.grid(row=r, column=3)
    labels.extend(new_labels)
    entries.extend(new_entries)
    combobox.unbind('<<ComboboxSelected>>')
    combobox.bind('<<ComboboxSelected>>', lambda event, w=widget,
                  cb=code_box, eb=executed_box, lab=label, comb_b=combobox,
                  s=selected, l=labels, e=entries, r=r: 
                  add_class_function(event, w, cb, eb, lab, comb_b, s, l, e, r))

def tag_class(event, line):
    toplevel = Toplevel()
    code_box = Text(toplevel, height=20, width=50, wrap=NONE)
    executed_box = Text(toplevel, height=20, width=50, wrap=NONE)
    class_lines = [line]
    labels = []
    entries = []
    func_names = []
    if ('classes' in data and line in data and 'name' in data[line] and
            data[line]['name'] in data['classes'] and
            'functions' in data['classes'][data[line]['name']]):
        for func, lines in data['classes'][data[line]['name']]['functions'].iteritems():
            class_lines.extend(lines)
            if func != '__init__':
                func_names.append(func)
            else:
                for expr in data[lines[0]]['expressions']:
                    labels.append(Label(toplevel, text='{0}:'.format(expr)))
                    entries.append(Entry(toplevel))
    class_lines.sort()
    code_box.config(height=len(class_lines)+2)
    executed_box.config(height=len(class_lines)+2)
    code_output = ''
    for l in class_lines:
        code_output += '{0}\n'.format(str(user_code.split('\n')[l-1]))
    code_box.insert(INSERT, code_output)
    code_box.config(state=DISABLED)

    # Add __init__ labels and entries
    r = 2
    c = 0
    for l, e in zip(labels, entries):
        l.grid(row=r, column=c, sticky='E')
        e.grid(row=r, column=c+1, sticky='W')
        c += 2
        if c >= 4:
            r += 1
            c = 0
    # Add button below
    r += 1
    selected = StringVar()
    label = Label(toplevel, text='Add Function Call')
    label.grid(row=r, column=2)
    combobox = ttk.Combobox(toplevel, values=tuple(func_names), 
                            textvariable=selected, state='readonly')
    combobox.grid(row=r, column=3)
    combobox.unbind('<<ComboboxSelected>>')
    combobox.bind('<<ComboboxSelected>>', lambda event, w=toplevel,
                  cb=code_box, eb=executed_box, lab=label, comb_b=combobox,
                  s=selected, l=labels, e=entries, r=r: 
                  add_class_function(event, w, cb, eb, lab, comb_b, s, l, e, r))
    # Add function labels and entries
    # Add button Below and
    # a run button
    test_class_button = Button(toplevel, text='Test Class',
        command=lambda tl=toplevel, eb=executed_box, c=code_output, c_lno=line,
        c_lines=class_lines, l=labels, e=entries:
        test_class_call(tl, eb, c, c_lno, c_lines, l, e))
    test_class_button.grid(row=0, column=3)
    code_box.grid(row=1, column=0, columnspan=2)
    executed_box.grid(row=1, column=2, columnspan=2)


def tag_function_calls(event, line, call_points):
    toplevel = Toplevel()
    selected_call = StringVar()
    code_box = Text(toplevel, height=10, width=50, wrap=NONE)
    executed_box = Text(toplevel, height=10, width=50, wrap=NONE)
    combobox = ttk.Combobox(toplevel, textvariable=selected_call)
    labels = []
    entries = []
    for expr in data[line]['expressions']:
        labels.append(Label(toplevel, text='{0}:'.format(expr)))
        entries.append(Entry(toplevel))
    func_lines = []
    func_name = ''
    if 'name' in data[line] and 'function_lines' in data:
        func_name = data[line]['name']
        func_lines = data['function_lines'][func_name]
        # for func, lines in data['function_lines'].iteritems():
        #     if line in lines:
        #         func_name = func
        #         func_lines = lines
        #         continue
    code_box.config(height=len(func_lines)+2)
    executed_box.config(height=len(func_lines)+2)
    code_output = ''
    for l in func_lines:
        code_output += '{0}\n'.format(str(user_code.split('\n')[l-1]))
    code_box.insert(INSERT, code_output)
    code_box.config(state=DISABLED)
    
    test_function_button = Button(toplevel, text='Test Function',
        command=lambda tl=toplevel, eb=executed_box, c=code_output, f_lno=line,
        f_name=func_name, f_lines=func_lines, l=labels, e=entries:
        test_function_call(tl, eb, c, f_lno, f_name, f_lines, l, e))
    combobox['state'] = 'readonly'
    result = []

    index = 1
    for lineno, calls in call_points.iteritems():
        for call in calls:
            if len(calls) > 1:
                call_line = 'Call: {0} @ Line: {1}'.format(index, lineno)
            else:
                call_line = 'Line: {1}'.format(index, lineno)
            for variable, value in executed_code[call]['values'].iteritems():
                if ':' in call_line:
                    call_line += ', {0}={1}'.format(variable, value)
                else:
                    call_line += ': {0}={1}'.format(variable, value)
            result.append(call_line)
            index += 1
    result.sort()
    combobox['values'] = tuple(result)
    combobox.unbind('<<ComboboxSelected>>')
    combobox.bind('<<ComboboxSelected>>', lambda event,
                        eb=executed_box, f_lno=line, f_lines=func_lines, sc=selected_call:
                        display_func_output(event, eb, f_lno, f_lines, sc))
    combobox.grid(row=0, column=1)
    test_function_button.grid(row=0, column=2)
    code_box.grid(row=1, column=0, columnspan=2)
    executed_box.grid(row=1, column=2, columnspan=2)
    r = 2
    c = 0
    for l, e in zip(labels, entries):
        l.grid(row=r, column=c, sticky='E')
        e.grid(row=r, column=c+1, sticky='W')
        c += 2
        if c >= 4:
            r += 1
            c = 0


def simple_tag_function_calls(event, line, call_points):
    toplevel = Toplevel()
    selected_call = StringVar()
    code_box = Text(toplevel, height=10, width=50, wrap=NONE)
    executed_box = Text(toplevel, height=10, width=50, wrap=NONE)
    combobox = ttk.Combobox(toplevel, textvariable=selected_call)
    func_lines = []
    func_name = ''
    if 'name' in data[line] and 'function_lines' in data:
        func_name = data[line]['name']
        func_lines = data['function_lines'][func_name]
    code_box.config(height=len(func_lines)+2)
    executed_box.config(height=len(func_lines)+2)
    code_output = ''
    for l in func_lines:
        code_output += '{0}\n'.format(str(user_code.split('\n')[l-1]))
    code_box.insert(INSERT, code_output)
    code_box.config(state=DISABLED)
    combobox['state'] = 'readonly'
    result = []
    index = 1
    for lineno, calls in call_points.iteritems():
        for call in calls:
            if len(calls) > 1:
                call_line = 'Call: {0} @ Line: {1}'.format(index, lineno)
            else:
                call_line = 'Line: {1}'.format(index, lineno)
            for variable, value in executed_code[call]['values'].iteritems():
                if ':' in call_line:
                    call_line += ', {0}={1}'.format(variable, value)
                else:
                    call_line += ': {0}={1}'.format(variable, value)
            result.append(call_line)
            index += 1
    result.sort()
    combobox['values'] = tuple(result)
    combobox.unbind('<<ComboboxSelected>>')
    combobox.bind('<<ComboboxSelected>>', lambda event,
                        eb=executed_box, f_lno=line, f_lines=func_lines, sc=selected_call:
                        display_func_output(event, eb, f_lno, f_lines, sc))
    combobox.grid(row=0, column=1)
    code_box.grid(row=1, column=0, columnspan=2)
    executed_box.grid(row=1, column=2, columnspan=2)


def display_loop_output(value, lines, calls, executed_box):
    executed_box.config(state=NORMAL)
    executed_box.delete(0.0, END)
    index = int(value) * len(lines)
    executed_output = ''
    i = 0
    while i < len(lines):
        executed_line = None
        if index < len(calls):
            if 'result' in executed_code[calls[index]]:
                if 'instance' in executed_code[calls[index]]['result'] and '.' in executed_code[calls[index]]['result']:
                    variable = executed_code[calls[index]]['result'].split('=')[0]
                    value = executed_code[calls[index]]['result'].split('=')[1]
                    class_name = value.split(' instance')[0].split('.')[1]
                    instance_id = value.split(' instance at ')[1].split('>')[0]
                    obj = get_object(instance_id)
                    value = '{0}_{1}'.format(class_name, obj.simple_id)
                    executed_line = '{0}={1}'.format(variable, value)
                else:
                    executed_line = executed_code[calls[index]]['result']
            else:
                for variable, value in executed_code[calls[index]]['values'].iteritems():
                    if 'instance' in value and '.' in value:
                        class_name = value.split(' instance')[0].split('.')[1]
                        instance_id = value.split(' instance at ')[1].split('>')[0]
                        obj = get_object(instance_id)
                        value = '{0}_{1}'.format(class_name, obj.simple_id)
                    if executed_line is None:
                        executed_line = '{0}={1}'.format(variable, value)
                    else:
                        executed_line += ',{0}={1}'.format(variable, value)
            executed_output += '{0}\n'.format(executed_line)
        index += 1
        i += 1
    executed_box.insert(INSERT, executed_output)
    executed_box.config(state=DISABLED)


def tag_loops(event, line):
    toplevel = Toplevel()
    lines = data['loop_lines'][line]
    calls, length = get_loop_iteration_calls(line, lines)
    code_box = Text(toplevel, height=10, width=50, wrap=NONE)
    executed_box = Text(toplevel, height=10, width=50, wrap=NONE)
    scale = Scale(toplevel, orient=HORIZONTAL, to=length-1,
                  command=lambda value, l=lines, c=calls, eb=executed_box:
                  display_loop_output(value, l, c, eb))

    scale.pack()
    code_box.pack(side=LEFT)
    executed_box.pack(side=LEFT)

    code_output = ''
    for l in lines:
        code_output += '{0}\n'.format(str(user_code.split('\n')[l-1]))
    code_box.insert(INSERT, code_output)
    code_box.config(state=DISABLED)


def set_line_tag(code_box, lineno, line):
    code_box.tag_remove('line{0}'.format(lineno),
                                '{0}.0'.format(lineno),
                                '{0}.{1}'.format(lineno, len(line)))
    code_box.tag_add('line{0}'.format(lineno),
                     '{0}.0'.format(lineno),
                     '{0}.{1}'.format(lineno, len(line)))


def get_additional_lines(lineno):
    additional_lines = []
    if (data is not None and lineno in data and
            'additional_lines' in data[lineno]):
        for name in data[lineno]['additional_lines']:
            if '.' in name:
                name = name.split('.')[-1]

            if 'function_lines' in data and name in data['function_lines']:
                additional_lines.extend(data['function_lines'][name])
            elif ('classes' in data and name in data['classes'] and
                    '__init__' in data['classes'][name]['functions']):
                additional_lines.extend(data['classes'][name]['functions']['__init__'])
    return additional_lines


def bind_line_tags(code_box, lineno, call, line, additional_lines):
    code_box.tag_unbind('line{0}'.format(lineno), '<Enter>')
    code_box.tag_unbind('line{0}'.format(lineno), '<Leave>')
    code_box.tag_bind(
        'line{0}'.format(lineno),
        '<Enter>',
        lambda event, widget=code_box, lineno=lineno, call=call,
        line_length=len(line),
        lines=additional_lines: add_highlight(
            event, widget, lineno, call, 0, line_length, lines))
    code_box.tag_bind(
        'line{0}'.format(lineno),
        '<Leave>',
        lambda event, widget=code_box, lineno=lineno, call=call,
        line_length=len(line),
        lines=additional_lines: remove_highlight(
            event, widget, lineno, call, 0, line_length, lines))


def set_class_tag(code_box, lineno):
    if (lineno in data and 'type' in data[lineno] and
            'class' == data[lineno]['type']):
        code_box.tag_unbind('line{0}'.format(lineno), '<Button-1>')
        code_box.tag_bind(
            'line{0}'.format(lineno),
            '<Button-1>',
            lambda event, lineno=lineno:
            tag_class(event, lineno))


def set_function_tag(code_box, lineno):
    if (lineno in data and 'type' in data[lineno] and
            'func' == data[lineno]['type']):
        call_points = get_function_call_points(lineno)
        code_box.tag_unbind('line{0}'.format(lineno), '<Button-1>')
        should_bind = True
        if lineno in data and 'classes' in data:
            for class_name, class_items in data['classes'].iteritems():
                if 'functions' in class_items:
                    for func, lines in class_items['functions'].iteritems():
                        if lineno in lines:
                            should_bind = False
                            break
        if should_bind:
            code_box.tag_bind(
                'line{0}'.format(lineno),
                '<Button-1>',
                lambda event, lineno=lineno, cp=call_points:
                tag_function_calls(event, lineno, cp))
        else:
            code_box.tag_bind(
                'line{0}'.format(lineno),
                '<Button-1>',
                lambda event, lineno=lineno, cp=call_points:
                simple_tag_function_calls(event, lineno, cp))


def set_loop_tag(code_box, lineno):
    if (lineno in data and 'type' in data[lineno] and
            'loop' == data[lineno]['type']):
        code_box.tag_unbind('line{0}'.format(lineno), '<Button-1>')
        code_box.tag_bind(
            'line{0}'.format(lineno),
            '<Button-1>',
            lambda event, lineno=lineno: tag_loops(event, lineno))


def tag_lines(code_box):
    global data
    user_code = code_box.get('0.0', 'end-1c')
    lines = str(user_code).split('\n')
    called_lines = {}
    try:
        for call, values in executed_code.iteritems():
            lineno = values['lineno']
            line = lines[lineno-1]
            if lineno in data and lineno not in called_lines:
                called_lines[lineno] = True
                set_line_tag(code_box, lineno, line)
                additional_lines = get_additional_lines(lineno)
                bind_line_tags(code_box, lineno, call, line, additional_lines)
                set_function_tag(code_box, lineno)
                set_class_tag(code_box, lineno)
                set_loop_tag(code_box, lineno)
        lineno = 0
        for line in lines:
            if lineno in data and lineno not in called_lines:
                set_line_tag(code_box, lineno, line)
                set_function_tag(code_box, lineno)
                set_class_tag(code_box, lineno)
            lineno += 1
    except:
        pass


def correct_mangled_variables():
    global executed_code
    for call, evaluated in executed_code.iteritems():
        scope = get_scope(evaluated['lineno'])
        for key, value in evaluated['values'].iteritems():
            try:
                correct_value = variable_values_per_line[call-1][scope][key]
                correct_result = variable_values_per_line[call][scope][key]
                if value != correct_value: # and 'instance at 0x' not in value:
                    # print 'CORRECTING: {0} --> from {1} --> to {2} --> result {3}'.format(key, value, correct_value, correct_result)
                    executed_code[call]['values'][key] = correct_value
                    if value == evaluated['result']:
                        executed_code[call]['result'] = correct_result
                    elif evaluated['result'] == '{0}={1}'.format(key, value):
                        executed_code[call]['result'] = '{0}={1}'.format(key, correct_result)
            except KeyError:
                pass


class CommunicationThread(threading.Thread):
    def __init__(self, filename):
        threading.Thread.__init__(self)
        self.filename = filename
        self.stop_event = threading.Event()

    def run(self):
        global executed_code
        global data
        global variable_scope
        global input_event
        global user_inputs
        global additional_lines_call_point
        global variable_values_per_line
        global successful_exit
        try:
            communicator = Communicate.main(self.filename, self.stop_event,
                                            input_event, user_inputs)
            if not self.stop_event.isSet():
                executed_code = communicator.executed_code
                data = communicator.data
                variable_scope = communicator.variable_scope
                additional_lines_call_point = \
                    communicator.additional_lines_call_point
                variable_values_per_line = communicator.variable_values
                correct_mangled_variables()
                reset_objects()
                successful_exit = True
        except Exception as e:
            print 'ERROR ERROR ERROR'
            successful_exit = False
            self.stop()

    def stop(self):
        self.stop_event.set()


def check_for_new_input(lines):
    global user_inputs
    # By removing the last line split, this forces the user to hit enter after
    # each of their line inputs. Leaving an empty line at the bottom of the
    # input box
    if len(lines) > len(user_inputs):
        if lines[len(user_inputs)] != '':
            user_inputs.append(lines[len(user_inputs)])
            input_event.set()
            with open(INPUT_FILE_NAME, "w") as input_file:
                for user_input in user_inputs:
                    input_file.write('{0}\n'.format(user_input))
                input_file.close()


def input_box_has_changes(lines):
    global user_inputs
    has_changed = False
    if len(user_inputs) > len(lines):
        while len(user_inputs) > len(lines):
            del user_inputs[len(user_inputs) - 1]
        has_changed = True
    else:
        i = 0
        while i < len(user_inputs):
            if user_inputs[i] != lines[i]:
                user_inputs[i] = lines[i]
                has_changed = True
            i += 1
    if has_changed:
        with open(INPUT_FILE_NAME, "w") as input_file:
            for user_input in user_inputs:
                input_file.write('{0}\n'.format(user_input))
            input_file.close()
    return has_changed


def reset_tags(code_box):
    for tag in code_box.tag_names():
        code_box.tag_delete(tag)

    code_box.tag_configure('Token.Keyword', foreground='orange red')
    code_box.tag_configure('Token.Operator', foreground='orange red')
    code_box.tag_configure('Token.Name.Function', foreground='lawn green')
    code_box.tag_configure('Token.Literal.Number.Integer', foreground='medium orchid')
    code_box.tag_configure('Token.Name.Builtin', foreground='medium turquoise')
    code_box.tag_configure('Token.Literal.String.Single', foreground='yellow')
    code_box.tag_configure('Token.Name.Builtin.Pseudo', foreground='orange')
    code_box.tag_configure('HIGHLIGHT', background='gray5')


def run_user_code(code_box, new_user_code):
    global user_code
    global communicationThread

    reset_tags(code_box)
    highlight_code(code_box)
    try:
        if communicationThread is None:
            user_code = new_user_code
            with open(FILE_NAME, "w") as code_file:
                code_file.write(user_code)
                code_file.close()
            communicationThread = CommunicationThread(FILE_NAME)
            communicationThread.start()
    except:
        pass


def on_scale_change(code_box, variable_box, output_box, start_scale, scale,
                    tree_wrapper, tree_viewer, combobox):
    global prev_scale_setting
    global prev_start_scale_setting

    prev_scale_setting = scale.get()
    start_scale.config(to=prev_scale_setting)
    prev_start_scale_setting = start_scale.get()
    reset_boxes(variable_box, output_box)
    reset_objects()
    if executed_code is not None:
        display_executed_code(executed_code, code_box,
                              variable_box, output_box,
                              start_scale.get(), scale.get())
    display_objects(tree_wrapper, tree_viewer, combobox)


def display_user_code(code_box, variable_box, output_box, start_scale, scale,
                      tree_wrapper, tree_viewer, combobox):
    global scale_size
    global prev_scale_setting
    global prev_start_scale_setting
    global communicationThread
    global input_event
    global successful_exit

    input_event.clear()
    communicationThread = None
    if successful_exit:
        successful_exit = False
        reset_boxes(variable_box,
                    output_box)
        tag_lines(code_box)
        scale_size = len(executed_code)
        scale.config(to=scale_size)
        scale.set(scale_size)
        prev_scale_setting = scale_size
        start_scale.config(to=scale_size)
        prev_start_scale_setting = start_scale.get()
        display_executed_code(executed_code, code_box,
                              variable_box, output_box, start_scale.get(),
                              scale_size)
        display_objects(tree_wrapper, tree_viewer, combobox)


def set_line_numbers(lineno_box, line_count):
    lineno_box.config(state=NORMAL)
    lineno_box.delete(0.0, END)
    lineno = 1
    while lineno < line_count:
        lineno_box.insert(INSERT, '{0}\n'.format(lineno))
        lineno += 1
    lineno_box.insert(INSERT, '{0}'.format(lineno))
    lineno_box.config(state=DISABLED)


def main_loop(scrolled_text_pair, lineno_box, from_box, input_box, variable_box,
              output_box, start_scale, scale, tree_wrapper, tree_viewer,
              combobox):
    global user_code
    global prev_scale_setting
    global prev_start_scale_setting
    global communicationThread
    global input_event
    global rerun_event
    global scroll_position

    if exit_event.isSet():
        return
    if not DO_NOT_RUN:
        new_user_code = from_box.get(0.0, END)[:-1]

        if user_code != new_user_code:
            scroll_position = scrolled_text_pair.scrollbar.get()
            scrolled_text_pair.right.configure(yscrollcommand=None, state=DISABLED)
            set_line_numbers(lineno_box, len(new_user_code.split('\n')))
            run_user_code(from_box, new_user_code)
        elif (scale.get() != prev_scale_setting or 
                start_scale.get() != prev_start_scale_setting):
            # scroll_position = scrolled_text_pair.scrollbar.get()
            # scrolled_text_pair.right.configure(yscrollcommand=None, state=DISABLED)
            on_scale_change(from_box, variable_box, output_box, start_scale,
                            scale, tree_wrapper, tree_viewer, combobox)
            # if scroll_position is not None:
            #     scrolled_text_pair.right.configure(
            #         yscrollcommand=scrolled_text_pair.on_textscroll)
            #     scrolled_text_pair.right.yview('moveto', scroll_position[0])
            #     scroll_position = None

        if communicationThread is not None and not communicationThread.isAlive():
            display_user_code(from_box, variable_box, output_box, start_scale,
                              scale, tree_wrapper, tree_viewer, combobox)
            if scroll_position is not None:
                scrolled_text_pair.right.configure(
                    yscrollcommand=scrolled_text_pair.on_textscroll)
                scrolled_text_pair.right.yview('moveto', scroll_position[0])
                scroll_position = None

        # Check for new input
        lines = str(input_box.get(0.0, END)[:-1]).split('\n')[:-1]
        check_for_new_input(lines)

        if input_box_has_changes(lines):
            # If a thread is running, kill the thread and set the rerun flag.
            # Else rerun the user's code right away.
            if communicationThread is not None and communicationThread.isAlive():
                communicationThread.stop()
                rerun_event.set()
            else:
                user_code = ''
            input_event.clear()

        # Wait for the thread to kill itself, then rerun the user's code.
        if communicationThread is None and rerun_event.isSet():
            rerun_event.clear()
            user_code = ''

    root.after(10, main_loop, scrolled_text_pair, lineno_box, from_box,
               input_box, variable_box, output_box, start_scale, scale,
               tree_wrapper, tree_viewer, combobox)


class ScrolledTextPair(Frame):
    # http://stackoverflow.com/questions/32038701/python-tkinter-making-two-text-widgets-scrolling-synchronize
    '''Two Text widgets and a Scrollbar in a Frame'''
    def __init__(self, master, **kwargs):
        Frame.__init__(self, master)  # no need for super
        # Different default width
        # if 'width' not in kwargs:
        #     kwargs['width'] = 30
        # Creating the widgets
        self.left = Text(self, foreground='gray', background='gray15', height=55, width=3, wrap=NONE)
        self.right = Text(self, foreground='white', background='gray15', height=55, wrap=NONE)
        if os.path.isfile(FILE_NAME):
            with open(FILE_NAME, 'r') as code_file:
                lines = code_file.readlines()
                lineno = 1
                for line in lines:
                    self.right.insert(INSERT, line)
                    if lineno == len(lines):
                        self.left.insert(INSERT, '{0}'.format(lineno))
                    else:
                        self.left.insert(INSERT, '{0}\n'.format(lineno))
                    lineno += 1
                code_file.close()
        self.left.pack(side=LEFT, fill=Y)
        self.right.pack(side=LEFT, fill=Y)

        self.scrollbar = Scrollbar(self)
        self.scrollbar.pack(side=RIGHT, fill=Y)
        # Changing the settings to make the scrolling work
        self.scrollbar['command'] = self.on_scrollbar
        self.left['yscrollcommand'] = self.on_textscroll
        self.right['yscrollcommand'] = self.on_textscroll

    def on_scrollbar(self, *args):
        '''Scrolls both text widgets when the scrollbar is moved'''
        self.left.yview(*args)
        self.right.yview(*args)

    def on_textscroll(self, *args):
        '''Moves the scrollbar and scrolls text widgets when the mousewheel
        is moved on a text widget'''
        self.scrollbar.set(*args)
        self.on_scrollbar('moveto', args[0])



class Application(Frame):
    def close_all(self):
        global communicationThread
        exit_event.set()
        if communicationThread is not None and communicationThread.isAlive():
            communicationThread.stop()
            user_inputs.append('quit')
            input_event.set()
            while communicationThread.isAlive():
                continue
            communicationThread = None
        self.quit()

    def open_input_file(self, input_box):
        file = tkFileDialog.askopenfile(parent=root, mode='rb',
                                        title='Choose a file')
        if file is not None:
            data = file.read()
            input_box.delete(0.0, END)
            input_box.insert(INSERT, data)
            file.close()

    def createWidgets(self):
        self.bg = 'grey'
        main_frame = Frame(self, bg='grey')
        menu_frame = Frame(main_frame)
        left_frame = Frame(main_frame, bg='grey')
        center_frame = Frame(main_frame, bg='grey')
        right_frame = Frame(main_frame, bg='grey')

        code_frame = Frame(left_frame)
        variable_frame = Frame(center_frame)
        tree_frame = Frame(center_frame)
        input_frame = Frame(right_frame, width=50)
        output_frame = Frame(right_frame, width=50)

        main_frame.pack()
        menu_frame.pack(side=TOP, fill=X)
        left_frame.pack(side=LEFT, fill=Y)
        center_frame.pack(side=LEFT)
        right_frame.pack(side=LEFT)

        code_frame.pack(fill=Y)
        variable_frame.pack(side=TOP)
        tree_frame.pack(side=TOP)
        input_frame.pack(side=TOP)
        output_frame.pack(side=TOP)

        # Menu Frame
        QUIT = Button(master=menu_frame, text='Quit', command=self.close_all)
        QUIT.pack(side=LEFT)
        start_execution_step = Scale(menu_frame, orient=HORIZONTAL)
        start_execution_step.pack(side=LEFT, padx=200)
        input_button = Button(master=menu_frame, text='Input File',
                              command=lambda: self.open_input_file(input_box))
        input_button.pack(side=RIGHT)
        execution_step = Scale(menu_frame, orient=HORIZONTAL)
        execution_step.pack(side=RIGHT, padx=200)

        # Left Frame
        code_title = Label(code_frame, text='Source Code')
        code_title.pack(side=TOP, fill=X)
        paired_text_boxes = ScrolledTextPair(code_frame, foreground='white',
                                             background='gray15')
        lineno_box = paired_text_boxes.left
        lineno_box.config(state=DISABLED)
        code_box = paired_text_boxes.right
        paired_text_boxes.pack()
        # lineno_box = Text(code_frame, foreground='gray', background='gray15', height=55, width=3, wrap=NONE)
        # code_box = Text(code_frame, foreground='white', background='gray15', height=55, wrap=NONE)
        # code_box.tag_configure('Token.Keyword', foreground='orange red')
        # code_box.tag_configure('Token.Operator', foreground='orange red')
        # code_box.tag_configure('Token.Name.Class', foreground='green yellow')
        # code_box.tag_configure('Token.Name.Function', foreground='green yellow')
        # code_box.tag_configure('Token.Literal.Number.Integer',
        #                         foreground='medium orchid')
        # code_box.tag_configure('Token.Name.Builtin', foreground='medium turquoise')
        # code_box.tag_configure('Token.Literal.String.Single',
        #                         foreground='yellow')
        # code_box.tag_configure('Token.Name.Builtin.Pseudo',
        #                         foreground='orange')
        # code_box.tag_configure('HIGHLIGHT', background='gray5')
        # if os.path.isfile(FILE_NAME):
        #     with open(FILE_NAME, 'r') as code_file:
        #         lines = code_file.readlines()
        #         lineno = 1
        #         for line in lines:
        #             code_box.insert(INSERT, line)
        #             lineno_box.insert(INSERT, '{0}\n'.format(lineno))
        #             lineno += 1
        #         code_file.close()
        # lineno_box.pack(side=LEFT, fill=Y)
        # code_box.pack(side=LEFT, fill=Y)

        # Center Frame
        variable_title = Label(variable_frame, text='Variables')
        variable_title.pack(side=TOP, fill=X)
        variable_box = Text(variable_frame)
        variable_box.tag_configure("BOLD", font=('-weight bold'))
        variable_box.pack(side=TOP)

        tree_frame_title = Label(tree_frame, text='Objects')
        tree_frame_title.pack(side=TOP, fill=X)
        combobox = ttk.Combobox(tree_frame, textvariable=selected_object)
        combobox['state'] = 'readonly'
        combobox.pack()
        tree_wrapper = treeview.GenericObjectWrapper()
        tree_viewer = TreeViewer(tree_wrapper, tree_frame)
        combobox.bind('<<ComboboxSelected>>', lambda event, cb=combobox,
                        tv=tree_viewer: display_tree(event, cb, tv))

        # Right Frame
        input_title = Label(input_frame, text='Input')
        input_title.pack(side=TOP, fill=X)
        input_box = Text(input_frame)
        input_box.pack(side=TOP, fill=Y)
        if os.path.isfile(INPUT_FILE_NAME):
            with open(INPUT_FILE_NAME, 'r') as input_file:
                lines = input_file.readlines()
                for line in lines:
                    input_box.insert(INSERT, line)
                    user_inputs.append(line[:-1])
                input_file.close()

        output_title = Label(output_frame, text='Output')
        output_title.pack(side=TOP, fill=X)
        output_box = Text(output_frame)
        output_box.pack(side=TOP, fill=Y)

        root.after(500, main_loop, paired_text_boxes, lineno_box,
                   code_box, input_box, variable_box, output_box,
                   start_execution_step, execution_step, tree_wrapper,
                   tree_viewer, combobox)

    def __init__(self, master=None):
        Frame.__init__(self, master)
        self.pack()
        self.createWidgets()


app = Application(master=root)
app.mainloop()
root.destroy()
