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


def combine_all_data(target_data, from_data):
    for lineno in from_data.keys():
        combine_target_data(lineno, target_data, from_data)
        for s in from_data[lineno]['expressions']:
            add_string(target_data, lineno, s)
        if 'type' in from_data[lineno]:
            target_data[lineno]['type'] = from_data[lineno]['type']
        if 'assigned' in from_data[lineno]:
            target_data[lineno]['assigned'] = from_data[lineno]['assigned']


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
