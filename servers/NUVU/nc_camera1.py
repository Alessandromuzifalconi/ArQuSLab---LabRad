        # file: nuvu_cam_wrapper.py
# author: Cédric Vallée
# date: 16/04/18
# desc: Sert d'interface plus classique à python, gère les pointeurs, références et typages de ctypes
# desc: Only for camlink interface

from NC_api1 import *
import numpy as np
from ctypes import c_void_p
import sys

class NuvuException(Exception):
    """
        Classe: NuvuException, Hérite Exception
        permet le raise custom d'une erroeur provenant du sdk de Nuvu
    :attribut:  -error: numéro de l'erreur obtenue
    """
    def __init__(self, error):
        self.error = error
    def __str__(self):
        return repr(self.error)
    def value(self):
        """
            methode Value, class NuvuException
        :return: la valeur de l'erreur, définie dans le fichier erreur.h du sdk de nuvu
        """
        return self.error


class nc_camera:
    """
        Classe nc_camera, Hérite: aucun
        donne une interface python-like au sdk de Nuvu.
    :attributs: -macAdress:     Adresse mac de la caméra que l'on tente de controler
                -ncCam:         pointeur sur le handle de l'api de la caméra
                -ncImage:       pointeur sur le handle de l'image de la caméra
                -readoutTime:   type c_double temps de lecture, initialisé a -1
                -WaitingTime:   type c_double temps d'attente, initialisé a -1
                -ExposureTime:  type c_double temps d'exposition, initialisé a -1
                -shutterMode:   type c_int état du shutter de la caméra, (0=NOT SET, 1=open, 2=closed, 3=auto)
                -name:          nom de sauvegarde de l'images sur le disque si l'on utilise les fonction du sdk
                -comment:       Commentaire dans les méta données de l'image sauvegardée avec les fonction du sdk
                -width:         largeur de l'image en pixels
                -height:        hauteur de l'image en pixels
                -inMemoryAccess:bool détermine si l'on alloue un pointeur sur un array pour l'image
                -saveFormat:    détermine le format des images enregistrées par le sdk
                -targetdetectorTempMin: température minimum cible du détecteur
                -targetdetectorTempMax: température maximum cible du détecteur
    """
    def __init__(self, MacAdress = None):
        self.macAdress = MacAdress
        self.ncCam = NCCAM()
        self.ncImage = NCIMAGE()
        self.nbBuff = 0
        self.ampliType = c_int(-2)
        self.vertFreq = c_int(0)
        self.horizFreq = c_int(0)
        self.readoutMode = c_int(-1)
        self.ampliString = "12345678"
        self.nbrReadoutMode = c_int(0)
        self.readoutTime = c_double(-1.0)
        self.waitingTime = c_double(-1.0)
        self.exposureTime = c_double(-1.0)
        self.shutterMode = c_int(0)
        self.name = "image1"
        self.namec = "cube1"
        self.comment = ""
        self.width = c_int(-1)
        self.height = c_int(-1)
        self.saveFormat = 1
        self.detectorTemp = c_double(100.0)
        self.controllerTemp = c_double(100.0)
        self.powerSupplyTemp = c_double(100.0)
        self.fpgaTemp = c_double(100.0)
        self.heatsinkTemp = c_double(100.0)
        self.targetDetectorTemp = c_double(100.0)
        self.targetDetectorTempMin = c_double(100.0)
        self.targetDetectorTempMax = c_double(100.0)
        self.rawEmGain = c_int(-1)
        self.rawEmGainRangeMin = c_int(-1)
        self.rawEmGainRangeMax = c_int(-1)
        self.calibratedEmGain = c_int(-1)
        self.calibratedEmGainMin = c_int(-1)
        self.calibratedEmGainMax = c_int(-1)
        self.calibratedEmGainTempMin = c_double(100.0)
        self.calibratedEmGainTempMax = c_double(100.0)
        self.binx = c_int(0)
        self.biny = c_int(0)
        self.roiwidth = c_int(-1)
        self.roiheight = c_int(-1)
        self.roix = c_int(0)
        self.roiy = c_int(0)
        self.controllerlist = c_void_p()
        self.procType = c_int(0)
        self.subimage_per_burst = c_int(0)



    def errorHandling(self, error):
        """
        Méthode qui assure une réaction appropriée aux erreurs
        Jusqu'a présent, la fonction plante le programme, ferme le driver et sort du logiciel
        :param error: numéro de l'erreur retournée par le sdk
        :return: None
        """
        if error == 107:
            pass
            #print(error)
        # if error == 131:
        # Camera is started when it shouldn't be
        #     pass
        if error == 27:
            raise NuvuException("Error 27: Could not find camera")
        else:
            print("Code d'erreur: " + str(error)+ ". \n Se référer au fichier erreur.h du SDK de Nuvu.")
            self.closeCam(noRaise = True)
            sys.exit("Erreur d'exécution du driver Nuvu")


       
    def freeList(self):
        try:
            error = ncControllerListFree(self.controllerlist)
            if(error):
                raise NuvuException(error)

        except NuvuException as nuvuException:
            self.errorHandling(nuvuException.value())
        
    
    def openCaml(self, index, nbBuff=4):
        controllerlist = NCCTRLLST()
        try:
            error = ncControllerListOpen(byref(controllerlist))
            if(error):
                raise NuvuException(error)

        except NuvuException as nuvuException:
            self.errorHandling(nuvuException.value())
        print(controllerlist)
            
        

    def openCam(self, nbBuff=4):
        """
        Ouvre la connection avec la caméra, si la classe à été initialisée avec l'adresse mac de la caméra,
        la méthode tentera de se conecter directement a cette caméra
        :param nbBuff: Nombre de buffer initialisés dans l'api de nuvu
        :return:None
        """
        try:
            if self.macAdress is None:
                error = ncCamOpen(NC_AUTO_UNIT, NC_AUTO_CHANNEL, nbBuff, byref(self.ncCam))
                if error:
                    raise NuvuException(error)
                self.nbBuff = nbBuff
            else:
                print("Still not implemented")

        except NuvuException as nuvuException:
            self.errorHandling(nuvuException.value())


    def closeCam(self, noRaise=False):
        """
        Fonction qui ferme le driver de la caméra
        :param noRaise: Paramètre interne qui permet de ne pas raise d'erreur si le driver est déja fermé.
        :return: None
        """
        try:
            error = ncCamClose(self.ncCam)
            if (error and not noRaise):
                raise NuvuException(error)
        except NuvuException as nuvuException:
            self.errorHandling(nuvuException.value())


    def setReadoutMode(self, mode):
        """
        Permet de sélectionner le mode de lecture de la caméra
        :param mode: (int) mode nothing=0, EM = 1, CONV = 2
        :return: None
        """
        try:
            error = ncCamSetReadoutMode(self.ncCam, mode)
            if (error):
                raise NuvuException(error)

        except NuvuException as nuvuException:
            self.errorHandling(nuvuException.value())


    def getReadoutTime(self):
        """
        Méthode permettant de faire un appel a la caméra pour connaitre le temps de lecture, stoque le mode dans
        l'attribut readoutTime
        :return: None
        """
        try:
            error = ncCamGetReadoutTime(self.ncCam, byref(self.readoutTime))
            if(error):
                raise NuvuException(error)

        except NuvuException as nuvuException:
            self.errorHandling(nuvuException.value())




    def setExposureTime(self, exposureTime):
        """
        Méthode permettant de sélectionner le temps d'exposition des images.
        :param exposureTime: (float) le temps d'exposition en ms
        :return: None
        """
        try:
            error = ncCamSetExposureTime(self.ncCam, exposureTime)
            if (error):
                raise NuvuException(error)
            self.getExposureTime()
        except NuvuException as nuvuException:
            self.errorHandling(nuvuException.value())


    def getExposureTime(self, cameraCall = 1):
        """
        Méthode qui récupère le temps d'exposition sur la caméra
        :param cameraCall: Sélectionne si on vérifie la valeur dans le driver (0) ou dans la caméra (1)
        A noter: un appel à la caméra prend du temps
        :return: None
        """
        try:
            error = ncCamGetExposureTime(self.ncCam, cameraCall, byref(self.exposureTime))
            if(error):
                raise NuvuException(error)
        except NuvuException as nuvuException:
            self.errorHandling(nuvuException.value())


    def setWaitingTime(self, waitTime):
        """
        Méthode qui permet de sélectionner le temps d'attente entre deux acquisition
        :param waitTime: (float) temps d'attente en ms
        :return: None
        """
        try:
            error = ncCamSetWaitingTime(self.ncCam, waitTime)
            if(error):
                raise NuvuException(error)
            self.getWaitingTime(cameraCall=0)
        except NuvuException as nuvuException:
            self.errorHandling(nuvuException.value())


    def getWaitingTime(self, cameraCall = 1):
        """
        Méthode qui permet d'obtenir le temps d'attente entre deux acquisitions
        :param cameraCall: Sélectionne si on apelle le temps dans le driver (0) ou dans la caméra (1)
        A noter, un appel à la caméra prendra plus de temps.
        :return: None
        """
        try:
            error = ncCamGetWaitingTime(self.ncCam, cameraCall, byref(self.waitingTime))
            if(error):
                raise NuvuException(error)
        except NuvuException as nuvuException:
            self.errorHandling(nuvuException.value())


    def setTimeout(self, timeout):
        """
        Méthode qui permet de sélectionner un temps de timeout qui représente le temps avant que le driver déclare une
        erreur si il attend qu'une nouvelle image entre dans un buffer.
        :param timeout: (float) temps d'attente (en ms)
        :return: None
        """
        try:
            error = ncCamSetTimeout(self.ncCam, int(timeout))
            if (error):
                raise NuvuException(error)
        except NuvuException as nuvuException:
            self.errorHandling(nuvuException.value())


    def setShutterMode(self, mode):
        """
        Méthode qui sélectionne le mode de l'obturateur
        :param mode: (int) mode de l'obturateur
        :return: None
        """
        try:
            error = ncCamSetShutterMode(self.ncCam, mode)
            if (error):
                raise NuvuException(error)
        except NuvuException as nuvuException:
            self.errorHandling(nuvuException.value())


    def getShutterMode(self, cameraCall = 1):
        """
        Méthode qui récupère le mode de l'obturateur
        :param mode: (int) mode de l'obturateur
        :return: None
        """
        try:
            error = ncCamGetShutterMode(self.ncCam, cameraCall, byref(self.shutterMode))
            if (error):
                raise NuvuException(error)
        except NuvuException as nuvuException:
            self.errorHandling(nuvuException.value())


    def getSize(self):
        """
        Méthode qui récupère la hauteur et la largeur des images de la caméra, ces deux valeurs aux attributs height
        et width de la classe caméra
        :return: None
        """
        try:
            error =  ncCamGetSize(self.ncCam, byref(self.width), byref(self.height))
            if (error):
                raise NuvuException(error)
        except NuvuException as nuvuException:
            self.errorHandling(nuvuException.value())


    def camStart(self, nbrImg = 0):
        """
        Méthode qui démarre l'acquisition d'images sur la caméra et les envoie au buffer
        :param nbrImg: Détermine le nombre d'images que le driver prendra, si 0 alors l'acquisition est continue
        :return: None
        """
        try:
            error = ncCamStart(self.ncCam, nbrImg)
            if (error):
                raise NuvuException(error)
        except NuvuException as nuvuException:
            self.errorHandling(nuvuException.value())


    def camAbort(self):
        """
        Méthode qui arrète toute acquisition sur la caméra
        :return: None
        """
        try:
            error = ncCamAbort(self.ncCam)
            if (error):
                raise NuvuException(error)
        except NuvuException as nuvuException:
            self.errorHandling(nuvuException.value())


    def read(self):
        """
        Méthode qui lit la prochaine image dans le buffer et l'envoie en mémoire.
        :return: None
        """
        try:
            error = ncCamReadChronological(self.ncCam, self.ncImage, byref(c_int()))
            if (error):
                raise NuvuException(error)
        except NuvuException as nuvuException:
            self.errorHandling(nuvuException.value())


    def getImg(self):
        """
        Méthode qui apelle read() puis cast le pointeur vers l'image en array de 16 bit que l'on copie vers une autre
        partie de la mémoire.
        :return: None
        """
        self.read()
        return np.copy(np.ctypeslib.as_array(cast(self.ncImage, POINTER(c_uint16)),(self.width.value,self.height.value)))


    def saveImage(self, encode = 0):
        """
        Méthode qui sauvegarde l'image stoquée dans ncImage et l'encode en tiff (0) ou fits(1) sur le disque dur
        :param encode: (int) mode d'encodage
        :return: None
        """
        try:
            error = ncCamSaveImage(self.ncCam, self.ncImage, self.name.encode(), encode, self.comment.encode(), 1)
            if (error):
                raise NuvuException(error)
        except NuvuException as nuvuException:
            self.errorHandling(nuvuException.value())


    def setSequence(self, nbr_imgs):
        try:
            error = ncCamPrepareAcquisition(self.ncCam, nbr_imgs)
            if (error):
                raise NuvuException(error)
        except NuvuException as nuvuException:
            self.errorHandling(nuvuException.value())


    def startSequence(self, nbr_imgs):
        self.setSequence(nbr_imgs)
        try:
            error = ncCamBeginAcquisition(self.ncCam, nbr_imgs)
            if (error):
                raise NuvuException(error)
        except NuvuException as nuvuException:
            self.errorHandling(nuvuException.value())


    def saveSequence(self, nbr_imgs, nbr_cubes, encode = 0):
        try:
            error = ncCamStartSaveAcquisition(self.ncCam, self.namec.encode(), encode, nbr_imgs, self.comment.encode(), nbr_cubes, 1)
            if (error):
                raise NuvuException(error)
        except NuvuException as nuvuException:
            self.errorHandling(nuvuException.value())


    def stopSequence(self):
        try:
            error = ncCamStopSaveAcquisition(self.ncCam)
            if (error):
                raise NuvuException(error)
        except NuvuException as nuvuException:
            self.errorHandling(nuvuException.value())



    def getTargetDetectorTempRange(self):
        """
        Permet de récupérer le range de températures demandées du détecteur
        :return: None
        """
        try:
            error = ncCamGetTargetDetectorTempRange(self.ncCam, byref(self.targetDetectorTempMin), byref(self.targetDetectorTempMax))
            if (error):
                raise NuvuException(error)
        except NuvuException as nuvuException:
            self.errorHandling(nuvuException.value())


    def getControllerTemp(self):
        """
        récupère la température actuelle du controleur et la store dans l'attribut controller temp
        :return: None
        """
        try:
            error = ncCamGetControllerTemp(self.ncCam, byref(self.controllerTemp))
            if (error):
                raise NuvuException(error)
        except NuvuException as nuvuException:
            self.errorHandling(nuvuException.value())


    def getComponentTemp(self, comp):
        """
        Méthode qui récupère la température du composant spécifié et la stoque dans la valeur associée
        :param comp: identifiant du composant. 0=CCD, 1=controleur, 2=powerSupply, 3=FGPA, 4=heatSink
        :return: None
        """
        try:
            if (comp == 0):
                temp = self.detectorTemp
            elif (comp == 1):
                temp = self.controllerTemp
            elif (comp == 2):
                temp = self.powerSupplyTemp
            elif (comp == 3):
                temp = self.fpgaTemp
            elif (comp == 4):
                temp = self.heatsinkTemp
            else:
                comp = -1
    
            error = ncCamGetComponentTemp(self.ncCam, c_int(comp), byref(temp))
            if (error):
                raise NuvuException(error)
        except NuvuException as nuvuException:
            self.errorHandling(nuvuException.value())


    def setTargetDetectorTemp(self, temp):
        """
        Méthode permettant de donner à la caméra la température visée du détecteur
        :param temp: (float) Température visée
        :return: None
        """
        try:
            error = ncCamSetTargetDetectorTemp(self.ncCam, c_double(temp))
            if (error):
                raise NuvuException(error)
        except NuvuException as nuvuException:
            self.errorHandling(nuvuException.value())


    def getTargetDetectorTemp(self, cameraCall=1):
        """
        Méthode permettant de récupérer la température visée du détecteur et la stoquer dans
        l'attribut targetDetectorTemp
        :param cameraCall: Détermine si on apelle la caméra ou le driver, setté de base sur la camméra
        :return: None
        """
        try:
            error = ncCamGetTargetDetectorTemp(self.ncCam, cameraCall, byref(self.targetDetectorTemp))
            if (error):
                raise NuvuException(error)
        except NuvuException as nuvuException:
            self.errorHandling(nuvuException.value())


    def setRawEmGain(self, gain):
        """
        Méthode qui envoie une gain à la caméra
        :return: None
        """
        try:
            error = ncCamSetRawEmGain(self.ncCam, gain)
            if (error):
                raise NuvuException(error)
        except NuvuException as nuvuException:
            self.errorHandling(nuvuException.value())


    def getRawEmGain(self, cameracall=1):
        """
        Méthode qui récupère la valeur rawEmGain de la caméra et la stoque dans l'attribut rawEmGain
        :return: None
        """
        try:
            error = ncCamGetRawEmGain(self.ncCam, cameracall, byref(self.rawEmGain))
            if (error):
                raise NuvuException(error)
        except NuvuException as nuvuException:
            self.errorHandling(nuvuException.value())


    def getRawEmGainRange(self):
        """
        Méthode permettant de récupérer le range de Em gain disponible, stoque dans les attributs
        :return: None
        """
        try:
            error = ncCamGetRawEmGainRange(self.ncCam, byref(self.rawEmGainRangeMin), byref(self.rawEmGainRangeMax))
            if (error):
                raise NuvuException(error)
        except NuvuException as nuvuException:
            self.errorHandling(nuvuException.value())


    def setCalibratedEmGain(self, emGain):
        """
        Méthode permettant de sélectionner un EmGain calibré
        :param emGain: (int) Em gain
        :return: None
        """
        try:
            error = ncCamSetCalibratedEmGain(self.ncCam, emGain)
            if (error):
                raise NuvuException(error)
        except NuvuException as nuvuException:
            self.errorHandling(nuvuException.value())


    def getCalibratedEmGain(self, cameraCall=1):
        """
        Méthode permettant de récupérer le Em Gain calibré sur la caméra
        :param cameraCall: Détermine si on accède a la caméra ou au driver
        :return: None
        """
        try:
            error = ncCamGetCalibratedEmGain(self.ncCam, cameraCall, byref(self.calibratedEmGain))
            if (error):
                raise NuvuException(error)
        except NuvuException as nuvuException:
            self.errorHandling(nuvuException.value())


    def getCalibratedEmGainRange(self):
        """
        Méthode permettant d'obtenir le range ou la calibration du emGain est valide
        :return: None
        """
        try:
            error = ncCamGetCalibratedEmGainRange(self.ncCam, byref(self.calibratedEmGainMin), byref(self.calibratedEmGainMax))
            if(error):
                raise NuvuException(error)
        except NuvuException as nuvuException:
            self.errorHandling(nuvuException.value())


    def getCalibratedEmGainTempRange(self):
        """
        Méthode permettant de connaitre l'intervalle en température de validité de la calibration du emGain
        :return: None
        """
        try:
            error = ncCamGetCalibratedEmGainTempRange(self.ncCam, byref(self.calibratedEmGainTempMin),byref(self.calibratedEmGainTempMax))
            if (error):
                raise NuvuException(error)
        except NuvuException as nuvuException:
            self.errorHandling(nuvuException.value())


    def getCurrentReadoutMode(self):
        """
        Méthode permettant de récupérer les informations du readout mode utilisé
        :return: None
        """
        try:
            error = ncCamGetCurrentReadoutMode(self.ncCam, byref(self.readoutMode), byref(self.ampliType), self.ampliString.encode(), byref(self.vertFreq), byref(self.horizFreq))
            if (error):
                raise NuvuException(error)
        except NuvuException as nuvuException:
            self.errorHandling(nuvuException.value())


    def getNbrReadoutModes(self):
        """
        Récupère le nombre de readoutmode disponibles
        :return:
        """
        try:
            error = ncCamGetNbrReadoutModes(self.ncCam, byref(self.nbrReadoutMode))
            if (error):
                raise NuvuException(error)
        except NuvuException as nuvuException:
            self.errorHandling(nuvuException.value())


    def camInit(self):
        """
        retrieve every info about cam
        :return: no Return
        """
        self.getNbrReadoutModes()
        self.getCurrentReadoutMode()
        self.getReadoutTime()
        self.getSize()
        self.getWaitingTime()
        self.getExposureTime()
        self.getComponentTemp(0)
        self.getComponentTemp(1)
        self.getComponentTemp(2)
        self.getComponentTemp(3)
        self.getShutterMode()
        self.getCalibratedEmGain()
        self.getCalibratedEmGainRange()
        self.getCalibratedEmGainTempRange()
        self.getRawEmGain()
        self.getRawEmGainRange()
        self.getTargetDetectorTemp()
        self.getTargetDetectorTempRange()

    def updateCam(self):
        """
        retrieve info about cam
        :return: Ǹo return
        """
        pass


    def purgeBuffer(self):
        for i in range(self.nbBuff):
            self.read()

    def setSquareBinning(self, bin):
        """
        sets binning mode and actualise data in cam class
        :param bin:
        :return:
        """
        try:
            error = ncCamSetBinningMode(self.ncCam, bin, bin)
            if(error):
                raise NuvuException(error)
            error = ncCamGetBinningMode(self.ncCam, byref(self.binx), byref(self.biny))
            if (error):
                raise NuvuException(error)
            self.getSize()

        except NuvuException as nuvuException:
            self.errorHandling(nuvuException.value())

    def flushReadQueue(self):
        """
        flushes all images acquired prior to this call
        :param self:
        :return:
        """
        try:
            error = ncCamFlushReadQueue(self.ncCam)
            if (error):
                raise NuvuException(error)
        except NuvuException as nuvuException:
            self.errorHandling(nuvuException.value())

    def getRoiSize(self, region):
        try:
            error = ncCamGetMRoiSize(self.ncCam, region, byref(self.roiwidth), byref(self.roiheight))
            if (error):
                raise NuvuException(error)
        except NuvuException as nuvuException:
            self.errorHandling(nuvuException.value())

    def setRoiSize(self, region, roiwidth, roiheight):
        try:
            error = ncCamSetMRoiSize(self.ncCam, region, roiwidth, roiheight)
            if (error):
                raise NuvuException(error)
        except NuvuException as nuvuException:
            self.errorHandling(nuvuException.value())

    def applyRoi(self):
        try:
            error = ncCamMRoiApply(self.ncCam)
            if (error):
                raise NuvuException(error)
        except NuvuException as nuvuException:
            self.errorHandling(nuvuException.value())

    def getRoiPosition(self, region):
        try:
            error = ncCamGetMRoiPosition(self.ncCam, region, byref(self.roix), byref(self.roiy))
            if (error):
                raise NuvuException(error)
        except NuvuException as nuvuException:
            self.errorHandling(nuvuException.value())

    def setRoiPosition(self, region, roix, roiy) :
        try:
            error = ncCamSetMRoiPosition(self.ncCam, region, roix, roiy)
            if (error):
                raise NuvuException(error)
        except NuvuException as nuvuException:
            self.errorHandling(nuvuException.value())

    def addRoi(self, x, y, roiWidth, roiHeight):
        try:
            error = ncCamAddMRoi(self.ncCam, x, y, roiWidth, roiHeight)
            if (error):
                raise NuvuException(error)
        except NuvuException as nuvuException:
            self.errorHandling(nuvuException.value())

    def isacquiring(self):
        is_acquiring = c_int()
        try:
            error = ncCamIsAcquiring(self.ncCam, byref(is_acquiring))
            if (error):
                raise NuvuException(error)
        except NuvuException as nuvuException:
            self.errorHandling(nuvuException.value())
        return is_acquiring.value !=0
    

    def getReadoutMode(self, mode):
        amplistring=c_long()
        try:
            error = ncCamGetReadoutMode(self.ncCam, mode, byref(self.ampliType), amplistring, byref(self.vertFreq), byref(self.horizFreq))
            if (error):
                raise NuvuException(error)
        except NuvuException as nuvuException:
            self.errorHandling(nuvuException.value())


    def readUInt32(self):
        """
        Méthode qui lit la prochaine image dans le buffer et l'envoie en mémoire.
        :return: None
        """
        image=[]
        try:
            error = ncCamReadUInt32(self.ncCam, image)
            if (error):
                raise NuvuException(error)
        except NuvuException as nuvuException:
            self.errorHandling(nuvuException.value())

            return image
        
            

    def setProc(self, proc, nbr_imgs = 0):
        
     #NO_PROC (None), LM (bias subtraction), PC (photon counting).   nbr_imgs è quante immagini prese prima di partire in photon counting (altrimenti ignorato)
        
      
        proc_map = {
        'PC': 0x02,
        'LM': 0x01,
        'NO_PROC' : 0x00
         }

        proc_type = proc_map.get(f'{proc}')

        

        try:
            error = ncCamSetProcType(self.ncCam, proc_type, nbr_imgs)
            if (error):
                    raise NuvuException(error)
        except NuvuException as nuvuException:
            self.errorHandling(nuvuException.value())




    def getProc(self):
        imgs = c_int(0)
     #NO_PROC (None), LM (bias subtraction), PC (photon counting).   nbr_imgs è quante immagini prese prima di partire in photon counting (altrimenti ignorato)
        try:
            error = ncCamGetProcType(self.ncCam, byref(self.procType), byref(imgs))
            if (error):
                raise NuvuException(error)
        except NuvuException as nuvuException:
            self.errorHandling(nuvuException.value())


    def createBias(self, nbr_imgs):
        
        #BIAS_DEFAULT = CLOSE, altrimenti mettere OPEN.    nbr_imgs è il numero di immagini che vengono usate per creare il bias, vengono consigliate tra le 50 e 300 
        try:
            error = ncCamCreateBias(self.ncCam, nbr_imgs, BIAS_DEFAULT)
            if (error):
                raise NuvuException(error)
        except NuvuException as nuvuException:
            self.errorHandling(nuvuException.value())

    def setFastKinetics(self, nbr_imgs):

        #discard_count = numero di immagini per burst
        try:
            error = ncCamSetFastKineticsMode(self.ncCam, nbr_imgs)
            if (error):
                raise NuvuException(error)
        except NuvuException as nuvuException:
            self.errorHandling(nuvuException.value())

        
    def setKineticsDiscard(self, discard_count):
        #discard_count = immagini da scartare all'inizio di ogni burst

        try:
            error = ncCamSetFastKineticsModeDiscard(self.ncCam, discard_count)
            if (error):
                raise NuvuException(error)
        except NuvuException as nuvuException:
            self.errorHandling(nuvuException.value())

    def getKineticsImageCount(self):
        #quante immagini ottieni per busrt?

        try:
            error = ncCamGetFastKineticsModeImageCount(self.ncCam, byref(self.subimage_per_burst))
            if (error):
                raise NuvuException(error)
        except NuvuException as nuvuException:
            self.errorHandling(nuvuException.value())
        
