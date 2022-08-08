import { Injectable } from '@angular/core';
import { from, Observable } from 'rxjs';
import { map } from 'rxjs/operators';
import axios from 'axios';

@Injectable()
export class ClassificationService {
  options(): Observable<string[]> {
    return from(axios('/api/classifications/options')).pipe(
      map((response) => response.data.options),
    );
  }

  load(): Observable<Classifications> {
    return from(axios('/api/classifications')).pipe(
      map((response) => response.data as Classifications),
    );
  }

  save(updates: Classifications) {
    return from(axios.put('/api/classifications', updates));
  }
}

export interface Classifications {
  [filename: string]: Classification;
}

export interface Classification {
  readonly classification: string;
  readonly mountainPosition: [number, number];
}
