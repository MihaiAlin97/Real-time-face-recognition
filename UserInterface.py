from kivy.app import App
from kivy.uix.label import Label
from kivy.uix.boxlayout import BoxLayout
from  kivy.graphics.texture import Texture
from kivy.core.window import Window
from kivy.clock import Clock


from ListView import RV
from kivy.uix.image import Image


class Screen(BoxLayout):

    def __init__(self,**kwargs):
        super(Screen, self).__init__(**kwargs)


        self.orientation = 'horizontal'


        self.img=Image()


        self.add_widget(RV())

        self.add_widget(self.img)

        Clock.schedule_interval(self.update, 1.0/15.0)
    def set_queue(self,queue):
        self.queue=queue

    def update(self,dt):

        from Config import webcam_info,webcam
        import cv2

        webcam_info = webcam_info()
        cameras = webcam_info.list_webcams()


        for child in self.children:
            if isinstance(child, RV):
                child.data = [{'text': camera} for camera in cameras]

        buf=self.queue.get(0)
        buf=cv2.flip(buf,0)
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
        Window.maximize()
        return self.Screen