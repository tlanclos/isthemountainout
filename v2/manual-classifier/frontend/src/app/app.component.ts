import { AppNavigationService } from './app-navigation.service';
import {
  ClassificationService,
  Classifications,
  Classification,
} from './classification.service';
import {
  AfterViewInit,
  Component,
  ElementRef,
  OnDestroy,
  ViewChild,
} from '@angular/core';
import { combineLatest, ReplaySubject } from 'rxjs';
import { filter, map, shareReplay, switchMap, takeUntil } from 'rxjs/operators';
import { HistoryService, MountainFile } from './history.service';

@Component({
  selector: 'app-root',
  templateUrl: './app.component.html',
  styleUrls: ['./app.component.scss'],
})
export class AppComponent implements OnDestroy {
  private readonly destroyedSubject = new ReplaySubject<void>(1);

  private mountainPosition: [number, number] | undefined = [
    1026.9767441860465, 449.84509466437174,
  ];
  readonly canvasSize = [1920, 1080];

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

  @ViewChild('mountainCanvas')
  mountainCanvas!: ElementRef<HTMLCanvasElement>;

  @ViewChild('mountainImage')
  mountainImage!: ElementRef<HTMLImageElement>;

  readonly classificationOptions$ = this.classifications
    .options()
    .pipe(shareReplay(1));

  readonly classificationUpdates = new Map<string, Classification>();

  constructor(
    readonly navigator: AppNavigationService,
    private readonly history: HistoryService,
    private readonly classifications: ClassificationService,
  ) {
    combineLatest({
      content: this.currentContent$,
      classifications: this.classifications.load().pipe(shareReplay(1)),
    })
      .pipe(takeUntil(this.destroyedSubject))
      .subscribe(({ content, classifications }) => {
        if (this.classificationUpdates.has(content.fileName)) {
          this.mountainPosition = this.classificationUpdates.get(
            content.fileName,
          )!.mountainPosition;
        } else if (classifications[content.fileName]) {
          this.mountainPosition =
            classifications[content.fileName].mountainPosition;
        }
      });
    this.navigator.reload();
  }

  ngDoCheck() {
    if (this.mountainCanvas && this.mountainImage) {
      this.drawMountainPosition(
        this.mountainCanvas.nativeElement,
        this.mountainImage.nativeElement,
      );
    }
  }

  ngOnDestroy(): void {
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
    this.classifications.save(classifications).subscribe();
    this.navigator.reload();
  }
}

function assertExists<T>(value: T | undefined): value is T {
  if (value === undefined) {
    throw new Error('value was undefined');
  }
  return true;
}
