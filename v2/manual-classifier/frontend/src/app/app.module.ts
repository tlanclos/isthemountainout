import { NgModule } from '@angular/core';
import { BrowserModule } from '@angular/platform-browser';
import { MatCardModule } from '@angular/material/card';
import { MatIconModule } from '@angular/material/icon';
import { AppComponent } from './app.component';
import { AppNavigationService } from './app-navigation.service';
import { HistoryService } from './history.service';
import { ClassificationService } from './classification.service';
import { BrowserAnimationsModule } from '@angular/platform-browser/animations';
import { MatButtonModule } from '@angular/material/button';

@NgModule({
  declarations: [AppComponent],
  imports: [
    BrowserModule,
    BrowserAnimationsModule,
    MatButtonModule,
    MatCardModule,
    MatIconModule,
  ],
  providers: [AppNavigationService, HistoryService, ClassificationService],
  bootstrap: [AppComponent],
})
export class AppModule {}
