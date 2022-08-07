import {
  Controller,
  Get,
  Put,
  Body,
  HttpException,
  HttpStatus,
} from '@nestjs/common';
import { Storage } from '@google-cloud/storage';

const CLASSIFICATIONS: BucketFile = {
  bucketName: 'isthemountainout.appspot.com',
  fileName: 'mountain-history.classifications.json',
};

@Controller('api/classifications')
export class ClassificationsController {
  private readonly storage = new Storage({});

  @Get()
  getClassifications(): Promise<string> {
    const bucket = this.storage.bucket(CLASSIFICATIONS.bucketName, {});
    const file = bucket.file(CLASSIFICATIONS.fileName, {});
    return file.exists().then((exists) => {
      if (exists[0]) {
        return file.download().then((data) => data[0].toString());
      } else {
        return JSON.stringify({});
      }
    });
  }

  @Put()
  updateClassifications(@Body() request: unknown): Promise<string> {
    assertClassifications(request);
    const bucket = this.storage.bucket(CLASSIFICATIONS.bucketName, {});
    const file = bucket.file(CLASSIFICATIONS.fileName, {});
    const content = JSON.stringify(request);
    return file.save(content).then(() => content);
  }
}

function assertClassifications(value: unknown): value is Classifications {
  const classifications = value as Classifications;
  for (const [filename, value] of Object.entries(classifications)) {
    if (typeof filename !== 'string') {
      throw new HttpException(
        'Each key must be a filename string',
        HttpStatus.BAD_REQUEST,
      );
    }
    assertClassification(value);
  }
  return true;
}

function assertClassification(value: unknown): value is Classification {
  const classification = value as Classification;
  if (
    !Object.values(ClassificationNameEnum).includes(
      classification.classification,
    )
  ) {
    throw new HttpException(
      `classification must be one of ${Object.values(
        ClassificationNameEnum,
      ).join(',')}.`,
      HttpStatus.BAD_REQUEST,
    );
  }
  return true;
}

interface Classifications {
  [filename: string]: Classification;
}

interface Classification {
  readonly classification: ClassificationName;
}

enum ClassificationNameEnum {
  NIGHT = 'Night',
  HIDDEN = 'Hidden',
  MYSTICAL = 'Mystical',
  BEAUTIFUL = 'Beautiful',
}
type ClassificationName =
  typeof ClassificationNameEnum[keyof typeof ClassificationNameEnum];

interface BucketFile {
  readonly bucketName: string;
  readonly fileName: string;
}
