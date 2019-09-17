
from multiprocessing import Process


def first_process():
    from Config import webcam, feed
    from threading import Lock
    import queue
    from UserInterface import FaceRecognition

    webcam = webcam()
    webcam.init("Microsoft® LifeCam HD-3000 - 1")
    webcam.set_callback()
    webcam.set_callback_properties()
    webcam.grabber_cb.grab_sample()
    webcam.run()

    images_queue = queue.Queue()

    lock = Lock()
    thread1 = feed(lock, webcam.queue, images_queue)

    lek = FaceRecognition(images_queue)
    lek.run()
def second_process():
    print("got it")
if __name__ == '__main__':
    p = Process(target=first_process(),)
    p2 = Process(target=second_process(), )
    p.start()
    p2.start()
    while(True):
        print("main works")
