
import threading
class PrelucrateFeed(object):
    """ Threading example class
    The run() method will be started and it will run in the background
    until the application exits.
    """

    def __init__(self, lock,source,output):
        """ Constructor
        :type interval: int
        :param interval: Check interval, in seconds
        """


        thread = threading.Thread(target=self.run, args=(lock,source,output,))
        thread.daemon = True                            # Daemonize thread
        thread.start()                                  # Start the execution

    def run(self,lock,source,output):
        import numpy as np
        import time
        while True:
            if source.empty() == False:
                print("rendering")
                start_time = time.time()
                with lock:
                    pBuffer = source.get(0)

                bsize = 480 * 640 * 3
                buffer_relevant_data = pBuffer[:bsize]

                frame = np.array(buffer_relevant_data)
                img = np.reshape(frame, (480, 640, 3))
                img = img[::-1]
                img = img.astype("uint8")
                with lock:
                    output.put(img)
                print("--- %s seconds ---" % (time.time() - start_time))
            else:
                print("empty buffer queeue")
                pass

