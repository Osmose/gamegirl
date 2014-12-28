import traceback

import urwid

from gamegirl.memory import Rom


class DebuggerInterface(object):
    def __init__(self, cpu):
        self.cpu = cpu
        cpu.debug = True

        self.stopped = False

        self.palette = [
            ('titlebar', 'black', 'light gray'),
            ('background', 'yellow', 'dark blue'),
            ('gutter', 'black', 'light gray'),
            ('register_name', 'black', 'light gray'),
        ]

        self.titlebar = urwid.AttrMap(urwid.Text(('titlebar', 'GameGirl'), align='center'), 'titlebar')

        # Instruction log
        self.log_walker = urwid.SimpleFocusListWalker([])
        self.log_list = urwid.ListBox(self.log_walker)

        # Sidebar
        register_grid = []
        for register in ('A', 'B', 'C', 'D', 'E', 'F', 'HL', 'SP', 'PC'):
            text_widget = urwid.Text('_')
            setattr(self, 'register_' + register, text_widget)
            register_grid.append(urwid.AttrMap(urwid.Padding(urwid.Text(register, align='center'), width=('relative', 100)), 'register_name'))
            register_grid.append(text_widget)

        self.cpu_heading = urwid.Text('CPU', align='center')
        self.sidebar = urwid.ListBox(urwid.SimpleListWalker([
            self.cpu_heading,
            urwid.Divider(div_char='-'),
            urwid.GridFlow(register_grid, cell_width=5, h_sep=1, v_sep=1, align='center'),
        ]))

        # Main layout and loop
        self.top_columns = urwid.Columns([
            ('weight', 2, self.log_list),
            (27, urwid.LineBox(self.sidebar)),
        ])
        self.top_frame = urwid.Frame(self.top_columns, header=self.titlebar)
        self.top = urwid.AttrMap(self.top_frame, 'background')
        self.loop = urwid.MainLoop(self.top, self.palette, unhandled_input=self.unhandled_input)

        self.update_sidebar()

    def start(self):
        # Print some info about the game we're running.
        rom = self.cpu.memory.rom
        self.log('Game: ' + rom.title)
        self.log('Start address: ${0:04x}'.format(rom.start_address))
        self.log('Game code: ' + rom.game_code)

        if rom.gbc_compatible == Rom.GBC_INCOMPATIBLE:
            self.log('Gameboy Color: Incompatible')
        elif rom.gbc_compatible == Rom.GBC_COMPATIBLE:
            self.log('Gameboy Color: Compatible')
        elif rom.gbc_compatible == Rom.GBC_EXCLUSIVE:
            self.log('Gameboy Color: Exclusive')
        else:
            self.log('Gameboy Color: Unknown')

        self.log('Maker code: ' + rom.maker_code)
        self.log('Super Gameboy: ' + ('Yes' if rom.super_gameboy else 'No'))
        self.log('ROM Size: ' + rom.rom_size[1])
        self.log('Destination: ' + ('Other' if rom.destination == Rom.DESTINATION_OTHER else 'Japan'))
        self.log('Mask ROM Version: {0}'.format(rom.mask_rom_version))
        self.log('Complement check: ' + ('Passed' if rom.passed_complement_check else 'Failed'))
        self.log('Checksum: ${0:04x}'.format(rom.checksum))
        self.log_divider()

        self.loop.run()

    def update_sidebar(self):
        for register in ('A', 'B', 'C', 'D', 'E', 'F', 'HL', 'SP', 'PC'):
            widget = getattr(self, 'register_' + register)
            widget.set_text('${0:04x}'.format(getattr(self.cpu, register)))

    def log(self, text, lineno=''):
        gutter_length = max(9, len(lineno))
        gutter = urwid.AttrMap(
            urwid.Padding(
                urwid.Text(('gutter', lineno), align='right'),
                width=('relative', 100), right=1),
            'gutter')

        self.log_walker.append(urwid.Columns([
            (gutter_length, gutter),
            urwid.Text(text),
        ], dividechars=1))

    def log_divider(self):
        self.log_walker.append(urwid.Divider(div_char='-'))

    def log_focus_bottom(self):
        self.log_walker.set_focus(len(self.log_walker) - 1)

    def execute(self):
        if self.stopped:
            self.log('Execution has stopped, cannot continue.')
        else:
            try:
                result = self.cpu.read_and_execute()
                self.log(result, lineno=unicode(self.cpu.instruction_count))
                self.log_focus_bottom()
            except Exception as e:
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
            import pudb; pudb.set_trace()
