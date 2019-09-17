from kivy.app import App
from kivy.uix.gridlayout import GridLayout
from kivy.uix.label import Label
from kivy.graphics import Rectangle,Color
from kivy.uix.boxlayout import BoxLayout

from kivy.core.window import Window
from kivy.clock import Clock

from Config import webcam_info
from ListView import RV


print(Window.size)
Window.maximize()
print(Window.size)


class LoginScreen(BoxLayout):

    def __init__(self, **kwargs):
        super(LoginScreen, self).__init__(**kwargs)

        self.orientation = 'horizontal'

        lab=Label(text='Listdfsafsafasfas')


        self.add_widget(RV())

        self.add_widget(Label(text='CameraView'))

        self.add_widget(lab)

        Clock.schedule_interval(self.update, 1.0)

    def update(self,dt):

        from Config import webcam_info,webcam

        webcam_info = webcam_info()
        cameras = webcam_info.list_webcams()

        for child in self.children:
            if isinstance(child, RV):
                child.data = [{'text': camera} for camera in cameras]

class MyApp(App):

    def build(self):

        return LoginScreen()





if __name__ == '__main__':
    MyApp().run()

    from Config import webcam_info, webcam

    webcam_info = webcam_info()
    cameras = webcam_info.list_webcams()
    MyApp.data = [{'text': camera} for camera in cameras]
    print(MyApp.data)
