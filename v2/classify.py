from common.image import LatestSnapshotImageProvider

provider = LatestSnapshotImageProvider()
image, date = provider.get()
print(date)
image.show()
