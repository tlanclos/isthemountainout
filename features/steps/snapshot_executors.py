from behave import *

import snapshot
from common.config import RootConfiguration
from common.snapshot import Snapshotter


@when(u'snapshot is executed')
def execute_snapshot(context):
    snapshot.main(config=RootConfiguration(
        brand=None,
        classifier=None,
        classification_tracker=None,
        snapshotter=Snapshotter(
            image_provider=context.image_provider,
            store=context.storage
        ),
        publishers=[]))
