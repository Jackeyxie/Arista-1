#!/usr/bin/env Python

import argparse
import wget
import sys
import re
import time
from subprocess import Popen, call, check_output
import os
from os.path import expanduser

images = {'veos':['vEOS-lab'],
          'ceos':['cEOS'],
          'vmdk':['EOS.vmd'],
          'all':['EOS','cEOS','vEOS-lab','EOS.vmdk'],
          'eos':['EOS']}
outputFilename = []
vpn_name = 'Arista VPN'

def main(args,version):
  urls = []
  home = expanduser("~")
  outputDir = home + "/Downloads/"
  failed = False #Default value to False
  vpn_reconnect_counter = 0 #Counter to prevent a forever loop
  vpn_max_reconnect = 20 #Max VPN reconnect tries to prevent forever loop

  for image in images[args.package]:
    if image == "cEOS":
      ext = ".tar.xz"
    elif image == "EOS.vmdk":
      ext = ""
    else:
      ext = ".swi"
    urls.append("http://dist/release/EOS-" + version + "/final/images/" + image + ext)  
    if image == "EOS.vmdk":
      image = "EOS" 
      ext = ".vmdk"
    outputFilename.append(outputDir + image + "-" + version + ext)

  vpncheck = check_output(["scutil", "--nc", "status", vpn_name])
  vpncheckStr = vpncheck.split("\n")

  if vpncheckStr[0] == "Connected":
    print("VPN Connection is up...\n")
    print ("Downloading EOS: " + version + " To: " + outputDir + "\n")
    try:
      for url, filename in map(None, urls, outputFilename):
        file = wget.download(url, filename)
        print("\nFile downloaded to " + filename)
    except:
      failed = True
  else:
    print("VPN Connection is down...\n")
    print("Attempting to connect to {0}}".format(vpn_name))
    check_output(["scutil", "--nc", "start", vpn_name])
    while True:
      vpncheck = check_output(["scutil", "--nc", "status", vpn_name])
      vpncheckStr = vpncheck.split("\n")
      vpncheckResult = vpncheckStr[0].strip()
      if vpncheckResult == "Connected":
        break
      elif vpn_reconnect_counter >= vpn_max_reconnect:
        failed = True
        break
      else:
        vpn_reconnect_counter += 1
    
    #Check to make sure that the VPN tunnel didn't hit reconnect max tries
    if not failed:
      print ("Downloading EOS: " + version + " To: " + outputDir + "\n")
      try:
        for url, filename in map(None, urls, outputFilename):
          # print ("URL is " + url)
          # print ("Filename is " + filename)
          file = wget.download(url, filename)
          print("\nFile downloaded to " + filename)
      except:
        failed = True
    else:
      print("Unable to start VPN connection:\nEither you are not connected to the internet or you don't have the right VPN name")

  if not failed:
    for filename, urls in map(None, outputFilename, urls):
      filesize = os.stat(filename)[6]
      if filesize < 1024:
        with open(filename) as myfile:
          content = myfile.read()
        match = re.search(r'<p>(.*).</p>', content)
        reason = match.group(1)
        os.remove(filename)
        print ("\n\nThere was an error downloading: " + url + "\n")
        print ("\t" + reason + "\n")

if __name__ == '__main__':
  parser = argparse.ArgumentParser()
  parser.add_argument(
    "version", type=str, help="EOS image version", default=None)

  parser.add_argument(
    "-p", "--package", type=str, default="eos", choices=["eos", "vmdk", "veos", "ceos", "all"],
    help="specify which EOS packaging", required=False)

  args = parser.parse_args()
  version = args.version
  #Adding in redundancy check in case no version supplied.
  while not version:
    version = raw_input("Enter EOS Version: ").strip()
  main(args,version.upper())