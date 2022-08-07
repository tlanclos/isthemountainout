import {
  Controller,
  Get,
  HttpException,
  HttpStatus,
  Param,
  Res,
  StreamableFile,
} from '@nestjs/common';
import { Storage } from '@google-cloud/storage';
import { file as tmpFile } from 'tmp';
import { createReadStream, writeFileSync } from 'fs';
import type { Response } from 'express';

const HISTORY_BUCKET = 'mountain-history';

@Controller('api/mountain')
export class MountainController {
  private readonly storage = new Storage({});
  private readonly formatter = new Intl.DateTimeFormat('en-US', {
    dateStyle: 'short',
    timeStyle: 'short',
    timeZone: 'America/Los_Angeles',
  });

  @Get('history')
  getMountainHistory(): Promise<string> {
    const bucket = this.storage.bucket(HISTORY_BUCKET, {});
    return bucket
      .getFiles()
      .then((response) =>
        response[0].map((file): MountainFile => {
          return {
            name: file.name,
            datetime: this.formatter.format(
              new Date(
                file.name.replace('MountRainier-', '').replace('.png', ''),
              ),
            ),
          };
        }),
      )
      .then((mountainFiles): MountainHistoryResponse => ({ mountainFiles }))
      .then((response) => JSON.stringify(response));
  }

  @Get('history/:filename')
  getMountainHistoryFile(
    @Param('filename') filename: string,
    @Res({ passthrough: true }) response: Response,
  ): Promise<StreamableFile> {
    const bucket = this.storage.bucket(HISTORY_BUCKET, {});
    const file = bucket.file(filename, {});
    return file.exists().then((exists) => {
      if (!exists[0]) {
        throw new HttpException(
          `Mountain history file, ${filename}, does not exists.`,
          HttpStatus.BAD_REQUEST,
        );
      }
      return file.download().then((content) => {
        return new Promise((resolve) => {
          tmpFile((err, path, fd, cleanupCallback) => {
            writeFileSync(path, content[0]);
            console.log(path);
            response.set({
              'Content-Type': 'image/png',
              'Content-Disposition': `inline`,
            });
            const f = createReadStream(path);
            f.on('close', () => {
              cleanupCallback();
            });
            resolve(new StreamableFile(f));
          });
        });
      });
    });
  }
}

interface MountainHistoryResponse {
  readonly mountainFiles: MountainFile[];
}

interface MountainFile {
  readonly name: string;
  readonly datetime: string;
}

interface BucketFile {
  readonly bucketName: string;
  readonly fileName: string;
}
