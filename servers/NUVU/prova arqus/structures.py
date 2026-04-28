from ctypes import Structure, POINTER, c_void_p

class NCCAMHANDLE(Structure):
    pass

NCCAM = POINTER(NCCAMHANDLE)

class NCIMAGEHANDLE(Structure):
    pass

NCIMAGE = POINTER(NCIMAGEHANDLE)

class NCCTRLLSTHANDLE(Structure):
    pass

NCCTRLLST = POINTER(NCCTRLLSTHANDLE)