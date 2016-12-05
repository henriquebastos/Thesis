import threading


class communicationThread(threading.Thread):
    def __init__(self, threadID, name, filename, new_user_code, executed_code_box, variable_box, output_box):
        threading.Thread.__init__(self)
        self.threadID = threadID
        self.name = name
        self.filename = filename


    def run(self):
        print "Starting " + self.name
        print_time(self.name, self.counter, 5)
        print "Exiting " + self.name

communicator = Communicate.main('user_code.py', input_field)
executed_code = communicator.executed_code
reset_boxes(new_user_code, executed_code_box, variable_box,
            output_box)
scale.config(to=len(executed_code))
scale.set(len(executed_code))
scale_size = len(executed_code)
prev_scale_setting = scale_size
display_executed_code(executed_code, executed_code_box,
                      variable_box, output_box, scale_size)
