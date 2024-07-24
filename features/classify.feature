Feature: Classification

  Scenario: Classifies and posts an image
    Given today is 2024-01-01T20:00:00-08:00
      And an image that classifies as night
      And an in memory classification tracker
      And the isthemountainout model interpreter
      And a mock publisher
     When classify is executed
     Then the latest tracked classification is night
      And the image should not be posted
      And the image will not be posted

    Given today is 2024-01-01T12:00:00-08:00
      And an image that classifies as hidden
      And an in memory classification tracker
      And the isthemountainout model interpreter
      And a mock publisher
     When classify is executed
     Then the latest tracked classification is hidden
      And the image should be posted
      And the image will be posted

    Given today is 2024-01-01T12:00:00-08:00
      And an image that classifies as mystical
      And an in memory classification tracker
      And the isthemountainout model interpreter
      And a mock publisher
     When classify is executed
     Then the latest tracked classification is mystical
      And the image should be posted
      And the image will be posted

    Given today is 2024-01-01T12:00:00-08:00
      And an image that classifies as beautiful
      And an in memory classification tracker
      And the isthemountainout model interpreter
      And a mock publisher
     When classify is executed
     Then the latest tracked classification is beautiful
      And the image should be posted
      And the image will be posted

  Scenario: Posts an image once per day
    Given today is 2024-01-01T12:00:00-08:00
      And an image that classifies as mystical, mystical, mystical, mystical
      And an in memory classification tracker
      And the isthemountainout model interpreter
      And a mock publisher
     When the latest classification is hidden
      And classify is executed
     Then the classification, mystical, was posted exactly once

  Scenario: Posts only notable changes
    Given today is 2024-01-01T12:00:00-08:00
      And an image that classifies as hidden, hidden, hidden
      And an in memory classification tracker
      And the isthemountainout model interpreter
      And a mock publisher
     When the latest classification is night
      And classify is executed 3 times
     Then the classification, hidden, was posted exactly once

    Given today is 2024-01-01T12:00:00-08:00
      And an image that classifies as mystical, mystical, mystical
      And an in memory classification tracker
      And the isthemountainout model interpreter
      And a mock publisher
     When the latest classification is night
      And classify is executed 3 times
     Then the classification, mystical, was posted exactly once

    Given today is 2024-01-01T12:00:00-08:00
      And an image that classifies as beautiful, beautiful, beautiful
      And an in memory classification tracker
      And the isthemountainout model interpreter
      And a mock publisher
     When the latest classification is night
      And classify is executed 3 times
     Then the classification, beautiful, was posted exactly once

    Given today is 2024-01-01T12:00:00-08:00
      And an image that classifies as mystical, mystical, mystical
      And an in memory classification tracker
      And the isthemountainout model interpreter
      And a mock publisher
     When the latest classification is hidden
      And classify is executed 3 times
     Then the classification, mystical, was posted exactly once

    Given today is 2024-01-01T12:00:00-08:00
      And an image that classifies as beautiful, beautiful, beautiful
      And an in memory classification tracker
      And the isthemountainout model interpreter
      And a mock publisher
     When the latest classification is hidden
      And classify is executed 3 times
     Then the classification, beautiful, was posted exactly once

    Given today is 2024-01-01T12:00:00-08:00
      And an image that classifies as beautiful, beautiful, beautiful
      And an in memory classification tracker
      And the isthemountainout model interpreter
      And a mock publisher
     When the latest classification is mystical
      And classify is executed 3 times
     Then the classification, beautiful, was posted exactly once

    Given today is 2024-01-01T12:00:00-08:00
      And an image that classifies as hidden, hidden, hidden
      And an in memory classification tracker
      And the isthemountainout model interpreter
      And a mock publisher
     When the latest classification is beautiful
      And classify is executed 3 times
     Then the classification, hidden, was posted exactly once

    Given today is 2024-01-01T12:00:00-08:00
      And an image that classifies as mystical, mystical, mystical
      And an in memory classification tracker
      And the isthemountainout model interpreter
      And a mock publisher
     When the latest classification is beautiful
      And classify is executed 3 times
     Then the classification, mystical, was never posted
