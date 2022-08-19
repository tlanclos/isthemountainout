import { ClassificationService } from './classification.service';
import { BehaviorSubject, combineLatest } from 'rxjs';
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

  next() {
    this.index = Math.min(this.index + 1, this.files.length - 1);
    this.currentFileSubject.next(this.files[this.index]);
  }

  previous() {
    this.index = Math.max(0, this.index - 1);
    this.currentFileSubject.next(this.files[this.index]);
  }
}
