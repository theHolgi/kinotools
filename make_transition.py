#!/usr/bin/env python3
import json
import os, sys
import re
import shutil
import subprocess
from datetime import date

basedir = "~/Dropbox/DCP/Transition"
fsklib  = "fsk.json"
outdir  = "/srv/dev-disk-by-label-Trailers/neue"
base    = "/tmp"
dockerbase = "/data"

def debug(s):
    print(s)

class DockerRun:
    def __init__(self, image, mappings):
        self._image = image
        self._mappings = ""
        for (key, value) in mappings.items():
            self._mappings += " -v"+key+":"+value
        
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
        for dirname, dirnames, filenames in os.walk(basedir):
            for filename in filenames:
                m = re.match(".+\.tif", filename)
                if (m):
                    self.inputs.append(filename)
        
        debug("Found the inputs: " + str(self.inputs))

    def generate(self, outdir):
        if len(self.inputs) == 0:
            debug("No inputs")
            return
        tmpdir  = base + "/tmp"
        tmpout  = base + "/out"
        dockertmp = dockerbase + "/tmp"
        dockerout = dockerbase + "/out"
        converter = DockerRun("dcpomatic", { base: dockerbase })
        outdir += "/Transition-" + date.today().isoformat()
        
        # clean up
        if os.path.isdir(tmpdir): shutil.rmtree(tmpdir)
        if os.path.isdir(tmpout): shutil.rmtree(tmpout)
        os.mkdir(tmpdir)
        os.mkdir(tmpout)
        if not os.path.isdir(outdir):
            os.mkdir(outdir)

        for input in self.inputs:
            name = input[:-4]
            shutil.copyfile(self.basedir + "/" + input, tmpdir + "/" + input)
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
            converter.execute("dcpomatic2_create " + input + " -o " + dockerout + " -s 10 -c XSN -n " + name)
            converter.execute("dcpomatic_cli " + dockerout)
            
            os.mkdir(outdir + "/" + name)
            for dirname, dirnames, filenames in os.walk(tmpout):
                for filename in filenames:
                    shutil.move(os.path.join(tmpout, filename), os.path.join(outdir + "/" + name, filename))

    def fskOf(self, name):
        for candidate in self._fsk.keys():
            if candidate in name:
                return self._fsk[candidate]
        return self._fsk.get('*')

    def ratingKey(self, name):
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
