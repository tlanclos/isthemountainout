import { AfterViewInit, Component } from '@angular/core';

@Component({
  selector: 'app-root',
  template: '<router-outlet></router-outlet>',
})
export class AppComponent implements AfterViewInit {
  ngAfterViewInit(): void {
    if (!new URL(window.location.href).searchParams.get('accessToken')) {
      this.authenticate();
    }
  }

  authenticate() {
    window.location.href = '/auth';
  }
}
