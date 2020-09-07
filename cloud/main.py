import requests
import shutil
import os
import sys

sys.path.append(os.path.join('..'))

classifier = None


def classify(request):
    from trainer.classifier import Classifier, ClassifierOptions
    global classifier
    if classifier is None:
        classifier = Classifier(
            ClassifierOptions(
                saved_model_path=os.path.join(
                    '..', 'trainer', 'isthemountainout.h5'),
                save_labels_file=os.path.join(
                    '..', 'trainer', 'savelabels.txt'),
            )
        )

    classification, confidence, image = classifier.classify(__download_image(
        "http://backend.roundshot.com/cams/241/original"))
    return f'{classification} {confidence:.2f}%'

# download an image and place it in a temporary file


def __download_image(url: str, *, to_file: str = 'current.jpg') -> str:
    request = requests.get(url, stream=True)
    if request.status_code == 200:
        request.raw.decode_content = True
        with open(to_file, 'wb') as f:
            shutil.copyfileobj(request.raw, f)

        return to_file
    else:
        raise IOError('Could not download latest image')
