from Tkinter import *
import os
import ScrolledText as ST
import threading

from pygments import lex
from pygments.lexers import PythonLexer

import communicate as Communicate

# RENAME to Environment

name = 'Noah\'s Live Programming Environment'
root = Tk(screenName=name, baseName=name, className=name)
user_code = ''
user_inputs = []
FILE_NAME = 'user_code.py'
scale_size = 0
prev_scale_setting = 0
executed_code = None
data = None
communicationThread = None
input_event = threading.Event()
highlight_map = {}
additional_lines_call_point = None


def display_executed_code(executed_code, code_box, executed_code_box,
                          variable_box, output_box, total):
    global highlight_map
    highlight_map = {}
    display_map = {}
    tab_count = 0
    for key, value in executed_code.iteritems():
        display_line = ''
        if total >= 0:
            if 'result' in value:
                display_line += '{0}'.format(value['result'])
                if 'assigned' in value:
                    variable_box.insert(INSERT, value['result'] + '\n')
                if 'print' in value:
                    output_box.insert(INSERT, value['result'] + '\n')
            else:
                no_comma = True
                for k, v in value['values'].iteritems():
                    if no_comma:
                        no_comma = False
                    else:
                        display_line += ', '
                    display_line += '{0}={1}'.format(k, v)
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
            highlight_map[key]['start'] = current_length + len(tabs[current_length:])
        else:
            # Display executed code at the correct indentation
            display_map[value['lineno']] = tabs + display_line
            # Mark lines start point
            highlight_map[key]['start'] = current_length + len(tabs)
        highlight_map[key]['lineno'] = value['lineno']
        highlight_map[key]['end'] = len(display_map[value['lineno']])
        tab_count += 1

    for key, value in display_map.iteritems():
        executed_code_box.insert(float(key), value)
    for key, value in highlight_map.iteritems():
        executed_code_box.tag_add('call{0}'.format(key),
                                  '{0}.{1}'.format(value['lineno'], value['start']),
                                  '{0}.{1}'.format(value['lineno'], value['end']))
        executed_code_box.tag_bind(
            'call{0}'.format(key),
            '<Enter>',
            lambda event, widget=executed_code_box, lineno=value['lineno'],
                line_start=value['start'], line_length=value['end'],
                opt_widget=code_box: 
                    add_highlight(event, widget, lineno, line_start,
                                  line_length, opt_widget))
        executed_code_box.tag_bind(
            'call{0}'.format(key),
            '<Leave>',
            lambda event, widget=executed_code_box, lineno=value['lineno'],
                line_start=value['start'], line_length=value['end'],
                opt_widget=code_box: 
                    remove_highlight(event, widget, lineno, line_start,
                                     line_length, opt_widget))


def reset_boxes(new_user_code, executed_code_box, variable_box, output_box):
    executed_code_box.delete(0.0, END)
    variable_box.delete(0.0, END)
    output_box.delete(0.0, END)
    for i in range(len(new_user_code.split('\n'))):
        executed_code_box.insert(float(i), '\n')


def highlight_code(code_box):
    code_box.mark_set('range_start', '1.0')
    data = code_box.get('1.0', 'end-1c')
    for token, content in lex(data, PythonLexer()):
        code_box.mark_set('range_end', 'range_start + %dc' % len(content))
        code_box.tag_add(str(token), 'range_start', 'range_end')
        code_box.mark_set('range_start', 'range_end')


def tag_add_highlight(widget, line, start, length):
    widget.tag_add('HIGHLIGHT','{0}.{1}'.format(line, start),
                '{0}.{1}'.format(line, length))


def tag_remove_highlight(widget, line, start, length):
    widget.tag_remove('HIGHLIGHT','{0}.{1}'.format(line, start),
                      '{0}.{1}'.format(line, length))


def optional_add_highlights(widget, lineno, line_start, line_length,
                            lines=None):
    tag_add_highlight(widget, lineno, 0, 'end')
    if lines is not None:
        for line in lines:
            if line in additional_lines_call_point[lineno]:
                call = additional_lines_call_point[lineno][line]
                start = highlight_map[call]['start']
                end = highlight_map[call]['end']
                tag_add_highlight(widget, line, start, end)
            else:
                tag_add_highlight(widget, line, 0, line_length)


def optional_remove_highlights(widget, lineno, line_start, line_length,
                               lines=None):
    tag_remove_highlight(widget, lineno, 0, 'end')
    if lines is not None:
        for line in lines:
            if line in additional_lines_call_point[lineno]:
                call = additional_lines_call_point[lineno][line]
                start = highlight_map[call]['start']
                end = highlight_map[call]['end']
                tag_remove_highlight(widget, line, start, end)
            else:
                tag_remove_highlight(widget, line, 0, line_length)


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
        if data is not None and line_count in data and 'additional_lines' in data[line_count]:
            for func in data[line_count]['additional_lines']:
                if func in data['function_lines']:
                    for func_line in data['function_lines'][func]:
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
    def __init__(self, filename, input_field):
        threading.Thread.__init__(self)
        self.filename = filename
        self.input_field = input_field

    def run(self):
        global executed_code
        global data
        global input_event
        global user_inputs
        global additional_lines_call_point
        communicator = Communicate.main(self.filename, self.input_field,
                                        input_event, user_inputs)
        executed_code = communicator.executed_code
        data = communicator.data
        additional_lines_call_point = communicator.additional_lines_call_point


def check_input_box(input_box):
    global user_inputs
    update = False
    lines = str(input_box.get(0.0, END)[:-1])
    if len(lines) == 0:
        if len(user_inputs) > 0:
            for i in user_inputs:
                input_box.insert(INSERT, '{0}\n'.format(i))
    else:
        lines = lines.split('\n')[:-1]
        if len(user_inputs) != len(lines):
            input_box.delete(0.0, END)
            for i in user_inputs:
                input_box.insert(INSERT, '{0}\n'.format(i))
        else:
            i = 0
            while i < len(lines):
                if user_inputs[i] != lines[i]:
                    user_inputs[i] = lines[i]
                    update = True
                i += 1
    return update


def debug_loop(from_box, executed_code_box, input_box, variable_box,
               output_box, scale, input_field):
    global user_code
    global scale_size
    global executed_code
    global prev_scale_setting
    global communicationThread
    global input_event
    new_user_code = from_box.get(0.0, END)[:-1]

    if user_code != new_user_code:
        highlight_code(from_box)
        tag_lines(from_box, executed_code_box)
        user_code = new_user_code
        with open(FILE_NAME, "w") as code_file:
            code_file.write(user_code)
        try:
            if communicationThread is None:
                communicationThread = CommunicationThread('user_code.py', input_field)
                communicationThread.start()
        except:
            pass
    elif scale.get() < scale_size or scale.get() != prev_scale_setting:
        prev_scale_setting = scale.get()
        reset_boxes(new_user_code, executed_code_box, variable_box, output_box)
        display_executed_code(executed_code, from_box, executed_code_box, variable_box,
                              output_box, scale.get())

    if communicationThread is not None and not communicationThread.isAlive():
        input_event.clear()
        communicationThread = None
        reset_boxes(new_user_code, executed_code_box, variable_box,
                    output_box)
        tag_lines(from_box, executed_code_box)
        scale.config(to=len(executed_code))
        scale.set(len(executed_code))
        scale_size = len(executed_code)
        prev_scale_setting = scale_size
        display_executed_code(executed_code, from_box, executed_code_box,
                              variable_box, output_box, scale_size)

    if len(input_field.get()) > 0:
        input_event.set()

    if check_input_box(input_box):
        user_code = ''

    root.after(500, debug_loop, from_box, executed_code_box, input_box,
               variable_box, output_box, scale, input_field)


class Application(Frame):
    def get_input(self):
        print "hi there, everyone!"

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
        output_frame = Frame(bottom_frame)

        main_frame.pack()
        middle_frame.pack(side=TOP)
        menu_frame.pack(side=TOP)
        code_frame.pack(side=LEFT)
        executed_code_frame.pack(side=LEFT)
        input_frame.pack(side=LEFT)
        bottom_frame.pack(side=BOTTOM)
        variable_frame.pack(side=LEFT)
        output_frame.pack(side=LEFT)

        QUIT = Button(menu_frame)
        QUIT["text"] = "QUIT"
        QUIT["command"] = self.quit
        QUIT.pack(side=LEFT)

        execution_step = Scale(menu_frame, orient=HORIZONTAL)
        execution_step.pack(side=LEFT)

        input_label = Label(menu_frame, text='Input')
        input_label.pack(side=LEFT)

        input_field = Entry(menu_frame)
        input_field.pack(side=LEFT)

        # input_button = Button(menu_frame)
        # input_button["text"] = "Enter",
        # input_button["command"] = self.get_input
        # input_button.pack(side=LEFT)

        code_box = ST.ScrolledText(code_frame, foreground='white',
                                   background='gray15')
        code_box.tag_configure('Token.Keyword', foreground='red')
        code_box.tag_configure('Token.Operator', foreground='red')
        code_box.tag_configure('Token.Name.Function', foreground='green')
        code_box.tag_configure('Token.Literal.Number.Integer',
                               foreground='purple')
        code_box.tag_configure('Token.Name.Builtin', foreground='cyan')
        code_box.tag_configure('Token.Literal.String.Single',
                               foreground='yellow')
        code_box.tag_configure('HIGHLIGHT', background='gray5')
        if os.path.isfile(FILE_NAME):
            with open(FILE_NAME, 'r') as code_file:
                lines = code_file.readlines()
                for line in lines:
                    code_box.insert(INSERT, line)
        code_box.pack({'side': 'left'})

        executed_code_box = Text(executed_code_frame, foreground='white',
                                 background='gray15', wrap=NONE)
        executed_code_box.tag_configure('HIGHLIGHT', background='gray5')
        executed_code_box.pack({'side': 'left'})

        input_box = Text(input_frame)
        input_box.pack({'side': 'left'})

        variable_box = Text(variable_frame)
        variable_box.pack({'side': 'left'})

        output_box = Text(output_frame)
        output_box.pack({'side': 'left'})

        root.after(500, debug_loop, code_box, executed_code_box, input_box,
                   variable_box, output_box, execution_step, input_field)

    def __init__(self, master=None):
        Frame.__init__(self, master)
        self.pack()
        self.createWidgets()


app = Application(master=root)
app.mainloop()
root.destroy()

# tkFont
# tkMessageBox
# tkSimpleDialog
# Tkdnd
# TkDND
