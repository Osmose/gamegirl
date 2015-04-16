import logging
import logging.config
import traceback

import urwid

from gamegirl.memory import Rom


# This code is meant to work, not meant to be pretty.
# I'll maybe make it better someday.


line_divider = urwid.Divider(div_char=u'\u2500')
blank_divider = urwid.Divider()


def block_text(text, align='left', style=None, right=0, left=0):
    if not isinstance(text, urwid.Text):
        text = urwid.Text(text, align=align)

    widget = urwid.Padding(text, width=('relative', 100), right=right, left=left)
    if style:
        widget = urwid.AttrMap(widget, style)

    return widget


def sidebar_title(text):
    return urwid.Padding(urwid.Text(('sidebar_title', ' {0} '.format(text))), left=2)


def sidebar_value(text):
    return urwid.Padding(urwid.Text(('sidebar_value', ' {0} '.format(text))),
                         width=('relative', 100), right=2, left=4)


class DebuggerLogHandler(logging.Handler):
    def __init__(self, *args, **kwargs):
        self.debugger = kwargs.pop('debugger')
        super(DebuggerLogHandler, self).__init__(*args, **kwargs)

    def emit(self, record):
        self.debugger.log(record.getMessage(), lineno=record.levelname,
                          walker=self.debugger.log_walker)


class DebuggerInterface(object):
    def __init__(self, cpu):
        self.cpu = cpu
        self.mode = None
        cpu.debug = True
        rom = cpu.memory.rom

        self.stopped = False

        self.palette = [
            ('titlebar', 'black', 'light gray'),
            ('helpbar', 'black', 'dark cyan'),
            ('background', 'yellow', 'dark blue'),
            ('gutter', 'black', 'dark cyan'),
            ('register_name', 'white', 'dark cyan'),
            ('register_value', 'yellow', 'dark blue'),
            ('sidebar', 'black', 'light gray'),
            ('sidebar_title', 'white', 'dark cyan'),
            ('sidebar_value', 'yellow', 'dark blue'),
        ]

        self.titlebar = urwid.AttrMap(urwid.Text(('titlebar', 'GameGirl'), align='center'), 'titlebar')
        self.help_text = urwid.Text((
            'helpbar',
            ''
        ), align='left')
        self.helpbar = urwid.AttrMap(self.help_text, 'helpbar')

        # Instruction log
        self.instruction_walker = urwid.SimpleFocusListWalker([])
        self.instruction_list = urwid.ListBox(self.instruction_walker)

        # Debug log
        self.log_walker = urwid.SimpleFocusListWalker([])
        self.log_list = urwid.ListBox(self.log_walker)

        # Memory view
        self.memory_walker = urwid.SimpleFocusListWalker([])
        self.memory_list = urwid.ListBox(self.memory_walker)

        # Sidebar
        register_grid = []
        for register in ('A', 'B', 'C', 'D', 'E', 'F', 'H', 'L', 'SP', 'PC'):
            text_widget = urwid.Text('_', align='center')
            setattr(self, 'register_' + register, text_widget)
            register_grid.append(block_text(register, align='center', style='register_name'))
            register_grid.append(block_text(text_widget, style='register_value'))

        flag_grid = []
        for flag in ('Z', 'N', 'H', 'C'):
            text_widget = urwid.Text('_', align='center')
            setattr(self, 'flag_' + flag, text_widget)
            flag_grid.append(block_text(flag, align='center', style='register_name'))
            flag_grid.append(block_text(text_widget, style='register_value'))

        if rom.gbc_compatible == Rom.GBC_INCOMPATIBLE:
            gbc_status = 'Incompatible'
        elif rom.gbc_compatible == Rom.GBC_COMPATIBLE:
            gbc_status = 'Compatible'
        elif rom.gbc_compatible == Rom.GBC_EXCLUSIVE:
            gbc_status = 'Exclusive'
        else:
            gbc_status = 'Unknown'

        self.sidebar = urwid.ListBox(urwid.SimpleListWalker([
            urwid.Text('Registers', align='center'),
            line_divider,
            urwid.GridFlow(register_grid, cell_width=7, h_sep=1, v_sep=1, align='center'),
            blank_divider,

            urwid.Text('Flags', align='center'),
            line_divider,
            urwid.GridFlow(flag_grid, cell_width=7, h_sep=1, v_sep=1, align='center'),
            blank_divider,

            urwid.Text('ROM', align='center'),
            line_divider,
            sidebar_title('Game'),
            sidebar_value(rom.title),
            blank_divider,
            sidebar_title('Game Code'),
            sidebar_value(rom.game_code),
            blank_divider,
            sidebar_title('Start address'),
            sidebar_value('${0:04x}'.format(rom.start_address)),
            blank_divider,
            sidebar_title('Gameboy Color'),
            sidebar_value(gbc_status),
            blank_divider,
            sidebar_title('Maker code'),
            sidebar_value(rom.maker_code),
            blank_divider,
            sidebar_title('Super Gameboy'),
            sidebar_value('Yes' if rom.super_gameboy else 'No'),
            blank_divider,
            sidebar_title('ROM Size'),
            sidebar_value(rom.rom_size[1]),
            blank_divider,
            sidebar_title('Destination'),
            sidebar_value('Other' if rom.destination == Rom.DESTINATION_OTHER else 'Japan'),
            blank_divider,
            sidebar_title('Mask ROM Version'),
            sidebar_value(rom.mask_rom_version),
            blank_divider,
            sidebar_title('Complement check'),
            sidebar_value('Passed' if rom.passed_complement_check else 'Failed'),
            blank_divider,
            sidebar_title('Checksum'),
            sidebar_value('${0:04x}'.format(rom.checksum)),
            blank_divider,
        ]))

        # Main layout and loop
        self.top_columns = urwid.Columns([
            ('weight', 2, self.instruction_list),
            (35, urwid.AttrMap(self.sidebar, 'sidebar')),
        ])
        self.top_frame = urwid.Frame(self.top_columns, header=self.titlebar, footer=self.helpbar)
        self.top = urwid.AttrMap(self.top_frame, 'background')
        self.loop = urwid.MainLoop(self.top, self.palette, unhandled_input=self.unhandled_input)

        self.enter_instruction_mode()
        self.update_sidebar()

        logging.config.dictConfig({
            'version': 1,
            'handlers': {
                'debugger': {
                    'class': 'gamegirl.debugger.DebuggerLogHandler',
                    'level': 'DEBUG',
                    'debugger': self
                }
            },
            'root': {
                'level': 'DEBUG',
                'handlers': ['debugger']
            }
        })

    def start(self):
        self.loop.run()

    def enter_instruction_mode(self):
        self.set_main(self.instruction_list)
        self.set_help(
            '(N)ext instruction',
            '(C)ontinue until error',
            '(W)atch until error',
            '(M)emory mode',
            '(L)og mode',
            '(Q)uit'
        )
        self.mode = 'instruction'

    def enter_memory_mode(self):
        self.update_memory_view()
        self.set_main(self.memory_list)
        self.set_help('(I)nstruction mode', '(L)og mode', '(Q)uit')
        self.mode = 'memory'

    def enter_log_mode(self):
        self.set_main(self.log_list)
        self.set_help('(I)nstruction mode', '(M)emory mode', '(Q)uit')
        self.log_focus_bottom(walker=self.log_walker)
        self.mode = 'log'

    def set_main(self, widget):
        self.top_columns.contents[0] = (widget, self.top_columns.options('weight', 2))

    def set_help(self, *items):
        self.help_text.set_text('   ' + ', '.join(items))

    def update_sidebar(self):
        for register in ('A', 'B', 'C', 'D', 'E', 'F', 'H', 'L', 'SP', 'PC'):
            if len(register) == 1:
                format_string = '${0:02x}'
            else:
                format_string = '${0:04x}'

            widget = getattr(self, 'register_' + register)
            widget.set_text(format_string.format(getattr(self.cpu, register)))

        for flag in ('Z', 'N', 'H', 'C'):
            widget = getattr(self, 'flag_' + flag)
            widget.set_text(unicode(getattr(self.cpu, 'flag_' + flag)))

    def log(self, text, lineno='', bytes=None, walker=None):
        gutter_length = max(9, len(lineno))
        gutter = block_text(lineno, style='gutter', right=1, align='right')
        columns = [(gutter_length, gutter), urwid.Text(text)]

        if bytes:
            byte_gutter_length = max(6, len(bytes) * 2) + 3
            byte_string = '$' + ''.join(['{0:02x}'.format(b) for b in bytes])
            byte_gutter = block_text(byte_string, style='gutter', left=1, align='left')
            columns.append((byte_gutter_length, byte_gutter))

        walker = walker if walker is not None else self.instruction_walker
        walker.append(urwid.Columns(columns, dividechars=1))

    def log_divider(self):
        self.instruction_walker.append(urwid.Divider(div_char='-'))

    def log_focus_bottom(self, walker=None):
        walker = walker if walker is not None else self.instruction_walker
        walker.set_focus(len(walker) - 1)

    def execute(self):
        if self.stopped:
            self.log('Execution has stopped, cannot continue.')
        else:
            try:
                lineno = '${0:04x}'.format(self.cpu.PC)
                result, debug_bytes = self.cpu.read_and_execute()
                self.log(result, lineno=lineno, bytes=debug_bytes)
                self.log_focus_bottom()
            except Exception:
                self.log(traceback.format_exc())
                self.stopped = True

    def unhandled_input(self, key):
        if key in ('q', 'Q'):
            raise urwid.ExitMainLoop()

        if self.mode == 'instruction':
            if key in ('n', 'N'):
                self.execute()
                self.update_sidebar()

            if key in ('c', 'C', 'w', 'W'):
                screen = self.loop.screen
                user_stop = False
                watch = key in ('w', 'W')
                self.help_text.set_text('   (S)top')

                self.execute()
                while not self.stopped and not user_stop:
                    self.execute()
                    if watch:
                        self.update_sidebar()
                        self.loop.draw_screen()

                    # Since we're not running the main loop during this
                    # command we need to manually handle input.
                    keys, raw = screen.parse_input(None, None, screen.get_available_raw_input())
                    for key in keys:
                        if key in ('s', 'S'):
                            user_stop = True

                self.update_sidebar()
                self.enter_instruction_mode()

        if key in ('m', 'M'):
            self.enter_memory_mode()

        if key in ('i', 'I'):
            self.enter_instruction_mode()

        if key in ('l', 'L'):
            self.enter_log_mode()

        if key in ('d', 'D'):
            import pudb
            pudb.set_trace()

    def update_memory_view(self):
        del self.memory_walker[:]
        memory_string = ''
        for addr in range(0x10000):
            try:
                memory_string += '{0:02x} '.format(self.cpu.memory.read_byte(addr))
            except ValueError:
                memory_string += '-- '

            if addr % 16 == 15:
                self.log(memory_string, walker=self.memory_walker,
                         lineno='${0:04x}'.format(addr - 15))
                memory_string = ''
