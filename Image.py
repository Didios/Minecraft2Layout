from tkinter import Canvas
from PIL import Image, ImageTk

class TkImage(Canvas):

    def __init__(self, *args, **kwargs):
        self.image_base = kwargs.pop('image', None)
        self.image = None

        Canvas.__init__(self, *args, **kwargs)
        self.bind("<Configure>", self.__resize__)
        self.__display__()

    def __display__(self):
        if not self.image_base:
            return
        self.delete('all')

        width_img, height_img = self.image_base.size
        width_cv, height_cv = self.winfo_width(), self.winfo_height()
        ratio = min(width_cv / width_img, height_cv / height_img)

        size = (int(width_img * ratio), int(height_img * ratio))

        self.image = ImageTk.PhotoImage(self.image_base.resize(size, resample=Image.NEAREST))
        self.create_image(width_cv / 2, height_cv / 2, anchor='center', image=self.image)

    def set_image(self, image):
        self.image_base = image
        self.__display__()

    def __resize__(self, event):
        self.__display__()

    def refresh(self):
        self.__display__()
