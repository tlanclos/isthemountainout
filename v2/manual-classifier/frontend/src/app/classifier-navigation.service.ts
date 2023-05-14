import { ClassificationService } from './classification.service';
import { BehaviorSubject, Observable, combineLatest, from } from 'rxjs';
import { HistoryService, MountainFile } from './history.service';
import { Injectable } from '@angular/core';

@Injectable()
export class ClassifierNavigationService {
  private index = -1;
  private files: readonly MountainFile[] = [];

  private readonly currentFileSubject = new BehaviorSubject<
    MountainFile | undefined
  >(undefined);

  readonly currentFile$ = this.currentFileSubject.asObservable();

  constructor(
    private readonly history: HistoryService,
    private readonly classification: ClassificationService,
  ) {}

  reload() {
    combineLatest({
      files: this.history.list(),
      classifications: this.classification.load(),
    }).subscribe(({ files, classifications }) => {
      this.files = files.filter((f) => classifications[f.name] === undefined);
      this.index = -1;
      this.next();
    });
  }

  /** Get an observable returning the next {count} filenames in the current list. */
  peek(count: number): Observable<MountainFile> {
    const files: MountainFile[] = [];
    let currentIndex = this.index;
    for (let i = 0; i < count; i++) {
      const nextIndex = Math.min(currentIndex + 1, this.files.length - 1);
      if (nextIndex === currentIndex) {
        break;
      }
      files.push(this.files[nextIndex]);
      currentIndex = nextIndex;
    }
    return from(files);
  }

  next() {
    this.index = Math.min(this.index + 1, this.files.length - 1);
    this.currentFileSubject.next(this.files[this.index]);
  }

  previous() {
    this.index = Math.max(0, this.index - 1);
    this.currentFileSubject.next(this.files[this.index]);
  }
}
