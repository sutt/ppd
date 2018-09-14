import random, os, sys
import threading
import Tkinter as tk
import GlobalsB as Globals


class GuiData:

    def __init__(self):
        self.record_on = False
        self.sv_fn = None

class BuildGuiB:

    def __init__(self, b_log=False):
        self.b_log = b_log
        self.record_button = None
        self.dir_entry = None
        self.entry_dir_valid = True
        self.int_jumpcut = None
        self.int_preview_frame = None
        self.int_resize_preview = None
        self.int_frame_size = None
        self.int_cam_num = None
        self.int_codec_enum = None
        self.int_buffer = None
        self.int_log_enum = None

    def cmd_quit(self):
        Globals.gui_cmd_quit = True

    def cmd_record_sw(self):
        ''' toggle gui_cmd_record global; reformat record button color '''
        if Globals.gui_cmd_record:
            Globals.gui_cmd_record = False
            Globals.sw_record_stop = True
            self.record_button.configure(bg = 'gray')
        else:
            Globals.gui_cmd_record = True
            Globals.sw_record_start = True
            self.record_button.configure(bg = '#000fff000')
        if self.b_log:
            print 'gui_cmd_record: ', str(Globals.gui_cmd_record)
        
    def get_sv_fn(self):
        ''' unique filename entry box -> global '''
        Globals.gui_unique_fn = str(self.sv_fn.get())
        #TODO - validate its unqiue in the directory
        if self.b_log:
            print 'setting gui_unique_fn to: ', Globals.gui_unique_fn

    def set_sv_fn(self, fn):
        ''' unqiue filename entry box, set value displayed in gui '''
        self.sv_fn.set(str(fn))
        if self.b_log:
            print 'setting sv_fn to: ', str(fn)

    def get_sv_dir(self, b_apply_sw=False):
        ''' directory path as text (relative) -> global
            if called with b_apply_sw:
             - a validation step to check if directory exists
             - finally sets a switch to recalc uniqueFn for new directory in guirecord
         '''
        _temp = Globals.gui_dir_path                  
        Globals.gui_dir_path = str(self.sv_dir.get())
        if self.b_log:
            print 'setting gui_dir_path to: ', Globals.gui_dir_path
        if not(b_apply_sw): return
        
        #Validation ----
        try:
            _dummy = os.listdir(Globals.gui_dir_path) 
            if not(self.entry_dir_valid):
                self.dir_entry.configure(bg = 'white')
                self.entry_dir_valid = True
            Globals.sw_gui_dir = True                  
            
        except:
            if self.b_log: print 'directory entry validation exception'
            Globals.gui_dir_path = _temp
            if self.entry_dir_valid:
                self.dir_entry.configure(bg = 'red')
                self.entry_dir_valid = False

    def set_sv_dir(self, dir_path):
        ''' directory path entry box, set value displayed in gui '''
        self.sv_dir.set(str(dir_path))
        if self.b_log:
            print 'setting sv_dir to: ', str(dir_path)

    def set_jumpcut_var(self):
        ''' set global boolean gui_b_jumpcut from radio button '''
        Globals.gui_b_jumpcut = bool(self.int_jumpcut.get())
        if self.b_log:
            print 'setting gui_b_jumpcut to: ', str(Globals.gui_b_jumpcut)

    def set_preview_frame_var(self):
        ''' set sw_preview_frame to True, the radio button value is irrelevant '''
        Globals.sw_preview_frame = True
        Globals.gui_b_preview_frame = not(bool(self.int_preview_frame.get()))
        if self.b_log:
            print 'setting sw_preview_frame to: ', str(Globals.sw_preview_frame)

    def set_resize_preview_var(self):
        ''' set sw_preview_frame to True, the radio button value is irrelevant '''
        Globals.gui_b_resize = not(bool(self.int_resize_preview.get()))
        if self.b_log:
            print 'setting gui_b_resize to: ', str(Globals.gui_b_resize)

    def set_frame_size_var(self):
        ''' set global boolean gui_b_jumpcut from radio button '''
        Globals.gui_frame_size_enum = int(self.int_frame_size.get())
        Globals.sw_camera_reset = True
        if self.b_log:
            print 'setting gui_frame_size_enum to: ', str(Globals.gui_frame_size_enum)

    def set_cam_num_var(self):
        ''' set global int gui_cam_num from radio button '''
        Globals.gui_cam_num = int(self.int_cam_num.get())
        Globals.sw_camera_reset = True
        if self.b_log:
            print 'setting gui_cam_num to: ', str(Globals.gui_frame_size_enum)

    def set_codec_enum_var(self):
        Globals.gui_codec_enum = int(self.int_codec_enum.get())
        Globals.sw_camera_reset = True

    def set_buffer_var(self):
        Globals.gui_b_buffer = bool(int(self.int_buffer.get()))
        Globals.sw_camera_reset = True

    def set_log_enum_var(self):
        Globals.gui_log_enum = int(self.int_log_enum.get())
        Globals.sw_camera_reset = True
        
        

    def build_gui_b(self, root):
        
        f1 = tk.Frame(root)
        f1.pack(side = tk.TOP)
        tk.Button(
             f1
            ,text = 'quit'
            ,command = self.cmd_quit
            ).pack()
        f1a = tk.Frame(root)
        f1a.pack(side = tk.TOP)

        self.record_button = tk.Button(
                f1a
                ,text = 'record toggle'
                ,bg = 'gray'
                ,command = self.cmd_record_sw
                )
        self.record_button.pack()

        f1a2 = tk.Frame(f1a)
        f1a2.pack(side = tk.TOP)
        
        tk.Label(
                f1a2
                ,text="filename:"
            ).pack(side=tk.LEFT)
        
        self.sv_fn = tk.StringVar()
        self.set_sv_fn(Globals.gui_unique_fn)
        
        self.fn_entry = tk.Entry(
                f1a2
                ,textvariable = self.sv_fn
                ,width = 16
                )
        self.fn_entry.pack(side=tk.LEFT)
        
        tk.Button(
                f1a2
                ,text = 'set'
                ,command = self.get_sv_fn
            ).pack(side=tk.LEFT)

        
        f1a3 = tk.Frame(f1a)
        f1a3.pack(side = tk.TOP)

        tk.Label(
                f1a3
                ,text="dir:"
            ).pack(side=tk.LEFT)

        self.sv_dir = tk.StringVar()
        self.set_sv_dir(Globals.gui_dir_path)
        
        self.dir_entry = tk.Entry(
                f1a3
                ,textvariable = self.sv_dir
                ,width = 20
                ,bg = 'white'
                )
        self.dir_entry.pack(side=tk.LEFT)
        
        tk.Button(
                f1a3
                ,text = 'set'
                ,command = lambda: self.get_sv_dir(True)
            ).pack(side=tk.LEFT)

        
        f1a4 = tk.Frame(root)
        f1a4.pack(side = tk.TOP)

        tk.Label(f1a4, text="On Stop Record:").pack(side=tk.LEFT)

        self.int_jumpcut = tk.IntVar()
        self.int_jumpcut.set(0)
        
        tk.Radiobutton(
             f1a4
            ,text="new file"
            ,variable=self.int_jumpcut
            ,value=0
            ,command=self.set_jumpcut_var
            ).pack(side=tk.LEFT)

        tk.Radiobutton(
             f1a4
            ,text="jump cut"
            ,variable=self.int_jumpcut
            ,value=1
            ,command=self.set_jumpcut_var
            ).pack(side=tk.LEFT)

        f1a5 = tk.Frame(root)
        f1a5.pack(side = tk.TOP)

        tk.Label(f1a5, text="Preview Frame:").pack(side=tk.LEFT)

        self.int_preview_frame = tk.IntVar()
        self.int_preview_frame.set(0)
        
        tk.Radiobutton(
             f1a5
            ,text="on"
            ,variable=self.int_preview_frame
            ,value=0
            ,command=self.set_preview_frame_var
            ).pack(side=tk.LEFT)

        tk.Radiobutton(
             f1a5
            ,text="off"
            ,variable=self.int_preview_frame
            ,value=1
            ,command=self.set_preview_frame_var
            ).pack(side=tk.LEFT)

        f1a5b = tk.Frame(root)
        f1a5b.pack(side = tk.TOP)

        tk.Label(f1a5b, text="Resize Preveiw:").pack(side=tk.LEFT)

        self.int_resize_preview = tk.IntVar()
        self.int_resize_preview.set(0)
        
        tk.Radiobutton(
             f1a5b
            ,text="on"
            ,variable=self.int_resize_preview
            ,value=0
            ,command=self.set_resize_preview_var
            ).pack(side=tk.LEFT)

        tk.Radiobutton(
             f1a5b
            ,text="off"
            ,variable=self.int_resize_preview
            ,value=1
            ,command=self.set_resize_preview_var
            ).pack(side=tk.LEFT)

        f1a6 = tk.Frame(root)
        f1a6.pack(side = tk.TOP)

        tk.Label(f1a6, text="Frame Size:").pack(side=tk.LEFT)

        self.int_frame_size = tk.IntVar()
        self.int_frame_size.set(0)
        
        tk.Radiobutton(  
            f1a6
            ,text="640"
            ,variable=self.int_frame_size
            ,value=0
            ,command=self.set_frame_size_var
            ).pack(side=tk.LEFT)

        tk.Radiobutton(  
            f1a6
            ,text="1280"
            ,variable=self.int_frame_size
            ,value=1
            ,command=self.set_frame_size_var
            ).pack(side=tk.LEFT)

        tk.Radiobutton(  
            f1a6
            ,text="1920"
            ,variable=self.int_frame_size
            ,value=2
            ,command=self.set_frame_size_var
            ).pack(side=tk.LEFT)

        f1a7 = tk.Frame(root)
        f1a7.pack(side = tk.TOP)

        tk.Label(f1a7, text="Cam num:").pack(side=tk.LEFT)

        self.int_cam_num = tk.IntVar()
        self.int_cam_num.set(0)
        
        tk.Radiobutton(  
            f1a7
            ,text="0"
            ,variable=self.int_cam_num
            ,value=0
            ,command=self.set_cam_num_var
            ).pack(side=tk.LEFT)

        tk.Radiobutton(  
            f1a7
            ,text="1"
            ,variable=self.int_cam_num
            ,value=1
            ,command=self.set_cam_num_var
            ).pack(side=tk.LEFT)

        tk.Radiobutton(  
            f1a7
            ,text="2"
            ,variable=self.int_cam_num
            ,value=2
            ,command=self.set_cam_num_var
            ).pack(side=tk.LEFT)

        
        f1a8 = tk.Frame(root)
        f1a8.pack(side = tk.TOP)
        
        tk.Label(f1a8, text="Codec:").pack(side=tk.LEFT)

        self.int_codec_enum = tk.IntVar()
        self.int_codec_enum.set(0)
        
        tk.Radiobutton(  
            f1a8
            ,text="h264"
            ,variable=self.int_codec_enum
            ,value=0
            ,command=self.set_codec_enum_var
            ).pack(side=tk.LEFT)

        tk.Radiobutton(  
            f1a8
            ,text="prompt"
            ,variable=self.int_codec_enum
            ,value=1
            ,command=self.set_codec_enum_var
            ).pack(side=tk.LEFT)

        tk.Radiobutton(  
            f1a8
            ,text="lossless"
            ,variable=self.int_codec_enum
            ,value=2
            ,command=self.set_codec_enum_var
            ).pack(side=tk.LEFT)

        
        f1a9 = tk.Frame(root)
        f1a9.pack(side = tk.TOP)
        
        tk.Label(f1a9, text="Save Buffer:").pack(side=tk.LEFT)

        self.int_buffer = tk.IntVar()
        self.int_buffer.set(0)
        
        tk.Radiobutton(  
            f1a9
            ,text="off"
            ,variable=self.int_buffer
            ,value=0
            ,command=self.set_buffer_var
            ).pack(side=tk.LEFT)

        tk.Radiobutton(  
            f1a9
            ,text="on"
            ,variable=self.int_buffer
            ,value=1
            ,command=self.set_buffer_var
            ).pack(side=tk.LEFT)

        
        f1a10 = tk.Frame(root)
        f1a10.pack(side = tk.TOP)
        
        tk.Label(f1a10, text="Log Type:").pack(side=tk.LEFT)

        self.int_log_enum = tk.IntVar()
        self.int_log_enum.set(0)
        
        tk.Radiobutton(  
            f1a10
            ,text="simple"
            ,variable=self.int_log_enum
            ,value=0
            ,command=self.set_log_enum_var
            ).pack(side=tk.LEFT)

        tk.Radiobutton(  
            f1a10
            ,text="detailed"
            ,variable=self.int_log_enum
            ,value=1
            ,command=self.set_log_enum_var
            ).pack(side=tk.LEFT)

        tk.Radiobutton(  
            f1a10
            ,text="none"
            ,variable=self.int_log_enum
            ,value=2
            ,command=self.set_log_enum_var
            ).pack(side=tk.LEFT)


        return root

class GuiB(threading.Thread):
    
    def __init__(self, b_log=False):
        threading.Thread.__init__(self)
        self.start()
        self.myGui = BuildGuiB(b_log=b_log)
        # self.globeGui = globeGui

    def callback(self):
        self.root.quit()

    def run(self):
        self.root = tk.Tk()
        self.root.protocol("WM_DELETE_WINDOW", self.callback)
        self.root = self.myGui.build_gui_b(self.root)
        self.root.mainloop()



if __name__ == "__main__":

    Globals.init()
    Globals.gui_cmd_quit = False
    Globals.gui_cmd_record = False
    Globals.gui_cmd_reset = False
    Globals.sw_record_start = False
    Globals.sw_record_stop = False
    Globals.gui_unique_fn = "------N/A------"
    Globals.gui_dir_path = "/"
    Globals.sw_gui_dir = False
    Globals.gui_b_jumpcut = False
    
    gui = GuiB(b_log=True)