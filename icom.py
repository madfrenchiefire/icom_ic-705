"""
Created: by Jason Boucher - KC1SEC
Date    : 01/2023

"""

import serial
import time



class icom:

    def __init__(self, serialDevice, serialBaud, icomTrxCivAdress):
        self.icomTrxCivAdress = icomTrxCivAdress
        self.serialDevice = serialDevice
        self.serialBaud = serialBaud
        # start serial usb connection
        self.ser = serial.Serial(serialDevice, serialBaud)
        self.ser.setDTR(False)  # prevent TCVR cw send  if USB key is set on DTR
        self.ser.setRTS(False)  # prevent TCVR going transmit if USB Send is set on RTS

    # gives a empty bytearray when data crc is not valid
    def __readFromIcom(self):
        time.sleep(0.04)
        b = bytearray()
        while self.ser.inWaiting():
            b = b + self.ser.read()
        # drop all but the last frame
        while b.count(b'\xfd') > 1:
            del b[0:b.find(b'\xfd') + 1]
        if len(b) > 0:
            # valid message
            validMsg = bytes([254, 254, 0, self.icomTrxCivAdress, 251, 253])
            if b[0:5] == validMsg:
                b = b[6:len(b)]
                if len(b) > 0:  # read answer from icom trx
                    if b[0] == 254 and b[1] == 254 and b[-1] == 253:  # check for valid data CRC
                        return b
                    else:
                        b = bytearray()
                else:
                    b = bytearray()
            else:
                if b[0] == 254 and b[1] == 254 and b[-1] == 253:  # check for valid data CRC
                    b = b
                else:
                    b = bytearray()
        # print('   * readFromIcom return value: ', b)
        return b
        
    # gives a empty bytearray when data crc is not valid
    def __writeToIcom(self, b):
        s = self.ser.write(bytes([254, 254, self.icomTrxCivAdress, 0]) + b + bytes([253]))
        print('   * writeToIcom value: ', b)
        return self.__readFromIcom()

    def close(self):
        self.ser.close()

    def setMode(self, mode):
        mode = mode.upper()
        if mode == 'FM':
            self.__writeToIcom(b'\x06\x05\x01')
        if mode == 'USB':
            self.__writeToIcom(b'\x06\x01\x02')
        if mode == 'LSB':
            self.__writeToIcom(b'\x06\x00\x02')
        if mode == 'CW':
            self.__writeToIcom(b'\x06\x03\x01')
        if mode == 'AM':
            self.__writeToIcom(b'\x06\x02\x01')

    def setVFO(self, vfo):
        vfo = vfo.upper()
        if vfo == 'VFOA':
            self.__writeToIcom(b'\x07\x00')
        if vfo == 'VFOB':
            self.__writeToIcom(b'\x07\x01')
        if vfo == 'MAIN':
            self.__writeToIcom(b'\x07\xd0')  # select MAIN
        if vfo == 'SUB':
            self.__writeToIcom(b'\x07\xd1')  # select SUB

    # change main and sub
    def setExchange(self):
        self.__writeToIcom(b'\x07\xB0')


    # Parameter: hertz string with 3 numbers
    def setToneHz(self, hertz):
        b = b'\x1b\x00' + bytes([int('0' + hertz[0], 16), int(hertz[1] + hertz[2], 16)])
        self.__writeToIcom(b)

    # Caution: RIT CI-V Command only for IC-9700, the IC-9100 has no RIT CI-V command
    # Parameter: Integer
    def setRitFrequency(self, value):
        hertz = '0000' + str(abs(value))
        if value >= 0:
            b = b'\x21\x00' + bytes([int(hertz[-2] + hertz[-1], 16),  int(hertz[-4] + hertz[-3], 16)]) + b'\x00'
        else:
            b = b'\x21\x00' + bytes([int(hertz[-2] + hertz[-1], 16),  int(hertz[-4] + hertz[-3], 16)]) + b'\x01'
        self.__writeToIcom(b)

    # Parameter as string in hertz
    def setFrequency(self, freq):
        freq = '0000000000' + freq
        freq = freq[-10:]
        b = bytes([5, int(freq[8:10], 16), int(freq[6:8], 16), int(freq[4:6], 16),
                   int(freq[2:4], 16), int(freq[0:2], 16)])
        returnMsg = self.__writeToIcom(b)
        back = False
        if len(returnMsg) > 0:
            if returnMsg.count(b'\xfb') > 0:
                back = True
        return back

    # Caution: hex 25 CI-V Command only for IC-9700
    def setFrequencyOffUnselectVFO(self, freq):
        freq = '0000000000' + freq
        freq = freq[-10:]
        b = b'\x25\x01' + bytes([int(freq[8:10], 16), int(freq[6:8], 16), int(freq[4:6], 16),
                   int(freq[2:4], 16), int(freq[0:2], 16)])
        returnMsg = self.__writeToIcom(b)
        back = False
        if len(returnMsg) > 0:
            if returnMsg.count(b'\xfb') > 0:
                back = True
        return back

    def voiceTX(self, voicememory):
        b = b'\x28\x00' + bytes([int(voicememory[0:2], 16)])
        self.__writeToIcom(b)

    def memoryMode(self):
        b = b'\x08'
        self.__writeToIcom(b)

    def setMemory(self, memory):
        memory = '0000' + memory
        memory = memory[-4:]
        b = bytes([8, int(memory[0:2], 16), int(memory[2:4], 16)])
        self.__writeToIcom(b)

    def setGroup(self, group):
        group = '0000' + group
        group = group[-4:]
        b = b'\x08\xA0' + bytes([int(group[0:2], 16), int(group[2:4], 16)])
        self.__writeToIcom(b)

    def setVolume(self, volume):
        volume = '0000' + volume
        volume = volume[-4:]
        b = b'\x14\x01' + bytes([int(volume[0:2], 16), int(volume[2:4], 16)])
        self.__writeToIcom(b)

    def setMode(self, mode):
        mode = mode.upper()
        if mode == 'LSB':
            mode_value = "00"
        if mode == 'USB':
            mode_value = "01"
        if mode == 'AM':
            mode_value = "02"
        if mode == 'CW':
            mode_value = "03"
        if mode == 'RTTY':
            mode_value = "04"
        if mode == 'FM':
            mode_value = "05"
        if mode == 'WFM':
            mode_value = "06"
        if mode == 'CW-R':
            mode_value = "07"
        if mode == 'RTTY-R':
            mode_value = "08"
        if mode == 'DV':
            mode_value = "17"

        b = b'\x06' + bytes([int(mode_value[0:2], 16)])
        self.__writeToIcom(b)


    def setDataoffModinput(self, domi):
        domi = domi.upper()
        if domi == 'MIC':
            domi_value = "00"
        if domi == 'USB':
            domi_value = "01"
        if domi == 'MIC,USB':
            domi_value = "02"
        if domi == 'WLAN':
            domi_value = "03"
        b = b'\x1A\x05\x01\x18' + bytes([int(domi_value[0:2], 16)])
        self.__writeToIcom(b)

    def setDataonModinput(self, donmi):
        donmi = donmi.upper()
        if donmi == 'MIC':
            donmi_value = "00"
        if donmi == 'USB':
            donmi_value = "01"
        if donmi == 'MIC,USB':
            donmi_value = "02"
        if donmi == 'WLAN':
            donmi_value = "03"
        b = b'\x1A\x05\x01\x19' + bytes([int(donmi_value[0:2], 16)])
        self.__writeToIcom(b)


    def setRfpower(self, rfpower):
        rfpower = '0000' + rfpower
        rfpower = rfpower[-4:]
        b = b'\x14\x0A' + bytes([int(rfpower[0:2], 16), int(rfpower[2:4], 16)])
        self.__writeToIcom(b)


    def setSql(self, value):
        # parameter value 0000 to 0255 as number not as string
        squelch = '0000' + str(abs(value))
        b = b'\x14\x03' + bytes([int('0' + squelch[-3], 16), int(squelch[-2] + squelch[-1], 16)])
        self.__writeToIcom(b)


    # NF Loudness
    # Parameter value as string between 0000 to 0255
    def setAudioFrequenceLevel(self, value):
        loudness = '0000' + str(abs(value))
        b = b'\x14\x01' + bytes([int('0' + loudness[-3], 16), int(loudness[-2] + loudness[-1], 16)])
        self.__writeToIcom(b)

    def setToneSquelchOn(self, on):
        if on:
            self.__writeToIcom(b'\x16\x43\x01')
        else:
            self.__writeToIcom(b'\x16\x43\x00')

    def setToneOn(self, on):
        if on:
            self.__writeToIcom(b'\x16\x42\x01')
        else:
            self.__writeToIcom(b'\x16\x42\x00')

    def setAfcOn(self, on):
        if on:
            self.__writeToIcom(b'\x16\x4A\x01')
        else:
            self.__writeToIcom(b'\x16\x4A\x00')

    # Parameter b: True = set SPLIT ON, False = set SPLIT OFF
    def setSplitOn(self, on):
        if on:
            self.__writeToIcom(b'\x0F\x01')
        else:
            self.__writeToIcom(b'\x0F\x00')

    # Parameter b: True = set RIT ON, False = set RIT OFF
    def setRitOn(self, on):
        if on:
            self.__writeToIcom(b'\x21\x01\x01')
        else:
            self.__writeToIcom(b'\x21\x01\x00')

    def ptt(self, status):
        #status = self.isPttOff()
        if status == True:
            self.__writeToIcom(b'\x1C\x00\x01')
        else:
            self.__writeToIcom(b'\x1C\x00\x00')


    def setDuplex(self, value):
        value = value.upper()
        if value == 'OFF':
            self.__writeToIcom(b'\x0F\x10')
        if value == 'DUP-':
            self.__writeToIcom(b'\x0F\x11')
        if value == 'DUP+':
            self.__writeToIcom(b'\x0F\x12')


    def getFrequency(self):
        b = self.__writeToIcom(b'\x03')  # ask for used frequency
        c = ''
        if len(b) > 0:
            for a in reversed(b[5:10]):
                c = c + '%0.2X' % a
        if len(c) > 0: 
            if c[0] == '0':
                c = c[1:len(c)]
        return c

    # CI-V TRANSCEIVE have to be ON
    # function extract last frequency which is send to us when a user is dailing
    def getWhatFrequencyIcomSendUs(self):
        c = ''
        b = self.__readFromIcom()
        # find last CI-V message by searching from behind
        position = b.rfind(bytearray(b'\xfe\xfe'))
        if position >= 0:
            # extract answer
            answer = b[position:len(b)]
            # proof if CI-V frequence message from icom
            if len(answer) == 11 and answer[4] == 0:
                if len(answer) > 0:
                    for a in reversed(answer[5:10]):
                        c = c + '%0.2X' % a
                if c[0] == '0':
                    c = c[1:len(c)]
        return c

    def isPttOff(self):
        ret = True
        b = self.__writeToIcom(b'\x1C\x00')  # ask for PTT status
        if b[-2] == 1:
            ret = False
        return ret

