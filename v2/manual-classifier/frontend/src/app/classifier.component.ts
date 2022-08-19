import { ClassifierNavigationService } from './classifier-navigation.service';
import {
  ClassificationService,
  Classifications,
  Classification,
} from './classification.service';
import { Component, ElementRef, OnDestroy, ViewChild } from '@angular/core';
import { combineLatest, of, ReplaySubject, Observable } from 'rxjs';
import { map, shareReplay, switchMap, takeUntil } from 'rxjs/operators';
import { HistoryService } from './history.service';
import { MatSnackBar } from '@angular/material/snack-bar';

@Component({
  selector: 'classifier-component',
  templateUrl: './classifier.component.html',
  styleUrls: ['./classifier.component.scss'],
})
export class ClassifierComponent implements OnDestroy {
  private readonly destroyedSubject = new ReplaySubject<void>(1);
  private readonly mountainPositionIntervalId: number;

  private mountainPosition: [number, number] | undefined = [
    1026.9767441860465, 449.84509466437174,
  ];
  readonly canvasSize = [1920, 1080];

  readonly currentContent$: Observable<MountainImageContent | undefined> =
    this.navigator.currentFile$.pipe(
      switchMap((file) => {
        if (file) {
          return this.history
            .image(file.name)
            .pipe(map((imageBase64) => ({ file, imageBase64 })));
        } else {
          return of(undefined);
        }
      }),
      map((content) => {
        if (content) {
          return {
            title: 'Mt. Rainier',
            subTitle: content.file.name,
            fileName: content.file.name,
            imageBase64Url: `data:image/png;base64,${content.imageBase64}`,
          };
        } else {
          return undefined;
        }
      }),
    );

  @ViewChild('mountainCanvas')
  mountainCanvas!: ElementRef<HTMLCanvasElement>;

  @ViewChild('mountainImage')
  mountainImage!: ElementRef<HTMLImageElement>;

  readonly classificationOptions$ = this.classifications
    .options()
    .pipe(shareReplay(1));

  readonly classificationUpdates = new Map<string, Classification>();

  constructor(
    readonly navigator: ClassifierNavigationService,
    private readonly history: HistoryService,
    private readonly classifications: ClassificationService,
    private readonly snackBar: MatSnackBar,
  ) {
    combineLatest({
      content: this.currentContent$,
      classifications: this.classifications.load().pipe(shareReplay(1)),
    })
      .pipe(takeUntil(this.destroyedSubject))
      .subscribe(({ content, classifications }) => {
        if (!content) {
          return;
        }
        if (this.classificationUpdates.has(content.fileName)) {
          this.mountainPosition = this.classificationUpdates.get(
            content.fileName,
          )!.mountainPosition;
        } else if (classifications[content.fileName]) {
          this.mountainPosition =
            classifications[content.fileName].mountainPosition;
        }
      });
    this.mountainPositionIntervalId = setInterval(() => {
      if (this.mountainCanvas && this.mountainImage) {
        this.drawMountainPosition(
          this.mountainCanvas.nativeElement,
          this.mountainImage.nativeElement,
        );
      }
    }, 250);
    this.reload();
  }

  private reload() {
    this.navigator.reload();
    this.classificationUpdates.clear();
  }

  ngOnDestroy(): void {
    clearInterval(this.mountainPositionIntervalId);
    this.destroyedSubject.next();
    this.destroyedSubject.complete();
  }

  classify(filename: string, option: string) {
    assertExists(this.mountainPosition !== undefined);
    this.classificationUpdates.set(filename, {
      classification: option,
      mountainPosition: this.mountainPosition!,
    });
    this.navigator.next();
  }

  setPosition(
    event: MouseEvent,
    mountainCanvas: HTMLCanvasElement,
    mountainImage: HTMLImageElement,
  ) {
    const imagePositionX =
      (event.offsetX / mountainCanvas.clientWidth) * mountainImage.naturalWidth;
    const imagePositionY =
      (event.offsetY / mountainCanvas.clientHeight) *
      mountainImage.naturalHeight;
    this.mountainPosition = [imagePositionX, imagePositionY];
    this.drawMountainPosition(mountainCanvas, mountainImage);
  }

  drawMountainPosition(canvas: HTMLCanvasElement, image: HTMLImageElement) {
    if (this.mountainPosition === undefined) {
      return;
    }

    const canvasPositionX =
      this.mountainPosition[0] * (canvas.width / image.naturalWidth);
    const canvasPositionY =
      this.mountainPosition[1] * (canvas.height / image.naturalHeight);

    const context = canvas.getContext('2d')!;
    context.clearRect(0, 0, this.canvasSize[0], this.canvasSize[1]);
    context.beginPath();
    context.arc(canvasPositionX, canvasPositionY, 10, 0, 2 * Math.PI, false);
    context.fillStyle = 'red';
    context.fill();
  }

  saveClassificationUpdates(updates: Map<string, Classification>) {
    const classifications: Classifications = {};
    for (const [filename, classification] of updates.entries()) {
      classifications[filename] = classification;
    }
    this.classifications.save(classifications).subscribe(() => {
      this.snackBar.open('Successfully uploaded classifications!', 'Dismiss', {
        horizontalPosition: 'end',
        verticalPosition: 'top',
        duration: 2000,
      });
    });
    this.reload();
  }
}

function assertExists<T>(value: T | undefined): value is T {
  if (value === undefined) {
    throw new Error('value was undefined');
  }
  return true;
}

interface MountainImageContent {
  readonly title: string;
  readonly subTitle: string;
  readonly fileName: string;
  readonly imageBase64Url: string;
}
