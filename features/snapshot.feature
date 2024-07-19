Feature: Snapshotting

  Scenario: Stores image snapshots
    Given a live image snapshotter
      And storing on a disk
     When executed
     Then stores the image
    
    Given a constant image snapshotter
      And storing on a disk
     When executed
     Then stores the image
