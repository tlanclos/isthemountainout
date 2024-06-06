import { ActivatedRoute } from '@angular/router';
import { Injectable } from '@angular/core';
import { from, Observable } from 'rxjs';
import { map } from 'rxjs/operators';
import axios from 'axios';
import { Buffer } from 'buffer';

@Injectable()
export class HistoryService {
  constructor(private readonly route: ActivatedRoute) {}

  list(): Observable<MountainFile[]> {
    return from(
      axios.get('/api/mountain/history', {
        params: this.route.snapshot.queryParams,
      }),
    ).pipe(map((response) => response.data.mountainFiles as MountainFile[]));
  }

  image(filename: string): Observable<string> {
    return from(
      axios.get(`/api/mountain/history/${filename}`, {
        responseType: 'arraybuffer',
        params: this.route.snapshot.queryParams,
      }),
    ).pipe(
      map((response) =>
        Buffer.from(response.data, 'binary').toString('base64'),
      ),
    );
  }
}

export interface MountainFile {
  readonly name: string;
  readonly datetime: string;
}
