from ctypes import *
import xchat

__module_name__        = "treenumbers"
__module_version__     = "1.0"
__module_description__ = "Display tab numbers and an unread messages counter"

# from gtype.h
class GTypeClass(Structure):
    _fields_ = [("g_type", c_uint)]
class GTypeInstance(Structure):
    _fields_ = [("g_class", POINTER(GTypeClass))]

class GtkTreeIter(Structure):
    _fields_ = [("stamp",      c_int)
               ,("user_data",  c_void_p)
               ,("user_data2", c_void_p)
               ,("user_data3", c_void_p)
               ]

# gparamspecs.h
class GParamSpec(Structure):
    _fields_ = [("g_type_instance", GTypeInstance)
               ,("name", c_char_p)
               ,("flags", c_uint)
               ,("value_type", c_ulong)
               ,("owner_type", c_ulong)
               ]

class User(Structure):
    _fields_ = [("nick",       c_char * 30)
               ,("hostname",   c_char_p)
               ,("realname",   c_char_p)
               ,("servername", c_char_p)
               ]

# hexchat.h
class MSProxyState(Structure):
    _fields_ = [("clientid", c_int)
               ,("serverid", c_int)
               ,("seq_recv", c_char)
               ,("seq_sent", c_char)
               ]

class Server(Structure):
    _fields_ = [("f01", c_void_p) # stupid function pointers are at beginning
               ,("f02", c_void_p)
               ,("f03", c_void_p)
               ,("f04", c_void_p)
               ,("f05", c_void_p)
               ,("f06", c_void_p)
               ,("f07", c_void_p)
               ,("f08", c_void_p)
               ,("f09", c_void_p)
               ,("f10", c_void_p)
               ,("f11", c_void_p)
               ,("f12", c_void_p)
               ,("f13", c_void_p)
               ,("f14", c_void_p)
               ,("f15", c_void_p)
               ,("f16", c_void_p)
               ,("f17", c_void_p)
               ,("f18", c_void_p)
               ,("f19", c_void_p)
               ,("f20", c_void_p)
               ,("f21", c_void_p)
               ,("f22", c_void_p)
               ,("f23", c_void_p)
               ,("f24", c_void_p)
               ,("f25", c_void_p)
               ,("f26", c_void_p)
               ,("f27", c_void_p)
               ,("f28", c_void_p)
               ,("f29", c_void_p)
               ,("f30", c_void_p)
               ,("f31", c_void_p)
               ,("f32", c_void_p)
               ,("f33", c_void_p)
               ,("f34", c_void_p)
               ,("f35", c_void_p)
               ,("f36", c_void_p)
               ,("f37", c_void_p)
               ,("port",               c_int)
               ,("sok",                c_int)
               ,("sok4",               c_int)
               ,("sok6",               c_int)
               ,("proxy_type",         c_int)
               ,("proxy_sok",          c_int)
               ,("proxy_sok4",         c_int)
               ,("proxy_sok6",         c_int)
               ,("msp_state",          MSProxyState)
               ,("id",                 c_int)
               #ifdef USE_SSL
               ,("ssl",                c_void_p)
               ,("ssl_do_connect_tag", c_int)
               #else
               #,("ssl_", c_void_p)
               #endif
               ,("childread",          c_int)
               ,("childwrite",         c_int)
               ,("childpid",           c_int)
               ,("iotag",              c_int)
               ,("recondelay_tag",     c_int)
               ,("joindelay_tag",      c_int)
               ,("hostname",           c_char * 128)
               ,("servername",         c_char * 128)
               ]

class Session(Structure):
    _fields_ = [("alert_beep",        c_byte)
               ,("alert_taskbar",     c_byte)
               ,("alert_tray",        c_byte)
               ,("text_hidejoinpart", c_byte)
               ,("text_logging",      c_byte)
               ,("text_scrollback",   c_byte)
               ,("server",            POINTER(Server))
               ,("usertree_alpha",    c_void_p)
               ,("usertree",          c_void_p)
               ,("me",                POINTER(User))
               ,("channel",           c_char * 300)
               ]

# chanview.c
class Chan(Structure):
    _fields_ = [("chanview",      c_void_p)
               ,("iter",          GtkTreeIter)
               ,("userdata",      POINTER(Session))
               ,("family",        c_void_p)
               ,("impl",          c_void_p)
               ,("icon",          c_void_p)
               ,("allow_closure", c_short)
               ,("tag",           c_short)
               ]

# since 2.9.6b1, gtkwin_ptr is properly set as the address in a hex string
gtkwin = int(xchat.get_info("gtkwin_ptr"), 16)

# TODO detect platform and appropriately load the DLL or SO
gtk     = cdll.LoadLibrary("gtk-win32-2.0.dll")
gobject = cdll.LoadLibrary("gobject-2.0.dll")
glib    = cdll.LoadLibrary("glib-2.0.dll")

gobject.g_type_check_instance_is_a.restype = c_bool
gobject.g_object_class_list_properties.argtypes = [c_void_p, POINTER(c_int)]
gobject.g_object_class_list_properties.restype = POINTER(POINTER(GParamSpec))
gobject.g_type_name.restype = c_char_p
gtk.gtk_tree_model_iter_next.restype = c_bool
gtk.gtk_tree_path_to_string.restype = c_char_p

GTKCALLBACK = CFUNCTYPE(None, c_void_p, c_void_p)

# can't mutate global data from C callbacks
class TreeNumerator:
    treestore     = None
    activity      = {}
    prev_channels = []
    timerhook     = None

    def __init__(self):
        self.get_tree_store()

    def get_tree_store(self):
        if self.treestore:
            return self.treestore
        gtk.gtk_container_foreach(gtkwin,
                GTKCALLBACK(self.get_tree_store_cb), None)
        return self.treestore

    def get_tree_store_cb(self, a, data):

        gobj = cast(a, POINTER(GTypeInstance))

        if gobject.g_type_check_instance_is_a(gobj,
                gtk.gtk_tree_view_get_type()):
            number = 1
            gtk.gtk_tree_view_set_show_expanders(gobj, 0)
            gtk.gtk_tree_view_set_enable_tree_lines(gobj, 0)
            gtk.gtk_tree_view_set_level_indentation(gobj, 0)
            store = gtk.gtk_tree_view_get_model(gobj)

            if gobject.g_type_check_instance_is_a(
                    cast(store, POINTER(GTypeInstance)),
                    gtk.gtk_tree_store_get_type()):
                self.treestore = store
                return

        gtk.gtk_container_foreach(a, GTKCALLBACK(self.get_tree_store_cb), None)

    def process_tab(self, iter, n, seek=True):
        v = c_char_p()
        chan = POINTER(Chan)()
        gtk.gtk_tree_model_get(self.treestore, byref(iter),
                1, byref(chan), # COL_CHAN
                -1)

        if chan:
            oldname = chan.contents.userdata.contents.channel
            server = chan.contents.userdata.contents.server
            activity = 0
            if server:
                servername = server.contents.servername
                if servername:
                    activity = self.get_activity(servername, oldname)

            newlabel = "(%d) %s" % (n, oldname.strip())
            if activity != 0:
                newlabel = "%s : %d" % (newlabel, activity)

            gtk.gtk_tree_store_set(self.treestore, byref(iter),
                    0, c_char_p(newlabel), # COL_NAME
                    -1)

        if seek:
            return gtk.gtk_tree_model_iter_next(self.treestore, iter)
        else:
            return True

    enumerating = False
    def enumerate_tabs(self):
        if self.enumerating:
            return

        store = self.get_tree_store()
        number = 1

        iter = GtkTreeIter()
        has_next = gtk.gtk_tree_model_get_iter_first(
                store, byref(iter))

        while has_next:
            self.process_tab(iter, number, False)

            child = GtkTreeIter()
            has_children = gtk.gtk_tree_model_iter_children(
                    store, byref(child), byref(iter))

            number = number + 1

            while self.process_tab(child, number) and has_children:
                number = number + 1

            if has_children:
                number = number + 1

            has_next = gtk.gtk_tree_model_iter_next(self.treestore, iter)
        self.enumerating = False

    def enumerate_cb(self, data):
        try:
            self.enumerate_tabs()
        except:
            pass
        if self.timerhook:
            xchat.unhook(self.timerhook)
        self.timerhook = None

    def get_update_cb(self, delay=250, force=False, eatmode=xchat.EAT_NONE):

        def update_cb(word=None, word_eol=None, data=None):
            channels = map(lambda c: c.channel, xchat.get_list("channels"))
            if force or (
                    self.prev_channels != channels and not self.timerhook):
                self.timerhook = xchat.hook_timer(delay, self.enumerate_cb)
                self.prev_channels = channels
            return eatmode
        return update_cb

    def get_activity(self, server, channel):
        key = server + ":" + channel
        if key not in self.activity:
            self.activity[key] = 0
        return self.activity[key]

    def add_activity(self, server, channel):
        key = server + ":" + channel
        if key not in self.activity:
            self.activity[key] = 0
        self.activity[key] = self.activity[key] + 1
        if not self.timerhook:
            self.timerhook = xchat.hook_timer(250, self.enumerate_cb)

    def reset_activity_cb(self, word=None, word_eol=None, data=None):
        channel = xchat.get_context().get_info("channel")
        server = xchat.get_context().get_info("server")
        key = server + ":" + channel
        self.activity[key] = 0
        return xchat.EAT_NONE

    def activity_cb(self, word=None, word_eol=None, data=None):
        ctx = xchat.get_context()
        if ctx != xchat.find_context():
            channel = xchat.get_context().get_info("channel")
            server = xchat.get_context().get_info("server")
            self.add_activity(server, channel)
        return xchat.EAT_NONE

    def update_timer_cb(self, ignore_data):
        try:
            self.enumerate_tabs()
        except RuntimeError as e:
            self.log("unable to enumerate tabs: %s" % e)
        return 1

    def log(self, msg):
        ctx = xchat.find_context(channel=">>python<<")
        if ctx:
            # using emit_print results in an infinite loop with activity_cb
            # even when filtering by channel != >>python<<
            #ctx.emit_print("Channel Message", "treenumbers", msg)
            ctx.prnt("treenumbers: %s" % msg)

numerator = TreeNumerator()

# open context seems to overwrite any label changes, delay longer
hooks = []

def unload_cb(arg):
    for hook in hooks:
        xchat.unhook(hook)
    numerator.log("successfully unloaded")

hooks.append(xchat.hook_unload(unload_cb))

def init(ignore_data=None):
    # concurrent updates, or near concurrent updates seem to trigger crashes
    # perform updates every half second instead
    hooks.append(xchat.hook_timer(500, numerator.update_timer_cb))
    #hooks.append(xchat.hook_print("Key Press", numerator.get_update_cb()))
    #hooks.append(xchat.hook_print("Open Context",
    #    numerator.get_update_cb(750, True)))
    #hooks.append(xchat.hook_print("Focus Tab",
    #    numerator.get_update_cb(force=True)))
    hooks.append(xchat.hook_print("Focus Tab",
        numerator.reset_activity_cb))
    #hooks.append(xchat.hook_print("Close Context",
    #    numerator.get_update_cb(force=True)))

    for evt in ('Channel Action Hilight'
               ,'Channel Msg Hilight'
               ,'Channel Action'
               ,'Channel Message'
               ,'Private Message to Dialog'
               ,'Private Action to Dialog'):
        hooks.append(xchat.hook_print(evt, numerator.activity_cb))


    numerator.enumerate_tabs()
    numerator.log("successfully loaded")
    return 0 # do not repeat timer

# too soon and the plugin fails to load at startup, too many events firing...
# happens when connecting to my BNC, maybe not a problem with normal servers
xchat.hook_timer(5000, init)