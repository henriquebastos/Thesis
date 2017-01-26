from Tkinter import *
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

name = 'Noah\'s Live Programming Environment'
root = Tk(screenName=name, baseName=name, className=name)
user_code = ''
user_inputs = []
FILE_NAME = 'user_code.py'
INPUT_FILE_NAME = 'user_input.txt'
scale_size = 0
prev_scale_setting = 0
executed_code = None
data = None
variable_scope = None
variable_values = {}
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


def get_function_call_lineno(call, lineno):
    for line, values in additional_lines_call_point.iteritems():
        for additional_line, additional_call in values.iteritems():
            if lineno == additional_line and call == additional_call:
                return line


def display_variables(variable_box):
    global variable_scope
    global variable_values

    # print '\n\n\n\nVariable Values: '
    # for k,v in variable_values.items():
    #     print '\t{0}: {1}'.format(k,v)
    # print 'Variable Scope:'
    # for k,v in variable_scope.items():
    #     print '\t{0}: {1}'.format(k,v)
    # print 'Executed Code: '
    # for k,v in executed_code.items():
    #     print '\t{0}: {1}'.format(k,v)
    # print 'DATA: '
    # for k,v in data.items():
    #     print '\t{0}: {1}'.format(k,v)
    # print 'Generic Objects:'
    # for k,v in generic_objects.items():
    #     print '\t{0}: {1}'.format(k,v)

    variable_box.delete(0.0, END)
    for func, variables in variable_scope.items():
        variables_line = ''
        for variable in variables:
            if func in variable_values and variable in variable_values[func]:
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


def set_variable_value(scope, variable, result):
    global variable_values
    if scope not in variable_values:
        variable_values[scope] = {}
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
                                                         instance_id)
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
            main_object.add_variable(new_variable, result)


def check_function_variables_arguments(lineno, values):
    if lineno in current_object_lines:
        for k,v in values.iteritems():
            if current_generic_object is not None and current_function is not None:
                current_generic_object.add_function_variable(current_function, k, v)


def display_executed_code(executed_code, code_box, executed_code_box,
                          variable_box, output_box, total):
    global highlight_map
    global current_generic_object
    global current_object_lines
    global current_function
    highlight_map = {}
    display_map = {}
    tab_count = 0

    for key, value in executed_code.iteritems():
        display_line = ''
        if total >= 0:
            if 'result' in value:
                display_line += '{0}'.format(value['result'])
                if 'assigned' in value:
                    scope = get_scope(value['lineno'])
                    variable = value['result'].split('=')[0]
                    result = value['result'].split('=')[1]
                    set_variable_value(scope, variable, result)
                    if not check_for_new_object(scope, variable, result):
                        check_add_to_object(scope, variable, value['result'],
                                            value['lineno'])
                    else:
                        check_modify_object(variable, value['result'], value['lineno'])
                if 'print' in value:
                    output_box.insert(INSERT, value['result'] + '\n')
                # Add functions for classes
                # if lineno of value has additional lines in data[lineno]
                if (value['lineno'] in data and
                        'additional_lines' in data[value['lineno']]):
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
            else:
                no_comma = True
                scope = get_scope(value['lineno'])
                for k, v in value['values'].iteritems():
                    if no_comma:
                        no_comma = False
                    else:
                        display_line += ', '
                    display_line += '{0}={1}'.format(k, v)
                    set_variable_value(scope, k, v)
                check_function_variables_arguments(value['lineno'], value['values'])
            display_variables(variable_box)
        total -= 1
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

    # print '\nHIGHLIGHT_MAP: {0}'.format(highlight_map)
    # print '\nADDITIONAL_LINES_CALL_POINT: {0}'.format(additional_lines_call_point)

    for key, value in display_map.iteritems():
        executed_code_box.insert(float(key), value)

    for key, value in highlight_map.iteritems():
        calling_lines = []
        calling_line = get_function_call_lineno(key, value['lineno'])
        if calling_line is not None:
            calling_lines.append(calling_line)
        executed_code_box.tag_add('call{0}'.format(key),
                                  '{0}.{1}'.format(value['lineno'],
                                                   value['start']),
                                  '{0}.{1}'.format(value['lineno'],
                                                   value['end']))
        executed_code_box.tag_bind(
            'call{0}'.format(key),
            '<Enter>',
            lambda event, widget=executed_code_box, lineno=value['lineno'],
            line_start=value['start'], line_length=value['end'],
            opt_widget=code_box, lines=calling_lines:
                add_highlight(event, widget, lineno, line_start,
                              line_length, opt_widget, lines))
        executed_code_box.tag_bind(
            'call{0}'.format(key),
            '<Leave>',
            lambda event, widget=executed_code_box, lineno=value['lineno'],
            line_start=value['start'], line_length=value['end'],
            opt_widget=code_box, lines=calling_lines:
                remove_highlight(event, widget, lineno, line_start,
                                 line_length, opt_widget, lines))


def get_classes():
    classes = []
    if 'classes' in data:
        classes = data['classes'].keys()
    return classes


def display_objects(tree_wrapper, tree_viewer):
    tree_viewer.clearTree()
    tree_wrapper.generic_objects = generic_objects
    tree_wrapper.classes = get_classes()
    trees = []
    root_obj = None

    for obj in generic_objects.values():
        trees.append(treeview.GenericTree(tree_viewer, obj))
    for instance_id in generic_objects.keys():
        appears_as_child = False
        this_tree = None
        for tree in trees:
            if instance_id != tree.generic_object.instance_id:
                for value in tree.generic_object.variables.values():
                    if instance_id in value:
                        appears_as_child = True
            else:
                this_tree = tree
        if not appears_as_child:
            root_obj = this_tree
    root_obj.view()


def reset_boxes(new_user_code, executed_code_box, variable_box, output_box):
    global variable_values
    executed_code_box.delete(0.0, END)
    variable_box.delete(0.0, END)
    output_box.delete(0.0, END)
    variable_values = {}
    for i in range(len(new_user_code.split('\n'))):
        executed_code_box.insert(float(i), '\n')


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
    for token, content in lex(data, PythonLexer()):
        code_box.mark_set('range_end', 'range_start + %dc' % len(content))
        code_box.tag_add(str(token), 'range_start', 'range_end')
        code_box.mark_set('range_start', 'range_end')


def tag_add_highlight(widget, line, start, length):
    widget.tag_add('HIGHLIGHT', '{0}.{1}'.format(line, start),
                   '{0}.{1}'.format(line, length))


def tag_remove_highlight(widget, line, start, length):
    widget.tag_remove('HIGHLIGHT', '{0}.{1}'.format(line, start),
                      '{0}.{1}'.format(line, length))


def optional_add_highlights(widget, lineno, line_start, line_length,
                            lines=None):
    tag_add_highlight(widget, lineno, 0, 'end')
    if lines is not None:
        for line in lines:
            if (lineno in additional_lines_call_point and
                    line in additional_lines_call_point[lineno]):
                call = additional_lines_call_point[lineno][line]
                if call in highlight_map:
                    start = highlight_map[call]['start']
                    end = highlight_map[call]['end']
                    tag_add_highlight(widget, line, start, end)
            else:
                tag_add_highlight(widget, line, 0, 'end')


def optional_remove_highlights(widget, lineno, line_start, line_length,
                               lines=None):
    tag_remove_highlight(widget, lineno, 0, 'end')
    if lines is not None:
        for line in lines:
            if (lineno in additional_lines_call_point and
                    line in additional_lines_call_point[lineno]):
                call = additional_lines_call_point[lineno][line]
                if call in highlight_map:
                    start = highlight_map[call]['start']
                    end = highlight_map[call]['end']
                    tag_remove_highlight(widget, line, start, end)
            else:
                tag_remove_highlight(widget, line, 0, 'end')


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


def tag_lines(code_box, executed_code_box):
    global data
    user_code = code_box.get('0.0', 'end-1c')
    lines = str(user_code).split('\n')
    line_count = 1
    for line in lines:
        code_box.tag_add('line{0}'.format(line_count),
                         '{0}.0'.format(line_count),
                         '{0}.{1}'.format(line_count, len(line)))
        additional_lines = []
        if (data is not None and line_count in data and
                'additional_lines' in data[line_count]):
            for name in data[line_count]['additional_lines']:
                if '.' in name:
                    name = name.split('.')[-1]

                if name in data['function_lines']:
                    for func_line in data['function_lines'][name]:
                        additional_lines.append(func_line)
                elif ('classes' in data and name in data['classes'] and
                        '__init__' in data['classes'][name]['functions']):
                    for func_line in data['classes'][name]['functions']['__init__']:
                        additional_lines.append(func_line)

        code_box.tag_bind(
            'line{0}'.format(line_count),
            '<Enter>',
            lambda event, widget=code_box, lineno=line_count,
            line_length=len(line), opt_widget=executed_code_box,
            lines=additional_lines: add_highlight(
                event, widget, lineno, 0, line_length, opt_widget, lines))
        code_box.tag_bind(
            'line{0}'.format(line_count),
            '<Leave>',
            lambda event, widget=code_box, lineno=line_count,
            line_length=len(line), opt_widget=executed_code_box,
            lines=additional_lines: remove_highlight(
                event, widget, lineno, 0, line_length, opt_widget, lines))

        line_count += 1


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
                reset_objects()
                successful_exit = True

        except Exception as e:
            successful_exit = False
            self.stop()

    def stop(self):
        self.stop_event.set()


def check_for_new_input(input_box):
    global user_inputs
    # By removing the last line split, this forces the user to hit enter after
    # each of their line inputs. Leaving an empty line at the bottom of the
    # input box
    lines = str(input_box.get(0.0, END)[:-1]).split('\n')[:-1]
    if len(lines) > len(user_inputs):
        if lines[len(user_inputs)] != '':
            user_inputs.append(lines[len(user_inputs)])
            input_event.set()
            with open(INPUT_FILE_NAME, "w") as input_file:
                for user_input in user_inputs:
                    input_file.write('{0}\n'.format(user_input))


def input_box_has_changes(input_box):
    global user_inputs
    has_changed = False
    lines = str(input_box.get(0.0, END)[:-1]).split('\n')[:-1]
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
    return has_changed


def debug_loop(from_box, executed_code_box, input_box, variable_box,
               output_box, scale, scrolled_text_pair, tree_wrapper,
               tree_viewer):
    global user_code
    global scale_size
    global executed_code
    global prev_scale_setting
    global communicationThread
    global input_event
    global scroll_position
    global rerun_event

    if exit_event.isSet():
        return

    new_user_code = from_box.get(0.0, END)[:-1]

    if user_code != new_user_code:
        scroll_position = scrolled_text_pair.scrollbar.get()
        scrolled_text_pair.right.configure(yscrollcommand=None, state=NORMAL)
        highlight_code(from_box)
        tag_lines(from_box, executed_code_box)
        user_code = new_user_code
        with open(FILE_NAME, "w") as code_file:
            code_file.write(user_code)
        try:
            if communicationThread is None:
                communicationThread = CommunicationThread('user_code.py')
                communicationThread.start()
        except:
            pass
    # elif scale.get() < scale_size or scale.get() != prev_scale_setting:
    elif scale.get() != prev_scale_setting:
        scroll_position = scrolled_text_pair.scrollbar.get()
        scrolled_text_pair.right.configure(yscrollcommand=None, state=NORMAL)
        prev_scale_setting = scale.get()
        reset_boxes(new_user_code, executed_code_box, variable_box, output_box)
        reset_objects()
        display_executed_code(executed_code, from_box, executed_code_box,
                              variable_box, output_box, scale.get())
        display_objects(tree_wrapper, tree_viewer)
        if scroll_position is not None:
            scrolled_text_pair.right.configure(
                yscrollcommand=scrolled_text_pair.on_textscroll)
            scrolled_text_pair.right.yview('moveto', scroll_position[0])
            scroll_position = None

    if communicationThread is not None and not communicationThread.isAlive():
        input_event.clear()
        communicationThread = None
        if successful_exit:
            reset_boxes(new_user_code, executed_code_box, variable_box,
                        output_box)
            tag_lines(from_box, executed_code_box)
            scale.config(to=len(executed_code))
            scale.set(len(executed_code))
            scale_size = len(executed_code)
            prev_scale_setting = scale_size
            display_executed_code(executed_code, from_box, executed_code_box,
                                  variable_box, output_box, scale_size)
            display_objects(tree_wrapper, tree_viewer)
            if scroll_position is not None:
                scrolled_text_pair.right.configure(
                    yscrollcommand=scrolled_text_pair.on_textscroll)
                scrolled_text_pair.right.yview('moveto', scroll_position[0])
                scroll_position = None

    # Check for new input
    check_for_new_input(input_box)

    if input_box_has_changes(input_box):
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

    root.after(500, debug_loop, from_box, executed_code_box, input_box,
               variable_box, output_box, scale, scrolled_text_pair,
               tree_wrapper, tree_viewer)


class ScrolledTextPair(Frame):
    # http://stackoverflow.com/questions/32038701/python-tkinter-making-two-text-widgets-scrolling-synchronize
    '''Two Text widgets and a Scrollbar in a Frame'''

    def __init__(self, master, **kwargs):
        Frame.__init__(self, master)  # no need for super
        # Different default width
        # if 'width' not in kwargs:
        #     kwargs['width'] = 30
        # Creating the widgets
        self.left = Text(self, foreground='white', background='gray15')
        self.left.tag_configure('Token.Keyword', foreground='red')
        self.left.tag_configure('Token.Operator', foreground='red')
        self.left.tag_configure('Token.Name.Function', foreground='green')
        self.left.tag_configure('Token.Literal.Number.Integer',
                                foreground='purple')
        self.left.tag_configure('Token.Name.Builtin', foreground='cyan')
        self.left.tag_configure('Token.Literal.String.Single',
                                foreground='yellow')
        self.left.tag_configure('Token.Name.Builtin.Pseudo',
                                foreground='orange')
        self.left.tag_configure('HIGHLIGHT', background='gray5')
        if os.path.isfile(FILE_NAME):
            with open(FILE_NAME, 'r') as code_file:
                lines = code_file.readlines()
                for line in lines:
                    self.left.insert(INSERT, line)
        self.left.pack({'side': 'left'})

        self.right = Text(self, foreground='white', background='gray15',
                          wrap=NONE)
        self.right.tag_configure('HIGHLIGHT', background='gray5')
        self.right.pack({'side': 'left'})

        self.scrollbar = Scrollbar(self)
        self.scrollbar.pack(side=RIGHT, fill=Y)
        # Changing the settings to make the scrolling work
        self.scrollbar['command'] = self.on_scrollbar
        self.left['yscrollcommand'] = self.on_textscroll
        self.right['yscrollcommand'] = self.on_textscroll

    def on_scrollbar(self, *args):
        '''Scrolls both text widgets when the scrollbar is moved'''
        # print args
        self.left.yview(*args)
        self.right.yview(*args)

    def on_textscroll(self, *args):
        '''Moves the scrollbar and scrolls text widgets when the mousewheel
        is moved on a text widget'''
        # print args
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
                print 'HERE'
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
        middle_frame = Frame(main_frame, bg='grey')
        menu_frame = Frame(middle_frame)
        code_frame = Frame(middle_frame)
        executed_code_frame = Frame(middle_frame)
        input_frame = Frame(middle_frame)

        bottom_frame = Frame(main_frame, bg='grey')
        variable_frame = Frame(bottom_frame)
        output_frame = Frame(bottom_frame, width=50)
        tree_frame = Frame(bottom_frame)

        main_frame.pack()
        middle_frame.pack(side=TOP)
        menu_frame.pack(side=TOP)
        code_frame.pack(side=LEFT)
        executed_code_frame.pack(side=LEFT)
        input_frame.pack(side=LEFT)
        bottom_frame.pack(side=BOTTOM)
        variable_frame.pack(side=LEFT)
        tree_frame.pack(side=LEFT)
        output_frame.pack(side=LEFT)

        QUIT = Button(master=menu_frame, text='Quit', command=self.close_all)
        QUIT.pack(side=LEFT)

        execution_step = Scale(menu_frame, orient=HORIZONTAL)
        execution_step.pack(side=LEFT)

        paired_text_boxes = ScrolledTextPair(code_frame, foreground='white',
                                             background='gray15')
        code_box = paired_text_boxes.left
        executed_code_box = paired_text_boxes.right
        paired_text_boxes.pack()

        input_box = Text(input_frame)
        input_box.pack({'side': 'left'})

        input_button = Button(master=menu_frame, text='Input File',
                              command=lambda: self.open_input_file(input_box))
        input_button.pack(side=LEFT)

        if os.path.isfile(INPUT_FILE_NAME):
            with open(INPUT_FILE_NAME, 'r') as input_file:
                lines = input_file.readlines()
                for line in lines:
                    input_box.insert(INSERT, line)

        variable_box = Text(variable_frame)
        variable_box.tag_configure("BOLD", font=('-weight bold'))
        variable_box.pack({'side': 'left'})

        output_box = Text(output_frame)
        output_box.pack({'side': 'left'})

        tree_wrapper = treeview.GenericObjectWrapper()
        tree_viewer = TreeViewer(tree_wrapper, tree_frame) 

        root.after(500, debug_loop, code_box, executed_code_box, input_box,
                   variable_box, output_box, execution_step, paired_text_boxes,
                   tree_wrapper, tree_viewer)

    def __init__(self, master=None):
        Frame.__init__(self, master)
        self.pack()
        self.createWidgets()


app = Application(master=root)
app.mainloop()
root.destroy()
