import { GoogleOAuthGuard, IsUserAuthorized } from './google-auth.guard';
import {
  Controller,
  Get,
  HttpException,
  HttpStatus,
  Param,
  Res,
  StreamableFile,
  UseGuards,
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
  private readonly imageCache = new Map<string, string>();

  @Get('history')
  @UseGuards(IsUserAuthorized)
  getMountainHistory(): Promise<string> {
    const bucket = this.storage.bucket(HISTORY_BUCKET, {});
    return bucket
      .getFiles()
      .then((response) =>
        response[0]
          .map((file): MountainFile => {
            return {
              name: file.name,
              datetime: this.formatter.format(
                new Date(
                  file.name.replace('MountRainier-', '').replace('.png', ''),
                ),
              ),
            };
          })
          .sort(
            (a, b) =>
              new Date(a.datetime).getTime() - new Date(b.datetime).getTime(),
          ),
      )
      .then((mountainFiles): MountainHistoryResponse => ({ mountainFiles }))
      .then((response) => JSON.stringify(response));
  }

  @Get('history/:filename')
  @UseGuards(IsUserAuthorized)
  getMountainHistoryFile(
    @Param('filename') filename: string,
    @Res({ passthrough: true }) response: Response,
  ): Promise<StreamableFile> {
    if (this.imageCache.has(filename)) {
      return new Promise((resolve) => {
        sendFile(
          // eslint-disable-next-line @typescript-eslint/no-non-null-assertion
          Buffer.from(this.imageCache.get(filename)!, 'base64'),
          response,
          resolve,
        );
      });
    }
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
          this.imageCache.set(filename, content[0].toString('base64'));
          sendFile(content[0], response, resolve);
        });
      });
    });
  }
}

function sendFile(
  content: Buffer,
  response: Response,
  resolve: (value: StreamableFile) => void,
) {
  tmpFile((err, path, fd, cleanupCallback) => {
    writeFileSync(path, content);
    content.toString('base64');
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
}

interface MountainHistoryResponse {
  readonly mountainFiles: MountainFile[];
}

interface MountainFile {
  readonly name: string;
  readonly datetime: string;
}
