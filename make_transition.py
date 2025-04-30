#!/usr/bin/env python3
import json
import os, sys
import re
import shutil
import subprocess
from datetime import date

basedir = "~/Dropbox/DCP/Transition"
fsklib  = "fsk.json"
outdir  = "/srv/trailers/neue"
base    = "/tmp"
dockerbase = "/data"

def debug(s):
    print(s)

class DockerRun:
    def __init__(self, image, mappings):
        self._image = image
        self._mappings = ""
        for (key, value) in mappings.items():
            self._mappings += ' -v"'+key+'":"' +value + '"'
        
    def execute(self, cmd, cwd="."):
        cmd = " ".join(["docker", "run", "--rm", self._mappings, self._image, cmd])
        debug("Execute: " + cmd)
        return subprocess.call(cmd, shell=True, cwd=cwd)

class Transition:
    def __init__(self, basedir, fsk):
        try:
            with open(fsk) as f:
                self._fsk = json.loads(f.read())
                debug("FSK Liste: " + str(self._fsk))
        except:
            self._fsk = {}
        self.basedir = basedir
        self.inputs = []
        dirname, dirnames, filenames = next(os.walk(basedir))
        self.inputs.extend(f for f in filenames if f.endswith('.tif') and not f.startswith('.'))
        
        debug("Found the inputs: " + str(self.inputs))

    @property
    def tmpdir(self) -> str:
        return base + "/tmp"

    @property
    def tmpout(self) -> str:
        return base + "/out"

    def generate(self):
        if len(self.inputs) == 0:
            debug("No inputs")
            return
        dockertmp = dockerbase + "/tmp"
        dockerout = dockerbase + "/out"
        converter = DockerRun("dcpomatic", { base: dockerbase })

        # clean up
        if os.path.isdir(self.tmpdir): shutil.rmtree(self.tmpdir)
        if os.path.isdir(self.tmpout): shutil.rmtree(self.tmpout)
        os.mkdir(self.tmpdir)
        os.mkdir(self.tmpout)

        for input in self.inputs:
            name = input[:-4]
            shutil.copyfile(self.basedir + "/" + input, self.tmpdir + "/" + input)
            fsk = self.fskOf(name)
            # Hint: dcpname will be built by DCP-o-matic itself.
            dcpname = name + "_XSN_F_2K_" + date.today().strftime("%Y%m%d") + "_SMPTE"
            if fsk is not None:
                dcpname = name + "_XSN_F-" + str(fsk) + "_2K_" + date.today().strftime("%Y%m%d") + "_SMPTE"
            print("========================================================================================\n" +
                  "Input: " + input + "\n" + 
                  "DCP: " + dcpname + "\n" +
                  "FSK: " + str(fsk) + "\n" +
                  "========================================================================================\n")
            converter.execute("dcpomatic2_create tmp/" + input + " -o " + dockerout + "/" + name + " -s 10 -c XSN -n " + name)
            converter.execute("dcpomatic2_cli " + dockerout + "/" + name)
            # Clean up a bit: "video" is redundant
            converter.execute("rm -rf " + dockerout + "/" + name + "/video")

            # shutil.move(os.path.join(tmpout, name), outdir)
        converter.execute("chown -R 1000 " + dockerout)

    def fskOf(self, name) -> str:
        for candidate in self._fsk.keys():
            if candidate in name:
                return self._fsk[candidate]
        return self._fsk.get('*')

    def ratingKey(self, name) -> str:
        fsk = self.fskOf(name)
        if fsk is None:
            return ""
        if fsk == 0:
            return "-m G" # General audience
        if fsk == 6:
            return "-m PG" # Parental guidance suggested
        if fsk == 12:
            return "-m PG-13" # Not suided for children under 13
        if fsk == 16:
            return "-m R" # Restricted
        if fsk == 18:
            return "-m NC-17" # No one 17 and under
        
    def cleanup(self, donedir):
        for input in self.inputs:
            shutil.move(os.path.join(self.basedir, input), os.path.join(donedir, input))

if len(sys.argv) > 1:
    basedir = sys.argv[1]
t = Transition(basedir, basedir + "/" + fsklib)
t.generate(outdir)
if len(sys.argv) > 2:
    t.cleanup(sys.argv[2])
