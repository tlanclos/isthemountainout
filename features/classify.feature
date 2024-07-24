Feature: Classification

  Scenario: Classifies and posts an image
    Given today is 2024-01-01T00:00:00Z
      And an image that classifies as "Night"
      And an in memory classification tracker
      And the isthemountainout model interpreter
      And a mock publisher
     When classify is executed
     Then the latest tracked classification is "Night"
      But the image should not be posted
      And the image will not be posted

    Given today is 2024-01-01T00:00:00Z
      And an image that classifies as "Hidden"
      And an in memory classification tracker
      And the isthemountainout model interpreter
      And a mock publisher
     When classify is executed
     Then the latest tracked classification is "Hidden"
      But the image should not be posted
      And the image will not be posted

    Given today is 2024-01-01T00:00:00Z
      And an image that classifies as "Mystical"
      And an in memory classification tracker
      And the isthemountainout model interpreter
      And a mock publisher
     When classify is executed
     Then the latest tracked classification is "Mystical"
      But the image should not be posted
      And the image will not be posted

    Given today is 2024-01-01T00:00:00Z
      And an image that classifies as "Beautiful"
      And an in memory classification tracker
      And the isthemountainout model interpreter
      And a mock publisher
     When classify is executed
     Then the latest tracked classification is "Beautiful"
      But the image should not be posted
      And the image will not be posted

# Test posting an image
# Test that posting only happens once
# Test that posting only posts on notable changes