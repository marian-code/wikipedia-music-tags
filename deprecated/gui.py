import package_setup

import io
import os
import subprocess
import sys
import time
import tkinter
import webbrowser
from threading import Lock, Thread
from tkinter import *  # pylint: disable=W0614
from tkinter import filedialog, messagebox, ttk
from tkinter.ttk import *  # pylint: disable=W0614

if __name__ == '__main__':
    from utils import clean_logs
    clean_logs()

from wiki_music import log_gui, parser, shared_vars

log_gui.info("started imports")

from PIL import Image, ImageTk

from application import LYRICS, MAIN
from libb.ID3_tags import write_tags
from utils import list_files, module_path, we_are_frozen

log_gui.info("finished imports")


class Tkinter_GUI(Frame):

    def __init__(self, root):
        super().__init__()

        # initialize
        self.initUI()
        self.define_styles()
        self.lock = Lock()
        self.root = root

        # misc
        self.input_work_dir = StringVar()
        self.input_work_dir.set("")
        self.input_album = StringVar()
        self.input_band = StringVar()
        self.write_json = BooleanVar()
        self.offline_debbug = BooleanVar()
        # self.check_bind = []
        # self.check_all = StringVar()

        # tag related variables
        self.album = StringVar()
        # self.album.trace_add('write', self.to_uppercase)
        self.band = StringVar()
        self.release_date = StringVar()
        self.selected_genre = StringVar()
        self.numbers = []
        self.tracks = []
        self.types = []
        self.artists = []
        self.composers = []
        self.disc_num = []
        self.files = []
        self.lyrics = []
        self.lyrics_preview = []
        self.files_prewiew = []

        # tag names
        self.table_headers()

        # init checker
        self.remember = None
        self.description_checker()

    def description_checker(self):

        global shared_vars
        try:
            if " . . ." in shared_vars.describe:
                shared_vars.describe = shared_vars.describe.replace(" . . .", "")

            self.remember = shared_vars.describe

            if shared_vars.describe != " " and shared_vars.describe != "":
                if (self.remember == shared_vars.describe and
                   "Done" not in shared_vars.describe):
                    shared_vars.describe = shared_vars.describe + " ."
                self.master.title("Wiki_parse - " + shared_vars.describe)
            else:
                self.master.title("Wiki_parse")
        except Exception as e:
            log_gui.exception(e)
            print(e)
            shared_vars.exception = str(e)

        self.root.after(400, self.description_checker)

    def table_headers(self):

        self.tag_names = []
        for _ in range(8):
            self.tag_names.append(StringVar())

        self.tag_names[0].set("Number:")
        self.tag_names[1].set("Name:")
        self.tag_names[2].set("Type:")
        self.tag_names[3].set("Artists:")
        self.tag_names[4].set("Composers:")
        self.tag_names[5].set("Discnumber:")
        self.tag_names[6].set("Lyrics:")
        self.tag_names[7].set("File:")

    def define_styles(self):

        style = ttk.Style()

        style.configure("BW.TLabel", foreground="black", background="white")
        # grey --> (240, 240, 237)
        style.configure("BG.TLabel", foreground="Black", background="grey95")

        style.map("C.TButton",
                  foreground=[('active', 'blue')],
                  background=[('pressed', '!disabled', 'black'),
                              ('active', 'white')]
                  )

        style.map("C.TEntry",
                  foreground=[('active', 'blue')],
                  background=[('active', 'white')]
                  )

    def init_parser(self):
        global parser
        global shared_vars
        parser.__init__()
        parser.work_dir = self.input_work_dir.get()
        shared_vars.re_init()

    def initUI(self):

        self.master.title("Wiki Music")
        self.grid(columnspan=3, rowspan=3)

    def select_dir(self):
        global parser

        self.input_work_dir.set(filedialog.askdirectory())
        parser.work_dir = self.input_work_dir.get()
        try:
            parser.files = list_files(parser.work_dir)
            parser.read_files()

            self.input_album.set(parser.album)
            self.input_band.set(parser.band)
            self.re_init()
        except Exception as e:
            log_gui.exception(e)
            print(e)
            global shared_vars
            shared_vars.exception = str(e)

    def open_dir(self):
        try:
            if self.input_work_dir.get() == "":
                messagebox.showinfo("Title",
                                    "You must select directory first!")
            else:
                print("Opening folder...")
                os.startfile(self.input_work_dir.get())
                """
                if sys.platform == "linux" or sys.platform == "linux2":
                    subprocess.check_call(['xdg-open',
                                            self.input_work_dir.get()])
                elif sys.platform == "win32":
                    #subprocess.Popen('explorer "self.input_work_dir.get()"')
                """
        except Exception as e:
            log_gui.exception(e)
            print(e)
            global shared_vars
            shared_vars.exception = str(e)

    def run_search(self, *args):
        if str(self.input_band.get()) == "":
            messagebox.showinfo("Title", "You must input artist!")
            return 0
        elif str(self.input_album.get()) == "":
            messagebox.showinfo("Title", "You must input album!")
            return 0
        elif str(self.input_work_dir.get()) == "":
            messagebox.showinfo("Title", "You must select working directory!")
            return 0
        else:
            # threading
            log_gui.info("starting wikipedia search")
            try:
                self.init_parser()

                main_app = Thread(target=MAIN,
                                  args=(str(self.input_band.get()),
                                        str(self.input_album.get()),
                                        self.input_work_dir.get(),
                                        True))
                main_app.daemon = True
                main_app.start()
            except Exception as e:
                log_gui.exception(e)
                print(e)
                global shared_vars
                shared_vars.exception = str(e)

    def run_lyrics_search(self, *args):
        if str(self.input_work_dir.get()) == "":
            messagebox.showinfo("Title", "You must select working directory!")

        if self.input_work_dir is not None:

            # threading
            log_gui.info("starting lyrics search")

            try:
                main_app = Thread(target=LYRICS,
                                  args=(self.input_work_dir.get(),
                                        True))
                main_app.start()
            except Exception as e:
                log_gui.exception(e)
                print(e)
                global shared_vars
                shared_vars.exception = str(e)

            log_gui.info("lyrics search started")

    def save_all(self, lyrics_only):
        global parser

        if len(self.numbers) == 0:
            messagebox.showinfo("Title", "You must run the search first!")
        else:
            if self.input_work_dir.get() == "":
                messagebox.showinfo("Title",
                                    "You must specify directory with files!")
                return 0

            try:
                self.gui_to_parser()
                dict_data, _ = parser.data_to_dict()
                for data in dict_data:
                    write_tags(data, lyrics_only=lyrics_only)

                # reload files from disc after save
                self.init_parser()
                parser.files = list_files(self.input_work_dir.get())
                parser.read_files()
                self.re_init()
            except Exception as e:
                log_gui.exception(e)
                print(e)
                global shared_vars
                shared_vars.exception = str(e)

    def parser_to_gui(self):
        global parser

        self.selected_genre.set(parser.selected_genre)
        self.release_date.set(parser.release_date)
        self.album.set(parser.album)
        self.band.set(parser.band)

        longest = len(parser.numbers)

        self.numbers = self.spawn_rows_cols(parser.numbers, False, longest)
        self.tracks = self.spawn_rows_cols(parser.tracks, False, longest)
        self.types = self.spawn_rows_cols(parser.types, False, longest)
        self.disc_num = self.spawn_rows_cols(parser.disc_num, False, longest)
        self.artists = self.spawn_rows_cols(parser.artists, False, longest)
        self.lyrics = self.spawn_rows_cols(parser.lyrics, False, longest)
        self.lyrics_preview = self.spawn_rows_cols(parser.lyrics,
                                                   True, longest)
        self.composers = self.spawn_rows_cols(parser.composers, False, longest)
        self.files = self.spawn_rows_cols(parser.files, False, longest)
        self.files_prewiew = self.spawn_rows_cols(parser.files, True, longest)

    def gui_to_parser(self):
        global parser

        parser.selected_genre = self.selected_genre.get()
        parser.release_date = self.release_date.get()
        parser.album = self.album.get()
        parser.band = self.band.get()

        parser.numbers = self.unspawn_rows_cols(self.numbers, separate=True)
        parser.tracks = self.unspawn_rows_cols(self.tracks, separate=False)
        parser.types = self.unspawn_rows_cols(self.types, separate=True)
        parser.disc_num = self.unspawn_rows_cols(self.disc_num, separate=True)
        parser.artists = self.unspawn_rows_cols(self.artists, separate=True)
        parser.lyrics = self.unspawn_rows_cols(self.lyrics, separate=False)
        parser.composers = self.unspawn_rows_cols(self.composers,
                                                  separate=True)
        parser.files = self.unspawn_rows_cols(self.files, separate=True)

    def open_browser(self):
        global parser

        if parser.url is not None:
            try:
                webbrowser.open_new_tab(parser.url)
            except Exception as e:
                log_gui.exception(e)
                print(e)
                global shared_vars
                shared_vars.exception = str(e)
        else:
            messagebox.showinfo("Title", "You must run the search first!")

    def run_Mp3tag(self):
        if self.input_work_dir.get() == "":
            messagebox.showinfo("Title", "You must select directory first!")
        else:
            try:
                subprocess.Popen([r"C:\Program Files (x86)\Mp3tag\Mp3tag.exe",
                                  r'/fp:'+self.input_work_dir.get()])
            except Exception as e:
                log_gui.exception(e)
                print(e)
                global shared_vars
                shared_vars.exception = str(e)

    def spawn_rows_cols(self, data, cut, longest):

        if len(data) == 0:
            return [""]*longest

        temp = []
        for i in range(len(data)):
            temp.append(StringVar())
            if isinstance(data[i], str) or isinstance(data[i], int):
                if cut is True:
                    if os.path.isfile(data[i]):
                        _, tail = os.path.split(data[i])
                        temp[i].set(tail)
                    else:
                        temp[i].set(data[i][:30])
                else:
                    temp[i].set(data[i])
            elif data[i] is None:
                temp[i].set("")
            else:
                temp[i].set(", ".join(sorted(data[i])))

        return temp

    def unspawn_rows_cols(self, data, separate):

        temp = []
        for i in range(len(data)):
            temp.append([])
            if isinstance(data[i], tkinter.StringVar):
                temp[i] = data[i].get()
                if "," in temp[i] and separate is True:
                    temp[i] = [x.strip() for x in temp[i].split(",")]

        return temp

    def center(self, win):
        win.update_idletasks()
        width = win.winfo_width()
        height = win.winfo_height()
        x = (win.winfo_screenwidth() // 2) - (width // 2)
        y = (win.winfo_screenheight() // 2) - (height // 2)
        win.geometry('{}x{}+{}+{}'.format(width, height, x, y))

    def ask_multiple_choice_question(self, prompt, options):

        root = Toplevel()
        self.center(root)
        root.lift()
        if prompt:
            Label(root, text=prompt).grid(row=0, column=0)

        index = IntVar()
        selected_genre = StringVar()

        button = Button(root, text="Submit", command=root.destroy)
        button.grid(row=len(options) + 2, column=0)

        if len(options) == 0:
            selected_genre.set(self.selected_genre.get())
            Entry(root, textvariable=selected_genre).grid(row=1, column=0)
            button.wait_window(root)  # wait until toplevel window is destroyed
            return selected_genre.get()
        elif len(options) == 1:
            root.destroy()
            return options[0]
        else:
            for i, option in enumerate(options):
                Radiobutton(root,
                            text=option,
                            variable=index,
                            value=i).grid(row=i + 1, column=0, sticky="ew")

            button.wait_window(root)  # wait until toplevel window is destroyed
            return options[index.get()]

    def re_init(self):
        """
        gets called after conditonns check is done
        from within conditions check function in main
        """

        try:
            self.lock.acquire()

            if len(parser.numbers) != 0:

                self.parser_to_gui()

                log_gui.info("init scrollable frame")

                tags_frame = Scrollable_frame(self.root, 8, 0,
                                              len(self.numbers), 8)
                tags_frame.grid(row=8, column=0, columnspan=7,
                                rowspan=len(self.numbers), sticky="ew")

                text_var = [self.numbers,
                              self.tracks,
                              self.types,
                              self.artists,
                              self.composers,
                              self.disc_num,
                              self.lyrics_preview,
                              self.files_prewiew]

                log_gui.info("init entries")
                entry_bind = []

                for i in range(len(self.numbers)):
                    # self.check_bind.append(IntVar())
                    # Checkbutton(master = tags_frame.frame,
                    # variable=self.check_bind[i]).grid(row=i + 8, column = 0)

                    # add line in list
                    entry_bind.append([])

                    index = 0
                    for tv in text_var:
                        entry_bind[i].append(Entry(master=tags_frame.frame,
                                                   textvariable=tv[i],
                                                   justify=RIGHT, width=20))
                        entry_bind[i][index].grid(row=i + 8, column=index)
                        entry_bind[i][index].bind("<Button-1>",
                                                  lambda event,
                                                  pos=i: self.detail(pos))
                        index += 1

                    """
                    # numbers entry
                    entry_bind[i].append(Entry(master=tags_frame.frame,
                                               textvariable=self.numbers[i],
                                               justify=RIGHT, width=20))
                    entry_bind[i][0].grid(row=i + 8, column=0)
                    entry_bind[i][0].bind("<Button-1>",
                                          lambda event,
                                          pos=i: self.detail(pos))

                    # tracks entry
                    entry_bind[i].append(Entry(master=tags_frame.frame,
                                               textvariable=self.tracks[i],
                                               justify=LEFT, width=20))
                    entry_bind[i][1].grid(row=i + 8, column=1)
                    entry_bind[i][1].bind("<Button-1>",
                                          lambda event,
                                          pos=i: self.detail(pos))

                    # typres entry
                    entry_bind[i].append(Entry(master=tags_frame.frame,
                                               textvariable=self.types[i],
                                               justify=LEFT, width=20))
                    entry_bind[i][2].grid(row=i + 8, column=2)
                    entry_bind[i][2].bind("<Button-1>",
                                          lambda event,
                                          pos=i: self.detail(pos))

                    # artist entry
                    entry_bind[i].append(Entry(master=tags_frame.frame,
                                               textvariable=self.artists[i],
                                               justify=LEFT, width=20))
                    entry_bind[i][3].grid(row=i + 8, column=3)
                    entry_bind[i][3].bind("<Button-1>",
                                          lambda event,
                                          pos=i: self.detail(pos))

                    # composers entry
                    entry_bind[i].append(Entry(master=tags_frame.frame,
                                               textvariable=self.composers[i],
                                               justify=LEFT, width=20))
                    entry_bind[i][4].grid(row=i + 8, column=4)
                    entry_bind[i][4].bind("<Button-1>",
                                          lambda event,
                                          pos=i: self.detail(pos))

                    # disk number entry
                    entry_bind[i].append(Entry(master=tags_frame.frame,
                                               textvariable=self.disc_num[i],
                                               justify=LEFT, width=20))
                    entry_bind[i][5].grid(row=i + 8, column=5)
                    entry_bind[i][5].bind("<Button-1>",
                                          lambda event,
                                          pos=i: self.detail(pos))

                    # lyrics entry
                    entry_bind[i].append(Entry(master=tags_frame.frame,
                                               textvariable=self.lyrics_preview[i],
                                               justify=LEFT, width=20))
                    entry_bind[i][6].grid(row=i + 8, column=6)
                    entry_bind[i][6].bind("<Button-1>",
                                          lambda event,
                                          pos=i: self.detail(pos))

                    # file entry
                    entry_bind[i].append(Entry(master=tags_frame.frame,
                                               textvariable=self.files_prewiew[i],
                                               justify=LEFT, width=20))
                    entry_bind[i][7].grid(row=i + 8, column=7)
                    entry_bind[i][7].bind("<Button-1>",
                                          lambda event,
                                          pos=i: self.detail(pos))
                    """

            else:
                self.root.after(200, self.re_init)

            self.lock.release()
        except Exception as e:
            log_gui.exception(e)
            print(e)
            global shared_vars
            shared_vars.exception = str(e)
        else:
            log_gui.info("init entries done")

    def detail(self, pos):
        """
        Display detail of the row that is clicked
        """

        log_gui.info("bind detail function")
        try:
            remaining_space = self.root.winfo_height() - 147
            rowspan = len(self.numbers)
            if rowspan*21 > remaining_space:
                rowspan = int(self.root.winfo_height() / 21) + 3
            else:
                rowspan = rowspan + 5

            # detail label frame
            data_detail = ttk.Labelframe(self.root,
                                         text='Detail:',
                                         borderwidth=3)
            data_detail.grid(row=0, column=9, columnspan=2,
                             rowspan=rowspan, sticky="nsew")

            # song title
            ttk.Label(master=data_detail, textvariable=self.tracks[pos],
                      anchor="w", relief=FLAT, cursor="xterm",
                      style="BG.TLabel").grid(row=0, column=9, columnspan=2)

            # song number
            ttk.Label(master=data_detail, text="Number",
                      anchor="w", relief=FLAT, cursor="xterm",
                      style="BG.TLabel").grid(row=1, column=9, columnspan=2)
            Entry(master=data_detail, textvariable=self.numbers[pos],
                  justify=LEFT, width=40).grid(row=2, column=9, columnspan=2)

            # song artists
            ttk.Label(master=data_detail, text="Artists",
                      anchor="w", relief=FLAT, cursor="xterm",
                      style="BG.TLabel").grid(row=3, column=9, columnspan=2)
            Entry(master=data_detail, textvariable=self.artists[pos],
                  justify=LEFT, width=40).grid(row=4, column=9, columnspan=2)

            # song composers
            ttk.Label(master=data_detail, text="Composers",
                      anchor="w", relief=FLAT, cursor="xterm",
                      style="BG.TLabel").grid(row=5, column=9, columnspan=2)
            Entry(master=data_detail, textvariable=self.composers[pos],
                  justify=LEFT, width=40).grid(row=6, column=9, columnspan=2)

            # song file
            ttk.Label(master=data_detail, text="File",
                      anchor="w", relief=FLAT, cursor="xterm",
                      style="BG.TLabel").grid(row=7, column=9, columnspan=2)
            Entry(master=data_detail, textvariable=self.files[pos],
                  justify=LEFT, width=40).grid(row=8, column=9, columnspan=2)

            # song lyrics
            ttk.Label(master=data_detail, text="Lyrics",
                      anchor="w", relief=FLAT, cursor="xterm",
                      style="BG.TLabel").grid(row=9, column=9, columnspan=2)
            lyrics_box = Text_box(data_detail, self, pos, row=10, col=9,
                                  rowspan=rowspan - 6, colspan=2)

            lyrics_box.insert(self.lyrics[pos].get())
            self.root.after(0, lyrics_box.text_check)
        except Exception as e:
            log_gui.exception(e)
            print(e)
            global shared_vars
            shared_vars.exception = str(e)

    def sort_shit(self, column):

        def order(data):

            if type(data) == list:
                if len(data) == 0:
                    return "1"
                else:
                    data = data[0]

            if type(data) == int:
                return data
            elif data.isdigit():
                return int(data)
            else:
                return data

        try:
            zipped = zip(parser.numbers,
                         parser.tracks,
                         parser.types,
                         parser.artists,
                         parser.composers,
                         parser.disc_num,
                         parser.lyrics,
                         parser.files)
            if "▲" in self.tag_names[column].get():
                zipped = sorted(zipped,
                                key=lambda attr: order(attr[column]),
                                reverse=True)
                reverse = True
            else:
                zipped = sorted(zipped, key=lambda attr: order(attr[column]))
                reverse = False

            (parser.numbers,
             parser.tracks,
             parser.types,
             parser.artists,
             parser.composers,
             parser.disc_num,
             parser.lyrics,
             parser.files) = zip(*zipped)

            for i in range(len(self.tag_names)):
                self.tag_names[i].set(self.tag_names[i].get()[:(self.tag_names[i].get().find(":") + 1)])

            # sipecka sa furt posuva - tkinter nepouziva monospace font
            spaces = 25 - len(self.tag_names[column].get())
            # print(self.tag_names[column].get() + " "*spaces + "▼")
            if reverse is True:
                self.tag_names[column].set(self.tag_names[column].get() +
                                           " "*spaces + "▼")
            else:
                self.tag_names[column].set(self.tag_names[column].get() +
                                           " "*spaces + "▲")

            self.re_init()
        except Exception as e:
            log_gui.exception(e)
            print(e)
            global shared_vars
            shared_vars.exception = str(e)
    """
    def select_all(self):
        if self.check_all.get() == 1:
            value = 1
        else:
            value = 0

        for i in range(len(self.check_bind)):
            self.check_bind[i].set(value)
    """
    def select_json(self):
        global shared_vars
        shared_vars.write_json = self.write_json.get()

    def select_offline_debbug(self):
        global shared_vars
        shared_vars.offline_debbug = self.offline_debbug.get()

    def display_image(self, root):

        if parser.cover_art is not None:
            size = 109

            im = Image.open(io.BytesIO(parser.cover_art))
            im.thumbnail((size, size), Image.ANTIALIAS)
            photo = ImageTk.PhotoImage(im)

            cover_art = ttk.Labelframe(root, text='Cover art', borderwidth=3)
            cover_art.grid(row=0, column=6, columnspan=2, rowspan=4)

            cv = Canvas(master=cover_art, height=size, width=size)
            cv.create_image(0, 0, image=photo, anchor='nw')
            cv.grid(row=0, column=7, columnspan=1, rowspan=4)

            # need to keep referenc to image otherwise python garbge
            # collector makes it transparent
            # http://effbot.org/pyfaq/why-do-my-tkinter-images-not-appear.htm
            self.photo = photo


class Scrollable_frame(Frame):

    def __init__(self, root, row, col, row_span, col_span):

        Frame.__init__(self, root)
        canvas_height = row_span*21

        remaining_space = root.winfo_height() - 21*7

        if canvas_height > remaining_space:
            canvas_height = remaining_space

        # width +25 if checkboxes are present
        self.canvas = Canvas(root, borderwidth=0, background="grey95",
                             width=126 * col_span, height=canvas_height)
        self.canvas.bind_all("<MouseWheel>", self._on_mousewheel)
        self.frame = Frame(self.canvas, style="BG.TLabel")
        self.vsb = Scrollbar(root, orient="vertical",
                             command=self.canvas.yview)
        self.canvas.configure(yscrollcommand=self.vsb.set)

        self.vsb.grid(row=row, column=col + col_span,
                      rowspan=row_span, sticky="nsew")
        self.canvas.grid(row=row, column=col,
                         columnspan=col_span, rowspan=row_span)
        self.canvas.create_window((4, -4), window=self.frame,
                                  anchor="nw", tags="self.frame")

        self.frame.bind("<Configure>", self.onFrameConfigure)

    def onFrameConfigure(self, event):
        '''Reset the scroll region to encompass the inner frame'''
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))

    def _on_mousewheel(self, event):
        self.canvas.yview_scroll(int(-1*(event.delta/120)), "units")


class Text_box(Text):

    def __init__(self, root, app, pos, row, col, rowspan, colspan):

        super(Text_box, self).__init__()
        self.root = root
        self.pos = pos
        self.app = app

        self.myText_Box = Text(root, width=30, height=rowspan)
        self.myText_Box.grid(row=row, column=col,
                             rowspan=rowspan, columnspan=colspan)

        self.vsb = Scrollbar(root, orient="vertical",
                             command=self.myText_Box.yview)
        self.myText_Box.configure(yscrollcommand=self.vsb.set)
        self.vsb.grid(row=row, column=col + colspan,
                      rowspan=rowspan, sticky='nsew')

    def text_check(self):
        lyrics = StringVar()
        lyrics.set(self.myText_Box.get("1.0",  END))

        self.app.lyrics[self.pos] = lyrics
        self.app.lyrics_preview[self.pos].set(lyrics.get()[:30])

        self.root.after(250, self.text_check)

    def insert(self, text):
        self.myText_Box.insert(INSERT, text)

    def _on_mousewheel(self, event):
        self.myText_Box.yview_scroll(int(-1*(event.delta/120)), "units")


class Menu_bar(Menu):

    def __init__(self, root, app):

        super(Menu_bar, self).__init__()
        self.app = app
        self.menubar = Menu(root)

        # unused filemenu
        filemenu = Menu(self.menubar, tearoff=0)
        filemenu.add_command(label="New", command=self.donothing)
        filemenu.add_command(label="Open", command=self.donothing)
        filemenu.add_command(label="Save", command=self.donothing)
        filemenu.add_separator()
        filemenu.add_command(label="Exit", command=root.quit)
        self.menubar.add_cascade(label="File", menu=filemenu)

        # open external programs menu
        openmenu = Menu(self.menubar, tearoff=0)
        openmenu.add_command(label="Directory", command=app.open_dir)
        openmenu.add_command(label="Wikipedia", command=app.open_browser)
        openmenu.add_command(label="Cover art search",
                             command=self.image_search)
        openmenu.add_command(label="Mp3tag", command=app.run_Mp3tag)
        self.menubar.add_cascade(label="Open", menu=openmenu)

        # save tags menu
        savemenu = Menu(self.menubar, tearoff=0)
        savemenu.add_command(label="Only Lyrics",
                             command=lambda: app.save_all(True))
        savemenu.add_command(label="All Tags",
                             command=lambda: app.save_all(False))
        self.menubar.add_cascade(label="Save", menu=savemenu)

        # unused heplmenu
        helpmenu = Menu(self.menubar, tearoff=0)
        helpmenu.add_command(label="Help Index", command=self.donothing)
        helpmenu.add_command(label="Git", command=self.donothing)
        helpmenu.add_command(label="About...", command=self.about)
        self.menubar.add_cascade(label="Help", menu=helpmenu)

        root.config(menu=self.menubar)

    def donothing(self):
        pass

    def about(self):
        with open(os.path.join(module_path(), "README"), "r") as infile:
            info = infile.read()

        messagebox.showinfo("About", info)

    def image_search(self):
        url_start = r"https://www.google.com/search?q="
        url_end = r"""&tbm=isch&source=lnt&tbs=isz:l&sa=X&ved=
                      0ahUKEwiRpJa7zIXdAhUqIMUKHay3CZUQpwUIHQ&biw=
                      1299&bih=760&dpr=1.25"""
        url_mid = parser.album.casefold().replace(" ", "+") + "+" + parser.band
        try:
            webbrowser.open_new_tab(url_start + url_mid + url_end)
        except Exception as e:
            log_gui.exception(e)
            print(e)
            global shared_vars
            shared_vars.exception = str(e)
        # https://www.google.com/search?q=theatre+of+dimensions+xandria&tbm=isch&source=lnt&tbs=isz:l&sa=X&ved=0ahUKEwiRpJa7zIXdAhUqIMUKHay3CZUQpwUIHQ&biw=1299&bih=760&dpr=1.25


def main():

    def conditions_check():
        """
        checks for answers to questins the main app asks
        the sends them back to app
        """

        global shared_vars
        global parser

        try:
            # log_gui.info("conditions check - shared_vars.done: "
            #  + str(shared_vars.done))

            if shared_vars.wait is True:

                if shared_vars.switch == "genres":
                    log_gui.info("initialize question window")
                    app.lock.acquire()
                    if len(parser.genres) == 0:
                        parser.selected_genre = app.ask_multiple_choice_question("Input genre:", parser.genres)
                    else:
                        parser.selected_genre = app.ask_multiple_choice_question("Select genre:", parser.genres)
                    app.lock.release()

                if shared_vars.load is True:
                    root.after(0, app.re_init)

                if shared_vars.switch == "comp":
                    app.lock.acquire()
                    shared_vars.assign_artists = messagebox.askyesno("Title", "Do you want to copy artists to composers?")
                    app.lock.release()

                if shared_vars.switch == "lyrics":
                    log_gui.info("ask to find lyrics")
                    app.lock.acquire()
                    shared_vars.write_lyrics = messagebox.askyesno("Title", "Do you want to find lyrics?")
                    app.lock.release()

                app.lock.acquire()
                shared_vars.load = False
                shared_vars.switch = None
                shared_vars.wait = False
                app.lock.release()

            app.lock.acquire()
            if shared_vars.done is False:
                root.after(100, conditions_check)
            else:
                # announce that gui has reached the barrier
                log_gui.info("gui reached barrier")
                shared_vars.barrier.wait()

                log_gui.info("start re_init function")
                root.after(0, app.re_init)
                app.display_image(root)
            app.lock.release()

        except Exception as e:
            log_gui.exception(e)
            print(e)
            shared_vars.exception = str(e)

    def exception_check():
        global shared_vars
        if shared_vars.exception is not None:
            messagebox.showerror("Exception", shared_vars.exception)
            shared_vars.exception = None

        if shared_vars.warning is not None:
            messagebox.showwarning("Warning", shared_vars.warning)
            shared_vars.warning = None

        if shared_vars.ask_exit is not None:
            terminate = messagebox.askyesno("Warning", shared_vars.ask_exit +
                                            "\n\n" +
                                            "Do you want to stop the search?")
            if terminate is True:
                shared_vars.wait_exit = False
                shared_vars.terminate_app = True

                time.sleep(0.03)
                root.destroy()
            else:
                shared_vars.wait_exit = False
                shared_vars.ask_exit = None

        root.after(500, exception_check)

    # initialize main app window
    root = Tk()
    root.geometry("1300x700+150+50")
    app = Tkinter_GUI(root)

    root.after(0, conditions_check)
    root.after(0, exception_check)
    root.iconbitmap(os.path.join(module_path(), "files/icon.ico"))

    # create menubar
    Menu_bar(root, app)

    # define buttons
    browse_button = Button(master=root, text="Browse",
                           command=app.select_dir)
    browse_button.grid(row=1, column=4)

    run_button = Button(master=root, text="Wiki search",
                        command=app.run_search)
    run_button.grid(row=2, column=4)

    lyrics_button = Button(master=root, text="Lyrics search",
                           command=app.run_lyrics_search)
    lyrics_button.grid(row=3, column=4)

    json_write = Checkbutton(master=root, text="Write json?",
                             variable=app.write_json,
                             command=app.select_json,
                             onvalue=True, offvalue=False)
    json_write.grid(row=1, column=5)

    if we_are_frozen() is False:
        offline_debbug = Checkbutton(master=root, text="Offline debbug?",
                                     variable=app.offline_debbug,
                                     command=app.select_offline_debbug,
                                     onvalue=True, offvalue=False)
        offline_debbug.grid(row=1, column=6)

    # data input frame
    input_dada = ttk.Labelframe(root, text='Input:', borderwidth=3)
    input_dada.grid(row=1, column=0, columnspan=4, rowspan=2, sticky="ew")

    # field dispalying selected directory
    display_dir = ttk.Entry(master=input_dada, textvariable=app.input_work_dir,
                            justify=LEFT, cursor="xterm", style="C.TEntry")
    display_dir.grid(row=1, column=0, columnspan=4, sticky="ew")

    # labels designating input
    ttk.Label(master=input_dada, text="                  Input Artist: ",
              anchor="e", relief=FLAT, cursor="xterm",
              style="BG.TLabel").grid(row=2, column=0, sticky="ew")
    ttk.Label(master=input_dada, text="                  Input Album: ",
              anchor="e", relief=FLAT, cursor="xterm",
              style="BG.TLabel").grid(row=2, column=2, sticky="ew")

    # ediatable fields for artist and album input
    band_entry = ttk.Entry(master=input_dada,
                           textvariable=app.input_band,
                           justify=LEFT, cursor="xterm", style="C.TEntry")
    band_entry.focus()
    band_entry.icursor(0)
    band_entry.grid(row=2, column=1, sticky="ew")

    album_entry = ttk.Entry(master=input_dada,
                            textvariable=app.input_album,
                            justify=LEFT, cursor="xterm", style="C.TEntry")
    album_entry.grid(row=2, column=3, sticky="ew")
    album_entry.bind("<Return>", app.run_search)

    # create labelframe for commmon entries
    common_labels = ttk.Labelframe(root, text="Common Tags:")
    common_labels.grid(row=3, column=0, rowspan=2, columnspan=4)

    # display tags common for all tracks
    ttk.Label(master=common_labels, text="Album artist:", anchor="w",
              relief=FLAT, cursor="xterm",
              style="BG.TLabel").grid(row=4, column=0)

    ttk.Label(master=common_labels, text="Album:", anchor="w",
              relief=FLAT, cursor="xterm",
              style="BG.TLabel").grid(row=4, column=1)

    ttk.Label(master=common_labels, text="Year:", anchor="w",
              relief=FLAT, cursor="xterm",
              style="BG.TLabel").grid(row=4, column=2)

    ttk.Label(master=common_labels, text="Genre:", anchor="w",
              relief=FLAT, cursor="xterm",
              style="BG.TLabel").grid(row=4, column=3)

    # editable fields for common tags
    ttk.Entry(master=common_labels, textvariable=app.band,
              justify=LEFT, cursor="xterm",
              style="C.TEntry").grid(row=5, column=0)

    ttk.Entry(master=common_labels, textvariable=app.album,
              justify=LEFT, cursor="xterm",
              style="C.TEntry").grid(row=5, column=1)

    ttk.Entry(master=common_labels, textvariable=app.release_date,
              justify=LEFT, cursor="xterm",
              style="C.TEntry").grid(row=5, column=2)

    ttk.Entry(master=common_labels, textvariable=app.selected_genre,
              justify=LEFT, cursor="xterm",
              style="C.TEntry").grid(row=5, column=3)

    # labels for tags that are not common
    tag_labels = []
    for i in range(8):
        tag_labels.append(ttk.Label(master=root,
                                    textvariable=app.tag_names[i],
                                    relief=FLAT, cursor="xterm",
                                    style="BG.TLabel", width=20))
        tag_labels[-1].grid(row=7, column=i)
        tag_labels[-1].bind("<Button-1>",
                            lambda event, pos=i: app.sort_shit(pos))

    # ttk.Checkbutton(master=root, variable=app.check_all, width = 0,
    # command = app.select_all).grid(row=7, column = 0, columnspan = 1)

    root.mainloop()

if __name__ == '__main__':
    main()
