#!/usr/bin/python
from __future__ import print_function

import os

# MultipleCmd runs jobs in forked process in parallel
# max_in_flight specifies how many jobs can run in parallel
class MultipleCmd:
  def __init__(self, max_in_flight):
    self.max_in_flight = max_in_flight
    self.jobs = []

  # add_job adds a job to a queue.
  # cmd(arg) will be called in a forked process
  # callback(exit_code, cmd, arg, context) will be called in parent process
  #   after the child process exits. exit_code is an exit code of the
  #   chuld process
  # context may be used to pass MultipleCmd object, so the callback
  #   can schedule new jobs
  def add_job(self, cmd, arg, callback = None, context = None):
    self.jobs.append({'cmd': cmd, 'arg': arg, 'callback': callback,
      'context': context})

  # run the job queue creating subprocess per job.
  # will block until the queue is finished
  def run(self):
    while len(self.jobs):
      self._spawn_new_jobs()
      self._wait_job_finish()

  #creates new jobs up to in_flight limit
  def _spawn_new_jobs(self):
    in_flight = 0
    # find a job to run & run it
    for job in self.jobs:
      if 'pid' in job:
        in_flight += 1
        continue                            # skip if job is already running
      if in_flight == self.max_in_flight:
        return                              # can't run a new job

      pid = os.fork()                       # fork to run a job
      if pid < 0:
        raise Exception('Fork failed')
      elif pid >0:
        job['pid'] = pid                    # remember the pid of job we ran
        in_flight += 1
      else:
        exit(job['cmd'](job['arg']))        # run the job (in child process)

  # wait for a job to finish & call the callback
  def _wait_job_finish(self):
    pid, status = os.wait()                 # wait for some job to finish
    exit_code = status >> 8
    # find finished job in the queue and delete it
    for index, job in enumerate(self.jobs):
      if pid == job['pid']:
        if job['callback']:
          job['callback'](exit_code, job['cmd'], job['arg'], job['context'])
        del self.jobs[index]
        break

if __name__ == '__main__':
  import time
  import random


  def f(arg):
    i, comment = arg
    random.seed(i)
    s = random.randint(0, 10)
    print(i, comment)
    time.sleep(s)
    return i

  def done(exit_code,func, arg, ctx):
    print(exit_code)
    if ctx['i'] < 10:
      ctx['mcmd'].add_job(f, (ctx['i'], ':' + '*' * ctx['i']), done, ctx)
      ctx['i'] += 1

  ctx = {}
  ctx['mcmd'] = MultipleCmd(4)
  ctx['i'] = 0
  while ctx['i'] < 4:
    ctx['mcmd'].add_job(f, (ctx['i'], ':' + '*' * ctx['i']), done, ctx)
    ctx['i'] += 1
  ctx['mcmd'].run()
