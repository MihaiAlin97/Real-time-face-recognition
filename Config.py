from comtypes import client, GUID, COMMETHOD, CoClass, IUnknown ,CoInitialize ,CoInitializeEx,CoUninitialize
from comtypes._comobject import COMObject

from comtypes.gen.DirectShowLib import (
    FilterGraph,
    CaptureGraphBuilder2,
    ICreateDevEnum,
    IBaseFilter,
    IBindCtx,
    IMoniker,
    IAMStreamConfig,
    IAMVideoControl,
)
from comtypes.gen.DexterLib import SampleGrabber, _AMMediaType , ISampleGrabberCB , NullRenderer

from comtypes.persist import IPropertyBag
from comtypes.automation import VARIANT

from ctypes import POINTER, Structure, c_longlong, c_long, HRESULT ,sizeof
from ctypes import windll, byref, cast, create_string_buffer, c_long ,c_ubyte
import queue
from ctypes.wintypes import (
    RECT, DWORD, LONG, WORD, ULONG, HWND,
    UINT, LPCOLESTR, LCID, LPVOID )

from ctypes import *

import threading
from multiprocessing import Manager

from HRESULT import buffer_hresult,buffer_error_hresult
import time

import HRESULT

quartz = client.GetModule("quartz.dll")
qedit = client.GetModule("qedit.dll")


OA_TRUE = -1
OA_FALSE = 0

IVideoWindow = quartz.IVideoWindow
IMediaControl = quartz.IMediaControl

CLSID_VideoInputDeviceCategory = GUID("{860BB310-5D01-11d0-BD3B-00A0C911CE86}")
CLSID_SystemDeviceEnum = GUID('{62BE5D10-60EB-11d0-BD3B-00A0C911CE86}')
CLSID_IPropertyBag = GUID('{55272A00-42CB-11CE-8135-00AA004BB851}')

MEDIATYPE_Video = GUID('{73646976-0000-0010-8000-00AA00389B71}')
MEDIATYPE_Interleaved = GUID('{73766169-0000-0010-8000-00aa00389b71}')
MEDIASUBTYPE_RGB24 = GUID('{e436eb7d-524f-11ce-9f53-0020af0ba770}')
FORMAT_VideoInfo = GUID('{05589f80-c356-11ce-bf01-00aa0055595a}')
PIN_CATEGORY_CAPTURE = GUID('{fb6c4281-0353-11d1-905f-0000c0cc16ba}')

REFERENCE_TIME = c_longlong

class BITMAPINFOHEADER(Structure):
    _fields_ = (
        ('size', DWORD),
        ('width', LONG),
        ('height', LONG),
        ('planes', WORD),
        ('bit_count', WORD),
        ('compression', DWORD),
        ('image_size', DWORD),
        ('x_pels_per_meter', LONG),
        ('y_pels_per_meter', LONG),
        ('clr_used', DWORD),
        ('clr_important', DWORD),
    )
class VIDEOINFOHEADER(Structure):
    _fields_ = (
        ('source', RECT),
        ('target', RECT),
        ('bit_rate', DWORD),
        ('bit_error_rate', DWORD),
        ('avg_time_per_frame', REFERENCE_TIME),
        ('bmi_header', BITMAPINFOHEADER),
    )


class SampleGrabberCB(COMObject):
    _com_interfaces_ = [qedit.ISampleGrabberCB]
    def __init__(self, callback):
        self.callback = callback
        self.cnt = 0
        self.take_sample = False
        self.image_resolution = None
        self.size=None
        super(SampleGrabberCB, self).__init__()

    def grab_sample(self):
        self.take_sample = True
        print("inside grab sample")
    def SampleCB(self, this, SampleTime, pSample):
        return 0

    def BufferCB(self, this, SampleTime, pBuffer, BufferLen):
        if self.take_sample == True:
            self.cnt=self.cnt+1
            self.callback(pBuffer)
        else:
            print("inside b")
        return 0


class VidCapError(Exception):
	pass

class webcam_info:
    def __init__(self):
        ##dict of webcams as keys and monikers of them as values
        self.webcam_list={}
        ##dict for storing how many webcams with same name are present
        self.duplicate_webcam_count = {}
        self.obtain_webcams()
    def obtain_webcams(self):##call to refresh available webcams

        self.webcam_list.clear()
        self.duplicate_webcam_count.clear()
        ##create dev_enum
        device_enumerator = client.CreateObject(CLSID_SystemDeviceEnum, interface=ICreateDevEnum)
        ##create class enum
        class_enumerator = device_enumerator.CreateClassEnumerator(CLSID_VideoInputDeviceCategory, 0)

        ##get moniker from class enum
        (moniker, fetch) = class_enumerator.RemoteNext(1)
        while(fetch):
            ##obtain info about current moniker
            null_context = POINTER(IBindCtx)()
            null_moniker = POINTER(IMoniker)()

            property_bag = moniker.RemoteBindToStorage(null_context, null_moniker, IPropertyBag._iid_).QueryInterface(IPropertyBag)
            webcam_name = property_bag.Read("FriendlyName", pErrorLog=None)

            if(webcam_name in self.webcam_list):
                self.duplicate_webcam_count[webcam_name]+=1
                self.webcam_list[webcam_name + " - " + str(self.duplicate_webcam_count[webcam_name])] = moniker
            else:
                self.duplicate_webcam_count[webcam_name]=1
                self.webcam_list[webcam_name + " - " + str(self.duplicate_webcam_count[webcam_name])] = moniker

            (moniker, fetch) = class_enumerator.RemoteNext(1)
    def list_webcams(self):
        self.obtain_webcams()

        return self.webcam_list.keys()
        #for webcam_name in self.webcam_list.keys():
            #print(webcam_name)
            #print(self.webcam_list[webcam_name])



class webcam:
    def __init__(self):
        ##the queue will contain pointers to the buffer where each frame is stored

        self.queue=queue.Queue()

        ##create the filter graph
        self.filter_graph = client.CreateObject(FilterGraph)

        ##
        self.control = self.filter_graph.QueryInterface(IMediaControl)
        self.graph_builder = client.CreateObject(CaptureGraphBuilder2)
        self.graph_builder.SetFiltergraph(self.filter_graph)
        self.show_video_window = True

    def create_filter(self,moniker):

        null_context = POINTER(IBindCtx)()
        null_moniker = POINTER(IMoniker)()
        ##bind moniker to object
        self.source = moniker.RemoteBindToObject(null_context, null_moniker, IBaseFilter._iid_)
        self.filter_graph.AddFilter(self.source, "VideoCapture")

        self.grabber = client.CreateObject(SampleGrabber)
        self.filter_graph.AddFilter(self.grabber, "Grabber")

        self.renderer = client.CreateObject(NullRenderer)
        self.filter_graph.AddFilter(self.renderer,"Renderer")



        mt = _AMMediaType()
        mt.majortype = MEDIATYPE_Video
        mt.subtype = MEDIASUBTYPE_RGB24
        mt.formattype = FORMAT_VideoInfo

        self.grabber.SetMediaType(mt)

        self.graph_builder.RenderStream(
            PIN_CATEGORY_CAPTURE,
            MEDIATYPE_Video,
            self.source,
            self.grabber,
            self.renderer
        )
        self.grabber.SetBufferSamples(False)
        self.grabber.SetOneShot(False)

        ##print(moniker)

    def init(self,name):
        import Config as config
        webcam_info = config.webcam_info()
        cameras = webcam_info.list_webcams()

        print(cameras)

        if name in cameras:
            self.create_filter(webcam_info.webcam_list[name])
            print("Camera available")
        else:
            print("Camera not available")

    def run(self):
        self.control.run()
        time.sleep(1)
    def stop(self):
        self.control.Stop()
        self.control.Release()

    def get_resolution(self):
        media_type = _AMMediaType()
        self.grabber.GetConnectedMediaType(media_type)

        p_video_info_header = cast(media_type.pbFormat, POINTER(VIDEOINFOHEADER))
        hdr = p_video_info_header.contents.bmi_header

        return(hdr.width,hdr.height)

    def set_resolution(self, width, height):
        self.control.Stop()
        stream_config = self.get_graph_builder_interface(IAMStreamConfig)

        #self.get_webcam_formats(stream_config)

        p_media_type = stream_config.GetFormat()
        media_type = p_media_type.contents


        if media_type.majortype != MEDIATYPE_Video:
            print(media_type.majortype)
            raise VidCapError("Cannot query capture format:majortype")
        if media_type.subtype != MEDIASUBTYPE_RGB24:
            print(media_type.subtype,MEDIASUBTYPE_RGB24)
            #raise VidCapError("Cannot query capture format:subtype")
        if media_type.formattype != FORMAT_VideoInfo:
            print(media_type.formattype)
            raise VidCapError("Cannot query capture format:formattype")
        if media_type.cbFormat >= sizeof(VIDEOINFOHEADER):
            print(media_type.cbFormat,sizeof(VIDEOINFOHEADER))
            #raise VidCapError("Cannot query capture format:cbFormat")
        if media_type.pbFormat != 3:
            print(media_type.pbFormat)
            #raise VidCapError("Cannot query capture format:pbFormat")

        no_capabilities, _ = stream_config.GetNumberOfCapabilities()


        for index in range(no_capabilities):
            print("Capability no:", index)
            try:
                print(stream_config.GetStreamCaps(index))
            except VidCapError:
                print("passed")




        p_video_info_header = cast(media_type.pbFormat, POINTER(VIDEOINFOHEADER))
        hdr = p_video_info_header.contents.bmi_header
        hdr.width = width
        hdr.height = height

        #stream_config.SetFormat(media_type)

    def get_size(self):
        media_type = _AMMediaType()
        self.grabber.GetConnectedMediaType(media_type)

        p_video_info_header = cast(media_type.pbFormat, POINTER(VIDEOINFOHEADER))
        hdr = p_video_info_header.contents.bmi_header
        return (hdr.size)

    def sample_arrived(self,pBuffer):
        self.queue.put(pBuffer)
        #print("putted")
    def set_callback(self):
        ##create SampleGrabberCallback object and set SampleGrabber's Callback Property to the newly created object;
        self.grabber_cb = SampleGrabberCB(self.sample_arrived)
        self.grabber.SetCallback(self.grabber_cb, 1)

    def set_callback_properties(self):
        self.grabber_cb.image_resolution=self.get_resolution()
        self.grabber_cb.size=self.get_size()
        #print(self.grabber_cb.image_resolution[0])
        #print(self.grabber_cb.image_resolution[1])

    def get_graph_builder_interface(self,interface):

        args = [
            PIN_CATEGORY_CAPTURE,
            MEDIATYPE_Video,
            self.source,
            interface._iid_,
        ]

        result = self.graph_builder.RemoteFindInterface(*args)
        return cast(result, POINTER(interface)).value

    def get_webcam_formats(self,stream):

       no_capabilities,_ = stream.GetNumberOfCapabilities()

       for index in range(no_capabilities):
            print("Capability no:",index)
            result,_ ,_ = stream.GetStreamCaps(2)

class feed(object):

    def __init__(self,lock,source,output):
        thread = threading.Thread(target=self.run, args=(lock,source,output,))
        thread.daemon = True                            # Daemonize thread
        thread.start()                                  # Start the execution

    def run(self,lock,source,output):
        import numpy as np
        import time
        while True:
            if source.empty() == False:
                #print("rendering")
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
               # print("--- %s seconds ---" % (time.time() - start_time))
            else:
                #print("empty buffer queeue")
                pass















