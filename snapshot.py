"""
Provides snapshotting capabilities to the Mt. Rainier detection robot.
"""
import argparse

from common.config import RootConfiguration, create_root_config

parser = argparse.ArgumentParser(
    description='Snapshot an image of Mount Rainier')
parser.add_argument(
    '--config',
    type=create_root_config,
    help='Path to the configuration file')


def main(*, config: RootConfiguration):
    """
    Provided a configuration, requests an image and 
    stores it somewhere.
    """
    config.snapshotter.snapshot()


if __name__ == '__main__':
    args = parser.parse_args()
    main(config=args.config)
