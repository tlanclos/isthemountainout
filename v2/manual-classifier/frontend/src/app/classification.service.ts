import { ActivatedRoute } from '@angular/router';
import { Injectable } from '@angular/core';
import { from, Observable } from 'rxjs';
import { map } from 'rxjs/operators';
import axios from 'axios';

@Injectable()
export class ClassificationService {
  constructor(private readonly route: ActivatedRoute) {}

  options(): Observable<string[]> {
    return from(
      axios('/api/classifications/options', {
        params: this.route.snapshot.queryParams,
      }),
    ).pipe(map((response) => response.data.options));
  }

  load(): Observable<Classifications> {
    return from(
      axios('/api/classifications', {
        params: this.route.snapshot.queryParams,
      }),
    ).pipe(map((response) => response.data as Classifications));
  }

  save(updates: Classifications) {
    return from(
      axios.put('/api/classifications', updates, {
        params: this.route.snapshot.queryParams,
      }),
    );
  }
}

export interface Classifications {
  [filename: string]: Classification;
}

export interface Classification {
  readonly classification: string;
  readonly mountainPosition: [number, number];
}
