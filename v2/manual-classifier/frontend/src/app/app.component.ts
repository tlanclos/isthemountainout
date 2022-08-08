import { AppNavigationService } from './app-navigation.service';
import {
  ClassificationService,
  Classifications,
} from './classification.service';
import { Component } from '@angular/core';
import { filter, map, shareReplay, switchMap } from 'rxjs/operators';
import { HistoryService, MountainFile } from './history.service';

@Component({
  selector: 'app-root',
  templateUrl: './app.component.html',
  styleUrls: ['./app.component.scss'],
})
export class AppComponent {
  readonly currentContent$ = this.navigator.currentFile$.pipe(
    filter((file): file is MountainFile => file !== undefined),
    switchMap((file) =>
      this.history
        .image(file.name)
        .pipe(map((imageBase64) => ({ file, imageBase64 }))),
    ),
    map((content) => ({
      title: 'Mt. Rainier',
      subTitle: content.file.name,
      fileName: content.file.name,
      imageBase64Url: `data:image/png;base64,${content.imageBase64}`,
    })),
  );

  readonly classificationOptions$ = this.classifications
    .options()
    .pipe(shareReplay(1));

  readonly classificationUpdates = new Map<string, string>();

  constructor(
    readonly navigator: AppNavigationService,
    private readonly history: HistoryService,
    private readonly classifications: ClassificationService,
  ) {
    this.navigator.reload();
  }

  classify(filename: string, option: string) {
    this.classificationUpdates.set(filename, option);
    this.navigator.next();
  }

  saveClassificationUpdates(updates: Map<string, string>) {
    const classifications: Classifications = {};
    for (const [filename, classification] of updates.entries()) {
      classifications[filename] = { classification };
    }
    this.classifications.save(classifications).subscribe();
  }
}
