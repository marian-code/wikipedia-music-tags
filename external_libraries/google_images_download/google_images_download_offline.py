import os
from wiki_music.constants.paths import ROOT_DIR
from PIL import Image


class googleimagesdownload:

    def __init__(self):
        self.thumbs = []
        self.fullsize_url = []
        self.fullsize_dim = []
        self.count = 0
        self.finished = False
        self._exit = False

    def download(self, arguments):

        print(f"\nItem no.: 1 --> Item name = {arguments['keywords']}")
        print("Evaluating...")

        files = self.list_files()
        errorCount = 0

        for f in files:

            dim = Image.open(f).size
            disk_size = os.path.getsize(f)

            try:
                with open(f, "rb") as infile:
                    self.thumbs.append(bytearray(infile.read()))
                self.fullsize_dim.append([disk_size, dim])
                self.fullsize_url.append(f)
            except Exception as e:
                print(e)
                errorCount += 1
            else:
                self.count += 1
                print(f"Completed Image Thumbnail ====> {self.count}. {f}")

            if self._exit:
                print("Album art search exiting ...")
                return self.thumbs, errorCount, files

        print(f"\nErrors: {errorCount}\n")

        self.finished = True

    def close(self):
        self._exit = True

    def list_files(self):

        folder = os.path.join(ROOT_DIR, "tests", "offline_debug")

        return [os.path.join(folder, f.name) for f in os.scandir(folder)
                if f.is_file() and f.name.casefold().endswith(("jpg", "png"))]

    def get_max(self):
        return len(self.list_files())

