import requests
import shutil
import os
from trainer.classifier import Classifier, ClassifierOptions

classifier = None


def classify(request):
    global classifier
    if classifier is None:
        classifier = Classifier(
            ClassifierOptions(
                saved_model_path=os.path.join(
                    'trainer', 'isthemountainout.h5'),
                save_labels_file=os.path.join(
                    'trainer', 'savelabels.txt'),
            )
        )

    classification, confidence, image = classifier.classify(__download_image(
        "http://backend.roundshot.com/cams/241/original"))
    return f'{classification} {confidence:.2f}%'


def __download_image(url: str, *, to_file: str = '/tmp/current.jpg') -> str:
    # download an image and place it in a temporary file
    request = requests.get(url, stream=True)
    if request.status_code == 200:
        request.raw.decode_content = True
        with open(to_file, 'wb') as f:
            shutil.copyfileobj(request.raw, f)

        return to_file
    else:
        raise IOError('Could not download latest image')
