def setup_data(data, lineno):
    if lineno not in data:
        data[lineno] = {}


def setup_expressions(data, lineno):
    setup_data(data, lineno)
    if 'expressions' not in data[lineno]:
        data[lineno]['expressions'] = []


def setup_additional_lines(data, lineno):
    setup_data(data, lineno)
    if 'additional_lines' not in data[lineno]:
        data[lineno]['additional_lines'] = []


def setup_function_lines(data):
    if 'function_lines' not in data:
        data['function_lines'] = {}


def setup_loop_lines(data):
    if 'loop_lines' not in data:
        data['loop_lines'] = {}


def add_string(data, lineno, s):
    setup_expressions(data, lineno)
    if s not in data[lineno]['expressions']:
        data[lineno]['expressions'].append(s)


def add_targets_to_data(lineno, data, from_data):
    setup_data(data, lineno)
    if 'targets' not in data[lineno]:
        data[lineno]['targets'] = []
    for target in from_data[lineno]['expressions']:
        data[lineno]['targets'].append(target)


# Update walk_ast to use add String
def add_string_to_data(lineno, data, s):
    add_string(data, lineno, s)


def add_function_def(data, name, lineno):
    setup_function_lines(data)
    data['function_lines'][name] = [lineno]


def add_function_line(data, name, lineno):
    data['function_lines'][name].append(lineno)


def add_loop_def(data, lineno):
    setup_loop_lines(data)
    data['loop_lines'][lineno] = [lineno]


def add_loop_line(data, loop_line, lineno):
    data['loop_lines'][loop_line].append(lineno)


def add_additional_lines(data, lineno, func_name):
    setup_additional_lines(data, lineno)
    if func_name not in data[lineno]['additional_lines']:
        data[lineno]['additional_lines'].append(func_name)


def add_class(data, classname):
    if 'classes' not in data:
        data['classes'] = {}
    data['classes'][classname] = {}


def add_function_to_class(target_data, from_data, classname):
    if 'function_lines' in from_data:
        for func, lines in from_data['function_lines'].items():
            if func not in target_data['classes'][classname]:
                if 'functions' not in target_data['classes'][classname]:
                    target_data['classes'][classname]['functions'] = {}
                target_data['classes'][classname]['functions'][func] = lines


# TODO: remove functions from function_lines now that they are in class lines. check highlights


def add_variables_to_class(target_data, from_variable_scope, classname):
    for scope, variables in from_variable_scope.items():
        for variable in variables:
            if 'self.' in variable:
                if 'variables' not in target_data['classes'][classname]:
                    target_data['classes'][classname]['variables'] = []
                if variable not in target_data['classes'][classname]['variables']:
                    target_data['classes'][classname]['variables'].append(variable)


def combine_expressions(lineno, target_data, from_data):
    if lineno in from_data and 'expressions' in from_data[lineno]:
        for s in from_data[lineno]['expressions']:
            add_string(target_data, lineno, s)


def combine_type(lineno, target_data, from_data):
    if lineno in from_data and 'type' in from_data[lineno]:
        target_data[lineno]['type'] = from_data[lineno]['type']


def combine_assigned(lineno, target_data, from_data):
    if lineno in from_data and 'assigned' in from_data[lineno]:
        target_data[lineno]['assigned'] = from_data[lineno]['assigned']
    if lineno in from_data and 'assigned_expressions' in from_data[lineno]:
        target_data[lineno]['assigned_expressions'] = from_data[lineno]['assigned_expressions']


def combine_function_lines(lineno, target_data, from_data):
    if 'function_lines' in from_data:
        if 'function_lines' not in target_data:
            target_data['function_lines'] = from_data['function_lines']
        else:
            for func, lines in from_data['function_lines'].items():
                if func not in target_data['function_lines']:
                    target_data['function_lines'][func] = lines


def combine_loop_lines(lineno, target_data, from_data):
    if 'loop_lines' in from_data:
        if 'loop_lines' not in target_data:
            target_data['loop_liens'] = from_data['loop_lines']
        else:
            for lineno, lines, in from_data['loop_lines'].items():
                if lineno not in target_data['loop_lines']:
                    target_data['loop_lines'][lineno] = lines


def combine_additional_lines(lineno, target_data, from_data):
    if lineno in from_data and 'additional_lines' in from_data[lineno]:
        target_data[lineno]['additional_lines'] = \
            from_data[lineno]['additional_lines']


def combine_classes(target_data, from_data):
    if 'classes' in from_data:
        if 'classes' not in target_data:
            target_data['classes'] = from_data['classes']
        else:
            for func, lines in from_data['classes'].items():
                if func not in target_data['classes']:
                    target_data['classes'][func] = lines


def combine_name(lineno, target_data, from_data):
    if lineno in from_data and 'name' in from_data[lineno]:
        target_data[lineno]['name'] = from_data[lineno]['name']


def combine_data(lineno, target_data, from_data):
    combine_target_data(lineno, target_data, from_data)
    combine_expressions(lineno, target_data, from_data)
    combine_type(lineno, target_data, from_data)
    combine_assigned(lineno, target_data, from_data)
    combine_function_lines(lineno, target_data, from_data)
    combine_loop_lines(lineno, target_data, from_data)
    combine_additional_lines(lineno, target_data, from_data)
    combine_classes(target_data, from_data)
    combine_name(lineno, target_data, from_data)


def combine_all_data(target_data, from_data):
    for lineno in from_data.keys():
        combine_data(lineno, target_data, from_data)


def combine_target_data(lineno, data, from_data):
    setup_data(data, lineno)
    if lineno in from_data and 'targets' in from_data[lineno]:
        if 'targets' not in data[lineno]:
            data[lineno]['targets'] = []
        for target in from_data[lineno]['targets']:
            data[lineno]['targets'].append(target)


def combine_variable_scopes(target_scope, from_scope):
    for key, value in from_scope.items():
        if key not in target_scope:
            target_scope[key] = value
        else:
            for variable in value:
                if variable not in target_scope[key]:
                    target_scope[key].append(variable)


def remove_empty_string(data, lineno):
    if 'expressions' in data[lineno] and '' in data[lineno]['expressions']:
        data[lineno]['expressions'].remove('')
    if 'targets' in data[lineno] and '' in data[lineno]['targets']:
        data[lineno]['targets'].remove('')


def set_type(data, lineno, data_type):
    setup_data(data, lineno)
    data[lineno]['type'] = data_type


def set_assign(data, lineno, assigned):
    setup_data(data, lineno)
    if 'assigned' not in data[lineno]:
        data[lineno]['assigned'] = []
    data[lineno]['assigned'].append(assigned)


def set_assigned_expressions(data, lineno, assigned, expressions):
    if 'assigned_expressions' not in data[lineno]:
        data[lineno]['assigned_expressions'] = {}
    data[lineno]['assigned_expressions'][assigned] = expressions


def set_name(data, lineno, name):
    setup_data(data, lineno)
    data[lineno]['name'] = name
