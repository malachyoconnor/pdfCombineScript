from PIL import Image
import sys
import os
import platform
import threading

CHAPTERS_PER_PDF = 25
CURRENT_DIR = os.getcwd()

SPLIT_BY = "/"

if platform.system() == "Windows":
    SPLIT_BY = "\\"

MANGA_NAME = CURRENT_DIR.split(SPLIT_BY)[-1]

PROCESSING_SEM = threading.Semaphore()


def getChapterAndPage(path: str) -> tuple[str, str]:
    chapter, page = path.split(SPLIT_BY)[-2:]
    return (chapter, page)


droppedDict: dict[str, str] = dict()
chapterDirs = sorted([dir for dir in os.listdir(CURRENT_DIR) if os.path.isdir(CURRENT_DIR + SPLIT_BY + dir)])

allFiles = [[] for x in chapterDirs]
droppedPages = set()

for ind, chapterInd in enumerate(chapterDirs):
    chapterLocation = f"{CURRENT_DIR}{SPLIT_BY}{chapterInd}"
    for page in sorted(os.listdir(chapterLocation)):
        pageLocation = chapterLocation + SPLIT_BY + page
        allFiles[ind].append(pageLocation)


def combinePDF(start: int, end: int) -> None:
    try:
        startChap = allFiles[start][0].split(SPLIT_BY)[-2]
        endChap = allFiles[end - 1][0].split(SPLIT_BY)[-2]
        pages = []
        for chapterInd in range(start, end):
            for pageLocation in allFiles[chapterInd]:
                page = Image.open(pageLocation)
                page = page.convert("RGB")
                pages.append(page)
            PROCESSING_SEM.release()
        pages[0].save(f"{CURRENT_DIR}{SPLIT_BY}{MANGA_NAME}_{startChap}-{endChap}.pdf", save_all=True, append_images=pages[1:])
        del pages  # Explicitly clear memory
    except (KeyboardInterrupt, SystemError):
        sys.exit()


threadList = []
for chaptersNum in range(CHAPTERS_PER_PDF, len(allFiles) + CHAPTERS_PER_PDF, CHAPTERS_PER_PDF):
    thread = threading.Thread(target=combinePDF, args=(chaptersNum - CHAPTERS_PER_PDF, min(chaptersNum, len(allFiles))))
    threadList.append(thread)
    thread.start()


def updateProgress(processedItems: int, totalItems: int, description=None) -> None:
    percentage = int((processedItems) / totalItems * 100)

    print(f"[{u'█' * (percentage)}{"." * (100 - percentage)}] {processedItems}/{totalItems} : {description}",
          end="\r",
          file=sys.stdout,
          flush=True)


try:
    CHAPTERS_PROCESSED = 0
    while CHAPTERS_PROCESSED < len(allFiles):
        PROCESSING_SEM.acquire()
        CHAPTERS_PROCESSED = CHAPTERS_PROCESSED + 1
        updateProgress(CHAPTERS_PROCESSED, len(allFiles), "Processing chapters...")
except (KeyboardInterrupt, SystemError):
    sys.exit(1)

print("\n\n\n")
for i, t in enumerate(threadList):
    updateProgress(i + 1, len(threadList), "Combining chapters...")
    t.join()
updateProgress(len(threadList), len(threadList), "Combining chapters...")
