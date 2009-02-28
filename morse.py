from ctypes import *
from ctypes.util import find_library

# http://developer.apple.com/samplecode/HID_LED_test_tool/listing2.html

iokitLibraryLocation=find_library('IOKit')
print 'loading IOKit from: %s' % iokitLibraryLocation
iokit=CDLL(iokitLibraryLocation)

cfLibraryLocation=find_library('CoreFoundation')
print 'loading CoreFoundation from: %s' % cfLibraryLocation
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

print kCFTypeDictionaryValueCallBacks

def create_matching_dict(isDeviceNotElement,inUsagePage,inUsage):
    result=cf.CFDictionaryCreateMutable(kCFAllocatorDefault, 0, byref(kCFTypeDictionaryKeyCallBacks), byref(kCFTypeDictionaryValueCallBacks))
    if result:
        if inUsagePage:
            pageCFNumberRef = cf.CFNumberCreate( kCFAllocatorDefault, kCFNumberIntType, byref(inUsagePage) )
            print pageCFNumberRef
            if pageCFNumberRef:
                if isDeviceNotElement:
                    cf.CFDictionarySetValue( result, CFSTR( kIOHIDDeviceUsagePageKey ), pageCFNumberRef )
                else:
                    cf.CFDictionarySetValue( result, CFSTR( kIOHIDElementUsagePageKey ), pageCFNumberRef )
                
                cf.CFRelease( pageCFNumberRef )
            
                if inUsage:
                    usageCFNumberRef = cf.CFNumberCreate( kCFAllocatorDefault, kCFNumberIntType, byref(inUsage) )
                    print usageCFNumberRef
                    if usageCFNumberRef:
                        if isDeviceNotElement:
                            cf.CFDictionarySetValue( result, CFSTR( kIOHIDDeviceUsageKey ), usageCFNumberRef )
                        else:
                            cf.CFDictionarySetValue( result, CFSTR( kIOHIDElementUsageKey ), usageCFNumberRef )
                        
                        cf.CFRelease( usageCFNumberRef )
    return None

tIOHIDManagerRef = iokit.IOHIDManagerCreate( kCFAllocatorDefault, kIOHIDOptionsTypeNone )
print tIOHIDManagerRef

matchingCFDictRef=create_matching_dict(True, kHIDPage_GenericDesktop, kHIDUsage_GD_Keyboard)

iokit.IOHIDManagerSetDeviceMatching(tIOHIDManagerRef,matchingCFDictRef)

if matchingCFDictRef:
    cf.CFRelease( matchingCFDictRef )

tIOReturn = iokit.IOHIDManagerOpen( tIOHIDManagerRef, kIOHIDOptionsTypeNone )
print tIOReturn

deviceCFSetRef = iokit.IOHIDManagerCopyDevices( tIOHIDManagerRef )
print deviceCFSetRef

deviceCount = cf.CFSetGetCount( deviceCFSetRef )
print deviceCount

# array to hold device refs
tIOHIDDeviceRefs=(c_void_p*deviceCount)()

cf.CFSetGetValues( deviceCFSetRef, tIOHIDDeviceRefs )

matchingCFDictRef = create_matching_dict(False, kHIDPage_LEDs, c_int(0))

for deviceIndex in range(deviceCount):
    if not iokit.IOHIDDeviceConformsTo(tIOHIDDeviceRefs[deviceIndex], kHIDPage_GenericDesktop, kHIDUsage_GD_Keyboard):
        print "deviceIndex %d does not conform" % deviceIndex
        continue
    print "deviceIndex %d conforms" % deviceIndex
    
    elementCFArrayRef = iokit.IOHIDDeviceCopyMatchingElements( tIOHIDDeviceRefs[deviceIndex],matchingCFDictRef,kIOHIDOptionsTypeNone )
    print elementCFArrayRef
    
    elementCount = cf.CFArrayGetCount( elementCFArrayRef )
    print elementCount
    
    for elementIndex in range(elementCount):
        tIOHIDElementRef = cf.CFArrayGetValueAtIndex( elementCFArrayRef, elementIndex )
        usagePage = iokit.IOHIDElementGetUsagePage( tIOHIDElementRef );
        
        # if this isn't an LED element...
        if kHIDPage_LEDs.value != usagePage:
            continue
        
        print "found led at %d" % elementIndex
        
        usage = iokit.IOHIDElementGetUsage( tIOHIDElementRef );
        if usage == kHIDUsage_LED_CapsLock:
            # found capslock key
            print "found caps lock"
            print usage
            tIOHIDElementType = iokit.IOHIDElementGetType( tIOHIDElementRef )
            print tIOHIDElementType
            
            minCFIndex = iokit.IOHIDElementGetLogicalMin( tIOHIDElementRef )
            maxCFIndex = iokit.IOHIDElementGetLogicalMax( tIOHIDElementRef )
            
            print minCFIndex, maxCFIndex
            
            timestamp=c_uint64(0)
            tIOHIDValueRef = iokit.IOHIDValueCreateWithIntegerValue( kCFAllocatorDefault, tIOHIDElementRef, timestamp, minCFIndex )
            if tIOHIDValueRef:
                tIOReturn = iokit.IOHIDDeviceSetValue( tIOHIDDeviceRefs[deviceIndex], tIOHIDElementRef, tIOHIDValueRef )
                print tIOHIDValueRef
                cf.CFRelease(tIOHIDValueRef)
    cf.CFRelease( elementCFArrayRef )

if tIOHIDManagerRef:
    cf.CFRelease(tIOHIDManagerRef)

if matchingCFDictRef:
    cf.CFRelease( matchingCFDictRef )