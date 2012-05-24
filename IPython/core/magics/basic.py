"""Implementation of basic magic functions.
"""
#-----------------------------------------------------------------------------
#  Copyright (c) 2012 The IPython Development Team.
#
#  Distributed under the terms of the Modified BSD License.
#
#  The full license is in the file COPYING.txt, distributed with this software.
#-----------------------------------------------------------------------------

#-----------------------------------------------------------------------------
# Imports
#-----------------------------------------------------------------------------
from __future__ import print_function

# Stdlib
import io
import sys
from pprint import pformat

# Our own packages
from IPython.core.error import UsageError
from IPython.core.magic import Magics, magics_class, line_magic
from IPython.core.prefilter import ESC_MAGIC
from IPython.utils.text import format_screen
from IPython.core import magic_arguments, page
from IPython.testing.skipdoctest import skip_doctest
from IPython.utils.ipstruct import Struct
from IPython.utils.path import unquote_filename
from IPython.utils.warn import warn, error

#-----------------------------------------------------------------------------
# Magics class implementation
#-----------------------------------------------------------------------------

@magics_class
class BasicMagics(Magics):
    """Magics that provide central IPython functionality.

    These are various magics that don't fit into specific categories but that
    are all part of the base 'IPython experience'."""

    def _lsmagic(self):
        mesc = ESC_MAGIC
        cesc = mesc*2
        mman = self.shell.magics_manager
        magics = mman.lsmagic()
        out = ['Available line magics:',
               mesc + ('  '+mesc).join(magics['line']),
               '',
               'Available cell magics:',
               cesc + ('  '+cesc).join(magics['cell']),
               '',
               mman.auto_status()]
        return '\n'.join(out)

    @line_magic
    def lsmagic(self, parameter_s=''):
        """List currently available magic functions."""
        print(self._lsmagic())

    @line_magic
    def magic(self, parameter_s=''):
        """Print information about the magic function system.

        Supported formats: -latex, -brief, -rest
        """

        mode = ''
        try:
            mode = parameter_s.split()[0][1:]
            if mode == 'rest':
                rest_docs = []
        except:
            pass

        magic_docs = []
        escapes = dict(line=ESC_MAGIC, cell=ESC_MAGIC*2)
        magics = self.shell.magics_manager.magics

        for mtype in ('line', 'cell'):
            escape = escapes[mtype]
            for fname, fn in magics[mtype].iteritems():

                if mode == 'brief':
                    # only first line
                    if fn.__doc__:
                        fndoc = fn.__doc__.split('\n',1)[0]
                    else:
                        fndoc = 'No documentation'
                else:
                    if fn.__doc__:
                        fndoc = fn.__doc__.rstrip()
                    else:
                        fndoc = 'No documentation'

                if mode == 'rest':
                    rest_docs.append('**%s%s**::\n\n\t%s\n\n' %
                                     (escape, fname, fndoc))
                else:
                    magic_docs.append('%s%s:\n\t%s\n' %
                                      (escape, fname, fndoc))

        magic_docs = ''.join(magic_docs)

        if mode == 'rest':
            return "".join(rest_docs)

        if mode == 'latex':
            print(self.format_latex(magic_docs))
            return
        else:
            magic_docs = format_screen(magic_docs)
        if mode == 'brief':
            return magic_docs

        out = ["""
IPython's 'magic' functions
===========================

The magic function system provides a series of functions which allow you to
control the behavior of IPython itself, plus a lot of system-type
features. All these functions are prefixed with a % character, but parameters
are given without parentheses or quotes.

NOTE: If you have 'automagic' enabled (via the command line option or with the
%automagic function), you don't need to type in the % explicitly.  By default,
IPython ships with automagic on, so you should only rarely need the % escape.

Example: typing '%cd mydir' (without the quotes) changes you working directory
to 'mydir', if it exists.

For a list of the available magic functions, use %lsmagic. For a description
of any of them, type %magic_name?, e.g. '%cd?'.

Currently the magic system has the following functions:""",
       magic_docs,
       "Summary of magic functions (from %slsmagic):",
       self._lsmagic(),
       ]
        page.page('\n'.join(out))


    @line_magic
    def page(self, parameter_s=''):
        """Pretty print the object and display it through a pager.

        %page [options] OBJECT

        If no object is given, use _ (last output).

        Options:

          -r: page str(object), don't pretty-print it."""

        # After a function contributed by Olivier Aubert, slightly modified.

        # Process options/args
        opts, args = self.parse_options(parameter_s, 'r')
        raw = 'r' in opts

        oname = args and args or '_'
        info = self._ofind(oname)
        if info['found']:
            txt = (raw and str or pformat)( info['obj'] )
            page.page(txt)
        else:
            print('Object `%s` not found' % oname)

    @line_magic
    def profile(self, parameter_s=''):
        """Print your currently active IPython profile."""
        from IPython.core.application import BaseIPythonApplication
        if BaseIPythonApplication.initialized():
            print(BaseIPythonApplication.instance().profile)
        else:
            error("profile is an application-level value, but you don't appear to be in an IPython application")

    @line_magic
    def pprint(self, parameter_s=''):
        """Toggle pretty printing on/off."""
        ptformatter = self.shell.display_formatter.formatters['text/plain']
        ptformatter.pprint = bool(1 - ptformatter.pprint)
        print('Pretty printing has been turned',
              ['OFF','ON'][ptformatter.pprint])

    @line_magic
    def colors(self, parameter_s=''):
        """Switch color scheme for prompts, info system and exception handlers.

        Currently implemented schemes: NoColor, Linux, LightBG.

        Color scheme names are not case-sensitive.

        Examples
        --------
        To get a plain black and white terminal::

          %colors nocolor
        """
        def color_switch_err(name):
            warn('Error changing %s color schemes.\n%s' %
                 (name, sys.exc_info()[1]))


        new_scheme = parameter_s.strip()
        if not new_scheme:
            raise UsageError(
                "%colors: you must specify a color scheme. See '%colors?'")
            return
        # local shortcut
        shell = self.shell

        import IPython.utils.rlineimpl as readline

        if not shell.colors_force and \
                not readline.have_readline and sys.platform == "win32":
            msg = """\
Proper color support under MS Windows requires the pyreadline library.
You can find it at:
http://ipython.org/pyreadline.html
Gary's readline needs the ctypes module, from:
http://starship.python.net/crew/theller/ctypes
(Note that ctypes is already part of Python versions 2.5 and newer).

Defaulting color scheme to 'NoColor'"""
            new_scheme = 'NoColor'
            warn(msg)

        # readline option is 0
        if not shell.colors_force and not shell.has_readline:
            new_scheme = 'NoColor'

        # Set prompt colors
        try:
            shell.prompt_manager.color_scheme = new_scheme
        except:
            color_switch_err('prompt')
        else:
            shell.colors = \
                   shell.prompt_manager.color_scheme_table.active_scheme_name
        # Set exception colors
        try:
            shell.InteractiveTB.set_colors(scheme = new_scheme)
            shell.SyntaxTB.set_colors(scheme = new_scheme)
        except:
            color_switch_err('exception')

        # Set info (for 'object?') colors
        if shell.color_info:
            try:
                shell.inspector.set_active_scheme(new_scheme)
            except:
                color_switch_err('object inspector')
        else:
            shell.inspector.set_active_scheme('NoColor')

    @line_magic
    def xmode(self, parameter_s=''):
        """Switch modes for the exception handlers.

        Valid modes: Plain, Context and Verbose.

        If called without arguments, acts as a toggle."""

        def xmode_switch_err(name):
            warn('Error changing %s exception modes.\n%s' %
                 (name,sys.exc_info()[1]))

        shell = self.shell
        new_mode = parameter_s.strip().capitalize()
        try:
            shell.InteractiveTB.set_mode(mode=new_mode)
            print('Exception reporting mode:',shell.InteractiveTB.mode)
        except:
            xmode_switch_err('user')

    @line_magic
    def quickref(self,arg):
        """ Show a quick reference sheet """
        from IPython.core.usage import quick_reference
        qr = quick_reference + self.magic('-brief')
        page.page(qr)

    @line_magic
    def doctest_mode(self, parameter_s=''):
        """Toggle doctest mode on and off.

        This mode is intended to make IPython behave as much as possible like a
        plain Python shell, from the perspective of how its prompts, exceptions
        and output look.  This makes it easy to copy and paste parts of a
        session into doctests.  It does so by:

        - Changing the prompts to the classic ``>>>`` ones.
        - Changing the exception reporting mode to 'Plain'.
        - Disabling pretty-printing of output.

        Note that IPython also supports the pasting of code snippets that have
        leading '>>>' and '...' prompts in them.  This means that you can paste
        doctests from files or docstrings (even if they have leading
        whitespace), and the code will execute correctly.  You can then use
        '%history -t' to see the translated history; this will give you the
        input after removal of all the leading prompts and whitespace, which
        can be pasted back into an editor.

        With these features, you can switch into this mode easily whenever you
        need to do testing and changes to doctests, without having to leave
        your existing IPython session.
        """

        # Shorthands
        shell = self.shell
        pm = shell.prompt_manager
        meta = shell.meta
        disp_formatter = self.shell.display_formatter
        ptformatter = disp_formatter.formatters['text/plain']
        # dstore is a data store kept in the instance metadata bag to track any
        # changes we make, so we can undo them later.
        dstore = meta.setdefault('doctest_mode',Struct())
        save_dstore = dstore.setdefault

        # save a few values we'll need to recover later
        mode = save_dstore('mode',False)
        save_dstore('rc_pprint',ptformatter.pprint)
        save_dstore('xmode',shell.InteractiveTB.mode)
        save_dstore('rc_separate_out',shell.separate_out)
        save_dstore('rc_separate_out2',shell.separate_out2)
        save_dstore('rc_prompts_pad_left',pm.justify)
        save_dstore('rc_separate_in',shell.separate_in)
        save_dstore('rc_plain_text_only',disp_formatter.plain_text_only)
        save_dstore('prompt_templates',(pm.in_template, pm.in2_template, pm.out_template))

        if mode == False:
            # turn on
            pm.in_template = '>>> '
            pm.in2_template = '... '
            pm.out_template = ''

            # Prompt separators like plain python
            shell.separate_in = ''
            shell.separate_out = ''
            shell.separate_out2 = ''

            pm.justify = False

            ptformatter.pprint = False
            disp_formatter.plain_text_only = True

            shell.magic('xmode Plain')
        else:
            # turn off
            pm.in_template, pm.in2_template, pm.out_template = dstore.prompt_templates

            shell.separate_in = dstore.rc_separate_in

            shell.separate_out = dstore.rc_separate_out
            shell.separate_out2 = dstore.rc_separate_out2

            pm.justify = dstore.rc_prompts_pad_left

            ptformatter.pprint = dstore.rc_pprint
            disp_formatter.plain_text_only = dstore.rc_plain_text_only

            shell.magic('xmode ' + dstore.xmode)

        # Store new mode and inform
        dstore.mode = bool(1-int(mode))
        mode_label = ['OFF','ON'][dstore.mode]
        print('Doctest mode is:', mode_label)

    @line_magic
    def gui(self, parameter_s=''):
        """Enable or disable IPython GUI event loop integration.

        %gui [GUINAME]

        This magic replaces IPython's threaded shells that were activated
        using the (pylab/wthread/etc.) command line flags.  GUI toolkits
        can now be enabled at runtime and keyboard
        interrupts should work without any problems.  The following toolkits
        are supported:  wxPython, PyQt4, PyGTK, Tk and Cocoa (OSX)::

            %gui wx      # enable wxPython event loop integration
            %gui qt4|qt  # enable PyQt4 event loop integration
            %gui gtk     # enable PyGTK event loop integration
            %gui gtk3    # enable Gtk3 event loop integration
            %gui tk      # enable Tk event loop integration
            %gui OSX     # enable Cocoa event loop integration
                         # (requires %matplotlib 1.1)
            %gui         # disable all event loop integration

        WARNING:  after any of these has been called you can simply create
        an application object, but DO NOT start the event loop yourself, as
        we have already handled that.
        """
        opts, arg = self.parse_options(parameter_s, '')
        if arg=='': arg = None
        try:
            return self.enable_gui(arg)
        except Exception as e:
            # print simple error message, rather than traceback if we can't
            # hook up the GUI
            error(str(e))

    @skip_doctest
    @line_magic
    def precision(self, s=''):
        """Set floating point precision for pretty printing.

        Can set either integer precision or a format string.

        If numpy has been imported and precision is an int,
        numpy display precision will also be set, via ``numpy.set_printoptions``.

        If no argument is given, defaults will be restored.

        Examples
        --------
        ::

            In [1]: from math import pi

            In [2]: %precision 3
            Out[2]: u'%.3f'

            In [3]: pi
            Out[3]: 3.142

            In [4]: %precision %i
            Out[4]: u'%i'

            In [5]: pi
            Out[5]: 3

            In [6]: %precision %e
            Out[6]: u'%e'

            In [7]: pi**10
            Out[7]: 9.364805e+04

            In [8]: %precision
            Out[8]: u'%r'

            In [9]: pi**10
            Out[9]: 93648.047476082982
        """
        ptformatter = self.shell.display_formatter.formatters['text/plain']
        ptformatter.float_precision = s
        return ptformatter.float_format

    @magic_arguments.magic_arguments()
    @magic_arguments.argument(
        '-e', '--export', action='store_true', default=False,
        help='Export IPython history as a notebook. The filename argument '
             'is used to specify the notebook name and format. For example '
             'a filename of notebook.ipynb will result in a notebook name '
             'of "notebook" and a format of "xml". Likewise using a ".json" '
             'or ".py" file extension will write the notebook in the json '
             'or py formats.'
    )
    @magic_arguments.argument(
        '-f', '--format',
        help='Convert an existing IPython notebook to a new format. This option '
             'specifies the new format and can have the values: xml, json, py. '
             'The target filename is chosen automatically based on the new '
             'format. The filename argument gives the name of the source file.'
    )
    @magic_arguments.argument(
        'filename', type=unicode,
        help='Notebook name or filename'
    )
    @line_magic
    def notebook(self, s):
        """Export and convert IPython notebooks.

        This function can export the current IPython history to a notebook file
        or can convert an existing notebook file into a different format. For
        example, to export the history to "foo.ipynb" do "%notebook -e foo.ipynb".
        To export the history to "foo.py" do "%notebook -e foo.py". To convert
        "foo.ipynb" to "foo.json" do "%notebook -f json foo.ipynb". Possible
        formats include (json/ipynb, py).
        """
        args = magic_arguments.parse_argstring(self.notebook, s)

        from IPython.nbformat import current
        args.filename = unquote_filename(args.filename)
        if args.export:
            fname, name, format = current.parse_filename(args.filename)
            cells = []
            hist = list(self.shell.history_manager.get_range())
            for session, prompt_number, input in hist[:-1]:
                cells.append(current.new_code_cell(prompt_number=prompt_number,
                                                   input=input))
            worksheet = current.new_worksheet(cells=cells)
            nb = current.new_notebook(name=name,worksheets=[worksheet])
            with io.open(fname, 'w', encoding='utf-8') as f:
                current.write(nb, f, format);
        elif args.format is not None:
            old_fname, old_name, old_format = current.parse_filename(args.filename)
            new_format = args.format
            if new_format == u'xml':
                raise ValueError('Notebooks cannot be written as xml.')
            elif new_format == u'ipynb' or new_format == u'json':
                new_fname = old_name + u'.ipynb'
                new_format = u'json'
            elif new_format == u'py':
                new_fname = old_name + u'.py'
            else:
                raise ValueError('Invalid notebook format: %s' % new_format)
            with io.open(old_fname, 'r', encoding='utf-8') as f:
                nb = current.read(f, old_format)
            with io.open(new_fname, 'w', encoding='utf-8') as f:
                current.write(nb, f, new_format)
