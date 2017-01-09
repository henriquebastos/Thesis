def setup_data(data, lineno):
    if lineno not in data:
        data[lineno] = {}


def setup_expressions(data, lineno):
    setup_data(data, lineno)
    if 'expressions' not in data[lineno]:
        data[lineno]['expressions'] = []


def add_string(data, lineno, s):
    setup_expressions(data, lineno)
    if s not in data[lineno]['expressions']:
        data[lineno]['expressions'].append(s)


def combine_data(lineno, target_data, from_data):
    combine_target_data(lineno, target_data, from_data)
    for s in from_data[lineno]['expressions']:
        add_string(target_data, lineno, s)
    if 'type' in from_data[lineno]:
        target_data[lineno]['type'] = from_data[lineno]['type']
    if 'assigned' in from_data[lineno]:
        target_data[lineno]['assigned'] = from_data[lineno]['assigned']
    if 'function_lines' in from_data[lineno]:
            target_data[lineno]['function_lines'] = \
                from_data[lineno]['function_lines']
    if 'additional_lines' in from_data[lineno]:
            target_data[lineno]['additional_lines'] = \
                from_data[lineno]['additional_lines']


def combine_all_data(target_data, from_data):
    for lineno in from_data.keys():
        combine_target_data(lineno, target_data, from_data)
        for s in from_data[lineno]['expressions']:
            add_string(target_data, lineno, s)
        if 'type' in from_data[lineno]:
            target_data[lineno]['type'] = from_data[lineno]['type']
        if 'assigned' in from_data[lineno]:
            target_data[lineno]['assigned'] = from_data[lineno]['assigned']
        if 'function_lines' in from_data[lineno]:
            target_data[lineno]['function_lines'] = \
                from_data[lineno]['function_lines']
        if 'additional_lines' in from_data[lineno]:
            target_data[lineno]['additional_lines'] = \
                from_data[lineno]['additional_lines']


def combine_target_data(lineno, data, from_data):
    setup_data(data, lineno)
    if 'targets' in from_data[lineno]:
        if 'targets' not in data[lineno]:
            data[lineno]['targets'] = []
        for target in from_data[lineno]['targets']:
            data[lineno]['targets'].append(target)


def add_targets_to_data(lineno, data, from_data):
    setup_data(data, lineno)
    if 'targets' not in data[lineno]:
        data[lineno]['targets'] = []
    for target in from_data[lineno]['expressions']:
        data[lineno]['targets'].append(target)


def add_string_to_data(lineno, data, s):
    add_string(data, lineno, s)


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


def setup_function_lines(data):
    if 'function_lines' not in data:
        data['function_lines'] = {}


def add_function_def(data, name, lineno):
    setup_function_lines(data)
    data['function_lines'][name] = [lineno]


def add_function_line(data, name, lineno):
    data['function_lines'][name].append(lineno)


def setup_additional_lines(data, lineno):
    setup_data(data, lineno)
    if 'additional_lines' not in data[lineno]:
        data[lineno]['additional_lines'] = []


def add_additiona_lines(data, lineno, func_name):
    setup_additional_lines(data, lineno)
    if func_name not in data[lineno]['additional_lines']:
        data[lineno]['additional_lines'].append(func_name)
        # for line in data['function_lines'][func_name]:
        #     data[lineno]['additional_lines'].append(line)


def combine_variable_scopes(target_scope, from_scope):
    for key, value in from_scope.items():
        if key not in target_scope:
            target_scope[key] = value
        else:
            for variable in value:
                if variable not in target_scope[key]:
                    target_scope[key].append(variable)
