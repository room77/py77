"""
A Python server built on Flask and gunicorn.

This server follows most Room 77 conventions and is designed to be compatible
with the Master Packaging System and behave similarly to our C++ servers. These
conventions include the following.

 - GET and POST are equivalent
 - '/' provides an RPC interface showing all available methods
 - '/_shutdown' causes the server to die with status of 15
 - '/_shutdownloop' causes the the server to die with status of 100
 - '/.ping' always returns 1
"""

__copyright__ = '2013, Room 77, Inc.'
__author__ = 'Kyle Konrad'

from functools import wraps
import os
import signal
import subprocess
import sys
from threading import Timer

from flask import Flask, jsonify, json, request, render_template, url_for
from gunicorn.app.base import Application

from pylib.base.flags import Flags


class Server(object):
  _PID_FILE_DIR = '/tmp'
  def __init__(self, name, port):
    """
    Create a server

    Args:
      name (string): unique server name
      port (int): port number to run server on
    """
    self.name = name
    self.app = Flask(self.name)
    self.port = port
    self.examples = {}

  def configure(self):
    """
    create common methods and root form
    must be called after all methods have been added
    """
    self._add_common()
    self._add_root_form()

  def run(self, workers=4):
    if getattr(Flags.ARGS, 'die', False):
      sys.exit(0)
    if Flags.ARGS.workers:
      self.pid_file ='%s/%s_gunicorn_pid' % (self._PID_FILE_DIR, self.name)
      GunicornApplication(self.app, self.port, workers=Flags.ARGS.workers,
                          pidfile=self.pid_file).run()
    else:
      self.app.run('0.0.0.0', self.port, debug=True) # run with flask in debug mode

  def rpc(self, route, required={}, example={}):
    """
    decorator for creating a route with param validation and example

    Accepts parameters query parameters (for GET)
    or form data (for POST). GET and POST behave identically

    Params must be of the form 'q={"key": "value", ...}'

    Response should be JSON containing either 'error_msg' or 'success' key
    status code is 200 always

    Arguments:
      required: dict of required keys and their types for the route being wrapped
      example:  example request (keys should match required)
    """
    def decorator(method):
      """
      the decorator returned by rpc
      """
      self.examples[method.__name__] = example
      @wraps(method)
      def decorated():
        try:
          params = json.loads(request.values['q'])
        except KeyError:
          return jsonify(error_msg='Missing input (q).')
        except ValueError as e:
          return jsonify(error_msg=e.message)
        for p in required:
          if p not in params:
            return jsonify(error_msg='Missing "%s" param' % p)
          try:
            params[p] = required[p](params[p])
          except ValueError:
            return jsonify(error_msg='Unexpected type %s of "%s" param. Expected %s' % (type(params[p]).__name__, p, required[p].__name__))
        return method(params)
      return decorated
    # apply the flask app.route decorator to the returned function
    return lambda arg: self.app.route(route, methods=['GET', 'POST'])(decorator(arg))

  def _add_common(self):
    """
    add .ping, _usage, _shutdown, _shutdownloop endpoints
    """
    @self.rpc(route='/.ping', example=0)
    def ping(params):
      return '1'

    @self.app.route('/_usage', methods=['GET', 'POST'])
    def _usage():
      return 'TODO'

    def shutdown(delay, stop_loop):
      """
      exit with status after delay
      """
      def stop(stop_loop):
        with open(self.pid_file) as pid_file:
          pid = int(pid_file.read())
        signal = 'TRAP' if stop_loop else 'IOT'
        """
        These signals are handled by the gunicorn arbiter
        We use a modfied arbiter for setting exit codes on SIGTRAP and SIGIOT
        The modifications are the following:
        <             for x in "HUP QUIT INT TERM TTIN TTOU USR1 USR2 WINCH".split()]
        ---
        >             for x in "HUP QUIT INT TERM TTIN TTOU USR1 USR2 WINCH TRAP IOT".split()]

        >
        >     def handle_trap(self):
        >         "SIGTRAP handling"
        >         print 'handle_trap'
        >         self.halt(exit_status=100)
        >
        >     def handle_iot(self):
        >         "SIGIOT handling"
        >         print 'handle_iot'
        >         self.halt(exit_status=15)
        These modifications have been made in
          /home/share/packages/python/pyinstaller_mods/gunicorn/arbiter.py
        """
        subprocess.call(['kill', '-'+signal, str(pid)])

      print 'shutting down'
      Timer(delay, lambda: stop(stop_loop)).start()

    @self.app.route('/_shutdown', methods=['GET', 'POST'])
    def _shutdown():
      shutdown(1.0, False)
      return 'Preparing to shutdown...'

    @self.app.route('/_shutdownloop', methods=['GET', 'POST'])
    def _shutdownloop():
      shutdown(1.0, True)
      return 'Preparing to shutdown...'

  # construct the root web form for http debug interface
  def _add_root_form(self):
    """
    add a route for the default web interface for an rpc server
    """
    from jinja2 import ChoiceLoader, DictLoader
    template_path = os.path.abspath(os.path.join(os.path.dirname(__file__), 'templates'))
    self.app.jinja_loader = ChoiceLoader([self.app.jinja_loader,
                                          DictLoader({'root_form.html.jinja': self._root_form_html})]) # append folder with root form template to jinja loader path
    @self.app.route('/', methods=['GET'])
    def root():
      methods = {url_for(rule.endpoint)[1:]: json.dumps(self.examples[rule.endpoint]) for rule in self.app.url_map.iter_rules() if rule.endpoint not in ['root', 'static'] and not rule.endpoint.startswith('_')}
      return render_template('root_form.html.jinja', methods=sorted(methods.items()))

  # this is inline because adding a template to the jinja path is tricky
  _root_form_html = '''
  <html>
  <head>
    <title>R77 RPC Server</title>
    <link rel="icon" type="image/png" href="/images/icons/fav-internal.png">
    <script language="JavaScript">
      function settarget(seq) {
        var c = document.getElementById("targetcheck" + seq);
        var f = document.getElementById("query" + seq);
        if (c.checked)
          f.target = "optripjsonresultwin";
        else
          f.target = "result" + seq;
        }
    </script>
  </head>
  <body>
    <a href="/_usage">Usage report</a>
    <span style="padding-left:100px;"></span>
    <a href="/_status">Process status</a>
    <span style="padding-left:100px;"></span>
    <a href="/_param">View/edit parameters</a>
    <span style="padding-left:100px;"></span>
    <a href="/_validate">Validate</a>
    <p>
      This server supports the following {{ methods|length }} operation{{ "s" if methods else "" }}:
    <p><br>
    {% for method, _ in methods %}
      <a href="#{{ method }}">{{ method }}</a>&nbsp;
    {% endfor %}
    <br>
    <table>
    {% for method, example in methods %}
    <tr id="{{ method }}">
      <form id="query{{ loop.index }}"
            action="{{ method }}"
            method="post" target="result{{ loop.index }}">
      <td>
        <b>{{ method }}</b>
      </td>
      <td>
        <textarea name="q" rows=12 cols=55>{{ example }}</textarea><br>
        <input type="hidden" name="d" value="1">
      </td>
      <td>
        <input type="submit" value="Submit"><br>
        <input type="checkbox" id="targetcheck{{ loop.index }}"
               onclick="javascript:settarget({{ loop.index }})">
        <label for="targetcheck{{ loop.index }}"><font size=-1>
            in new<br>&nbsp;&nbsp;&nbsp;&nbsp;window</font>
      </label>
      </td>
      <td>
        Result:<br>
        <iframe name="result{{ loop.index }}" width=390 height=180></iframe>
      </td>
    </form></tr>
    {% endfor %}
    </table>
  </body>
  </html>
  '''


# gunicorn setup
class GunicornApplication(Application):
  def __init__(self, app, port, **kwargs):
    self.app = app
    self.port = port
    self.opts = kwargs
    Application.__init__(self)

  def init(self, parser, opts, args):
    self.opts.update({'bind': '%s:%d' % ('0.0.0.0', self.port),
                      'accesslog': '-', # log accesses to stdout
                      'errorlog': '-'} # log errors to stdout
                     )
    return self.opts

  def load(self):
    return self.app


Flags.PARSER.add_argument('--die', action='store_const', const=True,
                          help='Exit at beginning of main')
Flags.PARSER.add_argument('--workers', type=int, default=4,
                          help='Number of gunicorn processes to run. 0 serves without gunicorn')
