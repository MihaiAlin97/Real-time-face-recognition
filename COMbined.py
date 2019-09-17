
from Config import webcam,feed
import queue
from threading import Lock
import cv2

if __name__ == "__main__":
    webcam = webcam()
    webcam.init("Microsoft® LifeCam HD-3000 - 1")
    webcam.set_callback()
    webcam.set_callback_properties()
    webcam.grabber_cb.grab_sample()
    webcam.run()

    images_queue = queue.Queue()
    lock = Lock()

    for i in range (0,1):
        thread1 = feed(lock, webcam.queue, images_queue)

    while True:
        print("showing")
        if images_queue.empty() == False:
            img = images_queue.get(0)
            if cv2.waitKey(1) & 0xFF == ord('x'):
                break
            cv2.imshow("dsafas", img)
        else:
            print("empty images queue")
            pass
    cv2.destroyAllWindows()
