from kivy.app import App
from kivy.uix.gridlayout import GridLayout
from kivy.uix.label import Label
from kivy.graphics import Rectangle,Color
from kivy.uix.boxlayout import BoxLayout
from  kivy.graphics.texture import Texture
from kivy.core.window import Window
from kivy.clock import Clock

from Config import webcam_info
from ListView import RV
from kivy.uix.image import Image

print(Window.size)
Window.maximize()
print(Window.size)

from Config import webcam,feed
from threading import Lock
import queue




class Screen(BoxLayout):

    def __init__(self,**kwargs):
        super(Screen, self).__init__(**kwargs)


        self.orientation = 'horizontal'


        self.img=Image()


        self.add_widget(RV())

        self.add_widget(Label(text='CameraView'))

        self.add_widget(self.img)

        Clock.schedule_interval(self.update, 1.0/15.0)
    def set_queue(self,queue):
        self.queue=queue

    def update(self,dt):

        from Config import webcam_info,webcam

        webcam_info = webcam_info()
        cameras = webcam_info.list_webcams()


        for child in self.children:
            if isinstance(child, RV):
                child.data = [{'text': camera} for camera in cameras]

        buf=self.queue.get(0)
        buf = buf.tostring()
        texture1 = Texture.create(size=(640, 480), colorfmt='bgr')
        texture1.blit_buffer(buf, colorfmt='bgr', bufferfmt='ubyte')
        self.img.texture = texture1

class FaceRecognition(App):
    def __init__(self,queue,**kwargs):
        super(FaceRecognition, self).__init__(**kwargs)
        self.Screen = Screen()
        self.Screen.set_queue(queue)

    def build(self):
        return self.Screen

if __name__ == '__main__':
    webcam = webcam()
    webcam.init("Microsoft® LifeCam HD-3000 - 1")
    webcam.set_callback()
    webcam.set_callback_properties()
    webcam.grabber_cb.grab_sample()
    webcam.run()

    images_queue = queue.Queue()

    lock = Lock()
    thread1 = feed(lock, webcam.queue, images_queue)

    lek=MyApp(images_queue)
    lek.run()

