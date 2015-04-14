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


class DebuggerInterface(object):
    def __init__(self, cpu):
        self.cpu = cpu
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
        self.helpbar = urwid.AttrMap(
            urwid.Text(('helpbar', '  (N)ext instruction, (C)ontinue until error, (Q)uit'),
                       align='left'),
            'helpbar')

        # Instruction log
        self.log_walker = urwid.SimpleFocusListWalker([])
        self.log_list = urwid.ListBox(self.log_walker)

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
            ('weight', 2, self.log_list),
            (35, urwid.AttrMap(self.sidebar, 'sidebar')),
        ])
        self.top_frame = urwid.Frame(self.top_columns, header=self.titlebar, footer=self.helpbar)
        self.top = urwid.AttrMap(self.top_frame, 'background')
        self.loop = urwid.MainLoop(self.top, self.palette, unhandled_input=self.unhandled_input)

        self.update_sidebar()

    def start(self):
        self.loop.run()

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

    def log(self, text, lineno='', bytes=None):
        gutter_length = max(9, len(lineno))
        gutter = block_text(lineno, style='gutter', right=1, align='right')
        columns = [(gutter_length, gutter), urwid.Text(text)]

        if bytes:
            byte_gutter_length = max(6, len(bytes) * 2) + 3
            byte_string = '$' + ''.join(['{0:02x}'.format(b) for b in bytes])
            byte_gutter = block_text(byte_string, style='gutter', left=1, align='left')
            columns.append((byte_gutter_length, byte_gutter))

        self.log_walker.append(urwid.Columns(columns, dividechars=1))

    def log_divider(self):
        self.log_walker.append(urwid.Divider(div_char='-'))

    def log_focus_bottom(self):
        self.log_walker.set_focus(len(self.log_walker) - 1)

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

        if key in ('n', 'N'):
            self.execute()
            self.update_sidebar()

        if key in ('c', 'C'):
            self.execute()
            self.update_sidebar()
            while not self.stopped:
                self.execute()
                self.update_sidebar()

        if key in ('d', 'D'):
            import pudb
            pudb.set_trace()
