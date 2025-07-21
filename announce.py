import os
import sys
from PIL import Image

class ImageProcessor:
    def __init__(self, filename: str):
        self.im = Image.open(filename)
        self.outdir = '.'
        self.framerate = 24
        self.num = 0
        self.pattern = "image_%04i.tif"

    def _writeout(self, image: Image) -> None:
        outname = self.pattern % self.num
        image.save(os.path.join(self.outdir, outname))
        self.num += 1

    def ramp(self, start: float = 0, end: float = 1, time: float = 1):
        steps = int(time * self.framerate)
        input = self.im.copy()
        for n in range(steps):
            brightness = start + (n+1)*(end-start)/steps
            input.putalpha(int(brightness * 255))
            output = Image.new(self.im.mode, self.im.size, 0)
            output.putalpha(255)
            output.alpha_composite(input)
            self._writeout(output)

    def hold(self, time: float = 1) -> None:
        for n in range(int(time * self.framerate)):
            self._writeout(self.im)


filename = sys.argv[1]

processor = ImageProcessor(filename)
#assert processor.im.width == 1998
#assert processor.im.height == 1080

processor.outdir = "/tmp/out"
processor.ramp(0, 1, 1)
processor.hold(8)
processor.ramp(1, 0, 1)

