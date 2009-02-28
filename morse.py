from ctypes import *
from ctypes.util import find_library

import time
import fileinput
import sys

# http://en.wikipedia.org/wiki/Morse_code
DOT=0.2
SPACING=DOT

# http://developer.apple.com/samplecode/HID_LED_test_tool/listing2.html

iokitLibraryLocation=find_library('IOKit')
iokit=CDLL(iokitLibraryLocation)

cfLibraryLocation=find_library('CoreFoundation')
cf=CDLL(cfLibraryLocation)


kCFAllocatorDefault=None
kCFNumberIntType=9
kCFStringEncodingASCII = 0x0600
kCFTypeDictionaryKeyCallBacks=c_void_p.in_dll(cf, 'kCFTypeDictionaryKeyCallBacks')
kCFTypeDictionaryValueCallBacks=c_void_p.in_dll(cf, 'kCFTypeDictionaryValueCallBacks')

def CFSTR(cstr):
    return cf.CFStringCreateWithCString(kCFAllocatorDefault,cstr,kCFStringEncodingASCII)


kIOHIDOptionsTypeNone=0

kHIDPage_GenericDesktop=c_int(1)
kHIDUsage_GD_Keyboard=c_int(6)
kHIDPage_LEDs=c_int(0x08)
kHIDUsage_LED_CapsLock=2
kIOHIDDeviceUsagePageKey="DeviceUsagePage"
kIOHIDElementUsagePageKey="UsagePage"
kIOHIDDeviceUsageKey="DeviceUsage"
kIOHIDElementUsageKey="Usage"


def create_matching_dict(isDeviceNotElement,inUsagePage,inUsage):
    result=cf.CFDictionaryCreateMutable(kCFAllocatorDefault, 0, byref(kCFTypeDictionaryKeyCallBacks), byref(kCFTypeDictionaryValueCallBacks))
    if result:
        if inUsagePage:
            pageCFNumberRef = cf.CFNumberCreate( kCFAllocatorDefault, kCFNumberIntType, byref(inUsagePage) )
            if pageCFNumberRef:
                if isDeviceNotElement:
                    cf.CFDictionarySetValue( result, CFSTR( kIOHIDDeviceUsagePageKey ), pageCFNumberRef )
                else:
                    cf.CFDictionarySetValue( result, CFSTR( kIOHIDElementUsagePageKey ), pageCFNumberRef )
                
                cf.CFRelease( pageCFNumberRef )
            
                if inUsage:
                    usageCFNumberRef = cf.CFNumberCreate( kCFAllocatorDefault, kCFNumberIntType, byref(inUsage) )
                    if usageCFNumberRef:
                        if isDeviceNotElement:
                            cf.CFDictionarySetValue( result, CFSTR( kIOHIDDeviceUsageKey ), usageCFNumberRef )
                        else:
                            cf.CFDictionarySetValue( result, CFSTR( kIOHIDElementUsageKey ), usageCFNumberRef )
                        
                        cf.CFRelease( usageCFNumberRef )
    return None

class LED(object):
    def __init__(self):
        tIOHIDManagerRef = iokit.IOHIDManagerCreate( kCFAllocatorDefault, kIOHIDOptionsTypeNone )
        self.tIOHIDManagerRef=tIOHIDManagerRef
        self.valueOn=None
        self.valueOff=None
        self.elementCFArrayRef=None
        
        matchingCFDictRef=create_matching_dict(True, kHIDPage_GenericDesktop, kHIDUsage_GD_Keyboard)
        iokit.IOHIDManagerSetDeviceMatching(tIOHIDManagerRef,matchingCFDictRef)

        if matchingCFDictRef:
            cf.CFRelease( matchingCFDictRef )

        tIOReturn = iokit.IOHIDManagerOpen( tIOHIDManagerRef, kIOHIDOptionsTypeNone )
        deviceCFSetRef = iokit.IOHIDManagerCopyDevices( tIOHIDManagerRef )

        deviceCount = cf.CFSetGetCount( deviceCFSetRef )

        # array to hold device refs
        tIOHIDDeviceRefs=(c_void_p*deviceCount)()

        cf.CFSetGetValues( deviceCFSetRef, tIOHIDDeviceRefs )

        matchingCFDictRef = create_matching_dict(False, kHIDPage_LEDs, c_int(0))

        for deviceIndex in range(deviceCount):
            if not iokit.IOHIDDeviceConformsTo(tIOHIDDeviceRefs[deviceIndex], kHIDPage_GenericDesktop, kHIDUsage_GD_Keyboard):
                continue
    
            elementCFArrayRef = iokit.IOHIDDeviceCopyMatchingElements( tIOHIDDeviceRefs[deviceIndex],matchingCFDictRef,kIOHIDOptionsTypeNone )
    
            elementCount = cf.CFArrayGetCount( elementCFArrayRef )
            for elementIndex in range(elementCount):
                tIOHIDElementRef = cf.CFArrayGetValueAtIndex( elementCFArrayRef, elementIndex )
                usagePage = iokit.IOHIDElementGetUsagePage( tIOHIDElementRef );
        
                # if this isn't an LED element...
                if kHIDPage_LEDs.value != usagePage:
                    continue
        
                usage = iokit.IOHIDElementGetUsage( tIOHIDElementRef );
                if usage == kHIDUsage_LED_CapsLock:
                    # found capslock key
                    tIOHIDElementType = iokit.IOHIDElementGetType( tIOHIDElementRef )
            
                    minCFIndex = iokit.IOHIDElementGetLogicalMin( tIOHIDElementRef )
                    maxCFIndex = iokit.IOHIDElementGetLogicalMax( tIOHIDElementRef )
                    
                    self.tIOHIDDeviceRef=tIOHIDDeviceRefs[deviceIndex]
                    
                    self.tIOHIDElementRef = tIOHIDElementRef
                    
                    timestamp=c_uint64(0)
                    self.valueOn  = iokit.IOHIDValueCreateWithIntegerValue( kCFAllocatorDefault, tIOHIDElementRef, timestamp, maxCFIndex )
                    self.valueOff = iokit.IOHIDValueCreateWithIntegerValue( kCFAllocatorDefault, tIOHIDElementRef, timestamp, minCFIndex )
                    
                    self.elementCFArrayRef=elementCFArrayRef
                    break
                    
            if not self.elementCFArrayRef:        
                cf.CFRelease( elementCFArrayRef )
            else:
                break # found LED

        if matchingCFDictRef:
            cf.CFRelease( matchingCFDictRef )
    
    def close(self):
        if self.tIOHIDManagerRef:
            cf.CFRelease(self.tIOHIDManagerRef)
        if self.elementCFArrayRef:
            cf.CFRelease( self.elementCFArrayRef )
        if self.valueOn:
            cf.CFRelease(self.valueOn)
        if self.valueOff:
            cf.CFRelease(self.valueOff)
    
    def _set_on(self,enable):
        if enable:
            value=self.valueOn
        else:
            value=self.valueOff
        
        err=iokit.IOHIDDeviceSetValue( self.tIOHIDDeviceRef, self.tIOHIDElementRef, value )
        print err
        
    on=property(fset=_set_on)
    
    
    def dot(self):
        self.on=True
        time.sleep(DOT)
        self.on=False
        time.sleep(SPACING)
    
    def dash(self):
        self.on=True
        time.sleep(DOT*3)
        self.on=False
        time.sleep(SPACING)
    
    def space(self):
        time.sleep(DOT*3 + SPACING)
    
    def morse(self, code):
        fn={ '.': self.dot, '-': self.dash }
        for c in code:
            print c
            fn.get(c,self.space)()


def morse_code(input):
    table={
        'A': '.-',
        'B': '-...',
        'C': '-.-.',
        'D': '-..',
        'E': '.',
        'F': '..-.',
        'G': '--.',
        'H': '....',
        'I': '..',
        'J': '.---',
        'K': '-.-',
        'L': '.-..',
        'M': '--',
        'N': '-.',
        'O': '---',
        'P': '.--.',
        'Q': '--.-',
        'R': '.-.',
        'S': '...',
        'T': '-',
        'U': '..-',
        'V': '...-',
        'W': '.--',
        'X': '-..-',
        'Y': '-.--',
        'Z': '--..',
        
        '1': '.----',
        '2': '..---',
        '3': '...--',
        '4': '....-',
        '5': '.....',
        '6': '-....',
        '7': '--...',
        '8': '---..',
        '9': '----.',
        '0': '-----',
        
        ' ': ' '
    }
    
    def _lookup(c):
        # unknown chars get removed
        return table.get(c.upper(),'')
    
    for line in input:
        yield ' '.join(_lookup(c) for c in line if _lookup(c))

if __name__ == '__main__':
    led=LED()
    try:
        led.on=False
    
        verbose=False
        for arg in sys.argv:
            if arg == '-v':
                verbose=True
                sys.argv.remove(arg)
                break
    
        morse=morse_code(fileinput.input())
    
        for code in morse:
            if verbose:
                print code
            led.morse(code)
    finally:
        led.close()
        