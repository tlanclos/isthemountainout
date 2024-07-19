Feature: Snapshotting

  Scenario: Stores image snapshots
    Given a live image provider
      And a disk storage
     When snapshot is executed
     Then stores an image
    
    Given a constant image provider
      And a disk storage
     When snapshot is executed
     Then stores an image
