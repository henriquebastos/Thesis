import Tkinter as tk

class Node(tk.Canvas):
    def __init__(self, *args, **kwargs):
        tk.Canvas.__init__(self, *args)

        self.text_box = self.create_text(0,0)
        # Create small box
        # Variable Section
        # Method Section
        # Method's Variables
        # From lines
        # To lines

    def set_text(new_text):
        self.text_box.delete(0.0, tk.END)
        self.text_box.INSERT(tk.INSERT, new_text)

    def get_text():
        return self.text_box.get('0.0', 'end-1c')

class SampleApp(tk.Tk):
    '''Illustrate how to drag items on a Tkinter canvas'''

    def __init__(self, *args, **kwargs):
        tk.Tk.__init__(self, *args, **kwargs)

        # create a canvas
        self.canvas = tk.Canvas(width=400, height=400)
        self.canvas.pack(fill="both", expand=True)

        # this data is used to keep track of an 
        # item being dragged
        self._drag_data = {"x": 0, "y": 0, "item": None}

        # create a couple movable objects
        # self._create_token((100, 100), "white")
        self._create_token((200, 100), "red")

        # add bindings for clicking, dragging and releasing over
        # any object with the "token" tag
        self.canvas.tag_bind("token", "<ButtonPress-1>", self.OnTokenButtonPress)
        self.canvas.tag_bind("token", "<ButtonRelease-1>", self.OnTokenButtonRelease)
        self.canvas.tag_bind("token", "<B1-Motion>", self.OnTokenMotion)

    def _create_token(self, coord, color):
        '''Create a token at the given coordinate in the given color'''
        (x,y) = coord
        # node = Node()
        # self.canvas.insert(node, tk.INSERT)
        # self.canvas.create_oval(x-25, y-25, x+25, y+25, 
        #                         outline=color, fill=color, tags="token")
        
        # big_oval_id = self.canvas.create_oval(x-50, y-50, x+50, y+50, outline='blue', fill='blue', tags='token')
        # self.canvas.itemconfig(big_oval_id, fill='orange')
        # self.canvas.insert(big_oval_id, tk.INSERT, 'TEST')
        # textId = self.canvas.create_text(x, y, text='Object\nx=1', tags='token', borderwidth=1)
        # self.canvas.insert(textId, tk.INSERT, 'TEST')
        c = self.canvas.create_canvas(0, 0, tags='token')

        text_item = c.create_text(0, 0, anchor="w", text="Hello world!", fill="black")
        bbox = c.bbox(text_item)
        rect_item = c.create_rectangle(bbox, outline="red", fill="grey")
        c.tag_raise(text_item,rect_item)

        self.canvas.insert(c, tk.INSERT)
        

    def OnTokenButtonPress(self, event):
        '''Being drag of an object'''
        # record the item and its location
        self._drag_data["item"] = self.canvas.find_closest(event.x, event.y)[0]
        self._drag_data["x"] = event.x
        self._drag_data["y"] = event.y

    def OnTokenButtonRelease(self, event):
        '''End drag of an object'''
        # reset the drag information
        self._drag_data["item"] = None
        self._drag_data["x"] = 0
        self._drag_data["y"] = 0

    def OnTokenMotion(self, event):
        '''Handle dragging of an object'''
        # compute how much this object has moved
        delta_x = event.x - self._drag_data["x"]
        delta_y = event.y - self._drag_data["y"]
        # move the object the appropriate amount
        self.canvas.move(self._drag_data["item"], delta_x, delta_y)
        # record the new position
        self._drag_data["x"] = event.x
        self._drag_data["y"] = event.y

if __name__ == "__main__":
    app = SampleApp()
    app.mainloop()
