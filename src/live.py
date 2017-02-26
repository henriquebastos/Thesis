from Tkinter import *
from tkinter import ttk
from tkMessageBox import showinfo
import tkFileDialog
import os
import ScrolledText as ST
import threading

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
highlight_map = {}
additional_lines_call_point = None
scroll_position = None
successful_exit = True

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

    variable_box.delete(0.0, END)
    for func, variables in variable_scope.items():
        func_lines = None
        if 'function_lines' in data and func in data['function_lines']:
            func_lines = data['function_lines'][func]
        variables_line = ''
        for variable in variables:
            if (func in variable_values and variable in variable_values[func] and
                variable_declared_in_scope(variable, func, func_lines)):

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
                else:
                    variables_line += '{0}={1}\n'.format(
                        variable, variable_values[func][variable])
        if variables_line != '':
            variable_box.insert(INSERT, '{0}:\n'.format(func), 'BOLD')
            variable_box.insert(INSERT, variables_line)
            variable_box.insert(INSERT, '\n')


def get_scope(lineno):
    global data
    if 'function_lines' in data:
        for func, lines in data['function_lines'].items():
            for line in lines:
                if lineno == line:
                    return func
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
                value['result'] = value['result'].split('=')[1]
            return '{0}'.format(value['result'])
    else:
        if '=' in value['result']:
            value['result'] = value['result'].split('=')[1]
        return '{0}'.format(value['result'])


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


def handle_highlights_in_executed_code(key, value, display_map, display_line,
                                       tab_count):
    global highlight_map
    # Get correct tab length
    tabs = ''
    for i in range(tab_count):
        tabs += '  '
    current_length = 0
    if key not in highlight_map:  # Setup highlight map key
        highlight_map[key] = {}
    if value['lineno'] in display_map:
        # Display executed code at the correct indentation
        current_length = len(display_map[value['lineno']])
        if current_length >= len(tabs):
            tab_count += 2
            tabs += '    '
        display_map[value['lineno']] += tabs[current_length:] + \
            display_line
        # Mark lines start point
        highlight_map[key]['start'] = current_length + \
            len(tabs[current_length:])
    else:
        # Display executed code at the correct indentation
        display_map[value['lineno']] = tabs + display_line
        # Mark lines start point
        highlight_map[key]['start'] = current_length + len(tabs)
    highlight_map[key]['lineno'] = value['lineno']
    highlight_map[key]['end'] = len(display_map[value['lineno']])
    tab_count += 1
    return tab_count


def display_executed_code(executed_code, code_box,
                          variable_box, output_box, start, total):
    global highlight_map
    global current_generic_object
    global current_object_lines
    global current_function
    global display_map
    highlight_map = {}
    display_map = {}
    tab_count = 0
    for key, value in executed_code.iteritems():
        display_line = ''
        if total >= 0 and start <= 0:
            if 'result' in value:
                if 'assigned' in value:
                    handle_assignment_in_executed_code(value, key)
                if 'print' in value:
                    output_box.insert(INSERT, value['result'] + '\n')
                if (value['lineno'] in data and
                        'additional_lines' in data[value['lineno']]):
                    handle_additional_lines_in_executed_code(value)
                display_line += get_display_line_in_executed_code(value)
            else:
                display_line = handle_functions_in_executed_code(value, key)
            display_variables(variable_box, key)

            tab_count = handle_highlights_in_executed_code(key, value, display_map,
                                                       display_line, tab_count)
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


def reset_boxes(new_user_code, variable_box, output_box):
    global variable_values
    variable_box.delete(0.0, END)
    output_box.delete(0.0, END)
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


def tag_add_highlight(widget, line, start, length):
    global DO_NOT_RUN
    DO_NOT_RUN = True
    widget.tag_remove('HIGHLIGHT', '{0}.{1}'.format(line, start),
                      '{0}.{1}'.format(line, length))
    widget.tag_add('HIGHLIGHT', '{0}.{1}'.format(line, start),
                   '{0}.{1}'.format(line, length))
    if line in display_map:
        widget.insert('{0}.{1}'.format(line, length), '     {0}'.format(display_map[line].lstrip(' ')))


def tag_remove_highlight(widget, line, start, length):
    global DO_NOT_RUN
    widget.tag_remove('HIGHLIGHT', '{0}.{1}'.format(line, start),
                      '{0}.{1}'.format(line, length))
    widget.delete('{0}.{1}'.format(line, length), '{0}.end'.format(line))
    DO_NOT_RUN = False


def optional_add_highlights(widget, lineno, line_start, line_length,
                            lines=None):
    if lines is not None:
        for line in lines:
            end = len(user_code.split('\n')[line-1])
            tag_add_highlight(widget, line, 0, end)

def optional_remove_highlights(widget, lineno, line_start, line_length,
                               lines=None):
    if lines is not None:
        for line in lines:
            end = len(user_code.split('\n')[line-1])
            tag_remove_highlight(widget, line, 0, end)


def add_highlight(event, widget, lineno, line_start, line_length,
                  opt_widget=None, lines=None):
    tag_add_highlight(widget, lineno, line_start, line_length)
    if opt_widget is not None:
        optional_add_highlights(opt_widget, lineno, line_start, line_length,
                                lines)


def remove_highlight(event, widget, lineno, line_start, line_length,
                     opt_widget=None, lines=None):
    tag_remove_highlight(widget, lineno, line_start, line_length)
    if opt_widget is not None:
        optional_remove_highlights(opt_widget, lineno, line_start, line_length,
                                   lines)


def tag_add_code(event, widget, line):
    if len(widget.get('{0}.0'.format(line), '{0}.end'.format(line))) > 1:
        widget.delete('{0}.0'.format(line), '{0}.end'.format(line))
    else:
        widget.insert('{0}.end'.format(line), '     {0}'.format(display_map[line]))


def display_func_output(event, code_box, executed_box, func_lineno, selected_call):
    code_box.delete(0.0, END)
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
    # Get function Lines:
    func_lines = []
    if 'function_lines' in data:
        for func, lines in data['function_lines'].iteritems():
            if func_lineno in lines:
                func_lines = lines
                continue
    # Get the code for those lines
    code_output = ''
    executed_output = ''
    for line in func_lines:
        # Get executed_code
        call_no = additional_lines_call_point[calling_lineno][line][index]
        executed_line = None
        if 'result' in executed_code[call_no]:
            executed_line = executed_code[call_no]['result']
        else:
            for variable, value in executed_code[call_no]['values'].iteritems():
                if executed_line is None:
                    executed_line = '{0}={1}'.format(variable, value)
                else:
                    executed_line += ',{0}={1}'.format(variable, value)
        code_output += '{0}\n'.format(str(user_code.split('\n')[line-1]))
        executed_output += '{0}\n'.format(executed_line)
    code_box.insert(INSERT, code_output)
    executed_box.insert(INSERT, executed_output)

def tag_function_calls(event, line, call_points):
    toplevel = Toplevel()
    selected_call = StringVar()
    code_box = Text(toplevel, height=10, width=50)
    executed_box = Text(toplevel, height=10, width=50)
    combobox = ttk.Combobox(toplevel, textvariable=selected_call)
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
    combobox.bind('<<ComboboxSelected>>', lambda event, cb=code_box,
                        eb=executed_box, f_lno=line, sc=selected_call:
                        display_func_output(event, cb, eb, f_lno, sc))
    combobox.pack()
    code_box.pack(side=LEFT)
    executed_box.pack(side=LEFT)


def display_loop_output(value, lines, calls, executed_box):
    executed_box.delete(0.0, END)
    index = int(value) * len(lines)
    executed_output = ''
    i = 0
    while i < len(lines):
        executed_line = None
        if index < len(calls):
            if 'result' in executed_code[calls[index]]:
                executed_line = executed_code[calls[index]]['result']
            else:
                for variable, value in executed_code[calls[index]]['values'].iteritems():
                    if executed_line is None:
                        executed_line = '{0}={1}'.format(variable, value)
                    else:
                        executed_line += ',{0}={1}'.format(variable, value)
            executed_output += '{0}\n'.format(executed_line)
        index += 1
        i += 1
    executed_box.insert(INSERT, executed_output)


def tag_loops(event, line):
    toplevel = Toplevel()
    lines = data['loop_lines'][line]
    calls, length = get_loop_iteration_calls(line, lines)
    code_box = Text(toplevel, height=10, width=50)
    executed_box = Text(toplevel, height=10, width=50)
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


def tag_lines(code_box):
    global data
    user_code = code_box.get('0.0', 'end-1c')
    lines = str(user_code).split('\n')
    line_count = 1
    for line in lines:
        if line_count in data:
            code_box.tag_remove('line{0}'.format(line_count),
                                '{0}.0'.format(line_count),
                                '{0}.{1}'.format(line_count, len(line)))
            code_box.tag_add('line{0}'.format(line_count),
                             '{0}.0'.format(line_count),
                             '{0}.{1}'.format(line_count, len(line)))
            additional_lines = []
            if (data is not None and line_count in data and
                    'additional_lines' in data[line_count]):
                for name in data[line_count]['additional_lines']:
                    if '.' in name:
                        name = name.split('.')[-1]

                    if 'function_lines' in data and name in data['function_lines']:
                        additional_lines.extend(data['function_lines'][name])
                    elif ('classes' in data and name in data['classes'] and
                            '__init__' in data['classes'][name]['functions']):
                        additional_lines.extend(data['classes'][name]['functions']['__init__'])
            code_box.tag_unbind('line{0}'.format(line_count), '<Enter>')
            code_box.tag_unbind('line{0}'.format(line_count), '<Leave>')
            code_box.tag_bind(
                'line{0}'.format(line_count),
                '<Enter>',
                lambda event, widget=code_box, lineno=line_count,
                line_length=len(line), opt_widget=None,
                lines=additional_lines: add_highlight(
                    event, widget, lineno, 0, line_length, widget, lines))
            code_box.tag_bind(
                'line{0}'.format(line_count),
                '<Leave>',
                lambda event, widget=code_box, lineno=line_count,
                line_length=len(line), opt_widget=None,
                lines=additional_lines: remove_highlight(
                    event, widget, lineno, 0, line_length, widget, lines))
            if (line_count in data and 'type' in data[line_count] and
                    'func' == data[line_count]['type']):
                call_points = get_function_call_points(line_count)
                code_box.tag_unbind('line{0}'.format(line_count), '<Button-1>')
                code_box.tag_bind(
                    'line{0}'.format(line_count),
                    '<Button-1>',
                    lambda event, lineno=line_count, cp=call_points:
                    tag_function_calls(event, lineno, cp))
            if (line_count in data and 'type' in data[line_count] and
                    'loop' == data[line_count]['type']):
                code_box.tag_unbind('line{0}'.format(line_count), '<Button-1>')
                code_box.tag_bind(
                    'line{0}'.format(line_count),
                    '<Button-1>',
                    lambda event, lineno=line_count: tag_loops(event, lineno))
        line_count += 1


def correct_mangled_variables():
    global executed_code
    for call, evaluated in executed_code.iteritems():
        scope = get_scope(evaluated['lineno'])
        for key, value in evaluated['values'].iteritems():
            try:
                correct_value = variable_values_per_line[call-1][scope][key]
                correct_result = variable_values_per_line[call][scope][key]
                if value != correct_value:
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


def debug_loop(from_box, input_box, variable_box,
               output_box, start_scale, scale,
               tree_wrapper, tree_viewer, combobox):
    global user_code
    global scale_size
    global executed_code
    global prev_scale_setting
    global prev_start_scale_setting
    global communicationThread
    global input_event
    global successful_exit
    global scroll_position
    global rerun_event

    if exit_event.isSet():
        return
    if not DO_NOT_RUN:
        new_user_code = from_box.get(0.0, END)[:-1]

        if user_code != new_user_code:
            highlight_code(from_box)
            try:
                if communicationThread is None:
                    user_code = new_user_code
                    with open(FILE_NAME, "w") as code_file:
                        code_file.write(user_code)
                        code_file.close()
                    communicationThread = CommunicationThread('user_code.py')
                    communicationThread.start()
            except:
                pass
        elif (scale.get() != prev_scale_setting or 
                start_scale.get() != prev_start_scale_setting):
            prev_scale_setting = scale.get()
            start_scale.config(to=prev_scale_setting)
            prev_start_scale_setting = start_scale.get()
            reset_boxes(new_user_code, variable_box, output_box)
            reset_objects()
            if executed_code is not None:
                display_executed_code(executed_code, from_box,
                                      variable_box, output_box,
                                      start_scale.get(), scale.get())
            display_objects(tree_wrapper, tree_viewer, combobox)
            if scroll_position is not None:
                scrolled_text_pair.right.configure(
                    yscrollcommand=scrolled_text_pair.on_textscroll)
                scrolled_text_pair.right.yview('moveto', scroll_position[0])
                scroll_position = None

        if communicationThread is not None and not communicationThread.isAlive():
            input_event.clear()
            communicationThread = None
            if successful_exit:
                successful_exit = False
                reset_boxes(new_user_code, variable_box,
                            output_box)
                tag_lines(from_box)
                scale_size = len(executed_code)
                scale.config(to=scale_size)
                scale.set(scale_size)
                prev_scale_setting = scale_size
                start_scale.config(to=scale_size)
                prev_start_scale_setting = start_scale.get()
                display_executed_code(executed_code, from_box,
                                      variable_box, output_box, start_scale.get(),
                                      scale_size)
                display_objects(tree_wrapper, tree_viewer, combobox)
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

    root.after(500, debug_loop, from_box, input_box,
               variable_box, output_box, start_scale, scale,
               tree_wrapper, tree_viewer, combobox)


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
        code_box = Text(code_frame, foreground='white', background='gray15', height=55)
        code_box.tag_configure('Token.Keyword', foreground='orange red')
        code_box.tag_configure('Token.Operator', foreground='orange red')
        code_box.tag_configure('Token.Name.Class', foreground='green yellow')
        code_box.tag_configure('Token.Name.Function', foreground='green yellow')
        code_box.tag_configure('Token.Literal.Number.Integer',
                                foreground='medium orchid')
        code_box.tag_configure('Token.Name.Builtin', foreground='medium turquoise')
        code_box.tag_configure('Token.Literal.String.Single',
                                foreground='yellow')
        code_box.tag_configure('Token.Name.Builtin.Pseudo',
                                foreground='orange')
        code_box.tag_configure('HIGHLIGHT', background='gray5')
        if os.path.isfile(FILE_NAME):
            with open(FILE_NAME, 'r') as code_file:
                lines = code_file.readlines()
                for line in lines:
                    code_box.insert(INSERT, line)
                code_file.close()
        code_box.pack(side=TOP, fill=Y)

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

        root.after(500, debug_loop, code_box, input_box,
                   variable_box, output_box, start_execution_step,
                   execution_step, tree_wrapper,
                   tree_viewer, combobox)

    def __init__(self, master=None):
        Frame.__init__(self, master)
        self.pack()
        self.createWidgets()


app = Application(master=root)
app.mainloop()
root.destroy()
