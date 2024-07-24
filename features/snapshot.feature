Feature: Snapshotting

  Scenario: Stores image snapshots
    Given today is 2024-01-01T00:00:00Z
      And a live image provider
      And a disk storage
     When snapshot is executed
     Then stores an image
    
    Given today is 2024-01-01T00:00:00Z
      And a constant image provider
      And a disk storage
     When snapshot is executed
     Then stores an image
