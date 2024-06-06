import { IsUserAuthorized } from './google-auth.guard';
import {
  Controller,
  Get,
  Put,
  Body,
  HttpException,
  HttpStatus,
  UseGuards,
} from '@nestjs/common';
import { Storage } from '@google-cloud/storage';

const CLASSIFICATIONS: BucketFile = {
  bucketName: 'isthemountainout.appspot.com',
  fileName: 'mountain-history.classifications.json',
};

@Controller('api/classifications')
export class ClassificationsController {
  private readonly storage = new Storage({});

  private getCurrentClassifications(): Promise<Classifications> {
    const bucket = this.storage.bucket(CLASSIFICATIONS.bucketName, {});
    const file = bucket.file(CLASSIFICATIONS.fileName, {});
    return file.exists().then((exists) => {
      if (exists[0]) {
        return file.download().then((data) => JSON.parse(data[0].toString()));
      } else {
        return {};
      }
    });
  }

  @Get()
  @UseGuards(IsUserAuthorized)
  getClassifications(): Promise<string> {
    return this.getCurrentClassifications().then((classifications) =>
      JSON.stringify(classifications),
    );
  }

  @Get('options')
  @UseGuards(IsUserAuthorized)
  getClassificationOptions(): string {
    return JSON.stringify({ options: Object.values(ClassificationNameEnum) });
  }

  @Put()
  @UseGuards(IsUserAuthorized)
  updateClassifications(@Body() request: unknown): Promise<string> {
    assertClassifications(request);
    return this.getCurrentClassifications().then((currentClassifications) => {
      for (const [filename, classification] of Object.entries(request)) {
        currentClassifications[filename] = {
          ...currentClassifications[filename],
          ...classification,
        };
      }
      const bucket = this.storage.bucket(CLASSIFICATIONS.bucketName, {});
      const file = bucket.file(CLASSIFICATIONS.fileName, {});
      const content = JSON.stringify(currentClassifications);
      return file.save(content).then(() => content);
    });
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
