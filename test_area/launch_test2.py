#!/usr/bin/env python

import sys
import os
import time
import pty

def my_pty_fork():

  # fork this script
  try:
    ( child_pid, fd ) = pty.fork()    # OK
    #~ child_pid, fd = os.forkpty()      # OK
  except OSError as e:
    print str(e)

  #~ print "%d - %d" % (fd, child_pid)
  # NOTE - unlike OS fork; in pty fork we MUST use the fd variable
  #   somewhere (i.e. in parent process; it does not exist for child)
  # ... actually, we must READ from fd in parent process...
  #   if we don't - child process will never be spawned!

  if child_pid == 0:
    print "In Child Process: PID# %s" % os.getpid()
    # note: fd for child is invalid (-1) for pty fork!
    #~ print "%d - %d" % (fd, child_pid)

    # the os.exec replaces the child process
    sys.stdout.flush()
    try:
      #Note: "the first of these arguments is passed to the new program as its own name"
      # so:: "python": actual executable; 
      # "ThePythonProgram": name of executable in process list (`ps axf`); 
      #"pyecho.py": first argument to executable..
      os.execlp('python', 'python', 'test_code.py')
    except:
      print "Cannot spawn execlp..."
  else:
    print "In Parent Process: PID# %s" % os.getpid()
    # MUST read from fd; else no spawn of child!
    sys.stdout.write(os.read(fd, 1000)) # in fact, this line prints out the "In Child Process..." sentence above!
    time.sleep(1)
    # i = 0
    # while i < 10:
    #   os.write(fd,'s\n')
    #   output = os.read(fd, 10000)
    #   output += os.read(fd, 10000)
    #   sys.stdout.write(output)
    #   time.sleep(1)
    #   i += 1

    print os.read(fd, 1000)  
    os.write(fd,"s\n")
    print os.read(fd, 1000)        # message one
    # time.sleep(2)
    # os.write(fd,"s\n")
    # print os.read(fd, 10000)      # pyecho starting...\n MESSAGE ONE
    # time.sleep(2)
    # os.write(fd,"s\n")
    # print os.read(fd, 10000)      # pyecho starting...\n MESSAGE ONE
    # time.sleep(2)
    # os.write(fd,"s\n")
    # print os.read(fd, 10000)      # pyecho starting...\n MESSAGE ONE
    # time.sleep(2)
    # os.write(fd,"s\n")
    # print os.read(fd, 10000)      # pyecho starting...\n MESSAGE ONE
    # time.sleep(2)
    # print os.read(fd, 10000)      # message two \n MESSAGE TWO
    # uncomment to lock (can exit with Ctrl-C)
    #~ while True:
      #~ print os.read(fd, 10000)


if __name__ == "__main__":
    my_pty_fork()