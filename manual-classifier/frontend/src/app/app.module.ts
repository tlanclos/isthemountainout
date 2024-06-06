import { AppComponent } from './app.component';
import { NgModule } from '@angular/core';
import { BrowserModule } from '@angular/platform-browser';
import { MatCardModule } from '@angular/material/card';
import { MatIconModule } from '@angular/material/icon';
import { ClassifierComponent } from './classifier.component';
import { ClassifierNavigationService } from './classifier-navigation.service';
import { HistoryService } from './history.service';
import { ClassificationService } from './classification.service';
import { BrowserAnimationsModule } from '@angular/platform-browser/animations';
import { MatButtonModule } from '@angular/material/button';
import { MatSnackBarModule } from '@angular/material/snack-bar';
import { RouterModule } from '@angular/router';

@NgModule({
  declarations: [AppComponent, ClassifierComponent],
  imports: [
    BrowserModule,
    BrowserAnimationsModule,
    MatButtonModule,
    MatCardModule,
    MatIconModule,
    MatSnackBarModule,
    RouterModule.forRoot([{ path: '', component: ClassifierComponent }]),
  ],
  providers: [
    ClassifierNavigationService,
    HistoryService,
    ClassificationService,
  ],
  bootstrap: [AppComponent],
})
export class AppModule {}
