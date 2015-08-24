#!/usr/bin/env python

import os
import xml.etree.ElementTree as ET

ET.register_namespace("android", "http://schemas.android.com/apk/res/android")

manifest_file = os.path.join(os.path.dirname(__file__), '../platforms/android/AndroidManifest.xml')

tree = ET.parse(manifest_file)

root = tree.getroot()

current_permissions = []
permission_key = None
for child in root:
    if child.tag == 'uses-permission':
        for k,v in child.attrib.iteritems():
            if k.endswith('name'):
                permission_key = k
                current_permissions.append(v)
    
required_permissions = [
    'android.permission.ACCESS_NETWORK_STATE',
    'android.permission.ACCESS_WIFI_STATE',
    'android.permission.CAMERA',
    'android.permission.INTERNET',
    'android.permission.MODIFY_AUDIO_SETTINGS',
    'android.permission.RECORD_AUDIO',
    'android.permission.WAKE_LOCK',
    'android.permission.WRITE_EXTERNAL_STORAGE',
]

for permission in [p for p in required_permissions if p not in current_permissions]:
    attrib = {}
    attrib[permission_key] = permission
    ET.SubElement(root, 'uses-permission', attrib=attrib)
    print "Adding permission", permission

tree.write(manifest_file)
print "Updated ", manifest_file


    